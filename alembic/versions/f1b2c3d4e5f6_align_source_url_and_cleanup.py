"""align source_url and cleanup content_candidates with idempotency

Revision ID: f1b2c3d4e5f6
Revises: 260bae1bf65b
Create Date: 2026-04-25 21:35:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = "f1b2c3d4e5f6"
down_revision = "260bae1bf65b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # 1. Handle content_candidates
    cc_columns = [c['name'] for c in inspector.get_columns('content_candidates')]
    
    if 'url' in cc_columns and 'source_url' not in cc_columns:
        op.alter_column('content_candidates', 'url', new_column_name='source_url')
        print("Renamed url -> source_url in content_candidates")
    elif 'source_url' not in cc_columns:
        # If neither exists, add source_url (shouldn't happen based on audit)
        op.add_column('content_candidates', sa.Column('source_url', sa.String(), nullable=True))
        print("Added source_url to content_candidates")

    if 'views' in cc_columns:
        op.drop_column('content_candidates', 'views')
        print("Dropped legacy 'views' from content_candidates")
        
    if 'engagement_rate' in cc_columns:
        op.drop_column('content_candidates', 'engagement_rate')
        print("Dropped legacy 'engagement_rate' from content_candidates")

    # 2. Handle published_content
    pc_columns = [c['name'] for c in inspector.get_columns('published_content')]
    
    if 'url' in pc_columns and 'source_url' not in pc_columns:
        op.alter_column('published_content', 'url', new_column_name='source_url')
        print("Renamed url -> source_url in published_content")
    elif 'source_url' not in pc_columns:
        op.add_column('published_content', sa.Column('source_url', sa.String(), nullable=True))
        print("Added source_url to published_content")


def downgrade() -> None:
    # Minimal downgrade support for critical columns
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    cc_columns = [c['name'] for c in inspector.get_columns('content_candidates')]
    if 'source_url' in cc_columns and 'url' not in cc_columns:
        op.alter_column('content_candidates', 'source_url', new_column_name='url')
        
    pc_columns = [c['name'] for c in inspector.get_columns('published_content')]
    if 'source_url' in pc_columns and 'url' not in pc_columns:
        op.alter_column('published_content', 'source_url', new_column_name='url')
