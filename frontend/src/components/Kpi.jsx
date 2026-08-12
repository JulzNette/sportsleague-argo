export default function Kpi({ icon, tint, value, label }) {
  const tints = {
    blue: 'bg-blue-50 text-blue-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    amber: 'bg-amber-50 text-amber-600',
    rose: 'bg-rose-50 text-rose-600',
    slate: 'bg-gray-100 text-slate-700',
  }
  return (
    <div className="card p-4 flex items-start gap-3">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg ${tints[tint] || tints.slate}`}>
        <i className={`bi ${icon}`} />
      </div>
      <div>
        <div className="text-xl font-bold text-gray-900 leading-tight">{value}</div>
        <div className="text-xs text-gray-500 mt-0.5">{label}</div>
      </div>
    </div>
  )
}
