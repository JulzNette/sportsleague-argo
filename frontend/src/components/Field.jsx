export default function Field({ label, children }) {
  return (
    <div className="mb-3">
      <label className="label">{label}</label>
      {children}
    </div>
  )
}
