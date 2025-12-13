"""
Proyecto Eón - Plasticidad Hebbiana
Implementación de aprendizaje local continuo inspirado en neurociencia.

"Las neuronas que disparan juntas, se conectan juntas" - Donald Hebb (1949)
"""

import numpy as np
from typing import Optional, Tuple
import sys
import os

# Agregar path del proyecto para imports
_current_dir = os.path.dirname(os.path.abspath(__file__))
_python_dir = os.path.dirname(_current_dir)
if _python_dir not in sys.path:
    sys.path.insert(0, _python_dir)

from esn.esn import EchoStateNetwork, generate_mackey_glass
from utils.matrix_init import compute_spectral_radius


class HebbianESN(EchoStateNetwork):
    """
    ESN con plasticidad Hebbiana para aprendizaje continuo.
    
    A diferencia del ESN estándar donde el reservoir es estático,
    esta versión permite que las conexiones del reservoir se
    adapten gradualmente según la actividad, emulando la plasticidad
    sináptica biológica.
    
    Tipos de plasticidad soportados:
    - Hebb clásico: Δw = η * pre * post
    - STDP simplificado: considera timing entre activaciones
    - Anti-Hebbiano: para diversificar representaciones
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
        random_state: Optional[int] = None
    ):
        """
        Inicializa ESN con plasticidad.
        
        Args:
            learning_rate: Tasa de aprendizaje para plasticidad (η)
            plasticity_type: 'hebbian', 'stdp', o 'anti_hebbian'
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
        
        self.learning_rate = learning_rate
        self.plasticity_type = plasticity_type
        
        # Estado previo para STDP
        self._prev_state = np.zeros(n_reservoir)
        
        # Historial para análisis
        self.weight_history = []
        self._adaptation_count = 0
        
    def _hebbian_update(self, pre: np.ndarray, post: np.ndarray) -> np.ndarray:
        """
        Regla de Hebb clásica: Δw = η * pre * post
        
        Las conexiones se fortalecen cuando ambas neuronas están activas.
        """
        # Producto exterior: matriz de correlaciones
        delta_w = self.learning_rate * np.outer(post, pre)
        return delta_w
    
    def _stdp_update(self, pre: np.ndarray, post: np.ndarray, 
                     prev_pre: np.ndarray, prev_post: np.ndarray) -> np.ndarray:
        """
        Spike-Timing-Dependent Plasticity simplificado.
        
        - Si post se activa DESPUÉS de pre: LTP (potenciación)
        - Si post se activa ANTES de pre: LTD (depresión)
        
        Este esquema refleja la causalidad temporal en el aprendizaje.
        """
        # Detectar cambios de activación (pseudo-spikes)
        pre_became_active = (pre > 0.5) & (prev_pre <= 0.5)
        post_became_active = (post > 0.5) & (prev_post <= 0.5)
        
        # LTP: post después de pre
        ltp = np.outer(post_became_active.astype(float), pre.astype(float))
        
        # LTD: pre después de post
        ltd = np.outer(post.astype(float), pre_became_active.astype(float))
        
        delta_w = self.learning_rate * (ltp - 0.5 * ltd)
        return delta_w
    
    def _anti_hebbian_update(self, pre: np.ndarray, post: np.ndarray) -> np.ndarray:
        """
        Plasticidad anti-Hebbiana: Δw = -η * pre * post
        
        Las conexiones se DEBILITAN cuando ambas neuronas están activas.
        Promueve diversificación de representaciones y evita saturación.
        """
        delta_w = -self.learning_rate * np.outer(post, pre)
        return delta_w
    
    def _apply_plasticity(self, input_vector: np.ndarray, new_state: np.ndarray):
        """
        Aplica la regla de plasticidad seleccionada al reservoir.
        """
        if self.plasticity_type == 'hebbian':
            delta_w = self._hebbian_update(self._prev_state, new_state)
        elif self.plasticity_type == 'stdp':
            # Para STDP necesitamos acceso al input previo
            delta_w = self._stdp_update(
                self._prev_state, new_state,
                self._prev_state, self.state  # Aproximación
            )
        elif self.plasticity_type == 'anti_hebbian':
            delta_w = self._anti_hebbian_update(self._prev_state, new_state)
        else:
            return
        
        # Aplicar actualización manteniendo la máscara de escasez
        mask = (self.W_reservoir != 0)
        self.W_reservoir += delta_w * mask
        
        # Mantener radio espectral bajo control (estabilidad)
        self._normalize_spectral_radius()
        
        self._adaptation_count += 1
        
    def _normalize_spectral_radius(self):
        """Renormaliza el reservoir para mantener estabilidad."""
        # Usar compute_spectral_radius de utils/matrix_init.py
        # method='auto' usa power iteration para matrices grandes (más eficiente)
        current_radius = compute_spectral_radius(self.W_reservoir, method='auto')
        
        if current_radius > self.spectral_radius * 1.1:  # 10% tolerancia
            self.W_reservoir *= self.spectral_radius / current_radius
    
    def _update_state(self, input_vector: np.ndarray) -> np.ndarray:
        """
        Actualiza estado con plasticidad opcional.
        """
        # Guardar estado previo para STDP
        self._prev_state = self.state.copy()
        
        # Actualización estándar
        new_state = super()._update_state(input_vector)
        
        # Aplicar plasticidad
        self._apply_plasticity(input_vector, new_state)
        
        return new_state
    
    def adapt_online(self, inputs: np.ndarray, record_weights: bool = False) -> 'HebbianESN':
        """
        Adaptación continua online sin target explícito.
        
        El reservoir se adapta basándose solo en correlaciones de actividad.
        Esto simula aprendizaje no supervisado continuo.
        
        Args:
            inputs: Secuencia de entrada
            record_weights: Si guardar historial de pesos
            
        Returns:
            self
        """
        T = inputs.shape[0]
        
        if inputs.ndim == 1:
            inputs = inputs.reshape(-1, 1)
        
        for t in range(T):
            self._update_state(inputs[t])
            
            if record_weights and t % 100 == 0:
                self.weight_history.append({
                    'step': t,
                    'mean_weight': np.mean(np.abs(self.W_reservoir)),
                    'max_weight': np.max(np.abs(self.W_reservoir)),
                    'sparsity': np.mean(self.W_reservoir == 0)
                })
        
        return self
    
    def get_adaptation_stats(self) -> dict:
        """Retorna estadísticas de la adaptación."""
        return {
            'total_adaptations': self._adaptation_count,
            'current_mean_weight': np.mean(np.abs(self.W_reservoir)),
            'current_max_weight': np.max(np.abs(self.W_reservoir)),
            'current_sparsity': np.mean(self.W_reservoir == 0),
            'weight_history': self.weight_history
        }
    
    def reset_plasticity(self):
        """Resetea contadores de plasticidad (no los pesos)."""
        self._prev_state = np.zeros(self.n_reservoir)
        self.weight_history = []
        self._adaptation_count = 0


def compare_plasticity_types():
    """
    Compara diferentes tipos de plasticidad.
    """
    print("""
╔═══════════════════════════════════════════════════════════════╗
║         PROYECTO EÓN - Plasticidad Hebbiana                   ║
║   "Las neuronas que disparan juntas, se conectan juntas"      ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Generar datos
    print("[1/4] Preparando datos...")
    data = generate_mackey_glass(2500)
    data = (data - data.mean()) / data.std()
    
    X = data[:-1].reshape(-1, 1)
    y = data[1:].reshape(-1, 1)
    
    train_size = 1500
    adapt_size = 500
    X_train, X_adapt, X_test = X[:train_size], X[train_size:train_size+adapt_size], X[train_size+adapt_size:]
    y_train, y_adapt, y_test = y[:train_size], y[train_size:train_size+adapt_size], y[train_size+adapt_size:]
    
    results = []
    
    # ESN estándar (sin plasticidad)
    print("\n[2/4] Entrenando ESN estándar (sin plasticidad)...")
    esn_standard = EchoStateNetwork(
        n_inputs=1, n_reservoir=100, n_outputs=1,
        spectral_radius=0.9, random_state=42
    )
    esn_standard.fit(X_train, y_train)
    esn_standard.reset()
    pred_standard = esn_standard.predict(X_test)
    mse_standard = np.mean((pred_standard - y_test)**2)
    
    results.append({
        'name': 'ESN Estándar',
        'mse': mse_standard,
        'adaptations': 0
    })
    
    # Probar diferentes tipos de plasticidad
    print("[3/4] Probando tipos de plasticidad...")
    
    for plasticity_type in ['hebbian', 'anti_hebbian']:
        esn_plastic = HebbianESN(
            n_inputs=1, n_reservoir=100, n_outputs=1,
            spectral_radius=0.9, learning_rate=0.0001,
            plasticity_type=plasticity_type, random_state=42
        )
        
        # Entrenar inicialmente
        esn_plastic.fit(X_train, y_train)
        
        # Adaptación online
        esn_plastic.reset()
        esn_plastic.adapt_online(X_adapt, record_weights=True)
        
        # Evaluar
        pred = esn_plastic.predict(X_test)
        mse = np.mean((pred - y_test)**2)
        stats = esn_plastic.get_adaptation_stats()
        
        results.append({
            'name': f'ESN + {plasticity_type.title()}',
            'mse': mse,
            'adaptations': stats['total_adaptations']
        })
    
    # Mostrar resultados
    print("\n[4/4] Resultados:")
    print("-" * 60)
    print(f"{'Modelo':<25} {'MSE':<12} {'Adaptaciones':<15}")
    print("-" * 60)
    
    for r in results:
        print(f"{r['name']:<25} {r['mse']:<12.6f} {r['adaptations']:<15}")
    
    print("-" * 60)
    
    # Análisis
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                      OBSERVACIONES                            ║
╠═══════════════════════════════════════════════════════════════╣
║  • La plasticidad Hebbiana permite adaptación continua        ║
║  • El reservoir se auto-organiza sin etiquetas                ║
║  • STDP respeta causalidad temporal (más biológico)           ║
║  • Anti-Hebbiano promueve representaciones dispersas          ║
║                                                               ║
║  PRINCIPIO CLAVE:                                             ║
║  El aprendizaje ocurre LOCALMENTE en cada sinapsis,           ║
║  sin necesidad de backpropagation global.                     ║
╚═══════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    compare_plasticity_types()
