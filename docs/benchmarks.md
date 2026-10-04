# Benchmarks de Energía y Eficiencia

Este documento detalla el análisis de consumo energético y uso de recursos del Motor Eón.

## Benchmark Integral (Actual)

Ejecutar con:
```bash
python benchmark_full.py --quick     # Modo rápido
python benchmark_full.py             # Modo completo
python benchmark_full.py --export results.json
```

> Nota: `benchmark_full.py` en la raíz es el benchmark integral actual. El archivo `phase1-foundations/python/benchmark.py` se mantiene como benchmark legacy del núcleo ESN.

---

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

**Hallazgo**: 50 neuronas logran MSE 0.000317 con solo 20.70 KB — comparable a modelos 4x más grandes.

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

## 4. Módulos de Poda y Pipeline Avanzados

### Poda Dinámica (Pruning/Regrowth Cycle)
| Fase           | Conexiones Activas | MSE   | Descripción |
|----------------|--------------------|-------|-------------|
| FULL           | 100%               | 0.087 | Estado inicial, todas las conexiones |
| PRUNE          | 50%                | 0.095 | Poda del 50% conexiones con menor magnitud |
| REGROW         | 100%               | 0.082 | Regeneración con nuevos pesos aleatorios |

> **Implicación edge:** La poda dinámica permite reducir computación en períodos de baja energía y restaurar capacidad cuando hay alimentación estable.

### Pipeline ETL Multinivel
| Fase           | Reducción Ruido | Latencia | Descripción |
|----------------|-----------------|----------|-------------|
| INGESTA        | 0%              | <1ms     | Ingesta de datos crudos del sensor |
| FILTRADO       | ~70%            | <5ms     | Filtrado Kalman (suavizado online) |
| INFERENCIA     | N/A             | <10ms    | Inferencia ESN sobre datos filtrados |

### ESN Recursivo — Arquitectura Multi-Escala
| Nivel   | Neuronas | Escala Temporal | Uso |
|---------|----------|-----------------|-----|
| Micro   | 8/unidad | 1x-8x           | Patrones rápidos (vibración, audio) |
| Macro   | 10 unid. | Variable        | Patrones lentos (temperatura, tendencias) |
| Total   | ~80      | Multi-escala    | Memoria jerárquica para señales mixtas |

---

## 5. Energía Total por Ciclo Completo (NUEVO)

### 5.1 Desglose por Operación (ARM Cortex-M4F @ 80MHz, N=50)

| Operación | MACs | Tiempo (μs) | Energía (μJ) |
|-----------|------|-------------|---------------|
| Update estado x(t) | 2,550 | 31.9 | 0.00160 |
| Readout y(t) | 52 | 0.65 | 0.00003 |
| Online Learning (1 paso) | 2,500 | 31.3 | 0.00156 |
| Cuantización 1-bit | 50 | 0.63 | 0.00003 |
| **Total ciclo (con learning)** | **5,152** | **64.4** | **0.00322** |
| **Total ciclo (solo inferencia)** | **2,602** | **32.5** | **0.00163** |

### 5.2 Comparativa con Frameworks Edge

| Framework | μJ/Inferencia | Entrena on-device | Memoria temporal |
|-----------|---------------|-------------------|------------------|
| CMSIS-NN (optimizado ARM) | 0.001 | ❌ | ❌ |
| TinyML MLP (estático) | 0.0015 | ❌ | ❌ |
| **Eón (solo inferencia)** | **0.0016** | **✅** | **✅** |
| **Eón (ciclo completo)** | **0.0032** | **✅** | **✅** |

> **Nota:** Eón con solo inferencia es competitivo con TinyML MLP, pero agrega memoria temporal inherente. El ciclo completo (con learning) es 2x el costo, pero es el **único framework que permite adaptación on-device**.

### 5.3 Estimación de Vida de Batería

**Supuestos:** 1 ciclo/segundo, deep sleep entre ciclos.

| Batería | Capacidad (J) | Solo Inferencia | Ciclo Completo | Con LoRa (1 TX/min) |
|---------|---------------|-----------------|----------------|----------------------|
| CR2032 (3V, 225mAh) | 2,430 | ~760 días | ~380 días | ~6.5 días |
| 2×AA (3V, 2500mAh) | 27,000 | ~23 años* | ~11.5 años* | ~72 días |
| LiPo 500mAh (3.7V) | 6,660 | ~5.7 años* | ~2.8 años* | ~14 días |
| CR2477 (3V, 1000mAh) | 10,800 | ~9.5 años* | ~4.7 años* | ~29 días |

*Teórico, asumiendo deep sleep dominante y auto-descarga despreciable.

> **Observación clave:** En aplicaciones edge, la radio (LoRa/WiFi) domina el consumo. La eficiencia del protocolo 1-Bit (21 bytes vs 175 bytes) reduce el tiempo de aire LoRa en 2.6×, extendiendo proporcionalmente la vida de batería.

### 5.4 Desglose por Modo de Operación

| Modo | Corriente (mA) | Potencia (mW) | Proporción del presupuesto |
|------|----------------|---------------|---------------------------|
| Deep Sleep | 0.01 | 0.037 | Dominante (>99% del tiempo) |
| Idle (WiFi off) | 10 | 37 | Despreciable |
| CPU activo (ESN) | 50 | 185 | <0.01% del tiempo |
| LoRa RX | 15 | 55.5 | Variable |
| LoRa TX @17dBm | 85 | 314 | Pico de consumo |
| LoRa TX @20dBm | 120 | 444 | Máximo consumo |

---

## 6. Sistema de Aprendizaje

### Componentes
- **OnlineLearner**: Actualización en tiempo real (Recursive Ridge)
- **LongTermMemory**: Persistencia de conocimiento (JSON)
- **FeedbackSystem**: Mejora con retroalimentación (👍/👎)
- **ConsolidationEngine**: Optimización durante inactividad

### Métricas
| Métrica                    | Valor Típico |
|----------------------------|--------------| 
| Latencia de aprendizaje    | < 1ms        |
| Almacenamiento/usuario     | ~200 bytes   |
| Almacenamiento/hecho       | ~150 bytes   |
| Tiempo de consolidación    | < 100ms      |

## 7. Motor ESN Optimizado (v1.9.2)

### Características
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

## 8. Tests de Regresión

| Suite                        | Tests | Estado | Cobertura                          |
|------------------------------|-------|--------|------------------------------------| 
| test_discovery_paradigm.py   | 30    | ✅     | Core ESN, Genesis, Quantizer       |
| test_engine_improvements.py  | 34    | ✅     | Utils, validación, optimizaciones  |
| test_advanced_modules.py     | 28    | ✅     | Poda dinámica, Pipeline, Multi-escala |
| **Subtotal Core Regresión**  | **92**| **✅** | **0.23s**                          |
| **Total Ecosistema (v2.4.0)**| **720**| **✅** | **~6m (con excavación y sim.)**    |

## Metodología

- **Plataforma**: Python 3.13 + NumPy (default_rng)
- **Tarea**: Predicción Mackey-Glass (τ=17)
- **Series de datos**: 3000 puntos (70% train, 30% test)
- **Hardware simulado**: ARM Cortex-M4F equivalente
- **Motor ESN**: v1.9.2 con leaky integration y ridge optimizado

## Fórmulas Clave

Para la formalización matemática completa, consultar [MATHEMATICS.md](MATHEMATICS.md).

### Energía por inferencia:
```
E_inference = P_cpu × (N_MACs / f_clock)
```

### Energía por transmisión LoRa:
```
E_tx = P_tx × T_air(payload_bytes, SF, BW, CR)
```

### Compresión del protocolo 1-Bit:
```
Ratio = payload_JSON / (header + ⌈N/8⌉)
     = 175 / (14 + 7) = 8.3×
```

## Conclusión

Eón es la solución óptima cuando se requiere:

1.  **Eficiencia Extrema** — 50 neuronas logran MSE 0.000317 con 20.70 KB
2.  **Aprendizaje Continuo** — Anti-Hebbian logra 6x mejor MSE sin reentrenamiento
3.  **Cuantización Efectiva** — 8-bit reduce 8x memoria manteniendo utilidad
4.  **Motor Optimizado** (v1.9.2) — Ridge 3x más rápido, validación robusta
5.  **Ciclo completo eficiente** — Update + Predict + Learn en 64.4 μs y 0.0032 μJ
6.  **Vida de batería prolongada** — Meses con CR2032, años con baterías AA
7.  **720 tests automatizados** garantizando calidad y estabilidad global

---

*Última actualización: 2026-10-04 (v2.4.1)*
