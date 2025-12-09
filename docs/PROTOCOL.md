# Protocolo Eón 1-Bit: Intercambio de Conocimiento Ultra-Ligero

> "El conocimiento viaja como un susurro, no como un grito."

## Introducción

El **Protocolo 1-Bit** es el mecanismo de sincronización de conocimiento entre nodos Eón. Permite que dispositivos IoT con conectividad limitada (LoRa, Bluetooth LE, MQTT) compartan lo que han aprendido usando solo **1 bit por peso**.

### ¿Por qué 1 Bit?

En un ESN (Echo State Network), los pesos de salida $W_{out}$ son los únicos que cambian durante el aprendizaje. La observación clave es que:

- El **signo** del peso es más importante que su magnitud exacta
- Los reservoirs generados con la misma semilla producen estados similares
- La reconstrucción con magnitud fija es suficiente para transferir conocimiento útil

## Compresión Alcanzada

| Formato | 32 pesos | 100 pesos | 256 pesos |
|---------|----------|-----------|-----------|
| Float32 | 128 bytes | 400 bytes | 1024 bytes |
| Int16 | 64 bytes | 200 bytes | 512 bytes |
| **Eón 1-Bit** | **14 bytes** | **23 bytes** | **42 bytes** |
| **Ratio** | **9x** | **17x** | **24x** |

*Incluye header de 10 bytes*

## Estructura del Paquete

```
Offset  Campo      Tipo        Descripción
──────────────────────────────────────────────────────
0       MAGIC      char[3]     "EON" (identificador)
3       TYPE       uint8_t     0x01 = W_OUT_UPDATE
                               0x02 = STATE_QUERY
                               0x03 = HEARTBEAT
4       SEED       uint32_t    Semilla del reservoir (debe coincidir)
8       COUNT      uint16_t    Número de pesos (N)
10      PAYLOAD    uint8_t[]   Bits empaquetados (⌈N/8⌉ bytes)
```

### Empaquetado de Bits

Cada byte contiene 8 pesos, bit 0 es el peso de menor índice:

```
Byte 0: [W7][W6][W5][W4][W3][W2][W1][W0]  (bits 7-0)
Byte 1: [W15][W14][W13][W12][W11][W10][W9][W8]
...
```

Valor del bit:
- `1` = Peso positivo → reconstruir como `+SCALE`
- `0` = Peso negativo → reconstruir como `-SCALE`

Donde `SCALE` es típicamente 0.5 o el valor RMS de los pesos originales.

## Algoritmo de Cuantización

### Encoder (Nodo Emisor)

```c
void encode_1bit(const float* weights, int count, uint8_t* payload) {
    for (int i = 0; i < count; i++) {
        int byte_idx = i / 8;
        int bit_idx = i % 8;
        
        if (weights[i] >= 0) {
            payload[byte_idx] |= (1 << bit_idx);
        }
    }
}
```

### Decoder (Nodo Receptor)

```c
void decode_1bit(const uint8_t* payload, int count, 
                 float scale, float* weights) {
    for (int i = 0; i < count; i++) {
        int byte_idx = i / 8;
        int bit_idx = i % 8;
        
        bool is_positive = (payload[byte_idx] >> bit_idx) & 1;
        weights[i] = is_positive ? scale : -scale;
    }
}
```

## Fusión de Conocimiento

Cuando un nodo recibe pesos de otro nodo, debe mezclarlos con sus propios pesos:

### Estrategia: Promedio Ponderado por Experiencia

```c
float merge_ratio = external_samples / (local_samples + external_samples);

for (int i = 0; i < n_weights; i++) {
    local_W[i] = local_W[i] * (1 - merge_ratio) + 
                 external_W[i] * merge_ratio;
}
```

### Estrategia: Votación Mayoritaria (para múltiples nodos)

```c
// Cada nodo vota con el signo de su peso
int votes[n_weights] = {0};

for (int node = 0; node < n_nodes; node++) {
    for (int i = 0; i < n_weights; i++) {
        votes[i] += (node_W[node][i] > 0) ? 1 : -1;
    }
}

// El signo final es la mayoría
for (int i = 0; i < n_weights; i++) {
    final_W[i] = (votes[i] >= 0) ? scale : -scale;
}
```

## Transporte

### MQTT (Recomendado para WiFi)

- **Topic publicación**: `eon/hive/{seed}/update`
- **Topic suscripción**: `eon/hive/{seed}/#`
- **QoS**: 1 (at least once) para actualizaciones críticas
- **Retain**: false (el conocimiento debe ser fresco)

### LoRa (Largo alcance, bajo consumo)

- **Frecuencia**: 868 MHz (EU) / 915 MHz (US)
- **SF**: 7-10 según distancia
- **Payload máximo**: 51 bytes → hasta 328 pesos

### Bluetooth LE

- **Característica**: Custom GATT
- **MTU**: Negociar 200+ bytes para eficiencia

## Seguridad

### Verificación de Semilla

Antes de fusionar conocimiento, verificar que la semilla coincida:

```c
if (packet.seed != local_core.certificate.reservoir_seed) {
    // Rechazar: reservoirs incompatibles
    return ERROR_SEED_MISMATCH;
}
```

### Hash de Integridad (Opcional)

Añadir 2 bytes de CRC16 al final del paquete:

```
[HEADER 10 bytes][PAYLOAD N bytes][CRC16 2 bytes]
```

## Ejemplos de Uso

### Caso 1: Sensor de Temperatura Distribuido

```
Nodo A (cocina)     Nodo B (sala)       Nodo C (exterior)
     │                   │                     │
     └───────┬───────────┴─────────────────────┘
             │
        Coordinator
             │
    ┌────────┴────────┐
    │  Fusión 1-Bit   │
    │  de predicción  │
    │  climática      │
    └─────────────────┘
```

### Caso 2: Detección de Anomalías Colaborativa

1. Nodo detecta anomalía local
2. Entrena con nuevos datos
3. Exporta pesos actualizados (1-bit)
4. Otros nodos importan y mejoran detección

## Limitaciones

1. **Pérdida de precisión**: ~15-20% aumento en MSE vs float32
2. **Semilla debe coincidir**: Nodos con diferente semilla son incompatibles
3. **Sin gradientes**: Solo funciona para pesos finales, no durante entrenamiento

## Métricas de Rendimiento

| Métrica | Valor Típico |
|---------|--------------|
| Latencia de encoding | < 1ms (32 pesos) |
| Tamaño de mensaje | 14-50 bytes |
| Overhead de fusión | < 5ms |
| Degradación MSE | 15-25% |
| Ahorro de ancho de banda | 17x promedio |

## Implementación de Referencia

Ver `phase6-collective/src/quantization.c` para la implementación en C.
Ver `phase6-collective/collective_mind.py` para el wrapper Python.

---

*Proyecto Eón - Sistemas Ursol*
*"La inteligencia no se crea, se descubre."*
