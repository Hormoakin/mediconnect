// ══════════════════════════════════════════════════════════════
// frontend/src/pages/patient/SymptomChecker.tsx
// ══════════════════════════════════════════════════════════════
import { useState } from 'react'
import { Stethoscope as StethIcon, AlertTriangle, ArrowRight as ArrowRightIcon, Info } from 'lucide-react'
import type { SymptomCheckResult } from '../../types/ai'

const URGENCY_STYLES = {
  low:       'bg-emerald-50 text-emerald-700 border-emerald-200',
  medium:    'bg-brand-amber-tint text-amber-800 border-amber-200',
  high:      'bg-orange-50 text-orange-700 border-orange-200',
  emergency: 'bg-brand-coral-tint text-red-700 border-red-200',
}

export function SymptomChecker() {
  const [symptoms, setSymptoms] = useState('')
  const [result, setResult] = useState<SymptomCheckResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleCheck = async () => {
    if (symptoms.trim().length < 5) {
      setError('Please describe your symptoms in a bit more detail.')
      return
    }
    setError('')
    setLoading(true)
    try {
      const { data } = await api.post<SymptomCheckResult>('/ai/symptom-check/', { symptoms })
      setResult(data)
    } catch {
      setError('The AI service is temporarily unavailable. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-ink">AI Symptom Checker</h1>
        <p className="mt-1 font-body text-sm text-ink-soft">
          Describe what you're experiencing in your own words.
        </p>
      </div>

      <div className="card space-y-4">
        <div>
          <label className="label-text" htmlFor="symptoms">What's going on?</label>
          <textarea
            id="symptoms"
            rows={4}
            className="input-field resize-none"
            placeholder="e.g. I've had a fever since yesterday, bad headache, and my joints feel stiff…"
            value={symptoms}
            onChange={e => setSymptoms(e.target.value)}
          />
          {error && <p className="mt-1.5 font-body text-xs text-red-600">{error}</p>}
        </div>
        <button onClick={handleCheck} disabled={loading || symptoms.trim().length < 5} className="btn-primary w-full">
          {loading ? 'Analysing your symptoms…' : (<><StethIcon className="h-4 w-4" /> Analyse symptoms</>)}
        </button>
      </div>

      {result && (
        <div className="space-y-4">
          {/* Urgency */}
          <div className={`rounded-xl border p-4 ${URGENCY_STYLES[result.analysis.urgency_level]}`}>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              <span className="font-body text-sm font-semibold capitalize">
                Urgency: {result.analysis.urgency_level}
              </span>
            </div>
            <p className="mt-1 font-body text-sm">{result.analysis.urgency_reason}</p>
          </div>

          {/* Conditions */}
          <div className="card space-y-3">
            <h2 className="font-display text-base font-semibold text-ink">Possible conditions</h2>
            {result.analysis.possible_conditions.map(cond => (
              <div key={cond.condition} className="rounded-lg bg-surface p-3">
                <div className="flex items-center justify-between">
                  <span className="font-body text-sm font-medium text-ink">{cond.condition}</span>
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 w-20 overflow-hidden rounded-full bg-border-soft">
                      <div
                        className="h-full rounded-full bg-brand-teal"
                        style={{ width: `${cond.confidence * 100}%` }}
                      />
                    </div>
                    <span className="font-mono text-xs text-ink-faint">
                      {(cond.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
                {cond.description && (
                  <p className="mt-1 font-body text-xs text-ink-soft">{cond.description}</p>
                )}
              </div>
            ))}
          </div>

          {/* Recommended specialist + CTA */}
          <div className="card flex items-center justify-between gap-4">
            <div>
              <p className="font-body text-xs text-ink-soft">Recommended specialist</p>
              <p className="font-display text-base font-semibold text-ink">
                {result.analysis.recommended_specialist}
              </p>
            </div>
            <a href="/doctors" className="btn-primary !py-2 text-sm whitespace-nowrap">
              Book one <ArrowRightIcon className="h-3.5 w-3.5" />
            </a>
          </div>

          {/* Actions */}
          {result.analysis.recommended_actions.length > 0 && (
            <div className="card space-y-2">
              <h2 className="font-display text-sm font-semibold text-ink">Recommended actions</h2>
              <ul className="space-y-1">
                {result.analysis.recommended_actions.map((action, i) => (
                  <li key={i} className="flex items-start gap-2 font-body text-sm text-ink-soft">
                    <span className="mt-0.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-brand-teal" />
                    {action}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Disclaimer */}
          <div className="flex gap-2.5 rounded-xl bg-surface p-4">
            <Info className="mt-0.5 h-4 w-4 flex-shrink-0 text-ink-faint" />
            <p className="font-body text-xs leading-relaxed text-ink-faint">
              {result.analysis.disclaimer}
            </p>
          </div>

          <p className="text-center font-mono text-xs text-ink-faint">
            Analysis completed in {(result.response_time_ms / 1000).toFixed(1)}s
          </p>
        </div>
      )}
    </div>
  )
}
export default SymptomChecker
