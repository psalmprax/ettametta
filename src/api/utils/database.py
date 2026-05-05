from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from src.api.config import settings


# 1. Sync Database Configuration (for background workers/Celery)
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 2. Async Database Configuration (for FastAPI event loop)
def get_async_db_url(url: str | None) -> str:
    if not url:
        url = "sqlite:///./data/db/ettametta.db"
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///")
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://")
    return url


ASYNC_DATABASE_URL = get_async_db_url(settings.DATABASE_URL)
async_engine = create_async_engine(
    ASYNC_DATABASE_URL, echo=settings.DEBUG, future=True, pool_pre_ping=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# For backward compatibility with some service layers
async_session_factory = AsyncSessionLocal

Base = declarative_base()


async def get_db():
    """Async dependency for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
