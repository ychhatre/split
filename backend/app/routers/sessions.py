from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Session as SessionModel, SessionUser
from app.schemas import SessionCreate, SessionResponse, SessionStatusResponse, UserJoin, UserSelectItems, UserResponse, MarkPaid
from app.receipt_parser import calculate_user_totals
from app.config import FRONTEND_URL
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
    qr_data = f"{FRONTEND_URL}/session/{session_id}"
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
    Simple approach: each user claims entire items (no splitting).
    """
    # Get session
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get user
    user = db.query(SessionUser).filter(SessionUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get currently claimed items
    claimed_items = get_claimed_items_from_users(session_id, db)
    
    # Check for already claimed items (excluding current user's items)
    already_claimed = []
    for item_id in selection.item_ids:
        if item_id in claimed_items and claimed_items[item_id] != user_id:
            # Find the item name for the error message
            item_name = next((item.get("name", item_id) for item in session.receipt_items if item.get("id") == item_id), item_id)
            already_claimed.append(item_name)
    
    if already_claimed:
        raise HTTPException(
            status_code=400,
            detail=f"Items already claimed by others: {', '.join(already_claimed)}"
        )
    
    # Calculate user totals
    totals = calculate_user_totals(
        selected_item_ids=selection.item_ids,
        all_items=session.receipt_items,
        tax_amount=session.tax_amount,
        tip_amount=session.tip_amount,
        subtotal=session.subtotal
    )
    
    # Update user
    user.selected_items = selection.item_ids
    user.subtotal = totals["subtotal"]
    user.tax = totals["tax"]
    user.tip = totals["tip"]
    user.total = totals["total"]
    user.host_payment_handle = session.host_payment_handle
    user.payment_method = "venmo"
    
    db.commit()
    db.refresh(user)
    
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
