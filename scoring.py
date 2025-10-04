from ollama import Client
import json

client = Client()


def score_education_match(
    applicant_highest_degree: str,
    applicant_education_field: str,
    job_required_degree: str,
    job_education_field: str,
):
    model = "edu-match"

    degree_score = 0
    field_score = 0

    degree_values = {
        "None": 0,
        "High School": 1,
        "Bachelor": 2,
        "Master": 3,
        "PhD": 4,
    }

    applicant_highest_degree_value = degree_values.get(applicant_highest_degree, 0)
    job_required_degree_value = degree_values.get(job_required_degree, 0)

    if applicant_highest_degree_value > job_required_degree_value:
        bonus = (applicant_highest_degree_value - job_required_degree_value) * 10
        degree_score = 100 + bonus
    else:
        degree_score = (
            applicant_highest_degree_value / job_required_degree_value
        ) * 100

    response = client.chat(
        model=model,
        messages=[
            {
                "role": "user",
                "content": f"{job_education_field}, {applicant_education_field}",
            },
        ],
        think=False,
    )

    field_score_response = response["message"]["content"].strip()

    try:
        field_score = float(field_score_response)
    except ValueError:
        print(f"Error converting field score to float: {field_score_response}")
        field_score = 0

    overall_score = (degree_score * 0.6) + (field_score * 0.4)
    overall_score = min(overall_score, 100)

    print(f"Degree Score: {degree_score}, Field Score: {field_score}")

    return overall_score


# score = score_education_match("Bachelor", "Education", "Bachelor", "Computer Science")
# print(f"Education Match Score: {score}")


def score_skills_match(job_skills: list[str], applicant_skills: list[str]):
    model = "skills_score"
    score = 0

    data = {
        "job_skills": job_skills,
        "cv_skills": applicant_skills,
    }
    print(f"{data}")

    response = client.chat(
        model=model,
        messages=[
            {
                "role": "user",
                "content": f"{data}",
            },
        ],
        think=False,
    )

    skills_match_response = response["message"]["content"].strip()

    try:
        skills_match_json = json.loads(skills_match_response)
        total_score = 0
        for skill_entry in skills_match_json["job_skills"]:
            total_score += skill_entry.get("score", 0)
        score = total_score / len(job_skills) if job_skills else 0
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        score = 0

    return (score * 100, skills_match_json)


(score, skills_match_json) = score_skills_match(
    job_skills=["html", "css", "javascript", "typescript", "react", "webpack"],
    applicant_skills=[
        "javascript",
        "typescript",
        "angular",
        "react",
        "redux",
        "webpack",
        "sass",
        "jest",
        "cypress",
    ],
)

print(f"Skills Match Score: {score}")
print(f"Skills Match Details: {skills_match_json}")
