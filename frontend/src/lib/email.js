/**
 * EmailJS delivery for the Sports League module.
 *
 * The ONLY emailed message is the registration-fee reminder, sent to the Team
 * Manager when an admin clicks "Email registrant". It sends directly from the
 * browser via EmailJS, so no SMTP/domain verification is needed and the
 * manager receives it for real. If EmailJS isn't configured (dev without env
 * vars) this logs instead of failing, so the feature never breaks the host
 * flow that triggered it.
 */
import emailjs from '@emailjs/browser'

const SERVICE_ID = import.meta.env.VITE_EMAILJS_SERVICE_ID
const TEMPLATE_ID = import.meta.env.VITE_EMAILJS_TEMPLATE_ID_FEE
const PUBLIC_KEY = import.meta.env.VITE_EMAILJS_PUBLIC_KEY

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

  if (!SERVICE_ID || !PUBLIC_KEY || !TEMPLATE_ID) {
    console.info('[emailjs] fee template not configured — would send:', variables)
    return { sent: false, error: 'EmailJS not configured' }
  }
  try {
    await emailjs.send(SERVICE_ID, TEMPLATE_ID, variables, { publicKey: PUBLIC_KEY })
    return { sent: true, error: null }
  } catch (err) {
    console.error('[emailjs] fee reminder send failed:', err)
    return { sent: false, error: err?.message || 'EmailJS send failed' }
  }
}
