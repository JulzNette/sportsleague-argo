import { useQuery } from '@tanstack/react-query'
import { endpoints } from '../lib/api'
import {
  C, MONO, KICKER, HEAD, SECT, PublicHeader, Footer,
} from '../components/PublicKit'

const peso = (n) => (n == null ? null : `₱${Number(n).toLocaleString(undefined, { maximumFractionDigits: 2 })}`)

export default function PricingPage() {
  const { data = {} } = useQuery({
    queryKey: ['public-settings'],
    queryFn: () => endpoints.settings.public().then((r) => r.data),
  })
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

        <div style={{ marginTop: 14, display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center', background: C.blueDim, border: '1px solid #D5E2FB', borderRadius: 6, padding: '18px 22px' }}>
          <span style={{ fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.14em', color: C.blueDark, fontWeight: 700 }}>Current registration fee</span>
          <span style={{ ...MONO, fontSize: 26, fontWeight: 700, color: C.blueDark }}>{fee != null ? peso(fee) : '—'}</span>
          {fee == null && <span style={{ color: C.dim, fontSize: 13 }}>No fee set yet — check back soon.</span>}
        </div>
      </section>

      <Footer />
    </div>
  )
}
