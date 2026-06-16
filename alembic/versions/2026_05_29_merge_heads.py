"""merge multiple alembic heads

The production database has four divergent heads (verified via
``alembic heads`` on 2026-06-15 against w5m8yij9.vm):

  - 66623ae9808f                       (current applied head on main branch)
  - 2026_05_29_analysis_persistence    (orphan; down_revision=None)
  - 2026_05_29_add_impression_tracking (new branch off main)
  - 2026_05_29_revenue_txid            (new branch off e7b99c2d1f4a)

A merge migration is required before ``alembic upgrade head`` will
succeed. This file is a no-op on the schema: ``upgrade()`` and
``downgrade()`` are both empty. The migration's only purpose is to be a
common descendant of all four heads so that the linear ``alembic_version``
pointer can advance to a single revision.

After this migration is applied, ``alembic upgrade head`` will:

  1. Apply the merge (no schema change).
  2. Walk each branch from the merge down to any unrun migration.
  3. Apply ``2026_05_29_revenue_txid`` which adds
     ``revenue_logs.transaction_id`` + the
     ``uix_revenue_platform_txid`` unique constraint (Phase webhook
     idempotency fix).
  4. Apply ``2026_05_29_add_impression_tracking`` (its own concern).
  5. Leave the ``2026_05_29_analysis_persistence`` branch merged in
     without running it (it was previously not in the linear chain).

The merge is intentionally minimal: it does NOT consolidate or rewrite
any of the four branches. Future maintainers can prune the orphan
analysis_persistence branch separately if desired.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026_05_29_merge_heads"
down_revision = (
    "66623ae9808f",
    "2026_05_29_analysis_persistence",
    "2026_05_29_add_impression_tracking",
    "2026_05_29_revenue_txid",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op merge: the four branch heads all point at this revision as a
    # common descendant. The schema changes are owned by each branch's
    # own migration; we only consolidate the alembic_version pointer.
    pass


def downgrade() -> None:
    # No-op merge: downgrading would split the branches back apart. We
    # intentionally don't try to "unmerge" — alembic will refuse to move
    # past a multiple-head state once this is applied. If a true
    # downgrade is needed, manually edit alembic_version and downgrade
    # each branch's head explicitly.
    pass
