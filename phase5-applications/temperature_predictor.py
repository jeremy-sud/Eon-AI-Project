"""
Proyecto Eón - Aplicación IoT: Predicción y Anomalías
======================================================

Sistema de predicción de temperatura y detección de anomalías
usando el ESN ultraligero.

Uso:
    python temperature_predictor.py

(c) 2024 Sistemas Ursol - Jeremy Arias Solano
"""

import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path

# Añadir path del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "phase1-foundations" / "python"))

from esn.esn import EchoStateNetwork
import numpy as np


class TemperaturePredictor:
    """
    Predictor de temperatura con detección de anomalías.
    
    Usa un ESN pequeño para predecir la temperatura futura
    y detectar valores anómalos basados en el error de predicción.
    """
    
    def __init__(self, n_reservoir=32, anomaly_threshold=2.0):
        """
        Args:
            n_reservoir: Neuronas del reservoir
            anomaly_threshold: Umbral de desviaciones estándar para anomalía
        """
        self.esn = EchoStateNetwork(
            n_inputs=1,
            n_outputs=1,
            n_reservoir=n_reservoir,
            spectral_radius=0.9,
            sparsity=0.9
        )
        self.anomaly_threshold = anomaly_threshold
        self.is_trained = False
        self.prediction_errors = []
        self.error_mean = 0
        self.error_std = 1
        
    def train(self, temperatures: np.ndarray, washout: int = 50):
        """
        Entrena con datos históricos de temperatura.
        
        Args:
            temperatures: Array de temperaturas
            washout: Muestras a descartar
        """
        # Normalizar
        self.temp_mean = np.mean(temperatures)
        self.temp_std = np.std(temperatures) or 1
        normalized = (temperatures - self.temp_mean) / self.temp_std
        
        # Preparar datos: predecir siguiente valor
        X = normalized[:-1].reshape(-1, 1)
        Y = normalized[1:].reshape(-1, 1)
        
        # Entrenar
        self.esn.fit(X, Y, washout=washout)
        
        # Calcular errores de predicción para calibrar anomalías
        predictions = self.esn.predict(X)
        errors = np.abs(predictions.flatten() - Y.flatten())
        self.error_mean = np.mean(errors)
        self.error_std = np.std(errors) or 1
        
        self.is_trained = True
        
        mse = np.mean(errors ** 2)
        return mse
    
    def predict_next(self, current_temp: float) -> dict:
        """
        Predice la siguiente temperatura y detecta anomalías.
        
        Args:
            current_temp: Temperatura actual
            
        Returns:
            dict con prediction, is_anomaly, confidence
        """
        if not self.is_trained:
            raise RuntimeError("Modelo no entrenado")
        
        # Normalizar
        normalized = (current_temp - self.temp_mean) / self.temp_std
        
        # Predecir (usar el ESN directamente)
        input_arr = np.array([[normalized]])
        pred_normalized = self.esn.predict(input_arr)[0, 0]
        
        # Desnormalizar
        prediction = pred_normalized * self.temp_std + self.temp_mean
        
        # Detectar anomalía basada en valor actual vs predicción anterior
        if len(self.prediction_errors) > 0:
            last_prediction = self.prediction_errors[-1]['predicted']
            error = abs(current_temp - last_prediction)
            normalized_error = (error - self.error_mean * self.temp_std) / (self.error_std * self.temp_std + 1e-6)
            is_anomaly = normalized_error > self.anomaly_threshold
            confidence = 1 - min(normalized_error / (self.anomaly_threshold * 2), 1)
        else:
            is_anomaly = False
            confidence = 1.0
            error = 0
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'current': current_temp,
            'predicted_next': round(prediction, 2),
            'is_anomaly': is_anomaly,
            'confidence': round(confidence, 3),
            'error': round(error, 2)
        }
        
        self.prediction_errors.append({
            'actual': current_temp,
            'predicted': prediction
        })
        
        # Mantener solo las últimas 100
        if len(self.prediction_errors) > 100:
            self.prediction_errors.pop(0)
        
        return result
    
    def get_stats(self) -> dict:
        """Estadísticas del predictor."""
        return {
            'reservoir_size': self.esn.n_reservoir,
            'is_trained': self.is_trained,
            'temp_mean': round(self.temp_mean, 2) if hasattr(self, 'temp_mean') else None,
            'temp_std': round(self.temp_std, 2) if hasattr(self, 'temp_std') else None,
            'anomaly_threshold': self.anomaly_threshold,
            'samples_processed': len(self.prediction_errors)
        }


class AnomalyDetector:
    """
    Detector de anomalías genérico basado en ESN.
    
    Aprende el patrón "normal" de una señal y alerta
    cuando el comportamiento se desvía significativamente.
    """
    
    def __init__(self, n_reservoir=32, window_size=50, threshold=3.0):
        self.esn = EchoStateNetwork(
            n_inputs=1,
            n_outputs=1,
            n_reservoir=n_reservoir,
            spectral_radius=0.95,
            sparsity=0.85
        )
        self.window_size = window_size
        self.threshold = threshold
        self.history = []
        self.errors = []
        self.is_trained = False
        
    def train(self, normal_data: np.ndarray):
        """Entrena con datos que representan comportamiento normal."""
        # Normalizar
        self.data_mean = np.mean(normal_data)
        self.data_std = np.std(normal_data) or 1
        normalized = (normal_data - self.data_mean) / self.data_std
        
        # Entrenar para predecir siguiente valor
        X = normalized[:-1].reshape(-1, 1)
        Y = normalized[1:].reshape(-1, 1)
        
        self.esn.fit(X, Y, washout=min(50, len(X) // 4))
        
        # Calibrar errores normales
        predictions = self.esn.predict(X)
        self.normal_errors = np.abs(predictions.flatten() - Y.flatten())
        self.error_baseline = np.mean(self.normal_errors)
        self.error_scale = np.std(self.normal_errors) or 1
        
        self.is_trained = True
        
    def check(self, value: float) -> dict:
        """
        Verifica si un valor es anómalo.
        
        Returns:
            dict con is_anomaly, severity, details
        """
        if not self.is_trained:
            raise RuntimeError("Detector no entrenado")
        
        # Normalizar
        normalized = (value - self.data_mean) / self.data_std
        
        # Predecir
        self.esn.update(np.array([[normalized]]))
        pred = self.esn.predict(np.array([[normalized]]))[0, 0]
        
        # Calcular error
        error = abs(normalized - pred)
        severity = (error - self.error_baseline) / self.error_scale
        
        is_anomaly = severity > self.threshold
        
        # Guardar historial
        self.history.append(value)
        self.errors.append(error)
        
        if len(self.history) > self.window_size:
            self.history.pop(0)
            self.errors.pop(0)
        
        return {
            'value': value,
            'is_anomaly': is_anomaly,
            'severity': round(float(severity), 2),
            'threshold': self.threshold,
            'recent_anomaly_rate': sum(e > self.error_baseline + self.error_scale * self.threshold 
                                       for e in self.errors) / len(self.errors) if self.errors else 0
        }


# Demo
if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║       PROYECTO EÓN - Aplicación IoT: Predicción y Anomalías   ║
║              "La inteligencia no se crea, se descubre."       ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Simular datos de temperatura (24 horas, cada 10 minutos)
    np.random.seed(42)
    hours = np.linspace(0, 24, 144)
    
    # Patrón diurno + ruido
    temperature = 20 + 5 * np.sin((hours - 6) * np.pi / 12) + np.random.normal(0, 0.5, len(hours))
    
    print("[1/3] Entrenando predictor de temperatura...")
    predictor = TemperaturePredictor(n_reservoir=32)
    mse = predictor.train(temperature[:100])
    print(f"      MSE: {mse:.6f}")
    
    print("\n[2/3] Probando predicciones...")
    print("      Hora    | Actual | Predicho | Anomalía")
    print("      --------|--------|----------|----------")
    
    # Insertar una anomalía artificial
    temperature[110] = 40  # Pico anómalo
    
    for i in range(100, 120):
        result = predictor.predict_next(temperature[i])
        hora = f"{hours[i]:.1f}h"
        anomaly_str = "⚠️ SÍ" if result['is_anomaly'] else "  no"
        print(f"      {hora:>6} | {result['current']:>6.1f} | {result['predicted_next']:>8.1f} | {anomaly_str}")
    
    print("\n[3/3] Estadísticas del predictor:")
    stats = predictor.get_stats()
    for key, value in stats.items():
        print(f"      • {key}: {value}")
    
    print("\n✓ Demo completado")
    print("Proyecto Eón - Sistemas Ursol")
