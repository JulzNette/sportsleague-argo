"""add live game-clock fields to match results

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sportsleague_match_results",
        sa.Column("period", sa.Integer(), server_default=sa.text("1"), nullable=False),
    )
    op.add_column(
        "sportsleague_match_results",
        sa.Column("minutes", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column(
        "sportsleague_match_results",
        sa.Column("seconds", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("sportsleague_match_results", "seconds")
    op.drop_column("sportsleague_match_results", "minutes")
    op.drop_column("sportsleague_match_results", "period")
