FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run with unbuffered output for logging
CMD ["python", "-u", "engine/live_engine.py"]
