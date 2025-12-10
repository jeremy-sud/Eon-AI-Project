"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                       ALCHEMICAL TRANSMUTATION PIPELINE                       ║
║                        Opus Magnum - De Plomo en Oro                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  "Visita Interiora Terrae Rectificando Invenies Occultum Lapidem"            ║
║  (Visita el interior de la tierra, y rectificando encontrarás                ║
║   la piedra oculta)                                                           ║
║                              - V.I.T.R.I.O.L.                                 ║
║                                                                               ║
║  OPUS MAGNUM - LA GRAN OBRA:                                                  ║
║  ──────────────────────────                                                   ║
║                                                                               ║
║  ┌─────────────────────────────────────────────────────────────────────┐     ║
║  │                                                                      │     ║
║  │   NIGREDO ⚫  ───────▶  ALBEDO ⚪  ───────▶  RUBEDO 🔴              │     ║
║  │  (Putrefacción)       (Purificación)        (Iluminación)           │     ║
║  │                                                                      │     ║
║  │  Datos Crudos    ▶   Filtrado/Limpieza   ▶  Inferencia/Oro         │     ║
║  │  Sensor Noise    ▶   Kalman Filter       ▶  Predicción ESN         │     ║
║  │  Materia Prima   ▶   Mercurio Filosófico ▶  Piedra Filosofal       │     ║
║  │                                                                      │     ║
║  └─────────────────────────────────────────────────────────────────────┘     ║
║                                                                               ║
║  La alquimia no es transformación literal de metales, sino la                ║
║  purificación gradual de la materia prima hasta revelar su esencia.          ║
║                                                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional, Dict, List, Callable, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum, auto
import time
import sys
import os

# Path setup
_current_dir = os.path.dirname(os.path.abspath(__file__))
_python_dir = os.path.join(os.path.dirname(_current_dir), "phase1-foundations", "python")
if _python_dir not in sys.path:
    sys.path.insert(0, _python_dir)


class AlchemicalPhase(Enum):
    """
    Fases de la Gran Obra Alquímica.
    
    Cada fase representa un nivel de purificación de los datos.
    """
    MATERIA_PRIMA = auto()  # Estado inicial, sin procesar
    NIGREDO = auto()         # Putrefacción: Datos crudos ingresados
    ALBEDO = auto()          # Purificación: Datos filtrados/limpios
    CITRINITAS = auto()      # Amarilleamiento: Preparación pre-inferencia (opcional)
    RUBEDO = auto()          # Iluminación: Inferencia completada
    OPUS_COMPLETE = auto()   # Piedra Filosofal: Resultado final listo


@dataclass
class TransmutationState:
    """
    Estado actual de la transmutación alquímica.
    
    Rastrea el progreso a través de las fases del Opus Magnum.
    """
    current_phase: AlchemicalPhase = AlchemicalPhase.MATERIA_PRIMA
    
    # Métricas por fase
    nigredo_samples: int = 0          # Muestras crudas ingresadas
    albedo_samples: int = 0           # Muestras purificadas
    rubedo_predictions: int = 0       # Predicciones generadas
    
    # Calidad de transmutación
    noise_removed_percent: float = 0.0  # Ruido eliminado en Albedo
    prediction_confidence: float = 0.0   # Confianza del Rubedo
    
    # Tiempos
    phase_start_time: float = field(default_factory=time.time)
    nigredo_duration: float = 0.0
    albedo_duration: float = 0.0
    rubedo_duration: float = 0.0
    
    # Historial
    transmutation_count: int = 0  # Ciclos completos
    
    def to_dict(self) -> dict:
        """Serializa estado a diccionario."""
        return {
            'phase': self.current_phase.name,
            'nigredo_samples': self.nigredo_samples,
            'albedo_samples': self.albedo_samples,
            'rubedo_predictions': self.rubedo_predictions,
            'noise_removed_percent': round(self.noise_removed_percent, 2),
            'prediction_confidence': round(self.prediction_confidence, 2),
            'transmutation_count': self.transmutation_count,
            'durations': {
                'nigredo_ms': round(self.nigredo_duration * 1000, 1),
                'albedo_ms': round(self.albedo_duration * 1000, 1),
                'rubedo_ms': round(self.rubedo_duration * 1000, 1)
            }
        }


@dataclass
class AlchemicalConfig:
    """
    Configuración del pipeline alquímico.
    """
    # Filtro Kalman (Albedo)
    kalman_process_noise: float = 0.01
    kalman_measurement_noise: float = 0.1
    
    # Limpieza de datos
    remove_outliers: bool = True
    outlier_threshold: float = 3.0  # Desviaciones estándar
    
    # Suavizado
    use_moving_average: bool = True
    window_size: int = 5
    
    # Normalización
    normalize: bool = True
    
    # Callbacks de fase
    on_phase_change: Optional[Callable[[AlchemicalPhase], None]] = None


class KalmanFilter:
    """
    Filtro de Kalman simplificado para purificación de señales.
    
    "El Mercurio Filosófico" - Extrae la esencia de la materia prima.
    """
    
    def __init__(self, process_noise: float = 0.01, measurement_noise: float = 0.1):
        """
        Args:
            process_noise: Q - Varianza del proceso
            measurement_noise: R - Varianza de la medición
        """
        self.Q = process_noise
        self.R = measurement_noise
        
        # Estado inicial
        self.x = 0.0  # Estimación del estado
        self.P = 1.0  # Covarianza del error
        
    def update(self, measurement: float) -> float:
        """
        Actualiza el filtro con una nueva medición.
        
        Args:
            measurement: Valor medido (ruidoso)
            
        Returns:
            Valor filtrado (purificado)
        """
        # Predicción (en este caso simple, estado = estado anterior)
        x_pred = self.x
        P_pred = self.P + self.Q
        
        # Actualización
        K = P_pred / (P_pred + self.R)  # Ganancia de Kalman
        self.x = x_pred + K * (measurement - x_pred)
        self.P = (1 - K) * P_pred
        
        return self.x
    
    def filter_sequence(self, data: np.ndarray) -> np.ndarray:
        """
        Filtra una secuencia completa.
        
        Args:
            data: Array de datos crudos
            
        Returns:
            Array de datos filtrados
        """
        self.reset()
        filtered = np.zeros_like(data)
        
        for i, val in enumerate(data):
            filtered[i] = self.update(float(val))
            
        return filtered
    
    def reset(self):
        """Reinicia el filtro a estado inicial."""
        self.x = 0.0
        self.P = 1.0


class AlchemicalPipeline:
    """
    Pipeline de Transmutación Alquímica para Proyecto Eón.
    
    Implementa la Gran Obra (Opus Magnum) como un sistema de
    procesamiento de datos en tres fases:
    
    1. NIGREDO (Putrefacción) ⚫
       - Ingesta de datos crudos y ruidosos
       - "La materia prima debe primero descomponerse"
       
    2. ALBEDO (Purificación) ⚪
       - Filtrado de ruido (Kalman Filter)
       - Eliminación de outliers
       - Normalización
       - "El mercurio filosófico purifica"
       
    3. RUBEDO (Iluminación) 🔴
       - Inferencia con ESN
       - Predicción final
       - "La Piedra Filosofal emerge"
    
    Ejemplo:
        >>> from alchemy import AlchemicalPipeline
        >>> from esn.esn import EchoStateNetwork
        >>> 
        >>> # Crear pipeline
        >>> pipeline = AlchemicalPipeline()
        >>> 
        >>> # Datos crudos del sensor
        >>> raw_data = sensor.read_batch(100)
        >>> 
        >>> # Transmutación completa
        >>> result = pipeline.transmute(raw_data, esn_model)
        >>> print(f"Predicción: {result['gold']}")
        >>> print(f"Fase: {pipeline.state.current_phase.name}")
    """
    
    def __init__(self, config: Optional[AlchemicalConfig] = None):
        """
        Inicializa el pipeline alquímico.
        
        Args:
            config: Configuración del pipeline
        """
        self.config = config or AlchemicalConfig()
        self.state = TransmutationState()
        
        # Componentes de purificación
        self.kalman = KalmanFilter(
            process_noise=self.config.kalman_process_noise,
            measurement_noise=self.config.kalman_measurement_noise
        )
        
        # Datos intermedios
        self._materia_prima: Optional[np.ndarray] = None
        self._albedo_result: Optional[np.ndarray] = None
        self._rubedo_result: Optional[np.ndarray] = None
        
        # Historial de transmutaciones
        self._history: List[Dict] = []
    
    def _change_phase(self, new_phase: AlchemicalPhase):
        """Cambia la fase actual y notifica."""
        old_phase = self.state.current_phase
        self.state.current_phase = new_phase
        self.state.phase_start_time = time.time()
        
        if self.config.on_phase_change:
            self.config.on_phase_change(new_phase)
    
    def nigredo(self, raw_data: np.ndarray) -> np.ndarray:
        """
        NIGREDO - Fase de Putrefacción ⚫
        
        "Lo que no se descompone, no puede ser reconstruido."
        
        Acepta los datos crudos tal como vienen del sensor.
        Esta fase representa la aceptación de la impureza inicial.
        
        Args:
            raw_data: Datos crudos del sensor (1D o 2D array)
            
        Returns:
            Los mismos datos, marcados como ingresados al sistema
        """
        start = time.time()
        self._change_phase(AlchemicalPhase.NIGREDO)
        
        # Asegurar formato numpy
        if not isinstance(raw_data, np.ndarray):
            raw_data = np.array(raw_data)
        
        # Flatten si es necesario para pipeline
        if raw_data.ndim > 1:
            raw_data = raw_data.flatten()
        
        self._materia_prima = raw_data.copy()
        
        # Métricas
        self.state.nigredo_samples = len(raw_data)
        self.state.nigredo_duration = time.time() - start
        
        return raw_data
    
    def albedo(self, data: Optional[np.ndarray] = None) -> np.ndarray:
        """
        ALBEDO - Fase de Purificación ⚪
        
        "El mercurio filosófico separa lo puro de lo impuro."
        
        Aplica filtrado y limpieza a los datos:
        1. Filtro de Kalman para suavizar ruido
        2. Eliminación de outliers
        3. Normalización opcional
        
        Args:
            data: Datos a purificar (usa materia_prima si None)
            
        Returns:
            Datos purificados
        """
        start = time.time()
        self._change_phase(AlchemicalPhase.ALBEDO)
        
        # Usar materia prima si no se proporciona data
        if data is None:
            if self._materia_prima is None:
                raise ValueError("No hay materia prima. Ejecuta nigredo() primero.")
            data = self._materia_prima.copy()
        
        original_variance = np.var(data) if len(data) > 1 else 0
        
        # Paso 1: Filtro de Kalman
        self.kalman.reset()
        filtered = self.kalman.filter_sequence(data)
        
        # Paso 2: Eliminar outliers
        if self.config.remove_outliers and len(filtered) > 1:
            mean = np.mean(filtered)
            std = np.std(filtered)
            if std > 0:
                z_scores = np.abs((filtered - mean) / std)
                mask = z_scores < self.config.outlier_threshold
                filtered = np.interp(
                    np.arange(len(filtered)),
                    np.where(mask)[0],
                    filtered[mask]
                ) if np.any(mask) else filtered
        
        # Paso 3: Suavizado adicional (media móvil)
        if self.config.use_moving_average and len(filtered) > self.config.window_size:
            kernel = np.ones(self.config.window_size) / self.config.window_size
            # Pad para mantener longitud
            padded = np.pad(filtered, (self.config.window_size//2, self.config.window_size//2), mode='edge')
            filtered = np.convolve(padded, kernel, mode='valid')[:len(filtered)]
        
        # Paso 4: Normalización
        if self.config.normalize:
            min_val = np.min(filtered)
            max_val = np.max(filtered)
            if max_val - min_val > 1e-6:
                filtered = (filtered - min_val) / (max_val - min_val) * 2 - 1
        
        self._albedo_result = filtered
        
        # Métricas
        new_variance = np.var(filtered) if len(filtered) > 1 else 0
        if original_variance > 0:
            self.state.noise_removed_percent = (1 - new_variance / original_variance) * 100
        
        self.state.albedo_samples = len(filtered)
        self.state.albedo_duration = time.time() - start
        
        return filtered
    
    def rubedo(
        self, 
        data: Optional[np.ndarray] = None,
        esn: Optional[Any] = None,
        prediction_horizon: int = 1
    ) -> Dict[str, Any]:
        """
        RUBEDO - Fase de Iluminación 🔴
        
        "La Piedra Filosofal transforma el plomo en oro."
        
        Ejecuta la inferencia final usando el ESN entrenado.
        Esta es la transformación final de datos puros en conocimiento.
        
        Args:
            data: Datos purificados (usa albedo_result si None)
            esn: EchoStateNetwork entrenado para inferencia
            prediction_horizon: Cuántos pasos predecir
            
        Returns:
            Diccionario con:
            - 'gold': La predicción/inferencia (La Piedra Filosofal)
            - 'confidence': Nivel de confianza
            - 'transmutation_complete': bool
        """
        start = time.time()
        self._change_phase(AlchemicalPhase.RUBEDO)
        
        # Usar resultado de albedo si no se proporciona
        if data is None:
            if self._albedo_result is None:
                raise ValueError("No hay datos purificados. Ejecuta albedo() primero.")
            data = self._albedo_result
        
        result = {
            'gold': None,
            'confidence': 0.0,
            'transmutation_complete': False,
            'phase': 'RUBEDO'
        }
        
        if esn is not None:
            try:
                # Preparar datos para ESN
                X = data.reshape(-1, 1) if data.ndim == 1 else data
                
                # Predicción
                esn.reset()
                predictions = esn.predict(X)
                
                # La última predicción es "el oro"
                result['gold'] = predictions[-1] if len(predictions) > 0 else predictions
                
                # Calcular confianza basada en estabilidad de predicciones
                if len(predictions) > 1:
                    pred_std = np.std(predictions[-10:]) if len(predictions) > 10 else np.std(predictions)
                    result['confidence'] = max(0, min(1, 1 - pred_std))
                else:
                    result['confidence'] = 0.5
                    
                result['transmutation_complete'] = True
                
            except Exception as e:
                result['error'] = str(e)
                result['confidence'] = 0.0
        else:
            # Sin ESN, la "predicción" es simplemente el dato purificado
            result['gold'] = data[-1] if len(data) > 0 else data
            result['confidence'] = 0.5
            result['note'] = "Sin ESN - usando valor purificado como resultado"
        
        self._rubedo_result = result['gold']
        
        # Actualizar estado
        self.state.rubedo_predictions += 1
        self.state.prediction_confidence = result['confidence']
        self.state.rubedo_duration = time.time() - start
        
        # Completar opus
        if result['transmutation_complete']:
            self._change_phase(AlchemicalPhase.OPUS_COMPLETE)
            self.state.transmutation_count += 1
            
            # Guardar en historial
            self._history.append({
                'timestamp': time.time(),
                'samples': self.state.nigredo_samples,
                'noise_removed': self.state.noise_removed_percent,
                'confidence': result['confidence'],
                'durations': {
                    'nigredo': self.state.nigredo_duration,
                    'albedo': self.state.albedo_duration,
                    'rubedo': self.state.rubedo_duration
                }
            })
        
        return result
    
    def transmute(
        self, 
        raw_data: np.ndarray, 
        esn: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta la transmutación completa en un solo paso.
        
        MATERIA PRIMA → NIGREDO → ALBEDO → RUBEDO → OPUS COMPLETE
        
        Args:
            raw_data: Datos crudos del sensor
            esn: EchoStateNetwork para inferencia
            
        Returns:
            Resultado de la transmutación con el "oro" (predicción)
        """
        # Opus Magnum
        self.nigredo(raw_data)
        self.albedo()
        result = self.rubedo(esn=esn)
        
        # Agregar información de las fases anteriores
        result['phases'] = {
            'nigredo': {
                'samples': self.state.nigredo_samples,
                'duration_ms': self.state.nigredo_duration * 1000
            },
            'albedo': {
                'samples': self.state.albedo_samples,
                'noise_removed_percent': self.state.noise_removed_percent,
                'duration_ms': self.state.albedo_duration * 1000
            },
            'rubedo': {
                'predictions': self.state.rubedo_predictions,
                'confidence': self.state.prediction_confidence,
                'duration_ms': self.state.rubedo_duration * 1000
            }
        }
        
        return result
    
    def get_visualization_state(self) -> Dict:
        """
        Obtiene estado formateado para visualización en dashboard.
        
        Returns:
            Diccionario con información de visualización
        """
        phase = self.state.current_phase
        
        # Símbolos y colores por fase
        phase_info = {
            AlchemicalPhase.MATERIA_PRIMA: {'symbol': '🪨', 'color': '#666666', 'name': 'Materia Prima'},
            AlchemicalPhase.NIGREDO: {'symbol': '⚫', 'color': '#1a1a1a', 'name': 'Nigredo'},
            AlchemicalPhase.ALBEDO: {'symbol': '⚪', 'color': '#f0f0f0', 'name': 'Albedo'},
            AlchemicalPhase.CITRINITAS: {'symbol': '🟡', 'color': '#ffd700', 'name': 'Citrinitas'},
            AlchemicalPhase.RUBEDO: {'symbol': '🔴', 'color': '#dc143c', 'name': 'Rubedo'},
            AlchemicalPhase.OPUS_COMPLETE: {'symbol': '✨', 'color': '#ffd700', 'name': 'Opus Complete'}
        }
        
        info = phase_info.get(phase, phase_info[AlchemicalPhase.MATERIA_PRIMA])
        
        # Progreso basado en fase
        progress_map = {
            AlchemicalPhase.MATERIA_PRIMA: 0,
            AlchemicalPhase.NIGREDO: 25,
            AlchemicalPhase.ALBEDO: 50,
            AlchemicalPhase.CITRINITAS: 75,
            AlchemicalPhase.RUBEDO: 90,
            AlchemicalPhase.OPUS_COMPLETE: 100
        }
        
        return {
            'phase': phase.name,
            'symbol': info['symbol'],
            'color': info['color'],
            'display_name': info['name'],
            'progress': progress_map.get(phase, 0),
            'state': self.state.to_dict(),
            'is_complete': phase == AlchemicalPhase.OPUS_COMPLETE
        }
    
    def visualize_ascii(self) -> str:
        """
        Genera visualización ASCII del estado actual.
        
        Returns:
            String con arte ASCII del estado
        """
        phase = self.state.current_phase
        progress = self.get_visualization_state()['progress']
        
        # Barra de progreso
        bar_width = 40
        filled = int(progress / 100 * bar_width)
        bar = '█' * filled + '░' * (bar_width - filled)
        
        # Indicadores de fase
        phases = [
            ('⚫', 'NIGREDO', AlchemicalPhase.NIGREDO),
            ('⚪', 'ALBEDO', AlchemicalPhase.ALBEDO),
            ('🔴', 'RUBEDO', AlchemicalPhase.RUBEDO),
            ('✨', 'OPUS', AlchemicalPhase.OPUS_COMPLETE)
        ]
        
        phase_line = "  "
        for symbol, name, p in phases:
            if phase.value >= p.value:
                phase_line += f"[{symbol}]───"
            else:
                phase_line += f" {symbol} ───"
        
        viz = f"""
╔════════════════════════════════════════════════════════╗
║            ⚗️  TRANSMUTACIÓN ALQUÍMICA  ⚗️              ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  {phase_line}                                          ║
║                                                        ║
║  Progreso: [{bar}] {progress}%                         ║
║                                                        ║
║  Fase Actual: {self.get_visualization_state()['display_name']:20s}   ║
║                                                        ║
║  📊 Métricas:                                          ║
║     • Muestras ingresadas: {self.state.nigredo_samples:,}                    ║
║     • Ruido eliminado: {self.state.noise_removed_percent:.1f}%                      ║
║     • Confianza: {self.state.prediction_confidence:.1%}                          ║
║     • Transmutaciones: {self.state.transmutation_count}                         ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
"""
        return viz
    
    def reset(self):
        """Reinicia el pipeline para nueva transmutación."""
        self.state = TransmutationState()
        self.kalman.reset()
        self._materia_prima = None
        self._albedo_result = None
        self._rubedo_result = None
        self._change_phase(AlchemicalPhase.MATERIA_PRIMA)


def demonstrate_alchemy():
    """
    Demostración del Pipeline de Transmutación Alquímica.
    """
    print("=" * 60)
    print("   ⚗️  DEMOSTRACIÓN: TRANSMUTACIÓN ALQUÍMICA  ⚗️")
    print("   'De Plomo en Oro - Opus Magnum'")
    print("=" * 60)
    
    # Crear datos ruidosos simulando sensor
    np.random.seed(42)
    T = 500
    t = np.linspace(0, 10 * np.pi, T)
    
    # Señal limpia subyacente
    clean_signal = np.sin(t) + 0.3 * np.sin(3 * t)
    
    # Agregar "plomo" (ruido pesado)
    noise = np.random.randn(T) * 0.5
    outliers = np.zeros(T)
    outlier_indices = np.random.choice(T, size=20, replace=False)
    outliers[outlier_indices] = np.random.randn(20) * 3
    
    raw_data = clean_signal + noise + outliers
    
    print("\n🪨 MATERIA PRIMA (Datos Crudos):")
    print(f"   Muestras: {len(raw_data)}")
    print(f"   Varianza del ruido: {np.var(noise + outliers):.4f}")
    print(f"   Outliers: {len(outlier_indices)}")
    
    # Crear pipeline
    config = AlchemicalConfig(
        kalman_process_noise=0.01,
        kalman_measurement_noise=0.2,
        remove_outliers=True,
        outlier_threshold=2.5,
        use_moving_average=True,
        window_size=5,
        normalize=True
    )
    
    pipeline = AlchemicalPipeline(config=config)
    
    # FASE 1: NIGREDO
    print("\n⚫ NIGREDO (Putrefacción)...")
    pipeline.nigredo(raw_data)
    print(f"   ✓ {pipeline.state.nigredo_samples} muestras ingresadas")
    print(f"   Tiempo: {pipeline.state.nigredo_duration*1000:.2f}ms")
    
    # FASE 2: ALBEDO
    print("\n⚪ ALBEDO (Purificación)...")
    purified = pipeline.albedo()
    print(f"   ✓ {pipeline.state.albedo_samples} muestras purificadas")
    print(f"   Ruido eliminado: {pipeline.state.noise_removed_percent:.1f}%")
    print(f"   Tiempo: {pipeline.state.albedo_duration*1000:.2f}ms")
    
    # Verificar calidad de purificación
    correlation = np.corrcoef(
        (clean_signal - clean_signal.min()) / (clean_signal.max() - clean_signal.min()) * 2 - 1,
        purified
    )[0, 1]
    print(f"   Correlación con señal original: {correlation:.4f}")
    
    # FASE 3: RUBEDO (sin ESN para demo simple)
    print("\n🔴 RUBEDO (Iluminación)...")
    result = pipeline.rubedo()
    print(f"   ✓ Piedra Filosofal: {result['gold']:.4f}")
    print(f"   Confianza: {result['confidence']:.1%}")
    print(f"   Tiempo: {pipeline.state.rubedo_duration*1000:.2f}ms")
    
    # Visualización
    print(pipeline.visualize_ascii())
    
    # Resumen
    total_time = (
        pipeline.state.nigredo_duration + 
        pipeline.state.albedo_duration + 
        pipeline.state.rubedo_duration
    )
    
    print("\n" + "=" * 60)
    print("   OPUS MAGNUM COMPLETADO")
    print("=" * 60)
    print(f"""
   📊 Resumen:
      • Tiempo total: {total_time*1000:.2f}ms
      • Muestras procesadas: {pipeline.state.nigredo_samples}
      • Ruido eliminado: {pipeline.state.noise_removed_percent:.1f}%
      • Correlación con verdad: {correlation:.4f}
      
   🔮 Interpretación:
      "El plomo (datos ruidosos) ha sido transmutado en oro
       (señal purificada lista para inferencia)."
    """)
    
    return pipeline


if __name__ == "__main__":
    pipeline = demonstrate_alchemy()
