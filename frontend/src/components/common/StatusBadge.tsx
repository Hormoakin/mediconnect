// ══════════════════════════════════════════════════════════════
// frontend/src/components/common/StatusBadge.tsx
// ══════════════════════════════════════════════════════════════
import type { AppointmentStatus } from '../../types/appointment'
import type { PrescriptionStatus } from '../../types/prescription'

const labels: Record<string, string> = {
  pending: 'Pending', confirmed: 'Confirmed', completed: 'Completed',
  cancelled: 'Cancelled', no_show: 'No Show', issued: 'Issued',
  dispensed: 'Dispensed', expired: 'Expired',
}

const classMap: Record<string, string> = {
  pending: 'badge-pending', confirmed: 'badge-confirmed', completed: 'badge-completed',
  cancelled: 'badge-cancelled', no_show: 'badge-cancelled', issued: 'badge-pending',
  dispensed: 'badge-completed', expired: 'badge-cancelled',
}

export default function StatusBadge({ status }: { status: AppointmentStatus | PrescriptionStatus }) {
  return <span className={`badge ${classMap[status] || 'badge-pending'}`}>{labels[status] || status}</span>
}
