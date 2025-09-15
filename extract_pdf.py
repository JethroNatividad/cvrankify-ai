from pdfminer.high_level import extract_text


def extract_pdf_text(pdf_path: str) -> str:
    text = extract_text(pdf_path)
    # clean up text a bit
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    return text
