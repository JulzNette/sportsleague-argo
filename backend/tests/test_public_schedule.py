"""Public match schedule endpoint used by the landing page (no auth)."""


def test_public_schedule_returns_matches_without_auth(client, season_division_teams, org, add_match):
    season, division, teams = season_division_teams
    add_match(
        season, division, teams["A"], teams["B"],
        org_id=org.id, home_score=10, away_score=8,
    )

    res = client.get("/api/v1/matches/public")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    row = body[0]
    assert row["home_team"] == "Team A"
    assert row["away_team"] == "Team B"
    assert row["division"] == "Open"
    assert row["status"] == "Completed"
    assert row["home_score"] == 10
    assert row["away_score"] == 8


def test_public_schedule_empty_when_no_matches(client):
    res = client.get("/api/v1/matches/public")
    assert res.status_code == 200
    assert res.json() == []
