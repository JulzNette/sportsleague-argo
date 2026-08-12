import { useQuery } from '@tanstack/react-query'
import { endpoints } from '../lib/api'
import { useAuthStore } from '../store/authStore'
import PageHead from '../components/PageHead'
import Kpi from '../components/Kpi'
import Badge from '../components/Badge'

export default function DashboardPage() {
  const { role, email } = useAuthStore()

  const { data: leagues } = useQuery({ queryKey: ['leagues'], queryFn: () => endpoints.leagues.list().then((r) => r.data) })
  const { data: seasons } = useQuery({ queryKey: ['seasons'], queryFn: () => endpoints.seasons.list().then((r) => r.data) })
  const { data: teams } = useQuery({ queryKey: ['teams'], queryFn: () => endpoints.teams.list().then((r) => r.data) })
  const { data: matches } = useQuery({ queryKey: ['matches'], queryFn: () => endpoints.matches.list().then((r) => r.data) })

  const upcoming = (matches || [])
    .filter((m) => m.status === 'Scheduled')
    .sort((a, b) => `${a.scheduled_date}${a.scheduled_time}`.localeCompare(`${b.scheduled_date}${b.scheduled_time}`))
    .slice(0, 6)

  const teamName = (id) => teams?.find((t) => t.id === id)?.name || '—'

  return (
    <div>
      <PageHead title="Dashboard" subtitle={`Signed in as ${email} — ${role}`} />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 mb-6">
        <Kpi icon="bi-diagram-3" tint="blue" value={leagues?.length ?? '—'} label="Leagues" />
        <Kpi icon="bi-calendar-range" tint="emerald" value={seasons?.length ?? '—'} label="Seasons" />
        <Kpi icon="bi-people" tint="amber" value={teams?.length ?? '—'} label="Teams" />
        <Kpi icon="bi-controller" tint="rose" value={matches?.length ?? '—'} label="Matches" />
      </div>

      <div className="card">
        <div className="px-4 py-3 border-b border-gray-200">
          <h3 className="font-semibold text-sm text-gray-900">Upcoming matches</h3>
        </div>
        {upcoming.length === 0 ? (
          <p className="p-6 text-sm text-gray-400 text-center">Nothing scheduled right now.</p>
        ) : (
          <table className="w-full text-sm">
            <tbody>
              {upcoming.map((m) => (
                <tr key={m.id} className="border-b border-gray-100 last:border-0">
                  <td className="px-4 py-2.5 font-semibold text-gray-900">{teamName(m.home_team_id)} vs {teamName(m.away_team_id)}</td>
                  <td className="px-4 py-2.5 text-gray-500">{m.scheduled_date} {m.scheduled_time}</td>
                  <td className="px-4 py-2.5 text-gray-500">{m.venue}</td>
                  <td className="px-4 py-2.5"><Badge status={m.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
