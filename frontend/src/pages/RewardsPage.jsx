import { useQuery } from '@tanstack/react-query'
import { endpoints } from '../lib/api'
import { C, DISPLAY, MONO, KICKER, HEAD, SECT, PublicHeader, Footer } from '../components/PublicKit'

export default function RewardsPage() {
  const { data = {} } = useQuery({
    queryKey: ['public-settings'],
    queryFn: () => endpoints.settings.public().then((r) => r.data),
  })
  const rewards = data.rewards || []

  // Group reward entries by division so each division shows its own prize list.
  const byDivision = rewards.reduce((acc, r) => {
    const key = r.division || 'General'
    ;(acc[key] = acc[key] || []).push(r)
    return acc
  }, {})

  return (
    <div style={{ background: C.ink, color: C.chalk, fontFamily: "'Work Sans', sans-serif", overflowX: 'hidden' }}>
      <PublicHeader />

      <section style={{ ...SECT, paddingTop: 'clamp(70px,8vw,110px)' }}>
        <div style={KICKER}>Rewards<span style={{ flex: 1, height: 1, background: '#E7E4DC' }} /></div>
        <h1 style={HEAD}>Prizes are worth the run.</h1>
        <p style={{ maxWidth: 620, color: C.dim, fontSize: 17, lineHeight: 1.7, marginBottom: 40 }}>
          Every division plays for hardware, cash, and bragging rights. Here&apos;s what the winners bring home.
        </p>

        {Object.keys(byDivision).length === 0 ? (
          <div style={{ background: C.panel, border: '1px solid #E7E4DC', borderRadius: 6, padding: '40px 26px', color: C.dim, fontSize: 14 }}>
            Rewards are being finalized by the league administrator. Check back soon.
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(270px,1fr))', gap: 20 }}>
            {Object.entries(byDivision).map(([division, entries]) => (
              <div key={division} style={{ background: C.panel, border: '1px solid #E7E4DC', borderRadius: 6, overflow: 'hidden' }}>
                <div style={{ background: C.blue, color: '#fff', padding: '18px 22px' }}>
                  <div style={{ ...DISPLAY, fontSize: 18 }}>{division}</div>
                </div>
                <div style={{ display: 'grid', gap: 1, background: '#E7E4DC' }}>
                  {entries.map((e, i) => (
                    <div key={i} style={{ background: C.panel, padding: '16px 22px', display: 'flex', alignItems: 'center', gap: 14 }}>
                      <span style={{ ...MONO, color: C.accent, fontSize: 13, width: 58, textTransform: 'uppercase' }}>{e.place || 'Win'}</span>
                      <div style={{ fontSize: 14, lineHeight: 1.45 }}>
                        <div style={{ fontWeight: 700 }}>{e.prize || ''}</div>
                        {e.incentive && <div style={{ color: C.dim }}>{e.incentive}</div>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <Footer />
    </div>
  )
}
