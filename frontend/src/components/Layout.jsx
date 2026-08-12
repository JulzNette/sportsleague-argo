import { NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

const NAV = [
  { to: '/', label: 'Dashboard', icon: 'bi-grid-1x2' },
  { to: '/leagues', label: 'Leagues', icon: 'bi-diagram-3' },
  { to: '/seasons', label: 'Seasons', icon: 'bi-calendar-range' },
  { to: '/divisions', label: 'Divisions', icon: 'bi-collection' },
  { to: '/teams', label: 'Teams', icon: 'bi-people' },
  { to: '/players', label: 'Players', icon: 'bi-person-badge' },
  { to: '/matches', label: 'Matches', icon: 'bi-controller' },
  { to: '/standings', label: 'Standings', icon: 'bi-bar-chart-steps' },
  { to: '/referees', label: 'Referees', icon: 'bi-flag' },
  { to: '/reports', label: 'Reports', icon: 'bi-file-earmark-text' },
]

export default function Layout({ children }) {
  const { role, email, logout } = useAuthStore()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  const initials = (role || '?').split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase()

  return (
    <div className="flex min-h-screen">
      <aside className="w-60 shrink-0 bg-slate-900 text-white flex flex-col fixed top-0 bottom-0 left-0">
        <div className="flex items-center gap-2.5 px-4 py-4 border-b border-white/10">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-xs">SL</div>
          <div>
            <div className="font-semibold text-sm">Sports League</div>
            <div className="text-[11px] text-gray-400">ARGO Platform</div>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto px-2.5 py-3 space-y-0.5">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
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

      <div className="flex-1 flex flex-col ml-60 min-w-0">
        <header className="h-16 bg-slate-900 text-white flex items-center justify-between px-5 sticky top-0 z-30">
          <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-full pl-1.5 pr-3 py-1 text-sm font-semibold">
            <span className="w-5 h-5 rounded-full bg-violet-700 flex items-center justify-center text-[10px]">O</span>
            Metro Manila Sports League
          </div>
          <div className="flex items-center gap-3.5">
            <span className="text-xs text-gray-300">Viewing as: <b className="text-white">{role}</b></span>
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold">
              {initials}
            </div>
            <button onClick={handleLogout} title="Log out" className="text-gray-300 hover:text-white">
              <i className="bi bi-box-arrow-right text-lg" />
            </button>
          </div>
        </header>
        <main className="p-6 flex-1 min-w-0">{children}</main>
      </div>
    </div>
  )
}
