from extract2 import normal_extract_text, extract_text_word_level_columns

resume_path = "Applicant_4_Resume.pdf"

with open(resume_path, "rb") as resume_pdf:
    pdf_text = extract_text_word_level_columns(resume_pdf)
    print(pdf_text)


# from unstructured.partition.pdf import partition_pdf

# elements = partition_pdf(
#     resume_path,
#     strategy="hi_res",
#     infer_table_structure=True,
#     languages=["en"],  # or "fast" for speed
# )
# text = "\n".join([el.text for el in elements if el.text])

# print(text)
