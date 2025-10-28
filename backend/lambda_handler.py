import os
import sys
from mangum import Mangum
import logging

logger = logging.getLogger(__name__)

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
    printj(f"Lambda handler called with event: {event}")
    print(f"Context: {context.function_name}")
    return handler(event, context)
