/**
 * UI-side mirror of backend app/core/permissions.py, used ONLY to decide
 * what to show/hide/disable in the interface (e.g. don't render a "Delete"
 * button someone can't use). This is a convenience, not security - the
 * backend re-checks every permission on every request regardless of what
 * the UI allowed the user to click.
 */
export const ROLES = [
  'Superadmin',
  'Viewer',
  'League Administrator',
  'Season Manager',
  'Team Manager',
  'Referee',
  'Player',
  'System Administrator',
]

const ALL = [...ROLES]
const ADMIN = ['System Administrator', 'Superadmin']

export const PERMISSIONS = {
  'league.view': ALL,
  'league.create': ['League Administrator', ...ADMIN],
  'league.update': ['League Administrator', ...ADMIN],
  'league.delete': ADMIN,
  'season.view': ALL,
  'season.create': ['League Administrator', 'Season Manager', ...ADMIN],
  'season.update': ['League Administrator', 'Season Manager', ...ADMIN],
  'division.view': ALL,
  'division.manage': ['League Administrator', 'Season Manager', ...ADMIN],
  'team.view': ALL,
  'team.create': ['League Administrator', 'Season Manager', ...ADMIN],
  'team.update': ['League Administrator', 'Season Manager', 'Team Manager', ...ADMIN],
  'team.delete': ['League Administrator', ...ADMIN],
  'team.manage_roster': ['League Administrator', 'Season Manager', 'Team Manager', ...ADMIN],
  'registration.view': ALL,
  'registration.submit': ['League Administrator', 'Season Manager', 'Team Manager', ...ADMIN],
  'registration.review': ['League Administrator', 'Season Manager', ...ADMIN],
  'player.view': ALL,
  'player.create': ['League Administrator', 'Season Manager', 'Team Manager', ...ADMIN],
  'player.update': ['League Administrator', 'Season Manager', 'Team Manager', ...ADMIN],
  'player.delete': ['League Administrator', ...ADMIN],
  'coach.view': ALL,
  'coach.manage': ['League Administrator', 'Season Manager', 'Team Manager', ...ADMIN],
  'match.view': ALL,
  'match.schedule': ['League Administrator', 'Season Manager', ...ADMIN],
  'match.update': ['League Administrator', 'Season Manager', ...ADMIN],
  'assignment.create': ['League Administrator', 'Season Manager', ...ADMIN],
  'assignment.view': ['League Administrator', 'Season Manager', 'Team Manager', 'Referee', ...ADMIN],
  'result.view': ALL,
  'result.submit': ['League Administrator', 'Season Manager', 'Referee', ...ADMIN],
  'result.update': ['League Administrator', 'Season Manager', ...ADMIN],
  'standing.view': ALL,
  'player_stat.view': ALL.filter((r) => r !== 'Team Manager'),
  'player_stat.enter': ADMIN,
  'report.view': ['League Administrator', 'Season Manager', ...ADMIN],
  'report.generate': ['League Administrator', 'Season Manager', ...ADMIN],
  'notification.view': ALL,
  'referee.manage': ['League Administrator', ...ADMIN],
  'settings.manage': ADMIN,
  'user.view': ADMIN,
  'user.create': ['Superadmin'],
  'user.update': ['Superadmin'],
  'user.delete': ['Superadmin'],
  'user.reset_password': ['Superadmin'],
  'user.assign_role': ['Superadmin'],
}

export function can(role, permission) {
  return (PERMISSIONS[permission] || []).includes(role)
}
