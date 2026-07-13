
// ══════════════════════════════════════════════════════════════
// frontend/src/types/user.ts
// ══════════════════════════════════════════════════════════════
export type UserRole = 'patient' | 'doctor' | 'pharmacist' | 'admin'
 
export interface User {
  id: number
  email: string
  username: string
  full_name: string
  phone: string
  role: UserRole
  is_verified: boolean
  profile_photo?: string | null
  date_joined?: string
  doctor_profile?: DoctorProfile | null
  patient_profile?: PatientProfile | null
}
 
export interface DoctorAvailability {
  id: number
  day_of_week: number
  day_name: string
  start_time: string
  end_time: string
  slot_duration: number
  is_active: boolean
}
 
export interface DoctorProfile {
  id: number
  user_id: number
  user_full_name: string
  user_email: string
  user_phone: string
  speciality: string
  license_number: string
  bio: string
  years_experience: number
  consultation_fee: string
  rating: string
  total_reviews: number
  is_available: boolean
  hospital_name: string
  hospital_address: string
  availability: DoctorAvailability[]
}
 
export interface PatientProfile {
  id: number
  date_of_birth: string | null
  blood_group: string
  genotype: string
  allergies: string
  chronic_conditions: string
  current_medications: string
  next_of_kin_name: string
  next_of_kin_phone: string
  emergency_contact: string
}
