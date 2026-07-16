// ══════════════════════════════════════════════════════════════
// frontend/src/pages/Chat.tsx
// ══════════════════════════════════════════════════════════════
import { useEffect, useState, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { Send } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useSocket } from '../contexts/SocketContext'
import { api } from '../services/api'
import type { Message } from '../types/message'
import { format } from 'date-fns'
import clsx from 'clsx'

export default function Chat() {
  const { userId } = useParams<{ userId: string }>()
  const { user } = useAuth()
  const { socket } = useSocket()
  const [messages, setMessages] = useState<Message[]>([])
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [recipientName, setRecipientName] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!userId) return
    api.get(`/messages/${userId}/`)
      .then(r => {
        const msgs: Message[] = r.data.results ?? r.data
        setMessages(msgs)
        if (msgs.length > 0) {
          const other = msgs[0].sender === user?.id ? msgs[0].recipient_name : msgs[0].sender_name
          setRecipientName(other)
        }
      })
      .finally(() => setLoading(false))
  }, [userId, user?.id])

  useEffect(() => {
    if (!socket) return
    socket.on('new_message', (msg: Message) => {
      if (String(msg.sender_id) === userId || String(msg.recipient_id) === userId) {
        setMessages(prev => [...prev, msg as any])
      }
    })
    return () => { socket.off('new_message') }
  }, [socket, userId])

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const sendMessage = () => {
    if (!content.trim() || !socket || !userId || sending) return
    setSending(true)
    socket.emit('send_message', { recipient_id: parseInt(userId), content: content.trim() }, (ack: any) => {
      if (ack?.success) {
        setMessages(prev => [...prev, ack.message])
        setContent('')
      }
      setSending(false)
    })
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-teal-tint font-display text-sm font-semibold text-brand-teal-deep">
          {recipientName.charAt(0) || '?'}
        </div>
        <div>
          <p className="font-display text-base font-semibold text-ink">{recipientName || 'Chat'}</p>
          <p className="font-mono text-xs text-ink-faint">Real-time · end-to-end logged</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto rounded-xl border border-border-soft bg-surface-raised p-4 space-y-3">
        {loading ? <div className="flex justify-center pt-10"><LoadingSpinner /></div>
          : messages.map(msg => {
            const mine = msg.sender === user?.id
            return (
              <div key={msg.id} className={clsx('flex', mine ? 'justify-end' : 'justify-start')}>
                <div className={clsx(
                  'max-w-[75%] rounded-2xl px-4 py-2.5',
                  mine ? 'rounded-tr-sm bg-brand-teal text-white' : 'rounded-tl-sm bg-surface text-ink'
                )}>
                  <p className="font-body text-sm">{msg.content}</p>
                  <p className={clsx('mt-0.5 font-mono text-[10px]', mine ? 'text-white/60' : 'text-ink-faint')}>
                    {format(new Date(msg.sent_at), 'h:mm a')}
                    {mine && msg.is_read && ' · Read'}
                  </p>
                </div>
              </div>
            )
          })}
        <div ref={bottomRef} />
      </div>

      <div className="mt-3 flex gap-3">
        <input
          className="input-field flex-1"
          placeholder="Type your message…"
          value={content}
          onChange={e => setContent(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), sendMessage())}
        />
        <button onClick={sendMessage} disabled={!content.trim() || sending} className="btn-primary !px-4">
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
