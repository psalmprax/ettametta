"""add composition_id to nexus_blueprints

Revision ID: g1b2c3d4e5f7
Revises: f1b2c3d4e5f6
Create Date: 2026-04-26 08:15:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = "g1b2c3d4e5f7"
down_revision = "f1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # Handle nexus_blueprints
    nb_columns = [c['name'] for c in inspector.get_columns('nexus_blueprints')]
    
    if 'composition_id' not in nb_columns:
        op.add_column('nexus_blueprints', sa.Column('composition_id', sa.String(), nullable=True, server_default='ViralClip'))
        print("Added composition_id to nexus_blueprints")


def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    nb_columns = [c['name'] for c in inspector.get_columns('nexus_blueprints')]
    if 'composition_id' in nb_columns:
        op.drop_column('nexus_blueprints', 'composition_id')
        print("Dropped composition_id from nexus_blueprints")
