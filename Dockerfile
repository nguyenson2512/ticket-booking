# Dockerfile for FastAPI app
FROM python:3.11-slim

WORKDIR /app

# Copy environment variables from .env file if present
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
