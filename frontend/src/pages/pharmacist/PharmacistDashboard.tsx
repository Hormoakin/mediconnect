// ══════════════════════════════════════════════════════════════
// frontend/src/pages/pharmacist/PharmacistDashboard.tsx
// ══════════════════════════════════════════════════════════════
import { useEffect, useState } from 'react'
import { Pill, CheckCircle2, AlertCircle } from 'lucide-react'
import { api } from '../../services/api'
import type { Prescription } from '../../types/prescription'
import StatusBadge from '../../components/common/StatusBadge'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import EmptyState from '../../components/common/EmptyState'
import { format } from 'date-fns'

export function PharmacistDashboard() {
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([])
  const [loading, setLoading] = useState(true)
  const [dispensing, setDispensing] = useState<number | null>(null)

  useEffect(() => {
    api.get('/prescriptions/')
      .then(r => setPrescriptions(r.data.results ?? r.data))
      .finally(() => setLoading(false))
  }, [])

  const handleDispense = async (id: number) => {
    setDispensing(id)
    try {
      await api.patch(`/prescriptions/${id}/dispense/`)
      setPrescriptions(prev => prev.map(rx => rx.id === id ? { ...rx, status: 'dispensed' } : rx))
    } finally {
      setDispensing(null)
    }
  }

  if (loading) return <div className="flex justify-center pt-20"><LoadingSpinner size="lg" /></div>

  const pending   = prescriptions.filter(rx => rx.status === 'issued')
  const dispensed = prescriptions.filter(rx => rx.status === 'dispensed')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-ink">Pharmacy Dashboard</h1>
        <p className="mt-1 font-body text-sm text-ink-soft">
          {pending.length} prescription{pending.length !== 1 ? 's' : ''} awaiting dispensing
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {[
          { icon: AlertCircle,  label: 'Pending',   value: pending.length,   color: 'text-brand-amber' },
          { icon: CheckCircle2, label: 'Dispensed', value: dispensed.length, color: 'text-emerald-600' },
        ].map(({ icon: Icon, label, value, color }) => (
          <div key={label} className="card text-center">
            <Icon className={`mx-auto h-5 w-5 ${color}`} strokeWidth={1.75} />
            <p className={`mt-2 font-display text-2xl font-semibold ${color}`}>{value}</p>
            <p className="mt-0.5 font-body text-xs text-ink-soft">{label}</p>
          </div>
        ))}
      </div>

      <section className="card">
        <h2 className="mb-4 font-display text-base font-semibold text-ink">Pending Prescriptions</h2>
        {pending.length === 0
          ? <EmptyState icon={Pill} title="All clear" description="No prescriptions awaiting dispensing." />
          : (
            <ul className="divide-y divide-border-soft">
              {pending.map(rx => (
                <li key={rx.id} className="py-4 flex items-start justify-between">
                  <div>
                    <p className="font-body text-sm font-semibold text-ink">{rx.medication}</p>
                    <p className="font-body text-xs text-ink-soft">{rx.dosage} · {rx.frequency} · {rx.duration_days} days</p>
                    {rx.instructions && <p className="mt-0.5 font-body text-xs text-ink-faint">Note: {rx.instructions}</p>}
                    <p className="mt-1.5 font-mono text-xs text-ink-faint">
                      Issued: {format(new Date(rx.issued_at), 'd MMM yyyy')} · Rx #{rx.id}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDispense(rx.id)}
                    disabled={dispensing === rx.id}
                    className="btn-primary !py-1.5 !px-3 text-xs whitespace-nowrap"
                  >
                    {dispensing === rx.id ? 'Processing…' : 'Mark dispensed'}
                  </button>
                </li>
              ))}
            </ul>
          )}
      </section>
    </div>
  )
}
export default PharmacistDashboard
