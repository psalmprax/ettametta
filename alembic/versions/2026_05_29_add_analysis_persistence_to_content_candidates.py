"""add analysis persistence columns to content_candidates

Phase 10-01 of the Discovery → Analysis → Video pipeline fix. Adds 6 nullable
columns to ``content_candidates`` so that ``AnalysisReport`` can be persisted
alongside the candidate. All columns are nullable so existing rows are not
affected and the migration is purely additive (no data loss, no rewrites).

New columns:
  - analysis_task_id       (String(64), indexed) — Celery task ID for lookup
  - analysis_status        (String(16))          — PENDING|RUNNING|COMPLETED|FAILED
  - analysis_payload       (JSON)                — serialized AnalysisReport
  - analysis_persisted_at  (DateTime)            — when we wrote analysis_payload
  - viral_score_velocity   (Float)               — denormalized hot field
  - recommended_style      (String(64))          — denormalized hot field

The migration is wrapped in ``op.batch_alter_table`` to be SQLite-safe, since
the project supports both SQLite (local dev) and Postgres (production).
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026_05_29_analysis_persistence"
down_revision = None  # one-off branch; alembic picks the head from the FS
branch_labels = ["phase-10-pipeline-fixes"]
depends_on = []


def upgrade() -> None:
    with op.batch_alter_table("content_candidates") as batch_op:
        batch_op.add_column(
            sa.Column("analysis_task_id", sa.String(length=64), nullable=True)
        )
        batch_op.add_column(
            sa.Column("analysis_status", sa.String(length=16), nullable=True)
        )
        batch_op.add_column(
            sa.Column("analysis_payload", sa.JSON(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("analysis_persisted_at", sa.DateTime(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("viral_score_velocity", sa.Float(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("recommended_style", sa.String(length=64), nullable=True)
        )
        batch_op.create_index(
            "ix_content_candidates_analysis_task_id",
            ["analysis_task_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("content_candidates") as batch_op:
        batch_op.drop_index("ix_content_candidates_analysis_task_id")
        batch_op.drop_column("recommended_style")
        batch_op.drop_column("viral_score_velocity")
        batch_op.drop_column("analysis_persisted_at")
        batch_op.drop_column("analysis_payload")
        batch_op.drop_column("analysis_status")
        batch_op.drop_column("analysis_task_id")
