from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from src.api.config import settings
from authlib.integrations.base_client import OAuthError
from authlib.integrations.httpx_client import AsyncOAuth2Client
import redis
import hmac
import hashlib
import base64
import json
import logging

from src.api.utils.security import verify_password, get_password_hash, create_access_token, pwd_context, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


import redis.asyncio as redis_async

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
            logger.error(f"Internal error during JWT decode: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Redis error during token decode: {str(e)}")
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
