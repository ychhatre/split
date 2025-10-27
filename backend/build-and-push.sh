#!/bin/bash

# Build and push script for AWS Lambda deployment
# Usage: ./build-and-push.sh <aws-region> <ecr-repository-name>

set -e

# Check if required arguments are provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <aws-region> <ecr-repository-name>"
    echo "Example: $0 us-east-1 split-backend"
    exit 1
fi

AWS_REGION=$1
ECR_REPOSITORY=$2
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Full ECR repository URI
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"

echo "Building Docker image..."
docker build -t ${ECR_REPOSITORY} .

echo "Tagging image for ECR..."
docker tag ${ECR_REPOSITORY}:latest ${ECR_URI}:latest

echo "Logging in to ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URI}

echo "Pushing image to ECR..."
docker push ${ECR_URI}:latest

echo "Image pushed successfully!"
echo "ECR URI: ${ECR_URI}:latest"
echo ""
echo "To deploy to Lambda, use this image URI in your Lambda function configuration."
