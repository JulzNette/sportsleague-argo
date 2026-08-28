import { useEffect } from 'react'
import { Link } from 'react-router-dom'

const tipOff = new Date('2026-09-19T13:00:00+08:00').getTime()

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

  return (
    <div className="sb-value mono" id="countdown" style={{ display: 'flex', gap: '14px' }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <span id="cd-d">00</span>
        <small style={{ display: 'block', fontSize: '9px', color: 'var(--chalk-dim)', letterSpacing: '0.1em', marginTop: '2px' }}>DAYS</small>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <span id="cd-h">00</span>
        <small style={{ display: 'block', fontSize: '9px', color: 'var(--chalk-dim)', letterSpacing: '0.1em', marginTop: '2px' }}>HRS</small>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <span id="cd-m">00</span>
        <small style={{ display: 'block', fontSize: '9px', color: 'var(--chalk-dim)', letterSpacing: '0.1em', marginTop: '2px' }}>MIN</small>
      </div>
    </div>
  )
}

function CourtSVG() {
  return (
    <svg viewBox="0 0 300 300">
      <rect x="10" y="10" width="280" height="280" fill="none" stroke="#2A3040" strokeWidth="2"/>
      <circle cx="150" cy="150" r="45" fill="none" stroke="#2A3040" strokeWidth="2"/>
      <line x1="10" y1="150" x2="290" y2="150" stroke="#2A3040" strokeWidth="2"/>
      <path d="M 10 90 A 100 100 0 0 1 10 210" fill="none" stroke="#FF6A2B" strokeWidth="2"/>
      <path d="M 290 90 A 100 100 0 0 0 290 210" fill="none" stroke="#FF6A2B" strokeWidth="2"/>
      <rect x="10" y="105" width="70" height="90" fill="none" stroke="#2A3040" strokeWidth="2"/>
      <rect x="220" y="105" width="70" height="90" fill="none" stroke="#2A3040" strokeWidth="2"/>
    </svg>
  )
}

function BallSVG() {
  return (
    <svg viewBox="0 0 200 200" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
      <circle cx="100" cy="100" r="90" fill="none" stroke="rgba(0,0,0,0.15)" strokeWidth="3"/>
      <path d="M 10 100 Q 50 60 100 100 Q 150 140 190 100" fill="none" stroke="rgba(0,0,0,0.12)" strokeWidth="2.5"/>
      <path d="M 100 10 Q 60 50 100 100 Q 140 150 100 190" fill="none" stroke="rgba(0,0,0,0.12)" strokeWidth="2.5"/>
    </svg>
  )
}

export default function LandingPage() {
  return (
    <div style={{ background: 'var(--ink)', color: 'var(--chalk)', fontFamily: "'Work Sans', sans-serif", overflowX: 'hidden' }}>
      {/* NAV */}
      <header style={{ position: 'sticky', top: 0, zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '18px clamp(20px,5vw,64px)', background: 'rgba(11,14,20,0.82)', backdropFilter: 'blur(10px)', borderBottom: '1px solid var(--line)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: 34, height: 34, borderRadius: '50%', border: '2.5px solid var(--orange)', position: 'relative' }}>
            <div style={{ position: 'absolute', left: '50%', top: -1, bottom: -1, width: 2, background: 'var(--orange)', transform: 'translateX(-50%)' }} />
            <div style={{ position: 'absolute', top: '50%', left: -1, right: -1, height: 2, background: 'var(--orange)', transform: 'translateY(-50%)' }} />
          </div>
          <span style={{ fontFamily: "'Anton',sans-serif", letterSpacing: '0.04em', fontSize: 14, textTransform: 'uppercase' }}>Moonwalk Hardcourt</span>
        </div>
        <nav style={{ display: 'flex', gap: 'clamp(16px,3vw,34px)', fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>
          <a href="#about" style={{ textDecoration: 'none', color: 'var(--chalk-dim)', transition: 'color .2s' }}>About</a>
          <a href="#divisions" style={{ textDecoration: 'none', color: 'var(--chalk-dim)', transition: 'color .2s' }}>Divisions</a>
          <a href="#schedule" style={{ textDecoration: 'none', color: 'var(--chalk-dim)', transition: 'color .2s' }}>Schedule</a>
          <a href="#venue" style={{ textDecoration: 'none', color: 'var(--chalk-dim)', transition: 'color .2s' }}>Venue</a>
        </nav>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <Link to="/login" style={{ textDecoration: 'none', color: 'var(--chalk-dim)', fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>Sign In</Link>
          <Link to="/register?next=/register-team" style={{ display: 'inline-flex', alignItems: 'center', padding: '11px 20px', background: 'var(--orange)', color: 'var(--ink)', fontWeight: 700, fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.06em', borderRadius: 2, textDecoration: 'none', border: '2px solid transparent', transition: 'transform .18s ease, background .18s ease' }}>Register</Link>
        </div>
      </header>

      {/* HERO */}
      <section style={{ position: 'relative', padding: 'clamp(48px,9vw,110px) clamp(20px,5vw,64px) 0', minHeight: '92vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', inset: 0, backgroundImage: 'radial-gradient(circle at 50% 0%, transparent 0 118px, var(--line) 118px 120px, transparent 120px), linear-gradient(var(--line) 1px, transparent 1px)', backgroundSize: '100% 100%, 100% 120px', opacity: 0.35, pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', right: 'clamp(-60px,2vw,40px)', top: '50%', transform: 'translateY(-50%)', width: 'clamp(220px,32vw,460px)', height: 'clamp(220px,32vw,460px)', borderRadius: '50%', background: 'radial-gradient(circle at 32% 28%, #ff8a52, var(--orange) 55%, #b6440f 100%)', boxShadow: '0 40px 90px -20px rgba(255,106,43,0.35)', opacity: 0.9 }}>
          <BallSVG />
        </div>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10, fontSize: 12, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'var(--volt)', fontWeight: 700, marginBottom: 22 }}>
          <span style={{ width: 26, height: 2, background: 'var(--volt)', display: 'inline-block' }} />
          Barangay Moonwalk &middot; Para&ntilde;aque City
        </div>
        <h1 style={{ fontFamily: "'Anton', sans-serif", textTransform: 'uppercase', letterSpacing: '0.01em', lineHeight: 0.92, fontSize: 'clamp(52px,10.5vw,148px)', color: 'var(--chalk)', maxWidth: '16ch' }}>
          Moonwalk<br /><span style={{ fontStyle: 'normal', color: 'var(--orange)', WebkitTextStroke: '2px var(--orange)' }}>Hardcourt</span> Showdown
        </h1>
        <p style={{ marginTop: 26, maxWidth: 640, fontSize: 'clamp(16px,2vw,20px)', color: 'var(--chalk-dim)', lineHeight: 1.6 }}>
          Four divisions. One covered court. A full weekend of full-court runs, packed sidelines, and bragging rights that last until next season. Sign your barangay squad up before slots run out.
        </p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, marginTop: 40 }}>
          <Link to="/register?next=/register-team" style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '16px 30px', fontWeight: 700, fontSize: 14, textTransform: 'uppercase', letterSpacing: '0.06em', borderRadius: 2, textDecoration: 'none', background: 'var(--orange)', color: 'var(--ink)', border: '2px solid transparent', transition: 'transform .18s ease, background .18s ease' }}>Register a Team</Link>
          <a href="#schedule" style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '16px 30px', fontWeight: 700, fontSize: 14, textTransform: 'uppercase', letterSpacing: '0.06em', borderRadius: 2, textDecoration: 'none', border: '2px solid var(--line)', color: 'var(--chalk)', transition: 'transform .18s ease, border-color .18s ease' }}>See the Schedule</a>
        </div>

        {/* SCOREBOARD */}
        <div style={{ position: 'relative', zIndex: 2, margin: 'clamp(40px,7vw,70px) 0 0' }}>
          <div style={{ background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: 6, display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', overflow: 'hidden' }}>
            <div style={{ padding: '22px clamp(14px,2vw,28px)', borderRight: '1px solid var(--line)' }}>
              <div style={{ fontSize: 11, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--chalk-dim)', marginBottom: 10, fontWeight: 600 }}>Tip-off</div>
              <div className="mono" style={{ fontSize: 'clamp(20px,3vw,32px)', color: 'var(--volt)', letterSpacing: '0.03em' }}>Sep 19, 2026</div>
            </div>
            <div style={{ padding: '22px clamp(14px,2vw,28px)', borderRight: '1px solid var(--line)' }}>
              <div style={{ fontSize: 11, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--chalk-dim)', marginBottom: 10, fontWeight: 600 }}>Venue</div>
              <div className="mono" style={{ fontSize: 'clamp(15px,2vw,20px)', color: 'var(--volt)', letterSpacing: '0.03em' }}>Moonwalk Court</div>
            </div>
            <div style={{ padding: '22px clamp(14px,2vw,28px)', borderRight: '1px solid var(--line)' }}>
              <div style={{ fontSize: 11, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--chalk-dim)', marginBottom: 10, fontWeight: 600 }}>Divisions</div>
              <div className="mono" style={{ fontSize: 'clamp(20px,3vw,32px)', color: 'var(--volt)', letterSpacing: '0.03em' }}>04</div>
            </div>
            <div style={{ padding: '22px clamp(14px,2vw,28px)' }}>
              <div style={{ fontSize: 11, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--chalk-dim)', marginBottom: 10, fontWeight: 600 }}>Countdown</div>
              <Countdown />
            </div>
          </div>
        </div>
      </section>

      {/* ABOUT */}
      <section id="about" style={{ padding: 'clamp(70px,10vw,130px) clamp(20px,5vw,64px)', position: 'relative' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontSize: 12, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'var(--orange)', fontWeight: 700, marginBottom: 20 }}>
          The Event
          <span style={{ flex: 1, height: 1, background: 'var(--line)' }} />
        </div>
        <h2 style={{ fontFamily: "'Anton', sans-serif", textTransform: 'uppercase', letterSpacing: '0.01em', lineHeight: 0.92, fontSize: 'clamp(34px,5.5vw,64px)', maxWidth: '14ch', marginBottom: 20 }}>Built by the barangay, for the barangay.</h2>
        <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 0.9fr', gap: 'clamp(40px,6vw,80px)', marginTop: 56, alignItems: 'start' }}>
          <div>
            <p style={{ color: 'var(--chalk-dim)', fontSize: 16, lineHeight: 1.8, marginBottom: 18 }}><strong style={{ color: 'var(--chalk)' }}>Moonwalk Hardcourt Showdown</strong> is Moonwalk's annual community basketball tournament, played entirely on the barangay covered court. It's where sitio teams, out-of-town alumni, and weekend warriors settle the year's biggest question: whose block runs it best.</p>
            <p style={{ color: 'var(--chalk-dim)', fontSize: 16, lineHeight: 1.8, marginBottom: 18 }}>Every game is played straight-up, no shortcuts &mdash; single-elimination brackets, real refs, and a scoreboard the whole street can see. Expect loud benches, longer overtimes than you'd like, and a trophy presentation that shuts the street down for an hour.</p>
          </div>
          <div style={{ display: 'grid', gap: 1, background: 'var(--line)', border: '1px solid var(--line)', borderRadius: 4, overflow: 'hidden' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', background: 'var(--panel)', padding: '20px 22px' }}><span style={{ fontFamily: "'Anton',sans-serif", fontSize: 30, color: 'var(--volt)' }}>16</span><span style={{ fontSize: 12, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--chalk-dim)', textAlign: 'right' }}>Teams Expected</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', background: 'var(--panel)', padding: '20px 22px' }}><span style={{ fontFamily: "'Anton',sans-serif", fontSize: 30, color: 'var(--volt)' }}>04</span><span style={{ fontSize: 12, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--chalk-dim)', textAlign: 'right' }}>Divisions</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', background: 'var(--panel)', padding: '20px 22px' }}><span style={{ fontFamily: "'Anton',sans-serif", fontSize: 30, color: 'var(--volt)' }}>02</span><span style={{ fontSize: 12, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--chalk-dim)', textAlign: 'right' }}>Weekends of Play</span></div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', background: 'var(--panel)', padding: '20px 22px' }}><span style={{ fontFamily: "'Anton',sans-serif", fontSize: 30, color: 'var(--volt)' }}>01</span><span style={{ fontSize: 12, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--chalk-dim)', textAlign: 'right' }}>Covered Court, Full Capacity</span></div>
          </div>
        </div>
      </section>

      {/* DIVISIONS */}
      <section id="divisions" style={{ padding: 'clamp(70px,10vw,130px) clamp(20px,5vw,64px)', position: 'relative' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontSize: 12, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'var(--orange)', fontWeight: 700, marginBottom: 20 }}>
          Categories
          <span style={{ flex: 1, height: 1, background: 'var(--line)' }} />
        </div>
        <h2 style={{ fontFamily: "'Anton', sans-serif", textTransform: 'uppercase', letterSpacing: '0.01em', lineHeight: 0.92, fontSize: 'clamp(34px,5.5vw,64px)', maxWidth: '14ch', marginBottom: 20 }}>Pick your bracket.</h2>
        <p style={{ maxWidth: 600, color: 'var(--chalk-dim)', fontSize: 17, lineHeight: 1.7 }}>Four divisions, one covered court, every skill level welcome. Register under the bracket that fits your squad.</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 1, background: 'var(--line)', border: '1px solid var(--line)', borderRadius: 4, overflow: 'hidden', marginTop: 56 }}>
          {[
            { num: '01', title: "Open Men's", desc: "No age cap, full-speed play. The tournament's marquee division and usually the loudest crowd." },
            { num: '02', title: "Women's Division", desc: "Open to all barangay women's squads. Fastest-growing bracket the past two seasons running." },
            { num: '03', title: '18-Under Juniors', desc: "For the block's next generation — high school and out-of-school youth teams." },
            { num: '04', title: '35+ Masters', desc: "Slower pace, sharper shooting. The vets' division, and often the closest games of the weekend." },
          ].map((d) => (
            <div key={d.num} style={{ background: 'var(--panel)', padding: '32px 26px', position: 'relative' }}>
              <span className="mono" style={{ color: 'var(--orange)', fontSize: 13, marginBottom: 26, display: 'block' }}>{d.num}</span>
              <h3 style={{ fontFamily: "'Anton',sans-serif", textTransform: 'uppercase', fontSize: 21, marginBottom: 10, letterSpacing: '0.02em' }}>{d.title}</h3>
              <p style={{ color: 'var(--chalk-dim)', fontSize: 13.5, lineHeight: 1.6 }}>{d.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* SCHEDULE */}
      <section id="schedule" style={{ padding: 'clamp(70px,10vw,130px) clamp(20px,5vw,64px)', position: 'relative' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontSize: 12, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'var(--orange)', fontWeight: 700, marginBottom: 20 }}>
          Schedule
          <span style={{ flex: 1, height: 1, background: 'var(--line)' }} />
        </div>
        <h2 style={{ fontFamily: "'Anton', sans-serif", textTransform: 'uppercase', letterSpacing: '0.01em', lineHeight: 0.92, fontSize: 'clamp(34px,5.5vw,64px)', maxWidth: '14ch', marginBottom: 20 }}>Two weekends. One champion per bracket.</h2>
        <div style={{ marginTop: 50, borderTop: '1px solid var(--line)' }}>
          {[
            { day: 'SEP 19', title: "Group Stage — Open Men's & Women's", tag: 'Sat, 1PM' },
            { day: 'SEP 20', title: 'Group Stage — 18-Under & 35+ Masters', tag: 'Sun, 1PM' },
            { day: 'SEP 26', title: 'Quarterfinals & Semifinals, All Divisions', tag: 'Sat, 12PM' },
            { day: 'SEP 27', title: 'Finals & Awarding Night', tag: 'Sun, 3PM' },
          ].map((s) => (
            <div key={s.day} style={{ display: 'grid', gridTemplateColumns: '120px 1fr auto', gap: 24, alignItems: 'center', padding: '22px 0', borderBottom: '1px solid var(--line)' }}>
              <span className="mono" style={{ color: 'var(--volt)', fontSize: 14 }}>{s.day}</span>
              <h4 style={{ fontSize: 17, fontWeight: 700 }}>{s.title}</h4>
              <span style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--orange)', border: '1px solid var(--orange-dim)', padding: '6px 12px', borderRadius: 100, whiteSpace: 'nowrap' }}>{s.tag}</span>
            </div>
          ))}
        </div>
      </section>

      {/* VENUE */}
      <section id="venue" style={{ padding: 'clamp(70px,10vw,130px) clamp(20px,5vw,64px)', position: 'relative' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontSize: 12, letterSpacing: '0.22em', textTransform: 'uppercase', color: 'var(--orange)', fontWeight: 700, marginBottom: 20 }}>
          Venue
          <span style={{ flex: 1, height: 1, background: 'var(--line)' }} />
        </div>
        <h2 style={{ fontFamily: "'Anton', sans-serif", textTransform: 'uppercase', letterSpacing: '0.01em', lineHeight: 0.92, fontSize: 'clamp(34px,5.5vw,64px)', maxWidth: '14ch', marginBottom: 20 }}>Home court, home crowd.</h2>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'clamp(30px,5vw,60px)', marginTop: 50, alignItems: 'center' }}>
          <div style={{ border: '1px solid var(--line)', borderRadius: 6, padding: 36, background: 'linear-gradient(160deg, var(--panel), var(--court))' }}>
            <div style={{ fontSize: 22, fontWeight: 700, marginBottom: 10 }}>Moonwalk Covered Court</div>
            <div style={{ color: 'var(--chalk-dim)', fontSize: 14, lineHeight: 1.6, marginBottom: 26 }}>Barangay Moonwalk, Para&ntilde;aque City — the same court that's hosted the showdown since day one. Bleacher seating, full lighting for night games, and standing room along both baselines.</div>
          </div>
          <div style={{ width: '100%', aspectRatio: '1/1', border: '2px solid var(--line)', borderRadius: 6, position: 'relative', background: 'var(--court)' }}>
            <CourtSVG />
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ background: 'var(--orange)', color: 'var(--ink)', textAlign: 'center', padding: 'clamp(60px,9vw,110px) 24px', position: 'relative', overflow: 'hidden' }}>
        <h2 style={{ fontFamily: "'Anton', sans-serif", textTransform: 'uppercase', letterSpacing: '0.01em', lineHeight: 0.92, fontSize: 'clamp(36px,7vw,84px)', maxWidth: '18ch', margin: '0 auto 24px' }}>Get your squad on the bracket.</h2>
        <p style={{ fontSize: 16, opacity: 0.85, maxWidth: 480, margin: '0 auto 34px' }}>Team registration closes September 12. Roster of 8–12 players, one team fee, all divisions welcome.</p>
        <Link to="/register?next=/register-team" style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '16px 30px', fontWeight: 700, fontSize: 14, textTransform: 'uppercase', letterSpacing: '0.06em', borderRadius: 2, textDecoration: 'none', background: 'var(--ink)', color: 'var(--chalk)', border: '2px solid transparent', transition: 'transform .18s ease, background .18s ease' }}>Register Your Team</Link>
      </section>

      {/* FOOTER */}
      <footer style={{ padding: '40px clamp(20px,5vw,64px)', borderTop: '1px solid var(--line)', display: 'flex', flexWrap: 'wrap', gap: 16, justifyContent: 'space-between', alignItems: 'center', fontSize: 12, color: 'var(--chalk-dim)' }}>
        <span>&copy; 2026 Moonwalk Hardcourt Showdown &middot; Barangay Moonwalk, Para&ntilde;aque City</span>
        <span>For inquiries, message the barangay sports committee.</span>
      </footer>
    </div>
  )
}
