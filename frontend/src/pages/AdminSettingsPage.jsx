import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { endpoints } from '../lib/api'
import { can } from '../lib/permissions'
import { useAuthStore } from '../store/authStore'
import PageHead from '../components/PageHead'
import ErrorBanner from '../components/ErrorBanner'

export default function AdminSettingsPage() {
  const role = useAuthStore((s) => s.role)
  const qc = useQueryClient()
  const [error, setError] = useState(null)
  const [notice, setNotice] = useState(null)

  const settingsQ = useQuery({ queryKey: ['admin-settings'], queryFn: () => endpoints.settings.admin().then((r) => r.data) })
  const s = settingsQ.data || {}

  // Default registration fee
  const [feeInput, setFeeInput] = useState('')
  useEffect(() => { if (s.configured_fee) setFeeInput(String(s.registration_fee)) }, [s.configured_fee, s.registration_fee])

  // Foul-out limit used by the live scoring grid.
  const [foulLimit, setFoulLimit] = useState(5)
  useEffect(() => { if (s.foul_limit != null) setFoulLimit(s.foul_limit) }, [s.foul_limit])

  const flash = (msg) => { setNotice(msg); setTimeout(() => setNotice(null), 3500) }

  const feeMut = useMutation({
    mutationFn: (data) => endpoints.settings.setFee(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-settings'] }); flash('Registration fee saved') },
    onError: setError,
  })
  const foulLimitMut = useMutation({
    mutationFn: (data) => endpoints.settings.setFoulLimit(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-settings'] }); flash('Foul limit saved') },
    onError: setError,
  })

  if (!can(role, 'settings.manage')) {
    return <p className="text-sm text-gray-500">You do not have permission to manage settings.</p>
  }

  return (
    <div>
      <PageHead title="Admin Settings" subtitle="The single registration fee every registrant pays." />
      {error && <ErrorBanner message={error?.message || error?.detail || 'Something went wrong'} onClose={() => setError(null)} />}
      {notice && <div className="card p-3 mb-4 text-sm" style={{ background: '#EFF6FF', borderColor: '#BFDBFE', color: '#1D4ED8' }}>{notice}</div>}

      {/* ===== Default registration fee ===== */}
      <div className="card p-4 mb-4">
        <h3 className="text-base font-semibold mb-1">Registration fee</h3>
        <p className="text-sm text-gray-500 mb-3">A single fee applied to every team that registers. Registrants pay this amount on the form.</p>
        <div className="flex gap-3 items-end flex-wrap">
          <div>
            <label className="text-xs font-medium text-gray-600 block mb-1">Amount (₱)</label>
            <input className="input" style={{ width: 160 }} type="number" min="0" step="any"
              placeholder="e.g. 500" value={feeInput} onChange={(e) => setFeeInput(e.target.value)} />
          </div>
          <button className="btn btn-primary" disabled={feeMut.isPending}
            onClick={() => feeMut.mutate({ amount: feeInput === '' ? null : Number(feeInput) })}>
            {feeMut.isPending ? 'Saving...' : 'Save fee'}
          </button>
          <span className={`badge badge-${s.configured_fee ? 'success' : 'neutral'}`}>{s.configured_fee ? 'Configured' : 'Not set'}</span>
        </div>
      </div>

      {/* ===== Foul-out limit ===== */}
      <div className="card p-4 mb-4">
        <h3 className="text-base font-semibold mb-1">Foul-out limit</h3>
        <p className="text-sm text-gray-500 mb-3">The live scoring grid flags a player as "fouled out" when their fouls reach this number.</p>
        <div className="flex gap-3 items-end flex-wrap">
          <div>
            <label className="text-xs font-medium text-gray-600 block mb-1">Fouls</label>
            <input className="input" style={{ width: 120 }} type="number" min="1" max="20"
              value={foulLimit} onChange={(e) => setFoulLimit(e.target.value === '' ? '' : Number(e.target.value))} />
          </div>
          <button className="btn btn-primary" disabled={foulLimitMut.isPending || foulLimit === ''}
            onClick={() => foulLimitMut.mutate({ foul_limit: Number(foulLimit) })}>
            {foulLimitMut.isPending ? 'Saving...' : 'Save limit'}
          </button>
        </div>
      </div>
    </div>
  )
}
