# Changelog

Todos los cambios notables del Proyecto Eón.

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
