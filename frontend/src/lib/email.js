/**
 * EmailJS delivery for the Sports League module.
 *
 * Emails are sent directly from the browser via EmailJS, so no SMTP/domain
 * verification is needed and recipients receive mail for real. If EmailJS
 * isn't configured (dev without env vars) this logs instead of failing, so
 * the feature never breaks the registration flow.
 */
import emailjs from '@emailjs/browser'

const SERVICE_ID = import.meta.env.VITE_EMAILJS_SERVICE_ID
const TEMPLATE_ID = import.meta.env.VITE_EMAILJS_TEMPLATE_ID
const PUBLIC_KEY = import.meta.env.VITE_EMAILJS_PUBLIC_KEY

/**
 * Send the "registration received" ack to the registrant's contact email.
 * Returns {sent, error} so callers can decide how to surface it.
 */
export async function sendRegistrationAck({ to_email, team_name, coach_name, registration_fee, payment_status }) {
  if (!SERVICE_ID || !TEMPLATE_ID || !PUBLIC_KEY) {
    const fields = { to_email, team_name, coach_name, registration_fee, payment_status }
    console.info('[emailjs] not configured — would send:', fields)
    return { sent: false, error: 'EmailJS not configured' }
  }

  try {
    await emailjs.send(SERVICE_ID, TEMPLATE_ID, {
      to_email,
      team_name,
      coach_name,
      registration_fee,
      payment_status,
    }, { publicKey: PUBLIC_KEY })
    return { sent: true, error: null }
  } catch (err) {
    console.error('[emailjs] send failed:', err)
    return { sent: false, error: err?.message || 'EmailJS send failed' }
  }
}
