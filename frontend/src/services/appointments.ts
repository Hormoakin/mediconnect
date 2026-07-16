// ══════════════════════════════════════════════════════════════
// frontend/src/services/appointments.ts
// ══════════════════════════════════════════════════════════════
import { api } from './api'
import type { Appointment, AppointmentCreatePayload, AppointmentStatus } from '../types/appointment'
 
export const appointmentService = {
  async list(status?: AppointmentStatus) {
    const { data } = await api.get('/appointments/', { params: status ? { status } : {} })
    return data.results as Appointment[]
  },
  async book(payload: AppointmentCreatePayload) {
    const { data } = await api.post<Appointment>('/appointments/', payload)
    return data
  },
  async updateStatus(id: number, status: AppointmentStatus, doctor_notes?: string) {
    const { data } = await api.patch<Appointment>(`/appointments/${id}/`, { status, doctor_notes })
    return data
  },
  async cancel(id: number) {
    return api.delete(`/appointments/${id}/`)
  },
  async review(appointmentId: number, rating: number, comment: string) {
    return api.post(`/appointments/${appointmentId}/review/`, { appointment: appointmentId, rating, comment })
  },
}
