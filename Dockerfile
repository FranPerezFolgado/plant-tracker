# ---------------------------------------------------------------------------
# Plant Tracker — Dockerfile
# Builds a lightweight image for the FastAPI application.
# ---------------------------------------------------------------------------

FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy dependency list first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY app/ .

# Expose the port that uvicorn will listen on
EXPOSE 8000

# Start the FastAPI application with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
