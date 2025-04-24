FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs reports

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Create a non-root user
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# Command to run
CMD ["python", "main.py", "all", "--export"]