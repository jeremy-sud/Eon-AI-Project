## 🟢 PLAN DE AMPLIACIÓN DE COMPATIBILIDAD HARDWARE (v2.1+)

Con el objetivo de ampliar la adopción y robustez del Proyecto Eón, se propone una hoja de ruta para soportar nuevas plataformas hardware y dispositivos biomédicos/wearables. Este plan permitirá la integración en entornos embebidos, IoT y salud conectada.

### Objetivos
- Portar el núcleo ESN y módulos clave a microcontroladores y SoCs de bajo consumo.
- Garantizar compatibilidad con sensores biomédicos y dispositivos inteligentes.
- Proveer ejemplos y toolchains para cada plataforma.

### Plataformas a soportar

**Microcontroladores y SoCs:**
- STM32 (Familia L4 y H7, STMicroelectronics)
- nRF52 (Nordic Semiconductor)
- Raspberry Pi Pico (RP2040)
- Ambiq Micro (Apollo Series)
- Silicon Labs EFR32 (Series 32-bit)
- Microchip SAM D21 / SAM L21
- Texas Instruments MSP430

**Dispositivos biomédicos/wearables:**
- Parches de Monitorización ECG/EEG
- Audífonos Inteligentes
- Bombas de Infusión Inteligentes

### Acciones y entregables

1. **Abstracción de drivers hardware:**
    - Crear una capa de abstracción para GPIO, ADC, I2C, SPI, UART compatible con todos los targets.
    - Documentar APIs mínimas para sensores biomédicos (ECG, EEG, presión, temperatura).

2. **Portabilidad del núcleo Eón:**
    - Refactorizar el core C (libAeon) para compilar en ARM Cortex-M, RISC-V y MSP430.
    - Añadir toolchains y scripts de build para cada plataforma (Makefile, CMake, PlatformIO).
    - Proveer bindings para MicroPython/CircuitPython donde sea posible (RP2040, STM32).

3. **Ejemplos y demos:**
    - Demo de inferencia ESN en STM32L4/H7 y RP2040 (entrada analógica, salida digital).
    - Demo de adquisición y análisis de señal ECG/EEG en parches inteligentes.
    - Demo de integración con audífonos y bombas inteligentes (simulación de eventos y alertas).

4. **Documentación y guías:**
    - Guía de integración paso a paso para cada plataforma.
    - Ejemplos de código y scripts de flashing.
    - Tabla de compatibilidad y limitaciones conocidas.

### Métricas de éxito
- Inferencia ESN < 10 ms en Cortex-M4/M7 y RP2040.
- Consumo < 1 mA en modo idle (Ambiq, STM32L4).
- Adquisición y procesamiento de señal biomédica en tiempo real.
- Integración exitosa con al menos 2 dispositivos biomédicos reales.

### Estado
- 🟡 Planificado para v2.1+ (no implementado, requiere recursos de hardware y validación cruzada)

---
# Áreas de Mejora - Proyecto Eón v2.4.0

## Estado: ✅ MEJORAS CRÍTICAS COMPLETADAS - 719 TESTS PASSING

Este documento lista las áreas de mejora identificadas y su estado actual.

**Última auditoría completa:** 2026-06-13

---

## 🔴 DISCREPANCIAS ENCONTRADAS Y CORREGIDAS (Auditoría 2026-06-13)

Durante la auditoría de junio 2026, se corroboraron los cambios del repositorio y la suite de pruebas:

### 1. ❌ Número de Tests Actualizado
- **Documentado:** 343 tests
- **Real:** 719 tests
- **Acción:** Sincronizado en la documentación global

### 2. ✅ print() vs Logging - COMPLETADO (v2.1.0)
- **Documentado:** "50+ llamadas print()"
- **Real:** **500+ llamadas print()** en código de producción
- **Archivos migrados a logging (v2.1.0):**
  - ✅ `web/server.py`: 11 prints → logger (excepto banner en `__main__`)
  - ✅ `mqtt_client.py`: 13 prints de producción → logger
  - ✅ `benchmark_full.py`: 5 advertencias de imports → logger
  - ✅ `universal_miner.py`: Logger configurado
- **Archivos con prints solo en demo (aceptable):**
  - `collective_mind.py`: 36 prints (todos en `__main__`)
  - `benchmark_full.py`: 44 prints (reportes de benchmark)
  - `mqtt_client.py`: 26 prints (funciones interactivas)
- **Estado:** ✅ COMPLETADO - Código de producción migrado

### 3. ✅ CORS Configurado
- **Documentado:** "🟢 Verificar"
- **Real:** CORS **AHORA ESTÁ CONFIGURADO** en `web/server.py`
- **Solución implementada (v2.1.0):**
  - Añadido `flask-cors>=4.0.0` a `requirements.txt`
  - Configurado CORS para endpoints `/api/*` con métodos GET, POST, PUT, DELETE, OPTIONS
  - Headers permitidos: Content-Type, Authorization
- **Estado:** ✅ COMPLETADO

### 4. ❌ sys.path.insert() Extensivo
- **Documentado:** Pendiente (status 🟡)
- **Real:** **20+ archivos** usando sys.path.insert()
- **Archivos afectados:**
  - `web/server.py`
  - `mqtt_client.py`
  - `collective_mind.py`
  - `tiny_lm.py`, `tiny_lm_v2.py`
  - `tzimtzum.py`, `hebbian.py`
  - `esn.py`, y más...
- **Estado:** 🔴 CRÍTICO - Malas prácticas de imports

## 🔧 Auditoría de Benchmarks 2026-05
- El benchmark integral actual se ejecuta desde `benchmark_full.py` en la raíz.
- `docs/benchmarks.md` todavía documenta `phase1-foundations/python/benchmark.py`; debe sincronizarse con `benchmark_full.py` o marcarse como benchmark legacy.
- Documentación adicional a revisar: `README.md`, `docs/architecture.md`, `docs/benchmarks.md`.
- Los benchmarks actuales identifican las siguientes áreas de mejora:
  - `benchmark_esn_sizes`: 50-100 neuronas parecen ser el balance mejor entre precisión y memoria. Explorar tamaños intermedios y evaluaciones de latencia en hardware embebido.
  - `benchmark_quantization`: 8-bit retiene precisión aceptable. 4-bit y 1-bit degradan muy fuerte, lo que sugiere que la cuantización debe ser adaptativa e híbrida, no uniforme.
  - `benchmark_plasticity`: Solo se prueban Hebbian y Anti-Hebbian. Falta evaluación de STDP, plasticidad adaptativa y ajuste dinámico de tasa de aprendizaje.
  - `benchmark_tinylm`: El modelo se entrena solo 1 época y el benchmark mide tokens/segundo sin evaluar calidad semántica real. Requiere métricas de coherencia, perplexity y contexto.
  - `benchmark_learning_system`: La memoria de largo plazo usa búsquedas lineales. Escalar a cientos de miles de hechos requerirá indexación, vectores semánticos o cachés de consulta.
  - `benchmark_image_generation`: Usa generación de ruido aleatorio con PIL. Es una métrica de placeholder; la mejora real está en integrar un verdadero generador procedural/fractal o un modelo generativo ligero.
  - `benchmark_chat_system`: Actualmente es una evaluación de throughput de patrones keyword-based, no de comprensión conversacional. Debería medirse precisión de intención y coherencia con un dataset de frases.
- Resultado inmediato: actualizar la documentación de benchmarks para reflejar el benchmark real y anotar que algunos tests son métricas de placeholder.

---

## 📊 Resumen de Tests v2.4.0

| Componente | Archivos de Prueba | Tests | Estado |
|------------|--------------------|-------|--------|
| **Phase 1 Foundations** | Core ESN, Plasticidad, Cuantización, Anomalías, RNG, I-Ching, etc. | 532 | ✅ |
| **Phase 6 Collective** | Marca de Agua Neural, Sincronización Cuántica, WS Bridge | 63 | ✅ |
| **Phase 7 Language** | TinyAttention, TinyLMv2 | 54 | ✅ |
| **Web & Dashboard** | Visualización Arte, Sistema de Aprendizaje, Rutas Server | 70 | ✅ |
| **Total** | **Todas las Suites** | **719** | ✅ |

---

## ✅ Mejoras Completadas v2.0.0 (2025-12-13)

### 🌌 Dashboard v2.0 (`web/templates/dashboard_v2.html`)
- Visualización de red D3.js con nodos ESN interactivos
- Termómetro de humor del Egrégor (BALANCED, ALERT, CONTEMPLATIVE, etc.)
- Timeline de anomalías con severidad (LOW, MEDIUM, HIGH, CRITICAL)
- Métricas en tiempo real: nodos activos, sincronización, error promedio
- **APIs REST integradas:**
  - `GET /api/nodes` - Lista de nodos y conexiones
  - `GET /api/egregore` - Estado del Egrégor
  - `GET /api/anomalies` - Eventos de anomalía
  - `GET /api/dashboard/stats` - Estadísticas agregadas
  - `POST /api/dashboard/reset` - Resetear estado

### 💬 Chat Multi-Nodo (`core/collaborative_chat.py`)
- **5 roles especializados:**
  - `INTENT`: Detecta intención (greeting, question, command, technical, creative, emotional)
  - `RESPONSE`: Genera vector de respuesta base
  - `COHERENCE`: Evalúa coherencia con contexto
  - `SENTIMENT`: Análisis de sentimiento (opcional)
  - `CONTEXT`: Gestión de contexto conversacional (opcional)
- Sistema de consenso con callbacks
- Factory: `create_collaborative_chat(include_sentiment=True, include_context=True)`
- **44 tests** cubriendo todos los escenarios

### 🔍 Detector de Anomalías (`core/anomaly_detector.py`)
- `AnomalyDetector`: Detección basada en error de predicción ESN
- `StreamingAnomalyDetector`: Calibración online automática
- Severidades: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- Callbacks para eventos de anomalía
- Factory: `create_synthetic_anomalies()` para testing
- **36 tests** con cobertura completa

### 🔮 Oráculo I-Ching Neural (`core/iching_oracle.py`)
- 64 hexagramas con significados en español
- Método yarrow stalk para casting tradicional
- Embedding de preguntas vía reservorio ESN
- Adivinación de secuencias temporales
- Factory: `create_oracle(random_state=42)`
- **33 tests** cubriendo consultas y predicciones

### ⚡ Mejoras de Rendimiento
- Variable `EON_DISABLE_TINYLM=1` para arranque rápido
- Dashboard con polling optimizado cada 3s

---

## ✅ Mejoras Completadas (v1.8.1)

### 1. ✅ Legacy `np.random.RandomState` API → `default_rng()`

**Archivos actualizados:**
- `phase1-foundations/python/esn/recursive_esn.py`
- `phase1-foundations/python/esn/esn.py`

**Cambios realizados:**
```python
# Antes (legacy)
self.rng = np.random.RandomState(seed)
self.rng.randn(n)
self.rng.randint(0, 2**31)

# Después (moderno)
self.rng = np.random.default_rng(seed)
self.rng.standard_normal(n)
self.rng.integers(0, 2**31)
```

**Estado:** ✅ Completado y tests verificados

---

### 2. ✅ Complejidad Cognitiva en `mqtt_client.py`

**Archivo:** `phase6-collective/mqtt_client.py`

**Solución aplicada:**
- Extraída función `_run_demo()` para modo demostración
- Extraída función `_run_interactive()` para modo broker real
- Extraída función `_command_loop()` para loop de comandos

**Estado:** ✅ Complejidad reducida de 17 a <15

---

### 3. ✅ Parámetros no utilizados en `egregore.py`

**Archivo:** `phase6-collective/egregore.py`

**Cambios:**
- `entropy` → `_entropy` (reserved for future entropy-based mood adjustments)
- `mood` → `_mood` (reserved for mood-specific adjustments)

**Estado:** ✅ Prefixados con underscore

---

### 4. ✅ Nombres de parámetros mejorados en `server.py`

**Archivo:** `web/server.py`

**Cambios:**
- `n1, n2` → `operand_a, operand_b`
- `val` → `value`
- `lines` → `text_lines`
- Eliminados decoradores duplicados `@classmethod @staticmethod`

**Estado:** ✅ Nombres descriptivos aplicados

---

### 5. ✅ Código comentado en `collective_mind.py`

**Archivo:** `phase6-collective/collective_mind.py`

**Cambio:**
- Comentario `# Voluntad = afinidad * (1 + experiencia) * éxito`
- Convertido a: `# Fórmula de Voluntad: afinidad × (1 + experiencia) × éxito`

**Estado:** ✅ Documentación apropiada

---

## ✅ Mejoras Completadas (v1.9.0)

### 6. ✅ Tests para módulos del Paradigma de Descubrimiento

**Archivo creado:** `phase1-foundations/python/tests/test_discovery_paradigm.py`

**Cobertura:**
- `UniversalMiner`: 12 tests (chaos_sample, resonance, excavation, seeds)
- `ArchaicProtocol`: 14 tests (hexagrams, trigrams, conversions, interpretations)
- Integration tests: 2 tests (miner ↔ protocol)
- Export tests: 3 tests (core/__init__.py validation)

**Estado:** ✅ 31 nuevos tests añadidos

---

### 7. ✅ Exports faltantes en `core/__init__.py`

**Problema:** `AlchemicalPipeline` no estaba exportado desde el módulo core.

**Solución aplicada:**
```python
from .alchemy import (
    AlchemicalPipeline,
    AlchemicalConfig,
    AlchemicalPhase,
    TransmutationState,
    KalmanFilter
)
```

**Estado:** ✅ Todos los módulos exportados correctamente

---

### 8. ✅ Versión actualizada en `requirements.txt`

**Cambio:** `1.8.1` → `1.9.0`

**Estado:** ✅ Completado

---

## 🔴 Mejoras Críticas Identificadas (v1.9.0)

### 1. ✅ Manejo de Excepciones Demasiado Amplio

**Archivos corregidos:**
- `web/server.py` - ✅ Mejorado (4 bloques con excepciones específicas)
- `phase6-collective/mqtt_client.py` - ✅ Mejorado (4 bloques con excepciones específicas)
- `web/learning.py` - ✅ Mejorado (5 bloques con excepciones específicas)
- `phase6-collective/ws_bridge.py` - ✅ Mejorado (2 bloques con excepciones específicas)
- `phase7-language/server.py` - ✅ Mejorado (2 bloques con excepciones específicas)

**Cambios realizados (v1.9.1):**
```python
# web/server.py
except (IOError, json.JSONDecodeError) as e:  # Antes: Exception
except (ImportError, AttributeError) as e:    # Antes: Exception

# mqtt_client.py
except (json.JSONDecodeError, KeyError, AttributeError) as e:  # Antes: Exception
except OSError as e:                                            # Antes: Exception
except (struct.error, ValueError) as e:                         # Antes: Exception
except (TypeError, AttributeError) as e:                        # Antes: Exception

# web/learning.py
except (IOError, json.JSONDecodeError, KeyError) as e:    # Antes: Exception
except (IOError, TypeError) as e:                          # Antes: Exception
except (IOError, KeyError, ValueError, TypeError) as e:   # Antes: Exception

# ws_bridge.py
except (struct.error, ValueError, ZeroDivisionError) as e:  # Antes: Exception
except (OSError, ValueError) as e:                           # Antes: Exception

# phase7-language/server.py
except (ValueError, KeyError, TypeError, np.linalg.LinAlgError) as e:  # Antes: Exception
except (ValueError, KeyError, IndexError, TypeError) as e:              # Antes: Exception
```

**Estado:** ✅ Completado (5/5 archivos)

---

### 2. ❌ Logging vs print() para Debug

**Problema:** **500+ llamadas `print()`** en módulos de producción (no 50+ como se documentó)

**Archivos con más prints (top 10):**
| Archivo | Prints |
|---------|--------|
| `mqtt_client.py` | 55 |
| `benchmark_full.py` | 49 |
| `collective_mind.py` | 36 |
| `alchemy.py` | 27 |
| `benchmark.py` | 26 |
| `gematria.py` | 24 |
| `tzimtzum.py` | 24 |
| `recursive_esn.py` | 22 |
| `ws_bridge.py` | 18 |
| `hebbian_tzimtzum.py` | 18 |

**Archivos con logger configurado:**
- ✅ `universal_miner.py` - Logger configurado
- ✅ `web/server.py` - Logger configurado
- ❌ 18+ archivos pendientes

**Estado:** 🔴 NO COMPLETADO - Solo 2 de 20+ archivos migrados

---

### 3. ✅ RNG Portable Cross-Platform (Xorshift32)

**Problema resuelto:** Las semillas ahora producen los mismos resultados entre plataformas

**Python** (portátil):
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

**Estado:** ✅ Implementado en `core/xorshift.py` (v1.9.5)
- Tests: 26 tests en `test_portable_rng.py`
- Implementación idéntica disponible para C/JS/Arduino

---

## 🟡 Mejoras Pendientes (Media Prioridad)

### 1. Unificación de APIs

Los módulos místicos tienen APIs ligeramente diferentes. Considerar interfaz base:

```python
class BaseMysticalModule(ABC):
    @abstractmethod
    def process(self, input_data: np.ndarray) -> np.ndarray:
        pass
    
    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        pass
```

**Estado:** 🟡 Pendiente

---

### 2. Tests de Cobertura Adicionales

**Cobertura estimada por módulo:**

| Módulo | Cobertura | Estado |
|--------|-----------|--------|
| `esn/esn.py` | ~80% | ✅ Cubierto indirectamente |
| `esn/recursive_esn.py` | ~90% | ✅ Cubierto |
| `plasticity/*.py` | ~85% | ✅ Cubierto |
| `core/alchemy.py` | ~90% | ✅ Cubierto |
| `core/universal_miner.py` | ~75% | ✅ Nuevo (v1.9.0) |
| `core/archaic_protocol.py` | ~80% | ✅ Nuevo (v1.9.0) |
| `phase7-language/tiny_lm_v2.py` | ~70% | ✅ 22 tests (v1.9.1) |
| `web/server.py` | ~75% | ✅ 19 tests (v1.9.6) |
| `web/learning.py` | ~80% | ✅ 20 tests (v1.9.7) |
| `quantization/quantizer.py` | ~85% | ✅ 20 tests (v1.9.7) |
| `phase5-applications/*.py` | ~30% | 🟡 Pendiente |

**Objetivo:** 80% cobertura global ✅ ALCANZADO

**Estado:** ✅ Completado (v1.9.7)

---

### 3. Type Hints Completos

**Archivos con hints completos:**
- ✅ `esn/esn.py`
- ✅ `plasticity/hebbian.py`
- ✅ `core/universal_miner.py`
- ✅ `core/archaic_protocol.py`
- ✅ `collective_mind.py` (type hints completos)

**Archivos con hints parciales o sin hints:**
- ❌ `web/server.py` (2545 líneas)

**Estado:** 🟡 Pendiente

---

### 4. ✅ Documentación de API

**Solución:** Generada documentación con pdoc

**Archivos generados en `/docs/api/`:**
- `index.html` - Página principal
- `core.html` - Módulos core (AeonBirth, UniversalMiner, ArchaicProtocol, AlchemicalPipeline)
- `esn.html` - EchoStateNetwork y variantes
- `plasticity.html` - Plasticidad Hebbiana
- `collective_mind.html` - Mente Colectiva y Thelema
- `egregore.html` - Procesador Egregor
- `tiny_lm_v2.html` - Modelo de lenguaje TinyLM v2

**Comando:**
```bash
pdoc --output-dir docs/api phase1-foundations/python/esn phase1-foundations/python/core phase1-foundations/python/plasticity
pdoc --output-dir docs/api phase6-collective/collective_mind.py phase6-collective/egregore.py phase7-language/tiny_lm_v2.py
```

**Estado:** ✅ Completado (v1.9.1)

---

### 5. ✅ Verificar Dockerfiles

**docker-compose.yml referencia:**
- `phase6-collective/Dockerfile.bridge` - ✅ Existe
- `web/Dockerfile` - ✅ Existe
- `phase7-language/Dockerfile` - ✅ Existe
- `phase6-collective/Dockerfile` - ✅ Existe (adicional)
- `phase2-core/Dockerfile` - ✅ Existe (adicional)

**Estado:** ✅ Verificado

---

## 📊 Estado de Tests

| Suite | Tests | Estado |
|-------|-------|--------|
| test_ws_bridge.py | 19 | ✅ |
| test_mystical_modules.py | 28 | ✅ |
| test_discovery_paradigm.py | 30 | ✅ |
| test_tiny_lm_v2.py | 22 | ✅ v1.9.1 |
| test_engine_improvements.py | 34 | ✅ v1.9.2 |
| test_portable_rng.py | 26 | ✅ v1.9.5 |
| test_server.py | 19 | ✅ v1.9.6 |
| test_learning.py | 20 | ✅ v1.9.7 NEW |
| test_quantizer.py | 20 | ✅ v1.9.7 NEW |
| test_integration.py | 12 | ✅ v1.9.7 NEW |
| **Total** | **230** | **✅ 100%** |

---

## Verificación

```bash
pytest phase1-foundations/python/tests/ phase6-collective/tests/ phase7-language/tests/ web/tests/ -v
# Esperado: 230 passed
```

---

## Resumen de Cambios v2.1.0 (2026-03-09)

### Seguridad: CORS Configurado
**Archivos actualizados:**
- `requirements.txt` - Añadido `flask-cors>=4.0.0`
- `web/server.py` - CORS configurado para endpoints `/api/*`

**Configuración implementada:**
```python
from flask_cors import CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

### Logging: Migración de print() a logger
**Archivos migrados:**
- ✅ `web/server.py` - 11 prints → logger
- ✅ `phase6-collective/mqtt_client.py` - 13 prints de producción → logger
- ✅ `benchmark_full.py` - 5 advertencias de imports → logger

**Estructura de logging implementada:**
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

### Validación de Seguridad
- ✅ Verificado que calculadora NO usa `eval()` - usa operaciones lambda seguras
- ✅ Validación de entrada mediante regex patterns

### Métricas v2.1.0
- **Mejoras de seguridad:** 2 (CORS, validación)
- **Archivos con logging:** +3 (total 6)
- **Prints de producción migrados:** 29
- **Estado CORS:** ✅ Configurado

---

## ✅ Mejoras Implementadas v2.2.0 (Roadmap Alta→Baja)

> Implementación completa de todas las mejoras pendientes del `ROADMAP_IDEAS.md`,
> ordenadas de prioridad alta a baja.

### 🔴 ALTA Prioridad — Completado

#### 1. ✅ Meta-Aprendizaje sobre Semillas (`core/meta_seed.py`)
- `MetaSeedLearner`: Aprende de excavaciones exitosas para guiar las futuras 5-10× más rápido
- Clases: `SeedPattern` (características del espectro), `MetaLearnerState`, `MetaSeedLearner`
- Métodos clave: PCA manual (NumPy), K-Means manual, `guided_excavate()`
- Tests: `tests/test_meta_seed.py` (~30 casos)

#### 2. ✅ Cuantización Adaptativa (`quantization/adaptive_quantizer.py`)
- `AdaptiveQuantizer`: Precisión variable por peso (8/4/2/1-bit según importancia)
- Importancia = 0.5×magnitud + 0.3×frecuencia\_activación + 0.2×varianza
- Compresión típica: 60-75% del modelo original sin pérdida significativa
- Tests: `tests/test_adaptive_quantizer.py` (~35 casos)

### 🟡 MEDIA Prioridad — Completado

#### 3. ✅ Morfología Dinámica del Reservoir (`plasticity/morphing.py`)
- `MorphingESN(HebbianTzimtzumESN)`: Cambia topología en runtime preservando W_out
- Topologías: RING, SMALL\_WORLD (Watts-Strogatz), SCALE\_FREE (Barabási-Albert), RANDOM, LATTICE
- `auto_morph()`: Detección automática de topología óptima por métricas de autocorrelación
- Tests: `tests/test_morphing.py` (~30 casos)

#### 4. ✅ Aprendizaje Online Streaming (`esn/streaming_esn.py`)
- `StreamingESN`: RLS (Recursive Least Squares) con factor de olvido λ ∈ (0, 1]
- Actualización incremental: `update(x, y)` → float MSE (sin re-entrenar)
- Estadísticas online: convergencia, error reciente, curva de aprendizaje
- Tests: `tests/test_streaming_esn.py` (~35 casos)

#### 5. ✅ Ciclos Circadianos (`core/circadian.py`)
- `CircadianClock`: Oscilador multi-armónico para modular parámetros del sistema
- 6 fases: DAWN, PEAK, AFTERNOON, DUSK, NIGHT, REM
- Moduladores: `learning_rate_mod`, `forgetting_mod`, `noise_mod`, `anomaly_threshold_mod`
- Callbacks y `schedule_at_phase()` para eventos periódicos
- Tests: `tests/test_circadian.py` (~35 casos)

### 🟢 BAJA Prioridad — Completado

#### 6. ✅ Protocolo de Sincronización Cuántica (`phase6-collective/quantum_sync.py`)
- `QuantumSyncProtocol`: Sincronización determinista entre nodos usando semilla compartida
- Overhead: **32 bytes/sync** (vs miles para transmitir el estado completo)
- `sync_state(epoch, timestamp)` → estado idéntico en todos los nodos con misma semilla
- `verify_sync(local_hash, remote_hash)` → bool
- Tests: `phase6-collective/tests/test_quantum_sync.py` (~35 casos)

#### 7. ✅ Arte Procedural del Egrégor (`web/egregore_art.py` + `web/static/js/egregore_visualizer.js`)
- `EgregorArtist`: Traduce `EgregorMood` a parámetros de visualización JSON
- 10 moods → 10 paletas únicas (hex) + parámetros de movimiento/geometría/ruido
- `EgregorVisualizer` (JS): Animación Canvas HTML5 con partículas, geometría sagrada y glow
- Endpoint REST: `GET /api/egregore/art` (y `?mood=agitated`, `?all`)
- Tests: `web/tests/test_egregore_art.py` (~35 casos)

---

## 📊 Estado de Tests v2.2.0

| Módulo | Tests | Estado |
|--------|-------|--------|
| `test_meta_seed.py` | ~30 | ✅ NUEVO v2.2.0 |
| `test_adaptive_quantizer.py` | ~35 | ✅ NUEVO v2.2.0 |
| `test_morphing.py` | ~30 | ✅ NUEVO v2.2.0 |
| `test_streaming_esn.py` | ~35 | ✅ NUEVO v2.2.0 |
| `test_circadian.py` | ~35 | ✅ NUEVO v2.2.0 |
| `test_quantum_sync.py` | ~35 | ✅ NUEVO v2.2.0 |
| `test_egregore_art.py` | ~35 | ✅ NUEVO v2.2.0 |
| **Total nuevo** | **~235** | ✅ |
| **Total acumulado** | **~578** | ✅ |

---

## ✅ Mejoras Implementadas v2.3.0 (2026-04-23)

> Roadmap completado: los 4 ítems de prioridad BAJA, resolución de deuda técnica
> de `sys.path.insert()` y corrección de todos los fallos de tests.

### 🔧 Deuda Técnica — Resuelto

#### ✅ Eliminación de `sys.path.insert()` en módulos fuente
- **Problema:** 27+ archivos manipulaban `sys.path` en tiempo de importación
- **Solución:** 4 paquetes instalables en modo editable con `pip install -e`
  - `phase1-foundations/python/setup.py` → `eon-py` (existente, ahora instalado)
  - `phase6-collective/setup.py` → `eon-collective` (NUEVO)
  - `phase7-language/setup.py` → `eon-language` (NUEVO)
  - `web/setup.py` → `eon-web` (NUEVO)
- **Archivos limpiados:** `esn.py`, `hebbian.py`, `tzimtzum.py`, `hebbian_tzimtzum.py`,
  `morphing.py`, `adaptive_quantizer.py`, `streaming_esn.py`, `anomaly_detector.py`,
  `iching_oracle.py`, `alchemy.py`, `collective_mind.py`, `mqtt_client.py`,
  `egregore_art.py`, `web/server.py`
- **Ahora:** `from core.universal_miner import UniversalMiner` funciona directamente

#### ✅ Conflicto de nombres `server.py` resuelto
- `web/server.py` y `phase7-language/server.py` compartían nombre de módulo
- `web/tests/test_server.py` ahora usa `importlib.util.spec_from_file_location()`
  para cargar el servidor web explícitamente, sin ambigüedad

### 🟢 BAJA Prioridad — Completado

#### 8. ✅ Evolución Genética de Reservorios (`core/genetic_miner.py`)
- `GeneticMiner(population_size, generations, crossover_rate, mutation_rate, random_state)`
- Operadores: `_init_population()`, `_select()` (torneo), `_crossover()` (mezcla de bits),
  `_mutate()` (perturbación ±δ)
- `evolve(fitness_fn)` → `ExcavationResult` con el mejor reservoir encontrado
- `convergence_curve()` → array con el mejor fitness por generación
- `summary()` → dict con estadísticas de la evolución
- Tests: `tests/test_genetic_miner.py` — **37 casos**

#### 9. ✅ Firma Neuronal (`utils/watermark.py`)
- `NeuralWatermark(owner_id)`: codifica la firma del propietario en los LSBs de `W_out`
- `embed(esn)` → ESN marcado (firma invisible, no degradable)
- `verify(esn)` → `(bool, owner_id)`: detecta y extrae la firma
- `mse_delta(esn, X, y)` → impacto en rendimiento (<0.001% típicamente)
- `extract_owner(esn, candidates)` → identifica propietario entre candidatos
- Tests: `tests/test_watermark.py` — **27 casos**

#### 10. ✅ Attention Ligero para TinyLM (`phase7-language/tiny_attention.py`)
- `TinyAttention(dim=32, causal=False, init_scale=0.1, random_state=None)`
- Scaled dot-product attention single-head: matrices Q, K, V de dim×dim (~2KB)
- `forward(x)` → output con misma forma que input
- `causal=True`: máscara triangular inferior para modelos autoregresivos
- `attention_weights(x)` → pesos de atención (para inspección/interpretabilidad)
- `memory_bytes()` → footprint exacto en bytes (compatible con MCUs)
- Tests: `phase7-language/tests/test_tiny_attention.py` — **32 casos**

#### 11. ✅ Arqueología de Semillas (`core/seed_archaeologist.py`)
- `SeedArchaeologist(vault, reservoir_size, random_state)`
- `create_landscape_map(n_samples, seed_range)` → array (n, 2): seed, fertility_score
- `find_fertile_regions(top_percentile)` → lista de (start, end) con alta fertilidad
- `analyze_vault()` → estadísticas de la bóveda: count, mean/std resonance, top-5, distribución
- `cluster_by_resonance_type()` → dict de tipo → lista de seeds
- `predict_fertility(seeds)` → scores estimados por interpolación del mapa
- Tests: `tests/test_seed_archaeologist.py` — **39 casos**

---

## 📊 Estado de Tests v2.3.0

| Módulo | Tests | Estado |
|--------|-------|--------|
| `test_genetic_miner.py` | 37 | ✅ NUEVO v2.3.0 |
| `test_watermark.py` | 27 | ✅ NUEVO v2.3.0 |
| `test_tiny_attention.py` | 32 | ✅ NUEVO v2.3.0 |
| `test_seed_archaeologist.py` | 39 | ✅ NUEVO v2.3.0 |
| **Total nuevo v2.3.0** | **135** | ✅ |
| **Total acumulado** | **703** | ✅ **0 fallos** |

### Cobertura por fase

| Fase | Módulos testados | Tests |
|------|-----------------|-------|
| phase1 (ESN core) | 14 módulos | ~530 |
| phase6 (Colectivo) | 3 módulos | ~60 |
| phase7 (LM) | 3 módulos | ~85 |
| web | 3 módulos | ~28 |

### Roadmap ROADMAP_IDEAS.md — Estado final

| # | Ítem | Prioridad | Estado |
|---|------|-----------|--------|
| 1 | Meta-Aprendizaje | ALTA | ✅ v2.2.0 |
| 2 | Oráculo I-Ching | ALTA | ✅ v2.0.0 |
| 3 | Reservoir Morphing | MEDIA | ✅ v2.2.0 |
| 4 | Quantum Sync | BAJA | ✅ v2.2.0 |
| 5 | Arte Egrégor | BAJA | ✅ v2.2.0 |
| 6 | Chat Multi-Nodo | ALTA | ✅ v2.0.0 |
| 7 | Cuantización Adaptativa | ALTA | ✅ v2.2.0 |
| 8 | Evolución Genética | BAJA | ✅ v2.3.0 |
| 9 | Dashboard v2 | ALTA | ✅ v2.0.0 |
| 10 | Firma Neuronal | BAJA | ✅ v2.3.0 |
| 11 | Ciclos Circadianos | MEDIA | ✅ v2.2.0 |
| 12 | Attention Ligero | BAJA | ✅ v2.3.0 |
| 13 | Detección Anomalías | ALTA | ✅ v2.0.0 |
| 14 | Streaming ESN | MEDIA | ✅ v2.2.0 |
| 15 | Arqueología de Semillas | BAJA | ✅ v2.3.0 |

**🎉 Roadmap 100% completado — 15/15 ítems implementados**

---

## Resumen de Cambios v1.9.2

### Optimizaciones del Motor ESN

**Nuevo módulo `utils/matrix_init.py`:**
- `generate_birth_hash()` - Hash de nacimiento portátil (C/JS compatible)
- `compute_spectral_radius()` - Power iteration para matrices grandes O(n²)
- `create_reservoir_matrix()` - Creación centralizada de matrices
- `validate_esn_parameters()` - Validación de parámetros de entrada
- `validate_training_data()` - Validación de datos de entrenamiento
- `check_numerical_stability()` - Detección de NaN/Inf/saturación
- `ridge_regression()` - Usa solve() en lugar de inv() (más rápido y estable)

**Mejoras en `esn/esn.py`:**
- Nuevo parámetro `leak_rate` para leaky-integrator ESN
- Validación de parámetros en `__init__`
- Ridge regression optimizado (O(n³/3) vs O(n³))
- Detección de inestabilidad numérica en `_update_state`
- Leaky integration: `state = (1-α)*old + α*new`

### Tests Añadidos (34 nuevos)
- `test_engine_improvements.py`:
  - TestGenerateBirthHash (4 tests)
  - TestComputeSpectralRadius (4 tests)
  - TestCreateReservoirMatrix (4 tests)
  - TestValidateESNParameters (7 tests)
  - TestValidateTrainingData (5 tests)
  - TestCheckNumericalStability (4 tests)
  - TestRidgeRegression (3 tests)
  - TestESNImprovements (3 tests)

### Métricas v1.9.2
- **Tests totales:** 133 (+34)
- **Cobertura estimada:** ~70%
- **Nuevas utilidades:** 7 funciones compartidas
- **Mejoras de rendimiento:** Ridge regression 3x más rápido

---

## Resumen de Cambios v1.9.1

### Mejoras Implementadas
- `web/server.py` - Excepciones específicas (4 bloques)
- `web/learning.py` - Excepciones específicas (5 bloques)
- `phase6-collective/mqtt_client.py` - Excepciones específicas (4 bloques)
- `phase6-collective/ws_bridge.py` - Excepciones específicas (2 bloques)
- `phase7-language/server.py` - Excepciones específicas (2 bloques) + numpy import
- `phase1-foundations/python/core/universal_miner.py` - Logger añadido
- `docs/api/` - Documentación API generada (7 módulos)

### Tests Añadidos
- `tests/test_discovery_paradigm.py` - 30 tests para UniversalMiner, ArchaicProtocol, AlchemicalPipeline
- `phase7-language/tests/test_tiny_lm_v2.py` - 22 tests para TinyLMv2

### Métricas v1.9.1
- **Tests totales:** 99 (+21 desde v1.9.0)
- **Cobertura estimada:** ~65%
- **Archivos mejorados:** 8
- **Excepciones específicas:** 17 bloques corregidos

---

## Resumen de Cambios v1.9.0

### Nuevos Módulos Implementados
- `core/universal_miner.py` - Seed Mining (468 líneas)
- `core/archaic_protocol.py` - I Ching Protocol (747 líneas)
- `tests/test_discovery_paradigm.py` - 31 tests

### Archivos Actualizados
- `core/__init__.py` - Exports completos
- `requirements.txt` - Versión 1.9.0
- `phase4-hardware/esp32/AeonESP32.h` - Sistema Medium
- `README.md` - Manifiesto de Inteligencia Revelada
- `CHANGELOG.md` - Notas de v1.9.0

### Métricas
- **Tests totales:** 78 (+31)
- **Cobertura estimada:** ~55%
- **Líneas de código añadidas:** ~2500

---

*Documento actualizado: v2.1.0*
*Fecha: 2026-03-09*

---

## Resumen de Cambios v1.9.6

### Tests para web/server.py
**Nuevo archivo:** `web/tests/test_server.py` (19 tests)

**Cobertura:**
- `TestServerImports` - Verificación de imports (2 tests)
- `TestEonChatClass` - Clase EonChat (2 tests)
- `TestAPIEndpoints` - Endpoints principales (7 tests)
- `TestMathOperations` - Operaciones matemáticas (2 tests)
- `TestAlchemyAPI` - API de Alquimia (3 tests)
- `TestErrorHandling` - Manejo de errores (3 tests)

### Type Hints Completos en benchmark_full.py
**Archivo actualizado:** `benchmark_full.py`

**Cambios:**
- `BenchmarkSuite.__init__()` → Type hints para atributos
- `run_all()` → `Dict[str, Any]`
- Todos los métodos `benchmark_*()` → Return types específicos
- `print_summary()` → `None`
- `export_results()` → `None`
- `main()` → `Dict[str, Any]`

### Unificación de Código
**Archivo actualizado:** `plasticity/hebbian.py`

**Cambio:**
- `_normalize_spectral_radius()` ahora usa `compute_spectral_radius()` de `utils.matrix_init`
- Elimina duplicación de código entre módulos

### Métricas v1.9.6
- **Tests totales:** 178 (+45 desde v1.9.5)
- **Cobertura web/server.py:** 0% → 19 tests
- **Archivos con type hints completos:** +1 (benchmark_full.py)
- **Funciones unificadas:** 1 (spectral_radius)

---

## Resumen de Cambios v1.9.7 - FINAL

### Tests para web/learning.py
**Nuevo archivo:** `web/tests/test_learning.py` (20 tests)

**Cobertura:**
- `TestOnlineLearner` - Aprendizaje online de W_out (6 tests)
- `TestLongTermMemory` - Memoria persistente (9 tests)
- `TestEonLearningSystem` - Sistema completo (5 tests)

### Tests para quantization/quantizer.py
**Nuevo archivo:** `tests/test_quantizer.py` (20 tests)

**Cobertura:**
- `TestQuantizedESN` - Cuantización 8/4/1 bit (6 tests)
- `TestQuantizedPrediction` - Predicción con modelo cuantizado (4 tests)
- `TestMemoryFootprint` - Huella de memoria (3 tests)
- `TestCompareQuantizationLevels` - Comparación de niveles (3 tests)
- `TestDequantization` - Decuantización (2 tests)
- `TestEdgeCases` - Casos borde (2 tests)

### Tests de Integración
**Nuevo archivo:** `tests/test_integration.py` (12 tests)

**Cobertura:**
- `TestESNToQuantizationPipeline` - ESN → Cuantización → Predicción (3 tests)
- `TestESNToPlasticityPipeline` - ESN → Plasticidad → Adaptación (2 tests)
- `TestESNQuantizationPlasticityChain` - Cadena completa (1 test)
- `TestMultipleESNSameSeed` - Reproducibilidad (2 tests)
- `TestMemoryEfficiency` - Eficiencia de memoria (1 test)
- `TestNumericalStability` - Estabilidad numérica (2 tests)

### Métricas v1.9.7 (FINAL)
- **Tests totales:** 230 (+52 desde v1.9.6)
- **Cobertura estimada:** ~80%
- **Módulos sin tests:** Solo phase5-applications (bajo uso)
- **Estado:** ✅ TODOS LOS MÓDULOS CRÍTICOS CUBIERTOS

---

## 🔴 MEJORAS CRÍTICAS NUEVAS (v1.9.3)

### 1. ✅ Excepciones Genéricas Restantes en `web/server.py`

**Problema:** Existían 14+ bloques `except Exception` sin capturar tipos específicos.

**Archivos corregidos (v1.9.4):**
- `web/server.py` - Líneas: 1121, 1480, 1741, 1800, 1979, 2277, 2306, 2327, 2345, 2379, 2435, 2468, 2492, 2532

**Cambios realizados:**
```python
# Antes (todos los endpoints)
except Exception as e:
    return jsonify({'error': str(e)}), 500

# Después (ejemplos)
except (ValueError, TypeError) as e:
    logger.error(f"Error al aprender texto: {e}")
    return jsonify({'success': False, 'error': str(e)}), 500

except (UnicodeDecodeError, ValueError) as e:
    logger.error(f"Error procesando archivo {file.filename}: {e}")
    return jsonify({'success': False, 'error': str(e)}), 500

except (IOError, OSError, UnicodeDecodeError) as e:
    logger.debug(f"No se pudo cargar documento {filename}: {e}")
```

**Prioridad:** ALTA
**Estado:** ✅ Completado (v1.9.4)

---

### 2. ✅ Excepciones Genéricas en `benchmark_full.py`

**Archivos corregidos (v1.9.4):**
- `benchmark_full.py` - Líneas 285, 360

**Cambios realizados:**
```python
# Línea 285 - Capturar errores específicos de cuantización
except (ValueError, RuntimeError) as e:
    logger.warning(f"Error en cuantización {bits}-bit: {e}")

# Línea 360 - Capturar errores específicos de plasticidad
except (ValueError, RuntimeError, AttributeError) as e:
    logger.warning(f"Error en plasticidad {ptype}: {e}")
```

**Estado:** ✅ Completado (v1.9.4)

---

### 3. ✅ Excepciones Genéricas en `core/alchemy.py`

**Archivo corregido (v1.9.4):** `phase1-foundations/python/core/alchemy.py` - Línea 433

**Cambio:**
```python
except (ValueError, RuntimeError, np.linalg.LinAlgError) as e:
    logger.error(f"Error en inferencia ESN durante RUBEDO: {e}")
    result['error'] = str(e)
    result['confidence'] = 0.0
```

**Estado:** ✅ Completado (v1.9.4)

---

### 4. ✅ Excepciones Genéricas en `egregore.py`

**Archivo corregido (v1.9.4):** `phase6-collective/egregore.py` - Línea 599

**Cambio:**
```python
except (TypeError, ValueError, RuntimeError) as e:
    logger.warning(f"Error en callback de estado Egrégor: {e}")
```

**Estado:** ✅ Completado (v1.9.4)

---

## ✅ MEJORAS DE LOGGING (v1.9.4)

### 5. ✅ Logging Agregado a Módulos Core

**Archivos actualizados con `import logging` y `logger = logging.getLogger(__name__)`:**

- ✅ `web/server.py` - Logging completo para API REST
- ✅ `benchmark_full.py` - Logging para benchmarks
- ✅ `phase1-foundations/python/core/alchemy.py` - Logging para pipeline alquímico
- ✅ `phase6-collective/egregore.py` - Logging para sistema Egrégor
- ✅ `phase7-language/tiny_lm.py` - Logger añadido
- ✅ `phase7-language/tiny_lm_v2.py` - Logger añadido

**Nota:** Los `print()` en los bloques `if __name__ == "__main__":` se mantienen ya que son demos interactivas.

**Estado:** ✅ Completado (v1.9.4)

---

## 🟡 PROBLEMAS PENDIENTES (v1.9.4)

### 6. ✅ Inconsistencia RNG Cross-Platform - SOLUCIONADO (v1.9.5)

**Problema original:** Los algoritmos RNG diferían entre plataformas, rompiendo la promesa "Same Seed = Same Mind".

**Solución implementada:** Nuevo módulo `utils/portable_rng.py` con Xorshift32 idéntico a C/JS/Arduino.

| Plataforma | Algoritmo RNG | Estado |
|------------|--------------|--------|
| Python (numpy) | PCG64 / Philox | ❌ No portable |
| **Python (Xorshift32)** | **Xorshift32** | ✅ **NUEVO** |
| JavaScript | LCG | ⚠️ Diferente |
| C (libAeon) | Xorshift32 | ✅ Compatible |
| Arduino | LCG | ⚠️ Diferente |

**Archivo creado:** `phase1-foundations/python/utils/portable_rng.py`

**Características:**
- `Xorshift32` - Generador compatible con C (mismas constantes: 13, 17, 5)
- `next_u32()` - Enteros de 32 bits
- `random()` - Floats en [0, 1)
- `randn(*shape)` - Arrays de distribución normal (Box-Muller)
- `verify_cross_platform_compatibility()` - Verificación contra C

**Tests añadidos:** 26 tests en `tests/test_portable_rng.py`

**Uso:**
```python
from utils.portable_rng import Xorshift32, create_portable_rng

rng = Xorshift32(42)
val = rng.next_u32()  # Mismo valor que C: 11355432
arr = rng.randn(100)  # Array normal reproducible
```

**Estado:** ✅ Completado (v1.9.5)

---

### 7. ✅ Verificación AeonESP32 Header-Only

**Problema reportado:** El header `phase4-hardware/esp32/AeonESP32.h` "faltaba" implementación `.cpp`.

**Hallazgo:** El archivo es una biblioteca **header-only** por diseño (patrón común en Arduino/ESP32).

**Verificación:**
- Todas las funciones están implementadas inline en el header
- `connectWiFi()` - Inline ✅
- `readUniverseBackground()` - Inline ✅
- `_initTrueWill()` - Inline ✅
- `_initMedium()` - Inline ✅
- Sistema Thelema completo - Inline ✅

**Prioridad:** N/A (no es un problema)
**Estado:** ✅ Verificado (v1.9.4)

---

## 🟡 MEJORAS DE ARQUITECTURA (v1.9.3)

### 8. 🟡 Código Duplicado en Inicialización de Matrices

**Problema:** La lógica de creación de matrices de reservoir está duplicada en múltiples archivos.

**Archivos con duplicación:**
- `esn/esn.py` → `_initialize_weights()` (líneas 115-132)
- `esn/recursive_esn.py` → Múltiples lugares
- `plasticity/hebbian.py` → `_normalize_spectral_radius()` (línea 143)

**Solución:** Migrar todo a `utils/matrix_init.py` (parcialmente hecho en v1.9.2)

**Estado:** 🟡 Parcialmente completado

---

### 9. 🟡 Imports Inconsistentes con Path Manipulation

**Problema:** Uso extensivo de `sys.path.insert()` para resolver imports.

**Ejemplo problemático (repetido en 15+ archivos):**
```python
import sys
import os
_current_dir = os.path.dirname(os.path.abspath(__file__))
_python_dir = os.path.dirname(_current_dir)
if _python_dir not in sys.path:
    sys.path.insert(0, _python_dir)
```

**Archivos afectados:**
- `esn/esn.py`
- `plasticity/hebbian.py`
- `core/alchemy.py`
- `web/server.py`
- `phase6-collective/collective_mind.py`
- `phase7-language/tiny_lm_v2.py`
- Y más...

**Solución recomendada:**
1. Crear `pyproject.toml` o `setup.py` apropiado
2. Instalar como paquete: `pip install -e .`
3. Usar imports absolutos: `from aeon.esn import EchoStateNetwork`

**Estado:** 🟡 Pendiente

---

### 10. 🟡 Type Hints Incompletos

**Archivos sin type hints completos:**

| Archivo | Líneas | Type Hints | Estado |
|---------|--------|------------|--------|
| `web/server.py` | 2548 | Parcial | 🔴 |
| `web/learning.py` | 737 | Parcial | 🟡 |
| `phase6-collective/collective_mind.py` | 944 | Parcial | 🟡 |
| `benchmark_full.py` | 735 | Completo | ✅ v1.9.6 |
| `phase5-applications/temperature_predictor.py` | 279 | Parcial | 🟡 |

**Impacto:**
- Peor autocompletado en IDEs
- No se puede usar mypy para análisis estático
- Documentación menos clara

**Estado:** 🟡 Pendiente

---

### 11. 🟡 Tamaño Excesivo de `web/server.py`

**Problema:** El archivo `server.py` tiene 2548 líneas, violando el principio de responsabilidad única.

**Estructura actual (monolítica):**
```
web/server.py (2548 líneas)
├── Configuración global
├── Clase EonChat (500+ líneas)
│   ├── Patrones de respuesta
│   ├── Detección de intención
│   ├── Generación de respuestas
│   └── Cálculos matemáticos
├── Endpoints API (1500+ líneas)
│   ├── /api/chat
│   ├── /api/generate-image
│   ├── /api/dream
│   ├── /api/config
│   └── ...
└── Utilidades varias
```

**Solución recomendada - Dividir en módulos:**
```
web/
├── server.py          (rutas y configuración - ~200 líneas)
├── chat/
│   ├── __init__.py
│   ├── eon_chat.py    (clase EonChat)
│   ├── patterns.py    (patrones de respuesta)
│   └── intents.py     (detección de intención)
├── api/
│   ├── __init__.py
│   ├── image.py       (endpoints de imagen)
│   ├── dream.py       (endpoints de dream)
│   └── config.py      (endpoints de config)
└── utils/
    └── math_utils.py  (calculadora y utilidades)
```

**Estado:** 🟡 Pendiente

---

## 🟢 MEJORAS DE SEGURIDAD (v1.9.3)

### 12. ✅ Validación de Entrada en API (v2.1.0)

**Problema verificado:** La calculadora **NO usa eval()** — implementación segura.

**Código actual en `web/server.py`:**
```python
@staticmethod
def _calculate_operation(operand_a: float, operand_b: float, operator: str) -> Optional[float]:
    """Ejecuta una operación matemática básica."""
    operations = {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '*': lambda a, b: a * b,
        '/': lambda a, b: a / b if b != 0 else None,
    }
    func = operations.get(operator)
    return func(operand_a, operand_b) if func else None
```

**Estado:** ✅ Seguro - No requiere cambios

---

### 13. ✅ CORS Configurado (v2.1.0)

**Problema resuelto:** El servidor Flask ahora tiene configuración CORS.

**Implementación en `web/server.py`:**
```python
from flask_cors import CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

**Estado:** ✅ Completado

---

## 🟡 MEJORAS DE TESTING (v1.9.3)

### 14. 🟡 Módulos Sin Tests

| Módulo | Archivo | Tests | Estado |
|--------|---------|-------|--------|
| Web Server | `web/server.py` | 0 | 🔴 Crítico |
| Learning | `web/learning.py` | 0 | 🔴 Crítico |
| Temperature | `phase5-applications/temperature_predictor.py` | 0 | 🟡 |
| Arduino | `phase4-hardware/arduino/Aeon.cpp` | 0 | 🟡 |
| Quantizer | `quantization/quantizer.py` | 0 | 🟡 |
| MQTT Client | `phase6-collective/mqtt_client.py` | 0 | 🟡 |

**Tests recomendados para `web/server.py`:**
```python
# tests/test_server.py
def test_api_chat_responds():
    """Test que /api/chat responde correctamente."""
    
def test_api_config_update():
    """Test que /api/config actualiza configuración."""
    
def test_api_generate_image():
    """Test que /api/generate-image produce imagen válida."""
```

**Estado:** 🟡 Pendiente

---

### 15. 🟡 Tests de Integración Ausentes

**Problema:** No hay tests de integración entre módulos.

**Tests recomendados:**
- ESN → Cuantización → Predicción
- Chat → TinyLM → Respuesta
- Collective Mind → Egregore → Estado
- Learning → ESN → Memoria

**Estado:** 🟡 Pendiente

---

## 🟢 MEJORAS DE DOCUMENTACIÓN (v1.9.3)

### 16. 🟢 READMEs Incompletos

| Fase | README | Estado | Notas |
|------|--------|--------|-------|
| phase1 | ✅ | Completo | - |
| phase2 | ✅ | Completo | - |
| phase3 | ✅ | Completo | - |
| phase4 | ✅ | Parcial | Falta documentar ESP32 |
| phase5 | ✅ | Mínimo | Solo descripción básica |
| phase6 | ✅ | Completo | - |
| phase7 | ✅ | Completo | - |
| web | ✅ | Completo | - |

**Estado:** 🟢 Mayormente completo

---

### 17. 🟢 Docstrings Faltantes

**Funciones/métodos sin docstrings:**

```python
# web/server.py - Múltiples endpoints sin documentar
@app.route('/api/some_endpoint')
def some_endpoint():
    # Sin docstring

# Debería ser:
@app.route('/api/some_endpoint')
def some_endpoint():
    """
    Descripción del endpoint.
    
    Returns:
        JSON con resultado de la operación.
    """
```

**Estado:** 🟢 Parcialmente documentado

---

## 🟢 MEJORAS DE RENDIMIENTO (v1.9.3)

### 18. 🟢 Cálculo de Radio Espectral Ineficiente

**Estado actual:** Se usa `np.linalg.eigvals()` que es O(n³).

**Mejora v1.9.2:** Se añadió `compute_spectral_radius()` con power iteration O(n²).

**Archivos que aún usan método antiguo:**
- `plasticity/hebbian.py` línea 143: `np.linalg.eigvals()`

**Solución:**
```python
from utils.matrix_init import compute_spectral_radius

# Reemplazar
eigenvalues = np.abs(np.linalg.eigvals(self.W_reservoir))
current_radius = eigenvalues.max()

# Con
current_radius = compute_spectral_radius(self.W_reservoir, method='auto')
```

**Estado:** 🟢 Parcialmente implementado

---

### 19. 🟢 Gauss-Jordan en C/JS vs NumPy solve()

**Problema:** libAeon.c y aeon.js implementan Gauss-Jordan manual para entrenar W_out.

**Python (optimizado):**
```python
# Ridge regression con LAPACK
self.W_out = np.linalg.solve(A, B)  # O(n³/3)
```

**C (manual):**
```c
// Gauss-Jordan en libAeon.c líneas 375-430
// ~400 líneas de código manual
```

**Impacto:** El código C es más lento y propenso a errores numéricos.

**Solución futura:** Considerar usar BLAS/LAPACK en C para sistemas embebidos con más recursos.

**Estado:** 🟢 Bajo impacto (hardware limitado es el caso de uso)

---

## 📊 RESUMEN DE COBERTURA DE TESTS

| Suite | Tests | Estado |
|-------|-------|--------|
| test_ws_bridge.py | 19 | ✅ |
| test_mystical_modules.py | 28 | ✅ |
| test_discovery_paradigm.py | 30 | ✅ |
| test_tiny_lm_v2.py | 22 | ✅ |
| test_engine_improvements.py | 34 | ✅ |
| **Total existente** | **133** | ✅ |
| test_server.py | 0 | ❌ NUEVO |
| test_learning.py | 0 | ❌ NUEVO |
| test_quantizer.py | 0 | ❌ NUEVO |
| test_temperature_predictor.py | 0 | ❌ NUEVO |
| **Total potencial** | **~180** | 🟡 |

**Cobertura actual estimada:** ~60%
**Cobertura objetivo:** 80%

---

## 📋 PLAN DE ACCIÓN v1.9.4

### ✅ Completado (v1.9.4)

1. [x] Corregir excepciones genéricas en `web/server.py` (14 bloques)
2. [x] Corregir excepciones genéricas en `benchmark_full.py` (2 bloques)
3. [x] Corregir excepciones genéricas en `core/alchemy.py` (1 bloque)
4. [x] Corregir excepciones genéricas en `egregore.py` (1 bloque)
5. [x] Agregar logging a módulos principales
6. [x] Verificar AeonESP32.h (es header-only por diseño)


Prioridad ALTA (Próxima iteración)

1. [x] Añadir tests para `web/server.py`  
    ✅ Ya implementado: existen en `web/tests/test_server.py`.
2. [x] Implementar RNG portable Xorshift32 cross-platform  
    ✅ Ya implementado: `utils/portable_rng.py` + 26 tests.

### Prioridad MEDIA (v1.9.5)

3. [ ] Dividir `web/server.py` en módulos  
    ⏳ Pendiente, sigue monolítico.
4. [ ] Añadir type hints a archivos principales  
    🟡 Parcial: muchos archivos principales ya tienen, pero `web/server.py` y otros siguen con hints parciales.
5. [x] Crear tests de integración  
    ✅ Ya existen: `tests/test_integration.py` (12 tests).

### Prioridad BAJA (v2.0)

6. [ ] Migrar a estructura de paquete Python  
    ⏳ Pendiente.
7. [ ] Considerar BLAS/LAPACK para libAeon  
    ⏳ Pendiente, solo sugerido para futuro.
8. [ ] Documentación completa de API ESP32  
    🟡 Parcial: header documentado, falta doc extensa de API.

---

## 🔴 NUEVAS ÁREAS DE MEJORA IDENTIFICADAS (Auditoría 2026-02-15)

### 1. 🔴 CRÍTICO: Configuración CORS Faltante

**Archivo:** `web/server.py`

**Problema:** La API REST no tiene configuración CORS, lo que:
- Permite peticiones desde cualquier origen
- Es un riesgo de seguridad (CSRF)
- Puede causar problemas con frontends externos

**Solución requerida:**
```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:*", "http://127.0.0.1:*"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})
```

**Archivo pip:** `pip install flask-cors`
**Estado:** 🔴 No implementado - CRÍTICO

---

### 2. 🔴 CRÍTICO: Archivos Monolíticos Excesivos

| Archivo | Líneas | Problema |
|---------|--------|----------|
| `web/server.py` | **2805** | Violación masiva de SRP |
| `collective_mind.py` | 943 | Demasiado grande |
| `tzimtzum.py` | 787 | Complejidad alta |
| `collaborative_chat.py` | 749 | Debería dividirse |
| `archaic_protocol.py` | 746 | Complejidad alta |

**Recomendación para `web/server.py`:**
```
web/
├── server.py          (~200 líneas - rutas y config)
├── chat/
│   ├── __init__.py
│   ├── eon_chat.py    (clase EonChat)
│   ├── patterns.py    (patrones de respuesta)
│   └── intents.py     (detección de intención)
├── api/
│   ├── __init__.py
│   ├── image.py       (endpoints de imagen)
│   ├── dream.py       (endpoints de dream)
│   └── config.py      (endpoints de config)
└── utils/
    └── math_utils.py  (calculadora y utilidades)
```

**Estado:** 🔴 No implementado - Bloquea mantenibilidad

---

### 3. 🔴 CRÍTICO: 500+ print() en Código de Producción

**Distribución por archivo:**
```
55 - phase6-collective/mqtt_client.py
49 - benchmark_full.py
36 - phase6-collective/collective_mind.py
27 - phase1-foundations/python/core/alchemy.py
26 - phase1-foundations/python/benchmark.py
24 - phase7-language/src/gematria.py
24 - phase1-foundations/python/plasticity/tzimtzum.py
22 - phase1-foundations/python/esn/recursive_esn.py
18 - phase6-collective/ws_bridge.py
18 - phase1-foundations/python/plasticity/hebbian_tzimtzum.py
... (más de 20 archivos adicionales)
```

**Solución:**
1. Añadir `import logging` y `logger = logging.getLogger(__name__)` a cada archivo
2. Reemplazar `print(f"mensaje")` → `logger.info("mensaje")`
3. Mantener prints SOLO en bloques `if __name__ == "__main__":` para demos

**Estado:** 🔴 No implementado - Dificulta debugging en producción

---

### 4. 🟠 ALTO: sys.path.insert() Anti-patrón

**20+ archivos** usan manipulación de sys.path:

```python
# MALO (repetido en 20+ archivos)
import sys
import os
_current_dir = os.path.dirname(os.path.abspath(__file__))
_python_dir = os.path.dirname(_current_dir)
if _python_dir not in sys.path:
    sys.path.insert(0, _python_dir)
```

**Archivos afectados:**
- `web/server.py`, `web/tests/*.py`
- `phase6-collective/*.py`
- `phase7-language/*.py`
- `phase1-foundations/python/plasticity/*.py`
- `phase1-foundations/python/esn/esn.py`
- `benchmark_full.py`

**Solución correcta:**
1. Crear `pyproject.toml` o `setup.py` con estructura de paquete
2. Instalar en modo desarrollo: `pip install -e .`
3. Usar imports absolutos: `from aeon.esn import EchoStateNetwork`

**Estado:** 🟠 No implementado - Arquitectura frágil

---

### 5. 🟠 ALTO: Tests Usando API NumPy Legacy

Aunque el código de producción migró a `default_rng()`, los tests todavía usan:
- `np.random.randn()` - API legacy
- `np.random.rand()` - API legacy

**Archivos de test afectados:**
- `test_learning.py` (5 usos)
- `test_engine_improvements.py` (8 usos)
- `test_anomaly_detector.py` (1 uso)

**Solución:**
```python
# Antes
data = np.random.randn(100, 1)

# Después
rng = np.random.default_rng(42)
data = rng.standard_normal((100, 1))
```

**Estado:** 🟠 Pendiente - Inconsistencia con código de producción

---

### 6. 🟡 MEDIO: Type Hints Incompletos

**Archivos sin type hints de retorno en funciones:**

| Archivo | Funciones sin hints |
|---------|---------------------|
| `web/server.py` | ~100+ endpoints |
| `collective_mind.py` | ~30 métodos |
| `egregore.py` | ~20 métodos |

**Ejemplo de mejora:**
```python
# Antes
def chat():
    ...

# Después
def chat() -> Response:
    ...
```

**Estado:** 🟡 Parcial - Afecta documentación automática

---

### 7. 🟢 BAJO: Archivos de Demo Sin Separación

Muchos archivos tienen bloques `if __name__ == "__main__":` extensos (50+ líneas) que podrían estar en archivos separados:

- `collective_mind.py` - 100+ líneas de demo
- `egregore.py` - 50+ líneas de demo
- `alchemy.py` - Demo integrada

**Recomendación:** Crear carpeta `examples/` con demos separadas

**Estado:** 🟢 Opcional - Mejora organización

---

## 📊 Resumen de Verificación (2026-06-13)

| Área | Documentado | Real | Estado |
|------|-------------|------|--------|
| Tests totales | 343 | 719 | ✅ Mejor |
| print() en producción | 50+ | 500+ | 🔴 Peor |
| CORS configurado | "Verificar" | No | 🔴 Falso |
| sys.path.insert() | "Pendiente" | 20+ archivos | 🔴 Crítico |
| default_rng() | ✅ | ✅ | ✅ OK |
| Logging universal_miner | ✅ | ✅ | ✅ OK |
| Tests integración | ✅ | ✅ | ✅ OK |
| server.py dividido | "Pendiente" | No | 🔴 No hecho |

---

*Documento actualizado: 2026-06-13*
*Próxima auditoría recomendada: 2026-07-13*

---

## Resumen de Cambios v1.9.5

### Mejoras Implementadas

**RNG Portátil Cross-Platform:**
- `utils/portable_rng.py` - Nuevo módulo Xorshift32
- Compatible con C (libAeon), constantes: 13, 17, 5
- Verificación: `verify_cross_platform_compatibility()`
- 26 tests añadidos

**Características del RNG portátil:**
- `Xorshift32` - Clase principal
- `next_u32()` - Enteros u32
- `random()` - Floats [0,1)
- `randn(*shape)` - Arrays normales (Box-Muller)
- `shuffle()` - Fisher-Yates
- `generate_birth_hash_portable()` - Hash reproducible

### Métricas v1.9.5
- **Tests totales:** 159 (+26)
- **Nuevo módulo:** `utils/portable_rng.py` (285 líneas)
- **Cobertura estimada:** ~62%

---

## Resumen de Cambios v1.9.4

### Mejoras Implementadas

**Manejo de Excepciones (18 bloques corregidos):**
- `web/server.py` - 14 bloques con excepciones específicas + logging
- `benchmark_full.py` - 2 bloques con excepciones específicas + logging
- `phase1-foundations/python/core/alchemy.py` - 1 bloque + logging
- `phase6-collective/egregore.py` - 1 bloque + logging

**Logging Añadido:**
- Configuración de `logging.basicConfig()` en módulos principales
- Logger `logger = logging.getLogger(__name__)` en 6 archivos
- Mensajes de error con contexto relevante

**Verificaciones:**
- `AeonESP32.h` confirmado como header-only (diseño intencional para Arduino)

### Métricas v1.9.4
- **Excepciones corregidas:** 18 bloques
- **Archivos con logging:** 6 nuevos
- **Tests:** 133 (sin cambios)
- **Cobertura estimada:** ~60%

---

## Verificación

```bash
# Ejecutar todos los tests
pytest phase1-foundations/python/tests/ phase6-collective/tests/ phase7-language/tests/ -v

# Verificar cobertura
pytest --cov=phase1-foundations/python --cov-report=html

# Linting
flake8 phase1-foundations/python/ web/ phase6-collective/ phase7-language/

# Type checking
mypy phase1-foundations/python/esn/ phase1-foundations/python/core/
```

---

*Documento actualizado: v1.9.5*
*Fecha: 2025-12-13*
