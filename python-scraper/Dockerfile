FROM python:3.13-slim

WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code
COPY scraper.py .

# Run script by default
CMD ["python", "scraper.py"]
