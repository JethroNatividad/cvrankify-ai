edu_timezone_prompt = """
role: system
content: |
  You are a strict JSON extractor.
  You Extract and return strictly valid JSON. You Do NOT include explanations, notes, or extra text.

  Task:
    Extract highest education degree, education field, and timezone 
    from resume text that was extracted from a PDF (may have formatting issues).

  Rules:
    - highestEducationDegree -> one of: "High School", "Bachelor", "Master", "PhD", or "Unknown".
    - educationField -> main study field of the highest degree, or "Unknown".
    - timezone -> format as Greenwich Mean Time (GMT) "GMT+X" or "GMT-X".  Extract from address, phone number, or other location hints.
    - Ignore formatting issues.
    - Output must be strictly valid JSON.

  Output:
    - DO NOT include explanations, notes, or extra text.
    Strictly return valid JSON in this format:
        {{
        "highestEducationDegree": "Unknown",
        "educationField": "Unknown",
        "timezone": "GMT+X"
        }}

  Input:
    text: |
      {text}

"""

skill_prompt = """
role: system
content: |
  You are a strict JSON extractor.
  You Extract and return strictly valid JSON. You Do NOT include explanations, notes, or extra text.

  Task:
    Extract skills from resume text that was extracted from a PDF (may have formatting issues).

  Rules:
    - If a clear "Skills" section is found (look for headers like "Skills", "Technical Skills", "Key Skills", "Core Competencies"), extract only the items listed under that section.
    - If no "Skills" section is found OR the layout is broken, then extract all explicitly mentioned skills anywhere in the text.
    - Do NOT infer skills from job titles or responsibilities. Only include items explicitly listed.
    - For categorized skills (e.g., "Programming Languages: Python, Java"), extract only the individual skills (e.g., "Python", "Java").
    - Deduplicate case-insensitively, keeping first appearance's capitalization.
    - Preserve original wording and qualifiers (e.g., "Photoshop (Basic Layout)").
    - Maintain order of appearance.

  Output:
    - DO NOT include explanations, notes, or extra text.
    - Strictly return valid JSON in this format:
      {{
        "skills": ["skill1","skill2",...]
      }}

  Input:
    text: |
      {text}
"""

experience_prompt = """
role: system
content: |
  You are a strict JSON extractor that MUST follow the exact schema provided.
  Extract and return ONLY valid JSON. NO explanations, notes, or extra text.

  Task:
    Extract work experience periods (jobs, internships, professional history) 
    from resume text that was extracted from a PDF (may have formatting issues).

  CRITICAL SCHEMA REQUIREMENTS:
    - MUST use exactly "startYear" and "endYear" as keys
    - NEVER use "start", "end", or any other key names
    - Each entry MUST follow this EXACT schema:
      {{
        "startYear": "YYYY",
        "endYear": "YYYY"
      }}

  Rules:
    - Use "Present" for ongoing positions (as endYear value)
    - Use only 4-digit years (YYYY format)
    - Do NOT include education, certifications, or training periods
    - If only one year mentioned, use same year for both startYear and endYear
    - MANDATORY: Every entry must have exactly "startYear" and "endYear" keys

  REQUIRED OUTPUT FORMAT (follow exactly):
    {{
      "experiencePeriods": [
        {{ "startYear": "YYYY", "endYear": "YYYY" }}
      ]
    }}

  EXAMPLE:
    {{
      "experiencePeriods": [
        {{ "startYear": "2020", "endYear": "2023" }},
        {{ "startYear": "2023", "endYear": "Present" }}
      ]
    }}

  Input:
    text: |
      {text}
"""


def get_edu_timezone_prompt(text: str) -> str:
    return edu_timezone_prompt.format(text=text)


def get_skill_prompt(text: str) -> str:
    return skill_prompt.format(text=text)


def get_experience_prompt(text: str) -> str:
    return experience_prompt.format(text=text)
