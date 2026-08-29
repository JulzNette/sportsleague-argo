import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { endpoints } from '../lib/api'
import { sendFeeReminder } from '../lib/email'
import { can } from '../lib/permissions'
import { useAuthStore } from '../store/authStore'
import { buildSportMaps } from '../lib/sports'
import PageHead from '../components/PageHead'
import DataTable from '../components/DataTable'
import Modal from '../components/Modal'
import Badge from '../components/Badge'
import ErrorBanner from '../components/ErrorBanner'
import { SportBadge } from '../components/SportControls'

const FILTERS = ['', 'Pending', 'Approved', 'Rejected']

export default function RegistrationsPage() {
  const role = useAuthStore((s) => s.role)
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const { data: registrations, isLoading } = useQuery({
    queryKey: ['registrations'],
    queryFn: () => endpoints.registrations.list().then((r) => r.data),
  })
  const { data: leagues = [] } = useQuery({ queryKey: ['leagues'], queryFn: () => endpoints.leagues.list().then((r) => r.data) })
  const { data: seasons = [] } = useQuery({ queryKey: ['seasons'], queryFn: () => endpoints.seasons.list().then((r) => r.data) })
  const { data: divisions = [] } = useQuery({ queryKey: ['divisions'], queryFn: () => endpoints.divisions.list().then((r) => r.data) })
  const { sportOf } = buildSportMaps({ leagues, seasons, divisions })

  const [statusFilter, setStatusFilter] = useState('')
  const [selected, setSelected] = useState(null)
  const [comment, setComment] = useState('')
  const [error, setError] = useState(null)
  const [mailNotice, setMailNotice] = useState(null)

  const reviewMut = useMutation({
    mutationFn: ({ id, data }) => endpoints.registrations.review(id, data),
    onSuccess: (res) => {
      setSelected(res.data)
      setComment('')
      setError(null)
      qc.invalidateQueries({ queryKey: ['registrations'] })
      qc.invalidateQueries({ queryKey: ['teams'] })
      qc.invalidateQueries({ queryKey: ['players'] })
    },
    onError: setError,
  })

  const paymentMut = useMutation({
    mutationFn: ({ id, data }) => endpoints.registrations.payment(id, data),
    onSuccess: (res) => {
      setSelected(res.data)
      qc.invalidateQueries({ queryKey: ['registrations'] })
    },
    onError: setError,
  })

  const emailMut = useMutation({
    mutationFn: (reg) => sendFeeReminder(reg),
    onSuccess: (res) => {
      setMailNotice(
        res.sent
          ? `Emailed the registrant about their registration fee.`
          : `Email not sent (${res.error || 'unavailable'}). Check EmailJS template config.`
      )
      qc.invalidateQueries({ queryKey: ['registrations'] })
    },
    onError: setError,
  })

  const canReview = can(role, 'registration.review')
  const isReviewable = (r) => canReview && r.status === 'Pending'

  const divisionPath = (id) => {
    const div = divisions.find((d) => d.id === id)
    if (!div) return '—'
    const season = seasons.find((s) => s.id === div.season_id)
    const league = leagues.find((l) => l.id === season?.league_id)
    return [league?.name, season?.name, div.name].filter(Boolean).join(' / ')
  }

  const fmtFee = (v) => (v == null ? '—' : `₱${Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 })}`)
  const paymentBadge = (s) => (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${s === 'Paid' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
      {s}
    </span>
  )

  const visible = statusFilter ? registrations?.filter((r) => r.status === statusFilter) : registrations

  function openDetail(r) { setSelected(r); setComment(''); setError(null); setMailNotice(null) }
  function handleApprove() { if (selected) reviewMut.mutate({ id: selected.id, data: { status: 'Approved', review_comment: comment || null } }) }
  function handleReject() { if (selected) reviewMut.mutate({ id: selected.id, data: { status: 'Rejected', review_comment: comment || null } }) }

  useEffect(() => {
    const id = searchParams.get('id')
    if (id && registrations && !selected) {
      const match = registrations.find((r) => r.id === id)
      if (match) {
        openDetail(match)
        setSearchParams({}, { replace: true })
      }
    }
  }, [searchParams, registrations, selected])

  if (!can(role, 'registration.submit')) {
    return (
      <div className="card p-10 text-center text-gray-400">
        <i className="bi bi-lock text-2xl" />
        <p className="mt-2 text-sm">You don't have access to Registrations.</p>
      </div>
    )
  }

  return (
    <div>
      <PageHead
        title="Registrations"
        subtitle="Teams applying to join divisions — approvals create the team and roster."
        actions={can(role, 'registration.submit') && (
          <button className="btn btn-primary" onClick={() => navigate('/register-team')}>
            <i className="bi bi-plus-lg" />Register a team
          </button>
        )}
      />

      {isLoading ? <p className="text-sm text-gray-500">Loading...</p> : (
        <>
          <div className="card p-3.5 mb-4 flex gap-3 items-center flex-wrap">
            <label className="text-sm font-medium text-gray-700">Status</label>
            <select className="input w-auto" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              {FILTERS.map((f) => <option key={f} value={f}>{f === '' ? 'All statuses' : f}</option>)}
            </select>
          </div>
          <DataTable
            columns={[
              { key: 'team_name', label: 'Team', render: (r) => <span className="font-semibold text-gray-900">{r.team_name}</span> },
              { key: 'sport', label: 'Sport', render: (r) => <SportBadge sport={sportOf.division(r.division_id)} /> },
              { key: 'division', label: 'Division', render: (r) => divisionPath(r.division_id) },
              { key: 'players', label: 'Players', render: (r) => r.players.length },
              { key: 'submitted', label: 'Submitted', render: (r) => new Date(r.created_at).toLocaleDateString() },
              { key: 'status', label: 'Status', render: (r) => <Badge status={r.status} /> },
              { key: 'fee', label: 'Fee', render: (r) => <span className="font-medium">{fmtFee(r.registration_fee)}</span> },
              { key: 'payment', label: 'Payment', render: (r) => paymentBadge(r.payment_status) },
            ]}
            rows={visible}
            actions={(row) => [
              { label: 'View', icon: 'bi-eye', onClick: () => openDetail(row) },
              ...(isReviewable(row) ? [{ label: 'Review', icon: 'bi-clipboard-check', onClick: () => openDetail(row) }] : []),
              ...(canReview ? [
                { label: row.payment_status === 'Paid' ? 'Mark unpaid' : 'Mark paid', icon: row.payment_status === 'Paid' ? 'bi-arrow-counterclockwise' : 'bi-check2-circle', onClick: () => paymentMut.mutate({ id: row.id, data: { payment_status: row.payment_status === 'Paid' ? 'Pending' : 'Paid' } }) },
                { label: 'Email registrant', icon: 'bi-envelope', onClick: () => emailMut.mutate(row) },
              ] : []),
            ]}
            emptyLabel="No registrations yet."
          />
        </>
      )}

      {selected && (
        <Modal
          title={selected.team_name}
          subtitle={divisionPath(selected.division_id)}
          onClose={() => setSelected(null)}
          footer={<button className="btn btn-secondary" onClick={() => setSelected(null)}>Close</button>}
        >
          <ErrorBanner error={error} />
          {mailNotice && (
            <div className="rounded-md bg-blue-50 border border-blue-200 px-3.5 py-2.5 text-sm text-blue-700 mb-3 flex items-center gap-2">
              <i className="bi bi-envelope-check" />{mailNotice}
            </div>
          )}
          <div className="flex items-center gap-2 mb-3">
            <Badge status={selected.status} />
            <SportBadge sport={sportOf.division(selected.division_id)} />
          </div>

          <dl className="text-sm space-y-1.5 mb-4">
            <div className="flex justify-between gap-4"><dt className="text-gray-500">Coach</dt><dd className="font-medium text-right">{selected.coach_name || '—'}</dd></div>
            <div className="flex justify-between gap-4"><dt className="text-gray-500">Contact</dt><dd className="font-medium text-right">{[selected.contact_email, selected.contact_phone].filter(Boolean).join(' • ') || '—'}</dd></div>
            <div className="flex justify-between gap-4"><dt className="text-gray-500">Submitted</dt><dd className="font-medium text-right">{new Date(selected.created_at).toLocaleString()}</dd></div>
            <div className="flex justify-between gap-4"><dt className="text-gray-500">Registration fee</dt><dd className="font-medium text-right">{fmtFee(selected.registration_fee)}</dd></div>
            <div className="flex justify-between gap-4 items-center"><dt className="text-gray-500">Payment</dt><dd className="text-right">{paymentBadge(selected.payment_status)}</dd></div>
            {selected.reviewed_at && (
              <div className="flex justify-between gap-4"><dt className="text-gray-500">Reviewed</dt><dd className="font-medium text-right">{new Date(selected.reviewed_at).toLocaleString()}</dd></div>
            )}
          </dl>

          {selected.notes && <p className="text-sm text-gray-600 bg-gray-50 border border-gray-100 rounded-lg px-3 py-2 mb-4"><b>Notes:</b> {selected.notes}</p>}

          <div className="mb-4">
            <span className="text-sm font-semibold text-gray-700">Roster ({selected.players.length})</span>
            <div className="border border-gray-200 rounded-lg overflow-hidden mt-1.5">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-left text-xs uppercase text-gray-500">
                    <th className="px-3 py-2">Name</th><th className="px-3 py-2">Jersey</th><th className="px-3 py-2">Position</th><th className="px-3 py-2">Born</th><th className="px-3 py-2">Phone</th>
                  </tr>
                </thead>
                <tbody>
                  {selected.players.map((p) => (
                    <tr key={p.id} className="border-t border-gray-100">
                      <td className="px-3 py-2 font-medium">{p.full_name}</td>
                      <td className="px-3 py-2">{p.jersey_number}</td>
                      <td className="px-3 py-2">{p.position || '—'}</td>
                      <td className="px-3 py-2">{p.date_of_birth || '—'}</td>
                      <td className="px-3 py-2">{p.contact_phone || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {selected.documents.length > 0 && (
            <div className="mb-4">
              <span className="text-sm font-semibold text-gray-700">Documents ({selected.documents.length})</span>
              <ul className="mt-1.5 space-y-1.5 text-sm">
                {selected.documents.map((d) => (
                  <li key={d.id} className="flex items-start gap-2 text-gray-600">
                    <i className="bi bi-file-earmark-text text-gray-400 mt-0.5" />
                    <span>
                      <b>{d.document_type}</b>{d.player_full_name ? ` — ${d.player_full_name}` : ''}{d.file_name ? ` (${d.file_name})` : ''}
                      {d.notes ? <span className="block text-xs text-gray-500 mt-0.5">{d.notes}</span> : null}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {selected.review_comment && (
            <div className={`rounded-lg border px-3.5 py-2.5 text-sm mb-4 ${selected.status === 'Rejected' ? 'border-rose-200 bg-rose-50 text-rose-700' : 'border-emerald-200 bg-emerald-50 text-emerald-700'}`}>
              <b>{selected.status === 'Approved' ? 'Approved' : 'Rejected'}:</b> {selected.review_comment}
            </div>
          )}

          {selected.status === 'Approved' && (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3.5 py-2.5 text-sm text-emerald-700 mb-4 flex items-center gap-2">
              <i className="bi bi-check-circle" />Team and roster created — find it under Teams.
            </div>
          )}

          {canReview && (
            <div className="border border-gray-200 rounded-lg p-3.5 mb-4">
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <div className="text-sm">
                  <div className="font-semibold text-gray-900">Registration fee: {fmtFee(selected.registration_fee)}</div>
                  <div className="text-xs text-gray-500 mt-0.5">Payment status: <b>{selected.payment_status}</b></div>
                </div>
                <div className="flex gap-2">
                  <button className="btn btn-secondary" disabled={paymentMut.isPending} onClick={() => paymentMut.mutate({ id: selected.id, data: { payment_status: selected.payment_status === 'Paid' ? 'Pending' : 'Paid' } })}>
                    <i className="bi bi-credit-card" />{selected.payment_status === 'Paid' ? 'Mark unpaid' : 'Mark paid'}
                  </button>
                  <button className="btn btn-primary" disabled={emailMut.isPending} onClick={() => emailMut.mutate(selected)}>
                    <i className="bi bi-envelope" />{emailMut.isPending ? 'Sending...' : 'Email registrant'}
                  </button>
                </div>
              </div>
              {selected.contact_email
                ? <p className="text-xs text-gray-400 mt-2">Emails go to <b>{selected.contact_email}</b>.</p>
                : <p className="text-xs text-rose-500 mt-2">No contact email on this registration.</p>}
            </div>
          )}

          {isReviewable(selected) && (
            <div className="border border-gray-200 rounded-lg p-3.5">
              <label className="label">Review comment (required to reject)</label>
              <textarea className="input" rows={3} value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Optional for approval" />
              <div className="flex gap-2 mt-3 justify-end">
                <button className="btn btn-danger" disabled={reviewMut.isPending} onClick={handleReject}><i className="bi bi-x-lg" />Reject</button>
                <button className="btn btn-primary" disabled={reviewMut.isPending} onClick={handleApprove}><i className="bi bi-check-lg" />Approve</button>
              </div>
            </div>
          )}
        </Modal>
      )}
    </div>
  )
}
