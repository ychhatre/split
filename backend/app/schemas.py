from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class ReceiptItemBase(BaseModel):
    id: str
    name: str
    price: float
    quantity: int = 1


class ReceiptItem(ReceiptItemBase):
    pass


class ReceiptData(BaseModel):
    items: List[ReceiptItem]
    subtotal: float
    tax: float
    tip: float
    total: float


class SessionCreate(BaseModel):
    host_name: str
    receipt_data: ReceiptData
    receipt_image_url: Optional[str] = None  # MinIO URL to the receipt image
    session_id: Optional[str] = None  # Session ID from receipt upload
    host_payment_handle: Optional[str] = None
    number_of_guests: Optional[int] = 1


class SessionResponse(BaseModel):
    id: str
    host_name: str
    host_payment_handle: Optional[str] = None
    receipt_image_url: Optional[str] = None
    receipt_items: List[Dict[str, Any]]
    item_splits: Optional[Dict[str, Any]] = None
    claimed_items: Optional[Dict[str, Any]] = None  # Dynamically computed
    number_of_guests: Optional[int] = 1
    tax_amount: float
    tip_amount: float
    subtotal: float
    total: float
    qr_code_url: str
    created_at: datetime
    status: str
    
    class Config:
        from_attributes = True


class UserJoin(BaseModel):
    name: str


class UserSelectItems(BaseModel):
    item_ids: List[str]
    payment_method: Optional[str] = None
    payment_handle: Optional[str] = None
    host_payment_handle: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    name: str
    selected_items: List[str]
    subtotal: float
    tax: float
    tip: float
    total: float
    paid: bool
    payment_method: Optional[str] = None
    host_payment_handle: Optional[str] = None


class SessionStatusResponse(BaseModel):
    session: SessionResponse
    users: List[UserResponse]


class MarkPaid(BaseModel):
    paid: bool = True
