import { useState, FormEvent, ChangeEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { UserPlus, Stethoscope, User as UserIcon } from 'lucide-react'
import clsx from 'clsx'

import { useAuth, apiErrorMessage } from '../../contexts/AuthContext'
import { PulseLogo } from '../../components/layout/DashboardLayout'

type Role = 'patient' | 'doctor'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()

  const [role, setRole] = useState<Role>('patient')

  const [form, setForm] = useState({
    full_name: '',
    username: '',
    email: '',
    phone: '',
    password: '',
    confirm_password: '',
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const update =
    (field: keyof typeof form) =>
    (e: ChangeEvent<HTMLInputElement>) =>
      setForm((prev) => ({
        ...prev,
        [field]: e.target.value,
      }))

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()

    setError('')

    if (form.password !== form.confirm_password) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)

    try {
      await register({
        full_name: form.full_name,
        username: form.username,
        email: form.email,
        phone: form.phone,
        password: form.password,
        confirm_password: form.confirm_password,
        role,
      })

      navigate('/login')
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface px-5 py-10 font-body">
      <div className="w-full max-w-lg rounded-2xl bg-white p-8 shadow-xl">

        <Link
          to="/"
          className="mb-6 flex items-center justify-center gap-2"
        >
          <PulseLogo className="h-7 w-7 text-brand-teal" />
          <span className="font-display text-lg font-semibold text-brand-ink">
            MediConnect
          </span>
        </Link>

        <h1 className="text-center font-display text-3xl font-bold text-brand-ink">
          Create Account
        </h1>

        <p className="mt-2 text-center text-sm text-ink-soft">
          Takes about a minute.
        </p>

        {/* Role Selector */}
        <div className="mt-6 grid grid-cols-2 gap-3">
          {(['patient', 'doctor'] as Role[]).map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setRole(r)}
              className={clsx(
                'flex items-center justify-center gap-2 rounded-xl border p-4 transition',
                role === r
                  ? 'border-brand-teal bg-brand-teal/10'
                  : 'border-gray-200 hover:border-brand-teal'
              )}
            >
              {r === 'patient' ? (
                <UserIcon className="h-5 w-5" />
              ) : (
                <Stethoscope className="h-5 w-5" />
              )}

              <span className="capitalize">{r}</span>
            </button>
          ))}
        </div>

        {error && (
          <div className="mt-4 rounded-lg bg-red-100 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <form
          onSubmit={handleSubmit}
          className="mt-6 space-y-4"
        >
          <div>
            <label className="label-text">Full Name</label>
            <input
              required
              className="input-field"
              value={form.full_name}
              onChange={update('full_name')}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label-text">Username</label>
              <input
                required
                className="input-field"
                value={form.username}
                onChange={update('username')}
              />
            </div>

            <div>
              <label className="label-text">Phone</label>
              <input
                required
                className="input-field"
                value={form.phone}
                onChange={update('phone')}
              />
            </div>
          </div>

          <div>
            <label className="label-text">Email Address</label>
            <input
              required
              type="email"
              className="input-field"
              value={form.email}
              onChange={update('email')}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label-text">Password</label>
              <input
                required
                type="password"
                className="input-field"
                value={form.password}
                onChange={update('password')}
              />
            </div>

            <div>
              <label className="label-text">Confirm Password</label>
              <input
                required
                type="password"
                className="input-field"
                value={form.confirm_password}
                onChange={update('confirm_password')}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary flex w-full items-center justify-center gap-2"
          >
            {loading ? (
              'Creating account...'
            ) : (
              <>
                Create Account
                <UserPlus className="h-4 w-4" />
              </>
            )}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-ink-soft">
          Already have an account?{' '}
          <Link
            to="/login"
            className="font-medium text-brand-teal hover:underline"
          >
            Log in
          </Link>
        </p>
      </div>
    </div>
  )
}
