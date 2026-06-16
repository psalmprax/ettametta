"""Stub migration for revision 2026_05_29_add_impression_tracking.

The schema changes this branch introduced (affiliate_links.impression_count,
affiliate_links.last_impression_at) were applied directly to the production
DB and the revision was ``alembic stamp``-ed. This stub exists solely so
alembic can resolve the revision chain in merge_remaining_2026.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "2026_05_29_add_impression_tracking"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
