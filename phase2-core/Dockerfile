# ==========================================================
# Eón C Core Build Dockerfile
# ==========================================================
# Builds libAeon and test applications
# ==========================================================

FROM debian:bookworm-slim AS builder

LABEL maintainer="Eón Project AI"
LABEL description="Build environment for Eón C Core"
LABEL version="1.7.2"

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy C source code
COPY phase2-core /build/phase2-core

# Build libAeon
WORKDIR /build/phase2-core/libAeon
RUN mkdir -p build && cd build && \
    cmake .. && \
    make -j$(nproc)

# Build tests
WORKDIR /build/phase2-core/tests
RUN make -f ../Makefile test_core 2>/dev/null || gcc -o test_core test_core.c -I../libAeon -L../libAeon/build -laeon -lm

# Build bio-monitor
COPY phase5-applications/bio-monitor /build/bio-monitor
WORKDIR /build/bio-monitor
RUN make bio_monitor 2>/dev/null || \
    gcc -o bio_monitor bio_monitor.c -I../phase2-core/libAeon -L../phase2-core/libAeon/build -lm || true

# Build voice-kws
COPY phase5-applications/voice-command /build/voice-command
WORKDIR /build/voice-command
RUN make voice_kws 2>/dev/null || \
    gcc -o voice_kws voice_kws.c -I../phase2-core/libAeon -L../phase2-core/libAeon/build -lm || true

# Final slim image
FROM debian:bookworm-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libc6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN mkdir -p /app/bin /app/lib

# Copy built binaries (use shell to handle optional files)
COPY --from=builder /build/phase2-core/libAeon/build/aeon_demo /app/bin/aeon_demo
COPY --from=builder /build/phase2-core/libAeon/build/libaeon.a /app/lib/libaeon.a

# Optional binaries - use RUN with cp to allow failure
RUN cp /build/bio-monitor/bio_monitor /app/bin/ 2>/dev/null || true && \
    cp /build/voice-command/voice_kws /app/bin/ 2>/dev/null || true

# Set library path
ENV LD_LIBRARY_PATH=/app/lib

# Default command
CMD ["/app/bin/aeon_demo"]
