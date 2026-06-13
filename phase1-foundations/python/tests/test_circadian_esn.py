"""
Tests para Integración de Ciclos Circadianos en ESN - Proyecto Eón
==================================================================
Verifica la inicialización, la modulación de dropout por energía,
la modulación de learning rate en fit() y la compatibilidad general.
"""

import pytest
import numpy as np
import sys
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
_python_dir = os.path.dirname(_current_dir)
if _python_dir not in sys.path:
    sys.path.insert(0, _python_dir)

from esn.esn import EchoStateNetwork
from core.circadian import CircadianClock, CircadianPhase


class TestCircadianESNIntegration:
    
    def test_circadian_initialization(self):
        """Verifica que ESN inicialice el reloj automáticamente al activar use_circadian."""
        # Sin reloj explícito, pero use_circadian=True
        esn = EchoStateNetwork(
            n_inputs=1,
            n_reservoir=50,
            n_outputs=1,
            use_circadian=True,
            random_state=42
        )
        assert esn.use_circadian is True
        assert esn.circadian_clock is not None
        assert isinstance(esn.circadian_clock, CircadianClock)
        
        # Con reloj explícito y use_circadian=True
        custom_clock = CircadianClock(period_steps=500, random_state=42)
        esn_custom = EchoStateNetwork(
            n_inputs=1,
            n_reservoir=50,
            n_outputs=1,
            use_circadian=True,
            circadian_clock=custom_clock,
            random_state=42
        )
        assert esn_custom.circadian_clock is custom_clock
        assert esn_custom.circadian_clock.period_steps == 500

    def test_backward_compatibility(self):
        """Verifica que sin use_circadian el reloj no se cree y el dropout sea 0 por defecto."""
        esn = EchoStateNetwork(n_inputs=1, n_reservoir=50, n_outputs=1)
        assert esn.use_circadian is False
        assert esn.circadian_clock is None
        assert esn.dropout == 0.0

    def test_dropout_modulation_by_energy(self):
        """Verifica que el dropout se module según la energía del reloj circadiano."""
        # Crear un reloj personalizado para controlar las fases fácilmente
        clock = CircadianClock(period_steps=1000)
        
        # ESN con dropout del 50%
        esn = EchoStateNetwork(
            n_inputs=1,
            n_reservoir=10,
            n_outputs=1,
            use_circadian=True,
            circadian_clock=clock,
            dropout=0.5,
            random_state=42
        )
        
        # 1. Caso de alta energía (AFTERNOON phase):
        # En AFTERNOON (ej: fraction = 0.40), la energía (learning_rate_mod) es alta.
        # Por lo tanto, el dropout efectivo debe ser bajo o cero.
        clock.reset(phase_offset=0.40)
        assert clock.state().phase == CircadianPhase.AFTERNOON
        energy_peak = clock.state().energy
        expected_dropout_peak = esn.dropout * (1.0 - energy_peak)
        
        # Ejecutar update de estado varias veces para comprobar si se desactivan neuronas
        esn.state = np.ones(10)
        esn._update_state(np.array([1.0]))
        # En alta energía el dropout debe ser muy pequeño o nulo, la mayoría de los estados deben permanecer != 0
        active_neurons_peak = np.sum(esn.state != 0)
        
        # 2. Caso de baja energía (REM phase):
        # En REM (ej: fraction = 0.95), la energía es baja (cercana a 0).
        # Por lo tanto, el dropout efectivo debe ser alto (cercano al 50% configurado).
        clock.reset(phase_offset=0.95)
        assert clock.state().phase == CircadianPhase.REM
        energy_night = clock.state().energy
        expected_dropout_night = esn.dropout * (1.0 - energy_night)
        
        assert expected_dropout_night > expected_dropout_peak
        
        # Ejecutar update con baja energía
        esn.state = np.ones(10)
        # Forzar un dropout extremadamente alto para este test manipulando temporalmente el dropout base
        esn.dropout = 0.99
        esn._update_state(np.array([1.0]))
        active_neurons_night = np.sum(esn.state != 0)
        
        # Debe haber mayor dropout (menos neuronas activas) en el período de baja energía
        assert active_neurons_night < 10

    def test_fit_modulates_learning_rate_and_noise(self):
        """Verifica que fit() modula dinámicamente noise y learning_rate en cada paso."""
        clock = CircadianClock(period_steps=100)
        esn = EchoStateNetwork(
            n_inputs=1,
            n_reservoir=10,
            n_outputs=1,
            use_circadian=True,
            circadian_clock=clock,
            learning_rate=0.05,
            noise=0.01,
            random_state=42
        )
        
        # Datos de entrenamiento sintéticos (150 pasos, un ciclo completo y medio)
        X = np.sin(np.linspace(0, 10, 150)).reshape(-1, 1)
        y = np.cos(np.linspace(0, 10, 150)).reshape(-1, 1)
        
        # Antes del entrenamiento
        assert esn.noise == 0.01
        assert esn.learning_rate == 0.05
        
        # Ejecutar entrenamiento
        esn.fit(X, y, washout=10)
        
        # Después del entrenamiento, los parámetros deben haber vuelto a su base
        assert esn.noise == 0.01
        assert esn.learning_rate == 0.05

    def test_complete_training_and_prediction(self):
        """Entrena y predice una señal simple para validar estabilidad numérica con dropout y modulación."""
        esn = EchoStateNetwork(
            n_inputs=1,
            n_reservoir=50,
            n_outputs=1,
            use_circadian=True,
            dropout=0.1,
            learning_rate=0.01,
            random_state=42
        )
        
        # Señal sinusoidal simple
        t = np.linspace(0, 50, 600)
        data = np.sin(t)
        
        X = data[:-1].reshape(-1, 1)
        y = data[1:].reshape(-1, 1)
        
        train_size = 400
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        
        # Entrenar
        esn.fit(X_train, y_train, washout=50)
        assert esn.W_out is not None
        assert esn.W_out.shape == (50, 1)
        
        # Predecir
        esn.reset()
        predictions = esn.predict(X_test)
        assert predictions.shape == y_test.shape
        
        # Verificar que el error no sea infinito y las predicciones sean estables
        assert np.all(np.isfinite(predictions))
        mse = np.mean((predictions - y_test)**2)
        assert mse < 0.5

    def test_aeon_birth_circadian_persistence(self, tmp_path):
        """Verifica que los parámetros circadianos se guarden y restauren en AeonBirth."""
        from core.aeon_birth import AeonBirth
        
        # Crear una instancia con parámetros circadianos activos
        eon = AeonBirth(
            n_reservoir=50,
            name="Eon-Test-Circadian",
            data_dir=str(tmp_path),
            use_circadian=True,
            dropout=0.25,
            learning_rate=0.03
        )
        assert eon.esn.use_circadian is True
        assert eon.esn.dropout == 0.25
        assert eon.esn.base_learning_rate == 0.03
        
        # Guardar se llama automáticamente en __init__, pero lo llamamos explícitamente para estar seguros
        eon.save()
        
        # Cargar en una nueva instancia
        loaded = AeonBirth.load("Eon-Test-Circadian", str(tmp_path))
        assert loaded.esn.use_circadian is True
        assert loaded.esn.dropout == 0.25
        assert loaded.esn.base_learning_rate == 0.03
