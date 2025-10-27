from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Session as SessionModel, SessionUser
from app.schemas import SessionCreate, SessionResponse, SessionStatusResponse, UserJoin, UserSelectItems, UserResponse, MarkPaid
from app.receipt_parser import calculate_user_totals
import uuid
import qrcode
from io import BytesIO
import base64

router = APIRouter(prefix="/api/session", tags=["sessions"])


@router.post("/create", response_model=SessionResponse)
async def create_session(session_data: SessionCreate, db: Session = Depends(get_db)):
    """
    Create a new session with receipt data.
    Generates a QR code for sharing.
    Reuses the session_id from receipt upload if provided.
    """
    # Use provided session_id or generate new one
    session_id = session_data.session_id if hasattr(session_data, 'session_id') and session_data.session_id else str(uuid.uuid4())
    
    # Generate QR code
    # Assuming frontend URL will be passed or configured
    qr_data = f"http://localhost:3000/session/{session_id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    qr_code_url = f"data:image/png;base64,{qr_base64}"
    
    # Create session
    db_session = SessionModel(
        id=session_id,
        host_name=session_data.host_name,
        host_payment_handle=session_data.host_payment_handle,
        receipt_image_url=session_data.receipt_image_url,
        receipt_items=session_data.receipt_data.dict()["items"],
        item_splits={},  # Initialize empty dict for tracking item splits
        number_of_guests=session_data.number_of_guests if hasattr(session_data, 'number_of_guests') else 1,
        tax_amount=session_data.receipt_data.tax,
        tip_amount=session_data.receipt_data.tip,
        subtotal=session_data.receipt_data.subtotal,
        total=session_data.receipt_data.total,
        qr_code_url=qr_code_url
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """Get session details."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get claimed items and add to session object dynamically
    claimed_items = get_claimed_items_from_users(session_id, db)
    # Convert to dict for response
    session_dict = {**session.__dict__}
    session_dict['claimed_items'] = claimed_items
    return session_dict


@router.post("/{session_id}/join")
async def join_session(session_id: str, user_data: UserJoin, db: Session = Depends(get_db)):
    """
    Join a session as a user.
    Returns user ID for the session.
    """
    # Check if session exists
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Create user
    db_user = SessionUser(
        session_id=session_id,
        name=user_data.name
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {"user_id": db_user.id, "message": "Joined session successfully"}


def get_claimed_items_from_users(session_id: str, db: Session) -> dict:
    """
    Helper function to get claimed items by querying all users in the session.
    Returns a dict mapping item_id to user_id who claimed it.
    """
    users = db.query(SessionUser).filter(SessionUser.session_id == session_id).all()
    claimed_items = {}
    for user in users:
        if user.selected_items:
            for item_id in user.selected_items:
                claimed_items[item_id] = user.id
    return claimed_items


@router.post("/{session_id}/user/{user_id}/select")
async def select_items(
    session_id: str,
    user_id: int,
    selection: UserSelectItems,
    db: Session = Depends(get_db)
):
    """
    Select items for a user and calculate their totals.
    Supports splitting items across multiple users.
    """
    # Get session
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get user
    user = db.query(SessionUser).filter(SessionUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Initialize item_splits if None
    if session.item_splits is None:
        session.item_splits = {}
    
    # Track items and calculate totals
    user_item_ids = []
    user_subtotal = 0.0
    
    # Process each item split
    for item_split in selection.item_splits:
        item_id = item_split.item_id
        split_count = item_split.split_count
        
        # Find the item details
        item = next((item for item in session.receipt_items if item.get("id") == item_id), None)
        if not item:
            raise HTTPException(status_code=400, detail=f"Item {item_id} not found")
        
        # Calculate the user's share
        item_price = item.get("price", 0) * item.get("quantity", 1)
        user_share = item_price / split_count
        
        # Check if there's enough remaining amount for this item
        item_splits = session.item_splits.get(item_id, []) if session.item_splits else []

        # Calculate total amount already split (excluding current user's existing shares)
        total_split = sum(
            s.get("share", 0) for s in item_splits 
            if s.get("user_id") != user_id
        )
        remaining_amount = item_price - total_split
        
        # Validate that user's share doesn't exceed remaining amount
        if user_share > remaining_amount:
            raise HTTPException(
                status_code=400, 
                detail=f"Item '{item.get('name', item_id)}' has ${remaining_amount:.2f} remaining, but you're trying to claim ${user_share:.2f}"
            )
        
        user_subtotal += user_share
        user_item_ids.append(item_id)
        
        # Update item_splits tracking
        if item_id not in session.item_splits:
            session.item_splits[item_id] = []
        
        # Remove any existing entry for this user (in case they're updating)
        session.item_splits[item_id] = [
            s for s in session.item_splits[item_id] 
            if s.get("user_id") != user_id
        ]
        
        # Add the new split entry
        session.item_splits[item_id].append({
            "user_id": user_id,
            "user_name": user.name,
            "share": round(user_share, 2),
            "split_count": split_count
        })
    
    # Calculate proportional tax and tip
    if session.subtotal > 0:
        tax_rate = session.tax_amount / session.subtotal
        tip_rate = session.tip_amount / session.subtotal
        user_tax = user_subtotal * tax_rate
        user_tip = user_subtotal * tip_rate
    else:
        user_tax = 0.0
        user_tip = 0.0
    
    user_total = user_subtotal + user_tax + user_tip
    
    # Update user
    user.selected_items = user_item_ids
    user.subtotal = round(user_subtotal, 2)
    user.tax = round(user_tax, 2)
    user.tip = round(user_tip, 2)
    user.total = round(user_total, 2)
    user.host_payment_handle = session.host_payment_handle
    user.payment_method = "venmo"
    
    # Save changes
    db.commit()
    db.refresh(user)
    db.refresh(session)
    
    return user


@router.post("/{session_id}/user/{user_id}/pay")
async def mark_as_paid(
    session_id: str,
    user_id: int,
    payment_status: MarkPaid,
    db: Session = Depends(get_db)
):
    """Mark a user as paid."""
    user = db.query(SessionUser).filter(SessionUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.paid = payment_status.paid
    db.commit()
    
    return {"message": "Payment status updated"}


@router.get("/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(session_id: str, db: Session = Depends(get_db)):
    """Get full session status with all users and their payment status."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    users = db.query(SessionUser).filter(SessionUser.session_id == session_id).all()
    
    # Get claimed items and add to session
    claimed_items = get_claimed_items_from_users(session_id, db)
    session_dict = {**session.__dict__}
    session_dict['claimed_items'] = claimed_items
    
    return {
        "session": session_dict,
        "users": users
    }
