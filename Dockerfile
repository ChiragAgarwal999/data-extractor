FROM python:3.10-slim

# Install system dependencies for Selenium + Chrome
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg \
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set environment for Selenium
ENV PATH="/usr/lib/chromium:/usr/lib/chromium-browser:${PATH}"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
