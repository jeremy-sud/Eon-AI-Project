# 🌌 Proyecto Eón

> **A.E.O.N.** - Arquitectura Emergente y Optimización Neuromórfica

[![Fase](https://img.shields.io/badge/Fase-8%20Completa-success)]()
[![Python](https://img.shields.io/badge/Python-3.8+-blue)]()
[![C](https://img.shields.io/badge/C-1.3KB-orange)]()
[![JavaScript](https://img.shields.io/badge/JS-Browser-yellow)]()
[![Arduino](https://img.shields.io/badge/Arduino-Compatible-teal)]()
[![Licencia](https://img.shields.io/badge/Licencia-MIT-green)]()

---

## 🧠 Filosofía

> _"La inteligencia no se crea, se descubre."_

Eón demuestra que la inteligencia puede emerger de **recursos mínimos**. Mientras GPT-4 usa ~1.7 trillones de parámetros, Eón opera con **1.3KB de memoria**.

## ✨ Características

| Característica          | Descripción                      |
| ----------------------- | -------------------------------- |
| **Ultraligero**         | Núcleo C de 1.3KB de memoria     |
| **Multi-plataforma**    | Python, C, JavaScript, Arduino   |
| **Reservoir Computing** | Echo State Networks eficientes   |
| **Mente Colectiva**     | Aprendizaje federado entre nodos |
| **TinyLM**              | Generación de texto minimalista  |

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
├── docs/WHITEPAPER.md       # Paper técnico
├── phase1-foundations/      # Python ESN
├── phase2-core/             # C Ultraligero
├── phase3-integration/      # JavaScript Web
├── phase4-hardware/         # Arduino + ESP32
├── phase5-applications/     # IoT Predictor
├── phase6-collective/       # Mente Colectiva
├── phase7-language/         # TinyLM v2
└── phase8-paper/            # Paper LaTeX
```

## 🚀 Inicio Rápido

### Demo Python

```bash
cd phase1-foundations/python
python -m venv venv && source venv/bin/activate
pip install numpy flask
python esn/esn.py
```

### Demo C (1.3KB)

```bash
cd phase2-core/libAeon
make && ./aeon_demo
```

### Demo Web

```bash
cd phase3-integration/demos
python3 -m http.server 8888
# Abrir http://localhost:8888
```

### Demo TinyLM

```bash
cd phase7-language
python server.py
# Abrir http://localhost:5001
```

## 🔬 Resultados

- **ESN Python**: MSE 0.0004 en Mackey-Glass
- **ESN C**: MSE 0.009 con punto fijo Q8.8
- **TinyLM v2**: 99.9% accuracy en predicción de palabras
- **Arduino**: ~500 bytes RAM para 16 neuronas

## 📚 Documentación

- [WHITEPAPER.md](docs/WHITEPAPER.md) - Paper técnico completo
- [CONTRIBUTING.md](CONTRIBUTING.md) - Guía para contribuir
- [CHANGELOG.md](CHANGELOG.md) - Historial de cambios

## 🛣️ Roadmap

- [x] Fase 1-3: Fundamentos (Python, C, JS)
- [x] Fase 4: Hardware (Arduino, ESP32)
- [x] Fase 5: Aplicaciones IoT
- [x] Fase 6: Mente Colectiva
- [x] Fase 7: TinyLM
- [x] Fase 8: Paper académico
- [ ] Fase 9: RAG o LLM pequeño integrado
- [ ] Fase 10: Publicación arXiv

## 📜 Licencia

MIT License - 2024 [Sistemas Ursol](https://github.com/SistemasUrsol)

Desarrollado por [Jeremy Arias Solano](https://github.com/jeremy-sud)

---

**"La Nada es Todo"** - El reservoir aleatorio contiene toda la computación necesaria.
