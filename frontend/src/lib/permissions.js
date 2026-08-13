/**
 * UI-side mirror of backend app/core/permissions.py, used ONLY to decide
 * what to show/hide/disable in the interface (e.g. don't render a "Delete"
 * button someone can't use). This is a convenience, not security - the
 * backend re-checks every permission on every request regardless of what
 * the UI allowed the user to click.
 */
export const ROLES = [
  'Viewer',
  'League Administrator',
  'Season Manager',
  'Team Manager',
  'Referee',
  'Player',
  'System Administrator',
]

const ALL = [...ROLES]

export const PERMISSIONS = {
  'league.view': ALL,
  'league.create': ['League Administrator', 'System Administrator'],
  'league.update': ['League Administrator', 'System Administrator'],
  'league.delete': ['System Administrator'],
  'season.view': ALL,
  'season.create': ['League Administrator', 'Season Manager', 'System Administrator'],
  'season.update': ['League Administrator', 'Season Manager', 'System Administrator'],
  'division.view': ALL,
  'division.manage': ['League Administrator', 'Season Manager', 'System Administrator'],
  'team.view': ALL,
  'team.create': ['League Administrator', 'Season Manager', 'System Administrator'],
  'team.update': ['League Administrator', 'Season Manager', 'Team Manager', 'System Administrator'],
  'team.delete': ['League Administrator', 'System Administrator'],
  'team.manage_roster': ['League Administrator', 'Season Manager', 'Team Manager', 'System Administrator'],
  'player.view': ALL,
  'player.create': ['League Administrator', 'Season Manager', 'Team Manager', 'System Administrator'],
  'player.update': ['League Administrator', 'Season Manager', 'Team Manager', 'System Administrator'],
  'player.delete': ['League Administrator', 'System Administrator'],
  'match.view': ALL,
  'match.schedule': ['League Administrator', 'Season Manager', 'System Administrator'],
  'match.update': ['League Administrator', 'Season Manager', 'System Administrator'],
  'assignment.create': ['League Administrator', 'Season Manager', 'System Administrator'],
  'assignment.view': ['League Administrator', 'Season Manager', 'Team Manager', 'Referee', 'System Administrator'],
  'result.view': ALL,
  'result.submit': ['League Administrator', 'Season Manager', 'Referee', 'System Administrator'],
  'result.update': ['League Administrator', 'Season Manager', 'System Administrator'],
  'standing.view': ALL,
  'report.view': ['League Administrator', 'Season Manager', 'System Administrator'],
  'report.generate': ['League Administrator', 'Season Manager', 'System Administrator'],
  'referee.manage': ['League Administrator', 'System Administrator'],
  'settings.manage': ['System Administrator'],
}

export function can(role, permission) {
  return (PERMISSIONS[permission] || []).includes(role)
}
