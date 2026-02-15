"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           TZIMTZUM PROTOCOL                                   ║
║                        Divine Contraction Engine                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  "Para que la creación exista, lo infinito debe contraerse."                  ║
║                              - Isaac Luria, 1570                              ║
║                                                                               ║
║  En la Cábala Luriana, Tzimtzum describe el proceso por el cual Ein Sof      ║
║  (lo Infinito) se contrajo para crear un vacío (Challal) donde el universo   ║
║  finito pudiera existir. Sin esta contracción, la luz infinita no dejaría    ║
║  espacio para la individualidad.                                              ║
║                                                                               ║
║  PRINCIPIO COMPUTACIONAL:                                                     ║
║  ────────────────────────                                                     ║
║  Para aprender algo nuevo, primero debo olvidar.                              ║
║                                                                               ║
║  Este módulo implementa poda sináptica inspirada en:                          ║
║  1. Tzimtzum cabalístico (contracción divina)                                 ║
║  2. Poda sináptica biológica (developmental pruning)                          ║
║  3. "Dark Night of the Soul" - San Juan de la Cruz                            ║
║                                                                               ║
║  CICLO DE CONTRACCIÓN:                                                        ║
║  ─────────────────────                                                        ║
║                                                                               ║
║  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ║
║  │  PLENITUD   │───▶│ DARK NIGHT  │───▶│   VACÍO    │───▶│ RENACIMIENTO │    ║
║  │ (Saturación)│    │   (Poda)    │    │ (Challal)  │    │ (Regrowth)   │    ║
║  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    ║
║        ▲                                                         │           ║
║        └─────────────────────────────────────────────────────────┘           ║
║                                                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional, Tuple, Dict, List, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import sys
import os

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from esn.esn import EchoStateNetwork


class ContractionPhase(Enum):
    """
    Fases del ciclo Tzimtzum.
    
    El proceso de contracción-expansión es cíclico, reflejando
    el ritmo cósmico de creación y destrucción.
    """
    PLENITUD = auto()       # Red saturada, muchas conexiones
    DARK_NIGHT = auto()     # Proceso de poda activo
    CHALLAL = auto()        # Vacío primordial, mínimas conexiones
    RENACIMIENTO = auto()   # Recrecimiento de conexiones


@dataclass
class TzimtzumState:
    """
    Estado del proceso de contracción.
    
    Rastrea métricas del ciclo Tzimtzum para monitoreo
    y ajuste dinámico.
    """
    phase: ContractionPhase = ContractionPhase.PLENITUD
    
    # Métricas de poda
    total_connections: int = 0
    pruned_connections: int = 0
    regrown_connections: int = 0
    
    # Historial
    pruning_cycles: int = 0
    memory_saved_bytes: int = 0
    
    # Umbrales dinámicos
    current_threshold: float = 0.0
    min_weight_survived: float = 0.0
    max_weight_pruned: float = 0.0
    
    # Eficiencia
    compression_ratio: float = 1.0
    
    def to_dict(self) -> dict:
        """Serializa el estado a diccionario."""
        return {
            'phase': self.phase.name,
            'total_connections': self.total_connections,
            'pruned_connections': self.pruned_connections,
            'regrown_connections': self.regrown_connections,
            'pruning_cycles': self.pruning_cycles,
            'memory_saved_bytes': self.memory_saved_bytes,
            'current_threshold': float(self.current_threshold),
            'compression_ratio': self.compression_ratio
        }


@dataclass
class TzimtzumConfig:
    """
    Configuración del protocolo Tzimtzum.
    
    Parámetros que controlan la intensidad y frecuencia
    de los ciclos de contracción.
    """
    # Fracción de conexiones a podar (default: 50% - número sagrado)
    pruning_fraction: float = 0.5
    
    # Frecuencia de Dark Night (cada N pasos de adaptación)
    dark_night_interval: int = 1000
    
    # Regrowth después de poda (fracción de lo podado)
    regrowth_fraction: float = 0.1
    
    # Umbral mínimo de peso para sobrevivir (absoluto)
    min_survival_weight: float = 1e-6
    
    # Número mínimo de conexiones (nunca bajar de esto)
    min_connections_fraction: float = 0.1
    
    # Forzar sparsity estructurada (preservar topología)
    preserve_topology: bool = True
    
    # Usar importancia basada en gradiente (si está disponible)
    use_gradient_importance: bool = False
    
    # Semilla para reproducibilidad del regrowth
    regrowth_seed: Optional[int] = None


class TzimtzumESN(EchoStateNetwork):
    """
    Echo State Network con protocolo de contracción Tzimtzum.
    
    Implementa poda sináptica dinámica inspirada en:
    - Tzimtzum cabalístico (contracción del infinito)
    - Poda sináptica biológica (adolescencia neuronal)
    - Lottery Ticket Hypothesis (redes sparse superiores)
    
    FILOSOFÍA:
    ──────────
    "La vasija que está llena no puede recibir más agua.
     Solo el vacío puede ser llenado."
    
    Una red saturada de conexiones pierde la capacidad de
    aprender patrones nuevos. El Tzimtzum crea espacio para
    el crecimiento futuro eliminando las conexiones más débiles.
    
    PROCESO:
    ────────
    1. PLENITUD: Red opera normalmente, acumulando conexiones
    2. DARK NIGHT: Identificar y podar el 50% más débil
    3. CHALLAL: Estado de vacío, mínima conectividad
    4. RENACIMIENTO: Regrowth selectivo de nuevas conexiones
    
    Ejemplo:
        >>> tzim = TzimtzumESN(
        ...     input_size=3,
        ...     reservoir_size=100,
        ...     config=TzimtzumConfig(pruning_fraction=0.5)
        ... )
        >>> 
        >>> # Entrenar normalmente
        >>> tzim.fit(X_train, y_train)
        >>> 
        >>> # Ejecutar Dark Night (poda)
        >>> stats = tzim.dark_night()
        >>> print(f"Podadas {stats['pruned_count']} conexiones")
        >>> 
        >>> # El reservoir ahora tiene 50% menos conexiones
        >>> # pero mantiene (o mejora) su capacidad
    """
    
    def __init__(
        self,
        n_inputs: int = 1,
        n_reservoir: int = 100,
        n_outputs: int = 1,
        spectral_radius: float = 0.9,
        sparsity: float = 0.9,
        noise: float = 0.001,
        config: Optional[TzimtzumConfig] = None,
        random_state: Optional[int] = None
    ):
        """
        Inicializa TzimtzumESN.
        
        Args:
            n_inputs: Dimensión de entrada
            n_reservoir: Número de neuronas en reservoir
            n_outputs: Dimensión de salida
            spectral_radius: Radio espectral del reservoir
            sparsity: Sparsity inicial (fracción de ceros)
            noise: Ruido de regularización
            config: Configuración Tzimtzum
            random_state: Semilla aleatoria
        """
        super().__init__(
            n_inputs=n_inputs,
            n_reservoir=n_reservoir,
            n_outputs=n_outputs,
            spectral_radius=spectral_radius,
            sparsity=sparsity,
            noise=noise,
            random_state=random_state
        )
        
        # Alias for compatibility
        self.n_reservoir = n_reservoir
        
        self.config = config or TzimtzumConfig()
        self.tzimtzum_state = TzimtzumState()
        
        # RNG para regrowth
        regrowth_seed = self.config.regrowth_seed or random_state
        self._regrowth_rng = np.random.default_rng(regrowth_seed)
        
        # Máscara de conexiones activas
        self._connection_mask = (self.W_reservoir != 0)
        
        # Importancia de conexiones (actualizada durante forward)
        self._connection_importance = np.zeros_like(self.W_reservoir)
        
        # Historial para análisis
        self._pruning_history: List[Dict] = []
        
        # Contador de pasos para auto-poda
        self._step_count = 0
        
        # Inicializar métricas
        self._update_state_metrics()
    
    def _update_state_metrics(self):
        """Actualiza métricas del estado Tzimtzum."""
        self.tzimtzum_state.total_connections = int(np.sum(self._connection_mask))
        
        # Calcular ratio de compresión
        max_connections = self.n_reservoir ** 2
        active = self.tzimtzum_state.total_connections
        self.tzimtzum_state.compression_ratio = active / max_connections if max_connections > 0 else 0
    
    def _calculate_connection_importance(self) -> np.ndarray:
        """
        Calcula la importancia de cada conexión.
        
        Por defecto usa magnitud absoluta, pero puede extenderse
        para usar gradientes u otras métricas.
        
        Returns:
            Matriz de importancia (misma forma que W_reservoir)
        """
        # Importancia básica: magnitud absoluta del peso
        importance = np.abs(self.W_reservoir)
        
        # Acumular importancia temporal (momentum)
        alpha = 0.9
        self._connection_importance = (
            alpha * self._connection_importance + 
            (1 - alpha) * importance
        )
        
        return self._connection_importance
    
    def dark_night(self, fraction: Optional[float] = None) -> Dict:
        """
        Ejecuta el proceso de Dark Night (poda masiva).
        
        "En la noche oscura del alma, brillan más las estrellas."
        - San Juan de la Cruz
        
        Este método elimina una fracción de las conexiones más débiles
        del reservoir, creando espacio para nuevo aprendizaje.
        
        Args:
            fraction: Fracción de conexiones a podar (default: config)
            
        Returns:
            Estadísticas del proceso de poda
        """
        fraction = fraction or self.config.pruning_fraction
        
        # Cambiar fase
        self.tzimtzum_state.phase = ContractionPhase.DARK_NIGHT
        
        # Calcular importancia actual
        importance = self._calculate_connection_importance()
        
        # Solo considerar conexiones activas
        active_connections = self._connection_mask.copy()
        active_importance = importance[active_connections]
        
        if len(active_importance) == 0:
            # Restaurar fase a CHALLAL ya que no hay nada que podar
            self.tzimtzum_state.phase = ContractionPhase.CHALLAL
            return {'pruned_count': 0, 'message': 'No hay conexiones que podar'}
        
        # Calcular umbral de poda (percentil basado en fracción)
        prune_percentile = fraction * 100
        threshold = np.percentile(active_importance, prune_percentile)
        
        # Asegurar mínimo de conexiones
        min_connections = int(self.n_reservoir ** 2 * self.config.min_connections_fraction)
        current_connections = np.sum(active_connections)
        max_to_prune = current_connections - min_connections
        
        if max_to_prune <= 0:
            # Restaurar fase a CHALLAL ya que se alcanzó el mínimo
            self.tzimtzum_state.phase = ContractionPhase.CHALLAL
            return {
                'pruned_count': 0, 
                'message': f'Ya en mínimo de conexiones ({min_connections})'
            }
        
        # Crear máscara de poda basada SOLO en importancia
        # Las conexiones por debajo del threshold serán podadas
        survival_mask = importance >= threshold
        
        # min_survival_weight es solo para evitar eliminar conexiones ya casi muertas
        # (no debería salvar conexiones que tienen peso pero baja importancia)
        # Solo protege conexiones que de otra forma sobrevivirían
        
        # Preservar topología si está configurado
        if self.config.preserve_topology:
            # Asegurar al menos una entrada y salida por neurona
            for i in range(self.n_reservoir):
                # Al menos una entrada
                if not np.any(survival_mask[:, i]):
                    best_in = np.argmax(np.abs(self.W_reservoir[:, i]))
                    survival_mask[best_in, i] = True
                # Al menos una salida
                if not np.any(survival_mask[i, :]):
                    best_out = np.argmax(np.abs(self.W_reservoir[i, :]))
                    survival_mask[i, best_out] = True
        
        # Aplicar poda
        pre_prune_connections = np.sum(self.W_reservoir != 0)
        
        prune_mask = ~survival_mask & active_connections
        pruned_count = np.sum(prune_mask)
        
        # Limitar poda a max_to_prune
        if pruned_count > max_to_prune:
            # Podar solo las menos importantes
            prune_indices = np.argwhere(prune_mask)
            prune_importance = importance[prune_mask]
            sorted_indices = np.argsort(prune_importance)
            
            # Mantener las más importantes entre las que iban a ser podadas
            keep_count = pruned_count - max_to_prune
            keep_indices = sorted_indices[-keep_count:]
            
            for idx in keep_indices:
                i, j = prune_indices[idx]
                prune_mask[i, j] = False
            
            pruned_count = max_to_prune
        
        # Ejecutar poda
        self.W_reservoir[prune_mask] = 0
        self._connection_mask = (self.W_reservoir != 0)
        
        # Renormalizar radio espectral
        self._normalize_spectral_radius()
        
        # Estadísticas
        post_prune_connections = np.sum(self.W_reservoir != 0)
        memory_saved = (pre_prune_connections - post_prune_connections) * 8  # 8 bytes per float64
        
        # Actualizar estado
        self.tzimtzum_state.pruned_connections += pruned_count
        self.tzimtzum_state.pruning_cycles += 1
        self.tzimtzum_state.memory_saved_bytes += memory_saved
        self.tzimtzum_state.current_threshold = threshold
        self.tzimtzum_state.phase = ContractionPhase.CHALLAL
        
        self._update_state_metrics()
        
        # Registrar en historial
        stats = {
            'cycle': self.tzimtzum_state.pruning_cycles,
            'pruned_count': int(pruned_count),
            'threshold': float(threshold),
            'pre_connections': int(pre_prune_connections),
            'post_connections': int(post_prune_connections),
            'memory_saved_bytes': int(memory_saved),
            'compression_ratio': self.tzimtzum_state.compression_ratio
        }
        self._pruning_history.append(stats)
        
        return stats
    
    def _normalize_spectral_radius(self):
        """Renormaliza el reservoir para mantener estabilidad."""
        eigenvalues = np.abs(np.linalg.eigvals(self.W_reservoir))
        current_radius = eigenvalues.max() if len(eigenvalues) > 0 else 0
        
        if current_radius > 0:
            self.W_reservoir *= self.spectral_radius / current_radius
    
    def renacimiento(self, fraction: Optional[float] = None) -> Dict:
        """
        Proceso de regrowth controlado después del Dark Night.
        
        "De la nada, algo nuevo puede nacer."
        
        Permite que nuevas conexiones emerjan en el vacío
        creado por el Tzimtzum.
        
        Args:
            fraction: Fracción de conexiones podadas a recrecer
            
        Returns:
            Estadísticas del regrowth
        """
        fraction = fraction or self.config.regrowth_fraction
        
        self.tzimtzum_state.phase = ContractionPhase.RENACIMIENTO
        
        # Calcular cuántas conexiones regenerar
        pruned_this_cycle = self.tzimtzum_state.pruned_connections
        regrow_count = int(pruned_this_cycle * fraction)
        
        if regrow_count == 0:
            self.tzimtzum_state.phase = ContractionPhase.PLENITUD
            return {'regrown_count': 0, 'message': 'No hay espacio para regrowth'}
        
        # Encontrar posiciones vacías
        empty_positions = ~self._connection_mask
        empty_indices = np.argwhere(empty_positions)
        
        if len(empty_indices) == 0:
            return {'regrown_count': 0, 'message': 'No hay posiciones vacías'}
        
        # Seleccionar posiciones para regrowth
        regrow_count = min(regrow_count, len(empty_indices))
        selected_indices = self._regrowth_rng.choice(
            len(empty_indices), 
            size=regrow_count, 
            replace=False
        )
        
        # Crear nuevas conexiones con pesos pequeños
        for idx in selected_indices:
            i, j = empty_indices[idx]
            # Peso inicial pequeño (debe ganarse su lugar)
            new_weight = self._regrowth_rng.uniform(-0.1, 0.1)
            self.W_reservoir[i, j] = new_weight
        
        # Actualizar máscara y métricas
        self._connection_mask = (self.W_reservoir != 0)
        self.tzimtzum_state.regrown_connections += regrow_count
        
        # Renormalizar
        self._normalize_spectral_radius()
        
        self._update_state_metrics()
        
        # Volver a plenitud
        self.tzimtzum_state.phase = ContractionPhase.PLENITUD
        
        return {
            'regrown_count': regrow_count,
            'new_compression_ratio': self.tzimtzum_state.compression_ratio
        }
    
    def full_tzimtzum_cycle(self) -> Dict:
        """
        Ejecuta un ciclo completo de Tzimtzum.
        
        PLENITUD → DARK NIGHT → CHALLAL → RENACIMIENTO → PLENITUD
        
        Returns:
            Estadísticas del ciclo completo
        """
        # Fase 1: Dark Night
        dark_stats = self.dark_night()
        
        # Fase 2: Renacimiento
        rebirth_stats = self.renacimiento()
        
        return {
            'dark_night': dark_stats,
            'renacimiento': rebirth_stats,
            'final_connections': self.tzimtzum_state.total_connections,
            'total_cycles': self.tzimtzum_state.pruning_cycles
        }
    
    def _update_state(self, input_vector: np.ndarray) -> np.ndarray:
        """
        Actualiza estado con tracking de importancia.
        
        Además del forward normal, acumula información sobre
        qué conexiones están siendo utilizadas activamente.
        """
        # Forward normal
        new_state = super()._update_state(input_vector)
        
        # Actualizar importancia basada en activación
        # Conexiones usadas por neuronas activas son más importantes
        activation_importance = np.outer(
            np.abs(new_state),  # Post-synaptic
            np.abs(self.state)  # Pre-synaptic
        )
        
        alpha = 0.95
        self._connection_importance = (
            alpha * self._connection_importance +
            (1 - alpha) * activation_importance * np.abs(self.W_reservoir)
        )
        
        # Auto-poda si está configurado
        self._step_count += 1
        if (self.config.dark_night_interval > 0 and 
            self._step_count % self.config.dark_night_interval == 0):
            self.full_tzimtzum_cycle()
        
        return new_state
    
    def get_sparsity_report(self) -> Dict:
        """
        Genera reporte detallado de sparsity actual.
        
        Returns:
            Diccionario con métricas de sparsity
        """
        total_possible = self.n_reservoir ** 2
        active = np.sum(self._connection_mask)
        
        # Distribución de pesos
        active_weights = self.W_reservoir[self._connection_mask]
        
        if len(active_weights) > 0:
            weight_stats = {
                'mean': float(np.mean(active_weights)),
                'std': float(np.std(active_weights)),
                'min': float(np.min(active_weights)),
                'max': float(np.max(active_weights)),
                'median': float(np.median(active_weights))
            }
        else:
            weight_stats = {'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'median': 0}
        
        # Conectividad por neurona
        in_degree = np.sum(self._connection_mask, axis=0)
        out_degree = np.sum(self._connection_mask, axis=1)
        
        return {
            'total_possible_connections': total_possible,
            'active_connections': int(active),
            'sparsity': 1 - (active / total_possible),
            'compression_ratio': self.tzimtzum_state.compression_ratio,
            'weight_statistics': weight_stats,
            'connectivity': {
                'mean_in_degree': float(np.mean(in_degree)),
                'mean_out_degree': float(np.mean(out_degree)),
                'isolated_neurons': int(np.sum((in_degree == 0) & (out_degree == 0)))
            },
            'tzimtzum_state': self.tzimtzum_state.to_dict(),
            'pruning_history': self._pruning_history
        }
    
    def visualize_contraction(self) -> str:
        """
        Genera visualización ASCII del estado de contracción.
        
        Returns:
            String con visualización ASCII
        """
        phase = self.tzimtzum_state.phase.name
        ratio = self.tzimtzum_state.compression_ratio
        cycles = self.tzimtzum_state.pruning_cycles
        
        # Barra de compresión visual
        bar_width = 40
        filled = int(ratio * bar_width)
        empty = bar_width - filled
        bar = '█' * filled + '░' * empty
        
        # Fase emoji
        phase_emoji = {
            'PLENITUD': '🌕',
            'DARK_NIGHT': '🌑',
            'CHALLAL': '⚫',
            'RENACIMIENTO': '🌅'
        }
        
        viz = f"""
╔════════════════════════════════════════════════════╗
║              TZIMTZUM STATE MONITOR                ║
╠════════════════════════════════════════════════════╣
║  Phase: {phase_emoji.get(phase, '○')} {phase:15s}                  ║
║                                                    ║
║  Compression: [{bar}]                              ║
║  Ratio: {ratio:.1%} of original connections         ║
║                                                    ║
║  📊 Statistics:                                    ║
║     Total Connections: {self.tzimtzum_state.total_connections:,}                      ║
║     Pruned Total:      {self.tzimtzum_state.pruned_connections:,}                      ║
║     Regrown Total:     {self.tzimtzum_state.regrown_connections:,}                       ║
║     Dark Night Cycles: {cycles}                           ║
║     Memory Saved:      {self.tzimtzum_state.memory_saved_bytes:,} bytes              ║
╚════════════════════════════════════════════════════╝
"""
        return viz


class TzimtzumMixin:
    """
    Mixin para agregar capacidades Tzimtzum a cualquier ESN.
    
    Permite convertir un ESN existente en un ESN con poda dinámica
    sin necesidad de herencia directa.
    
    Ejemplo:
        >>> class MyHebbianTzimtzum(TzimtzumMixin, HebbianESN):
        ...     pass
        >>> 
        >>> esn = MyHebbianTzimtzum(input_size=3, reservoir_size=100)
        >>> esn.dark_night()  # Ahora tiene capacidad Tzimtzum
    """
    
    _tzimtzum_initialized: bool = False
    
    def init_tzimtzum(self, config: Optional[TzimtzumConfig] = None):
        """Inicializa las capacidades Tzimtzum."""
        self.tzimtzum_config = config or TzimtzumConfig()
        self.tzimtzum_state = TzimtzumState()
        self._connection_mask = (self.W_reservoir != 0)
        self._connection_importance = np.zeros_like(self.W_reservoir)
        self._pruning_history = []
        self._tzimtzum_initialized = True
    
    def dark_night(self, fraction: Optional[float] = None) -> Dict:
        """Ejecuta poda Tzimtzum."""
        if not self._tzimtzum_initialized:
            self.init_tzimtzum()
        
        fraction = fraction or self.tzimtzum_config.pruning_fraction
        
        # Implementación simplificada
        importance = np.abs(self.W_reservoir)
        threshold = np.percentile(importance[importance > 0], fraction * 100)
        
        prune_mask = (np.abs(self.W_reservoir) < threshold) & (self.W_reservoir != 0)
        pruned_count = np.sum(prune_mask)
        
        self.W_reservoir[prune_mask] = 0
        self._connection_mask = (self.W_reservoir != 0)
        
        self.tzimtzum_state.pruned_connections += pruned_count
        self.tzimtzum_state.pruning_cycles += 1
        
        return {'pruned_count': int(pruned_count)}


def demonstrate_tzimtzum():
    """
    Demostración del protocolo Tzimtzum.
    
    Muestra el ciclo completo de contracción y sus efectos
    en el rendimiento y memoria del ESN.
    """
    print("=" * 60)
    print("   DEMOSTRACIÓN DEL PROTOCOLO TZIMTZUM")
    print("   'Para que algo nuevo nazca, algo viejo debe morir'")
    print("=" * 60)
    print()
    
    # Crear datos de prueba (señal caótica)
    np.random.seed(42)
    T = 2000
    t = np.linspace(0, 20 * np.pi, T)
    
    # Señal compleja: combinación de sinusoides + ruido
    signal = (
        np.sin(t) + 
        0.5 * np.sin(3 * t) + 
        0.3 * np.sin(7 * t) + 
        0.1 * np.random.randn(T)
    )
    
    # Preparar datos
    X = signal[:-1].reshape(-1, 1)
    y = signal[1:].reshape(-1, 1)
    
    train_size = int(0.7 * len(X))
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]
    
    # Configuración Tzimtzum
    config = TzimtzumConfig(
        pruning_fraction=0.5,       # Podar 50% (número sagrado)
        regrowth_fraction=0.1,      # Recrecer 10%
        dark_night_interval=0,      # Manual, no automático
        preserve_topology=True,
        min_connections_fraction=0.02  # Permitir bajar hasta 2%
    )
    
    # Crear TzimtzumESN (con menos sparsity para demostración)
    tzim = TzimtzumESN(
        n_inputs=1,
        n_reservoir=100,
        n_outputs=1,
        spectral_radius=0.95,
        sparsity=0.7,               # 30% conexiones activas inicial
        config=config,
        random_state=42
    )
    
    print("📊 ESTADO INICIAL:")
    print(tzim.visualize_contraction())
    
    # Entrenar
    print("\n🎓 Entrenando red...")
    tzim.fit(X_train, y_train, washout=100)
    
    # Evaluar antes de poda
    y_pred_before = tzim.predict(X_test)
    mse_before = np.mean((y_test - y_pred_before) ** 2)
    
    print(f"   MSE antes de Tzimtzum: {mse_before:.6f}")
    
    initial_report = tzim.get_sparsity_report()
    print(f"   Conexiones activas: {initial_report['active_connections']}")
    
    # Ejecutar Dark Night
    print("\n🌑 EJECUTANDO DARK NIGHT...")
    print("   'En la noche oscura del alma, brillan más las estrellas'")
    
    dark_stats = tzim.dark_night()
    print(f"\n   Conexiones podadas: {dark_stats['pruned_count']}")
    print(f"   Umbral de supervivencia: {dark_stats['threshold']:.6f}")
    print(f"   Memoria liberada: {dark_stats['memory_saved_bytes']} bytes")
    
    print(tzim.visualize_contraction())
    
    # Evaluar después de poda (antes de reentrenar)
    y_pred_after_prune = tzim.predict(X_test)
    mse_after_prune = np.mean((y_test - y_pred_after_prune) ** 2)
    
    print(f"   MSE después de poda (sin reentrenar): {mse_after_prune:.6f}")
    
    # Reentrenar con menos conexiones
    print("\n🌅 RENACIMIENTO: Reentrenando red podada...")
    tzim.fit(X_train, y_train, washout=100)
    
    y_pred_after = tzim.predict(X_test)
    mse_after = np.mean((y_test - y_pred_after) ** 2)
    
    print(f"   MSE después de reentrenar: {mse_after:.6f}")
    
    # Comparación final
    print("\n" + "=" * 60)
    print("   RESULTADOS FINALES")
    print("=" * 60)
    
    improvement = (mse_before - mse_after) / mse_before * 100
    reduction = dark_stats['pruned_count'] / initial_report['active_connections'] * 100
    
    print(f"""
   📈 Rendimiento:
      • MSE Original:  {mse_before:.6f}
      • MSE Final:     {mse_after:.6f}
      • Cambio:        {improvement:+.1f}%
   
   💾 Eficiencia:
      • Conexiones Originales: {initial_report['active_connections']}
      • Conexiones Finales:    {tzim.get_sparsity_report()['active_connections']}
      • Reducción:             {reduction:.1f}%
   
   🔮 Interpretación:
      "El Tzimtzum demuestra que menos es más.
       Al eliminar las conexiones débiles, la red
       se enfoca en los patrones verdaderamente importantes."
    """)
    
    return tzim


if __name__ == "__main__":
    tzim = demonstrate_tzimtzum()
