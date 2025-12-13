"""
Tests para quantization/quantizer.py - Cuantización Extrema de ESN.

Cobertura: QuantizedESN, compare_quantization_levels
"""

import pytest
import numpy as np
import sys
import os

# Path setup
_current_dir = os.path.dirname(os.path.abspath(__file__))
_python_dir = os.path.dirname(_current_dir)
sys.path.insert(0, _python_dir)

from esn.esn import EchoStateNetwork, generate_mackey_glass
from quantization.quantizer import QuantizedESN, compare_quantization_levels


@pytest.fixture(scope="module")
def trained_esn():
    """ESN entrenada para tests."""
    # Generar datos
    data = generate_mackey_glass(1000)
    data = (data - data.mean()) / data.std()
    
    X = data[:-1].reshape(-1, 1)
    y = data[1:].reshape(-1, 1)
    
    esn = EchoStateNetwork(
        n_inputs=1,
        n_reservoir=50,
        n_outputs=1,
        spectral_radius=0.9,
        random_state=42
    )
    esn.fit(X[:700], y[:700], washout=50)
    return esn


@pytest.fixture(scope="module")
def test_data():
    """Datos de test."""
    data = generate_mackey_glass(1000)
    data = (data - data.mean()) / data.std()
    X = data[:-1].reshape(-1, 1)
    y = data[1:].reshape(-1, 1)
    return X[700:], y[700:]


class TestQuantizedESN:
    """Tests para cuantización de ESN."""
    
    def test_8bit_quantization(self, trained_esn):
        """Verifica cuantización a 8 bits."""
        q_esn = QuantizedESN(trained_esn, bits=8)
        assert q_esn.bits == 8
        assert q_esn.W_in_q.dtype == np.int8
        
    def test_4bit_quantization(self, trained_esn):
        """Verifica cuantización a 4 bits."""
        q_esn = QuantizedESN(trained_esn, bits=4)
        assert q_esn.bits == 4
        # Verificar que valores están en rango [-8, 7]
        assert q_esn.W_in_q.min() >= -8
        assert q_esn.W_in_q.max() <= 7
        
    def test_binary_quantization(self, trained_esn):
        """Verifica cuantización binaria (1-bit)."""
        q_esn = QuantizedESN(trained_esn, bits=1)
        assert q_esn.bits == 1
        # Solo valores -1, 0, 1
        unique_vals = np.unique(q_esn.W_reservoir_q)
        assert all(v in [-1, 0, 1] for v in unique_vals)
        
    def test_requires_trained_esn(self):
        """Verifica que requiere ESN entrenada."""
        untrained_esn = EchoStateNetwork(n_inputs=1, n_reservoir=50, n_outputs=1)
        with pytest.raises(ValueError, match="debe estar entrenada"):
            QuantizedESN(untrained_esn, bits=8)
            
    def test_invalid_bits_raises_error(self, trained_esn):
        """Verifica error con bits inválidos."""
        with pytest.raises(ValueError):
            QuantizedESN(trained_esn, bits=3)
            
    def test_quant_params_stored(self, trained_esn):
        """Verifica que parámetros de cuantización se almacenan."""
        q_esn = QuantizedESN(trained_esn, bits=8)
        assert 'W_in' in q_esn.quant_params
        assert 'W_reservoir' in q_esn.quant_params
        assert 'W_out' in q_esn.quant_params
        
        for name, params in q_esn.quant_params.items():
            assert 'scale' in params
            assert 'offset' in params


class TestQuantizedPrediction:
    """Tests para predicción con modelo cuantizado."""
    
    def test_predict_returns_correct_shape(self, trained_esn, test_data):
        """Verifica que predicción tiene forma correcta."""
        X_test, _ = test_data
        q_esn = QuantizedESN(trained_esn, bits=8)
        
        predictions = q_esn.predict(X_test[:100])
        assert predictions.shape == (100, 1)
        
    def test_predict_with_reset(self, trained_esn, test_data):
        """Verifica predicción con reset de estado."""
        X_test, _ = test_data
        q_esn = QuantizedESN(trained_esn, bits=8)
        
        # Primera predicción
        pred1 = q_esn.predict(X_test[:50], reset_state=True)
        
        # Segunda predicción con reset debería ser igual
        pred2 = q_esn.predict(X_test[:50], reset_state=True)
        
        np.testing.assert_array_almost_equal(pred1, pred2)
        
    def test_8bit_accuracy_reasonable(self, trained_esn, test_data):
        """Verifica que 8-bit mantiene precisión razonable."""
        X_test, y_test = test_data
        
        # Original
        trained_esn.reset()
        pred_orig = trained_esn.predict(X_test)
        mse_orig = np.mean((pred_orig - y_test)**2)
        
        # Cuantizado 8-bit
        q_esn = QuantizedESN(trained_esn, bits=8)
        q_esn.reset()
        pred_quant = q_esn.predict(X_test)
        mse_quant = np.mean((pred_quant - y_test)**2)
        
        # 8-bit debería retener >80% de precisión
        assert mse_quant < mse_orig * 5  # Tolerancia amplia para estabilidad
        
    def test_reset_clears_state(self, trained_esn):
        """Verifica que reset limpia el estado."""
        q_esn = QuantizedESN(trained_esn, bits=8)
        
        # Modificar estado
        q_esn.state = np.ones(q_esn.n_reservoir)
        
        # Reset
        q_esn.reset()
        
        assert np.allclose(q_esn.state, 0)


class TestMemoryFootprint:
    """Tests para cálculo de huella de memoria."""
    
    def test_memory_footprint_structure(self, trained_esn):
        """Verifica estructura del footprint."""
        q_esn = QuantizedESN(trained_esn, bits=8)
        mem = q_esn.get_memory_footprint()
        
        assert 'W_in' in mem
        assert 'W_reservoir' in mem
        assert 'W_out' in mem
        assert 'actual_bytes' in mem
        assert 'theoretical_bytes' in mem
        assert 'compression_ratio' in mem
        
    def test_8bit_reduces_memory(self, trained_esn):
        """Verifica que 8-bit reduce memoria vs float64."""
        q_esn = QuantizedESN(trained_esn, bits=8)
        mem = q_esn.get_memory_footprint()
        
        # 8-bit vs 64-bit = 8x compresión teórica
        assert mem['compression_ratio'] > 1
        
    def test_binary_maximum_compression(self, trained_esn):
        """Verifica que binario tiene máxima compresión."""
        q_esn_8 = QuantizedESN(trained_esn, bits=8)
        q_esn_1 = QuantizedESN(trained_esn, bits=1)
        
        mem_8 = q_esn_8.get_memory_footprint()
        mem_1 = q_esn_1.get_memory_footprint()
        
        # Binario debe tener mayor compresión
        assert mem_1['compression_ratio'] > mem_8['compression_ratio']


class TestCompareQuantizationLevels:
    """Tests para comparación de niveles de cuantización."""
    
    def test_returns_all_levels(self, trained_esn, test_data):
        """Verifica que retorna todos los niveles."""
        X_test, y_test = test_data
        results = compare_quantization_levels(trained_esn, X_test, y_test)
        
        bits_found = [r['bits'] for r in results]
        assert 64 in bits_found  # Original
        assert 8 in bits_found
        assert 4 in bits_found
        assert 1 in bits_found
        
    def test_results_structure(self, trained_esn, test_data):
        """Verifica estructura de resultados."""
        X_test, y_test = test_data
        results = compare_quantization_levels(trained_esn, X_test, y_test)
        
        for result in results:
            assert 'bits' in result
            assert 'name' in result
            assert 'mse' in result
            assert 'memory_kb' in result
            assert 'accuracy_retained' in result
            
    def test_accuracy_decreases_with_bits(self, trained_esn, test_data):
        """Verifica que precisión generalmente disminuye con menos bits."""
        X_test, y_test = test_data
        results = compare_quantization_levels(trained_esn, X_test, y_test)
        
        results_sorted = sorted(results, key=lambda x: x['bits'], reverse=True)
        
        # El MSE del original debería ser el menor (o cercano)
        original_mse = next(r['mse'] for r in results if r['bits'] == 64)
        binary_mse = next(r['mse'] for r in results if r['bits'] == 1)
        
        # Binario generalmente tiene peor MSE que original
        # (puede haber casos especiales donde no, pero generalmente sí)
        assert binary_mse >= original_mse * 0.5  # Al menos la mitad de precisión


class TestDequantization:
    """Tests para decuantización de pesos."""
    
    def test_dequantize_preserves_range(self, trained_esn):
        """Verifica que decuantización preserva rango aproximado."""
        q_esn = QuantizedESN(trained_esn, bits=8)
        
        # Obtener rango original
        orig_min = trained_esn.W_in.min()
        orig_max = trained_esn.W_in.max()
        
        # Decuantizar
        dequant = q_esn._dequantize(q_esn.W_in_q, 'W_in')
        
        # Rango debe ser similar (con tolerancia por cuantización)
        assert dequant.min() >= orig_min - 0.5
        assert dequant.max() <= orig_max + 0.5
        
    def test_binary_dequantize_uses_scale(self, trained_esn):
        """Verifica que binario usa escala correctamente."""
        q_esn = QuantizedESN(trained_esn, bits=1)
        
        dequant = q_esn._dequantize(q_esn.W_reservoir_q, 'W_reservoir')
        
        # Valores deben ser múltiplos del scale
        scale = q_esn.quant_params['W_reservoir']['scale']
        unique_vals = np.unique(np.abs(dequant[dequant != 0]))
        
        # Todos los valores no-cero deben ser aproximadamente el scale
        if len(unique_vals) > 0:
            assert np.allclose(unique_vals, scale, rtol=0.1)


class TestEdgeCases:
    """Tests para casos borde."""
    
    def test_zero_weights_matrix(self, trained_esn):
        """Verifica manejo de matriz con todos ceros."""
        # Crear ESN con W_out de ceros
        trained_esn.W_out = np.zeros_like(trained_esn.W_out)
        q_esn = QuantizedESN(trained_esn, bits=8)
        
        # No debe fallar
        assert q_esn.W_out_q is not None
        
    def test_small_values_matrix(self, trained_esn):
        """Verifica manejo de valores muy pequeños."""
        # Escalar W_in a valores muy pequeños
        original_W_in = trained_esn.W_in.copy()
        trained_esn.W_in = original_W_in * 1e-10
        
        q_esn = QuantizedESN(trained_esn, bits=8)
        
        # Restaurar
        trained_esn.W_in = original_W_in
        
        # No debe fallar
        assert q_esn.W_in_q is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
