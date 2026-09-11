FROM python:3.12-slim

# Install system dependencies (FFmpeg for video/audio processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY run.py .

# Ensure storage directories exist
RUN mkdir -p uploads temp_audio outputs

# Environment settings
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV HF_HUB_DISABLE_SYMLINKS_WARNING=1
ENV PORT=7860

EXPOSE 7860

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]

