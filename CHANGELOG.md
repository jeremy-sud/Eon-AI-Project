# Changelog

Todos los cambios notables del Proyecto Eón.

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
