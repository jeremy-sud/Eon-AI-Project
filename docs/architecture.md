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
| Flask Server | \`web/server.py\` | ~2000 |
| Learning System | \`web/learning.py\` | ~400 |
| Frontend | \`web/static/js/app.js\` | ~600 |
| ESN Core | \`phase1-foundations/python/esn/esn.py\` | ~300 |
| TinyLMv2 | \`phase7-language/tiny_lm_v2.py\` | ~250 |

---

*Updated: 2025-12-08 (v1.5.0)*
