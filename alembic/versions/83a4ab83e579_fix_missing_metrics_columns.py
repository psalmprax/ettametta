"""fix_missing_metrics_columns

Revision ID: 83a4ab83e579
Revises: d410fb0d40a9
Create Date: 2026-05-01 07:08:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = "83a4ab83e579"
down_revision = "d410fb0d40a9"
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    rl_columns = [c["name"] for c in inspector.get_columns("revenue_logs")]
    if "views" in rl_columns and "view_count" not in rl_columns:
        op.alter_column("revenue_logs", "views", new_column_name="view_count")
    elif "view_count" not in rl_columns:
        op.add_column("revenue_logs", sa.Column("view_count", sa.Integer(), nullable=True, server_default="0"))
    cc_columns = [c["name"] for c in inspector.get_columns("content_candidates")]
    if "view_count" not in cc_columns:
        op.add_column("content_candidates", sa.Column("view_count", sa.Integer(), nullable=True, server_default="0"))
    pc_columns = [c["name"] for c in inspector.get_columns("published_content")]
    if "view_count" not in pc_columns:
        op.add_column("published_content", sa.Column("view_count", sa.Integer(), nullable=True, server_default="0"))

def downgrade() -> None:
    pass
