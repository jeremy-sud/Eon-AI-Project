# Benchmarks de Energía y Eficiencia

Este documento detalla el análisis de consumo energético y uso de recursos del Motor Eón.

## Benchmark Integral v2.2

Ejecutar con:
```bash
cd phase1-foundations/python
python benchmark.py --quick   # Modo rápido (~30s)
python benchmark.py           # Modo completo (~2min)
python benchmark.py --export  # Exportar a JSON
```

## 1. Tamaño del Reservoir

| Neuronas | MSE        | Memoria    | Train (ms) | Predict (ms) |
|----------|------------|------------|------------|--------------|
| 10       | 0.000498   | 1.02 KB    | 32.3       | 16.5         |
| 25       | 0.000568   | 5.47 KB    | 29.0       | 11.9         |
| **50**   | **0.000317** | **20.70 KB** | 25.8    | 12.2         |
| 75       | 0.000427   | 45.70 KB   | 26.7       | 12.1         |
| 100      | 0.000369   | 80.47 KB   | 81.6       | 32.1         |
| 150      | 0.000427   | 179.30 KB  | 101.9      | 31.8         |
| 200      | 0.000365   | 317.19 KB  | 253.8      | 32.5         |

**Hallazgo**: 50 neuronas logran MSE 0.000317 con solo 20.70 KB - comparable a modelos 4x más grandes.

## 2. Cuantización

| Precisión      | MSE        | Memoria (KB) | Precisión (%) | Compresión |
|----------------|------------|--------------|---------------|------------|
| float64 (base) | 0.000369   | 80.47        | 100.0%        | 1.0x       |
| **8-bit**      | 0.000543   | 9.96         | **52.9%**     | **8.1x**   |
| 4-bit          | 0.691686   | 4.98         | 0.0%          | 16.2x      |
| binario (1-bit)| 1.215819   | 1.25         | 0.0%          | 64.6x      |

**Hallazgo**: Cuantización 8-bit retiene rendimiento aceptable con 8x menos memoria.

## 3. Plasticidad Hebbiana

| Modelo              | MSE        | Adaptaciones |
|---------------------|------------|--------------|
| ESN Estándar        | 0.000356   | 0            |
| ESN + Hebbian       | 0.062474   | 2999         |
| **ESN + Anti-Hebbian** | **0.000057** | **2999** |

**Hallazgo**: Anti-Hebbian logra 6x mejor MSE que el estándar con aprendizaje continuo sin reentrenamiento.

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

## 6. Motor ESN Optimizado (v1.9.2)

### Nuevas Características
| Característica            | Descripción                                      | Impacto           |
|---------------------------|--------------------------------------------------|-------------------|
| **Leaky Integration**     | Parámetro `leak_rate` para integración suave     | +Estabilidad      |
| **Ridge Optimizado**      | `np.linalg.solve()` vs inversión directa         | **3x más rápido** |
| **Validación Parámetros** | Verificación en `__init__`                       | +Robustez         |
| **Estabilidad Numérica**  | Detección NaN/Inf antes de fallo                 | +Confiabilidad    |
| **Radio Espectral O(n²)** | Power iteration vs eigenvalores O(n³)            | +Eficiencia       |

### Módulo utils/matrix_init.py
| Función                    | Propósito                              |
|----------------------------|----------------------------------------|
| `generate_birth_hash()`    | Hash portable sin dependencia de SO    |
| `compute_spectral_radius()`| Cálculo eficiente O(n²)               |
| `create_reservoir_matrix()`| Matriz de reservoir centralizada       |
| `validate_esn_parameters()`| Validación de parámetros ESN           |
| `validate_training_data()` | Verificación dimensiones X, y          |
| `check_numerical_stability()`| Detección de NaN/Inf                 |
| `ridge_regression()`       | Regresión ridge optimizada             |

## 7. Tests de Regresión

| Suite                        | Tests | Estado | Cobertura                          |
|------------------------------|-------|--------|------------------------------------|
| test_discovery_paradigm.py   | 30    | ✅     | Core ESN, Genesis, Quantizer       |
| test_engine_improvements.py  | 34    | ✅     | Utils, validación, optimizaciones  |
| test_mystical_modules.py     | 28    | ✅     | Tzimtzum, Alquimia, Fractal        |
| **Total**                    | **92**| **✅** | **0.23s**                          |

## Metodología

- **Plataforma**: Python 3.13 + NumPy (default_rng)
- **Tarea**: Predicción Mackey-Glass (τ=17)
- **Series de datos**: 3000 puntos (70% train, 30% test)
- **Hardware simulado**: ARM Cortex-M4F equivalente
- **Motor ESN**: v1.9.2 con leaky integration y ridge optimizado

## Conclusión

Eón es la solución óptima cuando se requiere:

1.  **Eficiencia Extrema** - 50 neuronas logran MSE 0.000317 con 20.70 KB
2.  **Aprendizaje Continuo** - Anti-Hebbian logra 6x mejor MSE sin reentrenamiento
3.  **Cuantización Efectiva** - 8-bit reduce 8x memoria manteniendo utilidad
4.  **Motor Optimizado** (v1.9.2) - Ridge 3x más rápido, validación robusta
5.  **Arquitecturas Místicas** - Tzimtzum, Alquimia, Fractal
6.  **92 tests automatizados** garantizando calidad en 0.23s

---

*Última actualización: 2025-12-10 (v2.2)*
