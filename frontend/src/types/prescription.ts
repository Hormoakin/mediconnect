// ══════════════════════════════════════════════════════════════
// frontend/src/types/prescription.ts
// ══════════════════════════════════════════════════════════════
export type PrescriptionStatus = 'issued' | 'dispensed' | 'cancelled' | 'expired'
 
export interface Prescription {
  id: number
  appointment: number | null
  patient: number
  doctor: number
  pharmacist: number | null
  medication: string
  dosage: string
  frequency: string
  duration_days: number
  instructions: string
  status: PrescriptionStatus
  issued_at: string
  dispensed_at: string | null
  expires_at: string
}
