"""add trial_ends_at to users for 14-day subscription trial

Adds a nullable ``trial_ends_at`` timestamp column to the ``users`` table.
When set and in the future, the user is in an active free trial on the
SOVEREIGN tier. When ``NULL`` or in the past, the user is not in a trial.

New column:
  - trial_ends_at  (DateTime, nullable=True) — when the 14-day trial expires

The migration uses ``op.batch_alter_table`` to be SQLite-safe, matching
the project convention for portability.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026_06_13_trial_ends_at"
down_revision = None  # one-off branch
branch_labels = ["phase-14-trial"]
depends_on = []


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column("trial_ends_at", sa.DateTime(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("trial_ends_at")
