// ══════════════════════════════════════════════════════════════
// websocket_service/handlers/notification.js
//
// Implements FR-05.5: SMS notification when a new message arrives
// and the recipient is not currently connected to the WebSocket
// server. Calls back into the Django backend's internal API
// rather than re-implementing the Twilio integration here —
// this preserves the single-responsibility boundary established
// in Chapter 3 (the Notification Service lives in the Django app).
// ══════════════════════════════════════════════════════════════
const https = require('https');
const http  = require('http');

const BACKEND_INTERNAL_URL =
  process.env.BACKEND_INTERNAL_URL || 'http://backend-service:8000';

/**
 * Calls an internal Django endpoint to trigger an SMS fallback
 * notification when the recipient is offline.
 *
 * This requires a corresponding internal-only Django view:
 *   POST /api/v1/internal/notify-offline-message/
 *   (protected by a shared internal service token, NOT the user JWT)
 */
async function notifyOfflineRecipient(recipientId, senderName, messagePreview) {
  return new Promise((resolve) => {
    const payload = JSON.stringify({
      recipient_id: recipientId,
      sender_name:  senderName,
      preview:      messagePreview.slice(0, 100),
    });

    const url = new URL(`${BACKEND_INTERNAL_URL}/api/v1/internal/notify-offline-message/`);
    const lib = url.protocol === 'https:' ? https : http;

    const req = lib.request(
      url,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(payload),
          'X-Internal-Service-Token': process.env.INTERNAL_SERVICE_TOKEN || '',
        },
        timeout: 5000,
      },
      (res) => {
        res.on('data', () => {});
        res.on('end', () => resolve(res.statusCode === 200));
      }
    );

    req.on('error', (err) => {
      console.error('notifyOfflineRecipient request failed:', err.message);
      resolve(false);
    });
    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });

    req.write(payload);
    req.end();
  });
}

module.exports = { notifyOfflineRecipient };
