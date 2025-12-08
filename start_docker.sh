#!/bin/bash
set -e

echo "=== Proyecto Eón Docker Launcher ==="
echo "Bypassing docker-compose due to version incompatibility..."

# 1. Create network
echo "[1/4] Creating network..."
docker network create eon-net 2>/dev/null || true

# 2. Build images
echo "[2/4] Building TinyLM..."
docker build -t enprojectai_tinylm -f phase7-language/Dockerfile .

echo "[2/4] Building Collective Mind..."
docker build -t enprojectai_collective-mind -f phase6-collective/Dockerfile .

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
  enprojectai_tinylm

# Collective Mind (Interactive/Logs)
docker run -d \
  --name collective-mind \
  --network eon-net \
  -v "$(pwd)/phase6-collective:/app/phase6-collective" \
  -v "$(pwd)/phase1-foundations:/app/phase1-foundations" \
  enprojectai_collective-mind

echo ""
echo "✅ Services started!"
echo "   - TinyLM: http://localhost:5001"
echo "   - Logs: docker logs -f collective-mind"
