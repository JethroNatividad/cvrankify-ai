# CVRankify AI

A FastAPI-based application for CV ranking and analysis using AI.

## Features

- Built with FastAPI for high-performance API development
- AI-powered CV analysis and ranking capabilities
- RESTful API endpoints for easy integration

## Prerequisites

- Python 3.11 or higher
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
   pip install -r requirements.txt
   pip install "fastapi[standard]"
   ```

## Running the Application

### Development Mode
```bash
python -m fastapi dev main.py
```

The application will be available at:
- **API**: http://localhost:8000
- **Interactive Documentation**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

### Production Mode
```bash
python -m fastapi run main.py
```

## API Documentation

Once the server is running, you can access:
- **Swagger UI**: Navigate to http://localhost:8000/docs for interactive API documentation
- **ReDoc**: Navigate to http://localhost:8000/redoc for alternative documentation format