// ══════════════════════════════════════════════════════════════
// frontend/src/pages/auth/Register.tsx
// ══════════════════════════════════════════════════════════════
import { useState, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { UserPlus, Stethoscope, User as UserIcon } from 'lucide-react'
import { useAuth, apiErrorMessage } from '../../contexts/AuthContext'
import { PulseLogo } from '../../components/layout/DashboardLayout'
import clsx from 'clsx'

type Role = 'patient' | 'doctor'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()

  const [role, setRole] = useState<Role>('patient')
  const [form, setForm] = useState({
    full_name: '', email: '', username: '', phone: '',
    password: '', confirm_password: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const update = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }))

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')

    if (form.password !== form.confirm_password) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)
    try {
      await register({ ...form, role })
      navigate('/dashboard')
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface px-5 py-10 font-body">
      <div className="w-full max-w-sm">
        <Link to="/" className="mb-8 flex items-center justify-center gap-2">
          <PulseLogo className="h-7 w-7 text-brand-teal" />
          <span className="font-display text-lg font-semibold text-brand-ink">MediConnect</span>
        </Link>

        <div className="card">
          <h1 className="font-display text-xl font-semibold text-ink">Create your account</h1>
          <p className="mt-1 font-body text-sm text-ink-soft">Takes about a minute.</p>

          {/* Role selector — pharmacist/admin accounts are created by an
              administrator only (see Chapter 3, Section 3.3.2, FR-01.1
              validation: allowed_self_register_roles) *\/}
          <div className="mt-4 grid grid-cols-2 gap-2">
            {(['patient', 'doctor'] as Role[]).map((r) => (
              <button
                key={r} type="button" onClick={() => setRole(r)}
                className={clsx(
                  'flex flex-col items-center gap-1.5 rounded-lg border px-3 py-3 transition-colors',
                  role === r ? 'border-brand-teal bg-brand-teal-tint' : 'border-border-soft hover:border-ink-faint'
                )}
              >
                {r === 'patient' ? <UserIcon className="h-4 w-4 text-brand-teal-deep" /> : <Stethoscope className="h-4 w-4 text-brand-teal-deep" />}
                <span className="font-body text-sm font-medium capitalize text-ink">{r}</span>
              </button>
            ))}
          </div>

          {error && (
            <div className="mt-4 rounded-lg bg-brand-coral-tint px-3.5 py-2.5 font-body text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-5 space-y-4">
            <div>
              <label className="label-text">Full name</label>
              <input required className="input-field" value={form.full_name} onChange={update('full_name')} placeholder="Ada Obi" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label-text">Username</label>
                <input required className="input-field" value={form.username} onChange={update('username')} placeholder="adaobi" />
              </div>
              <div>
                <label className="label-text">Phone</label>
                <input required className="input-field" value={form.phone} onChange={update('phone')} placeholder="+234…" />
              </div>
            </div>
            <div>
              <label className="label-text">Email address</label>
              <input required type="email" className="input-field" value={form.email} onChange={update('email')} placeholder="you@example.com" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label-text">Password</label>
                <input required type="password" className="input-field" value={form.password} onChange={update('password')} />
              </div>
              <div>
                <label className="label-text">Confirm</label>
                <input required type="password" className="input-field" value={form.confirm_password} onChange={update('confirm_password')} />
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? 'Creating account…' : (<>Create account <UserPlus className="h-4 w-4" /></>)}
            </button>
          </form>
        </div>

        <p className="mt-6 text-center font-body text-sm text-ink-soft">
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-brand-teal hover:underline">Log in</Link>
        </p>
      </div>
    </div>
  )
}
