from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.api.utils.database import async_session_factory
from src.api.utils.models import SystemSettings, UserSetting
from src.api.config import settings
import logging

logger = logging.getLogger(__name__)

async def get_secret_async(key: str, default=None, user_id: str = None, db: AsyncSession = None) -> str:
    """
    Retrieves a secret asynchronously.
    Priority:
    1. User-specific override (UserSetting table)
    2. System-wide setting (SystemSettings table)
    3. environment-based settings (api.config)
    """
    async def _fetch(session: AsyncSession):
        # 1. Check User-specific override if user_id is provided
        if user_id:
            stmt = select(UserSetting).where(
                UserSetting.user_id == user_id,
                UserSetting.key == key.lower()
            )
            result = await session.execute(stmt)
            user_setting = result.scalar_one_or_none()
            if user_setting and user_setting.value:
                return user_setting.value

        # 2. Check Database (System-wide)
        stmt_sys = select(SystemSettings).where(SystemSettings.key == key.lower())
        result_sys = await session.execute(stmt_sys)
        db_setting = result_sys.scalar_one_or_none()
        if db_setting and db_setting.value:
            return db_setting.value

        # 3. Check api.config settings
        config_key = key.upper()
        if hasattr(settings, config_key):
            val = getattr(settings, config_key)
            if val:
                return val

        return default

    try:
        if db:
            return await _fetch(db)
        else:
            async with async_session_factory() as session:
                return await _fetch(session)
    except Exception as e:
        logger.warning(f"Database unreachable during secret resolution for {key}: {e}. Falling back to config.")
        # Fallback to api.config settings on DB failure
        config_key = key.upper()
        if hasattr(settings, config_key):
            val = getattr(settings, config_key)
            if val:
                return val
        return default

def get_secret(key: str, default=None, user_id: str = None) -> str:
    """
    Synchronous implementation of get_secret.
    Avoids asyncio issues in Celery workers.
    """
    from src.api.utils.database import SessionLocal

    try:
        with SessionLocal() as session:
            # 1. Check User-specific override
            if user_id:
                from .models import UserSetting
                user_setting = session.query(UserSetting).filter(
                    UserSetting.user_id == user_id,
                    UserSetting.key == key.lower()
                ).first()
                if user_setting and user_setting.value:
                    return user_setting.value

            # 2. Check Database (System-wide)
            from .models import SystemSettings
            db_setting = session.query(SystemSettings).filter(
                SystemSettings.key == key.lower()
            ).first()
            if db_setting and db_setting.value:
                return db_setting.value

            # 3. Check api.config settings
            config_key = key.upper()
            if hasattr(settings, config_key):
                val = getattr(settings, config_key)
                if val:
                    return val

            return default
    except Exception as e:
        logger.warning(f"Database unreachable during sync secret resolution for {key}: {e}. Falling back to config.")
        # Fallback to api.config settings on DB failure
        config_key = key.upper()
        if hasattr(settings, config_key):
            val = getattr(settings, config_key)
            if val:
                return val
        return default
