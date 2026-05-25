from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app.models import Admin
from app.config import DEFAULT_ADMIN_NAME, DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD
from app.routes.auth import hash_password
from app.ml_engine.classifier import load_models

# Import routers
from app.routes import auth, feed, chat, auditor, admin

app = FastAPI(
    title="SentryText API",
    description="Proactive Machine Learning-Based Cyberbullying Detection & Moderation API Engine",
    version="1.0"
)

# CORS middleware to allow SPA connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(feed.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(auditor.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

@app.on_event("startup")
def on_startup():
    # 1. Create DB tables
    print("SentryText: Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Run manual migrations to drop Likes/Dislikes cached columns from posts/comments tables
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE posts DROP COLUMN Likes"))
            print("SentryText Migration: Dropped Likes column from posts table.")
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE posts DROP COLUMN Dislikes"))
            print("SentryText Migration: Dropped Dislikes column from posts table.")
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE comments DROP COLUMN Likes"))
            print("SentryText Migration: Dropped Likes column from comments table.")
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE comments DROP COLUMN Dislikes"))
            print("SentryText Migration: Dropped Dislikes column from comments table.")
        except Exception:
            pass
    
    # 2. Seed default admin account if table is empty
    db = next(get_db())
    try:
        admin_exists = db.query(Admin).first()
        if not admin_exists:
            print(f"SentryText: Seeding default administrator account: {DEFAULT_ADMIN_EMAIL}")
            hashed_pwd = hash_password(DEFAULT_ADMIN_PASSWORD)
            default_admin = Admin(
                AdminName=DEFAULT_ADMIN_NAME,
                Email=DEFAULT_ADMIN_EMAIL,
                Password=hashed_pwd
            )
            db.add(default_admin)
            db.commit()
    except Exception as e:
        print(f"SentryText DB Error seeding admin: {e}")
    finally:
        db.close()
        
    # 3. Load machine learning models
    print("SentryText: Loading ML models at startup...")
    load_models()

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "SentryText Cyberbullying Detection & Prevention API Server",
        "documentation": "/docs"
    }
