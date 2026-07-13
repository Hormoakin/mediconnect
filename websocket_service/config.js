
// ══════════════════════════════════════════════════════════════
// websocket_service/config.js
// ══════════════════════════════════════════════════════════════
require('dotenv').config();
 
module.exports = {
  port:           process.env.PORT || 3001,
  jwtSecret:      process.env.JWT_SECRET || 'dev-secret-key-change-in-production',
  redisUrl:       process.env.REDIS_URL || 'redis://localhost:6379/3',
  corsOrigin:     process.env.CORS_ORIGIN || 'https://mediconnect.salman-aak.com',
  db: {
    host:     process.env.DATABASE_HOST || 'localhost',
    port:     process.env.DATABASE_PORT || 5432,
    database: process.env.DATABASE_NAME || 'mediconnect',
    user:     process.env.DATABASE_USER || 'mediconnect_user',
    password: process.env.DATABASE_PASSWORD || 'mediconnect_dev_password',
  },
};
