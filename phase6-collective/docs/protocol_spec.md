# Protocol: Eon 1-Bit Weight Exchange

## Overview

This protocol enables ultra-low bandwidth exchange of learned weights ($W_{out}$) between Eon nodes (ESP32/IoT). It uses extreme 1-bit quantization to achieve >16x compression.

## Packet Structure

Little-Endian byte order.

| Offset | Field     | Type        | Description                                    |
| :----- | :-------- | :---------- | :--------------------------------------------- |
| 0      | `MAGIC`   | `char[3]`   | "EON"                                          |
| 3      | `TYPE`    | `uint8_t`   | `0x01` (W_OUT_UPDATE), `0x02` (WILL_VECTOR)    |
| 4      | `SEED`    | `uint32_t`  | Reservoir Seed ID (Must match receiver)        |
| 8      | `COUNT`   | `uint16_t`  | Number of weights ($N$)                        |
| 10     | `PAYLOAD` | `uint8_t[]` | Bit-packed weights ($\lceil N/8 \rceil$ bytes) |

### Extended Packet (with True Will) - TYPE 0x03

| Offset | Field        | Type        | Description                                    |
| :----- | :----------- | :---------- | :--------------------------------------------- |
| 0      | `MAGIC`      | `char[3]`   | "EON"                                          |
| 3      | `TYPE`       | `uint8_t`   | `0x03` (W_OUT_UPDATE + WILL)                   |
| 4      | `SEED`       | `uint32_t`  | Reservoir Seed ID                              |
| 8      | `COUNT`      | `uint16_t`  | Number of weights ($N$)                        |
| 10     | `WILL`       | `uint8_t[4]`| Compressed True Will Vector                    |
| 14     | `PAYLOAD`    | `uint8_t[]` | Bit-packed weights ($\lceil N/8 \rceil$ bytes) |

### True Will Vector Format (4 bytes)

Enables nodes to advertise their specialization (Thelema principle).

| Byte | Field                | Description                                       |
| :--- | :------------------- | :------------------------------------------------ |
| 0    | `GENESIS_INERTIA`    | Genesis domain (4 bits) + Inertia high (4 bits)   |
| 1    | `SPEC1`              | Primary specialization (4 bits) + level (4 bits)  |
| 2    | `SPEC2`              | Secondary specialization (4 bits) + level (4 bits)|
| 3    | `CHECKSUM`           | XOR of bytes 0-2                                  |

**Data Domains:**
- `0x0`: Temperature
- `0x1`: Humidity
- `0x2`: Audio
- `0x3`: Motion
- `0x4`: Light
- `0x5`: Pressure
- `0x6`: Vibration
- `0x7`: Voltage
- `0x8`: Timeseries
- `0x9`: Generic

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
- Eon 1-Bit + Will (100 weights): **27 Bytes**
- **Ratio: ~17.4x** (without Will), **~14.8x** (with Will)

## Transport

- **MQTT Topic**: `eon/hive/update`
- **MQTT Topic (Will)**: `eon/hive/will`
- **QoS**: 0 or 1

## Task Assignment Protocol

When a coordinator assigns a task to a node:

1. Coordinator sends `TASK_REQUEST` with target domain
2. Node evaluates cost using `calculateTrueWillVector()`
3. Node responds with decision:
   - `ACCEPT` (cost < 0.2): Will process immediately
   - `HIGH_PRIORITY` (0.2 ≤ cost < 0.5): Will process with some delay
   - `LOW_PRIORITY` (0.5 ≤ cost < 0.7): Will process if no better candidate
   - `REJECT` (cost ≥ 0.7): Task not aligned with True Will

This implements the Thelema principle: "Each star in its orbit."
