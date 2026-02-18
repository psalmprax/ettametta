import os
from typing import Dict, Optional

from api.utils.database import SessionLocal
from api.utils.models import SocialAccount
import datetime

class TokenManager:
    def get_token(self, platform: str, account_id: Optional[int] = None) -> Optional[str]:
        """Returns the access token for a platform from the DB."""
        db = SessionLocal()
        try:
            query = db.query(SocialAccount).filter(SocialAccount.platform == platform)
            if account_id:
                account = query.filter(SocialAccount.id == account_id).first()
            else:
                account = query.first()
            return account.access_token if account else None
        finally:
            db.close()

    def get_token_data(self, platform: str, account_id: Optional[int] = None) -> Optional[Dict]:
        """Returns the full token data dict for a platform/account."""
        db = SessionLocal()
        try:
            query = db.query(SocialAccount).filter(SocialAccount.platform == platform)
            if account_id:
                account = query.filter(SocialAccount.id == account_id).first()
            else:
                account = query.first()
            if not account: return None
            return {
                "access_token": account.access_token,
                "refresh_token": account.refresh_token,
                "open_id": account.username
            }
        finally:
            db.close()

    def store_token(self, platform: str, token_data: Dict):
        """Stores token data (access_token, refresh_token, expiry) in the DB."""
        db = SessionLocal()
        try:
            username = token_data.get("username")
            account = None
            if username:
                account = db.query(SocialAccount).filter(
                    SocialAccount.platform == platform, 
                    SocialAccount.username == username
                ).first()
            
            if not account:
                account = SocialAccount(platform=platform, username=username)
            
            account.access_token = token_data.get("access_token")
            account.refresh_token = token_data.get("refresh_token")
            account.token_type = token_data.get("token_type")
            account.scope = token_data.get("scope")
            
            # Handle expiry (assuming tokens have 'expires_in' or similar)
            expires_in = token_data.get("expires_in", 3600)
            account.expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expires_in)
            account.updated_at = datetime.datetime.now(datetime.timezone.utc)
            
            db.merge(account)
            db.commit()
            print(f"[TokenManager] Securely persisted token for {platform} account {username}")
        finally:
            db.close()

    def is_token_expired(self, platform: str, account_id: Optional[int] = None) -> bool:
        db = SessionLocal()
        try:
            query = db.query(SocialAccount).filter(SocialAccount.platform == platform)
            if account_id:
                account = query.filter(SocialAccount.id == account_id).first()
            else:
                account = query.first()
            
            if not account or not account.expiry:
                return True
            # Ensure account.expiry is aware if it's stored as naive but assumed UTC
            expiry = account.expiry
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=datetime.timezone.utc)
            return datetime.datetime.now(datetime.timezone.utc) > expiry
        finally:
            db.close()

token_manager = TokenManager()
