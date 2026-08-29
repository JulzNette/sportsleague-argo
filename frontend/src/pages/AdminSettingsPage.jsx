import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { endpoints } from '../lib/api'
import { can } from '../lib/permissions'
import { useAuthStore } from '../store/authStore'
import PageHead from '../components/PageHead'
import ErrorBanner from '../components/ErrorBanner'

const EMPTY_PRICING = { title: '', amount: '', description: '' }
const EMPTY_REWARD = { division: '', place: '', prize: '', incentive: '' }

function Divider({ label }) {
  return (
    <div style={{ margin: '34px 0 18px' }}>
      <div style={{ fontSize: 13, letterSpacing: '0.14em', textTransform: 'uppercase', fontWeight: 700, color: '#2563EB' }}>{label}</div>
      <div style={{ height: 1, background: '#E7E4DC', marginTop: 8 }} />
    </div>
  )
}

export default function AdminSettingsPage() {
  const role = useAuthStore((s) => s.role)
  const qc = useQueryClient()
  const [error, setError] = useState(null)
  const [notice, setNotice] = useState(null)

  const settingsQ = useQuery({ queryKey: ['admin-settings'], queryFn: () => endpoints.settings.admin().then((r) => r.data) })
  const divisionsQ = useQuery({ queryKey: ['divisions'], queryFn: () => endpoints.divisions.list().then((r) => r.data) })
  const s = settingsQ.data || {}
  const divisions = divisionsQ.data || []

  // Default fee
  const [feeInput, setFeeInput] = useState('')
  useEffect(() => { if (s.configured_fee) setFeeInput(String(s.registration_fee)) }, [s.configured_fee, s.registration_fee])

  // Per-division override map: division_id -> input string
  const [overrides, setOverrides] = useState({})
  useEffect(() => {
    if (!divisionsQ.data) return
    const m = {}
    for (const d of divisionsQ.data) m[d.id] = ''
    for (const f of (s.division_fees || [])) m[f.division_id] = String(f.registration_fee)
    setOverrides(m)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [divisionsQ.data, s.division_fees])

  // Pricing / rewards content editors
  const [pricing, setPricing] = useState([])
  const [rewards, setRewards] = useState([])
  useEffect(() => { setPricing(Array.isArray(s.pricing) ? s.pricing : []) }, [s.pricing])
  useEffect(() => { setRewards(Array.isArray(s.rewards) ? s.rewards : []) }, [s.rewards])

  const flash = (msg) => { setNotice(msg); setTimeout(() => setNotice(null), 3500) }

  const feeMut = useMutation({
    mutationFn: (data) => endpoints.settings.setFee(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-settings'] }); flash('Default fee saved') },
    onError: setError,
  })
  const contentMut = useMutation({
    mutationFn: (data) => endpoints.settings.setContent(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-settings'] }); flash('Page content saved') },
    onError: setError,
  })
  const divFeeMut = useMutation({
    mutationFn: (data) => endpoints.settings.setDivisionFee(data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-settings'] }); flash('Division fee saved') },
    onError: setError,
  })
  const clearFeeMut = useMutation({
    mutationFn: (divisionId) => endpoints.settings.clearDivisionFee(divisionId),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-settings'] }); flash('Division override cleared') },
    onError: setError,
  })

  if (!can(role, 'settings.manage')) {
    return <p className="text-sm text-gray-500">You do not have permission to manage settings.</p>
  }

  return (
    <div>
      <PageHead title="Admin Settings" subtitle="Registration fees and public Pricing / Rewards page content." />
      {error && <ErrorBanner message={error?.message || error?.detail || 'Something went wrong'} onClose={() => setError(null)} />}
      {notice && <div className="card p-3 mb-4 text-sm" style={{ background: '#EFF6FF', borderColor: '#BFDBFE', color: '#1D4ED8' }}>{notice}</div>}

      {/* ===== Default fee ===== */}
      <div className="card p-4 mb-4">
        <h3 className="text-base font-semibold mb-1">Default registration fee</h3>
        <p className="text-sm text-gray-500 mb-3">Applied to every division unless a division has its own override. Registrants pay this on the form.</p>
        <div className="flex gap-3 items-end flex-wrap">
          <div>
            <label className="text-xs font-medium text-gray-600 block mb-1">Amount (₱)</label>
            <input className="input" style={{ width: 160 }} type="number" min="0" step="any"
              placeholder="e.g. 1500" value={feeInput} onChange={(e) => setFeeInput(e.target.value)} />
          </div>
          <button className="btn btn-primary" disabled={feeMut.isPending}
            onClick={() => feeMut.mutate({ amount: feeInput === '' ? null : Number(feeInput) })}>
            {feeMut.isPending ? 'Saving...' : 'Save fee'}
          </button>
          <span className={`badge badge-${s.configured_fee ? 'success' : 'neutral'}`}>{s.configured_fee ? 'Configured' : 'Not set'}</span>
        </div>
      </div>

      {/* ===== Per-division overrides ===== */}
      <div className="card p-4 mb-4">
        <h3 className="text-base font-semibold mb-1">Per-division overrides</h3>
        <p className="text-sm text-gray-500 mb-3">Override the default fee for a specific division. Leave blank to use the default.</p>
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-left text-xs uppercase text-gray-500">
                <th className="px-3 py-2">Division</th>
                <th className="px-3 py-2">Override (₱)</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {divisions.length === 0 ? (
                <tr><td colSpan={4} className="px-3 py-4 text-sm text-gray-400">No divisions yet.</td></tr>
              ) : divisions.map((d) => {
                const override = (s.division_fees || []).find((f) => f.division_id === d.id)
                const effective = override ? override.registration_fee : s.registration_fee
                return (
                  <tr key={d.id} className="border-t border-gray-100">
                    <td className="px-3 py-2 font-medium">{d.name}</td>
                    <td className="px-3 py-2">
                      <input className="input" style={{ width: 140 }} type="number" min="0" step="any"
                        placeholder={effective != null ? `default ${effective}` : 'no fee'}
                        value={overrides[d.id] || ''}
                        onChange={(e) => setOverrides((m) => ({ ...m, [d.id]: e.target.value }))} />
                    </td>
                    <td className="px-3 py-2">
                      {override ? <span className="badge badge-primary">Override</span> : <span className="badge badge-neutral">Default</span>}
                    </td>
                    <td className="px-3 py-2 text-right whitespace-nowrap">
                      {overrides[d.id] !== '' && (
                        <button className="btn btn-sm btn-primary" disabled={divFeeMut.isPending}
                          onClick={() => divFeeMut.mutate({ division_id: d.id, registration_fee: Number(overrides[d.id]) })}>
                          Set
                        </button>
                      )}
                      {override && !clearFeeMut.isPending && (
                        <button className="btn btn-sm btn-outline" onClick={() => clearFeeMut.mutate(d.id)}>Clear</button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* ===== Pricing content ===== */}
      <div className="card p-4 mb-4">
        <h3 className="text-base font-semibold mb-1">Pricing page content</h3>
        <p className="text-sm text-gray-500 mb-3">Shown on the public /pricing page. Fields: title, amount (₱, optional), description.</p>
        {pricing.map((it, i) => (
          <div key={i} className="flex gap-2 mb-2 flex-wrap items-center">
            <input className="input" style={{ flex: '1 1 160px' }} value={it.title || ''}
              onChange={(e) => setPricing((arr) => arr.map((x, j) => (j === i ? { ...x, title: e.target.value } : x)))} placeholder="Title" />
            <input className="input" style={{ width: 110 }} type="number" min="0" value={it.amount ?? ''}
              onChange={(e) => setPricing((arr) => arr.map((x, j) => (j === i ? { ...x, amount: e.target.value === '' ? null : Number(e.target.value) } : x)))} placeholder="Amount" />
            <input className="input" style={{ flex: '2 1 220px' }} value={it.description || ''}
              onChange={(e) => setPricing((arr) => arr.map((x, j) => (j === i ? { ...x, description: e.target.value } : x)))} placeholder="Description" />
            <button className="btn btn-sm btn-outline" onClick={() => setPricing((arr) => arr.filter((_, j) => j !== i))}>Remove</button>
          </div>
        ))}
        <button className="btn btn-sm btn-outline mb-3" onClick={() => setPricing((arr) => [...arr, { ...EMPTY_PRICING }])}>+ Add item</button>
        <div>
          <button className="btn btn-primary" disabled={contentMut.isPending}
            onClick={() => contentMut.mutate({ key: 'pricing_content', items: pricing })}>
            {contentMut.isPending ? 'Saving...' : 'Save pricing content'}
          </button>
        </div>
      </div>

      {/* ===== Rewards content ===== */}
      <div className="card p-4 mb-4">
        <h3 className="text-base font-semibold mb-1">Rewards page content</h3>
        <p className="text-sm text-gray-500 mb-3">Shown on the public /rewards page, grouped by division. Fields: division, place, prize, incentive.</p>
        {rewards.map((it, i) => (
          <div key={i} className="grid gap-2 mb-2" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(140px,1fr))' }}>
            <input className="input" value={it.division || ''}
              onChange={(e) => setRewards((arr) => arr.map((x, j) => (j === i ? { ...x, division: e.target.value } : x)))} placeholder="Division" />
            <input className="input" value={it.place || ''}
              onChange={(e) => setRewards((arr) => arr.map((x, j) => (j === i ? { ...x, place: e.target.value } : x)))} placeholder="Place (Champion)" />
            <input className="input" value={it.prize || ''}
              onChange={(e) => setRewards((arr) => arr.map((x, j) => (j === i ? { ...x, prize: e.target.value } : x)))} placeholder="Prize (₱5,000 cash)" />
            <input className="input" value={it.incentive || ''}
              onChange={(e) => setRewards((arr) => arr.map((x, j) => (j === i ? { ...x, incentive: e.target.value } : x)))} placeholder="Incentive (trophy)" />
            <button className="btn btn-sm btn-outline" onClick={() => setRewards((arr) => arr.filter((_, j) => j !== i))}>Remove</button>
          </div>
        ))}
        <button className="btn btn-sm btn-outline mb-3" onClick={() => setRewards((arr) => [...arr, { ...EMPTY_REWARD }])}>+ Add reward</button>
        <div>
          <button className="btn btn-primary" disabled={contentMut.isPending}
            onClick={() => contentMut.mutate({ key: 'rewards_content', items: rewards })}>
            {contentMut.isPending ? 'Saving...' : 'Save rewards content'}
          </button>
        </div>
      </div>

      <Divider />
    </div>
  )
}
