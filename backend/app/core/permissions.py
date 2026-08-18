"""
Role/permission matrix - mirrors the PERMISSIONS map from the original
sports-league-management.html prototype exactly, so behavior is a straight
port rather than a redesign. Enforced server-side (the HTML version only
enforced it client-side, which is not real security).
"""

ROLES = [
    "Viewer",
    "League Administrator",
    "Season Manager",
    "Team Manager",
    "Referee",
    "Player",
    "System Administrator",
]

_ALL_ROLES = list(ROLES)

PERMISSIONS: dict[str, list[str]] = {
    "league.view": _ALL_ROLES,
    "league.create": ["League Administrator", "System Administrator"],
    "league.update": ["League Administrator", "System Administrator"],
    "league.delete": ["System Administrator"],
    "season.view": _ALL_ROLES,
    "season.create": ["League Administrator", "Season Manager", "System Administrator"],
    "season.update": ["League Administrator", "Season Manager", "System Administrator"],
    "division.view": _ALL_ROLES,
    "division.manage": ["League Administrator", "Season Manager", "System Administrator"],
    "team.view": _ALL_ROLES,
    "team.create": ["League Administrator", "Season Manager", "System Administrator"],
    "team.update": ["League Administrator", "Season Manager", "Team Manager", "System Administrator"],
    "team.delete": ["League Administrator", "System Administrator"],
    "team.manage_roster": [
        "League Administrator", "Season Manager", "Team Manager", "System Administrator",
    ],
    "registration.view": _ALL_ROLES,
    "registration.submit": ["League Administrator", "Season Manager", "Team Manager", "System Administrator"],
    "registration.review": ["League Administrator", "Season Manager", "System Administrator"],
    "player.view": _ALL_ROLES,
    "player.create": ["League Administrator", "Season Manager", "Team Manager", "System Administrator"],
    "player.update": ["League Administrator", "Season Manager", "Team Manager", "System Administrator"],
    "player.delete": ["League Administrator", "System Administrator"],
    "match.view": _ALL_ROLES,
    "match.schedule": ["League Administrator", "Season Manager", "System Administrator"],
    "match.update": ["League Administrator", "Season Manager", "System Administrator"],
    "assignment.create": ["League Administrator", "Season Manager", "System Administrator"],
    "assignment.view": [
        "League Administrator", "Season Manager", "Team Manager", "Referee", "System Administrator",
    ],
    "result.view": _ALL_ROLES,
    "result.submit": ["League Administrator", "Season Manager", "Referee", "System Administrator"],
    "result.update": ["League Administrator", "Season Manager", "System Administrator"],
    "standing.view": _ALL_ROLES,
    "player_stat.view": _ALL_ROLES,
    "player_stat.enter": [
        "League Administrator", "Season Manager", "Referee", "System Administrator",
    ],
    "report.view": ["League Administrator", "Season Manager", "System Administrator"],
    "report.generate": ["League Administrator", "Season Manager", "System Administrator"],
    "notification.view": _ALL_ROLES,
    "referee.manage": ["League Administrator", "System Administrator"],
    "settings.manage": ["System Administrator"],
}


def role_has_permission(role: str, permission: str) -> bool:
    return role in PERMISSIONS.get(permission, [])
