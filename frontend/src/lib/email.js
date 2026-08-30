/**
 * EmailJS delivery for the Sports League module.
 *
 * Emails are sent directly from the browser via EmailJS, so no SMTP/domain
 * verification is needed and recipients get them for real:
 *  - the registration-fee reminder (admin clicks "Email registrant"), and
 *  - the sign-up email-verification code (sent to whatever address was typed).
 * If EmailJS isn't configured (dev without env vars) this logs instead of
 * failing, so the feature never breaks the host flow that triggered it.
 */
import emailjs from '@emailjs/browser'

const SERVICE_ID = import.meta.env.VITE_EMAILJS_SERVICE_ID
const PUBLIC_KEY = import.meta.env.VITE_EMAILJS_PUBLIC_KEY
const TEMPLATE_ID_FEE = import.meta.env.VITE_EMAILJS_TEMPLATE_ID_FEE
const TEMPLATE_ID_VERIFY = import.meta.env.VITE_EMAILJS_TEMPLATE_ID_VERIFY

/**
 * Send the registration-fee reminder to the Team Manager.
 * Returns {sent, error} so callers can decide how to surface failures.
 */
export async function sendFeeReminder(r) {
  const to_email = r?.manager_email || r?.contact_email
  const variables = {
    to_email,
    manager_name: r?.manager_name || r?.coach_name || 'there',
    team_name: r?.team_name,
    coach_name: r?.coach_name,
    registration_fee: r?.registration_fee,
    payment_status: r?.payment_status,
    registration_status: r?.status,
  }

  if (!SERVICE_ID || !PUBLIC_KEY || !TEMPLATE_ID_FEE) {
    console.info('[emailjs] fee template not configured — would send:', variables)
    return { sent: false, error: 'EmailJS not configured' }
  }
  try {
    await emailjs.send(SERVICE_ID, TEMPLATE_ID_FEE, variables, { publicKey: PUBLIC_KEY })
    return { sent: true, error: null }
  } catch (err) {
    console.error('[emailjs] fee reminder send failed:', err)
    return { sent: false, error: err?.message || 'EmailJS send failed' }
  }
}

/**
 * Send the 6-digit email-verification code to the address typed at sign-up.
 * Uses the same EmailJS service as the fee reminder, so the code is delivered
 * for real from the browser with no SMTP/domain setup. Callers get {sent,error}.
 */
export async function sendVerificationEmail(to_email, verification_code) {
  if (!SERVICE_ID || !PUBLIC_KEY || !TEMPLATE_ID_VERIFY) {
    console.info('[emailjs] verify template not configured — would send:', { to_email, verification_code })
    return { sent: false, error: 'EmailJS verify template not configured' }
  }
  const variables = { to_email, verification_code }
  try {
    await emailjs.send(SERVICE_ID, TEMPLATE_ID_VERIFY, variables, { publicKey: PUBLIC_KEY })
    return { sent: true, error: null }
  } catch (err) {
    console.error('[emailjs] verification email send failed:', err)
    return { sent: false, error: err?.message || 'EmailJS send failed' }
  }
}
