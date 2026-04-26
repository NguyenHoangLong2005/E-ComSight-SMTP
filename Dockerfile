# E-ComSight Docker deployment
FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Backend deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Frontend pre-built dist (build locally, commit to git)
COPY frontend/dist ./frontend/dist

# Backend code
COPY backend/ ./

# Create data dir
RUN mkdir -p data

# Seed demo data
RUN python seed_data.py || true

EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
