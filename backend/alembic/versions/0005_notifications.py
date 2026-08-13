"""add notifications table

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sportsleague_notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("registration_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "organization_id", "user_id", "type", "registration_id",
            name="uq_sportsleague_notifications_user_type_registration",
        ),
    )
    op.create_index(
        "ix_sportsleague_notifications_organization_id",
        "sportsleague_notifications", ["organization_id"],
    )
    op.create_index(
        "ix_sportsleague_notifications_user_id",
        "sportsleague_notifications", ["user_id"],
    )
    op.create_index(
        "ix_sportsleague_notifications_registration_id",
        "sportsleague_notifications", ["registration_id"],
    )
    op.create_index(
        "ix_sportsleague_notifications_is_read",
        "sportsleague_notifications", ["is_read"],
    )


def downgrade() -> None:
    op.drop_table("sportsleague_notifications")
