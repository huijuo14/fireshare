FROM python:3.11-slim

# Install system dependencies for Firefox and Playwright
RUN apt-get update && apt-get install -y \
    wget \
    xvfb \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libatspi2.0-0 \
    fonts-liberation \
    libappindicator3-1 \
    libxtst6 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
RUN mkdir -p /app
WORKDIR /app

# Download uBlock Origin
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
