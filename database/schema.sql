-- ============================================================
-- Sports League Management — reference schema (PostgreSQL 14)
--
-- SOURCE OF TRUTH: backend/alembic/versions/0001_initial_schema.py
-- This file is a plain-SQL mirror of that migration, provided so you
-- can inspect or apply the schema without touching Python/Alembic at
-- all (e.g. `psql -f schema.sql`). If you ever change the migration,
-- regenerate this file to match — don't hand-edit them separately.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- gen_random_uuid(), if you want DB-side defaults

-- ---- Local sandbox stub tables (NOT part of the module deliverable) ----
-- The real Argo platform owns organizations/users elsewhere; these exist
-- only so this module can be run and demoed standalone.
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(64) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_users_organization_id ON users(organization_id);

-- ---- sportsleague_leagues ----
CREATE TABLE sportsleague_leagues (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    sport_type VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'Active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL,
    updated_by UUID NOT NULL,
    CONSTRAINT uq_sportsleague_leagues_org_name UNIQUE (organization_id, name)
);
CREATE INDEX ix_sportsleague_leagues_organization_id ON sportsleague_leagues(organization_id);

-- ---- sportsleague_seasons ----
CREATE TABLE sportsleague_seasons (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    league_id UUID NOT NULL REFERENCES sportsleague_leagues(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    format VARCHAR(50) NOT NULL DEFAULT 'Round Robin',
    status VARCHAR(32) NOT NULL DEFAULT 'Draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL,
    updated_by UUID NOT NULL,
    CONSTRAINT uq_sportsleague_seasons_org_league_name UNIQUE (organization_id, league_id, name)
);
CREATE INDEX ix_sportsleague_seasons_organization_id ON sportsleague_seasons(organization_id);
CREATE INDEX ix_sportsleague_seasons_league_id ON sportsleague_seasons(league_id);

-- ---- sportsleague_divisions ----
CREATE TABLE sportsleague_divisions (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    season_id UUID NOT NULL REFERENCES sportsleague_seasons(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    max_teams INTEGER NOT NULL DEFAULT 8,
    status VARCHAR(32) NOT NULL DEFAULT 'Active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL,
    updated_by UUID NOT NULL,
    CONSTRAINT uq_sportsleague_divisions_org_season_name UNIQUE (organization_id, season_id, name)
);
CREATE INDEX ix_sportsleague_divisions_organization_id ON sportsleague_divisions(organization_id);
CREATE INDEX ix_sportsleague_divisions_season_id ON sportsleague_divisions(season_id);

-- ---- sportsleague_teams ----
CREATE TABLE sportsleague_teams (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    division_id UUID NOT NULL REFERENCES sportsleague_divisions(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    coach_name VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(32),
    status VARCHAR(32) NOT NULL DEFAULT 'Active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL,
    updated_by UUID NOT NULL,
    CONSTRAINT uq_sportsleague_teams_org_division_name UNIQUE (organization_id, division_id, name)
);
CREATE INDEX ix_sportsleague_teams_organization_id ON sportsleague_teams(organization_id);
CREATE INDEX ix_sportsleague_teams_division_id ON sportsleague_teams(division_id);

-- ---- sportsleague_players ----
CREATE TABLE sportsleague_players (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES sportsleague_teams(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    date_of_birth DATE,
    position VARCHAR(100),
    jersey_number VARCHAR(10) NOT NULL,
    contact_phone VARCHAR(32),
    status VARCHAR(32) NOT NULL DEFAULT 'Active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL,
    updated_by UUID NOT NULL,
    CONSTRAINT uq_sportsleague_players_org_team_jersey UNIQUE (organization_id, team_id, jersey_number)
);
CREATE INDEX ix_sportsleague_players_organization_id ON sportsleague_players(organization_id);
CREATE INDEX ix_sportsleague_players_team_id ON sportsleague_players(team_id);

-- ---- sportsleague_referees ----
CREATE TABLE sportsleague_referees (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    license_number VARCHAR(64) NOT NULL,
    contact_phone VARCHAR(32),
    status VARCHAR(32) NOT NULL DEFAULT 'Active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL,
    updated_by UUID NOT NULL,
    CONSTRAINT uq_sportsleague_referees_org_license UNIQUE (organization_id, license_number)
);
CREATE INDEX ix_sportsleague_referees_organization_id ON sportsleague_referees(organization_id);

-- ---- sportsleague_matches ----
CREATE TABLE sportsleague_matches (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    season_id UUID NOT NULL REFERENCES sportsleague_seasons(id) ON DELETE CASCADE,
    division_id UUID NOT NULL REFERENCES sportsleague_divisions(id) ON DELETE CASCADE,
    home_team_id UUID NOT NULL REFERENCES sportsleague_teams(id) ON DELETE CASCADE,
    away_team_id UUID NOT NULL REFERENCES sportsleague_teams(id) ON DELETE CASCADE,
    referee_id UUID REFERENCES sportsleague_referees(id) ON DELETE SET NULL,
    scheduled_date DATE NOT NULL,
    scheduled_time TIME NOT NULL,
    venue VARCHAR(255) NOT NULL,
    round_number INTEGER NOT NULL DEFAULT 0,
    match_type VARCHAR(32) NOT NULL DEFAULT 'Regular',
    status VARCHAR(32) NOT NULL DEFAULT 'Scheduled',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL,
    updated_by UUID NOT NULL,
    CONSTRAINT ck_sportsleague_matches_distinct_teams CHECK (home_team_id <> away_team_id)
);
CREATE INDEX ix_sportsleague_matches_organization_id ON sportsleague_matches(organization_id);
CREATE INDEX ix_sportsleague_matches_season_id ON sportsleague_matches(season_id);
CREATE INDEX ix_sportsleague_matches_division_id ON sportsleague_matches(division_id);
CREATE INDEX ix_sportsleague_matches_home_team_id ON sportsleague_matches(home_team_id);
CREATE INDEX ix_sportsleague_matches_away_team_id ON sportsleague_matches(away_team_id);
CREATE INDEX ix_sportsleague_matches_referee_id ON sportsleague_matches(referee_id);

-- ---- sportsleague_match_results ----
CREATE TABLE sportsleague_match_results (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    match_id UUID NOT NULL UNIQUE REFERENCES sportsleague_matches(id) ON DELETE CASCADE,
    home_score INTEGER NOT NULL DEFAULT 0,
    away_score INTEGER NOT NULL DEFAULT 0,
    result_type VARCHAR(32) NOT NULL DEFAULT 'Normal',
    forfeit_winner_team_id UUID REFERENCES sportsleague_teams(id) ON DELETE SET NULL,
    notes TEXT,
    submitted_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL,
    updated_by UUID NOT NULL
);
CREATE INDEX ix_sportsleague_match_results_organization_id ON sportsleague_match_results(organization_id);

-- ---- sportsleague_reports ----
CREATE TABLE sportsleague_reports (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    season_id UUID,
    division_id UUID,
    generated_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL,
    updated_by UUID NOT NULL
);
CREATE INDEX ix_sportsleague_reports_organization_id ON sportsleague_reports(organization_id);
