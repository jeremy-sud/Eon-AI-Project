# 🌌 Proyecto Eón

> **A.E.O.N.** - Arquitectura Emergente y Optimización Neuromórfica

[![Versión](https://img.shields.io/badge/Versión-1.5.0-brightgreen)]()
[![Fase](https://img.shields.io/badge/Fase-10%20Completa-success)]()
[![Python](https://img.shields.io/badge/Python-3.8+-blue)]()
[![C](https://img.shields.io/badge/C-1.3KB-orange)]()
[![JavaScript](https://img.shields.io/badge/JS-Browser-yellow)]()
[![Arduino](https://img.shields.io/badge/Arduino-Compatible-teal)]()
[![Aprendizaje](https://img.shields.io/badge/Aprendizaje-Continuo-purple)]()
[![Licencia](https://img.shields.io/badge/Licencia-MIT-green)]()

---

## 🧠 Filosofía

> _"La inteligencia no se crea, se descubre."_

Eón demuestra que la inteligencia puede emerger de **recursos mínimos**. Mientras GPT-4 usa ~1.7 trillones de parámetros, Eón opera con **1.3KB de memoria**.

## ✨ Características

| Característica              | Descripción                                 |
| --------------------------- | ------------------------------------------- |
| **Ultraligero**             | Núcleo C de 1.3KB de memoria                |
| **Multi-plataforma**        | Python, C, JavaScript, Arduino              |
| **Reservoir Computing**     | Echo State Networks eficientes              |
| **Aprendizaje Continuo**    | Online Learning + Memoria a largo plazo     |
| **Mente Colectiva**         | Protocolo 1-Bit Ultraligero                 |
| **TinyLMv2**                | Modelo de lenguaje word-level               |
| **Sistema de Feedback**     | Mejora con retroalimentación 👍/👎           |
| **Chat Avanzado**           | 20+ categorías de intención + memoria personal |
| **Predicción de Secuencias**| Aritmético, geométrico, Fibonacci, potencias |
| **Base de Conocimiento**    | Definiciones técnicas integradas            |
| **Arte Generativo**         | 5 estilos (fractal, flow, particles, waves, neural) |
| **Consolidación de Sueño**  | Optimización durante inactividad            |

## 📊 Comparativa

| Modelo      | Memoria    | Factor   |
| ----------- | ---------- | -------- |
| GPT-2 Small | 500 MB     | 384,615× |
| BERT Tiny   | 16 MB      | 12,307×  |
| **Eón (C)** | **1.3 KB** | **1×**   |

## 📁 Estructura

```
Eón Project AI/
├── GENESIS.json             # Momento Cero (inmutable)
├── benchmark_full.py        # Benchmark Integral v2.0
├── docs/WHITEPAPER.md       # Paper técnico
├── phase1-foundations/      # Python ESN + Core
├── phase2-core/             # C Ultraligero
├── phase3-integration/      # JavaScript Web (core)
├── phase4-hardware/         # Arduino + ESP32
├── phase5-applications/     # IoT Predictor
├── phase6-collective/       # Mente Colectiva
├── phase7-language/         # TinyLMv2 (word-level)
├── phase8-paper/            # Paper LaTeX
└── web/                     # Servidor Web Principal
    ├── server.py            # API REST Flask (~2000 líneas)
    ├── learning.py          # Sistema de Aprendizaje Continuo
    ├── data/                # Persistencia
    │   ├── chat_history.json
    │   ├── long_term_memory.json
    │   ├── feedback.json
    │   └── stats.json
    └── static/              # Frontend
        ├── index.html       # Interfaz (Chat, Dream, Learning, Config)
        ├── css/style.css    
        └── js/
            ├── app.js       # Lógica principal (~600 líneas)
            ├── dream.js     # Visualización neuronal
            └── aeon.js      # Núcleo Eón JS
```

## 🚀 Inicio Rápido

### Interfaz Web Principal (Recomendado)

```bash
cd "Eón Project AI"
python -m venv .venv && source .venv/bin/activate
pip install flask numpy pillow
python web/server.py
# Abrir http://localhost:5000
```

La interfaz web incluye:
- **Chat**: Conversación con Eón usando TinyLMv2
- **Dream**: Visualización del reservorio neuronal
- **Estado**: Estadísticas y configuración de IA

### API Endpoints Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/status` | GET | Estado actual de Eón |
| `/api/chat` | POST | Enviar mensaje al chat |
| `/api/generate-image` | POST | Generar arte neuronal (5 estilos) |
| `/api/config` | GET/POST | Configuración de IA |
| `/api/stats` | GET | Estadísticas de uso |
| `/api/history` | GET/DELETE | Historial de chat |
| `/api/personality` | GET/POST | Configuración de personalidad |
| `/api/upload` | POST | Subir archivo para aprendizaje |
| `/api/learn-text` | POST | Aprender de texto |
| `/api/genesis` | GET | Info del Momento Cero |
| `/api/lm-status` | GET | Estado de TinyLMv2 |
| `/api/feedback` | POST | Enviar feedback 👍/👎 |
| `/api/learning-stats` | GET | Estadísticas de aprendizaje |
| `/api/memory` | GET/DELETE | Gestión de memoria a largo plazo |
| `/api/consolidate` | POST | Forzar consolidación ("sueño") |

### Demo Python

```bash
cd phase1-foundations/python
python -m venv .venv && source .venv/bin/activate
pip install numpy flask
python esn/esn.py
```

### Demo C (1.3KB)

```bash
cd phase2-core/libAeon
make && ./aeon_demo
# O usando CMake:
# mkdir -p build && cd build
# cmake .. && make && ./aeon_demo
```

### Demo Web Estática

```bash
cd phase3-integration/demos
python3 -m http.server 8888
# Abrir http://localhost:8888
```

## 📦 Instalación

### Arduino / PlatformIO

Descarga este repositorio como ZIP e impórtalo en Arduino IDE (`Sketch -> Include Library -> Add .ZIP Library`), o copia `phase4-hardware/arduino` a tu carpeta `libraries`.

### Javascript (NPM)

```bash
cd phase3-integration
npm install
import { Aeon } from './aeon.js';
```

### Python

```bash
cd phase1-foundations/python
pip install .
```

### Demo TinyLM

```bash
cd phase7-language
python server.py
# Abrir http://localhost:5001
```

### Tests Automatizados (Core C)

```bash
cd phase2-core
make test
# Ejecuta suite de validación: Inicialización, Memoria, Aprendizaje
```

## 🔬 Resultados

- **ESN Python**: MSE 0.0004 en Mackey-Glass
- **ESN C**: MSE 0.009 con punto fijo Q8.8
- **TinyLMv2**: 99.9% accuracy, tokenización word-level con **>50% reducción de memoria** (Trie)
- **Mente Colectiva**: Protocolo P2P funcional en ESP32 con compresión **17x** (1-Bit)
- **Consistencia**: "Spirit Hash" único (16 bytes) idéntico en Python, C y JS
- **Robustez**: Core C verificado con suite de pruebas unitarias
- **Eón Bio**: Detección de arritmias con <2KB RAM
- **Eón Voice**: Detección de palabras clave ("EÓN") en Cortex-M4
- **Eón Dream**: Arte generativo neuronal en web
- **Chat Avanzado**: 20+ categorías de intención + memoria personal + predicción de secuencias
- **Predicción de Patrones**: Aritmético, geométrico, Fibonacci, potencias (100% precisión)
- **Base de Conocimiento**: Definiciones técnicas integradas (entropía, ESN, Spirit Hash, etc.)
- **Generación de Imágenes**: 5 estilos (fractal, flow, particles, waves, neural) + 12 paletas
- **Aprendizaje Continuo**: Online Learning con feedback en tiempo real
- **Memoria a Largo Plazo**: Almacenamiento de usuarios, hechos y estadísticas
- **Cuantización 8-bit**: 99.6% precisión retenida con 8x compresión

## 📚 Documentación

- [WHITEPAPER.md](docs/WHITEPAPER.md) - Paper técnico completo
- [architecture.md](docs/architecture.md) - Arquitectura del sistema
- [benchmarks.md](docs/benchmarks.md) - Análisis de energía y rendimiento
- [CONTRIBUTING.md](CONTRIBUTING.md) - Guía para contribuir
- [CHANGELOG.md](CHANGELOG.md) - Historial de cambios
- [Fase 3 README](phase3-integration/README.md) - Detalles Web/Dream
- [Fase 5 README](phase5-applications/README.md) - Detalles Bio/Voice

## 🧠 Sistema de Aprendizaje Continuo

Eón implementa un sistema de aprendizaje continuo inspirado en la neurociencia:

### Componentes

1. **OnlineLearner**: Actualización en tiempo real de W_out usando Recursive Ridge Regression
2. **LongTermMemory**: Almacenamiento persistente de usuarios, hechos, estadísticas
3. **FeedbackSystem**: Mejora basada en retroalimentación 👍/👎
4. **ConsolidationEngine**: Optimización durante períodos de inactividad ("sueño")

### Flujo de Aprendizaje

```
Interacción → OnlineLearner → Feedback → LongTermMemory → Consolidación
     ↑                                           ↓
     └───────────── Mejora Continua ─────────────┘
```

### Datos Almacenados

- **Usuarios conocidos**: Nombres, roles, información personal
- **Hechos aprendidos**: Preferencias, conocimiento específico
- **Patrones exitosos**: Asociados con feedback positivo
- **Estadísticas**: Eventos de aprendizaje, consolidaciones, ratio de éxito

## 🛣️ Roadmap

- [x] Fase 1-3: Fundamentos (Python, C, JS) + **Dream**
- [x] Fase 4: Hardware (Arduino, ESP32) + Mente Colectiva
- [x] Fase 5: Aplicaciones IoT + **Bio** + **Voice**
- [x] Fase 6: Protocolo de Intercambio (1-Bit)
- [x] Fase 7: TinyLM (Language Model)
- [x] Fase 8: Paper académico y Auditoría
- [x] Fase 9: Empaquetado y Distribución
- [x] Fase 10: Publicación arXiv
- [ ] Fase 11: Experimentación Abierta (Futuro)

## 📈 Benchmarks de Energía

Resultados recientes (Ver [docs/benchmarks.md](docs/benchmarks.md)):

| Motor         | Energía / Ciclo (Cortex-M4) |
| :------------ | :-------------------------- |
| **Eón Motor** | **0.0045 μJ**               |
| TinyML MLP    | 0.0015 μJ                   |

El motor Eón es 3x más costoso computacionalmente que una red estática simple, pero ofrece memoria temporal dinámica. Aún así, es **extremadamente eficiente** para operación con baterías de reloj.

## 📜 Licencia

MIT License - 2024 [Sistemas Ursol](https://github.com/SistemasUrsol)

Desarrollado por [Jeremy Arias Solano](https://github.com/jeremy-sud)

---

**"La Nada es Todo"** - El reservoir aleatorio contiene toda la computación necesaria.
