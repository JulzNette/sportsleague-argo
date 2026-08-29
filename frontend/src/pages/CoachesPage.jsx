import { useMemo, useState } from 'react'
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

const EMPTY = { team_id: '', full_name: '', role: 'Head Coach', email: '', phone: '', credentials: '', status: 'Active' }

const STATUS_COLOR = { Active: 'success', Inactive: 'neutral' }

export default function CoachesPage() {
  const role = useAuthStore((s) => s.role)
  const qc = useQueryClient()
  const { data: coaches, isLoading } = useQuery({ queryKey: ['coaches'], queryFn: () => endpoints.coaches.list().then((r) => r.data) })
  const { data: teams } = useQuery({ queryKey: ['teams'], queryFn: () => endpoints.teams.list().then((r) => r.data) })

  const [modal, setModal] = useState(null)
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState(null)

  const teamName = (id) => teams?.find((t) => t.id === id)?.name || 'Unassigned'

  const createMut = useMutation({
    mutationFn: (data) => endpoints.coaches.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['coaches'] }); setModal(null) },
    onError: setError,
  })
  const updateMut = useMutation({
    mutationFn: ({ id, data }) => endpoints.coaches.update(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['coaches'] }); setModal(null) },
    onError: setError,
  })
  const deleteMut = useMutation({
    mutationFn: (id) => endpoints.coaches.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['coaches'] }),
    onError: setError,
  })

  function openCreate() { setForm({ ...EMPTY, team_id: teams?.[0]?.id || '' }); setError(null); setModal('create') }
  function openEdit(c) { setForm(c); setError(null); setModal(c) }
  function handleSave() {
    if (modal === 'create') createMut.mutate(form)
    else updateMut.mutate({ id: modal.id, data: form })
  }

  const groups = useMemo(() => {
    const byTeam = {}
    for (const c of coaches || []) byTeam[c.team_id] = (byTeam[c.team_id] || []).concat(c)
    return Object.entries(byTeam)
      .sort(([a], [b]) => teamName(a).localeCompare(teamName(b)))
      .map(([tid, list]) => ({ id: tid, coaches: list }))
  }, [coaches, teams])

  return (
    <div>
      <PageHead
        title="Coaches"
        subtitle="Coaching staff records, one head coach per team."
        actions={can(role, 'coach.manage') && teams?.length > 0 && (
          <button className="btn btn-primary" onClick={openCreate}><i className="bi bi-plus-lg" />New Coach</button>
        )}
      />

      {isLoading ? (
        <p className="text-sm text-gray-500">Loading...</p>
      ) : groups.length === 0 ? (
        <DataTable rows={[]} emptyLabel="No coaches yet." />
      ) : (
        <div className="space-y-5">
          {groups.map((group) => (
            <div key={group.id} className="card overflow-hidden">
              <div className="flex items-center gap-2.5 px-4 py-3 bg-gray-50 border-b border-gray-200">
                <i className="bi bi-people text-gray-400" />
                <span className="font-semibold text-sm text-gray-900">{teamName(group.id)}</span>
                <span className="ml-auto text-xs text-gray-500">{group.coaches.length} coach{group.coaches.length === 1 ? '' : 'es'}</span>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-y border-gray-200">
                    <th className="text-left font-semibold text-gray-500 uppercase text-xs tracking-wide px-4 py-2">Name</th>
                    <th className="text-left font-semibold text-gray-500 uppercase text-xs tracking-wide px-4 py-2">Role</th>
                    <th className="text-left font-semibold text-gray-500 uppercase text-xs tracking-wide px-4 py-2">Email</th>
                    <th className="text-left font-semibold text-gray-500 uppercase text-xs tracking-wide px-4 py-2">Phone</th>
                    <th className="text-left font-semibold text-gray-500 uppercase text-xs tracking-wide px-4 py-2">Status</th>
                    {can(role, 'coach.manage') && <th className="w-1" />}
                  </tr>
                </thead>
                <tbody>
                  {group.coaches.map((c) => (
                    <tr key={c.id} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                      <td className="px-4 py-2.5 font-semibold text-gray-900">{c.full_name}</td>
                      <td className="px-4 py-2.5 text-gray-700">{c.role}</td>
                      <td className="px-4 py-2.5 text-gray-500">{c.email || '—'}</td>
                      <td className="px-4 py-2.5 text-gray-500">{c.phone || '—'}</td>
                      <td className="px-4 py-2.5">{STATUS_COLOR[c.status] ? <Badge status={c.status} /> : c.status}</td>
                      {can(role, 'coach.manage') && (
                        <td className="px-4 py-2.5 text-right whitespace-nowrap">
                          <div className="flex justify-end gap-1">
                            <button onClick={() => openEdit(c)} title="Edit" className="w-7 h-7 inline-flex items-center justify-center rounded-md border border-gray-200 text-gray-500 hover:bg-gray-100">
                              <i className="bi bi-pencil" />
                            </button>
                            <button onClick={() => { if (confirm(`Remove "${c.full_name}"?`)) deleteMut.mutate(c.id) }} title="Delete" className="w-7 h-7 inline-flex items-center justify-center rounded-md border border-gray-200 text-gray-500 hover:bg-gray-100">
                              <i className="bi bi-trash" />
                            </button>
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      )}

      {modal && (
        <Modal
          title={modal === 'create' ? 'New coach' : `Edit ${modal.full_name}`}
          onClose={() => setModal(null)}
          footer={<>
            <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
            <button className="btn btn-primary" onClick={handleSave}><i className="bi bi-check-lg" />Save</button>
          </>}
        >
          <ErrorBanner error={error} />
          <Field label="Team">
            <select className="input" value={form.team_id || ''} onChange={(e) => setForm({ ...form, team_id: e.target.value })}>
              <option value="">Unassigned</option>
              {teams?.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </Field>
          <Field label="Full name"><input className="input" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></Field>
          <Field label="Role">
            <select className="input" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              <option>Head Coach</option><option>Assistant Coach</option>
            </select>
          </Field>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Field label="Email"><input className="input" value={form.email || ''} onChange={(e) => setForm({ ...form, email: e.target.value })} /></Field>
            <Field label="Phone"><input className="input" value={form.phone || ''} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></Field>
          </div>
          <Field label="Credentials / License"><input className="input" value={form.credentials || ''} onChange={(e) => setForm({ ...form, credentials: e.target.value })} /></Field>
          <Field label="Status">
            <select className="input" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              <option>Active</option><option>Inactive</option>
            </select>
          </Field>
        </Modal>
      )}
    </div>
  )
}
