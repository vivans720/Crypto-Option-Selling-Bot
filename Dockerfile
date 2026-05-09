FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set Timezone
ENV TZ=UTC

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure storage and logs exist
RUN mkdir -p storage logs

# Run live engine with unbuffered output
CMD ["python", "-u", "run_live.py"]
