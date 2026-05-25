import logging
import redis.asyncio as redis
from src.api.config import settings

logger = logging.getLogger(__name__)

async def start_hot_reload_listener():
    """
    Listens for 'system_config_reload' signals from Redis and re-initializes 
    frameworks (LangChain, CrewAI) dynamically.
    """
    logger.info("Initializing system hot-reload listener...")
    
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe("system_config_reload")
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = message["data"]
                logger.warning(f"🔔 Hot-Reload Signal Received: {data}")
                
                # Reload LangChain
                try:
                    from src.services.langchain.service import langchain_service
                    langchain_service.hot_reload()
                except Exception as e:
                    logger.exception(f"Failed to reload LangChain: {e}")
                
                # Reload CrewAI
                try:
                    from src.services.crewai.service import crewai_service
                    crewai_service.hot_reload()
                except Exception as e:
                    logger.exception(f"Failed to reload CrewAI: {e}")
                
                logger.info("✅ All systems hot-reloaded successfully.")
    except Exception as e:
        logger.exception(f"Hot-reload listener encountered an error: {e}")
    finally:
        await pubsub.unsubscribe("system_config_reload")
