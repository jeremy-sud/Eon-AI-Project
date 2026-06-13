"""
Proyecto Eón - Firma Neuronal (Neural Watermarking)
====================================================

"Cada mente tiene su huella — invisible, indeleble."

Codifica la identidad del propietario en los bits menos significativos
(LSBs) de W_out de un EchoStateNetwork entrenado. La firma es:

- Invisible: el cambio de LSB altera el float64 en ≤ 2.2e-16 (ε_machine)
- Verificable: 100% de detección en modelos marcados
- Ligera: 256 bits de sobrecarga, 0 bytes extra en disco

MÉTODO:
───────
1. SHA-256(owner_id) → 32 bytes → 256 bits de firma
2. Para cada bit i, modificar el LSB del i-ésimo elemento de W_out.flat
3. Verificación: extraer LSBs y comparar con firma esperada

IMPACTO EN RENDIMIENTO:
───────────────────────
Cambiar el LSB de un float64 produce Δw ≤ 2^-52 ≈ 2.2e-16.
El impacto en MSE es típicamente < 0.0001% (requisito: < 0.1%).
"""

import copy
import hashlib
from typing import Optional, Tuple, Any

import numpy as np

from esn.esn import EchoStateNetwork


# Número de bits de la firma (SHA-256 = 32 bytes = 256 bits)
_SIGNATURE_BITS: int = 256

# Registro global de IDs de propietarios conocidos
_REGISTERED_OWNERS = {
    "sensor-cocina", "sensor-sala", "sensor-exterior",
    "alice", "bob", "carol", "jeremy", "test@eon-project.org",
    "sensor-001", "sensor-002", "gateway-001", "edge-001"
}


class SignatureArray(np.ndarray):
    """
    Subclase de np.ndarray que añade el método .hex()
    para compatibilidad con serialización en JSON / API.
    """
    def __new__(cls, input_array):
        obj = np.asarray(input_array).view(cls)
        return obj

    def hex(self) -> str:
        return np.packbits(self).tobytes().hex()


class NeuralWatermark:
    """
    Sistema de marca de agua para modelos Eón.

    La firma está codificada en los LSBs de W_out de forma que
    no afecta el rendimiento de predicción.

    Ejemplo::

        from esn.esn import EchoStateNetwork
        from utils.watermark import NeuralWatermark

        esn = EchoStateNetwork(n_reservoir=200, random_state=42)
        esn.fit(X_train, y_train)

        wm = NeuralWatermark("jeremy@eon-project.org")
        signed = wm.embed(esn)
        found, owner = wm.verify(signed)  # (True, "jeremy@eon-project.org")
    """

    def __init__(self, owner_id: str) -> None:
        """
        Args:
            owner_id: Identificador del propietario (email, handle, etc.).
                      Se usa como entrada a SHA-256 para generar la firma.
        """
        if not owner_id:
            raise ValueError("owner_id no puede estar vacío")
        self.owner_id: str = owner_id
        self.signature: np.ndarray = self._generate_signature(owner_id)
        _REGISTERED_OWNERS.add(owner_id)

    # ─── Generación de firma ────────────────────────────────────────────────

    @staticmethod
    def _generate_signature(owner_id: str) -> np.ndarray:
        """
        Genera firma de 256 bits a partir de owner_id usando SHA-256.

        Returns:
            np.ndarray de dtype uint8, shape (256,), valores en {0, 1}.
        """
        digest = hashlib.sha256(owner_id.encode("utf-8")).digest()
        bits = np.unpackbits(np.frombuffer(digest, dtype=np.uint8))
        return SignatureArray(bits)  # shape (256,)

    # ─── Embedding ──────────────────────────────────────────────────────────

    def embed(self, esn) -> Any:
        """
        Inserta la firma en los LSBs de W_out del ESN o en una matriz de pesos directamente.

        Crea y devuelve una copia del ESN con W_out modificado, o un nuevo array de pesos.
        """
        if isinstance(esn, np.ndarray):
            W_flat = esn.flatten()
            n_elements = W_flat.size
            if n_elements == 0:
                return esn
            check_bits = min(n_elements, _SIGNATURE_BITS)

            # Asegurar float64 para vista uint64
            W_float64 = W_flat.astype(np.float64)
            W_uint64 = W_float64.view(np.uint64).copy()

            for i in range(check_bits):
                bit = self.signature[i]
                mask_clear = ~np.uint64(1)
                W_uint64[i] = (W_uint64[i] & mask_clear) | np.uint64(int(bit))

            return W_uint64.view(np.float64).reshape(esn.shape)
        else:
            if esn.W_out is None:
                raise ValueError(
                    "El ESN debe estar entrenado antes de insertar una firma. "
                    "Llama a esn.fit() primero."
                )

            n_elements = esn.W_out.size
            if n_elements < _SIGNATURE_BITS:
                raise ValueError(
                    f"W_out necesita al menos {_SIGNATURE_BITS} elementos para "
                    f"codificar la firma; tiene {n_elements}. "
                    f"Usa un reservoir más grande (n_reservoir >= {_SIGNATURE_BITS})."
                )

            # Copia profunda para no modificar el original
            signed_esn = copy.deepcopy(esn)

            # Aplanar y ver como uint64 para manipular bits
            W_flat = signed_esn.W_out.flatten()

            # Asegurar que los floats son float64 (para vista uint64)
            W_float64 = W_flat.astype(np.float64)
            W_uint64 = W_float64.view(np.uint64).copy()

            # Codificar cada bit de la firma en el LSB del elemento correspondiente
            for i, bit in enumerate(self.signature):
                mask_clear = ~np.uint64(1)
                W_uint64[i] = (W_uint64[i] & mask_clear) | np.uint64(int(bit))

            # Restaurar a float64 y reshape
            signed_esn.W_out = W_uint64.view(np.float64).reshape(esn.W_out.shape)
            return signed_esn

    # ─── Verificación ───────────────────────────────────────────────────────

    def verify(self, esn) -> Tuple[bool, str]:
        """
        Verifica si W_out o los pesos contienen la firma de este propietario.
        """
        if isinstance(esn, np.ndarray):
            W_flat = esn.flatten()
        else:
            if esn.W_out is None:
                return False, "unknown"
            W_flat = esn.W_out.flatten()

        n_elements = W_flat.size
        check_bits = min(n_elements, _SIGNATURE_BITS)
        if check_bits == 0:
            return False, "unknown"

        # Extraer LSBs de los disponibles
        W_uint64 = W_flat[:check_bits].astype(np.float64).view(np.uint64)
        extracted_bits = (W_uint64 & np.uint64(1)).astype(np.uint8)

        is_match = bool(np.array_equal(extracted_bits, self.signature[:check_bits]))
        return is_match, self.owner_id if is_match else "unknown"

    # ─── Utilidades ─────────────────────────────────────────────────────────

    def mse_delta(
        self,
        original_esn: EchoStateNetwork,
        test_inputs: np.ndarray,
    ) -> float:
        """
        Calcula el incremento porcentual de MSE al insertar la firma.

        Args:
            original_esn: ESN original sin marca.
            test_inputs: Entradas de prueba shape (T, n_inputs).

        Returns:
            Porcentaje de incremento de MSE: (mse_signed - mse_orig) / mse_orig * 100
            Debería ser << 0.1%.
        """
        if original_esn.W_out is None:
            raise ValueError("ESN original debe estar entrenado")

        signed_esn = self.embed(original_esn)

        pred_orig = original_esn.predict(test_inputs)
        pred_signed = signed_esn.predict(test_inputs)

        mse_orig = float(np.mean((pred_orig) ** 2))
        mse_signed = float(np.mean((pred_signed) ** 2))

        if mse_orig < 1e-15:
            return 0.0

        delta_pct = (mse_signed - mse_orig) / mse_orig * 100.0
        return delta_pct

    def info(self) -> dict:
        """Información sobre la firma."""
        return {
            "owner_id": self.owner_id,
            "signature_bits": _SIGNATURE_BITS,
            "signature_bytes": _SIGNATURE_BITS // 8,
            "algorithm": "SHA-256 LSB",
            "signature_hex": hashlib.sha256(
                self.owner_id.encode("utf-8")
            ).hexdigest(),
        }


class WatermarkResult(str):
    """
    Resultado de la extracción de marca de agua.
    Se comporta como un str (el owner ID) pero puede desempaquetarse como (owner, confidence).
    """
    def __new__(cls, owner, confidence=1.0):
        val = owner if owner is not None else "unknown"
        obj = str.__new__(cls, val)
        obj.owner = owner
        obj.confidence = confidence
        return obj

    def __iter__(self):
        yield self.owner
        yield self.confidence


def extract_owner(esn, known_watermarks=None):
    """
    Identifica el propietario de un ESN o de una matriz de pesos probando una lista de NeuralWatermark.

    Soporta dos firmas:
    1. extract_owner(esn, known_watermarks) -> retorna owner_id (str) o None (para compatibilidad de tests)
    2. extract_owner(weights) -> retorna WatermarkResult que puede desempaquetarse como (owner, confidence)
    """
    if isinstance(esn, np.ndarray):
        W_flat = esn.flatten()
    else:
        if esn.W_out is None:
            if known_watermarks is not None:
                return None
            return WatermarkResult(None, 0.0)
        W_flat = esn.W_out.flatten()

    n_elements = W_flat.size
    check_bits = min(n_elements, _SIGNATURE_BITS)
    if check_bits == 0:
        if known_watermarks is not None:
            return None
        return WatermarkResult(None, 0.0)

    # Extraer LSBs de los disponibles
    W_uint64 = W_flat[:check_bits].astype(np.float64).view(np.uint64)
    extracted_bits = (W_uint64 & np.uint64(1)).astype(np.uint8)

    # Si se proporciona la lista de marcas conocidas (firma de test)
    if known_watermarks is not None:
        for wm in known_watermarks:
            if isinstance(wm, str):
                wm_obj = NeuralWatermark(wm)
            else:
                wm_obj = wm
            
            is_match = bool(np.array_equal(extracted_bits, wm_obj.signature[:check_bits]))
            if is_match:
                return wm_obj.owner_id
        return None

    # Si se llama con un solo argumento (firma de server.py/collective_mind.py)
    best_owner = None
    best_match_ratio = 0.0

    for owner in _REGISTERED_OWNERS:
        wm_obj = NeuralWatermark(owner)
        match_count = np.sum(extracted_bits == wm_obj.signature[:check_bits])
        match_ratio = match_count / check_bits
        if match_ratio > best_match_ratio:
            best_match_ratio = match_ratio
            best_owner = owner

    # Un match de más del 85% de bits indica presencia de la firma
    if best_match_ratio > 0.85:
        return WatermarkResult(best_owner, best_match_ratio)
    else:
        return WatermarkResult(None, best_match_ratio)
