FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Caddy: serves the built frontend and reverse-proxies API calls to the
# backend, getting automatic HTTPS for free when DOMAIN is a real public
# domain — no separate nginx + certbot setup needed.
FROM caddy:2-alpine
COPY --from=build /app/dist /srv/app
COPY Caddyfile /etc/caddy/Caddyfile
