// ══════════════════════════════════════════════════════════════
// frontend/src/services/records.ts
// ══════════════════════════════════════════════════════════════
import { api } from './api'
import type { ClinicalRecord } from '../types/record'
 
export const recordService = {
  async list() {
    const { data } = await api.get('/records/')
    return data.results as ClinicalRecord[]
  },
  async create(payload: Partial<ClinicalRecord>) {
    const { data } = await api.post<ClinicalRecord>('/records/', payload)
    return data
  },
}
