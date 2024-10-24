# Use an official Python image as a base
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Pipenv
RUN pip install --upgrade pip && pip install pipenv

# Copy Pipfile and Pipfile.lock to the working directory
COPY Pipfile Pipfile.lock /app/

# Create the logs directory
RUN mkdir -p /app/logs

# Ensure the logs directory is writable
RUN chmod -R 777 /app/logs

# Copy logging configuration
COPY logging.conf /app/logging.conf

# Generate requirements.txt from Pipfile.lock and install dependencies
RUN pipenv requirements > requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project, including tests, to /app/
COPY . /app/  

# Expose port 8000 for the FastAPI app
EXPOSE 8000

# Set environment variables (dynamic, can be overridden in docker run)
ENV MONGO_URI=mongodb://localhost:27017/vehicle_allocation_db
ENV REDIS_HOST=redis://localhost:6379
ENV ENV=dev

# Command to run the FastAPI app using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
