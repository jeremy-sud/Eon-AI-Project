"""
Tests para el módulo de utilidades del motor ESN.
"""

import numpy as np
import pytest
import sys
import os

# Path setup
_current_dir = os.path.dirname(os.path.abspath(__file__))
_python_dir = os.path.dirname(_current_dir)
sys.path.insert(0, _python_dir)

from utils.matrix_init import (
    generate_birth_hash,
    create_reservoir_matrix,
    compute_spectral_radius,
    validate_esn_parameters,
    validate_training_data,
    check_numerical_stability,
    ridge_regression
)


class TestGenerateBirthHash:
    """Tests para generate_birth_hash."""
    
    def test_deterministic(self):
        """El mismo seed y timestamp produce el mismo hash."""
        hash1 = generate_birth_hash(12345, 1000000)
        hash2 = generate_birth_hash(12345, 1000000)
        assert hash1 == hash2
    
    def test_different_seeds(self):
        """Diferentes seeds producen diferentes hashes."""
        hash1 = generate_birth_hash(12345, 1000000)
        hash2 = generate_birth_hash(54321, 1000000)
        assert hash1 != hash2
    
    def test_hash_length(self):
        """El hash tiene 32 caracteres (16 bytes en hex)."""
        hash_result = generate_birth_hash(42, 1000)
        assert len(hash_result) == 32
    
    def test_hex_format(self):
        """El hash contiene solo caracteres hexadecimales."""
        hash_result = generate_birth_hash(42, 1000)
        assert all(c in '0123456789abcdef' for c in hash_result)


class TestComputeSpectralRadius:
    """Tests para compute_spectral_radius."""
    
    def test_identity_matrix(self):
        """La matriz identidad tiene radio espectral 1."""
        I = np.eye(10)
        radius = compute_spectral_radius(I, method='exact')
        assert abs(radius - 1.0) < 1e-6
    
    def test_zero_matrix(self):
        """La matriz cero tiene radio espectral 0."""
        Z = np.zeros((10, 10))
        radius = compute_spectral_radius(Z, method='exact')
        assert radius == 0.0
    
    def test_scaled_identity(self):
        """Una matriz escalada tiene radio espectral igual al escalar."""
        scale = 0.5
        M = scale * np.eye(10)
        radius = compute_spectral_radius(M, method='exact')
        assert abs(radius - scale) < 1e-6
    
    def test_power_iteration_vs_exact(self):
        """Power iteration aproxima correctamente el radio espectral."""
        rng = np.random.default_rng(42)
        W = rng.uniform(-1, 1, (20, 20))
        
        exact = compute_spectral_radius(W, method='exact')
        power = compute_spectral_radius(W, method='power', rng=rng)
        
        # Tolerancia del 5%
        assert abs(exact - power) / exact < 0.05


class TestCreateReservoirMatrix:
    """Tests para create_reservoir_matrix."""
    
    def test_correct_shape(self):
        """La matriz tiene el tamaño correcto."""
        rng = np.random.default_rng(42)
        W = create_reservoir_matrix(50, 0.9, 0.8, rng)
        assert W.shape == (50, 50)
    
    def test_sparsity(self):
        """La matriz tiene aproximadamente la escasez especificada."""
        rng = np.random.default_rng(42)
        W = create_reservoir_matrix(100, 0.9, 0.9, rng)
        
        sparsity = np.mean(W == 0)
        # Tolerancia del 5%
        assert 0.85 < sparsity < 0.95
    
    def test_spectral_radius(self):
        """La matriz tiene aproximadamente el radio espectral especificado."""
        rng = np.random.default_rng(42)
        target_radius = 0.95
        W = create_reservoir_matrix(50, target_radius, 0.8, rng)
        
        actual_radius = compute_spectral_radius(W, method='exact')
        # Tolerancia del 1%
        assert abs(actual_radius - target_radius) / target_radius < 0.01
    
    def test_reproducibility(self):
        """Con la misma semilla, produce la misma matriz."""
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        
        W1 = create_reservoir_matrix(30, 0.9, 0.8, rng1)
        W2 = create_reservoir_matrix(30, 0.9, 0.8, rng2)
        
        np.testing.assert_array_equal(W1, W2)


class TestValidateESNParameters:
    """Tests para validate_esn_parameters."""
    
    def test_valid_parameters(self):
        """Parámetros válidos no lanzan excepción."""
        validate_esn_parameters(1, 100, 1, 0.9, 0.9, 0.001)
    
    def test_invalid_n_inputs(self):
        """n_inputs < 1 lanza ValueError."""
        with pytest.raises(ValueError, match="n_inputs"):
            validate_esn_parameters(0, 100, 1, 0.9, 0.9, 0.001)
    
    def test_invalid_n_reservoir(self):
        """n_reservoir < 1 lanza ValueError."""
        with pytest.raises(ValueError, match="n_reservoir"):
            validate_esn_parameters(1, 0, 1, 0.9, 0.9, 0.001)
    
    def test_invalid_spectral_radius_too_low(self):
        """spectral_radius <= 0 lanza ValueError."""
        with pytest.raises(ValueError, match="spectral_radius"):
            validate_esn_parameters(1, 100, 1, 0.0, 0.9, 0.001)
    
    def test_invalid_spectral_radius_too_high(self):
        """spectral_radius > 2.0 lanza ValueError."""
        with pytest.raises(ValueError, match="spectral_radius"):
            validate_esn_parameters(1, 100, 1, 2.5, 0.9, 0.001)
    
    def test_invalid_sparsity(self):
        """sparsity >= 1 lanza ValueError."""
        with pytest.raises(ValueError, match="sparsity"):
            validate_esn_parameters(1, 100, 1, 0.9, 1.0, 0.001)
    
    def test_invalid_noise(self):
        """noise < 0 lanza ValueError."""
        with pytest.raises(ValueError, match="noise"):
            validate_esn_parameters(1, 100, 1, 0.9, 0.9, -0.001)


class TestValidateTrainingData:
    """Tests para validate_training_data."""
    
    def test_valid_data(self):
        """Datos válidos retornan arrays normalizados."""
        inputs = np.random.randn(100)
        outputs = np.random.randn(100)
        
        inputs_norm, outputs_norm = validate_training_data(
            inputs, outputs, 1, 1, 10
        )
        
        assert inputs_norm.shape == (100, 1)
        assert outputs_norm.shape == (100, 1)
    
    def test_dimension_mismatch_inputs(self):
        """Dimensión de entrada incorrecta lanza ValueError."""
        inputs = np.random.randn(100, 3)  # 3 dimensiones
        outputs = np.random.randn(100, 1)
        
        with pytest.raises(ValueError, match="Dimensión de entrada"):
            validate_training_data(inputs, outputs, 1, 1, 10)
    
    def test_dimension_mismatch_outputs(self):
        """Dimensión de salida incorrecta lanza ValueError."""
        inputs = np.random.randn(100, 1)
        outputs = np.random.randn(100, 3)  # 3 dimensiones
        
        with pytest.raises(ValueError, match="Dimensión de salida"):
            validate_training_data(inputs, outputs, 1, 1, 10)
    
    def test_sample_count_mismatch(self):
        """Diferente número de muestras lanza ValueError."""
        inputs = np.random.randn(100, 1)
        outputs = np.random.randn(50, 1)  # Diferente número
        
        with pytest.raises(ValueError, match="mismo número de muestras"):
            validate_training_data(inputs, outputs, 1, 1, 10)
    
    def test_washout_too_large(self):
        """Washout >= número de muestras lanza ValueError."""
        inputs = np.random.randn(100, 1)
        outputs = np.random.randn(100, 1)
        
        with pytest.raises(ValueError, match="washout"):
            validate_training_data(inputs, outputs, 1, 1, 100)


class TestCheckNumericalStability:
    """Tests para check_numerical_stability."""
    
    def test_stable_state(self):
        """Estado estable no lanza excepción."""
        state = np.random.randn(100) * 0.5
        check_numerical_stability(state)  # No debería lanzar
    
    def test_nan_raises_error(self):
        """Estado con NaN lanza RuntimeError."""
        state = np.array([1.0, np.nan, 2.0])
        
        with pytest.raises(RuntimeError, match="NaN"):
            check_numerical_stability(state)
    
    def test_inf_raises_error(self):
        """Estado con Inf lanza RuntimeError."""
        state = np.array([1.0, np.inf, 2.0])
        
        with pytest.raises(RuntimeError, match="Inf"):
            check_numerical_stability(state)
    
    def test_saturation_warning(self):
        """Estado saturado genera warning."""
        # Estado con >90% de valores en [-1, 1] bordes
        state = np.ones(100) * 0.999
        
        with pytest.warns(RuntimeWarning, match="saturado"):
            check_numerical_stability(state)


class TestRidgeRegression:
    """Tests para ridge_regression."""
    
    def test_simple_regression(self):
        """Ridge regression con datos simples."""
        # Datos lineales: y = 2*x
        X = np.arange(100).reshape(-1, 1).astype(float)
        Y = (2 * np.arange(100)).reshape(-1, 1).astype(float)
        
        W = ridge_regression(X, Y, regularization=1e-6)
        
        # El peso debería ser ~2
        assert abs(W[0, 0] - 2.0) < 0.01
    
    def test_multiple_outputs(self):
        """Ridge regression con múltiples salidas."""
        X = np.random.randn(100, 10)
        Y = np.random.randn(100, 5)
        
        W = ridge_regression(X, Y)
        
        assert W.shape == (10, 5)
    
    def test_regularization_effect(self):
        """Mayor regularización produce pesos más pequeños."""
        X = np.random.randn(50, 10)
        Y = np.random.randn(50, 1)
        
        W_low_reg = ridge_regression(X, Y, regularization=1e-6)
        W_high_reg = ridge_regression(X, Y, regularization=1.0)
        
        # Pesos con más regularización deberían ser menores en magnitud
        assert np.linalg.norm(W_high_reg) < np.linalg.norm(W_low_reg)


class TestESNImprovements:
    """Tests para las mejoras del ESN."""
    
    def test_leak_rate_parameter(self):
        """El parámetro leak_rate existe y funciona."""
        from esn.esn import EchoStateNetwork
        
        # ESN con leak_rate
        esn = EchoStateNetwork(n_reservoir=50, leak_rate=0.5, random_state=42)
        assert esn.leak_rate == 0.5
        
        # ESN sin leak_rate (default 1.0)
        esn_default = EchoStateNetwork(n_reservoir=50, random_state=42)
        assert esn_default.leak_rate == 1.0
    
    def test_leak_rate_effect(self):
        """Leak rate afecta la dinámica del estado."""
        from esn.esn import EchoStateNetwork
        
        # Misma configuración, diferente leak_rate
        esn_no_leak = EchoStateNetwork(n_reservoir=50, leak_rate=1.0, random_state=42)
        esn_leaky = EchoStateNetwork(n_reservoir=50, leak_rate=0.3, random_state=42)
        
        # Input constante
        inputs = np.ones((100, 1))
        
        # Recolectar estados
        states_no_leak = []
        states_leaky = []
        
        for i in range(100):
            esn_no_leak._update_state(inputs[i])
            esn_leaky._update_state(inputs[i])
            states_no_leak.append(esn_no_leak.state.copy())
            states_leaky.append(esn_leaky.state.copy())
        
        # El ESN con leak debería converger más lentamente
        # (mayor diferencia entre primeros y últimos estados)
        convergence_no_leak = np.linalg.norm(states_no_leak[-1] - states_no_leak[10])
        convergence_leaky = np.linalg.norm(states_leaky[-1] - states_leaky[10])
        
        # Este test verifica que el leak_rate tiene algún efecto
        assert convergence_no_leak != convergence_leaky
    
    def test_parameter_validation(self):
        """El ESN valida parámetros incorrectos."""
        from esn.esn import EchoStateNetwork
        
        with pytest.raises(ValueError):
            EchoStateNetwork(n_inputs=0)  # Invalid
        
        with pytest.raises(ValueError):
            EchoStateNetwork(n_reservoir=-5)  # Invalid
        
        with pytest.raises(ValueError):
            EchoStateNetwork(spectral_radius=3.0)  # Invalid (> 2.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
