"""
Proyecto Eón - Cliente MQTT Real
================================

Cliente MQTT para transmisión real del Protocolo 1-Bit.
Compatible con Mosquitto, HiveMQ, y otros brokers MQTT.

Uso:
    python mqtt_client.py --broker localhost --port 1883

(c) 2024 Sistemas Ursol - Jeremy Arias Solano
"""

import sys
import json
import time
import base64
import struct
import argparse
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Callable, Optional
import numpy as np

# Intentar importar paho-mqtt
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("⚠️  paho-mqtt no instalado. Ejecutar: pip install paho-mqtt")

# Path del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "phase1-foundations" / "python"))

from esn.esn import EchoStateNetwork


# ============================================================
# PROTOCOLO 1-BIT - Formato de Paquete
# ============================================================
# Byte 0-2:   Magic "EON" (3 bytes)
# Byte 3:     Type (1=SYNC, 2=REQ, 3=ACK, 4=PING, 5=STATUS)
# Byte 4-7:   Seed (uint32)
# Byte 8-9:   Count (uint16) - número de pesos
# Byte 10-13: Scale (float32)
# Byte 14+:   Payload (bits empaquetados)
# ============================================================

PACKET_TYPES = {
    'SYNC': 1,      # Sincronización de pesos
    'REQ': 2,       # Solicitud de pesos
    'ACK': 3,       # Confirmación
    'PING': 4,      # Heartbeat
    'STATUS': 5,    # Estado del nodo
}

PACKET_TYPE_NAMES = {v: k for k, v in PACKET_TYPES.items()}


class AeonMQTTNode:
    """
    Nodo Eón con soporte MQTT real.
    
    Características:
    - Conexión a broker MQTT (Mosquitto, HiveMQ, etc.)
    - Publicación de pesos en formato 1-bit binario
    - Suscripción a tópicos de sincronización
    - Heartbeat automático
    - Reconexión automática
    """
    
    def __init__(self, 
                 node_id: str,
                 n_reservoir: int = 50,
                 broker: str = "localhost",
                 port: int = 1883,
                 username: str = None,
                 password: str = None):
        """
        Args:
            node_id: Identificador único del nodo
            n_reservoir: Tamaño del reservoir
            broker: Dirección del broker MQTT
            port: Puerto del broker
            username: Usuario (opcional)
            password: Contraseña (opcional)
        """
        self.node_id = node_id
        self.n_reservoir = n_reservoir
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        
        # ESN
        self.esn = EchoStateNetwork(
            n_inputs=1,
            n_outputs=1,
            n_reservoir=n_reservoir,
            spectral_radius=0.9,
            sparsity=0.85
        )
        
        # Inicializar W_out para demo
        rng = np.random.default_rng(hash(node_id) % (2**32))
        self.esn.W_out = rng.standard_normal((1, n_reservoir)) * 0.5
        
        # Estado
        self.connected = False
        self.samples_learned = 0
        self.sync_count = 0
        self.last_sync = None
        self.peers: Dict[str, dict] = {}  # peer_id -> info
        
        # Callbacks
        self.on_sync_received: Optional[Callable] = None
        self.on_peer_discovered: Optional[Callable] = None
        
        # MQTT Client
        self.client = None
        if MQTT_AVAILABLE:
            self._setup_mqtt()
        
        # Topics
        self.topic_base = "aeon/colony"
        self.topic_sync = f"{self.topic_base}/sync"
        self.topic_status = f"{self.topic_base}/status"
        self.topic_node = f"{self.topic_base}/node/{self.node_id}"
        
    def _setup_mqtt(self):
        """Configura cliente MQTT."""
        self.client = mqtt.Client(
            client_id=f"aeon-{self.node_id}",
            protocol=mqtt.MQTTv311
        )
        
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
    def _on_connect(self, client, userdata, flags, rc):
        """Callback de conexión."""
        if rc == 0:
            self.connected = True
            print(f"✓ [{self.node_id}] Conectado a {self.broker}:{self.port}")
            
            # Suscribirse a tópicos
            self.client.subscribe(f"{self.topic_sync}/#")
            self.client.subscribe(f"{self.topic_status}/#")
            
            # Anunciar presencia
            self._publish_status()
        else:
            print(f"✗ [{self.node_id}] Error de conexión: {rc}")
            
    def _on_disconnect(self, client, userdata, rc):
        """Callback de desconexión."""
        self.connected = False
        print(f"⚠ [{self.node_id}] Desconectado (rc={rc})")
        
    def _on_message(self, client, userdata, msg):
        """Callback de mensaje recibido."""
        try:
            topic = msg.topic
            payload = msg.payload
            
            # Determinar tipo de mensaje
            if "/sync/" in topic:
                self._handle_sync_message(topic, payload)
            elif "/status/" in topic:
                self._handle_status_message(topic, payload)
                
        except Exception as e:
            print(f"✗ [{self.node_id}] Error procesando mensaje: {e}")
            
    def _handle_sync_message(self, topic: str, payload: bytes):
        """Procesa mensaje de sincronización."""
        try:
            # Extraer sender del topic
            parts = topic.split("/")
            sender_id = parts[-1] if len(parts) > 0 else "unknown"
            
            # Ignorar mensajes propios
            if sender_id == self.node_id:
                return
            
            # Decodificar paquete binario
            packet = self._decode_binary_packet(payload)
            if not packet:
                return
            
            print(f"📥 [{self.node_id}] Sync recibido de {sender_id}")
            print(f"    Tipo: {PACKET_TYPE_NAMES.get(packet['type'], 'UNKNOWN')}")
            print(f"    Pesos: {packet['count']}")
            print(f"    Compresión: {packet.get('compression', 'N/A')}x")
            
            # Importar pesos
            if packet['type'] == PACKET_TYPES['SYNC']:
                self._import_weights_from_packet(packet)
                self.sync_count += 1
                self.last_sync = datetime.now(timezone.utc).isoformat()
                
                # Callback
                if self.on_sync_received:
                    self.on_sync_received(sender_id, packet)
                    
        except Exception as e:
            print(f"✗ [{self.node_id}] Error en sync: {e}")
            
    def _handle_status_message(self, _topic: str, payload: bytes):
        """Procesa mensaje de estado."""
        try:
            data = json.loads(payload.decode())
            peer_id = data.get("node_id")
            
            if peer_id and peer_id != self.node_id:
                self.peers[peer_id] = {
                    "last_seen": time.time(),
                    "reservoir": data.get("reservoir_size"),
                    "samples": data.get("samples_learned"),
                    "syncs": data.get("sync_count"),
                }
                
                if self.on_peer_discovered:
                    self.on_peer_discovered(peer_id, data)
                    
        except (json.JSONDecodeError, KeyError):
            pass  # Ignorar errores de status
            
    def connect(self, keepalive: int = 60) -> bool:
        """
        Conectar al broker MQTT.
        
        Args:
            keepalive: Intervalo de keepalive en segundos
            
        Returns:
            True si la conexión fue exitosa
        """
        if not MQTT_AVAILABLE:
            print("✗ paho-mqtt no disponible")
            return False
            
        try:
            self.client.connect(self.broker, self.port, keepalive)
            self.client.loop_start()
            
            # Esperar conexión
            for _ in range(50):  # 5 segundos máximo
                if self.connected:
                    return True
                time.sleep(0.1)
                
            return False
            
        except Exception as e:
            print(f"✗ [{self.node_id}] Error conectando: {e}")
            return False
            
    def disconnect(self):
        """Desconectar del broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            
    def _publish_status(self):
        """Publica estado del nodo."""
        status = {
            "node_id": self.node_id,
            "reservoir_size": self.n_reservoir,
            "samples_learned": self.samples_learned,
            "sync_count": self.sync_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        self.client.publish(
            f"{self.topic_status}/{self.node_id}",
            json.dumps(status),
            qos=1
        )
        
    def publish_weights(self, qos: int = 1) -> bool:
        """
        Publica pesos en formato 1-bit binario.
        
        Args:
            qos: Nivel de QoS (0, 1, o 2)
            
        Returns:
            True si la publicación fue exitosa
        """
        if not self.connected:
            print(f"✗ [{self.node_id}] No conectado")
            return False
            
        try:
            # Crear paquete binario
            packet = self._create_binary_packet()
            
            # Publicar
            result = self.client.publish(
                f"{self.topic_sync}/{self.node_id}",
                packet,
                qos=qos
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📤 [{self.node_id}] Pesos publicados ({len(packet)} bytes)")
                return True
            else:
                print(f"✗ [{self.node_id}] Error publicando: {result.rc}")
                return False
                
        except Exception as e:
            print(f"✗ [{self.node_id}] Error: {e}")
            return False
            
    def _create_binary_packet(self) -> bytes:
        """
        Crea paquete binario con protocolo 1-bit.
        
        Formato:
            Magic (3B) + Type (1B) + Seed (4B) + Count (2B) + Scale (4B) + Bits
        """
        w_out = self.esn.W_out.flatten()
        
        # Header
        magic = b"EON"
        ptype = PACKET_TYPES['SYNC']
        seed = hash(self.node_id) % (2**32)
        count = len(w_out)
        scale = float(np.abs(w_out).max())
        
        # Cuantizar a 1-bit (signo)
        bits = (w_out >= 0).astype(np.uint8)
        
        # Empaquetar bits en bytes
        n_bytes = (count + 7) // 8
        packed = bytearray(n_bytes)
        for i, bit in enumerate(bits):
            if bit:
                packed[i // 8] |= (1 << (7 - (i % 8)))
                
        # Construir paquete
        packet = bytearray()
        packet.extend(magic)
        packet.append(ptype)
        packet.extend(struct.pack(">I", seed))      # Big-endian uint32
        packet.extend(struct.pack(">H", count))     # Big-endian uint16
        packet.extend(struct.pack(">f", scale))     # Big-endian float32
        packet.extend(packed)
        
        return bytes(packet)
        
    def _decode_binary_packet(self, data: bytes) -> Optional[dict]:
        """Decodifica paquete binario."""
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
            packed = data[14:]
            
            # Desempaquetar bits
            bits = []
            for byte in packed:
                for i in range(8):
                    if len(bits) < count:
                        bits.append((byte >> (7 - i)) & 1)
                        
            return {
                "magic": magic,
                "type": ptype,
                "seed": seed,
                "count": count,
                "scale": scale,
                "bits": bits,
                "original_size": count * 4,
                "compressed_size": len(data),
                "compression": round(count * 4 / len(data), 1),
            }
            
        except Exception as e:
            print(f"Error decodificando: {e}")
            return None
            
    def _import_weights_from_packet(self, packet: dict):
        """Importa pesos desde paquete decodificado."""
        if packet['count'] != self.n_reservoir:
            print(f"⚠ Tamaño incompatible: {packet['count']} vs {self.n_reservoir}")
            return
            
        # Reconstruir pesos desde bits
        bits = np.array(packet['bits'])
        signs = 2 * bits - 1  # 0 -> -1, 1 -> +1
        
        # Escalar
        weights = signs * packet['scale'] * 0.5
        
        # Fusionar con pesos actuales (promedio ponderado)
        alpha = 0.5  # Factor de mezcla
        current = self.esn.W_out.flatten()
        fused = alpha * current + (1 - alpha) * weights
        
        self.esn.W_out = fused.reshape(1, -1)
        
    def feed(self, value: float):
        """Alimenta un valor al ESN."""
        self.esn.predict(np.array([[value]]))
        self.samples_learned += 1
        
    def start_heartbeat(self, interval: int = 30):
        """Inicia heartbeat periódico."""
        def heartbeat_loop():
            while self.connected:
                self._publish_status()
                time.sleep(interval)
                
        thread = threading.Thread(target=heartbeat_loop, daemon=True)
        thread.start()


# ============================================================
# CLI Principal
# ============================================================

def _run_demo(node: AeonMQTTNode):
    """Ejecuta demostración sin broker real."""
    print("[MODO DEMO - Sin broker real]")
    print()
    
    # Crear paquete binario
    packet = node._create_binary_packet()
    print("Paquete binario creado:")
    print(f"  Tamaño: {len(packet)} bytes")
    print(f"  Header: {packet[:14].hex()}")
    print()
    
    # Decodificar
    decoded = node._decode_binary_packet(packet)
    print("Paquete decodificado:")
    print(f"  Magic: {decoded['magic']}")
    print(f"  Type: {PACKET_TYPE_NAMES.get(decoded['type'], 'UNKNOWN')}")
    print(f"  Seed: {decoded['seed']}")
    print(f"  Count: {decoded['count']} pesos")
    print(f"  Scale: {decoded['scale']:.4f}")
    print(f"  Compresión: {decoded['compression']}x")
    print()
    
    # Métricas
    print("=== MÉTRICAS 1-BIT ===")
    print(f"Tamaño float32: {decoded['original_size']} bytes")
    print(f"Tamaño 1-bit:   {decoded['compressed_size']} bytes")
    print(f"Ahorro:         {(1-decoded['compressed_size']/decoded['original_size'])*100:.1f}%")
    print()
    print("✓ Demo completado")


def _run_interactive(node: AeonMQTTNode, broker: str, port: int):
    """Ejecuta modo interactivo con broker real."""
    print(f"Conectando a {broker}:{port}...")
    
    if not node.connect():
        print("✗ No se pudo conectar al broker")
        print("  Asegúrese de que el broker esté corriendo.")
        print("  Para instalar Mosquitto: sudo apt install mosquitto mosquitto-clients")
        return
    
    print("✓ Conectado")
    
    # Callbacks
    node.on_sync_received = lambda peer, pkt: print(f"  Sync de {peer}: {pkt['count']} pesos")
    node.on_peer_discovered = lambda peer, info: print(f"  Peer descubierto: {peer}")
    
    # Iniciar heartbeat
    node.start_heartbeat(30)
    
    try:
        _command_loop(node)
    except KeyboardInterrupt:
        print("\n")
    finally:
        node.disconnect()
        print("Desconectado")


def _command_loop(node: AeonMQTTNode):
    """Loop de comandos interactivo."""
    print("\nEscuchando mensajes (Ctrl+C para salir)...")
    print("Comandos: 'sync' para publicar pesos, 'quit' para salir\n")
    
    while True:
        cmd = input("> ").strip().lower()
        
        if cmd == "sync":
            node.publish_weights()
        elif cmd == "status":
            print(f"Peers conocidos: {list(node.peers.keys())}")
            print(f"Syncs recibidos: {node.sync_count}")
        elif cmd in ("quit", "exit", "q"):
            break


def main():
    parser = argparse.ArgumentParser(description="Eón MQTT Client")
    parser.add_argument("--broker", default="localhost", help="Broker MQTT")
    parser.add_argument("--port", type=int, default=1883, help="Puerto")
    parser.add_argument("--node-id", default="demo-node", help="ID del nodo")
    parser.add_argument("--reservoir", type=int, default=50, help="Tamaño reservoir")
    parser.add_argument("--demo", action="store_true", help="Ejecutar demo")
    args = parser.parse_args()
    
    print("=" * 60)
    print("  EON MQTT CLIENT - Protocolo 1-Bit")
    print("=" * 60)
    print()
    
    # Crear nodo
    node = AeonMQTTNode(
        node_id=args.node_id,
        n_reservoir=args.reservoir,
        broker=args.broker,
        port=args.port
    )
    
    if args.demo:
        _run_demo(node)
    else:
        _run_interactive(node, args.broker, args.port)


if __name__ == "__main__":
    main()
