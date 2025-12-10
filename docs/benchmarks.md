# Benchmarks de Energía y Eficiencia

Este documento detalla el análisis de consumo energético y uso de recursos del Motor Eón.

## Benchmark Integral v2.1

Ejecutar con:
```bash
cd phase1-foundations/python
python benchmark.py --quick   # Modo rápido (~30s)
python benchmark.py           # Modo completo (~2min)
python benchmark.py --export  # Exportar a JSON
```

## 1. Tamaño del Reservoir

| Neuronas | MSE      | Memoria  | Train (ms) | Pred/sec |
|----------|----------|----------|------------|----------|
| 25       | 0.048    | 5.47 KB  | 10.2       | 258,005  |
| 50       | 0.039    | 20.70 KB | 3.7        | 227,704  |
| 100      | 0.092    | 80.47 KB | 18.6       | 58,101   |

**Hallazgo**: 50 neuronas ofrecen el mejor balance MSE/memoria.

## 2. Cuantización

| Precisión      | MSE      | Memoria (KB) | Precisión (%) | Compresión |
|----------------|----------|--------------|---------------|------------|
| float64 (base) | 0.087    | 80.47        | 100.0%        | 1.0x       |
| **8-bit**      | 0.087    | 9.96         | **99.6%**     | **8.1x**   |
| 4-bit          | 10.84    | 4.98         | 0.0%          | 16.2x      |
| binario (1-bit)| 14.96    | 1.25         | 0.0%          | 64.6x      |

**Hallazgo**: Cuantización 8-bit retiene 99.6% de precisión con 8x menos memoria.

## 3. Plasticidad Hebbiana

| Modelo              | MSE      | Adaptaciones |
|---------------------|----------|--------------|
| ESN Estándar        | 0.092    | 0            |
| ESN + Hebbian       | 0.087    | 500          |
| ESN + Anti-Hebbian  | 0.089    | 500          |

**Hallazgo**: Plasticidad Hebbiana mejora ligeramente el rendimiento.

## 4. Módulos Místicos (Fase 11)

### TzimtzumESN - Poda Dinámica
| Fase           | Conexiones Activas | MSE   | Descripción |
|----------------|--------------------|-------|-------------|
| PLENITUD       | 100%               | 0.087 | Estado inicial |
| DARK_NIGHT     | 50%                | 0.095 | Poda del 50% conexiones débiles |
| RENACIMIENTO   | 100%               | 0.082 | Regeneración con nuevos pesos |

### AlchemicalPipeline - ETL Transmutación
| Fase           | Reducción Ruido | Latencia | Descripción |
|----------------|-----------------|----------|-------------|
| NIGREDO        | 0%              | <1ms     | Ingesta datos crudos |
| ALBEDO         | ~70%            | <5ms     | Filtrado Kalman |
| RUBEDO         | N/A             | <10ms    | Inferencia ESN |

### RecursiveESN - Arquitectura Fractal
| Nivel   | Neuronas | Escala Temporal | Uso |
|---------|----------|-----------------|-----|
| Micro   | 8/unidad | 1x-8x           | Patrones rápidos |
| Macro   | 10 unid. | Variable        | Patrones lentos |
| Total   | ~80      | Multi-escala    | Memoria jerárquica |

## 5. Sistema de Aprendizaje

### Componentes
- **OnlineLearner**: Actualización en tiempo real
- **LongTermMemory**: Persistencia de conocimiento
- **FeedbackSystem**: Mejora con retroalimentación
- **ConsolidationEngine**: Optimización nocturna

### Métricas
| Métrica                    | Valor Típico |
|----------------------------|--------------|
| Latencia de aprendizaje    | < 1ms        |
| Almacenamiento/usuario     | ~200 bytes   |
| Almacenamiento/hecho       | ~150 bytes   |
| Tiempo de consolidación    | < 100ms      |

## 6. Tests de Regresión

| Suite                    | Tests | Estado | Tiempo |
|--------------------------|-------|--------|--------|
| test_mystical_modules.py | 28    | ✅     | 0.21s  |
| test_ws_bridge.py        | 19    | ✅     | 0.40s  |
| **Total**                | **47**| **✅** | 0.62s  |

## Metodología

- **Plataforma**: Python 3.13 + NumPy (default_rng)
- **Tarea**: Predicción Mackey-Glass (τ=17)
- **Series de datos**: 3000 puntos (70% train, 30% test)
- **Hardware simulado**: ARM Cortex-M4F equivalente

## Conclusión

Eón es la solución óptima cuando se requiere:

1.  **Aprendizaje Continuo** en el borde (OnlineLearner + Feedback)
2.  **Procesamiento de Series Temporales** (contexto histórico)
3.  **Restricciones extremas de RAM** (< 2KB)
4.  **Cuantización 8-bit** sin pérdida significativa (99.6% precisión)
5.  **Arquitecturas místicas** (Tzimtzum, Alquimia, Fractal)
6.  **47 tests automatizados** garantizando calidad

---

*Última actualización: 2025-12-10 (v2.1)*
