// Mirrors backend app/core/state_machines.py — for disabling invalid status
// options in the UI. The backend enforces this regardless of what's shown here.
export const MATCH_STATUS_TRANSITIONS = {
  Scheduled: ['In Progress', 'Postponed', 'Cancelled', 'Forfeited'],
  'In Progress': ['Completed', 'Forfeited'],
  Postponed: ['Scheduled', 'Cancelled'],
  Completed: [],
  Cancelled: [],
  Forfeited: [],
}

export const SEASON_STATUS_TRANSITIONS = {
  Draft: ['Active', 'Cancelled'],
  Active: ['Completed', 'Cancelled'],
  Completed: [],
  Cancelled: [],
}

export const STATUS_COLOR = {
  Active: 'success', Completed: 'success',
  Scheduled: 'primary', 'In Progress': 'primary',
  Draft: 'warning', Postponed: 'warning',
  Cancelled: 'danger', Forfeited: 'danger', Disqualified: 'danger', Suspended: 'danger',
  Archived: 'neutral', Withdrawn: 'neutral', Inactive: 'neutral',
}
