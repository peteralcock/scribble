# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies that might be needed by some Python packages
# (e.g., for packages with C extensions). For this project, it might not be
# strictly necessary but is good practice.
# RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy the requirements files into the container at /app
COPY requirements.txt test-requirements.txt /app/

# Install project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install test dependencies
RUN pip install --no-cache-dir -r test-requirements.txt

# Copy the pytest configuration file
COPY pytest.ini /app/

# Copy the application source code and tests into the container at /app
COPY ./app /app/app
COPY ./tests /app/tests
COPY application.py /app/

# Expose the port the app runs on
EXPOSE 8000

# Define the default command to run when the container starts
# This will be used by the 'app' service in docker-compose.yml
CMD ["python", "application.py"]
