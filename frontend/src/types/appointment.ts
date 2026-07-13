// ══════════════════════════════════════════════════════════════
// frontend/src/types/appointment.ts
// ══════════════════════════════════════════════════════════════
export type AppointmentStatus = 'pending' | 'confirmed' | 'completed' | 'cancelled' | 'no_show'
 
export interface Appointment {
  id: number
  patient: number
  patient_name: string
  doctor: number
  doctor_name: string
  doctor_speciality: string
  scheduled_at: string
  duration_mins: number
  status: AppointmentStatus
  reason: string
  doctor_notes: string
  is_upcoming: boolean
  can_cancel: boolean
  has_review: boolean
  created_at: string
}
 
export interface AppointmentCreatePayload {
  doctor: number
  scheduled_at: string
  duration_mins?: number
  reason: string
}
