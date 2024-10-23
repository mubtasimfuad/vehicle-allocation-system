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

# Copy Pipfile and Pipfile.lock to the working directory
COPY Pipfile Pipfile.lock /app/

# Create the logs directory
RUN mkdir -p /app/logs

# Ensure the logs directory is writable
RUN chmod -R 777 /app/logs

# Copy logging configuration
COPY logging.conf /app/logging.conf

# Install Pipenv and dependencies
RUN pip install --upgrade pip && pip install pipenv
RUN pipenv install --deploy --ignore-pipfile

# Copy the rest of the app code to the container
COPY . /app

# Expose port 8000 for the FastAPI app
EXPOSE 8000

# Set environment variables (dynamic, can be overridden in docker run)
ENV MONGO_URI=mongodb://localhost:27017/vehicle_allocation_db
ENV REDIS_HOST=redis://localhost:6379

# Command to run the FastAPI app using Uvicorn
CMD ["pipenv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
