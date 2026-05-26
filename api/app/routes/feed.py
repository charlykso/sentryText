from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Post, Comment, User, PredictionResult, PostReaction, CommentReaction
from app.schemas import PostCreate, PostResponse, CommentCreate, CommentResponse
from app.routes.auth import get_current_user
from app.ml_engine.classifier import predict_comment

router = APIRouter(prefix="/feed", tags=["Social Feed"])

@router.get("/posts", response_model=List[PostResponse])
def get_posts(db: Session = Depends(get_db), current_actor: dict = Depends(get_current_user)):
    """Fetch all post entries (both Approved and Blocked). Content of blocked items is scrubbed."""
    posts = db.query(Post).filter(Post.ModerationStatus.in_(['Approved', 'Blocked'])).order_by(Post.Timestamp.desc()).all()
    
    response = []
    for post in posts:
        user = db.query(User).filter(User.Id == post.UserId).first()
        username = user.Username if user else "Deleted User"
        
        content = post.PostContent
        if post.ModerationStatus == 'Blocked' and post.UserId != current_actor["user_id"]:
            content = "🚫 This post was blocked by the SentryText proactive safety engine."
            
        likes_count = db.query(PostReaction).filter(PostReaction.PostId == post.Id, PostReaction.Type == 'like').count()
        dislikes_count = db.query(PostReaction).filter(PostReaction.PostId == post.Id, PostReaction.Type == 'dislike').count()
        
        response.append({
            "Id": post.Id,
            "UserId": post.UserId,
            "Username": username,
            "PostContent": content,
            "ModerationStatus": post.ModerationStatus,
            "Likes": likes_count,
            "Dislikes": dislikes_count,
            "Timestamp": post.Timestamp
        })
    return response

@router.post("/posts")
def create_post(post_in: PostCreate, db: Session = Depends(get_db), current_actor: dict = Depends(get_current_user)):
    """
    Creates a new post after proactive cyberbullying screening.
    Consensus rule determines if post content is written as 'Approved' or 'Blocked'.
    """
    user_id = current_actor["user_id"]
    text = post_in.PostContent.strip()
    
    if not text:
        raise HTTPException(status_code=400, detail="Post content cannot be empty.")
        
    # Proactive screening
    verdict = predict_comment(text)
    moderation_status = verdict["moderation_status"] # 'Approved' or 'Blocked'
    
    # Save the post entry
    new_post = Post(
        UserId=user_id,
        PostContent=text,
        ModerationStatus=moderation_status
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    # Save prediction log for admin review
    result_log = PredictionResult(
        ContentId=new_post.Id,
        ContentType='post',
        Classification=verdict["classification"],
        ConfidenceScore=verdict["confidence_score"],
        ModerationStatus=moderation_status
    )
    db.add(result_log)
    db.commit()
    
    if moderation_status == 'Blocked':
        return {
            "moderation_status": "Blocked",
            "message": "Warning: Harmful Content Detected. Please modify your message before posting.",
            "verdict": verdict,
            "post_id": new_post.Id
        }
        
    return {
        "moderation_status": "Approved",
        "post": {
            "Id": new_post.Id,
            "UserId": new_post.UserId,
            "Username": current_actor["name"],
            "PostContent": new_post.PostContent,
            "ModerationStatus": new_post.ModerationStatus,
            "Likes": new_post.Likes,
            "Dislikes": new_post.Dislikes,
            "Timestamp": new_post.Timestamp
        }
    }

@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
def get_comments(post_id: int, db: Session = Depends(get_db), current_actor: dict = Depends(get_current_user)):
    """Fetch comments belonging to a specific post (both Approved and Blocked). Content of blocked items is scrubbed."""
    comments = db.query(Comment).filter(
        Comment.PostId == post_id, 
        Comment.ModerationStatus.in_(['Approved', 'Blocked'])
    ).order_by(Comment.Timestamp.asc()).all()
    
    response = []
    for comment in comments:
        user = db.query(User).filter(User.Id == comment.UserId).first()
        username = user.Username if user else "Deleted User"
        
        content = comment.CommentText
        if comment.ModerationStatus == 'Blocked' and comment.UserId != current_actor["user_id"]:
            content = "🚫 Comment blocked by SentryText."
            
        likes_count = db.query(CommentReaction).filter(CommentReaction.CommentId == comment.Id, CommentReaction.Type == 'like').count()
        dislikes_count = db.query(CommentReaction).filter(CommentReaction.CommentId == comment.Id, CommentReaction.Type == 'dislike').count()
        
        response.append({
            "Id": comment.Id,
            "PostId": comment.PostId,
            "UserId": comment.UserId,
            "Username": username,
            "CommentText": content,
            "ModerationStatus": comment.ModerationStatus,
            "Likes": likes_count,
            "Dislikes": dislikes_count,
            "Timestamp": comment.Timestamp
        })
    return response

@router.post("/posts/{post_id}/comments")
def create_comment(post_id: int, comment_in: CommentCreate, db: Session = Depends(get_db), current_actor: dict = Depends(get_current_user)):
    """
    Creates a new comment on a post after proactive cyberbullying screening.
    Blocked comments are stored in DB to audit history, but excluded from rendering.
    """
    user_id = current_actor["user_id"]
    text = comment_in.CommentText.strip()
    
    # Check post existence
    post = db.query(Post).filter(Post.Id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
        
    if not text:
        raise HTTPException(status_code=400, detail="Comment content cannot be empty.")
        
    # Proactive screening
    verdict = predict_comment(text)
    moderation_status = verdict["moderation_status"] # 'Approved' or 'Blocked'
    
    # Save the comment
    new_comment = Comment(
        PostId=post_id,
        UserId=user_id,
        CommentText=text,
        ModerationStatus=moderation_status
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    # Save telemetry prediction result log
    result_log = PredictionResult(
        ContentId=new_comment.Id,
        ContentType='comment',
        Classification=verdict["classification"],
        ConfidenceScore=verdict["confidence_score"],
        ModerationStatus=moderation_status
    )
    db.add(result_log)
    db.commit()
    
    if moderation_status == 'Blocked':
        return {
            "moderation_status": "Blocked",
            "message": "Warning: Harmful Comment Detected. Please modify your comment before posting.",
            "verdict": verdict,
            "comment_id": new_comment.Id
        }
        
    return {
        "moderation_status": "Approved",
        "comment": {
            "Id": new_comment.Id,
            "PostId": new_comment.PostId,
            "UserId": new_comment.UserId,
            "Username": current_actor["name"],
            "CommentText": new_comment.CommentText,
            "ModerationStatus": new_comment.ModerationStatus,
            "Likes": 0,
            "Dislikes": 0,
            "Timestamp": new_comment.Timestamp
        }
    }

@router.get("/safety-history")
def get_user_safety_history(db: Session = Depends(get_db), current_actor: dict = Depends(get_current_user)):
    """
    Fetch the historical prediction logs (violations/blocks) triggered by the current user.
    Enables the Personal Safety Center to show them which comments/posts were flagged.
    """
    user_id = current_actor["user_id"]
    
    # 1. Fetch user's post IDs
    user_posts = db.query(Post.Id).filter(Post.UserId == user_id).all()
    post_ids = [p[0] for p in user_posts]
    
    # 2. Fetch user's comment IDs
    user_comments = db.query(Comment.Id).filter(Comment.UserId == user_id).all()
    comment_ids = [c[0] for c in user_comments]
    
    # 3. Fetch user's sent message IDs
    user_messages = db.query(Message.Id).filter(Message.SenderId == user_id).all()
    message_ids = [m[0] for m in user_messages]
    
    # Query PredictionResult where ContentId matches user content
    logs = []
    
    # Post logs
    if post_ids:
        post_logs = db.query(PredictionResult).filter(
            PredictionResult.ContentType == 'post',
            PredictionResult.ContentId.in_(post_ids)
        ).all()
        logs.extend(post_logs)
        
    # Comment logs
    if comment_ids:
        comment_logs = db.query(PredictionResult).filter(
            PredictionResult.ContentType == 'comment',
            PredictionResult.ContentId.in_(comment_ids)
        ).all()
        logs.extend(comment_logs)
        
    # Message logs
    if message_ids:
        message_logs = db.query(PredictionResult).filter(
            PredictionResult.ContentType == 'message',
            PredictionResult.ContentId.in_(message_ids)
        ).all()
        logs.extend(message_logs)
        
    # Sort logs by timestamp descending
    logs.sort(key=lambda x: x.Timestamp, reverse=True)
    
    response = []
    for log in logs:
        raw_text = "[Deleted or Unreachable]"
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
            "ContentType": log.ContentType,
            "RawText": raw_text,
            "Classification": log.Classification,
            "ConfidenceScore": log.ConfidenceScore,
            "ModerationStatus": log.ModerationStatus,
            "Timestamp": log.Timestamp
        })
        
    return response

@router.post("/posts/{post_id}/like")
def like_post(post_id: int, db: Session = Depends(get_db), current_actor: dict = Depends(get_current_user)):
    """Toggle user post reaction 'like'."""
    user_id = current_actor["user_id"]
    post = db.query(Post).filter(Post.Id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
        
    # Check for existing reaction
    existing = db.query(PostReaction).filter(
        PostReaction.PostId == post_id,
        PostReaction.UserId == user_id
    ).first()
    
    if existing:
        if existing.Type == 'like':
            db.delete(existing)
        else:
            existing.Type = 'like'
    else:
        new_reaction = PostReaction(UserId=user_id, PostId=post_id, Type='like')
        db.add(new_reaction)
        
    db.commit()
    
    # Recalculate counts
    likes_count = db.query(PostReaction).filter(PostReaction.PostId == post_id, PostReaction.Type == 'like').count()
    dislikes_count = db.query(PostReaction).filter(PostReaction.PostId == post_id, PostReaction.Type == 'dislike').count()
    
    return {"status": "success", "likes": likes_count, "dislikes": dislikes_count}

@router.post("/posts/{post_id}/dislike")
def dislike_post(post_id: int, db: Session = Depends(get_db), current_actor: dict = Depends(get_current_user)):
    """Toggle user post reaction 'dislike'."""
    user_id = current_actor["user_id"]
    post = db.query(Post).filter(Post.Id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
        
    # Check for existing reaction
    existing = db.query(PostReaction).filter(
        PostReaction.PostId == post_id,
        PostReaction.UserId == user_id
    ).first()
    
    if existing:
        if existing.Type == 'dislike':
            db.delete(existing)
        else:
            existing.Type = 'dislike'
    else:
        new_reaction = PostReaction(UserId=user_id, PostId=post_id, Type='dislike')
        db.add(new_reaction)
        
    db.commit()
    
    # Recalculate counts
    likes_count = db.query(PostReaction).filter(PostReaction.PostId == post_id, PostReaction.Type == 'like').count()
    dislikes_count = db.query(PostReaction).filter(PostReaction.PostId == post_id, PostReaction.Type == 'dislike').count()
    
    return {"status": "success", "likes": likes_count, "dislikes": dislikes_count}

@router.post("/comments/{comment_id}/like")
def like_comment(comment_id: int, db: Session = Depends(get_db), current_actor: dict = Depends(get_current_user)):
    """Toggle user comment reaction 'like'."""
    user_id = current_actor["user_id"]
    comment = db.query(Comment).filter(Comment.Id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
        
    # Check for existing reaction
    existing = db.query(CommentReaction).filter(
        CommentReaction.CommentId == comment_id,
        CommentReaction.UserId == user_id
    ).first()
    
    if existing:
        if existing.Type == 'like':
            db.delete(existing)
        else:
            existing.Type = 'like'
    else:
        new_reaction = CommentReaction(UserId=user_id, CommentId=comment_id, Type='like')
        db.add(new_reaction)
        
    db.commit()
    
    # Recalculate counts
    likes_count = db.query(CommentReaction).filter(CommentReaction.CommentId == comment_id, CommentReaction.Type == 'like').count()
    dislikes_count = db.query(CommentReaction).filter(CommentReaction.CommentId == comment_id, CommentReaction.Type == 'dislike').count()
    
    return {"status": "success", "likes": likes_count, "dislikes": dislikes_count}

@router.post("/comments/{comment_id}/dislike")
def dislike_comment(comment_id: int, db: Session = Depends(get_db), current_actor: dict = Depends(get_current_user)):
    """Toggle user comment reaction 'dislike'."""
    user_id = current_actor["user_id"]
    comment = db.query(Comment).filter(Comment.Id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
        
    # Check for existing reaction
    existing = db.query(CommentReaction).filter(
        CommentReaction.CommentId == comment_id,
        CommentReaction.UserId == user_id
    ).first()
    
    if existing:
        if existing.Type == 'dislike':
            db.delete(existing)
        else:
            existing.Type = 'dislike'
    else:
        new_reaction = CommentReaction(UserId=user_id, CommentId=comment_id, Type='dislike')
        db.add(new_reaction)
        
    db.commit()
    
    # Recalculate counts
    likes_count = db.query(CommentReaction).filter(CommentReaction.CommentId == comment_id, CommentReaction.Type == 'like').count()
    dislikes_count = db.query(CommentReaction).filter(CommentReaction.CommentId == comment_id, CommentReaction.Type == 'dislike').count()
    
    return {"status": "success", "likes": likes_count, "dislikes": dislikes_count}

@router.put("/posts/{post_id}")
def update_post(post_id: int, post_in: PostCreate, db: Session = Depends(get_db), current_actor: dict = Depends(get_current_user)):
    """Update a post. Requires ownership and runs proactive screening."""
    user_id = current_actor["user_id"]
    post = db.query(Post).filter(Post.Id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    if post.UserId != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to edit this post.")
        
    text = post_in.PostContent.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Post content cannot be empty.")
        
    # Proactive screening
    verdict = predict_comment(text)
    moderation_status = verdict["moderation_status"]
    
    post.PostContent = text
    post.ModerationStatus = moderation_status
    db.commit()
    db.refresh(post)
    
    # Save prediction result log
    result_log = PredictionResult(
        ContentId=post.Id,
        ContentType='post',
        Classification=verdict["classification"],
        ConfidenceScore=verdict["confidence_score"],
        ModerationStatus=moderation_status
    )
    db.add(result_log)
    db.commit()
    
    if moderation_status == 'Blocked':
        return {
            "moderation_status": "Blocked",
            "message": "Warning: Harmful Content Detected. Please modify your message before posting.",
            "verdict": verdict,
            "post_id": post.Id
        }
        
    likes_count = db.query(PostReaction).filter(PostReaction.PostId == post.Id, PostReaction.Type == 'like').count()
    dislikes_count = db.query(PostReaction).filter(PostReaction.PostId == post.Id, PostReaction.Type == 'dislike').count()
    
    return {
        "moderation_status": "Approved",
        "post": {
            "Id": post.Id,
            "UserId": post.UserId,
            "Username": current_actor["name"],
            "PostContent": post.PostContent,
            "ModerationStatus": post.ModerationStatus,
            "Likes": likes_count,
            "Dislikes": dislikes_count,
            "Timestamp": post.Timestamp
        }
    }

@router.delete("/posts/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db), current_actor: dict = Depends(get_current_user)):
    """Delete a post. Requires ownership."""
    user_id = current_actor["user_id"]
    post = db.query(Post).filter(Post.Id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    if post.UserId != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this post.")
        
    db.delete(post)
    db.commit()
    return {"status": "success", "message": "Post successfully deleted."}

@router.put("/comments/{comment_id}")
def update_comment(comment_id: int, comment_in: CommentCreate, db: Session = Depends(get_db), current_actor: dict = Depends(get_current_user)):
    """Update a comment. Requires ownership and runs proactive screening."""
    user_id = current_actor["user_id"]
    comment = db.query(Comment).filter(Comment.Id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
    if comment.UserId != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to edit this comment.")
        
    text = comment_in.CommentText.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Comment content cannot be empty.")
        
    # Proactive screening
    verdict = predict_comment(text)
    moderation_status = verdict["moderation_status"]
    
    comment.CommentText = text
    comment.ModerationStatus = moderation_status
    db.commit()
    db.refresh(comment)
    
    # Save prediction result log
    result_log = PredictionResult(
        ContentId=comment.Id,
        ContentType='comment',
        Classification=verdict["classification"],
        ConfidenceScore=verdict["confidence_score"],
        ModerationStatus=moderation_status
    )
    db.add(result_log)
    db.commit()
    
    if moderation_status == 'Blocked':
        return {
            "moderation_status": "Blocked",
            "message": "Warning: Harmful Comment Detected. Please modify your comment before posting.",
            "verdict": verdict,
            "comment_id": comment.Id
        }
        
    likes_count = db.query(CommentReaction).filter(CommentReaction.CommentId == comment.Id, CommentReaction.Type == 'like').count()
    dislikes_count = db.query(CommentReaction).filter(CommentReaction.CommentId == comment.Id, CommentReaction.Type == 'dislike').count()
    
    return {
        "moderation_status": "Approved",
        "comment": {
            "Id": comment.Id,
            "PostId": comment.PostId,
            "UserId": comment.UserId,
            "Username": current_actor["name"],
            "CommentText": comment.CommentText,
            "ModerationStatus": comment.ModerationStatus,
            "Likes": likes_count,
            "Dislikes": dislikes_count,
            "Timestamp": comment.Timestamp
        }
    }

@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db), current_actor: dict = Depends(get_current_user)):
    """Delete a comment. Requires ownership."""
    user_id = current_actor["user_id"]
    comment = db.query(Comment).filter(Comment.Id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
    if comment.UserId != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this comment.")
        
    db.delete(comment)
    db.commit()
    return {"status": "success", "message": "Comment successfully deleted."}


