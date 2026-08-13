import { sportBadgeClass } from '../lib/sports'

export function SportBadge({ sport }) {
  return <span className={`badge ${sportBadgeClass(sport)}`}>{sport}</span>
}

export function SportFilter({ sports = [], value, onChange }) {
  return (
    <select className="input w-auto" value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="">All sports</option>
      {sports.map((s) => <option key={s} value={s}>{s}</option>)}
    </select>
  )
}
