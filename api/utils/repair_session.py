import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from api.utils.database import SessionLocal
from api.utils.user_models import UserDB, UserRole, SubscriptionTier
from api.utils.security import get_password_hash

def repair_admin():
    db = SessionLocal()
    try:
        username = "psalmprax"
        email = "psalmprax@example.com"
        password = "ettametta_pass" # Default password for recovery
        
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
        print("[REPAIR] Admin user created successfully. Use default password to login if current session fails.")
    except Exception as e:
        print(f"[REPAIR] Error creating user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    repair_admin()
