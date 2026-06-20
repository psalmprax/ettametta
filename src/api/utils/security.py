from datetime import datetime, timedelta, timezone
from joserfc import jwt
from joserfc.jwk import OctKey
import bcrypt
import logging
from src.api.config import settings

logger = logging.getLogger(__name__)

class DirectBcryptWrapper:
    def verify(self, plain_password: str | bytes, hashed_password: str | bytes) -> bool:
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        try:
            return bcrypt.checkpw(plain_password[:72], hashed_password)
        except Exception:
            return False

    def hash(self, password: str | bytes) -> str:
        if isinstance(password, str):
            password = password.encode('utf-8')
        # Generate a standard salt and hash the password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password[:72], salt)
        return hashed.decode('utf-8')

pwd_context = DirectBcryptWrapper()

if settings.ENV == "production" and (not settings.SECRET_KEY or settings.SECRET_KEY == "dev_secret_key_change_me_in_production" or settings.SECRET_KEY == "dev_secret_key_vforge_2026_change_in_prod"):
    raise RuntimeError("SECRET_KEY must be set to a secure value in production environment.")

SECRET_KEY = settings.SECRET_KEY
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required. Please set it in your environment.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours

def verify_password(plain_password, hashed_password):
    # Bcrypt has a 72-byte limit - truncate if necessary
    if isinstance(plain_password, str):
        if len(plain_password) > 72:
            logger.warning("Password exceeds 72 bytes, truncating for bcrypt compatibility")
        plain_password = plain_password[:72]
    elif isinstance(plain_password, bytes):
        if len(plain_password) > 72:
            logger.warning("Password exceeds 72 bytes, truncating for bcrypt compatibility")
        plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    # Bcrypt has a 72-byte limit - truncate if necessary
    if isinstance(password, str):
        if len(password) > 72:
            logger.warning("Password exceeds 72 bytes, truncating for bcrypt compatibility")
        password = password[:72]
    elif isinstance(password, bytes):
        if len(password) > 72:
            logger.warning("Password exceeds 72 bytes, truncating for bcrypt compatibility")
        password = password[:72]
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    key = OctKey.import_key(SECRET_KEY)
    encoded_jwt = jwt.encode({"alg": ALGORITHM}, to_encode, key)
    return encoded_jwt


