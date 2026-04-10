from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from api.utils.database import get_db
from api.utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    sign_oauth_state,
    verify_oauth_state,
)
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from api.config import settings
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
from authlib.integrations.base_client import OAuthError
import secrets
import redis
import redis.asyncio as redis_async
from api.utils.user_models import UserDB

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def create_google_flow():
    """Create a configured Google OAuth flow instance."""
    return Flow.from_client_config(
        client_config={
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_AUTH_REDIRECT_URI],
            }
        },
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ],
        redirect_uri=settings.GOOGLE_AUTH_REDIRECT_URI,
    )


class UserCreate(BaseModel):
    email: EmailStr
    password: str

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
    email: Optional[EmailStr] = None
    telegram_chat_id: Optional[str] = None
    telegram_token: Optional[str] = None
    whatsapp_number: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class UserResponse(BaseModel):
    id: str
    email: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.utils.database import get_db


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    stmt = select(UserDB).where(UserDB.email == user.email)
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()

    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pwd = get_password_hash(user.password)
    username = user.email.split("@")[0]

    new_user = UserDB(
        username=username,
        email=user.email,
        hashed_password=hashed_pwd,
    )
    db.add(new_user)
    # db.commit() and refresh are handled by get_db dependency or can be explicit
    await db.flush()
    await db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserDB).where(UserDB.email == form_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = await decode_access_token(token)
    if payload is None:
        raise credentials_exception
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    stmt = select(UserDB).where(UserDB.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    return user


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserDB = Depends(get_current_user)):
    return current_user


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
        await redis_client.aclose()
    return {"message": "Logged out"}


@router.get("/callback/google")
async def google_auth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
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

        await flow.fetch_token(code=code)
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
            await db.flush()
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
