from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from api.utils.database import get_db
from api.utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)
from pydantic import BaseModel, EmailStr
from api.config import settings
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
import secrets
import redis
from api.utils.models import UserDB

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class UserCreate(BaseModel):
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
    id: str
    email: str

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

    hashed_pwd = get_password_hash(user.password)

    new_user = UserDB(
        email=user.email,
        password_hash=hashed_pwd,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(UserDB).filter(UserDB.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    user = db.query(UserDB).filter(UserDB.email == email).first()
    if user is None:
        raise credentials_exception
    return user


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserDB = Depends(get_current_user)):
    return current_user


@router.get("/google")
async def google_auth():
    flow = Flow.from_client_config(
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
    authorization_url, state = flow.authorization_url()
    return RedirectResponse(url=authorization_url)


@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    redis_client = redis.Redis(host="localhost", port=6379, db=0)
    redis_client.sadd("token_blacklist", token)
    return {"message": "Logged out"}


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
            user = UserDB(
                email=email,
                password_hash=get_password_hash(
                    secrets.token_urlsafe(32)
                ),  # Random password for OAuth users
                google_id=id_info.get("sub"),
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Create access token
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role}
        )

        # Redirect to frontend with token
        dashboard_url = (
            settings.PRODUCTION_DOMAIN.split("/api/v1")[0].rstrip("/")
            or "http://localhost:7202"
        )
        return RedirectResponse(
            url=f"{dashboard_url}/auth/callback?token={access_token}&provider=google",
            status_code=302,
        )

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Google authentication failed: {str(e)}"
        )
