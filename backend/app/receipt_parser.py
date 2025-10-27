from openai import OpenAI
import os
import json
import base64
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from typing import Optional

# Set up logger
logger = logging.getLogger(__name__)


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
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
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
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini for cost efficiency
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
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]}
                ],
                max_tokens=2000,
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
