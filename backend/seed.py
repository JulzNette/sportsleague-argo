"""
Local dev/demo seed script. Creates one fake organization, one user per
role (for logging in and exercising RBAC), and sample league data mirroring
the original HTML prototype's dataset so the frontend has something to show.

Run after migrations:  python seed.py
"""
import uuid
from datetime import date, time

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.division import Division
from app.models.league import League
from app.models.match import Match
from app.models.match_result import MatchResult
from app.models.player import Player
from app.models.referee import Referee
from app.models.season import Season
from app.models.stub import Organization, User
from app.models.team import Team

ORG_ID = uuid.uuid4()
SYSTEM_USER_ID = uuid.uuid4()  # used as created_by/updated_by for seeded rows


def main():
    db = SessionLocal()
    try:
        org = Organization(id=ORG_ID, name="Metro Manila Sports League")
        db.add(org)

        roles = [
            "League Administrator", "Season Manager", "Team Manager",
            "Referee", "Player", "System Administrator",
        ]
        users = {}
        for role in roles:
            slug = role.lower().replace(" ", ".")
            user = User(
                id=uuid.uuid4() if role != "System Administrator" else SYSTEM_USER_ID,
                organization_id=ORG_ID,
                email=f"{slug}@example.com",
                hashed_password=hash_password("Password123!"),
                full_name=role,
                role=role,
                is_active=True,
            )
            db.add(user)
            users[role] = user
        db.flush()
        admin_id = users["System Administrator"].id

        def audit(model, **kw):
            return model(organization_id=ORG_ID, created_by=admin_id, updated_by=admin_id, **kw)

        league = audit(
            League, name="Barangay Basketball League", sport_type="Basketball",
            description="Annual inter-barangay competition", status="Active",
        )
        db.add(league)
        db.flush()

        season = audit(
            Season, league_id=league.id, name="Season 1 - 2026",
            start_date=date(2026, 8, 1), end_date=date(2026, 11, 30),
            format="Round Robin", status="Active",
        )
        db.add(season)
        db.flush()

        division_a = audit(Division, season_id=season.id, name="Division A", max_teams=8, status="Active")
        db.add(division_a)
        db.flush()

        team_names = [
            ("Red Dragons", "Jose Reyes"), ("Blue Thunder", "Mila Santos"),
            ("Golden Eagles", "Ramon Cruz"), ("Iron Wolves", "Carla Dizon"),
        ]
        teams = []
        for name, coach in team_names:
            t = audit(
                Team, division_id=division_a.id, name=name, coach_name=coach,
                contact_email=f"{coach.split()[0].lower()}@{name.split()[0].lower()}.ph",
                contact_phone="09181234567", status="Active",
            )
            db.add(t)
            teams.append(t)
        db.flush()

        positions = ["Guard", "Forward", "Center", "Guard"]
        for i, team in enumerate(teams):
            for j in range(2):
                db.add(audit(
                    Player, team_id=team.id, full_name=f"Player {i}-{j}",
                    date_of_birth=date(2001, 1, 1), position=positions[(i + j) % len(positions)],
                    jersey_number=str(i * 10 + j + 1), contact_phone="09171111111", status="Active",
                ))

        ref = audit(Referee, full_name="Mark Santos", license_number="REF-2201",
                     contact_phone="09201111111", status="Active")
        db.add(ref)
        db.flush()

        m1 = audit(
            Match, season_id=season.id, division_id=division_a.id,
            home_team_id=teams[0].id, away_team_id=teams[1].id, referee_id=ref.id,
            scheduled_date=date(2026, 7, 14), scheduled_time=time(14, 0),
            venue="Barangay Gym A", round_number=1, match_type="Regular", status="Scheduled",
        )
        m2 = audit(
            Match, season_id=season.id, division_id=division_a.id,
            home_team_id=teams[2].id, away_team_id=teams[3].id, referee_id=ref.id,
            scheduled_date=date(2026, 7, 14), scheduled_time=time(16, 0),
            venue="Barangay Gym A", round_number=1, match_type="Regular", status="Completed",
        )
        db.add_all([m1, m2])
        db.flush()

        db.add(audit(
            MatchResult, match_id=m2.id, home_score=70, away_score=65,
            result_type="Normal", notes="Clean game, no incidents.", submitted_by=ref.id,
        ))

        db.commit()
        print("Seed complete.")
        print(f"Organization ID: {ORG_ID}")
        print("Login with any of these (password: Password123!):")
        for role in roles:
            print(f"  - {role.lower().replace(' ', '.')}@example.com  ({role})")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
