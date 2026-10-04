"""
Proyecto Eón - Guardián de Estabilidad Numérica y Control de Lyapunov
====================================================================

Monitoreo en tiempo real de la Echo State Property (ESP) y estabilidad
dinámica del reservoir computing para despliegues edge de larga duración.

Fundamentos Matemáticos:
- Condición de estabilidad: rho(W) < 1
- Exponente local de Lyapunov: lambda_max < 0
- Control de contracción espectral instantáneo O(N^2)

(c) 2024-2026 SenseLab - Build with Sense
"""

import numpy as np
import logging
from typing import Optional, Dict, Tuple, List

try:
    from utils.matrix_init import compute_spectral_radius
except ImportError:
    def compute_spectral_radius(W: np.ndarray, **kwargs) -> float:
        eigenvalues = np.abs(np.linalg.eigvals(W))
        return float(eigenvalues.max()) if len(eigenvalues) > 0 else 0.0

logger = logging.getLogger(__name__)


class StabilityGuard:
    """
    Guardián de estabilidad para Echo State Networks en tiempo real.
    
    Monitorea:
    1. Divergencia de Lyapunov (lambda_max): detecta transición a régimen caótico inestable.
    2. Radio espectral dinámico: verifica rho(W) <= rho_target tras plasticidad o poda.
    3. Saturación neuronal: ratio de neuronas con |x_i| cercano a 1.0 (saturación tanh).
    4. Integridad de punto flotante: detección preventiva de NaN/Inf.
    """
    
    def __init__(
        self,
        spectral_radius_target: float = 0.90,
        spectral_radius_max: float = 0.99,
        lyapunov_window: int = 50,
        saturation_threshold: float = 0.995,
        max_saturation_ratio: float = 0.80,
        damping_factor: float = 0.90
    ):
        self.spectral_radius_target = spectral_radius_target
        self.spectral_radius_max = spectral_radius_max
        self.lyapunov_window = lyapunov_window
        self.saturation_threshold = saturation_threshold
        self.max_saturation_ratio = max_saturation_ratio
        self.damping_factor = damping_factor
        
        # Estado y métricas
        self.divergence_history: List[float] = []
        self.last_lyapunov_exponent: float = 0.0
        self.contraction_events: int = 0
        self.saturation_events: int = 0
        self._prev_delta: Optional[float] = None
        self._prev_state: Optional[np.ndarray] = None
        
    def check_state(self, state: np.ndarray) -> Tuple[bool, Dict[str, float]]:
        """
        Analiza un vector de estado x(t) para verificar estabilidad numérica.
        
        Args:
            state: Vector de estado x(t) del reservoir (N,)
            
        Returns:
            Tuple (is_stable, metrics_dict)
        """
        # 1. Chequeo de NaN/Inf
        if not np.all(np.isfinite(state)):
            raise FloatingPointError("Guardián de Estabilidad: Detectado NaN/Inf en el estado del reservoir.")
            
        state_flat = state.ravel()
        n_neurons = len(state_flat)
        
        # 2. Análisis de saturación
        saturated_count = np.sum(np.abs(state_flat) >= self.saturation_threshold)
        saturation_ratio = float(saturated_count) / float(n_neurons)
        
        # 3. Estimación del exponente local de Lyapunov
        if self._prev_state is not None:
            delta = float(np.linalg.norm(state_flat - self._prev_state))
            if self._prev_delta is not None and self._prev_delta > 1e-12 and delta > 1e-12:
                local_divergence = np.log(delta / self._prev_delta)
                self.divergence_history.append(local_divergence)
                if len(self.divergence_history) > self.lyapunov_window:
                    self.divergence_history.pop(0)
                self.last_lyapunov_exponent = float(np.mean(self.divergence_history))
            self._prev_delta = delta
            
        self._prev_state = state_flat.copy()
        
        # Determinar si el estado está en régimen estable
        is_stable = True
        if saturation_ratio > self.max_saturation_ratio:
            self.saturation_events += 1
            is_stable = False
            
        metrics = {
            "saturation_ratio": saturation_ratio,
            "lyapunov_exponent": self.last_lyapunov_exponent,
            "contraction_events": float(self.contraction_events),
            "saturation_events": float(self.saturation_events)
        }
        
        return is_stable, metrics
        
    def check_and_stabilize_weights(self, W: np.ndarray) -> Tuple[np.ndarray, bool, float]:
        """
        Verifica el radio espectral de W y aplica contracción si excede el límite máximo.
        
        Args:
            W: Matriz de conexiones del reservoir (N x N)
            
        Returns:
            Tuple (W_stabilized, was_contracted, current_spectral_radius)
        """
        current_rho = compute_spectral_radius(W, method='auto')
        was_contracted = False
        
        if current_rho > self.spectral_radius_max:
            # Contracción instantánea hacia rho_target
            scaling = self.spectral_radius_target / current_rho
            W = W * scaling
            self.contraction_events += 1
            was_contracted = True
            current_rho = self.spectral_radius_target
            logger.warning(
                f"Estabilidad: Matriz W contraída por factor {scaling:.4f} "
                f"(rho_prev={current_rho/scaling:.3f} -> rho_new={current_rho:.3f})"
            )
            
        return W, was_contracted, current_rho

    def stabilize_state(self, state: np.ndarray) -> np.ndarray:
        """
        Aplica amortiguamiento suave a un estado saturado para evitar pérdida de dinámica.
        
        Args:
            state: Vector de estado saturado
            
        Returns:
            Vector de estado estabilizado
        """
        return np.tanh(state * self.damping_factor)

    def reset(self) -> None:
        """Reinicia los acumuladores temporales del guardián."""
        self.divergence_history.clear()
        self.last_lyapunov_exponent = 0.0
        self._prev_delta = None
        self._prev_state = None
