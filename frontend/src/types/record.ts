// ══════════════════════════════════════════════════════════════
// frontend/src/types/record.ts
// ══════════════════════════════════════════════════════════════
export interface ClinicalRecord {
  id: number
  patient: number
  patient_name: string
  doctor: number
  doctor_name: string
  appointment: number | null
  chief_complaint: string
  history_of_illness: string
  examination_findings: string
  diagnosis: string
  treatment_plan: string
  follow_up_date: string | null
  is_confidential: boolean
  created_at: string
  updated_at: string
}
