
// ══════════════════════════════════════════════════════════════
// websocket_service/middleware/auth.js
//
// JWT authentication middleware for Socket.io connections.
// Validates the same JWT issued by the Django backend
// (Section 3.8.1 — shared HMAC-SHA256 secret).
// ══════════════════════════════════════════════════════════════
const jwt = require('jsonwebtoken');
const config = require('../config');
 
function socketAuthMiddleware(socket, next) {
  const token = socket.handshake.auth?.token || socket.handshake.query?.token;
 
  if (!token) {
    return next(new Error('AUTH_REQUIRED: No token provided'));
  }
 
  try {
    const payload = jwt.verify(token, config.jwtSecret, { algorithms: ['HS256'] });
 
    // Django SimpleJWT embeds user_id, role, full_name (see MediConnectTokenObtainSerializer)
    socket.userId   = payload.user_id;
    socket.userRole = payload.role;
    socket.fullName = payload.full_name;
 
    if (!socket.userId || !socket.userRole) {
      return next(new Error('AUTH_INVALID: Token missing required claims'));
    }
 
    next();
  } catch (err) {
    if (err.name === 'TokenExpiredError') {
      return next(new Error('AUTH_EXPIRED: Token has expired'));
    }
    return next(new Error('AUTH_INVALID: Token verification failed'));
  }
}
 
module.exports = { socketAuthMiddleware };
 
