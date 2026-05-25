from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List

from app.database import get_db
from app.models import Message, User, PredictionResult
from app.schemas import MessageCreate, MessageResponse, UserResponse
from app.routes.auth import get_current_user
from app.ml_engine.classifier import predict_comment

router = APIRouter(prefix="/chat", tags=["Private Chat"])

@router.get("/users", response_model=List[UserResponse])
def get_chat_users(db: Session = Depends(get_db), current_actor: dict = Depends(get_current_user)):
    """Fetch all registered users except the currently logged-in actor."""
    users = db.query(User).filter(User.Id != current_actor["user_id"]).all()
    return users

@router.get("/messages/{receiver_id}", response_model=List[MessageResponse])
def get_messages(receiver_id: int, db: Session = Depends(get_db), current_actor: dict = Depends(get_current_user)):
    """Fetch the conversation history with a selected recipient (both Approved and Blocked)."""
    user_id = current_actor["user_id"]
    
    # Confirm recipient exists
    receiver = db.query(User).filter(User.Id == receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Recipient user not found.")
        
    # Fetch messages in ascending chronological order
    messages = db.query(Message).filter(
        and_(
            Message.ModerationStatus.in_(['Approved', 'Blocked']),
            or_(
                and_(Message.SenderId == user_id, Message.ReceiverId == receiver_id),
                and_(Message.SenderId == receiver_id, Message.ReceiverId == user_id)
            )
        )
    ).order_by(Message.Timestamp.asc()).all()
    
    response = []
    for msg in messages:
        sender_user = db.query(User).filter(User.Id == msg.SenderId).first()
        receiver_user = db.query(User).filter(User.Id == msg.ReceiverId).first()
        
        content = msg.MessageText
        if msg.ModerationStatus == 'Blocked':
            content = "🚫 Message blocked by SentryText."
            
        response.append({
            "Id": msg.Id,
            "SenderId": msg.SenderId,
            "SenderName": sender_user.Username if sender_user else "Deleted User",
            "ReceiverId": msg.ReceiverId,
            "ReceiverName": receiver_user.Username if receiver_user else "Deleted User",
            "MessageText": content,
            "ModerationStatus": msg.ModerationStatus,
            "Timestamp": msg.Timestamp
        })
    return response

@router.post("/messages")
def send_message(msg_in: MessageCreate, db: Session = Depends(get_db), current_actor: dict = Depends(get_current_user)):
    """
    Sends a direct message after screening for cyberbullying.
    Blocked messages are stored in the DB for audit logs but not delivered to the chat screen.
    """
    sender_id = current_actor["user_id"]
    receiver_id = msg_in.ReceiverId
    text = msg_in.MessageText.strip()
    
    if sender_id == receiver_id:
        raise HTTPException(status_code=400, detail="You cannot send direct messages to yourself.")
        
    # Check receiver existence
    receiver = db.query(User).filter(User.Id == receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Recipient user not found.")
        
    if not text:
        raise HTTPException(status_code=400, detail="Message text cannot be empty.")
        
    # Proactive moderation
    verdict = predict_comment(text)
    moderation_status = verdict["moderation_status"] # 'Approved' or 'Blocked'
    
    # Save message in DB
    new_msg = Message(
        SenderId=sender_id,
        ReceiverId=receiver_id,
        MessageText=text,
        ModerationStatus=moderation_status
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    
    # Save logs
    result_log = PredictionResult(
        ContentId=new_msg.Id,
        ContentType='message',
        Classification=verdict["classification"],
        ConfidenceScore=verdict["confidence_score"],
        ModerationStatus=moderation_status
    )
    db.add(result_log)
    db.commit()
    
    if moderation_status == 'Blocked':
        return {
            "moderation_status": "Blocked",
            "message": "Warning: Harmful content detected. Your message could not be sent because it violates platform safety guidelines.",
            "verdict": verdict,
            "message_id": new_msg.Id
        }
        
    return {
        "moderation_status": "Approved",
        "message": {
            "Id": new_msg.Id,
            "SenderId": new_msg.SenderId,
            "SenderName": current_actor["name"],
            "ReceiverId": new_msg.ReceiverId,
            "ReceiverName": receiver.Username,
            "MessageText": new_msg.MessageText,
            "ModerationStatus": new_msg.ModerationStatus,
            "Timestamp": new_msg.Timestamp
        }
    }
