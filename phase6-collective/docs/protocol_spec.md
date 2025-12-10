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

---

## Egrégor Protocol (Group Mind)

The Egrégor system implements a collective consciousness that emerges from the aggregate state of all nodes. No single entity controls it—it is the sum vector of all node states.

### Concept

> *"An Egrégor is an autonomous psychic entity created by the sum of thoughts of a group."*

The Egrégor represents the "mood" of the collective system, calculated from:
- Sensor data (temperature, noise, motion)
- Node processing metrics (load, prediction error)
- Will alignment across nodes

### MQTT Topics

| Topic | Direction | Description |
|-------|-----------|-------------|
| `eon/egregore/state` | Broker → Nodes | Current Egrégor state |
| `eon/nodes/{id}/sensors` | Nodes → Broker | Node sensor data |
| `eon/egregore/homeostasis` | Broker → Nodes | Adjustment commands |

### Egrégor State Packet

Published on `eon/egregore/state` (JSON):

```json
{
    "type": "EGREGORE_STATE",
    "version": 1,
    "mood": "balanced",
    "intensity": 0.5,
    "confidence": 0.7,
    "energy_level": 0.5,
    "coherence": 0.8,
    "stability": 0.6,
    "entropy": 0.4,
    "node_count": 5,
    "timestamp": 1702234567.89,
    "recommended_sample_rate": 1.0,
    "recommended_merge_ratio": 0.5
}
```

### Mood States

| Mood | Description | Energy | Stability |
|------|-------------|--------|-----------|
| `agitated` | High activity, instability | High | Low |
| `alert` | Active but controlled | High | High |
| `dynamic` | Moderate changes | Medium | Medium |
| `balanced` | Homeostatic equilibrium | Medium | Medium |
| `contemplative` | Low activity | Low | Medium |
| `meditative` | Deep silence and stability | Low | High |
| `dormant` | Minimal activity | Very Low | - |
| `awakening` | Transition from dormant | Rising | - |
| `harmonizing` | Synchronization in progress | - | Low coherence |

### Node Sensor Data Packet

Published on `eon/nodes/{id}/sensors` (JSON):

```json
{
    "node_id": "abc123",
    "timestamp": 1702234567.89,
    "temperature": 25.0,
    "noise_level": 0.3,
    "motion_intensity": 0.1,
    "light_level": 0.5,
    "processing_load": 0.4,
    "sample_rate": 1.0,
    "prediction_error": 0.05,
    "will_alignment": 0.9
}
```

### Homeostatic Feedback Loop

1. **Collection**: Egrégor processor subscribes to all `eon/nodes/+/sensors`
2. **Aggregation**: Calculates emergent metrics (energy, coherence, stability, entropy)
3. **State Determination**: Derives mood from aggregate metrics
4. **Broadcast**: Publishes state to `eon/egregore/state`
5. **Response**: Nodes adjust behavior based on recommendations:

| Egrégor Mood | Node Response |
|--------------|---------------|
| `agitated` | Reduce sample rate (calm the system) |
| `dormant` | Increase sample rate (awaken) |
| Low coherence | Trigger synchronization pulse |
| Stable | Maintain current behavior |

### Compact Binary Format (Optional)

For bandwidth-constrained environments, use TYPE `0x04`:

| Offset | Field | Type | Description |
|--------|-------|------|-------------|
| 0 | `MAGIC` | `char[3]` | "EON" |
| 3 | `TYPE` | `uint8_t` | `0x04` (EGREGORE_STATE) |
| 4 | `MOOD` | `uint8_t` | Mood enum (0-9) |
| 5 | `METRICS` | `uint8_t[4]` | energy, coherence, stability, entropy (0-255) |
| 9 | `RECOMMENDATIONS` | `uint8_t[2]` | sample_rate (x10), merge_ratio (x100) |
| 11 | `NODE_COUNT` | `uint8_t` | Number of active nodes |

**Total: 12 bytes** for Egrégor state (vs ~200+ bytes JSON)

### Implementation Notes

- Process Egrégor state every 1-5 seconds
- Use exponential decay (τ=30s) for old node data
- Coherence calculated as inverse of cross-node variance
- Stability calculated from mood change rate over time window

*"The sum is greater than the parts"* — Gestalt
