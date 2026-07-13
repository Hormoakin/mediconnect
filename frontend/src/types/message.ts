// ══════════════════════════════════════════════════════════════
// frontend/src/types/message.ts
// ══════════════════════════════════════════════════════════════
export interface Message {
  id: number
  sender: number
  sender_name: string
  recipient: number
  recipient_name: string
  appointment: number | null
  content: string
  is_read: boolean
  read_at: string | null
  sent_at: string
}
