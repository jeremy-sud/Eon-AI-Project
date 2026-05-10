# Contribuir a Proyecto Eón

¡Gracias por tu interés en contribuir! Este documento explica cómo hacerlo.

## 🎯 Filosofía del Proyecto

> _"La inteligencia no se crea, se descubre."_

Eón busca demostrar que la inteligencia puede emerger de recursos mínimos. Al contribuir, mantén estos principios:

1. **Eficiencia sobre features**: Menos código, menos memoria, más impacto
2. **Simplicidad**: Si no puedes explicarlo simplemente, es demasiado complejo
3. **Reproducibilidad**: Todo debe ser verificable

## 🔧 Cómo Contribuir

### 1. Reportar Bugs

Abre un issue con:

- Descripción clara del problema
- Pasos para reproducir
- Comportamiento esperado vs actual
- Entorno (OS, versión Python/GCC)

### 2. Proponer Features

Antes de implementar:

1. Abre un issue para discutir
2. Espera feedback del mantenedor
3. Considera el impacto en memoria/rendimiento

### 3. Pull Requests

```bash
# Fork y clone
git clone https://github.com/tu-usuario/eon-project.git

# Crear rama
git checkout -b feature/tu-feature

# Hacer cambios y commit
git commit -m "feat: descripción concisa"

# Push y crear PR
git push origin feature/tu-feature
```

## 📐 Estándares de Código

### Python

- PEP 8
- Docstrings en funciones públicas
- Type hints cuando sea posible
- Solo NumPy como dependencia

### C

- C99 estándar
- Comentarios Doxygen
- Variables con prefijo `aeon_`
- Sin warnings con `-Wall -Wextra`

### JavaScript

- ES6+
- JSDoc para documentación
- Sin dependencias externas

## 🧪 Tests

Antes de enviar PR:

```bash
# Python
cd phase1-foundations/python
python esn/esn.py
python quantization/quantizer.py
python core/genesis.py

# C
cd phase2-core/libAeon
make clean && make run
```

## 📊 Benchmarks

Si tu cambio afecta rendimiento:

1. Ejecuta `benchmark_full.py` antes y después (benchmark integral actual)
2. Si trabajas solo con el núcleo ESN, también puedes usar `phase1-foundations/python/benchmark.py`
3. Incluye resultados en el PR
4. Justifica cualquier degradación

## 📝 Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Nueva funcionalidad
- `fix:` Corrección de bug
- `docs:` Documentación
- `perf:` Mejora de rendimiento
- `refactor:` Refactorización sin cambio funcional

## 📜 Licencia

Al contribuir, aceptas que tu código será licenciado bajo MIT.

---

**Proyecto Eón** - [SenseLab](https://github.com/SenseLab-dev)

**SenseLab - Build with Sense**
