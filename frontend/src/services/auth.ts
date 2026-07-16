// ══════════════════════════════════════════════════════════════
// frontend/src/services/auth.ts
// ══════════════════════════════════════════════════════════════
import { api, setTokens, clearTokens } from './api'
import type { User, UserRole } from '../types/user'
 
interface LoginResponse {
  access: string
  refresh: string
  user: { id: number; email: string; full_name: string; role: UserRole; is_verified: boolean }
}
 
export const authService = {
  async login(email: string, password: string) {
    const { data } = await api.post<LoginResponse>('/auth/login/', { email, password })
    setTokens(data.access, data.refresh)
    localStorage.setItem('mc_access', data.access)
    localStorage.setItem('mc_refresh', data.refresh)
    return data.user
  },
 
  async register(payload: {
    email: string; username: string; full_name: string; phone: string
    role: 'patient' | 'doctor'; password: string; confirm_password: string
  }) {
    const { data } = await api.post('/auth/register/', payload)
    setTokens(data.tokens.access, data.tokens.refresh)
    localStorage.setItem('mc_access', data.tokens.access)
    localStorage.setItem('mc_refresh', data.tokens.refresh)
    return data.user
  },
 
  async logout() {
    const refresh = localStorage.getItem('mc_refresh')
    try {
      if (refresh) await api.post('/auth/logout/', { refresh })
    } finally {
      clearTokens()
      localStorage.removeItem('mc_access')
      localStorage.removeItem('mc_refresh')
    }
  },
 
  async getMe(): Promise<User> {
    const { data } = await api.get<User>('/users/me/')
    return data
  },
 
  async requestPasswordReset(email: string) {
    return api.post('/auth/password-reset/', { email })
  },
}
