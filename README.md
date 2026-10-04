# ⚡ Proyecto Eón: Arquitectura Emergente y Optimización Neuromórfica

> **A.E.O.N.** — Arquitectura Emergente y Optimización Neuromórfica

[Badges]

---

## ⚖️ Licenciamiento Dual de Eón

[Existing Licensing Text]

---

## 🎯 ¿Qué es Eón?

Eón es una plataforma de inteligencia artificial ultraligera y eficiente, diseñada específicamente para entornos de edge computing e IoT. Se basa en el paradigma de Reservoir Computing, utilizando Echo State Networks (ESN) para operar con requisitos de memoria excepcionalmente bajos, lo que la hace ideal para microcontroladores y dispositivos con recursos limitados donde los frameworks tradicionales de IA no son viables.

### Desafíos del Edge vs. Solución de Eón

[Existing table for Problem vs Solution]

### 📊 Comparativa de Huella de Memoria

[Existing Memory Comparison Table]

---

## ✨ Características Técnicas Principales

Esta sección detalla las funcionalidades clave de Eón y su relevancia técnica.

| Característica              | Descripción Técnica                                                                                                                                                                                                                                                                                                                                                                                                                            |
| :-------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Núcleo Ultraligero (C)**  | Implementación fundamental en C con una huella de memoria de solo 1.3 KB, optimizada para microcontroladores y entornos con RAM extremadamente limitada.                                                                                                                                                                                                                                                                                        |
| **Multi-plataforma**        | Compatibilidad nativa con Python para desarrollo de alto nivel y simulación, C/C++ para rendimiento en el edge, JavaScript para interfaz web, y firmware para Arduino/ESP32, garantizando versatilidad en el despliegue.                                                                                                                                                                                                                          |
| **Reservoir Computing (ESN)**| Utiliza Echo State Networks, un tipo de Red Neuronal Recurrente, para procesar series temporales con un entrenamiento mínimo y eficiente. La dinámica intrínseca del "reservoir" proporciona una memoria temporal inherente para el reconocimiento de patrones y la predicción.                                                                                                                                                                      |
| **Aprendizaje Continuo On-Device**| Implementa algoritmos de aprendizaje online (regresión lineal adaptativa) que permiten al modelo ajustarse y mejorar continuamente en el dispositivo con nuevos datos, sin necesidad de re-flashear el firmware o depender de reentrenamiento en la nube.                                                                                                                                                                                  |
| **Protocolo de Sincronización 1-Bit**| Un protocolo de comunicación propietario ultraligero que optimiza la transferencia de datos de estado y pesos del modelo. Logra una compresión de ~8.3x en el tamaño del paquete y reduce el consumo energético en la transmisión.                                                                                                                                                                                                             |
| **Integración MQTT Nativa**| Cliente paho-mqtt integrado para una comunicación robusta y eficiente con brokers MQTT estándar, facilitando la integración en arquitecturas IoT distribuidas.                                                                                                                                                                                                                                                                                         |
| **Conectividad ESP32 + LoRa**| Soporte para el SoC ESP32 con módulos LoRa, permitiendo transmisión inalámbrica de largo alcance y bajo consumo (P2P), ideal para redes de sensores distantes o entornos con conectividad limitada.                                                                                                                                                                                                                                                    |
| **Dashboard Web Interactivo v2.0**| Interfaz de usuario basada en D3.js para la visualización en tiempo real del estado de la red Eón, monitoreo de métricas operacionales y un timeline de anomalías detectadas.                                                                                                                                                                                                                                                                          |
| **Sistema de Chat Multi-Nodo**| Arquitectura de chat distribuida donde nodos especializados (INTENT, RESPONSE, COHERENCE, SENTIMENT, CONTEXT) colaboran para procesar y generar respuestas, optimizando la gestión del diálogo y la inferencia contextual.                                                                                                                                                                                                                             |
| **Detección de Anomalías en Streaming**| Algoritmos de detección de anomalías en tiempo real con calibración dinámica y capacidad de ejecutar callbacks personalizables ante diferentes niveles de severidad (LOW, MEDIUM, HIGH, CRITICAL).                                                                                                                                                                                                                                              |
| **TinyLMv2 (Word-Level)**   | Un modelo de lenguaje compacto diseñado para inferencia eficiente a nivel de palabra en el edge, facilitando capacidades básicas de procesamiento de lenguaje natural en dispositivos con recursos limitados.                                                                                                                                                                                                                                          |
| **RAG Ligero (Edge)**       | Implementación de Retrieval-Augmented Generation (RAG) optimizada para el edge, permitiendo búsquedas semánticas en documentación local para enriquecer las respuestas generadas sin dependencia de la nube.                                                                                                                                                                                                                                         |
| **Memoria Factual con Timestamps**| Sistema de memoria a largo plazo que incorpora timestamps para resolver ambigüedades temporales y contextuales en los datos, mejorando la coherencia y relevancia de las respuestas.                                                                                                                                                                                                                                                              |
| **Sistema de Feedback Adaptativo**| Mecanismo de mejora continua basado en la retroalimentación positiva/negativa (👍/👎), permitiendo al sistema ajustar sus parámetros y comportamiento de forma incremental.                                                                                                                                                                                                                                                                       |
| **Predicción Avanzada de Secuencias**| Capacidades para predecir patrones aritméticos, geométricos, Fibonacci, y series de potencias, demostrando la habilidad del ESN para aprender y generalizar relaciones complejas en series temporales.                                                                                                                                                                                                                                               |
| **Arte Generativo Integrado**| Módulo para la generación de arte visual en 5 estilos distintos (fractal, flujo, partículas, ondas, neural), mostrando la capacidad creativa de la IA en el edge.                                                                                                                                                                                                                                                                                          |
| **Cuantización Multi-nivel**| Soporte para cuantización de pesos y activaciones a 8-bit, 4-bit, y 1-bit, con análisis de retención de información, crucial para reducir la huella de memoria y el consumo energético sin sacrificar excesivamente la precisión.                                                                                                                                                                                                                         |
| **Actualizaciones OTA (ESP32)**| Implementación robusta de actualizaciones Over-The-Air para dispositivos ESP32, permitiendo la actualización remota de firmware y modelos de IA sin intervención física.                                                                                                                                                                                                                                                                                  |
| **Persistencia Circadiana** | Soporte para guardar y cargar estados de red ESN (`use_circadian`, `dropout`, `learning_rate`) en archivos `.npz` y metadatos JSON, facilitando la gestión de modelos y la reanudación del aprendizaje.                                                                                                                                                                                                                                                      |
| **Ciclos Circadianos & Entrenamiento Adaptativo** | Modulación dinámica de parámetros clave como el ruido del reservoir y la tasa de aprendizaje (`learning_rate`) durante el entrenamiento, inspirada en ritmos biológicos, para optimizar la convergencia y la adaptabilidad. El dropout se basa en la energía interna del sistema.                                                                                                                                                                   |
| **Homeostasis & Watermark Neural**| Mecanismos avanzados para la sincronización robusta de pesos de 1-bit y la verificación de la integridad del modelo mediante firmas de hash criptográficas, garantizando la estabilidad y autenticidad del sistema en entornos distribuidos.                                                                                                                                                                                                   |

---

## 📈 Benchmarks y Rendimiento

Documentación de benchmarks completa disponible en [docs/benchmarks.md](/home/dawnweaber/Workspace/Eón Project AI/docs/benchmarks.md).

### Consumo Energético por Ciclo (Cortex-M4F @ 80MHz, N=50)

[Existing table]

### Comparativa de Eficiencia Energética en Inferencia

[Existing table and explanation]

### Estimación de Vida Útil de Batería (1 inferencia/seg, deep sleep)

[Existing table and explanation]

Para un análisis matemático exhaustivo, consulte [docs/MATHEMATICS.md](/home/dawnweaber/Workspace/Eón Project AI/docs/MATHEMATICS.md).

---

## 📡 Hardware y Firmware

### Hardware Soportado

[Existing table]

### Métricas de Comunicación (Protocolo 1-Bit vs JSON)

[Existing table]

### Documentación de Firmware y OTA

Acceda a la documentación completa sobre firmware, actualización over-the-air, compatibilidad y deployment en: **[docs/FIRMWARE_OTA.md](/home/dawnweaber/Workspace/Eón Project AI/docs/FIRMWARE_OTA.md)**

---

## 📁 Estructura del Proyecto
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
│   ├── ROADMAP.md                  # 🆕 Roadmap de ingeniería y matemática (v2.5-v3.5)
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

## 🗓️ Roadmap del Proyecto

El desarrollo de Eón evoluciona desde sus fundamentos hacia el estándar industrial de **TinyML con aprendizaje continuo on-device**. El plan de ingeniería detallado con formulaciones matemáticas y criterios de aceptación está disponible en **[docs/ROADMAP.md](docs/ROADMAP.md)**.

### ✅ Fases Completadas (v1.0 – v2.4.1)

- [x] **Fase 1-3: Fundamentos**: Núcleo C ultraligero (1.3 KB), Python ESN, JavaScript Web.
- [x] **Fase 4: Hardware & Edge**: Arduino Library, ESP32 + LoRa, métricas energéticas.
- [x] **Fase 5: Aplicaciones IoT**: Sensores biomédicos, clasificación de voz y temperatura.
- [x] **Fase 6: Mente Colectiva**: Broker MQTT real, sincronización WebSocket y consenso.
- [x] **Fase 7-9: TinyLM & Full-Stack**: TinyLMv2, Docker Compose, Paper académico compilado.
- [x] **Fase 10-12: v2.0 – v2.4.1 (Estado Actual)**:
  - [x] Dashboard v2.0 (D3.js en tiempo real)
  - [x] Chat Multi-Nodo Colaborativo
  - [x] Detector de Anomalías Streaming
  - [x] Sincronización 1-Bit robusta con verificación de hash
  - [x] Persistencia de ciclos circadianos en estados `.npz` y JSON
  - [x] Suite de 720 tests automatizados (cobertura ~92%)
  - [x] Consolidación matemática formal ([docs/MATHEMATICS.md](docs/MATHEMATICS.md))
  - [x] Ecosistema de firmware y OTA ([docs/FIRMWARE_OTA.md](docs/FIRMWARE_OTA.md))
  - [x] Nueva tabla de energía total por ciclo y benchmarks normalizados ([docs/benchmarks.md](docs/benchmarks.md))

### 🚀 Nuevas Fases de Ingeniería Matemática (v2.5 – v3.5)

- [ ] **Fase 13 (v2.5): Control Numérico y Estabilidad Dinámica**
  - [ ] Monitor online de estabilidad: Máximo exponente de Lyapunov y guardián de radio espectral $\rho(W) < 1$ en tiempo real.
  - [ ] Optimización analítica de Capacidad de Memoria ($MC$) acoplada a la autocorrelación de señal $R_{uu}(\tau)$.
  - [ ] Recursive Least Squares (RLS) con factor de olvido exponencial $\beta$ y factorización U-D para evitar pérdida de condición positiva.
  - [ ] Reservoirs ortogonales estrictos mediante transformación de Cayley.
- [ ] **Fase 14 (v2.6): Aceleración DSP Hardware y Optimización SIMD**
  - [ ] Vectorización CMSIS-DSP para ARM Cortex-M4/M7/M33 (`__SMLAD`, `arm_dot_prod_q15`), reduciendo inferencia a $< 8.4$ µs y $0.00042$ µJ.
  - [ ] Extensiones vectoriales ESP32-S3 (ESP-DSP PIE) con arquitectura asimétrica de doble núcleo.
  - [ ] Aritmética Block Floating Point (BFP Q1.14) con retención de precisión del 98% vs float64.
  - [ ] Despertar por evento neuromórfico (interrupción de derivada analógica para autonomía $> 5$ años).
- [ ] **Fase 15 (v2.7): Edge Mesh Distribuido, Sincronización y OTA Seguro**
  - [ ] Compresión diferencial Delta-RLE para sincronización LoRa (payload reducido de 21B a 4–6B, duplicando autonomía con radio activa).
  - [ ] Federated Averaging descentralizado (Decentralized FedAvg) sobre consenso binario 1-bit en enjambre sin servidor central.
  - [ ] Verificación criptográfica Ed25519 integrada para binarios OTA y paquetes de sincronización de pesos.
  - [ ] Adaptive Data Rate (ADR) para LoRa según SNR/RSSI.
- [ ] **Fase 16 (v3.0): Tooling de Producción, Interoperabilidad y Certificación**
  - [ ] Compilador `eon2c` AOT: Generador de código C99 puro estático con matrices en Flash ROM (zero RAM footprint).
  - [ ] Harness de co-simulación bit-exact (Python ↔ C) validado en CI/CD con QEMU ARM.
  - [ ] Certificación formal en la suite MLCommons / TinyML Perf (Mackey-Glass, IMS Bearings, MIT-BIH ECG).
  - [ ] Módulos oficiales para Zephyr RTOS y MicroPython/CircuitPython.

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
