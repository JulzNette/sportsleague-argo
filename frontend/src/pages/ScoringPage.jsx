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

  const [matchId, setMatchId] = useState('')
  const [error, setError] = useState(null)

  const [period, setPeriod] = useState(1)
  const [minutes, setMinutes] = useState(0)
  const [seconds, setSeconds] = useState(0)
  const [running, setRunning] = useState(false)
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
  function onMinutesChange(raw) {
    const v = Math.floor(Number(raw))
    if (raw === '' || Number.isNaN(v)) return
    const next = clamp(v, 0, 59)
    setMinutes(next)
    if (matchId) emit({ minutes: next })
  }
  function onSecondsChange(raw) {
    const v = Math.floor(Number(raw))
    if (raw === '' || Number.isNaN(v)) return
    const next = clamp(v, 0, 59)
    setSeconds(next)
    if (matchId) emit({ seconds: next })
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
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Scoreboard */}
          <div className="card p-5">
            <div className="bg-slate-900 rounded-2xl p-5 text-white">
              <div className="flex items-center justify-between mb-3 text-xs font-semibold uppercase tracking-widest">
                <span className="flex-1 text-center">{home?.name || 'Home'}</span>
                <span className="bg-slate-700 text-blue-300 px-3 py-1 rounded-full">Q{period} · {fmt} <span className={running ? 'text-green-400' : 'text-red-400'}>●</span></span>
                <span className="flex-1 text-center">{away?.name || 'Away'}</span>
              </div>
              <div className="flex items-center justify-center gap-6 mb-2">
                <div className="min-w-[90px] text-center bg-blue-900/60 rounded-lg py-2 px-4 text-5xl font-mono font-bold text-blue-400 tabular-nums">{scores?.home_score ?? 0}</div>
                <div className="text-slate-500 font-bold">VS</div>
                <div className="min-w-[90px] text-center bg-blue-900/60 rounded-lg py-2 px-4 text-5xl font-mono font-bold text-blue-400 tabular-nums">{scores?.away_score ?? 0}</div>
              </div>
            </div>

            {/* Clock controls */}
            <div className="mt-5 flex items-end justify-center gap-3 flex-wrap">
              {/* Period stepper */}
              <div className="flex flex-col items-center">
                <span className="text-[10px] uppercase tracking-widest text-gray-400 mb-1 font-semibold">Period</span>
                <button className="btn btn-secondary px-3 py-1" onClick={() => changePeriod(1)}><i className="bi bi-chevron-up" /></button>
                <div className="text-center font-mono text-lg py-1 tabular-nums w-12">{period}</div>
                <button className="btn btn-secondary px-3 py-1" onClick={() => changePeriod(-1)} disabled={period <= 1}><i className="bi bi-chevron-down" /></button>
              </div>

              <span className="text-3xl font-mono text-gray-300 pb-8 px-1">:</span>

              {/* Minutes */}
              <div className="flex flex-col items-center">
                <span className="text-[10px] uppercase tracking-widest text-gray-400 mb-1 font-semibold">Minutes</span>
                <button className="btn btn-secondary px-3 py-1" onClick={() => stepMinutes(1)}><i className="bi bi-caret-up-fill" /></button>
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={2}
                  className="input font-mono text-center text-2xl w-20 py-1 tabular-nums"
                  value={pad(minutes)}
                  onChange={(e) => onMinutesChange(e.target.value)}
                />
                <button className="btn btn-secondary px-3 py-1" onClick={() => stepMinutes(-1)}><i className="bi bi-caret-down-fill" /></button>
              </div>

              <span className="text-3xl font-mono text-gray-300 pb-8 px-1">:</span>

              {/* Seconds */}
              <div className="flex flex-col items-center">
                <span className="text-[10px] uppercase tracking-widest text-gray-400 mb-1 font-semibold">Seconds</span>
                <button className="btn btn-secondary px-3 py-1" onClick={() => stepSeconds(1)}><i className="bi bi-caret-up-fill" /></button>
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={2}
                  className="input font-mono text-center text-2xl w-20 py-1 tabular-nums"
                  value={pad(seconds)}
                  onChange={(e) => onSecondsChange(e.target.value)}
                />
                <button className="btn btn-secondary px-3 py-1" onClick={() => stepSeconds(-1)}><i className="bi bi-caret-down-fill" /></button>
              </div>

              <button
                className={`btn self-center ${running ? 'btn-secondary' : 'btn-primary'}`}
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
                  <button key={n} className="btn btn-primary flex-1 text-lg" onClick={() => emit({ home_delta: n })}>+{n}</button>
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">{away?.name || 'Away'}</h3>
              <div className="flex gap-2">
                {[1, 2, 3].map((n) => (
                  <button key={n} className="btn btn-primary flex-1 text-lg" onClick={() => emit({ away_delta: n })}>+{n}</button>
                ))}
              </div>
            </div>
            <p className="text-xs text-gray-500">Scores save live. The final result still gets submitted from the Matches page when the game ends.</p>
          </div>
        </div>
      )}
    </div>
  )
}
