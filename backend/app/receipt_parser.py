from openai import AsyncOpenAI
import os
import json
import base64
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from typing import Optional
from app.config import OPENAI_API_KEY 
from io import BytesIO

# Set up logger
logger = logging.getLogger(__name__)


def compress_image_for_vision(image_data: bytes, max_size: int = 2048) -> str:
    """
    Compress and resize image for OpenAI Vision API to improve speed.
    Returns base64 encoded string.
    
    Args:
        image_data: Raw image bytes
        max_size: Maximum width/height in pixels (default 2048 for good quality)
    
    Returns:
        Base64 encoded compressed image
    """
    try:
        from PIL import Image
        
        # Open image
        img = Image.open(BytesIO(image_data))
        
        # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize if too large
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            logger.info(f"Resized image to {img.size}")
        
        # Compress to JPEG with good quality
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=85, optimize=True)
        compressed_data = buffer.getvalue()
        
        # Log compression results
        original_size = len(image_data)
        compressed_size = len(compressed_data)
        reduction = (1 - compressed_size/original_size) * 100
        logger.info(f"Image compression: {original_size/1024:.1f}KB → {compressed_size/1024:.1f}KB ({reduction:.1f}% reduction)")
        
        return base64.b64encode(compressed_data).decode('utf-8')
        
    except ImportError:
        logger.warning("Pillow not installed, skipping image compression")
        return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        logger.warning(f"Image compression failed, using original: {e}")
        return base64.b64encode(image_data).decode('utf-8')


class ReceiptItem(BaseModel):
    id: str
    name: str
    price: float
    quantity: int = 1


class ReceiptData(BaseModel):
    items: List[ReceiptItem] = Field(default_factory=list)
    subtotal: float = 0.0
    tax: float = 0.0
    tip: float = 0.0
    total: Optional[float] = None
    
    def model_post_init(self, __context):
        """Calculate total if not provided"""
        if self.total is None:
            self.total = round(self.subtotal + self.tax + self.tip, 2)


class ReceiptParser:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    
    async def parse_receipt_image(self, image_base64: str) -> ReceiptData:
        """
        Parse a receipt image using OpenAI Vision API.
        Returns structured ReceiptData with validated items, prices, tax, tip, and total.
        """
        logger.info("Starting receipt parsing...")
        
        # Construct the system and user prompts
        system_prompt = """You are an expert at parsing restaurant receipts. 
Extract the following information from the receipt image and return it as valid JSON:

1. items: array of objects with 'id' (unique identifier), 'name' (item name), 'price' (item price), and 'quantity' (default 1)
2. subtotal: total before tax and tip
3. tax: tax amount
4. tip: tip amount (if present)
5. total: final total amount

Return ONLY valid JSON in this exact format (no markdown, no code blocks):
{
  "items": [
    {"id": "item1", "name": "Item Name", "price": 12.99, "quantity": 1}
  ],
  "subtotal": 50.00,
  "tax": 4.50,
  "tip": 10.00,
  "total": 64.50
}"""

        user_prompt = "Please extract the receipt information as specified."

        try:
            logger.info("Sending request to OpenAI Vision API...")
            logger.info(f"Image base64 length: {len(image_base64)} characters")
            
            # Use async OpenAI client for better performance
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {
                            "type": "text",
                            "text": user_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"  # Use high detail for better accuracy
                            }
                        }
                    ]}
                ],
                max_tokens=1500,  # Reduced from 2000 to speed up response
                temperature=0.1,  # Low temperature for more consistent results
                response_format={"type": "json_object"}
            )
            
            logger.info("Received response from OpenAI")
            
            # Extract JSON from response
            content = response.choices[0].message.content.strip()
            logger.info(f"Response content length: {len(content)} characters")
            logger.info(f"Response content (first 200 chars): {content[:200]}")
            
            # Parse JSON and validate with Pydantic
            logger.info("Parsing JSON response...")
            raw_data = json.loads(content)
            logger.info(f"Parsed JSON successfully. Keys: {list(raw_data.keys())}")
            
            logger.info("Validating with Pydantic...")
            receipt_data = ReceiptData(**raw_data)
            logger.info(f"Validation successful. Items count: {len(receipt_data.items)}")
            logger.info(f"Totals - Subtotal: {receipt_data.subtotal}, Tax: {receipt_data.tax}, Tip: {receipt_data.tip}, Total: {receipt_data.total}")
            
            return receipt_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Content that failed to parse: {content[:500] if 'content' in locals() else 'N/A'}")
            raise ValueError(f"Failed to parse JSON from OpenAI response: {e}")
        except ValueError as e:
            logger.error(f"Pydantic validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error parsing receipt: {e}", exc_info=True)
            raise ValueError(f"Error parsing receipt: {e}")


def calculate_user_totals(
    selected_item_ids: List[str],
    all_items: List[Dict[str, Any]],
    tax_amount: float,
    tip_amount: float,
    subtotal: float
) -> Dict[str, float]:
    """
    Calculate the user's subtotal, tax, tip, and total based on selected items.
    
    Args:
        selected_item_ids: List of item IDs the user selected
        all_items: List of all receipt items with id, name, price, quantity
        tax_amount: Total tax from receipt
        tip_amount: Total tip from receipt
        subtotal: Total subtotal from receipt
    
    Returns:
        Dictionary with subtotal, tax, tip, and total for the user
    """
    user_subtotal = 0.0
    
    # Calculate user's subtotal from selected items
    for item in all_items:
        if item.get("id") in selected_item_ids:
            user_subtotal += item.get("price", 0) * item.get("quantity", 1)
    
    # Calculate proportional tax and tip
    if subtotal > 0:
        tax_proportion = user_subtotal / subtotal
        user_tax = tax_amount * tax_proportion
        user_tip = tip_amount * tax_proportion
    else:
        user_tax = 0.0
        user_tip = 0.0
    
    user_total = user_subtotal + user_tax + user_tip
    
    return {
        "subtotal": round(user_subtotal, 2),
        "tax": round(user_tax, 2),
        "tip": round(user_tip, 2),
        "total": round(user_total, 2)
    }
