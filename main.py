from bullmq import Worker
import asyncio
import signal
from minio import Minio
from dotenv import load_dotenv
from ai import extract_resume_data
import os
from api import (
    set_status,
    update_parsed_data,
    update_matched_skills,
    update_applicant_experience_relevance,
)
import json
from scoring import score_education_match, score_skills_match, score_experience_years
from extract2 import extract_text_word_level_columns

# Load environment variables from .env file
load_dotenv()

minio_client = Minio(
    os.getenv("MINIO_ENDPOINT") + ":" + os.getenv("MINIO_PORT"),
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=False,  # Use True for HTTPS, False for HTTP
)


def handle_extraction(job):
    # job.data will include the data added to the queue
    print(f"Processing job {job.id} with data: {job.data}")
    # get applicantId and resumePath from job.data
    applicant_id = job.data.get("applicantId")
    resume_path = job.data.get("resumePath")

    try:
        response = minio_client.get_object(os.getenv("MINIO_BUCKET_NAME"), resume_path)
        data = response.read()
        resume_text = extract_text_word_level_columns(data)
        resume_data = extract_resume_data(resume_text)
        status_code, resp_json = set_status(applicant_id, "parsing")
        print(f"Set status to parsing: {status_code}, {resp_json}")
        status_code, resp_json = update_parsed_data(applicant_id, resume_data)
        print(f"Updated parsed data: {status_code}, {resp_json}")
        status_code, resp_json = set_status(applicant_id, "processing")
        print(f"Set status to processing: {status_code}, {resp_json}")
    except Exception as e:
        print(f"Error processing job {job.id}: {e}")
    finally:
        response.close()
        response.release_conn()


def score_applicant(job):
    print(f"Scoring applicant {job.id}")
    applicant_id = job.data.get("applicantId")
    applicant_data = job.data.get("applicantData")
    job_data = job.data.get("jobData")

    # json parse data
    try:
        applicant_data = json.loads(applicant_data)
        # {'id': 19, 'createdAt': '2025-10-09T16:18:05.826Z', 'updatedAt': '2025-10-09T19:19:54.241Z', 'name': 'BOT', 'email': 'bot@email.com', 'resume': 'resumes/2025/bot-1760026685155.pdf', 'statusAI': 'processing', 'parsedHighestEducationDegree': 'Bachelor', 'parsedEducationField': 'Computer Science', 'parsedTimezone': 'GMT+8', 'parsedSkills': 'C++ Programming Language, Visual Basic 6.0, PHP Scripting Language, HTML/CSS, Mysql Database, Joomla, Adobe Photoshop (any version), Adobe Illustrator, Adobe Dreamweaver, Adobe Flash, Adobe After Effects', 'parsedYearsOfExperience': 14, 'skillsScoreAI': '0', 'experienceScoreAI': '0', 'educationScoreAI': '0', 'timezoneScoreAI': '0', 'overallScoreAI': '0', 'skillsFeedbackAI': None, 'experienceFeedbackAI': None, 'educationFeedbackAI': None, 'timezoneFeedbackAI': None, 'overallFeedbackAI': None, 'currentStage': 0, 'interviewStatus': 'pending', 'interviewNotes': None, 'jobId': 5, 'experiences': [{'id': 1, 'createdAt': '2025-10-09T19:19:54.051Z', 'updatedAt': '2025-10-09T19:19:54.051Z', 'jobTitle': 'Graphic Artist', 'startYear': '2011', 'endYear': 'Present', 'startMonth': 'April', 'endMonth': 'None', 'isRelevant': False, 'applicantId': 19}]}
        job_data = json.loads(job_data)
        # {'id': 5, 'createdAt': '2025-08-20T18:30:19.479Z', 'updatedAt': '2025-08-20T18:30:19.479Z', 'title': 'Data Scientist', 'description': "Join our data team as a Data Scientist to extract insights from large datasets and drive data-informed decision making across the organization. You will develop machine learning models, conduct statistical analysis, create predictive algorithms, and work with stakeholders to translate business questions into analytical solutions.\n\nThe role involves working with various data sources, building dashboards and reports, and presenting findings to both technical and non-technical audiences. We're looking for someone with strong analytical skills and the ability to work with complex datasets to solve challenging business problems.\n\nKey Responsibilities:\n- Develop and deploy machine learning models and algorithms\n- Conduct statistical analysis and data mining\n- Create data visualizations and dashboards\n- Collaborate with business stakeholders to identify opportunities\n- Design and implement A/B tests and experiments\n- Build data pipelines and ETL processes\n- Present findings and recommendations to leadership\n- Stay current with latest developments in data science and ML\n\nThis is an excellent opportunity to work with cutting-edge data science technologies and make a significant impact on business strategy and operations.", 'skills': 'Python, R, SQL, Machine Learning, TensorFlow, Pandas, NumPy, Tableau, Power BI, Statistics, A/B Testing, Data Visualization', 'yearsOfExperience': 3, 'educationDegree': 'Master', 'educationField': 'Data Science', 'timezone': 'GMT+1', 'skillsWeight': '0.5', 'experienceWeight': '0.2', 'educationWeight': '0.2', 'timezoneWeight': '0.1', 'interviewing': 0, 'interviewsNeeded': 2, 'hires': 0, 'hiresNeeded': 1, 'isOpen': True, 'createdById': 'cmekb012x0001ln2w562lrr62'}
        print(applicant_data)
        print(job_data)
        # education_score = score_education_match(
        #     applicant_education_field=applicant_data.get("parsedEducationField"),
        #     applicant_highest_degree=applicant_data.get("parsedHighestEducationDegree"),
        #     job_education_field=job_data.get("educationField"),
        #     job_required_degree=job_data.get("educationDegree"),
        # )
        # print(f"Education Score: {education_score}")

        # job_skills = job_data.get("skills").split(", ")
        # applicant_skills = applicant_data.get("parsedSkills").split(", ")
        # (skills_score, skills_match_json) = score_skills_match(
        #     job_skills=job_skills, applicant_skills=applicant_skills
        # )
        # skills_match = skills_match_json.get("job_skills", [])
        # status_code, resp_json = update_matched_skills(applicant_id, skills_match)
        # print(f"Updated matched skills: {status_code}, {resp_json}")
        # print(f"Skills Score: {skills_score}")

        job_title = job_data.get("title")
        applicant_experience_periods = applicant_data.get("experiences", [])
        job_relevant_experience_years = job_data.get("yearsOfExperience", 0)

        (relevant_experience, experience_score, total_years_with_months) = (
            score_experience_years(
                experience_periods=applicant_experience_periods,
                job_relevant_experience_years=job_relevant_experience_years,
                job_title=job_title,
            )
        )

        print(f"Relevant Experience: {relevant_experience}")
        print(f"Experience Score: {experience_score}")
        print(f"Total Years with Months: {total_years_with_months}")

        status_code, resp_json = update_applicant_experience_relevance(
            applicant_id, relevant_experience
        )
        print(f"Updated experience relevance: {status_code}, {resp_json}")

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON data for job {job.id}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error processing job {job.id}: {e}")
    return None


async def process(job, job_token):

    # return type Future based on Worker
    print(job.name)
    if job.name == "process-resume":
        return handle_extraction(job)
    if job.name == "score-applicant":
        return score_applicant(job)

    return None


async def main():

    # Create an event that will be triggered for shutdown
    shutdown_event = asyncio.Event()

    def signal_handler(signal, frame):
        print("Signal received, shutting down.")
        shutdown_event.set()

    # Assign signal handlers to SIGTERM and SIGINT
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Feel free to remove the connection parameter, if your redis runs on localhost
    worker = Worker(
        "cvrankify-jobs",
        process,
        {"connection": "redis://localhost:6379"},
    )

    # Wait until the shutdown event is set
    await shutdown_event.wait()

    # close the worker
    print("Cleaning up worker...")
    await worker.close()
    print("Worker shut down successfully.")


if __name__ == "__main__":
    asyncio.run(main())
