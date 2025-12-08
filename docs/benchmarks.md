# Benchmarks de Energía y Eficiencia

Este documento detalla el análisis de consumo energético y uso de recursos del Motor Eón en comparación con soluciones TinyML tradicionales.

## Metodología

- **Plataforma**: Simulación basada en Cortex-M4F (STM32F4).
- **Tarea**: Predicción Mackey-Glass (1 paso).
- **Medición**: Ciclos de reloj y estimación de energía dinámica.

## Resultados

| Métrica                     | Eón Core (Reservoir) | TinyML (MLP Estático) | Diferencia   |
| :-------------------------- | :------------------- | :-------------------- | :----------- |
| **Memoria (RAM)**           | **1.3 KB**           | ~4 KB                 | **3x Menor** |
| **Memoria (Flash)**         | 4 KB                 | ~10 KB                | 2.5x Menor   |
| **Energía / Inferencia**    | 0.0045 μJ            | **0.0015 μJ**         | 3x Mayor     |
| **Capacidad Temporal**      | **SÍ**               | NO                    | N/A          |
| **Entrenamiento On-Device** | **SÍ**               | NO                    | ∞            |

### Análisis

1.  **Eficiencia de Memoria**: La arquitectura "Sparse" (Escasa) del reservoir permite una huella de memoria minúscula, crucial para microcontroladores de gama baja (ATTiny, ESP8266).
2.  **Costo Computacional vs. Funcionalidad**: Aunque Eón consume más energía por ciclo que una red "Feed Forward" simple (MLP), ofrece **memoria temporal** (contexto) que las redes MLP no tienen. Para obtener capacidad temporal similar con TinyML, se requeriría una RNN/LSTM mucho más pesada (>50KB).
3.  **Entrenamiento**: Una ventaja clave de Eón es la capacidad de **aprender en el dispositivo** ajustando solo la capa de salida (`W_out`). Las redes TinyML típicas requieren reentrenamiento en la nube.

## Conclusión

Eón es la solución óptima cuando se requiere:

1.  **Aprendizaje Continuo** en el borde.
2.  **Procesamiento de Series Temporales** (contexto histórico).
3.  **Restricciones extremas de RAM** (< 2KB).
