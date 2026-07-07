FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY verify_connectivity.py .
COPY .env.example .

CMD ["python", "verify_connectivity.py"]
