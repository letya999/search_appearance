FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY README.md .
COPY mvp/ mvp/
COPY data/ data/
COPY config/ config/

# Install dependencies
RUN pip install --no-cache-dir .

# Expose the API port
EXPOSE 8000

# Set environment variables
ENV GRADIO_SERVER_NAME="0.0.0.0"

# Command to run the application
CMD ["uvicorn", "mvp.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
