// ══════════════════════════════════════════════════════════════
// frontend/src/services/messages.ts
// ══════════════════════════════════════════════════════════════
import { api } from './api'
import type { Message } from '../types/message'
 
export const messageService = {
  async conversations() {
    const { data } = await api.get('/messages/')
    return data.results as Message[]
  },
  async history(userId: number) {
    const { data } = await api.get(`/messages/${userId}/`)
    return data.results as Message[]
  },
}
