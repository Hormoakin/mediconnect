// ══════════════════════════════════════════════════════════════
// frontend/src/components/common/LoadingSpinner.tsx
// ══════════════════════════════════════════════════════════════
interface Props {
  size?: 'sm' | 'md' | 'lg'
  label?: string
}

const sizeMap = { sm: 'h-5 w-5', md: 'h-8 w-8', lg: 'h-12 w-12' }

export default function LoadingSpinner({ size = 'md', label }: Props) {
  return (
    <div className="flex flex-col items-center gap-3">
      <div
        className={`${sizeMap[size]} animate-spin rounded-full border-[3px] border-brand-teal-tint border-t-brand-teal`}
        role="status"
        aria-label={label || 'Loading'}
      />
      {label && <p className="font-body text-sm text-ink-soft">{label}</p>}
    </div>
  )
}
