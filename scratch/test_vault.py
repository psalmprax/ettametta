import sys
import os
import asyncio
from pathlib import Path

# Add src and root to path
PROJECT_ROOT = Path("/home/psalmprax/ALL_PROJECTS/ettametta")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.api.utils.vault import get_secret_async, get_secret
from src.api.config import settings

async def test_vault():
    print(f"Config Settings PEXELS_API_KEY: {settings.PEXELS_API_KEY}")
    
    sec_async = await get_secret_async("pexels_api_key")
    print(f"Vault (Async) PEXELS_API_KEY: {sec_async}")
    
    sec_sync = get_secret("pexels_api_key")
    print(f"Vault (Sync) PEXELS_API_KEY: {sec_sync}")

if __name__ == "__main__":
    asyncio.run(test_vault())
