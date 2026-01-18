# Dockerfile for A2A Joke Generator Agent
# This container can be deployed to any platform that supports Docker

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port
EXPOSE 8000

# Run the server
# Note: The PORT environment variable will be used if set (for platforms like Render)
CMD ["python", "main.py", "--host", "0.0.0.0"]
