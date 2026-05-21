from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from src.api.utils.database import get_db
from src.api.utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    sign_oauth_state,
    verify_oauth_state,
    get_current_user,
    admin_required,
    oauth2_scheme,
)
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from src.api.config import settings
from src.api.utils.api_responses import (
    success_response,
    ConflictError,
    APIError,
)
from src.api.utils.user_models import UserDB, SubscriptionTier, UserRole
from sqlalchemy import select, func
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
from authlib.integrations.base_client import OAuthError
import secrets
import redis
import redis.asyncio as redis_async
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def create_google_flow():
    """Create a configured Google OAuth flow instance."""
    return Flow.from_client_config(
        client_config={
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_OAUTH_REDIRECT_URI],
            }
        },
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ],
        redirect_uri=settings.GOOGLE_OAUTH_REDIRECT_URI,
    )


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    telegram_chat_id: str | None = None
    telegram_token: str | None = None
    whatsapp_number: str | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    subscription: SubscriptionTier | None = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.api.utils.database import get_db


@router.post("/register")
async def register(user: UserCreate, db=Depends(get_db)):
    # 1. Check for duplicate email
    stmt = select(UserDB).where(UserDB.email == user.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise ConflictError(message="Email already registered", resource_id=user.email)

    # 2. Determine username
    username = user.username or user.email.split("@")[0]

    # 3. Check for duplicate username
    stmt = select(UserDB).where(UserDB.username == username)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        # If auto-generated username exists, append a suffix
        if not user.username:
            import random
            username = f"{username}_{random.randint(100, 999)}"
        else:
            raise ConflictError(message="Username already taken", resource_id=username)

    # 4. Check if this is the first user (for Admin promotion)
    stmt = select(func.count()).select_from(UserDB)
    result = await db.execute(stmt)
    user_count = result.scalar()
    
    role = UserRole.ADMIN if user_count == 0 else UserRole.USER

    # 5. Create user
    hashed_pwd = get_password_hash(user.password)
    new_user = UserDB(
        username=username,
        email=user.email,
        hashed_password=hashed_pwd,
        role=role,
    )
    
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except Exception as e:
        await db.rollback()
        logger.error(f"Registration failure: {e}")
        raise APIError(message="Could not complete registration", status_code=500)

    return success_response(
        data=UserResponse.model_validate(new_user).model_dump(),
        message="Registration successful"
    )


class LoginRequest(BaseModel):
    """Login request supporting both username and email."""
    username: str | None = None
    email: str | None = None
    password: str


@router.post("/login")
async def login(
    request: Request,
    db=Depends(get_db),
):
    # Detect content type and parse accordingly
    content_type = request.headers.get("content-type", "")
    
    if "application/json" in content_type:
        # JSON request from frontend
        try:
            body = await request.json()
            identifier = body.get("username") or body.get("email")
            password = body.get("password")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON body"
            )
    else:
        # Form-encoded request (OAuth2 standard)
        form_data = await request.form()
        identifier = form_data.get("username")
        password = form_data.get("password")
    
    if not identifier or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username/email and password are required"
        )

    # Support login with either username OR email
    stmt = select(UserDB).where(
        (UserDB.email == identifier) | (UserDB.username == identifier)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"[LOGIN] User not found: {identifier}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"[LOGIN] Verifying password for user: {user.email}")
    try:
        password_valid = verify_password(password, user.hashed_password)
    except Exception as e:
        logger.error(f"[LOGIN] Password verification error: {type(e).__name__}: {e}")
        raise
    
    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email})

    return success_response(data={"access_token": access_token, "token_type": "bearer"})


@router.get("/me")
async def get_me(current_user: UserDB = Depends(get_current_user)):
    return success_response(data=UserResponse.model_validate(current_user).model_dump())


@router.get("/google")
async def google_auth():
    flow = create_google_flow()
    authorization_url, state = flow.authorization_url()

    # Sign the state parameter for CSRF protection
    signed_state = sign_oauth_state(state)

    # Append signed state to the authorization URL
    separator = "&" if "?" in authorization_url else "?"
    auth_url_with_state = f"{authorization_url}{separator}state={signed_state}"

    return RedirectResponse(url=auth_url_with_state)


@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    import redis.asyncio as redis_async

    redis_client = redis_async.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        await redis_client.sadd("token_blacklist", token)
    finally:
        await redis_client.close()
    return success_response(data={"message": "Logged out"})


@router.get("/callback/google")
async def google_auth_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    db=Depends(get_db),
):
    """
    Google OAuth callback endpoint.
    Handles the redirect from Google after user authentication.
    """
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")

    if not state:
        raise HTTPException(status_code=400, detail="State parameter missing")

    # Verify the signed state parameter
    original_state = verify_oauth_state(state)
    if not original_state:
        raise HTTPException(
            status_code=400, detail="Invalid or expired state parameter"
        )

    try:
        # Exchange authorization code for tokens
        flow = create_google_flow()

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
        stmt = select(UserDB).where(UserDB.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            # Create new user
            user = UserDB(
                username=username,
                email=email,
                hashed_password=get_password_hash(
                    secrets.token_urlsafe(32)
                ),  # Random password for OAuth users
                google_id=id_info.get("sub"),
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Create access token
        access_token = create_access_token(data={"sub": user.email})

        # Redirect to frontend with token
        dashboard_url = (
            settings.PRODUCTION_DOMAIN.split("/api/v1")[0].rstrip("/")
            or "http://localhost:7202"
        )
        return RedirectResponse(
            url=f"{dashboard_url}/auth/callback?token={access_token}&provider=google",
            status_code=302,
        )

    except (ValueError, HTTPException, OAuthError) as e:
        raise HTTPException(
            status_code=400, detail=f"Google authentication failed: {str(e)}"
        )


# Internal endpoint for OpenClaw to fetch users with Telegram bots
@router.get("/internal/users-with-bots", tags=["Internal"])
async def get_users_with_bots(request: Request, db=Depends(get_db)):
    """Internal endpoint for OpenClaw to get users configured with Telegram bots."""
    from sqlalchemy import select

    # Verify internal token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not settings.INTERNAL_API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if auth_header != f"Bearer {settings.INTERNAL_API_TOKEN}":
        raise HTTPException(status_code=401, detail="Invalid token")

    # Get all users with telegram_bot_token set
    result = await db.execute(
        select(UserDB).where(UserDB.telegram_token != None, UserDB.telegram_token != "")
    )
    users = result.scalars().all()

    return [
        {
            "id": user.id,
            "email": user.email,
            "telegram_bot_token": user.telegram_token,
            "role": user.role,
        }
        for user in users
    ]
