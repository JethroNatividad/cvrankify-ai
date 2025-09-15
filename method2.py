from ollama import Client
import json
import extract_pdf

text = extract_pdf.extract_pdf_text("resumes/in.pdf")

client = Client()

edu_timezone_prompt = """
The following text is unstructured (from a PDF). Ignore formatting issues.
Do not include explanations, notes, or extra text.
Extract and return strictly valid JSON with the following fields:
- highestEducationDegree -> one of: "High School", "Bachelor", "Master", "PhD", or "Unknown".
- educationField -> main study field of the highest degree, or "Unknown".
- timezone -> format "GMT+X" or "GMT-X", or "Unknown". Extract from address, phone number, or other location hints.

Return JSON only:
{{
  "highestEducationDegree": "Unknown",
  "educationField": "Unknown",
  "timezone": "Unknown",
}}

Text:
{text}
"""

skill_prompt = """
The following text is unstructured (from a PDF). Ignore formatting issues.
Do not include explanations, notes, or extra text.
Extract all technical and soft skills mentioned. Return as a JSON list of unique strings only.

Return JSON only:
{{
  "skills": ["skill1", "skill2"]
}}

Text:
{text}
"""

experience_prompt = """
The following text is unstructured (from a PDF). Ignore formatting issues.
Do not include explanations, notes, or extra text.
Extract work experience periods (jobs, internships, professional history). 
Rules:
- Each entry: {{"startYear": "YYYY", "endYear": "YYYY"}}
- Use "Present" if ongoing.
- Use only numeric years (YYYY).
- Do NOT include education, certifications, or training years.
- If only one year is mentioned, use it for both startYear and endYear.

Return JSON only:
{{
  "experiencePeriods": [
    {{ "startYear": "YYYY", "endYear": "YYYY" }},
  ]
}}

Text:
{text}
"""


edu_timezone_prompt = edu_timezone_prompt.format(text=text)
skill_prompt = skill_prompt.format(text=text)
experience_prompt = experience_prompt.format(text=text)


# models = ["qwen3:8b", "deepseek-r1:8b", "llama3.1:8b", "gemma3:4b"]
models = ["qwen3:8b", "deepseek-r1:8b"]

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


def clean_response(response: str) -> str:
    response = response.split("</think>")[-1].strip()
    # if response has ```json ... ```
    if response.startswith("```json"):
        response = response[len("```json") :].strip()
    if response.endswith("```"):
        response = response[: -len("```")].strip()
    return response


for model in models:
    for i in range(3):

        edu_timezone_response = client.chat(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": edu_timezone_prompt,
                },
            ],
        )

        skill_response = client.chat(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": skill_prompt,
                },
            ],
        )

        experience_response = client.chat(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": experience_prompt,
                },
            ],
        )

        edu_timezone_response = edu_timezone_response["message"]["content"].strip()
        skill_response = skill_response["message"]["content"].strip()
        experience_response = experience_response["message"]["content"].strip()

        try:
            edu_timezone_response = clean_response(edu_timezone_response)
            skill_response = clean_response(skill_response)
            experience_response = clean_response(experience_response)
            print(edu_timezone_response)
            print(skill_response)
            print(experience_response)

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
            print(response_json)

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
        with open(f"{model}_accuracy_{i}.json", "w") as f:
            json.dump(accuracy, f, indent=2)
