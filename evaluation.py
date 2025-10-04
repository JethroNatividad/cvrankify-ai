import os
import json
import datetime
from prompts import (
    get_edu_timezone_prompt,
    get_skill_prompt,
    get_experience_prompt,
)
from utils import clean_response, extract_pdf_text
from ollama import Client
from extract2 import extract_text_word_level_columns

client = Client()

pdf_resumes = [f for f in os.listdir("resumes") if f.endswith(".pdf")]

json_expected = [f for f in os.listdir("resumes") if f.endswith("_expected.json")]

evaluation_dataset = {}
for pdf in pdf_resumes:
    expected_file = pdf.replace(".pdf", "_expected.json")
    if expected_file in json_expected:
        evaluation_dataset[pdf] = expected_file

output_dir = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
os.makedirs(os.path.join("evaluation", output_dir), exist_ok=True)

models = [
    (
        "edu-timezone-extractor:latest",
        "experience-extractor:latest",
        "skills-extractor:latest",
        "mixed-model-1",
    )
]
# models = ["qwen3:8b", "deepseek-r1:8b", "llama3.1:8b", "gemma3:4b"]
runs_per_model = 1

for pdf_file, expected_output_path in evaluation_dataset.items():
    with open(os.path.join("resumes", pdf_file), "rb") as resume_pdf:
        pdf_text = extract_text_word_level_columns(resume_pdf)
        print(f"Evaluating {pdf_file}...")

        for model in models:
            (model_edu, model_exp, model_skill, dir_label) = model
            runs = []
            for run in range(runs_per_model):
                predicted = {}
                print(f"  Run {run + 1}/{runs_per_model}...")
                print(f"    Using model {model_edu} to extract edu-timezone..")
                edu_timezone_response = client.chat(
                    model=model_edu,
                    messages=[
                        {
                            "role": "user",
                            "content": pdf_text,
                        },
                    ],
                    think=False,
                )
                print(f"    Using model {model_skill} to extract skills..")
                skill_response = client.chat(
                    model=model_skill,
                    messages=[
                        {
                            "role": "user",
                            "content": pdf_text,
                        },
                    ],
                    think=False,
                )

                print(f"    Using model {model_exp} to extract experience..")
                experience_response = client.chat(
                    model=model_exp,
                    messages=[
                        {
                            "role": "user",
                            "content": pdf_text,
                        },
                    ],
                    think=False,
                )

                edu_timezone_response = clean_response(
                    edu_timezone_response["message"]["content"]
                )
                skill_response = clean_response(skill_response["message"]["content"])
                experience_response = clean_response(
                    experience_response["message"]["content"]
                )

                try:
                    # load each part as json
                    edu_timezone_json = json.loads(edu_timezone_response)
                    skill_json = json.loads(skill_response)
                    experience_json = json.loads(experience_response)

                    # Combine all three parts into one JSON
                    response_json = {
                        **edu_timezone_json,
                        **skill_json,
                        **experience_json,
                    }

                    predicted = response_json
                    print(f"      Predicted: {predicted}")
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    print(edu_timezone_response)
                    print(skill_response)
                    print(experience_response)
                    continue

                # Calculate metrics
                metrics = {
                    "highestEducationDegree": 0.0,
                    "educationField": 0.0,
                    "timezone": 0.0,
                    "skills_precision": 0.0,
                    "skills_recall": 0.0,
                    "skills_f1": 0.0,
                    "experiencePeriods_accuracy": 0.0,
                }
                with open(os.path.join("resumes", expected_output_path), "r") as f:
                    expected_output = json.load(f)
                    # highestEducationDegree, educationField, timezone = exact match
                    for key in ["highestEducationDegree", "educationField", "timezone"]:
                        if key in expected_output and key in predicted:
                            metrics[key] = (
                                1.0 if expected_output[key] == predicted[key] else 0.0
                            )
                        else:
                            metrics[key] = 0.0

                    # skills = precision, recall, f1
                    if "skills" in expected_output and "skills" in predicted:
                        expected_skills = set(
                            skill.lower() for skill in expected_output["skills"]
                        )
                        predicted_skills = set(
                            skill.lower() for skill in predicted["skills"]
                        )
                        true_positives = len(expected_skills & predicted_skills)
                        precision = (
                            true_positives / len(predicted_skills)
                            if predicted_skills
                            else 0.0
                        )
                        recall = (
                            true_positives / len(expected_skills)
                            if expected_skills
                            else 0.0
                        )
                        f1 = (
                            2 * (precision * recall) / (precision + recall)
                            if (precision + recall) > 0
                            else 0.0
                        )
                        metrics["skills_precision"] = precision
                        metrics["skills_recall"] = recall
                        metrics["skills_f1"] = f1
                    else:
                        metrics["skills_precision"] = 0.0
                        metrics["skills_recall"] = 0.0
                        metrics["skills_f1"] = 0.0
                    # experiencePeriods = accuracy (exact match of list of dicts, order-independent)
                    if (
                        "experiencePeriods" in expected_output
                        and "experiencePeriods" in predicted
                    ):
                        expected_experience = expected_output["experiencePeriods"]
                        predicted_experience = predicted["experiencePeriods"]
                        # Convert dicts to tuples of sorted items for hashability (order-independent comparison)
                        expected_tuples = set(
                            tuple(sorted(exp.items())) for exp in expected_experience
                        )
                        predicted_tuples = set(
                            tuple(sorted(pred.items())) for pred in predicted_experience
                        )
                        metrics["experiencePeriods_accuracy"] = (
                            len(expected_tuples & predicted_tuples)
                            / len(expected_tuples)
                            if expected_experience
                            else 0.0
                        )
                    else:
                        metrics["experiencePeriods_accuracy"] = 0.0
                print(f"      Metrics: {metrics}")
                runs.append(
                    {
                        "predicted": predicted,
                        "metrics": metrics,
                    }
                )
            # calculate per_resume average metrics
            avg_metrics = {}
            for run in runs:
                for key, value in run["metrics"].items():
                    if key not in avg_metrics:
                        avg_metrics[key] = []
                    avg_metrics[key].append(value)
            for key in avg_metrics:
                avg_metrics[key] = sum(avg_metrics[key]) / len(avg_metrics[key])
            print(f"    Average Metrics: {avg_metrics}")
            model_output = {
                "resume": pdf_file,
                "model": model,
                "runs": runs,
                "average_metrics": avg_metrics,
            }

            # make dir of model if not exists
            os.makedirs(
                os.path.join("evaluation", output_dir, dir_label), exist_ok=True
            )
            # save output to json file
            with open(
                os.path.join(
                    "evaluation",
                    output_dir,
                    dir_label,
                    pdf_file.replace(".pdf", ".json"),
                ),
                "w",
            ) as f:
                json.dump(model_output, f, indent=2)
