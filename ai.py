from minio import Minio
from dotenv import load_dotenv
import json
import os
from ollama import Client
from extract2 import extract_text_word_level_columns
from prompts import get_edu_timezone_prompt, get_experience_prompt, get_skill_prompt
from utils import clean_response
from api import set_status, update_parsed_data

load_dotenv()

minio_client = Minio(
    os.getenv("MINIO_ENDPOINT") + ":" + os.getenv("MINIO_PORT"),
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=False,  # Use True for HTTPS, False for HTTP
)
ollama_client = Client()


def extract_resume_data(pdf_text: str) -> dict:
    edu_timezone_response = ollama_client.chat(
        model="edu-timezone-extractor:latest",
        messages=[
            {
                "role": "user",
                "content": pdf_text,
            },
        ],
        think=False,
    )

    skill_response = ollama_client.chat(
        model="skills-extractor:latest",
        messages=[
            {
                "role": "user",
                "content": pdf_text,
            },
        ],
        think=False,
    )

    experience_response = ollama_client.chat(
        model="experience-extractor:latest",
        messages=[
            {
                "role": "user",
                "content": pdf_text,
            },
        ],
        think=False,
    )

    edu_timezone_response = clean_response(edu_timezone_response["message"]["content"])
    skill_response = clean_response(skill_response["message"]["content"])
    experience_response = clean_response(experience_response["message"]["content"])

    try:
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

        predicted = response_json
        return predicted
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(edu_timezone_response)
        print(skill_response)
        print(experience_response)
        return {}


# resumes/2025/wawasd-1758326293362.pdf

# try:
#     resume_path = "resumes/2025/wawasd-1758326293362.pdf"
#     response = minio_client.get_object(os.getenv("MINIO_BUCKET_NAME"), resume_path)
#     data = response.read()
#     pdf_text = extract_text_word_level_columns(data)
#     res = set_status(11, "parsing")
#     print(res)
#     result = extract_resume_data(pdf_text)
#     res = update_parsed_data(11, result)
#     print(res)
#     res = set_status(11, "processing")
#     print(res)

#     print("Resume Data:")
#     print(result)
# finally:
#     response.close()
#     response.release_conn()
