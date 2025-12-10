#!/bin/bash
# ==========================================================
# Proyecto Eón Docker Launcher v1.8.1
# ==========================================================
# Launches the Eón ecosystem via Docker
#
# Usage: ./start_docker.sh [--tinylm-only]
# ==========================================================

set -e

echo "=== Proyecto Eón Docker Launcher v1.8.1 ==="

# Parse arguments
TINYLM_ONLY=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --tinylm-only)
            TINYLM_ONLY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --tinylm-only   Only start TinyLM service"
            echo "  -h, --help      Show this help"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

# 1. Create network
echo "[1/4] Creating network..."
docker network create eon-net 2>/dev/null || true

# 2. Build images
echo "[2/4] Building TinyLM..."
docker build -t eonprojectai_tinylm -f phase7-language/Dockerfile .

if [ "$TINYLM_ONLY" = false ]; then
    echo "[2/4] Building Collective Mind..."
    docker build -t eonprojectai_collective-mind -f phase6-collective/Dockerfile .
fi

# 3. Stop running containers
echo "[3/4] Cleaning up..."
docker rm -f tinylm collective-mind 2>/dev/null || true

# 4. Run containers
echo "[4/4] Starting services..."

# TinyLM (Background)
docker run -d \
  --name tinylm \
  --network eon-net \
  -p 5001:5001 \
  -v "$(pwd)/phase7-language:/app/phase7-language" \
  -v "$(pwd)/phase1-foundations:/app/phase1-foundations" \
  eonprojectai_tinylm

if [ "$TINYLM_ONLY" = false ]; then
    # Collective Mind (Background)
    docker run -d \
      --name collective-mind \
      --network eon-net \
      -v "$(pwd)/phase6-collective:/app/phase6-collective" \
      -v "$(pwd)/phase1-foundations:/app/phase1-foundations" \
      eonprojectai_collective-mind
fi

echo ""
echo "✅ Services started!"
echo "   - TinyLM: http://localhost:5001"
if [ "$TINYLM_ONLY" = false ]; then
    echo "   - Collective Mind: docker logs -f collective-mind"
fi
echo ""
echo "📋 Commands:"
echo "   docker logs -f tinylm          # View TinyLM logs"
echo "   docker stop tinylm             # Stop TinyLM"
echo "   docker rm -f tinylm            # Remove TinyLM container"
