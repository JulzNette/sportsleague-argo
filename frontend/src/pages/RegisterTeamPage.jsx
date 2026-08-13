import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { endpoints } from '../lib/api'
import { buildSportMaps } from '../lib/sports'
import { SportBadge } from '../components/SportControls'
import PageHead from '../components/PageHead'
import ErrorBanner from '../components/ErrorBanner'

const STEPS = ['Team & division', 'Players', 'Documents', 'Review & submit']

const EMPTY_PLAYER = { full_name: '', jersey_number: '', position: '', date_of_birth: '', contact_phone: '' }
const EMPTY_DOC = { player_full_name: '', document_type: '', file_name: '', notes: '' }

export default function RegisterTeamPage() {
  const { data: leagues = [] } = useQuery({ queryKey: ['leagues'], queryFn: () => endpoints.leagues.list().then((r) => r.data) })
  const { data: seasons = [] } = useQuery({ queryKey: ['seasons'], queryFn: () => endpoints.seasons.list().then((r) => r.data) })
  const { data: divisions = [] } = useQuery({ queryKey: ['divisions'], queryFn: () => endpoints.divisions.list().then((r) => r.data) })
  const { sportOf } = buildSportMaps({ leagues, seasons, divisions })

  const [step, setStep] = useState(0)
  const [form, setForm] = useState({
    division_id: '', team_name: '', coach_name: '', contact_email: '', contact_phone: '', notes: '',
    players: [{ ...EMPTY_PLAYER }],
    documents: [],
  })
  const [error, setError] = useState(null)
  const [submitted, setSubmitted] = useState(null)

  const submitMut = useMutation({
    mutationFn: (data) => endpoints.registrations.create(data),
    onSuccess: (res) => setSubmitted(res.data),
    onError: setError,
  })

  const divisionPath = (id) => {
    const div = divisions.find((d) => d.id === id)
    if (!div) return '—'
    const season = seasons.find((s) => s.id === div.season_id)
    const league = leagues.find((l) => l.id === season?.league_id)
    return [league?.name, season?.name, div.name].filter(Boolean).join(' / ')
  }

  function update(field, value) { setForm((f) => ({ ...f, [field]: value })) }
  function updatePlayer(i, field, value) {
    setForm((f) => ({ ...f, players: f.players.map((p, idx) => (idx === i ? { ...p, [field]: value } : p)) }))
  }
  function updateDoc(i, field, value) {
    setForm((f) => ({ ...f, documents: f.documents.map((d, idx) => (idx === i ? { ...d, [field]: value } : d)) }))
  }

  function validate() {
    if (step === 0) {
      if (!form.division_id) return 'Choose the division you want to join.'
      if (!form.team_name.trim()) return 'Enter a team name.'
    }
    if (step === 1) {
      const filled = form.players.filter((p) => p.full_name.trim())
      if (filled.length === 0) return 'Add at least one player to the roster.'
      if (filled.some((p) => !p.jersey_number.trim())) return 'Every player needs a jersey number.'
      if (new Set(filled.map((p) => p.jersey_number.trim())).size !== filled.length) return 'Jersey numbers must be unique.'
    }
    return null
  }

  function next() {
    const problem = validate()
    if (problem) { setError({ message: problem }); return }
    setError(null)
    setStep((s) => Math.min(s + 1, STEPS.length - 1))
  }

  function cleanPlayers() {
    return form.players
      .filter((p) => p.full_name.trim())
      .map((p) => ({
        full_name: p.full_name.trim(),
        jersey_number: p.jersey_number.trim(),
        position: p.position?.trim() || null,
        date_of_birth: p.date_of_birth || null,
        contact_phone: p.contact_phone?.trim() || null,
      }))
  }

  function cleanDocs() {
    return form.documents
      .filter((d) => d.document_type.trim())
      .map((d) => ({
        player_full_name: d.player_full_name || null,
        document_type: d.document_type.trim(),
        file_name: d.file_name?.trim() || null,
        notes: d.notes?.trim() || null,
      }))
  }

  function handleSubmit() {
    setError(null)
    const players = cleanPlayers()
    if (players.length === 0) { setError({ message: 'Add at least one player to the roster.' }); return }
    submitMut.mutate({
      division_id: form.division_id,
      team_name: form.team_name.trim(),
      coach_name: form.coach_name?.trim() || null,
      contact_email: form.contact_email?.trim() || null,
      contact_phone: form.contact_phone?.trim() || null,
      notes: form.notes?.trim() || null,
      players,
      documents: cleanDocs(),
    })
  }

  function reset() {
    setForm({ division_id: '', team_name: '', coach_name: '', contact_email: '', contact_phone: '', notes: '', players: [{ ...EMPTY_PLAYER }], documents: [] })
    setSubmitted(null)
    setError(null)
    setStep(0)
  }

  if (submitted) {
    return (
      <div>
        <PageHead title="Register a team" subtitle="League registration workflow." />
        <div className="card max-w-xl p-8 text-center">
          <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-3">
            <i className="bi bi-check-lg text-2xl" />
          </div>
          <h2 className="font-semibold text-gray-900 text-lg">{submitted.team_name} submitted</h2>
          <p className="text-sm text-gray-500 mt-1">
            Registration for <b>{divisionPath(submitted.division_id)}</b> is <b>Pending</b> review
            by the league administrator. You can track it on the Registrations page.
          </p>
          <div className="flex gap-2 justify-center mt-5">
            <Link to="/registrations" className="btn btn-primary">View registrations</Link>
            <button className="btn btn-secondary" onClick={reset}>Register another team</button>
          </div>
        </div>
      </div>
    )
  }

  if (divisions.length === 0) {
    return (
      <div>
        <PageHead title="Register a team" subtitle="League registration workflow." />
        <div className="card p-10 text-center text-gray-400">
          <i className="bi bi-inbox text-2xl" />
          <p className="mt-2 text-sm">No divisions are open for registration yet.</p>
          <Link to="/" className="btn btn-secondary mt-4">Back to dashboard</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-3xl">
      <PageHead title="Register a team" subtitle="Apply to join a division — approval auto-creates your team and roster." />

      <ol className="flex items-center gap-0 mb-5">
        {STEPS.map((label, i) => (
          <li key={label} className="flex items-center flex-1 last:flex-none">
            <button
              type="button"
              onClick={() => i < step && setStep(i)}
              className={`flex items-center gap-1.5 text-xs font-medium ${i < step ? 'text-blue-600' : i === step ? 'text-gray-900' : 'text-gray-400'}`}
            >
              <span className={`w-5 h-5 rounded-full inline-flex items-center justify-center text-[10px] ${i <= step ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}`}>
                {i < step ? <i className="bi bi-check" /> : i + 1}
              </span>
              {label}
            </button>
            {i < STEPS.length - 1 && <span className="flex-1 h-px bg-gray-200 mx-2" />}
          </li>
        ))}
      </ol>

      <ErrorBanner error={error} />

      {step === 0 && (
        <div className="card p-5">
          <h3 className="font-semibold text-gray-900 mb-3">Team &amp; division</h3>
          <div className="mb-3">
            <label className="label">Division</label>
            <select className="input" value={form.division_id} onChange={(e) => update('division_id', e.target.value)}>
              <option value="">Select a division...</option>
              {leagues.map((league) => (
                <optgroup key={league.id} label={league.name}>
                  {seasons.filter((s) => s.league_id === league.id).map((season) =>
                    divisions.filter((d) => d.season_id === season.id).map((div) => (
                      <option key={div.id} value={div.id}>{season.name} • {div.name}</option>
                    ))
                  )}
                </optgroup>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="mb-3">
              <label className="label">Team name</label>
              <input className="input" value={form.team_name} onChange={(e) => update('team_name', e.target.value)} />
            </div>
            <div className="mb-3">
              <label className="label">Coach name</label>
              <input className="input" value={form.coach_name} onChange={(e) => update('coach_name', e.target.value)} />
            </div>
            <div className="mb-3">
              <label className="label">Contact email</label>
              <input type="email" className="input" value={form.contact_email} onChange={(e) => update('contact_email', e.target.value)} />
            </div>
            <div className="mb-3">
              <label className="label">Contact phone</label>
              <input className="input" value={form.contact_phone} onChange={(e) => update('contact_phone', e.target.value)} />
            </div>
          </div>
          <div className="mb-1">
            <label className="label">Notes</label>
            <textarea className="input" rows={3} value={form.notes} onChange={(e) => update('notes', e.target.value)} placeholder="Anything the league should know (optional)" />
          </div>
        </div>
      )}

      {step === 1 && (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900">Players</h3>
            <button className="btn btn-secondary" onClick={() => setForm((f) => ({ ...f, players: [...f.players, { ...EMPTY_PLAYER }] }))}>
              <i className="bi bi-plus-lg" />Add player
            </button>
          </div>
          {form.players.map((p, i) => (
            <div key={i} className="border border-gray-200 rounded-lg p-3.5 mb-3">
              <div className="flex items-center justify-between mb-2.5">
                <span className="text-sm font-semibold text-gray-700">Player {i + 1}</span>
                {form.players.length > 1 && (
                  <button className="text-gray-400 hover:text-rose-600" onClick={() => setForm((f) => ({ ...f, players: f.players.filter((_, idx) => idx !== i) }))}>
                    <i className="bi bi-trash" />
                  </button>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <label className="block"><span className="label">Full name</span>
                  <input className="input" value={p.full_name} onChange={(e) => updatePlayer(i, 'full_name', e.target.value)} />
                </label>
                <label className="block"><span className="label">Jersey #</span>
                  <input className="input" value={p.jersey_number} onChange={(e) => updatePlayer(i, 'jersey_number', e.target.value)} />
                </label>
                <label className="block"><span className="label">Position</span>
                  <input className="input" value={p.position} onChange={(e) => updatePlayer(i, 'position', e.target.value)} />
                </label>
                <label className="block"><span className="label">Birth date</span>
                  <input type="date" className="input" value={p.date_of_birth} onChange={(e) => updatePlayer(i, 'date_of_birth', e.target.value)} />
                </label>
                <label className="block"><span className="label">Phone</span>
                  <input className="input" value={p.contact_phone} onChange={(e) => updatePlayer(i, 'contact_phone', e.target.value)} />
                </label>
              </div>
            </div>
          ))}
        </div>
      )}

      {step === 2 && (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900">Documents</h3>
            <button className="btn btn-secondary" onClick={() => setForm((f) => ({ ...f, documents: [...f.documents, { ...EMPTY_DOC }] }))}>
              <i className="bi bi-plus-lg" />Add document
            </button>
          </div>
          <p className="text-xs text-gray-500 mb-3">Optional — list requirements like birth certificates or waivers. No files are uploaded yet.</p>
          {form.documents.length === 0 && (
            <div className="border border-dashed border-gray-200 rounded-lg p-6 text-center text-sm text-gray-400">No documents listed.</div>
          )}
          {form.documents.map((d, i) => (
            <div key={i} className="border border-gray-200 rounded-lg p-3.5 mb-3">
              <div className="flex items-center justify-between mb-2.5">
                <span className="text-sm font-semibold text-gray-700">Document {i + 1}</span>
                <button className="text-gray-400 hover:text-rose-600" onClick={() => setForm((f) => ({ ...f, documents: f.documents.filter((_, idx) => idx !== i) }))}>
                  <i className="bi bi-trash" />
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <label className="block"><span className="label">Applies to</span>
                  <select className="input" value={d.player_full_name} onChange={(e) => updateDoc(i, 'player_full_name', e.target.value)}>
                    <option value="">Whole team</option>
                    {cleanPlayers().map((p) => <option key={p.jersey_number} value={p.full_name}>{p.full_name}</option>)}
                  </select>
                </label>
                <label className="block"><span className="label">Document type</span>
                  <input className="input" value={d.document_type} onChange={(e) => updateDoc(i, 'document_type', e.target.value)} placeholder="e.g. Birth certificate" />
                </label>
                <label className="block"><span className="label">File name</span>
                  <input className="input" value={d.file_name} onChange={(e) => updateDoc(i, 'file_name', e.target.value)} placeholder="e.g. jules-birth.pdf" />
                </label>
              </div>
              <label className="block mt-3"><span className="label">Notes</span>
                <input className="input" value={d.notes} onChange={(e) => updateDoc(i, 'notes', e.target.value)} />
              </label>
            </div>
          ))}
        </div>
      )}

      {step === 3 && (
        <div className="card p-5">
          <h3 className="font-semibold text-gray-900 mb-3">Review &amp; submit</h3>
          <dl className="text-sm space-y-2">
            <div className="flex justify-between gap-4"><dt className="text-gray-500">Division</dt><dd className="font-medium text-right">{divisionPath(form.division_id)}</dd></div>
            <div className="flex justify-between gap-4"><dt className="text-gray-500">Team</dt><dd className="font-medium text-right">{form.team_name || '—'}</dd></div>
            <div className="flex justify-between gap-4"><dt className="text-gray-500">Coach</dt><dd className="font-medium text-right">{form.coach_name || '—'}</dd></div>
            <div className="flex justify-between gap-4"><dt className="text-gray-500">Contact</dt><dd className="font-medium text-right">{[form.contact_email, form.contact_phone].filter(Boolean).join(' • ') || '—'}</dd></div>
          </dl>
          <div className="mt-4">
            <span className="text-sm font-medium text-gray-700">Roster ({cleanPlayers().length})</span>
            <div className="border border-gray-200 rounded-lg overflow-hidden mt-1.5">
              <table className="w-full text-sm">
                <thead><tr className="bg-gray-50 text-left text-xs uppercase text-gray-500"><th className="px-3 py-2">Name</th><th className="px-3 py-2">Jersey</th><th className="px-3 py-2">Position</th><th className="px-3 py-2">Born</th></tr></thead>
                <tbody>
                  {cleanPlayers().map((p) => (
                    <tr key={p.jersey_number} className="border-t border-gray-100">
                      <td className="px-3 py-2">{p.full_name}</td><td className="px-3 py-2">{p.jersey_number}</td><td className="px-3 py-2">{p.position || '—'}</td><td className="px-3 py-2">{p.date_of_birth || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          {cleanDocs().length > 0 && (
            <div className="mt-4">
              <span className="text-sm font-medium text-gray-700">Documents ({cleanDocs().length})</span>
              <ul className="mt-1.5 space-y-1 text-sm text-gray-600">
                {cleanDocs().map((d, i) => (
                  <li key={i} className="flex items-center gap-2"><i className="bi bi-file-earmark-text text-gray-400" />{d.document_type}{d.player_full_name ? ` — ${d.player_full_name}` : ''}{d.file_name ? ` (${d.file_name})` : ''}</li>
                ))}
              </ul>
            </div>
          )}
          {form.notes && <p className="mt-4 text-sm text-gray-600 border-t border-gray-100 pt-3"><b>Notes:</b> {form.notes}</p>}
        </div>
      )}

      <div className="flex justify-between mt-5">
        <button className="btn btn-secondary" disabled={step === 0} onClick={() => { setError(null); setStep((s) => Math.max(s - 1, 0)) }}>
          <i className="bi bi-arrow-left" />Back
        </button>
        {step < STEPS.length - 1 ? (
          <button className="btn btn-primary" onClick={next}>Next<i className="bi bi-arrow-right" /></button>
        ) : (
          <button className="btn btn-primary" disabled={submitMut.isPending} onClick={handleSubmit}>
            {submitMut.isPending ? 'Submitting...' : <><i className="bi bi-send" />Submit registration</>}
          </button>
        )}
      </div>

      {submitted && (
        <div className="mt-6 rounded-md bg-emerald-50 border border-emerald-200 px-3.5 py-2.5 text-sm text-emerald-700 flex items-center gap-2">
          <i className="bi bi-check-circle" />Submitted — {divisionPath(submitted.division_id)} • <SportBadge sport={sportOf.division(submitted.division_id)} />
        </div>
      )}
    </div>
  )
}
