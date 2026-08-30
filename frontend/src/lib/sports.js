export const SPORTS = [
  'Basketball',
  'Volleyball',
  'Badminton',
  'Soccer',
  'Football',
  'Baseball',
  'Softball',
  'Tennis',
  'Table Tennis',
  'Swimming',
  'Athletics / Track & Field',
  'Esports',
  'Chess',
  'Darts',
  'Other',
]

// Basketball playing positions used in the player / roster forms.
export const BASKETBALL_POSITIONS = [
  'Point Guard',
  'Shooting Guard',
  'Small Forward',
  'Power Forward',
  'Center',
  'Guard',
  'Forward',
]

// Colored badge classes (see .badge-sport-* in index.css) so each sport is
// visually distinct when leagues of different sports are shown together.
export const SPORT_BADGE = {
  Basketball: 'badge-sport-basketball',
  Volleyball: 'badge-sport-volleyball',
  Badminton: 'badge-sport-badminton',
  Soccer: 'badge-sport-soccer',
  Football: 'badge-sport-football',
  Baseball: 'badge-sport-baseball',
  Softball: 'badge-sport-softball',
  Tennis: 'badge-sport-tennis',
  'Table Tennis': 'badge-sport-table-tennis',
  Swimming: 'badge-sport-swimming',
  'Athletics / Track & Field': 'badge-sport-athletics',
  Esports: 'badge-sport-esports',
  Chess: 'badge-sport-chess',
  Darts: 'badge-sport-darts',
  Other: 'badge-sport-other',
}

export const sportBadgeClass = (sport) => SPORT_BADGE[sport] || 'badge-sport-other'

// A team's sport isn't stored on the team - it lives up the chain:
// Team -> Division -> Season -> League -> sport_type. This derives that chain
// from the list endpoints and returns lookups plus the ordered list of sports.
export function buildSportMaps({ leagues = [], seasons = [], divisions = [], teams = [] }) {
  const leagueById = new Map(leagues.map((l) => [l.id, l]))
  const seasonById = new Map(seasons.map((s) => [s.id, s]))
  const divisionById = new Map(divisions.map((d) => [d.id, d]))

  const sportOf = {
    league: (id) => leagueById.get(id)?.sport_type || 'Other',
    season: (id) => {
      const s = seasonById.get(id)
      return s ? sportOf.league(s.league_id) : 'Other'
    },
    division: (id) => {
      const d = divisionById.get(id)
      return d ? sportOf.season(d.season_id) : 'Other'
    },
    team: (id) => {
      const t = teams.find((x) => x.id === id)
      return t ? sportOf.division(t.division_id) : 'Other'
    },
  }

  const present = new Set()
  leagues.forEach((l) => present.add(l.sport_type || 'Other'))
  seasons.forEach((s) => present.add(sportOf.season(s.id)))
  divisions.forEach((d) => present.add(sportOf.division(d.id)))
  teams.forEach((t) => present.add(sportOf.team(t.id)))
  present.delete('Other')

  const known = new Set(SPORTS)
  const ordered = [
    ...SPORTS.filter((s) => present.has(s)),
    ...[...present].filter((s) => !known.has(s)).sort(),
  ]

  return { sportOf, sports: ordered }
}
