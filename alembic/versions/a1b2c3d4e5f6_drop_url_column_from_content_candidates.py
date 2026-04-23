"""drop legacy url column from content_candidates

Revision ID: a1b2c3d4e5f6
Revises: 86ebe6287aea
Create Date: 2026-04-23 13:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str = "86ebe6287aea"
branch_labels: None = None
depends_on: None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column("content_candidates", "url")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("content_candidates", sa.Column("url", sa.String(), nullable=True))
