"""Add discovery metrics to ContentCandidateDB

Revision ID: c8d2e4f5g6h7
Revises: b00605d117b1
Create Date: 2026-02-16 23:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8d2e4f5g6h7'
down_revision: Union[str, Sequence[str], None] = 'b00605d117b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to content_candidates table
    op.add_column('content_candidates', sa.Column('views', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('content_candidates', sa.Column('engagement_score', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('content_candidates', sa.Column('viral_score', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('content_candidates', sa.Column('duration_seconds', sa.Float(), nullable=True, server_default='0.0'))


def downgrade() -> None:
    op.drop_column('content_candidates', 'duration_seconds')
    op.drop_column('content_candidates', 'viral_score')
    op.drop_column('content_candidates', 'engagement_score')
    op.drop_column('content_candidates', 'views')
