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
from typing import Optional, List
from api.config import settings

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
    whatsapp_number: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

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
    # 1. Check for Internal Master Token
    if settings.INTERNAL_API_TOKEN and token == settings.INTERNAL_API_TOKEN:
        # Return the admin user for operations triggered by internal services
        admin = db.query(UserDB).filter(UserDB.role == UserRole.ADMIN).first()
        if admin:
            return admin
        
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
            
    if user_update.whatsapp_number is not None:
        current_user.whatsapp_number = user_update.whatsapp_number
            
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/me/change-password")
async def change_password(password_change: PasswordChange, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    """Change user password"""
    if not verify_password(password_change.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    current_user.hashed_password = get_password_hash(password_change.new_password)
    db.commit()
    return {"message": "Password changed successfully"}

@router.post("/me/upgrade-subscription")
async def upgrade_subscription(tier: str, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    """Upgrade user subscription tier"""
    valid_tiers = ["free", "basic", "premium"]
    if tier.lower() not in valid_tiers:
        raise HTTPException(status_code=400, detail=f"Invalid tier. Must be one of: {', '.join(valid_tiers)}")
    
    current_user.subscription = tier.lower()
    db.commit()
    db.refresh(current_user)
    return {"message": f"Subscription upgraded to {tier}", "subscription": current_user.subscription}

@router.get("/verify-telegram/{telegram_id}", response_model=UserResponse)
async def verify_telegram(telegram_id: str, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.telegram_chat_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/verify-whatsapp/{whatsapp_id}", response_model=UserResponse)
async def verify_whatsapp(whatsapp_id: str, db: Session = Depends(get_db)):
    """
    Resolves a user by their WhatsApp phone number (identifier).
    """
    user = db.query(UserDB).filter(UserDB.whatsapp_number == whatsapp_id).first()
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

@router.get("/internal/users-with-bots", response_model=List[UserResponse])
async def get_internal_users_with_bots(db: Session = Depends(get_db)):
    """
    Returns all users who have configured a private Telegram bot token.
    Used by OpenClaw on startup.
    """
    users = db.query(UserDB).filter(UserDB.telegram_token.isnot(None), UserDB.telegram_token != "").all()
    return users
