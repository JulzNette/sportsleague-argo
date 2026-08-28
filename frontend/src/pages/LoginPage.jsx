import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { endpoints } from '../lib/api'
import { useAuthStore } from '../store/authStore'
import ErrorBanner from '../components/ErrorBanner'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const login = useAuthStore((s) => s.login)
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await endpoints.login({ email, password })
      login({ access_token: res.data.access_token, role: res.data.role, email })
      navigate('/dashboard')
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 px-4">
      <div className="card w-full max-w-sm p-6">
        <div className="flex items-center gap-2.5 mb-6">
          <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white text-sm">SL</div>
          <div>
            <div className="font-semibold text-gray-900 text-sm">Sports League Management</div>
            <div className="text-[11px] text-gray-500">ARGO Platform</div>
          </div>
        </div>

        <ErrorBanner error={error} />

        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="label">Email</label>
            <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="mb-4">
            <label className="label">Password</label>
            <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <button className="btn btn-primary w-full justify-center" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-500">
          Don't have an account? <Link to="/register" className="text-blue-600 font-semibold">Create one</Link>
        </p>
      </div>
    </div>
  )
}