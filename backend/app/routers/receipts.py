from fastapi import APIRouter, UploadFile, File, HTTPException
from app.receipt_parser import ReceiptParser, compress_image_for_vision
from app.storage_client import s3_client
import base64
import uuid
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/receipt", tags=["receipts"])
parser = ReceiptParser()


@router.post("/upload")
async def upload_receipt(file: UploadFile = File(...)):
    """
    Upload a receipt image and parse it using OpenAI Vision API.
    Returns the parsed receipt data with a session ID for storing the image.
    """
    logger.info(f"📤 Receipt upload request - Filename: {file.filename}, Content-Type: {file.content_type}")
    
    # Generate session ID for this receipt
    session_id = str(uuid.uuid4())
    logger.info(f"Generated session ID: {session_id}")
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        logger.warning(f"Invalid file type rejected: {file.content_type}")
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read file content
        logger.debug("Reading file content...")
        image_content = await file.read()
        logger.info(f"File size: {len(image_content)} bytes")
        
        # Prepare data for parallel operations
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        object_name = f"{session_id}/receipt.{file_extension}"
        
        # Compress image for faster OpenAI processing (run in thread to not block)
        logger.info("Compressing image for OpenAI...")
        image_base64 = await asyncio.to_thread(compress_image_for_vision, image_content)
        
        # Run S3 upload and OpenAI parsing in parallel for speed
        logger.info("Starting parallel S3 upload and receipt parsing...")
        
        async def upload_to_s3():
            """Upload image to S3 in background"""
            try:
                return await asyncio.to_thread(
                    s3_client.upload_file,
                    object_name=object_name,
                    file_data=image_content,
                    content_type=file.content_type
                )
            except Exception as e:
                logger.error(f"S3 upload failed: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Failed to store image: {e}")
        
        # Run both operations concurrently
        s3_url, receipt_data = await asyncio.gather(
            upload_to_s3(),
            parser.parse_receipt_image(image_base64)
        )
        
        logger.info(f"✓ S3 upload successful: {s3_url}")
        logger.info(f"✓ Receipt parsed successfully - {len(receipt_data.items)} items found, total: ${receipt_data.total}")
        
        # Convert Pydantic model to dict for JSON response
        response_data = receipt_data.model_dump()
        response_data["image_url"] = s3_url
        response_data["session_id"] = session_id
        
        return response_data
        
    except ValueError as e:
        logger.error(f"Receipt processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error processing receipt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing receipt: {str(e)}")
