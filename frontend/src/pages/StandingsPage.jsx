import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { endpoints } from '../lib/api'
import PageHead from '../components/PageHead'
import DataTable from '../components/DataTable'

export default function StandingsPage() {
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

  return (
    <div>
      <PageHead title="Standings" subtitle="Always computed live from completed match results — never stored." />

      <div className="card p-3.5 mb-4 flex gap-3 flex-wrap items-center">
        <select className="input w-auto" value={activeSeasonId || ''} onChange={(e) => { setSeasonId(e.target.value); setDivisionId('') }}>
          {seasons?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <select className="input w-auto" value={divisionId} onChange={(e) => setDivisionId(e.target.value)}>
          <option value="">All divisions</option>
          {divisions?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
      </div>

      {isLoading ? <p className="text-sm text-gray-500">Computing standings...</p> : (
        <DataTable
          columns={[
            { key: 'rank', label: '#', render: (r) => r.rank },
            { key: 'team_name', label: 'Team', render: (r) => <span className="font-semibold text-gray-900">{r.team_name}</span> },
            { key: 'matches_played', label: 'MP' },
            { key: 'wins', label: 'W' },
            { key: 'losses', label: 'L' },
            { key: 'draws', label: 'D' },
            { key: 'points', label: 'PTS', render: (r) => <b>{r.points}</b> },
          ]}
          rows={standings?.map((r, i) => ({ ...r, id: r.team_id, rank: i + 1 }))}
          emptyLabel="No completed matches yet for this season/division."
        />
      )}
    </div>
  )
}
