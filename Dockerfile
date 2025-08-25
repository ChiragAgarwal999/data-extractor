FROM python:3.10-slim

# Install system dependencies for Selenium + Chromium
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg \
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables so Selenium finds Chromium
ENV PATH="/usr/bin/chromium:/usr/bin/chromium-browser:${PATH}"
ENV CHROMIUM_BIN="/usr/bin/chromium"
ENV CHROMEDRIVER_BIN="/usr/bin/chromedriver"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-b", "0.0.0.0:8080", "main:app"]
