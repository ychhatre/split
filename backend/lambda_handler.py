import os
import sys
from mangum import Mangum
import logging
import json

logger = logging.getLogger(__name__)

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import app after configuration is loaded
from app.main import app

# Create the Lambda handler using Mangum with custom config
handler = Mangum(app, lifespan="off", api_gateway_base_path="/")

def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    This function is the entry point for Lambda invocations.
    """
    try:
        print(f"Lambda invoked: {context.function_name}")
        print(f"Request method: {event.get('requestContext', {}).get('http', {}).get('method', 'UNKNOWN')}")
        print(f"Request path: {event.get('requestContext', {}).get('http', {}).get('path', 'UNKNOWN')}")
        print(f"Content-Type: {event.get('headers', {}).get('content-type', 'NONE')}")
        
        # Check if body is present
        if 'body' in event:
            print(f"Body present: {len(event['body']) if event['body'] else 0} bytes")
            print(f"Is Base64: {event.get('isBase64Encoded', False)}")
        
        result = handler(event, context)
        print(f"Handler completed successfully")
        return result
    except Exception as e:
        print(f"ERROR in lambda_handler: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise
