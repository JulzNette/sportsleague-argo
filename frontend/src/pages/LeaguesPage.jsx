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
import { SPORTS } from '../lib/sports'

const EMPTY = { name: '', sport_type: '', description: '', status: 'Active' }

export default function LeaguesPage() {
  const role = useAuthStore((s) => s.role)
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['leagues'], queryFn: () => endpoints.leagues.list().then((r) => r.data) })

  const [modal, setModal] = useState(null) // null | 'create' | league object being edited
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState(null)

  const createMut = useMutation({
    mutationFn: (data) => endpoints.leagues.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['leagues'] }); setModal(null) },
    onError: setError,
  })
  const updateMut = useMutation({
    mutationFn: ({ id, data }) => endpoints.leagues.update(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['leagues'] }); setModal(null) },
    onError: setError,
  })
  const deleteMut = useMutation({
    mutationFn: (id) => endpoints.leagues.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['leagues'] }),
    onError: setError,
  })

  function openCreate() { setForm(EMPTY); setError(null); setModal('create') }
  function openEdit(league) { setForm(league); setError(null); setModal(league) }

  function handleSave() {
    if (modal === 'create') createMut.mutate(form)
    else updateMut.mutate({ id: modal.id, data: form })
  }

  return (
    <div>
      <PageHead
        title="Leagues"
        subtitle="Top-level competitions your organization runs."
        actions={can(role, 'league.create') && (
          <button className="btn btn-primary" onClick={openCreate}><i className="bi bi-plus-lg" />New League</button>
        )}
      />
      {isLoading ? (
        <p className="text-sm text-gray-500">Loading...</p>
      ) : (
        <DataTable
          columns={[
            { key: 'name', label: 'Name', render: (r) => <span className="font-semibold text-gray-900">{r.name}</span> },
            { key: 'sport_type', label: 'Sport' },
            { key: 'description', label: 'Description' },
            { key: 'status', label: 'Status', render: (r) => <Badge status={r.status} /> },
          ]}
          rows={data}
          actions={(row) => [
            ...(can(role, 'league.update') ? [{ label: 'Edit', icon: 'bi-pencil', onClick: () => openEdit(row) }] : []),
            ...(can(role, 'league.delete') ? [{ label: 'Delete', icon: 'bi-trash', onClick: () => { if (confirm(`Delete "${row.name}"?`)) deleteMut.mutate(row.id) } }] : []),
          ]}
          emptyLabel="No leagues yet — create one to get started."
        />
      )}

      {modal && (
        <Modal
          title={modal === 'create' ? 'New league' : `Edit ${modal.name}`}
          onClose={() => setModal(null)}
          footer={<>
            <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
            <button className="btn btn-primary" onClick={handleSave} disabled={createMut.isPending || updateMut.isPending}>
              <i className="bi bi-check-lg" />Save
            </button>
          </>}
        >
          <ErrorBanner error={error} />
          <Field label="Name">
            <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Field>
          <Field label="Sport type">
            <select className="input" value={form.sport_type} onChange={(e) => setForm({ ...form, sport_type: e.target.value })}>
              <option value="" disabled>Select a sport...</option>
              {SPORTS.map((sport) => <option key={sport} value={sport}>{sport}</option>)}
            </select>
          </Field>
          <Field label="Description">
            <textarea className="input" rows={2} value={form.description || ''} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </Field>
          <Field label="Status">
            <select className="input" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              <option>Active</option>
              <option>Archived</option>
            </select>
          </Field>
        </Modal>
      )}
    </div>
  )
}
