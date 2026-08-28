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

const EMPTY = { full_name: '', license_number: '', contact_phone: '', status: 'Active' }

export default function RefereesPage() {
  const role = useAuthStore((s) => s.role)
  const qc = useQueryClient()
  const { data: referees, isLoading } = useQuery({ queryKey: ['referees'], queryFn: () => endpoints.referees.list().then((r) => r.data) })

  const [modal, setModal] = useState(null)
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState(null)

  const createMut = useMutation({
    mutationFn: (data) => endpoints.referees.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['referees'] }); setModal(null) },
    onError: setError,
  })
  const updateMut = useMutation({
    mutationFn: ({ id, data }) => endpoints.referees.update(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['referees'] }); setModal(null) },
    onError: setError,
  })

  function openCreate() { setForm(EMPTY); setError(null); setModal('create') }
  function openEdit(r) { setForm(r); setError(null); setModal(r) }
  function handleSave() {
    if (modal === 'create') createMut.mutate(form)
    else updateMut.mutate({ id: modal.id, data: form })
  }

  if (!can(role, 'referee.manage')) {
    return (
      <div className="card p-10 text-center text-gray-400">
        <i className="bi bi-lock text-2xl" />
        <p className="mt-2 text-sm">Referees requires the <b>referee.manage</b> permission, held by League Administrators, System Administrators, and Superadmins.</p>
      </div>
    )
  }

  return (
    <div>
      <PageHead
        title="Referees"
        subtitle="Officials who can be assigned to matches."
        actions={<button className="btn btn-primary" onClick={openCreate}><i className="bi bi-plus-lg" />New Referee</button>}
      />
      {isLoading ? <p className="text-sm text-gray-500">Loading...</p> : (
        <DataTable
          columns={[
            { key: 'full_name', label: 'Name', render: (r) => <span className="font-semibold text-gray-900">{r.full_name}</span> },
            { key: 'license_number', label: 'License #' },
            { key: 'contact_phone', label: 'Phone' },
            { key: 'status', label: 'Status', render: (r) => <Badge status={r.status} /> },
          ]}
          rows={referees}
          actions={(row) => [{ label: 'Edit', icon: 'bi-pencil', onClick: () => openEdit(row) }]}
          emptyLabel="No referees yet."
        />
      )}

      {modal && (
        <Modal
          title={modal === 'create' ? 'New referee' : `Edit ${modal.full_name}`}
          onClose={() => setModal(null)}
          footer={<>
            <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
            <button className="btn btn-primary" onClick={handleSave}><i className="bi bi-check-lg" />Save</button>
          </>}
        >
          <ErrorBanner error={error} />
          <Field label="Full name"><input className="input" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></Field>
          <Field label="License number"><input className="input" value={form.license_number} onChange={(e) => setForm({ ...form, license_number: e.target.value })} /></Field>
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
