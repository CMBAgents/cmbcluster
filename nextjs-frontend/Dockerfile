# Multi-stage Dockerfile for Next.js production deployment
# Based on existing Python Dockerfile patterns with Node.js optimizations

# Stage 1: Base stage with Node.js
FROM public.ecr.aws/docker/library/node:18-alpine AS base
WORKDIR /app

# Install system dependencies (matching Python setup)
RUN apk update && apk add --no-cache \
    curl \
    ca-certificates \
    && rm -rf /var/cache/apk/*

# Stage 2: Dependencies stage - Install and cache node_modules
FROM base AS deps
# Copy package files
COPY package.json package-lock.json* ./
# Install dependencies with production optimizations
RUN npm ci --only=production --prefer-offline --no-audit --progress=false && \
    npm cache clean --force

# Stage 3: Builder stage - Build the application
FROM base AS builder
WORKDIR /app

# Copy package files and install all dependencies (including devDependencies)
COPY package.json package-lock.json* ./
RUN npm ci --prefer-offline --no-audit --progress=false

# Copy source code
COPY . .

# Set build-time environment variables (minimal values for build)
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV SKIP_ENV_VALIDATION=true
# Remove hardcoded NEXT_PUBLIC_* vars - these will be set at runtime via API routes

# Build the application with production optimizations
RUN npm run build

# Stage 4: Runner stage - Final production image
FROM base AS runner
WORKDIR /app

# Create non-root user (matching Python container pattern)
# Using same UID/GID as Python container for consistency
RUN addgroup -g 1001 -S nextjs && \
    adduser -S nextjs -u 1001 -G nextjs -h /app -s /bin/sh

# Set production environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=8501
ENV HOSTNAME="0.0.0.0"

# Copy built application from builder stage
COPY --from=builder --chown=nextjs:nextjs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nextjs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nextjs /app/public ./public

# Create necessary directories and set permissions
RUN mkdir -p /tmp/.next && \
    chown -R nextjs:nextjs /tmp/.next /app

# Switch to non-root user
USER nextjs

# Health check (matching Python container pattern)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/api/health || exit 1

# Expose port 8501 (same as Streamlit)
EXPOSE 8501

# Start the application
CMD ["node", "server.js"]