from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from api.config import settings
from authlib.integrations.base_client import OAuthError
from authlib.integrations.httpx_client import AsyncOAuth2Client
import redis
import hmac
import hashlib
import base64
import json

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(
    settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24
)  # Default 24 hours


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def decode_access_token(token: str):
    import redis.asyncio as redis

    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    try:
        if await redis_client.sismember("token_blacklist", token):
            return None
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            print(f"DEBUG: JWT Decode Error for token {token[:10]}... : {str(e)}")
            return None
        except Exception as e:
            print(f"DEBUG: Internal Error during decode: {str(e)}")
            return None

    finally:
        await redis_client.close()


# Google OAuth setup
def get_google_oauth_client():
    return AsyncOAuth2Client(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        redirect_uri=settings.GOOGLE_AUTH_REDIRECT_URI,
    )


# OAuth state signing utilities
def sign_oauth_state(state: str) -> str:
    """Sign OAuth state parameter with HMAC-SHA256."""
    message = state.encode("utf-8")
    signature = hmac.new(SECRET_KEY.encode("utf-8"), message, hashlib.sha256).digest()
    signed_state = json.dumps(
        {"state": state, "signature": base64.b64encode(signature).decode("utf-8")}
    )
    return base64.b64encode(signed_state.encode("utf-8")).decode("utf-8")


def verify_oauth_state(signed_state: str) -> Optional[str]:
    """Verify and extract original state from signed state parameter."""
    try:
        decoded = base64.b64decode(signed_state.encode("utf-8")).decode("utf-8")
        data = json.loads(decoded)
        original_state = data.get("state")
        expected_signature = data.get("signature")

        message = original_state.encode("utf-8")
        expected_sig_bytes = hmac.new(
            SECRET_KEY.encode("utf-8"), message, hashlib.sha256
        ).digest()
        actual_signature = base64.b64encode(expected_sig_bytes).decode("utf-8")

        if hmac.compare_digest(actual_signature, expected_signature):
            return original_state
        return None
    except (ValueError, KeyError):
        return None
