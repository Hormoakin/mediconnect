// ══════════════════════════════════════════════════════════════
// frontend/Dockerfile  (multi-stage: dev target + production build)
// ══════════════════════════════════════════════════════════════
# ── Development stage (used by docker-compose.yml) ──────────────
FROM node:20-alpine AS development
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]
 
# ── Build stage (production) ─────────────────────────────────────
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
 
# ── Production stage — Nginx serving static files ────────────────
FROM nginx:1.27-alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

