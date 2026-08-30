import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { endpoints } from '../lib/api'
import { sendVerificationEmail } from '../lib/email'
import { useAuthStore } from '../store/authStore'
import ErrorBanner from '../components/ErrorBanner'

export default function RegisterPage() {
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [contactPhone, setContactPhone] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [code, setCode] = useState('')
  const [step, setStep] = useState(1) // 1 = details, 2 = email code
  const [error, setError] = useState(null)
  const [notice, setNotice] = useState(null)
  const [simulatedCode, setSimulatedCode] = useState(null)
  const [emailNotice, setEmailNotice] = useState(null)
  const [fieldErrors, setFieldErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const login = useAuthStore((s) => s.login)
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const next = searchParams.get('next') || '/register-team'

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setNotice(null)
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
      const code = res.data.verification_code || null
      setSimulatedCode(code)
      if (code) {
        const delivery = await sendVerificationEmail(email, code)
        if (delivery.sent) {
          setNotice(`A 6-digit verification code was sent to ${email}. Enter it below to finish creating your account.`)
          setEmailNotice(null)
        } else {
          setEmailNotice(`Email not sent: ${delivery.error || 'unknown reason'} — using the on-screen code below for now.`)
          setNotice('A 6-digit verification code is required. Enter it below to finish creating your account.')
        }
      } else {
        setNotice('A 6-digit verification code was sent to your email. Enter it below to finish creating your account.')
      }
      setStep(2)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  async function handleVerify(e) {
    e.preventDefault()
    setError(null)
    setNotice(null)
    setLoading(true)
    try {
      const res = await endpoints.verifyEmail({ email, code })
      login({ access_token: res.data.access_token, role: res.data.role, email })
      navigate(next)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  async function handleResend() {
    setError(null)
    setNotice(null)
    setLoading(true)
    try {
      const res = await endpoints.resendVerificationCode({ email })
      const code = res.data.verification_code || null
      setSimulatedCode(code)
      if (code) {
        const delivery = await sendVerificationEmail(email, code)
        if (delivery.sent) {
          setNotice(`A new verification code was sent to ${email}.`)
          setEmailNotice(null)
        } else {
          setEmailNotice(`Email not sent: ${delivery.error || 'unknown reason'} — using the on-screen code below.`)
          setNotice('A new verification code is required. Use the code shown below.')
        }
      } else {
        setNotice('A new verification code was sent to your email.')
      }
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
        {notice && <div className="mb-3 text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-md px-3 py-2">{notice}</div>}
        {emailNotice && <div className="mb-3 text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-md px-3 py-2">{emailNotice}</div>}

        {step === 1 ? (
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
        ) : (
          <form onSubmit={handleVerify} noValidate>
            <div className="mb-1">
              <label className="label">Verification code</label>
              <input
                className={`input ${fieldErrors.code ? 'input-error' : ''} text-center text-lg tracking-[0.4em]`}
                value={code}
                inputMode="numeric"
                maxLength={6}
                placeholder="· · · · · ·"
                onChange={(e) => { setCode(e.target.value.replace(/\D/g, '')); if (fieldErrors.code) setFieldErrors((f) => ({ ...f, code: undefined })) }}
                required
              />
              {fieldErrors.code && <p className="field-error">{fieldErrors.code}</p>}
            </div>
            <p className="mb-4 text-sm text-gray-500">
              We emailed a 6-digit code to <span className="font-semibold text-gray-700">{email}</span>. Enter it to finish signing up.
            </p>
            {simulatedCode && emailNotice && (
              <div className="mb-4 text-center text-sm bg-amber-50 border border-amber-200 text-amber-800 rounded-md px-3 py-2">
                <div className="font-semibold mb-1">Your code (email delivery not set up yet)</div>
                <div className="text-2xl font-bold tracking-[0.3em] text-gray-900">{simulatedCode}</div>
                <div className="mt-1 text-xs text-amber-700">Enter this code to continue.</div>
              </div>
            )}
            <button className="btn btn-primary w-full justify-center" disabled={loading || code.length !== 6}>
              {loading ? 'Verifying...' : 'Verify & continue'}
            </button>
            <button type="button" className="btn btn-secondary w-full justify-center mt-2" onClick={handleResend} disabled={loading}>
              Resend code
            </button>
            <button type="button" className="btn btn-ghost w-full justify-center mt-1" onClick={() => setStep(1)} disabled={loading}>
              Back
            </button>
          </form>
        )}

        <p className="mt-4 text-center text-sm text-gray-500">
          Already have an account? <Link to="/login" className="text-blue-600 font-semibold">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
