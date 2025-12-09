# Changelog

Todos los cambios notables del Proyecto Eón.

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
