# 🚀 Guía Rápida - Integraciones v2.2.0

## TinyAttention en TinyLMv2

```python
from phase7_language.tiny_lm_v2 import TinyLMv2

# Crear modelo CON atención
model = TinyLMv2(
    input_size=64,
    hidden_size=128,
    use_attention=True,        # ← Habilitar atención
    attention_window=256        # ← Tamaño de ventana
)

# Generar texto
output = model.generate(
    input_tokens,
    use_attention=True           # ← Usar atención en generación
)
```

**Key Points**:
- `use_attention` default: `False` (backward compatible)
- Overhead de memoria: < 2%
- Ventana de atención ajustable según disponibilidad

---

## SeedArchaeologist en GeneticMiner

```python
from core.genetic_miner import GeneticMiner
from core.universal_miner import SeedVault, UniversalMiner

# Setup
vault = SeedVault()
miner = UniversalMiner(reservoir_size=50)

def fitness(seed):
    result = miner.excavate(starting_seed=seed, max_attempts=1)
    return result.resonance

# OPCIÓN 1: Evolución estándar (aleatoria)
basic = GeneticMiner(population_size=50, generations=30)
result1 = basic.evolve(fitness)

# OPCIÓN 2: Evolución inteligente (con archaeologist)
smart = GeneticMiner(
    population_size=50,
    generations=30,
    use_archaeologist=True,      # ← Activar análisis
    fertile_bias=0.8,             # ← 80% de pop en regiones fértiles
    archaeologist_samples=1000    # ← Muestras para mapeo
)
result2 = smart.evolve(fitness, vault)  # ← Pasar vault

# Obtener estadísticas
stats = smart.archaeologist_stats()
print(f"Regiones fértiles: {stats['fertile_regions_found']}")
```

**Key Points**:
- `use_archaeologist` default: `False` (backward compatible)
- `fertile_bias`: 0.0-1.0 (qué porcentaje en regiones fértiles)
- `archaeologist_samples`: más alto = mejor mapeo pero más lento
- Aceleración: ~1.5-2x más rápido para convergencia

---

## 📚 Documentación Completa

| Archivo | Descripción |
|---------|-------------|
| [ROADMAP_IDEAS.md](./ROADMAP_IDEAS.md) | Todas las ideas y su estado |
| [INTEGRATION_STATUS.md](./INTEGRATION_STATUS.md) | Estado detallado de integraciones |
| [DOCUMENTATION_UPDATE_SUMMARY.md](./DOCUMENTATION_UPDATE_SUMMARY.md) | Resumen de cambios |
| [../CHANGELOG.md](../CHANGELOG.md) | Historia de versiones |

---

## 🧪 Ejecutar Tests

```bash
# Tests de TinyLMv2 (en phase7-language)
python -m pytest tests/test_tiny_lm_v2.py -v

# Tests de GeneticMiner (en phase1-foundations/python)
python -m pytest tests/test_genetic_miner.py -v

# Todos los tests del proyecto
python -m pytest tests/ --tb=short
```

---

## ❓ FAQ

**P: ¿Es backward compatible?**  
R: Sí, ambas integraciones usan parámetros opcionales default a False.

**P: ¿Qué impacto en memoria tiene?**  
R: TinyAttention <2%, GeneticMiner negligible (usa arrays numpy).

**P: ¿Dónde empiezo?**  
R: Lee [INTEGRATION_STATUS.md](./INTEGRATION_STATUS.md) para contexto.

**P: ¿Cómo contribuyo con nuevas integraciones?**  
R: Sigue el patrón: imports opcionales → parámetros opcionales → tests.

---

*Última actualización: 2024-01-15*
