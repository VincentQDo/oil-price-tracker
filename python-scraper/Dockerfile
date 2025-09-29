FROM python:3.13-slim

# Install deps
RUN pip install requests

# Copy code
WORKDIR /app
COPY scraper.py .

# Run script by default
CMD ["python", "scraper.py"]
