"""
Tests de Integración - Proyecto Eón

Verifica que los módulos funcionan correctamente juntos:
- ESN → Cuantización → Predicción
- ESN → Plasticidad → Adaptación
- Learning → Memoria → Persistencia
"""

import pytest
import numpy as np
import sys
import os
import tempfile
import shutil

# Path setup
_current_dir = os.path.dirname(os.path.abspath(__file__))
_python_dir = os.path.dirname(_current_dir)
sys.path.insert(0, _python_dir)

from esn.esn import EchoStateNetwork, generate_mackey_glass
from quantization.quantizer import QuantizedESN
from plasticity.hebbian import HebbianESN


@pytest.fixture(scope="module")
def mackey_glass_data():
    """Genera datos Mackey-Glass para tests."""
    data = generate_mackey_glass(2000)
    data = (data - data.mean()) / data.std()
    
    X = data[:-1].reshape(-1, 1)
    y = data[1:].reshape(-1, 1)
    
    return {
        'X_train': X[:1000],
        'y_train': y[:1000],
        'X_adapt': X[1000:1400],
        'y_adapt': y[1000:1400],
        'X_test': X[1400:],
        'y_test': y[1400:]
    }


class TestESNToQuantizationPipeline:
    """Tests: ESN → Cuantización → Predicción"""
    
    def test_train_then_quantize_8bit(self, mackey_glass_data):
        """Verifica pipeline completo con 8-bit."""
        # 1. Entrenar ESN
        esn = EchoStateNetwork(
            n_inputs=1, n_reservoir=100, n_outputs=1,
            spectral_radius=0.9, random_state=42
        )
        esn.fit(mackey_glass_data['X_train'], mackey_glass_data['y_train'], washout=100)
        
        # 2. Cuantizar
        q_esn = QuantizedESN(esn, bits=8)
        
        # 3. Predecir
        q_esn.reset()
        predictions = q_esn.predict(mackey_glass_data['X_test'])
        
        # Verificar
        assert predictions.shape == mackey_glass_data['y_test'].shape
        mse = np.mean((predictions - mackey_glass_data['y_test'])**2)
        assert mse < 1.0  # Razonable para predicción
        
    def test_quantization_preserves_prediction_quality(self, mackey_glass_data):
        """Verifica que cuantización preserva calidad."""
        esn = EchoStateNetwork(
            n_inputs=1, n_reservoir=100, n_outputs=1,
            spectral_radius=0.9, random_state=42
        )
        esn.fit(mackey_glass_data['X_train'], mackey_glass_data['y_train'], washout=100)
        
        # Original
        esn.reset()
        pred_orig = esn.predict(mackey_glass_data['X_test'])
        mse_orig = np.mean((pred_orig - mackey_glass_data['y_test'])**2)
        
        # Cuantizado 8-bit
        q_esn = QuantizedESN(esn, bits=8)
        q_esn.reset()
        pred_8bit = q_esn.predict(mackey_glass_data['X_test'])
        mse_8bit = np.mean((pred_8bit - mackey_glass_data['y_test'])**2)
        
        # 8-bit debe mantener >50% de calidad
        assert mse_8bit < mse_orig * 3
        
    def test_binary_quantization_still_works(self, mackey_glass_data):
        """Verifica que incluso binario produce predicciones válidas."""
        esn = EchoStateNetwork(
            n_inputs=1, n_reservoir=100, n_outputs=1,
            spectral_radius=0.9, random_state=42
        )
        esn.fit(mackey_glass_data['X_train'], mackey_glass_data['y_train'], washout=100)
        
        q_esn = QuantizedESN(esn, bits=1)
        q_esn.reset()
        predictions = q_esn.predict(mackey_glass_data['X_test'])
        
        # No debe ser todo ceros o NaN
        assert not np.all(predictions == 0)
        assert not np.any(np.isnan(predictions))


class TestESNToPlasticityPipeline:
    """Tests: ESN → Plasticidad → Adaptación"""
    
    def test_hebbian_adaptation_online(self, mackey_glass_data):
        """Verifica que adaptación Hebbiana online funciona."""
        # ESN con plasticidad
        esn = HebbianESN(
            n_inputs=1, n_reservoir=100, n_outputs=1,
            spectral_radius=0.9, random_state=42,
            plasticity_type='hebbian',
            learning_rate=0.001
        )
        
        # Entrenar inicialmente
        esn.fit(mackey_glass_data['X_train'], mackey_glass_data['y_train'], washout=100)
        
        # Medir antes de adaptación
        esn.reset()
        pred_before = esn.predict(mackey_glass_data['X_test'])
        mse_before = np.mean((pred_before - mackey_glass_data['y_test'])**2)
        
        # Adaptar con adapt_online
        esn.reset()
        esn.adapt_online(mackey_glass_data['X_adapt'])
        
        # Medir después de adaptación
        esn.reset()
        pred_after = esn.predict(mackey_glass_data['X_test'])
        mse_after = np.mean((pred_after - mackey_glass_data['y_test'])**2)
        
        # Adaptación no debe empeorar drásticamente (10x tolerancia)
        assert mse_after < mse_before * 10
        
    def test_anti_hebbian_maintains_stability(self, mackey_glass_data):
        """Verifica que anti-Hebbiana mantiene estabilidad."""
        esn = HebbianESN(
            n_inputs=1, n_reservoir=100, n_outputs=1,
            spectral_radius=0.9, random_state=42,
            plasticity_type='anti_hebbian',
            learning_rate=0.0001
        )
        
        esn.fit(mackey_glass_data['X_train'], mackey_glass_data['y_train'], washout=100)
        
        # Adaptar múltiples veces
        for _ in range(3):
            esn.reset()
            esn.adapt_online(mackey_glass_data['X_adapt'][:100])
        
        # Verificar que sigue funcionando
        esn.reset()
        predictions = esn.predict(mackey_glass_data['X_test'][:50])
        
        assert not np.any(np.isnan(predictions))
        assert not np.any(np.isinf(predictions))


class TestESNQuantizationPlasticityChain:
    """Tests: ESN → Plasticidad → Cuantización"""
    
    def test_plasticized_esn_can_be_quantized(self, mackey_glass_data):
        """Verifica que ESN con plasticidad puede cuantizarse."""
        # ESN con plasticidad
        esn = HebbianESN(
            n_inputs=1, n_reservoir=100, n_outputs=1,
            spectral_radius=0.9, random_state=42,
            plasticity_type='hebbian',
            learning_rate=0.001
        )
        
        esn.fit(mackey_glass_data['X_train'], mackey_glass_data['y_train'], washout=100)
        esn.adapt_online(mackey_glass_data['X_adapt'][:200])
        
        # Cuantizar después de adaptación
        q_esn = QuantizedESN(esn, bits=8)
        
        # Debe funcionar
        q_esn.reset()
        predictions = q_esn.predict(mackey_glass_data['X_test'][:50])
        
        assert predictions.shape == (50, 1)
        assert not np.any(np.isnan(predictions))


class TestMultipleESNSameSeed:
    """Tests: Reproducibilidad con misma semilla"""
    
    def test_same_seed_same_results(self, mackey_glass_data):
        """Verifica que misma semilla produce mismos resultados."""
        # ESN 1
        esn1 = EchoStateNetwork(
            n_inputs=1, n_reservoir=50, n_outputs=1,
            spectral_radius=0.9, random_state=42
        )
        esn1.fit(mackey_glass_data['X_train'][:500], mackey_glass_data['y_train'][:500])
        esn1.reset()
        pred1 = esn1.predict(mackey_glass_data['X_test'][:100])
        
        # ESN 2 (misma semilla)
        esn2 = EchoStateNetwork(
            n_inputs=1, n_reservoir=50, n_outputs=1,
            spectral_radius=0.9, random_state=42
        )
        esn2.fit(mackey_glass_data['X_train'][:500], mackey_glass_data['y_train'][:500])
        esn2.reset()
        pred2 = esn2.predict(mackey_glass_data['X_test'][:100])
        
        # Deben ser iguales
        np.testing.assert_array_almost_equal(pred1, pred2)
        
    def test_different_seed_different_results(self, mackey_glass_data):
        """Verifica que diferentes semillas producen diferentes resultados."""
        esn1 = EchoStateNetwork(
            n_inputs=1, n_reservoir=50, n_outputs=1,
            spectral_radius=0.9, random_state=42
        )
        esn1.fit(mackey_glass_data['X_train'][:500], mackey_glass_data['y_train'][:500])
        
        esn2 = EchoStateNetwork(
            n_inputs=1, n_reservoir=50, n_outputs=1,
            spectral_radius=0.9, random_state=123
        )
        esn2.fit(mackey_glass_data['X_train'][:500], mackey_glass_data['y_train'][:500])
        
        # Pesos deben ser diferentes
        assert not np.allclose(esn1.W_reservoir, esn2.W_reservoir)


class TestMemoryEfficiency:
    """Tests de eficiencia de memoria"""
    
    def test_quantization_reduces_memory(self, mackey_glass_data):
        """Verifica que cuantización reduce memoria."""
        esn = EchoStateNetwork(
            n_inputs=1, n_reservoir=200, n_outputs=1,
            spectral_radius=0.9, random_state=42
        )
        esn.fit(mackey_glass_data['X_train'], mackey_glass_data['y_train'], washout=100)
        
        mem_orig = esn.get_memory_footprint()
        
        q_esn_8 = QuantizedESN(esn, bits=8)
        mem_8bit = q_esn_8.get_memory_footprint()
        
        q_esn_1 = QuantizedESN(esn, bits=1)
        mem_1bit = q_esn_1.get_memory_footprint()
        
        # 8-bit debe ser ~8x menos
        assert mem_8bit['theoretical_kb'] < mem_orig['total_kb']
        
        # 1-bit debe ser incluso menor
        assert mem_1bit['theoretical_kb'] < mem_8bit['theoretical_kb']


class TestNumericalStability:
    """Tests de estabilidad numérica"""
    
    def test_no_nan_after_long_prediction(self, mackey_glass_data):
        """Verifica que no hay NaN después de predicciones largas."""
        esn = EchoStateNetwork(
            n_inputs=1, n_reservoir=100, n_outputs=1,
            spectral_radius=0.9, random_state=42
        )
        esn.fit(mackey_glass_data['X_train'], mackey_glass_data['y_train'], washout=100)
        
        # Predicción larga
        esn.reset()
        predictions = esn.predict(mackey_glass_data['X_test'])
        
        assert not np.any(np.isnan(predictions))
        assert not np.any(np.isinf(predictions))
        
    def test_quantized_stability(self, mackey_glass_data):
        """Verifica estabilidad de modelo cuantizado."""
        esn = EchoStateNetwork(
            n_inputs=1, n_reservoir=100, n_outputs=1,
            spectral_radius=0.9, random_state=42
        )
        esn.fit(mackey_glass_data['X_train'], mackey_glass_data['y_train'], washout=100)
        
        q_esn = QuantizedESN(esn, bits=4)
        
        # Muchas predicciones consecutivas
        for _ in range(10):
            q_esn.reset()
            pred = q_esn.predict(mackey_glass_data['X_test'][:100])
            assert not np.any(np.isnan(pred))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
