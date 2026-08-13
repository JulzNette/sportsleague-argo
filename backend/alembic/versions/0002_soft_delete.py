"""add deleted_at soft-delete column to business tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = [
    "sportsleague_leagues",
    "sportsleague_seasons",
    "sportsleague_divisions",
    "sportsleague_teams",
    "sportsleague_players",
    "sportsleague_referees",
    "sportsleague_matches",
    "sportsleague_match_results",
    "sportsleague_reports",
]


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(
            table,
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    for table in _TABLES:
        op.drop_column(table, "deleted_at")
