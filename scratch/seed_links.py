
import asyncio
import uuid
from datetime import datetime
from sqlalchemy import select
from src.api.utils.database import async_session_factory
from src.api.utils.models import AffiliateLinkDB, UserDB

async def seed():
    async with async_session_factory() as session:
        # Get first user
        res_user = await session.execute(select(UserDB))
        user = res_user.scalars().first()
        if not user:
            print("No user found to seed links for.")
            return

        user_id = user.id
        print(f"Seeding links for user: {user.email} ({user_id})")

        # Check if already seeded
        res_links = await session.execute(select(AffiliateLinkDB).where(AffiliateLinkDB.user_id == user_id))
        if res_links.scalars().first():
            print("Affiliate links already exist. Skipping seed.")
            return

        demo_links = [
            {
                "product_name": "neural_optimizer_v1",
                "niche": "AI Technology",
                "link": "https://ettametta.ai/products/neural-opt",
                "cta_text": "Boost your neural output"
            },
            {
                "product_name": "stoic_journal_pro",
                "niche": "Stoic Wisdom",
                "link": "https://ettametta.ai/products/stoic-journal",
                "cta_text": "Master your emotions"
            },
            {
                "product_name": "market_alpha_signals",
                "niche": "Market Trends",
                "link": "https://ettametta.ai/products/alpha-signals",
                "cta_text": "Outperform the market"
            }
        ]

        for link_data in demo_links:
            link = AffiliateLinkDB(
                id=str(uuid.uuid4()),
                user_id=user_id,
                **link_data,
                created_at=datetime.utcnow()
            )
            session.add(link)
        
        await session.commit()
        print(f"Successfully seeded {len(demo_links)} affiliate links.")

if __name__ == "__main__":
    import os
    import sys
    sys.path.append(os.getcwd())
    asyncio.run(seed())
