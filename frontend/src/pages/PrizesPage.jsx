import { useQuery } from '@tanstack/react-query'
import { endpoints } from '../lib/api'

const MEDALS = ['🥇', '🥈', '🥉']
const PLACE_RANK = { champion: 0, '1st': 1, '2nd': 2, '3rd': 3, '4th': 4, '5th': 5, '6th': 6 }

export default function PrizesPage() {
  const { data = {} } = useQuery({
    queryKey: ['inapp-prizes'],
    queryFn: () => endpoints.settings.public().then((r) => r.data),
  })
  const rewards = data.rewards || []

  const byDivision = rewards.reduce((acc, r) => {
    const key = r.division || 'General'
    ;(acc[key] = acc[key] || []).push(r)
    return acc
  }, {})

  return (
    <div>
      <h1 className="text-xl font-bold mb-1">Prizes</h1>
      <p className="text-sm text-gray-500 mb-5">What the winners take home in each division.</p>

      {Object.keys(byDivision).length === 0 ? (
        <div className="card p-8 text-sm text-gray-500">Rewards are being finalized by the league administrator. Check back soon.</div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Object.entries(byDivision).map(([division, entries]) => (
            <div key={division} className="card overflow-hidden">
              <div className="px-4 py-3 bg-slate-900 text-white font-semibold text-sm">{division}</div>
              <div className="divide-y divide-gray-100">
                {entries
                  .slice()
                  .sort((a, b) => {
                    const ra = PLACE_RANK[a.place?.trim().toLowerCase()] ?? 99
                    const rb = PLACE_RANK[b.place?.trim().toLowerCase()] ?? 99
                    if (ra !== rb) return ra - rb
                    return a.place?.toLowerCase().localeCompare(b.place?.toLowerCase())
                  })
                  .map((e, i) => (
                    <div key={i} className="px-4 py-3 flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-blue-50 text-blue-700 flex items-center justify-center text-lg shrink-0">
                        {MEDALS[i] || '🏅'}
                      </div>
                      <div className="min-w-0">
                        <div className="text-sm font-semibold truncate">{e.prize || e.place || 'Prize'}</div>
                        <div className="text-xs text-gray-400 uppercase tracking-wide">{e.place || 'Win'}</div>
                        {e.incentive && <div className="text-xs text-gray-500">{e.incentive}</div>}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
