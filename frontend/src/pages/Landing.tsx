// ══════════════════════════════════════════════════════════════
// frontend/src/pages/Landing.tsx
//
// Design brief executed here (see design-token rationale in
// tailwind.config.js): the hero opens with the single most
// characteristic interaction in the product — a patient describing
// symptoms in plain language and MediConnect responding with
// structured clinical guidance — rather than generic marketing
// copy over a stock photo. The signature element is a "pulse
// line" (an ECG-style trace) that runs through the hero and
// reappears as the section divider; it is grounded in the
// subject twice over, once as a literal nod to vitals/healthcare,
// and once as a quiet reference to the uptime/monitoring stack
// (Prometheus + Grafana) that is itself one of the system's
// real engineering features documented in Chapter Three.
// ══════════════════════════════════════════════════════════════
import { Link } from 'react-router-dom'
import {
  Stethoscope, MessageCircle, FileText, Pill, ShieldCheck,
  Clock, ArrowRight, Activity,
} from 'lucide-react'
import { PulseLogo } from '../components/layout/DashboardLayout'

export default function Landing() {
  return (
    <div className="min-h-screen bg-surface font-body text-ink">
      <NavBar />
      <Hero />
      <PulseDivider />
      <TrustStrip />
      <Features />
      <HowItWorks />
      <ClosingCTA />
      <Footer />
    </div>
  )
}

// ── Navigation ──────────────────────────────────────────────────
function NavBar() {
  return (
    <header className="sticky top-0 z-30 border-b border-border-soft/70 bg-surface/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5">
        <div className="flex items-center gap-2">
          <PulseLogo className="h-7 w-7 text-brand-teal" />
          <span className="font-display text-lg font-semibold text-brand-ink">MediConnect</span>
        </div>
        <nav className="flex items-center gap-3">
          <Link to="/login" className="font-body text-sm font-medium text-ink-soft hover:text-ink">
            Log in
          </Link>
          <Link to="/register" className="btn-primary !px-4 !py-2 text-sm">
            Get started
          </Link>
        </nav>
      </div>
    </header>
  )
}

// ── Hero ────────────────────────────────────────────────────────
function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div className="mx-auto grid max-w-6xl items-center gap-12 px-5 py-16 sm:py-24 lg:grid-cols-2">
        <div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-teal-tint px-3 py-1 font-mono text-xs font-medium text-brand-teal-deep">
            <Activity className="h-3 w-3" /> Built for Nigerian healthcare
          </span>
          <h1 className="mt-5 font-display text-4xl font-semibold leading-[1.1] tracking-tight text-brand-ink sm:text-5xl">
            Tell it what hurts.
            <br />
            Get a doctor, not a queue.
          </h1>
          <p className="mt-5 max-w-md font-body text-lg leading-relaxed text-ink-soft">
            MediConnect pairs an AI symptom checker with real appointment booking,
            electronic records, and live messaging — so the gap between
            "something's wrong" and "someone's looking after it" gets shorter.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link to="/register" className="btn-primary text-base">
              Create your account <ArrowRight className="h-4 w-4" />
            </Link>
            <Link to="/login" className="btn-secondary text-base">
              I already have one
            </Link>
          </div>
          <p className="mt-6 font-mono text-xs text-ink-faint">
            Nigeria's doctor-to-patient ratio sits near 1:2,500 — almost
            4× the WHO-recommended 1:600. MediConnect exists to make every one
            of those doctors reach further.
          </p>
        </div>

        {/* Signature interaction — a realistic symptom-check exchange,
            standing in for a screenshot. This is the product's
            actual hero feature rendered as itself, not a metaphor. */}
        <SymptomCheckDemo />
      </div>
    </section>
  )
}

function SymptomCheckDemo() {
  return (
    <div className="relative mx-auto w-full max-w-sm rounded-xl2 border border-border-soft bg-surface-raised p-1.5 shadow-card-hover">
      <div className="rounded-[1rem] bg-brand-ink p-4">
        <div className="flex items-center gap-2 px-1 pb-3">
          <Stethoscope className="h-4 w-4 text-brand-amber" />
          <span className="font-display text-sm font-medium text-white">AI Symptom Checker</span>
        </div>

        <div className="space-y-3">
          <div className="ml-auto max-w-[85%] rounded-2xl rounded-tr-sm bg-white/10 px-4 py-2.5 font-body text-sm text-white">
            Fever since yesterday, bad headache, and my joints ache.
          </div>

          <div className="max-w-[90%] rounded-2xl rounded-tl-sm bg-brand-teal-tint px-4 py-3">
            <p className="font-mono text-[11px] font-semibold uppercase tracking-wide text-brand-teal-deep">
              Possible · not a diagnosis
            </p>
            <ul className="mt-1.5 space-y-1 font-body text-sm text-ink">
              <li className="flex justify-between"><span>Malaria</span><span className="font-mono text-ink-faint">72%</span></li>
              <li className="flex justify-between"><span>Typhoid fever</span><span className="font-mono text-ink-faint">41%</span></li>
              <li className="flex justify-between"><span>Viral infection</span><span className="font-mono text-ink-faint">33%</span></li>
            </ul>
            <div className="mt-2.5 flex items-center justify-between rounded-lg bg-white px-3 py-2">
              <span className="font-body text-xs font-medium text-ink">Recommended: General Practitioner</span>
              <ArrowRight className="h-3.5 w-3.5 text-brand-teal" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Pulse divider — the recurring signature motif ────────────────
function PulseDivider() {
  return (
    <div className="relative h-12 w-full overflow-hidden">
      <svg viewBox="0 0 1200 48" preserveAspectRatio="none" className="h-full w-full" aria-hidden="true">
        <path
          d="M0 24 H420 L450 8 L478 40 L506 24 H560 L585 14 L610 34 L635 24 H1200"
          fill="none"
          stroke="#0F6F5C"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray="8 6"
          className="animate-pulseLine"
          opacity="0.35"
        />
      </svg>
    </div>
  )
}

// ── Trust strip ────────────────────────────────────────────────
function TrustStrip() {
  const stats = [
    { value: '< 500ms', label: 'median API response time' },
    { value: '99.5%', label: 'monthly uptime target' },
    { value: '24h + 2h', label: 'automatic SMS reminders' },
    { value: '4', label: 'roles, one platform' },
  ]
  return (
    <section className="border-y border-border-soft bg-surface-raised">
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-6 px-5 py-10 sm:grid-cols-4">
        {stats.map((s) => (
          <div key={s.label} className="text-center sm:text-left">
            <p className="font-display text-2xl font-semibold text-brand-teal-deep">{s.value}</p>
            <p className="mt-1 font-body text-xs text-ink-soft">{s.label}</p>
          </div>
        ))}
      </div>
    </section>
  )
}

// ── Feature cards ─────────────────────────────────────────────
function Features() {
  const items = [
    {
      icon: Stethoscope,
      title: 'AI symptom checker',
      body: 'Describe what you feel in your own words. Get likely conditions, an urgency level, and the right kind of specialist — every answer carries a clear disclaimer.',
    },
    {
      icon: MessageCircle,
      title: 'Real-time care',
      body: 'Message your doctor directly once you\u2019re booked. Read receipts and instant delivery, backed by an SMS nudge if you\u2019re offline.',
    },
    {
      icon: FileText,
      title: 'One record, always with you',
      body: 'Diagnoses, visit history, allergies, and current medication — kept in one place your doctor can open before you\u2019ve even sat down.',
    },
    {
      icon: Pill,
      title: 'Prescriptions that track themselves',
      body: 'Your doctor issues it, your pharmacist dispenses it, and you get a text either way. No lost paper scripts.',
    },
  ]
  return (
    <section className="mx-auto max-w-6xl px-5 py-20">
      <h2 className="font-display text-3xl font-semibold text-brand-ink">
        Everything a visit needs, before and after the room.
      </h2>
      <div className="mt-10 grid gap-5 sm:grid-cols-2">
        {items.map(({ icon: Icon, title, body }) => (
          <div key={title} className="card hover:shadow-card-hover transition-shadow">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-teal-tint">
              <Icon className="h-5 w-5 text-brand-teal-deep" strokeWidth={1.75} />
            </div>
            <h3 className="mt-4 font-display text-lg font-semibold text-ink">{title}</h3>
            <p className="mt-1.5 font-body text-sm leading-relaxed text-ink-soft">{body}</p>
          </div>
        ))}
      </div>
    </section>
  )
}

// ── How it works — a genuine sequence, so numbered steps earn their keep ──
function HowItWorks() {
  const steps = [
    { n: '01', title: 'Describe or search', body: 'Type your symptoms for an AI read, or search doctors directly by speciality.' },
    { n: '02', title: 'Pick a real slot', body: 'See live availability and book the exact time — no double-booking, ever.' },
    { n: '03', title: 'Show up informed', body: 'Reminders land by SMS and email at 24 hours and again at 2 hours out.' },
    { n: '04', title: 'Leave with a record', body: 'Notes, prescriptions, and follow-ups are saved the moment the visit ends.' },
  ]
  return (
    <section className="bg-brand-ink py-20">
      <div className="mx-auto max-w-6xl px-5">
        <h2 className="font-display text-3xl font-semibold text-white">From symptom to seen-to, in four steps.</h2>
        <div className="mt-10 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((s) => (
            <div key={s.n}>
              <span className="font-mono text-sm text-brand-amber">{s.n}</span>
              <h3 className="mt-2 font-display text-base font-semibold text-white">{s.title}</h3>
              <p className="mt-1.5 font-body text-sm leading-relaxed text-white/65">{s.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

// ── Closing CTA ────────────────────────────────────────────────
function ClosingCTA() {
  return (
    <section className="mx-auto max-w-6xl px-5 py-20 text-center">
      <ShieldCheck className="mx-auto h-9 w-9 text-brand-teal" strokeWidth={1.5} />
      <h2 className="mx-auto mt-4 max-w-xl font-display text-3xl font-semibold text-brand-ink">
        Your data, encrypted end to end — built to NDPR standards from day one.
      </h2>
      <div className="mt-8 flex items-center justify-center gap-3">
        <Link to="/register" className="btn-primary text-base">
          Create your free account
        </Link>
      </div>
    </section>
  )
}

// ── Footer ──────────────────────────────────────────────────────
function Footer() {
  return (
    <footer className="border-t border-border-soft py-8">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-5 font-mono text-xs text-ink-faint sm:flex-row">
        <span>© {new Date().getFullYear()} MediConnect — mediconnect.salman-aak.com</span>
        <div className="flex items-center gap-1.5">
          <Clock className="h-3 w-3" /> Lagos, Nigeria · WAT (UTC+1)
        </div>
      </div>
    </footer>
  )
}

