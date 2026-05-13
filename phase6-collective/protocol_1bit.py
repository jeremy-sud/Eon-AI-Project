"""Módulo común para el protocolo Eón 1-Bit.

Este módulo define el formato del paquete, la codificación y la decodificación
que deben ser usados por los nodos Python, el bridge WebSocket/MQTT y los
clientes de hardware.
"""

import struct
from typing import Any, Dict, Iterable, List, Optional

PACKET_MAGIC = b"EON"
HEADER_SIZE = 14

PACKET_TYPES = {
    'SYNC': 1,
    'REQ': 2,
    'ACK': 3,
    'PING': 4,
    'STATUS': 5,
}
PACKET_TYPE_NAMES = {v: k for k, v in PACKET_TYPES.items()}


def _payload_size_for_count(count: int) -> int:
    return (count + 7) // 8


def _pack_signs(weights: Iterable[float]) -> bytes:
    values = list(weights)
    count = len(values)
    payload = bytearray(_payload_size_for_count(count))

    for i, value in enumerate(values):
        if value >= 0:
            byte_idx = i // 8
            bit_idx = 7 - (i % 8)
            payload[byte_idx] |= 1 << bit_idx

    return bytes(payload)


def _unpack_signs(payload: bytes, count: int) -> List[int]:
    signs: List[int] = []
    total_bits = count
    for byte in payload:
        for bit_position in range(7, -1, -1):
            if len(signs) >= total_bits:
                break
            signs.append((byte >> bit_position) & 1)
    return signs


def encode_1bit_packet(
    weights: Iterable[float],
    seed: int,
    scale: float = 0.5,
    ptype: int = PACKET_TYPES['SYNC'],
) -> bytes:
    """Codifica un paquete binario del protocolo 1-bit."""
    values = list(weights)
    payload = _pack_signs(values)
    count = len(values)

    header = bytearray()
    header.extend(PACKET_MAGIC)
    header.append(ptype)
    header.extend(struct.pack(">I", seed))
    header.extend(struct.pack(">H", count))
    header.extend(struct.pack(">f", float(scale)))
    return bytes(header) + payload


def decode_1bit_packet(data: bytes) -> Optional[Dict[str, Any]]:
    """Decodifica un paquete binario del protocolo 1-bit."""
    if len(data) < HEADER_SIZE:
        return None

    try:
        magic = data[0:3]
        if magic != PACKET_MAGIC:
            return None

        ptype = data[3]
        seed = struct.unpack(">I", data[4:8])[0]
        count = struct.unpack(">H", data[8:10])[0]
        scale = struct.unpack(">f", data[10:14])[0]
        payload = data[HEADER_SIZE:]

        expected_payload_len = _payload_size_for_count(count)
        if len(payload) != expected_payload_len:
            return None

        signs = _unpack_signs(payload, count)
        weights = [scale if bit else -scale for bit in signs]

        return {
            'magic': magic.decode('ascii'),
            'type': ptype,
            'type_name': PACKET_TYPE_NAMES.get(ptype, 'UNKNOWN'),
            'seed': seed,
            'count': count,
            'scale': scale,
            'payload': payload,
            'weights': weights,
            'original_size': count * 4,
            'compressed_size': len(data),
            'compression_ratio': round((count * 4) / len(data), 2),
        }

    except (struct.error, UnicodeDecodeError, ValueError):
        return None


def validate_packet(data: bytes) -> bool:
    """Valida un paquete 1-bit sin necesidad de decodificarlo por completo."""
    if len(data) < HEADER_SIZE:
        return False
    if data[0:3] != PACKET_MAGIC:
        return False
    try:
        count = struct.unpack(">H", data[8:10])[0]
    except struct.error:
        return False
    payload_len = len(data) - HEADER_SIZE
    return payload_len == _payload_size_for_count(count)


def merge_weights(local: 'numpy.ndarray', external: Iterable[float], ratio: float = 0.5):
    """Mezcla pesos locales y externos con un ratio ponderado."""
    import numpy as np

    external_arr = np.array(external, dtype=float)
    if external_arr.shape != local.shape:
        external_arr = external_arr.reshape(local.shape)
    return local * (1 - ratio) + external_arr * ratio
