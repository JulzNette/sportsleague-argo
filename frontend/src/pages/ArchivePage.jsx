import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { endpoints } from '../lib/api'
import { can } from '../lib/permissions'
import { useAuthStore } from '../store/authStore'
import PageHead from '../components/PageHead'
import DataTable from '../components/DataTable'
import Badge from '../components/Badge'
import ErrorBanner from '../components/ErrorBanner'

const SECTIONS = [
  { key: 'leagues', label: 'Leagues', view: 'league.view', restore: 'league.update', purge: 'league.delete', list: () => endpoints.leagues.archived() },
  { key: 'seasons', label: 'Seasons', view: 'season.view', restore: 'season.update', purge: 'season.update', list: () => endpoints.seasons.archived() },
  { key: 'divisions', label: 'Divisions', view: 'division.view', restore: 'division.manage', purge: 'division.manage', list: () => endpoints.divisions.archived() },
  { key: 'teams', label: 'Teams', view: 'team.view', restore: 'team.update', purge: 'team.delete', list: () => endpoints.teams.archived() },
  { key: 'players', label: 'Players', view: 'player.view', restore: 'player.update', purge: 'player.delete', list: () => endpoints.players.archived() },
  { key: 'referees', label: 'Referees', view: 'referee.manage', restore: 'referee.manage', purge: 'referee.manage', list: () => endpoints.referees.archived() },
  { key: 'matches', label: 'Matches', view: 'match.view', restore: 'match.update', purge: 'match.update', list: () => endpoints.matches.archived() },
]

const TYPE_COLOR = {
  Leagues: 'bg-blue-50 text-blue-700',
  Seasons: 'bg-emerald-50 text-emerald-700',
  Divisions: 'bg-violet-50 text-violet-700',
  Teams: 'bg-amber-50 text-amber-700',
  Players: 'bg-rose-50 text-rose-700',
  Referees: 'bg-cyan-50 text-cyan-700',
  Matches: 'bg-indigo-50 text-indigo-700',
}

function rowName(row) {
  return row.name || row.full_name || (row.venue ? `${row.venue} · ${row.scheduled_date}` : row.id)
}

export default function ArchivePage() {
  const role = useAuthStore((s) => s.role)
  const qc = useQueryClient()
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('All')

  const sections = useMemo(() => SECTIONS.filter((s) => can(role, s.view)), [role])

  const queries = useQuery({
    queryKey: ['archive'],
    queryFn: async () => {
      const entries = {}
      await Promise.all(
        sections.map(async (sec) => {
          try {
            const { data } = await sec.list()
            entries[sec.key] = data.map((row) => ({ ...row, _type: sec.label }))
          } catch {
            entries[sec.key] = []
          }
        })
      )
      return entries
    },
  })

  const restoreMut = useMutation({
    mutationFn: ({ key, id }) => endpoints[key].restore(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['archive'] }); setError(null) },
    onError: setError,
  })
  const purgeMut = useMutation({
    mutationFn: ({ key, id }) => endpoints[key].purge(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['archive'] }); setError(null) },
    onError: setError,
  })

  const rows = useMemo(() => {
    const all = (queries.data ? Object.values(queries.data).flat() : []).sort(
      (a, b) => new Date(b.deleted_at || 0) - new Date(a.deleted_at || 0)
    )
    return filter === 'All' ? all : all.filter((r) => r._type === filter)
  }, [queries.data, filter])

  const totals = useMemo(() => {
    const t = {}
    SECTIONS.forEach((s) => { t[s.label] = queries.data?.[s.key]?.length || 0 })
    return t
  }, [queries.data])

  return (
    <div>
      <PageHead
        title="Archive"
        subtitle="Deleted records stay here until you restore or permanently remove them."
      />
      <ErrorBanner error={error} />

      <div className="flex flex-wrap gap-2 mb-4">
        <select className="input w-44" value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option>All</option>
          {SECTIONS.filter((s) => can(role, s.view)).map((s) => (
            <option key={s.key}>{s.label} ({totals[s.label]})</option>
          ))}
        </select>
      </div>

      {queries.isLoading ? <p className="text-sm text-gray-500">Loading...</p> : (
        <DataTable
          columns={[
            { key: '_type', label: 'Type', render: (r) => <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${TYPE_COLOR[r._type] || 'bg-gray-50 text-gray-600'}`}>{r._type}</span> },
            { key: 'name', label: 'Name', render: (r) => (
              <span className="font-semibold text-gray-900">{rowName(r)}</span>
            ) },
            { key: 'status', label: 'Status', render: (r) => <Badge status={r.status} /> },
            { key: 'deleted_at', label: 'Archived', render: (r) => new Date(r.deleted_at).toLocaleString() },
          ]}
          rows={rows}
          actions={(row) => {
            const sec = SECTIONS.find((s) => s.label === row._type)
            return [
              ...(can(role, sec.restore) ? [{ label: 'Restore', icon: 'bi-arrow-counterclockwise', onClick: () => restoreMut.mutate({ key: sec.key, id: row.id }) }] : []),
              ...(can(role, sec.purge) ? [{ label: 'Delete permanently', icon: 'bi-trash3', onClick: () => { if (confirm(`Permanently delete this ${row._type.toLowerCase()}? This cannot be undone.`)) purgeMut.mutate({ key: sec.key, id: row.id }) } }] : []),
            ]
          }}
          emptyLabel="Archive is empty."
        />
      )}
    </div>
  )
}

