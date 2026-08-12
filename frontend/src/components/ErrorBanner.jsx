export default function ErrorBanner({ error }) {
  if (!error) return null
  const detail = error?.response?.data?.detail || error?.message || 'Something went wrong.'
  return (
    <div className="mb-4 flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-sm text-rose-700">
      <i className="bi bi-exclamation-triangle mt-0.5" />
      <span>{typeof detail === 'string' ? detail : JSON.stringify(detail)}</span>
    </div>
  )
}
