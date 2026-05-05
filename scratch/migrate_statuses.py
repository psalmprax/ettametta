
import asyncio
import logging
from sqlalchemy import text
from src.api.utils.database import async_session_factory
from src.shared.enums import SystemJobStatus, ContentPublishStatus, ABTestStatus, ScanStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StatusMigration")

# Mapping of legacy string statuses to standardized Enum values
STATUS_MAPPING = {
    "video_jobs": {
        "pending": SystemJobStatus.QUEUED.value,
        "queued": SystemJobStatus.QUEUED.value,
        "running": SystemJobStatus.PROCESSING.value,
        "processing": SystemJobStatus.PROCESSING.value,
        "completed": SystemJobStatus.COMPLETED.value,
        "success": SystemJobStatus.COMPLETED.value,
        "failed": SystemJobStatus.FAILED.value,
        "error": SystemJobStatus.FAILED.value,
    },
    "nexus_jobs": {
        "pending": SystemJobStatus.QUEUED.value,
        "queued": SystemJobStatus.QUEUED.value,
        "running": SystemJobStatus.PROCESSING.value,
        "processing": SystemJobStatus.PROCESSING.value,
        "completed": SystemJobStatus.COMPLETED.value,
        "failed": SystemJobStatus.FAILED.value,
    },
    "ab_tests": {
        "active": ABTestStatus.ACTIVE.value,
        "completed": ABTestStatus.COMPLETED.value,
        "finished": ABTestStatus.COMPLETED.value,
    },
    "scheduled_posts": {
        "pending": ContentPublishStatus.PENDING.value,
        "PENDING": ContentPublishStatus.PENDING.value,
        "published": ContentPublishStatus.PUBLISHED.value,
        "PUBLISHED": ContentPublishStatus.PUBLISHED.value,
        "failed": ContentPublishStatus.FAILED.value,
        "FAILED": ContentPublishStatus.FAILED.value,
        "expired": ContentPublishStatus.EXPIRED.value,
        "EXPIRED": ContentPublishStatus.EXPIRED.value,
    },
    "published_content": {
        "pending": ContentPublishStatus.PENDING.value,
        "Published": ContentPublishStatus.PUBLISHED.value,
        "published": ContentPublishStatus.PUBLISHED.value,
        "failed": ContentPublishStatus.FAILED.value,
    },
    "scan_history": {
        "pending": ScanStatus.PENDING.value,
        "running": ScanStatus.PROCESSING.value,
        "completed": ScanStatus.COMPLETED.value,
        "scan_completed": ScanStatus.COMPLETED.value,
        "failed": ScanStatus.FAILED.value,
    },
    "system_activity": {
        "SYSTEM": "SYSTEM",
        "INFO": "INFO",
        "ERROR": "ERROR",
        "SUCCESS": "SUCCESS",
        "WARNING": "WARNING",
    }
}

async def migrate_statuses():
    logger.info("🚀 Starting status standardization migration...")
    
    async with async_session_factory() as session:
        for table, mapping in STATUS_MAPPING.items():
            logger.info(f"Checking table: {table}")
            
            # Check if column is 'status' (except system_activity which is 'level')
            column = "level" if table == "system_activity" else "status"
            
            # Increase column length to accommodate longer Enums (e.g., PROCESSING)
            if table != "system_activity":
                try:
                    alter_query = text(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE VARCHAR(20)")
                    await session.execute(alter_query)
                    logger.info(f"✅ Increased column length for {table}.{column}")
                except Exception as alter_err:
                    # SQLite doesn't support ALTER COLUMN TYPE, but it doesn't enforce VARCHAR length anyway
                    logger.warning(f"⚠️ Could not alter column for {table}: {alter_err}")
            
            for legacy, standard in mapping.items():
                if legacy == standard:
                    continue
                    
                query = text(f"UPDATE {table} SET {column} = :standard WHERE {column} = :legacy")
                result = await session.execute(query, {"standard": standard, "legacy": legacy})
                
                if result.rowcount > 0:
                    logger.info(f"✅ Updated {result.rowcount} rows in {table}: '{legacy}' -> '{standard}'")
        
        await session.commit()
    
    logger.info("🎉 Status migration completed successfully.")

if __name__ == "__main__":
    asyncio.run(migrate_statuses())
