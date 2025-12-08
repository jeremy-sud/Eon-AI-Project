# Fase 6: Mente Colectiva

El objetivo de esta fase es permitir que múltiples nodos Eón aprendan juntos sin compartir sus datos privados. Utiliza un esquema federado descentralizado donde solo se intercambian los pesos aprendidos ($W_{out}$).

## Características Principales

- **Intercambio de Pesos 1-Bit**:

  - Protocolo ultraligero para microcontroladores (ESP32).
  - Comprime los pesos de punto flotante a **1 bit por peso** (signo).
  - Tasa de compresión: **~17.4x** (400 bytes $\to$ 23 bytes).
  - Ver [Especificación del Protocolo](docs/protocol_spec.md).

- **Sincronización por "Momento Cero"**:
  - Todos los nodos comparten la misma semilla de nacimiento, garantizando reservoirs matemáticamente idénticos.
  - Esto permite sumar/promediar $W_{out}$ directamente.

## Estructura

- `src/quantization.c`: Lógica de compresión.
- `src/mock_mqtt.c`: Demo de transmisión de paquetes.
- `collective_mind.py`: Orquestador (prototipo Python).

## Ejecución Demo (C)

```bash
gcc -o mock_mqtt src/mock_mqtt.c src/quantization.c
./mock_mqtt
```
