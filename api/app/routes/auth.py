import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Admin
from app.schemas import UserCreate, UserLogin, AdminLogin
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["Authentication"])

def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict) -> str:
    """Generates a signed JWT with expiration timestamp."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    FastAPI security dependency. Decodes and verifies incoming HttpOnly cookie.
    Returns the actor payload: user_id, email, name, and role.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or not authenticated. Please log in."
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        user_id: int = payload.get("user_id")
        
        if email is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token.")
            
        if role == "admin":
            admin = db.query(Admin).filter(Admin.Id == user_id).first()
            if not admin:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin account not found")
            return {"user_id": user_id, "email": email, "role": "admin", "name": admin.AdminName}
        else:
            user = db.query(User).filter(User.Id == user_id).first()
            if not user:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account not found")
            return {"user_id": user_id, "email": email, "role": "user", "name": user.Username}
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid token.",
        )

def get_current_admin(current_actor: dict = Depends(get_current_user)):
    """Enforces administrator role check on protected endpoints."""
    if current_actor["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Admin privileges required."
        )
    return current_actor

@router.post("/register")
def register_user(user_in: UserCreate, response: Response, db: Session = Depends(get_db)):
    # Check duplicate username
    existing_username = db.query(User).filter(User.Username == user_in.Username).first()
    if existing_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is already taken.")
        
    # Check duplicate email
    existing_email = db.query(User).filter(User.Email == user_in.Email).first()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered.")
        
    hashed_pwd = hash_password(user_in.Password)
    new_user = User(
        Username=user_in.Username,
        Email=user_in.Email,
        Password=hashed_pwd,
        Gender=user_in.Gender
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate token and set in HttpOnly cookie
    token_data = {"sub": new_user.Email, "role": "user", "user_id": new_user.Id}
    access_token = create_access_token(token_data)
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False  # Set to True in production (HTTPS)
    )
    
    return {
        "status": "success",
        "role": "user",
        "name": new_user.Username
    }

@router.post("/login")
def login_user(login_in: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.Email == login_in.Email).first()
    if not user or not verify_password(login_in.Password, user.Password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or password.")
        
    token_data = {"sub": user.Email, "role": "user", "user_id": user.Id}
    access_token = create_access_token(token_data)
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False
    )
    
    return {
        "status": "success",
        "role": "user",
        "name": user.Username
    }

@router.post("/admin/login")
def login_admin(login_in: AdminLogin, response: Response, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.Email == login_in.Email).first()
    if not admin or not verify_password(login_in.Password, admin.Password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid admin credentials.")
        
    token_data = {"sub": admin.Email, "role": "admin", "user_id": admin.Id}
    access_token = create_access_token(token_data)
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False
    )
    
    return {
        "status": "success",
        "role": "admin",
        "name": admin.AdminName
    }

@router.get("/me")
def get_me(current_actor: dict = Depends(get_current_user)):
    """Returns details of the currently logged-in actor from the secure session cookie."""
    return {
        "id": current_actor["user_id"],
        "email": current_actor["email"],
        "role": current_actor["role"],
        "name": current_actor["name"]
    }

@router.post("/logout")
def logout_user(response: Response):
    """Deletes the HttpOnly session cookie, logging out the actor."""
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    return {"status": "success"}
