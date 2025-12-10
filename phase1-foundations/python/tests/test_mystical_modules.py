"""
Tests for Mystical Modules
==========================
Tests for Tzimtzum, Alchemy, Recursive ESN, HebbianTzimtzum, and Egrégor.

Run with: pytest phase1-foundations/python/tests/test_mystical_modules.py -v
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add paths for imports
_current_dir = Path(__file__).parent
_python_dir = _current_dir.parent
sys.path.insert(0, str(_python_dir))
sys.path.insert(0, str(_python_dir.parent.parent.parent / "phase6-collective"))


class TestTzimtzumESN:
    """Test cases for TzimtzumESN - Divine Contraction pruning."""
    
    @pytest.fixture
    def tzimtzum_esn(self):
        """Create a TzimtzumESN instance for testing."""
        from plasticity.tzimtzum import TzimtzumESN, TzimtzumConfig
        config = TzimtzumConfig(
            pruning_fraction=0.5,
            min_connections_fraction=0.1
        )
        return TzimtzumESN(
            n_inputs=3,
            n_reservoir=50,
            config=config,
            random_state=42
        )
    
    def test_initialization(self, tzimtzum_esn):
        """Test TzimtzumESN initializes correctly."""
        assert tzimtzum_esn.n_reservoir == 50
        assert tzimtzum_esn.n_inputs == 3
        assert hasattr(tzimtzum_esn, 'tzimtzum_state')
        assert tzimtzum_esn.tzimtzum_state.phase.name == 'PLENITUD'
    
    def test_dark_night_pruning(self, tzimtzum_esn):
        """Test that dark_night() changes phase and prepares for pruning."""
        from plasticity.tzimtzum import ContractionPhase
        
        # Initial state should be PLENITUD
        assert tzimtzum_esn.tzimtzum_state.phase == ContractionPhase.PLENITUD
        
        result = tzimtzum_esn.dark_night()
        
        assert 'pruned_count' in result
        # After dark_night, phase should transition
        assert tzimtzum_esn.tzimtzum_state.phase in [
            ContractionPhase.DARK_NIGHT, 
            ContractionPhase.CHALLAL
        ]
    
    def test_renacimiento_regrowth(self, tzimtzum_esn):
        """Test that renacimiento() regrows connections after pruning."""
        # First prune
        tzimtzum_esn.dark_night()
        connections_after_prune = np.sum(tzimtzum_esn.W_reservoir != 0)
        
        # Then regrow
        result = tzimtzum_esn.renacimiento()
        connections_after_regrow = np.sum(tzimtzum_esn.W_reservoir != 0)
        
        assert 'regrown_count' in result
        assert connections_after_regrow >= connections_after_prune
    
    def test_full_cycle(self, tzimtzum_esn):
        """Test a complete Tzimtzum cycle returns expected structure."""
        result = tzimtzum_esn.full_tzimtzum_cycle()
        
        assert 'dark_night' in result
        assert 'renacimiento' in result
        assert 'final_connections' in result
    
    def test_phase_transitions(self, tzimtzum_esn):
        """Test that phases transition during cycle."""
        from plasticity.tzimtzum import ContractionPhase
        
        # Initial state
        assert tzimtzum_esn.tzimtzum_state.phase == ContractionPhase.PLENITUD
        
        # After dark_night, phase should change from PLENITUD
        tzimtzum_esn.dark_night()
        phase_after_dark = tzimtzum_esn.tzimtzum_state.phase
        assert phase_after_dark != ContractionPhase.PLENITUD
        
        # After renacimiento, phase should return to PLENITUD
        tzimtzum_esn.renacimiento()
        assert tzimtzum_esn.tzimtzum_state.phase == ContractionPhase.PLENITUD


class TestAlchemicalPipeline:
    """Test cases for AlchemicalPipeline - ETL Transmutation."""
    
    @pytest.fixture
    def pipeline(self):
        """Create an AlchemicalPipeline instance."""
        from core.alchemy import AlchemicalPipeline, AlchemicalConfig
        config = AlchemicalConfig(
            kalman_process_noise=0.01,
            kalman_measurement_noise=0.1,
            remove_outliers=True,
            outlier_threshold=2.5
        )
        return AlchemicalPipeline(config=config)
    
    @pytest.fixture
    def noisy_data(self):
        """Generate noisy test data."""
        rng = np.random.default_rng(42)
        t = np.linspace(0, 4 * np.pi, 200)
        clean = np.sin(t)
        noise = rng.normal(0, 0.2, len(t))
        return clean + noise
    
    def test_pipeline_initialization(self, pipeline):
        """Test AlchemicalPipeline initializes correctly."""
        from core.alchemy import AlchemicalPhase
        assert pipeline.state.current_phase == AlchemicalPhase.MATERIA_PRIMA
        assert pipeline.state.nigredo_samples == 0
    
    def test_nigredo_phase(self, pipeline, noisy_data):
        """Test Nigredo (black) phase - data ingestion."""
        result = pipeline.nigredo(noisy_data)
        
        assert result is not None
        assert pipeline.state.nigredo_samples == len(noisy_data)
        assert pipeline.state.nigredo_duration > 0
    
    def test_albedo_phase(self, pipeline, noisy_data):
        """Test Albedo (white) phase - purification."""
        pipeline.nigredo(noisy_data)
        purified = pipeline.albedo()
        
        assert purified is not None
        assert len(purified) == len(noisy_data)
        assert pipeline.state.noise_removed_percent > 0
        # Purified data should have lower variance than raw
        assert np.var(purified) < np.var(noisy_data)
    
    def test_rubedo_phase(self, pipeline, noisy_data):
        """Test Rubedo (red) phase - illumination/output."""
        pipeline.nigredo(noisy_data)
        pipeline.albedo()
        result = pipeline.rubedo()
        
        assert 'gold' in result
        assert 'confidence' in result
        assert 0 <= result['confidence'] <= 1
    
    def test_full_transmutation(self, pipeline, noisy_data):
        """Test complete transmutation process."""
        result = pipeline.transmute(noisy_data)
        
        assert result is not None
        assert 'phases' in result
        assert 'nigredo' in result['phases']
        assert 'albedo' in result['phases']
        assert 'rubedo' in result['phases']
    
    def test_kalman_filter(self, pipeline, noisy_data):
        """Test that Kalman filter reduces noise effectively."""
        from core.alchemy import KalmanFilter
        
        kf = KalmanFilter(process_noise=0.01, measurement_noise=0.1)
        filtered = kf.filter_sequence(noisy_data)
        
        # Filtered should be smoother (lower variance of differences)
        raw_diff_var = np.var(np.diff(noisy_data))
        filtered_diff_var = np.var(np.diff(filtered))
        
        assert filtered_diff_var < raw_diff_var


class TestRecursiveESN:
    """Test cases for RecursiveEchoStateNetwork - Fractal Architecture."""
    
    @pytest.fixture
    def recursive_esn(self):
        """Create a RecursiveEchoStateNetwork instance."""
        from esn.recursive_esn import RecursiveEchoStateNetwork
        return RecursiveEchoStateNetwork(
            n_inputs=2,
            n_macro_units=5,
            n_micro_neurons=8,
            random_state=42
        )
    
    def test_fractal_initialization(self, recursive_esn):
        """Test RecursiveESN creates fractal hierarchy."""
        assert recursive_esn.n_macro_units == 5
        assert len(recursive_esn.micro_reservoirs) == 5
    
    def test_micro_reservoir_count(self, recursive_esn):
        """Test that correct number of micro reservoirs are created."""
        assert len(recursive_esn.micro_reservoirs) == recursive_esn.n_macro_units
    
    def test_forward_propagation(self, recursive_esn):
        """Test forward pass through fractal architecture."""
        input_vec = np.array([0.5, -0.3])
        state = recursive_esn._update_state(input_vec)
        
        assert state is not None
        assert len(state) > 0
    
    def test_multiple_updates(self, recursive_esn):
        """Test that multiple updates accumulate state."""
        states = []
        for i in range(10):
            input_vec = np.array([np.sin(i * 0.1), np.cos(i * 0.1)])
            state = recursive_esn._update_state(input_vec)
            states.append(state.copy())
        
        # States should evolve over time
        assert not np.allclose(states[0], states[-1])


class TestHebbianTzimtzum:
    """Test cases for HebbianTzimtzumESN - Combined plasticity and pruning."""
    
    @pytest.fixture
    def hebbian_tzimtzum(self):
        """Create a HebbianTzimtzumESN instance."""
        from plasticity.hebbian_tzimtzum import HebbianTzimtzumESN
        return HebbianTzimtzumESN(
            n_inputs=3,
            n_reservoir=50,
            random_state=42
        )
    
    def test_initialization(self, hebbian_tzimtzum):
        """Test HebbianTzimtzumESN initializes with both systems."""
        assert hasattr(hebbian_tzimtzum, 'tzimtzum_state')
        assert hasattr(hebbian_tzimtzum, 'W_reservoir')
    
    def test_hebbian_update_via_state(self, hebbian_tzimtzum):
        """Test that _update_state modifies internal state."""
        input_vec = np.array([0.5, -0.3, 0.1])
        
        initial_state = hebbian_tzimtzum.state.copy()
        hebbian_tzimtzum._update_state(input_vec)
        
        # State should have changed
        assert not np.allclose(initial_state, hebbian_tzimtzum.state)
    
    def test_dark_night_works(self, hebbian_tzimtzum):
        """Test that dark_night() changes phase."""
        from plasticity.tzimtzum import ContractionPhase
        
        result = hebbian_tzimtzum.dark_night()
        
        assert 'pruned_count' in result
        # Phase should have changed from PLENITUD
        assert hebbian_tzimtzum.tzimtzum_state.phase != ContractionPhase.PLENITUD


class TestEgregorProcessor:
    """Test cases for EgregorProcessor - Group Mind system."""
    
    @pytest.fixture
    def processor(self):
        """Create an EgregorProcessor instance."""
        import sys
        import os
        egregore_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "phase6-collective"
        )
        if egregore_path not in sys.path:
            sys.path.insert(0, egregore_path)
        from egregore import EgregorProcessor
        return EgregorProcessor(decay_time=30.0)
    
    @pytest.fixture
    def sample_sensor_data(self):
        """Create sample sensor data."""
        import sys
        import os
        import time
        egregore_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "phase6-collective"
        )
        if egregore_path not in sys.path:
            sys.path.insert(0, egregore_path)
        from egregore import NodeSensorData
        return NodeSensorData(
            node_id="test_node",
            timestamp=time.time(),
            temperature=25.0,
            noise_level=0.3,
            motion_intensity=0.5,
            processing_load=0.4,
            prediction_error=0.1,
            will_alignment=0.8
        )
    
    def test_processor_initialization(self, processor):
        """Test EgregorProcessor initializes correctly."""
        assert processor.decay_time == pytest.approx(30.0, abs=0.1)
        assert len(processor.node_data) == 0
    
    def test_update_node_data(self, processor, sample_sensor_data):
        """Test updating node data in processor."""
        processor.update_node_data(sample_sensor_data)
        
        assert "test_node" in processor.node_data
        assert processor.node_data["test_node"].temperature == pytest.approx(25.0, abs=0.1)
    
    def test_process_generates_state(self, processor, sample_sensor_data):
        """Test that process() generates EgregorState."""
        # Add some nodes
        processor.update_node_data(sample_sensor_data)
        
        state = processor.process()
        
        assert state is not None
        assert hasattr(state, 'mood')
        assert hasattr(state, 'energy_level')
        assert hasattr(state, 'coherence')
    
    def test_energy_calculation(self, processor, sample_sensor_data):
        """Test energy is calculated within valid range."""
        processor.update_node_data(sample_sensor_data)
        state = processor.process()
        
        assert 0.0 <= state.energy_level <= 1.0


class TestKalmanFilter:
    """Dedicated tests for KalmanFilter component."""
    
    @pytest.fixture
    def kalman(self):
        """Create a KalmanFilter instance."""
        from core.alchemy import KalmanFilter
        return KalmanFilter(process_noise=0.01, measurement_noise=0.1)
    
    def test_single_update(self, kalman):
        """Test single Kalman update."""
        result = kalman.update(1.0)
        assert result is not None
        assert isinstance(result, float)
    
    def test_convergence(self, kalman):
        """Test that Kalman converges to true value."""
        rng = np.random.default_rng(42)
        true_value = 5.0
        noisy_measurements = true_value + rng.normal(0, 0.5, 100)
        
        filtered = kalman.filter_sequence(noisy_measurements)
        
        # Last estimates should be close to true value
        assert abs(filtered[-1] - true_value) < 1.0
    
    def test_reset(self, kalman):
        """Test that reset() clears filter state."""
        kalman.update(10.0)
        kalman.reset()
        
        assert kalman.x == pytest.approx(0.0, abs=1e-6)
        assert kalman.P == pytest.approx(1.0, abs=1e-6)


class TestIntegration:
    """Integration tests combining multiple mystical modules."""
    
    def test_tzimtzum_with_fit(self):
        """Test TzimtzumESN can fit data after pruning."""
        from plasticity.tzimtzum import TzimtzumESN
        
        esn = TzimtzumESN(n_inputs=1, n_reservoir=50, random_state=42)
        
        # Generate training data
        T = 200
        X = np.sin(np.linspace(0, 4 * np.pi, T)).reshape(-1, 1)
        Y = np.roll(X, -1, axis=0)  # Predict next step
        
        # Prune first
        esn.dark_night()
        
        # Then fit (should not raise error)
        esn.fit(X, Y, washout=20)
        
        # Verify W_out was learned
        assert esn.W_out is not None
    
    def test_alchemy_pipeline_with_real_pattern(self):
        """Test alchemy pipeline completes transmutation."""
        from core.alchemy import AlchemicalPipeline, AlchemicalConfig, AlchemicalPhase
        
        config = AlchemicalConfig(
            kalman_process_noise=0.005,
            kalman_measurement_noise=0.1,
            remove_outliers=True
        )
        pipeline = AlchemicalPipeline(config=config)
        
        # Create data with clear pattern
        rng = np.random.default_rng(42)
        t = np.linspace(0, 2 * np.pi, 100)
        pattern = np.sin(t)
        noisy = pattern + rng.normal(0, 0.3, len(t))
        
        # Transmute
        result = pipeline.transmute(noisy)
        
        # Pipeline should have processed through to at least RUBEDO
        assert pipeline.state.current_phase in [
            AlchemicalPhase.RUBEDO, 
            AlchemicalPhase.OPUS_COMPLETE
        ]
        assert 'gold' in result
    
    def test_recursive_esn_fit(self):
        """Test RecursiveEchoStateNetwork can fit data."""
        from esn.recursive_esn import RecursiveEchoStateNetwork
        
        esn = RecursiveEchoStateNetwork(
            n_inputs=1, 
            n_outputs=1,
            n_macro_units=3,
            n_micro_neurons=5,
            random_state=42
        )
        
        # Generate data
        T = 100
        X = np.sin(np.linspace(0, 4 * np.pi, T)).reshape(-1, 1)
        Y = X  # Simple autoregression
        
        # Fit
        esn.fit(X, Y, washout=10)
        
        # Should have W_out after fitting
        assert esn.W_out is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
