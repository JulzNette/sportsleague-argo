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
import { SportBadge, SportFilter } from '../components/SportControls'
import { buildSportMaps, SPORTS, BASKETBALL_POSITIONS } from '../lib/sports'

const EMPTY = { team_id: '', full_name: '', date_of_birth: '', position: '', jersey_number: '', contact_phone: '', status: 'Active' }

const SPORT_ORDER = new Map(SPORTS.map((s, i) => [s, i]))

export default function PlayersPage() {
  const role = useAuthStore((s) => s.role)
  const qc = useQueryClient()
  const { data: players, isLoading } = useQuery({ queryKey: ['players'], queryFn: () => endpoints.players.list().then((r) => r.data) })
  const { data: teams } = useQuery({ queryKey: ['teams'], queryFn: () => endpoints.teams.list().then((r) => r.data) })
  const { data: divisions } = useQuery({ queryKey: ['divisions'], queryFn: () => endpoints.divisions.list().then((r) => r.data) })
  const { data: seasons } = useQuery({ queryKey: ['seasons'], queryFn: () => endpoints.seasons.list().then((r) => r.data) })
  const { data: leagues } = useQuery({ queryKey: ['leagues'], queryFn: () => endpoints.leagues.list().then((r) => r.data) })

  const { sportOf, sports } = buildSportMaps({ leagues, seasons, divisions, teams })

  const [modal, setModal] = useState(null)
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState(null)
  const [loginFor, setLoginFor] = useState(null)
  const [loginForm, setLoginForm] = useState({ email: '', password: '' })
  const [sportFilter, setSportFilter] = useState('Basketball')

  const teamName = (id) => teams?.find((t) => t.id === id)?.name || 'Unassigned'

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
  const accountMut = useMutation({
    mutationFn: ({ id, data }) => endpoints.players.createAccount(id, data),
    onSuccess: () => { setLoginFor(null); setLoginForm({ email: '', password: '' }); setError(null) },
    onError: setError,
  })

  function openLogin(p) { setLoginFor(p); setLoginForm({ email: '', password: '' }); setError(null) }

  function openCreate() { setForm({ ...EMPTY, team_id: teams?.[0]?.id || '' }); setError(null); setModal('create') }
  function openEdit(p) { setForm(p); setError(null); setModal(p) }
  function handleSave() {
    if (modal === 'create') createMut.mutate(form)
    else updateMut.mutate({ id: modal.id, data: form })
  }

  // Players grouped by sport, then by team - so it's obvious who belongs where.
  const groups = useMemo(() => {
    const bySport = {}
    for (const p of players || []) {
      if (sportFilter && sportOf.team(p.team_id) !== sportFilter) continue
      const sport = sportOf.team(p.team_id)
      const tid = p.team_id || 'unassigned'
      if (!bySport[sport]) bySport[sport] = {}
      if (!bySport[sport][tid]) bySport[sport][tid] = []
      bySport[sport][tid].push(p)
    }
    return Object.entries(bySport)
      .sort(([a], [b]) => (SPORT_ORDER.get(a) ?? 999) - (SPORT_ORDER.get(b) ?? 999) || a.localeCompare(b))
      .map(([sport, teamsMap]) => ({
        sport,
        count: Object.values(teamsMap).reduce((n, list) => n + list.length, 0),
        teams: Object.entries(teamsMap)
          .sort(([a], [b]) => teamName(a).localeCompare(teamName(b)))
          .map(([tid, list]) => ({ id: tid, players: list })),
      }))
  }, [players, teams, sportFilter])

  const total = groups.reduce((n, g) => n + g.count, 0)

  return (
    <div>
      <PageHead
        title="Players"
        subtitle="Roster members grouped by sport and team."
        actions={can(role, 'player.create') && teams?.length > 0 && (
          <button className="btn btn-primary" onClick={openCreate}><i className="bi bi-plus-lg" />New Player</button>
        )}
      />

      {sports.length > 0 && (
        <div className="card p-3.5 mb-4 flex gap-3 flex-wrap items-center">
          <label className="text-sm font-medium text-gray-700">Sport</label>
          <SportFilter sports={sports} value={sportFilter} onChange={setSportFilter} />
          <span className="ml-auto text-xs text-gray-500">{total} player{total === 1 ? '' : 's'}</span>
        </div>
      )}

      {isLoading ? (
        <p className="text-sm text-gray-500">Loading...</p>
      ) : groups.length === 0 ? (
        <DataTable rows={[]} emptyLabel="No players yet." />
      ) : (
        <div className="space-y-5">
          {groups.map(({ sport, count, teams: teamGroups }) => (
            <div key={sport} className="card overflow-hidden">
              <div className="flex items-center gap-2.5 px-4 py-3 bg-gray-50 border-b border-gray-200">
                <SportBadge sport={sport} />
                <span className="font-semibold text-sm text-gray-900">{sport}</span>
                <span className="ml-auto text-xs text-gray-500">{count} player{count === 1 ? '' : 's'}</span>
              </div>

              {teamGroups.map((team) => (
                <div key={team.id} className="border-b border-gray-100 last:border-0">
                  <div className="flex items-center gap-2 px-4 py-2 bg-white">
                    <i className="bi bi-people text-gray-400" />
                    <span className="font-semibold text-sm text-gray-700">{teamName(team.id)}</span>
                    <span className="text-xs text-gray-400">{team.players.length}</span>
                  </div>
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 border-y border-gray-200">
                        <th className="text-left font-semibold text-gray-500 uppercase text-xs tracking-wide px-4 py-2">Name</th>
                        <th className="text-left font-semibold text-gray-500 uppercase text-xs tracking-wide px-4 py-2">Position</th>
                        <th className="text-left font-semibold text-gray-500 uppercase text-xs tracking-wide px-4 py-2">#</th>
                        <th className="text-left font-semibold text-gray-500 uppercase text-xs tracking-wide px-4 py-2">Contact</th>
                        <th className="text-left font-semibold text-gray-500 uppercase text-xs tracking-wide px-4 py-2">Status</th>
                        {(can(role, 'player.update') || can(role, 'player.delete') || can(role, 'player.login')) && <th className="w-1" />}
                      </tr>
                    </thead>
                    <tbody>
                      {team.players.map((p) => (
                        <tr key={p.id} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                          <td className="px-4 py-2.5 font-semibold text-gray-900">{p.full_name}</td>
                          <td className="px-4 py-2.5 text-gray-700">{p.position || '—'}</td>
                          <td className="px-4 py-2.5 text-gray-700">{p.jersey_number || '—'}</td>
                          <td className="px-4 py-2.5 text-gray-500">{p.contact_phone || '—'}</td>
                          <td className="px-4 py-2.5"><Badge status={p.status} /></td>
                          {(can(role, 'player.update') || can(role, 'player.delete') || can(role, 'player.login')) && (
                            <td className="px-4 py-2.5 text-right whitespace-nowrap">
                              <div className="flex justify-end gap-1">
                                {p.login_allowed && (
                                  <button onClick={() => openLogin(p)} title="Create login" className="w-7 h-7 inline-flex items-center justify-center rounded-md border border-gray-200 text-gray-500 hover:bg-gray-100">
                                    <i className="bi bi-box-arrow-in-right" />
                                  </button>
                                )}
                                {can(role, 'player.update') && (
                                  <button onClick={() => openEdit(p)} title="Edit" className="w-7 h-7 inline-flex items-center justify-center rounded-md border border-gray-200 text-gray-500 hover:bg-gray-100">
                                    <i className="bi bi-pencil" />
                                  </button>
                                )}
                                {can(role, 'player.delete') && (
                                  <button onClick={() => { if (confirm(`Remove "${p.full_name}"?`)) deleteMut.mutate(p.id) }} title="Delete" className="w-7 h-7 inline-flex items-center justify-center rounded-md border border-gray-200 text-gray-500 hover:bg-gray-100">
                                    <i className="bi bi-trash" />
                                  </button>
                                )}
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
          ))}
        </div>
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
          <Field label="Team">
            <select className="input" value={form.team_id || ''} onChange={(e) => setForm({ ...form, team_id: e.target.value })}>
              <option value="">Unassigned</option>
              {teams?.map((t) => <option key={t.id} value={t.id}>{t.name} — {sportOf.team(t.id)}</option>)}
            </select>
          </Field>
          <Field label="Full name"><input className="input" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></Field>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Field label="Position">
  <select className="input" value={form.position || ''} onChange={(e) => setForm({ ...form, position: e.target.value })}>
    <option value="">Select...</option>
    {BASKETBALL_POSITIONS.map((p) => <option key={p} value={p}>{p}</option>)}
  </select>
</Field>
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

      {loginFor && (
        <Modal
          title={`Create login for ${loginFor.full_name}`}
          subtitle="This creates a Player account — view-only access to the league."
          onClose={() => setLoginFor(null)}
          footer={<>
            <button className="btn btn-secondary" onClick={() => setLoginFor(null)}>Cancel</button>
            <button className="btn btn-primary" disabled={accountMut.isPending} onClick={() => accountMut.mutate({ id: loginFor.id, data: loginForm })}>
              <i className="bi bi-check-lg" />Create account
            </button>
          </>}
        >
          <ErrorBanner error={error} />
          <Field label="Login email"><input className="input" type="email" value={loginForm.email} onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })} /></Field>
          <Field label="Temporary password">
            <input className="input" type="password" value={loginForm.password} onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })} />
            <p className="text-xs text-gray-400 mt-1">At least 8 characters. Tell the player to change it after logging in.</p>
          </Field>
          <div className="text-xs text-gray-500 bg-gray-50 border border-gray-200 rounded-md px-3 py-2 mt-1">
            The player can sign in and view standings, schedule, and their own stats — they cannot manage anything.
          </div>
        </Modal>
      )}
    </div>
  )
}
