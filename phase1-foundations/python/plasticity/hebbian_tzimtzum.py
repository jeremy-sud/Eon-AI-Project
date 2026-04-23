"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     HEBBIAN TZIMTZUM ESN                                      ║
║              Plasticidad Sináptica con Contracción Divina                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  "Las neuronas que disparan juntas, permanecen juntas...                      ║
║   hasta que el Tzimtzum las separe."                                          ║
║                                                                               ║
║  Esta clase combina:                                                          ║
║  • Plasticidad Hebbiana: Aprendizaje basado en correlación                   ║
║  • Protocolo Tzimtzum: Poda cíclica de conexiones débiles                    ║
║                                                                               ║
║  El resultado es un sistema que:                                              ║
║  1. Fortalece conexiones útiles (Hebbian)                                     ║
║  2. Elimina periódicamente las más débiles (Tzimtzum)                         ║
║  3. Crea espacio para nuevo aprendizaje (Dark Night)                         ║
║  4. Permite regeneración controlada (Renacimiento)                            ║
║                                                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional, Dict, List
import os

from plasticity.hebbian import HebbianESN
from plasticity.tzimtzum import TzimtzumConfig, TzimtzumState, ContractionPhase

class HebbianTzimtzumESN(HebbianESN):
    """
    Echo State Network con Plasticidad Hebbiana y Protocolo Tzimtzum.
    
    Combina dos paradigmas de aprendizaje complementarios:
    
    1. PLASTICIDAD HEBBIANA (continua):
       - Fortalece conexiones entre neuronas co-activas
       - Opera en cada paso de tiempo
       - "Células que disparan juntas, permanecen juntas"
    
    2. PROTOCOLO TZIMTZUM (cíclico):
       - Elimina periódicamente conexiones débiles
       - Crea "vacío" para nuevo aprendizaje
       - "Para aprender algo nuevo, primero debo olvidar"
    
    FILOSOFÍA:
    ──────────
    La vida neuronal es un balance entre:
    - Crecimiento (Hebbian): Acumular conocimiento
    - Poda (Tzimtzum): Liberar lo obsoleto
    
    Sin poda, la red se satura.
    Sin crecimiento, la red muere.
    
    El HebbianTzimtzumESN implementa este ciclo vital.
    
    Ejemplo:
        >>> esn = HebbianTzimtzumESN(
        ...     input_size=3,
        ...     reservoir_size=100,
        ...     plasticity_type='hebbian',
        ...     tzimtzum_config=TzimtzumConfig(pruning_fraction=0.5)
        ... )
        >>> 
        >>> # Entrenar con adaptación online
        >>> esn.adapt_online(X_train)
        >>> 
        >>> # Ejecutar Dark Night
        >>> esn.dark_night()
        >>> 
        >>> # Continuar adaptación
        >>> esn.adapt_online(X_new)
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
        plasticity_type: str = 'hebbian',
        tzimtzum_config: Optional[TzimtzumConfig] = None,
        random_state: Optional[int] = None
    ):
        """
        Inicializa HebbianTzimtzumESN.
        
        Args:
            n_inputs: Dimensión de entrada
            n_reservoir: Número de neuronas
            n_outputs: Dimensión de salida
            spectral_radius: Radio espectral
            sparsity: Sparsity inicial
            noise: Ruido de regularización
            learning_rate: Tasa de aprendizaje Hebbiano
            plasticity_type: 'hebbian', 'stdp', o 'anti_hebbian'
            tzimtzum_config: Configuración del protocolo Tzimtzum
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
            plasticity_type=plasticity_type,
            random_state=random_state
        )
        
        # Configuración Tzimtzum
        self.tzimtzum_config = tzimtzum_config or TzimtzumConfig()
        self.tzimtzum_state = TzimtzumState()
        
        # RNG para regrowth
        regrowth_seed = self.tzimtzum_config.regrowth_seed or random_state
        self._regrowth_rng = np.random.default_rng(regrowth_seed)
        
        # Tracking de conexiones
        self._connection_mask = (self.W_reservoir != 0)
        self._connection_importance = np.zeros_like(self.W_reservoir)
        self._hebbian_contribution = np.zeros_like(self.W_reservoir)
        
        # Historial
        self._pruning_history: List[Dict] = []
        self._step_count = 0
        
        # Inicializar métricas
        self._update_tzimtzum_metrics()
    
    def _update_tzimtzum_metrics(self):
        """Actualiza métricas del estado Tzimtzum."""
        self.tzimtzum_state.total_connections = int(np.sum(self._connection_mask))
        max_connections = self.n_reservoir ** 2
        active = self.tzimtzum_state.total_connections
        self.tzimtzum_state.compression_ratio = active / max_connections if max_connections > 0 else 0
    
    def _apply_plasticity(self, input_vector: np.ndarray, new_state: np.ndarray):
        """
        Aplica plasticidad Hebbiana con tracking para Tzimtzum.
        
        Además del update Hebbiano normal, rastrea qué conexiones
        están siendo fortalecidas para informar decisiones de poda.
        """
        # Obtener delta antes de aplicar
        if self.plasticity_type == 'hebbian':
            delta_w = self._hebbian_update(self._prev_state, new_state)
        elif self.plasticity_type == 'stdp':
            delta_w = self._stdp_update(
                self._prev_state, new_state,
                self._prev_state, self.state
            )
        elif self.plasticity_type == 'anti_hebbian':
            delta_w = self._anti_hebbian_update(self._prev_state, new_state)
        else:
            return
        
        # Aplicar solo a conexiones activas
        mask = self._connection_mask
        self.W_reservoir += delta_w * mask
        
        # Tracking de contribución Hebbiana
        alpha = 0.99
        self._hebbian_contribution = (
            alpha * self._hebbian_contribution +
            (1 - alpha) * np.abs(delta_w)
        )
        
        # Mantener estabilidad
        self._normalize_spectral_radius()
        
        self._adaptation_count += 1
        self._step_count += 1
        
        # Auto-poda si está configurado
        if (self.tzimtzum_config.dark_night_interval > 0 and
            self._step_count % self.tzimtzum_config.dark_night_interval == 0):
            self.full_tzimtzum_cycle()
    
    def _calculate_importance(self) -> np.ndarray:
        """
        Calcula importancia de conexiones combinando múltiples señales.
        
        Combina:
        1. Magnitud del peso actual
        2. Contribución Hebbiana acumulada
        3. Frecuencia de uso
        
        Conexiones que son fuertes Y activamente reforzadas por
        plasticidad tienen mayor probabilidad de sobrevivir.
        """
        # Componente 1: Magnitud absoluta
        weight_importance = np.abs(self.W_reservoir)
        
        # Componente 2: Contribución Hebbiana (cuánto se refuerza)
        hebbian_importance = self._hebbian_contribution
        
        # Normalizar componentes
        if weight_importance.max() > 0:
            weight_importance = weight_importance / weight_importance.max()
        if hebbian_importance.max() > 0:
            hebbian_importance = hebbian_importance / hebbian_importance.max()
        
        # Combinación ponderada
        # Pesos que son fuertes Y reforzados son más importantes
        importance = 0.6 * weight_importance + 0.4 * hebbian_importance
        
        return importance
    
    def dark_night(self, fraction: Optional[float] = None) -> Dict:
        """
        Ejecuta Dark Night con criterio Hebbiano.
        
        Las conexiones que han sido activamente reforzadas por
        plasticidad Hebbiana tienen mayor probabilidad de sobrevivir.
        
        Args:
            fraction: Fracción de conexiones a podar
            
        Returns:
            Estadísticas de poda
        """
        fraction = fraction or self.tzimtzum_config.pruning_fraction
        
        self.tzimtzum_state.phase = ContractionPhase.DARK_NIGHT
        
        # Importancia combinada
        importance = self._calculate_importance()
        
        # Solo conexiones activas
        active_mask = self._connection_mask
        active_importance = importance[active_mask]
        
        if len(active_importance) == 0:
            return {'pruned_count': 0, 'message': 'No hay conexiones activas'}
        
        # Calcular umbral
        threshold = np.percentile(active_importance, fraction * 100)
        
        # Mínimo de conexiones
        min_connections = int(
            self.n_reservoir ** 2 * self.tzimtzum_config.min_connections_fraction
        )
        current_connections = np.sum(active_mask)
        max_to_prune = current_connections - min_connections
        
        if max_to_prune <= 0:
            return {'pruned_count': 0, 'message': 'Ya en mínimo de conexiones'}
        
        # Máscara de supervivencia
        survival_mask = importance >= threshold
        
        # Preservar topología
        if self.tzimtzum_config.preserve_topology:
            for i in range(self.n_reservoir):
                if not np.any(survival_mask[:, i]):
                    best_in = np.argmax(np.abs(self.W_reservoir[:, i]))
                    survival_mask[best_in, i] = True
                if not np.any(survival_mask[i, :]):
                    best_out = np.argmax(np.abs(self.W_reservoir[i, :]))
                    survival_mask[i, best_out] = True
        
        # Ejecutar poda
        pre_count = int(np.sum(self.W_reservoir != 0))
        
        prune_mask = ~survival_mask & active_mask
        pruned_count = min(int(np.sum(prune_mask)), max_to_prune)
        
        # Si hay más que max_to_prune, podar solo las menos importantes
        if np.sum(prune_mask) > max_to_prune:
            prune_indices = np.argwhere(prune_mask)
            prune_importance = importance[prune_mask]
            sorted_idx = np.argsort(prune_importance)[:max_to_prune]
            
            prune_mask = np.zeros_like(prune_mask)
            for idx in sorted_idx:
                i, j = prune_indices[idx]
                prune_mask[i, j] = True
        
        self.W_reservoir[prune_mask] = 0
        self._connection_mask = (self.W_reservoir != 0)
        self._hebbian_contribution[prune_mask] = 0
        
        # Renormalizar
        self._normalize_spectral_radius()
        
        post_count = int(np.sum(self.W_reservoir != 0))
        memory_saved = (pre_count - post_count) * 8
        
        # Actualizar estado
        self.tzimtzum_state.pruned_connections += pruned_count
        self.tzimtzum_state.pruning_cycles += 1
        self.tzimtzum_state.memory_saved_bytes += memory_saved
        self.tzimtzum_state.phase = ContractionPhase.CHALLAL
        
        self._update_tzimtzum_metrics()
        
        stats = {
            'cycle': self.tzimtzum_state.pruning_cycles,
            'pruned_count': pruned_count,
            'pre_connections': pre_count,
            'post_connections': post_count,
            'memory_saved_bytes': memory_saved,
            'compression_ratio': self.tzimtzum_state.compression_ratio,
            'hebbian_contribution_preserved': float(
                np.sum(self._hebbian_contribution) / 
                (np.sum(self._hebbian_contribution) + 1e-10)
            )
        }
        
        self._pruning_history.append(stats)
        return stats
    
    def renacimiento(self, fraction: Optional[float] = None) -> Dict:
        """
        Regrowth de conexiones después del Dark Night.
        
        Las nuevas conexiones comienzan con pesos pequeños y
        deben ganarse su lugar mediante aprendizaje Hebbiano.
        """
        fraction = fraction or self.tzimtzum_config.regrowth_fraction
        
        self.tzimtzum_state.phase = ContractionPhase.RENACIMIENTO
        
        # Cuántas conexiones regenerar
        pruned = self.tzimtzum_state.pruned_connections
        regrow_count = int(pruned * fraction)
        
        if regrow_count == 0:
            self.tzimtzum_state.phase = ContractionPhase.PLENITUD
            return {'regrown_count': 0}
        
        # Posiciones vacías
        empty_mask = ~self._connection_mask
        empty_indices = np.argwhere(empty_mask)
        
        if len(empty_indices) == 0:
            return {'regrown_count': 0}
        
        regrow_count = min(regrow_count, len(empty_indices))
        selected = self._regrowth_rng.choice(
            len(empty_indices), size=regrow_count, replace=False
        )
        
        # Crear nuevas conexiones débiles
        for idx in selected:
            i, j = empty_indices[idx]
            new_weight = self._regrowth_rng.uniform(-0.05, 0.05)
            self.W_reservoir[i, j] = new_weight
        
        self._connection_mask = (self.W_reservoir != 0)
        self.tzimtzum_state.regrown_connections += regrow_count
        
        self._normalize_spectral_radius()
        self._update_tzimtzum_metrics()
        
        self.tzimtzum_state.phase = ContractionPhase.PLENITUD
        
        return {
            'regrown_count': regrow_count,
            'compression_ratio': self.tzimtzum_state.compression_ratio
        }
    
    def full_tzimtzum_cycle(self) -> Dict:
        """Ejecuta ciclo completo: Dark Night + Renacimiento."""
        dark = self.dark_night()
        rebirth = self.renacimiento()
        
        return {
            'dark_night': dark,
            'renacimiento': rebirth,
            'final_connections': self.tzimtzum_state.total_connections,
            'total_cycles': self.tzimtzum_state.pruning_cycles
        }
    
    def get_combined_stats(self) -> Dict:
        """Estadísticas combinadas de Hebbian y Tzimtzum."""
        hebbian_stats = self.get_adaptation_stats()
        
        return {
            'hebbian': hebbian_stats,
            'tzimtzum': self.tzimtzum_state.to_dict(),
            'combined': {
                'total_connections': self.tzimtzum_state.total_connections,
                'adaptation_steps': self._adaptation_count,
                'pruning_cycles': self.tzimtzum_state.pruning_cycles,
                'compression_ratio': self.tzimtzum_state.compression_ratio,
                'mean_hebbian_contribution': float(np.mean(self._hebbian_contribution))
            }
        }

def demonstrate_hebbian_tzimtzum():
    """Demostración del HebbianTzimtzumESN."""
    print("=" * 60)
    print("   DEMOSTRACIÓN: HEBBIAN + TZIMTZUM")
    print("   Plasticidad con Contracción Cíclica")
    print("=" * 60)
    
    # Datos de prueba
    np.random.seed(42)
    T = 3000
    t = np.linspace(0, 30 * np.pi, T)
    
    # Señal con cambios de régimen
    signal = np.zeros(T)
    signal[:1000] = np.sin(t[:1000])
    signal[1000:2000] = np.sin(3 * t[1000:2000]) + 0.5 * np.cos(7 * t[1000:2000])
    signal[2000:] = np.sin(5 * t[2000:]) * np.exp(-0.001 * (t[2000:] - t[2000]))
    
    signal += 0.1 * np.random.randn(T)
    
    X = signal[:-1].reshape(-1, 1)
    y = signal[1:].reshape(-1, 1)
    
    # Crear HebbianTzimtzumESN
    config = TzimtzumConfig(
        pruning_fraction=0.4,
        regrowth_fraction=0.15,
        dark_night_interval=0,  # Manual
        min_connections_fraction=0.02
    )
    
    esn = HebbianTzimtzumESN(
        n_inputs=1,
        n_reservoir=100,
        n_outputs=1,
        spectral_radius=0.95,
        sparsity=0.7,
        learning_rate=0.0005,
        plasticity_type='hebbian',
        tzimtzum_config=config,
        random_state=42
    )
    
    # Fase 1: Entrenamiento inicial
    print("\n📚 Fase 1: Entrenamiento inicial (primeros 1000 pasos)")
    esn.fit(X[:1000], y[:1000], washout=100)
    
    initial_connections = np.sum(esn.W_reservoir != 0)
    print(f"   Conexiones activas: {initial_connections}")
    
    # Fase 2: Adaptación online con plasticidad
    print("\n🧠 Fase 2: Adaptación online con Hebbian (1000-2000)")
    esn.adapt_online(X[1000:2000], record_weights=True)
    
    post_hebbian_connections = np.sum(esn.W_reservoir != 0)
    print(f"   Conexiones tras Hebbian: {post_hebbian_connections}")
    
    # Fase 3: Dark Night
    print("\n🌑 Fase 3: Ejecutando Dark Night...")
    dark_stats = esn.dark_night()
    print(f"   Conexiones podadas: {dark_stats['pruned_count']}")
    print(f"   Conexiones restantes: {dark_stats['post_connections']}")
    
    # Fase 4: Regrowth
    print("\n🌅 Fase 4: Renacimiento...")
    rebirth_stats = esn.renacimiento()
    print(f"   Conexiones regeneradas: {rebirth_stats['regrown_count']}")
    
    # Fase 5: Continuar adaptación
    print("\n🔄 Fase 5: Continuando adaptación (2000-3000)")
    esn.adapt_online(X[2000:], record_weights=True)
    
    # Estadísticas finales
    final_stats = esn.get_combined_stats()
    
    print("\n" + "=" * 60)
    print("   ESTADÍSTICAS FINALES")
    print("=" * 60)
    print(f"""
   📊 Hebbian:
      • Pasos de adaptación: {final_stats['hebbian']['total_adaptations']}
      • Peso medio actual: {final_stats['hebbian']['current_mean_weight']:.6f}
   
   🌑 Tzimtzum:
      • Ciclos de poda: {final_stats['tzimtzum']['pruning_cycles']}
      • Conexiones podadas: {final_stats['tzimtzum']['pruned_connections']}
      • Memoria liberada: {final_stats['tzimtzum']['memory_saved_bytes']} bytes
   
   🔮 Combinado:
      • Conexiones finales: {final_stats['combined']['total_connections']}
      • Ratio de compresión: {final_stats['combined']['compression_ratio']:.1%}
      • Contribución Hebbiana media: {final_stats['combined']['mean_hebbian_contribution']:.6f}
    """)
    
    return esn

if __name__ == "__main__":
    esn = demonstrate_hebbian_tzimtzum()
