"""backfill transaction_id from metadata_json for legacy revenue_logs

Pre-existing rows stored the platform transaction ID inside
``metadata_json`` (under the key ``transaction_id``) instead of as a
top-level column. The ``revenue_logs.transaction_id`` column + the
``uix_revenue_platform_txid`` unique constraint were added in
``2026_05_29_revenue_txid`` (additive, ``nullable=True``) so the
backfill is safe to run after that migration. Historical rows were
left with the top-level column NULL — this migration copies the value
from ``metadata_json->>'transaction_id'`` into the top-level column so
the unique constraint can dedupe any future re-import of the same
transactions.

This migration depends on the column-add migration
``2026_06_16_revenue_metadata`` (which adds the ``metadata_json``
column that the dispatcher was already writing to but the model
didn't declare). Both ship together; the backfill cannot run
without the column existing.

Conflict handling — MVCC-safe
-----------------------------
If multiple legacy rows share the same ``(platform, transaction_id)``
pair (i.e. duplicate postbacks that pre-date the constraint), the
backfill would otherwise violate the unique constraint. An earlier
draft used ``NOT EXISTS (SELECT 1 FROM revenue_logs r2 WHERE
r2.id <> r.id ...)`` to skip duplicates — that version was BROKEN
because Postgres takes a single MVCC snapshot per statement, so the
correlated subquery could not see the in-flight UPDATEs of the same
statement, and BOTH duplicate rows would qualify, get the same
value, and trip the unique constraint. (Confirmed by a local docker
postgres test on 2026-06-16.)

The fix is structural, not just cosmetic: the migration MUST be a
two-step CTE so the winners are materialized BEFORE the UPDATE
writes. The CTE pattern below materializes one row per
``(platform, txid)`` group (the row with the oldest ``date`` wins,
tiebreak on ``id`` — the canonical first occurrence) and the UPDATE
joins against this pre-computed set, so the unique constraint is
never violated. Do not inline ``ranked`` into the UPDATE's source,
and do not collapse this into a single ``UPDATE ... FROM (SELECT
... ROW_NUMBER() ...)`` without a CTE — both forms re-introduce the
MVCC bug.

Losers (duplicate rows that did not win) are left with
``transaction_id = NULL``. Postgres unique constraints allow
multiple NULLs, so leaving them NULL is safe. They will not be
dedupable against future re-imports of the same transaction, but
they will not cause any constraint violation either. Operators can
identify losers with the JSON-portable query:

    SELECT id, platform, metadata_json->>'transaction_id' AS md_txid
    FROM revenue_logs
    WHERE transaction_id IS NULL
      AND metadata_json IS NOT NULL
      AND COALESCE(metadata_json->>'transaction_id', '') <> ''

for manual reconciliation. (The JSONB-only ``?`` operator is NOT
used here because the production column is ``JSON``, not ``JSONB``.)

JSON-portable existence check
-----------------------------
The ``metadata_json`` column is declared as ``Column(JSON)`` in the
model, which on Postgres maps to ``JSON`` (not ``JSONB``). The
JSONB-only ``?`` operator is therefore not available. The migration
uses ``COALESCE(metadata_json->>'transaction_id', '') <> ''``,
which works on both JSON and JSONB and handles the case where the
key is missing, null, or an empty string.

Idempotency
-----------
The candidates CTE filters to ``transaction_id IS NULL`` AND excludes
groups that already have a winner (via the ``NOT IN`` subquery on
``(platform, transaction_id)``). After the first run, winners are
excluded from a second run (they already have a non-NULL value), AND
the losers are also excluded because their group already has a
non-NULL row. Re-run is a true no-op (0 rows updated). Safe to re-run.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "2026_06_16_backfill_txid"
down_revision = "2026_06_16_revenue_metadata"  # the column-add migration
branch_labels = ["webhook-idempotency-fix"]  # same line as 2026_05_29_revenue_txid
depends_on = None


# Two-step backfill:
#   1) ``candidates`` CTE: legacy rows that have a usable transaction_id
#      in their metadata_json and no top-level value yet. Uses
#      COALESCE(... ->> ..., '') <> '' so it works on plain JSON
#      without the JSONB-only ``?`` operator. Includes ``date`` so the
#      ``ranked`` CTE doesn't need to JOIN back to revenue_logs.
#   2) ``ranked`` CTE: number the candidates per (platform, txid)
#      group; keep only rn=1 (oldest date, tiebreak on id) for the
#      UPDATE.
#   3) UPDATE joins against ``ranked`` and only writes the winners.
_BACKFILL_SQL = sa.text(
    """
    WITH candidates AS (
        SELECT id,
               platform,
               date,
               metadata_json->>'transaction_id' AS txid
        FROM revenue_logs
        WHERE transaction_id IS NULL
          AND metadata_json IS NOT NULL
          AND COALESCE(metadata_json->>'transaction_id', '') <> ''
          AND (platform, metadata_json->>'transaction_id') NOT IN (
              SELECT platform, transaction_id
              FROM revenue_logs
              WHERE transaction_id IS NOT NULL
          )
    ),
    ranked AS (
        SELECT id,
               txid,
               ROW_NUMBER() OVER (
                   PARTITION BY platform, txid
                   ORDER BY date, id
               ) AS rn
        FROM candidates
    )
    UPDATE revenue_logs AS r
    SET transaction_id = ranked.txid
    FROM ranked
    WHERE r.id = ranked.id
      AND ranked.rn = 1
    """
)


def upgrade() -> None:
    """Backfill revenue_logs.transaction_id from metadata_json."""
    conn = op.get_bind()
    result = conn.execute(_BACKFILL_SQL)
    # alembic surfaces print() to the operator running `alembic upgrade head`
    print(
        f"  [backfill_txid] updated {result.rowcount} revenue_logs rows "
        f"with transaction_id from metadata_json"
    )


def downgrade() -> None:
    """No-op: we do not un-set transaction_id on rollback.

    Un-setting would lose information. If a true rollback is required,
    an operator can issue:
        UPDATE revenue_logs SET transaction_id = NULL
    manually after downgrading.
    """
    pass
