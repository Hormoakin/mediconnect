// ══════════════════════════════════════════════════════════════
// frontend/src/components/common/EmptyState.tsx
//
// Treats emptiness as an invitation to act (per design guidance) —
// every empty list explains what's missing and what to do next,
// rather than a bare "No data" message.
// ══════════════════════════════════════════════════════════════
import { LucideIcon } from 'lucide-react'

interface Props {
  icon: LucideIcon
  title: string
  description: string
  action?: { label: string; onClick: () => void }
}

export default function EmptyState({ icon: Icon, title, description, action }: Props) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl2 border border-dashed border-border-soft bg-surface-raised py-16 px-6 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-brand-teal-tint">
        <Icon className="h-7 w-7 text-brand-teal" strokeWidth={1.75} />
      </div>
      <h3 className="font-display text-lg font-semibold text-ink">{title}</h3>
      <p className="mt-1.5 max-w-sm font-body text-sm text-ink-soft">{description}</p>
      {action && (
        <button onClick={action.onClick} className="btn-primary mt-5">
          {action.label}
        </button>
      )}
    </div>
  )
}
