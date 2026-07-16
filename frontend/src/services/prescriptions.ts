// ══════════════════════════════════════════════════════════════
// frontend/src/services/prescriptions.ts
// ══════════════════════════════════════════════════════════════
import { api } from './api'
import type { Prescription } from '../types/prescription'
 
export const prescriptionService = {
  async list() {
    const { data } = await api.get('/prescriptions/')
    return data.results as Prescription[]
  },
  async issue(payload: Omit<Prescription, 'id' | 'status' | 'issued_at' | 'dispensed_at' | 'expires_at' | 'pharmacist'>) {
    const { data } = await api.post<Prescription>('/prescriptions/', payload)
    return data
  },
  async dispense(id: number) {
    return api.patch(`/prescriptions/${id}/dispense/`)
  },
}
