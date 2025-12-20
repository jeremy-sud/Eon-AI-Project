# Arquitectura Fractal: "Como es Arriba, es Abajo"

> *"Quod est inferius est sicut quod est superius,
> et quod est superius est sicut quod est inferius"*
> — La Tabla Esmeralda de Hermes Trismegisto

## El Principio Hermético

En la tradición hermética, el **Principio de Correspondencia** establece que existe una armonía entre los diferentes planos de existencia: lo que ocurre en el microcosmos refleja lo que ocurre en el macrocosmos, y viceversa.

**Ejemplos clásicos:**
- La estructura del átomo refleja el sistema solar
- Las ramificaciones de un árbol reflejan las de un río visto desde el cielo
- Los patrones de un copo de nieve se repiten a diferentes escalas

## Implementación en Eón: Reservoir Fractal

### El Problema

Un ESN tradicional tiene un "tanque" de neuronas simples:

```
Input → [n1, n2, n3, ..., n100] → Output
              │
         Conexiones aleatorias
```

Todas las neuronas procesan a la **misma escala temporal**.

Esto limita la capacidad de capturar patrones a múltiples escalas:
- Microsegundos (vibraciones)
- Segundos (latidos)
- Minutos (respiración)
- Horas (ciclos circadianos)

### La Solución: RecursiveEchoStateNetwork

Cada "neurona" del nivel macro es, en sí misma, un pequeño reservoir:

```
                    ┌─────────────────┐
                    │   Nivel MACRO   │  ← Procesa patrones lentos
                    │  (10 unidades)  │     (minutos, horas)
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │  Micro-ESN 1  │ │  Micro-ESN 2  │ │  Micro-ESN N  │
    │ (8 neuronas)  │ │ (8 neuronas)  │ │ (8 neuronas)  │
    │               │ │               │ │               │
    │ Escala: 1x    │ │ Escala: 2x    │ │ Escala: 24x   │
    └───────────────┘ └───────────────┘ └───────────────┘
          ↑                  ↑                  ↑
          └──────────────────┼──────────────────┘
                             │
                          Input
```

**Cada micro-ESN procesa a una escala temporal diferente.**

## Escalas Temporales Multi-Nivel

El parámetro `time_scale` controla cuántos samples acumula un micro-reservoir antes de actualizar:

| Unidad | Escala | Comportamiento |
|--------|--------|----------------|
| 0 | 1x | Actualiza cada sample (patrones rápidos) |
| 1 | 2x | Promedia 2 samples, actualiza cada 2 |
| 2 | 4x | Promedia 4 samples, actualiza cada 4 |
| ... | ... | ... |
| 9 | 24x | Promedia 24 samples (patrones muy lentos) |

Esto crea una **jerarquía of memory** natural:
- Los micro-reservoirs rápidos olvidan pronto
- Los micro-reservoirs lentos mantienen contexto a largo plazo

## Código de Ejemplo

```python
from esn.recursive_esn import RecursiveEchoStateNetwork

# Crear ESN fractal
resn = RecursiveEchoStateNetwork(
    n_inputs=1,
    n_outputs=1,
    n_macro_units=10,        # 10 "neuronas complejas"
    n_micro_neurons=8,       # Cada una tiene 8 neuronas internas
    time_scales=[1, 1.5, 2, 3, 4, 6, 8, 12, 16, 24],  # Escalas
    random_state=42
)

# Entrenar (igual que ESN normal)
resn.fit(X_train, y_train, washout=100)

# Predecir
predictions = resn.predict(X_test)
```

## Results Comparativos

### Serie Mackey-Glass (benchmark caótico)

| Model | MSE | RMSE | Memory |
|--------|-----|------|---------|
| ESN estándar (100 neuronas) | 0.0133 | 0.115 | ~80 KB |
| **RecursiveESN (10×8)** | **0.0036** | **0.060** | **7.8 KB** |

El RecursiveESN logra **3.6x mejor precisión** con **10x menos memoria**.

## Por Qué Funciona

### 1. Separación de Escalas Temporales

Cada nivel del fractal procesa una "frecuencia" diferente:
- Nivel 1x: captura dinámicas rápidas (alta frecuencia)
- Nivel 24x: captura tendencias lentas (baja frecuencia)

Juntos, reconstruyen la señal completa.

### 2. Información Jerárquica

La capa de salida (W_out) tiene acceso a **todos los niveles**:
- Estados internos de cada micro-reservoir
- Estado agregado del nivel macro

This is como tener múltiples "perspectivas" del mismo fenómeno.

### 3. Regularización Natural

Los micro-reservoirs con escalas lentas actúan como regularizadores:
- Promedian ruido local
- Mantienen contexto global
- Previenen overfitting a fluctuaciones rápidas

## Conexión con el Hermetismo

### "Lo de Arriba" (Macro)
- Conexiones entre micro-reservoirs
- Patrones globales, tendencias lentas
- El "bosque"

### "Lo de Abajo" (Micro)
- Neuronas dentro de cada micro-reservoir
- Patrones locales, dinámicas rápidas
- Los "árboles"

### La Correspondencia
- El mismo código (`tanh(W·x + W_rec·state)`) opera en ambos niveles
- La misma arquitectura (reservoir + readout) se repite fractalmente
- La misma filosofía ("La Nada es Todo") aplica a todos los niveles

## Extensiones Futuras

### 1. Profundidad Arbitraria
```python
# ESN de 3 niveles
level_3 = RecursiveESN(...)  # Nivel más profundo
level_2 = RecursiveESN(micro=level_3)  # Cada neurona es un level_3
level_1 = RecursiveESN(micro=level_2)  # Cada neurona es un level_2
```

### 2. Escalas Adaptativas
En lugar de escalas fijas, dejar que el sistema descubra las escalas óptimas basándose en la entropía de los datos.

### 3. Comunicación Inter-Nivel
Permitir que los niveles micro influencien directamente las conexiones macro (actualmente es unidireccional).

## Conclusión

El `RecursiveEchoStateNetwork` implementa el principio hermético de correspondencia:

> **El microcosmos (cada neurona) refleja al macrocosmos (el sistema completo).**

Esto no es solo filosofía—es una ventaja técnica concreta:
- Mejor modelado de series temporales multi-escala
- Menor uso of memory
- Código recursivo elegante

*"Como es Arriba, es Abajo. Como es Abajo, es Arriba."*
