"""add transaction_id + unique constraint to revenue_logs

Webhook idempotency fix: ``monetization._idempotent_revenue_log`` used a
SELECT-then-INSERT pattern that allowed concurrent webhook retries to
double-credit the same (platform, transaction_id) pair. The fix:

  1. Add a top-level ``transaction_id`` column (String(128), nullable
     for backward compat with legacy rows that store the value in
     ``metadata_json``).
  2. Add a unique constraint on ``(platform, transaction_id)`` so the
     DB itself rejects concurrent duplicate inserts.
  3. Migration is wrapped in ``op.batch_alter_table`` for SQLite
     compatibility (project supports both SQLite dev and Postgres prod).

The column is ``nullable=True`` so the migration is purely additive:
existing rows with NULL ``transaction_id`` are not affected. Postgres
treats NULLs as distinct in unique constraints, so legacy rows are not
deduplicated by the new constraint — that's fine; the constraint only
needs to enforce uniqueness on NEW rows going forward. New webhook
handlers always set ``transaction_id`` so the constraint takes effect
immediately.

The unique index is created separately from the column for clarity and
to match the project's pattern of explicit index naming.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026_05_29_revenue_txid"
down_revision = "e7b99c2d1f4a"  # current head as of 2026-05-29
branch_labels = ["webhook-idempotency-fix"]
depends_on = []


def upgrade() -> None:
    with op.batch_alter_table("revenue_logs") as batch_op:
        batch_op.add_column(
            sa.Column("transaction_id", sa.String(length=128), nullable=True)
        )
        batch_op.create_index(
            "ix_revenue_logs_transaction_id",
            ["transaction_id"],
            unique=False,
        )
        batch_op.create_unique_constraint(
            "uix_revenue_platform_txid",
            ["platform", "transaction_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("revenue_logs") as batch_op:
        batch_op.drop_constraint("uix_revenue_platform_txid", type_="unique")
        batch_op.drop_index("ix_revenue_logs_transaction_id")
        batch_op.drop_column("transaction_id")
