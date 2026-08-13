import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { endpoints } from '../lib/api'
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

function LeaderboardCard({ metric, rows }) {
  return (
    <div className="card">
      <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2">
        <i className={`bi ${metric.icon} text-emerald-500`} />
        <h3 className="font-semibold text-sm text-gray-900">{metric.label}</h3>
      </div>
      <ol className="divide-y divide-gray-100">
        {rows.length === 0 && <li className="px-4 py-8 text-center text-sm text-gray-400">No data yet.</li>}
        {rows.map((r, i) => (
          <li key={r.team_id} className="flex items-center gap-3 px-4 py-2.5">
            <span className={`w-6 h-6 shrink-0 rounded-full flex items-center justify-center text-xs font-bold ${MEDAL[i] || MEDAL[3]}`}>
              {i + 1}
            </span>
            <span className="flex-1 font-semibold text-sm text-gray-900 truncate">{r.team_name}</span>
            <span className="text-sm text-gray-500">{metric.format(r)}</span>
          </li>
        ))}
      </ol>
    </div>
  )
}

export default function StatisticsPage() {
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

  const rows = (standings || []).map((r) => ({ ...r, id: r.team_id }))

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
        </>
      )}
    </div>
  )
}
