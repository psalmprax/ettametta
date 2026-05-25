from jose import JWTError, jwt
from src.api.config import settings
from authlib.integrations.httpx_client import AsyncOAuth2Client
import hmac
import hashlib
import base64
import json
import logging

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select

from src.api.utils.security import SECRET_KEY, ALGORITHM


import redis.asyncio as redis_async

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

logger = logging.getLogger(__name__)

# Global Redis client for async operations
redis_async_client = redis_async.from_url(settings.REDIS_URL, decode_responses=True)


async def decode_access_token(token: str):
    try:
        if await redis_async_client.sismember("token_blacklist", token):
            return None
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            logger.warning(f"JWT decode error for token {token[:10]}...: {str(e)}")
            return None
        except Exception as e:
            logger.exception(f"Internal error during JWT decode: {str(e)}")
            return None
    except Exception as e:
        logger.exception(f"Redis error during token decode: {str(e)}")
        return None


# Google OAuth setup
def get_google_oauth_client():
    return AsyncOAuth2Client(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        redirect_uri=settings.GOOGLE_OAUTH_REDIRECT_URI,
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


def verify_oauth_state(signed_state: str) -> str | None:
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


async def get_current_user(
    token: str = Depends(oauth2_scheme), db=None
):
    from src.api.utils.database import AsyncSessionLocal
    from src.api.utils.user_models import UserDB

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

    if db is not None:
        stmt = select(UserDB).where(UserDB.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
    else:
        async with AsyncSessionLocal() as session:
            stmt = select(UserDB).where(UserDB.email == email)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    return user


def admin_required(current_user=None):
    from src.api.utils.user_models import UserDB, UserRole

    async def _admin_dep(current_user: UserDB = Depends(get_current_user)) -> UserDB:
        if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrative privileges required for this operation.",
            )
        return current_user

    if current_user is not None:
        if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrative privileges required for this operation.",
            )
        return current_user
    return _admin_dep
