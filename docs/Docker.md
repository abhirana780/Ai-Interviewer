# Docker Guide

This guide shows a recommended, CPU-focused Docker setup for `wipronix` and notes for GPU setups.

## Recommended Dockerfile (CPU)

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential git ffmpeg libsndfile1 libsndfile1-dev \
      espeak-ng libespeak-ng-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/backend/requirements.txt

COPY . /app

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE ${PORT}
ENV FLASK_APP=backend.app
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "backend.app:app", "--workers", "3"]
```

### Notes
- `ffmpeg` and `libsndfile` are required for audio/video processing.
- `espeak` / `espeak-ng` helps `pyttsx3` generate audio in headless containers.
- If you require GPU acceleration, start from NVIDIA's CUDA images and install GPU-compatible `torch` wheels.

## docker-compose example (development)

```yaml
version: "3.8"
services:
  web:
    build: .
    ports:
      - "7860:7860"
    environment:
      - HF_API_KEY=${HF_API_KEY}
      - PORT=7860
    volumes:
      - ./frontend:/app/frontend:ro
      - ./backend/database:/app/backend/database
      - ./frontend/media:/app/frontend/media
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7860/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Volumes & persistence
- Persist `backend/database` and `frontend/media` using volumes so sessions, transcripts, and media are not lost when containers are recreated.

## Notes & Troubleshooting
- Some audio/TTS setups require additional system packages depending on the base image. If TTS fails inside the container, verify that `espeak` or platform-specific voice engines are installed.
- Pin `torch` and other large libs in `backend/requirements.txt` for reproducible builds.
- Use `.dockerignore` to reduce build context size (see project root `.dockerignore`).
