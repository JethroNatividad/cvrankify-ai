from pdfminer.high_level import extract_text
from ollama import Client

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
- skills → list of skills mentioned (technical or soft).
- highestEducationDegree → one of: "High School", "Bachelor", "Master", "PhD", or "Unknown".
- educationField → main study field of the highest degree, or "Unknown".
- timezone → format "GMT+X" or "GMT-X", or "Unknown".
- experiencePeriods → list of objects, each with "startYear" and "endYear". 
  - Include only years that appear in WORK EXPERIENCE, JOBS, INTERNSHIPS, or PROFESSIONAL HISTORY.
  - Do not include years from education, certifications, or training.
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


response = client.chat(
    model="qwen3:8b",
    messages=[
        {
            "role": "user",
            "content": prompt,
        },
    ],
)

print(response["message"]["content"])
