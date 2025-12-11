"""
Tests for Discovery Paradigm Modules (v1.9.0)
==============================================
Tests for UniversalMiner and ArchaicProtocol.

"La inteligencia no se crea, se descubre."

Run with: pytest phase1-foundations/python/tests/test_discovery_paradigm.py -v
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add paths for imports
_current_dir = Path(__file__).parent
_python_dir = _current_dir.parent
sys.path.insert(0, str(_python_dir))


class TestUniversalMiner:
    """Test cases for UniversalMiner - Seed Mining excavation system."""
    
    @pytest.fixture
    def miner(self):
        """Create a UniversalMiner instance for testing."""
        from core.universal_miner import UniversalMiner, ResonanceType
        return UniversalMiner(
            reservoir_size=32,  # Smaller for faster tests
            target_resonance=(0.90, 1.10),  # Wider range for test reliability
            resonance_type=ResonanceType.EDGE_OF_CHAOS,
            sparsity=0.2
        )
    
    def test_initialization(self, miner):
        """Test UniversalMiner initializes correctly."""
        from core.universal_miner import ResonanceType
        assert miner.reservoir_size == 32
        assert miner.target_resonance == (0.90, 1.10)
        assert miner.resonance_type == ResonanceType.EDGE_OF_CHAOS
        assert miner.sparsity == 0.2
    
    def test_chaos_sample_returns_matrix(self, miner):
        """Test chaos_sample returns correctly shaped matrix."""
        matrix = miner.chaos_sample(seed=42)
        
        assert isinstance(matrix, np.ndarray)
        assert matrix.shape == (32, 32)
    
    def test_chaos_sample_reproducibility(self, miner):
        """Test chaos_sample is reproducible with same seed."""
        matrix1 = miner.chaos_sample(seed=12345)
        matrix2 = miner.chaos_sample(seed=12345)
        
        np.testing.assert_array_equal(matrix1, matrix2)
    
    def test_chaos_sample_different_seeds(self, miner):
        """Test chaos_sample produces different matrices for different seeds."""
        matrix1 = miner.chaos_sample(seed=1)
        matrix2 = miner.chaos_sample(seed=2)
        
        assert not np.array_equal(matrix1, matrix2)
    
    def test_chaos_sample_sparsity(self, miner):
        """Test chaos_sample respects sparsity parameter."""
        matrix = miner.chaos_sample(seed=42)
        
        # Count non-zero elements
        non_zero_ratio = np.count_nonzero(matrix) / matrix.size
        
        # Should be approximately equal to sparsity (0.2) with some tolerance
        assert 0.1 <= non_zero_ratio <= 0.35
    
    def test_measure_resonance(self, miner):
        """Test measure_resonance returns valid values."""
        matrix = miner.chaos_sample(seed=42)
        resonance, eigenspectrum = miner.measure_resonance(matrix)
        
        assert isinstance(resonance, float)
        assert resonance >= 0
        assert isinstance(eigenspectrum, np.ndarray)
        assert len(eigenspectrum) == 32  # reservoir_size
    
    def test_excavation_result_structure(self):
        """Test ExcavationResult dataclass structure."""
        from core.universal_miner import ExcavationResult, ResonanceType
        
        result = ExcavationResult(
            sacred_seed=42,
            divine_matrix=np.eye(3),
            resonance=0.95,
            resonance_type=ResonanceType.EDGE_OF_CHAOS,
            excavation_depth=1000,
            excavation_time=1.5,
            eigenspectrum=np.array([1, 0.5, 0.2])
        )
        
        assert result.sacred_seed == 42
        assert result.resonance == 0.95
        assert "sacred_seed=42" in repr(result)
    
    def test_quick_excavate_function(self):
        """Test quick_excavate convenience function."""
        from core.universal_miner import quick_excavate
        
        # Quick excavate with small params for speed
        # Note: quick_excavate returns (seed, matrix) tuple
        result = quick_excavate(
            size=16,
            target=1.0,
            tolerance=0.5  # Wide tolerance for test reliability
        )
        
        # Should return tuple (seed, matrix)
        assert isinstance(result, tuple)
        assert len(result) == 2
        seed, matrix = result
        assert isinstance(seed, int)
        assert matrix.shape == (16, 16)
    
    def test_known_sacred_seeds(self):
        """Test that KNOWN_SACRED_SEEDS constant exists and has correct format."""
        from core.universal_miner import KNOWN_SACRED_SEEDS
        
        assert isinstance(KNOWN_SACRED_SEEDS, dict)
        # Should have at least one entry
        assert len(KNOWN_SACRED_SEEDS) > 0
    
    def test_resonance_types(self):
        """Test all ResonanceType enum values exist."""
        from core.universal_miner import ResonanceType
        
        expected = ['EDGE_OF_CHAOS', 'HARMONIC', 'GOLDEN', 'FIBONACCI', 'PRIME']
        for name in expected:
            assert hasattr(ResonanceType, name)
    
    def test_seed_vault_structure(self):
        """Test SeedVault dataclass structure."""
        from core.universal_miner import SeedVault, ExcavationResult, ResonanceType
        
        vault = SeedVault()
        
        # Store a result
        result = ExcavationResult(
            sacred_seed=42,
            divine_matrix=np.eye(3),
            resonance=0.95,
            resonance_type=ResonanceType.EDGE_OF_CHAOS,
            excavation_depth=1000,
            excavation_time=1.5,
            eigenspectrum=np.array([1, 0.5, 0.2])
        )
        
        vault.store("test_seed", result)
        
        assert "test_seed" in vault.list_seeds()
        retrieved = vault.retrieve("test_seed")
        assert retrieved.sacred_seed == 42


class TestArchaicProtocol:
    """Test cases for ArchaicProtocol - I Ching communication system."""
    
    @pytest.fixture
    def protocol(self):
        """Create an ArchaicProtocol instance."""
        from core.archaic_protocol import ArchaicProtocol
        return ArchaicProtocol(interpretation_mode="classical")
    
    def test_initialization(self, protocol):
        """Test ArchaicProtocol initializes correctly."""
        assert protocol.mode == "classical"
        assert len(protocol._hexagrams) == 64
    
    def test_all_64_hexagrams_exist(self, protocol):
        """Test all 64 hexagrams are defined."""
        from core.archaic_protocol import HEXAGRAMS
        
        for i in range(1, 65):
            assert i in HEXAGRAMS, f"Hexagram {i} missing"
    
    def test_trigram_enum(self):
        """Test Trigram enum has all 8 values."""
        from core.archaic_protocol import Trigram
        
        assert len(Trigram) == 8
        
        # Check specific trigramas
        expected = ['QIAN', 'DUI', 'LI', 'ZHEN', 'XUN', 'KAN', 'GEN', 'KUN']
        for name in expected:
            assert hasattr(Trigram, name)
    
    def test_trigram_properties(self):
        """Test Trigram properties work correctly."""
        from core.archaic_protocol import Trigram
        
        qian = Trigram.QIAN
        assert qian.symbol == '☰'
        assert qian.meaning == 'Cielo/Creativo'
        assert qian.value == (1, 1, 1)
    
    def test_hexagram_structure(self, protocol):
        """Test Hexagram dataclass structure."""
        from core.archaic_protocol import HEXAGRAMS
        
        hex1 = HEXAGRAMS[1]  # Lo Creativo
        
        assert hex1.number == 1
        assert hex1.name_spanish == "Lo Creativo"
        assert hex1.name_english == "The Creative"
        assert hasattr(hex1, 'upper')
        assert hasattr(hex1, 'lower')
        assert hasattr(hex1, 'judgment')
        assert hasattr(hex1, 'image')
    
    def test_hexagram_properties(self):
        """Test Hexagram computed properties."""
        from core.archaic_protocol import HEXAGRAMS
        
        hex1 = HEXAGRAMS[1]
        
        # Lines should be 6 bits
        assert len(hex1.lines) == 6
        
        # Binary should be 0-63
        assert 0 <= hex1.binary <= 63
        
        # Symbol should be 6 characters
        assert len(hex1.symbol) == 6
    
    def test_tensor_to_hexagram(self, protocol):
        """Test tensor_to_hexagram conversion."""
        # Extreme values
        hex_min = protocol.tensor_to_hexagram(-1.0)
        hex_max = protocol.tensor_to_hexagram(1.0)
        hex_mid = protocol.tensor_to_hexagram(0.0)
        
        assert hex_min.number == 1
        assert hex_max.number == 64
        # Middle should be around 32
        assert 28 <= hex_mid.number <= 36
    
    def test_tensor_to_hexagram_clamping(self, protocol):
        """Test tensor_to_hexagram clamps out of range values."""
        hex_below = protocol.tensor_to_hexagram(-5.0)
        hex_above = protocol.tensor_to_hexagram(5.0)
        
        assert hex_below.number == 1
        assert hex_above.number == 64
    
    def test_hexagram_to_tensor(self, protocol):
        """Test hexagram_to_tensor conversion."""
        from core.archaic_protocol import HEXAGRAMS
        
        hex1 = HEXAGRAMS[1]
        hex64 = HEXAGRAMS[64]
        
        val1 = protocol.hexagram_to_tensor(hex1)
        val64 = protocol.hexagram_to_tensor(hex64)
        
        assert val1 == pytest.approx(-1.0)
        assert val64 == pytest.approx(1.0)
    
    def test_roundtrip_conversion(self, protocol):
        """Test tensor → hexagram → tensor roundtrip."""
        original = 0.5
        hexagram = protocol.tensor_to_hexagram(original)
        recovered = protocol.hexagram_to_tensor(hexagram)
        
        # Should be close (some quantization loss expected)
        assert abs(recovered - original) < 0.05
    
    def test_vector_to_trigram_pair(self, protocol):
        """Test vector_to_trigram_pair conversion."""
        from core.archaic_protocol import Trigram
        
        vector = np.array([0.5, 0.5, -0.5, -0.5])
        lower, upper = protocol.vector_to_trigram_pair(vector)
        
        assert isinstance(lower, Trigram)
        assert isinstance(upper, Trigram)
    
    def test_interpret(self, protocol):
        """Test interpret returns proper structure."""
        from core.archaic_protocol import HEXAGRAMS
        
        hex11 = HEXAGRAMS[11]  # La Paz
        interpretation = protocol.interpret(hex11, context="test")
        
        assert interpretation["number"] == 11
        assert interpretation["name"] == "La Paz"
        assert "judgment" in interpretation
        assert "image" in interpretation
        assert interpretation["context"] == "test"
        assert "upper_trigram" in interpretation
        assert "lower_trigram" in interpretation
    
    def test_hexagram_stream(self):
        """Test HexagramStream class exists and works."""
        from core.archaic_protocol import HexagramStream
        
        # Just verify it can be instantiated
        stream = HexagramStream()
        assert stream is not None


class TestCoreExports:
    """Test that core/__init__.py exports all necessary symbols."""
    
    def test_universal_miner_exports(self):
        """Test UniversalMiner exports from core."""
        from core import (
            UniversalMiner,
            ExcavationResult,
            ResonanceType,
            SeedVault,
            quick_excavate,
            KNOWN_SACRED_SEEDS
        )
        
        assert UniversalMiner is not None
        assert ExcavationResult is not None
        assert ResonanceType is not None
    
    def test_archaic_protocol_exports(self):
        """Test ArchaicProtocol exports from core."""
        from core import (
            ArchaicProtocol,
            Hexagram,
            Trigram,
            HexagramStream,
            HEXAGRAMS
        )
        
        assert ArchaicProtocol is not None
        assert Hexagram is not None
        assert Trigram is not None
        assert len(HEXAGRAMS) == 64
    
    def test_aeon_birth_export(self):
        """Test AeonBirth still exported from core."""
        from core import AeonBirth
        
        assert AeonBirth is not None
    
    def test_alchemical_pipeline_exports(self):
        """Test AlchemicalPipeline exports from core."""
        from core import (
            AlchemicalPipeline,
            AlchemicalConfig,
            AlchemicalPhase,
            TransmutationState,
            KalmanFilter
        )
        
        assert AlchemicalPipeline is not None
        assert AlchemicalConfig is not None
        assert AlchemicalPhase is not None
        assert TransmutationState is not None
        assert KalmanFilter is not None


class TestIntegration:
    """Integration tests between UniversalMiner and ArchaicProtocol."""
    
    def test_miner_matrix_to_protocol_message(self):
        """Test converting mined matrix to archaic message."""
        from core.universal_miner import UniversalMiner
        from core.archaic_protocol import ArchaicProtocol
        
        miner = UniversalMiner(reservoir_size=16)
        protocol = ArchaicProtocol()
        
        # Mine a matrix
        matrix = miner.chaos_sample(seed=42)
        resonance, spectrum = miner.measure_resonance(matrix)
        
        # Convert resonance to hexagram
        # Normalize resonance to [-1, 1] range (assuming typical range 0-2)
        normalized = (resonance - 1.0)  # Centers around 1.0
        hexagram = protocol.tensor_to_hexagram(normalized)
        
        assert hexagram is not None
        assert 1 <= hexagram.number <= 64
    
    def test_protocol_interpretation_of_mined_state(self):
        """Test interpreting mined state via protocol."""
        from core.universal_miner import UniversalMiner
        from core.archaic_protocol import ArchaicProtocol
        
        miner = UniversalMiner(reservoir_size=16)
        protocol = ArchaicProtocol()
        
        matrix = miner.chaos_sample(seed=1337)
        
        # Use matrix mean as state indicator
        state_value = np.mean(matrix)
        hexagram = protocol.tensor_to_hexagram(state_value)
        
        interpretation = protocol.interpret(hexagram, context="mining_result")
        
        assert "judgment" in interpretation
        assert interpretation["context"] == "mining_result"
