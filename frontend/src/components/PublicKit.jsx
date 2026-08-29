import { Link } from 'react-router-dom'

export const C = {
  ink: '#FFFFFF',
  court: '#FBFAF7',
  panel: '#FFFFFF',
  line: '#E7E4DC',
  chalk: '#111827',
  dim: '#6B7280',
  blue: '#2563EB',
  blueDark: '#1D4ED8',
  blueDim: '#DBE7FE',
  accent: '#4F46E5',
}

export const DISPLAY = { fontFamily: "'Anton', sans-serif", textTransform: 'uppercase', letterSpacing: '0.01em', lineHeight: 0.92 }
export const MONO = { fontFamily: "'Share Tech Mono', monospace", letterSpacing: '0.08em' }
export const KICKER = {
  display: 'flex', alignItems: 'center', gap: 14, fontSize: 12, letterSpacing: '0.22em',
  textTransform: 'uppercase', color: C.blue, fontWeight: 700, marginBottom: 20,
}
export const HEAD = { ...DISPLAY, fontSize: 'clamp(34px,5.5vw,64px)', maxWidth: '14ch', marginBottom: 20 }
export const SECT = { padding: 'clamp(70px,10vw,130px) clamp(20px,5vw,64px)', position: 'relative' }

export const NAV_ANCHORS = [
  ['/pricing', 'Pricing'],
  ['/rewards', 'Rewards'],
  ['/#schedule', 'Schedule'],
]

function Logo() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div style={{ width: 34, height: 34, borderRadius: '50%', border: `2.5px solid ${C.blue}`, position: 'relative' }}>
        <div style={{ position: 'absolute', left: '50%', top: -1, bottom: -1, width: 2, background: C.blue, transform: 'translateX(-50%)' }} />
        <div style={{ position: 'absolute', top: '50%', left: -1, right: -1, height: 2, background: C.blue, transform: 'translateY(-50%)' }} />
      </div>
      <span style={{ fontFamily: "'Anton',sans-serif", letterSpacing: '0.04em', fontSize: 14, textTransform: 'uppercase' }}>Moonwalk Hardcourt</span>
    </div>
  )
}

export function PublicHeader() {
  return (
    <header style={{ position: 'sticky', top: 0, zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '18px clamp(20px,5vw,64px)', background: 'rgba(255,255,255,0.86)', backdropFilter: 'blur(10px)', borderBottom: '1px solid #E7E4DC' }}>
      <Link to="/" style={{ textDecoration: 'none', color: C.chalk }}><Logo /></Link>
      <nav className="lp-nav" style={{ display: 'flex', gap: 'clamp(16px,3vw,30px)', fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>
        {NAV_ANCHORS.map(([href, label]) => (
          <Link key={href} to={href} style={{ textDecoration: 'none', color: C.dim }}>{label}</Link>
        ))}
      </nav>
      <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
        <Link to="/login" style={{ textDecoration: 'none', color: C.dim, fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>Sign In</Link>
        <Link to="/register?next=/register-team" style={{ display: 'inline-flex', alignItems: 'center', padding: '11px 20px', background: C.blue, color: '#fff', fontWeight: 700, fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.06em', borderRadius: 2, textDecoration: 'none' }}>Register</Link>
      </div>
    </header>
  )
}

export function Footer() {
  return (
    <footer style={{ padding: '32px clamp(20px,5vw,64px)', borderTop: '1px solid #E7E4DC', display: 'flex', flexWrap: 'wrap', gap: 16, justifyContent: 'space-between', alignItems: 'center', color: C.dim, fontSize: 13 }}>
      <span>© {new Date().getFullYear()} Moonwalk Hardcourt Showdown</span>
      <div style={{ display: 'flex', gap: 20 }}>
        <Link to="/pricing" style={{ textDecoration: 'none', color: C.dim }}>Pricing</Link>
        <Link to="/rewards" style={{ textDecoration: 'none', color: C.dim }}>Rewards</Link>
        <Link to="/" style={{ textDecoration: 'none', color: C.dim }}>Home</Link>
      </div>
    </footer>
  )
}
