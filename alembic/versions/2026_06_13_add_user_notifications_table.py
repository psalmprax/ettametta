"""add user_notifications table for in-app notifications

Adds a ``user_notifications`` table for the in-app notification system.
Used by the NotificationCenter frontend component and the Stripe webhook
(``subscription.deleted``) to surface billing events and other system
notifications directly to users.

New table:
  - user_notifications: id (PK), user_id (FK→users), type, title, message,
                        link, read (bool), created_at
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026_06_13_user_notifications"
down_revision = None  # one-off branch
branch_labels = ["phase-14-notifications"]
depends_on = []


def upgrade() -> None:
    op.create_table(
        "user_notifications",
        sa.Column("id", sa.String(36), primary_key=True, index=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("type", sa.String(20), nullable=False, server_default="system"),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.String(500), nullable=True),
        sa.Column("link", sa.String(500), nullable=True),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("user_notifications")
