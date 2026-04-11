---
phase: 01-user-authentication-and-settings
reviewed: 2026-04-10T16:32:21+02:00
depth: standard
files_reviewed: 4
files_reviewed_list:
  - api/utils/auth.py
  - api/routes/auth.py
  - api/utils/models.py
  - alembic/versions/001_create_user_table.py
findings:
  critical: 1
  warning: 4
  info: 3
  total: 8
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-04-10T16:32:21+02:00
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Reviewed 4 files related to user authentication and settings. Found one critical schema mismatch between the Alembic migration and the SQLAlchemy model that will cause runtime errors. Several warnings around Redis connection management, password validation, and OAuth state handling. Three informational items for code quality improvements.

## Critical Issues

### CR-01: Schema Mismatch Between Migration and Model

**File:** `alembic/versions/001_create_user_table.py:25` vs `api/utils/user_models.py:25`

**Issue:** The Alembic migration creates the `users` table with an Integer primary key, but the UserDB model defines a String(36) UUID primary key:

Migration line 25:
```python
sa.Column("id", sa.Integer(), nullable=False),
```

Model line 25:
```python
id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
```

Additionally, the migration is missing many columns defined in the model:
- `username` (unique, indexed)
- `role` (Enum)
- `subscription` (Enum)
- `is_active`
- `telegram_chat_id`, `telegram_token`, `whatsapp_number`
- `stripe_customer_id`, `stripe_subscription_id`
- `is_google_oauth`
- `api_keys`, `system_settings`

**Fix:** Update the migration to match the model:
```python
def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role", sa.String(), default="user"),
        sa.Column("subscription", sa.String(), default="free"),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("telegram_chat_id", sa.String(), nullable=True),
        sa.Column("telegram_token", sa.String(), nullable=True),
        sa.Column("whatsapp_number", sa.String(), nullable=True),
        sa.Column("stripe_customer_id", sa.String(), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(), nullable=True),
        sa.Column("is_google_oauth", sa.Boolean(), default=False),
        sa.Column("google_id", sa.String(), nullable=True),
        sa.Column("api_keys", sa.JSON(), nullable=True),
        sa.Column("system_settings", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
```

---

## Warnings

### WR-01: Redis Connection Not Properly Closed

**File:** `api/utils/auth.py:39`

**Issue:** Redis client created but never closed, causing connection leaks:
```python
async def decode_access_token(token: str):
    import redis.asyncio as redis
    redis_client = redis.from_url(settings.REDIS_URL)
    
    if await redis_client.sismember("token_blacklist", token):
        return None
    # ... token decoded but redis_client never closed
```

**Fix:** Use async context manager or explicit close:
```python
async def decode_access_token(token: str):
    import redis.asyncio as redis
    redis_client = redis.from_url(settings.REDIS_URL)
    try:
        if await redis_client.sismember("token_blacklist", token):
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
    finally:
        await redis_client.close()
```

### WR-02: Redis Connections Not Closed in auth.py Routes

**File:** `api/routes/auth.py:162-164`, `172-173`, `194-196`

**Issue:** Multiple Redis clients created in route handlers without being closed:
- Line 162: `redis_client = redis_async.from_url(...)`
- Line 172: Same pattern in logout
- Line 194: `redis.asyncio.Redis(...)` using sync redis module

**Fix:** Use try/finally or context managers to ensure cleanup.

### WR-03: No Password Strength Validation

**File:** `api/routes/auth.py:31`

**Issue:** The `UserCreate` model accepts any password without validation:
```python
class UserCreate(BaseModel):
    email: EmailStr
    password: str  # No validation
```

**Fix:** Add password validation using Pydantic constraints:
```python
class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=128)
```

Or add a custom validator for complexity requirements.

### WR-04: OAuth State Parameter Only Stored, Not Verified

**File:** `api/routes/auth.py:139-165`

**Issue:** The OAuth state parameter is stored in Redis but not cryptographically signed/verified. An attacker could potentially manipulate the state if Redis is compromised. The current implementation trusts Redis state existence without cryptographic verification.

**Fix:** Consider signing the state parameter with a secret key before storing, then verifying the signature on callback:
```python
import hmac
import hashlib

def create_oauth_state():
    state = secrets.token_urlsafe(32)
    signature = hmac.new(SECRET_KEY.encode(), state.encode(), 'sha256').hexdigest()
    return f"{state}.{signature}"

def verify_oauth_state(state: str) -> bool:
    try:
        state_part, signature = state.rsplit('.', 1)
        expected = hmac.new(SECRET_KEY.encode(), state_part.encode(), 'sha256').hexdigest()
        return hmac.compare_digest(signature, expected)
    except:
        return False
```

---

## Info

### IN-01: Hardcoded Token Expiry

**File:** `api/utils/auth.py:15`

**Issue:** Token expiry is hardcoded:
```python
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
```

**Fix:** Move to settings configuration:
```python
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES or (60 * 24)
```

### IN-02: Unused Import

**File:** `api/routes/auth.py:21`

**Issue:** `asyncio` imported but not used:
```python
import asyncio
```

**Fix:** Remove unused import.

### IN-03: Duplicate OAuth Flow Configuration

**File:** `api/routes/auth.py:141-157` and `205-221`

**Issue:** The Google OAuth flow configuration is duplicated in both `/auth/google` and `/auth/callback/google` endpoints. This violates DRY principle.

**Fix:** Extract to a shared function:
```python
def get_google_oauth_flow():
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
```

---

_Reviewed: 2026-04-10T16:32:21+02:00_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_