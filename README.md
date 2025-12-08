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

| Característica          | Descripción                    |
| ----------------------- | ------------------------------ |
| **Ultraligero**         | Núcleo C de 1.3KB de memoria   |
| **Multi-plataforma**    | Python, C, JavaScript, Arduino |
| **Reservoir Computing** | Echo State Networks eficientes |
| **Mente Colectiva**     | Protocolo 1-Bit Ultraligero    |
| **TinyLM**              | Diccionario Trie Optimizado    |

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
# O usando CMake:
# mkdir -p build && cd build
# cmake .. && make && ./aeon_demo
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

### Tests Automatizados (Core C)

```bash
cd phase2-core
make test
# Ejecuta suite de validación: Inicialización, Memoria, Aprendizaje
```

## 🔬 Resultados

- **ESN Python**: MSE 0.0004 en Mackey-Glass
- **ESN C**: MSE 0.009 con punto fijo Q8.8
- **TinyLM v2**: 99.9% accuracy con **>50% reducción de memoria** (Trie).
- **Mente Colectiva**: Protocolo P2P funcional en ESP32 con compresión **17x** (1-Bit).
- **Consistencia**: "Spirit Hash" único (16 bytes) idéntico en Python, C y JS.
- **Robustez**: Core C verificado con suite de pruebas unitarias.

## 📚 Documentación

- [WHITEPAPER.md](docs/WHITEPAPER.md) - Paper técnico completo
- [audit_report.md](docs/audit_report.md) - Auditoría de código y mejoras
- [benchmarks.md](docs/benchmarks.md) - Análisis de energía
- [CONTRIBUTING.md](CONTRIBUTING.md) - Guía para contribuir
- [CHANGELOG.md](CHANGELOG.md) - Historial de cambios

## 🛣️ Roadmap

- [x] Fase 1-3: Fundamentos (Python, C, JS)
- [x] Fase 4: Hardware (Arduino, ESP32) + Mente Colectiva
- [x] Fase 5: Aplicaciones IoT
- [x] Fase 6: Protocolo de Intercambio (1-Bit)
- [x] Fase 7: TinyLM (Language Model)
- [x] Fase 8: Paper académico y Auditoría
- [ ] Fase 9: Experimentación Abierta y Descubrimiento
- [ ] Fase 10: Publicación arXiv

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
