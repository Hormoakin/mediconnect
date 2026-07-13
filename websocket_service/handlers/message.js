// ══════════════════════════════════════════════════════════════
// websocket_service/handlers/message.js
//
// Handles real-time messaging events (FR-05).
// Persists every message to PostgreSQL via direct pg query
// (not through the Django ORM, since this is a separate process —
// see Chapter 3, Section 3.4.1 service-boundary justification).
// ══════════════════════════════════════════════════════════════
const { Pool } = require('pg');
const config = require('../config');

const pool = new Pool(config.db);

/**
 * Registers all message-related Socket.io event handlers
 * for a single connected socket.
 */
function registerMessageHandlers(io, socket) {

  // ── Send a message ──────────────────────────────────────────
  socket.on('send_message', async (data, callback) => {
    const { recipient_id, content, appointment_id } = data;

    if (!recipient_id || !content || !content.trim()) {
      return callback?.({ error: 'recipient_id and content are required' });
    }

    try {
      // Persist to PostgreSQL (messages table — shared schema with Django)
      const result = await pool.query(
        `INSERT INTO messages (sender_id, recipient_id, appointment_id, content, is_read, sent_at)
         VALUES ($1, $2, $3, $4, false, NOW())
         RETURNING id, sent_at`,
        [socket.userId, recipient_id, appointment_id || null, content.trim()]
      );

      const saved = result.rows[0];

      const messagePayload = {
        id:             saved.id,
        sender_id:      socket.userId,
        sender_name:    socket.fullName,
        recipient_id,
        appointment_id,
        content:        content.trim(),
        is_read:        false,
        sent_at:        saved.sent_at,
      };

      // Acknowledge to sender immediately (optimistic UI confirmation)
      callback?.({ success: true, message: messagePayload });

      // Deliver to recipient's room if they're connected (across any
      // websocket pod instance, via the Redis adapter — see server.js)
      io.to(`user:${recipient_id}`).emit('new_message', messagePayload);

      // If recipient is NOT currently connected anywhere, trigger
      // an SMS fallback notification (FR-05.5) via the notification handler
      const recipientSockets = await io.in(`user:${recipient_id}`).fetchSockets();
      if (recipientSockets.length === 0) {
        const { notifyOfflineRecipient } = require('./notification');
        await notifyOfflineRecipient(recipient_id, socket.fullName, content);
      }

    } catch (err) {
      console.error('send_message failed:', err.message);
      callback?.({ error: 'Failed to send message. Please try again.' });
    }
  });

  // ── Mark message(s) as read ─────────────────────────────────
  socket.on('mark_read', async ({ message_ids, sender_id }) => {
    if (!Array.isArray(message_ids) || message_ids.length === 0) return;

    try {
      await pool.query(
        `UPDATE messages SET is_read = true, read_at = NOW()
         WHERE id = ANY($1::int[]) AND recipient_id = $2`,
        [message_ids, socket.userId]
      );

      // Notify the original sender that their messages were read
      if (sender_id) {
        io.to(`user:${sender_id}`).emit('messages_read', {
          message_ids,
          read_by: socket.userId,
          read_at: new Date().toISOString(),
        });
      }
    } catch (err) {
      console.error('mark_read failed:', err.message);
    }
  });

  // ── Typing indicator ─────────────────────────────────────────
  socket.on('typing', ({ recipient_id, is_typing }) => {
    if (!recipient_id) return;
    io.to(`user:${recipient_id}`).emit('user_typing', {
      user_id: socket.userId,
      is_typing: !!is_typing,
    });
  });
}

module.exports = { registerMessageHandlers, pool };
