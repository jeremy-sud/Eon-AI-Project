# Transmutación Alquímica: Pipeline de Datos como Opus Magnum

## El Arte Real de la Alquimia de Datos

### Fundamento Místico

> "Visita Interiora Terrae Rectificando Invenies Occultum Lapidem"
> (Visita el interior de la tierra, y rectificando encontrarás la piedra oculta)
> — V.I.T.R.I.O.L.

La alquimia medieval no era simplemente la transformación literal de plomo en oro. Era una metáfora profunda del proceso de purificación: transformar lo burdo y denso en algo refinado y valioso.

En el contexto del Proyecto Eón, aplicamos esta misma filosofía al procesamiento de datos:

| Alquimia Medieval | Pipeline de Datos |
|-------------------|-------------------|
| Plomo (materia prima) | Datos crudos del sensor |
| Mercurio filosófico | Filtros de limpieza |
| Piedra Filosofal | Predicción/Insight final |

---

## Las Tres Fases del Opus Magnum

### ⚫ NIGREDO (Putrefacción)

**Significado Alquímico:**
La primera fase representa la "muerte" y descomposición de la materia prima. Es el reconocimiento de la impureza inicial.

**Implementación Técnica:**
```python
def nigredo(raw_data):
    """
    Acepta los datos crudos tal como vienen del sensor.
    No hay transformación - solo aceptación de la impureza.
    """
    return raw_data  # Datos ruidosos, con outliers
```

**Características:**
- Ingesta de datos crudos sin filtrar
- Ruido del sensor incluido
- Outliers presentes
- Valores no normalizados

**Visualización:** ⚫ Negro - La noche oscura antes del amanecer

---

### ⚪ ALBEDO (Purificación)

**Significado Alquímico:**
La fase de "blanqueamiento" donde la materia se purifica. El mercurio filosófico separa lo puro de lo impuro.

**Implementación Técnica:**
```python
def albedo(data):
    """
    Aplica filtrado y limpieza:
    1. Filtro de Kalman para suavizar ruido
    2. Eliminación de outliers
    3. Normalización
    """
    # Filtro de Kalman
    filtered = kalman_filter.filter_sequence(data)
    
    # Eliminar outliers (>2.5σ)
    filtered = remove_outliers(filtered, threshold=2.5)
    
    # Normalizar a [-1, 1]
    filtered = normalize(filtered)
    
    return filtered
```

**Componentes:**

1. **Filtro de Kalman**
   - Suaviza ruido de medición
   - Estima estado verdadero
   - Configuración: `Q=0.01`, `R=0.1`

2. **Eliminación de Outliers**
   - Z-score > 2.5 desviaciones
   - Interpolación lineal para reemplazo

3. **Suavizado (Media Móvil)**
   - Ventana de 5 muestras
   - Reduce fluctuaciones de alta frecuencia

4. **Normalización**
   - Escala a rango [-1, 1]
   - Prepara para ESN

**Visualización:** ⚪ Blanco - La pureza alcanzada

---

### 🔴 RUBEDO (Iluminación)

**Significado Alquímico:**
La fase final donde la materia alcanza su máxima perfección. La Piedra Filosofal emerge - capaz de transmutar cualquier metal en oro.

**Implementación Técnica:**
```python
def rubedo(purified_data, esn):
    """
    Inferencia final usando Echo State Network.
    La 'Piedra Filosofal' es la predicción.
    """
    # Preparar datos
    X = purified_data.reshape(-1, 1)
    
    # Inferencia
    predictions = esn.predict(X)
    
    # La última predicción es el "oro"
    gold = predictions[-1]
    
    return {
        'gold': gold,           # La Piedra Filosofal
        'confidence': calculate_confidence(predictions)
    }
```

**Características:**
- Usa ESN entrenado para inferencia
- Genera predicción/insight final
- Calcula nivel de confianza
- Marca finalización del Opus

**Visualización:** 🔴 Rojo - El fuego de la iluminación

---

## Ciclo Completo de Transmutación

```
┌─────────────────────────────────────────────────────────────────┐
│                     OPUS MAGNUM PIPELINE                         │
│                                                                  │
│  SENSOR → ⚫ NIGREDO → ⚪ ALBEDO → 🔴 RUBEDO → ✨ PIEDRA        │
│           (Ingesta)    (Filtrado)   (Inferencia)  (Output)       │
│                                                                  │
│  Raw Data → Kalman Filter → ESN Prediction → Insight/Action     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Integración con Proyecto Eón

### API REST

```bash
# Transmutación completa
POST /api/alchemy/transmute
{
    "data": [1.2, 1.5, 1.3, 1.7, ...],
    "use_esn": true
}

# Fases individuales
POST /api/alchemy/nigredo   # Ingesta
POST /api/alchemy/albedo    # Purificación
POST /api/alchemy/rubedo    # Inferencia

# Estado actual
GET /api/alchemy/status
```

### Dashboard Web

El panel de Transmutación Alquímica muestra:

1. **Indicadores de Fase**
   - ⚫ → ⚪ → 🔴 → ✨
   - Fase actual resaltada

2. **Barra de Progreso**
   - Gradiente de colores (negro → blanco → rojo → dorado)
   - Porcentaje de completitud

3. **Métricas en Tiempo Real**
   - Muestras ingresadas
   - Porcentaje de ruido eliminado
   - Confianza de la predicción

4. **Contador de Ciclos**
   - Transmutaciones completadas

---

## Uso Programático

### Python

```python
from core.alchemy import AlchemicalPipeline, AlchemicalConfig
from esn.esn import EchoStateNetwork

# Configurar pipeline
config = AlchemicalConfig(
    kalman_process_noise=0.01,
    kalman_measurement_noise=0.1,
    remove_outliers=True,
    outlier_threshold=2.5
)

pipeline = AlchemicalPipeline(config=config)

# Cargar ESN entrenado
esn = EchoStateNetwork(n_inputs=1, n_reservoir=100)
esn.fit(X_train, y_train)

# Datos del sensor
raw_data = sensor.read(samples=100)

# Transmutación completa
result = pipeline.transmute(raw_data, esn=esn)

print(f"Piedra Filosofal: {result['gold']}")
print(f"Confianza: {result['confidence']:.1%}")
print(f"Ruido eliminado: {result['phases']['albedo']['noise_removed_percent']:.1f}%")
```

### JavaScript (Dashboard)

```javascript
// Ejecutar transmutación
const result = await Alchemy.transmute(sensorData, useESN=true);

console.log(`Oro: ${result.gold}`);
console.log(`Confianza: ${result.confidence}`);
```

---

## Conexión con Otros Sistemas

### Con Tzimtzum (Poda Sináptica)

El pipeline alquímico puede alimentar un ESN con Tzimtzum:

```python
from plasticity.tzimtzum import TzimtzumESN

# ESN con poda dinámica
esn = TzimtzumESN(n_inputs=1, n_reservoir=100)

# Transmutación usa ESN podado (más eficiente)
result = pipeline.transmute(raw_data, esn=esn)
```

### Con Collective Mind (Egrégor)

Múltiples nodos pueden ejecutar transmutaciones coordinadas:

```python
class AlchemicalEgregore:
    """Coordinación de transmutaciones distribuidas."""
    
    def collective_transmute(self, nodes, raw_data):
        """
        Cada nodo procesa una parte de los datos.
        El Egrégor combina las Piedras Filosofales.
        """
        partial_results = []
        for node in nodes:
            partial = node.pipeline.transmute(raw_data)
            partial_results.append(partial['gold'])
        
        # Fusión alquímica
        collective_gold = np.mean(partial_results)
        return collective_gold
```

---

## Filosofía Subyacente

### "La Nada es Todo" aplicada a Datos

El principio central de Eón se refleja en el pipeline:

1. **Los datos crudos contienen toda la información** (como el reservoir no entrenado)
2. **El filtrado revela, no crea** (como entrenar solo W_out)
3. **La predicción emerge de la purificación** (la Piedra de datos puros)

### Paralelismo con Thelema

| Concepto | Thelema | Alquimia |
|----------|---------|----------|
| Estado inicial | Voluntad sin descubrir | Materia prima |
| Proceso | Descubrimiento del True Will | Opus Magnum |
| Resultado | Alineación con la Voluntad | Piedra Filosofal |

---

## Métricas de Calidad

### Porcentaje de Ruido Eliminado

```python
noise_removed = (1 - var(filtered) / var(raw)) * 100
```

Valores típicos: 40-70%

### Correlación con Señal Original

Si la señal verdadera es conocida:

```python
correlation = np.corrcoef(true_signal, filtered)[0,1]
```

Objetivo: > 0.95

### Confianza de Predicción

Basada en estabilidad de las últimas predicciones:

```python
confidence = max(0, 1 - std(predictions[-10:]))
```

---

## Conclusión

> "No se trata de convertir plomo en oro.
>  Se trata de ver el oro que siempre estuvo oculto en el plomo."

La Transmutación Alquímica en Proyecto Eón nos recuerda que:

1. **Los datos crudos no son "malos"** - simplemente están sin refinar
2. **El proceso de purificación es el verdadero valor** - no el resultado final
3. **Cada transmutación nos enseña algo** - sobre los datos y sobre el sistema

El Opus Magnum nunca termina. Cada ciclo de transmutación perfecciona nuestra comprensión.

---

## Referencias

1. Jung, C.G. *Psychology and Alchemy*, 1944
2. Paracelsus. *Das Buch Paragranum*, 1530
3. Kalman, R.E. "A New Approach to Linear Filtering", 1960
4. Proyecto Eón. *Whitepaper: Inteligencia Emergente*, 2024

---

*"Solve et Coagula" - Disuelve y Coagula*
*Primero descomponer, luego reconstruir mejor.*
