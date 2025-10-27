import os
import sys
from mangum import Mangum

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import app after configuration is loaded
from app.main import app

# Create the Lambda handler using Mangum
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    This function is the entry point for Lambda invocations.
    """
    return handler(event, context)
