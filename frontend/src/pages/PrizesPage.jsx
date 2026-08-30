import { useQuery } from '@tanstack/react-query'
import { endpoints } from '../lib/api'

const PLACE_RANK = { champion: 0, '1st': 1, '2nd': 2, '3rd': 3, '4th': 4, '5th': 5, '6th': 6, '7th': 7, '8th': 8 }
const PLACE_LABEL = { champion: 'Champion', '1st': 'Runner-up', '2nd': 'Bronze', '3rd': '4th Place', '4th': '5th Place', '5th': '6th Place' }

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

  const sorted = (entries) => entries.slice().sort((a, b) => {
    const ra = PLACE_RANK[a.place?.trim().toLowerCase()] ?? 99
    const rb = PLACE_RANK[b.place?.trim().toLowerCase()] ?? 99
    if (ra !== rb) return ra - rb
    return a.place?.toLowerCase().localeCompare(b.place?.toLowerCase())
  })

  const isRanked = (e) => e.place?.trim() && PLACE_RANK[e.place.trim().toLowerCase()] != null
  const rankOf = (e) => (PLACE_RANK[e.place?.trim().toLowerCase()] ?? 98) + 1
  const labelOf = (e) => PLACE_LABEL[e.place?.trim().toLowerCase()] || e.place || 'Place'

  return (
    <div className="prz">
      <style>{`
        .prz .prz-head h1{ font-size:22px; font-weight:700; }
        .prz .prz-head p{ font-size:13.5px; color:var(--g500,#6B7280); margin-top:4px; }

        .prz .prz-div{ font-size:13px; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:#374151; margin:26px 0 14px; }

        .prz .prz-podium{
          display:grid; grid-template-columns:1fr 1fr 1fr; gap:14px; align-items:end; margin-bottom:22px;
        }
        .prz .prz-card{
          border-radius:14px; padding:20px 16px; text-align:center; position:relative;
          box-shadow:0 1px 2px rgba(15,23,42,0.04);
        }
        .prz .prz-first{ background:linear-gradient(160deg,#FFF8E8,#FFFBEB); border:1.5px solid #FDE68A; padding-top:28px; order:2; }
        .prz .prz-second{ background:linear-gradient(160deg,#F8FAFC,#F1F5F9); border:1.5px solid #E2E8F0; order:1; margin-top:22px; }
        .prz .prz-third{ background:linear-gradient(160deg,#FDF6F0,#FDF3EC); border:1.5px solid #F3DFCB; order:3; margin-top:32px; }

        .prz .prz-badge{
          width:40px; height:40px; border-radius:50%; display:flex; align-items:center; justify-content:center;
          font-size:17px; font-weight:800; color:#fff; margin:0 auto 12px;
          box-shadow:0 4px 10px -3px rgba(0,0,0,0.25);
        }
        .prz .prz-first .prz-badge{ background:linear-gradient(160deg,#FCD34D,#F59E0B); width:52px; height:52px; font-size:20px; }
        .prz .prz-second .prz-badge{ background:linear-gradient(160deg,#CBD5E1,#94A3B8); }
        .prz .prz-third .prz-badge{ background:linear-gradient(160deg,#D89A6A,#C2703D); }

        .prz .prz-place{ font-size:10.5px; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:#6B7280; margin-bottom:6px; }
        .prz .prz-main{ font-size:15px; font-weight:800; line-height:1.3; margin-bottom:4px; color:#111827; }
        .prz .prz-sub{ font-size:12.5px; color:#6B7280; }
        .prz .prz-first .prz-main{ font-size:17px; }
        .prz .prz-trophy{ position:absolute; top:8px; left:50%; transform:translateX(-50%); color:#F59E0B; font-size:18px; }

        .prz .prz-rest{ background:#fff; border:1px solid #E5E7EB; border-radius:14px; overflow:hidden; }
        .prz .prz-rest-row{ display:flex; align-items:center; gap:14px; padding:16px 18px; border-bottom:1px solid #F1F1F1; }
        .prz .prz-rest-row:last-child{ border-bottom:none; }
        .prz .prz-rest-rank{
          width:32px; height:32px; border-radius:8px; background:#E5E7EB; color:#6B7280;
          display:flex; align-items:center; justify-content:center; font-weight:700; font-size:13px; flex-shrink:0;
        }
        .prz .prz-rest-main{ font-weight:700; font-size:14px; color:#111827; }
        .prz .prz-rest-sub{ font-size:12px; color:#6B7280; margin-top:1px; }

        @media (max-width:560px){
          .prz .prz-podium{ grid-template-columns:1fr; }
          .prz .prz-first, .prz .prz-second, .prz .prz-third{ order:0; margin-top:0; }
        }
      `}</style>

      <div className="prz-head">
        <h1>Prizes</h1>
        <p>What the winners take home in each division.</p>
      </div>

      {Object.keys(byDivision).length === 0 ? (
        <div className="card p-8 text-sm text-gray-500">Rewards are being finalized by the league administrator. Check back soon.</div>
      ) : (
        Object.entries(byDivision).map(([division, entries]) => {
          const list = sorted(entries)
          const [first, second, third, ...rest] = list
          return (
            <div key={division}>
              <div className="prz-div">{division}</div>

              <div className="prz-podium">
                {second && (
                  <div className="prz-card prz-second">
                    <div className="prz-badge">{rankOf(second)}</div>
                    <div className="prz-place">{labelOf(second)}</div>
                    <div className="prz-main">{second.prize || 'Runner-up prize'}</div>
                    {second.incentive && <div className="prz-sub">{second.incentive}</div>}
                  </div>
                )}
                {first && (
                  <div className="prz-card prz-first">
                    <i className="bi bi-trophy-fill prz-trophy"></i>
                    <div className="prz-badge">{rankOf(first)}</div>
                    <div className="prz-place">{labelOf(first)}</div>
                    <div className="prz-main">{first.prize || 'Champion prize'}</div>
                    {first.incentive && <div className="prz-sub">{first.incentive}</div>}
                  </div>
                )}
                {third && (
                  <div className="prz-card prz-third">
                    <div className="prz-badge">{rankOf(third)}</div>
                    <div className="prz-place">{labelOf(third)}</div>
                    <div className="prz-main">{third.prize || '3rd place prize'}</div>
                    {third.incentive && <div className="prz-sub">{third.incentive}</div>}
                  </div>
                )}
              </div>

              {rest.length > 0 && (
                <div className="prz-rest">
                  {rest.map((e, i) => (
                    <div key={i} className="prz-rest-row">
                      <div className="prz-rest-rank">
                        {isRanked(e) ? rankOf(e) : <i className="bi bi-star-fill" style={{ fontSize: 13 }} />}
                      </div>
                      <div>
                        <div className="prz-rest-main">{[labelOf(e), e.prize].filter(Boolean).join(' — ') || 'Prize'}</div>
                        {e.incentive && <div className="prz-rest-sub">{e.incentive}</div>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })
      )}
    </div>
  )
}