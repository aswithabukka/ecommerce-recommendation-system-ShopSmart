FROM python:3.11

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy pipeline code
COPY . .

# Default command (can be overridden)
CMD ["python", "-c", "print('ML pipeline container ready. Run pipelines with: docker exec shopsmart-ml python -m pipelines.<pipeline_name>')"]
