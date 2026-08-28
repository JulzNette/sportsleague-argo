import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { endpoints } from '../lib/api'
import { can } from '../lib/permissions'
import { MATCH_STATUS_TRANSITIONS } from '../lib/statusMachines'
import { useAuthStore } from '../store/authStore'
import PageHead from '../components/PageHead'
import DataTable from '../components/DataTable'
import Modal from '../components/Modal'
import Field from '../components/Field'
import Badge from '../components/Badge'
import ErrorBanner from '../components/ErrorBanner'
import { SportBadge, SportFilter } from '../components/SportControls'
import { buildSportMaps } from '../lib/sports'

const EMPTY = {
  season_id: '', division_id: '', home_team_id: '', away_team_id: '', referee_id: '',
  scheduled_date: '', scheduled_time: '', venue: '', round_number: 1, match_type: 'Regular',
}
const EMPTY_RESULT = { home_score: 0, away_score: 0, result_type: 'Normal', forfeit_winner_team_id: '', notes: '' }

export default function MatchesPage() {
  const role = useAuthStore((s) => s.role)
  const qc = useQueryClient()
  const { data: matches, isLoading } = useQuery({ queryKey: ['matches'], queryFn: () => endpoints.matches.list().then((r) => r.data) })
  const { data: seasons } = useQuery({ queryKey: ['seasons'], queryFn: () => endpoints.seasons.list().then((r) => r.data) })
  const { data: divisions } = useQuery({ queryKey: ['divisions'], queryFn: () => endpoints.divisions.list().then((r) => r.data) })
  const { data: teams } = useQuery({ queryKey: ['teams'], queryFn: () => endpoints.teams.list().then((r) => r.data) })
  const { data: leagues } = useQuery({ queryKey: ['leagues'], queryFn: () => endpoints.leagues.list().then((r) => r.data) })
  const { data: referees } = useQuery({ queryKey: ['referees'], queryFn: () => endpoints.referees.list().then((r) => r.data), enabled: can(role, 'referee.manage') })
  const { data: players } = useQuery({ queryKey: ['players'], queryFn: () => endpoints.players.list().then((r) => r.data) })

  const { sportOf, sports } = buildSportMaps({ leagues, seasons, divisions, teams })

  const [modal, setModal] = useState(null) // 'create' | { type: 'status'|'result'|'stats', match }
  const [form, setForm] = useState(EMPTY)
  const [resultForm, setResultForm] = useState(EMPTY_RESULT)
  const [statusChoice, setStatusChoice] = useState('')
  const [error, setError] = useState(null)
  const [sportFilter, setSportFilter] = useState('')
  const [statsForm, setStatsForm] = useState({})

  const { data: matchStats } = useQuery({
    queryKey: ['matchStats', modal?.match?.id],
    queryFn: () => endpoints.playerStats.get(modal.match.id).then((r) => r.data),
    enabled: modal?.type === 'stats',
  })
  const canEnterStats = can(role, 'player_stat.enter')
  const roster = players?.filter((p) => p.team_id === modal?.match?.home_team_id || p.team_id === modal?.match?.away_team_id) || []
  const statsTeam = (teamId) => roster.filter((p) => p.team_id === teamId)

  useEffect(() => {
    if (modal?.type !== 'stats') return
    const base = {}
    roster.forEach((p) => { base[p.id] = { points: 0, assists: 0, fouls: 0, rebounds: 0, steals: 0 } })
    ;(matchStats || []).forEach((s) => { base[s.player_id] = { points: s.points, assists: s.assists, fouls: s.fouls, rebounds: s.rebounds, steals: s.steals } })
    setStatsForm(base)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modal?.type, matchStats])

  const teamName = (id) => teams?.find((t) => t.id === id)?.name || '—'
  const refereeName = (id) => referees?.find((r) => r.id === id)?.full_name || 'Unassigned'

  const visibleMatches = sportFilter ? matches?.filter((m) => sportOf.division(m.division_id) === sportFilter) : matches

  const resultSummary = (m) => {
    const res = m.result
    if (!res) return null
    if (res.result_type === 'Forfeit') return { text: `Forfeit — ${teamName(res.forfeit_winner_team_id)}`, winnerId: res.forfeit_winner_team_id }
    if (res.result_type === 'Draw') return { text: `Draw ${res.home_score} – ${res.away_score}`, winnerId: null }
    const winnerId = res.home_score > res.away_score ? m.home_team_id : res.away_score > res.home_score ? m.away_team_id : null
    return { text: `${res.home_score} – ${res.away_score}`, winnerId }
  }

  const invalidate = () => qc.invalidateQueries({ queryKey: ['matches'] })

  const createMut = useMutation({ mutationFn: (data) => endpoints.matches.create(data), onSuccess: () => { invalidate(); setModal(null) }, onError: setError })
  const statusMut = useMutation({ mutationFn: ({ id, status }) => endpoints.matches.setStatus(id, status), onSuccess: () => { invalidate(); setModal(null) }, onError: setError })
  const assignMut = useMutation({ mutationFn: ({ id, refereeId }) => endpoints.matches.assignReferee(id, refereeId), onSuccess: invalidate, onError: setError })
  const resultMut = useMutation({ mutationFn: ({ id, data }) => endpoints.results.submit(id, data), onSuccess: () => { invalidate(); setModal(null) }, onError: setError })
  const statsMut = useMutation({
    mutationFn: ({ id, data }) => endpoints.playerStats.submit(id, data),
    onSuccess: () => { invalidate(); qc.invalidateQueries({ queryKey: ['matchStats'] }); qc.invalidateQueries({ queryKey: ['playerStats'] }); setModal(null) },
    onError: setError,
  })

  function openCreate() {
    const firstSeasonWithDivisions = seasons?.find((s) => divisions?.some((d) => d.season_id === s.id))
    setForm({ ...EMPTY, season_id: firstSeasonWithDivisions?.id || seasons?.[0]?.id || '' })
    setError(null)
    setModal('create')
  }
  function openStatus(match) { setStatusChoice(''); setError(null); setModal({ type: 'status', match }) }
  function openResult(match) { setResultForm(EMPTY_RESULT); setError(null); setModal({ type: 'result', match }) }
  function openStats(match) { setStatsForm({}); setError(null); setModal({ type: 'stats', match }) }

  const divisionsForSeason = divisions?.filter((d) => d.season_id === form.season_id) || []
  const teamsForDivision = teams?.filter((t) => t.division_id === form.division_id) || []

  return (
    <div>
      <PageHead
        title="Matches"
        subtitle="Scheduling, referee assignment, and results."
        actions={can(role, 'match.schedule') && seasons?.length > 0 && (
          <button className="btn btn-primary" onClick={openCreate}><i className="bi bi-plus-lg" />Schedule Match</button>
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
              { key: 'matchup', label: 'Matchup', render: (r) => {
                const s = resultSummary(r)
                const home = teamName(r.home_team_id)
                const away = teamName(r.away_team_id)
                if (s?.winnerId === r.home_team_id) return <span className="font-semibold text-gray-900"><b className="text-emerald-700">{home}</b> vs {away}</span>
                if (s?.winnerId === r.away_team_id) return <span className="font-semibold text-gray-900">{home} vs <b className="text-emerald-700">{away}</b></span>
                return <span className="font-semibold text-gray-900">{home} vs {away}</span>
              } },
              { key: 'result', label: 'Result', render: (r) => {
                const s = resultSummary(r)
                return s ? <span className="text-gray-700">{s.text}</span> : <span className="text-gray-400">—</span>
              } },
              { key: 'sport', label: 'Sport', render: (r) => <SportBadge sport={sportOf.division(r.division_id)} /> },
              { key: 'when', label: 'When', render: (r) => `${r.scheduled_date} ${r.scheduled_time}` },
              { key: 'venue', label: 'Venue' },
              { key: 'round_number', label: 'Round' },
              { key: 'match_type', label: 'Type' },
              { key: 'referee_id', label: 'Referee', render: (r) => refereeName(r.referee_id) },
              { key: 'status', label: 'Status', render: (r) => <Badge status={r.status} /> },
            ]}
            rows={visibleMatches}
            actions={(row) => [
              ...(can(role, 'match.update') ? [{ label: 'Change status', icon: 'bi-arrow-repeat', onClick: () => openStatus(row) }] : []),
              ...(can(role, 'result.submit') && !row.result && ['In Progress', 'Scheduled'].includes(row.status) ? [{ label: 'Submit result', icon: 'bi-clipboard-check', onClick: () => openResult(row) }] : []),
              ...(can(role, 'player_stat.view') && row.result ? [{ label: 'Player stats', icon: 'bi-person-lines-fill', onClick: () => openStats(row) }] : []),
            ]}
            emptyLabel="No matches scheduled yet."
          />
        </>
      )}

      {modal === 'create' && (
        <Modal
          title="Schedule match"
          onClose={() => setModal(null)}
          footer={<>
            <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
            <button className="btn btn-primary" onClick={() => createMut.mutate({ ...form, referee_id: form.referee_id || null })}><i className="bi bi-check-lg" />Schedule</button>
          </>}
        >
          <ErrorBanner error={error} />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Field label="Season">
              <select className="input" value={form.season_id} onChange={(e) => setForm({ ...form, season_id: e.target.value, division_id: '', home_team_id: '', away_team_id: '' })}>
                {seasons?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </Field>
            <Field label="Division">
              <select className="input" value={form.division_id} onChange={(e) => setForm({ ...form, division_id: e.target.value, home_team_id: '', away_team_id: '' })}>
                <option value="">Select...</option>
                {divisionsForSeason.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </Field>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Field label="Home team">
              <select className="input" value={form.home_team_id} onChange={(e) => setForm({ ...form, home_team_id: e.target.value })}>
                <option value="">Select...</option>
                {teamsForDivision.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
            </Field>
            <Field label="Away team">
              <select className="input" value={form.away_team_id} onChange={(e) => setForm({ ...form, away_team_id: e.target.value })}>
                <option value="">Select...</option>
                {teamsForDivision.filter((t) => t.id !== form.home_team_id).map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
            </Field>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Field label="Date"><input type="date" className="input" value={form.scheduled_date} onChange={(e) => setForm({ ...form, scheduled_date: e.target.value })} /></Field>
            <Field label="Time"><input type="time" className="input" value={form.scheduled_time} onChange={(e) => setForm({ ...form, scheduled_time: e.target.value })} /></Field>
          </div>
          <Field label="Venue"><input className="input" value={form.venue} onChange={(e) => setForm({ ...form, venue: e.target.value })} /></Field>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Field label="Round #"><input type="number" min={0} className="input" value={form.round_number} onChange={(e) => setForm({ ...form, round_number: Number(e.target.value) })} /></Field>
            <Field label="Match type">
              <select className="input" value={form.match_type} onChange={(e) => setForm({ ...form, match_type: e.target.value })}>
                <option>Regular</option><option>Playoff</option>
              </select>
            </Field>
          </div>
          {can(role, 'assignment.create') && (
            <Field label="Referee (optional)">
              <select className="input" value={form.referee_id} onChange={(e) => setForm({ ...form, referee_id: e.target.value })}>
                <option value="">Unassigned</option>
                {referees?.map((r) => <option key={r.id} value={r.id}>{r.full_name}</option>)}
              </select>
            </Field>
          )}
        </Modal>
      )}

      {modal?.type === 'status' && (
        <Modal
          title={`Change status — ${teamName(modal.match.home_team_id)} vs ${teamName(modal.match.away_team_id)}`}
          subtitle={`Currently: ${modal.match.status}`}
          onClose={() => setModal(null)}
          footer={<>
            <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
            <button
              className="btn btn-primary"
              disabled={!statusChoice}
              onClick={() => statusMut.mutate({ id: modal.match.id, status: statusChoice })}
            >
              <i className="bi bi-check-lg" />Apply
            </button>
          </>}
        >
          <ErrorBanner error={error} />
          <div className="flex flex-col gap-2">
            {(MATCH_STATUS_TRANSITIONS[modal.match.status] || []).map((s) => (
              <label key={s} className="flex items-center gap-2 text-sm border border-gray-200 rounded-md px-3 py-2 cursor-pointer hover:bg-gray-50">
                <input type="radio" name="status" checked={statusChoice === s} onChange={() => setStatusChoice(s)} />
                {s}
              </label>
            ))}
            {(MATCH_STATUS_TRANSITIONS[modal.match.status] || []).length === 0 && (
              <p className="text-sm text-gray-500">This match is in a final state — no further transitions allowed.</p>
            )}
          </div>
        </Modal>
      )}

      {modal?.type === 'result' && (
        <Modal
          title={`Submit result — ${teamName(modal.match.home_team_id)} vs ${teamName(modal.match.away_team_id)}`}
          onClose={() => setModal(null)}
          footer={<>
            <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
            <button
              className="btn btn-primary"
              onClick={() => resultMut.mutate({
                id: modal.match.id,
                data: { ...resultForm, forfeit_winner_team_id: resultForm.forfeit_winner_team_id || null },
              })}
            >
              <i className="bi bi-check-lg" />Submit
            </button>
          </>}
        >
          <ErrorBanner error={error} />
          <Field label="Result type">
            <select className="input" value={resultForm.result_type} onChange={(e) => setResultForm({ ...resultForm, result_type: e.target.value })}>
              <option>Normal</option><option>Draw</option><option>Forfeit</option>
            </select>
          </Field>
          {resultForm.result_type !== 'Forfeit' ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Field label={`${teamName(modal.match.home_team_id)} score`}>
                <input type="number" min={0} className="input" value={resultForm.home_score} onChange={(e) => setResultForm({ ...resultForm, home_score: Number(e.target.value) })} />
              </Field>
              <Field label={`${teamName(modal.match.away_team_id)} score`}>
                <input type="number" min={0} className="input" value={resultForm.away_score} onChange={(e) => setResultForm({ ...resultForm, away_score: Number(e.target.value) })} />
              </Field>
            </div>
          ) : (
            <Field label="Forfeit winner">
              <select className="input" value={resultForm.forfeit_winner_team_id} onChange={(e) => setResultForm({ ...resultForm, forfeit_winner_team_id: e.target.value })}>
                <option value="">Select winner...</option>
                <option value={modal.match.home_team_id}>{teamName(modal.match.home_team_id)}</option>
                <option value={modal.match.away_team_id}>{teamName(modal.match.away_team_id)}</option>
              </select>
            </Field>
          )}
          <Field label="Notes"><textarea className="input" rows={2} value={resultForm.notes} onChange={(e) => setResultForm({ ...resultForm, notes: e.target.value })} /></Field>
        </Modal>
      )}

      {modal?.type === 'stats' && (
        <Modal
          title={`Player stats — ${teamName(modal.match.home_team_id)} vs ${teamName(modal.match.away_team_id)}`}
          subtitle={`Result: ${resultSummary(modal.match)?.text}`}
          onClose={() => setModal(null)}
          footer={<>
            <button className="btn btn-secondary" onClick={() => setModal(null)}>Cancel</button>
            {canEnterStats && (
              <button
                className="btn btn-primary"
                onClick={() => statsMut.mutate({
                  id: modal.match.id,
                  data: { lines: roster.map((p) => ({ player_id: p.id, ...statsForm[p.id] })) },
                })}
              >
                <i className="bi bi-check-lg" />Save stats
              </button>
            )}
          </>}
        >
          <ErrorBanner error={error} />
          {canEnterStats && <p className="text-xs text-gray-500 mb-3">Values are saved per player per match. Re-saving overwrites.</p>}
          {[modal.match.home_team_id, modal.match.away_team_id].map((teamId) => (
            <div key={teamId} className="mb-4">
              <h3 className="text-sm font-semibold text-gray-900 mb-2">{teamName(teamId)}</h3>
              {statsTeam(teamId).length === 0 && <p className="text-xs text-gray-400">No players on roster yet.</p>}
              <div className="flex flex-col gap-2">
                {statsTeam(teamId).map((p) => {
                  const v = statsForm[p.id] || { points: 0, assists: 0, fouls: 0, rebounds: 0, steals: 0 }
                  const setStat = (k) => (e) => setStatsForm({ ...statsForm, [p.id]: { ...v, [k]: Math.max(0, Number(e.target.value)) } })
                  return (
                    <div key={p.id} className="border border-gray-200 rounded-md px-3 py-2 grid grid-cols-2 sm:grid-cols-6 gap-2 items-center">
                      <span className="col-span-1 text-sm font-medium text-gray-900 truncate">{p.full_name}</span>
                      {[['points', 'PTS'], ['assists', 'AST'], ['rebounds', 'REB'], ['steals', 'STL'], ['fouls', 'FLS']].map(([k, label]) => (
                        <label key={k} className="flex flex-col">
                          <span className="text-[10px] uppercase text-gray-400">{label}</span>
                          <input
                            type="number"
                            min={0}
                            className="input input-sm"
                            disabled={!canEnterStats}
                            value={v[k]}
                            onChange={setStat(k)}
                          />
                        </label>
                      ))}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </Modal>
      )}
    </div>
  )
}
