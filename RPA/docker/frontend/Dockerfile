# RPA Frontend - React + Nginx
# Multi-stage build: build React app, then serve with Nginx

# Stage 1: Build React App
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --silent

# Copy source code
COPY web/ ./web/
COPY public/ ./public/

# Build arguments for environment variables
ARG REACT_APP_API_URL=/api
ARG REACT_APP_WS_URL=/ws

# Set environment variables for build
ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV REACT_APP_WS_URL=$REACT_APP_WS_URL

# Build the app
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

LABEL org.opencontainers.image.source="https://github.com/BBRNGIT/RPA"
LABEL org.opencontainers.image.description="RPA Frontend - React + Nginx"
LABEL org.opencontainers.image.licenses="MIT"

# Install curl for health checks
RUN apk add --no-cache curl

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY docker/frontend/nginx.conf /etc/nginx/nginx.conf
COPY docker/frontend/default.conf /etc/nginx/conf.d/default.conf

# Copy built app from builder
COPY --from=builder /app/build /usr/share/nginx/html

# Create directories for SSL
RUN mkdir -p /etc/nginx/ssl

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
