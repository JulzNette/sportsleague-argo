"""add registration fee + payment status

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sportsleague_registrations",
        sa.Column("registration_fee", sa.Numeric(12, 2), nullable=True),
    )
    op.add_column(
        "sportsleague_registrations",
        sa.Column(
            "payment_status",
            sa.String(32),
            nullable=False,
            server_default=sa.text("'Pending'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("sportsleague_registrations", "payment_status")
    op.drop_column("sportsleague_registrations", "registration_fee")
