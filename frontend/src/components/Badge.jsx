import { STATUS_COLOR } from '../lib/statusMachines'

export default function Badge({ status }) {
  const color = STATUS_COLOR[status] || 'neutral'
  return <span className={`badge badge-${color}`}>{status}</span>
}
