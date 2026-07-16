// ══════════════════════════════════════════════════════════════
// frontend/src/contexts/SocketContext.tsx
//
// Establishes one Socket.io connection per authenticated session,
// authenticated via the same JWT used for REST calls (see
// websocket_service/middleware/auth.js — shared HMAC secret).
// ══════════════════════════════════════════════════════════════
import React, { createContext, useContext, useEffect, useRef, useState } from 'react'
import { io, Socket } from 'socket.io-client'
import { useAuth } from './AuthContext'
import { getAccessToken } from '../services/api'

interface IncomingMessage {
  id: number
  sender_id: number
  sender_name: string
  recipient_id: number
  content: string
  is_read: boolean
  sent_at: string
}

interface SocketContextType {
  socket: Socket | null
  onlineUsers: Set<number>
  unreadCount: number
  clearUnread: () => void
}

const SocketContext = createContext<SocketContextType | null>(null)

const WS_URL = import.meta.env.VITE_WS_URL || 'http://localhost:3001'

export function SocketProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  const socketRef = useRef<Socket | null>(null)
  const [onlineUsers, setOnlineUsers] = useState<Set<number>>(new Set())
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    if (!user) return

    const token = getAccessToken()
    const socket = io(WS_URL, {
      auth: { token },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 2000,
    })

    socket.on('connect', () => console.log('🔌 Connected to MediConnect real-time service'))
    socket.on('connect_error', (err) => console.error('Socket connection error:', err.message))

    socket.on('user_online',  ({ user_id }: { user_id: number }) =>
      setOnlineUsers((prev) => new Set(prev).add(user_id)))
    socket.on('user_offline', ({ user_id }: { user_id: number }) =>
      setOnlineUsers((prev) => { const next = new Set(prev); next.delete(user_id); return next }))

    socket.on('new_message', (_msg: IncomingMessage) => {
      setUnreadCount((c) => c + 1)
      // Individual chat screens also listen for 'new_message' directly
      // to append to their own thread in real time.
    })

    socketRef.current = socket
    return () => { socket.disconnect(); socketRef.current = null }
  }, [user])

  return (
    <SocketContext.Provider
      value={{
        socket: socketRef.current,
        onlineUsers,
        unreadCount,
        clearUnread: () => setUnreadCount(0),
      }}
    >
      {children}
    </SocketContext.Provider>
  )
}

export function useSocket() {
  const ctx = useContext(SocketContext)
  if (!ctx) throw new Error('useSocket must be used within SocketProvider')
  return ctx
}
