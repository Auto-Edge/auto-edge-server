FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libprotobuf-dev \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create shared data directory
RUN mkdir -p /app/shared_data

# Set Python path to include app and worker modules
ENV PYTHONPATH=/app

EXPOSE 8000

# Default command for API server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
