import { useQuery } from '@tanstack/react-query'
import { endpoints } from '../lib/api'
import { useAuthStore } from '../store/authStore'
import PageHead from '../components/PageHead'
import Kpi from '../components/Kpi'
import Badge from '../components/Badge'

function BarList({ rows, valueKey, maxKey, suffix }) {
  const max = Math.max(1, ...rows.map((r) => r[maxKey]))
  return (
    <div className="space-y-2">
      {rows.length === 0 && <p className="text-sm text-gray-400 text-center py-4">No data yet.</p>}
      {rows.map((r) => (
        <div key={r.team_id} className="flex items-center gap-3">
          <span className="w-28 shrink-0 truncate text-sm text-gray-700 text-right font-medium">{r.team_name}</span>
          <div className="flex-1 h-5 rounded bg-gray-100 overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded"
              style={{ width: `${Math.round((r[maxKey] / max) * 100)}%` }}
            />
          </div>
          <span className="w-14 shrink-0 text-sm text-gray-500">{r[valueKey]}{suffix}</span>
        </div>
      ))}
    </div>
  )
}

export default function DashboardPage() {
  const { role, email } = useAuthStore()

  const { data: leagues } = useQuery({ queryKey: ['leagues'], queryFn: () => endpoints.leagues.list().then((r) => r.data) })
  const { data: seasons } = useQuery({ queryKey: ['seasons'], queryFn: () => endpoints.seasons.list().then((r) => r.data) })
  const { data: teams } = useQuery({ queryKey: ['teams'], queryFn: () => endpoints.teams.list().then((r) => r.data) })
  const { data: matches } = useQuery({ queryKey: ['matches'], queryFn: () => endpoints.matches.list().then((r) => r.data) })

  const teamName = (id) => teams?.find((t) => t.id === id)?.name || '—'

  const upcoming = (matches || [])
    .filter((m) => m.status === 'Scheduled')
    .sort((a, b) => `${a.scheduled_date}${a.scheduled_time}`.localeCompare(`${b.scheduled_date}${b.scheduled_time}`))
    .slice(0, 6)

  const recent = (matches || [])
    .filter((m) => m.status === 'Completed' && m.result)
    .sort((a, b) => `${b.scheduled_date}${b.scheduled_time}`.localeCompare(`${a.scheduled_date}${a.scheduled_time}`))
    .slice(0, 5)

  const resultLine = (m) => {
    const r = m.result
    if (!r) return null
    if (r.result_type === 'Forfeit') return `${teamName(r.forfeit_winner_team_id)} wins by forfeit`
    if (r.home_score === r.away_score) return `${teamName(m.home_team_id)} ${r.home_score} – ${r.away_score} ${teamName(m.away_team_id)}`
    return `${teamName(m.home_team_id)} ${r.home_score} – ${r.away_score} ${teamName(m.away_team_id)}`
  }

  const leaderSeasonId = seasons?.[0]?.id
  const { data: standings } = useQuery({
    queryKey: ['standings', leaderSeasonId],
    queryFn: () => (leaderSeasonId ? endpoints.standings.get(leaderSeasonId).then((r) => r.data) : []),
    enabled: !!leaderSeasonId,
  })
  const leader = standings?.[0]
  const topTeams = (standings || []).slice(0, 6)

  return (
    <div>
      <PageHead title="Dashboard" subtitle={`Signed in as ${email} — ${role}`} />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 mb-6">
        <Kpi icon="bi-diagram-3" tint="blue" value={leagues?.length ?? '—'} label="Leagues" />
        <Kpi icon="bi-calendar-range" tint="emerald" value={seasons?.length ?? '—'} label="Seasons" />
        <Kpi icon="bi-people" tint="amber" value={teams?.length ?? '—'} label="Teams" />
        <Kpi icon="bi-controller" tint="rose" value={matches?.length ?? '—'} label="Matches" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3.5 mb-6">
        <div className="card">
          <div className="px-4 py-3 border-b border-gray-200">
            <h3 className="font-semibold text-sm text-gray-900">Recent results</h3>
          </div>
          {recent.length === 0 ? (
            <p className="p-6 text-sm text-gray-400 text-center">No completed matches yet.</p>
          ) : (
            <ul className="divide-y divide-gray-100">
              {recent.map((m) => (
                <li key={m.id} className="px-4 py-2.5 flex items-center justify-between gap-3">
                  <span className="text-sm font-semibold text-gray-900">{resultLine(m)}</span>
                  <span className="text-xs text-gray-400 shrink-0">{m.scheduled_date}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2">
            <i className="bi bi-trophy text-emerald-500" />
            <h3 className="font-semibold text-sm text-gray-900">Current leader</h3>
          </div>
          {!leader ? (
            <p className="p-6 text-sm text-gray-400 text-center">No standings yet.</p>
          ) : (
            <ul className="divide-y divide-gray-100">
              <li className="px-4 py-3 flex items-center gap-3">
                <span className="w-8 h-8 rounded-full bg-yellow-100 text-yellow-800 flex items-center justify-center text-sm font-bold">1</span>
                <div className="flex-1">
                  <div className="font-semibold text-sm text-gray-900">{leader.team_name}</div>
                  <div className="text-xs text-gray-400">{leader.wins}W · {leader.draws}D · {leader.losses}L</div>
                </div>
                <b className="text-emerald-600">{leader.points} pts</b>
              </li>
              {topTeams.slice(1).map((r, i) => (
                <li key={r.team_id} className="px-4 py-2.5 flex items-center gap-3">
                  <span className="w-8 h-8 rounded-full bg-gray-100 text-gray-500 flex items-center justify-center text-sm font-bold">{i + 2}</span>
                  <span className="flex-1 font-medium text-sm text-gray-700">{r.team_name}</span>
                  <span className="text-sm text-gray-500">{r.points} pts</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <div className="px-4 py-3 border-b border-gray-200">
            <h3 className="font-semibold text-sm text-gray-900">Upcoming matches</h3>
          </div>
          {upcoming.length === 0 ? (
            <p className="p-6 text-sm text-gray-400 text-center">Nothing scheduled right now.</p>
          ) : (
            <ul className="divide-y divide-gray-100">
              {upcoming.map((m) => (
                <li key={m.id} className="px-4 py-2.5">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-sm font-semibold text-gray-900 truncate">{teamName(m.home_team_id)} vs {teamName(m.away_team_id)}</span>
                    <span className="text-xs text-gray-400 shrink-0">{m.scheduled_date} {m.scheduled_time}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">{m.venue} <Badge status={m.status} /></div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
        <div className="card">
          <div className="px-4 py-3 border-b border-gray-200">
            <h3 className="font-semibold text-sm text-gray-900">Wins per team</h3>
          </div>
          <div className="p-4">
            <BarList rows={topTeams} valueKey="wins" maxKey="wins" suffix="" />
          </div>
        </div>
        <div className="card">
          <div className="px-4 py-3 border-b border-gray-200">
            <h3 className="font-semibold text-sm text-gray-900">Points scored per team</h3>
          </div>
          <div className="p-4">
            <BarList rows={topTeams} valueKey="points_for" maxKey="points_for" suffix="" />
          </div>
        </div>
      </div>
    </div>
  )
}
