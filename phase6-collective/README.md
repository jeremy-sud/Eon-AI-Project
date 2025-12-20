# Fase 6: Collective Mind

El objetivo de esta fase es permitir que múltiples nodos Eón aprendan juntos sin compartir sus datos privados. Utiliza un esquema federado descentralizado donde solo se intercambian los pesos aprendidos ($W_{out}$).

## Features Principales

- **Intercambio de Pesos 1-Bit**:

  - Protocolo ultraligero para microcontroladores (ESP32).
  - Comprime los pesos de punto flotante a **1 bit por peso** (signo).
  - Tasa de compression: **~11.8x** (200 bytes → 17 bytes).
  - Ver [Especificación del Protocolo](docs/protocol_spec.md).

- **Cliente MQTT Real** (NUEVO v1.7.0):
  - Conexión a brokers reales (Mosquitto, HiveMQ, AWS IoT)
  - Paquetes binarios nativos del Protocolo 1-Bit
  - Heartbeat automático y reconexión
  - CLI interactivo para pruebas

- **Dashboard de Monitoreo** (NUEVO v1.7.0):
  - Visualización de topología de red
  - Estado de nodos en tiempo real
  - Métricas de compression y latencia
  - Log de sincronización

- **ESP32 + LoRa** (NUEVO v1.7.0):
  - P2P wireless transmission sin WiFi
  - Ideal para IoT rural y redes mesh
  - Compatible con TTGO LoRa32, Heltec

- **Sincronización por "Momento Cero"**:
  - Todos los nodos comparten la misma semilla de nacimiento
  - Reservoirs mathematicalmente idénticos
  - Permite sumar/promediar $W_{out}$ directamente

## Structure

```
phase6-collective/
├── collective_mind.py    # Orquestador Python principal
├── mqtt_client.py        # Cliente MQTT real (NUEVO)
├── dashboard.html        # Dashboard de monitoreo (NUEVO)
├── Dockerfile
├── README.md
├── docs/
│   └── protocol_spec.md
└── src/
    ├── quantization.c    # Lógica de compresión 1-bit
    └── mock_mqtt.c       # Demo de transmisión
```

## Ejecución Demo (C)

```bash
gcc -o mock_mqtt src/mock_mqtt.c src/quantization.c
./mock_mqtt
```

## Cliente MQTT Real (Python)

```bash
# Instalar dependencias
pip install paho-mqtt numpy

# Modo demo (sin broker)
python mqtt_client.py --demo

# Conectar a broker real
python mqtt_client.py --broker localhost --port 1883 --node-id sensor-001

# Comandos interactivos:
#   sync   - Publicar pesos al topic de sincronización
#   status - Ver peers conocidos
#   quit   - Salir
```

## Dashboard de Monitoreo

```bash
python3 -m http.server 8080
# Abrir http://localhost:8080/dashboard.html
```

Features del dashboard:
- 🌐 Visualización de red con canvas animado
- 📡 Lista de nodos con estado (online/syncing/offline)
- 📊 Métricas: compression 91.5%, precisión 100%, latencia ~15ms
- 📜 Log de sincronización en tiempo real

## Formato del Paquete Binario

```
Byte 0-2:   Magic "EON" (3 bytes)
Byte 3:     Type (1=SYNC, 2=REQ, 3=ACK, 4=PING, 5=STATUS)
Byte 4-7:   Seed (uint32, big-endian)
Byte 8-9:   Count (uint16, big-endian)
Byte 10-13: Scale (float32, big-endian)
Byte 14+:   Bits empaquetados (ceil(N/8) bytes)
```

Ejemplo para 50 neuronas:
- Header: 14 bytes
- Payload: 7 bytes (50 bits empaquetados)
- **Total: 21 bytes** vs 200 bytes (float32) = **9.5x compression**

