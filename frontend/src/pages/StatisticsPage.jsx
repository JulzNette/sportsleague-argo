import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from 'recharts'
import { endpoints } from '../lib/api'
import { can } from '../lib/permissions'
import { useAuthStore } from '../store/authStore'
import PageHead from '../components/PageHead'
import DataTable from '../components/DataTable'

const METRICS = [
  { key: 'points', label: 'League points', icon: 'bi-trophy', format: (r) => `${r.points} pts` },
  { key: 'points_for', label: 'Points scored', icon: 'bi-activity', format: (r) => String(r.points_for) },
  { key: 'wins', label: 'Most wins', icon: 'bi-award', format: (r) => `${r.wins} W` },
  {
    key: 'point_differential',
    label: 'Point differential',
    icon: 'bi-graph-up-arrow',
    format: (r) => (r.point_differential > 0 ? `+${r.point_differential}` : String(r.point_differential)),
  },
]

const MEDAL = [
  'bg-yellow-100 text-yellow-800',
  'bg-slate-200 text-slate-800',
  'bg-orange-100 text-orange-800',
  'bg-gray-100 text-gray-500',
]

function LeaderboardCard({ metric, rows, nameKey = 'team_name', idKey = 'team_id' }) {
  return (
    <div className="card">
      <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2">
        <i className={`bi ${metric.icon} text-emerald-500`} />
        <h3 className="font-semibold text-sm text-gray-900">{metric.label}</h3>
      </div>
      <ol className="divide-y divide-gray-100">
        {rows.length === 0 && <li className="px-4 py-8 text-center text-sm text-gray-400">No data yet.</li>}
        {rows.map((r, i) => (
          <li key={r[idKey]} className="flex items-center gap-3 px-4 py-2.5">
            <span className={`w-6 h-6 shrink-0 rounded-full flex items-center justify-center text-xs font-bold ${MEDAL[i] || MEDAL[3]}`}>
              {i + 1}
            </span>
            <span className="flex-1 font-semibold text-sm text-gray-900 truncate">{r[nameKey]}</span>
            <span className="text-sm text-gray-500">{metric.format(r)}</span>
          </li>
        ))}
      </ol>
    </div>
  )
}

const PLAYER_METRICS = [
  { key: 'points', label: 'Top scorer', icon: 'bi-trophy', format: (r) => `${r.points} pts` },
  { key: 'assists', label: 'Top playmaker', icon: 'bi-dribbble', format: (r) => `${r.assists} ast` },
  { key: 'rebounds', label: 'Top rebounder', icon: 'bi-arrow-up-circle', format: (r) => `${r.rebounds} reb` },
  { key: 'steals', label: 'Most steals', icon: 'bi-lightning', format: (r) => `${r.steals} stl` },
]

export default function StatisticsPage() {
  const role = useAuthStore((s) => s.role)
  const canViewPlayerStats = can(role, 'player_stat.view')
  const { data: seasons } = useQuery({ queryKey: ['seasons'], queryFn: () => endpoints.seasons.list().then((r) => r.data) })
  const [seasonId, setSeasonId] = useState('')
  const { data: divisions } = useQuery({
    queryKey: ['divisions', seasonId],
    queryFn: () => endpoints.divisions.list({ season_id: seasonId }).then((r) => r.data),
    enabled: !!seasonId,
  })
  const [divisionId, setDivisionId] = useState('')

  const activeSeasonId = seasonId || seasons?.[0]?.id
  const { data: standings, isLoading } = useQuery({
    queryKey: ['standings', activeSeasonId, divisionId],
    queryFn: () => endpoints.standings.get(activeSeasonId, divisionId || undefined).then((r) => r.data),
    enabled: !!activeSeasonId,
  })
  const { data: playerStats } = useQuery({
    queryKey: ['playerStats', activeSeasonId, divisionId],
    queryFn: () => endpoints.stats.players({
      season_id: activeSeasonId,
      division_id: divisionId || undefined,
    }).then((r) => r.data),
    enabled: !!activeSeasonId,
  })

  const rows = (standings || []).map((r) => ({ ...r, id: r.team_id }))
  const playerRows = (playerStats || []).map((r) => ({ ...r, id: r.player_id }))

  return (
    <div>
      <PageHead title="Statistics" subtitle="Team form and rankings, computed live from completed match results." />

      <div className="card p-3.5 mb-4 flex gap-3 flex-wrap items-center">
        <select className="input w-auto" value={activeSeasonId || ''} onChange={(e) => { setSeasonId(e.target.value); setDivisionId('') }}>
          {seasons?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <select className="input w-auto" value={divisionId} onChange={(e) => setDivisionId(e.target.value)}>
          <option value="">All divisions</option>
          {divisions?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
      </div>

      {isLoading ? <p className="text-sm text-gray-500">Computing statistics...</p> : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3.5 mb-6">
            {METRICS.map((m) => (
              <LeaderboardCard
                key={m.key}
                metric={m}
                rows={[...rows].sort((a, b) => b[m.key] - a[m.key]).slice(0, 5)}
              />
            ))}
          </div>

          {rows.length > 0 && (
            <div className="card p-4 mb-6">
              <h3 className="font-semibold text-sm text-gray-900 mb-1 flex items-center gap-2">
                <i className="bi bi-bar-chart-line text-emerald-500" /> Points scored vs. allowed
              </h3>
              <p className="text-xs text-gray-500 mb-4">Per completed match results, across all teams in the selected season/division.</p>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart
                  data={rows.slice().sort((a, b) => b.points_for - a.points_for)}
                  margin={{ top: 4, right: 8, left: -14, bottom: 4 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="team_name" tick={{ fontSize: 11 }} interval={0} angle={-18} textAnchor="end" height={60} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="points_for" name="Points scored" fill="#2563EB" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="points_against" name="Points allowed" fill="#F59E0B" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          <DataTable
            columns={[
              { key: 'rank', label: '#', render: (r) => r.rank },
              { key: 'team_name', label: 'Team', render: (r) => <span className="font-semibold text-gray-900">{r.team_name}</span> },
              { key: 'matches_played', label: 'GP' },
              { key: 'wins', label: 'W' },
              { key: 'losses', label: 'L' },
              { key: 'draws', label: 'D' },
              { key: 'points_for', label: 'PF' },
              { key: 'points_against', label: 'PA' },
              {
                key: 'point_differential',
                label: '+/-',
                render: (r) => <span className={r.point_differential > 0 ? 'text-emerald-600 font-semibold' : 'text-gray-700'}>{r.point_differential > 0 ? `+${r.point_differential}` : r.point_differential}</span>,
              },
              { key: 'win_percentage', label: 'Win %', render: (r) => `${r.win_percentage.toFixed(1)}%` },
              { key: 'points', label: 'PTS', render: (r) => <b>{r.points}</b> },
            ]}
            rows={rows}
            emptyLabel="No completed matches yet for this season/division."
          />

          {canViewPlayerStats && (
            <>
              <h2 className="text-lg font-bold text-gray-900 mt-8 mb-4">Player statistics</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3.5 mb-6">
                {PLAYER_METRICS.map((m) => (
                  <LeaderboardCard
                    key={m.key}
                    metric={m}
                    rows={[...playerRows].sort((a, b) => b[m.key] - a[m.key]).slice(0, 5)}
                    nameKey="player_name"
                    idKey="player_id"
                  />
                ))}
              </div>

              <DataTable
                columns={[
                  { key: 'rank', label: '#', render: (r) => r.rank },
                  { key: 'player_name', label: 'Player', render: (r) => <span className="font-semibold text-gray-900">{r.player_name}</span> },
                  { key: 'team_name', label: 'Team' },
                  { key: 'games_played', label: 'GP' },
                  { key: 'points', label: 'PTS', render: (r) => <b>{r.points}</b> },
                  { key: 'assists', label: 'AST' },
                  { key: 'rebounds', label: 'REB' },
                  { key: 'steals', label: 'STL' },
                  { key: 'fouls', label: 'FLS' },
                ]}
                rows={playerRows}
                emptyLabel="No player statistics recorded yet for this season/division."
              />
            </>
          )}
        </>
      )}
    </div>
  )
}
