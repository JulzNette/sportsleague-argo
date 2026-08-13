export default function ErrorBanner({ error }) {
  if (!error) return null
  const detail = error?.response?.data?.detail || error?.message || 'Something went wrong.'
  const messages = Array.isArray(detail) ? detail : [detail]
  return (
    <div className="mb-4 flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-sm text-rose-700">
      <i className="bi bi-exclamation-triangle mt-0.5" />
      <ul className="space-y-1">
        {messages.map((msg, i) => (
          <li key={i}>{typeof msg === 'string' ? msg : JSON.stringify(msg)}</li>
        ))}
      </ul>
    </div>
  )
}
