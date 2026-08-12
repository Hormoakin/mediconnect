// ══════════════════════════════════════════════════════════════
// frontend/src/pages/receptionist/ReceptionistDashboard.tsx
// ══════════════════════════════════════════════════════════════
import { useState, useEffect, useCallback } from 'react'
import { Search, CalendarPlus, Users, Clock, Phone, CheckCircle } from 'lucide-react'
import { api } from '../../services/api'
import LoadingSpinner from '../../components/common/LoadingSpinner'

interface Stats {
  appointments_today: number
  pending_today: number
  confirmed_today: number
  completed_today: number
  total_patients: number
  booked_on_behalf: number
}

interface Patient {
  id: number
  full_name: string
  email: string
  phone: string
}

interface Doctor {
  id: number
  user_full_name: string
  speciality: string
  hospital_name: string
  rating: string
  consultation_fee: string
  is_available: boolean
}

interface Appointment {
  id: number
  patient_name: string
  doctor_name: string
  scheduled_at: string
  status: string
}

export default function ReceptionistDashboard() {
  const [stats, setStats]               = useState<Stats | null>(null)
  const [tab, setTab]                   = useState<'overview' | 'book' | 'schedule' | 'patient'>('overview')
  const [loading, setLoading]           = useState(true)

  // Patient search
  const [patientQuery, setPatientQuery] = useState('')
  const [patients, setPatients]         = useState<Patient[]>([])
  const [searchingPatients, setSearchingPatients] = useState(false)
  const [selectedPatient, setSelectedPatient]     = useState<Patient | null>(null)

  // Doctor selection
  const [doctors, setDoctors]           = useState<Doctor[]>([])
  const [specialityFilter, setSpecialityFilter]   = useState('')
  const [selectedDoctor, setSelectedDoctor]       = useState<Doctor | null>(null)

  // Booking
  const [scheduledAt, setScheduledAt]  = useState('')
  const [reason, setReason]            = useState('')
  const [notes, setNotes]              = useState('')
  const [booking, setBooking]          = useState(false)
  const [bookingSuccess, setBookingSuccess] = useState('')

  // Schedule
  const [schedule, setSchedule]        = useState<Appointment[]>([])

  // New patient form
  const [newPatient, setNewPatient]     = useState({ full_name: '', email: '', phone: '' })
  const [creatingPatient, setCreatingPatient] = useState(false)
  const [createSuccess, setCreateSuccess]     = useState('')

  const fetchStats = useCallback(async () => {
    try {
      const { data } = await api.get('/receptionist/stats/')
      setStats(data)
    } catch {
      setStats(null)
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchDoctors = async (speciality = '') => {
    try {
      const { data } = await api.get('/receptionist/doctors/available/', {
        params: speciality ? { speciality } : {}
      })
      setDoctors(data.doctors || [])
    } catch {
      setDoctors([])
    }
  }

  const fetchSchedule = async () => {
    try {
      const { data } = await api.get('/receptionist/schedule/today/')
      setSchedule(data.appointments || [])
    } catch {
      setSchedule([])
    }
  }

  const searchPatients = useCallback(async () => {
    if (!patientQuery.trim()) {
      setPatients([])
      return
    }

    setSearchingPatients(true)

    try {
      const { data } = await api.get('/receptionist/patients/search/', {
        params: { q: patientQuery }
      })
      setPatients(data.results || [])
    } catch {
      setPatients([])
    } finally {
      setSearchingPatients(false)
    }
  }, [patientQuery])

  useEffect(() => {
    fetchStats()
    fetchDoctors(specialityFilter)
    fetchSchedule()
  }, [fetchStats, specialityFilter])

  const bookAppointment = async () => {
    if (!selectedPatient || !selectedDoctor || !scheduledAt) return
    setBooking(true)
    try {
      const { data } = await api.post('/receptionist/appointments/book/', {
        patient_id:          selectedPatient.id,
        doctor_id:           selectedDoctor.id,
        scheduled_at:        scheduledAt,
        reason:              reason || 'Walk-in/phone booking via receptionist',
        receptionist_notes:  notes,
      })
      setBookingSuccess(`Appointment booked for ${selectedPatient.full_name} with Dr. ${selectedDoctor.user_full_name}`)
      setSelectedPatient(null); setSelectedDoctor(null); setScheduledAt(''); setReason(''); setNotes('')
      fetchStats(); fetchSchedule()
    } catch (err: any) {
      alert(err?.response?.data?.message || 'Booking failed. Please try again.')
    } finally { setBooking(false) }
  }

  const createWalkInPatient = async () => {
    if (!newPatient.full_name || !newPatient.email) return
    setCreatingPatient(true)
    try {
      const { data } = await api.post('/receptionist/patients/create/', { ...newPatient, role: 'patient' })
      setCreateSuccess(`Patient account created for ${newPatient.full_name}. Password setup email sent.`)
      setSelectedPatient(data.patient)
      setNewPatient({ full_name: '', email: '', phone: '' })
      setTab('book')
    } catch (err: any) {
      alert(err?.response?.data?.message || 'Failed to create patient.')
    } finally { setCreatingPatient(false) }
  }

  const statItems = stats ? [
    { label: "Today's Appointments", value: stats.appointments_today, color: 'text-teal-700', icon: Clock },
    { label: 'Pending',              value: stats.pending_today,       color: 'text-amber-600', icon: Clock },
    { label: 'Confirmed',            value: stats.confirmed_today,     color: 'text-blue-600',  icon: CheckCircle },
    { label: 'Booked by You Today',  value: stats.booked_on_behalf,    color: 'text-purple-600',icon: CalendarPlus },
  ] : []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-ink">Receptionist Dashboard</h1>
        <p className="mt-1 font-body text-sm text-ink-soft">
          Book appointments, register walk-in patients, and manage the front desk.
        </p>
      </div>

      {/* Stats Row */}
      {loading ? <LoadingSpinner /> : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {statItems.map((item) => (
            <div key={item.label} className="card">
              <item.icon className={`h-5 w-5 ${item.color} mb-2`} />
              <p className={`font-display text-3xl font-semibold ${item.color}`}>{item.value}</p>
              <p className="font-body text-sm text-ink-soft">{item.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-border-soft">
        {(['overview', 'book', 'patient', 'schedule'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 font-body text-sm capitalize transition-colors
              ${tab === t ? 'border-b-2 border-teal-700 text-teal-700 font-semibold' : 'text-ink-soft hover:text-ink'}`}>
            {t === 'book' ? 'Book Appointment' : t === 'patient' ? 'New Patient' : t === 'schedule' ? "Today's Schedule" : 'Overview'}
          </button>
        ))}
      </div>

      {/* OVERVIEW TAB */}
      {tab === 'overview' && (
        <div className="card">
          <h2 className="font-display text-base font-semibold text-ink mb-4">Quick Actions</h2>
          <div className="grid gap-3 sm:grid-cols-3">
            <button onClick={() => setTab('book')} className="btn-primary flex items-center gap-2 justify-center">
              <CalendarPlus className="h-4 w-4" /> Book Appointment
            </button>
            <button onClick={() => setTab('patient')} className="btn-secondary flex items-center gap-2 justify-center">
              <Users className="h-4 w-4" /> Register Walk-in Patient
            </button>
            <button onClick={() => setTab('schedule')} className="btn-secondary flex items-center gap-2 justify-center">
              <Clock className="h-4 w-4" /> View Today's Schedule
            </button>
          </div>
        </div>
      )}

      {/* BOOK APPOINTMENT TAB */}
      {tab === 'book' && (
        <div className="space-y-5">
          {bookingSuccess && (
            <div className="rounded-xl border border-green-200 bg-green-50 p-4 font-body text-sm text-green-700">
              ✅ {bookingSuccess}
            </div>
          )}

          {/* Step 1 — Find Patient */}
          <div className="card space-y-3">
            <h2 className="font-display text-base font-semibold text-ink">Step 1 — Find Patient</h2>
            {selectedPatient ? (
              <div className="flex items-center justify-between rounded-lg bg-teal-50 px-4 py-3">
                <div>
                  <p className="font-body text-sm font-semibold text-teal-800">{selectedPatient.full_name}</p>
                  <p className="font-body text-xs text-teal-600">{selectedPatient.email} · {selectedPatient.phone}</p>
                </div>
                <button onClick={() => setSelectedPatient(null)} className="font-body text-xs text-teal-700 underline">Change</button>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex gap-2">
                  <input className="input-field flex-1" placeholder="Search by name, email..."
                    value={patientQuery} onChange={e => setPatientQuery(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && searchPatients()} />
                  <button onClick={searchPatients} disabled={searchingPatients} className="btn-primary !px-4">
                    <Search className="h-4 w-4" />
                  </button>
                </div>
                {patients.length > 0 && (
                  <div className="max-h-48 overflow-y-auto rounded-xl border border-border-soft divide-y">
                    {patients.map(p => (
                      <button key={p.id} onClick={() => { setSelectedPatient(p); setPatients([]) }}
                        className="w-full px-4 py-3 text-left hover:bg-surface transition-colors">
                        <p className="font-body text-sm font-medium text-ink">{p.full_name}</p>
                        <p className="font-body text-xs text-ink-soft">{p.email} · {p.phone}</p>
                      </button>
                    ))}
                  </div>
                )}
                <p className="font-body text-xs text-ink-faint">
                  New patient? <button onClick={() => setTab('patient')} className="text-teal-700 underline">Register them first</button>
                </p>
              </div>
            )}
          </div>

          {/* Step 2 — Select Doctor */}
          <div className="card space-y-3">
            <h2 className="font-display text-base font-semibold text-ink">Step 2 — Select Doctor</h2>
            <div className="flex gap-2">
              <input className="input-field flex-1" placeholder="Filter by speciality..."
                value={specialityFilter}
                onChange={e => { setSpecialityFilter(e.target.value); fetchDoctors(e.target.value) }} />
            </div>
            {selectedDoctor ? (
              <div className="flex items-center justify-between rounded-lg bg-blue-50 px-4 py-3">
                <div>
                  <p className="font-body text-sm font-semibold text-blue-800">Dr. {selectedDoctor.user_full_name}</p>
                  <p className="font-body text-xs text-blue-600">{selectedDoctor.speciality} · {selectedDoctor.hospital_name} · ₦{parseFloat(selectedDoctor.consultation_fee).toLocaleString()}</p>
                </div>
                <button onClick={() => setSelectedDoctor(null)} className="font-body text-xs text-blue-700 underline">Change</button>
              </div>
            ) : (
              <div className="max-h-56 overflow-y-auto space-y-2">
                {doctors.map(d => (
                  <button key={d.id} onClick={() => setSelectedDoctor(d)}
                    className="w-full rounded-xl border border-border-soft px-4 py-3 text-left hover:border-teal-300 hover:bg-teal-50 transition-colors">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-body text-sm font-semibold text-ink">Dr. {d.user_full_name}</p>
                        <p className="font-body text-xs text-ink-soft">{d.speciality} · {d.hospital_name}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-mono text-sm text-ink">₦{parseFloat(d.consultation_fee).toLocaleString()}</p>
                        <span className={`text-xs ${d.is_available ? 'text-green-600' : 'text-red-500'}`}>
                          {d.is_available ? 'Available' : 'Unavailable'}
                        </span>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Step 3 — Date/Time + Reason */}
          <div className="card space-y-3">
            <h2 className="font-display text-base font-semibold text-ink">Step 3 — Appointment Details</h2>
            <input type="datetime-local" className="input-field w-full"
              value={scheduledAt} onChange={e => setScheduledAt(e.target.value)} />
            <input className="input-field w-full" placeholder="Reason for visit (optional)"
              value={reason} onChange={e => setReason(e.target.value)} />
            <textarea className="input-field w-full min-h-[80px]" placeholder="Receptionist notes (optional — not visible to patient)"
              value={notes} onChange={e => setNotes(e.target.value)} />
          </div>

          {/* Book Button */}
          <button
            onClick={bookAppointment}
            disabled={!selectedPatient || !selectedDoctor || !scheduledAt || booking}
            className="btn-primary w-full flex items-center justify-center gap-2">
            <CalendarPlus className="h-4 w-4" />
            {booking ? 'Booking...' : 'Confirm Appointment'}
          </button>
        </div>
      )}

      {/* NEW PATIENT TAB */}
      {tab === 'patient' && (
        <div className="card max-w-lg space-y-4">
          <h2 className="font-display text-base font-semibold text-ink">Register Walk-in / Phone Patient</h2>
          {createSuccess && <div className="rounded-lg bg-green-50 border border-green-200 p-3 font-body text-sm text-green-700">✅ {createSuccess}</div>}
          <div className="space-y-3">
            <input className="input-field w-full" placeholder="Full Name *" value={newPatient.full_name}
              onChange={e => setNewPatient(p => ({ ...p, full_name: e.target.value }))} />
            <input type="email" className="input-field w-full" placeholder="Email Address *" value={newPatient.email}
              onChange={e => setNewPatient(p => ({ ...p, email: e.target.value }))} />
            <input className="input-field w-full" placeholder="Phone Number" value={newPatient.phone}
              onChange={e => setNewPatient(p => ({ ...p, phone: e.target.value }))} />
          </div>
          <p className="font-body text-xs text-ink-faint">
            A password setup email will be sent automatically so the patient can access their account later.
          </p>
          <button onClick={createWalkInPatient} disabled={creatingPatient || !newPatient.full_name || !newPatient.email}
            className="btn-primary w-full">
            {creatingPatient ? 'Creating...' : 'Create Patient Account'}
          </button>
        </div>
      )}

      {/* TODAY'S SCHEDULE TAB */}
      {tab === 'schedule' && (
        <div className="card">
          <h2 className="font-display text-base font-semibold text-ink mb-4">Today's Appointment Schedule</h2>
          {schedule.length === 0 ? (
            <div className="py-12 text-center">
              <Clock className="mx-auto h-10 w-10 text-ink-faint mb-3" />
              <p className="font-body text-sm text-ink-soft">No appointments scheduled for today.</p>
            </div>
          ) : (
            <div className="divide-y divide-border-soft">
              {schedule.map(appt => (
                <div key={appt.id} className="flex items-center justify-between py-3 px-1">
                  <div>
                    <p className="font-body text-sm font-medium text-ink">{appt.patient_name}</p>
                    <p className="font-body text-xs text-ink-soft">Dr. {appt.doctor_name}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-mono text-sm text-ink">
                      {new Date(appt.scheduled_at).toLocaleTimeString('en-NG', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                    <span className={`text-xs font-medium ${
                      appt.status === 'confirmed' ? 'text-green-600' :
                      appt.status === 'pending'   ? 'text-amber-600' :
                      appt.status === 'completed' ? 'text-teal-700'  : 'text-red-500'}`}>
                      {appt.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
