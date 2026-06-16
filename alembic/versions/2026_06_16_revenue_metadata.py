"""add metadata_json to revenue_logs

The webhook dispatcher in
``src.api.routes.monetization._idempotent_insert_revenue_log`` writes
``metadata_json = {"transaction_id": ...}`` for every new postback
(for backward-compat with analytics/aggregation queries that look
there). The ``RevenueLogDB`` model, however, never declared the
column, so any incoming postback would have failed at runtime with
``column "metadata_json" of relation "revenue_logs" does not exist``.

This migration adds the column to make the dispatcher work. The
column is:

  - ``JSON`` (not JSONB) — matches the SQLAlchemy ``Column(JSON)``
    declaration on the model. The backfill migration uses a
    JSON-portable existence check (``COALESCE(... ->> ..., '') <> ''``)
    so it does not depend on the JSONB-only ``?`` operator.

  - ``nullable=True`` — purely additive, does not affect existing
    rows. Legacy rows that pre-date the column will simply have NULL,
    and the backfill migration will fill in the top-level
    ``transaction_id`` from any pre-existing JSON values.

  - ``default=dict`` — matches the model default. New rows that
    forget to set the field will get an empty object instead of NULL,
    so ``->>`` always returns a usable value.

Idempotency
-----------
The migration wraps the ``ALTER TABLE`` in a ``DO $$ ... $$`` block
that checks ``information_schema.columns`` first, so re-running on a
DB that already has the column is a safe no-op. This is important
because the previous turn's re-init dropped the volume; if the
re-apply of migrations races with anything else, this migration will
not blow up.

The raw ``DO $$`` block is intentional — alembic's
``op.batch_alter_table.add_column`` does not support ``IF NOT EXISTS``
on the column itself in alembic 1.10+, so this is the only way to
get a re-runnable schema migration. The check is schema-qualified
(``table_schema = current_schema()``) to avoid matching a same-named
column in a different schema (Dify's ``langgenius`` schema lives in
the same cluster).

Downgrade
---------
``downgrade()`` uses ``DROP COLUMN IF EXISTS`` for the same reason —
running downgrade twice (or on a DB that was never upgraded) is a
safe no-op. The dispatcher in
``monetization._idempotent_insert_revenue_log`` will start failing
again immediately after a downgrade, so this is destructive — the
operator is expected to follow the downgrade with a re-upgrade.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "2026_06_16_revenue_metadata"
down_revision = "merge_remaining_2026"  # current head after the 4-head merge
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Idempotently add metadata_json column to revenue_logs."""
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = current_schema()
                      AND table_name = 'revenue_logs'
                      AND column_name = 'metadata_json'
                ) THEN
                    ALTER TABLE revenue_logs
                    ADD COLUMN metadata_json JSON;
                END IF;
            END$$;
            """
        )
    )


def downgrade() -> None:
    """Drop metadata_json column. Idempotent — uses ``IF EXISTS`` so
    re-running on a DB that already lacks the column is a no-op.

    WARNING: webhook inserts will start failing with
    'column does not exist' immediately after this downgrade.
    Re-upgrade to restore the column.
    """
    op.execute(
        sa.text("ALTER TABLE revenue_logs DROP COLUMN IF EXISTS metadata_json")
    )
