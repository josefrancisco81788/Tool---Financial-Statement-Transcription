# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

# Optional system deps for pdf2image (Poppler). Remove if relying solely on PyMuPDF.
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
  && rm -rf /var/lib/apt/lists/*

# Install API dependencies
COPY requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy project
COPY . .

# Switch to API directory and run Uvicorn
WORKDIR /app/api

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
