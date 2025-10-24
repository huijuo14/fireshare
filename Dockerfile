FROM python:3.11-slim

# Install system dependencies including Firefox and geckodriver
RUN apt-get update && apt-get install -y \
    firefox-esr \
    wget \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install geckodriver for Firefox
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux64.tar.gz \
    && tar -xzf geckodriver-v0.34.0-linux64.tar.gz -C /usr/local/bin/ \
    && rm geckodriver-v0.36.0-linux64.tar.gz \
    && chmod +x /usr/local/bin/geckodriver

# Create app directory and download uBlock Origin
RUN mkdir -p /app
WORKDIR /app
RUN wget -O ublock.xpi https://addons.mozilla.org/firefox/downloads/file/4598854/ublock_origin-1.67.0.xpi

# Copy application files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers
RUN playwright install
RUN playwright install-deps

# Run the application
CMD ["python", "app.py"]
