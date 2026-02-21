from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from api.utils.database import get_db
from api.utils.user_models import UserDB, UserRole, SubscriptionTier
from api.utils.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    decode_access_token
)
from pydantic import BaseModel, EmailStr
from typing import Optional

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    telegram_chat_id: Optional[str] = None
    telegram_token: Optional[str] = None

class UserResponse(BaseModel):
    username: str
    email: str
    role: str
    subscription: str
    telegram_chat_id: Optional[str] = None
    telegram_token: Optional[str] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user_name = db.query(UserDB).filter(UserDB.username == user.username).first()
    if db_user_name:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_pwd = get_password_hash(user.password)
    
    # First user becomes admin
    user_count = db.query(UserDB).count()
    role = UserRole.ADMIN if user_count == 0 else UserRole.USER
    
    new_user = UserDB(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pwd,
        role=role,
        subscription=SubscriptionTier.PREMIUM if role == UserRole.ADMIN else SubscriptionTier.FREE
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if user is None:
        raise credentials_exception
    return user

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserDB = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_me(user_update: UserUpdate, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_update.email:
        current_user.email = user_update.email
    if user_update.telegram_chat_id is not None:
        current_user.telegram_chat_id = user_update.telegram_chat_id
    if user_update.telegram_token is not None:
        current_user.telegram_token = user_update.telegram_token
        # Trigger OpenClaw Bot Refresh
        try:
            import requests
            requests.post(f"http://openclaw:3001/refresh-bot/{current_user.id}", timeout=2)
        except Exception as e:
            print(f"Failed to notify OpenClaw: {e}")
            
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/verify-telegram/{telegram_id}", response_model=UserResponse)
async def verify_telegram(telegram_id: str, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.telegram_chat_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/verify-telegram-internal/{user_id}", response_model=UserResponse)
async def verify_telegram_internal(user_id: int, db: Session = Depends(get_db)):
    """
    Internal-only endpoint for OpenClaw to fetch user tokens.
    """
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
