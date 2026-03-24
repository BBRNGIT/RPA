# RPA Frontend - Next.js Static Export + Nginx
# Build context: Repository root (.)

# Stage 1: Build Next.js App
FROM node:20-alpine AS builder

RUN apk add --no-cache libc6-compat

WORKDIR /app

COPY package.json package-lock.json* ./

RUN npm ci --legacy-peer-deps || npm install --legacy-peer-deps

COPY src/ ./src/
COPY public/ ./public/
COPY next.config.ts tsconfig.json tailwind.config.ts postcss.config.mjs components.json ./

ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

LABEL org.opencontainers.image.source="https://github.com/BBRNGIT/RPA"
LABEL org.opencontainers.image.description="RPA Frontend"

RUN apk add --no-cache curl && rm -f /etc/nginx/conf.d/default.conf

COPY RPA/docker/frontend/nginx.conf /etc/nginx/nginx.conf
COPY RPA/docker/frontend/default.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/public /usr/share/nginx/html
COPY --from=builder /app/.next/static /usr/share/nginx/html/_next/static

RUN echo '<!DOCTYPE html><html><head><meta charset="utf-8"><title>RPA</title></head><body><div id="root"></div></body></html>' > /usr/share/nginx/html/index.html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
