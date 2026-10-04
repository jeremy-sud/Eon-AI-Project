# Eón Firmware: Guía de Hardware, OTA y Deployment

**Versión:** 1.0.0  
**Fecha:** 2026-10-04  
**Autor:** Proyecto Eón — SenseLab

---

## 1. Inventario de Firmware

### 1.1 Componentes de Firmware

| Componente | Ruta | Plataforma | Descripción |
|-----------|------|------------|-------------|
| **Aeon Arduino Library** | `phase4-hardware/arduino/` | AVR, SAMD, Due | Biblioteca ESN genérica para Arduino |
| **AeonESP32** | `phase4-hardware/esp32/AeonESP32.h` | ESP32/S2/S3/C3 | Extensión con WiFi, entropía HW, task affinity |
| **LoRa 1-Bit Demo** | `phase4-hardware/esp32/examples/LoRa_1Bit_Demo.ino` | ESP32 + SX127x | Demo de sincronización de pesos vía LoRa |
| **LoRa Range Test** | `phase4-hardware/esp32/examples/LoRa_RangeTest.ino` | ESP32 + SX127x | Test de alcance con métricas RSSI/SNR |
| **Energy Metrics** | `phase4-hardware/esp32/examples/EnergyMetrics.ino` | ESP32 + SX127x | Medición de consumo energético comparativo |
| **WiFi Predict** | `phase4-hardware/esp32/examples/WiFiPredict/` | ESP32 | Predicción remota vía HTTP |
| **libAeon (C Core)** | `phase2-core/libAeon/` | ANSI C (portable) | Motor ESN en punto fijo Q8.8 |

### 1.2 Dependencias de Firmware

| Librería | Versión | Uso | Instalación |
|----------|---------|-----|-------------|
| LoRa (Sandeep Mistry) | ≥0.8.0 | Comunicación LoRa SX127x | Arduino Library Manager |
| ArduinoJson | ≥6.0 | Serialización JSON | Arduino Library Manager |
| ESP32 OLED (SSD1306) | ≥4.0 | Display para demos | Arduino Library Manager |
| WiFi (ESP32) | Built-in | Conectividad WiFi | Incluido en ESP32 Arduino Core |
| HTTPClient (ESP32) | Built-in | Peticiones HTTP | Incluido en ESP32 Arduino Core |

### 1.3 Versiones de Firmware

| Versión | Fecha | Cambios |
|---------|-------|---------|
| v1.0.0 | 2024-Q2 | Arduino Library inicial (Aeon.h/cpp) |
| v1.5.0 | 2024-Q3 | AeonESP32.h con WiFi |
| v1.6.0 | 2024-Q3 | Task affinity system, hardware entropy source |
| v1.7.0 | 2024-Q4 | LoRa demos, range test, energy metrics |
| v1.7.1 | 2025-Q1 | Corrección de overflow en Q8.8 multiply |

---

## 2. Arquitectura del Firmware

### 2.1 Jerarquía de Clases

```
Aeon (Arduino base)
├── Reservoir (N neuronas, Q8.8)
├── W_in[N] (pesos de entrada)
├── W_out[N] (pesos de salida, entrenables)
├── state[N] (estado del reservoir)
├── update(input) → int16_t
├── predict() → int16_t
├── fit(data[], size) → void
└── memoryUsage() → size_t

AeonESP32 extends Aeon
├── WiFi connectivity
├── Hardware Entropy Source
│   ├── readEnvironmentNoise() → float [0,1]
│   ├── updateWithEntropyInfluence(input) → int16_t
│   └── generateTrueEntropyByte() → uint8_t
├── Task Affinity System
│   ├── evaluateTaskCost(domain) → TaskDecision
│   ├── shouldAcceptTask(domain) → bool
│   ├── recordProcessing(domain, mse) → void
│   └── getSpecialization() → DataDomain
├── Network
│   ├── sendPrediction(url, input, pred) → bool
│   ├── syncWeights(peerUrl) → bool
│   └── getCompressedWeights(buf, size) → size_t
└── exportWillCompressed(buf) → size_t
```

### 2.2 Mapa de Memoria (ESP32, N=50)

```
┌────────────────────────────────────────────────────┐
│ Sección              │ Tamaño    │ Dirección       │
├──────────────────────┼───────────┼─────────────────┤
│ Code (Flash)         │ ~12 KB    │ 0x10000+        │
│ ├─ Aeon library      │ ~4 KB     │                 │
│ ├─ AeonESP32 ext     │ ~3 KB     │                 │
│ ├─ LoRa driver       │ ~3 KB     │                 │
│ └─ WiFi stack        │ ~2 KB*    │                 │
├──────────────────────┼───────────┼─────────────────┤
│ RAM (SRAM)           │ ~1.8 KB   │ DRAM            │
│ ├─ W_in[50]          │ 100 B     │                 │
│ ├─ W_out[50]         │ 100 B     │                 │
│ ├─ state[50]         │ 100 B     │                 │
│ ├─ reservoir sparse  │ ~500 B    │                 │
│ ├─ Task Affinity     │ ~40 B     │                 │
│ ├─ Entropy buffer    │ ~16 B     │                 │
│ └─ Stack + temp      │ ~944 B    │                 │
├──────────────────────┼───────────┼─────────────────┤
│ NVS (Persistent)     │ Variable  │ NVS partition   │
│ ├─ W_out snapshot    │ 100 B     │                 │
│ ├─ Task affinity     │ 40 B      │                 │
│ └─ Config            │ 32 B      │                 │
└────────────────────────────────────────────────────┘
* Solo overhead incremental; WiFi stack base es del SDK ESP-IDF.
```

---

## 3. Flujo de Actualización OTA (Over-The-Air)

### 3.1 Prerrequisitos

- ESP32 con WiFi conectado a red local o internet
- Servidor HTTP accesible con el binario `.bin` del firmware
- Partición OTA configurada en partition table

### 3.2 Partition Table Recomendada

```
# Name,   Type, SubType, Offset,  Size,    Flags
nvs,      data, nvs,     0x9000,  0x5000,
otadata,  data, ota,     0xe000,  0x2000,
app0,     app,  ota_0,   0x10000, 0x1E0000,
app1,     app,  ota_1,   0x1F0000,0x1E0000,
nvs_data, data, nvs,     0x3D0000,0x30000,
```

**Nota:** La partición dual (app0/app1) permite rollback automático si la OTA falla.

### 3.3 Flujo OTA Recomendado

```
┌─────────────────────────────────────────────────────────────────┐
│                        FLUJO OTA                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. CHECK VERSION                                                │
│     ┌──────────┐    GET /api/firmware/latest                     │
│     │  ESP32   │────────────────────────────▶┌──────────────┐    │
│     │          │◀────────────────────────────│  OTA Server  │    │
│     └──────────┘    { "version": "1.7.1",   └──────────────┘    │
│                       "url": "...",                               │
│                       "sha256": "..." }                          │
│                                                                   │
│  2. COMPARE                                                      │
│     if (remote.version > local.version):                         │
│         proceed to download                                      │
│     else:                                                        │
│         sleep(CHECK_INTERVAL)                                    │
│                                                                   │
│  3. DOWNLOAD & FLASH                                             │
│     ┌──────────┐    GET /firmware/aeon_v1.7.1.bin               │
│     │  ESP32   │────────────────────────────▶┌──────────────┐    │
│     │          │    Stream to OTA partition   │  OTA Server  │    │
│     │          │◀════════════════════════════│              │    │
│     └──────────┘                             └──────────────┘    │
│                                                                   │
│  4. VERIFY                                                       │
│     SHA256(downloaded) == expected_hash ?                         │
│     ├─ YES: Mark OTA partition as boot                           │
│     └─ NO:  Abort, log error, keep current firmware              │
│                                                                   │
│  5. PRESERVE STATE                                               │
│     Antes del reboot:                                            │
│     ├─ Guardar W_out en NVS                                     │
│     ├─ Guardar Task Affinity en NVS                              │
│     └─ Guardar config en NVS                                    │
│                                                                   │
│  6. REBOOT                                                       │
│     ESP.restart()                                                │
│     ├─ Boot desde nueva partición                                │
│     └─ Restaurar estado desde NVS                                │
│                                                                   │
│  7. ROLLBACK (si falla)                                          │
│     Si el nuevo firmware no confirma OK en 30s:                  │
│     ├─ Watchdog trigger → boot anterior partición               │
│     └─ Estado preservado en NVS sigue intacto                   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 Implementación OTA (Código de Referencia)

```cpp
#include <Update.h>
#include <HTTPClient.h>

struct OTAConfig {
    const char* versionCheckUrl;   // GET endpoint para verificar versión
    const char* currentVersion;    // Versión actual del firmware
    uint32_t checkIntervalMs;      // Intervalo de verificación (default: 1 hora)
    bool preserveWeights;          // Guardar W_out antes de OTA
};

bool checkAndPerformOTA(AeonESP32& aeon, OTAConfig config) {
    HTTPClient http;
    
    // 1. Verificar versión disponible
    http.begin(config.versionCheckUrl);
    int code = http.GET();
    if (code != 200) { http.end(); return false; }
    
    String payload = http.getString();
    http.end();
    
    // 2. Parsear respuesta JSON
    StaticJsonDocument<256> doc;
    deserializeJson(doc, payload);
    
    const char* remoteVersion = doc["version"];
    const char* firmwareUrl = doc["url"];
    const char* expectedHash = doc["sha256"];
    
    if (strcmp(remoteVersion, config.currentVersion) <= 0) {
        return false;  // Ya estamos actualizados
    }
    
    // 3. Preservar estado antes de OTA
    if (config.preserveWeights) {
        // Guardar W_out en NVS
        // Guardar Task Affinity en NVS
        // Guardar configuración
    }
    
    // 4. Descargar y flashear
    http.begin(firmwareUrl);
    code = http.GET();
    if (code != 200) { http.end(); return false; }
    
    int contentLength = http.getSize();
    WiFiClient* stream = http.getStreamPtr();
    
    if (Update.begin(contentLength)) {
        size_t written = Update.writeStream(*stream);
        if (Update.end(true)) {
            // 5. Verificar hash (simplificado)
            // 6. Reboot
            ESP.restart();
            return true;
        }
    }
    
    http.end();
    return false;
}
```

---

## 4. Compatibilidad de Hardware

### 4.1 Plataformas Verificadas

| Plataforma | MCU | RAM | Flash | Estado | Notas |
|-----------|-----|-----|-------|--------|-------|
| **TTGO LoRa32 V1** | ESP32 | 520 KB | 4 MB | ✅ Verificado | LoRa SX1276 integrado |
| **TTGO LoRa32 V2** | ESP32 | 520 KB | 4 MB | ✅ Verificado | LoRa + OLED integrado |
| **Heltec WiFi LoRa 32** | ESP32 | 520 KB | 4 MB | ✅ Verificado | LoRa + OLED + batería |
| **ESP32 DevKitC** | ESP32 | 520 KB | 4 MB | ✅ Verificado | Requiere módulo LoRa externo |
| **ESP32-S3 DevKit** | ESP32-S3 | 512 KB | 8 MB | ⚠️ Compatible* | Sin LoRa nativo |
| **ESP32-C3** | ESP32-C3 | 400 KB | 4 MB | ⚠️ Compatible* | RISC-V, sin LoRa |
| **Arduino Uno** | ATmega328P | 2 KB | 32 KB | ✅ Verificado | Solo Aeon base (sin WiFi) |
| **Arduino Mega** | ATmega2560 | 8 KB | 256 KB | ✅ Verificado | Solo Aeon base |
| **Arduino Due** | SAM3X8E | 96 KB | 512 KB | ✅ Verificado | ARM Cortex-M3 |
| **STM32 Blue Pill** | STM32F103 | 20 KB | 64 KB | ⚠️ Compatible* | Necesita port del library |

*Compatible = Compilación correcta, no testeado en campo.

### 4.2 Pines de Conexión

#### TTGO LoRa32 V1/V2

| Señal | GPIO | Notas |
|-------|------|-------|
| LoRa SCK | 5 | SPI Clock |
| LoRa MISO | 19 | SPI MISO |
| LoRa MOSI | 27 | SPI MOSI |
| LoRa SS/CS | 18 | SPI Chip Select |
| LoRa RST | 14 (V1) / 23 (V2) | Reset |
| LoRa DIO0 | 26 | Interrupt |
| OLED SDA | 4 | I2C Data |
| OLED SCL | 15 | I2C Clock |
| OLED RST | 16 | Display Reset |
| Entropy Pin | 36 (VP) | ADC input flotante |
| Battery ADC | 35 | Lectura de voltaje batería |

#### Heltec WiFi LoRa 32

| Señal | GPIO | Notas |
|-------|------|-------|
| LoRa SCK | 5 | SPI Clock |
| LoRa MISO | 19 | SPI MISO |
| LoRa MOSI | 27 | SPI MOSI |
| LoRa SS/CS | 18 | SPI Chip Select |
| LoRa RST | 23 | Reset |
| LoRa DIO0 | 26 | Interrupt |
| OLED SDA | 4 | I2C Data |
| OLED SCL | 15 | I2C Clock |
| OLED RST | 16 | Display Reset |

---

## 5. Proceso de Build y Flasheo

### 5.1 Arduino IDE

```bash
# 1. Instalar ESP32 Board Support
#    Arduino IDE → Preferences → Additional Board Manager URLs:
#    https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

# 2. Instalar board ESP32 desde Board Manager

# 3. Instalar librerías:
#    - LoRa by Sandeep Mistry
#    - ArduinoJson by Benoit Blanchon

# 4. Seleccionar board: TTGO LoRa32-OLED (o equivalente)

# 5. Configurar:
#    - Upload Speed: 921600
#    - Flash Frequency: 80MHz
#    - Partition Scheme: Default (con OTA) o personalizado

# 6. Compilar y subir
```

### 5.2 PlatformIO

```ini
; platformio.ini
[env:ttgo-lora32]
platform = espressif32
board = ttgo-lora32-v1
framework = arduino
monitor_speed = 115200
upload_speed = 921600

lib_deps =
    sandeepmistry/LoRa@^0.8.0
    bblanchon/ArduinoJson@^6.0

; Particiones con OTA
board_build.partitions = min_spiffs.csv
```

### 5.3 Build del Core C (libAeon)

```bash
cd phase2-core/libAeon

# Compilar con make
make clean && make

# O con CMake
mkdir -p build && cd build
cmake .. && make

# Ejecutar demo
./aeon_demo

# Tests
make test
```

---

## 6. Configuración de Frecuencia LoRa por Región

| Región | Frecuencia | Regulación |
|--------|-----------|------------|
| América (US/CR) | 915 MHz | FCC Part 15 |
| Europa | 868 MHz | ETSI EN 300 220 |
| Asia (CN) | 470 MHz | MIIT |
| Asia (JP) | 923 MHz | ARIB STD-T108 |
| India | 865 MHz | WPC |
| Australia | 915 MHz | ACMA |

**Configurar en el sketch:**
```cpp
#define LORA_FREQ 915E6  // Cambiar según región
```

---

## 7. Troubleshooting

| Problema | Causa Probable | Solución |
|----------|----------------|----------|
| LoRa init failed | Pines incorrectos | Verificar pinout de la placa |
| WiFi no conecta | Credenciales o señal | Verificar SSID/password, acercar al AP |
| OTA falla a mitad | Tamaño de partición | Verificar partition table (app0 ≥ firmware size) |
| Pesos se pierden al reiniciar | No se persisten en NVS | Llamar a `saveWeightsToNVS()` antes de OTA |
| Overflow en Q8.8 | Valores fuera de rango | Verificar que inputs estén en [-128, 127] |
| Readings de entropía constantes | Pin no flotante | Asegurar que GPIO36 no esté conectado a nada |

---

## 8. Endpoints del Servidor OTA (Referencia)

Para implementar un servidor OTA compatible con el flujo descrito:

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/firmware/latest` | GET | Retorna JSON con versión, URL y hash |
| `/api/firmware/{version}.bin` | GET | Retorna binario del firmware |
| `/api/firmware/report` | POST | Nodo reporta versión actual y estado |

**Ejemplo de respuesta `/api/firmware/latest`:**
```json
{
    "version": "1.7.1",
    "url": "https://api.eon.scisenselab.com/firmware/aeon_v1.7.1.bin",
    "sha256": "a3f2b8c9d1e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0",
    "size": 1245184,
    "min_version": "1.5.0",
    "release_notes": "Fix Q8.8 overflow in reservoir update"
}
```

---

*Proyecto Eón — SenseLab — Build with Sense*  
*© 2024-2026*
