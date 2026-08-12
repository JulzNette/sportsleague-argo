"""initial schema - stub tenant tables + sportsleague_ module tables

Revision ID: 0001
Revises:
Create Date: 2026-08-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_columns():
    """created_at/updated_at/created_by/updated_by, shared by every business table."""
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=False),
    ]


def upgrade() -> None:
    # ---- LOCAL SANDBOX STUB TABLES (not part of the module deliverable) ----
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(64), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_organization_id", "users", ["organization_id"])

    # ---- sportsleague_leagues ----
    op.create_table(
        "sportsleague_leagues",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sport_type", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="Active"),
        *_audit_columns(),
        sa.UniqueConstraint("organization_id", "name", name="uq_sportsleague_leagues_org_name"),
    )
    op.create_index("ix_sportsleague_leagues_organization_id", "sportsleague_leagues", ["organization_id"])

    # ---- sportsleague_seasons ----
    op.create_table(
        "sportsleague_seasons",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "league_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sportsleague_leagues.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("format", sa.String(50), nullable=False, server_default="Round Robin"),
        sa.Column("status", sa.String(32), nullable=False, server_default="Draft"),
        *_audit_columns(),
        sa.UniqueConstraint("organization_id", "league_id", "name", name="uq_sportsleague_seasons_org_league_name"),
    )
    op.create_index("ix_sportsleague_seasons_organization_id", "sportsleague_seasons", ["organization_id"])
    op.create_index("ix_sportsleague_seasons_league_id", "sportsleague_seasons", ["league_id"])

    # ---- sportsleague_divisions ----
    op.create_table(
        "sportsleague_divisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "season_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sportsleague_seasons.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("max_teams", sa.Integer, nullable=False, server_default="8"),
        sa.Column("status", sa.String(32), nullable=False, server_default="Active"),
        *_audit_columns(),
        sa.UniqueConstraint("organization_id", "season_id", "name", name="uq_sportsleague_divisions_org_season_name"),
    )
    op.create_index("ix_sportsleague_divisions_organization_id", "sportsleague_divisions", ["organization_id"])
    op.create_index("ix_sportsleague_divisions_season_id", "sportsleague_divisions", ["season_id"])

    # ---- sportsleague_teams ----
    op.create_table(
        "sportsleague_teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "division_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sportsleague_divisions.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("coach_name", sa.String(255), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("contact_phone", sa.String(32), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="Active"),
        *_audit_columns(),
        sa.UniqueConstraint("organization_id", "division_id", "name", name="uq_sportsleague_teams_org_division_name"),
    )
    op.create_index("ix_sportsleague_teams_organization_id", "sportsleague_teams", ["organization_id"])
    op.create_index("ix_sportsleague_teams_division_id", "sportsleague_teams", ["division_id"])

    # ---- sportsleague_players ----
    op.create_table(
        "sportsleague_players",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "team_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sportsleague_teams.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("date_of_birth", sa.Date, nullable=True),
        sa.Column("position", sa.String(100), nullable=True),
        sa.Column("jersey_number", sa.String(10), nullable=False),
        sa.Column("contact_phone", sa.String(32), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="Active"),
        *_audit_columns(),
        sa.UniqueConstraint(
            "organization_id", "team_id", "jersey_number", name="uq_sportsleague_players_org_team_jersey"
        ),
    )
    op.create_index("ix_sportsleague_players_organization_id", "sportsleague_players", ["organization_id"])
    op.create_index("ix_sportsleague_players_team_id", "sportsleague_players", ["team_id"])

    # ---- sportsleague_referees ----
    op.create_table(
        "sportsleague_referees",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("license_number", sa.String(64), nullable=False),
        sa.Column("contact_phone", sa.String(32), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="Active"),
        *_audit_columns(),
        sa.UniqueConstraint("organization_id", "license_number", name="uq_sportsleague_referees_org_license"),
    )
    op.create_index("ix_sportsleague_referees_organization_id", "sportsleague_referees", ["organization_id"])

    # ---- sportsleague_matches ----
    op.create_table(
        "sportsleague_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "season_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sportsleague_seasons.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "division_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sportsleague_divisions.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "home_team_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sportsleague_teams.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "away_team_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sportsleague_teams.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "referee_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sportsleague_referees.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("scheduled_date", sa.Date, nullable=False),
        sa.Column("scheduled_time", sa.Time, nullable=False),
        sa.Column("venue", sa.String(255), nullable=False),
        sa.Column("round_number", sa.Integer, nullable=False, server_default="0"),
        sa.Column("match_type", sa.String(32), nullable=False, server_default="Regular"),
        sa.Column("status", sa.String(32), nullable=False, server_default="Scheduled"),
        *_audit_columns(),
        sa.CheckConstraint("home_team_id <> away_team_id", name="ck_sportsleague_matches_distinct_teams"),
    )
    op.create_index("ix_sportsleague_matches_organization_id", "sportsleague_matches", ["organization_id"])
    op.create_index("ix_sportsleague_matches_season_id", "sportsleague_matches", ["season_id"])
    op.create_index("ix_sportsleague_matches_division_id", "sportsleague_matches", ["division_id"])
    op.create_index("ix_sportsleague_matches_home_team_id", "sportsleague_matches", ["home_team_id"])
    op.create_index("ix_sportsleague_matches_away_team_id", "sportsleague_matches", ["away_team_id"])
    op.create_index("ix_sportsleague_matches_referee_id", "sportsleague_matches", ["referee_id"])

    # ---- sportsleague_match_results ----
    op.create_table(
        "sportsleague_match_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "match_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sportsleague_matches.id", ondelete="CASCADE"), nullable=False, unique=True,
        ),
        sa.Column("home_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("away_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("result_type", sa.String(32), nullable=False, server_default="Normal"),
        sa.Column(
            "forfeit_winner_team_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sportsleague_teams.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True), nullable=False),
        *_audit_columns(),
    )
    op.create_index("ix_sportsleague_match_results_organization_id", "sportsleague_match_results", ["organization_id"])

    # ---- sportsleague_reports ----
    op.create_table(
        "sportsleague_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("season_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("division_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("generated_by", postgresql.UUID(as_uuid=True), nullable=False),
        *_audit_columns(),
    )
    op.create_index("ix_sportsleague_reports_organization_id", "sportsleague_reports", ["organization_id"])


def downgrade() -> None:
    op.drop_table("sportsleague_reports")
    op.drop_table("sportsleague_match_results")
    op.drop_table("sportsleague_matches")
    op.drop_table("sportsleague_referees")
    op.drop_table("sportsleague_players")
    op.drop_table("sportsleague_teams")
    op.drop_table("sportsleague_divisions")
    op.drop_table("sportsleague_seasons")
    op.drop_table("sportsleague_leagues")
    op.drop_table("users")
    op.drop_table("organizations")
