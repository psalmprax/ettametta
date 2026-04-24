"""Merge multiple heads

Revision ID: efb25ef5b164
Revises: a1b2c3d4e5f6, ee8627d8341b
Create Date: 2026-04-23 17:56:10.516149

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'efb25ef5b164'
down_revision: Union[str, Sequence[str], None] = ('a1b2c3d4e5f6', 'ee8627d8341b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
