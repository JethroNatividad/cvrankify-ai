from extract2 import extract_text_word_level_columns

resume_path = "resumes/angelo.pdf"

with open(resume_path, "rb") as resume_pdf:
    pdf_text = extract_text_word_level_columns(resume_pdf)
    print(pdf_text)
