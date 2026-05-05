import asyncio
import sys
import os
sys.path.append(os.getcwd())
from src.services.knowledge.service import base_knowledge_service

async def main():
    try:
        print("Starting embedding test...")
        emb = await base_knowledge_service.get_embedding("test")
        print(f"Success! Embedding length: {len(emb)}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(main())
