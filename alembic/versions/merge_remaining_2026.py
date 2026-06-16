"""merge all 4 remaining alembic heads on remote production

After the webhook idempotency migration ``2026_05_29_revenue_txid`` was
applied to the production DB on 2026-06-15, four heads remain:

  - 66623ae9808f                            (current applied head on main branch)
  - 2026_05_29_revenue_txid                 (applied; new)
  - 2026_05_29_add_impression_tracking      (work already in DB; not applied)
  - 2026_05_29_analysis_persistence         (work already in DB; not applied)

``alembic upgrade head`` cannot advance past a multi-head DAG, so the
two unapplied branches were ``alembic stamp``-ed as applied (the
columns they would have added already exist on ``affiliate_links`` and
``content_candidates`` respectively) and this merge migration is
applied to consolidate the DAG into a single linear head.

The merge is intentionally a no-op on the schema. ``upgrade()`` and
``downgrade()`` are both ``pass``. The migration's only purpose is to
be a common descendant of all four heads so that ``alembic_version``
can advance to a single revision and future ``alembic upgrade head``
runs are a no-op.

Revision ID note: ``merge_remaining_2026`` is 20 characters to fit
within the ``alembic_version.version_num varchar(32)`` column. The
``2026_05_29_*`` prefix in the parent revisions is what blew the
column width for ``alembic stamp`` on ``impression_tracking``
(33 chars) earlier today.

Verification on w5m8yij9.vm (2026-06-15):
  - affiliate_links.impression_count:     already present (work done)
  - affiliate_links.last_impression_at:    already present (work done)
  - content_candidates.analysis_*:         already present (work done)
  - revenue_logs.transaction_id:           applied via 2026_05_29_revenue_txid
  - revenue_logs.uix_revenue_platform_txid: applied

Future migrations should chain off this revision
(``down_revision = "merge_remaining_2026"``).

Downgrade: a no-op ``pass`` is intentional. Alembic does not support
cleanly unmerging; running ``alembic downgrade -1`` would leave the
DB in a 4-head state. If a true downgrade is needed, manually edit
``alembic_version.version_num`` back to the prior head and downgrade
each branch's head explicitly.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "merge_remaining_2026"
down_revision = (
    "66623ae9808f",
    "2026_05_29_revenue_txid",
    "2026_05_29_add_impression_tracking",
    "2026_05_29_analysis_persistence",
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
    # past a multiple-head state once this is applied.
    pass
