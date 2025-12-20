# Especificación Técnica: Echo State Network (ESN)

## Visión General

El ESN es un tipo de Reservoir Computing que utiliza una red recurrente aleatoria (reservoir) como proyector de alta dimensión, entrenando únicamente una capa de salida lineal.

**Implementaciones disponibles:**

- Python (NumPy) - 80KB - alta precisión
- C (punto fijo Q8.8) - 1.3KB - embebido
- JavaScript - navegador - sin dependencias

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Input (x)                                                 │
│      │                                                      │
│      ▼                                                      │
│   ┌──────┐                                                  │
│   │ W_in │  Matriz de entrada (aleatoria, fija)             │
│   └──┬───┘                                                  │
│      │                                                      │
│      ▼                                                      │
│   ┌──────────────────────┐                                  │
│   │      RESERVOIR       │◄───┐                             │
│   │   (W_reservoir)      │    │ Conexiones recurrentes      │
│   │   100 neuronas       │────┘                             │
│   │   90% escaso         │                                  │
│   └──────────┬───────────┘                                  │
│              │                                              │
│              ▼                                              │
│         state(t) = tanh(W_in·x + W_reservoir·state(t-1))    │
│              │                                              │
│              ▼                                              │
│          ┌───────┐                                          │
│          │ W_out │  Matriz de salida (ÚNICA ENTRENADA)      │
│          └───┬───┘                                          │
│              │                                              │
│              ▼                                              │
│          Output (y)                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Parámetros

| Parámetro         | Tipo  | Por Defecto | Description                   |
| ----------------- | ----- | ----------- | ----------------------------- |
| `n_inputs`        | int   | 1           | Dimensión de entrada          |
| `n_reservoir`     | int   | 100         | Neuronas en el reservoir      |
| `n_outputs`       | int   | 1           | Dimensión de salida           |
| `spectral_radius` | float | 0.9         | Radio espectral (estabilidad) |
| `sparsity`        | float | 0.9         | Proporción de conexiones cero |
| `noise`           | float | 0.001       | Ruido de regularización       |

### Radio Espectral

- `< 1.0`: Red estable, buena para predicción
- `≈ 0.9`: Balance memoria corta/larga
- `> 1.0`: Riesgo de inestabilidad (evitar)

### Escasez (Sparsity)

- `0.9` = 90% conexiones son cero
- Reduce cálculo y mejora generalización
- Emula conectividad biológica

## Uso

```python
from esn.esn import EchoStateNetwork, generate_mackey_glass

# Crear ESN
esn = EchoStateNetwork(
    n_inputs=1,
    n_reservoir=100,
    n_outputs=1,
    spectral_radius=0.9,
    random_state=42
)

# Entrenar (solo W_out)
esn.fit(X_train, y_train, washout=100)

# Predecir
predictions = esn.predict(X_test)

# Memoria
memory = esn.get_memory_footprint()
print(f"Memoria total: {memory['total_kb']:.2f} KB")
```

## Cuantización

Reduce precisión de pesos manteniendo rendimiento:

| Bits        | Rango       | Precisión Retenida\* |
| ----------- | ----------- | -------------------- |
| 64 (base)   | float64     | 100%                 |
| 8           | [-128, 127] | ~99%                 |
| 4           | [-8, 7]     | ~95%                 |
| 1 (binario) | {-1, +1}    | ~80-90%              |

\*Valores típicos en Mackey-Glass

```python
from quantization.quantizer import QuantizedESN

q_esn = QuantizedESN(esn_entrenada, bits=8)
predictions = q_esn.predict(X_test)
```

## Plasticidad Hebbiana

Aprendizaje local continuo:

```python
from plasticity.hebbian import HebbianESN

esn = HebbianESN(
    n_reservoir=100,
    learning_rate=0.0001,
    plasticity_type='anti_hebbian'  # o 'hebbian', 'stdp'
)

# Entrenamiento inicial
esn.fit(X_train, y_train)

# Adaptación online (sin targets)
esn.adapt_online(X_new_data)
```

## Rendimiento Esperado

| Configuración       | MSE (Mackey-Glass) | Memory |
| ------------------- | ------------------ | ------- |
| ESN-100             | ~0.001             | ~80 KB  |
| ESN-100 (8-bit)     | ~0.001             | ~10 KB  |
| ESN-50              | ~0.003             | ~22 KB  |
| ESN-100 + anti_hebb | ~0.0001            | ~80 KB  |

## Referencias

- Jaeger, H. (2001). "The echo state approach"
- Lukoševičius, M. (2012). "A Practical Guide to Applying ESNs"
