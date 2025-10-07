# =============================================================================
# DRP (Decentralized Rights Protocol) - Multi-stage Docker Build
# =============================================================================
# This Dockerfile creates a production-ready container for the DRP blockchain
# with optimized layers, security best practices, and multi-architecture support

# =============================================================================
# Stage 1: Build Environment
# =============================================================================
FROM python:3.11-slim as builder

# Set environment variables for build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    make \
    nasm \
    libssl-dev \
    libffi-dev \
    libgmp-dev \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /build

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 2: Assembly Code Compilation
# =============================================================================
FROM builder as asm-builder

# Copy assembly source code
COPY src/crypto/hash_asm.asm ./src/crypto/
COPY src/crypto/build_asm.sh ./src/crypto/

# Build assembly library
WORKDIR /build/src/crypto
RUN chmod +x build_asm.sh && ./build_asm.sh

# =============================================================================
# Stage 3: Production Runtime
# =============================================================================
FROM python:3.11-slim as runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DRP_ENV=production \
    DRP_LOG_LEVEL=INFO

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    libffi8 \
    libgmp10 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r drp && useradd -r -g drp drp

# Create application directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/drp/.local

# Copy assembly libraries from asm-builder stage
COPY --from=asm-builder /build/src/crypto/libhash.* ./src/crypto/

# Copy application source code
COPY --chown=drp:drp . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/keys && \
    chown -R drp:drp /app

# Switch to non-root user
USER drp

# Expose ports
EXPOSE 8000 8080 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "app.py"]

# =============================================================================
# Stage 4: Development Environment (Optional)
# =============================================================================
FROM runtime as development

# Switch back to root for development tools
USER root

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    git \
    htop \
    strace \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN pip install --no-cache-dir \
    pytest \
    flake8 \
    pytest-cov \
    black \
    isort \
    mypy

# Switch back to drp user
USER drp

# Override command for development
CMD ["python", "-m", "pytest", "tests/", "-v"]

# =============================================================================
# Stage 5: Testing Environment
# =============================================================================
FROM runtime as testing

# Install testing dependencies
USER root
RUN pip install --no-cache-dir pytest pytest-cov flake8

USER drp

# Run tests
CMD ["python", "-m", "pytest", "tests/", "--cov=src", "--cov-report=html"]

