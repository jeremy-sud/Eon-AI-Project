"""
Proyecto Eón - WebSocket Bridge MQTT
====================================

Servidor WebSocket que conecta el dashboard con el broker MQTT.
Permite visualización en tiempo real de la Mente Colectiva.

Uso:
    python ws_bridge.py --mqtt-broker localhost --ws-port 8765

Dependencias:
    pip install websockets paho-mqtt

(c) 2024 Sistemas Ursol - Jeremy Arias Solano
"""

import sys
import json
import time
import asyncio
import argparse
import struct
from pathlib import Path
from datetime import datetime
from typing import Set, Dict, Any

# Intentar importar dependencias
try:
    import websockets
    from websockets.server import serve
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False
    print("⚠️  websockets no instalado. Ejecutar: pip install websockets")

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("⚠️  paho-mqtt no instalado. Ejecutar: pip install paho-mqtt")


# ============================================================
# PROTOCOLO 1-BIT - Decodificación
# ============================================================

PACKET_TYPE_NAMES = {
    1: 'SYNC',
    2: 'REQ',
    3: 'ACK',
    4: 'PING',
    5: 'STATUS'
}


def decode_1bit_packet(data: bytes) -> Dict[str, Any]:
    """Decodifica paquete binario del Protocolo 1-Bit."""
    if len(data) < 14:
        return None
        
    try:
        magic = data[0:3].decode()
        if magic != "EON":
            return None
            
        ptype = data[3]
        seed = struct.unpack(">I", data[4:8])[0]
        count = struct.unpack(">H", data[8:10])[0]
        scale = struct.unpack(">f", data[10:14])[0]
        
        return {
            "magic": magic,
            "type": ptype,
            "type_name": PACKET_TYPE_NAMES.get(ptype, "UNKNOWN"),
            "seed": seed,
            "count": count,
            "scale": round(scale, 4),
            "payload_size": len(data) - 14,
            "total_size": len(data),
            "original_size": count * 4,
            "compression": round(count * 4 / len(data), 1),
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# WebSocket Bridge
# ============================================================

class MQTTWebSocketBridge:
    """
    Bridge entre MQTT y WebSocket.
    
    Recibe mensajes del broker MQTT y los retransmite
    a todos los clientes WebSocket conectados.
    """
    
    def __init__(self, 
                 mqtt_broker: str = "localhost",
                 mqtt_port: int = 1883,
                 ws_host: str = "0.0.0.0",
                 ws_port: int = 8765):
        
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.ws_host = ws_host
        self.ws_port = ws_port
        
        # Clientes WebSocket conectados
        self.ws_clients: Set = set()
        
        # Estado de nodos
        self.nodes: Dict[str, Dict] = {}
        
        # Estadísticas
        self.stats = {
            "total_syncs": 0,
            "bytes_received": 0,
            "bytes_saved": 0,
            "start_time": time.time()
        }
        
        # MQTT Client
        self.mqtt_client = None
        if MQTT_AVAILABLE:
            self._setup_mqtt()
            
    def _setup_mqtt(self):
        """Configura cliente MQTT."""
        # Usar callback API v2 para evitar deprecation warning
        try:
            self.mqtt_client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id="aeon-ws-bridge",
                protocol=mqtt.MQTTv311
            )
        except (AttributeError, TypeError):
            # Fallback para versiones antiguas de paho-mqtt
            self.mqtt_client = mqtt.Client(
                client_id="aeon-ws-bridge",
                protocol=mqtt.MQTTv311
            )
        
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._on_mqtt_message
        
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback de conexión MQTT."""
        if rc == 0:
            print(f"✓ Conectado a MQTT broker {self.mqtt_broker}:{self.mqtt_port}")
            # Suscribirse a todos los topics de Eón
            client.subscribe("aeon/colony/#")
        else:
            print(f"✗ Error conectando a MQTT: {rc}")
            
    def _on_mqtt_message(self, client, userdata, msg):
        """Callback de mensaje MQTT recibido."""
        topic = msg.topic
        payload = msg.payload
        
        # Procesar mensaje
        message = self._process_message(topic, payload)
        
        if message:
            # Enviar a todos los clientes WebSocket
            asyncio.run(self._broadcast(message))
            
    def _process_message(self, topic: str, payload: bytes) -> Dict:
        """Procesa mensaje MQTT y retorna datos para WebSocket."""
        parts = topic.split("/")
        
        message = {
            "timestamp": datetime.now().isoformat(),
            "topic": topic,
        }
        
        # Determinar tipo de mensaje
        if "/sync/" in topic:
            # Paquete de sincronización binario
            sender_id = parts[-1] if len(parts) > 0 else "unknown"
            packet = decode_1bit_packet(payload)
            
            if packet:
                message["type"] = "sync"
                message["node_id"] = sender_id
                message["packet"] = packet
                
                # Actualizar estadísticas
                self.stats["total_syncs"] += 1
                self.stats["bytes_received"] += len(payload)
                self.stats["bytes_saved"] += packet.get("original_size", 0) - len(payload)
                
                # Actualizar nodo
                self._update_node(sender_id, {
                    "last_sync": message["timestamp"],
                    "reservoir": packet.get("count"),
                    "status": "syncing"
                })
                
                # Marcar como online después de un momento
                asyncio.get_event_loop().call_later(
                    1.0, 
                    lambda: self._update_node(sender_id, {"status": "online"})
                )
                
        elif "/status/" in topic:
            # Mensaje de estado JSON
            try:
                data = json.loads(payload.decode())
                sender_id = data.get("node_id", parts[-1])
                
                message["type"] = "status"
                message["node_id"] = sender_id
                message["data"] = data
                
                self._update_node(sender_id, {
                    "last_seen": message["timestamp"],
                    "reservoir": data.get("reservoir_size"),
                    "samples": data.get("samples_learned"),
                    "status": "online"
                })
                
            except json.JSONDecodeError:
                return None
                
        else:
            # Otro tipo de mensaje
            message["type"] = "other"
            message["payload"] = payload.hex() if isinstance(payload, bytes) else str(payload)
            
        return message
        
    def _update_node(self, node_id: str, data: Dict):
        """Actualiza información de un nodo."""
        if node_id not in self.nodes:
            self.nodes[node_id] = {
                "id": node_id,
                "first_seen": datetime.now().isoformat(),
                "syncs": 0
            }
            
        self.nodes[node_id].update(data)
        
        if data.get("status") == "syncing":
            self.nodes[node_id]["syncs"] = self.nodes[node_id].get("syncs", 0) + 1
            
    async def _broadcast(self, message: Dict):
        """Envía mensaje a todos los clientes WebSocket."""
        if not self.ws_clients:
            return
            
        data = json.dumps(message)
        
        # Enviar a todos los clientes conectados
        disconnected = set()
        for ws in self.ws_clients:
            try:
                await ws.send(data)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(ws)
                
        # Limpiar clientes desconectados
        self.ws_clients -= disconnected
        
    async def ws_handler(self, websocket, path):
        """Manejador de conexiones WebSocket."""
        self.ws_clients.add(websocket)
        client_id = id(websocket)
        print(f"📱 Cliente WebSocket conectado ({client_id})")
        
        try:
            # Enviar estado inicial
            await websocket.send(json.dumps({
                "type": "init",
                "nodes": self.nodes,
                "stats": self.stats
            }))
            
            # Mantener conexión abierta
            async for message in websocket:
                # Procesar comandos del dashboard
                try:
                    cmd = json.loads(message)
                    await self._handle_ws_command(websocket, cmd)
                except json.JSONDecodeError:
                    pass
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.ws_clients.discard(websocket)
            print(f"📴 Cliente WebSocket desconectado ({client_id})")
            
    async def _handle_ws_command(self, websocket, cmd: Dict):
        """Maneja comandos recibidos del dashboard."""
        cmd_type = cmd.get("type")
        
        if cmd_type == "get_stats":
            await websocket.send(json.dumps({
                "type": "stats",
                "data": self.stats
            }))
            
        elif cmd_type == "get_nodes":
            await websocket.send(json.dumps({
                "type": "nodes",
                "data": self.nodes
            }))
            
        elif cmd_type == "broadcast_sync":
            # Publicar solicitud de sync a todos los nodos
            if self.mqtt_client:
                self.mqtt_client.publish(
                    "aeon/colony/command/sync_all",
                    json.dumps({"action": "sync"})
                )
                
    def start_mqtt(self):
        """Inicia conexión MQTT en thread separado."""
        if self.mqtt_client:
            try:
                self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port)
                self.mqtt_client.loop_start()
                return True
            except Exception as e:
                print(f"✗ Error conectando MQTT: {e}")
                return False
        return False
        
    async def start_ws(self):
        """Inicia servidor WebSocket."""
        if not WS_AVAILABLE:
            print("✗ websockets no disponible")
            return
            
        print(f"🌐 Servidor WebSocket en ws://{self.ws_host}:{self.ws_port}")
        
        async with serve(self.ws_handler, self.ws_host, self.ws_port):
            await asyncio.Future()  # Correr indefinidamente
            
    def stop(self):
        """Detiene el bridge."""
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()


# ============================================================
# Modo Simulación (sin broker real)
# ============================================================

async def simulation_mode(bridge: MQTTWebSocketBridge):
    """Modo simulación que genera eventos ficticios."""
    import random
    
    DEMO_NODES = [
        {"id": "sensor-001", "name": "Temp. Sala", "reservoir": 50},
        {"id": "sensor-002", "name": "Humid. Exterior", "reservoir": 50},
        {"id": "gateway-001", "name": "Gateway Principal", "reservoir": 100},
        {"id": "edge-001", "name": "Edge Processor", "reservoir": 200},
    ]
    
    print("🎮 Modo simulación activo")
    
    # Inicializar nodos
    for node in DEMO_NODES:
        bridge._update_node(node["id"], {
            "name": node["name"],
            "reservoir": node["reservoir"],
            "status": "online",
            "samples": random.randint(100, 1000)
        })
        
    await asyncio.sleep(2)
    
    # Enviar estado inicial a clientes
    await bridge._broadcast({
        "type": "init",
        "nodes": bridge.nodes,
        "stats": bridge.stats
    })
    
    while True:
        await asyncio.sleep(random.uniform(3, 8))
        
        # Seleccionar dos nodos aleatorios para sync
        nodes = list(bridge.nodes.keys())
        if len(nodes) >= 2:
            sender = random.choice(nodes)
            receiver = random.choice([n for n in nodes if n != sender])
            
            # Simular sync
            reservoir_size = bridge.nodes[sender].get("reservoir", 50)
            packet = {
                "magic": "EON",
                "type": 1,
                "type_name": "SYNC",
                "seed": random.randint(0, 2**32),
                "count": reservoir_size,
                "scale": round(random.random(), 4),
                "total_size": 14 + (reservoir_size + 7) // 8,
                "original_size": reservoir_size * 4,
                "compression": round(reservoir_size * 4 / (14 + (reservoir_size + 7) // 8), 1)
            }
            
            # Actualizar stats
            bridge.stats["total_syncs"] += 1
            bridge.stats["bytes_received"] += packet["total_size"]
            bridge.stats["bytes_saved"] += packet["original_size"] - packet["total_size"]
            
            # Marcar como syncing
            bridge._update_node(sender, {"status": "syncing"})
            bridge._update_node(receiver, {"status": "syncing"})
            
            # Broadcast sync event
            await bridge._broadcast({
                "type": "sync",
                "timestamp": datetime.now().isoformat(),
                "node_id": sender,
                "target_id": receiver,
                "packet": packet
            })
            
            await asyncio.sleep(0.8)
            
            # Volver a online
            bridge._update_node(sender, {"status": "online"})
            bridge._update_node(receiver, {"status": "online"})
            
            # Broadcast updated nodes
            await bridge._broadcast({
                "type": "nodes_update",
                "nodes": bridge.nodes,
                "stats": bridge.stats
            })


# ============================================================
# CLI Principal
# ============================================================

async def main():
    parser = argparse.ArgumentParser(description="Eón WebSocket Bridge")
    parser.add_argument("--mqtt-broker", default="localhost", help="Broker MQTT")
    parser.add_argument("--mqtt-port", type=int, default=1883, help="Puerto MQTT")
    parser.add_argument("--ws-host", default="0.0.0.0", help="Host WebSocket")
    parser.add_argument("--ws-port", type=int, default=8765, help="Puerto WebSocket")
    parser.add_argument("--simulate", action="store_true", help="Modo simulación")
    args = parser.parse_args()
    
    print("=" * 60)
    print("  EON WEBSOCKET BRIDGE - Dashboard en Tiempo Real")
    print("=" * 60)
    print()
    
    bridge = MQTTWebSocketBridge(
        mqtt_broker=args.mqtt_broker,
        mqtt_port=args.mqtt_port,
        ws_host=args.ws_host,
        ws_port=args.ws_port
    )
    
    if args.simulate:
        # Modo simulación
        await asyncio.gather(
            bridge.start_ws(),
            simulation_mode(bridge)
        )
    else:
        # Conectar a broker real
        if bridge.start_mqtt():
            await bridge.start_ws()
        else:
            print("✗ No se pudo conectar al broker MQTT")
            print("  Use --simulate para modo de demostración")


if __name__ == "__main__":
    if not WS_AVAILABLE:
        print("\nPara usar el bridge, instale: pip install websockets paho-mqtt")
        sys.exit(1)
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✓ Bridge detenido")
