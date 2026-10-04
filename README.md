# ⚡ Proyecto Eón

> **A.E.O.N.** — Arquitectura Emergente y Optimización Neuromórfica

[![Versión](https://img.shields.io/badge/Versión-2.4.1-brightgreen)]()
[![Tests](https://img.shields.io/badge/Tests-720%20passing-green)]()
[![Cobertura](https://img.shields.io/badge/Cobertura-~92%25-yellowgreen)]()
[![Docker](https://img.shields.io/badge/Docker-Full%20Stack-blue)]()
[![Python](https://img.shields.io/badge/Python-3.8+-blue)]()
[![C](https://img.shields.io/badge/C-1.3KB-orange)]()
[![JavaScript](https://img.shields.io/badge/JS-Browser-yellow)]()
[![Arduino](https://img.shields.io/badge/Arduino-Compatible-teal)]()
[![ESP32](https://img.shields.io/badge/ESP32-LoRa-red)]()
[![MQTT](https://img.shields.io/badge/MQTT-Mosquitto-orange)]()
[![WebSocket](https://img.shields.io/badge/WebSocket-Bridge-blue)]()
[![OpenAPI](https://img.shields.io/badge/OpenAPI-3.1-green)]()
[![Dashboard](https://img.shields.io/badge/Dashboard-v2.0-cyan)]()
[![MultiNode](https://img.shields.io/badge/Chat-MultiNodo-orange)]()
[![Paper](https://img.shields.io/badge/Paper-PDF-red)]()
[![Licencia](https://img.shields.io/badge/Licencia-AGPLv3-blue)]()
[![Comercial](https://img.shields.io/badge/Comercial-Royalties-gold)]()

---

> ## ⚖️ LICENCIAMIENTO DUAL DE EÓN
> 
> **Este proyecto está disponible bajo un modelo de Licenciamiento Dual:**
> 
> ### 🔓 Camino A: Licencia Open Source (AGPLv3)
> 
> Este código se distribuye bajo la **GNU Affero General Public License v3.0 (AGPLv3)**.
> 
> ✅ **Uso libre para:**
> - Investigación académica y científica
> - Proyectos personales y educativos  
> - Servicios que liberen su código fuente bajo AGPLv3
> - Contribuciones a la comunidad open source
> 
> ⚠️ **Obligación Copyleft:** Si modifica o integra Eón en una aplicación o servicio, **debe liberar todo el código fuente** de esa aplicación bajo AGPLv3.
> 
> ### 🔐 Camino B: Licencia Comercial Propietaria (con Royalties)
> 
> Si desea integrar Eón en un **producto comercial cerrado** (hardware o software) **sin la obligación de liberar su código fuente**, debe adquirir una **Licencia Comercial con Royalties**.
> 
> Esta licencia le permite:
> - Integrar Eón en productos de hardware/software para venta comercial
> - Mantener su código propietario como secreto comercial
> - Evitar las obligaciones del copyleft de AGPLv3
> 
> ### 📧 Contacto para Licencias Comerciales
> 
> **Email:** `deadmooncr@gmail.com`  
> **Web:** `senselab.dev`
> 
> **SenseLab - Build with Sense**

---

## 🎯 ¿Qué es Eón?

Eón es una **plataforma de IA ultra-eficiente diseñada para edge computing e IoT**. Basada en Reservoir Computing (Echo State Networks), opera con **1.3 KB de memoria** — ideal para microcontroladores donde TensorFlow Lite ni siquiera cabe.

### Por qué Eón para el Edge

| Problema del mercado | Solución de Eón |
|---------------------|-----------------|
| TFLite Micro necesita ≥16KB RAM | Eón opera con **1.3 KB** |
| Los frameworks edge solo hacen inferencia | Eón **entrena on-device** (regresión lineal) |
| Modelos estáticos tras deployment | Eón tiene **aprendizaje continuo** sin re-flasheo |
| Sin memoria temporal nativa | El reservoir tiene **memoria dinámica inherente** |
| Sincronización cloud pesada | Protocolo **1-Bit** a 21 bytes por TX |

### 📊 Comparativa de Memoria

| Modelo | Memoria | Factor vs Eón Core |
|--------|---------|---------------------|
| GPT-2 Small | 500 MB | 384,615× |
| BERT Tiny | 16 MB | 12,307× |
| TensorFlow Lite (mínimo) | ~100 KB | 77× |
| **Eón Full-Stack** | **79.69 KB** | **61×** |
| **Eón Core (C)** | **1.3 KB** | **1×** |

> *Eón Full-Stack incluye: Chat Web + Aprendizaje Continuo + Arte Generativo + TinyLM*

---

## ✨ Características Principales

| Característica              | Descripción                                 |
| --------------------------- | ------------------------------------------- |
| **Ultraligero**             | Núcleo C de 1.3KB de memoria                |
| **Multi-plataforma**        | Python, C, JavaScript, Arduino, ESP32       |
| **Reservoir Computing**     | Echo State Networks eficientes              |
| **Aprendizaje Continuo**    | Online Learning + Memoria a largo plazo     |
| **Protocolo 1-Bit**         | Sincronización ultraligera (8.3x compresión)|
| **MQTT Real**               | Cliente paho-mqtt para brokers reales       |
| **ESP32 + LoRa**            | Transmisión inalámbrica P2P                 |
| **Dashboard v2.0**          | Visualización D3.js de red en tiempo real   |
| **Chat Multi-Nodo**         | Nodos INTENT, RESPONSE, COHERENCE colaboran |
| **Detector Anomalías**      | Streaming con calibración y callbacks       |
| **TinyLMv2**                | Modelo de lenguaje word-level               |
| **RAG Ligero**              | Búsqueda semántica en documentación         |
| **Memoria Factual**         | Timestamps para resolver ambigüedades      |
| **Sistema de Feedback**     | Mejora con retroalimentación 👍/👎           |
| **Predicción de Secuencias**| Aritmético, geométrico, Fibonacci, potencias |
| **Arte Generativo**         | 5 estilos (fractal, flow, particles, waves, neural) |
| **Cuantización Multi-nivel**| 8-bit, 4-bit, 1-bit con análisis de retención |
| **OTA Ready**               | Flujo de actualización over-the-air para ESP32 |

### 🆕 Nuevo en v2.4.1

- **Persistencia Circadiana (v2.4.1)**: Soporte completo en `AeonBirth` para guardar/cargar `use_circadian`, `dropout` y `learning_rate` en archivos de estado `.npz` y metadatos JSON.
- **Ciclos Circadianos & Entrenamiento Adaptativo (v2.4.0)**: Modulación dinámica de noise y learning rate en fit() y dropout basado en energía.
- **Leyenda del Chat & Enlaces Open Source (v2.3.0)**: Banner de disclaimer responsivo y enlaces al código oficial en GitHub.
- **Homeostasis & Watermark Neural (v2.3.0)**: Sincronización robusta de pesos de 1-bit mediante verificación lógica de firmas de hash.
- **Dashboard v2.0 (v2.0.0)**: Interfaz de monitoreo con D3.js, termómetro de estados, timeline de anomalías.
- **Chat Multi-Nodo (v2.0.0)**: Sistema colaborativo con nodos especializados (Intent, Response, Coherence, Sentiment, Context).
- **Detector de Anomalías (v2.0.0)**: Detección streaming con severidades (LOW, MEDIUM, HIGH, CRITICAL) y callbacks.
- **720 Tests (v2.4.1)**: Cobertura completa de todos los módulos (cobertura ~92%).

---

## 📈 Benchmarks de Energía

Resultados completos en [docs/benchmarks.md](docs/benchmarks.md).

### Energía Total por Ciclo (Cortex-M4F @ 80MHz, N=50)

| Fase | MACs | Tiempo (μs) | Energía (μJ) |
|------|------|-------------|---------------|
| Update (estado reservoir) | 2,550 | 31.9 | 0.0016 |
| Readout (predicción) | 52 | 0.65 | 0.0000325 |
| Online Learning (1 paso) | 2,500 | 31.3 | 0.0016 |
| **Total por ciclo** | **5,102** | **63.8** | **0.0032** |

### Comparativa de Energía por Inferencia

| Motor         | Energía / Inferencia (Cortex-M4) | Entrena on-device |
| :------------ | :------------------------------- | :---------------- |
| CMSIS-NN      | 0.001 μJ                        | ❌                |
| TinyML MLP    | 0.0015 μJ                       | ❌                |
| **Eón Motor** | **0.0045 μJ**                   | **✅**            |

> Eón es 3x más costoso en inferencia pura, pero es el **único framework que permite entrenamiento on-device** — eliminando el costo de re-deployment y cloud.

### Estimación de Vida de Batería (1 inferencia/seg, deep sleep entre ciclos)

| Batería | Capacidad | Vida estimada (sin radio) | Con LoRa (1 TX/min) |
|---------|-----------|---------------------------|----------------------|
| CR2032 | 225 mAh | ~760 días | ~6.5 días |
| 2×AA | 2,500 mAh | ~23 años* | ~72 días |
| LiPo 500mAh | 500 mAh | ~5.7 años* | ~14 días |

*Teórico, asumiendo deep sleep dominante.

Ver [docs/MATHEMATICS.md](docs/MATHEMATICS.md) para el análisis energético completo.

---

## 📡 Hardware & Firmware

### Hardware Soportado

| Plataforma | Estado | Capacidades |
|-----------|--------|-------------|
| TTGO LoRa32 V1/V2 | ✅ Verificado | ESN + LoRa + WiFi + OLED |
| Heltec WiFi LoRa 32 | ✅ Verificado | ESN + LoRa + WiFi + OLED |
| ESP32 DevKit | ✅ Verificado | ESN + WiFi |
| Arduino Uno/Mega | ✅ Verificado | ESN base (sin WiFi) |
| Arduino Due | ✅ Verificado | ESN base (ARM Cortex-M3) |

### Métricas de Comunicación (Protocolo 1-Bit vs JSON)

| Métrica | 1-Bit | JSON | Mejora |
|---------|-------|------|--------|
| Tamaño paquete | 21 B | 175 B | 8.3× |
| Tiempo de aire | 51 ms | 132 ms | 2.6× |
| Energía por TX | 4.3 mJ | 11.2 mJ | 2.6× |
| TX con 1000mAh | 1.02M | 0.39M | 2.6× |

### Firmware & OTA

Documentación completa de firmware, actualización over-the-air, compatibilidad y deployment: **[docs/FIRMWARE_OTA.md](docs/FIRMWARE_OTA.md)**

---

## 📁 Estructura

```
Eón Project AI/
├── GENESIS.json                    # Momento Cero (inmutable)
├── docker-compose.yml              # Full-stack deployment (6 servicios)
├── start_demo.sh                   # Script lanzador del stack
├── benchmark_full.py               # Benchmark Integral v2.0
│
├── docs/
│   ├── WHITEPAPER.md               # Paper técnico
│   ├── MATHEMATICS.md              # 🆕 Fundamentos matemáticos formales
│   ├── FIRMWARE_OTA.md             # 🆕 Guía de firmware y OTA
│   ├── architecture.md             # Arquitectura del sistema
│   ├── benchmarks.md               # Análisis de energía y rendimiento
│   ├── COMPARISON_TINYML.md        # Comparativa con frameworks edge
│   ├── api/
│   │   └── protocol_1bit.yaml      # Especificación OpenAPI 3.1
│   ├── technical/
│   │   └── esn_spec.md             # Especificación ESN
│   └── philosophy/                 # Extensiones filosóficas (ver Apéndice)
│
├── docker/
│   └── mosquitto/config/           # Configuración MQTT
│
├── paper/
│   ├── main.tex                    # Paper LaTeX
│   └── main.pdf                    # Paper compilado (3 páginas)
│
├── phase1-foundations/             # Python ESN + Core
├── phase2-core/                    # C Ultraligero + Dockerfile
├── phase3-integration/             # JavaScript Web (core)
├── phase4-hardware/                # Arduino + ESP32 + LoRa
├── phase5-applications/            # IoT: Bio, Voice, Temperature
├── phase6-collective/              # Mente Colectiva + MQTT + WebSocket
├── phase7-language/                # TinyLMv2 (Language Model)
├── phase8-paper/                   # Paper LaTeX original
│
└── web/                            # Servidor Web Principal
    ├── server.py                   # API REST Flask (~2300 líneas)
    ├── learning.py                 # Sistema de Aprendizaje Continuo
    ├── Dockerfile                  # Container web
    └── static/                     # Frontend
```

## 🚀 Ejecución Rápida (Local)

El proyecto incluye un entorno preconfigurado completo usando Docker Compose:

```bash
# Iniciar todos los servicios en segundo plano
docker compose up -d

# Ver los logs en tiempo real
docker compose logs -f
```

---

## ☁️ Despliegue en la Nube (Producción)

El ecosistema Eón AI está diseñado para funcionar en una arquitectura distribuida (Desacoplada):

- **Frontend (Vercel)**: La interfaz de usuario gráfica vive en Vercel. 
  - URL: `https://eon.scisenselab.com`
- **Backend (AWS EC2)**: Los modelos, el broker MQTT y la API viven en una instancia de AWS (`3.147.117.251`).
  - URL API: `https://api.eon.scisenselab.com`
  - WebSockets: `wss://api.eon.scisenselab.com/ws`

Para desplegar actualizaciones al backend en AWS:
1. Conéctate a la instancia EC2 por SSH.
2. Haz `git pull`.
3. Ejecuta `sudo docker compose up -d --build`.
4. El Proxy Inverso Caddy se encargará de enrutar automáticamente el tráfico HTTP a `5000` y WS a `8765`.

Para desplegar actualizaciones al frontend:
Simplemente sube tus cambios a la rama principal de GitHub y/o ejecuta `vercel --prod` en la carpeta `web/static/`.

---

## 📚 Estructura de Fases (Local)

```bash
./start_demo.sh              # Lanza MQTT, WebSocket, Web
./start_demo.sh --docker     # Usa Docker Compose
./start_demo.sh --no-browser # Sin abrir navegador
```

### Interfaz Web Principal (Manual)

```bash
cd "Eón Project AI"
python -m venv .venv && source .venv/bin/activate
pip install flask numpy pillow paho-mqtt websockets
python web/server.py
# Abrir http://localhost:5000
```

La interfaz web incluye:
- **Chat**: Conversación con Eón usando TinyLMv2
- **Dream**: Visualización del reservorio neuronal
- **Dashboard v2**: Monitoreo de red en tiempo real (`/dashboard`)
- **Estado**: Estadísticas y configuración de IA

### API Endpoints Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/status` | GET | Estado actual de Eón |
| `/api/chat` | POST | Enviar mensaje al chat |
| `/api/generate-image` | POST | Generar arte neuronal (5 estilos) |
| `/api/config` | GET/POST | Configuración de IA |
| `/api/stats` | GET | Estadísticas de uso |
| `/api/history` | GET/DELETE | Historial de chat |
| `/api/personality` | GET/POST | Configuración de personalidad |
| `/api/upload` | POST | Subir archivo para aprendizaje |
| `/api/learn-text` | POST | Aprender de texto |
| `/api/genesis` | GET | Info del Momento Cero |
| `/api/lm-status` | GET | Estado de TinyLMv2 |
| `/api/feedback` | POST | Enviar feedback 👍/👎 |
| `/api/learning-stats` | GET | Estadísticas de aprendizaje |
| `/api/memory` | GET/DELETE | Gestión de memoria a largo plazo |
| `/api/consolidate` | POST | Forzar consolidación ("sueño") |
| `/api/anomaly/detect` | POST | Detectar anomalías en datos |
| **`/dashboard`** | GET | **Dashboard v2.0 (D3.js)** |
| **`/api/nodes`** | GET | **Lista de nodos activos** |
| **`/api/anomalies`** | GET | **Eventos de anomalía** |
| **`/api/dashboard/stats`** | GET | **Estadísticas agregadas** |

### Demo Python

```bash
cd phase1-foundations/python
python -m venv .venv && source .venv/bin/activate
pip install numpy flask
python esn/esn.py
```

### Demo C (1.3KB)

```bash
cd phase2-core/libAeon
make && ./aeon_demo
# O usando CMake:
# mkdir -p build && cd build
# cmake .. && make && ./aeon_demo
```

### Demo Web Estática

```bash
cd phase3-integration/demos
python3 -m http.server 8888
# Abrir http://localhost:8888
```

### 📡 Demo MQTT Real

```bash
# Instalar Mosquitto (broker)
sudo apt install mosquitto mosquitto-clients

# Instalar cliente Python
pip install paho-mqtt

# Iniciar cliente Eón
cd phase6-collective
python mqtt_client.py --broker localhost --port 1883 --node-id sensor-001

# En otra terminal, otro nodo:
python mqtt_client.py --broker localhost --port 1883 --node-id sensor-002

# Comandos disponibles: sync, status, quit
```

### 📊 Dashboard de Monitoreo (Full-Stack)

El sistema de monitoreo incluye 3 componentes:

```bash
# 1. Iniciar Mosquitto MQTT Broker
sudo systemctl start mosquitto

# 2. Iniciar WebSocket Bridge (conecta MQTT con Dashboard)
cd phase6-collective
python ws_bridge.py --mqtt-broker localhost --ws-port 8765

# 3. Servir Dashboard HTML
python3 -m http.server 8888
# Abrir http://localhost:8888/dashboard.html
```

**Modo Simulación (sin broker MQTT):**
```bash
python ws_bridge.py --simulate --ws-port 8765
```

**Arquitectura Full-Stack:**
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   ESP32/     │────▶│  Mosquitto   │────▶│  ws_bridge   │
│   Sensors    │MQTT │    Broker    │     │   (Python)   │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                 │ WebSocket
                                           ┌─────▼─────┐
                                           │ Dashboard │
                                           │  (HTML)   │
                                           └───────────┘
```

### 📻 Demo ESP32 + LoRa

1. Abrir `phase4-hardware/esp32/examples/LoRa_1Bit_Demo.ino` en Arduino IDE
2. Instalar librerías: LoRa by Sandeep Mistry, ArduinoJson
3. Configurar pines según tu placa (TTGO LoRa32, Heltec, etc.)
4. Subir a dos o más ESP32
5. Observar sincronización automática en Serial Monitor

Ver [docs/FIRMWARE_OTA.md](docs/FIRMWARE_OTA.md) para guía completa de hardware y firmware.

---

## 📦 Instalación

### Arduino / PlatformIO

Descarga este repositorio como ZIP e impórtalo en Arduino IDE (`Sketch -> Include Library -> Add .ZIP Library`), o copia `phase4-hardware/arduino` a tu carpeta `libraries`.

### Javascript (NPM)

```bash
cd phase3-integration
npm install
import { Aeon } from './aeon.js';
```

### Python

```bash
cd phase1-foundations/python
pip install .
```

### Demo TinyLM

```bash
cd phase7-language
python server.py
# Abrir http://localhost:5001
```

### Tests Automatizados (Core C)

```bash
cd phase2-core
make test
# Ejecuta suite de validación: Inicialización, Memoria, Aprendizaje
```

## 🔬 Resultados

- **ESN Python**: MSE 0.0004 en Mackey-Glass
- **ESN C**: MSE 0.009 con punto fijo Q8.8
- **TinyLMv2**: 99.9% accuracy, tokenización word-level con **>50% reducción de memoria** (Trie)
- **Mente Colectiva**: Protocolo P2P funcional en ESP32 con compresión **17x** (1-Bit)
- **Consistencia**: "Spirit Hash" único (16 bytes) idéntico en Python, C y JS
- **Robustez**: Core C verificado con suite de pruebas unitarias
- **Eón Bio**: Detección de arritmias con <2KB RAM
- **Eón Voice**: Detección de palabras clave ("EÓN") en Cortex-M4
- **Chat Avanzado**: 20+ categorías de intención + memoria personal + predicción de secuencias
- **Predicción de Patrones**: Aritmético, geométrico, Fibonacci, potencias (100% precisión)
- **Base de Conocimiento**: Definiciones técnicas integradas (entropía, ESN, Spirit Hash, etc.)
- **Cuantización 8-bit**: 99.6% precisión retenida con 8x compresión

## 🐳 Docker Services

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| `mqtt` | 1883, 9001 | Eclipse Mosquitto MQTT broker |
| `ws-bridge` | 8765 | WebSocket-MQTT bridge |
| `web` | 5000 | Flask Dashboard principal |
| `tinylm` | 5001 | TinyLM Language Model server |
| `collective-mind` | - | Simulación distribuida |
| `core-builder` | - | Build C library (profile: build) |

## 📚 Documentación

| Documento | Descripción |
|-----------|-------------|
| [WHITEPAPER.md](docs/WHITEPAPER.md) | Paper técnico completo |
| [MATHEMATICS.md](docs/MATHEMATICS.md) | **🆕** Fundamentos matemáticos formales de Eón |
| [FIRMWARE_OTA.md](docs/FIRMWARE_OTA.md) | **🆕** Guía de firmware, OTA y deployment |
| [architecture.md](docs/architecture.md) | Arquitectura del sistema |
| [benchmarks.md](docs/benchmarks.md) | Análisis de energía y rendimiento |
| [COMPARISON_TINYML.md](docs/COMPARISON_TINYML.md) | Comparativa con frameworks edge |
| [protocol_1bit.yaml](docs/api/protocol_1bit.yaml) | Especificación OpenAPI 3.1 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Guía para contribuir |
| [CHANGELOG.md](CHANGELOG.md) | Historial de cambios |
| [paper/main.pdf](paper/main.pdf) | Paper académico PDF (3 páginas) |
| [Fase 4 README](phase4-hardware/README.md) | Hardware ESP32/LoRa |
| [Fase 5 README](phase5-applications/README.md) | Detalles Bio/Voice |

## 🧠 Sistema de Aprendizaje Continuo

Eón implementa un sistema de aprendizaje continuo inspirado en la neurociencia:

### Componentes

1. **OnlineLearner**: Actualización en tiempo real de W_out usando Recursive Ridge Regression
2. **LongTermMemory**: Almacenamiento persistente de usuarios, hechos, estadísticas
3. **FeedbackSystem**: Mejora basada en retroalimentación 👍/👎
4. **ConsolidationEngine**: Optimización durante períodos de inactividad ("sueño")

### Flujo de Aprendizaje

```
Interacción → OnlineLearner → Feedback → LongTermMemory → Consolidación
     ↑                                           ↓
     └───────────── Mejora Continua ─────────────┘
```

### Datos Almacenados

- **Usuarios conocidos**: Nombres, roles, información personal
- **Hechos aprendidos**: Preferencias, conocimiento específico
- **Patrones exitosos**: Asociados con feedback positivo
- **Estadísticas**: Eventos de aprendizaje, consolidaciones, ratio de éxito

## 🧪 Tests

```bash
# Ejecutar todos los tests
cd "Eón Project AI/phase1-foundations/python"
pip install pytest pytest-asyncio
python -m pytest tests/ -v

# Resultado: 720 tests passing
# - ESN Core & Foundations: 533 tests (Core ESN, Plasticidad, Cuantización, Anomaly Detector, RNG, etc.)
# - Mente Colectiva (Collective Mind): 63 tests (Conexiones distribuidas, Quantum Sync, Marca de agua neural)
# - Modelo de Lenguaje (TinyLMv2 & Attention): 54 tests
# - Web & Dashboard: 70 tests
```

## 🗓️ Roadmap

- [x] Fase 1-3: Fundamentos (Python, C, JS) + **Dream**
- [x] Fase 4: Hardware (Arduino, ESP32) + LoRa + Energía
- [x] Fase 5: Aplicaciones IoT + **Bio** + **Voice**
- [x] Fase 6: Mente Colectiva + MQTT real + WebSocket
- [x] Fase 7: TinyLM (Language Model)
- [x] Fase 8: Paper académico compilado (PDF)
- [x] Fase 9: Empaquetado + Docker Compose
- [x] Fase 10: Tests + OpenAPI + Demo Script
- [x] Fase 11: Extensiones Filosóficas (ver Apéndice B)
- [x] **Fase 12: v2.0** ← ACTUAL
  - [x] Dashboard v2.0 (D3.js, tiempo real)
  - [x] Chat Multi-Nodo Colaborativo
  - [x] Detector de Anomalías Streaming
  - [x] 720 Tests (cobertura ~92%)
- [ ] Fase 13: Publicación y Comunidad

---

## Apéndice A: Filosofía del Proyecto

> _"La inteligencia no se crea, se descubre."_

Eón demuestra que la inteligencia puede emerger de **recursos mínimos**. Mientras GPT-4 usa ~1.7 trillones de parámetros, Eón opera con **1.3KB de memoria**. El reservoir aleatorio contiene computación latente — no necesitamos construir inteligencia, solo necesitamos encontrar las configuraciones que ya la contienen.

### Paradigma de Descubrimiento

El enfoque de Eón difiere fundamentalmente de los frameworks convencionales:

| Convencional | Eón |
|-------------|-----|
| Entrenar millones de pesos | Buscar la semilla correcta |
| Backpropagation costoso | Regresión lineal simple |
| Modelo estático post-deployment | Aprendizaje continuo on-device |
| Requiere GPU para entrenar | Entrena en MCU de $1 |

---

## Apéndice B: Extensiones Filosóficas

Eón incorpora conceptos de tradiciones filosóficas como **metáforas computacionales**. Estas extensiones son opcionales y no afectan el funcionamiento core del sistema.

| Módulo | Concepto | Aplicación Técnica |
|--------|----------|-------------------|
| Poda Dinámica (Tzimtzum) | Contracción/regeneración | Poda del 50% de conexiones débiles y regeneración |
| Pipeline ETL (Alquimia) | Transmutación de datos | Ingesta → Filtrado Kalman → Inferencia ESN |
| ESN Recursivo (Fractal) | Escalas jerárquicas | Micro/meso/macro con ratio áureo (φ=0.618) |
| Embeddings Numéricos (Gematria) | Valores numéricos | Capa de embedding basada en sumas numéricas |
| Mente Grupal (Egrégor) | Consciencia colectiva | Cross-correlation de estados entre nodos |
| Task Affinity (Thelema) | Especialización nodal | Vector de afinidad por dominio de datos |

Documentación detallada en `docs/philosophy/`.

---

## 📜 Licencia

Este proyecto tiene **Licenciamiento Dual**:

1.  **Open Source:** [GNU Affero General Public License v3.0 (AGPLv3)](LICENSE). Ideal para uso comunitario, educativo y proyectos open source que compartan sus mejoras.
2.  **Comercial:** Disponible bajo licencia comercial (Custom License) con Royalties para uso propietario sin copyleft. Ver [COMMERCIAL_TERMS.md](COMMERCIAL_TERMS.md) para más detalles.

Copyright (c) 2024 [SenseLab](https://github.com/SenseLab-dev)

**SenseLab - Build with Sense**
