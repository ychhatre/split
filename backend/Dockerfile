# Use the official AWS Lambda Python runtime base image
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.11

# Set the working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Create a lambda handler wrapper
COPY lambda_handler.py .

# Set the CMD to your handler
CMD ["lambda_handler.lambda_handler"]
