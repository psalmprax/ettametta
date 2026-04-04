"""Add user_id to monitored_niches

Revision ID: add_user_id_monitored_niches
Revises: a1b2c3d4e5f
Create Date: 2026-04-04 14:50:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_user_id_monitored_niches"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("monitored_niches", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_monitored_niches_user_id"),
        "monitored_niches",
        ["user_id"],
        unique=False,
    )
    op.create_foreign_key(None, "monitored_niches", "users", ["user_id"], ["id"])
    op.create_unique_constraint(
        "uix_user_niche", "monitored_niches", ["user_id", "niche"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uix_user_niche", "monitored_niches", type_="unique")
    op.drop_constraint(None, "monitored_niches", type_="foreignkey")
    op.drop_index(op.f("ix_monitored_niches_user_id"), table_name="monitored_niches")
    op.drop_column("monitored_niches", "user_id")
