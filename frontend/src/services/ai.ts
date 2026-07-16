// ══════════════════════════════════════════════════════════════
// frontend/src/services/ai.ts
// ══════════════════════════════════════════════════════════════
import { api } from './api'
import type { SymptomCheckResult } from '../types/ai'
import type { DoctorProfile } from '../types/user'
 
export const aiService = {
  async checkSymptoms(symptoms: string): Promise<SymptomCheckResult> {
    const { data } = await api.post<SymptomCheckResult>('/ai/symptom-check/', { symptoms })
    return data
  },
  async recommendDoctors(specialist_type: string, symptoms?: string) {
    const { data } = await api.post('/ai/recommend-doctor/', { specialist_type, symptoms })
    return data.recommendations as DoctorProfile[]
  },
}
