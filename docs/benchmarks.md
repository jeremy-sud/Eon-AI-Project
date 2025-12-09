# Benchmarks de Energía y Eficiencia

Este documento detalla el análisis de consumo energético y uso de recursos del Motor Eón.

## Benchmark Integral v2.0

Ejecutar con:
```bash
python benchmark_full.py --quick  # Modo rápido (~30s)
python benchmark_full.py          # Modo completo (~2min)
python benchmark_full.py --export # Exportar a JSON
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

## 3. Plasticidad

| Modelo              | MSE      | Adaptaciones |
|---------------------|----------|--------------|
| ESN Estándar        | 0.092    | 0            |
| ESN + hebbian       | 0.087    | 500          |
| ESN + anti_hebbian  | 0.089    | 500          |

**Hallazgo**: Plasticidad Hebbiana mejora ligeramente el rendimiento.

## 4. Sistema de Aprendizaje (NUEVO)

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

## 5. Generación de Imágenes

| Estilo    | Tiempo (s) | Tamaño (KB) | Colores |
|-----------|------------|-------------|---------|
| fractal   | 0.15       | 45-60       | 12 paletas |
| flow      | 0.12       | 40-55       | 12 paletas |
| particles | 0.18       | 50-70       | 12 paletas |
| waves     | 0.10       | 35-50       | 12 paletas |
| neural    | 0.20       | 55-75       | 12 paletas |

## 6. Comparativa con TinyML

| Métrica                     | Eón Core (Reservoir) | TinyML (MLP Estático) | Diferencia   |
| :-------------------------- | :------------------- | :-------------------- | :----------- |
| **Memoria (RAM)**           | **1.3 KB**           | ~4 KB                 | **3x Menor** |
| **Memoria (Flash)**         | 4 KB                 | ~10 KB                | 2.5x Menor   |
| **Energía / Inferencia**    | 0.0045 μJ            | **0.0015 μJ**         | 3x Mayor     |
| **Capacidad Temporal**      | **SÍ**               | NO                    | N/A          |
| **Entrenamiento On-Device** | **SÍ**               | NO                    | ∞            |
| **Aprendizaje Continuo**    | **SÍ**               | NO                    | ∞            |

## Metodología

- **Plataforma**: Python 3.13 + simulación Cortex-M4F
- **Tarea**: Predicción Mackey-Glass
- **Series de datos**: 3000 puntos (70% train, 30% test)

## Conclusión

Eón es la solución óptima cuando se requiere:

1.  **Aprendizaje Continuo** en el borde (OnlineLearner + Feedback)
2.  **Procesamiento de Series Temporales** (contexto histórico)
3.  **Restricciones extremas de RAM** (< 2KB)
4.  **Cuantización 8-bit** sin pérdida significativa (99.6% precisión)
5.  **Memoria persistente** de usuarios y hechos

---

*Última actualización: 2024-12-08 (v2.0)*
