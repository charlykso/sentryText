from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

class UserCreate(BaseModel):
    Username: str
    Email: EmailStr
    Password: str
    Gender: Optional[str] = None

class UserLogin(BaseModel):
    Email: EmailStr
    Password: str

class UserResponse(BaseModel):
    Id: int
    Username: str
    Email: str
    Gender: Optional[str]
    DateRegistered: datetime

    class Config:
        from_attributes = True

class PostCreate(BaseModel):
    PostContent: str

class PostResponse(BaseModel):
    Id: int
    UserId: int
    Username: str
    PostContent: str
    ModerationStatus: str
    Likes: int
    Dislikes: int
    Timestamp: datetime

    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    CommentText: str

class CommentResponse(BaseModel):
    Id: int
    PostId: int
    UserId: int
    Username: str
    CommentText: str
    ModerationStatus: str
    Likes: int
    Dislikes: int
    Timestamp: datetime

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    ReceiverId: int
    MessageText: str

class MessageResponse(BaseModel):
    Id: int
    SenderId: int
    SenderName: str
    ReceiverId: int
    ReceiverName: str
    MessageText: str
    ModerationStatus: str
    Timestamp: datetime

    class Config:
        from_attributes = True

class AuditorRequest(BaseModel):
    Text: str

class AuditorResponse(BaseModel):
    classification: str
    confidence_score: float
    moderation_status: str
    lr_classification: str
    lr_confidence: float
    svm_classification: str
    svm_confidence: float
    is_fallback: bool

class AdminCreate(BaseModel):
    AdminName: str
    Email: EmailStr
    Password: str

class AdminLogin(BaseModel):
    Email: EmailStr
    Password: str

class AdminResponse(BaseModel):
    Id: int
    AdminName: str
    Email: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    name: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None

class AuditLogEntry(BaseModel):
    Id: int
    ContentId: int
    ContentType: str
    RawText: str
    Classification: str
    ConfidenceScore: float
    ModerationStatus: str
    Timestamp: datetime

class AdminTelemetry(BaseModel):
    total_users: int
    total_posts: int
    total_violations: int
    total_approved: int

class AdminUserResponse(BaseModel):
    Id: int
    Username: str
    Email: str
    Gender: Optional[str]
    DateRegistered: datetime
    PostCount: int
    CommentCount: int
    ViolationCount: int

    class Config:
        from_attributes = True
