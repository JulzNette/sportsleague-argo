-- ============================================================================
-- Sample data â€” one organization, one login per role, and a small set of
-- leagues/seasons/divisions/teams/players/referees/matches/results so the
-- frontend has something real to show immediately after setup.
--
-- Usage: psql -U sportsleague_user -d sportsleague_db -f seed.sql
-- (run schema.sql first)
--
-- All demo users share the password:  Password123!
-- pgcrypto is used only to bcrypt-hash that password with crypt()/gen_salt('bf'),
-- producing a hash the backend's passlib[bcrypt] can verify directly.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
DECLARE
    v_org_id           UUID := '11111111-1111-1111-1111-111111111111';
    v_admin_id         UUID := '22222222-2222-2222-2222-222222222222';
    v_league_admin_id  UUID := '22222222-2222-2222-2222-222222222223';
    v_season_mgr_id    UUID := '22222222-2222-2222-2222-222222222224';
    v_team_mgr_id      UUID := '22222222-2222-2222-2222-222222222225';
    v_referee_user_id  UUID := '22222222-2222-2222-2222-222222222226';
    v_player_user_id   UUID := '22222222-2222-2222-2222-222222222227';
    v_password_hash    VARCHAR := crypt('Password123!', gen_salt('bf'));

    v_league_id  UUID := '33333333-3333-3333-3333-333333333331';
    v_league2_id UUID := '33333333-3333-3333-3333-333333333332';
    v_league3_id UUID := '33333333-3333-3333-3333-333333333333';
    v_league4_id UUID := '33333333-3333-3333-3333-333333333334';
    v_season_id  UUID := '44444444-4444-4444-4444-444444444441';
    v_season2_id UUID := '44444444-4444-4444-4444-444444444442';
    v_div_a_id   UUID := '55555555-5555-5555-5555-555555555551';
    v_div_b_id   UUID := '55555555-5555-5555-5555-555555555552';

    v_tm1 UUID := '66666666-6666-6666-6666-666666666661';
    v_tm2 UUID := '66666666-6666-6666-6666-666666666662';
    v_tm3 UUID := '66666666-6666-6666-6666-666666666663';
    v_tm4 UUID := '66666666-6666-6666-6666-666666666664';

    v_ref1 UUID := '77777777-7777-7777-7777-777777777771';
    v_ref2 UUID := '77777777-7777-7777-7777-777777777772';

    v_m1 UUID := '88888888-8888-8888-8888-888888888881';
    v_m2 UUID := '88888888-8888-8888-8888-888888888882';
    v_m3 UUID := '88888888-8888-8888-8888-888888888883';
BEGIN
    -- Tenant + demo users (one per role)
    INSERT INTO organizations (id, name) VALUES (v_org_id, 'Metro Manila Sports League');

    INSERT INTO users (id, organization_id, email, hashed_password, full_name, role) VALUES
        (v_admin_id,        v_org_id, 'system.administrator@gmail.com', v_password_hash, 'System Administrator', 'System Administrator'),
        (v_league_admin_id, v_org_id, 'league.administrator@gmail.com', v_password_hash, 'League Administrator', 'League Administrator'),
        (v_season_mgr_id,   v_org_id, 'season.manager@gmail.com',       v_password_hash, 'Season Manager',       'Season Manager'),
        (v_team_mgr_id,     v_org_id, 'team.manager@gmail.com',         v_password_hash, 'Team Manager',         'Team Manager'),
        (v_referee_user_id, v_org_id, 'referee@gmail.com',              v_password_hash, 'Referee User',         'Referee'),
        (v_player_user_id,  v_org_id, 'player@gmail.com',               v_password_hash, 'Player User',          'Player');

    -- Leagues
    INSERT INTO sportsleague_leagues (id, organization_id, name, sport_type, description, status, created_by, updated_by) VALUES
        (v_league_id,  v_org_id, 'Barangay Basketball League', 'Basketball', 'Annual inter-barangay competition', 'Active', v_admin_id, v_admin_id),
        (v_league2_id, v_org_id, 'Metro Volleyball Cup',       'Volleyball', 'Open volleyball tournament',         'Active', v_admin_id, v_admin_id),
        (v_league3_id, v_org_id, 'Badminton Club Open',        'Badminton',  'Open division badminton tournament', 'Active', v_admin_id, v_admin_id),
        (v_league4_id, v_org_id, 'Metro Football League',      'Soccer',     'Community football league',          'Active', v_admin_id, v_admin_id);

    -- Seasons
    INSERT INTO sportsleague_seasons (id, organization_id, league_id, name, start_date, end_date, format, status, created_by, updated_by) VALUES
        (v_season_id,  v_org_id, v_league_id,  'Season 1 - 2026', '2026-08-01', '2026-11-30', 'Round Robin', 'Active', v_admin_id, v_admin_id),
        (v_season2_id, v_org_id, v_league2_id, 'Cup Season 1',    '2026-06-01', '2026-09-15', 'Round Robin', 'Active', v_admin_id, v_admin_id);

    -- Divisions
    INSERT INTO sportsleague_divisions (id, organization_id, season_id, name, max_teams, status, created_by, updated_by) VALUES
        (v_div_a_id, v_org_id, v_season_id, 'Division A', 8, 'Active', v_admin_id, v_admin_id),
        (v_div_b_id, v_org_id, v_season_id, 'Division B', 8, 'Active', v_admin_id, v_admin_id);

    -- Teams
    INSERT INTO sportsleague_teams (id, organization_id, division_id, name, coach_name, contact_email, contact_phone, status, created_by, updated_by) VALUES
        (v_tm1, v_org_id, v_div_a_id, 'Red Dragons',   'Jose Reyes',  'jose@redragons.ph',   '09181234567', 'Active', v_admin_id, v_admin_id),
        (v_tm2, v_org_id, v_div_a_id, 'Blue Thunder',  'Mila Santos', 'mila@bluethunder.ph', '09181234568', 'Active', v_admin_id, v_admin_id),
        (v_tm3, v_org_id, v_div_a_id, 'Golden Eagles', 'Ramon Cruz',  'ramon@goldeneagles.ph', '09181234569', 'Active', v_admin_id, v_admin_id),
        (v_tm4, v_org_id, v_div_a_id, 'Iron Wolves',   'Carla Dizon', 'carla@ironwolves.ph', '09181234570', 'Active', v_admin_id, v_admin_id);

    -- Players
    INSERT INTO sportsleague_players (organization_id, team_id, full_name, date_of_birth, position, jersey_number, contact_phone, status, created_by, updated_by) VALUES
        (v_org_id, v_tm1, 'Marco Villanueva', '2001-03-12', 'Guard',   '7',  '09171111111', 'Active', v_admin_id, v_admin_id),
        (v_org_id, v_tm1, 'Enzo Ramos',        '2000-11-02', 'Forward', '11', '09171111112', 'Active', v_admin_id, v_admin_id),
        (v_org_id, v_tm2, 'Dominic Alba',      '1999-07-19', 'Center',  '23', '09171111113', 'Active', v_admin_id, v_admin_id),
        (v_org_id, v_tm2, 'Kevin Uy',          '2002-01-30', 'Guard',   '3',  '09171111114', 'Suspended', v_admin_id, v_admin_id),
        (v_org_id, v_tm3, 'Rafael Torres',     '2001-09-09', 'Forward', '15', '09171111115', 'Active', v_admin_id, v_admin_id),
        (v_org_id, v_tm4, 'Andres Ocampo',     '1998-12-14', 'Center',  '44', '09171111117', 'Inactive', v_admin_id, v_admin_id);

    -- Referees
    INSERT INTO sportsleague_referees (id, organization_id, full_name, license_number, contact_phone, status, created_by, updated_by) VALUES
        (v_ref1, v_org_id, 'Mark Santos', 'REF-2201', '09201111111', 'Active', v_admin_id, v_admin_id),
        (v_ref2, v_org_id, 'Ana Cruz',    'REF-2202', '09201111112', 'Active', v_admin_id, v_admin_id);

    -- Matches (mix of statuses)
    INSERT INTO sportsleague_matches (id, organization_id, season_id, division_id, home_team_id, away_team_id, referee_id, scheduled_date, scheduled_time, venue, round_number, match_type, status, created_by, updated_by) VALUES
        (v_m1, v_org_id, v_season_id, v_div_a_id, v_tm1, v_tm2, v_ref1, '2026-07-14', '14:00', 'Barangay Gym A', 1, 'Regular', 'Completed', v_admin_id, v_admin_id),
        (v_m2, v_org_id, v_season_id, v_div_a_id, v_tm3, v_tm4, v_ref2, '2026-07-14', '16:00', 'Barangay Gym A', 1, 'Regular', 'Completed', v_admin_id, v_admin_id),
        (v_m3, v_org_id, v_season_id, v_div_a_id, v_tm1, v_tm3, v_ref1, '2026-08-11', '14:00', 'Barangay Gym A', 2, 'Regular', 'Scheduled', v_admin_id, v_admin_id);

    -- Results for the two completed matches
    INSERT INTO sportsleague_match_results (organization_id, match_id, home_score, away_score, result_type, notes, submitted_by, created_by, updated_by) VALUES
        (v_org_id, v_m1, 78, 65, 'Normal', 'Clean game, no incidents.', v_ref1, v_admin_id, v_admin_id),
        (v_org_id, v_m2, 60, 60, 'Draw',   '',                          v_ref2, v_admin_id, v_admin_id);
END $$;
