import { useState } from 'react'
import { endpoints } from '../lib/api'
import { useAuthStore } from '../store/authStore'
import ErrorBanner from '../components/ErrorBanner'

export default function SettingsPage() {
  const email = useAuthStore((s) => s.email)
  const role = useAuthStore((s) => s.role)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setSuccess(false)
    if (newPassword.length < 8) {
      setError({ message: 'New password must be at least 8 characters.' })
      return
    }
    if (newPassword !== confirm) {
      setError({ message: 'New passwords do not match.' })
      return
    }
    setLoading(true)
    try {
      await endpoints.changePassword({ current_password: currentPassword, new_password: newPassword })
      setCurrentPassword('')
      setNewPassword('')
      setConfirm('')
      setSuccess(true)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md">
      <div className="mb-5">
        <h1 className="text-xl font-bold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500">Manage your account and security.</p>
      </div>

      <div className="card p-5 mb-5">
        <div className="mb-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-gray-400">Signed in as</div>
          <div className="text-sm font-semibold text-gray-900 mt-0.5">{email || '—'}</div>
          <div className="text-xs text-gray-500">Role: <b>{role || '—'}</b></div>
        </div>
      </div>

      <div className="card p-5">
        <h2 className="text-sm font-semibold text-gray-900 mb-1">Change password</h2>
        <p className="text-xs text-gray-500 mb-4">Your current password is required to make the change.</p>

        <ErrorBanner error={error} />

        {success && (
          <div className="mb-4 flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3.5 py-2.5 text-sm text-emerald-700">
            <i className="bi bi-check-circle mt-0.5" />
            <span>Password changed. Use your new password the next time you sign in.</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="label">Current password</label>
            <input
              className="input"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
          </div>
          <div className="mb-3">
            <label className="label">New password</label>
            <input
              className="input"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
          </div>
          <div className="mb-4">
            <label className="label">Confirm new password</label>
            <input
              className="input"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
            />
          </div>
          <button className="btn btn-primary justify-center" disabled={loading}>
            {loading ? 'Saving...' : 'Change password'}
          </button>
        </form>
      </div>
    </div>
  )
}
