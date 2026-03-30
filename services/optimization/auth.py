import os
import datetime
import base64
import logging
from typing import Dict, Optional
from cryptography.fernet import Fernet
from api.utils.database import SessionLocal
from api.utils.models import SocialAccount
from api.config import settings

logger = logging.getLogger(__name__)


class TokenManager:
    def __init__(self):
        # Derive a stable Fernet key from the app's SECRET_KEY
        secret = settings.SECRET_KEY or "dev_secret_key_Ettametta_2026_forge"
        if len(secret) < 32:
            secret = secret.ljust(32, "0")
        key = base64.urlsafe_b64encode(secret[:32].encode())
        self.fernet = Fernet(key)

    def _encrypt(self, text: str) -> str:
        if not text:
            return None
        return self.fernet.encrypt(text.encode()).decode()

    def _decrypt(self, encrypted_text: str) -> str:
        if not encrypted_text:
            return None
        try:
            return self.fernet.decrypt(encrypted_text.encode()).decode()
        except Exception as e:
            logger.error(f"[TokenManager] Decryption failed: {e}")
            return None

    def get_token(
        self, platform: str, user_id: int, account_id: Optional[int] = None
    ) -> Optional[str]:
        """Returns the decrypted access token for a platform/user."""
        db = SessionLocal()
        try:
            query = db.query(SocialAccount).filter(
                SocialAccount.platform == platform, SocialAccount.user_id == user_id
            )
            if account_id:
                account = query.filter(SocialAccount.id == account_id).first()
            else:
                account = query.first()

            return self._decrypt(account.access_token) if account else None
        finally:
            db.close()

    def get_token_data(
        self, platform: str, user_id: int, account_id: Optional[int] = None
    ) -> Optional[Dict]:
        """Returns the full decrypted token data dict."""
        db = SessionLocal()
        try:
            query = db.query(SocialAccount).filter(
                SocialAccount.platform == platform, SocialAccount.user_id == user_id
            )
            if account_id:
                account = query.filter(SocialAccount.id == account_id).first()
            else:
                account = query.first()

            if not account:
                return None

            return {
                "access_token": self._decrypt(account.access_token),
                "refresh_token": self._decrypt(account.refresh_token),
                "username": account.username,
                "expiry": account.expiry,
            }
        finally:
            db.close()

    def store_token(self, platform: str, user_id: int, token_data: Dict):
        """Stores encrypted token data in the DB with user association."""
        db = SessionLocal()
        try:
            username = token_data.get("username")
            account = None
            if username:
                account = (
                    db.query(SocialAccount)
                    .filter(
                        SocialAccount.platform == platform,
                        SocialAccount.username == username,
                        SocialAccount.user_id == user_id,
                    )
                    .first()
                )

            if not account:
                account = SocialAccount(
                    platform=platform, username=username, user_id=user_id
                )

            # Encrypt sensitive tokens
            account.access_token = self._encrypt(token_data.get("access_token"))
            account.refresh_token = self._encrypt(token_data.get("refresh_token"))

            account.token_type = token_data.get("token_type")
            account.scope = token_data.get("scope")

            # Handle expiry
            expires_in = token_data.get("expires_in", 3600)
            account.expiry = datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(seconds=expires_in)
            account.updated_at = datetime.datetime.now(datetime.timezone.utc)

            db.merge(account)
            db.commit()
            logger.info(
                f"[TokenManager] Encrypted and persisted token for {platform} (User: {user_id})"
            )
        finally:
            db.close()

    async def ensure_valid_token(
        self, platform: str, user_id: int, account_id: Optional[int] = None
    ) -> bool:
        """
        Public helper to ensure a token is valid, triggering refresh if needed.
        """
        if self.is_token_expired(platform, user_id, account_id):
            return await self.refresh_token(platform, user_id, account_id)
        return True

    async def refresh_token(
        self, platform: str, user_id: int, account_id: Optional[int] = None
    ) -> bool:
        """
        Triggers a refresh flow for a specific platform/user.
        """
        token_data = self.get_token_data(platform, user_id, account_id)
        if not token_data or not token_data.get("refresh_token"):
            logger.error(
                f"[TokenManager] No refresh token available for {platform} (User: {user_id})"
            )
            return False

        import httpx
        from api.utils.vault import get_secret

        try:
            if platform == "youtube":
                url = "https://oauth2.googleapis.com/token"
                data = {
                    "client_id": get_secret("google_client_id"),
                    "client_secret": get_secret("google_client_secret"),
                    "refresh_token": token_data["refresh_token"],
                    "grant_type": "refresh_token",
                }
            elif platform == "tiktok":
                url = "https://open.tiktokapis.com/v2/oauth/token/"
                data = {
                    "client_key": get_secret("tiktok_client_key"),
                    "client_secret": get_secret("tiktok_client_secret"),
                    "refresh_token": token_data["refresh_token"],
                    "grant_type": "refresh_token",
                }
            elif platform in ("instagram", "facebook"):
                url = "https://graph.facebook.com/v18.0/oauth/access_token"
                data = {
                    "grant_type": "fb_exchange_token",
                    "client_id": get_secret("facebook_app_id"),
                    "client_secret": get_secret("facebook_app_secret"),
                    "fb_exchange_token": token_data["access_token"],
                }
            elif platform == "x":
                url = "https://api.twitter.com/2/oauth2/token"
                data = {
                    "grant_type": "refresh_token",
                    "refresh_token": token_data["refresh_token"],
                    "client_id": get_secret("x_client_id"),
                }
            elif platform == "linkedin":
                url = "https://www.linkedin.com/oauth/v2/accessToken"
                data = {
                    "grant_type": "refresh_token",
                    "refresh_token": token_data["refresh_token"],
                    "client_id": get_secret("linkedin_client_id"),
                    "client_secret": get_secret("linkedin_client_secret"),
                }
            else:
                return False

            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data)
                new_tokens = response.json()

                if response.status_code != 200:
                    logger.error(
                        f"[TokenManager] Refresh failed for {platform}: {new_tokens}"
                    )
                    return False

                # Persistence
                self.store_token(
                    platform,
                    user_id,
                    {
                        "access_token": new_tokens["access_token"],
                        "refresh_token": new_tokens.get(
                            "refresh_token", token_data["refresh_token"]
                        ),
                        "expires_in": new_tokens.get("expires_in", 3600),
                        "username": token_data["username"],
                    },
                )
                return True
        except Exception as e:
            logger.error(f"[TokenManager] Exception during {platform} refresh: {e}")
            return False

    def is_token_expired(
        self, platform: str, user_id: int, account_id: Optional[int] = None
    ) -> bool:
        db = SessionLocal()
        try:
            query = db.query(SocialAccount).filter(
                SocialAccount.platform == platform, SocialAccount.user_id == user_id
            )
            if account_id:
                account = query.filter(SocialAccount.id == account_id).first()
            else:
                account = query.first()

            if not account or not account.expiry:
                return True

            expiry = account.expiry
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=datetime.timezone.utc)

            # Expired if less than 5 minutes remaining
            return datetime.datetime.now(datetime.timezone.utc) > (
                expiry - datetime.timedelta(minutes=5)
            )
        finally:
            db.close()


token_manager = TokenManager()
