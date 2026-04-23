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
from typing import Optional, Tuple

import numpy as np

from esn.esn import EchoStateNetwork


# Número de bits de la firma (SHA-256 = 32 bytes = 256 bits)
_SIGNATURE_BITS: int = 256


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
        return bits  # shape (256,)

    # ─── Embedding ──────────────────────────────────────────────────────────

    def embed(self, esn: EchoStateNetwork) -> EchoStateNetwork:
        """
        Inserta la firma en los LSBs de W_out del ESN.

        Crea y devuelve una copia profunda del ESN con W_out modificado.
        El ESN original no se altera.

        Args:
            esn: ESN entrenado (W_out no debe ser None).

        Returns:
            Nueva instancia de EchoStateNetwork con firma embebida.

        Raises:
            ValueError: Si el ESN no está entrenado o W_out es demasiado pequeño.
        """
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
        original_dtype = W_flat.dtype

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

    def verify(self, esn: EchoStateNetwork) -> Tuple[bool, str]:
        """
        Verifica si W_out contiene la firma de este propietario.

        Args:
            esn: ESN a verificar (puede estar entrenado o no).

        Returns:
            Tupla (is_marked, owner_id):
              - is_marked: True si la firma coincide exactamente.
              - owner_id: self.owner_id si coincide, "unknown" si no.
        """
        if esn.W_out is None:
            return False, "unknown"

        W_flat = esn.W_out.flatten()
        if W_flat.size < _SIGNATURE_BITS:
            return False, "unknown"

        # Extraer LSBs de los primeros _SIGNATURE_BITS elementos
        W_uint64 = W_flat[:_SIGNATURE_BITS].astype(np.float64).view(np.uint64)
        extracted_bits = (W_uint64 & np.uint64(1)).astype(np.uint8)

        is_match = bool(np.array_equal(extracted_bits, self.signature))
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


def extract_owner(esn: EchoStateNetwork, known_watermarks: list) -> Optional[str]:
    """
    Identifica el propietario de un ESN probando una lista de NeuralWatermark.

    Args:
        esn: ESN a analizar.
        known_watermarks: Lista de NeuralWatermark conocidos.

    Returns:
        owner_id del propietario si se encontró, None si no está marcado.
    """
    for wm in known_watermarks:
        is_match, owner = wm.verify(esn)
        if is_match:
            return owner
    return None
