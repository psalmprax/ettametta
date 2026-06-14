"""
Manual seed script — populates FALLBACK_BLUEPRINTS into the DB.
Idempotent: skips blueprints that already exist by ID.

Usage:
    python3 scripts/seed_nexus_blueprints.py

Run this after a fresh database migration if auto-seed didn't fire
(e.g., container started before migration was applied).
"""

import asyncio
import sys

sys.path.insert(0, ".")


async def main():
    from src.services.nexus_engine.blueprints import seed_blueprints

    count = await seed_blueprints()
    if count > 0:
        print(f"✅ Seeded {count} blueprints into the database.")
    else:
        print("ℹ️  No blueprints needed seeding (table already populated).")


if __name__ == "__main__":
    asyncio.run(main())
