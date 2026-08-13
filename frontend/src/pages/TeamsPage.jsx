import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { endpoints } from '../lib/api'
import { can } from '../lib/permissions'
import { useAuthStore } from '../store/authStore'
import PageHead from '../components/PageHead'
import DataTable from '../components/DataTable'
import Modal from '../components/Modal'
import Field from '../components/Field'
import Badge from '../components/Badge'
import ErrorBanner from '../components/ErrorBanner'
import { SportBadge, SportFilter } from '../components/SportControls'
import { buildSportMaps } from '../lib/sports'

const EMPTY = { division_id: '', name: '', coach_name: '', contact_email: '', contact_phone: '', status: 'Active' }

export default function TeamsPage() {
  const role = useAuthStore((s) => s.role)
  const qc = useQueryClient()
  const { data: teams, isLoading } = useQuery({ queryKey: ['teams'], queryFn: () => endpoints.teams.list().then((r) => r.data) })
  const { data: divisions } = useQuery({ queryKey: ['divisions'], queryFn: () => endpoints.divisions.list().then((r) => r.data) })
  const { data: seasons } = useQuery({ queryKey: ['seasons'], queryFn: () => endpoints.seasons.list().then((r) => r.data) })
  const { data: leagues } = useQuery({ queryKey: ['leagues'], queryFn: () => endpoints.leagues.list().then((r) => r.data) })

  const { sportOf, sports } = buildSportMaps({ leagues, seasons, divisions, teams })

  const [modal, setModal] = useState(null)
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState(null)
  const [sportFilter, setSportFilter] = useState('')

  const divisionName = (id) => divisions?.find((d) => d.id === id)?.name || '—'

  const visibleTeams = sportFilter ? teams?.filter((t) => sportOf.team(t.id) === sportFilter) : teams

  const createMut = useMutation({
    mutationFn: (data) => endpoints.teams.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['teams'] }); setModal(null) },
    onError: setError,
  })
  const updateMut = useMutation({
    mutationFn: ({ id, data }) => endpoints.teams.update(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['teams'] }); setModal(null) },
    onError: setError,
  })
  const deleteMut = useMutation({
    mutationFn: (id) => endpoints.teams.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['teams'] }),
    onError: setError,
  })

  function openCreate() { setForm({ ...EMPTY, division_id: divisions?.[0]?.id || '' }); setError(null); setModal('create') }
  function openEdit(t) { setForm(t); setError(null); setModal(t) }
  function handleSave() {
    if (modal === 'create') createMut.mutate(form)
    else { const { division_id, ...rest } = form; updateMut.mutate({ id: modal.id, data: rest }) }
  }

  return (
    <div>
      <PageHead
        title="Teams"
        subtitle="Teams compete within a division."
        actions={can(role, 'team.create') && divisions?.length > 0 && (
          <button className="btn btn-primary" onClick={openCreate}><i className="bi bi-plus-lg" />New Team</button>
        )}
      />
      {isLoading ? <p className="text-sm text-gray-500">Loading...</p> : (
        <>
          {sports.length > 0 && (
            <div className="card p-3.5 mb-4 flex gap-3 flex-wrap items-center">
              <label className="text-sm font-medium text-gray-700">Sport</label>
              <SportFilter sports={sports} value={sportFilter} onChange={setSportFilter} />
            </div>
          )}
          <DataTable
            columns={[
              { key: 'name', label: 'Name', render: (r) => <span className="font-semibold text-gray-900">{r.name}</span> },
              { key: 'sport', label: 'Sport', render: (r) => <SportBadge sport={sportOf.team(r.id)} /> },
              { key: 'division', label: 'Division', render: (r) => divisionName(r.division_id) },
              { key: 'coach_name', label: 'Coach' },
              { key: 'contact_email', label: 'Contact' },
              { key: 'status', label: 'Status', render: (r) => <Badge status={r.status} /> },
            ]}
            rows={visibleTeams}
            actions={(row) => [
              ...(can(role, 'team.update') ? [{ label: 'Edit', icon: 'bi-pencil', onClick: () => openEdit(row) }] : []),
              ...(can(role, 'team.delete') ? [{ label: 'Delete', icon: 'bi-trash', onClick: () => { if (confirm(`Delete "${row.name}"?`)) deleteMut.mutate(row.id) } }] : []),
            ]}
            emptyLabel="No teams yet."
          />
        </>
      )}

      {modal && (
        <Modal
          title={modal === 'create' ? 'New team' : `Edit ${modal.name}`}
          onClose={() => setModal(null)}
          footer={<>
            <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
            <button className="btn btn-primary" onClick={handleSave}><i className="bi bi-check-lg" />Save</button>
          </>}
        >
          <ErrorBanner error={error} />
          {modal === 'create' && (
            <Field label="Division">
              <select className="input" value={form.division_id} onChange={(e) => setForm({ ...form, division_id: e.target.value })}>
                {divisions?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </Field>
          )}
          <Field label="Name"><input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></Field>
          <Field label="Coach name"><input className="input" value={form.coach_name || ''} onChange={(e) => setForm({ ...form, coach_name: e.target.value })} /></Field>
          <Field label="Contact email"><input type="email" className="input" value={form.contact_email || ''} onChange={(e) => setForm({ ...form, contact_email: e.target.value })} /></Field>
          <Field label="Contact phone"><input className="input" value={form.contact_phone || ''} onChange={(e) => setForm({ ...form, contact_phone: e.target.value })} /></Field>
          <Field label="Status">
            <select className="input" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              <option>Active</option><option>Disqualified</option><option>Withdrawn</option>
            </select>
          </Field>
        </Modal>
      )}
    </div>
  )
}
