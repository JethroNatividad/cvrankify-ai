from pdfminer.high_level import extract_text
from ollama import Client
import json

pdf_path = "resumes/in.pdf"
pdf_txt_output = "resumes/out.txt"

text = extract_text(pdf_path)
# clean up text a bit
text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

with open(pdf_txt_output, "w") as f:
    f.write(text)

client = Client()

prompt = """
The following text is unstructured (from a PDF). Ignore formatting issues.

Extract and return strictly valid JSON. Do not include explanations, notes, or extra text.

Fields to extract:
- skills -> list of skills mentioned (technical or soft).
- highestEducationDegree -> one of: "High School", "Bachelor", "Master", "PhD", or "Unknown".
- educationField -> main study field of the highest degree, or "Unknown".
- timezone -> format "GMT+X" or "GMT-X", or "Unknown". Extract from address, phone number, or other location hints.
- experiencePeriods -> list of objects, each with "startYear" and "endYear".
  - Include only years that appear in WORK EXPERIENCE, JOBS, INTERNSHIPS, or PROFESSIONAL HISTORY.
  - Do not include years from education, certifications, or training.
  - Use the same year for startYear and endYear if only one year is mentioned.
  - Use "Present" if ongoing.
  - Use only numeric years (YYYY).

Return output only in this JSON format:
{{
  "skills": ["skill1", "skill2"],
  "highestEducationDegree": "Unknown",
  "educationField": "Unknown",
  "timezone": "Unknown",
  "experiencePeriods": [
    {{ "startYear": "YYYY", "endYear": "YYYY" }},
  ]
}}

Text:
{text}

"""

prompt = prompt.format(text=text)

models = ["gemma3:4b", "deepseek-r1:8b", "qwen3:8b"]
# models = ["qwen3:8b", "deepseek-r1:8b", "llama3.1:8b", "gemma3:4b"]

expected_output = {
    "skills": [
        "SQL",
        "MySQL",
        "VB.Net",
        "C#",
        "C++",
        "Java",
        "Processing",
        "HTML",
        "Bootstrap",
        "Minutes of Meetings",
        "Reports",
        "Personnel Orders",
        "Process mapping & documentation",
        "Canva",
        "Photoshop (Basic Layout)",
        "Word",
        "Excel",
        "PowerPoint",
        "Outlook",
        "SharePoint",
        "Teams",
        "Power Automate",
        "Docs",
        "Sheets",
        "Forms",
        "Drive",
        "Calendar",
        "Software",
        "Hardware",
        "Networking Issues",
    ],
    "highestEducationDegree": "Bachelor",
    "educationField": "Computer Science",
    "timezone": "GMT+8",
    "experiencePeriods": [
        {"startYear": "2024", "endYear": "Present"},
        {"startYear": "2023", "endYear": "2023"},
        {"startYear": "2022", "endYear": "2022"},
        {"startYear": "2021", "endYear": "2021"},
        {"startYear": "2020", "endYear": "2020"},
        {"startYear": "2019", "endYear": "2021"},
    ],
}
# Deepseek 8B model

for model in models:
    for i in range(3):
        response = client.chat(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        print(response["message"]["content"])

        response = response["message"]["content"].strip()

        # Save response to a file {model}_out.json in ./
        with open(f"{model}_out_{i}.json", "w") as f:
            f.write(response)

        # load response as json then check accuracy with expected_output, for all keys in expected_output

        try:
            # if response has </think>
            response = response.split("</think>")[-1].strip()
            # if response has ```json ... ```
            if response.startswith("```json"):
                response = response[len("```json") :].strip()
            if response.endswith("```"):
                response = response[: -len("```")].strip()

            response_json = json.loads(response)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            continue
        accuracy = {}
        for key in expected_output:
            if key in response_json:
                if response_json[key] == expected_output[key]:
                    accuracy[key] = 1.0
                else:
                    # if list, check how many items are correct
                    if isinstance(expected_output[key], list) and isinstance(
                        response_json[key], list
                    ):
                        # Handle lists of dictionaries (like experiencePeriods)
                        if expected_output[key] and isinstance(
                            expected_output[key][0], dict
                        ):
                            # Convert dicts to frozensets for comparison
                            expected_items = [
                                frozenset(item.items()) for item in expected_output[key]
                            ]
                            response_items = [
                                frozenset(item.items()) for item in response_json[key]
                            ]
                            correct_items = set(expected_items) & set(response_items)
                        else:
                            # Handle regular lists (like skills)
                            correct_items = set(expected_output[key]) & set(
                                response_json[key]
                            )
                        accuracy[key] = len(correct_items) / len(expected_output[key])
                    else:
                        accuracy[key] = 0.0
            else:
                accuracy[key] = 0.0
        print(f"Accuracy: {accuracy}")

        # Save accuracy to a file {model}_accuracy.json in ./
        with open(f"method1/{model}_accuracy_{i}.json", "w") as f:
            json.dump(accuracy, f, indent=2)
