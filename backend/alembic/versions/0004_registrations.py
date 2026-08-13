"""add league registration workflow tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sportsleague_registrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "division_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sportsleague_divisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("team_name", sa.String(255), nullable=False),
        sa.Column("coach_name", sa.String(255), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("contact_phone", sa.String(32), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'Pending'")),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "organization_id", "division_id", "team_name",
            name="uq_sportsleague_registrations_org_division_team",
        ),
    )
    op.create_index(
        "ix_sportsleague_registrations_organization_id",
        "sportsleague_registrations", ["organization_id"],
    )
    op.create_index(
        "ix_sportsleague_registrations_division_id",
        "sportsleague_registrations", ["division_id"],
    )

    op.create_table(
        "sportsleague_registration_players",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "registration_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sportsleague_registrations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("position", sa.String(100), nullable=True),
        sa.Column("jersey_number", sa.String(10), nullable=False),
        sa.Column("contact_phone", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "organization_id", "registration_id", "jersey_number",
            name="uq_sportsleague_reg_players_reg_jersey",
        ),
    )
    op.create_index(
        "ix_sportsleague_registration_players_organization_id",
        "sportsleague_registration_players", ["organization_id"],
    )
    op.create_index(
        "ix_sportsleague_registration_players_registration_id",
        "sportsleague_registration_players", ["registration_id"],
    )

    op.create_table(
        "sportsleague_registration_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "registration_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sportsleague_registrations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("player_full_name", sa.String(255), nullable=True),
        sa.Column("document_type", sa.String(255), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_sportsleague_registration_documents_organization_id",
        "sportsleague_registration_documents", ["organization_id"],
    )
    op.create_index(
        "ix_sportsleague_registration_documents_registration_id",
        "sportsleague_registration_documents", ["registration_id"],
    )


def downgrade() -> None:
    op.drop_table("sportsleague_registration_documents")
    op.drop_table("sportsleague_registration_players")
    op.drop_table("sportsleague_registrations")
