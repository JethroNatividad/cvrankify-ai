from dotenv import load_dotenv
import os
import requests
import json
import datetime

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


def update_parsed_data(applicant_id: int, parsed_data: dict):
    # {'highestEducationDegree': 'Bachelor', 'educationField': 'Computer Science', 'timezone': 'GMT+8', 'skills': ['C++ Programming Language', 'Visual Basic 6.0', 'PHP Scripting Language', 'HTML/CSS', 'Mysql Database', 'Joomla', 'Adobe Photoshop (any version)', 'Adobe Illustrator', 'Adobe Dreamweaver', 'Adobe Flash', 'Adobe After Effects'], 'experiencePeriods': [{'startYear': '2011', 'endYear': 'Present'}]}
    data = {}
    data["parsedHighestEducationDegree"] = parsed_data.get("highestEducationDegree")
    data["parsedEducationField"] = parsed_data.get("educationField")
    data["parsedTimezone"] = parsed_data.get("timezone")
    if "skills" in parsed_data:
        data["parsedSkills"] = ", ".join(parsed_data["skills"])
    else:
        data["parsedSkills"] = ""

    # For experience periods, calculate total years of experience, present is current year
    # experience periods is a list of dicts with startYear and endYear, it is not guaranteed to be sorted
    # if "experiencePeriods" in parsed_data:
    #     current_year = datetime.datetime.now().year

    #     # Normalize periods (replace "Present" with current year)
    #     normalized = []
    #     for period in parsed_data["experiencePeriods"]:
    #         start_year = int(period["startYear"])
    #         end_year = (
    #             current_year
    #             if period["endYear"].lower() == "present"
    #             else int(period["endYear"])
    #         )
    #         normalized.append((start_year, end_year))

    #     # Sort by start year
    #     normalized.sort(key=lambda x: x[0])

    #     # Merge overlapping intervals
    #     merged = []
    #     for start, end in normalized:
    #         if not merged or merged[-1][1] < start - 1:
    #             merged.append([start, end])
    #         else:
    #             merged[-1][1] = max(merged[-1][1], end)

    #     # Calculate total years of experience
    #     total_years = sum((end - start + 1) for start, end in merged)
    #     data["parsedYearsOfExperience"] = total_years - 1
    # else:
    #     data["parsedYearsOfExperience"] = 0
    data["parsedYearsOfExperience"] = 0

    API_URL = "http://localhost:3000/api/trpc/applicant.updateParsedDataAI"
    data = {
        "json": {
            "applicantId": applicant_id,
            "parsedHighestEducationDegree": data["parsedHighestEducationDegree"],
            "parsedEducationField": data["parsedEducationField"],
            "parsedTimezone": data["parsedTimezone"],
            "parsedSkills": data["parsedSkills"],
            "parsedYearsOfExperience": data["parsedYearsOfExperience"],
            "parsedExperiences": (
                parsed_data["experiencePeriods"]
                if "experiencePeriods" in parsed_data
                else []
            ),
        }
    }
    print(data)
    response = requests.post(API_URL, headers=headers, data=json.dumps(data))
    return response.status_code, response.json()


def re_queue_resume(applicant_id: int):
    API_URL = "http://localhost:3000/api/trpc/applicant.reQueueResumeProcessing"
    data = {
        "json": {
            "applicantId": applicant_id,
        }
    }
    response = requests.post(API_URL, headers=headers, data=json.dumps(data))
    return response.status_code, response.json()


def queue_score_resume(applicant_id: int):
    API_URL = "http://localhost:3000/api/trpc/applicant.queueScoring"
    data = {
        "json": {
            "applicantId": applicant_id,
        }
    }
    response = requests.post(API_URL, headers=headers, data=json.dumps(data))
    return response.status_code, response.json()


def update_matched_skills(applicant_id: int, matched_skills: list[dict]):
    """
    Update matched skills for an applicant.

    Args:
        applicant_id: The ID of the applicant
        matched_skills: List of matched skills, each containing:
            - jobSkill: str (max 100 chars)
            - matchType: str ("explicit", "implied", or "missing")
            - applicantSkill: str (max 100 chars)
            - score: float (0-100)
            - reason: str (optional)

    Example:
        matched_skills = [
            {
                "jobSkill": "Python",
                "matchType": "explicit",
                "applicantSkill": "Python Programming",
                "score": 95.0,
                "reason": "Direct match found in resume"
            }
        ]
    """
    API_URL = "http://localhost:3000/api/trpc/applicant.updateApplicantMatchedSkillsAI"
    data = {
        "json": {
            "applicantId": applicant_id,
            "matchedSkills": matched_skills,
        }
    }
    print("DATA TO SEND:", data)
    response = requests.post(API_URL, headers=headers, data=json.dumps(data))
    return response.status_code, response.json()


def update_applicant_experience_relevance(applicant_id: int, experiences: list[dict]):
    """
    Update experience relevance for an applicant.

    Args:
        applicant_id: The ID of the applicant
        experiences: List of experiences, each containing:
            - id: int (experience ID)
            - relevant: bool

    Example:
        experiences = [
            {
                "id": 123,
                "relevant": True
            },
            {
                "id": 124,
                "relevant": False
            }
        ]
    """
    API_URL = (
        "http://localhost:3000/api/trpc/applicant.updateApplicantExperienceRelevanceAI"
    )
    data = {
        "json": {
            "applicantId": applicant_id,
            "experiences": experiences,
        }
    }
    print("DATA TO SEND:", data)
    response = requests.post(API_URL, headers=headers, data=json.dumps(data))
    return response.status_code, response.json()


def update_applicant_scores(
    applicant_id: int,
    skills_score: float,
    experience_score: float,
    education_score: float,
    timezone_score: float,
    overall_score: float,
    parsedYearsOfExperience: float = 0.0,
):
    """
    Update AI scores for an applicant.

    Args:
        applicant_id: The ID of the applicant
        skills_score: Skills score (0-100)
        experience_score: Experience score (0-100)
        education_score: Education score (0-100)
        timezone_score: Timezone score (0-100)
        overall_score: Overall score (0-100)

    Example:
        update_applicant_scores(
            applicant_id=123,
            skills_score=85.5,
            experience_score=90.0,
            education_score=75.0,
            timezone_score=100.0,
            overall_score=87.6
        )
    """
    API_URL = "http://localhost:3000/api/trpc/applicant.updateApplicantScoresAI"
    data = {
        "json": {
            "applicantId": applicant_id,
            "skillsScoreAI": skills_score,
            "experienceScoreAI": experience_score,
            "educationScoreAI": education_score,
            "timezoneScoreAI": timezone_score,
            "overallScoreAI": overall_score,
            "parsedYearsOfExperience": parsedYearsOfExperience,
        }
    }
    print("DATA TO SEND:", data)
    response = requests.post(API_URL, headers=headers, data=json.dumps(data))
    return response.status_code, response.json()


def queue_all_applicants(job_id: int):
    API_URL = "http://localhost:3000/api/trpc/job.queueScoringAll"
    data = {
        "json": {
            "jobId": job_id,
        }
    }
    response = requests.post(API_URL, headers=headers, data=json.dumps(data))
    return response.status_code, response.json()
