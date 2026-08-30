"""link Player-role accounts to players

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sportsleague_players",
        sa.Column("login_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_sportsleague_players_login_user_id",
        "sportsleague_players", ["login_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_sportsleague_players_login_user_id", table_name="sportsleague_players")
    op.drop_column("sportsleague_players", "login_user_id")
