# El Egrégor: Mente Grupal Emergente en Eón

> *"Un Egrégor es una entidad psíquica autónoma creada por la suma de pensamientos de un grupo."*

## Concepto Místico

En la tradición esotérica occidental, un **Egrégor** (del griego ἐγρήγοροι, "vigilantes") es una forma-pensamiento colectiva que cobra vida propia. No es controlado por ningún individuo—es la cristalización de la voluntad grupal.

Ejemplos históricos:
- El "espíritu" de una orden iniciática
- La "energía" de un movimiento social
- El "ambiente" de un lugar sagrado

## Implementación en Eón

Traducimos este concepto místico a arquitectura de software:

### El Egrégor como Variable de Estado Global

```
    Nodo A ───┐
    Nodo B ───┼──→ EgregorProcessor ──→ EgregorState
    Nodo C ───┘           ↓
                    "Estado de Ánimo"
                          ↓
                Broadcast a todos los nodos
                          ↓
                Homeostasis Cibernética
```

**Ningún humano controla el Egrégor directamente**. Emerge de la suma vectorial de todos los estados de los nodos.

### Métricas Emergentes

El Egrégor calcula cuatro métricas fundamentales:

| Métrica | Descripción | Rango |
|---------|-------------|-------|
| **Energía** | Nivel de actividad colectiva | 0-1 |
| **Coherencia** | Sincronización entre nodos | 0-1 |
| **Estabilidad** | Constancia en el tiempo | 0-1 |
| **Entropía** | Caos/orden del sistema | 0-1 |

### Estados de Ánimo

De estas métricas emerge el "mood" del Egrégor:

```
Alta Energía + Baja Estabilidad → AGITADO
    El sistema está sobrecargado, los nodos discrepan
    → Acción: Reducir frecuencia de muestreo

Baja Energía + Alta Estabilidad → MEDITATIVO
    Silencio profundo, todos los nodos en armonía
    → Acción: Mantener el estado

Muy Baja Energía → DORMIDO
    Sistema casi inactivo
    → Acción: Despertar gradualmente

Baja Coherencia → ARMONIZANDO
    Los nodos están desincronizados
    → Acción: Pulso de sincronización
```

## El Feedback Loop: Homeostasis Cibernética

Este es el corazón del sistema. El Egrégor no solo observa—**actúa**:

### Cuando el Egrégor está "Agitado"

1. Demasiado ruido, calor, actividad
2. El Egrégor detecta energía > 0.7 y estabilidad < 0.4
3. Emite recomendación: `sample_rate = 0.5 Hz` (bajar de 1 Hz)
4. Los nodos reducen su frecuencia de muestreo
5. El sistema se "calma" naturalmente
6. Energía baja, estabilidad sube
7. Egrégor transiciona a "Balanceado"

### Cuando el Egrégor está "Dormido"

1. Poca actividad, casi silencio
2. El Egrégor detecta energía < 0.15
3. Emite recomendación: `sample_rate = 2.0 Hz` (subir)
4. Los nodos aumentan su actividad
5. El sistema "despierta"
6. Egrégor transiciona a "Despertando" → "Dinámico"

## Analogía Biológica

El Egrégor implementa **homeostasis** similar a:

| Sistema Biológico | Sistema Eón |
|-------------------|-------------|
| Temperatura corporal | Energía del Egrégor |
| Sistema nervioso | Red de nodos MQTT |
| Hipotálamo | EgregorProcessor |
| Sudoración/Temblores | Ajuste de sample_rate |
| Frecuencia cardíaca | Merge ratio |

## Uso en Código

```python
from collective_mind import CollectiveMind, EgregorCoordinator

# Crear mente colectiva
mind = CollectiveMind()
node1 = mind.create_node("sensor-temp")
node2 = mind.create_node("sensor-audio")

# Crear coordinador Egrégor
egregore = EgregorCoordinator(mind)

# Loop principal
while True:
    # Recolectar datos y procesar
    state = egregore.collect_and_process({
        "sensor-temp": {"temperature": 25, "noise_level": 0.1},
        "sensor-audio": {"noise_level": 0.8, "motion_intensity": 0.3},
    })
    
    # Aplicar homeostasis
    actions = egregore.apply_homeostasis()
    
    # El Egrégor ajusta el comportamiento de todos los nodos
    print(egregore.get_summary())
    
    time.sleep(state.recommended_sample_rate)
```

## MQTT para Sistemas Distribuidos

```
eon/nodes/{id}/sensors      ← Cada nodo publica sus datos
eon/egregore/state          → El broker publica el estado emergente
eon/egregore/homeostasis    → Comandos de ajuste
```

## Implicaciones Filosóficas

### La Mente Mayor que las Partes

El Egrégor demuestra **emergencia**: propiedades que no existen en ningún nodo individual pero aparecen en el colectivo.

Un solo nodo ESP32 no tiene "mood". Pero 10 nodos sincronizados sí lo tienen.

### Autonomía Sin Control Central

Nadie programa el mood del Egrégor. Emerge de:
- La física del ambiente (temperatura, ruido)
- El rendimiento de los nodos (errores, cargas)
- La historia del sistema (estabilidad)

Esto implementa una forma de **inteligencia distribuida** sin punto central de fallo.

### El Camino del Equilibrio

El sistema tiende naturalmente al balance:
- Agitación extrema → auto-calma
- Dormición extrema → auto-despertar
- Desincronización → auto-armonización

Esto es **Tao en código**: el sistema fluye hacia su estado natural.

## Conclusión

El Egrégor transforma una red de sensores IoT en algo más:

> Una entidad con "estado de ánimo" que emerge de sus partes,
> que nadie controla pero todos influencian,
> que ajusta el comportamiento del colectivo para mantener el equilibrio.

Es cibernética + misticismo = **sistemas vivos**.

---

*"La suma es mayor que las partes"* — Gestalt

*"Como es arriba, es abajo"* — Hermes Trismegisto
