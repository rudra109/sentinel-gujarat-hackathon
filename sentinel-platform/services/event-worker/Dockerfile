FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Reuse the API requirements
COPY ../api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/worker
COPY ../api /app/api

ENV PYTHONPATH=/app/api

CMD ["python", "/app/worker/worker.py"]
