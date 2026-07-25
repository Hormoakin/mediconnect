# ── Development stage ───────────────────────────────────────────
FROM node:20-alpine AS development
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]

# ── Build stage ─────────────────────────────────────────────────
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Production API URL
ENV VITE_API_URL=https://api.mediconnect.salman-aak.com/api/v1
ENV VITE_WS_URL=https://ws.mediconnect.salman-aak.com

RUN npm run build

# ── Production stage ────────────────────────────────────────────
FROM nginx:1.27-alpine AS production

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

