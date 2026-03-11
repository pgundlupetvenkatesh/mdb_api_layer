# This file should define the environment for running tests in a containerized setup on how to build an image.
# It uses Poetry for dependency management and pytest for testing, with HTML reporting.
# Dockerfile → build → Docker Image

# Use official Python slim image for smaller size
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy dependency files first (leverages Docker layer caching)
COPY pyproject.toml poetry.lock ./

# Install dependencies (no root package, just deps)
RUN poetry install --no-root --no-ansi

# Copy the rest of the project
COPY . .

# Default command: run tests
# Local runs only execute this command from the Dockerfile.
CMD ["pytest", "tests/", \
     "--html=report/tmdb_full_report.html", \
     "--self-contained-html", "-v", "-s"]