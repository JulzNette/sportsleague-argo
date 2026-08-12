"""
Valid status transitions, ported 1:1 from STATUS_TRANSITIONS_MATCH /
STATUS_TRANSITIONS_SEASON in the original HTML prototype, now enforced
server-side instead of only in the UI.
"""

MATCH_STATUS_TRANSITIONS: dict[str, list[str]] = {
    "Scheduled": ["In Progress", "Postponed", "Cancelled", "Forfeited"],
    "In Progress": ["Completed", "Forfeited"],
    "Postponed": ["Scheduled", "Cancelled"],
    "Completed": [],
    "Cancelled": [],
    "Forfeited": [],
}

SEASON_STATUS_TRANSITIONS: dict[str, list[str]] = {
    "Draft": ["Active", "Cancelled"],
    "Active": ["Completed", "Cancelled"],
    "Completed": [],
    "Cancelled": [],
}


def is_valid_transition(table: dict[str, list[str]], current: str, target: str) -> bool:
    if current == target:
        return True
    return target in table.get(current, [])
