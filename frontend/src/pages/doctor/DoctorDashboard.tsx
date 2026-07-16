// ══════════════════════════════════════════════════════════════
// frontend/src/pages/doctor/DoctorDashboard.tsx
// ══════════════════════════════════════════════════════════════
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Calendar, Users, Pill, CheckCircle2, Clock, ArrowRight } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { api } from '../../services/api'
import type { Appointment } from '../../types/appointment'
import StatusBadge from '../../components/common/StatusBadge'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import EmptyState from '../../components/common/EmptyState'
import { format, isToday } from 'date-fns'

export default function DoctorDashboard() {
  const { user } = useAuth()
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/appointments/?ordering=scheduled_at')
      .then(r => setAppointments(r.data.results ?? r.data))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center pt-20"><LoadingSpinner size="lg" /></div>

  const todayAppts  = appointments.filter(a => isToday(new Date(a.scheduled_at)))
  const upcoming    = appointments.filter(a => a.is_upcoming)
  const completed   = appointments.filter(a => a.status === 'completed').length

  const updateStatus = async (id: number, status: string) => {
    await api.patch(`/appointments/${id}/`, { status })
    setAppointments(prev => prev.map(a => a.id === id ? { ...a, status: status as any } : a))
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-ink">
          Dr. {user?.full_name?.split(' ').slice(-1)[0]}'s Dashboard
        </h1>
        <p className="mt-1 font-body text-sm text-ink-soft">
          {todayAppts.length} appointment{todayAppts.length !== 1 ? 's' : ''} today
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { icon: Calendar, label: "Today's appointments", value: todayAppts.length, color: 'text-brand-teal' },
          { icon: Users,    label: 'Upcoming total',        value: upcoming.length,   color: 'text-brand-amber' },
          { icon: CheckCircle2, label: 'Completed',         value: completed,          color: 'text-emerald-600' },
        ].map(({ icon: Icon, label, value, color }) => (
          <div key={label} className="card text-center">
            <Icon className={`mx-auto h-5 w-5 ${color}`} strokeWidth={1.75} />
            <p className={`mt-2 font-display text-2xl font-semibold ${color}`}>{value}</p>
            <p className="mt-0.5 font-body text-xs text-ink-soft">{label}</p>
          </div>
        ))}
      </div>

      {/* Today's appointments */}
      <section className="card">
        <h2 className="mb-4 font-display text-base font-semibold text-ink">Today's Schedule</h2>
        {todayAppts.length === 0
          ? <EmptyState icon={Calendar} title="No appointments today" description="Your schedule is clear for today." />
          : (
            <ul className="divide-y divide-border-soft">
              {todayAppts.map(appt => (
                <li key={appt.id} className="flex items-start justify-between py-3">
                  <div>
                    <p className="font-body text-sm font-medium text-ink">{appt.patient_name}</p>
                    <div className="mt-0.5 flex items-center gap-1.5 font-mono text-xs text-ink-faint">
                      <Clock className="h-3 w-3" />
                      {format(new Date(appt.scheduled_at), 'h:mm a')} · {appt.duration_mins} min
                    </div>
                    {appt.reason && <p className="mt-1 font-body text-xs text-ink-soft">{appt.reason}</p>}
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <StatusBadge status={appt.status} />
                    <div className="flex gap-1.5">
                      {appt.status === 'pending' && (
                        <button onClick={() => updateStatus(appt.id, 'confirmed')} className="btn-primary !py-1 !px-2.5 text-xs">
                          Confirm
                        </button>
                      )}
                      {appt.status === 'confirmed' && (
                        <>
                          <button onClick={() => updateStatus(appt.id, 'completed')} className="btn-primary !py-1 !px-2.5 text-xs">
                            Complete
                          </button>
                          <button onClick={() => updateStatus(appt.id, 'no_show')} className="btn-secondary !py-1 !px-2.5 text-xs">
                            No-show
                          </button>
                        </>
                      )}
                    </div>
                    <Link to={`/chat/${appt.patient}`} className="flex items-center gap-1 font-body text-xs text-brand-teal hover:underline">
                      Message patient <ArrowRight className="h-3 w-3" />
                    </Link>
                  </div>
                </li>
              ))}
            </ul>
          )}
      </section>
    </div>
  )
}
