"""
Proyecto Eón - Detector de Anomalías basado en ESN
===================================================

Usa el error de predicción del Echo State Network como indicador
de anomalías. Cuando el ESN encuentra patrones que no ha visto,
su error de predicción aumenta significativamente.

Principio:
---------
1. El ESN aprende patrones "normales" durante entrenamiento
2. Durante inferencia, predice el siguiente valor
3. Si el error es alto (>3σ), el punto es anómalo

Aplicaciones:
- Monitoreo IoT (sensores industriales)
- Detección de fraude (transacciones atípicas)
- Salud (arritmias, anomalías en señales vitales)
- Mantenimiento predictivo

(c) 2024 Proyecto Eón - Jeremy Arias Solano
"""

import numpy as np
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Callable
from enum import Enum
import time
import logging

# Path setup
import sys
import os
_current_dir = os.path.dirname(os.path.abspath(__file__))
_python_dir = os.path.dirname(_current_dir)
if _python_dir not in sys.path:
    sys.path.insert(0, _python_dir)

from esn.esn import EchoStateNetwork

# Importar constantes globales
try:
    from utils.constants import (
        EPSILON, ANOMALY_THRESHOLD_SIGMA, 
        WARNING_THRESHOLD_SIGMA, CRITICAL_THRESHOLD_SIGMA,
        DEFAULT_BUFFER_SIZE, DEFAULT_ANOMALY_COOLDOWN
    )
except ImportError:
    EPSILON = 1e-10
    ANOMALY_THRESHOLD_SIGMA = 3.0
    WARNING_THRESHOLD_SIGMA = 2.0
    CRITICAL_THRESHOLD_SIGMA = 5.0
    DEFAULT_BUFFER_SIZE = 1000
    DEFAULT_ANOMALY_COOLDOWN = 5.0

logger = logging.getLogger(__name__)


class AnomalySeverity(Enum):
    """Niveles de severidad de anomalía."""
    NORMAL = "normal"           # z-score < 2
    WARNING = "warning"         # 2 <= z-score < 3
    ANOMALY = "anomaly"         # 3 <= z-score < 5
    CRITICAL = "critical"       # z-score >= 5


@dataclass
class AnomalyEvent:
    """Representa un evento de anomalía detectado."""
    timestamp: float
    value: np.ndarray
    predicted: np.ndarray
    error: float
    z_score: float
    severity: AnomalySeverity
    description: str
    context: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Serializa el evento para logging/transmisión."""
        return {
            "timestamp": self.timestamp,
            "value": self.value.tolist() if hasattr(self.value, 'tolist') else float(self.value),
            "predicted": self.predicted.tolist() if hasattr(self.predicted, 'tolist') else float(self.predicted),
            "error": self.error,
            "z_score": self.z_score,
            "severity": self.severity.value,
            "description": self.description,
            "context": self.context
        }


@dataclass
class DetectorStats:
    """Estadísticas del detector."""
    samples_processed: int = 0
    anomalies_detected: int = 0
    warnings_detected: int = 0
    critical_detected: int = 0
    mean_error: float = 0.0
    std_error: float = 1.0
    last_anomaly_time: Optional[float] = None
    
    @property
    def anomaly_rate(self) -> float:
        """Tasa de anomalías detectadas."""
        if self.samples_processed == 0:
            return 0.0
        return self.anomalies_detected / self.samples_processed


class AnomalyDetector:
    """
    Detector de anomalías basado en error de predicción ESN.
    
    El ESN aprende patrones "normales" durante entrenamiento.
    Durante inferencia, compara predicciones con valores reales.
    Errores significativamente altos indican anomalías.
    
    Attributes:
        esn: Echo State Network entrenado
        threshold_sigma: Umbral en desviaciones estándar (default 3.0)
        window_size: Tamaño de ventana para estadísticas móviles
        adaptive: Si True, actualiza estadísticas continuamente
    
    Example:
        >>> esn = EchoStateNetwork(n_inputs=1, n_reservoir=100, n_outputs=1)
        >>> esn.fit(normal_data, normal_data[1:])  # Predecir siguiente valor
        >>> 
        >>> detector = AnomalyDetector(esn, threshold_sigma=3.0)
        >>> detector.fit_baseline(normal_data)
        >>> 
        >>> for point in stream:
        ...     is_anomaly, score, event = detector.detect(point)
        ...     if is_anomaly:
        ...         alert(event)
    """
    
    def __init__(
        self,
        esn: EchoStateNetwork,
        threshold_sigma: float = 3.0,
        window_size: int = 1000,
        adaptive: bool = True,
        warmup_samples: int = 100
    ):
        """
        Inicializa el detector de anomalías.
        
        Args:
            esn: ESN entrenado para predicción
            threshold_sigma: Umbral en desviaciones estándar
            window_size: Tamaño de ventana para estadísticas
            adaptive: Actualizar estadísticas continuamente
            warmup_samples: Muestras antes de detectar
        """
        self.esn = esn
        self.threshold_sigma = threshold_sigma
        self.window_size = window_size
        self.adaptive = adaptive
        self.warmup_samples = warmup_samples
        
        # Buffer de errores para estadísticas móviles
        self.error_history: deque = deque(maxlen=window_size)
        
        # Estadísticas de baseline
        self.mean_error: float = 0.0
        self.std_error: float = 1.0
        self.is_calibrated: bool = False
        
        # Historial de anomalías
        self.anomaly_history: List[AnomalyEvent] = []
        self.max_history: int = 1000
        
        # Estadísticas generales
        self.stats = DetectorStats()
        
        # Callbacks para alertas
        self._callbacks: List[Callable[[AnomalyEvent], None]] = []
        
        # Estado anterior para predicción
        self._last_input: Optional[np.ndarray] = None
        
        logger.info(f"AnomalyDetector inicializado: threshold={threshold_sigma}σ, window={window_size}")
    
    def fit_baseline(self, normal_data: np.ndarray, verbose: bool = False) -> 'AnomalyDetector':
        """
        Establece baseline de errores usando datos normales.
        
        Calcula media y desviación estándar de errores de predicción
        sobre un conjunto de datos que se considera "normal".
        
        Args:
            normal_data: Datos de entrenamiento (T, n_inputs)
            verbose: Mostrar progreso
            
        Returns:
            self para encadenamiento
        """
        if len(normal_data) < self.warmup_samples:
            raise ValueError(f"Necesita al menos {self.warmup_samples} muestras para calibrar")
        
        # Asegurar dimensiones correctas
        if normal_data.ndim == 1:
            normal_data = normal_data.reshape(-1, 1)
        
        # Reset ESN state
        self.esn.reset()
        
        # Calcular errores de predicción
        errors = []
        
        for i in range(len(normal_data) - 1):
            current = normal_data[i:i+1]
            next_val = normal_data[i+1:i+2]
            
            # Predecir siguiente valor
            pred = self.esn.predict(current)
            
            # Calcular error
            error = np.mean(np.abs(next_val - pred))
            errors.append(error)
            
            if verbose and (i + 1) % 500 == 0:
                logger.info(f"Calibración: {i+1}/{len(normal_data)-1} muestras")
        
        errors = np.array(errors)
        
        # Calcular estadísticas de baseline
        self.mean_error = float(np.mean(errors))
        self.std_error = float(np.std(errors))
        
        # Evitar división por cero
        if self.std_error < 1e-10:
            self.std_error = 1e-10
            logger.warning("std_error muy pequeño, ajustado a 1e-10")
        
        # Inicializar buffer con errores históricos
        for e in errors[-self.window_size:]:
            self.error_history.append(e)
        
        self.is_calibrated = True
        self.stats.mean_error = self.mean_error
        self.stats.std_error = self.std_error
        
        logger.info(f"Baseline calibrado: mean={self.mean_error:.6f}, std={self.std_error:.6f}")
        
        return self
    
    def detect(self, new_point: np.ndarray) -> Tuple[bool, float, Optional[AnomalyEvent]]:
        """
        Detecta si un nuevo punto es anómalo.
        
        Args:
            new_point: Nuevo valor a evaluar (n_inputs,)
            
        Returns:
            Tuple de (is_anomaly, z_score, AnomalyEvent o None)
        """
        if not self.is_calibrated:
            raise RuntimeError("Detector no calibrado. Llama fit_baseline() primero.")
        
        # Asegurar dimensiones
        if new_point.ndim == 1:
            new_point = new_point.reshape(1, -1)
        
        # Predecir valor actual basado en estado anterior
        prediction = self.esn.predict(new_point)
        
        # Calcular error (usamos el estado anterior para la predicción real)
        if self._last_input is not None:
            # Predecir este punto basado en el anterior
            self.esn.reset()
            _ = self.esn.predict(self._last_input)  # Actualizar estado
            actual_pred = self.esn.predict(new_point)
            error = float(np.mean(np.abs(new_point - actual_pred)))
        else:
            # Primera muestra, usar predicción directa
            error = float(np.mean(np.abs(new_point - prediction)))
        
        # Guardar para siguiente iteración
        self._last_input = new_point.copy()
        
        # Calcular z-score
        z_score = (error - self.mean_error) / self.std_error
        
        # Determinar severidad
        severity = self._get_severity(z_score)
        is_anomaly = severity in [AnomalySeverity.ANOMALY, AnomalySeverity.CRITICAL]
        
        # Actualizar estadísticas
        self.stats.samples_processed += 1
        
        if self.adaptive:
            self._update_statistics(error)
        
        # Crear evento si es anomalía
        event = None
        if severity != AnomalySeverity.NORMAL:
            event = self._create_event(
                new_point, prediction, error, z_score, severity
            )
            self._record_event(event)
            
            # Ejecutar callbacks
            for callback in self._callbacks:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error en callback: {e}")
        
        return is_anomaly, z_score, event
    
    def detect_batch(self, data: np.ndarray) -> List[AnomalyEvent]:
        """
        Detecta anomalías en un batch de datos.
        
        Args:
            data: Secuencia de datos (T, n_inputs)
            
        Returns:
            Lista de eventos de anomalía detectados
        """
        if data.ndim == 1:
            data = data.reshape(-1, 1)
        
        anomalies = []
        for i in range(len(data)):
            is_anomaly, _, event = self.detect(data[i])
            if event is not None:
                anomalies.append(event)
        
        return anomalies
    
    def _get_severity(self, z_score: float) -> AnomalySeverity:
        """Determina severidad basada en z-score."""
        abs_z = abs(z_score)
        if abs_z >= 5.0:
            return AnomalySeverity.CRITICAL
        elif abs_z >= self.threshold_sigma:
            return AnomalySeverity.ANOMALY
        elif abs_z >= 2.0:
            return AnomalySeverity.WARNING
        return AnomalySeverity.NORMAL
    
    def _create_event(
        self,
        value: np.ndarray,
        predicted: np.ndarray,
        error: float,
        z_score: float,
        severity: AnomalySeverity
    ) -> AnomalyEvent:
        """Crea un evento de anomalía."""
        descriptions = {
            AnomalySeverity.WARNING: "Desviación moderada detectada",
            AnomalySeverity.ANOMALY: "¡Anomalía detectada!",
            AnomalySeverity.CRITICAL: "⚠️ ANOMALÍA CRÍTICA ⚠️"
        }
        
        return AnomalyEvent(
            timestamp=time.time(),
            value=value.flatten(),
            predicted=predicted.flatten(),
            error=error,
            z_score=z_score,
            severity=severity,
            description=descriptions.get(severity, ""),
            context={
                "mean_error": self.mean_error,
                "std_error": self.std_error,
                "threshold": self.threshold_sigma,
                "samples_processed": self.stats.samples_processed
            }
        )
    
    def _record_event(self, event: AnomalyEvent):
        """Registra evento en historial y estadísticas."""
        # Actualizar estadísticas
        if event.severity == AnomalySeverity.WARNING:
            self.stats.warnings_detected += 1
        elif event.severity == AnomalySeverity.ANOMALY:
            self.stats.anomalies_detected += 1
            self.stats.last_anomaly_time = event.timestamp
        elif event.severity == AnomalySeverity.CRITICAL:
            self.stats.anomalies_detected += 1
            self.stats.critical_detected += 1
            self.stats.last_anomaly_time = event.timestamp
        
        # Guardar en historial
        self.anomaly_history.append(event)
        if len(self.anomaly_history) > self.max_history:
            self.anomaly_history.pop(0)
        
        logger.info(f"{event.severity.value.upper()}: z={event.z_score:.2f}, error={event.error:.6f}")
    
    def _update_statistics(self, error: float):
        """Actualiza estadísticas móviles."""
        self.error_history.append(error)
        
        if len(self.error_history) >= self.warmup_samples:
            errors = np.array(self.error_history)
            self.mean_error = float(np.mean(errors))
            self.std_error = float(np.std(errors))
            
            if self.std_error < 1e-10:
                self.std_error = 1e-10
            
            self.stats.mean_error = self.mean_error
            self.stats.std_error = self.std_error
    
    def add_callback(self, callback: Callable[[AnomalyEvent], None]):
        """Añade callback para alertas de anomalía."""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[AnomalyEvent], None]):
        """Elimina callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas del detector."""
        return {
            "samples_processed": self.stats.samples_processed,
            "anomalies_detected": self.stats.anomalies_detected,
            "warnings_detected": self.stats.warnings_detected,
            "critical_detected": self.stats.critical_detected,
            "anomaly_rate": self.stats.anomaly_rate,
            "mean_error": self.mean_error,
            "std_error": self.std_error,
            "threshold_sigma": self.threshold_sigma,
            "is_calibrated": self.is_calibrated,
            "last_anomaly_time": self.stats.last_anomaly_time
        }
    
    def get_recent_anomalies(self, n: int = 10) -> List[AnomalyEvent]:
        """Retorna las n anomalías más recientes."""
        return self.anomaly_history[-n:]
    
    def reset(self):
        """Resetea el detector manteniendo calibración."""
        self.error_history.clear()
        self.anomaly_history.clear()
        self.stats = DetectorStats()
        self.stats.mean_error = self.mean_error
        self.stats.std_error = self.std_error
        self._last_input = None
        self.esn.reset()
        logger.info("Detector reseteado")
    
    def recalibrate(self, new_normal_data: np.ndarray):
        """Recalibra el detector con nuevos datos normales."""
        self.is_calibrated = False
        self.error_history.clear()
        self.fit_baseline(new_normal_data)


class StreamingAnomalyDetector(AnomalyDetector):
    """
    Versión streaming del detector para datos en tiempo real.
    
    Optimizado para:
    - Baja latencia (<1ms por punto)
    - Memoria constante
    - Adaptación continua
    """
    
    def __init__(
        self,
        esn: EchoStateNetwork,
        threshold_sigma: float = 3.0,
        window_size: int = 500,
        alert_cooldown: float = 5.0
    ):
        """
        Args:
            alert_cooldown: Segundos mínimos entre alertas
        """
        super().__init__(
            esn=esn,
            threshold_sigma=threshold_sigma,
            window_size=window_size,
            adaptive=True
        )
        self.alert_cooldown = alert_cooldown
        self._last_alert_time = 0.0
    
    def detect_streaming(self, new_point: np.ndarray) -> Tuple[bool, float, Optional[AnomalyEvent]]:
        """
        Detección optimizada para streaming.
        
        Incluye cooldown para evitar alertas excesivas.
        """
        is_anomaly, z_score, event = self.detect(new_point)
        
        # Aplicar cooldown
        if event is not None:
            current_time = time.time()
            if current_time - self._last_alert_time < self.alert_cooldown:
                # Dentro de cooldown, degradar a warning
                if event.severity == AnomalySeverity.ANOMALY:
                    event = None
                    is_anomaly = False
            else:
                self._last_alert_time = current_time
        
        return is_anomaly, z_score, event


def create_synthetic_anomalies(
    normal_data: np.ndarray,
    anomaly_ratio: float = 0.05,
    anomaly_magnitude: float = 3.0,
    seed: int = 42
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Crea datos con anomalías sintéticas para testing.
    
    Args:
        normal_data: Datos base
        anomaly_ratio: Proporción de anomalías
        anomaly_magnitude: Magnitud de anomalías (en std)
        seed: Semilla aleatoria
        
    Returns:
        (data_with_anomalies, anomaly_mask)
    """
    rng = np.random.default_rng(seed)
    data = normal_data.copy()
    n_anomalies = int(len(data) * anomaly_ratio)
    
    # Índices aleatorios para anomalías
    anomaly_indices = rng.choice(len(data), n_anomalies, replace=False)
    
    # Crear máscara
    mask = np.zeros(len(data), dtype=bool)
    mask[anomaly_indices] = True
    
    # Insertar anomalías
    std = np.std(data)
    for idx in anomaly_indices:
        # Spike positivo o negativo
        direction = rng.choice([-1, 1])
        data[idx] += direction * anomaly_magnitude * std
    
    return data, mask


# Ejemplo de uso
if __name__ == "__main__":
    from esn.esn import EchoStateNetwork, generate_mackey_glass
    
    # Generar datos
    print("Generando datos Mackey-Glass...")
    data = generate_mackey_glass(2000)
    
    # Dividir en entrenamiento y test
    train_data = data[:1000]
    test_data = data[1000:]
    
    # Crear y entrenar ESN
    print("Entrenando ESN...")
    esn = EchoStateNetwork(
        n_inputs=1,
        n_reservoir=100,
        n_outputs=1,
        spectral_radius=0.9,
        random_state=42
    )
    
    # Entrenar para predecir siguiente valor
    X_train = train_data[:-1].reshape(-1, 1)
    y_train = train_data[1:].reshape(-1, 1)
    esn.fit(X_train, y_train, washout=100)
    
    # Crear detector
    print("Calibrando detector...")
    detector = AnomalyDetector(esn, threshold_sigma=3.0)
    detector.fit_baseline(train_data.reshape(-1, 1))
    
    # Crear datos de test con anomalías
    print("Creando anomalías sintéticas...")
    test_with_anomalies, anomaly_mask = create_synthetic_anomalies(
        test_data, anomaly_ratio=0.05, anomaly_magnitude=4.0
    )
    
    # Detectar
    print("\nDetectando anomalías...")
    detected_mask = np.zeros(len(test_with_anomalies), dtype=bool)
    
    for i, point in enumerate(test_with_anomalies):
        is_anomaly, z_score, event = detector.detect(np.array([point]))
        detected_mask[i] = is_anomaly
    
    # Métricas
    true_positives = np.sum(detected_mask & anomaly_mask)
    false_positives = np.sum(detected_mask & ~anomaly_mask)
    false_negatives = np.sum(~detected_mask & anomaly_mask)
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"\n=== Resultados ===")
    print(f"Anomalías reales: {np.sum(anomaly_mask)}")
    print(f"Anomalías detectadas: {np.sum(detected_mask)}")
    print(f"True Positives: {true_positives}")
    print(f"False Positives: {false_positives}")
    print(f"False Negatives: {false_negatives}")
    print(f"Precision: {precision:.2%}")
    print(f"Recall: {recall:.2%}")
    print(f"F1 Score: {f1:.2%}")
    
    print(f"\n{detector.get_stats()}")
