
import asyncio
from sqlalchemy import select
from src.api.utils.database import async_session_factory
from src.api.utils.models import AffiliateLinkDB, MonitoredNiche

async def check():
    async with async_session_factory() as session:
        # Check affiliate links
        res_links = await session.execute(select(AffiliateLinkDB))
        links = res_links.scalars().all()
        print(f'Found {len(links)} affiliate links')
        for link in links:
            print(f' - {link.product_name} ({link.niche})')
            
        # Check monitored niches
        res_niches = await session.execute(select(MonitoredNiche))
        niches = res_niches.scalars().all()
        print(f'Found {len(niches)} monitored niches')
        for n in niches:
            print(f' - {n.niche}')

if __name__ == "__main__":
    import os
    import sys
    sys.path.append(os.getcwd())
    asyncio.run(check())
