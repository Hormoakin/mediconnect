// ══════════════════════════════════════════════════════════════
// websocket_service/server.js
//
// MediConnect Real-Time Communication Service.
// Implements FR-05 (real-time doctor-patient messaging).
//
// Design rationale (see Chapter 3, Section 3.4.3 and 3.7.4):
//   - Deployed as a separate service from the Django backend
//     because long-lived WebSocket connections have different
//     scaling characteristics from stateless REST requests.
//   - Uses the Redis adapter so that messages are correctly
//     routed between users even when they are connected to
//     DIFFERENT websocket pod replicas behind the load balancer
//     (a single pod's in-memory socket registry is not enough
//     once this service is horizontally scaled).
// ══════════════════════════════════════════════════════════════
const { createServer } = require('http');
const { Server } = require('socket.io');
const { createClient } = require('redis');
const { createAdapter } = require('@socket.io/redis-adapter');

const config = require('./config');
const { socketAuthMiddleware } = require('./middleware/auth');
const { registerMessageHandlers } = require('./handlers/message');

// ── HTTP server (also serves the K8s liveness/readiness probe) ──
const httpServer = createServer((req, res) => {
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'healthy',
      service: 'mediconnect-websocket',
      connections: io?.engine?.clientsCount ?? 0,
    }));
    return;
  }
  res.writeHead(404);
  res.end();
});

// ── Socket.io server ─────────────────────────────────────────────
const io = new Server(httpServer, {
  cors: {
    origin: config.corsOrigin,
    methods: ['GET', 'POST'],
    credentials: true,
  },
  // Fallback to HTTP long-polling for clients on networks that
  // block raw WebSocket connections (see Chapter 3, Section 3.4.3
  // justification — relevant to variable Nigerian mobile networks).
  transports: ['websocket', 'polling'],
});

// ── Redis adapter setup (enables horizontal scaling) ─────────────
async function setupRedisAdapter() {
  const pubClient = createClient({ url: config.redisUrl });
  const subClient = pubClient.duplicate();

  pubClient.on('error', (err) => console.error('Redis pub client error:', err));
  subClient.on('error', (err) => console.error('Redis sub client error:', err));

  await Promise.all([pubClient.connect(), subClient.connect()]);

  io.adapter(createAdapter(pubClient, subClient));
  console.log('✅ Redis adapter connected — multi-pod message routing enabled');
}

// ── Authentication middleware (runs on every connection attempt) ─
io.use(socketAuthMiddleware);

// ── Connection handler ────────────────────────────────────────────
io.on('connection', (socket) => {
  console.log(`🔌 User ${socket.userId} (${socket.userRole}) connected — socket ${socket.id}`);

  // Join a personal room so messages can be routed to this user
  // regardless of which pod replica or which of their devices/tabs
  // is currently connected.
  socket.join(`user:${socket.userId}`);

  // Broadcast presence to anyone interested (e.g. doctor dashboard
  // showing which patients are currently online)
  socket.broadcast.emit('user_online', { user_id: socket.userId });

  // Register all chat/message event handlers for this socket
  registerMessageHandlers(io, socket);

  // ── Disconnect handling ─────────────────────────────────────────
  socket.on('disconnect', (reason) => {
    console.log(`🔌 User ${socket.userId} disconnected — reason: ${reason}`);

    // Only broadcast "offline" if this was the user's LAST connected
    // socket (they might have multiple tabs/devices open)
    io.in(`user:${socket.userId}`).fetchSockets().then((remaining) => {
      if (remaining.length === 0) {
        socket.broadcast.emit('user_offline', { user_id: socket.userId });
      }
    });
  });

  socket.on('error', (err) => {
    console.error(`Socket error for user ${socket.userId}:`, err.message);
  });
});

// ── Connection error handling (auth failures land here) ──────────
io.engine.on('connection_error', (err) => {
  console.error('Connection error:', err.req?.url, '-', err.message);
});

// ── Graceful shutdown ──────────────────────────────────────────────
function shutdown(signal) {
  console.log(`\n${signal} received — shutting down gracefully...`);
  io.close(() => {
    console.log('Socket.io server closed.');
    httpServer.close(() => {
      console.log('HTTP server closed.');
      process.exit(0);
    });
  });
  // Force exit if graceful shutdown takes too long
  setTimeout(() => process.exit(1), 10000);
}
process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT',  () => shutdown('SIGINT'));

// ── Start server ──────────────────────────────────────────────────
async function start() {
  try {
    await setupRedisAdapter();
    httpServer.listen(config.port, () => {
      console.log(`🚀 MediConnect WebSocket service listening on port ${config.port}`);
      console.log(`   CORS origin: ${config.corsOrigin}`);
    });
  } catch (err) {
    console.error('Failed to start WebSocket service:', err);
    process.exit(1);
  }
}

start();
