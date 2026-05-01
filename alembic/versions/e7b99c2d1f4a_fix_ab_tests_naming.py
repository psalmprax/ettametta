"""fix_ab_tests_naming

Revision ID: e7b99c2d1f4a
Revises: 83a4ab83e579
Create Date: 2026-05-01 15:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = "e7b99c2d1f4a"
down_revision = "83a4ab83e579"
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [c["name"] for c in inspector.get_columns("ab_tests")]
    
    # Rename columns to match models.py
    if "variant_a_views" in columns:
        op.alter_column("ab_tests", "variant_a_views", new_column_name="variant_a_view_count")
    if "variant_b_views" in columns:
        op.alter_column("ab_tests", "variant_b_views", new_column_name="variant_b_view_count")
    if "variant_a_clicks" in columns:
        op.alter_column("ab_tests", "variant_a_clicks", new_column_name="variant_a_click_count")
    if "variant_b_clicks" in columns:
        op.alter_column("ab_tests", "variant_b_clicks", new_column_name="variant_b_click_count")
    if "variant_a_conversions" in columns:
        op.alter_column("ab_tests", "variant_a_conversions", new_column_name="variant_a_conversion_count")
    if "variant_b_conversions" in columns:
        op.alter_column("ab_tests", "variant_b_conversions", new_column_name="variant_b_conversion_count")

def downgrade() -> None:
    pass
