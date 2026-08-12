import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { endpoints } from '../lib/api'
import { can } from '../lib/permissions'
import { useAuthStore } from '../store/authStore'
import PageHead from '../components/PageHead'
import DataTable from '../components/DataTable'
import Modal from '../components/Modal'
import Field from '../components/Field'
import ErrorBanner from '../components/ErrorBanner'

const EMPTY = { name: '', type: 'Season Summary', season_id: '', division_id: '' }

export default function ReportsPage() {
  const role = useAuthStore((s) => s.role)
  const qc = useQueryClient()
  const { data: reports, isLoading } = useQuery({ queryKey: ['reports'], queryFn: () => endpoints.reports.list().then((r) => r.data) })
  const { data: seasons } = useQuery({ queryKey: ['seasons'], queryFn: () => endpoints.seasons.list().then((r) => r.data) })

  const [modal, setModal] = useState(null) // 'create' | { view: report }
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState(null)
  const [viewRows, setViewRows] = useState(null)

  const seasonName = (id) => seasons?.find((s) => s.id === id)?.name || 'All seasons'

  const createMut = useMutation({
    mutationFn: (data) => endpoints.reports.create({ ...data, season_id: data.season_id || null, division_id: data.division_id || null }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['reports'] }); setModal(null) },
    onError: setError,
  })

  async function openView(report) {
    setError(null)
    setViewRows(null)
    setModal({ view: report })
    try {
      const res = await endpoints.reports.viewStandings(report.id)
      setViewRows(res.data)
    } catch (err) {
      setError(err)
    }
  }

  if (!can(role, 'report.view')) {
    return (
      <div className="card p-10 text-center text-gray-400">
        <i className="bi bi-lock text-2xl" />
        <p className="mt-2 text-sm">Reports requires the <b>report.view</b> permission.</p>
      </div>
    )
  }

  return (
    <div>
      <PageHead
        title="Reports"
        subtitle="Metadata only — standings content is always recomputed live when you open a report."
        actions={can(role, 'report.generate') && (
          <button className="btn btn-primary" onClick={() => { setForm({ ...EMPTY, season_id: seasons?.[0]?.id || '' }); setError(null); setModal('create') }}>
            <i className="bi bi-plus-lg" />Generate Report
          </button>
        )}
      />
      {isLoading ? <p className="text-sm text-gray-500">Loading...</p> : (
        <DataTable
          columns={[
            { key: 'name', label: 'Report name', render: (r) => <span className="font-semibold text-gray-900">{r.name}</span> },
            { key: 'type', label: 'Type' },
            { key: 'season', label: 'Season', render: (r) => seasonName(r.season_id) },
            { key: 'created_at', label: 'Generated at', render: (r) => new Date(r.created_at).toLocaleString() },
          ]}
          rows={reports}
          actions={(row) => [{ label: 'View', icon: 'bi-eye', onClick: () => openView(row) }]}
          emptyLabel="No reports generated yet."
        />
      )}

      {modal === 'create' && (
        <Modal
          title="Generate report"
          onClose={() => setModal(null)}
          footer={<>
            <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
            <button className="btn btn-primary" onClick={() => createMut.mutate(form)}><i className="bi bi-check-lg" />Generate</button>
          </>}
        >
          <ErrorBanner error={error} />
          <Field label="Report name"><input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></Field>
          <Field label="Type">
            <select className="input" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
              <option>Season Summary</option><option>Match Report</option><option>Team Statistics</option><option>Referee Activity</option>
            </select>
          </Field>
          <Field label="Season">
            <select className="input" value={form.season_id} onChange={(e) => setForm({ ...form, season_id: e.target.value })}>
              {seasons?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </Field>
        </Modal>
      )}

      {modal?.view && (
        <Modal
          title={modal.view.name}
          subtitle={`${modal.view.type} · Standings recomputed live, right now`}
          onClose={() => setModal(null)}
          footer={<button className="btn btn-secondary" onClick={() => setModal(null)}>Close</button>}
        >
          <ErrorBanner error={error} />
          {viewRows === null ? (
            <p className="text-sm text-gray-500">Loading...</p>
          ) : (
            <DataTable
              columns={[
                { key: 'team_name', label: 'Team', render: (r) => <span className="font-semibold">{r.team_name}</span> },
                { key: 'matches_played', label: 'MP' },
                { key: 'wins', label: 'W' },
                { key: 'losses', label: 'L' },
                { key: 'draws', label: 'D' },
                { key: 'points', label: 'PTS' },
              ]}
              rows={viewRows.map((r) => ({ ...r, id: r.team_id }))}
              emptyLabel="No completed matches to report on."
            />
          )}
        </Modal>
      )}
    </div>
  )
}
