FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
# build-essential can be useful for some python extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY README.md .
COPY mvp/ mvp/
COPY run_demo.py .

# Install dependencies
# We use pip to install the current directory/project
RUN pip install --no-cache-dir .

# Expose the Gradio port
EXPOSE 7860

# Set environment variables if needed
ENV GRADIO_SERVER_NAME="0.0.0.0"

# Command to run the application
CMD ["python", "run_demo.py"]
