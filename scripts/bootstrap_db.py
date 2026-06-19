import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from src.api.utils.database import engine, Base
from src.api.utils.models import *
from src.api.utils.user_models import *
from src.api.utils.credit_models import *
from src.api.utils.auth import get_password_hash
from sqlalchemy.orm import Session
import secrets
import string
import uuid
from datetime import datetime, timezone


# ── Credentials resolution ──────────────────────────────────────────────────────
# Bootstrap used to hardcode an admin user (`samuelolle` / `Single123.`) and
# a personal email (`samuelolle@yahoo.com`) directly in this file. That
# leaked real-looking creds into git history and any container image built
# from this script. We now require explicit env vars and refuse to run
# without them, AND we generate a strong random password if the operator
# only supplies the username (so the value never lives on disk at all).


def _resolve_bootstrap_credentials() -> tuple[str, str, str, str]:
    """Return (username, email, password, role) from env or raise."""
    username = os.getenv("BOOTSTRAP_ADMIN_USERNAME")
    email = os.getenv("BOOTSTRAP_ADMIN_EMAIL")
    password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD")

    if not username:
        raise RuntimeError(
            "BOOTSTRAP_ADMIN_USERNAME env var is required. "
            "Refusing to bootstrap with a hardcoded identity."
        )
    if not email:
        raise RuntimeError(
            "BOOTSTRAP_ADMIN_EMAIL env var is required. "
            "Refusing to bootstrap with a hardcoded email."
        )

    if not password:
        # Operator didn't supply one → generate a strong random one and
        # print it ONCE to stdout. They are responsible for capturing it
        # from the bootstrap log before the script exits.
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = "".join(secrets.choice(alphabet) for _ in range(24))
        print(
            "🔐 Generated random admin password (24 chars). "
            "CAPTURE THIS NOW — it will not be shown again:",
            password,
        )
    return username, email, password, os.getenv("BOOTSTRAP_ADMIN_ROLE", "admin")


def bootstrap():
    print("🚀 Bootstrapping Ettametta Database...")

    # 1. Create all tables
    print("📋 Creating all tables via SQLAlchemy...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created.")

    # 2. Add the bootstrap admin user (creds from env, never hardcoded)
    username, email, password, role = _resolve_bootstrap_credentials()
    print(f"👤 Checking user: {username}...")
    with Session(engine) as session:
        # Check if user exists
        existing = session.query(UserDB).filter(UserDB.username == username).first()
        if existing:
            print(f"ℹ️ User {username} already exists. Updating password from env.")
            user_id = existing.id
            existing.hashed_password = get_password_hash(password)
            existing.updated_at = datetime.now(timezone.utc)
        else:
            user_id = str(uuid.uuid4())
            new_user = UserDB(
                id=user_id,
                username=username,
                email=email,
                hashed_password=get_password_hash(password),
                role=role,
                subscription=os.getenv("BOOTSTRAP_ADMIN_SUBSCRIPTION", "premium"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(new_user)
            print(f"✅ Created user: {username} ({user_id})")

        # 3. Ensure credits exist for the user
        initial_balance = int(os.getenv("BOOTSTRAP_INITIAL_CREDITS", "1000"))
        credits = (
            session.query(UserCreditDB).filter(UserCreditDB.user_id == user_id).first()
        )
        if not credits:
            print(f"💰 Initializing credits ({initial_balance}) for {user_id}...")
            new_credits = UserCreditDB(
                id=str(uuid.uuid4()),
                user_id=user_id,
                balance=initial_balance,
                lifetime_purchased=initial_balance,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(new_credits)
            print("✅ Credits initialized.")

        session.commit()

    print(f"✅ User {username} ready.")


def populate_niches():
    """Populate default niches for discovery"""
    print("📊 Populating niches...")

    niches = [
        "motivation",
        "fitness",
        "crypto",
        "tech",
        "comedy",
        "business",
        "finance",
        "gaming",
        "music",
        "travel",
        "food",
        "fashion",
        "education",
        "mindfulness",
        "sports",
    ]

    print(f"✅ Added {len(niches)} niches")


if __name__ == "__main__":
    bootstrap()
    populate_niches()
