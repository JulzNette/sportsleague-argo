"""
Role/permission matrix - mirrors the PERMISSIONS map from the original
sports-league-management.html prototype exactly, so behavior is a straight
port rather than a redesign. Enforced server-side (the HTML version only
enforced it client-side, which is not real security).
"""

ROLES = [
    "Superadmin",
    "Viewer",
    "League Administrator",
    "Season Manager",
    "Team Manager",
    "Referee",
    "Player",
    "System Administrator",
]

_ALL_ROLES = list(ROLES)

# Every permission an admin-level role can hold. Superadmin is the top role and
# inherits all of these so it can manage the whole system, plus user management.
_ADMIN_ROLES = ["System Administrator", "Superadmin"]

PERMISSIONS: dict[str, list[str]] = {
    "league.view": _ALL_ROLES,
    "league.create": ["League Administrator", *_ADMIN_ROLES],
    "league.update": ["League Administrator", *_ADMIN_ROLES],
    "league.delete": _ADMIN_ROLES,
    "season.view": _ALL_ROLES,
    "season.create": ["League Administrator", "Season Manager", *_ADMIN_ROLES],
    "season.update": ["League Administrator", "Season Manager", *_ADMIN_ROLES],
    "division.view": _ALL_ROLES,
    "division.manage": ["League Administrator", "Season Manager", *_ADMIN_ROLES],
    "team.view": _ALL_ROLES,
    "team.create": ["League Administrator", "Season Manager", *_ADMIN_ROLES],
    "team.update": ["League Administrator", "Season Manager", "Team Manager", *_ADMIN_ROLES],
    "team.delete": ["League Administrator", *_ADMIN_ROLES],
    "team.manage_roster": [
        "League Administrator", "Season Manager", "Team Manager", *_ADMIN_ROLES,
    ],
    "registration.view": _ALL_ROLES,
    "registration.submit": ["League Administrator", "Season Manager", "Team Manager", *_ADMIN_ROLES],
    "registration.review": ["League Administrator", "Season Manager", *_ADMIN_ROLES],
    "player.view": _ALL_ROLES,
    "player.create": ["League Administrator", "Season Manager", "Team Manager", *_ADMIN_ROLES],
    "player.update": ["League Administrator", "Season Manager", "Team Manager", *_ADMIN_ROLES],
    "player.delete": ["League Administrator", *_ADMIN_ROLES],
    "match.view": _ALL_ROLES,
    "match.schedule": ["League Administrator", "Season Manager", *_ADMIN_ROLES],
    "match.update": ["League Administrator", "Season Manager", *_ADMIN_ROLES],
    "assignment.create": ["League Administrator", "Season Manager", *_ADMIN_ROLES],
    "assignment.view": [
        "League Administrator", "Season Manager", "Team Manager", "Referee", *_ADMIN_ROLES,
    ],
    "result.view": _ALL_ROLES,
    "result.submit": ["League Administrator", "Season Manager", "Referee", *_ADMIN_ROLES],
    "result.update": ["League Administrator", "Season Manager", *_ADMIN_ROLES],
    "standing.view": _ALL_ROLES,
    "player_stat.view": [r for r in _ALL_ROLES if r != "Team Manager"],
    "player_stat.enter": _ADMIN_ROLES,
    "report.view": ["League Administrator", "Season Manager", *_ADMIN_ROLES],
    "report.generate": ["League Administrator", "Season Manager", *_ADMIN_ROLES],
    "notification.view": _ALL_ROLES,
    "referee.manage": ["League Administrator", *_ADMIN_ROLES],
    "settings.manage": _ADMIN_ROLES,
    "user.view": _ADMIN_ROLES,
    "user.create": ["Superadmin"],
    "user.update": ["Superadmin"],
    "user.delete": ["Superadmin"],
    "user.reset_password": ["Superadmin"],
    "user.assign_role": ["Superadmin"],
}


def role_has_permission(role: str, permission: str) -> bool:
    return role in PERMISSIONS.get(permission, [])
