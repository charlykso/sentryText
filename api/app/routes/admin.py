from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, Post, Comment, Message, PredictionResult
from app.schemas import AdminTelemetry, AuditLogEntry, AdminUserResponse
from app.routes.auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

@router.get("/telemetry", response_model=AdminTelemetry)
def get_telemetry(db: Session = Depends(get_db), current_admin: dict = Depends(get_current_admin)):
    """Fetch global platform statistics for dashboard counters."""
    total_users = db.query(User).count()
    total_posts = db.query(Post).count()
    
    # Aggregated results from prediction logs
    total_violations = db.query(PredictionResult).filter(PredictionResult.ModerationStatus == 'Blocked').count()
    total_approved = db.query(PredictionResult).filter(PredictionResult.ModerationStatus == 'Approved').count()
    
    return {
        "total_users": total_users,
        "total_posts": total_posts,
        "total_violations": total_violations,
        "total_approved": total_approved
    }

@router.get("/logs", response_model=List[AuditLogEntry])
def get_audit_logs(db: Session = Depends(get_db), current_admin: dict = Depends(get_current_admin)):
    """
    Fetch all content moderation logs. Resolves ContentID based on ContentType 
    to retrieve raw text entries for administrative scrutiny.
    """
    logs = db.query(PredictionResult).order_by(PredictionResult.Timestamp.desc()).all()
    
    response = []
    for log in logs:
        raw_text = "[Deleted or Unreachable Content]"
        try:
            if log.ContentType == 'post':
                post = db.query(Post).filter(Post.Id == log.ContentId).first()
                if post:
                    raw_text = post.PostContent
            elif log.ContentType == 'comment':
                comment = db.query(Comment).filter(Comment.Id == log.ContentId).first()
                if comment:
                    raw_text = comment.CommentText
            elif log.ContentType == 'message':
                message = db.query(Message).filter(Message.Id == log.ContentId).first()
                if message:
                    raw_text = message.MessageText
        except Exception:
            pass
            
        response.append({
            "Id": log.Id,
            "ContentId": log.ContentId,
            "ContentType": log.ContentType,
            "RawText": raw_text,
            "Classification": log.Classification,
            "ConfidenceScore": log.ConfidenceScore,
            "ModerationStatus": log.ModerationStatus,
            "Timestamp": log.Timestamp
        })
    return response

@router.get("/users", response_model=List[AdminUserResponse])
def list_users(db: Session = Depends(get_db), current_admin: dict = Depends(get_current_admin)):
    """Fetch list of all registered users with their respective counts and violations."""
    users = db.query(User).all()
    response = []
    
    for u in users:
        post_ids = [p.Id for p in u.posts]
        comment_ids = [c.Id for c in u.comments]
        message_ids = [m.Id for m in u.sent_messages]
        
        post_violations = db.query(PredictionResult).filter(
            PredictionResult.ContentType == 'post',
            PredictionResult.ContentId.in_(post_ids) if post_ids else False,
            PredictionResult.ModerationStatus == 'Blocked'
        ).count() if post_ids else 0

        comment_violations = db.query(PredictionResult).filter(
            PredictionResult.ContentType == 'comment',
            PredictionResult.ContentId.in_(comment_ids) if comment_ids else False,
            PredictionResult.ModerationStatus == 'Blocked'
        ).count() if comment_ids else 0

        message_violations = db.query(PredictionResult).filter(
            PredictionResult.ContentType == 'message',
            PredictionResult.ContentId.in_(message_ids) if message_ids else False,
            PredictionResult.ModerationStatus == 'Blocked'
        ).count() if message_ids else 0
        
        total_violations = post_violations + comment_violations + message_violations
        
        response.append({
            "Id": u.Id,
            "Username": u.Username,
            "Email": u.Email,
            "Gender": u.Gender,
            "DateRegistered": u.DateRegistered,
            "PostCount": len(u.posts),
            "CommentCount": len(u.comments),
            "ViolationCount": total_violations
        })
    return response

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_admin: dict = Depends(get_current_admin)):
    """Delete a user, cascading to purge all posts, comments, and messages associated."""
    user = db.query(User).filter(User.Id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    # We must also clean up the associated prediction results to avoid dangling prediction logs.
    # We retrieve IDs of all content items authored by the user.
    post_ids = [p.Id for p in user.posts]
    comment_ids = [c.Id for c in user.comments]
    message_ids = [m.Id for m in user.sent_messages]
    
    if post_ids:
        db.query(PredictionResult).filter(
            PredictionResult.ContentType == 'post',
            PredictionResult.ContentId.in_(post_ids)
        ).delete(synchronize_session=False)
    if comment_ids:
        db.query(PredictionResult).filter(
            PredictionResult.ContentType == 'comment',
            PredictionResult.ContentId.in_(comment_ids)
        ).delete(synchronize_session=False)
    if message_ids:
        db.query(PredictionResult).filter(
            PredictionResult.ContentType == 'message',
            PredictionResult.ContentId.in_(message_ids)
        ).delete(synchronize_session=False)

    db.delete(user)
    db.commit()
    return {"status": "success", "message": f"User '{user.Username}' and all their content purged."}
