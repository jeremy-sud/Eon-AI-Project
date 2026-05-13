# 🌌 Roadmap de Ideas - Proyecto Eón v2.0+

> Ideas de mejora basadas en la infraestructura existente del proyecto.
> 
> Última actualización: 2024-01-15

---

## 📊 Resumen de Priorización

| # | Idea | Dificultad | Impacto | Prioridad | Estado |
|---|------|------------|---------|-----------|--------|
| 16 | TinyAttention → TinyLMv2 | ✅ Completada | ALTA | ⭐⭐ |
| 17 | SeedArchaeologist → GeneticMiner | ✅ Completada | ALTA | ⭐⭐ |
| 24 | API REST Completa | ✅ Completada | ALTA | ⭐⭐ |
| 18 | NeuralWatermark → Collective Mind | ✅ Completada | MEDIA | ⭐⭐ |
| 21 | Dashboard Dinámico | 🔄 Pendiente | MEDIA | ⭐⭐ |
| 19 | Circadian Rhythms → ESN Training | 🔄 Pendiente | MEDIA | ⭐⭐ |
| 25 | Benchmarks Comparativos | 🔄 Pendiente | MEDIA | ⭐⭐ |
| 23 | Visualización 2D/3D | 🔄 Pendiente | MEDIA | ⭐⭐ |
| 20 | Hardware Integration | 🔄 Pendiente | BAJA | ⭐⭐⭐ |
| 28 | Protocolo 1-Bit: chipdecoder y compatibilidad | ✅ Completada | ALTA | ⭐⭐ |
| 29 | Regenerar benchmarks al completar roadmap | 🔄 Pendiente | ALTA | ⭐⭐ |
| 22 | Multi-Head Attention | 🔄 Pendiente | BAJA | ⭐⭐ |
| 26 | Optimización Memoria | 🔄 Pendiente | BAJA | ⭐⭐ |
| 27 | Persistencia Estado | 🔄 Pendiente | BAJA | ⭐⭐ |

---

## 🧠 Idea #1: Meta-Aprendizaje Cross-Seed (Seed Transfer Learning)

### Basado en
- `core/universal_miner.py` - UniversalMiner, SeedVault
- `phase6-collective/collective_mind.py` - AeonNode
- `core/alchemy.py` - AlchemicalPipeline

### Concepto
Las semillas exitosas comparten patrones estructurales. Un nuevo nodo podría "heredar" características de semillas exitosas previas, reduciendo dramáticamente el tiempo de excavación.

### Implementación Propuesta

```python
class MetaSeedLearner:
    """
    Aprende patrones de semillas exitosas para acelerar
    futuras excavaciones.
    """
    
    def __init__(self, seed_vault: SeedVault):
        self.vault = seed_vault
        self.meta_patterns = {}
        
    def analyze_successful_seeds(self) -> Dict:
        """Extrae patrones comunes de semillas exitosas."""
        eigenspectra = [s.eigenspectrum for s in self.vault.seeds]
        # Análisis de componentes principales
        # Clustering de patrones
        # Identificación de "regiones fértiles"
        
    def generate_guided_seed(self) -> int:
        """Genera semilla basada en patrones aprendidos."""
        # Usar meta_patterns para guiar la búsqueda
        # Reducción estimada: 10x en tiempo de excavación
```

### Archivos a Crear/Modificar
- `core/meta_seed.py` (nuevo)
- `core/universal_miner.py` (extender)
- `tests/test_meta_seed.py` (nuevo)

### Métricas de Éxito
- Reducción de tiempo de excavación: >5x
- Tasa de éxito en primeras 1000 semillas: >50%

---

## 🔮 Idea #2: Oráculo I-Ching Neural (Predicción de Hexagramas)

### Basado en
- `core/archaic_protocol.py` - Hexagram, Trigram, HEXAGRAMS
- `esn/esn.py` - EchoStateNetwork
- `phase7-language/tiny_lm_v2.py` - TinyLMv2

### Concepto
Usar el ESN para predecir secuencias de hexagramas del I-Ching. Los 64 estados = 6 bits, perfecto para representación binaria. Crear un "Oráculo Neural" que combina matemática y tradición milenaria.

### Implementación Propuesta

```python
class IChing Oracle:
    """
    Oráculo Neural basado en ESN y el I-Ching.
    
    El I-Ching tiene 64 hexagramas, cada uno con 6 líneas (bits).
    El ESN aprende patrones de cambio entre estados.
    """
    
    def __init__(self, reservoir_size: int = 64):
        self.esn = EchoStateNetwork(
            n_inputs=6,      # 6 líneas del hexagrama
            n_reservoir=reservoir_size,
            n_outputs=6,     # Siguiente hexagrama
        )
        self.protocol = ArchaicProtocol()
        
    def consult(self, question: str, current_state: Hexagram) -> Tuple[Hexagram, str]:
        """
        Consulta al oráculo con una pregunta.
        
        Returns:
            Tuple de (hexagrama_resultado, interpretación)
        """
        # Convertir hexagrama a input
        # Predecir siguiente estado
        # Interpretar transición
        
    def divine_sequence(self, n_steps: int = 3) -> List[Hexagram]:
        """Genera secuencia de hexagramas (lectura extendida)."""
```

### Archivos a Crear/Modificar
- `core/iching_oracle.py` (nuevo)
- `core/archaic_protocol.py` (extender con corpus de transiciones)
- `tests/test_iching_oracle.py` (nuevo)
- `web/server.py` (añadir endpoint /oracle)

### Métricas de Éxito
- Coherencia de secuencias: Transiciones válidas según I-Ching clásico
- Diversidad: No repetir hexagramas en secuencias cortas
- Interpretabilidad: Cada predicción tiene explicación basada en trigramas

---

## 🌀 Idea #3: Reservoir Morphing Dinámico

### Basado en
- `plasticity/tzimtzum.py` - TzimtzumESN, poda/regeneración
- `plasticity/hebbian.py` - HebbianESN
- `plasticity/hebbian_tzimtzum.py` - HebbianTzimtzumESN

### Concepto
El reservoir cambia de forma adaptándose al tipo de tarea. No solo poda/regenera conexiones - modifica la topología completa entre configuraciones óptimas.

### Implementación Propuesta

```python
class TopologyType(Enum):
    RING = "ring"           # Para secuencias cíclicas
    SMALL_WORLD = "small_world"  # Patrones complejos
    SCALE_FREE = "scale_free"    # Distribución power-law
    RANDOM = "random"       # Topología original ESN
    LATTICE = "lattice"     # Datos espaciales

class MorphingESN(HebbianTzimtzumESN):
    """
    ESN con topología dinámica que se adapta a la tarea.
    """
    
    def __init__(self, base_topology: TopologyType = TopologyType.RANDOM):
        super().__init__()
        self.current_topology = base_topology
        
    def morph_to(self, target: TopologyType, transition_steps: int = 100):
        """Transición suave entre topologías."""
        # Usar Tzimtzum para poda gradual
        # Regenerar con nueva topología
        # Mantener pesos W_out compatibles
        
    def auto_morph(self, task_metrics: Dict) -> TopologyType:
        """Detecta topología óptima basada en métricas."""
```

### Archivos a Crear/Modificar
- `plasticity/morphing.py` (nuevo)
- `plasticity/__init__.py` (añadir exports)
- `tests/test_morphing.py` (nuevo)

### Métricas de Éxito
- Mejora de MSE: >20% vs topología fija
- Tiempo de adaptación: <1000 pasos

---

## 📡 Idea #4: Protocolo de Sincronización Cuántica-Simulada

### Basado en
- `phase6-collective/collective_mind.py` - AeonNode, mezcla de pesos
- `egregore.py` - EgregorState
- `docs/PROTOCOL.md` - Protocolo 1-Bit

### Concepto
Simular "entanglement cuántico" para sincronización instantánea. Nodos con la misma semilla calculan estados idénticos sin comunicación explícita.

### Implementación Propuesta

```python
class QuantumSyncProtocol:
    """
    Sincronización "instantánea" usando semillas compartidas.
    
    Principio: Si dos nodos tienen la misma semilla y procesan
    la misma secuencia, sus estados internos son idénticos.
    """
    
    def __init__(self, shared_seed: int):
        self.seed = shared_seed
        self.epoch = 0
        
    def sync_state(self, timestamp: int) -> np.ndarray:
        """Calcula estado sincronizado para un timestamp."""
        # Usar timestamp como input determinista
        # El estado resultante es idéntico en todos los nodos
        
    def verify_sync(self, local_hash: str, remote_hash: str) -> bool:
        """Verifica sincronización por hash."""
```

### Archivos a Crear/Modificar
- `phase6-collective/quantum_sync.py` (nuevo)
- `phase6-collective/mqtt_client.py` (integrar)
- `tests/test_quantum_sync.py` (nuevo)

### Métricas de Éxito
- Latencia efectiva: 0ms (solo timestamp)
- Overhead de comunicación: <10 bytes/sync

---

## 🎨 Idea #5: Arte Generativo con Feedback de Egrégor

### Basado en
- `egregore.py` - EgregorState, EgregorMood
- `web/static/js/aeon.js` - Arte neural existente
- `web/server.py` - Endpoints de arte

### Concepto
El estado de ánimo del Egrégor (mente colectiva) influye en la generación de arte. Visualización en tiempo real del estado emocional del sistema.

### Implementación Propuesta

```python
MOOD_TO_STYLE = {
    EgregorMood.AGITATED: {
        'style': 'particles',
        'speed': 2.0,
        'palette': 'fire',
        'chaos': 0.9
    },
    EgregorMood.MEDITATIVE: {
        'style': 'waves',
        'speed': 0.3,
        'palette': 'ocean',
        'chaos': 0.1
    },
    EgregorMood.AWAKENING: {
        'style': 'fractal',
        'speed': 1.0,
        'palette': 'aurora',
        'chaos': 0.5
    },
    # ... más mappings
}

class EgregorArtist:
    """Genera arte basado en el estado del Egrégor."""
    
    def generate(self, egregore_state: EgregorState) -> Image:
        """Genera imagen según el mood colectivo."""
        style = MOOD_TO_STYLE[egregore_state.mood]
        # Aplicar intensidad y coherencia como modificadores
```

### Archivos a Crear/Modificar
- `web/egregore_art.py` (nuevo)
- `web/static/js/egregore_visualizer.js` (nuevo)
- `web/server.py` (endpoint /egregore/art)

### Métricas de Éxito
- Correlación visual con mood: Claramente distinguible
- Performance: <100ms por frame

---

## 💬 Idea #6: Chat Multi-Nodo (Conversación Distribuida)

### Basado en
- `phase7-language/tiny_lm_v2.py` - TinyLMv2
- `phase6-collective/collective_mind.py` - AeonNode, DataDomain
- `phase6-collective/mqtt_client.py` - Comunicación

### Concepto
Múltiples nodos colaboran para generar una respuesta. Cada nodo contribuye según su especialización (True Will / Thelema).

### Implementación Propuesta

```python
class CollaborativeChatOrchestrator:
    """
    Orquesta múltiples nodos para responder una pregunta.
    
    Pipeline:
    1. Nodo Analista: Detecta intención
    2. Nodo Generador: Crea respuesta base
    3. Nodo Validador: Verifica coherencia
    4. Egrégor: Ajusta tono según mood colectivo
    """
    
    def __init__(self, nodes: List[AeonNode], egregore: EgregorProcessor):
        self.analyst = self._find_specialist(DataDomain.CLASSIFICATION)
        self.generator = self._find_specialist(DataDomain.LANGUAGE)
        self.validator = self._find_specialist(DataDomain.GENERIC)
        self.egregore = egregore
        
    async def respond(self, user_message: str) -> str:
        """Genera respuesta colaborativa."""
        # 1. Analizar intención
        intent = await self.analyst.classify(user_message)
        
        # 2. Generar respuesta
        response = await self.generator.generate(user_message, intent)
        
        # 3. Validar
        is_valid, corrections = await self.validator.validate(response)
        
        # 4. Ajustar tono según Egrégor
        mood = self.egregore.current_state.mood
        final = self._adjust_tone(response, mood)
        
        return final
```

### Archivos a Crear/Modificar
- `phase6-collective/collaborative_chat.py` (nuevo)
- `phase7-language/server.py` (integrar)
- `tests/test_collaborative_chat.py` (nuevo)

### Métricas de Éxito
- Latencia: <2s para respuesta completa
- Coherencia: >90% según evaluación humana
- Diversidad: Respuestas varían según nodos disponibles

---

## 🔢 Idea #7: Cuantización Adaptativa por Contexto

### Basado en
- `quantization/quantizer.py` - QuantizedESN
- `utils/matrix_init.py` - check_numerical_stability()

### Concepto
Usar más bits donde importa, menos donde no. Cuantización variable según la importancia de cada conexión.

### Implementación Propuesta

```python
class AdaptiveQuantizer:
    """
    Cuantiza con precisión variable según importancia.
    
    - Conexiones críticas (alto gradiente): 8 bits
    - Conexiones frecuentes: 4 bits
    - Conexiones raras (bajo uso): 1-2 bits
    """
    
    def __init__(self, esn: EchoStateNetwork):
        self.esn = esn
        self.importance_map = None
        
    def compute_importance(self, X_val: np.ndarray) -> np.ndarray:
        """Calcula importancia de cada conexión."""
        # Método 1: Magnitud de pesos
        # Método 2: Frecuencia de activación
        # Método 3: Gradiente (si disponible)
        
    def quantize_adaptive(self) -> 'AdaptiveQuantizedESN':
        """Aplica cuantización adaptativa."""
        # Conexiones con importance > 0.8: 8 bits
        # Conexiones con importance 0.5-0.8: 4 bits
        # Conexiones con importance < 0.5: 2 bits
```

### Archivos a Crear/Modificar
- `quantization/adaptive_quantizer.py` (nuevo)
- `quantization/__init__.py` (añadir export)
- `tests/test_adaptive_quantizer.py` (nuevo)

### Métricas de Éxito
- Reducción de memoria: >50% vs 8-bit uniforme
- Retención de precisión: >95% vs original

---

## 🔄 Idea #8: Evolución de Reservorios (Genetic ESN)

### Basado en
- `core/universal_miner.py` - UniversalMiner, excavación
- `core/seed_vault.py` - SeedVault
- `utils/matrix_init.py` - create_reservoir_matrix()

### Concepto
Evolucionar poblaciones de ESNs usando algoritmos genéticos. Las semillas son el "genoma" - mutaciones = pequeños cambios de semilla.

### Implementación Propuesta

```python
class GeneticMiner:
    """
    Evolución de ESNs usando algoritmos genéticos.
    
    Genoma: La semilla (entero)
    Fitness: MSE en tarea específica
    Crossover: Mezcla de bits de semillas padre
    Mutación: ±1 en semilla (exploración local)
    """
    
    def __init__(self, population_size: int = 100, 
                 generations: int = 50):
        self.pop_size = population_size
        self.generations = generations
        
    def evolve(self, fitness_fn: Callable) -> ExcavationResult:
        """Evoluciona población hacia óptimo."""
        population = self._init_population()
        
        for gen in range(self.generations):
            # Evaluar fitness
            scores = [fitness_fn(seed) for seed in population]
            
            # Selección (tournament)
            parents = self._select(population, scores)
            
            # Crossover
            children = self._crossover(parents)
            
            # Mutación
            population = self._mutate(children)
            
        return self._best_result(population, scores)
```

### Archivos a Crear/Modificar
- `core/genetic_miner.py` (nuevo)
- `core/__init__.py` (añadir export)
- `tests/test_genetic_miner.py` (nuevo)

### Métricas de Éxito
- Convergencia: <50 generaciones
- Mejora sobre random: >30% en MSE

---

## 📊 Idea #9: Dashboard de Monitoreo en Tiempo Real

### Basado en
- `phase6-collective/dashboard.html` - Dashboard existente
- `egregore.py` - EgregorState
- `ws_bridge.py` - WebSocket bridge

### Concepto
Visualizar toda la red Eón en una interfaz unificada. Nodos, conexiones, Egrégor, métricas - todo en tiempo real.

### Implementación Propuesta

```javascript
// dashboard_v2.js
class EonDashboard {
    constructor(wsUrl) {
        this.ws = new WebSocket(wsUrl);
        this.nodes = new Map();
        this.egregore = null;
        
        // Visualización con D3.js
        this.networkGraph = new NetworkGraph('#network-container');
        this.egregorMeter = new EgregorMeter('#egregore-container');
        this.metricsPanel = new MetricsPanel('#metrics-container');
    }
    
    render() {
        // Grafo de nodos interactivo
        this.networkGraph.update(this.nodes);
        
        // Termómetro del Egrégor
        this.egregorMeter.update(this.egregore);
        
        // Panel de métricas
        this.metricsPanel.update({
            totalNodes: this.nodes.size,
            avgError: this.calculateAvgError(),
            syncRate: this.calculateSyncRate()
        });
    }
}
```

### Archivos a Crear/Modificar
- `web/static/js/dashboard_v2.js` (nuevo)
- `web/static/css/dashboard.css` (nuevo)
- `web/templates/dashboard_v2.html` (nuevo)
- `web/server.py` (endpoint /dashboard/v2)

### Métricas de Éxito
- Latencia de actualización: <100ms
- Escalabilidad: >100 nodos visualizados
- Usabilidad: Interfaz intuitiva sin manual

---

## 🔐 Idea #10: Firma Neuronal (Neural Watermarking)

### Basado en
- `esn/esn.py` - birth_hash, generate_birth_hash()
- `utils/matrix_init.py` - Utilidades de inicialización

### Concepto
Cada modelo entrenado tiene una firma indetectable codificada en los pesos. Permite verificar propiedad sin acceso al modelo original.

### Implementación Propuesta

```python
class NeuralWatermark:
    """
    Sistema de marca de agua para modelos Eón.
    
    La firma está codificada en los LSBs de W_out
    de forma que no afecta el rendimiento.
    """
    
    def __init__(self, owner_id: str):
        self.owner_id = owner_id
        self.signature = self._generate_signature()
        
    def embed(self, esn: EchoStateNetwork) -> EchoStateNetwork:
        """Inserta firma en el modelo."""
        # Codificar signature en LSBs de W_out
        # Verificable pero invisible
        
    def verify(self, esn: EchoStateNetwork) -> Tuple[bool, str]:
        """Verifica si el modelo tiene nuestra firma."""
        # Extraer LSBs
        # Comparar con signature conocida
        # Retornar (es_nuestro, owner_id)
```

### Archivos a Crear/Modificar
- `utils/watermark.py` (nuevo)
- `esn/esn.py` (método opcional embed_watermark)
- `tests/test_watermark.py` (nuevo)

### Métricas de Éxito
- Detección: 100% en modelos marcados
- Impacto en rendimiento: <0.1% MSE
- Robustez: Sobrevive cuantización 8-bit

---

## 🌙 Idea #11: Ciclos Circadianos para Consolidación

### Basado en
- `web/learning.py` - ConsolidationEngine
- `plasticity/tzimtzum.py` - dark_night(), renacimiento()

### Concepto
El sistema aprende mejor con ciclos día/noche. Consolidación activa durante "sueño" programado, similar al cerebro biológico.

### Implementación Propuesta

```python
class CircadianLearning:
    """
    Aprendizaje con ritmo circadiano.
    
    - Día: Aprendizaje activo, learning_rate alto
    - Noche: Consolidación, pruning, replay
    - Amanecer: Renacimiento, nuevas conexiones
    """
    
    def __init__(self, day_hours: int = 16, night_hours: int = 8):
        self.day_duration = day_hours * 3600
        self.night_duration = night_hours * 3600
        self.cycle_start = time.time()
        
    def get_phase(self) -> str:
        """Retorna fase actual: 'day', 'dusk', 'night', 'dawn'."""
        elapsed = time.time() - self.cycle_start
        # Calcular fase según tiempo transcurrido
        
    def get_learning_rate(self, base_lr: float) -> float:
        """Ajusta learning rate según fase."""
        phase = self.get_phase()
        if phase == 'day':
            return base_lr * 1.0
        elif phase == 'dusk':
            return base_lr * 0.5
        elif phase == 'night':
            return base_lr * 0.1  # Solo consolidación
        else:  # dawn
            return base_lr * 0.8
```

### Archivos a Crear/Modificar
- `web/circadian.py` (nuevo)
- `web/learning.py` (integrar CircadianLearning)
- `tests/test_circadian.py` (nuevo)

### Métricas de Éxito
- Retención a largo plazo: +20% vs aprendizaje continuo
- Estabilidad: Menos "olvido catastrófico"

---

## 🎯 Idea #12: Attention Ligero para TinyLM

### Basado en
- `phase7-language/tiny_lm_v2.py` - TinyLMv2
- `src/gematria.py` - GematriaEmbeddingLayer

### Concepto
Agregar un mecanismo de atención ultra-ligero compatible con TinyML. Solo 1 cabeza, dimensión 32 - ~2KB extra de memoria.

### Implementación Propuesta

```python
class TinyAttention:
    """
    Atención single-head ultra-ligera.
    
    Memoria: ~2KB (32x32 matrices Q, K, V)
    Compatible con MCUs de bajo costo.
    """
    
    def __init__(self, dim: int = 32):
        self.dim = dim
        # Matrices de proyección (32x32 cada una)
        self.W_q = np.random.randn(dim, dim) * 0.1
        self.W_k = np.random.randn(dim, dim) * 0.1
        self.W_v = np.random.randn(dim, dim) * 0.1
        
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Aplica atención sobre secuencia de embeddings."""
        Q = x @ self.W_q
        K = x @ self.W_k
        V = x @ self.W_v
        
        # Scaled dot-product attention
        scores = Q @ K.T / np.sqrt(self.dim)
        weights = self._softmax(scores)
        return weights @ V
```

### Archivos a Crear/Modificar
- `phase7-language/tiny_attention.py` (nuevo)
- `phase7-language/tiny_lm_v2.py` (integrar opcionalmente)
- `tests/test_tiny_attention.py` (nuevo)

### Métricas de Éxito
- Mejora en perplexity: >10%
- Overhead de memoria: <3KB
- Latencia: <5ms adicionales

---

## 🌊 Idea #13: Detección de Anomalías en Series Temporales

### Basado en
- `esn/esn.py` - predict()
- `utils/matrix_init.py` - check_numerical_stability()

### Concepto
Usar el error de predicción del ESN como detector de anomalías. Error alto = evento anómalo detectado. Simple, efectivo, y ya tenemos la infraestructura.

### Implementación Propuesta

```python
class AnomalyDetector:
    """
    Detector de anomalías basado en error de predicción ESN.
    
    Principio: El ESN aprende patrones "normales".
    Cuando encuentra algo anormal, su error aumenta.
    """
    
    def __init__(self, esn: EchoStateNetwork, threshold_sigma: float = 3.0):
        self.esn = esn
        self.threshold_sigma = threshold_sigma
        self.error_history = deque(maxlen=1000)
        self.mean_error = 0.0
        self.std_error = 1.0
        
    def fit_baseline(self, normal_data: np.ndarray):
        """Establece baseline de errores normales."""
        predictions = self.esn.predict(normal_data)
        errors = np.abs(normal_data[1:] - predictions[:-1])
        self.mean_error = np.mean(errors)
        self.std_error = np.std(errors)
        
    def detect(self, new_point: np.ndarray) -> Tuple[bool, float, str]:
        """
        Detecta si el punto es anómalo.
        
        Returns:
            (is_anomaly, anomaly_score, description)
        """
        pred = self.esn.predict(new_point.reshape(1, -1))
        error = np.abs(new_point - pred)
        
        z_score = (error - self.mean_error) / self.std_error
        is_anomaly = z_score > self.threshold_sigma
        
        return is_anomaly, float(z_score), self._describe(z_score)
```

### Archivos a Crear/Modificar
- `core/anomaly_detector.py` (nuevo)
- `core/__init__.py` (añadir export)
- `tests/test_anomaly_detector.py` (nuevo)
- `web/server.py` (endpoint /anomaly/detect)

### Métricas de Éxito
- Precision: >90% en anomalías sintéticas
- Recall: >85%
- Latencia: <10ms por punto

---

## 🔄 Idea #14: Streaming Infinito (Ventana Deslizante)

### Basado en
- `web/learning.py` - OnlineLearner
- `plasticity/hebbian.py` - adapt_online()
- `esn/esn.py` - leak_rate

### Concepto
Procesar streams infinitos sin agotar memoria. Olvido gradual del pasado lejano, foco en el presente. Perfecto para IoT y edge computing.

### Implementación Propuesta

```python
class StreamingESN:
    """
    ESN para streaming infinito con memoria acotada.
    
    Características:
    - Buffer circular de estados
    - Forgetting factor exponencial
    - Memoria fija (compatible con ESP32)
    """
    
    def __init__(self, esn: EchoStateNetwork, 
                 buffer_size: int = 100,
                 forgetting_factor: float = 0.99):
        self.esn = esn
        self.buffer = np.zeros((buffer_size, esn.n_reservoir))
        self.buffer_idx = 0
        self.forgetting = forgetting_factor
        self.samples_seen = 0
        
    def process(self, x: np.ndarray) -> np.ndarray:
        """Procesa un punto del stream."""
        # Actualizar estado
        self.esn._update_state(x)
        
        # Guardar en buffer circular
        self.buffer[self.buffer_idx] = self.esn.state
        self.buffer_idx = (self.buffer_idx + 1) % len(self.buffer)
        
        # Aplicar forgetting
        self.buffer *= self.forgetting
        
        self.samples_seen += 1
        return self.esn.predict(x.reshape(1, -1))
        
    def get_memory_usage(self) -> int:
        """Retorna bytes usados (constante)."""
        return self.buffer.nbytes + self.esn.state.nbytes
```

### Archivos a Crear/Modificar
- `esn/streaming.py` (nuevo)
- `esn/__init__.py` (añadir export)
- `tests/test_streaming.py` (nuevo)
- `phase4-hardware/esp32/` (versión C)

### Métricas de Éxito
- Memoria: Constante O(1) independiente de longitud del stream
- Latencia: <1ms por punto
- Precisión: >90% de ESN con memoria completa

---

## 🏛️ Idea #15: Arqueología de Semillas (Seed Archaeology)

### Basado en
- `core/universal_miner.py` - SeedVault, ExcavationResult
- `core/seed_vault.py` - Almacenamiento de semillas

### Concepto
Estudiar el "mapa" del espacio de semillas. ¿Hay regiones más fértiles? ¿Patrones en semillas exitosas? Generar "mapas del tesoro" para futuras excavaciones.

### Implementación Propuesta

```python
class SeedArchaeologist:
    """
    Estudia el paisaje del espacio de semillas.
    
    Objetivo: Encontrar patrones que indiquen
    regiones fértiles para excavación.
    """
    
    def __init__(self, vault: SeedVault):
        self.vault = vault
        
    def create_landscape_map(self, n_samples: int = 10000) -> np.ndarray:
        """Muestrea el espacio y crea mapa de fertilidad."""
        samples = []
        for seed in range(n_samples):
            resonance = self._quick_evaluate(seed)
            samples.append([seed, resonance])
        return np.array(samples)
        
    def visualize_2d(self, method: str = 'tsne') -> Figure:
        """Visualiza semillas exitosas en 2D."""
        eigenspectra = [s.eigenspectrum for s in self.vault.seeds]
        # Reducir dimensionalidad
        # Colorear por tipo de resonancia
        # Marcar "islas de fertilidad"
        
    def find_fertile_regions(self) -> List[Tuple[int, int]]:
        """Identifica rangos de semillas prometedores."""
        # Análisis de clustering
        # Retornar rangos [start, end] de alta fertilidad
```

### Archivos a Crear/Modificar
- `core/seed_archaeologist.py` (nuevo)
- `notebooks/seed_exploration.ipynb` (nuevo)
- `tests/test_seed_archaeologist.py` (nuevo)

### Métricas de Éxito
- Identificación de clusters: >5 regiones distintas
- Predicción de fertilidad: >70% accuracy
- Visualización: Mapas interpretables

---

## 🚀 Plan de Implementación

### Fase 1: Prioridad Alta (v2.0)
1. ✅ Crear este documento
2. 🔄 #13 Detección de Anomalías
3. 🔄 #9 Dashboard Mejorado
4. 🔄 #2 Oráculo I-Ching
5. 🔄 #6 Chat Multi-Nodo

### Fase 2: Prioridad Media (v2.1)
6. #7 Cuantización Adaptativa
7. #11 Ciclos Circadianos
8. #14 Streaming ESN
9. #1 Meta-Aprendizaje

### Fase 3: Exploración (v2.2+)
10. #3 Reservoir Morphing
11. #4 Sincronización Cuántica
12. #5 Arte con Egrégor
13. #8 Evolución Genética
14. #10 Firma Neuronal
15. #12 Attention Ligero

---

## 🚀 Mejoras e Integraciones Futuras (v2.3+)

### Integraciones a Medias Identificadas

| # | Integración | Estado | Prioridad | Complejidad |
|---|-------------|--------|-----------|-------------|
| 16 | TinyAttention → TinyLMv2 | 🔄 Parcial | ALTA | ⭐⭐ |
| 17 | SeedArchaeologist → GeneticMiner | 🔄 Pendiente | ALTA | ⭐⭐ |
| 18 | NeuralWatermark → Collective Mind | 🔄 Pendiente | MEDIA | ⭐⭐ |
| 19 | Circadian Rhythms → ESN Training | 🔄 Pendiente | MEDIA | ⭐⭐ |
| 20 | Hardware (Arduino/ESP32) → Python Core | 🔄 Pendiente | BAJA | ⭐⭐⭐ |
| 21 | Dashboard → Métricas en Tiempo Real | 🔄 Pendiente | MEDIA | ⭐⭐ |

### Mejoras en Componentes Existentes

| # | Mejora | Componente | Estado | Prioridad |
|---|--------|------------|--------|-----------|
| 22 | Multi-Head Attention | TinyAttention | 🔄 Pendiente | BAJA |
| 23 | Visualización 2D/3D | SeedArchaeologist | 🔄 Pendiente | MEDIA |
| 24 | API REST Completa | Todos los módulos | 🔄 Pendiente | ALTA |
| 25 | Benchmarks Comparativos | Sistema completo | 🔄 Pendiente | MEDIA |
| 26 | Optimización Memoria | TinyAttention | 🔄 Pendiente | BAJA |
| 27 | Persistencia Estado | CircadianClock | 🔄 Pendiente | BAJA |

---

### 🔄 Idea #16: Integración Completa TinyAttention → TinyLMv2

**Estado Actual**: TinyAttention existe como módulo separado con AttentionTinyLMv2 opcional.

**Problema**: TinyLMv2 base no usa atención. AttentionTinyLMv2 es una subclase separada.

**Solución Propuesta**:
- Integrar TinyAttention directamente en TinyLMv2 como opción configurable
- Modificar `forward()` para aplicar atención sobre secuencia antes del ESN
- Mantener compatibilidad backward

**Archivos**: `phase7-language/tiny_lm_v2.py`, `phase7-language/tiny_attention.py`

**Beneficios**: Mejor captura de dependencias largo alcance, mayor perplexity.

---

### 🔄 Idea #17: SeedArchaeologist → GeneticMiner Integration

**Estado Actual**: Ambos existen independientemente.

**Problema**: GeneticMiner busca semillas aleatoriamente sin usar mapas de fertilidad.

**Solución Propuesta**:
- Usar `find_fertile_regions()` para inicializar población genética
- Guiar mutaciones hacia regiones fértiles conocidas
- Logging de evolución con métricas arqueológicas

**Archivos**: `core/genetic_miner.py`, `core/seed_archaeologist.py`

**Beneficios**: Aceleración dramática de convergencia genética.

---

### ✅ Idea #18: NeuralWatermark → Collective Mind Authentication

**Estado Actual**: Completado; se integró watermarking automático en export/import de pesos en `phase6-collective/collective_mind.py`.

**Problema**: Riesgo de modelos falsificados o maliciosos en federated learning.

**Solución Propuesta**:
- Watermark automático en modelos antes de compartir
- Verificación de watermark en modelos recibidos
- Rechazo de modelos sin firma válida o de owner desconocido

**Archivos**: `phase6-collective/collective_mind.py`, `utils/watermark.py`, `phase1-foundations/python/utils/watermark.py`

**Beneficios**: Seguridad en aprendizaje federado, trazabilidad de modelos.

---

### 🔄 Idea #19: Circadian Rhythms → ESN Training Adaptation

**Estado Actual**: CircadianClock existe pero no afecta training.

**Problema**: ESN no se adapta a ciclos circadianos naturales.

**Solución Propuesta**:
- Modificar learning rate según fase circadiana
- Ajustar sparsity durante "sueño" vs "vigilia"
- Logging de performance por fase del día

**Archivos**: `core/circadian.py`, `esn/esn.py`

**Beneficios**: Mejor alineación con ritmos biológicos, performance más natural.

---

### 🔄 Idea #20: Hardware Integration Arduino/ESP32 → Python Core

**Estado Actual**: Código C++ existe pero no integrado.

**Problema**: Hardware no se comunica con sistema Python principal.

**Solución Propuesta**:
- MQTT bridge entre Arduino/ESP32 y Python
- TinyESN corriendo en microcontroladores
- Sincronización de modelos vía Collective Mind

**Archivos**: `phase4-hardware/arduino/`, `phase4-hardware/esp32/`, `phase6-collective/mqtt_client.py`

**Beneficios**: Edge computing distribuido, menor latencia.

---

### ✅ Idea #28: Estándar de chipdecoder / decoder 1-Bit para hardware y Python

**Estado Actual**: Completado; se creó módulo compartido `phase6-collective/protocol_1bit.py`, se unificó decodificación en Python, y se alineó hardware ESP32 con formato canónico.

**Problema**:
- `docs/PROTOCOL.md` y `phase6-collective/docs/protocol_spec.md` describen formatos distintos.
- `phase6-collective/mqtt_client.py` y `phase6-collective/ws_bridge.py` usan su propia versión del header y el empaquetado de bits.
- No existe un módulo único `chipdecoder` o clase de protocolo compartida para garantizar compatibilidad Python ↔ hardware.
- Falta validación CRC/checksum, verificación robusta de semilla y pruebas de roundtrip.

**Solución Propuesta**:
- Crear un módulo común de protocolo 1-bit: `phase6-collective/protocol_1bit.py`.
- Unificar endianness, bit order y campos de header en una única especificación canónica.
- Implementar funciones compartidas:
  - `encode_1bit_packet(weights, seed, scale, type)`
  - `decode_1bit_packet(data)`
  - `validate_packet(data)`
  - `merge_weights(local, external, ratio)`
- Extender hardware/ESP32/Arduino para usar el mismo formato y checksums.
- Añadir tests de compatibilidad byte-a-byte y de roundtrip en `phase6-collective/tests/`.

**Archivos**: `phase6-collective/protocol_1bit.py`, `phase6-collective/mqtt_client.py`, `phase6-collective/ws_bridge.py`, `phase4-hardware/esp32/`, `phase4-hardware/arduino/`, `phase6-collective/tests/test_ws_bridge.py`

**Beneficios**: Compatibilidad cruzada, menor deuda técnica, integración fiable con chips y redes IoT.

---

### 🔄 Idea #29: Regenerar benchmarks, actualizar papers y documentación al completar el roadmap

**Estado Actual**: El roadmap contiene muchas mejoras previstas, pero no hay un paso sistemático para volver a medir el impacto global, actualizar papers científicos y mejorar documentación tras su ejecución completa.

**Problema**:
- Las métricas actuales pueden quedar obsoletas después de que se implementen múltiples mejoras.
- Los papers científicos (whitepaper, paper.tex) contienen datos antiguos que no reflejan las mejoras implementadas.
- La documentación técnica puede tener inconsistencias o información desactualizada.
- No existe un ciclo formal de re-evaluación que cuantifique el valor real de cada fase del roadmap.
- Sin benchmarks actualizados y papers revisados, es difícil priorizar futuras iteraciones o validar las ganancias reales de Eón.

**Solución Propuesta**:
- Al completar el roadmap al 100%, regenerar todos los benchmarks del proyecto.
- Actualizar papers científicos con datos frescos y nuevas comparativas.
- Mejorar documentación técnica con información actualizada y correcciones.
- Incluir comparativas de:
  - cuantización 1-bit vs 4/8-bit
  - rendimiento de `phase7-language` y `phase6-collective`
  - consumo energético de hardware ESP32/LoRa
  - latencia y precisión de sincronización de modelos
  - impacto de watermarking en seguridad federada
  - mejoras en APIs REST y compatibilidad cross-platform
- Revisar y actualizar secciones en papers sobre arquitectura, benchmarks y casos de uso.
- Añadir un script o workflow automático para ejecutar benchmarks y publicar resultados en `docs/benchmarks.md`.
- Generar informe de métricas finales con análisis de impacto del roadmap completo.

**Archivos**: `docs/benchmarks.md`, `benchmark_full.py`, `phase6-collective/tests/`, `phase4-hardware/esp32/examples/`, `docs/ROADMAP_IDEAS.md`, `docs/WHITEPAPER.md`, `paper/paper.tex`, `paper/main.tex`, `docs/api/`, `README.md`

**Beneficios**: Validación objetiva del roadmap, papers científicos actualizados con evidencia fresca, documentación coherente, mayor credibilidad del proyecto y mejor posicionamiento académico.

---

### 🔄 Idea #21: Dashboard Dinámico con Métricas en Tiempo Real

**Estado Actual**: Dashboard HTML estático.

**Problema**: No muestra métricas de nuevos módulos (SeedArchaeologist, watermarking, etc.).

**Solución Propuesta**:
- WebSocket para updates en tiempo real
- Visualización de mapas de fertilidad
- Métricas de collective mind y circadian rhythms
- API REST backend en Flask/FastAPI

**Archivos**: `phase6-collective/dashboard.html`, `web/server.py`

**Beneficios**: Mejor monitoreo y debugging del sistema.

---

### 🔄 Idea #22: Multi-Head Attention en TinyAttention

**Estado Actual**: Solo single-head.

**Problema**: Limitada capacidad de modelado de diferentes tipos de dependencias.

**Solución Propuesta**:
- Extender a múltiples cabezas de atención
- Mantener ultra-ligero (< 100KB total)
- Configurable: 1-4 cabezas

**Archivos**: `phase7-language/tiny_attention.py`

**Beneficios**: Mejor performance en tareas complejas.

---

### 🔄 Idea #23: Visualización 2D/3D de Espacios de Semillas

**Estado Actual**: Solo análisis numérico.

**Problema**: Difícil interpretar mapas de fertilidad.

**Solución Propuesta**:
- Reducción dimensionalidad (t-SNE/UMAP)
- Plotly.js para visualización interactiva
- Clustering visual de regiones fértiles

**Archivos**: `core/seed_archaeologist.py`, `web/`

**Beneficios**: Mejor comprensión del landscape de semillas.

---

### ✅ Idea #24: API REST Completa para Todos los Módulos

**Estado Actual**: Completado; se agregaron endpoints REST para watermarking, genetic mining y seed archaeology en `web/server.py`.

**Problema**: No todos los módulos son accesibles vía HTTP.

**Solución Propuesta**:
- Endpoints para: watermarking, genetic mining, seed archaeology
- Documentación OpenAPI/Swagger
- Autenticación básica

**Archivos**: `web/server.py`, `phase6-collective/`, `phase1-foundations/python/utils/watermark.py`, `phase1-foundations/python/core/genetic_miner.py`, `phase1-foundations/python/core/seed_archaeologist.py`

**Beneficios**: Mejor integración con otros sistemas.

---

### 🔄 Idea #25: Benchmarks Comparativos Entre Versiones

**Estado Actual**: Benchmarks individuales.

**Problema**: Difícil comparar performance entre versiones.

**Solución Propuesta**:
- Suite de benchmarks automatizada
- Comparación TinyLMv1 vs v2 + attention
- Métricas: latency, accuracy, memory, perplexity

**Archivos**: `benchmark_full.py`, `docs/benchmarks.md`

**Beneficios**: Mejor tracking de progreso.

---

### 🔄 Idea #26: Optimización de Memoria en TinyAttention

**Estado Actual**: ~24KB para dim=32.

**Problema**: Podría ser más eficiente.

**Solución Propuesta**:
- Quantization de matrices de atención
- Sparse attention patterns
- Memory pooling para secuencias largas

**Archivos**: `phase7-language/tiny_attention.py`

**Beneficios**: Compatibilidad con más dispositivos edge.

---

### 🔄 Idea #27: Persistencia de Estado Circadian

**Estado Actual**: CircadianClock stateless.

**Problema**: Reinicia en cada ejecución.

**Solución Propuesta**:
- Guardar estado en archivo/Redis
- Restaurar fase actual al iniciar
- Logging histórico de fases

**Archivos**: `core/circadian.py`

**Beneficios**: Continuidad en reinicios del sistema.

---

## 🎯 Integraciones Completadas (2024-01-15)

### ✅ Integración #1: TinyAttention → TinyLMv2

**Estado**: ✅ Completada y Probada

**Descripción**:
Integración del mecanismo de atención single-head ultra-ligero `TinyAttention` (~24KB memoria) en el modelo de lenguaje `TinyLMv2`. Permite que el modelo seleccione contexto relevante durante generación de texto.

**Cambios Implementados**:
- Parámetro `use_attention` en constructor de `TinyLMv2` (default: `False`)
- Parámetro `attention_window` configurable (default: 128 tokens)
- Buffer de embeddings para cálculo eficiente de atención
- Integración transparente en método `generate()`
- Compatibilidad backward mantenida

**Archivos Modificados**:
- `phase7-language/tiny_lm_v2.py` - Integración principal
- `phase7-language/tiny_attention.py` - Sin cambios, usada como dependencia opcional

**Ejemplo de Uso**:
```python
from phase7_language.tiny_lm_v2 import TinyLMv2

# Con atención habilitada
lm = TinyLMv2(
    input_size=64,
    hidden_size=128,
    use_attention=True,
    attention_window=256
)

# Generar texto con mecanismo de atención activo
output = lm.generate(input_tokens, use_attention=True)
```

**Métricas de Éxito**:
- ✅ 523 tests pasando (incluyendo nuevos tests de atención)
- ✅ Overhead de memoria < 2%
- ✅ Compatibilidad backward 100%

---

### ✅ Integración #2: SeedArchaeologist → GeneticMiner

**Estado**: ✅ Completada y Probada

**Descripción**:
Integración del análisis topológico `SeedArchaeologist` en el algoritmo genético `GeneticMiner`. Permite inicializar la población genética de forma inteligente usando mapas de "fertilidad" en lugar de aleatoriedad pura. Acelera convergencia genética hacia regiones de alta resonancia.

**Cambios Implementados**:
- Parámetro `use_archaeologist` en constructor (default: `False`)
- Parámetro `fertile_bias` configurable (default: 0.5, rango: 0.0-1.0)
- Parámetro `archaeologist_samples` para análisis de paisaje (default: 1000)
- Método `_init_population_with_archaeologist()` para inicialización inteligente
- Método `_init_population_random()` para compatibilidad
- Método `archaeologist_stats()` para monitoreo y debugging
- Actualización de `evolve()` para aceptar parámetro `vault` opcional

**Archivos Modificados**:
- `phase1-foundations/python/core/genetic_miner.py` - Integración principal
- `phase1-foundations/python/tests/test_genetic_miner.py` - 4 nuevos tests de integración

**Ejemplo de Uso**:
```python
from core.genetic_miner import GeneticMiner
from core.universal_miner import SeedVault, UniversalMiner

# Crear vault y miner básico
vault = SeedVault()
miner = UniversalMiner(reservoir_size=50)

# Función de fitness
def fitness(seed):
    result = miner.excavate(starting_seed=seed, max_attempts=1)
    return result.resonance

# Evolución básica (aleatoria)
basic_genetic = GeneticMiner(population_size=50, generations=30)
result1 = basic_genetic.evolve(fitness)

# Evolución inteligente (con archaeologist)
smart_genetic = GeneticMiner(
    population_size=50,
    generations=30,
    use_archaeologist=True,
    fertile_bias=0.8,
    archaeologist_samples=1000,
    random_state=42
)
result2 = smart_genetic.evolve(fitness, vault)

# Obtener estadísticas del archaeologist
stats = smart_genetic.archaeologist_stats()
print(f"Regiones fértiles encontradas: {stats['fertile_regions_found']}")
```

**Métricas de Éxito**:
- ✅ 41 tests pasando en test_genetic_miner.py
- ✅ Aceleración convergencia: ~1.5-2x más rápido
- ✅ Compatibilidad backward 100%
- ✅ Integración sin dependencias circulares

**Impacto Esperado**:
- Reducción de tiempo de búsqueda genética
- Mejora en calidad de semillas encontradas
- Mejor exploración de espacios de semillas
- Compatible con otros componentes de Eón

---

*Documento actualizado: 2024-01-15*
*Próxima revisión: Después de implementar NeuralWatermark → Collective Mind*
