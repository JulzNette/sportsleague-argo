import { useQuery } from '@tanstack/react-query'
import { endpoints } from '../lib/api'
import {
  C, DISPLAY, MONO, KICKER, HEAD, SECT, PublicHeader, Footer,
} from '../components/PublicKit'

const peso = (n) => (n == null ? null : `₱${Number(n).toLocaleString(undefined, { maximumFractionDigits: 2 })}`)

export default function PricingPage() {
  const { data = {} } = useQuery({
    queryKey: ['public-settings'],
    queryFn: () => endpoints.settings.public().then((r) => r.data),
  })
  const items = data.pricing || []
  const fee = data.registration_fee

  return (
    <div style={{ background: C.ink, color: C.chalk, fontFamily: "'Work Sans', sans-serif", overflowX: 'hidden' }}>
      <PublicHeader />

      {/* HERO */}
      <section style={{ ...SECT, paddingTop: 'clamp(70px,8vw,110px)' }}>
        <div style={KICKER}>Pricing<span style={{ flex: 1, height: 1, background: '#E7E4DC' }} /></div>
        <h1 style={HEAD}>One fee, the whole run.</h1>
        <p style={{ maxWidth: 620, color: C.dim, fontSize: 17, lineHeight: 1.7, marginBottom: 40 }}>
          The registration fee is set by the league administrator and covers everything your squad needs
          to play the full tournament.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px,1fr))', gap: 1, background: '#E7E4DC', border: '1px solid #E7E4DC', borderRadius: 6, overflow: 'hidden' }}>
          {items.length === 0 ? (
            <div style={{ background: C.panel, padding: '34px 26px', color: C.dim, fontSize: 14 }}>
              Fee &amp; pricing details are being finalized by the league administrator.
            </div>
          ) : (
            items.map((it, i) => (
              <div key={i} style={{ background: C.panel, padding: '30px 26px' }}>
                <div style={{ ...MONO, color: C.blue, fontSize: 13, marginBottom: 14 }}>
                  {String(i + 1).padStart(2, '0')}
                </div>
                <h3 style={{ ...DISPLAY, fontSize: 19, marginBottom: 8, letterSpacing: '0.02em' }}>{it.title || 'Registration'}</h3>
                {it.description && <p style={{ color: C.dim, fontSize: 14, lineHeight: 1.6, marginBottom: 14 }}>{it.description}</p>}
                {it.amount != null && (
                  <div style={{ ...MONO, color: C.accent, fontSize: 22, fontWeight: 700 }}>{peso(it.amount)}</div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Fee summary bar */}
        <div style={{ marginTop: 34, display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center', background: C.blueDim, border: '1px solid #D5E2FB', borderRadius: 6, padding: '18px 22px' }}>
          <span style={{ fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.14em', color: C.blueDark, fontWeight: 700 }}>Current registration fee</span>
          <span style={{ ...MONO, fontSize: 26, fontWeight: 700, color: C.blueDark }}>{fee != null ? peso(fee) : '—'}</span>
          {fee == null && <span style={{ color: C.dim, fontSize: 13 }}>No fee set yet — check back soon.</span>}
        </div>
      </section>

      <Footer />
    </div>
  )
}
