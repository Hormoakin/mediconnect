// ══════════════════════════════════════════════════════════════
// frontend/src/services/api.ts
//
// Central axios instance. Implements:
//  - Automatic JWT attachment on every request
//  - Automatic token refresh on 401 (transparent to the caller)
//  - Consistent error shape (matches Django's custom_exception_handler)
// ══════════════════════════════════════════════════════════════
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
 
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
 
export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})
 
let accessToken: string | null = localStorage.getItem('mc_access') // see AuthContext note below
let refreshToken: string | null = localStorage.getItem('mc_refresh')
 
export function setTokens(access: string, refresh?: string) {
  accessToken = access
  if (refresh) refreshToken = refresh
}
export function clearTokens() {
  accessToken = null
  refreshToken = null
}
export function getAccessToken() {
  return accessToken
}
 
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})
 
let isRefreshing = false
let queue: Array<(token: string) => void> = []
 
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
 
    if (error.response?.status === 401 && refreshToken && !originalRequest._retry) {
      if (isRefreshing) {
        // Queue this request until the in-flight refresh completes
        return new Promise((resolve) => {
          queue.push((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(api(originalRequest))
          })
        })
      }
 
      originalRequest._retry = true
      isRefreshing = true
 
      try {
        const { data } = await axios.post(`${API_URL}/auth/token/refresh/`, {
          refresh: refreshToken,
        })
        setTokens(data.access)
        localStorage.setItem('mc_access', data.access)
 
        queue.forEach((cb) => cb(data.access))
        queue = []
 
        originalRequest.headers.Authorization = `Bearer ${data.access}`
        return api(originalRequest)
      } catch (refreshError) {
        clearTokens()
        localStorage.removeItem('mc_access')
        localStorage.removeItem('mc_refresh')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }
 
    return Promise.reject(error)
  }
)
 
/** Extracts a user-friendly message from any API error. */
export function apiErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    return (err.response?.data as any)?.message || 'Something went wrong. Please try again.'
  }
  return 'Something went wrong. Please try again.'
}
