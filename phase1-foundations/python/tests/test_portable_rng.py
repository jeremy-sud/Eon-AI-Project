"""
Tests para el módulo portable_rng (Xorshift32).

Verifica:
- Compatibilidad cross-platform con C/JS/Arduino
- Funciones de generación de números
- Distribuciones estadísticas
- Reproducibilidad con semillas
"""

import pytest
import numpy as np
import sys
import os

# Path setup
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.portable_rng import (
    Xorshift32,
    create_portable_rng,
    generate_birth_hash_portable,
    verify_cross_platform_compatibility
)


class TestXorshift32Basics:
    """Tests básicos del generador Xorshift32."""
    
    def test_initialization_with_seed(self):
        """Verifica inicialización con semilla."""
        rng = Xorshift32(42)
        assert rng.state == 42
    
    def test_initialization_zero_seed(self):
        """Verifica que semilla 0 se ajusta a 1."""
        rng = Xorshift32(0)
        assert rng.state == 1  # No puede ser 0
    
    def test_initialization_default_seed(self):
        """Verifica semilla por defecto."""
        rng = Xorshift32()
        assert rng.state == 1
    
    def test_next_u32_produces_integers(self):
        """Verifica que next_u32 produce enteros válidos."""
        rng = Xorshift32(42)
        for _ in range(100):
            val = rng.next_u32()
            assert isinstance(val, int)
            assert 0 < val <= 0xFFFFFFFF
    
    def test_random_produces_floats_in_range(self):
        """Verifica que random produce floats en [0, 1)."""
        rng = Xorshift32(42)
        for _ in range(100):
            val = rng.random()
            assert isinstance(val, float)
            assert 0.0 <= val < 1.0


class TestXorshift32CrossPlatform:
    """Tests de compatibilidad cross-platform."""
    
    def test_seed_42_matches_reference(self):
        """Verifica valores de referencia con seed=42."""
        rng = Xorshift32(42)
        expected = [11355432, 2836018348, 476557059, 3648046016, 3759983556]
        
        for exp in expected:
            assert rng.next_u32() == exp
    
    def test_seed_1_matches_reference(self):
        """Verifica valores de referencia con seed=1."""
        rng = Xorshift32(1)
        expected = [270369, 67634689, 2647435461, 307599695, 2398689233]
        
        for exp in expected:
            assert rng.next_u32() == exp
    
    def test_seed_12345_matches_reference(self):
        """Verifica valores de referencia con seed=12345."""
        rng = Xorshift32(12345)
        expected = [3336926330, 1697253807, 2816511904, 1955480042, 718842323]
        
        for exp in expected:
            assert rng.next_u32() == exp
    
    def test_verify_function_passes(self):
        """Verifica que la función de verificación pasa."""
        assert verify_cross_platform_compatibility() == True


class TestXorshift32Reproducibility:
    """Tests de reproducibilidad."""
    
    def test_same_seed_same_sequence(self):
        """Verifica que misma semilla produce misma secuencia."""
        rng1 = Xorshift32(42)
        rng2 = Xorshift32(42)
        
        for _ in range(100):
            assert rng1.next_u32() == rng2.next_u32()
    
    def test_different_seeds_different_sequences(self):
        """Verifica que semillas diferentes producen secuencias diferentes."""
        rng1 = Xorshift32(42)
        rng2 = Xorshift32(43)
        
        # Los primeros valores deben ser diferentes
        assert rng1.next_u32() != rng2.next_u32()
    
    def test_state_save_restore(self):
        """Verifica guardar y restaurar estado."""
        rng = Xorshift32(42)
        
        # Avanzar un poco
        for _ in range(50):
            rng.next_u32()
        
        # Guardar estado
        saved_state = rng.get_state()
        
        # Generar más valores
        next_values = [rng.next_u32() for _ in range(10)]
        
        # Restaurar y verificar
        rng.set_state(saved_state)
        restored_values = [rng.next_u32() for _ in range(10)]
        
        assert next_values == restored_values


class TestXorshift32Distributions:
    """Tests de distribuciones estadísticas."""
    
    def test_uniform_distribution(self):
        """Verifica distribución uniforme."""
        rng = Xorshift32(42)
        n = 10000
        values = [rng.random() for _ in range(n)]
        
        mean = np.mean(values)
        std = np.std(values)
        
        # Media debería ser ~0.5, std ~0.289 para uniforme [0,1)
        assert abs(mean - 0.5) < 0.02
        assert abs(std - 0.289) < 0.02
    
    def test_normal_distribution(self):
        """Verifica distribución normal."""
        rng = Xorshift32(42)
        n = 10000
        values = [rng.standard_normal() for _ in range(n)]
        
        mean = np.mean(values)
        std = np.std(values)
        
        # Media ~0, std ~1 para N(0,1)
        assert abs(mean) < 0.05
        assert abs(std - 1.0) < 0.1
    
    def test_randn_shape(self):
        """Verifica que randn produce shape correcto."""
        rng = Xorshift32(42)
        
        arr1 = rng.randn(10)
        assert arr1.shape == (10,)
        
        arr2 = rng.randn(3, 4)
        assert arr2.shape == (3, 4)
        
        arr3 = rng.randn(2, 3, 4)
        assert arr3.shape == (2, 3, 4)
    
    def test_rand_shape(self):
        """Verifica que rand produce shape correcto."""
        rng = Xorshift32(42)
        
        arr = rng.rand(5, 6)
        assert arr.shape == (5, 6)
        assert np.all(arr >= 0) and np.all(arr < 1)


class TestXorshift32Utilities:
    """Tests de funciones utilitarias."""
    
    def test_uniform_range(self):
        """Verifica uniform con rango personalizado."""
        rng = Xorshift32(42)
        n = 1000
        
        values = [rng.uniform(-10, 10) for _ in range(n)]
        assert all(-10 <= v < 10 for v in values)
        assert np.mean(values) - 0 < 1.0  # Media cerca de 0
    
    def test_randint_range(self):
        """Verifica randint produce enteros en rango."""
        rng = Xorshift32(42)
        n = 1000
        
        values = [rng.randint(0, 10) for _ in range(n)]
        assert all(0 <= v < 10 for v in values)
        assert all(isinstance(v, int) for v in values)
    
    def test_choice_from_array(self):
        """Verifica choice selecciona de array."""
        rng = Xorshift32(42)
        arr = np.array([10, 20, 30, 40, 50])
        
        selections = [rng.choice(arr) for _ in range(100)]
        assert all(s in arr for s in selections)
    
    def test_shuffle_permutes_array(self):
        """Verifica que shuffle permuta array."""
        rng = Xorshift32(42)
        arr = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        original = arr.copy()
        
        rng.shuffle(arr)
        
        # Debe contener los mismos elementos
        assert set(arr) == set(original)
        # Muy probablemente no estará en el mismo orden
        assert not np.array_equal(arr, original)


class TestFactoryFunctions:
    """Tests de funciones factory."""
    
    def test_create_portable_rng(self):
        """Verifica factory function."""
        rng = create_portable_rng(42)
        assert isinstance(rng, Xorshift32)
        assert rng.state == 42
    
    def test_generate_birth_hash_portable(self):
        """Verifica generación de birth hash."""
        hash1 = generate_birth_hash_portable(42, 100)
        hash2 = generate_birth_hash_portable(42, 100)
        hash3 = generate_birth_hash_portable(43, 100)
        
        # Mismo seed = mismo hash
        assert hash1 == hash2
        # Diferente seed = diferente hash
        assert hash1 != hash3
        # Formato correcto (16 caracteres hex)
        assert len(hash1) == 16
        assert all(c in '0123456789abcdef' for c in hash1)
    
    def test_birth_hash_varies_with_reservoir_size(self):
        """Verifica que hash varía con tamaño de reservorio."""
        hash1 = generate_birth_hash_portable(42, 100)
        hash2 = generate_birth_hash_portable(42, 200)
        
        assert hash1 != hash2


class TestXorshift32EdgeCases:
    """Tests de casos extremos."""
    
    def test_large_seed(self):
        """Verifica comportamiento con semilla grande."""
        rng = Xorshift32(0xFFFFFFFF)
        val = rng.next_u32()
        assert 0 < val <= 0xFFFFFFFF
    
    def test_many_iterations(self):
        """Verifica estabilidad después de muchas iteraciones."""
        rng = Xorshift32(42)
        
        # Generar un millón de valores
        for _ in range(1000000):
            val = rng.next_u32()
        
        # Debe seguir produciendo valores válidos
        assert 0 < val <= 0xFFFFFFFF
    
    def test_period_not_zero_quickly(self):
        """Verifica que no hay ciclos cortos."""
        rng = Xorshift32(42)
        
        # Guardar primeros valores
        first_values = [rng.next_u32() for _ in range(10)]
        
        # Generar muchos más
        for _ in range(10000):
            rng.next_u32()
        
        # Los siguientes no deberían coincidir con los primeros
        next_values = [rng.next_u32() for _ in range(10)]
        assert first_values != next_values


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
