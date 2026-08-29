import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { endpoints } from '../lib/api'
import { useAuthStore } from '../store/authStore'
import PageHead from '../components/PageHead'
import Kpi from '../components/Kpi'

const KPIS = [
  { key: 'leagues', label: 'Leagues', icon: 'bi-diagram-3', tint: 'blue' },
  { key: 'seasons', label: 'Seasons', icon: 'bi-calendar-range', tint: 'emerald' },
  { key: 'divisions', label: 'Divisions', icon: 'bi-collection', tint: 'slate' },
  { key: 'teams', label: 'Teams', icon: 'bi-people', tint: 'amber' },
  { key: 'players', label: 'Players', icon: 'bi-person-badge', tint: 'blue' },
  { key: 'coaches', label: 'Coaches', icon: 'bi-person-video3', tint: 'slate' },
  { key: 'referees', label: 'Referees', icon: 'bi-flag', tint: 'rose' },
  { key: 'matches', label: 'Matches', icon: 'bi-controller', tint: 'emerald' },
  { key: 'users', label: 'Users', icon: 'bi-people-fill', tint: 'rose' },
]

const QUICK_LINKS = [
  { to: '/users', label: 'User Management', icon: 'bi-people', desc: 'Create accounts, assign roles, reset passwords.' },
  { to: '/registrations', label: 'Registrations', icon: 'bi-clipboard-check', desc: 'Review and approve pending team registrations.' },
  { to: '/admin-settings', label: 'Admin Settings', icon: 'bi-gear', desc: 'Fees, division fee overrides, pricing/rewards, foul limit.' },
  { to: '/archive', label: 'Archive', icon: 'bi-archive', desc: 'Restore or permanently purge soft-deleted records.' },
]

export default function SuperadminPage() {
  const { role, email } = useAuthStore()
  const { data, isLoading } = useQuery({
    queryKey: ['superadmin-summary'],
    queryFn: () => endpoints.superadmin.summary().then((r) => r.data),
  })

  const counts = data?.counts || {}
  const registrations = data?.registrations || {}
  const usersByRole = data?.users_by_role || {}
  const roleKeys = Object.keys(usersByRole).sort()
  const maxRole = Math.max(1, ...roleKeys.map((k) => usersByRole[k]))
  const totalUsers = counts.users || 0

  const pipeline = [
    { key: 'pending', label: 'Pending', color: 'bg-amber-400', count: registrations.pending || 0 },
    { key: 'approved', label: 'Approved', color: 'bg-emerald-500', count: registrations.approved || 0 },
    { key: 'rejected', label: 'Rejected', color: 'bg-rose-500', count: registrations.rejected || 0 },
  ]
  const pipelineTotal = pipeline.reduce((s, p) => s + p.count, 0) || 1

  return (
    <div>
      <PageHead
        title="Superadmin Portal"
        subtitle={`Org-wide oversight — signed in as ${email} (${role})`}
      />

      {isLoading ? (
        <p className="text-sm text-gray-500">Loading...</p>
      ) : (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-9 gap-3.5 mb-6">
            {KPIS.map((kpi) => (
              <Kpi key={kpi.key} icon={kpi.icon} tint={kpi.tint} value={counts[kpi.key] ?? 0} label={kpi.label} />
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-3.5 mb-6">
            <div className="card">
              <div className="px-4 py-3 border-b border-gray-200">
                <h3 className="font-semibold text-sm text-gray-900">Registration pipeline</h3>
              </div>
              <div className="p-4">
                <div className="flex h-3 rounded-full overflow-hidden mb-4">
                  {pipeline.map((p) => (
                    <div key={p.key} className={p.color} style={{ width: `${(p.count / pipelineTotal) * 100}%` }} />
                  ))}
                </div>
                <ul className="space-y-2">
                  {pipeline.map((p) => (
                    <li key={p.key} className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2 text-gray-700">
                        <span className={`w-2.5 h-2.5 rounded-full ${p.color}`} />
                        {p.label}
                      </span>
                      <b className="text-gray-900">{p.count}</b>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="card lg:col-span-2">
              <div className="px-4 py-3 border-b border-gray-200">
                <h3 className="font-semibold text-sm text-gray-900">Users by role</h3>
              </div>
              <div className="p-4">
                {roleKeys.length === 0 ? (
                  <p className="text-sm text-gray-400 text-center py-4">No users yet.</p>
                ) : (
                  <div className="space-y-2.5">
                    {roleKeys.map((r) => (
                      <div key={r} className="flex items-center gap-3">
                        <span className="w-44 shrink-0 truncate text-sm text-gray-700 font-medium">{r}</span>
                        <div className="flex-1 h-5 rounded bg-gray-100 overflow-hidden">
                          <div className="h-full bg-blue-500 rounded" style={{ width: `${(usersByRole[r] / maxRole) * 100}%` }} />
                        </div>
                        <span className="w-8 shrink-0 text-sm text-gray-500 text-right">{usersByRole[r]}</span>
                      </div>
                    ))}
                  </div>
                )}
                <p className="text-xs text-gray-400 mt-4">{totalUsers} total account{totalUsers === 1 ? '' : 's'} in this organization.</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            {QUICK_LINKS.map((link) => (
              <Link key={link.to} to={link.to} className="card p-4 flex items-start gap-3 hover:border-blue-300 transition-colors">
                <div className="w-10 h-10 rounded-lg bg-gray-100 text-slate-700 flex items-center justify-center text-lg shrink-0">
                  <i className={`bi ${link.icon}`} />
                </div>
                <div>
                  <div className="font-semibold text-sm text-gray-900">{link.label}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{link.desc}</div>
                </div>
                <i className="bi bi-chevron-right ml-auto text-gray-300 mt-2" />
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
