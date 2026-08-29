"""add app settings + division fee overrides

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sportsleague_app_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.UniqueConstraint("organization_id", "key", name="uq_sportsleague_app_settings_org_key"),
    )
    op.create_index(
        "ix_sportsleague_app_settings_organization_id",
        "sportsleague_app_settings", ["organization_id"],
    )

    op.create_table(
        "sportsleague_division_fees",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("division_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sportsleague_divisions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("registration_fee", sa.Numeric(12, 2), nullable=False),
        sa.UniqueConstraint("division_id", name="uq_sportsleague_division_fees_division"),
    )
    op.create_index(
        "ix_sportsleague_division_fees_organization_id",
        "sportsleague_division_fees", ["organization_id"],
    )
    op.create_index(
        "ix_sportsleague_division_fees_division_id",
        "sportsleague_division_fees", ["division_id"],
    )


def downgrade() -> None:
    op.drop_table("sportsleague_division_fees")
    op.drop_table("sportsleague_app_settings")
