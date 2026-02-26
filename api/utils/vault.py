from sqlalchemy.orm import Session
from api.utils.database import SessionLocal
from api.utils.models import SystemSettings
from api.config import settings
import logging

logger = logging.getLogger(__name__)

def get_secret(key: str, default=None, user_id: int = None) -> str:
    """
    Retrieves a secret. 
    Priority:
    1. User-specific override (UserSetting table)
    2. System-wide setting (SystemSettings table)
    3. environment-based settings (api.config)
    """
    db = SessionLocal()
    try:
        # 1. Check User-specific override if user_id is provided
        if user_id:
            from api.utils.models import UserSetting
            user_setting = db.query(UserSetting).filter(
                UserSetting.user_id == user_id, 
                UserSetting.key == key.lower()
            ).first()
            if user_setting and user_setting.value:
                return user_setting.value

        # 2. Check Database (System-wide)
        db_setting = db.query(SystemSettings).filter(SystemSettings.key == key.lower()).first()
        if db_setting and db_setting.value:
            return db_setting.value
            
        # 3. Check api.config settings
        # Convert key to uppercase for api.config match (e.g., groq_api_key -> GROQ_API_KEY)
        config_key = key.upper()
        if hasattr(settings, config_key):
            val = getattr(settings, config_key)
            if val:
                return val
                
        return default
    except Exception as e:
        logger.error(f"Error resolving secret {key} for user {user_id}: {e}")
        return default
    finally:
        db.close()
