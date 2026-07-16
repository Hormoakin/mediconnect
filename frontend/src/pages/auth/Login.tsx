// ══════════════════════════════════════════════════════════════
// frontend/src/pages/auth/Login.tsx
// ══════════════════════════════════════════════════════════════
import { useState, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, LogIn } from 'lucide-react'
import { useAuth, apiErrorMessage } from '../../contexts/AuthContext'
import { PulseLogo } from '../../components/layout/DashboardLayout'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface px-5 font-body">
      <div className="w-full max-w-sm">
        <Link to="/" className="mb-8 flex items-center justify-center gap-2">
          <PulseLogo className="h-7 w-7 text-brand-teal" />
          <span className="font-display text-lg font-semibold text-brand-ink">MediConnect</span>
        </Link>

        <div className="card">
          <h1 className="font-display text-xl font-semibold text-ink">Welcome back</h1>
          <p className="mt-1 font-body text-sm text-ink-soft">Log in to continue to your dashboard.</p>

          {error && (
            <div className="mt-4 rounded-lg bg-brand-coral-tint px-3.5 py-2.5 font-body text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-5 space-y-4">
            <div>
              <label className="label-text" htmlFor="email">Email address</label>
              <input
                id="email" type="email" required autoComplete="email"
                className="input-field" placeholder="you@example.com"
                value={email} onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div>
              <div className="flex items-center justify-between">
                <label className="label-text" htmlFor="password">Password</label>
                <Link to="/forgot-password" className="mb-1.5 font-body text-xs font-medium text-brand-teal hover:underline">
                  Forgot it?
                </Link>
              </div>
              <div className="relative">
                <input
                  id="password" type={showPassword ? 'text' : 'password'} required autoComplete="current-password"
                  className="input-field pr-10" placeholder="••••••••"
                  value={password} onChange={(e) => setPassword(e.target.value)}
                />
                <button
                  type="button" onClick={() => setShowPassword((s) => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-faint hover:text-ink-soft"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? 'Logging in…' : (<>Log in <LogIn className="h-4 w-4" /></>)}
            </button>
          </form>
        </div>

        <p className="mt-6 text-center font-body text-sm text-ink-soft">
          New to MediConnect?{' '}
          <Link to="/register" className="font-medium text-brand-teal hover:underline">Create an account</Link>
        </p>
      </div>
    </div>
  )
}
