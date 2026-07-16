// ══════════════════════════════════════════════════════════════
// frontend/src/contexts/AuthContext.tsx
//
// Reads role, full_name, user_id directly from the decoded JWT
// (see backend MediConnectTokenObtainSerializer in Chapter 3,
// Section 3.6.1) so the dashboard can render the correct
// role-specific view immediately on load, before the slower
// /users/me/ profile fetch completes.
// ══════════════════════════════════════════════════════════════
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { jwtDecode } from 'jwt-decode'
import { api, setTokens, clearTokens, getAccessToken, apiErrorMessage } from '../services/api'
import type { User, UserRole } from '../types/user'

interface DecodedToken {
  user_id: number
  role: UserRole
  full_name: string
  is_verified: boolean
  exp: number
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (payload: RegisterPayload) => Promise<void>
  logout: () => Promise<void>
  refreshProfile: () => Promise<void>
}

interface RegisterPayload {
  email: string
  username: string
  full_name: string
  phone: string
  role: 'patient' | 'doctor'
  password: string
  confirm_password: string
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const hydrateFromToken = useCallback((token: string): Partial<User> | null => {
    try {
      const decoded = jwtDecode<DecodedToken>(token)
      if (decoded.exp * 1000 < Date.now()) return null
      return {
        id: decoded.user_id,
        role: decoded.role,
        full_name: decoded.full_name,
        is_verified: decoded.is_verified,
      }
    } catch {
      return null
    }
  }, [])

  const refreshProfile = useCallback(async () => {
    try {
      const { data } = await api.get<User>('/users/me/')
      setUser(data)
    } catch {
      // Token invalid/expired and refresh failed — interceptor already redirects to /login
      setUser(null)
    }
  }, [])

  useEffect(() => {
    const access = localStorage.getItem('mc_access')
    const refresh = localStorage.getItem('mc_refresh')

    if (access && refresh) {
      setTokens(access, refresh)
      const partial = hydrateFromToken(access)
      if (partial) {
        // Optimistically render with token claims, then fetch full profile
        setUser(partial as User)
        refreshProfile().finally(() => setLoading(false))
        return
      }
    }
    setLoading(false)
  }, [hydrateFromToken, refreshProfile])

  const login = async (email: string, password: string) => {
    const { data } = await api.post('/auth/login/', { email, password })
    setTokens(data.access, data.refresh)
    localStorage.setItem('mc_access', data.access)
    localStorage.setItem('mc_refresh', data.refresh)
    setUser(data.user)
    await refreshProfile()
  }

  const register = async (payload: RegisterPayload) => {
    const { data } = await api.post('/auth/register/', payload)
    setTokens(data.tokens.access, data.tokens.refresh)
    localStorage.setItem('mc_access', data.tokens.access)
    localStorage.setItem('mc_refresh', data.tokens.refresh)
    setUser(data.user)
  }

  const logout = async () => {
    const refresh = localStorage.getItem('mc_refresh')
    try {
      if (refresh) await api.post('/auth/logout/', { refresh })
    } finally {
      clearTokens()
      localStorage.removeItem('mc_access')
      localStorage.removeItem('mc_refresh')
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshProfile }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

export { apiErrorMessage }
