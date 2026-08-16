"""
Local dev/demo seed script. Creates one fake organization, one user per
role (for logging in and exercising RBAC), and sample league data mirroring
the original HTML prototype's dataset so the frontend has something to show.

Idempotent: re-running reuses the existing "Metro Manila Sports League"
organization + role users and only refreshes the sportsleague_* sample rows.
Pass --reset to wipe and rebuild those rows.

Run after migrations:  python seed.py
"""
import argparse
import uuid
from datetime import date, time
from sqlalchemy import text

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.division import Division
from app.models.league import League
from app.models.match import Match
from app.models.match_result import MatchResult
from app.models.player import Player
from app.models.registration import Registration, RegistrationDocument, RegistrationPlayer
from app.models.referee import Referee
from app.models.season import Season
from app.models.stub import Organization, User
from app.models.team import Team

ORG_NAME = "Metro Manila Sports League"
SYSTEM_USER_ID = uuid.uuid4()  # used as created_by/updated_by for seeded rows

# (full_name, position, jersey, dob)
BASKETBALL_ROSTERS = {
    "Red Dragons": [
        ("Paolo Rivera", "Guard", "7", date(2001, 3, 12)),
        ("Marco Villanueva", "Forward", "10", date(2000, 7, 25)),
        ("Andrei Bautista", "Center", "15", date(1999, 11, 2)),
        ("Joshua Dela Cruz", "Guard", "23", date(2002, 1, 18)),
    ],
    "Blue Thunder": [
        ("Carlo Mendoza", "Guard", "5", date(2001, 5, 9)),
        ("Kenneth Ramos", "Forward", "8", date(2000, 9, 30)),
        ("Luis Fernandez", "Center", "14", date(1999, 2, 14)),
        ("Miguel Santos", "Guard", "20", date(2003, 4, 22)),
    ],
    "Golden Eagles": [
        ("Nathan Cruz", "Guard", "3", date(2002, 6, 8)),
        ("Rafael Garcia", "Forward", "9", date(2001, 8, 17)),
        ("Daniel Reyes", "Center", "12", date(2000, 12, 5)),
        ("Angelo Torres", "Guard", "21", date(2003, 10, 11)),
    ],
    "Iron Wolves": [
        ("Justin Aquino", "Guard", "4", date(2002, 3, 27)),
        ("Kevin Domingo", "Forward", "11", date(2001, 10, 19)),
        ("Mark Navarro", "Center", "16", date(1999, 6, 15)),
        ("Ivan Castillo", "Guard", "25", date(2003, 1, 5)),
    ],
}

# Extra leagues: (league, sport, desc, season_name, [(team, coach, [players])])
EXTRA_LEAGUES = [
    ("Liga Barangay Volleyball", "Volleyball", "Inter-barangay women's and men's league", "Season 1 - 2026", [
        ("Smash Volleyball Club", "Karen Lim", [
            ("Nicole Alonzo", "Setter", "1", date(2002, 4, 16)),
            ("Dana Reyes", "Outside Hitter", "6", date(2001, 7, 8)),
            ("Grace Santos", "Libero", "8", date(2003, 11, 23)),
        ]),
        ("Net Runners", "Patrick Suarez", [
            ("Althea Ramos", "Middle Blocker", "4", date(2001, 2, 11)),
            ("Sofia Tan", "Outside Hitter", "9", date(2002, 9, 29)),
            ("Bea Fernandez", "Opposite", "12", date(2000, 5, 14)),
        ]),
    ]),
    ("Badminton Club Open", "Badminton", "Open division badminton tournament", "2026 Open Tournament", [
        ("Shuttle Kings", "Dennis Uy", [
            ("Kevin Tan", "Singles", "1", date(2002, 1, 30)),
            ("Nina Lim", "Doubles", "2", date(2003, 7, 17)),
        ]),
        ("Smash Aces", "Marco Delgado", [
            ("Erica Ong", "Singles", "1", date(2001, 12, 2)),
            ("Ryan Chu", "Doubles", "2", date(2002, 6, 21)),
        ]),
    ]),
    ("Metro Football League", "Soccer", "Community football league", "2026 Season", [
        ("United FC", "Antonio Salazar", [
            ("Diego Ramirez", "Forward", "9", date(2001, 4, 3)),
            ("Mateo Cruz", "Midfielder", "8", date(2000, 8, 26)),
            ("Julian Ramos", "Defender", "4", date(1999, 12, 19)),
            ("Sebastian Torres", "Goalkeeper", "1", date(2002, 3, 8)),
        ]),
        ("Metro Strikers", "Paolo Villamor", [
            ("Lucas Garcia", "Forward", "10", date(2001, 9, 14)),
            ("Rafael Mendoza", "Midfielder", "6", date(2002, 5, 27)),
            ("Tomas Aquino", "Defender", "5", date(2000, 11, 9)),
            ("Andres Lopez", "Goalkeeper", "13", date(1999, 7, 31)),
        ]),
    ]),
]

RESET_ORDER = [
    "sportsleague_registration_documents",
    "sportsleague_registration_players",
    "sportsleague_registrations",
    "sportsleague_player_game_stats",
    "sportsleague_match_results",
    "sportsleague_players",
    "sportsleague_matches",
    "sportsleague_teams",
    "sportsleague_referees",
    "sportsleague_divisions",
    "sportsleague_seasons",
    "sportsleague_leagues",
]


def wipe_module_rows(db, org_id):
    """Delete all sportsleague_* sample rows for the org, children first."""
    for table in RESET_ORDER:
        db.execute(text(f"DELETE FROM {table} WHERE organization_id = :org_id"), {"org_id": org_id})
    db.commit()


def main():
    parser = argparse.ArgumentParser(description="Seed demo data for the sports league module.")
    parser.add_argument("--reset", action="store_true", help="Wipe existing sportsleague_* rows for the org before seeding.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.name == ORG_NAME).first()
        if org:
            ORG_ID = org.id
            print(f"Reusing organization '{ORG_NAME}' ({ORG_ID})")
            if args.reset:
                wipe_module_rows(db, ORG_ID)
                print("Existing sportsleague_* sample rows removed.")
        else:
            ORG_ID = uuid.uuid4()
            org = Organization(id=ORG_ID, name=ORG_NAME)
            db.add(org)
            db.flush()
            print(f"Created organization '{ORG_NAME}' ({ORG_ID})")

        roles = [
            "Viewer", "League Administrator", "Season Manager", "Team Manager",
            "Referee", "Player", "System Administrator",
        ]
        users = {}
        for role in roles:
            email = f"{role.lower().replace(' ', '.')}@gmail.com"
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    id=uuid.uuid4() if role != "System Administrator" else SYSTEM_USER_ID,
                    organization_id=ORG_ID,
                    email=email,
                    hashed_password=hash_password("Admin123"),
                    full_name=role,
                    role=role,
                    is_active=True,
                )
                db.add(user)
                db.flush()
            users[role] = user
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

        teams = {}
        for name, coach in [
            ("Red Dragons", "Jose Reyes"), ("Blue Thunder", "Mila Santos"),
            ("Golden Eagles", "Ramon Cruz"), ("Iron Wolves", "Carla Dizon"),
        ]:
            t = audit(
                Team, division_id=division_a.id, name=name, coach_name=coach,
                contact_email=f"{coach.split()[0].lower()}@{name.split()[0].lower()}.ph",
                contact_phone="09181234567", status="Active",
            )
            db.add(t)
            teams[name] = t
        db.flush()
        for name, roster in BASKETBALL_ROSTERS.items():
            for full_name, position, jersey, dob in roster:
                db.add(audit(
                    Player, team_id=teams[name].id, full_name=full_name, date_of_birth=dob,
                    position=position, jersey_number=jersey,
                    contact_phone=f"0917{abs(hash(full_name)) % 100000000:08d}", status="Active",
                ))
        db.flush()

        ref = audit(Referee, full_name="Mark Santos", license_number="REF-2201",
                     contact_phone="09201111111", status="Active")
        ref2 = audit(Referee, full_name="Grace Lim", license_number="REF-2202",
                     contact_phone="09202222222", status="Active")
        db.add_all([ref, ref2])
        db.flush()

        registration = audit(
            Registration, division_id=division_a.id, team_name="Silver Sharks",
            coach_name="Nina Ramos", contact_email="nina.ramos@example.com",
            contact_phone="09171234567",
            notes="New team hoping to join Division A this season.", status="Pending",
        )
        registration.players = [
            RegistrationPlayer(
                organization_id=ORG_ID, created_by=admin_id, updated_by=admin_id,
                full_name="Jules Aquino", date_of_birth=date(2003, 5, 12),
                position="Guard", jersey_number="7", contact_phone="09171112222",
            ),
            RegistrationPlayer(
                organization_id=ORG_ID, created_by=admin_id, updated_by=admin_id,
                full_name="Bea Navarro", date_of_birth=date(2004, 9, 1),
                position="Forward", jersey_number="11", contact_phone="09173334444",
            ),
        ]
        registration.documents = [
            RegistrationDocument(
                organization_id=ORG_ID, created_by=admin_id, updated_by=admin_id,
                player_full_name="Jules Aquino", document_type="Birth Certificate",
                file_name="jules-birth.pdf", notes="Notarized copy.",
            ),
            RegistrationDocument(
                organization_id=ORG_ID, created_by=admin_id, updated_by=admin_id,
                document_type="Team Waiver", file_name="silver-sharks-waiver.pdf",
            ),
        ]
        db.add(registration)

        def match(home, away, day, hour, venue, round_number, status, refr, **kw):
            return audit(
                Match, season_id=season.id, division_id=division_a.id,
                home_team_id=teams[home].id, away_team_id=teams[away].id,
                referee_id=refr.id, scheduled_date=date(2026, 7, day),
                scheduled_time=time(hour, 0), venue=venue, round_number=round_number,
                match_type="Regular", status=status, **kw,
            )

        m1 = match("Red Dragons", "Blue Thunder", 14, 14, "Barangay Gym A", 1, "Scheduled", ref)
        m2 = match("Golden Eagles", "Iron Wolves", 14, 16, "Barangay Gym A", 1, "Completed", ref)
        m3 = match("Blue Thunder", "Golden Eagles", 21, 15, "Barangay Gym B", 2, "Completed", ref2)
        m4 = match("Iron Wolves", "Red Dragons", 21, 17, "Barangay Gym B", 2, "Scheduled", ref2)
        m5 = match("Red Dragons", "Golden Eagles", 28, 14, "Barangay Gym A", 3, "Scheduled", ref)
        m6 = match("Blue Thunder", "Iron Wolves", 28, 16, "Barangay Gym A", 3, "Scheduled", ref)
        db.add_all([m1, m2, m3, m4, m5, m6])
        db.flush()

        db.add(audit(
            MatchResult, match_id=m2.id, home_score=70, away_score=65,
            result_type="Normal", notes="Clean game, no incidents.", submitted_by=ref.id,
        ))
        db.add(audit(
            MatchResult, match_id=m3.id, home_score=62, away_score=58,
            result_type="Normal", notes="Close match decided in the final minutes.", submitted_by=ref2.id,
        ))

        # Additional sample leagues covering other sports, so the app clearly
        # supports more than basketball. Each gets a season + division + teams
        # with real-looking rosters.
        for league_name, sport_type, desc, season_name, roster in EXTRA_LEAGUES:
            extra_league = audit(
                League, name=league_name, sport_type=sport_type,
                description=desc, status="Active",
            )
            db.add(extra_league)
            db.flush()

            extra_season = audit(
                Season, league_id=extra_league.id, name=season_name,
                start_date=date(2026, 9, 1), end_date=date(2026, 12, 15),
                format="Round Robin", status="Active",
            )
            db.add(extra_season)
            db.flush()

            extra_div = audit(Division, season_id=extra_season.id, name="Open Division", max_teams=8, status="Active")
            db.add(extra_div)
            db.flush()

            for team_name, coach_name, players in roster:
                t = audit(
                    Team, division_id=extra_div.id, name=team_name, coach_name=coach_name,
                    contact_email=f"coach.{team_name.split()[0].lower()}@example.com",
                    contact_phone="09181234567", status="Active",
                )
                db.add(t)
                db.flush()
                for full_name, position, jersey, dob in players:
                    db.add(audit(
                        Player, team_id=t.id, full_name=full_name, date_of_birth=dob,
                        position=position, jersey_number=jersey,
                        contact_phone=f"0917{abs(hash(full_name)) % 100000000:08d}", status="Active",
                    ))

        db.commit()
        print("Seed complete.")
        print(f"Organization ID: {ORG_ID}")
        print("Login with any of these (password: Admin123):")
        for role in roles:
            print(f"  - {role.lower().replace(' ', '.')}@gmail.com  ({role})")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
