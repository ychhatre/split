#!/bin/bash

# Complete deployment script with database migrations
# Usage: ./deploy.sh <aws-region> <ecr-repository-name>

set -e

# Check if required arguments are provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <aws-region> <ecr-repository-name>"
    echo "Example: $0 us-east-1 split-backend"
    exit 1
fi

AWS_REGION=$1
ECR_REPOSITORY=$2

echo "🚀 Starting deployment process..."

# Step 1: Run database migrations
echo "📊 Running database migrations..."
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL environment variable not set!"
    echo "Please set your RDS database URL:"
    echo "export DATABASE_URL='postgresql://username:password@your-rds-endpoint:5432/your-database'"
    exit 1
fi

python migrate.py

# Step 2: Build and push Docker image
echo "🐳 Building and pushing Docker image..."
./build-and-push.sh $AWS_REGION $ECR_REPOSITORY

echo "✅ Deployment completed successfully!"
echo ""
echo "Next steps:"
echo "1. Update your Lambda function to use the new image"
echo "2. Test your API endpoints"
echo "3. Monitor CloudWatch logs for any issues"
