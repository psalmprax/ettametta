"""Merge multiple heads

Revision ID: merge_heads_2026
Revises: 001_create_user_table, add_user_id_monitored_niches, b2c3d4e5f6g7
Create Date: 2026-04-11 13:40:00

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = 'merge_heads_2026'
down_revision: Union[str, Sequence[str], None] = ('001_create_user_table', 'add_user_id_monitored_niches', 'b2c3d4e5f6g7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge heads."""
    pass


def downgrade() -> None:
    """Merge heads."""
    pass
