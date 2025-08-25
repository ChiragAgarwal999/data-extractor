FROM python:3.10-slim

# Install dependencies for Selenium + Chrome
RUN apt-get update && apt-get install -y wget gnupg unzip curl \
    && wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+') \
    && MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d. -f1) \
    && wget -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${MAJOR_VERSION}/linux64/chromedriver-linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && mv /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver.zip /usr/local/bin/chromedriver-linux64

# Environment variables
ENV PATH="/usr/local/bin:${PATH}"
ENV CHROME_BIN="/usr/bin/google-chrome"
ENV CHROMEDRIVER_BIN="/usr/local/bin/chromedriver"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-b", "0.0.0.0:8080", "main:app"]
