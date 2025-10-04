from bullmq import Worker
import asyncio
import signal
from minio import Minio
from dotenv import load_dotenv
from ai import extract_resume_data
import os
from api import set_status, update_parsed_data

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

    finally:
        response.close()
        response.release_conn()


async def process_extraction(job, job_token):

    # return type Future based on Worker
    return handle_extraction(job)


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
        process_extraction,
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
