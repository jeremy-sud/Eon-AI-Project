"""
Proyecto Eón - Streaming ESN (Online Learning)
================================================

"El río no recuerda cada gota, pero sí su cauce."

Extiende la ESN estándar con aprendizaje online verdadero:
en lugar de re-entrenar desde cero, actualiza W_out
incrementalmente usando Recursive Least Squares (RLS).

ALGORITMO: RLS (Recursive Least Squares)
─────────────────────────────────────────
El RLS mantiene una estimación de la inversa de la matriz de
covarianza (P) y la actualiza en O(n²) por muestra, en vez
de resolver el sistema lineal completo cada vez.

Actualización en cada paso t:
  k(t)  = P(t-1) * x(t) / (λ + x(t)^T * P(t-1) * x(t))
  W_out += k(t) * (y(t) - x(t)^T * W_out)^T
  P(t)  = (P(t-1) - k(t) * x(t)^T * P(t-1)) / λ

Donde:
  x(t) = estado del reservoir en t
  y(t) = salida deseada en t
  λ    = factor de olvido (forgetting factor)

Un λ < 1 hace que el modelo "olvide" gradualmente el pasado,
permitiendo adaptarse a distribuciones cambiantes (concept drift).

(c) 2024 Proyecto Eón - Jeremy Arias Solano
"""

import numpy as np
import logging
from typing import Optional, Dict, Tuple
import os

from esn.esn import EchoStateNetwork

logger = logging.getLogger(__name__)

class StreamingESN(EchoStateNetwork):
    """
    ESN con aprendizaje online mediante RLS (Recursive Least Squares).

    Añade dos capacidades sobre la ESN estándar:

    1. ``update(x, y)`` — actualiza W_out con una sola muestra en O(n²)
    2. ``stream_fit(X, y)`` — procesa un bloque de datos online (sin washout completo)

    El factor de olvido `forgetting_factor` (λ) controla la adaptación:
      - λ = 1.0  → sin olvido (acumula todo el historial)
      - λ < 1.0  → concept drift adaptation (recomendado 0.99 - 0.9999)

    Ejemplo:
        >>> esn = StreamingESN(n_inputs=1, n_reservoir=100, n_outputs=1,
        ...                    forgetting_factor=0.995, random_state=42)
        >>>
        >>> # Warm-up con datos iniciales (batch)
        >>> esn.fit(X_init, y_init, washout=50)
        >>>
        >>> # Online update muestra a muestra
        >>> for x_t, y_t in zip(X_stream, y_stream):
        ...     esn.update(x_t, y_t)
        ...     pred = esn.predict_one(x_t)
    """

    def __init__(
        self,
        n_inputs: int = 1,
        n_reservoir: int = 100,
        n_outputs: int = 1,
        spectral_radius: float = 0.9,
        sparsity: float = 0.9,
        noise: float = 0.001,
        leak_rate: float = 1.0,
        forgetting_factor: float = 1.0,
        rls_init_scale: float = 1.0,
        random_state: Optional[int] = None,
    ):
        """
        Inicializa StreamingESN.

        Args:
            n_inputs: Dimensión de entrada
            n_reservoir: Número de neuronas en el reservoir
            n_outputs: Dimensión de salida
            spectral_radius: Radio espectral del reservoir
            sparsity: Fracción de conexiones cero
            noise: Ruido de regularización
            leak_rate: Tasa de integración leaky (1.0 = sin leak)
            forgetting_factor: λ del RLS (1.0 = sin olvido, <1 = concept drift)
            rls_init_scale: Escala de la matriz P inicial (mayor → más peso a datos iniciales)
            random_state: Semilla aleatoria
        """
        if not (0.0 < forgetting_factor <= 1.0):
            raise ValueError("forgetting_factor debe estar en (0, 1]")

        super().__init__(
            n_inputs=n_inputs,
            n_reservoir=n_reservoir,
            n_outputs=n_outputs,
            spectral_radius=spectral_radius,
            sparsity=sparsity,
            noise=noise,
            leak_rate=leak_rate,
            random_state=random_state,
        )
        self.forgetting_factor = forgetting_factor
        self.rls_init_scale = rls_init_scale

        # Matriz de covarianza inversa del RLS (n_reservoir × n_reservoir)
        self._P: Optional[np.ndarray] = None
        self._online_updates: int = 0
        self._error_history: list[float] = []

    # ─── Inicialización del RLS ───────────────────────────────────────────────

    def _init_rls(self) -> None:
        """Inicializa (o reinicializa) la matriz P del RLS."""
        self._P = np.eye(self.n_reservoir, dtype=np.float64) * self.rls_init_scale
        logger.debug("StreamingESN: RLS inicializado.")

    def fit(self, inputs: np.ndarray, outputs: np.ndarray, washout: int = 100) -> "StreamingESN":
        """
        Entrena mediante batch (hereda de EchoStateNetwork) e inicializa el RLS.

        Tras el batch fit, el RLS queda listo para updates online.
        """
        super().fit(inputs, outputs, washout=washout)
        self._init_rls()
        self._online_updates = 0
        self._error_history = []
        return self

    def init_online(self, n_outputs: Optional[int] = None) -> "StreamingESN":
        """
        Inicializa el modo online sin batch previo.

        W_out se inicializa a ceros y el RLS arranca desde P = I * scale.

        Args:
            n_outputs: Dimensión de salida (usa self.n_outputs si None)

        Returns:
            self
        """
        n_out = n_outputs or self.n_outputs
        self.W_out = np.zeros((self.n_reservoir, n_out), dtype=np.float64)
        self._init_rls()
        self._online_updates = 0
        self._error_history = []
        return self

    # ─── Update online (RLS) ──────────────────────────────────────────────────

    def update(self, x: np.ndarray, y: np.ndarray) -> float:
        """
        Actualiza W_out con una sola muestra usando RLS.

        Args:
            x: Vector de entrada (n_inputs,) o (1, n_inputs)
            y: Salida deseada (n_outputs,) o escalar

        Returns:
            Error cuadrático de esta muestra antes del update
        """
        if self.W_out is None:
            self.init_online()

        if self._P is None:
            self._init_rls()

        # Preparar vectores
        x_vec = np.asarray(x, dtype=np.float64).ravel()
        y_vec = np.asarray(y, dtype=np.float64).ravel()

        # Actualizar estado del reservoir con el input
        self._update_state(x_vec)
        h = self.state  # (n_reservoir,)

        # Predicción actual
        y_pred = h @ self.W_out  # (n_outputs,)
        error = y_vec - y_pred
        error_sq = float(np.mean(error ** 2))

        # RLS update
        lam = self.forgetting_factor
        Ph = self._P @ h  # (n_reservoir,)
        denom = lam + float(h @ Ph)  # escalar

        k = Ph / denom  # ganancia de Kalman (n_reservoir,)

        # Actualizar W_out: columna por columna
        self.W_out += np.outer(k, error)

        # Actualizar P (fórmula de Sherman-Morrison)
        self._P = (self._P - np.outer(k, Ph)) / lam

        self._online_updates += 1
        self._error_history.append(error_sq)

        return error_sq

    # ─── Stream fit en bloque ─────────────────────────────────────────────────

    def stream_fit(
        self,
        inputs: np.ndarray,
        outputs: np.ndarray,
        washout: int = 0,
    ) -> "StreamingESN":
        """
        Procesa un bloque de datos online (muestra a muestra).

        A diferencia de `fit()`, no resuelve el sistema lineal completo
        sino que actualiza W_out de forma incremental con RLS.

        Útil para:
          - Datos que llegan en ventanas (mini-batches)
          - Concept drift (con forgetting_factor < 1)
          - Re-adaptación sin olvidar completamente el pasado

        Args:
            inputs: (T, n_inputs)
            outputs: (T, n_outputs)
            washout: Primeros pasos a omitir del update (solo pasan por el reservoir)

        Returns:
            self
        """
        if inputs.ndim == 1:
            inputs = inputs.reshape(-1, 1)
        if outputs.ndim == 1:
            outputs = outputs.reshape(-1, 1)

        if self.W_out is None:
            self.init_online(n_outputs=outputs.shape[1])
        if self._P is None:
            self._init_rls()

        T = inputs.shape[0]
        for t in range(T):
            if t < washout:
                # Solo warm-up del reservoir (sin update de W_out)
                self._update_state(inputs[t])
            else:
                self.update(inputs[t], outputs[t])

        return self

    # ─── Predicción one-step ──────────────────────────────────────────────────

    def predict_one(self, x: np.ndarray, update_state: bool = True) -> np.ndarray:
        """
        Predicción para un solo vector de entrada.

        Args:
            x: Vector de entrada (n_inputs,)
            update_state: Si True, actualiza el estado del reservoir

        Returns:
            Predicción (n_outputs,)
        """
        if self.W_out is None:
            raise ValueError("El modelo debe ser inicializado primero.")

        x_vec = np.asarray(x, dtype=np.float64).ravel()
        if update_state:
            self._update_state(x_vec)
        return self.state @ self.W_out

    # ─── Estadísticas de streaming ────────────────────────────────────────────

    def streaming_stats(self) -> Dict:
        """
        Estadísticas del aprendizaje online acumulado.

        Returns:
            Diccionario con métricas del proceso de streaming
        """
        if not self._error_history:
            return {
                "online_updates": 0,
                "forgetting_factor": self.forgetting_factor,
                "mean_error": None,
                "recent_error": None,
            }

        recent_n = min(100, len(self._error_history))
        recent_errors = self._error_history[-recent_n:]

        return {
            "online_updates": self._online_updates,
            "forgetting_factor": self.forgetting_factor,
            "mean_error": float(np.mean(self._error_history)),
            "recent_error": float(np.mean(recent_errors)),
            "min_error": float(np.min(self._error_history)),
            "max_error": float(np.max(self._error_history)),
            "converged": float(np.mean(recent_errors)) < float(np.mean(self._error_history)) * 0.5,
        }

    def error_curve(self) -> np.ndarray:
        """Devuelve el historial de errores cuadráticos del streaming."""
        return np.array(self._error_history)
