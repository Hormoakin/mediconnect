// ══════════════════════════════════════════════════════════════
// frontend/src/pages/patient/PatientDashboard.tsx
// ══════════════════════════════════════════════════════════════
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Calendar, Stethoscope, FileText, Pill, ArrowRight, Clock } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { api } from '../../services/api'
import type { Appointment } from '../../types/appointment'
import type { Prescription } from '../../types/prescription'
import StatusBadge from '../../components/common/StatusBadge'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import EmptyState from '../../components/common/EmptyState'
import { format } from 'date-fns'

export default function PatientDashboard() {
  const { user } = useAuth()
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/appointments/?ordering=-scheduled_at').then(r => r.data.results ?? r.data),
      api.get('/prescriptions/').then(r => r.data.results ?? r.data),
    ])
      .then(([appts, rxs]) => { setAppointments(appts.slice(0, 3)); setPrescriptions(rxs.slice(0, 3)) })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center pt-20"><LoadingSpinner size="lg" /></div>

  const upcoming = appointments.filter(a => a.is_upcoming)

  return (
    <div className="space-y-6">
      {/* Greeting */}
      <div>
        <h1 className="font-display text-2xl font-semibold text-ink">
          Good day, {user?.full_name?.split(' ')[0]} 👋
        </h1>
        <p className="mt-1 font-body text-sm text-ink-soft">
          {upcoming.length > 0
            ? `You have ${upcoming.length} upcoming appointment${upcoming.length > 1 ? 's' : ''}.`
            : 'No upcoming appointments. Book one when you\'re ready.'}
        </p>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { to: '/symptom-checker', icon: Stethoscope, label: 'Check symptoms', color: 'bg-brand-teal-tint text-brand-teal-deep' },
          { to: '/doctors',         icon: Calendar,    label: 'Book appointment', color: 'bg-brand-amber-tint text-amber-800' },
          { to: '/records',         icon: FileText,    label: 'Medical records',  color: 'bg-blue-50 text-blue-700' },
          { to: '/prescriptions',   icon: Pill,        label: 'Prescriptions',    color: 'bg-purple-50 text-purple-700' },
        ].map(({ to, icon: Icon, label, color }) => (
          <Link key={to} to={to}
            className="card flex flex-col items-start gap-3 hover:shadow-card-hover transition-shadow">
            <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${color}`}>
              <Icon className="h-4.5 w-4.5" strokeWidth={1.75} />
            </div>
            <span className="font-body text-sm font-medium text-ink">{label}</span>
          </Link>
        ))}
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        {/* Upcoming appointments */}
        <section className="card">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-display text-base font-semibold text-ink">Upcoming Appointments</h2>
            <Link to="/dashboard?tab=appointments" className="flex items-center gap-1 font-body text-xs font-medium text-brand-teal hover:underline">
              View all <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          {appointments.length === 0
            ? <EmptyState icon={Calendar} title="No appointments yet" description="Find a doctor and book your first appointment." action={{ label: 'Find a doctor', onClick: () => {} }} />
            : (
              <ul className="space-y-3">
                {appointments.map(appt => (
                  <li key={appt.id} className="flex items-start justify-between rounded-lg bg-surface p-3">
                    <div>
                      <p className="font-body text-sm font-medium text-ink">Dr. {appt.doctor_name}</p>
                      <p className="font-body text-xs text-ink-soft">{appt.doctor_speciality}</p>
                      <div className="mt-1.5 flex items-center gap-1.5 font-mono text-xs text-ink-faint">
                        <Clock className="h-3 w-3" />
                        {format(new Date(appt.scheduled_at), 'EEE d MMM · h:mm a')}
                      </div>
                    </div>
                    <StatusBadge status={appt.status} />
                  </li>
                ))}
              </ul>
            )}
        </section>

        {/* Recent prescriptions */}
        <section className="card">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-display text-base font-semibold text-ink">Recent Prescriptions</h2>
            <Link to="/prescriptions" className="flex items-center gap-1 font-body text-xs font-medium text-brand-teal hover:underline">
              View all <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          {prescriptions.length === 0
            ? <EmptyState icon={Pill} title="No prescriptions" description="Your prescriptions from doctors will appear here." />
            : (
              <ul className="space-y-3">
                {prescriptions.map(rx => (
                  <li key={rx.id} className="flex items-start justify-between rounded-lg bg-surface p-3">
                    <div>
                      <p className="font-body text-sm font-medium text-ink">{rx.medication}</p>
                      <p className="font-body text-xs text-ink-soft">{rx.dosage} · {rx.frequency} · {rx.duration_days} days</p>
                    </div>
                    <StatusBadge status={rx.status} />
                  </li>
                ))}
              </ul>
            )}
        </section>
      </div>
    </div>
  )
}
