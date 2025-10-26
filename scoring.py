from ollama import Client
import json
from datetime import datetime

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

    print(f"Degree Score: {degree_score}, Field Score: {field_score}")

    return overall_score


# score = score_education_match("Bachelor", "Mathematics", "Bachelor", "Computer Science")
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
                "content": json.dumps(data, ensure_ascii=False),
            },
        ],
        think=False,
    )

    skills_match_response = response["message"]["content"].strip()

    print(f"Skills Match Response: {skills_match_response}")
    try:
        skills_match_json = json.loads(skills_match_response)
        total_score = 0
        for skill_entry in skills_match_json["job_skills"]:
            total_score += skill_entry.get("score", 0)
        score = total_score / len(job_skills) if job_skills else 0
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        score = 0

    # Replace match_type with matchType, skill with jobSkill, from_cv with applicantSkill
    skills_match_json = {
        "job_skills": [
            {
                "jobSkill": entry["skill"],
                "matchType": entry["match_type"],
                "applicantSkill": (
                    entry["from_cv"] if entry["from_cv"] is not None else ""
                ),
                "score": entry["score"],
                "reason": entry.get("reason", ""),
            }
            for entry in skills_match_json["job_skills"]
        ]
    }

    return (score * 100, skills_match_json)


# (score, skills_match_json) = score_skills_match(
#     job_skills=["html", "css", "javascript", "typescript", "react", "webpack"],
#     applicant_skills=[
#         "javascript",
#         "typescript",
#         "angular",
#         "react",
#         "redux",
#         "webpack",
#         "sass",
#         "jest",
#         "cypress",
#     ],
# )

# print(f"Skills Match Score: {score}")
# print(f"Skills Match Details: {skills_match_json}")


# "experiencePeriods": [
#     { "startYear": "2024", "startMonth": "None", "endYear": "Present", "endMonth": "None", "jobTitle": "Computer Programmer, City Medical Center" },
#     { "startYear": "2023", "startMonth": "March", "endYear": "2023", "endMonth": "July", "jobTitle": "Tour Siri Star Coordinator, Travel and Tours" },
#     { "startYear": "2022", "startMonth": "June", "endYear": "2022", "endMonth": "December", "jobTitle": "Admin Aide III (Programmer), Medical Center" },
#     { "startYear": "2021", "startMonth": "December", "endYear": "2021", "endMonth": "December", "jobTitle": "Unicef Data Manager, Vaccination Team under DOH & CHO" },
#     { "startYear": "2020", "startMonth": "None", "endYear": "2020", "endMonth": "None", "jobTitle": "Gemzon Facebook Teleconsultation Admin & Technical Clinic Support (Part-time)" },
#     { "startYear": "2019", "startMonth": "May", "endYear": "2021", "endMonth": "October", "jobTitle": "Programmer, West Metro Medical Center" }
#   ]


def score_experience_years(
    experience_periods: list[dict], job_relevant_experience_years: int, job_title: str
):
    model = "exp_relevance_eval"
    score = 0
    relevant_experience = []

    # First get the relevant experience periods based on job title

    data = {
        "experiencePeriods": experience_periods,
        "jobTitle": job_title,
    }

    print(f"{json.dumps(data, indent=2)}")

    response = client.chat(
        model=model,
        messages=[
            {
                "role": "user",
                "content": json.dumps(data, indent=2),
            },
        ],
        think=False,
    )

    relevant_experience_response = response["message"]["content"].strip()
    print(f"Relevant Experience Response: {relevant_experience_response}")
    # parse json
    try:
        relevant_experience_json = json.loads(relevant_experience_response)
        relevant_experience = relevant_experience_json.get("experiencePeriods", [])
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        relevant_experience = []

    month_map = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12,
        "None": 1,
        None: 1,
    }

    current_year = datetime.now().year
    current_month = datetime.now().month
    # Step 1: Filter only relevant experiences and normalize dates
    # [{'id': 2, 'createdAt': '2025-10-10T13:44:04.582Z', 'updatedAt': '2025-10-10T13:47:20.892Z', 'jobTitle': 'Graphic Artist', 'startYear': '2011', 'endYear': 'Present', 'startMonth': 'April', 'endMonth': 'None', 'relevant': True, 'applicantId': 20}]
    ranges = []
    for exp in relevant_experience:
        if not exp.get("relevant", False):
            continue

        start_year = int(exp["startYear"])
        start_month = month_map.get(exp["startMonth"], 1)

        if exp["endYear"] == "Present":
            end_year = current_year
            end_month = current_month
        else:
            end_year = int(exp["endYear"])
            end_month = month_map.get(exp["endMonth"], 1)

        start_index = start_year * 12 + start_month
        end_index = end_year * 12 + end_month

        ranges.append((start_index, end_index))
    print("RANGESSSSSS", ranges)
    if not ranges:
        return (relevant_experience, 0.0, 0.0)

    ranges.sort()
    merged = [ranges[0]]

    for start, end in ranges[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:  # overlap or continuous
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    # Step 3: Compute total months
    print("MERGEDDDD", merged)
    print("MERGE SUM", sum(end - start for start, end in merged))
    total_months = sum(end - start for start, end in merged)
    total_years = total_months // 12
    remaining_months = total_months % 12

    total_years_with_months = total_years + (remaining_months / 12)

    # Score calculation based on required years, if more than required, give bonus
    if total_years_with_months >= job_relevant_experience_years:
        bonus = (total_years_with_months - job_relevant_experience_years) * 10
        score = 100 + bonus
    else:
        score = (total_years_with_months / job_relevant_experience_years) * 100

    return (relevant_experience, score, total_years_with_months)
    #


# score, total_years = score_experience_years(
#     experience_periods=[
#         {
#             "startYear": "2024",
#             "startMonth": "None",
#             "endYear": "Present",
#             "endMonth": "None",
#             "jobTitle": "Computer Programmer, City Medical Center",
#         },
#         {
#             "startYear": "2023",
#             "startMonth": "March",
#             "endYear": "2023",
#             "endMonth": "July",
#             "jobTitle": "Tour Siri Star Coordinator, Travel and Tours",
#         },
#         {
#             "startYear": "2022",
#             "startMonth": "June",
#             "endYear": "2022",
#             "endMonth": "December",
#             "jobTitle": "Admin Aide III (Programmer), Medical Center",
#         },
#         {
#             "startYear": "2021",
#             "startMonth": "December",
#             "endYear": "2021",
#             "endMonth": "December",
#             "jobTitle": "Unicef Data Manager, Vaccination Team under DOH & CHO",
#         },
#         {
#             "startYear": "2020",
#             "startMonth": "None",
#             "endYear": "2020",
#             "endMonth": "None",
#             "jobTitle": "Gemzon Facebook Teleconsultation Admin & Technical Clinic Support (Part-time)",
#         },
#         {
#             "startYear": "2019",
#             "startMonth": "May",
#             "endYear": "2021",
#             "endMonth": "October",
#             "jobTitle": "Programmer, West Metro Medical Center",
#         },
#     ],
#     job_title="web developer",
#     job_relevant_experience_years=2,
# )

# print(f"Experience Relevance Score: {score}, Total Years: {total_years}")


def tz_score(a_hours: float, b_hours: float) -> float:
    # convert to 0..24 circle
    a = (a_hours + 24) % 24
    b = (b_hours + 24) % 24
    d = abs(a - b)
    diff = min(d, 24 - d)  # minimal circular distance, in hours
    score = (1 - diff / 12) * 100  # 100 = same zone, 0 = 12h apart
    return max(0.0, min(100.0, score)), diff


# print(tz_score(-12, +14))
