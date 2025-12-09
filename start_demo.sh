#!/bin/bash
# ==========================================================
# Eón Project - Full Stack Demo Launcher
# ==========================================================
# Launches the complete Eón ecosystem:
#   - Mosquitto MQTT Broker
#   - WebSocket Bridge (MQTT ↔ Browser)
#   - Web Dashboard Server
#   - Browser (optional)
# 
# Usage: ./start_demo.sh [--no-browser] [--docker]
# ==========================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
MQTT_PORT=1883
WS_PORT=8765
WEB_PORT=8000
OPEN_BROWSER=true
USE_DOCKER=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-browser)
            OPEN_BROWSER=false
            shift
            ;;
        --docker)
            USE_DOCKER=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-browser    Don't open browser automatically"
            echo "  --docker        Use Docker Compose instead of local services"
            echo "  -h, --help      Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# ASCII Banner
print_banner() {
    echo -e "${CYAN}"
    cat << 'EOF'
    ███████╗ ██████╗ ███╗   ██╗
    ██╔════╝██╔═══██╗████╗  ██║
    █████╗  ██║   ██║██╔██╗ ██║
    ██╔══╝  ██║   ██║██║╚██╗██║
    ███████╗╚██████╔╝██║ ╚████║
    ╚══════╝ ╚═════╝ ╚═╝  ╚═══╝
    
    Ultra-Low Power Edge Intelligence
    Full Stack Demo v1.7.1
EOF
    echo -e "${NC}"
}

# Function to check if a port is in use
port_in_use() {
    lsof -i:"$1" >/dev/null 2>&1
}

# Function to wait for port to be available
wait_for_port() {
    local port=$1
    local max_wait=30
    local waited=0
    
    while ! port_in_use "$port" && [ $waited -lt $max_wait ]; do
        sleep 0.5
        waited=$((waited + 1))
    done
    
    if [ $waited -ge $max_wait ]; then
        echo -e "${RED}✗ Timeout waiting for port $port${NC}"
        return 1
    fi
    return 0
}

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    
    # Kill background processes
    if [ -n "$WEB_PID" ]; then
        kill "$WEB_PID" 2>/dev/null || true
    fi
    if [ -n "$WS_PID" ]; then
        kill "$WS_PID" 2>/dev/null || true
    fi
    
    # If we started mosquitto, stop it
    if [ "$MOSQUITTO_STARTED" = true ]; then
        sudo systemctl stop mosquitto 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✓ Cleanup complete${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Main
print_banner

if [ "$USE_DOCKER" = true ]; then
    echo -e "${BLUE}▶ Starting with Docker Compose...${NC}"
    cd "$PROJECT_ROOT"
    docker compose up --build -d
    
    echo -e "\n${GREEN}✓ Docker services started!${NC}"
    echo -e "  Dashboard: ${CYAN}http://localhost:$WEB_PORT${NC}"
    echo -e "  TinyLM:    ${CYAN}http://localhost:5001${NC}"
    echo -e "  MQTT:      ${CYAN}localhost:$MQTT_PORT${NC}"
    echo ""
    echo -e "${YELLOW}Run 'docker compose logs -f' to see logs${NC}"
    echo -e "${YELLOW}Run 'docker compose down' to stop${NC}"
    
    if [ "$OPEN_BROWSER" = true ]; then
        xdg-open "http://localhost:$WEB_PORT" 2>/dev/null || open "http://localhost:$WEB_PORT" 2>/dev/null || true
    fi
    exit 0
fi

# Check dependencies
echo -e "${BLUE}▶ Checking dependencies...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Python $(python3 --version | cut -d' ' -f2)"

# Check paho-mqtt
if ! python3 -c "import paho.mqtt.client" 2>/dev/null; then
    echo -e "  ${YELLOW}⚠ Installing paho-mqtt...${NC}"
    pip install paho-mqtt --quiet
fi
echo -e "  ${GREEN}✓${NC} paho-mqtt"

# Check websockets
if ! python3 -c "import websockets" 2>/dev/null; then
    echo -e "  ${YELLOW}⚠ Installing websockets...${NC}"
    pip install websockets --quiet
fi
echo -e "  ${GREEN}✓${NC} websockets"

# Check Mosquitto
if ! command -v mosquitto &> /dev/null; then
    echo -e "${RED}✗ Mosquitto not found. Install with: sudo apt install mosquitto${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Mosquitto"

echo ""

# Step 1: Start MQTT Broker
echo -e "${BLUE}▶ Step 1: Starting MQTT Broker...${NC}"
MOSQUITTO_STARTED=false

if systemctl is-active --quiet mosquitto; then
    echo -e "  ${GREEN}✓${NC} Mosquitto already running on port $MQTT_PORT"
else
    echo -e "  ${YELLOW}Starting Mosquitto...${NC}"
    sudo systemctl start mosquitto
    sleep 1
    if systemctl is-active --quiet mosquitto; then
        echo -e "  ${GREEN}✓${NC} Mosquitto started on port $MQTT_PORT"
        MOSQUITTO_STARTED=true
    else
        echo -e "  ${RED}✗ Failed to start Mosquitto${NC}"
        exit 1
    fi
fi

# Step 2: Start WebSocket Bridge
echo -e "\n${BLUE}▶ Step 2: Starting WebSocket Bridge...${NC}"

if port_in_use $WS_PORT; then
    echo -e "  ${YELLOW}⚠ Port $WS_PORT already in use, skipping${NC}"
else
    cd "$PROJECT_ROOT/phase6-collective"
    python3 ws_bridge.py &
    WS_PID=$!
    sleep 2
    
    if port_in_use $WS_PORT; then
        echo -e "  ${GREEN}✓${NC} WebSocket Bridge running on ws://localhost:$WS_PORT"
    else
        echo -e "  ${YELLOW}⚠ WebSocket Bridge may not have started correctly${NC}"
    fi
fi

# Step 3: Start Web Server
echo -e "\n${BLUE}▶ Step 3: Starting Web Dashboard...${NC}"

if port_in_use $WEB_PORT; then
    echo -e "  ${YELLOW}⚠ Port $WEB_PORT already in use, skipping${NC}"
else
    cd "$PROJECT_ROOT/web"
    python3 -m http.server $WEB_PORT --directory static &
    WEB_PID=$!
    sleep 1
    
    if port_in_use $WEB_PORT; then
        echo -e "  ${GREEN}✓${NC} Web Dashboard running on http://localhost:$WEB_PORT"
    else
        echo -e "  ${YELLOW}⚠ Web server may not have started correctly${NC}"
    fi
fi

# Summary
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Eón Demo Stack is running!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${CYAN}Dashboard${NC}:     http://localhost:$WEB_PORT"
echo -e "  ${CYAN}WebSocket${NC}:     ws://localhost:$WS_PORT"
echo -e "  ${CYAN}MQTT Broker${NC}:   localhost:$MQTT_PORT"
echo ""
echo -e "  ${YELLOW}Topics:${NC}"
echo -e "    aeon/colony/status/+    - Node status"
echo -e "    aeon/colony/weights/+   - Weight updates"
echo -e "    aeon/colony/consensus   - Consensus broadcasts"
echo ""

# Open browser
if [ "$OPEN_BROWSER" = true ]; then
    echo -e "${BLUE}▶ Opening browser...${NC}"
    xdg-open "http://localhost:$WEB_PORT" 2>/dev/null || open "http://localhost:$WEB_PORT" 2>/dev/null || true
fi

# Test MQTT connectivity
echo -e "\n${BLUE}▶ Testing MQTT connectivity...${NC}"
mosquitto_pub -t "aeon/colony/test" -m '{"test":"demo_startup","timestamp":"'$(date -Iseconds)'"}' 2>/dev/null && \
    echo -e "  ${GREEN}✓${NC} MQTT publish successful" || \
    echo -e "  ${YELLOW}⚠${NC} MQTT publish test skipped"

echo ""
echo -e "${CYAN}Press Ctrl+C to stop all services${NC}"
echo ""

# Keep running
wait
