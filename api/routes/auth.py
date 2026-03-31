from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from api.utils.database import get_db
from api.utils.user_models import UserDB, UserRole, SubscriptionTier
from api.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from api.config import settings
from api.utils.audit_service import audit_service
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
import os
import json

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    referral_code: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    telegram_chat_id: Optional[str] = None
    telegram_token: Optional[str] = None
    whatsapp_number: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    subscription: str
    credits: Optional[int] = 0
    referral_code: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_token: Optional[str] = None
    whatsapp_number: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/register", response_model=UserResponse)
async def register(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    from services.payment.credit_service import credit_service

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
        subscription=SubscriptionTier.PREMIUM
        if role == UserRole.ADMIN
        else SubscriptionTier.FREE,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Initial credits & Referral
    credit_service.add_credits(
        new_user.id, 100 if role == UserRole.ADMIN else 10, "earned", "Welcome bonus"
    )

    if user.referral_code:
        credit_service.apply_referral_code(new_user.id, user.referral_code)

    audit_service.log(
        action="USER_REGISTER",
        user_id=new_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        db=db,
    )

    return new_user


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(UserDB).filter(UserDB.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username, "role": user.role})

    audit_service.log(
        action="USER_LOGIN",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        db=db,
    )

    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
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
    from services.payment.credit_service import credit_service

    # Enrich user response with monetization data
    response = UserResponse.model_validate(current_user)
    try:
        response.credits = credit_service.get_balance(current_user.id)
        response.referral_code = credit_service.get_referral_code(current_user.id)
    except Exception:
        response.credits = 0
        response.referral_code = None
    return response


@router.patch("/me", response_model=UserResponse)
async def update_me(
    user_update: UserUpdate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_update.email:
        current_user.email = user_update.email
    if user_update.telegram_chat_id is not None:
        current_user.telegram_chat_id = user_update.telegram_chat_id
    if user_update.telegram_token is not None:
        current_user.telegram_token = user_update.telegram_token
        # Trigger OpenClaw Bot Refresh
        try:
            import requests

            requests.post(
                f"http://openclaw:3001/refresh-bot/{current_user.id}", timeout=2
            )
        except Exception as e:
            print(f"Failed to notify OpenClaw: {e}")

    if user_update.whatsapp_number is not None:
        current_user.whatsapp_number = user_update.whatsapp_number

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change user password"""
    if not verify_password(
        password_change.current_password, current_user.hashed_password
    ):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.hashed_password = get_password_hash(password_change.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@router.post("/me/upgrade-subscription")
async def upgrade_subscription(
    request: Request,
    tier: str,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upgrade user subscription tier.
    SECURITY: This endpoint is restricted to ADMIN users only. For regular users, use the billing flow.
    """
    # Restrict to admin only to prevent unauthorized upgrades
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Direct tier upgrades are admin-only. Please use the billing checkout flow for upgrades.",
        )

    valid_tiers = ["free", "basic", "premium"]
    if tier.lower() not in valid_tiers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tier. Must be one of: {', '.join(valid_tiers)}",
        )

    current_user.subscription = tier.lower()
    db.commit()
    db.refresh(current_user)

    audit_service.log(
        action="SUBSCRIPTION_CHANGE",
        user_id=current_user.id,
        resource_type="USER",
        resource_id=str(current_user.id),
        details={"tier": tier.lower()},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        db=db,
    )

    return {
        "message": f"Subscription upgraded to {tier}",
        "subscription": current_user.subscription,
    }


@router.get("/verify-telegram/{telegram_id}", response_model=UserResponse)
async def verify_telegram(telegram_id: str, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.telegram_chat_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/verify-comms")
async def verify_comms(
    platform: str,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Sends a test verification message to the user's configured communication platform.
    """
    try:
        import requests

        message = f"🦅 *Viral Forge Identity Verification*\n\nYour connection to the Nexus is active. Comms for user *{current_user.username}* have been verified at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC."

        target_id = None
        if platform.lower() == "telegram":
            target_id = current_user.telegram_chat_id
        elif platform.lower() == "whatsapp":
            target_id = current_user.whatsapp_number
            if target_id and not target_id.startswith("whatsapp:"):
                target_id = f"whatsapp:{target_id}"

        if not target_id:
            raise HTTPException(
                status_code=400,
                detail=f"No configuration found for platform: {platform}",
            )

        # Call OpenClaw broadcast endpoint
        openclaw_url = os.getenv("OPENCLAW_URL", "http://openclaw:3001")
        response = requests.post(
            f"{openclaw_url}/broadcast",
            json={
                "user_ids": [target_id],
                "message": message,
                "platform_hint": platform.lower(),
            },
            timeout=5,
        )

        if response.status_code == 200:
            return {"status": "success", "message": f"Verification sent to {platform}"}
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send verification via OpenClaw: {response.text}",
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal error during verification: {str(e)}"
        )


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
async def verify_telegram_internal(
    user_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Internal-only endpoint for OpenClaw to fetch user tokens.
    Requires authentication (internal API token recommended).
    """
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/internal/users-with-bots", response_model=List[UserResponse])
async def get_internal_users_with_bots(
    current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Returns all users who have configured a private Telegram bot token.
    Used by OpenClaw on startup.
    Requires authentication (internal API token recommended).
    """
    users = (
        db.query(UserDB)
        .filter(UserDB.telegram_token.isnot(None), UserDB.telegram_token != "")
        .all()
    )
    return users


@router.get("/callback/google")
async def google_auth_callback(
    request: Request, code: str = None, state: str = None, db: Session = Depends(get_db)
):
    """
    Google OAuth callback endpoint.
    Handles the redirect from Google after user authentication.
    """
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")

    try:
        # Exchange authorization code for tokens
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                }
            },
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
            ],
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
        )

        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Verify ID token
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, requests.Request(), settings.GOOGLE_CLIENT_ID
        )

        # Extract user info
        email = id_info.get("email")
        username = id_info.get("name", email.split("@")[0] if email else "google_user")

        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by Google")

        # Check if user already exists
        user = db.query(UserDB).filter(UserDB.email == email).first()

        if not user:
            # Create new user
            role = UserRole.ADMIN if db.query(UserDB).count() == 0 else UserRole.USER
            subscription = (
                SubscriptionTier.PREMIUM
                if role == UserRole.ADMIN
                else SubscriptionTier.FREE
            )

            user = UserDB(
                username=username,
                email=email,
                hashed_password=get_password_hash(
                    secrets.token_urlsafe(32)
                ),  # Random password for OAuth users
                role=role,
                subscription=subscription,
                is_google_oauth=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Give welcome credits
            from services.payment.credit_service import credit_service

            credit_service.add_credits(
                user.id,
                100 if role == UserRole.ADMIN else 10,
                "earned",
                "Welcome bonus",
            )

        # Create access token
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role}
        )

        # Redirect to frontend with token
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?token={access_token}&provider=google",
            status_code=302,
        )

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Google authentication failed: {str(e)}"
        )
