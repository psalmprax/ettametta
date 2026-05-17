from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from src.api.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
        plain_password = plain_password[:72]
    elif isinstance(plain_password, bytes):
        plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    # Bcrypt has a 72-byte limit - truncate if necessary
    if isinstance(password, str):
        password = password[:72]
    elif isinstance(password, bytes):
        password = password[:72]
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
