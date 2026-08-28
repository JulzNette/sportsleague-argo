import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { endpoints } from '../lib/api'
import { useAuthStore } from '../store/authStore'
import { can } from '../lib/permissions'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: 'bi-grid-1x2' },
  { to: '/leagues', label: 'Leagues', icon: 'bi-diagram-3', perms: ['league.view'] },
  { to: '/seasons', label: 'Seasons', icon: 'bi-calendar-range', perms: ['season.view'] },
  { to: '/divisions', label: 'Divisions', icon: 'bi-collection', perms: ['division.view'] },
  { to: '/teams', label: 'Teams', icon: 'bi-people', perms: ['team.view'] },
  { to: '/players', label: 'Players', icon: 'bi-person-badge', perms: ['player.view'] },
  { to: '/registrations', label: 'Registrations', icon: 'bi-clipboard-check', perms: ['registration.submit'] },
  { to: '/matches', label: 'Matches', icon: 'bi-controller', perms: ['match.view'] },
  { to: '/standings', label: 'Standings', icon: 'bi-bar-chart-steps', perms: ['standing.view'] },
  { to: '/statistics', label: 'Statistics', icon: 'bi-pie-chart', perms: ['standing.view'] },
  { to: '/referees', label: 'Referees', icon: 'bi-flag', perms: ['referee.manage'] },
  { to: '/reports', label: 'Reports', icon: 'bi-file-earmark-text', perms: ['report.view'] },
  { to: '/archive', label: 'Archive', icon: 'bi-archive', perms: ['league.update', 'team.delete'] },
]

export default function Layout({ children }) {
  const { role, email, logout } = useAuthStore()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [bellOpen, setBellOpen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const { data: notifications = [] } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => endpoints.notifications.list().then((r) => r.data),
    refetchInterval: 30000,
  })
  const { data: unread } = useQuery({
    queryKey: ['notifications-unread'],
    queryFn: () => endpoints.notifications.unreadCount().then((r) => r.data),
    refetchInterval: 30000,
  })
  const markReadMut = useMutation({
    mutationFn: (id) => endpoints.notifications.markRead(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
      qc.invalidateQueries({ queryKey: ['notifications-unread'] })
    },
  })
  const markAllMut = useMutation({
    mutationFn: () => endpoints.notifications.markAllRead(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
      qc.invalidateQueries({ queryKey: ['notifications-unread'] })
    },
  })

  function openNotification(n) {
    if (!n.is_read) markReadMut.mutate(n.id)
    setBellOpen(false)
    navigate(n.registration_id ? `/registrations?id=${n.registration_id}` : '/registrations')
  }

  function handleLogout() {
    logout()
    window.location.href = '/'
  }

  function closeSidebar() { setSidebarOpen(false) }

  const initials = (role || '?').split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase()

  const visibleNav = NAV.filter((item) => !item.perms || item.perms.some((p) => can(role, p)))

  return (
    <div className="flex min-h-screen">
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 bg-slate-900/50 lg:hidden" onClick={closeSidebar} />
      )}
      <aside className={`fixed top-0 bottom-0 left-0 z-50 w-60 shrink-0 bg-slate-900 text-white flex flex-col transition-transform duration-200 lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex items-center justify-between gap-2.5 px-4 py-4 border-b border-white/10">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-xs">SL</div>
            <div>
              <div className="font-semibold text-sm">Sports League</div>
              <div className="text-[11px] text-gray-400">ARGO Platform</div>
            </div>
          </div>
          <button onClick={closeSidebar} className="lg:hidden text-gray-400 hover:text-white" title="Close menu">
            <i className="bi bi-x-lg" />
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto px-2.5 py-3 space-y-0.5">
          {visibleNav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/dashboard'}
              onClick={closeSidebar}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-[13.5px] font-medium ${
                  isActive ? 'bg-slate-800 text-white' : 'text-gray-300 hover:bg-white/5 hover:text-white'
                }`
              }
            >
              <i className={`bi ${item.icon} text-base w-4 text-center`} />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-4 py-3 text-[11px] text-gray-500 border-t border-white/10">
          Sports League Management module
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0 lg:ml-60">
        <header className="h-16 bg-slate-900 text-white flex items-center justify-between gap-3 px-4 lg:px-5 sticky top-0 z-30">
          <div className="flex items-center gap-2 min-w-0">
            <button onClick={() => setSidebarOpen(true)} className="lg:hidden text-gray-300 hover:text-white" title="Open menu">
              <i className="bi bi-list text-xl" />
            </button>
          </div>
          <div className="flex items-center gap-3 sm:gap-3.5">
            <span className="hidden md:inline text-xs text-gray-300">Viewing as: <b className="text-white">{role}</b></span>
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold">
              {initials}
            </div>
            <div className="relative">
              <button onClick={() => setBellOpen((v) => !v)} className="relative text-gray-300 hover:text-white" title="Notifications">
                <i className="bi bi-bell text-lg" />
                {unread?.count > 0 && (
                  <span className="absolute -top-1.5 -right-2 min-w-4 h-4 px-1 rounded-full bg-rose-500 text-[10px] font-bold text-white flex items-center justify-center">
                    {unread.count}
                  </span>
                )}
              </button>
              {bellOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setBellOpen(false)} />
                  <div className="absolute right-0 top-9 z-50 w-[calc(100vw-2rem)] sm:w-80 max-h-96 overflow-y-auto card !p-0">
                    <div className="flex items-center justify-between px-4 py-2.5 border-b border-gray-200">
                      <span className="text-sm font-semibold text-gray-900">Notifications</span>
                      {unread?.count > 0 && (
                        <button className="text-xs text-blue-600 font-medium" onClick={() => markAllMut.mutate()}>Mark all read</button>
                      )}
                    </div>
                    {notifications.length === 0 ? (
                      <div className="p-6 text-center text-sm text-gray-400">No notifications yet.</div>
                    ) : (
                      <ul>
                        {notifications.map((n) => (
                          <li key={n.id}>
                            <button
                              onClick={() => openNotification(n)}
                              className={`w-full text-left px-4 py-2.5 border-b border-gray-100 last:border-0 hover:bg-gray-50 ${n.is_read ? '' : 'bg-blue-50/60'}`}
                            >
                              <div className="flex items-start justify-between gap-2">
                                <span className="text-sm font-medium text-gray-900">{n.title}</span>
                                {!n.is_read && <span className="w-2 h-2 rounded-full bg-blue-600 mt-1 shrink-0" />}
                              </div>
                              {n.message && <p className="text-xs text-gray-500 mt-0.5">{n.message}</p>}
                              <span className="text-[11px] text-gray-400 mt-1 block">{new Date(n.created_at).toLocaleString()}</span>
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </>
              )}
            </div>
            <button onClick={() => navigate('/settings')} title="Settings" className="text-gray-300 hover:text-white">
              <i className="bi bi-gear text-lg" />
            </button>
            <button onClick={handleLogout} title="Log out" className="text-gray-300 hover:text-white">
              <i className="bi bi-box-arrow-right text-lg" />
            </button>
          </div>
        </header>
        <main className="p-4 lg:p-6 flex-1 min-w-0">{children}</main>
      </div>
    </div>
  )
}
