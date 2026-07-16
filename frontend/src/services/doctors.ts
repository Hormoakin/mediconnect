// ══════════════════════════════════════════════════════════════
// frontend/src/services/doctors.ts
// ══════════════════════════════════════════════════════════════
import { api } from './api'
import type { DoctorProfile } from '../types/user'
 
export const doctorService = {
  async list(params?: { speciality?: string; search?: string; ordering?: string }) {
    const { data } = await api.get('/doctors/', { params })
    return data.results as DoctorProfile[]
  },
  async getById(id: number) {
    const { data } = await api.get<DoctorProfile>(`/doctors/${id}/`)
    return data
  },
  async getSlots(id: number, date: string) {
    const { data } = await api.get(`/doctors/${id}/slots/`, { params: { date } })
    return data as { available_slots: string[]; slot_duration_minutes: number }
  },
}

