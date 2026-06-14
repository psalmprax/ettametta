"""Add metadata_json column to ab_tests for variant job tracking

Revision ID: 2026_06_13_add_metadata_json_ab
Revises: efb25ef5b164
Create Date: 2026-06-13 14:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2026_06_13_add_metadata_json_ab'
down_revision: Union[str, Sequence[str], None] = 'efb25ef5b164'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add metadata_json column to ab_tests."""
    with op.batch_alter_table('ab_tests') as batch_op:
        batch_op.add_column(
            sa.Column('metadata_json', sa.JSON(), nullable=True)
        )


def downgrade() -> None:
    """Remove metadata_json column from ab_tests."""
    with op.batch_alter_table('ab_tests') as batch_op:
        batch_op.drop_column('metadata_json')
