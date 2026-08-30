import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { endpoints } from '../lib/api'

const tipOff = new Date('2026-09-19T13:00:00+08:00').getTime()

const C = {
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

const DISPLAY = { fontFamily: "'Anton', sans-serif", textTransform: 'uppercase', letterSpacing: '0.01em', lineHeight: 0.92 }
const MONO = { fontFamily: "'Share Tech Mono', monospace", letterSpacing: '0.08em' }

function Countdown() {
  useEffect(() => {
    function tick() {
      const dist = tipOff - Date.now()
      const d = document.getElementById('cd-d')
      const h = document.getElementById('cd-h')
      const m = document.getElementById('cd-m')
      if (!d || dist <= 0) return
      d.textContent = String(Math.floor(dist / 864e5)).padStart(2, '0')
      h.textContent = String(Math.floor((dist % 864e5) / 36e5)).padStart(2, '0')
      m.textContent = String(Math.floor((dist % 36e5) / 6e4)).padStart(2, '0')
    }
    tick()
    const id = setInterval(tick, 60000)
    return () => clearInterval(id)
  }, [])

  const unit = (id, label) => (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <span id={id}>00</span>
      <small style={{ display: 'block', fontSize: 9, color: C.dim, letterSpacing: '0.1em', marginTop: 2 }}>{label}</small>
    </div>
  )
  return (
    <div style={{ display: 'flex', gap: 14, ...MONO, color: C.blue }}>
      {unit('cd-d', 'DAYS')}
      {unit('cd-h', 'HRS')}
      {unit('cd-m', 'MIN')}
    </div>
  )
}

function CourtSVG() {
  return (
    <svg viewBox="0 0 300 300" style={{ width: '100%', height: '100%' }}>
      <rect x="10" y="10" width="280" height="280" fill="none" stroke="#2563EB" strokeWidth="2"/>
      <circle cx="150" cy="150" r="45" fill="none" stroke="#2563EB" strokeWidth="2"/>
      <line x1="10" y1="150" x2="290" y2="150" stroke="#2563EB" strokeWidth="2"/>
      <path d="M 10 90 A 100 100 0 0 1 10 210" fill="none" stroke="#FF6A2B" strokeWidth="2"/>
      <path d="M 290 90 A 100 100 0 0 0 290 210" fill="none" stroke="#FF6A2B" strokeWidth="2"/>
      <rect x="10" y="105" width="70" height="90" fill="none" stroke="#2563EB" strokeWidth="2"/>
      <rect x="220" y="105" width="70" height="90" fill="none" stroke="#2563EB" strokeWidth="2"/>
    </svg>
  )
}

function BallSVG() {
  return (
    <svg viewBox="0 0 200 200" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
      <circle cx="100" cy="100" r="90" fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="3"/>
      <path d="M 10 100 Q 50 60 100 100 Q 150 140 190 100" fill="none" stroke="rgba(255,255,255,0.3)" strokeWidth="2.5"/>
      <path d="M 100 10 Q 60 50 100 100 Q 140 150 100 190" fill="none" stroke="rgba(255,255,255,0.3)" strokeWidth="2.5"/>
    </svg>
  )
}

const KICKER = {
  display: 'flex', alignItems: 'center', gap: 14, fontSize: 12, letterSpacing: '0.22em',
  textTransform: 'uppercase', color: C.blue, fontWeight: 700, marginBottom: 20,
}
const HEAD = { ...DISPLAY, fontSize: 'clamp(34px,5.5vw,64px)', maxWidth: '14ch', marginBottom: 20 }
const SECT = { padding: 'clamp(70px,10vw,130px) clamp(20px,5vw,64px)', position: 'relative' }

export default function LandingPage() {
  const { data: schedule = [] } = useQuery({
    queryKey: ['public-matches'],
    queryFn: () => endpoints.matches.publicSchedule().then((r) => r.data),
    refetchInterval: 60000,
  })
  const { data: prizes = [] } = useQuery({
    queryKey: ['public-rewards'],
    queryFn: () => endpoints.settings.public().then((r) => r.data?.rewards ?? []),
  })
  const fmtTime = (t) => (t ? t.slice(0, 5) : '')
  const fmtDate = (d) => {
    if (!d) return ''
    const dt = new Date(`${d}T00:00:00`)
    const mon = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    return `${String(dt.getDate()).padStart(2, '0')} ${mon[dt.getMonth()]}`
  }
  const statusColor = (s) =>
    s === 'Scheduled' ? C.blue : (s === 'Completed' ? '#059669' : (s === 'In Progress' ? '#D97706' : C.dim))

  return (
    <div style={{ background: C.ink, color: C.chalk, fontFamily: "'Work Sans', sans-serif", overflowX: 'hidden' }}>
      <style>{`
        @media (max-width: 767px) {
          .lp-nav { display: none !important; }
          .lp-sched {
            grid-template-columns: 1fr !important;
            gap: 10px !important;
            align-items: start !important;
          }
        }
      `}</style>
      {/* NAV */}
      <header style={{ position: 'sticky', top: 0, zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '18px clamp(20px,5vw,64px)', background: 'rgba(255,255,255,0.86)', backdropFilter: 'blur(10px)', borderBottom: '1px solid #E7E4DC' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 34, height: 34, borderRadius: '50%', border: `2.5px solid ${C.blue}`, position: 'relative' }}>
            <div style={{ position: 'absolute', left: '50%', top: -1, bottom: -1, width: 2, background: C.blue, transform: 'translateX(-50%)' }} />
            <div style={{ position: 'absolute', top: '50%', left: -1, right: -1, height: 2, background: C.blue, transform: 'translateY(-50%)' }} />
          </div>
          <span style={{ fontFamily: "'Anton',sans-serif", letterSpacing: '0.04em', fontSize: 14, textTransform: 'uppercase' }}>Moonwalk Hardcourt</span>
        </div>
        <nav className="lp-nav" style={{ display: 'flex', gap: 'clamp(16px,3vw,34px)', fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>
          {[['#about', 'About'], ['#divisions', 'Divisions'], ['#prizes', 'Prizes'], ['#schedule', 'Schedule'], ['#venue', 'Venue']].map(([href, label]) => (
            <a key={href} href={href} style={{ textDecoration: 'none', color: C.dim }}>{label}</a>
          ))}
          <Link to="/pricing" style={{ textDecoration: 'none', color: C.dim }}>Pricing</Link>
        </nav>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <Link to="/login" style={{ textDecoration: 'none', color: C.dim, fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>Sign In</Link>
          <Link to="/register?next=/register-team" style={{ display: 'inline-flex', alignItems: 'center', padding: '11px 20px', background: C.blue, color: '#fff', fontWeight: 700, fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.06em', borderRadius: 2, textDecoration: 'none', border: '2px solid transparent' }}>Register</Link>
        </div>
      </header>

      {/* HERO */}
      <section style={{ position: 'relative', padding: 'clamp(48px,9vw,110px) clamp(20px,5vw,64px) 0', minHeight: '92vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', inset: 0, backgroundImage: `radial-gradient(circle at 50% 0%, transparent 0 118px, ${C.line} 118px 120px, transparent 120px), linear-gradient(${C.line} 1px, transparent 1px)`, backgroundSize: '100% 100%, 100% 120px', opacity: 0.2, pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', right: 'clamp(-60px,2vw,40px)', top: '50%', transform: 'translateY(-50%)', width: 'clamp(220px,32vw,460px)', height: 'clamp(220px,32vw,460px)', borderRadius: '50%', background: `radial-gradient(circle at 32% 28%, #4F81E8, ${C.blue} 55%, #1D4ED8 100%)`, boxShadow: '0 40px 90px -20px rgba(37,99,235,0.35)', opacity: 0.9 }}>
          <BallSVG />
        </div>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10, fontSize: 12, letterSpacing: '0.22em', textTransform: 'uppercase', color: C.blue, fontWeight: 700, marginBottom: 22 }}>
          <span style={{ width: 26, height: 2, background: C.blue, display: 'inline-block' }} />
          Barangay Moonwalk &middot; Para&ntilde;aque City
        </div>
        <h1 style={{ ...DISPLAY, fontSize: 'clamp(52px,10.5vw,148px)', color: C.chalk, maxWidth: '16ch' }}>
          Moonwalk<br /><span style={{ fontStyle: 'normal', color: C.blue, WebkitTextStroke: `2px ${C.blue}` }}>Hardcourt</span> Showdown
        </h1>
        <p style={{ marginTop: 26, maxWidth: 640, fontSize: 'clamp(16px,2vw,20px)', color: C.dim, lineHeight: 1.6 }}>
          Four divisions. One covered court. A full weekend of full-court runs, packed sidelines, and bragging rights that last until next season. Sign your barangay squad up before slots run out.
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, marginTop: 40 }}>
          <Link to="/register?next=/register-team" style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '16px 30px', fontWeight: 700, fontSize: 14, textTransform: 'uppercase', letterSpacing: '0.06em', borderRadius: 2, textDecoration: 'none', background: C.blue, color: '#fff', border: '2px solid transparent' }}>Register a Team</Link>
          <a href="#schedule" style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '16px 30px', fontWeight: 700, fontSize: 14, textTransform: 'uppercase', letterSpacing: '0.06em', borderRadius: 2, textDecoration: 'none', border: '2px solid #E7E4DC', color: C.chalk }}>See the Schedule</a>
        </div>

        {/* SCOREBOARD */}
        <div style={{ position: 'relative', zIndex: 2, margin: 'clamp(40px,7vw,70px) 0 0' }}>
          <div style={{ background: C.panel, border: '1px solid #E7E4DC', borderRadius: 6, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px,1fr))', overflow: 'hidden' }}>
            <div style={{ padding: '22px clamp(14px,2vw,28px)', borderRight: '1px solid #E7E4DC' }}>
              <div style={{ fontSize: 11, letterSpacing: '0.18em', textTransform: 'uppercase', color: C.dim, marginBottom: 10, fontWeight: 600 }}>Tip-off</div>
              <div style={{ ...MONO, fontSize: 'clamp(20px,3vw,32px)', color: C.blue }}>Sep 19, 2026</div>
            </div>
            <div style={{ padding: '22px clamp(14px,2vw,28px)', borderRight: '1px solid #E7E4DC' }}>
              <div style={{ fontSize: 11, letterSpacing: '0.18em', textTransform: 'uppercase', color: C.dim, marginBottom: 10, fontWeight: 600 }}>Venue</div>
              <div style={{ ...MONO, fontSize: 'clamp(15px,2vw,20px)', color: C.blue }}>Moonwalk Court</div>
            </div>
            <div style={{ padding: '22px clamp(14px,2vw,28px)', borderRight: '1px solid #E7E4DC' }}>
              <div style={{ fontSize: 11, letterSpacing: '0.18em', textTransform: 'uppercase', color: C.dim, marginBottom: 10, fontWeight: 600 }}>Divisions</div>
              <div style={{ ...MONO, fontSize: 'clamp(20px,3vw,32px)', color: C.blue }}>04</div>
            </div>
            <div style={{ padding: '22px clamp(14px,2vw,28px)' }}>
              <div style={{ fontSize: 11, letterSpacing: '0.18em', textTransform: 'uppercase', color: C.dim, marginBottom: 10, fontWeight: 600 }}>Countdown</div>
              <Countdown />
            </div>
          </div>
        </div>

        {/* Live matchups right under the scoreboard */}
        <div id="schedule" style={{ position: 'relative', zIndex: 2, margin: 'clamp(24px,5vw,40px) 0 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontSize: 11, letterSpacing: '0.2em', textTransform: 'uppercase', color: C.blue, fontWeight: 700, marginBottom: 14 }}>
            Upcoming &amp; Live Matchups<span style={{ flex: 1, height: 1, background: '#E7E4DC' }} />
          </div>
          <div style={{ background: C.panel, border: '1px solid #E7E4DC', borderRadius: 6, overflow: 'hidden' }}>
            {schedule.length === 0 ? (
              <div style={{ padding: '28px 22px', color: C.dim, fontSize: 16 }}>No matches are scheduled yet. Check back soon.</div>
            ) : (
              schedule.map((m, i) => (
                <div key={m.id || i} className="lp-sched" style={{ display: 'grid', gridTemplateColumns: '120px 1fr auto', gap: 18, alignItems: 'center', padding: '18px clamp(14px,2vw,22px)', borderBottom: i < schedule.length - 1 ? '1px solid #E7E4DC' : 'none' }}>
                  <div>
                    <span style={{ ...MONO, color: C.accent, fontSize: 14.5, display: 'block' }}>{fmtDate(m.scheduled_date)}</span>
                    {m.scheduled_time && <span style={{ ...MONO, color: C.blue, fontSize: 12.5 }}>{fmtTime(m.scheduled_time)}</span>}
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 17, fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {m.home_team} <span style={{ color: C.dim, fontWeight: 500 }}>vs</span> {m.away_team}
                    </div>
                    {(m.home_score != null || m.away_score != null) && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 5, flexWrap: 'wrap' }}>
                        <span style={{ ...MONO, color: C.blue, fontSize: 20, fontWeight: 700 }}>{m.home_score ?? 0} – {m.away_score ?? 0}</span>
                        {m.status === 'In Progress' && (m.minutes != null || m.seconds != null) && (
                          <span style={{ ...MONO, fontSize: 12, color: C.accent, border: '1px solid #E7E4DC', padding: '2px 7px', borderRadius: 100 }}>
                            Q{m.period ?? 1} · {String(m.minutes ?? 0).padStart(2, '0')}:{String(m.seconds ?? 0).padStart(2, '0')}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  <span style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.12em', color: statusColor(m.status), border: '1px solid #E7E4DC', padding: '5px 11px', borderRadius: 100, whiteSpace: 'nowrap' }}>
                    {m.status}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* PRIZES right under the schedule */}
        <div id="prizes" style={{ position: 'relative', zIndex: 2, margin: 'clamp(28px,5vw,48px) 0 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontSize: 11, letterSpacing: '0.2em', textTransform: 'uppercase', color: C.blue, fontWeight: 700, marginBottom: 14 }}>
            What Winners Take Home<span style={{ flex: 1, height: 1, background: '#E7E4DC' }} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px,1fr))', gap: 16 }}>
            {prizes.length === 0 ? (
              <div style={{ gridColumn: '1 / -1', background: C.panel, border: '1px solid #E7E4DC', borderRadius: 6, padding: '30px 26px', color: C.dim, fontSize: 15, textAlign: 'center' }}>Prize details will be announced closer to tip-off. Check back soon.</div>
            ) : (
              prizes.map((p, i) => (
                <div key={i} style={{ background: C.panel, border: `1px solid #E7E4DC`, borderTop: `3px solid ${i === 0 ? '#F59E0B' : (i === 1 ? '#94A3B8' : '#B45309')}`, borderRadius: 6, padding: '24px 22px', display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 8 }}>
                    <span style={{ ...DISPLAY, fontSize: 22 }}>{p.place || 'Place'}</span>
                    <span style={{ fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', color: C.dim, textAlign: 'right' }}>{p.division || 'Division'}</span>
                  </div>
                  <div style={{ ...MONO, fontSize: 17, color: C.blue, fontWeight: 700 }}>{p.prize || 'TBA'}</div>
                  {p.extra && <div style={{ fontSize: 13, color: C.dim, lineHeight: 1.6 }}>{p.extra}</div>}
                </div>
              ))
            )}
          </div>
        </div>
      </section>

      {/* ABOUT */}
      <section id="about" style={SECT}>
        <div style={KICKER}>The Event<span style={{ flex: 1, height: 1, background: '#E7E4DC' }} /></div>
        <h2 style={HEAD}>Built by the barangay, for the barangay.</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px,1fr))', gap: 'clamp(40px,6vw,80px)', marginTop: 56, alignItems: 'start' }}>
          <div>
            <p style={{ color: C.dim, fontSize: 16, lineHeight: 1.8, marginBottom: 18 }}><strong style={{ color: C.chalk }}>Moonwalk Hardcourt Showdown</strong> is Moonwalk's annual community basketball tournament, played entirely on the barangay covered court. It's where sitio teams, out-of-town alumni, and weekend warriors settle the year's biggest question: whose block runs it best.</p>
            <p style={{ color: C.dim, fontSize: 16, lineHeight: 1.8, marginBottom: 18 }}>Every game is played straight-up, no shortcuts &mdash; single-elimination brackets, real refs, and a scoreboard the whole street can see. Expect loud benches, longer overtimes than you'd like, and a trophy presentation that shuts the street down for an hour.</p>
          </div>
          <div style={{ display: 'grid', gap: 1, background: '#E7E4DC', border: '1px solid #E7E4DC', borderRadius: 4, overflow: 'hidden' }}>
            {[['16', 'Teams Expected'], ['04', 'Divisions'], ['02', 'Weekends of Play'], ['01', 'Covered Court, Full Capacity']].map(([n, l], i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', background: C.panel, padding: '20px 22px' }}>
                <span style={{ ...DISPLAY, fontSize: 30, color: C.accent }}>{n}</span>
                <span style={{ fontSize: 12, letterSpacing: '0.1em', textTransform: 'uppercase', color: C.dim, textAlign: 'right' }}>{l}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* DIVISIONS */}
      <section id="divisions" style={SECT}>
        <div style={KICKER}>Categories<span style={{ flex: 1, height: 1, background: '#E7E4DC' }} /></div>
        <h2 style={HEAD}>Pick your bracket.</h2>
        <p style={{ maxWidth: 600, color: C.dim, fontSize: 17, lineHeight: 1.7 }}>Four divisions, one covered court, every skill level welcome. Register under the bracket that fits your squad.</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px,1fr))', gap: 1, background: '#E7E4DC', border: '1px solid #E7E4DC', borderRadius: 4, overflow: 'hidden', marginTop: 56 }}>
          {[
            { num: '01', title: "Open Men's", desc: "No age cap, full-speed play. The tournament's marquee division and usually the loudest crowd." },
            { num: '02', title: "Women's Division", desc: "Open to all barangay women's squads. Fastest-growing bracket the past two seasons running." },
            { num: '03', title: '18-Under Juniors', desc: "For the block's next generation — high school and out-of-school youth teams." },
            { num: '04', title: '35+ Masters', desc: "Slower pace, sharper shooting. The vets' division, and often the closest games of the weekend." },
          ].map((d) => (
            <div key={d.num} style={{ background: C.panel, padding: '32px 26px', position: 'relative' }}>
              <span style={{ ...MONO, color: C.blue, fontSize: 13, marginBottom: 26, display: 'block' }}>{d.num}</span>
              <h3 style={{ ...DISPLAY, fontSize: 21, marginBottom: 10, letterSpacing: '0.02em' }}>{d.title}</h3>
              <p style={{ color: C.dim, fontSize: 13.5, lineHeight: 1.6 }}>{d.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* VENUE */}
      <section id="venue" style={SECT}>
        <div style={KICKER}>Venue<span style={{ flex: 1, height: 1, background: '#E7E4DC' }} /></div>
        <h2 style={HEAD}>Home court, home crowd.</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px,1fr))', gap: 'clamp(30px,5vw,60px)', marginTop: 50, alignItems: 'center' }}>
          <div style={{ border: '1px solid #E7E4DC', borderRadius: 6, padding: 36, background: 'linear-gradient(160deg, #FFFFFF, #FBFAF7)' }}>
            <div style={{ fontSize: 22, fontWeight: 700, marginBottom: 10 }}>Moonwalk Covered Court</div>
            <div style={{ color: C.dim, fontSize: 14, lineHeight: 1.6, marginBottom: 26 }}>Barangay Moonwalk, Para&ntilde;aque City — the same court that's hosted the showdown since day one. Bleacher seating, full lighting for night games, and standing room along both baselines.</div>
          </div>
          <div style={{ width: '100%', aspectRatio: '1/1', border: `2px solid ${C.line}`, borderRadius: 6, position: 'relative', background: C.court }}>
            <CourtSVG />
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ background: C.blue, color: '#fff', textAlign: 'center', padding: 'clamp(60px,9vw,110px) 24px', position: 'relative', overflow: 'hidden' }}>
        <h2 style={{ ...DISPLAY, fontSize: 'clamp(36px,7vw,84px)', maxWidth: '18ch', margin: '0 auto 24px' }}>Get your squad on the bracket.</h2>
        <p style={{ fontSize: 16, opacity: 0.9, maxWidth: 480, margin: '0 auto 34px' }}>Team registration closes September 12. Roster of 8–12 players, one team fee, all divisions welcome.</p>
        <Link to="/register?next=/register-team" style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '16px 30px', fontWeight: 700, fontSize: 14, textTransform: 'uppercase', letterSpacing: '0.06em', borderRadius: 2, textDecoration: 'none', background: '#fff', color: C.blue, border: '2px solid transparent' }}>Register Your Team</Link>
      </section>

      {/* FOOTER */}
      <footer style={{ padding: '40px clamp(20px,5vw,64px)', borderTop: '1px solid #E7E4DC', display: 'flex', flexWrap: 'wrap', gap: 16, justifyContent: 'space-between', alignItems: 'center', fontSize: 12, color: C.dim }}>
        <span>&copy; 2026 Moonwalk Hardcourt Showdown &middot; Barangay Moonwalk, Para&ntilde;aque City</span>
        <span>For inquiries, message the barangay sports committee.</span>
      </footer>
    </div>
  )
}
