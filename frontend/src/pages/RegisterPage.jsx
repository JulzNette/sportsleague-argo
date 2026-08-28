import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { endpoints } from '../lib/api'
import { useAuthStore } from '../store/authStore'
import ErrorBanner from '../components/ErrorBanner'

export default function RegisterPage() {
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [contactPhone, setContactPhone] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState(null)
  const [fieldErrors, setFieldErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const login = useAuthStore((s) => s.login)
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const next = searchParams.get('next') || '/register-team'

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    const errors = {}
    if (!fullName.trim()) errors.fullName = 'Enter your full name.'
    if (!email.trim()) errors.email = 'Enter your email address.'
    if (!contactPhone.trim()) errors.contactPhone = 'Please add your contact number.'
    if (password.length < 8) errors.password = 'Password must be at least 8 characters.'
    if (password !== confirm) errors.confirm = 'Passwords do not match.'
    setFieldErrors(errors)
    if (Object.keys(errors).length > 0) return
    setLoading(true)
    try {
      const res = await endpoints.register({ full_name: fullName, email, contact_phone: contactPhone, password })
      login({ access_token: res.data.access_token, role: res.data.role, email })
      navigate(next)
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

        <form onSubmit={handleSubmit} noValidate>
          <div className="mb-3">
            <label className="label">Full name</label>
            <input className={`input ${fieldErrors.fullName ? 'input-error' : ''}`} value={fullName} onChange={(e) => { setFullName(e.target.value); if (fieldErrors.fullName) setFieldErrors((f) => ({ ...f, fullName: undefined })) }} required />
            {fieldErrors.fullName && <p className="field-error">Please add your full name</p>}
          </div>
          <div className="mb-3">
            <label className="label">Email</label>
            <input className={`input ${fieldErrors.email ? 'input-error' : ''}`} type="email" value={email} onChange={(e) => { setEmail(e.target.value); if (fieldErrors.email) setFieldErrors((f) => ({ ...f, email: undefined })) }} required />
            {fieldErrors.email && <p className="field-error">Please add your email address</p>}
          </div>
          <div className="mb-3">
            <label className="label">Contact number</label>
            <input className={`input ${fieldErrors.contactPhone ? 'input-error' : ''}`} type="tel" value={contactPhone} onChange={(e) => { setContactPhone(e.target.value); if (fieldErrors.contactPhone) setFieldErrors((f) => ({ ...f, contactPhone: undefined })) }} placeholder="09XX XXX XXXX" />
            {fieldErrors.contactPhone && <p className="field-error">Please add your contact number</p>}
          </div>
          <div className="mb-3">
            <label className="label">Password</label>
            <input className={`input ${fieldErrors.password ? 'input-error' : ''}`} type="password" value={password} onChange={(e) => { setPassword(e.target.value); if (fieldErrors.password) setFieldErrors((f) => ({ ...f, password: undefined })) }} required />
            {fieldErrors.password && <p className="field-error">{fieldErrors.password}</p>}
          </div>
          <div className="mb-4">
            <label className="label">Confirm password</label>
            <input className={`input ${fieldErrors.confirm ? 'input-error' : ''}`} type="password" value={confirm} onChange={(e) => { setConfirm(e.target.value); if (fieldErrors.confirm) setFieldErrors((f) => ({ ...f, confirm: undefined })) }} required />
            {fieldErrors.confirm && <p className="field-error">{fieldErrors.confirm}</p>}
          </div>
          <button className="btn btn-primary w-full justify-center" disabled={loading}>
            {loading ? 'Creating account...' : 'Create account'}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-500">
          Already have an account? <Link to="/login" className="text-blue-600 font-semibold">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
