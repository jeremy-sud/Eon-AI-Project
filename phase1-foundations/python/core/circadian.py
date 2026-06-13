"""
Proyecto Eón - Ciclos Circadianos
===================================

"Como el sol guía el cuerpo, el tiempo guía la mente."

Este módulo implementa ritmos circadianos para el sistema Eón:
modulación periódica de parámetros de aprendizaje, activación y
comportamiento basada en el tiempo del sistema.

INSPIRACIÓN BIOLÓGICA:
─────────────────────
Los organismos vivos regulan sus funciones cognitivas según el
ciclo día/noche (circadiano) y ciclos ultradianos más cortos.
En el cerebro:
  - La consolidación de memoria ocurre principalmente durante el sueño
  - La atención y aprendizaje son máximos en ciertos momentos del día
  - Las oscilaciones theta/gamma siguen ritmos ultradianos

IMPLEMENTACIÓN:
───────────────
CircadianClock mantiene un oscilador interno configurable y
expone un CircadianState con los parámetros modulados actuales.

Puede acoplarse a cualquier ESN o componente del sistema para
modular dinámicamente:
  - Tasa de aprendizaje
  - Factor de olvido (forgetting_factor en StreamingESN)
  - Umbral de anomalías
  - Nivel de ruido del reservoir

(c) 2024 Proyecto Eón - Jeremy Arias Solano
"""

import numpy as np
import time
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Dict, Callable, List, Tuple

logger = logging.getLogger(__name__)


class CircadianPhase(Enum):
    """
    Fases del ciclo circadiano del sistema.

    Inspiradas en el ciclo biológico, adaptadas al contexto computacional.
    """
    DAWN = "dawn"           # Despertar: incremento gradual de actividad
    PEAK = "peak"           # Máxima actividad y capacidad de aprendizaje
    AFTERNOON = "afternoon"  # Actividad sostenida, consolidación
    DUSK = "dusk"           # Declive: reducción de actividad
    NIGHT = "night"         # Mínima actividad, consolidación profunda
    REM = "rem"             # Ciclo de sueño activo: reorganización


# Fracción del ciclo para cada fase
_PHASE_BOUNDARIES: list[Tuple[float, CircadianPhase]] = [
    (0.10, CircadianPhase.DAWN),
    (0.35, CircadianPhase.PEAK),
    (0.55, CircadianPhase.AFTERNOON),
    (0.70, CircadianPhase.DUSK),
    (0.90, CircadianPhase.NIGHT),
    (1.00, CircadianPhase.REM),
]


def _phase_for_fraction(f: float) -> CircadianPhase:
    """Retorna la fase circadiana para una fracción [0, 1) del ciclo."""
    f = f % 1.0
    for boundary, phase in _PHASE_BOUNDARIES:
        if f < boundary:
            return phase
    return CircadianPhase.REM


@dataclass
class CircadianState:
    """
    Estado instante del reloj circadiano.

    Todos los valores de modulación están en [0, 1]:
      - 1.0 = máximo (fase PEAK)
      - 0.0 = mínimo (fase NIGHT/REM)
    """
    phase: CircadianPhase
    cycle_fraction: float       # Posición en el ciclo [0, 1)
    cycle_count: int            # Número de ciclos completos

    # Moduladores (normalizados a [0, 1])
    learning_rate_mod: float    # Multiplica la tasa de aprendizaje
    forgetting_mod: float       # Modula el factor de olvido (λ más bajo = más olvido)
    noise_mod: float            # Modula el ruido del reservoir
    anomaly_threshold_mod: float  # Modula el umbral de detección de anomalías

    # Señal cruda del oscilador
    oscillator_value: float     # Valor sin normalizar del oscilador principal

    @property
    def energy(self) -> float:
        """Alias del nivel de energía o actividad del estado circadiano (basado en learning_rate_mod)."""
        return self.learning_rate_mod

    def to_dict(self) -> Dict:
        return {
            "phase": self.phase.value,
            "cycle_fraction": round(self.cycle_fraction, 4),
            "cycle_count": self.cycle_count,
            "learning_rate_mod": round(self.learning_rate_mod, 4),
            "forgetting_mod": round(self.forgetting_mod, 4),
            "noise_mod": round(self.noise_mod, 4),
            "anomaly_threshold_mod": round(self.anomaly_threshold_mod, 4),
            "energy": round(self.energy, 4),
        }


class CircadianClock:
    """
    Reloj circadiano del sistema Eón.

    Mantiene un oscilador armónico multi-frecuencia y expone
    el estado actual (CircadianState) con moduladores normalizados.

    El oscilador combina:
      - Componente fundamental (período = `period_steps`)
      - Armónico ultradiano (período = period/4)
      - Componente de fase REM (modulación adicional)

    Ejemplo:
        >>> clock = CircadianClock(period_steps=1440)  # 1 ciclo / día
        >>> for t in range(1440):
        ...     state = clock.tick()
        ...     esn.noise = base_noise * state.noise_mod
        ...     print(state.phase)
    """

    def __init__(
        self,
        period_steps: int = 1000,
        ultradiant_ratio: float = 4.0,
        phase_offset: float = 0.0,
        random_state: Optional[int] = None,
    ):
        """
        Inicializa el reloj circadiano.

        Args:
            period_steps: Número de ticks que dura un ciclo completo
            ultradiant_ratio: Divisor del período para el armónico ultradiano
            phase_offset: Desplazamiento de fase inicial [0, 1)
            random_state: Semilla aleatoria (para perturbaciones estocásticas)
        """
        if period_steps < 4:
            raise ValueError("period_steps debe ser >= 4")
        if not (0.0 <= phase_offset < 1.0):
            raise ValueError("phase_offset debe estar en [0, 1)")

        self.period_steps = period_steps
        self.ultradiant_ratio = max(2.0, ultradiant_ratio)
        self.phase_offset = phase_offset
        self._rng = np.random.default_rng(random_state)

        self._tick_count: int = 0
        self._callbacks: List[Callable[[CircadianState], None]] = []

    # ─── Propiedades ──────────────────────────────────────────────────────────

    @property
    def current_fraction(self) -> float:
        """Fracción del ciclo actual [0, 1)."""
        return (self._tick_count / self.period_steps + self.phase_offset) % 1.0

    @property
    def current_phase(self) -> CircadianPhase:
        """Fase circadiana actual."""
        return _phase_for_fraction(self.current_fraction)

    @property
    def cycle_count(self) -> int:
        """Número de ciclos completos transcurridos."""
        return self._tick_count // self.period_steps

    # ─── Oscilador ────────────────────────────────────────────────────────────

    def _oscillator(self, fraction: float) -> float:
        """
        Oscilador multi-armónico principal.

        Combina:
          - Seno fundamental (período completo)
          - Armónico ultradiano (período / ratio)
          - Modulación de REM (pico adicional al final del ciclo)

        Returns:
            Valor en [-1, 1] (centrado en 0)
        """
        theta = 2.0 * np.pi * fraction
        fundamental = np.sin(theta - np.pi / 2)  # 0 en DAWN, 1 en PEAK, -1 en NIGHT

        theta_ultra = 2.0 * np.pi * fraction * self.ultradiant_ratio
        ultradiant = 0.25 * np.sin(theta_ultra)

        # REM: pequeña elevación al final del ciclo (0.85-1.0)
        rem_window = np.exp(-((fraction - 0.92) ** 2) / (2 * 0.02 ** 2)) * 0.2

        return float(fundamental + ultradiant + rem_window)

    def _normalize_oscillator(self, raw: float) -> float:
        """
        Normaliza el valor del oscilador a [0, 1].

        El oscilador tiene rango aproximado [-1.25, 1.45] con los armónicos.
        """
        raw_min, raw_max = -1.45, 1.45
        normalized = (raw - raw_min) / (raw_max - raw_min)
        return float(np.clip(normalized, 0.0, 1.0))

    # ─── Cálculo de moduladores ───────────────────────────────────────────────

    def _compute_modulators(self, fraction: float) -> Tuple[float, float, float, float]:
        """
        Calcula los 4 moduladores normalizados para una fracción dada.

        Returns:
            (learning_rate_mod, forgetting_mod, noise_mod, anomaly_threshold_mod)
        """
        raw = self._oscillator(fraction)
        base = self._normalize_oscillator(raw)

        phase = _phase_for_fraction(fraction)

        # Aprendizaje máximo en PEAK, mínimo en NIGHT
        learning_rate_mod = base

        # Factor de olvido: en NIGHT y REM hay más olvido (consolidación)
        # forgetting_mod bajo → λ más bajo → más olvido (biológicamente correcto)
        if phase in (CircadianPhase.NIGHT, CircadianPhase.REM):
            forgetting_mod = max(0.05, 1.0 - base)
        else:
            forgetting_mod = 0.5 + 0.5 * base

        # Ruido: mayor en DAWN y REM (exploración / reorganización)
        if phase in (CircadianPhase.DAWN, CircadianPhase.REM):
            noise_mod = max(0.3, 1.0 - base * 0.5)
        else:
            noise_mod = base * 0.5

        # Umbral de anomalías: más sensible de día, más permisivo de noche
        anomaly_threshold_mod = base

        return learning_rate_mod, forgetting_mod, noise_mod, anomaly_threshold_mod

    # ─── API pública ──────────────────────────────────────────────────────────

    def tick(self, n: int = 1) -> "CircadianState":
        """
        Avanza el reloj n ticks y devuelve el estado actual.

        Args:
            n: Número de ticks a avanzar (≥ 1)

        Returns:
            CircadianState con todos los moduladores actualizados
        """
        self._tick_count += max(1, n)
        return self.state()

    def state(self) -> CircadianState:
        """Devuelve el estado actual sin avanzar el reloj."""
        fraction = self.current_fraction
        raw = self._oscillator(fraction)
        lr_mod, forget_mod, noise_mod, anom_mod = self._compute_modulators(fraction)

        s = CircadianState(
            phase=self.current_phase,
            cycle_fraction=fraction,
            cycle_count=self.cycle_count,
            learning_rate_mod=lr_mod,
            forgetting_mod=forget_mod,
            noise_mod=noise_mod,
            anomaly_threshold_mod=anom_mod,
            oscillator_value=raw,
        )

        for cb in self._callbacks:
            try:
                cb(s)
            except Exception as e:
                logger.warning(f"CircadianClock: callback error: {e}")

        return s

    def add_callback(self, fn: Callable[[CircadianState], None]) -> None:
        """Registra una función que se llama en cada tick."""
        self._callbacks.append(fn)

    def reset(self, phase_offset: Optional[float] = None) -> None:
        """Reinicia el reloj. Si se pasa phase_offset, lo actualiza."""
        self._tick_count = 0
        if phase_offset is not None:
            if not (0.0 <= phase_offset < 1.0):
                raise ValueError("phase_offset debe estar en [0, 1)")
            self.phase_offset = phase_offset

    def full_cycle(self) -> List[CircadianState]:
        """
        Simula un ciclo completo y devuelve todos los estados.

        Útil para visualización o pre-computación de tablas.
        """
        saved_tick = self._tick_count
        self._tick_count = 0
        states = [self.tick() for _ in range(self.period_steps)]
        self._tick_count = saved_tick
        return states

    def schedule_at_phase(
        self,
        phase: CircadianPhase,
        fn: Callable[[], None],
        once: bool = False,
    ) -> None:
        """
        Registra una función para ejecutarse cuando el reloj entre en una fase.

        Args:
            phase: Fase en la que ejecutar la función
            fn: Función sin argumentos a ejecutar
            once: Si True, se ejecuta solo la primera vez
        """
        executed = {"done": False}

        def _cb(state: CircadianState) -> None:
            if state.phase == phase:
                if not once or not executed["done"]:
                    fn()
                    executed["done"] = True

        self.add_callback(_cb)

    def summary(self) -> Dict:
        """Resumen del estado actual del reloj."""
        s = self.state()
        return {
            "tick": self._tick_count,
            "period_steps": self.period_steps,
            **s.to_dict(),
        }
