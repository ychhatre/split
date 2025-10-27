from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, index=True)
    host_name = Column(String)
    host_payment_handle = Column(String)  # Host's payment handle (e.g., Venmo username)
    receipt_image_url = Column(String)  # MinIO URL to the receipt image
    receipt_items = Column(JSON)  # Parsed items
    item_splits = Column(JSON, default=dict)  # Track how items are split: {item_id: [{"user_id": int, "user_name": str, "share": float}]}
    number_of_guests = Column(Integer, default=1)  # Number of guests splitting the bill
    tax_amount = Column(Float, default=0.0)
    tip_amount = Column(Float, default=0.0)
    subtotal = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    qr_code_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="active")  # active, completed
    
    users = relationship("SessionUser", back_populates="session", cascade="all, delete-orphan")


class SessionUser(Base):
    __tablename__ = "session_users"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), index=True)
    name = Column(String)
    selected_items = Column(JSON, default=list)  # List of item IDs selected
    subtotal = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    tip = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    paid = Column(Boolean, default=False)
    payment_method = Column(String)  # venmo, paypal, cashapp, zelle, apple_pay
    payment_handle = Column(String)  # User's payment handle
    host_payment_handle = Column(String)  # Host's payment handle to send to
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("Session", back_populates="users")
