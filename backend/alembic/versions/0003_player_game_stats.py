"""add player game statistics table

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sportsleague_player_game_stats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "match_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sportsleague_matches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "player_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sportsleague_players.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sportsleague_teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("points", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("assists", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("fouls", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("rebounds", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("steals", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "organization_id", "match_id", "player_id",
            name="uq_sportsleague_player_game_stats_match_player",
        ),
    )
    op.create_index(
        "ix_sportsleague_player_game_stats_organization_id",
        "sportsleague_player_game_stats", ["organization_id"],
    )
    op.create_index(
        "ix_sportsleague_player_game_stats_match_id",
        "sportsleague_player_game_stats", ["match_id"],
    )
    op.create_index(
        "ix_sportsleague_player_game_stats_player_id",
        "sportsleague_player_game_stats", ["player_id"],
    )
    op.create_index(
        "ix_sportsleague_player_game_stats_team_id",
        "sportsleague_player_game_stats", ["team_id"],
    )


def downgrade() -> None:
    op.drop_table("sportsleague_player_game_stats")
