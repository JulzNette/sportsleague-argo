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

const EMPTY = { team_id: '', full_name: '', date_of_birth: '', position: '', jersey_number: '', contact_phone: '', status: 'Active' }

export default function PlayersPage() {
  const role = useAuthStore((s) => s.role)
  const qc = useQueryClient()
  const { data: players, isLoading } = useQuery({ queryKey: ['players'], queryFn: () => endpoints.players.list().then((r) => r.data) })
  const { data: teams } = useQuery({ queryKey: ['teams'], queryFn: () => endpoints.teams.list().then((r) => r.data) })

  const [modal, setModal] = useState(null)
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState(null)

  const teamName = (id) => teams?.find((t) => t.id === id)?.name || '—'

  const createMut = useMutation({
    mutationFn: (data) => endpoints.players.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['players'] }); setModal(null) },
    onError: setError,
  })
  const updateMut = useMutation({
    mutationFn: ({ id, data }) => endpoints.players.update(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['players'] }); setModal(null) },
    onError: setError,
  })
  const deleteMut = useMutation({
    mutationFn: (id) => endpoints.players.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['players'] }),
    onError: setError,
  })

  function openCreate() { setForm({ ...EMPTY, team_id: teams?.[0]?.id || '' }); setError(null); setModal('create') }
  function openEdit(p) { setForm(p); setError(null); setModal(p) }
  function handleSave() {
    if (modal === 'create') createMut.mutate(form)
    else { const { team_id, ...rest } = form; updateMut.mutate({ id: modal.id, data: rest }) }
  }

  return (
    <div>
      <PageHead
        title="Players"
        subtitle="Roster members belonging to a team."
        actions={can(role, 'player.create') && teams?.length > 0 && (
          <button className="btn btn-primary" onClick={openCreate}><i className="bi bi-plus-lg" />New Player</button>
        )}
      />
      {isLoading ? <p className="text-sm text-gray-500">Loading...</p> : (
        <DataTable
          columns={[
            { key: 'full_name', label: 'Name', render: (r) => <span className="font-semibold text-gray-900">{r.full_name}</span> },
            { key: 'team', label: 'Team', render: (r) => teamName(r.team_id) },
            { key: 'position', label: 'Position' },
            { key: 'jersey_number', label: '#' },
            { key: 'status', label: 'Status', render: (r) => <Badge status={r.status} /> },
          ]}
          rows={players}
          actions={(row) => [
            ...(can(role, 'player.update') ? [{ label: 'Edit', icon: 'bi-pencil', onClick: () => openEdit(row) }] : []),
            ...(can(role, 'player.delete') ? [{ label: 'Delete', icon: 'bi-trash', onClick: () => { if (confirm(`Remove "${row.full_name}"?`)) deleteMut.mutate(row.id) } }] : []),
          ]}
          emptyLabel="No players yet."
        />
      )}

      {modal && (
        <Modal
          title={modal === 'create' ? 'New player' : `Edit ${modal.full_name}`}
          onClose={() => setModal(null)}
          footer={<>
            <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
            <button className="btn btn-primary" onClick={handleSave}><i className="bi bi-check-lg" />Save</button>
          </>}
        >
          <ErrorBanner error={error} />
          {modal === 'create' && (
            <Field label="Team">
              <select className="input" value={form.team_id} onChange={(e) => setForm({ ...form, team_id: e.target.value })}>
                {teams?.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
            </Field>
          )}
          <Field label="Full name"><input className="input" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Position"><input className="input" value={form.position || ''} onChange={(e) => setForm({ ...form, position: e.target.value })} /></Field>
            <Field label="Jersey #"><input className="input" value={form.jersey_number} onChange={(e) => setForm({ ...form, jersey_number: e.target.value })} /></Field>
          </div>
          <Field label="Date of birth"><input type="date" className="input" value={form.date_of_birth || ''} onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })} /></Field>
          <Field label="Contact phone"><input className="input" value={form.contact_phone || ''} onChange={(e) => setForm({ ...form, contact_phone: e.target.value })} /></Field>
          <Field label="Status">
            <select className="input" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              <option>Active</option><option>Inactive</option><option>Suspended</option>
            </select>
          </Field>
        </Modal>
      )}
    </div>
  )
}
