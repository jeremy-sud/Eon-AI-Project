"""
Proyecto Eón - Cuantización Adaptativa por Contexto
=====================================================

"Más bits donde importa, menos donde no."

En vez de cuantizar todos los pesos con la misma precisión,
AdaptiveQuantizer asigna bits según la importancia de cada conexión:

  - Conexiones críticas (alta importancia): 8 bits
  - Conexiones moderadas:                   4 bits
  - Conexiones marginales:                  2 bits
  - Conexiones irrelevantes:                1 bit (binario)

IMPORTANCIA se calcula combinando tres señales:
  1. Magnitud del peso  — pesos grandes son más influyentes
  2. Frecuencia de activación — neuronas que se activan frecuentemente
  3. Varianza de activación — neuronas con alta varianza son más informativas

Resultado esperado:
  - Reducción de memoria: >50 % vs cuantización 8-bit uniforme
  - Retención de precisión: >95 % del MSE original

(c) 2024 Proyecto Eón - Jeremy Arias Solano
"""

import numpy as np
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
import os

from esn.esn import EchoStateNetwork

logger = logging.getLogger(__name__)

# ─── Esquema de bits por importancia ─────────────────────────────────────────

# Umbrales de importancia normalizada → bits asignados
# La importancia está en [0, 1]; los umbrales son los límites inferiores.
IMPORTANCE_TO_BITS: list[Tuple[float, int]] = [
    (0.75, 8),   # importancia >= 0.75 → 8 bits
    (0.40, 4),   # importancia >= 0.40 → 4 bits
    (0.15, 2),   # importancia >= 0.15 → 2 bits
    (0.00, 1),   # resto              → 1 bit (binario)
]

@dataclass
class AdaptiveQuantStats:
    """Estadísticas de la cuantización adaptativa."""
    n_weights_8bit: int = 0
    n_weights_4bit: int = 0
    n_weights_2bit: int = 0
    n_weights_1bit: int = 0
    total_weights: int = 0
    original_bytes: int = 0
    quantized_bytes: float = 0.0   # fraccional (bits → bytes)

    @property
    def compression_ratio(self) -> float:
        if self.quantized_bytes == 0:
            return 1.0
        return self.original_bytes / self.quantized_bytes

    @property
    def memory_reduction_pct(self) -> float:
        return (1.0 - self.quantized_bytes / max(1, self.original_bytes)) * 100.0

    def to_dict(self) -> Dict:
        return {
            "n_weights_8bit": self.n_weights_8bit,
            "n_weights_4bit": self.n_weights_4bit,
            "n_weights_2bit": self.n_weights_2bit,
            "n_weights_1bit": self.n_weights_1bit,
            "total_weights": self.total_weights,
            "original_bytes": self.original_bytes,
            "quantized_bytes_effective": self.quantized_bytes,
            "compression_ratio": round(self.compression_ratio, 3),
            "memory_reduction_pct": round(self.memory_reduction_pct, 2),
        }

@dataclass
class _QuantLayer:
    """
    Almacena los datos de una capa cuantizada adaptativamente.

    Cada peso se guarda como int8 (el rango se limita según bits asignados),
    más una máscara de bits y parámetros de escala/offset por segmento.
    """
    weights_q: np.ndarray          # int8, shape original
    bit_mask: np.ndarray           # uint8, bits asignados por peso
    scales: np.ndarray             # float32, escala por peso
    offsets: np.ndarray            # float32, offset por peso
    shape: Tuple

class AdaptiveQuantizedESN:
    """
    ESN con cuantización adaptativa (precisión variable por conexión).

    Uso:
        >>> esn = EchoStateNetwork(...)
        >>> esn.fit(X_train, y_train)
        >>>
        >>> aq = AdaptiveQuantizer(esn)
        >>> aq.compute_importance(X_val)
        >>> aq_esn = aq.quantize_adaptive()
        >>>
        >>> predictions = aq_esn.predict(X_test)
        >>> print(aq.stats.to_dict())
    """

    def __init__(
        self,
        original_esn: EchoStateNetwork,
        W_in_layer: "_QuantLayer",
        W_res_layer: "_QuantLayer",
        W_out_layer: "_QuantLayer",
    ):
        self.original_esn = original_esn
        self._W_in = W_in_layer
        self._W_res = W_res_layer
        self._W_out = W_out_layer

        self.n_reservoir = original_esn.n_reservoir
        self.n_inputs = original_esn.n_inputs
        self.n_outputs = original_esn.n_outputs
        self.state = np.zeros(self.n_reservoir)

    @staticmethod
    def _dequantize_layer(layer: "_QuantLayer") -> np.ndarray:
        """Reconstruye una matriz float32 desde su representación cuantizada."""
        return (layer.weights_q.astype(np.float32) * layer.scales + layer.offsets).reshape(layer.shape)

    def _update_state(self, input_vector: np.ndarray) -> np.ndarray:
        W_in = self._dequantize_layer(self._W_in)
        W_res = self._dequantize_layer(self._W_res)
        self.state = np.tanh(W_in @ input_vector + W_res @ self.state)
        return self.state

    def predict(self, inputs: np.ndarray, reset_state: bool = False) -> np.ndarray:
        if inputs.ndim == 1:
            inputs = inputs.reshape(-1, 1)
        if reset_state:
            self.state = np.zeros(self.n_reservoir)

        W_out = self._dequantize_layer(self._W_out)
        T = inputs.shape[0]
        predictions = np.zeros((T, self.n_outputs))
        for t in range(T):
            self._update_state(inputs[t])
            predictions[t] = self.state @ W_out
        return predictions

    def reset(self):
        self.state = np.zeros(self.n_reservoir)

# ─── AdaptiveQuantizer ───────────────────────────────────────────────────────

class AdaptiveQuantizer:
    """
    Cuantiza una ESN con precisión variable según importancia de conexiones.

    Args:
        esn: ESN entrenada (debe tener W_out != None)
        importance_to_bits: Esquema de umbrales → bits.
            Lista de (umbral_importancia, bits) ordenada de mayor a menor.
        activation_samples: Pasos de activación para estimar frecuencia/varianza.
            Si es None se usa 500.

    Ejemplo:
        >>> aq = AdaptiveQuantizer(esn)
        >>> aq.compute_importance(X_val)
        >>> aq_esn = aq.quantize_adaptive()
        >>> print(aq.stats.to_dict())
    """

    def __init__(
        self,
        esn: EchoStateNetwork,
        importance_to_bits: Optional[list] = None,
        activation_samples: int = 500,
    ):
        if esn.W_out is None:
            raise ValueError("La ESN debe estar entrenada antes de cuantizar.")

        self.esn = esn
        self.importance_to_bits = importance_to_bits or IMPORTANCE_TO_BITS
        self.activation_samples = activation_samples

        self._importance_W_in: Optional[np.ndarray] = None
        self._importance_W_res: Optional[np.ndarray] = None
        self._importance_W_out: Optional[np.ndarray] = None
        self.stats: Optional[AdaptiveQuantStats] = None

    # ─── Cálculo de importancia ───────────────────────────────────────────────

    def _activation_stats(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Recorre X y recopila frecuencia de activación y varianza por neurona.

        Returns:
            (freq, var) — vectores de longitud n_reservoir
        """
        n = self.esn.n_reservoir
        activations = np.zeros((min(len(X), self.activation_samples), n))
        self.esn.reset()

        lim = min(len(X), self.activation_samples)
        for t in range(lim):
            inp = X[t] if X.ndim > 1 else np.array([X[t]])
            self.esn._update_state(inp)
            activations[t] = self.esn.state.copy()

        self.esn.reset()

        # Frecuencia: fracción de pasos donde |activación| > 0.1
        freq = (np.abs(activations) > 0.1).mean(axis=0)
        # Varianza por neurona
        var = activations.var(axis=0)
        return freq, var

    def compute_importance(self, X_val: np.ndarray) -> "AdaptiveQuantizer":
        """
        Calcula la importancia de cada peso a partir de datos de validación.

        La importancia combina:
          - Magnitud del peso (0.5 peso)
          - Frecuencia de activación de la neurona (0.3 peso)
          - Varianza de activación de la neurona (0.2 peso)

        Args:
            X_val: Datos de validación (T, n_inputs) o (T,)

        Returns:
            self (para encadenamiento)
        """
        if X_val.ndim == 1:
            X_val = X_val.reshape(-1, 1)

        freq, var = self._activation_stats(X_val)

        # Normalizar componentes a [0, 1]
        def _norm(v: np.ndarray) -> np.ndarray:
            vmax = v.max()
            return v / vmax if vmax > 1e-12 else v

        freq_n = _norm(freq)
        var_n = _norm(var)

        # W_in: (n_reservoir, n_inputs) — importancia por fila (neurona destino)
        w_in_mag = _norm(np.abs(self.esn.W_in).mean(axis=1))  # (n_reservoir,)
        imp_W_in_row = 0.5 * w_in_mag + 0.3 * freq_n + 0.2 * var_n
        # Expandir a la misma forma que W_in
        self._importance_W_in = np.broadcast_to(
            imp_W_in_row[:, None], self.esn.W_in.shape
        ).copy()

        # W_reservoir: (n_reservoir, n_reservoir) — importancia por fila
        w_res_mag = _norm(np.abs(self.esn.W_reservoir).mean(axis=1))
        imp_W_res_row = 0.5 * w_res_mag + 0.3 * freq_n + 0.2 * var_n
        self._importance_W_res = np.broadcast_to(
            imp_W_res_row[:, None], self.esn.W_reservoir.shape
        ).copy()

        # W_out: (n_reservoir, n_outputs) — importancia por fila (neurona fuente)
        w_out_mag = _norm(np.abs(self.esn.W_out).mean(axis=1))  # (n_reservoir,)
        imp_W_out_row = 0.5 * w_out_mag + 0.3 * freq_n + 0.2 * var_n
        self._importance_W_out = np.broadcast_to(
            imp_W_out_row[:, None], self.esn.W_out.shape
        ).copy()

        logger.info(
            f"AdaptiveQuantizer: importancia calculada sobre {len(X_val)} muestras."
        )
        return self

    # ─── Cuantización ─────────────────────────────────────────────────────────

    def _bits_for_importance(self, importance: float) -> int:
        """Retorna bits asignados para un valor de importancia dado."""
        for threshold, bits in self.importance_to_bits:
            if importance >= threshold:
                return bits
        return 1

    def _quantize_weight(self, w: float, bits: int) -> Tuple[int, float, float]:
        """
        Cuantiza un único peso a `bits` bits.

        Returns:
            (value_q, scale, offset) tal que w ≈ value_q * scale + offset
        """
        if bits == 1:
            scale = abs(w) if abs(w) > 1e-12 else 1.0
            return (1 if w >= 0 else -1), scale, 0.0

        q_min = -(1 << (bits - 1))
        q_max = (1 << (bits - 1)) - 1
        # Escalar desde [w_min, w_max] → [q_min, q_max]
        # Para un único valor usamos su rango simétrico
        abs_w = abs(w)
        if abs_w < 1e-12:
            return 0, 1.0, 0.0
        scale = abs_w / q_max
        offset = 0.0
        v = int(np.clip(round(w / scale), q_min, q_max))
        return v, scale, offset

    def _quantize_matrix(
        self, weights: np.ndarray, importance: np.ndarray
    ) -> "_QuantLayer":
        """
        Cuantiza una matriz peso a peso según su importancia.

        Args:
            weights: Matriz float, forma arbitraria
            importance: Importancia normalizada, misma forma que weights

        Returns:
            _QuantLayer con los datos cuantizados
        """
        flat_w = weights.ravel()
        flat_imp = importance.ravel()
        n = len(flat_w)

        weights_q = np.zeros(n, dtype=np.int8)
        bit_mask = np.zeros(n, dtype=np.uint8)
        scales = np.zeros(n, dtype=np.float32)
        offsets = np.zeros(n, dtype=np.float32)

        for i in range(n):
            b = self._bits_for_importance(float(flat_imp[i]))
            vq, sc, off = self._quantize_weight(float(flat_w[i]), b)
            weights_q[i] = np.int8(np.clip(vq, -128, 127))
            bit_mask[i] = np.uint8(b)
            scales[i] = np.float32(sc)
            offsets[i] = np.float32(off)

        return _QuantLayer(
            weights_q=weights_q,
            bit_mask=bit_mask,
            scales=scales,
            offsets=offsets,
            shape=weights.shape,
        )

    def _count_bits_stats(self, layer: "_QuantLayer") -> Dict[int, int]:
        """Cuenta pesos por nivel de bits."""
        counts: Dict[int, int] = {1: 0, 2: 0, 4: 0, 8: 0}
        for b in layer.bit_mask:
            counts[int(b)] = counts.get(int(b), 0) + 1
        return counts

    def quantize_adaptive(self) -> AdaptiveQuantizedESN:
        """
        Aplica cuantización adaptativa a la ESN.

        Requiere haber llamado `compute_importance()` antes.

        Returns:
            AdaptiveQuantizedESN lista para inferencia
        """
        if self._importance_W_in is None:
            raise RuntimeError(
                "Llama a compute_importance(X_val) antes de quantize_adaptive()."
            )

        # Cuantizar cada matriz
        W_in_layer = self._quantize_matrix(self.esn.W_in, self._importance_W_in)
        W_res_layer = self._quantize_matrix(self.esn.W_reservoir, self._importance_W_res)
        W_out_layer = self._quantize_matrix(self.esn.W_out, self._importance_W_out)

        # Calcular estadísticas
        stats = AdaptiveQuantStats()
        for layer in (W_in_layer, W_res_layer, W_out_layer):
            counts = self._count_bits_stats(layer)
            stats.n_weights_8bit += counts.get(8, 0)
            stats.n_weights_4bit += counts.get(4, 0)
            stats.n_weights_2bit += counts.get(2, 0)
            stats.n_weights_1bit += counts.get(1, 0)
            stats.total_weights += len(layer.weights_q)

        # Bytes efectivos (fraccionando por bits)
        stats.original_bytes = (
            self.esn.W_in.nbytes
            + self.esn.W_reservoir.nbytes
            + self.esn.W_out.nbytes
        )
        stats.quantized_bytes = (
            stats.n_weights_8bit * 1.0
            + stats.n_weights_4bit * 0.5
            + stats.n_weights_2bit * 0.25
            + stats.n_weights_1bit * 0.125
        )
        self.stats = stats

        logger.info(
            f"AdaptiveQuantizer: cuantización completa. "
            f"Compresión {stats.compression_ratio:.2f}x "
            f"({stats.memory_reduction_pct:.1f}% reducción)"
        )

        return AdaptiveQuantizedESN(self.esn, W_in_layer, W_res_layer, W_out_layer)

    def summary(self) -> Dict:
        """Resumen de la cuantización aplicada."""
        if self.stats is None:
            return {"error": "Cuantización no aplicada aún."}
        return self.stats.to_dict()
