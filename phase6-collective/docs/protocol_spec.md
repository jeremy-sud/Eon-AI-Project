# Protocol: Eon 1-Bit Weight Exchange

## Overview

This protocol enables ultra-low bandwidth exchange of learned weights ($W_{out}$) between Eon nodes (ESP32/IoT). It uses extreme 1-bit quantization to achieve >16x compression.

## Packet Structure

Little-Endian byte order.

| Offset | Field     | Type        | Description                                    |
| :----- | :-------- | :---------- | :--------------------------------------------- |
| 0      | `MAGIC`   | `char[3]`   | "EON"                                          |
| 3      | `TYPE`    | `uint8_t`   | `0x01` (W_OUT_UPDATE)                          |
| 4      | `SEED`    | `uint32_t`  | Reservoir Seed ID (Must match receiver)        |
| 8      | `COUNT`   | `uint16_t`  | Number of weights ($N$)                        |
| 10     | `PAYLOAD` | `uint8_t[]` | Bit-packed weights ($\lceil N/8 \rceil$ bytes) |

## Payload Format (1-Bit Quantization)

Each bit represents the sign of a weight:

- `1`: Positive ($+Scale$)
- `0`: Negative ($-Scale$)

Packing:

- Byte 0, Bit 0: Weight[0]
- Byte 0, Bit 1: Weight[1]
- ...
- Byte 0, Bit 7: Weight[7]
- Byte 1, Bit 0: Weight[8]

## Compression Performance

- Float32 (100 weights): **400 Bytes**
- Eon 1-Bit (100 weights): **23 Bytes** (incl. header)
- **Ratio: ~17.4x**

## Transport

- **MQTT Topic**: `eon/hive/update`
- **QoS**: 0 or 1
