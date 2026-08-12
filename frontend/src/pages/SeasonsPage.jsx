import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { endpoints } from '../lib/api'
import { can } from '../lib/permissions'
import { SEASON_STATUS_TRANSITIONS } from '../lib/statusMachines'
import { useAuthStore } from '../store/authStore'
import PageHead from '../components/PageHead'
import DataTable from '../components/DataTable'
import Modal from '../components/Modal'
import Field from '../components/Field'
import Badge from '../components/Badge'
import ErrorBanner from '../components/ErrorBanner'

const EMPTY = { league_id: '', name: '', start_date: '', end_date: '', format: 'Round Robin', status: 'Draft' }

export default function SeasonsPage() {
  const role = useAuthStore((s) => s.role)
  const qc = useQueryClient()
  const { data: seasons, isLoading } = useQuery({ queryKey: ['seasons'], queryFn: () => endpoints.seasons.list().then((r) => r.data) })
  const { data: leagues } = useQuery({ queryKey: ['leagues'], queryFn: () => endpoints.leagues.list().then((r) => r.data) })

  const [modal, setModal] = useState(null)
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState(null)

  const leagueName = (id) => leagues?.find((l) => l.id === id)?.name || '—'

  const createMut = useMutation({
    mutationFn: (data) => endpoints.seasons.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['seasons'] }); setModal(null) },
    onError: setError,
  })
  const updateMut = useMutation({
    mutationFn: ({ id, data }) => endpoints.seasons.update(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['seasons'] }); setModal(null) },
    onError: setError,
  })

  function openCreate() { setForm({ ...EMPTY, league_id: leagues?.[0]?.id || '' }); setError(null); setModal('create') }
  function openEdit(season) { setForm(season); setError(null); setModal(season) }

  function handleSave() {
    if (modal === 'create') createMut.mutate(form)
    else {
      const { league_id, ...rest } = form // league_id is immutable after creation
      updateMut.mutate({ id: modal.id, data: rest })
    }
  }

  const availableTransitions = modal && modal !== 'create' ? SEASON_STATUS_TRANSITIONS[modal.status] || [] : []

  return (
    <div>
      <PageHead
        title="Seasons"
        subtitle="Each season belongs to one league and runs for a fixed date range."
        actions={can(role, 'season.create') && leagues?.length > 0 && (
          <button className="btn btn-primary" onClick={openCreate}><i className="bi bi-plus-lg" />New Season</button>
        )}
      />
      {isLoading ? <p className="text-sm text-gray-500">Loading...</p> : (
        <DataTable
          columns={[
            { key: 'name', label: 'Name', render: (r) => <span className="font-semibold text-gray-900">{r.name}</span> },
            { key: 'league', label: 'League', render: (r) => leagueName(r.league_id) },
            { key: 'dates', label: 'Dates', render: (r) => `${r.start_date} → ${r.end_date}` },
            { key: 'format', label: 'Format' },
            { key: 'status', label: 'Status', render: (r) => <Badge status={r.status} /> },
          ]}
          rows={seasons}
          actions={(row) => can(role, 'season.update') ? [{ label: 'Edit', icon: 'bi-pencil', onClick: () => openEdit(row) }] : []}
          emptyLabel="No seasons yet."
        />
      )}

      {modal && (
        <Modal
          title={modal === 'create' ? 'New season' : `Edit ${modal.name}`}
          onClose={() => setModal(null)}
          footer={<>
            <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
            <button className="btn btn-primary" onClick={handleSave} disabled={createMut.isPending || updateMut.isPending}>
              <i className="bi bi-check-lg" />Save
            </button>
          </>}
        >
          <ErrorBanner error={error} />
          {modal === 'create' && (
            <Field label="League">
              <select className="input" value={form.league_id} onChange={(e) => setForm({ ...form, league_id: e.target.value })}>
                {leagues?.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
              </select>
            </Field>
          )}
          <Field label="Name">
            <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Start date">
              <input type="date" className="input" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
            </Field>
            <Field label="End date">
              <input type="date" className="input" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
            </Field>
          </div>
          <Field label="Format">
            <select className="input" value={form.format} onChange={(e) => setForm({ ...form, format: e.target.value })}>
              <option>Round Robin</option>
              <option>Single Elimination</option>
              <option>Custom</option>
            </select>
          </Field>
          {modal !== 'create' && (
            <Field label={`Status (currently ${modal.status})`}>
              <select className="input" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                <option value={modal.status}>{modal.status} (no change)</option>
                {availableTransitions.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </Field>
          )}
        </Modal>
      )}
    </div>
  )
}
