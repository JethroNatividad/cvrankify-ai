from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()

API_KEY = os.getenv("AI_SERVICE_API_KEY")
headers = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY,
}


def set_status(applicant_id: int, status: str):
    if status not in ["pending", "parsing", "processing", "completed", "failed"]:
        raise ValueError("Invalid status")
    API_URL = "http://localhost:3000/api/trpc/applicant.updateStatusAI"
    data = {
        "json": {
            "applicantId": applicant_id,
            "statusAI": status,
        }
    }
    response = requests.post(API_URL, headers=headers, data=json.dumps(data))
    return response.status_code, response.json()
