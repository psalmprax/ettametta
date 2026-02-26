import sys
import os

# Add the project root to sys.path for absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.utils.database import SessionLocal
from api.utils.user_models import UserDB, SubscriptionTier

def upgrade_user(username: str, tier: str = "premium"):
    db = SessionLocal()
    try:
        user = db.query(UserDB).filter(UserDB.username == username).first()
        if not user:
            print(f"Error: User '{username}' not found.")
            return

        print(f"Current subscription for {username}: {user.subscription}")
        
        if tier.lower() == "premium":
            user.subscription = SubscriptionTier.PREMIUM
        elif tier.lower() == "free":
            user.subscription = SubscriptionTier.FREE
        else:
            print(f"Error: Invalid tier '{tier}'. Use 'premium' or 'free'.")
            return

        db.commit()
        print(f"Successfully upgraded {username} to {user.subscription}.")
    except Exception as e:
        print(f"Error during upgrade: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upgrade_user.py <username> [premium|free]")
        sys.exit(1)
    
    target_username = sys.argv[1]
    target_tier = sys.argv[2] if len(sys.argv) > 2 else "premium"
    
    upgrade_user(target_username, target_tier)
