// ══════════════════════════════════════════════════════════════
// frontend/src/pages/admin/AdminDashboard.tsx
// ══════════════════════════════════════════════════════════════
import { useEffect, useState } from 'react'
import { Users, Calendar, Pill, Activity } from 'lucide-react'
import { api } from '../../services/api'
import LoadingSpinner from '../../components/common/LoadingSpinner'

interface Stats {
  users: { total: number; patients: number; doctors: number; pharmacists: number; new_last_30d: number }
  appointments: { total_today: number; pending: number; confirmed: number; completed_30d: number; no_show_rate_30d: number }
  prescriptions: { issued_30d: number; dispensed_30d: number; pending: number }
  system: { status: string; timestamp: string }
}

export function AdminDashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/admin/stats/').then(r => setStats(r.data)).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center pt-20"><LoadingSpinner size="lg" /></div>
  if (!stats) return null

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink">System Overview</h1>
          <p className="mt-1 font-body text-sm text-ink-soft">Live platform statistics</p>
        </div>
        <div className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1.5">
          <Activity className="h-3.5 w-3.5 text-emerald-600" />
          <span className="font-mono text-xs text-emerald-700">{stats.system.status}</span>
        </div>
      </div>

      {/* KPI grid */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { icon: Users,    label: 'Total users',         value: stats.users.total,                    sub: `+${stats.users.new_last_30d} this month`, color: 'text-brand-teal' },
          { icon: Calendar, label: 'Appointments today',  value: stats.appointments.total_today,       sub: `${stats.appointments.pending} pending`,   color: 'text-brand-amber' },
          { icon: Pill,     label: 'Prescriptions (30d)', value: stats.prescriptions.issued_30d,       sub: `${stats.prescriptions.dispensed_30d} dispensed`, color: 'text-purple-600' },
          { icon: Activity, label: 'No-show rate (30d)',  value: `${stats.appointments.no_show_rate_30d}%`, sub: 'completed + no-show', color: 'text-brand-coral' },
        ].map(({ icon: Icon, label, value, sub, color }) => (
          <div key={label} className="card">
            <Icon className={`h-4.5 w-4.5 ${color}`} strokeWidth={1.75} />
            <p className={`mt-3 font-display text-2xl font-semibold ${color}`}>{value}</p>
            <p className="mt-0.5 font-body text-xs font-medium text-ink">{label}</p>
            <p className="mt-0.5 font-mono text-xs text-ink-faint">{sub}</p>
          </div>
        ))}
      </div>

      {/* User breakdown */}
      <div className="card">
        <h2 className="mb-4 font-display text-base font-semibold text-ink">User breakdown</h2>
        <div className="space-y-3">
          {[
            { label: 'Patients',      value: stats.users.patients,    color: 'bg-brand-teal' },
            { label: 'Doctors',       value: stats.users.doctors,     color: 'bg-brand-amber' },
            { label: 'Pharmacists',   value: stats.users.pharmacists, color: 'bg-purple-500' },
          ].map(({ label, value, color }) => (
            <div key={label}>
              <div className="mb-1 flex justify-between font-body text-xs text-ink-soft">
                <span>{label}</span>
                <span className="font-medium text-ink">{value}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-surface">
                <div
                  className={`h-full rounded-full ${color}`}
                  style={{ width: `${stats.users.total > 0 ? (value / stats.users.total) * 100 : 0}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
export default AdminDashboard
