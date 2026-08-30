import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { endpoints } from '../lib/api'
import { can, ROLES } from '../lib/permissions'
import { useAuthStore } from '../store/authStore'
import PageHead from '../components/PageHead'
import DataTable from '../components/DataTable'
import Modal from '../components/Modal'
import Field from '../components/Field'
import ErrorBanner from '../components/ErrorBanner'

const EMPTY = { full_name: '', email: '', contact_phone: '', password: '', role: 'Viewer' }

export default function UsersPage() {
  const role = useAuthStore((s) => s.role)
  const email = useAuthStore((s) => s.email)
  const qc = useQueryClient()
  const { data: users = [], isLoading } = useQuery({ queryKey: ['users'], queryFn: () => endpoints.users.list().then((r) => r.data) })

  const [modal, setModal] = useState(null)
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState(null)

  const canCreate = can(role, 'user.create')
  const canUpdate = can(role, 'user.update')
  const canReset = can(role, 'user.reset_password')
  const canDelete = can(role, 'user.delete')
  const canPurge = can(role, 'user.purge')

  const invalidate = () => qc.invalidateQueries({ queryKey: ['users'] })

  const createMut = useMutation({
    mutationFn: (data) => endpoints.users.create(data),
    onSuccess: () => { invalidate(); setModal(null) },
    onError: setError,
  })
  const updateMut = useMutation({
    mutationFn: ({ id, data }) => endpoints.users.update(id, data),
    onSuccess: () => { invalidate(); setModal(null) },
    onError: setError,
  })
  const resetMut = useMutation({
    mutationFn: ({ id, data }) => endpoints.users.resetPassword(id, data),
    onSuccess: () => { invalidate(); setModal(null) },
    onError: setError,
  })
  const deleteMut = useMutation({
    mutationFn: (id) => endpoints.users.remove(id),
    onSuccess: () => invalidate(),
    onError: setError,
  })
  const purgeMut = useMutation({
    mutationFn: (id) => endpoints.users.purge(id),
    onSuccess: () => invalidate(),
    onError: setError,
  })

  function openCreate() { setForm(EMPTY); setError(null); setModal('create') }
  function openEdit(u) { setForm({ full_name: u.full_name, email: u.email, contact_phone: u.contact_phone || '', role: u.role }); setError(null); setModal({ mode: 'edit', user: u }) }
  function openReset(u) { setForm({ password: '' }); setError(null); setModal({ mode: 'reset', user: u }) }

  function handleSaveCreate() {
    createMut.mutate(form)
  }
  function handleSaveEdit() {
    updateMut.mutate({ id: modal.user.id, data: { full_name: form.full_name, contact_phone: form.contact_phone, role: form.role } })
  }
  function handleSaveReset() {
    resetMut.mutate({ id: modal.user.id, data: { password: form.password } })
  }

  const columns = [
    { key: 'full_name', label: 'Name', render: (u) => (
      <div className="flex items-center gap-2">
        <span className="font-semibold text-gray-900">{u.full_name}</span>
        {u.email === email && <span className="text-[10px] font-bold uppercase bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">You</span>}
        {!u.is_active && <span className="text-[10px] font-bold uppercase bg-rose-100 text-rose-700 px-1.5 py-0.5 rounded">Inactive</span>}
      </div>
    ) },
    { key: 'email', label: 'Email' },
    { key: 'role', label: 'Role', render: (u) => <span className="font-medium text-gray-800">{u.role}</span> },
    { key: 'contact_phone', label: 'Contact', render: (u) => u.contact_phone || '—' },
    { key: 'created_at', label: 'Joined', render: (u) => new Date(u.created_at).toLocaleDateString() },
  ]

  const isSelf = (u) => u.email === email

  const actions = () => [
    ...(canUpdate ? [{ label: 'Edit', icon: 'bi-pencil', onClick: (u) => !isSelf(u) && openEdit(u) }] : []),
    ...(canReset ? [{ label: 'Reset password', icon: 'bi-key', onClick: (u) => !isSelf(u) && openReset(u) }] : []),
    ...(canDelete ? [{
      label: u => (u.is_active ? 'Deactivate' : 'Activate'),
      icon: 'bi-person-x',
      onClick: (u) => { if (isSelf(u)) return; const action = u.is_active ? 'deactivate' : 'activate'; if (confirm(`Do you want to ${action} "${u.full_name}"?`)) deleteMut.mutate(u.id) },
    }] : []),
    ...(canPurge ? [{
      label: 'Delete forever',
      icon: 'bi-trash',
      danger: true,
      onClick: (u) => { if (isSelf(u)) return; if (confirm(`Permanently delete "${u.full_name}"? This frees their email for reuse and cannot be undone.`)) purgeMut.mutate(u.id) },
    }] : []),
  ]

  return (
    <div>
      <PageHead
        title="User Management"
        subtitle="Manage all accounts and roles in the system."
        actions={canCreate && (
          <button className="btn btn-primary" onClick={openCreate}><i className="bi bi-person-plus" />New User</button>
        )}
      />

      {isLoading ? (
        <p className="text-sm text-gray-500">Loading...</p>
      ) : (
        <DataTable columns={columns} rows={users} actions={canUpdate || canReset || canDelete ? actions : undefined} emptyLabel="No users yet." />
      )}

      {modal === 'create' && (
        <Modal title="New user" subtitle="Create an account and assign a role." onClose={() => setModal(null)} footer={<>
          <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSaveCreate}><i className="bi bi-check-lg" />Create</button>
        </>}>
          <ErrorBanner error={error} />
          <Field label="Full name"><input className="input" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></Field>
          <Field label="Email"><input className="input" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></Field>
          <Field label="Contact phone"><input className="input" value={form.contact_phone || ''} onChange={(e) => setForm({ ...form, contact_phone: e.target.value })} /></Field>
          <Field label="Temporary password">
            <input className="input" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
            <p className="text-xs text-gray-400 mt-1">At least 8 characters. Tell the user to change it after logging in.</p>
          </Field>
          <Field label="Role">
            <select className="input" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </Field>
        </Modal>
      )}

      {modal?.mode === 'edit' && (
        <Modal title={`Edit ${modal.user.full_name}`} subtitle={modal.user.email} onClose={() => setModal(null)} footer={<>
          <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSaveEdit}><i className="bi bi-check-lg" />Save</button>
        </>}>
          <ErrorBanner error={error} />
          <Field label="Full name"><input className="input" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></Field>
          <Field label="Contact phone"><input className="input" value={form.contact_phone || ''} onChange={(e) => setForm({ ...form, contact_phone: e.target.value })} /></Field>
          <Field label="Role">
            <select className="input" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </Field>
        </Modal>
      )}

      {modal?.mode === 'reset' && (
        <Modal title={`Reset password for ${modal.user.full_name}`} subtitle={modal.user.email} onClose={() => setModal(null)} footer={<>
          <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSaveReset}><i className="bi bi-check-lg" />Reset</button>
        </>}>
          <ErrorBanner error={error} />
          <Field label="New password">
            <input className="input" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
            <p className="text-xs text-gray-400 mt-1">At least 8 characters. The user can log in with this new password.</p>
          </Field>
        </Modal>
      )}
    </div>
  )
}
