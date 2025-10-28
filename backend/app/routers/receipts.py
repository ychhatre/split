from fastapi import APIRouter, UploadFile, File, HTTPException
from app.receipt_parser import ReceiptParser
from app.storage_client import s3_client
import base64
import uuid

router = APIRouter(prefix="/api/receipt", tags=["receipts"])
parser = ReceiptParser()


@router.post("/upload")
async def upload_receipt(file: UploadFile = File(...)):
    """
    Upload a receipt image and parse it using OpenAI Vision API.
    Returns the parsed receipt data with a session ID for storing the image.
    """
    print(f"Received file upload request. Filename: {file.filename}, Content type: {file.content_type}")
    
    # Generate session ID for this receipt
    session_id = str(uuid.uuid4())
    print(f"Generated session ID: {session_id}")
    
    # Check file type
    if not file.content_type or not file.content_type.startswith("image/"):
        print(f"Invalid file type: {file.content_type}")
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read file content
        print("Reading file content...")
        image_content = await file.read()
        print(f"File size: {len(image_content)} bytes")
        
        # Upload to S3
        print("Uploading image to S3...")
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        object_name = f"{session_id}/receipt.{file_extension}"
        
        try:
            s3_url = s3_client.upload_file(
                object_name=object_name,
                file_data=image_content,
                content_type=file.content_type
            )
            print(f"S3 URL: {s3_url}")
        except Exception as e:
            print(f"S3 error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to store image: {e}")
        
        # Convert to base64 for OpenAI
        print("Converting to base64 for OpenAI...")
        image_base64 = base64.b64encode(image_content).decode('utf-8')
        print(f"Base64 length: {len(image_base64)} characters")
        
        # Parse receipt
        print("Calling receipt parser...")
        receipt_data = await parser.parse_receipt_image(image_base64)
        
        print("Receipt parsed successfully!")
        
        # Convert Pydantic model to dict for JSON response
        response_data = receipt_data.model_dump()
        response_data["image_url"] = s3_url  # Include S3 URL in response
        response_data["session_id"] = session_id  # Include session ID for session creation
        
        return response_data
        
    except ValueError as e:
        print(f"ValueError during receipt processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        print(f"Unexpected error processing receipt: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing receipt: {str(e)}")
