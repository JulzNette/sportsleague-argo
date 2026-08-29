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

const EMPTY = { season_id: '', name: '', max_teams: 8, status: 'Active' }

export default function DivisionsPage() {
  const role = useAuthStore((s) => s.role)
  const qc = useQueryClient()
  const { data: divisions, isLoading } = useQuery({ queryKey: ['divisions'], queryFn: () => endpoints.divisions.list().then((r) => r.data) })
  const { data: seasons } = useQuery({ queryKey: ['seasons'], queryFn: () => endpoints.seasons.list().then((r) => r.data) })
  const { data: leagues } = useQuery({ queryKey: ['leagues'], queryFn: () => endpoints.leagues.list().then((r) => r.data) })

  const { sportOf, sports } = buildSportMaps({ leagues, seasons, divisions })

  const [modal, setModal] = useState(null)
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState(null)
  const [sportFilter, setSportFilter] = useState('')

  const seasonName = (id) => seasons?.find((s) => s.id === id)?.name || '—'

  const visibleDivisions = sportFilter ? divisions?.filter((d) => sportOf.season(d.season_id) === sportFilter) : divisions

  const createMut = useMutation({
    mutationFn: (data) => endpoints.divisions.create(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['divisions'] }); setModal(null) },
    onError: setError,
  })
  const updateMut = useMutation({
    mutationFn: ({ id, data }) => endpoints.divisions.update(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['divisions'] }); setModal(null) },
    onError: setError,
  })
  const deleteMut = useMutation({
    mutationFn: (id) => endpoints.divisions.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['divisions'] }),
    onError: setError,
  })

  function openCreate() { setForm({ ...EMPTY, season_id: seasons?.[0]?.id || '' }); setError(null); setModal('create') }
  function openEdit(d) { setForm(d); setError(null); setModal(d) }
  function handleSave() {
    if (modal === 'create') createMut.mutate(form)
    else { const { season_id, ...rest } = form; updateMut.mutate({ id: modal.id, data: rest }) }
  }

  return (
    <div>
      <PageHead
        title="Divisions"
        subtitle="Groups of teams within a season that play each other."
        actions={can(role, 'division.manage') && seasons?.length > 0 && (
          <button className="btn btn-primary" onClick={openCreate}><i className="bi bi-plus-lg" />New Division</button>
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
              { key: 'sport', label: 'Sport', render: (r) => <SportBadge sport={sportOf.season(r.season_id)} /> },
              { key: 'season', label: 'Season', render: (r) => seasonName(r.season_id) },
              { key: 'max_teams', label: 'Max Teams' },
              { key: 'status', label: 'Status', render: (r) => <Badge status={r.status} /> },
            ]}
            rows={visibleDivisions}
            actions={(row) => [
              ...(can(role, 'division.manage') ? [{ label: 'Edit', icon: 'bi-pencil', onClick: () => openEdit(row) }] : []),
              ...(can(role, 'division.manage') ? [{ label: 'Archive', icon: 'bi-archive', onClick: () => { if (confirm(`Archive "${row.name}"? You can restore it later from the Archive page.`)) deleteMut.mutate(row.id) } }] : []),
            ]}
            emptyLabel="No divisions yet."
          />
        </>
      )}

      {modal && (
        <Modal
          title={modal === 'create' ? 'New division' : `Edit ${modal.name}`}
          onClose={() => setModal(null)}
          footer={<>
            <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
            <button className="btn btn-primary" onClick={handleSave}><i className="bi bi-check-lg" />Save</button>
          </>}
        >
          <ErrorBanner error={error} />
          {modal === 'create' && (
            <Field label="Season">
              <select className="input" value={form.season_id} onChange={(e) => setForm({ ...form, season_id: e.target.value })}>
                {seasons?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </Field>
          )}
          <Field label="Name">
            <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </Field>
          <Field label="Max teams">
            <input type="number" min={2} max={64} className="input" value={form.max_teams} onChange={(e) => setForm({ ...form, max_teams: Number(e.target.value) })} />
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
