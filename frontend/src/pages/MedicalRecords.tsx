// ══════════════════════════════════════════════════════════════
// frontend/src/pages/MedicalRecords.tsx
// ══════════════════════════════════════════════════════════════
import { useEffect, useState } from 'react'
import { FileText, ChevronDown, ChevronUp } from 'lucide-react'
import { api } from '../services/api'
import type { ClinicalRecord } from '../types/record'
import LoadingSpinner from '../components/common/LoadingSpinner'
import EmptyState from '../components/common/EmptyState'
import { format } from 'date-fns'

export default function MedicalRecords() {
  const [records, setRecords] = useState<ClinicalRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<number | null>(null)

  useEffect(() => {
    api.get('/records/').then(r => setRecords(r.data.results ?? r.data)).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center pt-20"><LoadingSpinner size="lg" /></div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-ink">Medical Records</h1>
        <p className="mt-1 font-body text-sm text-ink-soft">{records.length} record{records.length !== 1 ? 's' : ''} on file</p>
      </div>

      {records.length === 0
        ? <EmptyState icon={FileText} title="No records yet" description="Your clinical records from consultations will appear here." />
        : (
          <div className="space-y-3">
            {records.map(rec => (
              <div key={rec.id} className="card">
                <button
                  onClick={() => setExpanded(expanded === rec.id ? null : rec.id)}
                  className="flex w-full items-start justify-between text-left"
                >
                  <div>
                    <p className="font-display text-sm font-semibold text-ink">{rec.diagnosis || rec.chief_complaint}</p>
                    <p className="mt-0.5 font-body text-xs text-ink-soft">
                      Dr. {rec.doctor_name} · {format(new Date(rec.created_at), 'd MMM yyyy')}
                    </p>
                  </div>
                  {expanded === rec.id ? <ChevronUp className="h-4 w-4 text-ink-faint" /> : <ChevronDown className="h-4 w-4 text-ink-faint" />}
                </button>
                {expanded === rec.id && (
                  <div className="mt-4 space-y-3 border-t border-border-soft pt-4">
                    {[
                      { label: 'Chief complaint',     value: rec.chief_complaint },
                      { label: 'Diagnosis',           value: rec.diagnosis },
                      { label: 'Treatment plan',      value: rec.treatment_plan },
                      { label: 'Examination findings',value: rec.examination_findings },
                      { label: 'History of illness',  value: rec.history_of_illness },
                      { label: 'Follow-up date',      value: rec.follow_up_date ? format(new Date(rec.follow_up_date), 'd MMM yyyy') : null },
                    ].filter(f => f.value).map(({ label, value }) => (
                      <div key={label}>
                        <p className="font-body text-xs font-semibold uppercase tracking-wide text-ink-faint">{label}</p>
                        <p className="mt-0.5 font-body text-sm text-ink">{value}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
    </div>
  )
}
