import time
from ollama import Client
import json
import extract_pdf

text = extract_pdf.extract_pdf_text("resumes/in.pdf")
expected_output = "resumes/in_expected.json"

client = Client()

edu_timezone_prompt = """
role: system
content: |
  You are a strict JSON extractor.

  Task:
    Extract highest education degree, education field, and timezone 
    from resume text that was extracted from a PDF (may have formatting issues).

  Rules:
    - highestEducationDegree → one of: "High School", "Bachelor", "Master", "PhD", or "Unknown".
    - educationField → main study field of the highest degree, or "Unknown".
    - timezone → format "GMT+X" or "GMT-X", or "Unknown".
      * Derive from address, phone number, or other location hints if present.
    - Ignore formatting issues.
    - Do NOT include explanations, notes, or extra text.
    - Output must be strictly valid JSON.

  Output:
    Strictly return valid JSON in this format:
        {{
        "highestEducationDegree": "Unknown",
        "educationField": "Unknown",
        "timezone": "Unknown"
        }}

  Input:
    text: |
      {text}

"""

skill_prompt = """
role: system
content: |
  You are a strict JSON extractor.

  Task:
    Extract skills from resume text that was extracted from a PDF (may have formatting issues).

  Rules:
    - If a clear "Skills" section is found (look for headers like "Skills", "Technical Skills", "Key Skills", "Core Competencies"), extract only the items listed under that section.
    - If no "Skills" section is found OR the layout is broken, then extract all explicitly mentioned skills anywhere in the text.
    - Do NOT infer skills from job titles or responsibilities. Only include items explicitly listed.
    - For lines like "Category: item1, item2, item3", include each item separately.
    - Keep both umbrella terms and sub-items if present.
      Example: "Troubleshooting: Software, Hardware" → ["Software","Hardware"]
    - Deduplicate case-insensitively, keeping first appearance's capitalization.
    - Preserve original wording and qualifiers (e.g., "Photoshop (Basic Layout)").
    - Maintain order of appearance.
    - Output strictly valid JSON, with this schema:
      {{
        "skills": ["skill1","skill2",...]
      }}
    - If no skills are found, return:
      {{
        "skills": []
      }}

  Input:
    text: |
      {text}
"""

experience_prompt = """
role: system
content: |
  You are a strict JSON extractor.

  Task:
    Extract work experience periods (jobs, internships, professional history) 
    from resume text that was extracted from a PDF (may have formatting issues).

  Rules:
    - Each entry must follow this schema:
      {{
        "startYear": "YYYY",
        "endYear": "YYYY"
      }}
    - Use "Present" if the position is ongoing.
    - Use only numeric years (YYYY).
    - Do NOT include education, certifications, or training years.
    - If only one year is mentioned, use it for both startYear and endYear.
    - Do not include explanations, notes, or extra text.

  Output:
    Strictly return valid JSON in this format:
      {{
        "experiencePeriods": [
          {{ "startYear": "YYYY", "endYear": "YYYY" }}
        ]
      }}

  Input:
    text: |
      {text}

"""


edu_timezone_prompt = edu_timezone_prompt.format(text=text)
skill_prompt = skill_prompt.format(text=text)
experience_prompt = experience_prompt.format(text=text)


# models = ["qwen3:8b", "deepseek-r1:8b", "llama3.1:8b", "gemma3:4b"]
# models = ["qwen3:8b", "deepseek-r1:8b"]

# open expected output json file
with open(expected_output, "r") as f:
    expected_output = json.load(f)


def clean_response(response: str) -> str:
    response = response.split("</think>")[-1].strip()
    # if response has ```json ... ```
    if response.startswith("```json"):
        response = response[len("```json") :].strip()
    if response.endswith("```"):
        response = response[: -len("```")].strip()
    return response


for i in range(3):

    edu_timezone_response = client.chat(
        model="qwen3:8b",
        messages=[
            {
                "role": "user",
                "content": edu_timezone_prompt,
            },
        ],
        think=False,
    )

    skill_response = client.chat(
        model="qwen3:8b",
        messages=[
            {
                "role": "user",
                "content": skill_prompt,
            },
        ],
        stream=True,
        think=False,
    )

    experience_response = client.chat(
        model="qwen3:8b",
        messages=[
            {
                "role": "user",
                "content": experience_prompt,
            },
        ],
        stream=True,
        think=False,
    )

    # Collect streamed responses
    skill_content = ""
    time_took = 0
    # start timer
    start_time = time.perf_counter()
    for chunk in skill_response:
        print(chunk["message"]["content"], end="", flush=True)
        skill_content += chunk["message"]["content"]
    print()
    time_took = time.perf_counter() - start_time
    print(f"Skill extraction took {time_took:.2f} seconds")

    time_took = 0
    # start timer
    start_time = time.perf_counter()
    experience_content = ""
    for chunk in experience_response:
        print(chunk["message"]["content"], end="", flush=True)
        experience_content += chunk["message"]["content"]
    print()
    time_took = time.perf_counter() - start_time
    print(f"Experience extraction took {time_took:.2f} seconds")

    edu_timezone_response = edu_timezone_response["message"]["content"].strip()
    skill_response = skill_content.strip()
    experience_response = experience_content.strip()

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
    with open(f"mixed_accuracy_{i}.json", "w") as f:
        json.dump(accuracy, f, indent=2)
