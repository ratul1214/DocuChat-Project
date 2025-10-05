FROM python:3.11-slim

WORKDIR /app

# System deps (optional but nice to have for some packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 👉 Upgrade pip tooling first (prevents many resolver/wheel issues)
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY . .



EXPOSE 8000
