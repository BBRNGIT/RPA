# RPA Frontend - Next.js + Nginx
# Multi-stage build: build Next.js app, then serve with Nginx
#
# Build context: Parent directory (contains package.json, src/, etc.)
# Dockerfile path: RPA/docker/frontend/Dockerfile

# =============================================================================
# Stage 1: Build Next.js App
# =============================================================================
FROM node:20-alpine AS builder

# Install dependencies for native modules
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy package files first (for better caching)
COPY package.json bun.lock* package-lock.json* ./

# Install dependencies using npm (fallback if bun.lock exists)
RUN npm ci --legacy-peer-deps || npm install --legacy-peer-deps

# Copy source code
COPY src/ ./src/
COPY public/ ./public/
COPY next.config.ts tsconfig.json tailwind.config.ts postcss.config.mjs ./
COPY components.json ./

# Set environment variables for build
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Build arguments for runtime config
ARG NEXT_PUBLIC_API_URL=/api
ARG NEXT_PUBLIC_WS_URL=/ws

# Build the Next.js app
RUN npm run build

# =============================================================================
# Stage 2: Production Image with Nginx
# =============================================================================
FROM nginx:alpine

LABEL org.opencontainers.image.source="https://github.com/BBRNGIT/RPA"
LABEL org.opencontainers.image.description="RPA Frontend - Next.js + Nginx"
LABEL org.opencontainers.image.licenses="MIT"

# Install curl for health checks
RUN apk add --no-cache curl

# Remove default nginx config
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY RPA/docker/frontend/nginx.conf /etc/nginx/nginx.conf
COPY RPA/docker/frontend/default.conf /etc/nginx/conf.d/default.conf

# Copy Next.js static files (public folder)
COPY --from=builder /app/public /usr/share/nginx/html

# Copy Next.js build output
COPY --from=builder /app/.next/static /usr/share/nginx/html/_next/static

# Create SPA fallback for client-side routing
RUN echo '<!DOCTYPE html><html><head><meta charset="utf-8"><title>RPA Intelligence Engine</title><script>window.location.href="/";</script></head><body></body></html>' > /usr/share/nginx/html/index.html

# Create directories for SSL (optional)
RUN mkdir -p /etc/nginx/ssl

# Set proper permissions
RUN chown -R nginx:nginx /usr/share/nginx/html

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
