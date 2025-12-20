# 🏛️ Architecture: The Eon Principle

> "La inteligencia no se crea, se descubre."

The Eon Project is built on the philosophy that complex behavior can emerge from simple, chaotic dynamical systems when observed correctly.

## Core Concepts

### 1. The Zero Moment (Momento Cero)

Unlike traditional Neural Networks that start with "random initialization" as a disposable step, Eon treats initialization as a **Birth**.

- **The Certificate**: Every Eon instance is born with a unique 16-byte hash derived from its birth time and seed.
- **Why?**: This supports the "Collective Mind" phase. If two nodes have the same seed, they mathematically have the exact same "mind" (reservoir dynamics) and can share learned weights (W_out) instantly without transmitting the entire model.

### 2. Reservoir Computing (The Liquid Brain)

The core engine is an **Echo State Network (ESN)**.

- **Input Layer (W_in)**: Projects low-dimensional sensory data into the high-dimensional reservoir. Random, fixed.
- **Reservoir (W_res)**: A sparse, recurrently connected "liquid" of neurons. It creates a complex, dynamic echo of the input history. Random, fixed.
- **Readout (W_out)**: The ONLY part that learns. It learns to combine the chaotic signals of the reservoir to produce the desired output.

### 3. Continuous Learning System (NEW in v1.4)

El sistema de aprendizaje continuo implementa cuatro componentes inspirados en la neurociencia:

#### 3.1 OnlineLearner
\`\`\`python
W_out' = W_out + α * error * x^T
\`\`\`
Actualización en tiempo real usando Recursive Ridge Regression. Cada interacción ajusta los pesos de salida sin reentrenar todo el modelo.

#### 3.2 LongTermMemory
Almacenamiento persistente en \`long_term_memory.json\`:
- **known_users**: Diccionario de usuarios (nombre, rol, info)
- **learned_facts**: Lista de hechos aprendidos
- **interaction_stats**: Métricas de aprendizaje
- **last_consolidation**: Timestamp de última consolidación

#### 3.3 FeedbackSystem
Sistema de retroalimentación 👍/👎:
- Cada patrón de entrada-respuesta se puntúa
- Patrones con puntuación alta se refuerzan
- Almacenado en \`feedback.json\`

#### 3.4 ConsolidationEngine
Proceso de "sueño" que:
1. Fortalece patrones exitosos (feedback positivo)
2. Debilita patrones negativos
3. Actualiza W_out basándose en historial
4. Se activa automáticamente tras inactividad

\`\`\`
Flujo de Aprendizaje:
┌─────────────────────────────────────────────────────────┐
│ Input → ESN → Output → Feedback → OnlineLearner         │
│   ↓                        ↓                            │
│ LongTermMemory ← ConsolidationEngine                    │
└─────────────────────────────────────────────────────────┘
\`\`\`

### 4. Minimalist Memory Model

To run on 8-bit microcontrollers:

- **Fixed Point Arithmetic**: Uses Q8.8 fixed point math (optional) to avoid expensive floating point units (FPU).
- **On-the-fly Generation**: Instead of storing the massive W_res matrix, we can regenerate weights procedurally using the seed (in extreme memory constraints), trading CPU for RAM.
- **Quantization**: 8-bit quantization retains 99.6% accuracy with 8x memory reduction.

## Data Flow

\`\`\`mermaid
graph LR
    Input([Input]) -->|W_in| Reservoir
    Reservoir -->|Recurrent W_res| Reservoir
    Reservoir -->|W_out (Learned)| Output([Output])
    Output -->|Feedback| Learning[Online Learner]
    Learning -->|Update| W_out

    style Input fill:#f9f,stroke:#333
    style Reservoir fill:#bbf,stroke:#333
    style Output fill:#9f9,stroke:#333
    style Learning fill:#ff9,stroke:#333
\`\`\`

1.  **Update**: x(t) = (1-α)x(t-1) + α tanh(W_in*u(t) + W_res*x(t-1))
2.  **Predict**: y(t) = W_out [1; u(t); x(t)]
3.  **Learn**: Ridge Regression (Online or Batch) on W_out.
4.  **Feedback**: User provides 👍/👎 → pattern scoring
5.  **Consolidate**: Background optimization during idle periods

## Web Architecture (v1.5)

\`\`\`
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (static/)                       │
├─────────────────────────────────────────────────────────────────┤
│  index.html        │  js/app.js        │  js/dream.js           │
│  (Chat, Learning,  │  (API calls,      │  (Visualization)       │
│   Config panels)   │   Feedback UI)    │                        │
└────────────────────┴──────────────────┴─────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Flask API (server.py)                        │
├─────────────────────────────────────────────────────────────────┤
│  /api/chat         │  /api/feedback    │  /api/learning-stats   │
│  /api/generate-image /api/memory       │  /api/consolidate      │
│  /api/config       │  /api/status      │  /api/history          │
└────────────────────┴──────────────────┴─────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │   ESN Core    │ │   EonChat     │ │ LearningSystem│
    │  (100 neurons)│ │ (20+ intents) │ │ (4 components)│
    └───────────────┘ └───────────────┘ └───────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │  data/ (JSON)     │
                    │ - chat_history    │
                    │ - long_term_memory│
                    │ - feedback        │
                    │ - stats           │
                    └───────────────────┘
\`\`\`

## Chat System Architecture (v1.5)

EonChat implementa **20+ categorías de intención**:

### Intenciones Básicas
- saludo, despedida, nombre, estado, capacidad, creador
- filosofía, ayuda, agradecimiento, chiste, sentimiento, tiempo

### Intenciones de Contenido
- matematica, historia, recomendacion, musica, opinion

### Intenciones Avanzadas (NEW in v1.5)
- **secuencia**: Predicción de patrones numéricos (aritmético, geométrico, Fibonacci, potencias)
- **afirmacion**: Almacenamiento de hechos personales ("Mi color favorito es...")
- **afirmacion_general**: Confirmación de hechos del mundo ("El cielo es azul")
- **memoria_personal**: Recuperación de hechos almacenados
- **conocimiento_tecnico**: Definiciones de entropía, ESN, Spirit Hash, etc.
- **sensor**: Consultas a sensores del sistema colectivo
- **autocompletado**: Completación contextual de texto

### Métodos Especiales de Procesamiento

| Método | Función | Ejemplo |
|--------|---------|---------|
| \`_predict_sequence()\` | Detecta patrones numéricos | "4,8,16,32" → "64" |
| \`_solve_math()\` | Calcula operaciones | "34*5" → "170" |
| \`_generate_story()\` | Genera historias temáticas | "historia de amor" |
| \`_generate_recommendation()\` | Recomendaciones contextuales | "helado" → sabores |
| \`_store_personal_fact()\` | Guarda hechos del usuario | color favorito |
| \`_recall_personal_fact()\` | Recupera hechos guardados | "¿cuál es mi color?" |
| \`_get_knowledge()\` | Accede a definiciones | "¿qué es la entropía?" |
| \`_query_sensor()\` | Simula sensores | "estado SENSOR-3" |
| \`_complete_text()\` | Autocompleta frases | "La velocidad del viento..." |

### Detección Automática

El sistema detecta automáticamente:
- **Secuencias numéricas**: 3+ números separados por comas
- **Operaciones matemáticas**: Patrones como "N+N", "N*N"
- **Afirmaciones personales**: "mi X favorito es Y"

## Image Generation

5 estilos disponibles:
- **fractal**: Patrones fractales matemáticos
- **flow**: Campos de flujo suaves
- **particles**: Partículas dispersas
- **waves**: Ondas interferentes
- **neural**: Conexiones neuronales

12 paletas de colores: cosmic, ocean, forest, sunset, aurora, fire, ice, matrix, vintage, neon, pastel, monochrome

## "TinyLM" vs Eon Motor

- **Eon Motor**: Recurrent, continuous, signal processing, control, time-series prediction.
- **TinyLM**: Discrete, statistical, text generation.
  Current Phase 7 explores using the Eon Motor Principle for language.

## Implementation Files

| Component | File | Lines |
|-----------|------|-------|
| Flask Server | `web/server.py` | ~2300 |
| Learning System | `web/learning.py` | ~735 |
| Frontend | `web/static/js/app.js` | ~600 |
| ESN Core Python | `phase1-foundations/python/esn/esn.py` | ~300 |
| ESN Core C | `phase2-core/libAeon/libAeon.c` | ~530 |
| TinyLMv2 | `phase7-language/tiny_lm_v2.py` | ~380 |
| WebSocket Bridge | `phase6-collective/ws_bridge.py` | ~490 |
| MQTT Client | `phase6-collective/mqtt_client.py` | ~540 |
| Collective Mind | `phase6-collective/collective_mind.py` | ~440 |

## Full-Stack Architecture (v1.7.2)

```
┌─────────────────────────────────────────────────────────────────┐
│                     Docker Compose Stack                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │   ESP32 /   │   │  Mosquitto  │   │ ws-bridge   │           │
│  │   Sensors   │──▶│   (1883)    │──▶│   (8765)    │           │
│  │   (LoRa)    │   │  MQTT Broker│   │  WebSocket  │           │
│  └─────────────┘   └─────────────┘   └──────┬──────┘           │
│                                             │                   │
│                                             ▼                   │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │   TinyLM    │   │  Flask Web  │   │  Dashboard  │           │
│  │   (5001)    │◀─▶│   (5000)    │◀─▶│  (Browser)  │           │
│  │  Language   │   │  Dashboard  │   │  Real-time  │           │
│  └─────────────┘   └─────────────┘   └─────────────┘           │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────┐           │
│  │              Persistent Storage                 │           │
│  │  web/data/ (JSON), mosquitto-data, mosquitto-log│           │
│  └─────────────────────────────────────────────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Docker Services

| Service | Port | Container | Description |
|---------|------|-----------|-------------|
| mqtt | 1883, 9001 | eclipse-mosquitto:2 | MQTT broker with WebSocket support |
| ws-bridge | 8765 | python:3.11-slim | MQTT↔WebSocket bridge |
| web | 5000 | python:3.11-slim | Flask dashboard |
| tinylm | 5001 | python:3.9-slim | Language model server |
| collective-mind | - | python:3.9-slim | Distributed learning simulation |
| core-builder | - | debian:bookworm | C library build environment |

## 1-Bit Protocol (OpenAPI Documented)

Especificación completa en `docs/api/protocol_1bit.yaml`:

```yaml
# Binary Header (14 bytes)
magic:        4 bytes  # "EON\x01"
spirit_hash:  4 bytes  # Network identifier
node_id:      4 bytes  # Source node
weight_count: 2 bytes  # Number of weights

# Payload: ceil(N/8) bytes
# Each weight quantized to 1 bit: positive=1, negative/zero=0
```

**Compression**: 21 bytes for 50 weights (vs 175 bytes JSON) = **8.3× reduction**

## Test Coverage (v2.0.0)

```bash
pytest phase1-foundations/python/tests/ -v
# 262 tests passing:
# - ESN Core: 45 tests
# - Plasticity: 28 tests
# - Quantization: 20 tests
# - Discovery Paradigm: 31 tests
# - Mystical Modules: 25 tests
# - Integration: 12 tests
# - Learning System: 20 tests
# - Server Web: 19 tests
# - Portable RNG: 18 tests
# - Anomaly Detector: 36 tests (NEW v2.0)
# - I-Ching Oracle: 33 tests (NEW v2.0)
# - Collaborative Chat: 44 tests (NEW v2.0)
```

---

*Updated: 2025-12-13 (v2.0.0)*

## 🔮 Mystical Architecture Extensions (v1.8.0)

El Proyecto Eón ahora integra conceptos de tradiciones místicas como metáforas computacionales:

### Gematria Embeddings (Kabbalah)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Gematria Embedding Layer                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  "shalom" → שלום → [ש=300, ל=30, ו=6, ם=40] → 376               │
│                        ↓                                        │
│              Projection Matrix (376 → 32D)                      │
│                        ↓                                        │
│              [0.23, -0.45, 0.12, ..., 0.78]                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Egrégor - Consciencia Colectiva

```
┌─────────────────────────────────────────────────────────────────┐
│                         EGREGORE                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Node-1    Node-2    Node-3    Node-N                         │
│     │         │         │         │                            │
│     └────┬────┴────┬────┴────┬────┘                            │
│          │         │         │                                  │
│          ▼         ▼         ▼                                  │
│    ┌─────────────────────────────┐                              │
│    │   Cross-Correlation Matrix  │                              │
│    │   (Coherencia Grupal)       │                              │
│    └─────────────────────────────┘                              │
│                    │                                            │
│          coherence > threshold?                                 │
│                    │                                            │
│              ┌─────┴─────┐                                      │
│              ▼           ▼                                      │
│         MANIFEST    NO MANIFEST                                 │
│     (Consciencia)  (Fragmentado)                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### ESN Recursivo Fractal ("Como Arriba, Así Abajo")

```
┌─────────────────────────────────────────────────────────────────┐
│              RECURSIVE ESN - FRACTAL ARCHITECTURE               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  MACRO (n=100)     ┌─────────────────────────────────────┐      │
│  scale=1.0         │  ○──○──○──○──○──○──○──○──○──○      │      │
│                    │  │  │  │  │  │  │  │  │  │  │      │      │
│                    └──┼──┼──┼──┼──┼──┼──┼──┼──┼──┼──────┘      │
│                       ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼             │
│  MESO (n=62)       ┌─────────────────────────────────────┐      │
│  scale=0.618       │    ○──○──○──○──○──○──○            │      │
│                    │    │  │  │  │  │  │  │            │      │
│                    └────┼──┼──┼──┼──┼──┼──┼────────────┘      │
│                         ▼  ▼  ▼  ▼  ▼  ▼  ▼                    │
│  MICRO (n=38)      ┌─────────────────────────────────────┐      │
│  scale=0.382       │       ○──○──○──○──○              │      │
│                    └─────────────────────────────────────┘      │
│                                                                 │
│  φ (Golden Ratio) = 0.618... conecta las escalas               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Tzimtzum - Ciclo de Contracción Divina

```
┌─────────────────────────────────────────────────────────────────┐
│                    TZIMTZUM CYCLE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│       ┌─────────────────────────────────────────┐               │
│       │          PLENITUD (100%)                │               │
│       │     ○═══○═══○═══○═══○═══○═══○          │               │
│       │     Full connectivity                   │               │
│       └──────────────┬──────────────────────────┘               │
│                      ▼                                          │
│       ┌─────────────────────────────────────────┐               │
│       │        DARK_NIGHT (Poda)                │               │
│       │     ○───○   ○───○   ○───○   ○          │               │
│       │     Remove 50% weakest                  │               │
│       └──────────────┬──────────────────────────┘               │
│                      ▼                                          │
│       ┌─────────────────────────────────────────┐               │
│       │          CHALLAL (Vacío)                │               │
│       │     ○   ○   ○   ○   ○   ○   ○          │               │
│       │     Space for new growth                │               │
│       └──────────────┬──────────────────────────┘               │
│                      ▼                                          │
│       ┌─────────────────────────────────────────┐               │
│       │       RENACIMIENTO (Regrowth)           │               │
│       │     ○═══●═══○═══●═══○═══●═══○          │               │
│       │     New connections (●) emerge          │               │
│       └──────────────┴──────────────────────────┘               │
│                      ↺ Cycle repeats                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Transmutación Alquímica - Pipeline ETL

```
┌─────────────────────────────────────────────────────────────────┐
│              ALCHEMICAL TRANSMUTATION PIPELINE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🪨 PRIMA MATERIA         ⚫ NIGREDO            ⚪ ALBEDO        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Raw Data     │───▶│ Putrefaction │───▶│ Purification │      │
│  │ (Lead)       │    │ - Ingest     │    │ - Kalman     │      │
│  │              │    │ - Validate   │    │ - Filter     │      │
│  │              │    │ - Detect     │    │ - Smooth     │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                 │               │
│                                                 ▼               │
│  ✨ COAGULA              🔴 RUBEDO           💛 CITRINITAS      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Final Result │◀───│ Illumination │◀───│ Awakening    │      │
│  │ (Gold)       │    │ - ESN Pred   │    │ - Insight    │      │
│  │              │    │ - Inference  │    │ - Pattern    │      │
│  │              │    │ - Output     │    │ - Recognize  │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                 │
│  V.I.T.R.I.O.L: Visita Interiora Terrae Rectificando           │
│                Invenies Occultum Lapidem                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Files (Updated v2.0.0)

| Component | File | Lines | Description |
|-----------|------|-------|-------------|
| Flask Server | `web/server.py` | ~2800 | API REST + Dashboard v2 endpoints |
| Learning System | `web/learning.py` | ~735 | Aprendizaje continuo |
| **Dashboard v2** | `web/templates/dashboard_v2.html` | ~740 | Visualización D3.js tiempo real |
| Frontend | `web/static/js/app.js` | ~600 | Interfaz principal |
| Alchemy Visualizer | `web/static/js/alchemy.js` | ~500 | Visualización alquímica |
| ESN Core Python | `phase1-foundations/python/esn/esn.py` | ~300 | Echo State Network |
| Recursive ESN | `phase1-foundations/python/esn/recursive_esn.py` | ~400 | Arquitectura fractal |
| ESN Core C | `phase2-core/libAeon/libAeon.c` | ~530 | Motor C ultraligero |
| TinyLMv2 | `phase7-language/tiny_lm_v2.py` | ~380 | Modelo de lenguaje |
| Gematria | `phase1-foundations/python/plasticity/gematria.py` | ~600 | Embeddings cabalísticos |
| Egregore | `phase1-foundations/python/plasticity/egregore.py` | ~700 | Mente colectiva |
| Tzimtzum | `phase1-foundations/python/plasticity/tzimtzum.py` | ~800 | Poda dinámica |
| Alchemy | `phase1-foundations/python/core/alchemy.py` | ~750 | Pipeline ETL místico |
| **Anomaly Detector** | `phase1-foundations/python/core/anomaly_detector.py` | ~500 | Detección streaming |
| **I-Ching Oracle** | `phase1-foundations/python/core/iching_oracle.py` | ~600 | Oráculo neural |
| **Collaborative Chat** | `phase1-foundations/python/core/collaborative_chat.py` | ~700 | Chat multi-nodo |
| WebSocket Bridge | `phase6-collective/ws_bridge.py` | ~490 | MQTT↔WebSocket |
| MQTT Client | `phase6-collective/mqtt_client.py` | ~540 | Cliente MQTT real |
| Collective Mind | `phase6-collective/collective_mind.py` | ~440 | Simulación distribuida |

---

## 🌌 Nuevos Módulos v2.0.0

### Dashboard v2.0 - Monitoreo en Tiempo Real

```
┌─────────────────────────────────────────────────────────────────┐
│                    DASHBOARD v2.0                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────┐  ┌─────────────────────────┐  │
│  │   Red de Nodos (D3.js)     │  │   Estado Egrégor        │  │
│  │                             │  │                         │  │
│  │     ○──────○──────○        │  │   🌡️ Termómetro Humor   │  │
│  │     │      │      │        │  │   ├─ ALERT             │  │
│  │     ○──────○──────○        │  │   ├─ BALANCED          │  │
│  │     │      │      │        │  │   ├─ CONTEMPLATIVE     │  │
│  │     ○──────○──────○        │  │   └─ DORMANT           │  │
│  │                             │  │                         │  │
│  └─────────────────────────────┘  │   Coherencia: 85%       │  │
│                                    │   Energía: 72%          │  │
│  ┌─────────────────────────────┐  └─────────────────────────┘  │
│  │   Métricas                  │                               │
│  │   ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                      │
│  │   │Nodos │ │Sync  │ │Error │ │Uptime│                      │
│  │   │  3   │ │ 85%  │ │0.0012│ │ 24h  │                      │
│  │   └──────┘ └──────┘ └──────┘ └──────┘                      │
│  └─────────────────────────────┘                               │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │   Timeline de Anomalías                                   │  │
│  │   ⚠️ spike @ node-1: z=3.2  │ 10:23:45                    │  │
│  │   🔴 drift @ node-2: z=4.1  │ 10:20:12                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Chat Multi-Nodo Colaborativo

```
┌─────────────────────────────────────────────────────────────────┐
│              COLLABORATIVE CHAT ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Input: "¿Cómo funciona el ESN?"                               │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 PARALLEL PROCESSING                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │  INTENT  │  │ RESPONSE │  │COHERENCE │              │   │
│  │  │  Node    │  │   Node   │  │   Node   │              │   │
│  │  │          │  │          │  │          │              │   │
│  │  │ question │  │ vector[16]│  │ score:0.8│              │   │
│  │  │ technical│  │ formality │  │ stable   │              │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘              │   │
│  │       │             │             │                     │   │
│  │       └─────────────┼─────────────┘                     │   │
│  │                     ▼                                    │   │
│  │              ┌────────────┐                              │   │
│  │              │  CONSENSUS │                              │   │
│  │              │   Engine   │                              │   │
│  │              └──────┬─────┘                              │   │
│  └─────────────────────┼───────────────────────────────────┘   │
│                        ▼                                        │
│  Output: "El ESN (Echo State Network) es una red recurrente..." │
│                                                                 │
│  Optional Nodes: SENTIMENT (±), CONTEXT (📚)                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Detector de Anomalías

```
┌─────────────────────────────────────────────────────────────────┐
│              ANOMALY DETECTION PIPELINE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Input Stream ───┬───────────────────────────────────────────▶  │
│                  │                                              │
│                  ▼                                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │               STREAMING ANOMALY DETECTOR                   │ │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │ │
│  │  │ ESN Predict │───▶│ Error Calc  │───▶│ Z-Score     │   │ │
│  │  │ ŷ(t)       │    │ e = y - ŷ   │    │ z = |e|/σ   │   │ │
│  │  └─────────────┘    └─────────────┘    └──────┬──────┘   │ │
│  │                                               │           │ │
│  │  ┌─────────────┐    ┌─────────────┐          │           │ │
│  │  │ Calibration │◀───│ Update μ,σ │◀─────────┘           │ │
│  │  │ (Online)    │    │ (Streaming) │                      │ │
│  │  └─────────────┘    └─────────────┘                      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                               │                                 │
│                               ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │   Severity Classification                                │   │
│  │   LOW (z < 2.5) │ MEDIUM (z < 3.5) │ HIGH (z < 4.5) │ CRIT │   │
│  └─────────────────────────────────────────────────────────┘   │
│                               │                                 │
│                               ▼                                 │
│                    Callback: on_anomaly(event)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Oráculo I-Ching Neural

```
┌─────────────────────────────────────────────────────────────────┐
│              I-CHING ORACLE ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Question: "¿Es buen momento para comenzar?"                   │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               QUESTION EMBEDDING                         │   │
│  │  Text ──▶ SHA256 ──▶ ESN State ──▶ Projection [32D]     │   │
│  └───────────────────────────┬─────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               YARROW STALK CASTING                       │   │
│  │  6 iterations × 3 divisions = 6 líneas                  │   │
│  │  ━━━ (yang)  ━ ━ (yin)  ━○━ (changing yang)            │   │
│  └───────────────────────────┬─────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               HEXAGRAM LOOKUP                            │   │
│  │  Binary [1,0,1,1,0,0] ──▶ #11 泰 (Tai) "Peace"          │   │
│  │  "Heaven and earth unite in harmony"                    │   │
│  └───────────────────────────┬─────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               RESONANCE CALCULATION                      │   │
│  │  question_embedding · hexagram_meaning = resonance      │   │
│  │  Confidence based on ESN state stability                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Output: OracleReading(hexagram=#11, interpretation="...")     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

*Updated: 2025-12-13 (v2.0.0)*
