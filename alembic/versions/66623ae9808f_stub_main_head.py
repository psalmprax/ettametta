"""Stub migration for revision 66623ae9808f (main branch head).

This revision was stamped directly to the production DB on 2026-06-15
as the \"current applied head\" and never had a migration file. The
``merge_remaining_2026`` migration references it as one of its four
parent revisions. This stub exists solely so alembic can resolve the
revision chain — it is intentionally a no-op in both directions.

Created to fix: KeyError: '66623ae9808f' when running
``alembic upgrade head`` after the 999.5 backfill fix.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "66623ae9808f"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
