# Use a stable Python base (adjust tag if needed)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

# Install system dependencies required by audio/video packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential git ffmpeg libsndfile1 libsndfile1-dev \
      espeak-ng libespeak-ng-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies first to leverage cache
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/backend/requirements.txt

# Copy the rest of the repo
COPY . /app

# Create non-root user and give ownership of /app
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE ${PORT}

# Environment variable used by the Flask app
ENV FLASK_APP=backend.app

# Recommended production command (Gunicorn)
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "backend.app:app", "--workers", "3"]