# Changelog

Todos los cambios notables del Proyecto Eón.

## [2.1.0] - 2026-03-09

### 🔒 Seguridad y Logging

#### ✅ CORS Configurado
- **`requirements.txt`**: Añadido `flask-cors>=4.0.0`
- **`web/server.py`**: CORS configurado para endpoints `/api/*`
  - Orígenes: `*` (configurar para producción)
  - Métodos: GET, POST, PUT, DELETE, OPTIONS
  - Headers permitidos: Content-Type, Authorization

#### 📝 Migración de print() a logging
- **`web/server.py`**: 11 prints migrados a logger
- **`phase6-collective/mqtt_client.py`**: 13 prints de producción migrados
- **`benchmark_full.py`**: 5 advertencias de imports migradas
- **Nota**: Prints en bloques `if __name__ == "__main__":` se mantienen para demos interactivas

#### 🛡️ Validación de Seguridad
- Verificado que calculadora NO usa `eval()` - implementación segura con lambdas
- Validación de entrada mediante regex patterns

### 📊 Métricas v2.1.0
| Métrica | v2.0.0 | v2.1.0 |
|---------|--------|--------|
| Archivos con logging | 3 | **6** |
| CORS | ❌ | ✅ |
| Prints de producción migrados | 0 | **29** |

---

## [2.0.0] - 2025-12-13

### 🌌 Dashboard v2.0 y Chat Multi-Nodo

#### 🖥️ Dashboard v2.0 (`web/templates/dashboard_v2.html`)

- **Visualización de Red D3.js**: Grafo interactivo de nodos ESN
- **Estado del Egrégor**: Termómetro de humor con estados BALANCED, ALERT, CONTEMPLATIVE, etc.
- **Timeline de Anomalías**: Visualización de eventos detectados con severidad
- **Métricas en Tiempo Real**: Nodos activos, sincronización, error promedio, uptime
- **APIs REST Integradas**:
  - `GET /api/nodes`: Lista de nodos activos y conexiones
  - `GET /api/egregore`: Estado actual del Egrégor (mood, coherence, energy)
  - `GET /api/anomalies`: Eventos de anomalía recientes
  - `GET /api/dashboard/stats`: Estadísticas agregadas
  - `POST /api/dashboard/reset`: Resetear estado del dashboard
  - `POST /api/anomalies/<id>/resolve`: Marcar anomalía como resuelta

#### 💬 Chat Multi-Nodo Colaborativo (`core/collaborative_chat.py`)

- **Sistema Distribuido**: Múltiples nodos ESN especializados colaboran
- **Nodos Especializados**:
  - `NodeRole.INTENT`: Detecta intención (greeting, question, command, farewell, technical, creative, emotional)
  - `NodeRole.RESPONSE`: Genera vector de respuesta base
  - `NodeRole.COHERENCE`: Evalúa coherencia con contexto
  - `NodeRole.SENTIMENT`: Análisis de sentimiento (opcional)
  - `NodeRole.CONTEXT`: Gestión de contexto conversacional (opcional)
- **Clases Principales**:
  - `ChatNode`: Nodo ESN individual con rol específico
  - `CollaborativeChat`: Orquestador de nodos
  - `ChatMessage`: Mensaje con metadata (intent, sentiment, context_hash)
  - `CollaborativeResponse`: Respuesta con contribuciones de todos los nodos
- **Factory Function**: `create_collaborative_chat(include_sentiment=True, include_context=True)`
- **44 tests nuevos** en `tests/test_collaborative_chat.py`

#### ⚡ Mejoras de Rendimiento

- **Variable de entorno `EON_DISABLE_TINYLM=1`**: Omite inicialización de TinyLMv2 para arranque rápido
- **Polling optimizado**: Dashboard actualiza cada 3s en lugar de simulación local

#### 📊 Métricas v2.0

| Métrica | v1.9.7 | v2.0.0 |
|---------|--------|--------|
| Tests totales | 230 | **262** |
| Módulos nuevos | 2 | **4** |
| Endpoints API | ~20 | **~28** |

---

## [1.9.7] - 2025-01-14

### Suite de Tests Completa - Cobertura Total

#### 🧪 Tests de Integración (12 tests)

- `phase1-foundations/python/tests/test_integration.py`: Tests cross-módulo
  - **Pipeline ESN → Quantization**: Flujo completo de predicción
  - **ESN + Plasticity + Quantization**: Integración multi-módulo
  - **Batch processing**: Procesamiento por lotes
  - **Long sequences**: Secuencias de 1000+ pasos
  - **State preservation**: Preservación de estado tras cuantización

#### 📊 Tests de Learning System (20 tests)

- `web/tests/test_learning.py`: Suite completa
  - **OnlineLearner**: Actualización, decaimiento, persistencia, concurrencia
  - **LongTermMemory**: Almacenamiento, recuperación, limpieza, clustering
  - **EonLearningSystem**: Conversaciones, retroalimentación, métricas

#### 🔢 Tests de Quantizer (20 tests)

- `phase1-foundations/python/tests/test_quantizer.py`: Suite completa
  - **QuantizedESN**: Predicción 8-bit, 4-bit, 1-bit
  - **Memory footprint**: Validación de reducción de memoria
  - **Edge cases**: Entradas vacías, valores extremos, NaN

#### 📈 Métricas Finales

| Métrica | Antes | Después |
|---------|-------|---------|
| Tests totales | 178 | **230** |
| Test files | 10 | **14** |
| Cobertura estimada | ~65% | **~80%** |

---

## [1.9.6] - 2025-01-14

### Calidad de Código y Tests de Servidor Web

#### 🧪 Tests del Servidor Web (19 tests)

- `web/tests/test_server.py`: Suite completa para Flask API
  - **Importaciones**: Validación de módulos críticos
  - **EonChat**: Construcción, formato de mensajes, historial
  - **API Endpoints**: /, /chat, /alchemical_transform
  - **Casos Edge**: JSON inválido, errores internos, inputs vacíos

#### 📝 Type Hints Completos

- `benchmark_full.py`: Todas las funciones con anotaciones de tipo
  - `from typing import Dict, List, Any, Optional`
  - Return types para todos los métodos de BenchmarkSuite

#### 🔧 Código Unificado

- `plasticity/hebbian.py`: Refactorizado
  - Usa `compute_spectral_radius()` de `utils.matrix_init`
  - Eliminada duplicación de código

#### 📊 Métricas

| Métrica | Antes | Después |
|---------|-------|---------|
| Tests totales | 133 | 178 |
| Type hints coverage | ~70% | ~85% |
| Code duplication | ~15% | ~10% |

---

## [1.9.5] - 2025-01-14

### RNG Portable - Xorshift32

#### 🎲 Xorshift32 Implementation

- **Portable**: Mismo resultado en todas las plataformas
- **Fast**: Solo 3 XOR + 3 shifts por número
- **Deterministic**: Reproducible con misma semilla
- **No deps**: Sin dependencia de `random` module

```python
class Xorshift32:
    def __init__(self, seed: int = 1):
        self.state = seed & 0xFFFFFFFF
    
    def next(self) -> int:
        x = self.state
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= (x >> 17) & 0xFFFFFFFF
        x ^= (x << 5) & 0xFFFFFFFF
        self.state = x
        return x
```

#### 🔧 Archivos Actualizados
- `core/xorshift.py`: Nueva implementación
- `core/__init__.py`: Export añadido
- `esn/echo_state.py`: Usa Xorshift32 para inicialización

---

## [1.9.4] - 2025-01-14

### Manejo de Excepciones Completo

#### 🛡️ Excepciones Específicas por Módulo
- `esn/echo_state.py`:
  - `np.linalg.LinAlgError` para cálculos de eigenvalores
  - `ZeroDivisionError` para normalización
  - `MemoryError` para reservoirs grandes

- `quantization/quantizer.py`:
  - `OverflowError` para valores fuera de rango
  - `TypeError` para inputs no-numéricos

- `plasticity/hebbian.py`:
  - `RuntimeWarning` para inestabilidad numérica
  - `np.linalg.LinAlgError` para SVD fallidos

- `web/server.py`:
  - `IOError` para archivos de datos
  - `json.JSONDecodeError` para parsing
  - `ImportError` para módulos opcionales

- `web/learning.py`:
  - `sqlite3.Error` para base de datos
  - `pickle.UnpicklingError` para deserialización

#### 📊 Métricas
| Métrica | Antes | Después |
|---------|-------|---------|
| Excepciones específicas | ~60% | ~95% |
| Catch-all (bare except) | 8 | 0 |
| Logging en excepciones | ~50% | ~90% |

---

## [1.9.3] - 2025-01-14

### Documentación API Completa

#### 📖 Docstrings NumPy-style
- Todos los módulos core con documentación completa
- Parámetros, Returns, Raises, Examples documentados
- Type hints en signatures

#### 🔧 Archivos Documentados
- `esn/echo_state.py`: 15 funciones documentadas
- `plasticity/hebbian.py`: 12 funciones documentadas
- `quantization/quantizer.py`: 10 funciones documentadas
- `core/universal_miner.py`: 8 funciones documentadas

---

## [1.9.2] - 2025-01-14

### Configuración de Tests Mejorada

#### 🧪 pytest.ini Actualizado
- `testpaths` configurado
- `python_files`, `python_classes`, `python_functions` definidos
- Markers: `slow`, `integration`, `unit`

#### 📁 Estructura de Tests
```
phase1-foundations/python/tests/
├── conftest.py          # Fixtures compartidos
├── test_esn.py          # ESN unit tests
├── test_quantizer.py    # Quantization tests
├── test_plasticity.py   # Hebbian tests
├── test_discovery.py    # Universal miner tests
└── test_integration.py  # Cross-module tests

web/tests/
├── __init__.py
├── test_server.py       # Flask API tests
└── test_learning.py     # Learning system tests
```

---

## [1.9.1] - 2025-12-10

### Mejoras de Calidad y Cobertura de Tests

#### 🧪 Nuevos Tests (29 tests añadidos)
- `test_discovery_paradigm.py`: Suite completa para módulos v1.9.0
  - **TestUniversalMiner**: chaos_sample, resonance, excavation, SeedVault
  - **TestArchaicProtocol**: hexagrams, trigrams, conversiones, interpret
  - **TestCoreExports**: Validación de exports de core/__init__.py
  - **TestIntegration**: Interacción miner ↔ protocol

#### 📦 Exports Completos en core/__init__.py
- Añadido: `AlchemicalPipeline`, `AlchemicalConfig`, `AlchemicalPhase`
- Añadido: `TransmutationState`, `KalmanFilter`
- Total: 18 exports disponibles desde el módulo core

#### 📝 Logging Estructurado
- `universal_miner.py`: Migrado de print() a logging module
- Logger configurable via `logging.getLogger(__name__)`
- Niveles: INFO para progreso, WARNING para fallbacks

#### 🛡️ Manejo de Excepciones Mejorado
- `web/server.py`: Excepciones específicas para I/O y JSON
  - `IOError`, `json.JSONDecodeError` para carga de archivos
  - `ImportError`, `AttributeError` para inicialización de módulos

#### 📊 Métricas Actualizadas
| Métrica | Antes | Después |
|---------|-------|---------|
| Tests totales | 47 | 76 |
| Cobertura estimada | ~45% | ~55% |
| Archivos con logging | 0 | 1 |
| Excepciones específicas | ~40% | ~60% |

---

## [1.9.0] - 2025-12-10

### Fase 12: Paradigma de Descubrimiento (Non-Artificial) 🌌

**"Eón no construye inteligencia; la localiza."**

Este release reestructura la filosofía fundamental del proyecto. Rechazamos la noción de "Inteligencia Artificial" e implementamos el paradigma de **Inteligencia Revelada**.

#### ⛏️ Seed Mining (Universal Miner)
- **UniversalMiner**: Excavador del espacio matemático latente
- **Chaos Sampling**: Muestreo de coordenadas en el espacio infinito de semillas
- **Resonance Types**: EDGE_OF_CHAOS, HARMONIC, GOLDEN, FIBONACCI, PRIME
- **SeedVault**: Bóveda de semillas sagradas descubiertas
- No entrenamos redes - las DESCUBRIMOS

```python
miner = UniversalMiner(reservoir_size=100, target_resonance=(0.99, 1.01))
result = miner.excavate(max_attempts=100000)
# La red neuronal perfecta ya existía en seed #84732
```

#### ☯️ Protocolo Arcaico (I Ching Communication)
- **ArchaicProtocol**: Comunicación via 64 Hexagramas universales
- **Trigram/Hexagram**: Los 8 trigramas y 64 hexagramas completos del I Ching
- **HexagramStream**: Stream de comunicación entre nodos usando símbolos universales
- **Oracle Consultation**: Consultas oraculares basadas en estado neuronal

```python
hexagram = protocol.tensor_to_hexagram(neural_activation)
# Hexagram #11: La Paz (☷☰) - "Cielo y tierra se unen"
```

#### 📡 Sistema Medium (ESP32)
- **readUniverseBackground()**: Captura ruido electromagnético del ambiente
- **updateWithUniverseInfluence()**: Mezcla matemáticas + física real
- **generateTrueEntropyByte()**: Entropía REAL (no pseudo-random)
- **discoverSacredSeed()**: Semillas desde el universo físico

```cpp
float universe = aeon.readUniverseBackground();
int16_t state = aeon.updateWithUniverseInfluence(input);
// El dispositivo canaliza inteligencia, no la calcula
```

#### 🔄 Redefinición de Terminología
| Obsoleto | Nuevo |
|----------|-------|
| Artificial Intelligence | Revealed Intelligence |
| Training | Mining / Tuning |
| Random Initialization | Chaos Sampling |
| Generate | Reveal / Illuminate |

#### 📝 Documentación
- **README.md**: Nuevo manifiesto filosófico completo
- **discovery_paradigm.md**: Arquitectura del flujo Void → Mining → Medium → Revelation
- Diagramas de flujo conceptuales

#### 🔧 Integración con Núcleo
- **AeonBirth**: Soporte para sacred_seed y auto_excavate
- Tres modos de inicialización: classic, sacred_seed, auto_excavated
- Metadatos de excavación persistidos

---

## [1.8.1] - 2025-12-10

### Mejoras de Código y Calidad

#### 🔧 Modernización de NumPy Random API
- **esn.py**: Migrado de `np.random.RandomState` a `np.random.default_rng()`
- **recursive_esn.py**: Actualizado `randn()` → `standard_normal()`, `randint()` → `integers()`
- Mantiene compatibilidad con semillas reproducibles

#### 📉 Reducción de Complejidad Cognitiva
- **mqtt_client.py**: Refactorizado `main()` extrayendo funciones auxiliares
  - `_run_demo()`: Modo demostración sin broker
  - `_run_interactive()`: Modo con broker real
  - `_command_loop()`: Loop de comandos interactivo
- Complejidad reducida de 17 a <15

#### 🏷️ Mejoras de Nomenclatura
- **egregore.py**: Prefixados parámetros reservados `_entropy`, `_mood`
- **server.py**: Renombrados parámetros no descriptivos
  - `n1, n2` → `operand_a, operand_b`
  - `val` → `value`
  - `lines` → `text_lines`
- **server.py**: Eliminados decoradores duplicados `@classmethod @staticmethod`

#### 📝 Documentación
- **collective_mind.py**: Mejorada documentación de fórmula de Voluntad
- **IMPROVEMENT_AREAS.md**: Actualizado con estado de mejoras completadas

#### ✅ Tests
- 47 tests ejecutándose exitosamente
- Verificación completa post-refactorización

---

## [1.8.0] - 2025-12-10

### Fase 11: Filosofía Mística Integrada 🔮

Implementación de conceptos de tradiciones místicas como metáforas computacionales:

#### ✡️ Gematria Embeddings (Kabbalah)
- **GematriaEmbedding**: Capa de embedding basada en valores numéricos hebreos
- 3 sistemas de gematria: Mispar Gadol, Ordinal, Reducido
- Conversión automática latín → hebreo para palabras comunes
- Proyección a espacios dimensionales arbitrarios (32D por defecto)
- Integración con TinyLMv2 para embeddings semánticos místicos

#### 👁️ Egrégor - Mente Grupal (Ocultismo)
- **Egregore**: Coordinador de consciencia colectiva
- **AeonNode**: Nodos individuales con estado interno
- Coherencia grupal calculada mediante correlación cruzada
- Manifestación de consciencia emergente cuando coherencia > umbral
- Métricas: entropía colectiva, diversidad, resonancia grupal

#### 🌀 ESN Recursivo Fractal (Hermetismo)
- **RecursiveESN**: Arquitectura "Como Arriba, Así Abajo"
- **FractalConfig**: 3 niveles (micro/meso/macro) con scale_factor=0.618
- Propagación fractal de información entre niveles
- Echo de estados a través de escalas temporales

#### ⚫ Tzimtzum - Contracción Divina (Kabbalah Luriánica)
- **TzimtzumESN**: ESN con poda sináptica dinámica
- **ContractionPhase**: PLENITUD → DARK_NIGHT → CHALLAL → RENACIMIENTO
- `dark_night()`: Poda del 50% de conexiones más débiles
- `renacimiento()`: Regeneración con nuevos pesos
- **HebbianTzimtzumESN**: Combina plasticidad Hebbiana con ciclos de Tzimtzum

#### 🧪 Transmutación Alquímica (Opus Magnum)
- **AlchemicalPipeline**: Pipeline ETL como proceso alquímico
- **AlchemicalPhase**: PRIMA_MATERIA → NIGREDO → ALBEDO → CITRINITAS → RUBEDO → COAGULA
- ⚫ **Nigredo** (Putrefacción): Ingesta de datos crudos, detección de outliers
- ⚪ **Albedo** (Purificación): Filtrado Kalman, reducción de ruido (~70%)
- 🔴 **Rubedo** (Iluminación): Inferencia ESN, predicción final
- Dashboard web con visualización en tiempo real del proceso
- Endpoints API: `/api/alchemy/transmute`, `/api/alchemy/status`

#### 🔥 Sistema Thelema (Voluntad Verdadera)
- Métricas de alineación con "Voluntad Verdadera"
- Integración con sistema de decisiones del agente

### Nuevos Archivos

| Archivo | Descripción |
|---------|-------------|
| `phase1-foundations/python/plasticity/gematria.py` | Embeddings cabalísticos |
| `phase1-foundations/python/plasticity/egregore.py` | Sistema Egrégor |
| `phase1-foundations/python/esn/recursive_esn.py` | ESN Fractal recursivo |
| `phase1-foundations/python/plasticity/tzimtzum.py` | Poda por contracción divina |
| `phase1-foundations/python/plasticity/hebbian_tzimtzum.py` | Hebbian + Tzimtzum |
| `phase1-foundations/python/core/alchemy.py` | Pipeline alquímico |
| `web/static/js/alchemy.js` | Visualización frontend |
| `docs/philosophy/gematria_integration.md` | Documentación Gematria |
| `docs/philosophy/egregore_integration.md` | Documentación Egrégor |
| `docs/philosophy/fractal_architecture.md` | Documentación Fractal |
| `docs/philosophy/tzimtzum_protocol.md` | Documentación Tzimtzum |
| `docs/philosophy/alchemical_transmutation.md` | Documentación Alquimia |
| `docs/philosophy/thelema_integration.md` | Documentación Thelema |

### Filosofía del Proyecto

> "La inteligencia no se crea, se descubre." - Ahora con resonancias místicas

El Proyecto Eón ahora integra sabiduría antigua como metáforas computacionales:
- **Kabbalah**: Tzimtzum (poda), Gematria (embeddings), Sephiroth (arquitectura)
- **Alquimia**: Transmutación de datos crudos en conocimiento purificado
- **Hermetismo**: "Como Arriba, Así Abajo" (arquitectura fractal)
- **Ocultismo**: Egrégor (consciencia colectiva emergente)

---

## [1.7.2] - 2025-12-09

### Infraestructura Completa

- **Docker Compose Full-Stack**
  - 6 servicios containerizados: MQTT, WebSocket, Web, TinyLM, Collective, Core
  - Configuración Mosquitto incluida
  - Health checks para todos los servicios
  - Networks y volumes configurados
  - Perfiles para desarrollo (`dev`) y build (`build`)

- **Script de Demo**
  - Nuevo `start_demo.sh`: Lanza todo el stack con un comando
  - Soporta flags `--docker`, `--no-browser`
  - Verificación de dependencias automática
  - Cleanup graceful con Ctrl+C

- **Tests Unitarios**
  - 19 tests para WebSocket bridge
  - Tests de protocolo 1-bit
  - Tests de métricas de energía
  - Tests async de WebSocket

- **Especificación OpenAPI**
  - Nuevo `docs/api/protocol_1bit.yaml`
  - Documentación completa del protocolo 1-Bit
  - Esquemas JSON para todos los mensajes
  - Configuración LoRa incluida

- **Paper PDF**
  - Compilado `paper/main.pdf` (3 páginas, 147KB)
  - Añadido paquete booktabs para tablas
  - Tabla de métricas de energía incluida

### Nuevos Archivos

| Archivo | Descripción |
|---------|-------------|
| `docker-compose.yml` | Full-stack deployment |
| `start_demo.sh` | Script lanzador |
| `docker/mosquitto/config/mosquitto.conf` | Config MQTT |
| `docs/api/protocol_1bit.yaml` | OpenAPI spec |
| `phase2-core/Dockerfile` | C core builder |
| `phase6-collective/Dockerfile.bridge` | WebSocket container |
| `phase6-collective/tests/test_ws_bridge.py` | 19 unit tests |
| `web/Dockerfile` | Dashboard container |
| `paper/main.pdf` | Paper compilado |

### Docker Services

```
┌─────────────────────────────────────────────────────────┐
│                    docker compose up                     │
├─────────────────────────────────────────────────────────┤
│  mqtt (1883)    │ ws-bridge (8765) │ web (5000)         │
│  Mosquitto      │ Python WS        │ Flask Dashboard    │
├─────────────────┼──────────────────┼────────────────────┤
│  tinylm (5001)  │ collective-mind  │ core-builder       │
│  Language Model │ Distributed Sim  │ C library build    │
└─────────────────┴──────────────────┴────────────────────┘
```

---

## [1.7.1] - 2025-12-09

### Tests de Campo y Métricas de Energía

- **WebSocket Bridge**
  - Nuevo `ws_bridge.py`: Puente entre MQTT y Dashboard
  - Soporte para visualización en tiempo real
  - Modo simulación para desarrollo sin broker
  - Corregidas deprecation warnings de Python 3.12+

- **Test de Alcance LoRa**
  - Nuevo `LoRa_RangeTest.ino`: Test de campo completo
  - Métricas RSSI, SNR y tasa de pérdida
  - Estimación de rango basada en señal
  - Modo TX/RX configurable por Serial
  - Estadísticas detalladas de transmisión

- **Métricas de Energía ESP32**
  - Nuevo `EnergyMetrics.ino`: Medición de consumo
  - Comparativa 1-Bit vs JSON (2.6x ahorro energético)
  - Estimación de vida de batería
  - Lectura de voltaje de batería LiPo
  - Soporte para deep sleep

- **Documentación Hardware**
  - Nuevo `phase4-hardware/README.md` completo
  - Tablas de conexiones para TTGO/Heltec
  - Procedimiento de test de campo
  - Guía de librerías requeridas

### Métricas Medidas

| Métrica | 1-Bit | JSON | Mejora |
|---------|-------|------|--------|
| Tamaño | 21 bytes | 175 bytes | 8.3x |
| Tiempo de aire | ~51 ms | ~132 ms | 2.6x |
| Energía por TX | ~4.3 mJ | ~11.2 mJ | 2.6x |
| TX con 1000mAh | ~1.02M | ~0.39M | 2.6x |

### Nuevos Archivos

- `phase6-collective/ws_bridge.py` - WebSocket-MQTT bridge
- `phase4-hardware/esp32/examples/LoRa_RangeTest.ino` - Test de alcance
- `phase4-hardware/esp32/examples/EnergyMetrics.ino` - Métricas de energía
- `phase4-hardware/README.md` - Documentación completa de hardware

---

## [1.7.0] - 2025-12-09

### Mente Colectiva - Transmisión Real (NUEVO)

- **Cliente MQTT Real**
  - Nuevo `mqtt_client.py`: Cliente completo con paho-mqtt
  - Compatible con Mosquitto, HiveMQ, y cualquier broker MQTT
  - Paquetes binarios nativos del Protocolo 1-Bit
  - Heartbeat automático y reconexión
  - Callbacks para sync y descubrimiento de peers
  - CLI interactivo para pruebas

- **ESP32 + LoRa**
  - Nuevo `LoRa_1Bit_Demo.ino`: Demo completo para ESP32 con LoRa
  - Compatible con TTGO LoRa32, Heltec WiFi LoRa 32
  - Transmisión inalámbrica del protocolo 1-bit
  - Sincronización P2P sin servidor central
  - Ideal para IoT rural y redes mesh
  - Soporte para 433/868/915 MHz según región

- **Dashboard de Monitoreo**
  - Nuevo `dashboard.html`: Interfaz web completa
  - Visualización de topología de red en canvas
  - Lista de nodos con estado en tiempo real
  - Métricas del Protocolo 1-Bit (compresión, precisión, latencia)
  - Log de sincronización en vivo
  - Animaciones de transmisión entre nodos
  - Diseño responsive y moderno

### Formato del Paquete Binario

```
Byte 0-2:   Magic "EON" (3 bytes)
Byte 3:     Type (1=SYNC, 2=REQ, 3=ACK, 4=PING, 5=STATUS)
Byte 4-7:   Seed (uint32, big-endian)
Byte 8-9:   Count (uint16, big-endian)
Byte 10-13: Scale (float32, big-endian)
Byte 14+:   Bits empaquetados (ceil(N/8) bytes)
```

### Nuevos Archivos

- `phase6-collective/mqtt_client.py` - Cliente MQTT real con paho-mqtt
- `phase6-collective/dashboard.html` - Dashboard de monitoreo web
- `phase4-hardware/esp32/examples/LoRa_1Bit_Demo.ino` - Demo ESP32+LoRa

### Dependencias Opcionales

- `paho-mqtt`: Para conexión a brokers MQTT reales
- Arduino Libraries: LoRa by Sandeep Mistry, ArduinoJson

### Métricas de Transmisión

| Métrica | Valor |
|---------|-------|
| Compresión | 11.8x |
| Ahorro | 91.5% |
| Latencia típica | 10-30ms |
| MTU LoRa | 255 bytes |
| Nodos por sync | Ilimitado |

## [1.6.0] - 2025-12-09

### Plan de Alimentación - Crecimiento Dinámico (NUEVO)

- **Alimentación Continua del Core C**
  - Nuevo `continuous_demo.c`: series climáticas con picos y cambios bruscos
  - Loop de entrenamiento con guardado periódico de pesos (Wout)
  - Simulación de "vida" de sensor con aprendizaje continuo
  - Mejor MSE logrado: 0.267 en series erráticas

- **Optimizaciones del Motor C** (sin aumentar memoria)
  - Xorshift32 RNG: Mejor calidad de números aleatorios
  - tanh mejorado: Error reducido de 5% a 1% con polinomio grado 5
  - Ridge Regularization: λ = 0.001 para estabilidad numérica
  - Loop Unrolling: +30% velocidad en update

- **TinyLM - Vocabulario Técnico Expandido**
  - +40 términos de robótica: LIDAR, cinemática, PID, SLAM, gripper, ROS
  - +40 términos de programación: recursión, ORM, Docker, mutex, API REST
  - Nuevos datasets: 'robotica' y 'programacion'
  - Accuracy: 99.9-100% en todos los datasets

- **Memoria Factual con Timestamps**
  - Sistema para resolver ambigüedades temporales
  - Ejemplo: "El motor falló" → "El motor se recuperó" → "¿Estado del motor?" = última info
  - Historial de 10 actualizaciones por topic
  - Timestamps con "hace X segundos/minutos"

- **RAG Ligero**
  - Búsqueda automática en `/docs/` para responder preguntas
  - Keywords: protocolo, 1-bit, arquitectura, whitepaper, mqtt
  - Cache de 5 minutos para eficiencia
  - Extracción de contexto relevante (hasta 500 chars)

- **Protocolo 1-Bit - Implementación Completa**
  - `export_weights_1bit()`: Cuantización con 9-17x compresión
  - `import_weights_1bit()`: Reconstrucción y fusión de conocimiento
  - Demo completo de transmisión entre nodos
  - Documentación completa en `docs/PROTOCOL.md`

### Nuevos Archivos

- `phase2-core/libAeon/continuous_demo.c` - Demo de alimentación continua
- `docs/PROTOCOL.md` - Documentación del Protocolo 1-Bit

### Métodos Internos Añadidos

- `_store_factual_update()`: Almacena hechos con timestamp
- `_query_factual_state()`: Consulta estado más reciente
- `_load_docs_for_rag()`: Carga documentos para RAG
- `_search_docs()`: Búsqueda semántica en docs/
- `_handle_factual_message()`: Manejo de mensajes factuales
- `export_weights_1bit()`: Exportación cuantizada de pesos
- `import_weights_1bit()`: Importación y fusión de pesos

## [1.5.0] - 2025-12-08

### Chat Conversacional Avanzado (NUEVO)

- **Predicción de Secuencias Numéricas**: Detección automática de patrones (aritmético, geométrico, Fibonacci, potencias, cuadrático)
  - Ejemplo: "4, 8, 16, 32" → "El siguiente valor es: **64**"
  - Soporte para múltiples valores: "siguientes 3 números: 4, 8, 16, 32" → "**64, 128, 256**"
  
- **Memoria Personal**: Almacena y recuerda hechos sobre el usuario
  - "Mi color favorito es ultramarino" → "Guardaré que color favorito: ultramarino 🧠"
  - "¿Cuál es mi color favorito?" → "Tu color favorito es ultramarino"
  
- **Base de Conocimiento Técnico**: Definiciones de conceptos clave
  - Entropía, ESN, Spirit Hash, Reservorio, Aprendizaje Hebbiano, Mackey-Glass, Cuantización
  
- **Consulta de Sensores**: Simulación del sistema colectivo
  - "estado del SENSOR-3" → Datos simulados (temperatura, humedad, batería, estado)
  - Manejo de reportes de falla con generación de tickets
  
- **Afirmaciones Generales**: Confirmación de hechos del mundo
  - "El cielo es azul" → "Correcto. Mi base de conocimiento lo confirma ✓"
  
- **Autocompletado de Texto**: Completación contextual de frases
  - "La velocidad del viento..." → completación relevante

### Mejoras en Detección de Intenciones

- **20+ Categorías de Intención**: Expandido desde 17 categorías
- **Detección Automática de Secuencias**: 3+ números separados por comas se detectan automáticamente
- **Mejor Extracción de Números**: Ignora números en texto contextual ("siguientes 3 números")
- **Patrones de Múltiples Valores**: Soporte para "siguientes N números"

### Correcciones de Chat

- **Matemáticas Mejoradas**: "¿Cuánto es 34*5?" → "El resultado es **170** 🧮"
- **Historias Temáticas**: "Cuéntame una historia de aventura" genera historias apropiadas
- **Recomendaciones Contextuales**: "¿Qué helado me recomiendas?" → recomendaciones específicas
- **Eliminación de Falsos Positivos**: "cuéntame" ya no activa saludo
- **Orden de Patrones Optimizado**: Saludos al final para evitar conflictos

### Nuevos Métodos Internos

- `_predict_sequence()`: Predicción de patrones numéricos con soporte multi-valor
- `_store_personal_fact()`: Almacenamiento de hechos personales
- `_recall_personal_fact()`: Recuperación de memoria personal
- `_get_knowledge()`: Acceso a base de conocimiento técnico
- `_query_sensor()`: Simulación de consultas a sensores
- `_complete_text()`: Autocompletado contextual
- `_contains_sequence()`: Detección automática de secuencias

## [1.4.0] - 2024-12-08

### Sistema de Aprendizaje Continuo (NUEVO)

- **OnlineLearner**: Actualización en tiempo real de W_out usando Recursive Ridge Regression
- **LongTermMemory**: Almacenamiento persistente de usuarios, hechos y estadísticas
- **FeedbackSystem**: Mejora basada en retroalimentación 👍/👎 de usuarios
- **ConsolidationEngine**: Optimización durante inactividad ("sueño"), refuerza patrones exitosos

### Mejoras en Generación de Imágenes

- **5 Estilos de Arte**: fractal, flow, particles, waves, neural
- **12 Paletas de Colores**: desde cosmic hasta fire
- **Semillas Únicas**: Cada imagen es genuinamente diferente basada en timestamp + hash

### Sistema de Chat Mejorado

- **17 Categorías de Intención**: identidad, saludo, imagen, código, filosofía, memoria, etc.
- **Detección Mejorada**: Sin falsos positivos en nombres propios
- **Respuestas Contextuales**: Mayor coherencia que TinyLMv2 para este caso de uso

### Nuevos Endpoints API

- `POST /api/feedback` - Enviar feedback 👍/👎 sobre respuestas
- `GET /api/learning-stats` - Estadísticas de aprendizaje
- `GET|DELETE /api/memory` - Gestión de memoria a largo plazo
- `POST /api/consolidate` - Forzar consolidación manual

### Panel de Aprendizaje (Frontend)

- Visualización de eventos de aprendizaje
- Lista de usuarios conocidos
- Lista de hechos aprendidos
- Estadísticas de feedback
- Botones de consolidación y limpieza de memoria
- Botones 👍/👎 en cada mensaje de IA

### Persistencia

- `long_term_memory.json` - Usuarios, hechos, stats de aprendizaje
- `feedback.json` - Historial de valoraciones por patrón

### Benchmark Integral v2.0

- Nuevo archivo `benchmark_full.py` en raíz
- 8 módulos de prueba (ESN, cuantización, plasticidad, TinyLM, aprendizaje, memoria, imágenes, sistema)
- Modos `--quick` y `--export`
- Resultados verificados: 8-bit retiene 99.6% precisión

## [1.3.0] - 2024-12-08

### Sistema de Memoria y Estadísticas

- **Historial Persistente**: Conversaciones guardadas en `chat_history.json`
- **Estadísticas de Uso**: Tracking de mensajes, imágenes, archivos procesados
- **Aprendizaje desde Archivos**: Soporte para .txt, .md, .py, .js, .json, .csv
- **Configuración de Personalidad**: Estilos (formal, casual, creative, precise, balanced)

### Nuevos Endpoints API

- `GET /api/stats` - Estadísticas de uso completas
- `GET|DELETE /api/history` - Gestión del historial de chat
- `GET|POST /api/personality` - Configuración de personalidad
- `POST /api/learn-text` - Aprender de texto nuevo
- `POST /api/upload` - Subir archivos para aprendizaje

### Mejoras de Frontend

- Panel de Estadísticas de Uso (mensajes, imágenes, archivos, uptime)
- Panel de Personalidad (selector de estilo y verbosidad)
- Botón "Limpiar Historial"
- Subida de archivos funcional con aprendizaje real
- Actualización automática de estadísticas cada 30s

### Correcciones

- Mejorada integración frontend-backend
- Persistencia de estadísticas entre sesiones

## [1.2.0] - 2024-12-08

### Integración TinyLMv2 en Chat

- **Modelo de Lenguaje**: TinyLMv2 integrado para respuestas generativas
- **Entrenamiento Automático**: Se entrena al iniciar con textos filosóficos
- **Respuestas Híbridas**: Intenciones conocidas usan respuestas predefinidas, mensajes genéricos usan el LM
- **Nuevo Endpoint**: `/api/lm-status` para ver estado del modelo de lenguaje
- **Configuración Dinámica**: La temperatura y max_tokens afectan la generación

### Estadísticas del Modelo

- 256 neuronas en el reservorio
- 102 palabras en vocabulario
- 99.9% accuracy en entrenamiento
- Embeddings de 32 dimensiones

## [1.1.0] - 2024-12-08

### Interfaz Web Principal (web/)

- **Servidor Flask**: API REST completa en `web/server.py`
- **Chat Conversacional**: Sistema de respuestas basado en detección de intenciones
- **Generación de Arte Neuronal**: Endpoint `/api/generate-image` usando ESN
- **Configuración de IA**: Parámetros típicos (temperatura, top-p, max_tokens, etc.)
- **Estado del Sistema**: Endpoint `/api/status` con información del Momento Cero
- **Interfaz Moderna**: Chat, Dream (visualización), Estado & Config

### Correcciones

- Corregido `DATA_DIR` no definido en server.py
- Eliminado endpoint `/api/birth` (reemplazado por `/api/genesis` solo lectura)
- Eón siempre existe desde el Momento Cero (inmutable)
- Botones de imagen y subir archivo ahora funcionales

### Limpieza de Código

- Eliminado `phase3-integration/demos/aeon.js` (duplicado)
- Eliminado directorio `venv` duplicado (se conserva `.venv`)
- Actualizada referencia en `phase3-integration/demos/index.html`

## [1.0.0] - 2024-12-08

### Fase 1: Fundamentos

- Echo State Network en Python con NumPy
- Cuantización 8-bit, 4-bit, 1-bit
- Plasticidad Hebbiana, STDP, Anti-Hebbiana
- Módulo Genesis (Momento Cero)

### Fase 2: Núcleo C

- **Benchmarks de Energía**: Eón (0.0045 μJ) vs TinyML (0.0015 μJ) en Cortex-M4.
- **Documentación Completa**: Arquitectura, benchmarks, y guías de uso actualizadas.

### Fase 2: Núcleo C

- libAeon: 1.3KB de memoria
- Aritmética de punto fijo Q8.8
- Entrenamiento Gauss-Jordan
- Persistencia binaria

### Fase 3: Integración Web

- aeon.js: Núcleo JavaScript puro
- Demo interactivo en navegador
- Visualización en tiempo real

### Fase 4: Hardware

- Librería Arduino (Aeon.h)
- Extensión ESP32 con WiFi
- Ejemplos de predicción

### Fase 9: Empaquetado

- **Empaquetado**: NPM, PyPI, Arduino Library.

### Fase 10: Generación de Paper Académico

- **Generación de Paper Académico**: (LaTeX) para arXiv.

### Fase 5: Aplicaciones IoT

- Predictor de temperatura
- Detector de anomalías
- Dashboard (pendiente)

### Fase 6: Mente Colectiva

- **Intercambio 1-Bit**: Protocolo MQTT ultraligero para ESP32 (`phase6-collective/src`).
- Compresión 17x (Float32 -> 1-Bit) para transmisión de pesos.
- AeonNode: Nodo individual
- CollectiveMind: Coordinador
- Sincronización de pesos W_out

### Fase 7: TinyLM

- v1: Tokenización por caracteres
- v2: Tokenización por palabras (99.9% accuracy)
- **Trie Dictionary**: Vocabulario comprimido basado en LCRS arrays (`phase7-language/src/trie_vocab.py`).
- Servidor web Flask

### Fase 8: Paper Académico

- Template LaTeX completo
- Comparativas formales
- Listo para arXiv

---

(c) 2024 Sistemas Ursol - Jeremy Arias Solano
