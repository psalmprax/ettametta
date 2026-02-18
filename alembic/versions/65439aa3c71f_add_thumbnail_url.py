"""add_thumbnail_url

Revision ID: 65439aa3c71f
Revises: c8d2e4f5g6h7
Create Date: 2026-02-17 00:28:17.345182

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65439aa3c71f'
down_revision: Union[str, Sequence[str], None] = 'c8d2e4f5g6h7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
