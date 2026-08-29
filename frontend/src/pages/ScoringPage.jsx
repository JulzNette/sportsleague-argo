import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { endpoints } from '../lib/api'
import { useAuthStore } from '../store/authStore'
import PageHead from '../components/PageHead'
import ErrorBanner from '../components/ErrorBanner'

const pad = (n) => String(n).padStart(2, '0')

export default function ScoringPage() {
  const role = useAuthStore((s) => s.role)
  const qc = useQueryClient()

  const { data: matches = [], isLoading } = useQuery({
    queryKey: ['matches'],
    queryFn: () => endpoints.matches.list().then((r) => r.data),
  })
  const { data: teams = [] } = useQuery({ queryKey: ['teams'], queryFn: () => endpoints.teams.list().then((r) => r.data) })
  const { data: players = [] } = useQuery({ queryKey: ['players'], queryFn: () => endpoints.players.list().then((r) => r.data) })
  const { data: publicSettings = {} } = useQuery({ queryKey: ['public-settings'], queryFn: () => endpoints.settings.public().then((r) => r.data) })
  const foulLimit = publicSettings.foul_limit ?? 5

  const [matchId, setMatchId] = useState('')
  const [error, setError] = useState(null)

  const { data: grid = [], refetch: refetchGrid } = useQuery({
    queryKey: ['match-stats', matchId],
    queryFn: () => (matchId ? endpoints.playerStats.get(matchId).then((r) => r.data) : []),
    enabled: !!matchId,
  })

  // Poll-based live updates: refresh the match list (clock/score) and this
  // match's player grid every few seconds so the scoreboard stays current.
  useEffect(() => {
    const t = setInterval(() => {
      qc.refetchQueries({ queryKey: ['matches'] })
      if (matchId) refetchGrid()
    }, 5000)
    return () => clearInterval(t)
  }, [matchId])

  const [period, setPeriod] = useState(1)
  const [minutes, setMinutes] = useState(0)
  const [seconds, setSeconds] = useState(0)
  const [running, setRunning] = useState(false)
  const [editTime, setEditTime] = useState(false)
  const [editText, setEditText] = useState({ period: '1', minutes: '00', seconds: '00' })
  const validMatches = matches.filter((m) => !['Completed', 'Cancelled', 'Forfeited'].includes(m.status))

  const match = matches.find((m) => m.id === matchId)
  const home = teams.find((t) => t.id === (match && match.home_team_id))
  const away = teams.find((t) => t.id === (match && match.away_team_id))
  const scores = match?.result

  function applyClock(m) {
    const r = m?.result
    setPeriod(r?.period ?? 1)
    setMinutes(r?.minutes ?? 0)
    setSeconds(r?.seconds ?? 0)
    setRunning(false)
  }

  useEffect(() => {
    if (!matchId) { setMatchId(validMatches[0]?.id || ''); return }
    applyClock(matches.find((m) => m.id === matchId))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [matchId, matches])

  useEffect(() => {
    if (!running) return
    const t = setInterval(() => {
      setSeconds((s) => {
        if (s > 0) return s - 1
        setMinutes((m) => {
          if (m > 0) return m - 1
          setRunning(false)
          return 0
        })
        return 59
      })
    }, 1000)
    return () => clearInterval(t)
  }, [running])

  const scoreMut = useMutation({
    mutationFn: ({ id, data }) => endpoints.scoring.update(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['matches'] }); setError(null) },
    onError: setError,
  })

  function emit(delta) {
    if (!matchId) return
    scoreMut.mutate({
      id: matchId,
      data: {
        home_delta: delta.home_delta || 0,
        away_delta: delta.away_delta || 0,
        period: delta.period != null ? delta.period : period,
        minutes: delta.minutes != null ? delta.minutes : minutes,
        seconds: delta.seconds != null ? delta.seconds : seconds,
      },
    })
  }

  const undoMut = useMutation({
    mutationFn: ({ id, data }) => endpoints.scoring.undo(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['matches'] }); setError(null) },
    onError: setError,
  })

  function undo(side, points) {
    if (!matchId) return
    undoMut.mutate({ id: matchId, data: { side, points } })
  }

  const liveMut = useMutation({
    mutationFn: (data) => endpoints.playerStats.live(matchId, data),
    onSuccess: () => { refetchGrid(); qc.refetchQueries({ queryKey: ['matches'] }); setError(null) },
    onError: setError,
  })

  function addFoul(player) {
    if (!matchId) return
    liveMut.mutate({ player_id: player.id, points: 0, fouls: 1 })
  }
  function addPlayerPoint(player) {
    if (!matchId) return
    liveMut.mutate({ player_id: player.id, points: 1, fouls: 0 })
  }

  const statByPlayer = Object.fromEntries(grid.map((g) => [g.player_id, g]))

  function toggleClock() {
    setRunning((r) => !r)
    if (matchId && !running) {
      scoreMut.mutate({
        id: matchId,
        data: { home_delta: 0, away_delta: 0, period, minutes, seconds },
      })
    }
  }

  function changePeriod(dir) {
    const next = Math.max(1, period + dir)
    setPeriod(next)
    if (matchId) emit({ period: next })
  }

  function stepMinutes(dir) {
    const next = clamp(minutes + dir, 0, 59)
    setMinutes(next)
    if (dir && matchId) emit({ minutes: next })
  }
  function stepSeconds(dir) {
    const next = dir === 0 ? seconds : (seconds + dir + 60) % 60
    setSeconds(next)
    if (dir && matchId) emit({ seconds: next })
  }
  function clamp(v, min, max) {
    if (Number.isNaN(v)) return min
    return Math.min(max, Math.max(min, v))
  }
  // Editable clock fields: while editing we keep the raw typed string so the
  // user can backspace freely; we only parse/commit when a valid number is entered
  // or when they finish editing.
  function typeField(key, raw) {
    if (!/^\d*$/.test(raw)) return
    setEditText((t) => ({ ...t, [key]: raw }))
    if (raw === '' || Number.isNaN(Number(raw))) return
    if (key === 'period') {
      const next = clamp(Math.floor(Number(raw)), 1, 99)
      setPeriod(next)
      if (matchId) emit({ period: next })
    } else {
      const next = clamp(Math.floor(Number(raw)), 0, 59)
      if (key === 'minutes') { setMinutes(next); if (matchId) emit({ minutes: next }) }
      else { setSeconds(next); if (matchId) emit({ seconds: next }) }
    }
  }

  function commitEdit() {
    const p = clamp(editText.period === '' ? period : Math.floor(Number(editText.period)), 1, 99)
    const m = clamp(editText.minutes === '' ? minutes : Math.floor(Number(editText.minutes)), 0, 59)
    const s = clamp(editText.seconds === '' ? seconds : Math.floor(Number(editText.seconds)), 0, 59)
    setPeriod(p); setMinutes(m); setSeconds(s)
    if (matchId) emit({ period: p, minutes: m, seconds: s })
    setEditTime(false)
  }

  function openEdit() {
    setEditText({ period: String(period), minutes: pad(minutes), seconds: pad(seconds) })
    setEditTime(true)
  }

  const fmt = `${pad(minutes)}:${pad(seconds)}`

  return (
    <div>
      <PageHead title="Scoring" subtitle="Live scoreboard — track the clock and add points per team." />
      <ErrorBanner error={error} />

      <div className="card p-4 mb-4 max-w-xl">
        <label className="block text-sm font-medium text-gray-700 mb-2">Match</label>
        {isLoading ? (
          <p className="text-sm text-gray-500">Loading matches...</p>
        ) : (
          <select className="input" value={matchId} onChange={(e) => setMatchId(e.target.value)}>
            {validMatches.map((m) => (
              <option key={m.id} value={m.id}>
                {teams.find((t) => t.id === m.home_team_id)?.name || '—'} vs{' '}
                {teams.find((t) => t.id === m.away_team_id)?.name || '—'}
              </option>
            ))}
          </select>
        )}
      </div>

      {!match ? (
        <p className="text-sm text-gray-500">No matchable games right now. Schedule a match first.</p>
      ) : (
        <div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Scoreboard */}
          <div className="card p-5">
            <div className="bg-slate-900 rounded-2xl p-5 text-white">
              <div className="flex items-center justify-between mb-3 text-xs font-semibold uppercase tracking-widest">
                <span className="flex-1 text-center">{home?.name || 'Home'}</span>
                {editTime ? (
                  <span
                    className="bg-slate-700 text-blue-300 px-2 py-1 rounded-full flex items-center gap-1 font-mono tabular-nums"
                    onBlur={(e) => { if (!e.currentTarget.contains(e.relatedTarget)) commitEdit() }}
                  >
                    <span className="flex items-center gap-0.5">
                      Q
                      <input
                        autoFocus
                        type="text"
                        inputMode="numeric"
                        placeholder="1"
                        maxLength={2}
                        className="w-6 bg-slate-800 text-center text-blue-300 rounded outline-none"
                        value={editText.period}
                        onChange={(e) => typeField('period', e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter') commitEdit() }}
                      />
                    </span>
                    <span>·</span>
                    <input
                      type="text"
                      inputMode="numeric"
                      placeholder="00"
                      maxLength={2}
                      className="w-7 bg-slate-800 text-center text-blue-300 rounded outline-none"
                      value={editText.minutes}
                      onChange={(e) => typeField('minutes', e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') commitEdit() }}
                    />
                    <span>:</span>
                    <input
                      type="text"
                      inputMode="numeric"
                      placeholder="00"
                      maxLength={2}
                      className="w-7 bg-slate-800 text-center text-blue-300 rounded outline-none"
                      value={editText.seconds}
                      onChange={(e) => typeField('seconds', e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') commitEdit() }}
                    />
                  </span>
                ) : (
                  <span
                    title="Double-click to edit the clock"
                    className="bg-slate-700 text-blue-300 px-3 py-1 rounded-full cursor-pointer select-none"
                    onDoubleClick={openEdit}
                  >
                    Q{period} · {fmt} <span className={running ? 'text-green-400' : 'text-red-400'}>●</span>
                  </span>
                )}
                <span className="flex-1 text-center">{away?.name || 'Away'}</span>
              </div>
              <div className="flex items-center justify-center gap-6 mb-2">
                <div className="min-w-[90px] text-center bg-blue-900/60 rounded-lg py-2 px-4 text-5xl font-mono font-bold text-blue-400 tabular-nums">{scores?.home_score ?? 0}</div>
                <div className="text-slate-500 font-bold">VS</div>
                <div className="min-w-[90px] text-center bg-blue-900/60 rounded-lg py-2 px-4 text-5xl font-mono font-bold text-blue-400 tabular-nums">{scores?.away_score ?? 0}</div>
              </div>
            </div>

            {/* Clock controls */}
            <div className="mt-5 flex items-center justify-center gap-3 flex-wrap">
              <button
                className={`btn ${running ? 'btn-secondary' : 'btn-primary'}`}
                onClick={toggleClock}
              >
                <i className={`bi ${running ? 'bi-pause-fill' : 'bi-play-fill'}`} />{running ? 'Pause' : 'Start'}
              </button>
            </div>
          </div>

          {/* Score buttons */}
          <div className="card p-5 flex flex-col gap-6">
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">{home?.name || 'Home'}</h3>
              <div className="flex gap-2">
                {[1, 2, 3].map((n) => (
                  <span key={n} className="flex flex-1 gap-1">
                    <button className="btn btn-primary flex-1 text-lg" onClick={() => emit({ home_delta: n })}>+{n}</button>
                    <button className="btn btn-outline text-lg px-2" title={`Undo ${n} for ${home?.name || 'Home'}`} onClick={() => undo('home', n)}>−{n}</button>
                  </span>
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">{away?.name || 'Away'}</h3>
              <div className="flex gap-2">
                {[1, 2, 3].map((n) => (
                  <span key={n} className="flex flex-1 gap-1">
                    <button className="btn btn-primary flex-1 text-lg" onClick={() => emit({ away_delta: n })}>+{n}</button>
                    <button className="btn btn-outline text-lg px-2" title={`Undo ${n} for ${away?.name || 'Away'}`} onClick={() => undo('away', n)}>−{n}</button>
                  </span>
                ))}
              </div>
            </div>
            <p className="text-xs text-gray-500">Scores save live. The final result still gets submitted from the Matches page when the game ends.</p>
          </div>
        </div>

        {/* Live player scoring grid */}
        <div className="card p-5 mt-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-700">Live player grid</h3>
            <span className="text-xs text-gray-500">Polling every 5s · fouls out at {foulLimit} fouls</span>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {[['home', home], ['away', away]].map(([side, team]) => (
              <div key={side}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-semibold text-sm text-gray-900">{team?.name || (side === 'home' ? 'Home' : 'Away')}</span>
                  <span className="text-xs text-gray-400">{players.filter((p) => p.team_id === team?.id).length} players</span>
                </div>
                {players.filter((p) => p.team_id === team?.id).length === 0 ? (
                  <p className="text-sm text-gray-400">No rostered players.</p>
                ) : (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 text-left text-xs uppercase text-gray-500">
                        <th className="px-2 py-1.5">Player</th>
                        <th className="px-2 py-1.5 text-center">Pts</th>
                        <th className="px-2 py-1.5 text-center">FLS</th>
                        <th className="px-2 py-1.5 text-right"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {players.filter((p) => p.team_id === team?.id).map((p) => {
                        const st = statByPlayer[p.id]
                        const fouls = st?.fouls ?? 0
                        const out = fouls >= foulLimit
                        return (
                          <tr key={p.id} className={`border-t border-gray-100 ${out ? 'bg-rose-50' : ''}`}>
                            <td className="px-2 py-1.5 font-medium text-gray-900">
                              <span className="inline-flex items-center gap-1.5">
                                {p.jersey_number ? <span className="text-gray-400 text-xs">{p.jersey_number}</span> : null}
                                {p.full_name}
                                {out && <span className="badge badge-danger">Fouled out</span>}
                              </span>
                            </td>
                            <td className="px-2 py-1.5 text-center font-mono tabular-nums">{st?.points ?? 0}</td>
                            <td className={`px-2 py-1.5 text-center font-mono tabular-nums ${out ? 'text-rose-600 font-bold' : ''}`}>{fouls}</td>
                            <td className="px-2 py-1.5 text-right whitespace-nowrap">
                              <button className="btn btn-sm btn-outline mr-1" title="+1 point" disabled={liveMut.isPending} onClick={() => addPlayerPoint(p)}>+1 Pts</button>
                              <button className="btn btn-sm btn-danger" title="+1 foul" disabled={out || liveMut.isPending} onClick={() => addFoul(p)}>+1 Foul</button>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            ))}
          </div>
        </div>
        </div>
      )}
    </div>
  )
}
