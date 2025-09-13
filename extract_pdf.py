import pdfplumber
from ollama import Client

pdf_path = "in.pdf"
pdf_txt_output = "out.txt"

out = open(pdf_txt_output, "wb")

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            out.write(text.encode("utf8"))
            out.write(b"\n\n")
    out.close()


client = Client()

prompt = """
The following text is unstructured (from a PDF). Ignore formatting issues and focus only on finding the required fields.

Extract and return the result strictly as valid JSON. Do not include explanations, notes, or extra text. 

Fields to extract:
- skills → list of skills mentioned (technical or soft).
- highestEducationDegree → one of: "High School", "Bachelor", "Master", "PhD", or "Unknown".
- educationField → main study field of the highest degree, or "Unknown".
- timezone → format "GMT+X" or "GMT-X", or "Unknown".
- yearsOfExperience → integer years of professional experience (from text or date ranges). If unclear, return "Unknown".

Return output only in this JSON format:
{{
  "skills": [],
  "highestEducationDegree": "Unknown",
  "educationField": "Unknown",
  "timezone": "Unknown",
  "yearsOfExperience": "Unknown"
}}

Text:
{text}

"""

with open(pdf_txt_output, "r") as f:
    text = f.read()
    prompt = prompt.format(text=text)


response = client.chat(
    model="llama3.1:8b",
    messages=[
        {
            "role": "user",
            "content": prompt,
        },
    ],
)

print(response["message"]["content"])
