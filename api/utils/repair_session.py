import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from api.utils.database import SessionLocal
from api.utils.user_models import UserDB, UserRole, SubscriptionTier
from api.utils.security import get_password_hash
from api.config import settings


def repair_admin():
    db = SessionLocal()
    try:
        # Get credentials from environment variables - fail if not set
        username = os.getenv("ADMIN_USERNAME")
        email = os.getenv("ADMIN_EMAIL")
        password = os.getenv("ADMIN_PASSWORD")
        
        if not username or not email or not password:
            print("[REPAIR] ERROR: ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD environment variables must be set.")
            print("[REPAIR] Example: export ADMIN_USERNAME=admin ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=secure_password_here")
            return
            
        # Check if user exists
        user = db.query(UserDB).filter(UserDB.username == username).first()
        if user:
            print(f"[REPAIR] User {username} already exists.")
            return

        print(f"[REPAIR] Creating admin user: {username}")
        hashed_pwd = get_password_hash(password)
        
        admin_user = UserDB(
            username=username,
            email=email,
            hashed_password=hashed_pwd,
            role=UserRole.ADMIN,
            subscription=SubscriptionTier.PREMIUM
        )
        db.add(admin_user)
        db.commit()
        print("[REPAIR] Admin user created successfully.")
    except Exception as e:
        print(f"[REPAIR] Error creating user: {e}")
    finally:
        db.close()
