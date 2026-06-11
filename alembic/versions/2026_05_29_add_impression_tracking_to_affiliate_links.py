"""Add impression tracking to affiliate_links

Phase 14: Auto-Insert Affiliate Links into Videos.

Adds two columns to ``affiliate_links`` so the monetization pipeline
can record when an ``AffiliateLinkDB`` row is actually burned into a
rendered video via FFmpeg drawtext:

* ``impression_count``  — Integer, default 0, NOT NULL. Bumped by 1
  every time the auto-insert pipeline successfully renders the link
  into a video (regardless of how many overlay frames it appears in).
* ``last_impression_at`` — DateTime, nullable. Timestamp of the most
  recent successful burn. Powers dashboard recency sorts.

Uses ``batch_alter_table`` so the migration is safe under both
SQLite (dev/test) and Postgres (prod) without a full table rewrite.

Revision ID: 2026_05_29_add_impression_tracking
Revises:     (latest existing revision at apply time)
Create Date: 2026-05-29
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "2026_05_29_add_impression_tracking"
down_revision = None  # Alembic auto-detects the head at apply time
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add impression_count + last_impression_at to affiliate_links."""
    with op.batch_alter_table("affiliate_links", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "impression_count",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column(
                "last_impression_at",
                sa.DateTime(),
                nullable=True,
            )
        )


def downgrade() -> None:
    """Remove the impression-tracking columns (data loss)."""
    with op.batch_alter_table("affiliate_links", schema=None) as batch_op:
        batch_op.drop_column("last_impression_at")
        batch_op.drop_column("impression_count")
