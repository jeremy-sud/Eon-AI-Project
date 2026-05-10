# Eón Phase 4: Hardware
## Implementaciones para Edge Computing y IoT

Esta fase contiene las implementaciones del Proyecto Eón para hardware embebido, incluyendo Arduino, ESP32 y módulos de comunicación LoRa.

---

## 📁 Estructura

```
phase4-hardware/
├── arduino/                      # Biblioteca Arduino genérica
│   ├── Aeon.cpp                 # Implementación core
│   ├── Aeon.h                   # Header principal
│   ├── library.properties       # Metadatos de librería
│   └── examples/
│       └── BasicPrediction/     # Ejemplo básico
│
└── esp32/                        # Implementaciones ESP32
    ├── AeonESP32.h              # Header optimizado para ESP32
    └── examples/
        ├── LoRa_1Bit_Demo.ino   # Demo protocolo 1-bit + LoRa
        ├── LoRa_RangeTest.ino   # Test de alcance con métricas
        └── EnergyMetrics.ino    # Medición de consumo energético
```

---

## 🔧 Hardware Soportado

### Arduino
- Arduino Uno/Mega (AVR)
- Arduino Nano Every
- Arduino Due

### ESP32
- **TTGO LoRa32 V1/V2** ✓
- **Heltec WiFi LoRa 32** ✓
- ESP32 DevKit + módulo SX1276/SX1278
- ESP32-C3/S2/S3

---

## 📡 ESP32 + LoRa Examples

### 1. LoRa_1Bit_Demo.ino

**Propósito:** Demo completo del Protocolo 1-Bit sobre LoRa para sincronización de neuronas entre nodos.

**Características:**
- Transmisión bidireccional TX/RX
- Compresión 9.5x (21 bytes vs 175 bytes JSON)
- Display OLED para visualización
- Modos automático y manual

**Uso:**
1. Subir a dos ESP32 con LoRa
2. Configurar uno como `#define MODE_TX`
3. Configurar otro como `#define MODE_RX`
4. Observar sincronización de pesos

```cpp
// Configuración básica
#define LORA_FREQ 915E6  // Ajustar según región
#define RESERVOIR_SIZE 50
```

### 2. LoRa_RangeTest.ino 🆕

**Propósito:** Test de alcance para evaluar cobertura del Protocolo 1-Bit sobre LoRa.

**Métricas:**
- **RSSI:** Intensidad de señal recibida (dBm)
- **SNR:** Relación señal-ruido (dB)
- **Packet Loss:** Porcentaje de paquetes perdidos
- **Latencia aproximada**
- **Estimación de rango**

**Uso:**
```
1. Subir a ambos ESP32
2. Serial Monitor:
   - Escribir 'tx' → modo transmisor
   - Escribir 'rx' → modo receptor
3. Alejar los dispositivos
4. Escribir 's' para ver estadísticas
```

**Comandos:**
| Comando | Acción |
|---------|--------|
| `tx` | Iniciar modo transmisor |
| `rx` | Iniciar modo receptor |
| `s` | Mostrar estadísticas |
| `r` | Reiniciar contadores |

**Ejemplo de Salida:**
```
────────────────────────────────────────
📥 RX #42 | Seq: 42
   RSSI: -87 dBm | SNR: 8.5 dB
   Avg RSSI: -85.3 dBm | Avg SNR: 9.1 dB
   Pérdida: 2.3% | Bytes: 882
   Rango estimado: 100-500m (bueno)
   Latencia aprox: 45 ms
```

### 3. EnergyMetrics.ino 🆕

**Propósito:** Medición del consumo energético del Protocolo 1-Bit vs JSON.

**Métricas:**
- Consumo por transmisión (mJ)
- Tiempo de aire LoRa
- Comparativa 1-Bit vs JSON
- Estimación de vida de batería

**Consumos típicos medidos:**
| Modo | Corriente | Potencia |
|------|-----------|----------|
| Deep Sleep | 0.01 mA | 0.037 mW |
| Idle | 10 mA | 37 mW |
| LoRa RX | 15 mA | 55.5 mW |
| CPU Activo | 50 mA | 185 mW |
| LoRa TX @20dBm | 120 mA | 444 mW |

**Comparativa Protocolo 1-Bit vs JSON:**
| Métrica | 1-Bit | JSON | Mejora |
|---------|-------|------|--------|
| Tamaño | 21 bytes | 175 bytes | 8.3x |
| Tiempo de aire | ~51 ms | ~132 ms | 2.6x |
| Energía por TX | ~4.3 mJ | ~11.2 mJ | 2.6x |
| TX con 1000mAh | ~1.02M | ~0.39M | 2.6x |

**Comandos:**
| Comando | Acción |
|---------|--------|
| `m` | Repetir mediciones |
| `b` | Leer voltaje de batería |
| `s` | Entrar en deep sleep (10s) |

---

## 📊 Protocolo 1-Bit

El Protocolo 1-Bit comprime pesos sinápticos flotantes a bits individuales:

```
Estructura del Paquete (21 bytes para 50 neuronas):
┌──────────────────────────────────────────────────┐
│ Header (14 bytes)                                │
├──────┬──────┬──────┬────────────┬───────────────┤
│ EON  │ Type │ Ver  │ Timestamp  │ Node ID       │
│ 3B   │ 1B   │ 1B   │ 4B         │ 4B            │
├──────┴──────┴──────┴────────────┴───────────────┤
│ Payload (7 bytes = ceil(50/8))                  │
│ Bit[0..49] = sign(weight[i])                    │
└──────────────────────────────────────────────────┘
```

**Tipos de mensaje:**
- `0x00` - PING (heartbeat)
- `0x01` - SYNC (sincronización de pesos)
- `0x02` - ACK (confirmación)
- `0x03` - QUERY (solicitud de estado)

---

## 🔌 Conexiones Hardware

### TTGO LoRa32 V1
```
LoRa Module → ESP32
SCK  → GPIO 5
MISO → GPIO 19
MOSI → GPIO 27
SS   → GPIO 18
RST  → GPIO 14
DIO0 → GPIO 26

OLED SSD1306
SDA → GPIO 4
SCL → GPIO 15
RST → GPIO 16
```

### Heltec WiFi LoRa 32
```
LoRa Module → ESP32
SCK  → GPIO 5
MISO → GPIO 19
MOSI → GPIO 27
SS   → GPIO 18
RST  → GPIO 23
DIO0 → GPIO 26

OLED SSD1306
SDA → GPIO 4
SCL → GPIO 15
RST → GPIO 16
```

---

## 📚 Librerías Requeridas

Instalar desde Arduino Library Manager:

1. **LoRa** by Sandeep Mistry
2. **ArduinoJson** by Benoit Blanchon
3. **ESP32 OLED Driver** for SSD1306 (Heltec/TTGO)

---

## 🧪 Test de Campo

### Procedimiento recomendado:

1. **Preparación:**
   - Cargar completamente ambas baterías
   - Subir `LoRa_RangeTest.ino` a ambos ESP32
   - Verificar frecuencia legal para tu región

2. **Test:**
   - Colocar RX en punto fijo
   - Caminar con TX a incrementos de 50-100m
   - Anotar RSSI/SNR en cada punto

3. **Documentar:**
   - Condiciones (urbano/rural, clima)
   - Antenas utilizadas
   - Altura de dispositivos
   - Obstáculos

4. **Resultados esperados:**
   | RSSI (dBm) | Rango típico |
   |------------|--------------|
   | > -80 | < 100m |
   | -80 a -100 | 100-500m |
   | -100 a -110 | 500m-1km |
   | -110 a -120 | 1-3km |
   | < -120 | > 3km (límite) |

---

## 🔗 Enlaces Relacionados

- [Phase 6: Collective Mind](../phase6-collective/README.md) - MQTT y protocolo de red
- [ESN Specification](../docs/technical/esn_spec.md) - Especificación de la red neuronal
- [Protocol Spec](../phase6-collective/docs/protocol_spec.md) - Especificación del protocolo 1-bit

---

## 📝 Changelog

### v1.7.0 (2024)
- ✅ LoRa_1Bit_Demo.ino - Demo completo TX/RX
- ✅ LoRa_RangeTest.ino - Test de alcance con métricas
- ✅ EnergyMetrics.ino - Medición de consumo energético

### v1.6.0 (2024)
- Implementación inicial Arduino
- Header AeonESP32.h

---

*Eón Project - SenseLab © 2024*
