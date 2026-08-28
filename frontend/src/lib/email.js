/**
 * EmailJS delivery for the Sports League module.
 *
 * Emails are sent directly from the browser via EmailJS, so no SMTP/domain
 * verification is needed and recipients receive mail for real. Each message
 * type maps to an EmailJS template (created in the EmailJS dashboard) and is
 * configured through VITE_EMAILJS_TEMPLATE_ID_* env vars. If a template isn't
 * configured (dev without env vars) these log instead of failing, so the
 * feature never breaks the host flow that triggered it.
 */
import emailjs from '@emailjs/browser'

const SERVICE_ID = import.meta.env.VITE_EMAILJS_SERVICE_ID
const PUBLIC_KEY = import.meta.env.VITE_EMAILJS_PUBLIC_KEY

// Template IDs for each message type.
const T_ACK = import.meta.env.VITE_EMAILJS_TEMPLATE_ID_ACK
const T_APPROVED = import.meta.env.VITE_EMAILJS_TEMPLATE_ID_APPROVED
const T_PAYMENT = import.meta.env.VITE_EMAILJS_TEMPLATE_ID_PAYMENT
const T_FEE = import.meta.env.VITE_EMAILJS_TEMPLATE_ID_FEE

/**
 * Generic sender. Returns {sent, error} so callers can decide how to surface
 * failures. Never throws.
 */
async function sendTemplate(templateId, label, variables) {
  if (!SERVICE_ID || !PUBLIC_KEY || !templateId) {
    console.info(`[emailjs] ${label} template not configured — would send:`, variables)
    return { sent: false, error: `${label} template not configured` }
  }
  try {
    await emailjs.send(SERVICE_ID, templateId, variables, { publicKey: PUBLIC_KEY })
    return { sent: true, error: null }
  } catch (err) {
    console.error(`[emailjs] ${label} send failed:`, err)
    return { sent: false, error: err?.message || `${label} send failed` }
  }
}

/** Registration received — wait for approval. */
export function sendRegistrationAck(r) {
  return sendTemplate(T_ACK, 'registration ack', {
    to_email: r?.to_email || r?.contact_email,
    team_name: r?.team_name,
    coach_name: r?.coach_name,
    registration_fee: r?.registration_fee,
    payment_status: r?.payment_status,
  })
}

/** Registration approved. */
export function sendRegistrationApproved(r, review_comment) {
  return sendTemplate(T_APPROVED, 'approval', {
    to_email: r?.contact_email,
    team_name: r?.team_name,
    coach_name: r?.coach_name,
    review_comment: review_comment || '',
  })
}

/** Payment received. */
export function sendPaymentReceived(r) {
  return sendTemplate(T_PAYMENT, 'payment received', {
    to_email: r?.contact_email,
    team_name: r?.team_name,
    coach_name: r?.coach_name,
    registration_fee: r?.registration_fee,
    payment_status: r?.payment_status,
  })
}

/** Payment required / fee reminder (manual "email registrant" button). */
export function sendFeeReminder(r) {
  return sendTemplate(T_FEE, 'fee reminder', {
    to_email: r?.contact_email,
    team_name: r?.team_name,
    coach_name: r?.coach_name,
    registration_fee: r?.registration_fee,
    payment_status: r?.payment_status,
    registration_status: r?.status,
  })
}
