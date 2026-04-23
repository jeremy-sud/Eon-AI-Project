"""
Proyecto Eón - Reservoir Morphing Dinámico
===========================================

"La forma sigue a la función. El reservorio se moldea a su tarea."

Un ESN cuya topología cambia entre configuraciones óptimas según
el tipo de datos que procesa. No solo poda/regenera conexiones —
modifica la topología completa (anillo, small-world, scale-free…).

TOPOLOGÍAS DISPONIBLES:
  - RING:        Para secuencias cíclicas / datos periódicos
  - SMALL_WORLD: Para patrones complejos con correlaciones largas
  - SCALE_FREE:  Distribución power-law (hubs altamente conectados)
  - RANDOM:      Topología ESN estándar (aleatoria)
  - LATTICE:     Para datos con estructura espacial 2D

PROCESO DE MORPHING:
  1. Detectar topología más adecuada vía métricas de activación
  2. Usar Tzimtzum (poda) para vaciar la topología actual
  3. Regenerar con nueva topología preservando W_out

Mejora esperada de MSE: >20 % vs topología fija
Tiempo de adaptación: <1000 pasos

(c) 2024 Proyecto Eón - Jeremy Arias Solano
"""

import numpy as np
import logging
from enum import Enum, auto
from typing import Optional, Dict, Tuple
import os

from plasticity.hebbian_tzimtzum import HebbianTzimtzumESN
from plasticity.tzimtzum import TzimtzumConfig

logger = logging.getLogger(__name__)

class TopologyType(Enum):
    """Tipos de topología disponibles para el reservoir."""
    RING = "ring"             # Anillo: cada neurona conectada a sus k vecinos
    SMALL_WORLD = "small_world"  # Watts-Strogatz: alta agrupación, caminos cortos
    SCALE_FREE = "scale_free"    # Barabási-Albert: distribución power-law
    RANDOM = "random"            # Estándar ESN (aleatoria)
    LATTICE = "lattice"          # Rejilla 2D (√N × √N)

def _build_ring(n: int, k: int, rng: np.random.Generator, spectral_radius: float) -> np.ndarray:
    """
    Construye topología de anillo: cada neurona conectada a sus k vecinos más cercanos.

    Args:
        n: Tamaño del reservorio
        k: Número de vecinos por lado (total 2k conexiones por neurona)
        rng: Generador aleatorio
        spectral_radius: Radio espectral objetivo
    """
    W = np.zeros((n, n))
    for i in range(n):
        for d in range(1, k + 1):
            j_plus = (i + d) % n
            j_minus = (i - d) % n
            W[i, j_plus] = rng.standard_normal()
            W[i, j_minus] = rng.standard_normal()
    return _scale_spectral_radius(W, spectral_radius)

def _build_small_world(n: int, k: int, p: float, rng: np.random.Generator, spectral_radius: float) -> np.ndarray:
    """
    Watts-Strogatz small-world: anillo con rewiring aleatorio con probabilidad p.

    Args:
        n: Tamaño del reservorio
        k: Vecinos iniciales por lado
        p: Probabilidad de rewiring (0=anillo, 1=aleatorio)
        rng: Generador aleatorio
        spectral_radius: Radio espectral objetivo
    """
    W = np.zeros((n, n))
    # Fase 1: Anillo base
    for i in range(n):
        for d in range(1, k + 1):
            j = (i + d) % n
            W[i, j] = rng.standard_normal()

    # Fase 2: Rewiring
    for i in range(n):
        for d in range(1, k + 1):
            if rng.random() < p:
                j_old = (i + d) % n
                j_new = rng.integers(0, n)
                # Evitar self-loops y duplicados
                attempts = 0
                while (j_new == i or W[i, j_new] != 0) and attempts < n:
                    j_new = rng.integers(0, n)
                    attempts += 1
                if j_new != i and W[i, j_new] == 0:
                    W[i, j_old] = 0.0
                    W[i, j_new] = rng.standard_normal()

    return _scale_spectral_radius(W, spectral_radius)

def _build_scale_free(n: int, m: int, rng: np.random.Generator, spectral_radius: float) -> np.ndarray:
    """
    Barabási-Albert: preferential attachment → distribución power-law de grados.

    Args:
        n: Tamaño del reservorio
        m: Conexiones añadidas por cada nuevo nodo (m >= 1)
        rng: Generador aleatorio
        spectral_radius: Radio espectral objetivo
    """
    W = np.zeros((n, n))
    m = max(1, min(m, n - 1))

    # Iniciar con un grafo completo de m+1 nodos
    init_n = min(m + 1, n)
    for i in range(init_n):
        for j in range(i):
            W[i, j] = rng.standard_normal()
            W[j, i] = rng.standard_normal()

    # Grado acumulado (suma de conexiones por nodo)
    degree = np.array([np.sum(W[i] != 0) for i in range(n)], dtype=float)

    for new_node in range(init_n, n):
        # Probabilidad proporcional al grado
        probs = degree.copy()
        probs[new_node:] = 0.0  # Solo nodos ya existentes
        total = probs.sum()
        if total <= 0:
            probs[:new_node] = 1.0 / new_node
        else:
            probs = probs / total

        # Seleccionar m objetivos sin reemplazo
        targets = set()
        for _ in range(m):
            t = int(rng.choice(n, p=probs))
            attempts = 0
            while (t == new_node or t in targets or t >= new_node) and attempts < n:
                t = int(rng.choice(n, p=probs))
                attempts += 1
            if t != new_node and t not in targets and t < new_node:
                targets.add(t)

        for t in targets:
            W[new_node, t] = rng.standard_normal()
            W[t, new_node] = rng.standard_normal()
            degree[t] += 1
            degree[new_node] += 1

    return _scale_spectral_radius(W, spectral_radius)

def _build_random(n: int, sparsity: float, rng: np.random.Generator, spectral_radius: float) -> np.ndarray:
    """Topología aleatoria estándar ESN."""
    W = rng.standard_normal((n, n))
    mask = rng.random((n, n)) > sparsity
    W *= mask
    return _scale_spectral_radius(W, spectral_radius)

def _build_lattice(n: int, rng: np.random.Generator, spectral_radius: float) -> np.ndarray:
    """
    Rejilla 2D: √N × √N, con conexiones a los 4 vecinos cardinales.

    Para n no cuadrado perfecto, se redondea y recorta.
    """
    side = max(1, int(np.ceil(np.sqrt(n))))
    W = np.zeros((n, n))
    for i in range(n):
        row, col = divmod(i, side)
        neighbors = []
        if row > 0:
            neighbors.append((row - 1) * side + col)  # arriba
        if row < side - 1:
            neighbors.append((row + 1) * side + col)  # abajo
        if col > 0:
            neighbors.append(row * side + col - 1)     # izquierda
        if col < side - 1:
            neighbors.append(row * side + col + 1)     # derecha
        for nb in neighbors:
            if nb < n:
                W[i, nb] = rng.standard_normal()
    return _scale_spectral_radius(W, spectral_radius)

def _scale_spectral_radius(W: np.ndarray, target: float) -> np.ndarray:
    """Escala W para que su radio espectral sea target."""
    if not np.any(W != 0):
        return W
    try:
        eigs = np.abs(np.linalg.eigvals(W))
        current = eigs.max()
        if current > 1e-10:
            W = W * (target / current)
    except np.linalg.LinAlgError:
        pass
    return W

def build_topology(
    topology: TopologyType,
    n: int,
    spectral_radius: float,
    rng: np.random.Generator,
    sparsity: float = 0.9,
) -> np.ndarray:
    """
    Función fábrica: construye una matriz de reservorio con la topología indicada.

    Args:
        topology: Tipo de topología
        n: Tamaño del reservorio
        spectral_radius: Radio espectral objetivo
        rng: Generador aleatorio
        sparsity: Solo relevante para RANDOM

    Returns:
        Matriz W de reservorio (n, n)
    """
    k = max(2, n // 10)  # vecinos para RING / SMALL_WORLD
    m = max(2, n // 20)  # conexiones nuevas para SCALE_FREE

    if topology == TopologyType.RING:
        return _build_ring(n, k=k, rng=rng, spectral_radius=spectral_radius)
    elif topology == TopologyType.SMALL_WORLD:
        return _build_small_world(n, k=k, p=0.1, rng=rng, spectral_radius=spectral_radius)
    elif topology == TopologyType.SCALE_FREE:
        return _build_scale_free(n, m=m, rng=rng, spectral_radius=spectral_radius)
    elif topology == TopologyType.LATTICE:
        return _build_lattice(n, rng=rng, spectral_radius=spectral_radius)
    else:  # RANDOM (default)
        return _build_random(n, sparsity=sparsity, rng=rng, spectral_radius=spectral_radius)

# ─── Métricas para auto-morphing ─────────────────────────────────────────────

def _measure_autocorrelation(states: np.ndarray, lag: int = 5) -> float:
    """Autocorrelación media de las activaciones del reservorio."""
    if states.shape[0] < lag + 2:
        return 0.0
    corrs = []
    for i in range(states.shape[1]):
        s = states[:, i]
        if s.std() < 1e-8:
            continue
        c = float(np.corrcoef(s[:-lag], s[lag:])[0, 1])
        if np.isfinite(c):
            corrs.append(c)
    return float(np.mean(corrs)) if corrs else 0.0

def _measure_variance(states: np.ndarray) -> float:
    """Varianza media de activaciones del reservorio."""
    return float(np.mean(np.var(states, axis=0)))

def suggest_topology(states: np.ndarray) -> TopologyType:
    """
    Detecta la topología más adecuada basándose en las activaciones del reservorio.

    Heurística:
      - Alta autocorrelación (>0.7) → RING (buena para secuencias periódicas)
      - Baja varianza (<0.05)       → SCALE_FREE (hubs para amplificar señal)
      - Alta varianza (>0.3)        → SMALL_WORLD (balance memoria/diversidad)
      - Resto                       → RANDOM

    Args:
        states: Matriz (T, n_reservoir) de estados del reservorio

    Returns:
        TopologyType sugerida
    """
    if states.shape[0] < 10:
        return TopologyType.RANDOM

    autocorr = _measure_autocorrelation(states)
    variance = _measure_variance(states)

    if autocorr > 0.7:
        return TopologyType.RING
    elif variance < 0.05:
        return TopologyType.SCALE_FREE
    elif variance > 0.3:
        return TopologyType.SMALL_WORLD
    else:
        return TopologyType.RANDOM

# ─── MorphingESN ─────────────────────────────────────────────────────────────

class MorphingESN(HebbianTzimtzumESN):
    """
    ESN con topología dinámica que se adapta al tipo de datos.

    Hereda de HebbianTzimtzumESN para tener:
      - Plasticidad Hebbiana (fortalece conexiones útiles)
      - Protocolo Tzimtzum (poda conexiones débiles)
      - Morphing de topología (cambia la estructura completa)

    El morphing usa Tzimtzum para vaciar el reservoir actual y
    regenerarlo con la nueva topología preservando W_out (la
    única parte que "aprendió").

    Ejemplo:
        >>> esn = MorphingESN(n_inputs=1, n_reservoir=100, n_outputs=1)
        >>> esn.fit(X_train, y_train)
        >>>
        >>> # Morphing manual
        >>> esn.morph_to(TopologyType.RING)
        >>>
        >>> # Auto-morphing basado en los datos actuales
        >>> esn.adapt_online(X_new)
        >>> new_topology = esn.auto_morph()
    """

    def __init__(
        self,
        n_inputs: int = 1,
        n_reservoir: int = 100,
        n_outputs: int = 1,
        spectral_radius: float = 0.9,
        sparsity: float = 0.9,
        noise: float = 0.001,
        learning_rate: float = 0.001,
        base_topology: TopologyType = TopologyType.RANDOM,
        tzimtzum_config: Optional[TzimtzumConfig] = None,
        random_state: Optional[int] = None,
    ):
        """
        Inicializa MorphingESN.

        Args:
            n_inputs: Dimensión de entrada
            n_reservoir: Número de neuronas en el reservoir
            n_outputs: Dimensión de salida
            spectral_radius: Radio espectral objetivo
            sparsity: Sparsity para topología RANDOM
            noise: Ruido de regularización
            learning_rate: Tasa de aprendizaje Hebbiano
            base_topology: Topología inicial del reservoir
            tzimtzum_config: Config del protocolo Tzimtzum
            random_state: Semilla aleatoria
        """
        super().__init__(
            n_inputs=n_inputs,
            n_reservoir=n_reservoir,
            n_outputs=n_outputs,
            spectral_radius=spectral_radius,
            sparsity=sparsity,
            noise=noise,
            learning_rate=learning_rate,
            tzimtzum_config=tzimtzum_config,
            random_state=random_state,
        )
        self._morph_rng = np.random.default_rng(random_state)
        self.current_topology = base_topology
        self._morph_history: list[Dict] = []

        # Aplicar topología inicial (si no es RANDOM, regenerar)
        if base_topology != TopologyType.RANDOM:
            self._apply_topology(base_topology)

    # ─── Construcción de topología ─────────────────────────────────────────────

    def _apply_topology(self, topology: TopologyType) -> None:
        """Regenera W_reservoir con la topología indicada."""
        self.W_reservoir = build_topology(
            topology=topology,
            n=self.n_reservoir,
            spectral_radius=self.spectral_radius,
            rng=self._morph_rng,
            sparsity=self.sparsity,
        )
        self._connection_mask = (self.W_reservoir != 0)
        self._hebbian_contribution = np.zeros_like(self.W_reservoir)
        self.state = np.zeros(self.n_reservoir)

    # ─── API pública ──────────────────────────────────────────────────────────

    def morph_to(
        self,
        target: TopologyType,
        transition_steps: int = 100,
    ) -> Dict:
        """
        Transición suave entre topologías.

        Proceso:
          1. Tzimtzum rápido (vaciar reservoir actual)
          2. Regenerar con nueva topología
          3. Registrar en historial

        Args:
            target: Topología objetivo
            transition_steps: Pasos de adaptación post-morphing
                (reservado para uso futuro; actualmente no se ejecutan)

        Returns:
            Diccionario con estadísticas del morphing
        """
        if target == self.current_topology:
            return {"morphed": False, "reason": "Ya en topología objetivo"}

        prev = self.current_topology

        # Vaciar mediante Tzimtzum (poda total)
        self.dark_night(fraction=0.95)

        # Regenerar
        self._apply_topology(target)
        self.current_topology = target

        record = {
            "from": prev.value,
            "to": target.value,
            "step": self._step_count,
        }
        self._morph_history.append(record)

        logger.info(
            f"MorphingESN: {prev.value} → {target.value} "
            f"en paso {self._step_count}"
        )
        return {"morphed": True, **record}

    def auto_morph(
        self,
        observation_steps: int = 200,
        force: bool = False,
    ) -> TopologyType:
        """
        Detecta si la topología actual es subóptima y hace morphing automático.

        Recopila `observation_steps` estados del reservoir (usando la señal
        más reciente si ya se procesaron datos), analiza las activaciones y
        sugiere la topología más adecuada.

        Args:
            observation_steps: Pasos de estado a analizar
            force: Si True, hace morphing aunque la topología sugerida sea la actual

        Returns:
            Topología resultante (nueva o la misma si no cambió)
        """
        # Registrar estados actuales ejecutando señal nula
        states = []
        temp_state = self.state.copy()
        rng_tmp = np.random.default_rng(0)

        for _ in range(observation_steps):
            inp = rng_tmp.standard_normal(self.n_inputs) * 0.01
            self._update_state(inp)
            states.append(self.state.copy())

        self.state = temp_state  # Restaurar estado

        states_array = np.array(states)
        suggested = suggest_topology(states_array)

        if suggested != self.current_topology or force:
            self.morph_to(suggested)

        return self.current_topology

    def topology_metrics(self, observation_steps: int = 100) -> Dict:
        """
        Calcula métricas de la topología actual del reservoir.

        Returns:
            Diccionario con autocorrelación, varianza, sparsity y topología actual
        """
        states = []
        temp_state = self.state.copy()
        rng_tmp = np.random.default_rng(1)

        for _ in range(observation_steps):
            inp = rng_tmp.standard_normal(self.n_inputs) * 0.01
            self._update_state(inp)
            states.append(self.state.copy())

        self.state = temp_state
        states_array = np.array(states)

        autocorr = _measure_autocorrelation(states_array)
        variance = _measure_variance(states_array)
        n_connections = int(np.sum(self.W_reservoir != 0))
        sparsity = 1.0 - n_connections / self.n_reservoir ** 2

        return {
            "topology": self.current_topology.value,
            "autocorrelation": round(autocorr, 4),
            "activation_variance": round(variance, 6),
            "sparsity": round(sparsity, 4),
            "n_connections": n_connections,
            "morph_count": len(self._morph_history),
        }

    def morph_history(self) -> list:
        """Devuelve el historial de morphings realizados."""
        return list(self._morph_history)
