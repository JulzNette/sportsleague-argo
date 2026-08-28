"""Public match schedule endpoint used by the landing page (no auth)."""


def test_public_schedule_returns_matches_without_auth(client, season_division_teams, org, add_match):
    season, division, teams = season_division_teams
    add_match(
        season, division, teams["A"], teams["B"],
        org_id=org.id, home_score=10, away_score=8, status="Scheduled",
    )

    res = client.get("/api/v1/matches/public")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    row = body[0]
    assert row["home_team"] == "Team A"
    assert row["away_team"] == "Team B"
    assert row["division"] == "Open"
    assert row["status"] == "Scheduled"


def test_public_schedule_excludes_completed_and_non_basketball(
    client, season_division_teams, org, add_match, dbsession
):
    from datetime import date
    from app.models.league import League
    from app.models.season import Season
    from app.models.division import Division
    from app.models.team import Team

    season, division, teams = season_division_teams
    add_match(season, division, teams["A"], teams["B"], org_id=org.id, status="Completed")

    vball_league = League(organization_id=org.id, name="VLeague", sport_type="Volleyball",
                          status="Active", created_by=org.id, updated_by=org.id)
    dbsession.add(vball_league)
    dbsession.flush()
    vball_season = Season(organization_id=org.id, league_id=vball_league.id, name="V Season",
                          start_date=date(2026, 1, 1), end_date=date(2026, 6, 30),
                          format="Round Robin", status="Active",
                          created_by=org.id, updated_by=org.id)
    dbsession.add(vball_season)
    dbsession.flush()
    vball_division = Division(organization_id=org.id, season_id=vball_season.id, name="V Open",
                              max_teams=8, status="Active", created_by=org.id, updated_by=org.id)
    dbsession.add(vball_division)
    dbsession.flush()
    v1 = Team(organization_id=org.id, division_id=vball_division.id, name="Vox A", status="Active",
              created_by=org.id, updated_by=org.id)
    v2 = Team(organization_id=org.id, division_id=vball_division.id, name="Vox B", status="Active",
              created_by=org.id, updated_by=org.id)
    dbsession.add_all([v1, v2])
    dbsession.commit()
    add_match(vball_season, vball_division, v1, v2, org_id=org.id, status="Scheduled")

    res = client.get("/api/v1/matches/public")
    assert res.status_code == 200
    body = res.json()
    assert body == []


def test_public_schedule_empty_when_no_matches(client):
    res = client.get("/api/v1/matches/public")
    assert res.status_code == 200
    assert res.json() == []
