from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = 'users'
    
    Id = Column(Integer, primary_key=True, autoincrement=True)
    Username = Column(String(50), nullable=False, unique=True, index=True)
    Email = Column(String(100), nullable=False, unique=True, index=True)
    Password = Column(String(255), nullable=False)
    Gender = Column(String(10), nullable=True)
    DateRegistered = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")
    sent_messages = relationship("Message", foreign_keys="[Message.SenderId]", back_populates="sender", cascade="all, delete-orphan")
    received_messages = relationship("Message", foreign_keys="[Message.ReceiverId]", back_populates="receiver", cascade="all, delete-orphan")

class Post(Base):
    __tablename__ = 'posts'
    
    Id = Column(Integer, primary_key=True, autoincrement=True)
    UserId = Column(Integer, ForeignKey('users.Id', ondelete='CASCADE'), nullable=False)
    PostContent = Column(Text, nullable=False)
    ModerationStatus = Column(String(20), nullable=False, default='Pending') # Approved, Blocked, Flagged
    Timestamp = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")

class Comment(Base):
    __tablename__ = 'comments'
    
    Id = Column(Integer, primary_key=True, autoincrement=True)
    PostId = Column(Integer, ForeignKey('posts.Id', ondelete='CASCADE'), nullable=False)
    UserId = Column(Integer, ForeignKey('users.Id', ondelete='CASCADE'), nullable=False)
    CommentText = Column(Text, nullable=False)
    ModerationStatus = Column(String(20), nullable=False, default='Pending') # Approved, Blocked, Flagged
    Timestamp = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    post = relationship("Post", back_populates="comments")
    author = relationship("User", back_populates="comments")

class Message(Base):
    __tablename__ = 'messages'
    
    Id = Column(Integer, primary_key=True, autoincrement=True)
    SenderId = Column(Integer, ForeignKey('users.Id', ondelete='CASCADE'), nullable=False)
    ReceiverId = Column(Integer, ForeignKey('users.Id', ondelete='CASCADE'), nullable=False)
    MessageText = Column(Text, nullable=False)
    ModerationStatus = Column(String(20), nullable=False, default='Approved') # Approved, Blocked, Flagged
    Timestamp = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    sender = relationship("User", foreign_keys=[SenderId], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[ReceiverId], back_populates="received_messages")

class PredictionResult(Base):
    __tablename__ = 'prediction_results'
    
    Id = Column(Integer, primary_key=True, autoincrement=True)
    ContentId = Column(Integer, nullable=False) # References posts(Id), comments(Id), or messages(Id)
    ContentType = Column(String(20), nullable=False) # 'post', 'comment', or 'message'
    Classification = Column(String(20), nullable=False) # Harmful, Non-Harmful
    ConfidenceScore = Column(Float, nullable=False) # Certainty probability percentage (0.0 - 100.0)
    ModerationStatus = Column(String(20), nullable=False) # Approved, Blocked, Flagged
    Timestamp = Column(DateTime, nullable=False, default=func.now())

class Admin(Base):
    __tablename__ = 'admin'
    
    Id = Column(Integer, primary_key=True, autoincrement=True)
    AdminName = Column(String(50), nullable=False)
    Email = Column(String(100), nullable=False, unique=True, index=True)
    Password = Column(String(255), nullable=False)

class PostReaction(Base):
    __tablename__ = 'post_reactions'
    
    Id = Column(Integer, primary_key=True, autoincrement=True)
    UserId = Column(Integer, ForeignKey('users.Id', ondelete='CASCADE'), nullable=False)
    PostId = Column(Integer, ForeignKey('posts.Id', ondelete='CASCADE'), nullable=False)
    Type = Column(String(10), nullable=False) # 'like' or 'dislike'
    Timestamp = Column(DateTime, nullable=False, default=func.now())
    
    __table_args__ = (
        UniqueConstraint('UserId', 'PostId', name='unique_user_post'),
    )

class CommentReaction(Base):
    __tablename__ = 'comment_reactions'
    
    Id = Column(Integer, primary_key=True, autoincrement=True)
    UserId = Column(Integer, ForeignKey('users.Id', ondelete='CASCADE'), nullable=False)
    CommentId = Column(Integer, ForeignKey('comments.Id', ondelete='CASCADE'), nullable=False)
    Type = Column(String(10), nullable=False) # 'like' or 'dislike'
    Timestamp = Column(DateTime, nullable=False, default=func.now())
    
    __table_args__ = (
        UniqueConstraint('UserId', 'CommentId', name='unique_user_comment'),
    )
