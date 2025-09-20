from pdfminer.high_level import extract_text


def clean_response(response: str) -> str:
    response = response.split("</think>")[-1]
    # if response has ```json ... ```
    if response.startswith("```json"):
        response = response[len("```json") :]

    if response.startswith("```"):
        response = response[len("```") :]

    if response.endswith("```"):
        response = response[: -len("```")]
    return response.strip()


def extract_pdf_text(pdf_path: str) -> str:
    text = extract_text(pdf_path)
    # clean up text a bit
    return text
