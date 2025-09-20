# CVRankify AI

A Redis-based job processing worker for CV ranking and analysis using AI.

## Features

- Built with BullMQ for reliable job queue processing
- Redis-based job queue for scalable task management
- Asynchronous job processing with graceful shutdown handling
- AI-powered CV analysis and ranking capabilities

## Prerequisites

- Python 3.11 or higher
- Redis server running on localhost:6379 (or configure connection string)
- pip (Python package installer)

## Installation & Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cvrankify-ai
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv env
   ```

3. **Activate the virtual environment**
   ```bash
   source env/bin/activate  # On macOS/Linux
   # or
   env\Scripts\activate     # On Windows
   ```

4. **Install dependencies**
   ```bash
   pip install bullmq
   ```

### Start the Worker
```bash
python main.py
```

The worker will:
- Connect to Redis on `localhost:6379`
- Listen for jobs in the `cvrankify-jobs` queue
- Process jobs asynchronously with the defined job handler
- Handle graceful shutdown on SIGTERM/SIGINT signals

### Stopping the Worker
Use `Ctrl+C` to gracefully shut down the worker.

## Configuration

- **Redis Connection**: Modify the connection string in `main.py` if your Redis server is not on localhost:6379
- **Queue Name**: The worker listens to the `cvrankify-jobs` queue by default
- **Job Processing**: Customize the `process` function in `main.py` to implement your CV analysis logic

## Fine-tuning Models
In finetuned_models/, you can find the finetuned Modelfiles

## To create the finetuned models, run:
ollama create edu-timezone-extractor -f finetuned_models/edu_timezone_extractor/Modelfile
ollama create experience-extractor -f finetuned_models/experience_extractor/Modelfile
ollama create skills-extractor -f finetuned_models/skills_extractor/Modelfile