"""
Standings are always recomputed from completed match results - see
app/services/standings.py. These tests pin down the points model, forfeit
handling, non-completed filtering, and the read endpoint.
"""
from app.services.standings import compute_standings


def test_standings_points_and_sorting(dbsession, org, season_division_teams, add_match):
    season, division, teams = season_division_teams
    t = lambda name: teams[name]

    add_match(season, division, t("A"), t("B"), org_id=org.id, home_score=70, away_score=65)
    add_match(season, division, t("C"), t("D"), org_id=org.id, home_score=60, away_score=60)
    add_match(season, division, t("A"), t("C"), org_id=org.id, home_score=50, away_score=80)

    rows = compute_standings(dbsession, organization_id=org.id, season_id=season.id)
    by_name = {r["team_name"]: r for r in rows}

    assert [r["team_name"] for r in rows] == ["Team C", "Team A", "Team D", "Team B"]
    assert by_name["Team C"]["points"] == 4   # win (3) + draw (1)
    assert by_name["Team A"]["points"] == 3   # win + loss
    assert by_name["Team D"]["points"] == 1   # draw only
    assert by_name["Team B"]["points"] == 0   # loss only
    assert by_name["Team A"]["wins"] == 1 and by_name["Team A"]["losses"] == 1
    assert by_name["Team C"]["draws"] == 1


def test_standings_forfeit_counts_as_win_for_winner(dbsession, org, season_division_teams, add_match):
    season, division, teams = season_division_teams
    t = lambda name: teams[name]

    add_match(season, division, t("A"), t("B"), org_id=org.id,
              result_type="Forfeit", forfeit_winner_team_id=t("A").id, home_score=0, away_score=0)

    rows = compute_standings(dbsession, organization_id=org.id, season_id=season.id)
    by_name = {r["team_name"]: r for r in rows}

    assert by_name["Team A"]["points"] == 3 and by_name["Team A"]["wins"] == 1
    assert by_name["Team B"]["points"] == 0 and by_name["Team B"]["losses"] == 1
    assert by_name["Team A"]["matches_played"] == 1
    # Forfeits don't add to either team's scored points total.
    assert by_name["Team A"]["points_for"] == 0
    assert by_name["Team B"]["points_against"] == 0


def test_standings_ignores_non_completed_matches(dbsession, org, season_division_teams, add_match):
    season, division, teams = season_division_teams
    t = lambda name: teams[name]

    add_match(season, division, t("A"), t("B"), org_id=org.id, home_score=99, away_score=0)
    add_match(season, division, t("C"), t("D"), org_id=org.id,
              status="Scheduled", home_score=99, away_score=99)

    rows = compute_standings(dbsession, organization_id=org.id, season_id=season.id)

    assert len(rows) == 2
    assert {r["team_name"] for r in rows} == {"Team A", "Team B"}


def test_standings_endpoint_returns_table(client, dbsession, org, season_division_teams, add_match):
    season, division, teams = season_division_teams
    t = lambda name: teams[name]
    add_match(season, division, t("A"), t("B"), org_id=org.id, home_score=70, away_score=65)

    reg = client.post("/api/v1/auth/register", json={
        "full_name": "Viewer One", "email": "viewer.one@example.com", "password": "password123",
    })
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    res = client.get(
        "/api/v1/standings",
        params={"season_id": str(season.id), "division_id": str(division.id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    rows = res.json()
    assert len(rows) == 2
    assert rows[0]["team_name"] == "Team A"
    assert rows[0]["points"] == 3
    assert rows[0]["points_for"] == 70
    assert rows[0]["points_against"] == 65
    assert rows[0]["point_differential"] == 5
    assert rows[0]["win_percentage"] == 100.0
    assert rows[0]["rank"] == 1
    assert set(rows[0].keys()) == {
        "team_id", "team_name", "matches_played", "wins", "losses", "draws", "points",
        "points_for", "points_against", "point_differential", "win_percentage", "rank",
    }
