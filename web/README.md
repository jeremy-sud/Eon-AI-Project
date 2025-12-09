# 🌐 Eón Web Interface

Interfaz web completa para interactuar con Eón.

## Inicio Rápido

```bash
cd "Eón Project AI"
python -m venv .venv && source .venv/bin/activate
pip install flask numpy pillow
python web/server.py
# Abrir http://localhost:5000
```

## Estructura

```
web/
├── server.py        # Flask API (~1500 líneas)
├── learning.py      # Sistema de aprendizaje continuo
├── data/            # Persistencia JSON
│   ├── chat_history.json
│   ├── long_term_memory.json
│   ├── feedback.json
│   └── stats.json
└── static/
    ├── index.html   # Interfaz principal
    ├── css/style.css
    └── js/
        ├── app.js   # Lógica principal (~600 líneas)
        ├── dream.js # Visualización neuronal
        └── aeon.js  # Núcleo Eón JS
```

## API Endpoints

### Chat y Conversación
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/chat` | POST | Enviar mensaje |
| `/api/history` | GET/DELETE | Historial de chat |
| `/api/personality` | GET/POST | Estilo de respuesta |

### Generación de Imágenes
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/generate-image` | POST | Generar arte neuronal |

**Estilos disponibles**: fractal, flow, particles, waves, neural  
**Paletas**: cosmic, ocean, forest, sunset, aurora, fire, ice, matrix, vintage, neon, pastel, monochrome

### Sistema de Aprendizaje (v1.4)
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/feedback` | POST | Enviar 👍/👎 |
| `/api/learning-stats` | GET | Estadísticas de aprendizaje |
| `/api/memory` | GET/DELETE | Memoria a largo plazo |
| `/api/consolidate` | POST | Forzar consolidación |

### Estado y Configuración
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/status` | GET | Estado de Eón |
| `/api/config` | GET/POST | Configuración de IA |
| `/api/stats` | GET | Estadísticas de uso |
| `/api/genesis` | GET | Momento Cero |
| `/api/lm-status` | GET | Estado de TinyLMv2 |

## Sistema de Aprendizaje Continuo

### Componentes

1. **OnlineLearner**: Actualización en tiempo real de W_out
2. **LongTermMemory**: Almacena usuarios conocidos y hechos
3. **FeedbackSystem**: Valoración de respuestas
4. **ConsolidationEngine**: Optimización durante inactividad

### Ejemplo de uso

```bash
# Ver estadísticas de aprendizaje
curl http://localhost:5000/api/learning-stats

# Enviar feedback positivo
curl -X POST http://localhost:5000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{"message_id": 123, "feedback": "positive"}'

# Forzar consolidación
curl -X POST http://localhost:5000/api/consolidate
```

## Chat System

17 categorías de intención:
- identity, greeting, image, code, philosophy, memory
- help, capabilities, emotion, farewell, weather, time
- learning, feedback, config, joke, question, default

## Interfaz

La interfaz incluye 4 paneles:
- **Chat**: Conversación con Eón
- **Dream**: Visualización del reservorio neuronal
- **Learning**: Panel de aprendizaje continuo
- **Config**: Configuración de IA y personalidad

---

*v1.4.0 - 2024-12-08*
