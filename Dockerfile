# ==============================================================================
# OpenLore Multi-Stage Enterprise Production Container
# Stage 1: Build React 19 / Three.js Frontend Studio Cockpit
# Stage 2: Python 3.12 Runtime with Zero-Dependency API Server & Live Link Engine
# ==============================================================================

# --- Stage 1: Frontend Build ---
FROM node:22-alpine AS frontend-builder
WORKDIR /build/web

COPY web/package*.json ./
RUN npm ci

COPY web/ ./
RUN npm run build

# --- Stage 2: Production Python Runtime ---
FROM python:3.12-slim AS runtime

LABEL maintainer="OpenLore Engineering <engineering@openlore.io>"
LABEL description="OpenLore: Git for 3D worlds, game lore, and Hollywood pipelines."
LABEL version="2.0.0"

WORKDIR /app

# Install runtime dependencies and security updates
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy build files and install package
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY schemas/ ./schemas/

# Copy compiled frontend assets from Stage 1
COPY --from=frontend-builder /build/web/dist ./web/dist

RUN pip install --no-cache-dir . "psycopg[binary]"

# Create non-root system user for security hardening
RUN groupadd -r openlore && useradd -r -g openlore -d /app -s /sbin/nologin openlore \
    && mkdir -p /app/data/cas /app/data/lore /app/stages /app/builds \
    && chown -R openlore:openlore /app

USER openlore

ENV PYTHONUNBUFFERED=1 \
    OPENLORE_CAS_ROOT="/app/data/cas" \
    OPENLORE_AUTH_ENABLED="true"

# Expose HTTP/WebSocket (8000) and Unreal Live Link UDP (11111/11112)
EXPOSE 8000 11111/udp 11112/udp

HEALTHCHECK --interval=20s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["openlore", "web", "--host", "0.0.0.0", "--port", "8000", "--static-dir", "/app/web/dist"]
