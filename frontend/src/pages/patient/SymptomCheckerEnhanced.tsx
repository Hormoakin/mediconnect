// ══════════════════════════════════════════════════════════════
// frontend/src/pages/patient/SymptomCheckerEnhanced.tsx
// Enhanced AI Symptom Checker with full triage flow:
//   1. Symptom input
//   2. AI analysis → conditions + urgency
//   3. Department recommendation
//   4. Available doctors in that department
//   5. Direct appointment booking
// ══════════════════════════════════════════════════════════════
import { useState } from 'react'
import { AlertTriangle, CheckCircle, Clock, Stethoscope, CalendarPlus, ChevronRight, AlertCircle } from 'lucide-react'
import { api } from '../../services/api'

interface Condition {
  condition: string
  confidence: number
  description: string
}

interface TriageDoctor {
  id: number
  full_name: string
  speciality: string
  hospital_name: string
  rating: string
  consultation_fee: string
  is_available: boolean
  next_available_slot: string | null
}

interface BookingPayload {
  doctor_id: number
  doctor_name: string
  speciality: string
  suggested_reason: string
}

interface TriageResult {
  symptoms_submitted: string
  possible_conditions: Condition[]
  urgency_level: 'low' | 'medium' | 'high' | 'emergency'
  urgency_reason: string
  disclaimer: string
  recommended_department: string
  department_priority: number
  is_emergency: boolean
  emergency_instruction: string | null
  available_doctors: TriageDoctor[]
  total_doctors_found: number
  booking_payload: BookingPayload | null
  booking_instructions: string
  response_time_ms: number
  model_version: string
}

const URGENCY_CONFIG = {
  emergency: { label: 'EMERGENCY', bg: 'bg-red-50 border-red-200',   text: 'text-red-700',   badge: 'bg-red-100 text-red-700',   icon: AlertTriangle },
  high:      { label: 'URGENT',    bg: 'bg-amber-50 border-amber-200',text: 'text-amber-700', badge: 'bg-amber-100 text-amber-700',icon: AlertCircle },
  medium:    { label: 'MODERATE',  bg: 'bg-blue-50 border-blue-200',  text: 'text-blue-700',  badge: 'bg-blue-100 text-blue-700',  icon: Clock },
  low:       { label: 'ROUTINE',   bg: 'bg-green-50 border-green-200',text: 'text-green-700', badge: 'bg-green-100 text-green-700',icon: CheckCircle },
}

export default function SymptomCheckerEnhanced() {
  const [symptoms, setSymptoms]     = useState('')
  const [age, setAge]               = useState('')
  const [gender, setGender]         = useState('')
  const [loading, setLoading]       = useState(false)
  const [result, setResult]         = useState<TriageResult | null>(null)
  const [error, setError]           = useState('')

  // Booking flow
  const [selectedDoctor, setSelectedDoctor]   = useState<TriageDoctor | null>(null)
  const [scheduledAt, setScheduledAt]         = useState('')
  const [booking, setBooking]                 = useState(false)
  const [bookingSuccess, setBookingSuccess]   = useState('')
  const [showBooking, setShowBooking]         = useState(false)

  const runTriage = async () => {
    if (symptoms.trim().length < 5) {
      setError('Please describe your symptoms in more detail (at least a few words).')
      return
    }
    setLoading(true)
    setError('')
    setResult(null)
    setBookingSuccess('')
    setShowBooking(false)

    try {
      const { data } = await api.post<TriageResult>('/ai/triage/', {
        symptoms: symptoms.trim(),
        patient_age:    age    ? parseInt(age)    : undefined,
        patient_gender: gender ? gender           : undefined,
      })
      setResult(data)
      // Auto-select top doctor for booking
      if (data.booking_payload && data.available_doctors.length > 0) {
        setSelectedDoctor(data.available_doctors[0])
      }
    } catch (err: any) {
      const msg = err?.response?.data?.message || err?.response?.data?.detail
      setError(msg || 'The AI service is temporarily unavailable. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const bookAppointment = async () => {
    if (!selectedDoctor || !scheduledAt || !result?.booking_payload) return
    setBooking(true)
    try {
      await api.post('/appointments/', {
        doctor:       selectedDoctor.id,
        scheduled_at: scheduledAt,
        reason:       result.booking_payload.suggested_reason,
      })
      setBookingSuccess(
        `Appointment booked with Dr. ${selectedDoctor.full_name} on ${new Date(scheduledAt).toLocaleString('en-NG', { dateStyle: 'medium', timeStyle: 'short' })}`
      )
      setShowBooking(false)
    } catch (err: any) {
      alert(err?.response?.data?.message || 'Booking failed. Please try the Find a Doctor page.')
    } finally {
      setBooking(false)
    }
  }

  const reset = () => {
    setResult(null); setSymptoms(''); setAge(''); setGender('')
    setError(''); setSelectedDoctor(null); setScheduledAt('')
    setBookingSuccess(''); setShowBooking(false)
  }

  const urgencyConfig = result ? URGENCY_CONFIG[result.urgency_level] : null

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-ink">AI Symptom Checker</h1>
        <p className="mt-1 font-body text-sm text-ink-soft">
          Describe what you're experiencing. Our AI will assess your symptoms,
          recommend the right department, and help you book with an available doctor.
        </p>
      </div>

      {/* Booking success banner */}
      {bookingSuccess && (
        <div className="flex items-center gap-3 rounded-xl border border-green-200 bg-green-50 p-4">
          <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0" />
          <p className="font-body text-sm text-green-700">✅ {bookingSuccess}</p>
        </div>
      )}

      {/* Input form (show when no result) */}
      {!result && (
        <div className="card space-y-4">
          <div>
            <label className="font-body text-sm font-medium text-ink mb-1 block">What's going on?</label>
            <textarea
              className="input-field w-full min-h-[120px] resize-none"
              placeholder="Describe your symptoms in your own words, e.g. 'I have a fever since yesterday, bad headache, and my joints ache...'"
              value={symptoms}
              onChange={e => setSymptoms(e.target.value)}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="font-body text-xs text-ink-faint mb-1 block">Age (optional)</label>
              <input type="number" className="input-field w-full" placeholder="e.g. 34"
                value={age} onChange={e => setAge(e.target.value)} min={0} max={120} />
            </div>
            <div>
              <label className="font-body text-xs text-ink-faint mb-1 block">Gender (optional)</label>
              <select className="input-field w-full" value={gender} onChange={e => setGender(e.target.value)}>
                <option value="">Select...</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          {error && (
            <p className="font-body text-sm text-red-600">{error}</p>
          )}
          <button onClick={runTriage} disabled={loading || symptoms.trim().length < 5}
            className="btn-primary w-full flex items-center justify-center gap-2">
            <Stethoscope className="h-4 w-4" />
            {loading ? 'Analysing symptoms...' : 'Analyse symptoms'}
          </button>
          {loading && (
            <p className="text-center font-mono text-xs text-ink-faint animate-pulse">
              Running AI triage — this may take a few seconds...
            </p>
          )}
        </div>
      )}

      {/* TRIAGE RESULT */}
      {result && urgencyConfig && (
        <div className="space-y-4">
          {/* Emergency banner */}
          {result.is_emergency && (
            <div className="flex items-start gap-3 rounded-xl border-2 border-red-300 bg-red-50 p-4">
              <AlertTriangle className="h-6 w-6 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-display text-base font-bold text-red-700">⚠️ EMERGENCY — Seek Immediate Care</p>
                <p className="font-body text-sm text-red-600 mt-1">{result.emergency_instruction}</p>
              </div>
            </div>
          )}

          {/* Urgency + Department */}
          <div className={`rounded-xl border p-4 ${urgencyConfig.bg}`}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <urgencyConfig.icon className={`h-5 w-5 ${urgencyConfig.text}`} />
                <span className={`font-display text-sm font-bold ${urgencyConfig.text}`}>
                  {urgencyConfig.label}
                </span>
                <span className={`rounded-full px-2 py-0.5 font-body text-xs ${urgencyConfig.badge}`}>
                  {result.urgency_level}
                </span>
              </div>
              <span className="font-mono text-xs text-ink-faint">{result.response_time_ms}ms</span>
            </div>
            <p className={`font-body text-sm ${urgencyConfig.text} mb-3`}>{result.urgency_reason}</p>
            <div className={`rounded-lg px-3 py-2 bg-white/60 border ${urgencyConfig.bg.replace('50','100')}`}>
              <p className="font-body text-xs text-ink-faint mb-0.5">Recommended Department</p>
              <p className={`font-display text-sm font-semibold ${urgencyConfig.text}`}>
                {result.recommended_department}
              </p>
            </div>
          </div>

          {/* Possible Conditions */}
          <div className="card space-y-3">
            <h3 className="font-display text-sm font-semibold text-ink">Possible Conditions</h3>
            {result.possible_conditions.map((cond, i) => (
              <div key={i} className="space-y-1">
                <div className="flex items-center justify-between">
                  <p className="font-body text-sm font-medium text-ink">{cond.condition}</p>
                  <span className="font-mono text-sm text-teal-700 font-semibold">
                    {Math.round(cond.confidence * 100)}%
                  </span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-surface">
                  <div className="h-1.5 rounded-full bg-teal-600 transition-all"
                    style={{ width: `${Math.round(cond.confidence * 100)}%` }} />
                </div>
                {cond.description && (
                  <p className="font-body text-xs text-ink-faint">{cond.description}</p>
                )}
              </div>
            ))}
          </div>

          {/* Booking Instructions */}
          <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">
            <p className="font-body text-sm text-blue-700">{result.booking_instructions}</p>
          </div>

          {/* Available Doctors + Book */}
          {!result.is_emergency && result.available_doctors.length > 0 && (
            <div className="card space-y-3">
              <h3 className="font-display text-sm font-semibold text-ink">
                Available Doctors — {result.recommended_department}
              </h3>
              <div className="space-y-2">
                {result.available_doctors.map(doc => (
                  <button
                    key={doc.id}
                    onClick={() => { setSelectedDoctor(doc); setShowBooking(true) }}
                    className={`w-full rounded-xl border p-3 text-left transition-all
                      ${selectedDoctor?.id === doc.id && showBooking
                        ? 'border-teal-400 bg-teal-50'
                        : 'border-border-soft hover:border-teal-300 hover:bg-surface'}`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-body text-sm font-semibold text-ink">Dr. {doc.full_name}</p>
                        <p className="font-body text-xs text-teal-700">{doc.speciality}</p>
                        <p className="font-body text-xs text-ink-faint">{doc.hospital_name}</p>
                        {doc.next_available_slot && (
                          <p className="font-mono text-xs text-green-600 mt-0.5">
                            Next slot: {doc.next_available_slot}
                          </p>
                        )}
                      </div>
                      <div className="text-right">
                        <p className="font-mono text-sm font-medium text-ink">
                          ₦{parseFloat(doc.consultation_fee).toLocaleString()}
                        </p>
                        <p className="font-body text-xs text-amber-600">★ {doc.rating}</p>
                        <ChevronRight className="h-4 w-4 text-teal-600 mt-1 ml-auto" />
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              {/* Inline booking form */}
              {showBooking && selectedDoctor && (
                <div className="rounded-xl border-2 border-teal-200 bg-teal-50 p-4 space-y-3">
                  <p className="font-display text-sm font-semibold text-teal-700">
                    Book with Dr. {selectedDoctor.full_name}
                  </p>
                  <input type="datetime-local" className="input-field w-full"
                    value={scheduledAt} onChange={e => setScheduledAt(e.target.value)} />
                  {result.booking_payload && (
                    <p className="font-body text-xs text-ink-faint">
                      Reason: {result.booking_payload.suggested_reason.slice(0, 120)}...
                    </p>
                  )}
                  <div className="flex gap-2">
                    <button onClick={bookAppointment}
                      disabled={!scheduledAt || booking}
                      className="btn-primary flex items-center gap-2">
                      <CalendarPlus className="h-4 w-4" />
                      {booking ? 'Booking...' : 'Confirm Appointment'}
                    </button>
                    <button onClick={() => setShowBooking(false)} className="btn-secondary">Cancel</button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* No doctors available */}
          {!result.is_emergency && result.available_doctors.length === 0 && (
            <div className="card text-center py-6">
              <Stethoscope className="mx-auto h-8 w-8 text-ink-faint mb-2" />
              <p className="font-body text-sm text-ink-soft mb-3">
                No doctors currently available in {result.recommended_department}.
              </p>
              <a href="/doctors" className="btn-primary inline-flex items-center gap-2">
                Find a Doctor <ChevronRight className="h-4 w-4" />
              </a>
            </div>
          )}

          {/* Disclaimer */}
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
            <p className="font-body text-xs text-amber-700 leading-relaxed">{result.disclaimer}</p>
          </div>

          {/* Restart */}
          <button onClick={reset} className="btn-secondary w-full">
            Check Different Symptoms
          </button>
        </div>
      )}
    </div>
  )
}
