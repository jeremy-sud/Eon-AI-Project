# Fase 7: TinyLM (Language Modules)

Exploración en Modelos de Lenguaje Minimalistas utilizando la arquitectura Eón (ESN). Contrario a los Transformers, TinyLM busca eficiencia extrema y entrenamiento en el dispositivo.

## TinyLM v2

La versión 2 introduce mejoras significativas en arquitectura y memoria:

- **Tokenización por Palabras**: Mayor coherencia que la versión por caracteres.
- **Diccionario Trie Ultraligero**:
  - Implementación personalizada basada en arrays planos (LCRS).
  - Reduce el uso de memoria del vocabulario en >50% comparado con listas estándar (en C).
  - Soporte UTF-8 completo.
- **Decodificación Avanzada**: Greedy y Sampling con Top-K y Temperatura.

## Estructura

- `tiny_lm_v2.py`: Implementación completa del modelo.
- `src/trie_vocab.py`: Estructura de datos Trie eficiente.
- `server.py`: Interfaz Web para demos y chat colaborativo.

## Chat Colaborativo Multi-Nodo

El servidor incluye un sistema de chat colaborativo donde múltiples nodos ESN especializados colaboran para generar respuestas coherentes:

- **Nodo Analista**: Detecta intención del mensaje
- **Nodo Generador**: Crea respuesta base
- **Nodo Validador**: Verifica coherencia

### API Endpoint

```
POST /chat
{
  "message": "Tu pregunta aquí"
}
```

Respuesta:
```json
{
  "success": true,
  "response": "Respuesta colaborativa generada",
  "contributions": 3,
  "coherence_score": 0.85,
  "processing_time": 0.123
}
```

## Ejecución

```bash
# Entrenar y probar en consola
python3 tiny_lm_v2.py

# Iniciar servidor web
python3 server.py
```
