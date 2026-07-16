// ══════════════════════════════════════════════════════════════
// frontend/src/components/forms/BookAppointmentModal.tsx
// ══════════════════════════════════════════════════════════════
import { useState } from 'react'
import { X, Calendar, Clock } from 'lucide-react'
import { api, apiErrorMessage } from '../../services/api'
import type { DoctorProfile } from '../../types/user'
import { format, addDays } from 'date-fns'

interface Props {
  doctor: DoctorProfile
  onClose: () => void
  onBooked: () => void
}

export default function BookAppointmentModal({ doctor, onClose, onBooked }: Props) {
  const [date, setDate] = useState(format(addDays(new Date(), 1), 'yyyy-MM-dd'))
  const [slots, setSlots] = useState<string[]>([])
  const [selectedSlot, setSelectedSlot] = useState('')
  const [reason, setReason] = useState('')
  const [loadingSlots, setLoadingSlots] = useState(false)
  const [booking, setBooking] = useState(false)
  const [error, setError] = useState('')

  const fetchSlots = async () => {
    setLoadingSlots(true); setSlots([]); setSelectedSlot('')
    try {
      const { data } = await api.get(`/doctors/${doctor.id}/slots/`, { params: { date } })
      setSlots(data.available_slots)
      if (data.available_slots.length === 0) setError('No available slots on this date.')
      else setError('')
    } finally { setLoadingSlots(false) }
  }

  const handleBook = async () => {
    if (!selectedSlot) return
    setBooking(true); setError('')
    try {
      await api.post('/appointments/', {
        doctor: doctor.id,
        scheduled_at: `${date}T${selectedSlot}:00`,
        reason,
      })
      onBooked()
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally { setBooking(false) }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-brand-ink/60 px-4">
      <div className="card w-full max-w-md space-y-5">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="font-display text-lg font-semibold text-ink">Book appointment</h2>
            <p className="font-body text-sm text-ink-soft">Dr. {doctor.user_full_name} · {doctor.speciality}</p>
          </div>
          <button onClick={onClose} className="rounded-lg p-1 text-ink-faint hover:bg-surface"><X className="h-5 w-5" /></button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="label-text"><Calendar className="mr-1.5 inline h-3.5 w-3.5" />Select date</label>
            <div className="flex gap-2">
              <input type="date" className="input-field flex-1" value={date}
                min={format(addDays(new Date(), 1), 'yyyy-MM-dd')}
                onChange={e => { setDate(e.target.value); setSlots([]); setSelectedSlot('') }} />
              <button onClick={fetchSlots} disabled={loadingSlots} className="btn-secondary whitespace-nowrap">
                {loadingSlots ? 'Loading…' : 'Check slots'}
              </button>
            </div>
          </div>

          {slots.length > 0 && (
            <div>
              <label className="label-text"><Clock className="mr-1.5 inline h-3.5 w-3.5" />Available times</label>
              <div className="grid grid-cols-4 gap-2 mt-1">
                {slots.map(slot => (
                  <button key={slot} onClick={() => setSelectedSlot(slot)}
                    className={`rounded-lg border px-2 py-1.5 font-mono text-xs transition-colors ${
                      selectedSlot === slot ? 'border-brand-teal bg-brand-teal-tint text-brand-teal-deep' : 'border-border-soft hover:border-ink-faint'}`}>
                    {slot}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div>
            <label className="label-text">Reason for visit <span className="text-ink-faint">(optional)</span></label>
            <textarea rows={2} className="input-field resize-none" placeholder="Brief description…"
              value={reason} onChange={e => setReason(e.target.value)} />
          </div>

          {error && <p className="font-body text-sm text-red-600">{error}</p>}

          <div className="flex gap-2">
            <button onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button onClick={handleBook} disabled={!selectedSlot || booking} className="btn-primary flex-1">
              {booking ? 'Booking…' : 'Confirm booking'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
