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

To run deterministically on resource-constrained microcontrollers (Cortex-M0+/M3/M4, ESP32, AVR):

- **Fixed-Point Arithmetic (Q8.8 & Q15)**: Operates using integer shift registers (`>> 8`) without requiring hardware Floating-Point Units (FPU).
- **Procedural Synchronization (LCG Seed Re-generation)**: Generates identical high-dimensional reservoir topologies across edge swarms sharing a 32-bit linear congruential seed, eliminating matrix transmission overhead.
- **Multi-Level Quantization**:
  - 8-bit quantization (`int8`): 99.6% predictive retention with $8\times$ memory compression.
  - 1-bit sign quantization (`int1`): $64\times$ memory compression and $8.3\times$ LoRa packet reduction for distributed edge swarms.

### 5. Algoritmos Matemáticos y Optimizaciones de Silicio (v2.1)

#### 5.1 Factorización Exacta de Cholesky ($A = L L^T$) para Ridge Regression
La optimización del readout $W_{out}$ bajo regularización $L_2$ (Tikhonov) resuelve el sistema:
$$(X^T X + \lambda I_M) W_{out}^T = X^T Y$$
Dado que $\lambda > 0$, la matriz de covarianza regularizada $A = X^T X + \lambda I_M$ es **estrictamente simétrica y definida positiva (SPD)**:
$$\forall z \ne \mathbf{0}, \quad z^T A z = \|X z\|_2^2 + \lambda \|z\|_2^2 > 0$$
Eón factoriza $A = L L^T$ mediante el algoritmo de Cholesky-Banachiewicz e invoca la subrutina `DPOSV` de LAPACK / SciPy, reduciendo el costo operacional de $M^3$ a $\frac{1}{3} M^3$ operaciones de punto flotante ($2.98\times$ speedup en Cortex-M4 @ 64MHz) con cero necesidad de pivoteo parcial ni inestabilidades de punto fijo.

#### 5.2 Adaptación en Tiempo Real por Regla Delta Normalizada (NLMS $O(M)$)
Para aprendizaje ininterrumpido en microcontroladores sin capacidad para almacenar covarianzas de $M \times M$ palabras:
$$e(t) = y(t) - W_{out}(t-1) \tilde{x}(t)$$
$$W_{out}(t) = W_{out}(t-1) + \eta \frac{e(t) \tilde{x}(t)^T}{\|\tilde{x}(t)\|_2^2 + \epsilon}$$
Esta regla requiere complejidad temporal y espacial estrictamente $O(M)$, evitando la explosión cuadrática $O(M^2)$ de algoritmos RLS convencionales.

#### 5.3 Reservorios Ortogonales vía Transformada de Cayley
Para eliminar modos amortiguados espurios en el reservorio y maximizar la memoria a corto plazo en el régimen crítico ($\rho \approx 1$):
$$W = \rho (I - A)(I + A)^{-1}, \quad \text{con } A = -A^T$$
Garantiza que todos los autovalores residan sobre la circunferencia de radio $\rho$ ($|\lambda_i| = \rho$), impidiendo la atenuación prematura de secuencias temporales.

#### 5.4 Filtro de Criticalidad Espectral de Dos Etapas
1. **Cota de Gerschgorin ($O(N^2)$)**: Evalúa $\|W\|_\infty = \max_i \sum_j |w_{ij}|$. Si es $< 1$, la Echo State Property queda demostrada sin requerir espectro completo.
2. **Rayleigh Power Iteration ($O(k N^2)$)**: Si excede 1, itera $v^{(k+1)} = \frac{W v^{(k)}}{\|W v^{(k)}\|}$ hasta 15 pasos para aproximar $\lambda_{max}$ con un costo $10\times$ menor que la descomposición densa $O(N^3)$.

#### 5.5 Plasticidad No Supervisada de Oja ($\|w_i\|_2 \to 1$)
$$\Delta w_{ij}(t) = \eta_H x_i(t) \left( x_j(t) - x_i(t) w_{ij}(t) \right)$$
El término de decaimiento cuadrático autorregulado garantiza la convergencia asintótica del vector sináptico al primer componente principal, impidiendo desbordamientos en registros de punto fijo.

#### 5.6 Raíz Digital Cerrada $O(1)$ para Embeddings Numéricos
$$dr(n) = 1 + ((n - 1) \pmod 9)$$
Sustituye bucles iterativos de cadenas de texto por aritmética modular en un solo ciclo de reloj.

## Data Flow

\`\`\`mermaid
graph LR
    Input([Input]) -->|W_in| Reservoir
    Reservoir -->|Recurrent W_res (Orthogonal/Sparse)| Reservoir
    Reservoir -->|W_out (Cholesky / NLMS)| Output([Output])
    Output -->|Feedback / Target| Learning[Online NLMS Learner]
    Learning -->|O(M) Update| W_out

    style Input fill:#f9f,stroke:#333
    style Reservoir fill:#bbf,stroke:#333
    style Output fill:#9f9,stroke:#333
    style Learning fill:#ff9,stroke:#333
\`\`\`

1.  **Update**: $x(t) = (1-\alpha)x(t-1) + \alpha \tanh(W_{in} u(t) + W_{res} x(t-1))$
2.  **Predict**: $y(t) = W_{out} [1; u(t); x(t)]$
3.  **Learn**: Ridge Regression analítico exacto por Cholesky ($LL^T$) en batch, o regla delta normalizada NLMS ($O(M)$) en streaming.
4.  **Feedback**: Puntuación de patrones y refuerzo de pesos.
5.  **Consolidate**: Optimización en segundo plano durante periodos de inactividad.

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

## Test Coverage (v2.4.0)

```bash
pytest -v
# 720 tests passing:
# - ESN Core & Foundations: 533 tests (Core ESN, Plasticidad, Cuantización, Anomaly Detector, RNG, I-Ching Oracle, etc.)
# - Mente Colectiva (Collective Mind): 63 tests (Conexiones distribuidas, Quantum Sync, Marca de agua neural)
# - Modelo de Lenguaje (TinyLMv2 & Attention): 54 tests
# - Web & Dashboard: 70 tests
```

## 11. Control Numérico y Estabilidad Dinámica (v2.5)

El subsistema de control numérico asegura la estabilidad matemática incondicional en despliegues embebidos y edge continuos (meses de operación ininterrumpida sin reseteo de software):

### 11.1 Guardián de Estabilidad (`StabilityGuard`)
- **Monitoreo de Lyapunov:** Estimación periódica del exponente local de Lyapunov ($\lambda_{\max} < 0$) para prevenir bifurcaciones hacia regímenes caóticos inestables durante el aprendizaje continuo.
- **Contracción espectral automática:** Si $\rho(W) > \rho_{\max}$ tras plasticidad o poda, reescala instantáneamente $W \leftarrow \left(\frac{\rho_{\text{target}}}{\rho(W)}\right) W$.
- **Protección contra saturación:** Amortiguamiento suave si la tasa de neuronas saturadas ($|x_i| \ge 0.995$) excede el 80%.

### 11.2 Factorización U-D Bierman-Thornton (`UDFactorizedRLS`)
- **Problema en edge:** El algoritmo RLS clásico acumula errores de truncamiento en aritmética de 32 bits, perdiendo la condición semidefinida positiva de la matriz de covarianza $P$ y divergiendo con `NaN`.
- **Solución Eón:** Representación $P = U D U^T$ donde $U$ es triangular superior unitaria y $D$ es diagonal estrictamente positiva ($D_j > 0$). Actualiza directamente los factores sin inversión matricial ($O(N^2)$ por muestra), garantizando estabilidad numérica infinita y adaptación en tiempo real con factor de olvido $\beta$.

### 11.3 Reservoirs Ortogonales de Cayley
- Matriz ortogonal estricta $W_{\text{orth}} = (I - A)(I + A)^{-1}$ derivada de matrices antisimétricas $A = -A^T$.
- Escalado exacto $W = \rho \cdot W_{\text{orth}}$: todos los eigenvalores tienen $|\lambda_i| = \rho$, asegurando un decaimiento homogéneo sin modos resonantes descontrolados.

### 11.4 Sintonización Analítica de Capacidad de Memoria (`MemoryTuner`)
- Medición experimental del límite teórico de Jaeger: $MC = \sum_{k=1}^{k_{\max}} r^2(u(t-k), y_k(t)) \le N$.
- Selección óptima de $\alpha_{\text{opt}} \approx 1 - \exp(-\Delta t / \tau_{\text{corr}})$ a partir de la autocorrelación $R_{uu}(\tau)$ de la señal del sensor.

---

*Updated: 2026-10-29 (v2.5.0-dev)*

---

## Appendix: Philosophical Architecture Extensions (v1.8.0)

Estas extensiones usan conceptos de tradiciones filosóficas como **metáforas computacionales** para técnicas estándar de machine learning. Son módulos opcionales que no afectan el core del sistema:

### Numeric Embeddings (Gematria-inspired)

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

### Cross-Node Coherence (Egrégor pattern)

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

### Multi-Scale Recursive ESN (Fractal Architecture)

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

### Dynamic Pruning Cycle (Prune/Regrow)

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

### Multi-Stage ETL Pipeline

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
