import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from api.utils.database import engine, Base
from api.utils.models import *
from api.utils.user_models import *
from api.utils.credit_models import *
from api.utils.auth import get_password_hash
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timezone


def bootstrap():
    print("🚀 Bootstrapping Ettametta Database...")

    # 1. Create all tables
    print("📋 Creating all tables via SQLAlchemy...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created.")

    # 2. Add the samuelolle user
    print("👤 Checking user: samuelolle...")
    with Session(engine) as session:
        # Check if user exists
        existing = session.query(UserDB).filter(UserDB.username == "samuelolle").first()
        if existing:
            print("ℹ️ User samuelolle already exists. Updating password.")
            user_id = existing.id
            existing.hashed_password = get_password_hash("Single123.")
            existing.updated_at = datetime.now(timezone.utc)
        else:
            user_id = str(uuid.uuid4())
            new_user = UserDB(
                id=user_id,
                username="samuelolle",
                email="samuelolle@yahoo.com",
                hashed_password=get_password_hash("Single123."),
                role="admin",
                subscription="premium",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(new_user)
            print(f"✅ Created user: samuelolle ({user_id})")

        # 3. Ensure credits exist for the user
        credits = (
            session.query(UserCreditDB).filter(UserCreditDB.user_id == user_id).first()
        )
        if not credits:
            print(f"💰 Initializing credits for {user_id}...")
            new_credits = UserCreditDB(
                id=str(uuid.uuid4()),
                user_id=user_id,
                balance=1000,
                lifetime_purchased=1000,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(new_credits)
            print("✅ Credits initialized.")

        session.commit()

    print("✅ User samuelolle ready.")


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
