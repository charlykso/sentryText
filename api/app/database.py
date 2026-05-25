import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "sentryText_db")

# Connection strings
MYSQL_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
SQLITE_URL = "sqlite:///./sentrytext_sqlite.db"

engine = None
SessionLocal = None
Base = declarative_base()

# Try to connect to MySQL; fall back to SQLite if MySQL is unavailable
try:
    # Test connection with a short timeout
    test_engine = create_engine(MYSQL_URL, connect_args={"connect_timeout": 3} if "mysql" in MYSQL_URL else {})
    conn = test_engine.connect()
    conn.close()
    
    # If connection succeeded, create active engine
    engine = create_engine(MYSQL_URL, pool_pre_ping=True)
    print(f"Database Connection: Successfully connected to local MySQL database: '{DB_NAME}'")
except Exception as e:
    print(f"Database Connection Warning: Could not connect to MySQL at {DB_HOST}:{DB_PORT}. Error: {e}")
    print("Database Connection: Falling back to local SQLite database: 'sentrytext_sqlite.db'")
    engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False} if "sqlite" in SQLITE_URL else {})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
