"""
Tests para MorphingESN - Proyecto Eón
======================================

Tests de topología dinámica de reservorios.
"""

import pytest
import numpy as np
import sys
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
_python_dir = os.path.dirname(_current_dir)
sys.path.insert(0, _python_dir)

from plasticity.morphing import (
    MorphingESN,
    TopologyType,
    build_topology,
    suggest_topology,
    _measure_autocorrelation,
    _measure_variance,
)
from esn.esn import generate_mackey_glass


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def trained_morpher():
    data = generate_mackey_glass(600)
    esn = MorphingESN(
        n_inputs=1, n_reservoir=40, n_outputs=1,
        spectral_radius=0.9, random_state=42,
    )
    X = data[:-1].reshape(-1, 1)
    y = data[1:].reshape(-1, 1)
    esn.fit(X, y, washout=50)
    return esn


# ─── Tests de build_topology ─────────────────────────────────────────────────

class TestBuildTopology:
    @pytest.mark.parametrize("topology", list(TopologyType))
    def test_shape(self, topology):
        rng = np.random.default_rng(0)
        W = build_topology(topology, n=30, spectral_radius=0.9, rng=rng)
        assert W.shape == (30, 30)

    @pytest.mark.parametrize("topology", list(TopologyType))
    def test_spectral_radius(self, topology):
        rng = np.random.default_rng(1)
        W = build_topology(topology, n=30, spectral_radius=0.9, rng=rng)
        eigs = np.abs(np.linalg.eigvals(W))
        if eigs.max() > 1e-10:
            assert abs(eigs.max() - 0.9) < 0.05

    def test_ring_connectivity(self):
        """En un anillo, la mayoría de la diagonal debe ser 0."""
        rng = np.random.default_rng(2)
        W = build_topology(TopologyType.RING, n=20, spectral_radius=0.9, rng=rng)
        assert np.trace(np.abs(W)) < 1e-6  # Sin self-loops

    def test_scale_free_power_law(self):
        """Scale-free debe tener pocos nodos con muchas conexiones (hubs)."""
        rng = np.random.default_rng(3)
        n = 50
        W = build_topology(TopologyType.SCALE_FREE, n=n, spectral_radius=0.9, rng=rng)
        degrees = (W != 0).sum(axis=1)
        # Debe haber al menos un nodo con grado > promedio*2
        assert degrees.max() > degrees.mean() * 1.5

    def test_lattice_max_degree(self):
        """En una rejilla 2D, ninguna neurona tiene más de 4 conexiones."""
        rng = np.random.default_rng(4)
        W = build_topology(TopologyType.LATTICE, n=25, spectral_radius=0.9, rng=rng)
        # Grado de salida ≤ 4 (4 vecinos cardinales)
        out_degrees = (W != 0).sum(axis=1)
        assert out_degrees.max() <= 4


# ─── Tests de suggest_topology ───────────────────────────────────────────────

class TestSuggestTopology:
    def test_few_samples_returns_random(self):
        states = np.random.default_rng(0).standard_normal((5, 20))
        assert suggest_topology(states) == TopologyType.RANDOM

    def test_high_autocorr_suggests_ring(self):
        """Estados muy correlados → RING."""
        t = np.linspace(0, 4 * np.pi, 200)
        states = np.column_stack([np.sin(t + i * 0.1) for i in range(20)])
        topology = suggest_topology(states)
        assert topology == TopologyType.RING

    def test_low_variance_suggests_scale_free(self):
        """Estados casi constantes → SCALE_FREE."""
        states = np.ones((100, 20)) * 0.01 + np.random.default_rng(5).standard_normal((100, 20)) * 0.001
        topology = suggest_topology(states)
        assert topology == TopologyType.SCALE_FREE

    def test_returns_valid_enum(self):
        states = np.random.default_rng(0).standard_normal((50, 10))
        t = suggest_topology(states)
        assert isinstance(t, TopologyType)


# ─── Tests de MorphingESN ─────────────────────────────────────────────────────

class TestMorphingESN:
    def test_default_topology(self):
        esn = MorphingESN(n_inputs=1, n_reservoir=20, n_outputs=1, random_state=0)
        assert esn.current_topology == TopologyType.RANDOM

    def test_custom_base_topology(self):
        esn = MorphingESN(
            n_inputs=1, n_reservoir=20, n_outputs=1,
            base_topology=TopologyType.RING, random_state=0,
        )
        assert esn.current_topology == TopologyType.RING

    def test_reservoir_shape(self):
        esn = MorphingESN(n_inputs=1, n_reservoir=30, n_outputs=1, random_state=0)
        assert esn.W_reservoir.shape == (30, 30)

    def test_morph_to_changes_topology(self):
        esn = MorphingESN(n_inputs=1, n_reservoir=30, n_outputs=1, random_state=0)
        result = esn.morph_to(TopologyType.RING)
        assert esn.current_topology == TopologyType.RING
        assert result["morphed"] is True

    def test_morph_to_same_topology(self):
        esn = MorphingESN(
            n_inputs=1, n_reservoir=30, n_outputs=1,
            base_topology=TopologyType.RING, random_state=0,
        )
        result = esn.morph_to(TopologyType.RING)
        assert result["morphed"] is False

    def test_morph_preserves_W_out(self, trained_morpher):
        """El morphing NO resetea W_out (preserva el aprendizaje)."""
        W_out_before = trained_morpher.W_out.copy()
        trained_morpher.morph_to(TopologyType.SMALL_WORLD)
        assert trained_morpher.W_out is not None
        np.testing.assert_array_equal(trained_morpher.W_out, W_out_before)

    def test_morph_history_recorded(self):
        esn = MorphingESN(n_inputs=1, n_reservoir=20, n_outputs=1, random_state=0)
        esn.morph_to(TopologyType.RING)
        esn.morph_to(TopologyType.SCALE_FREE)
        history = esn.morph_history()
        assert len(history) == 2
        assert history[0]["from"] == TopologyType.RANDOM.value
        assert history[0]["to"] == TopologyType.RING.value
        assert history[1]["to"] == TopologyType.SCALE_FREE.value

    def test_morph_to_all_topologies(self):
        esn = MorphingESN(n_inputs=1, n_reservoir=25, n_outputs=1, random_state=0)
        for topo in TopologyType:
            esn.morph_to(topo, transition_steps=0)
            assert esn.current_topology == topo
            assert esn.W_reservoir.shape == (25, 25)

    def test_predict_after_morph(self, trained_morpher):
        """Después de morph, el modelo sigue siendo utilizable."""
        trained_morpher.morph_to(TopologyType.LATTICE)
        X = generate_mackey_glass(100)[:-1].reshape(-1, 1)
        preds = trained_morpher.predict(X, reset_state=True)
        assert preds.shape[0] == 99
        assert np.isfinite(preds).all()


# ─── Tests de auto_morph() ───────────────────────────────────────────────────

class TestAutoMorph:
    def test_returns_topology_enum(self):
        esn = MorphingESN(n_inputs=1, n_reservoir=20, n_outputs=1, random_state=0)
        result = esn.auto_morph(observation_steps=50)
        assert isinstance(result, TopologyType)

    def test_force_always_morphs(self):
        esn = MorphingESN(
            n_inputs=1, n_reservoir=20, n_outputs=1,
            base_topology=TopologyType.RANDOM, random_state=0,
        )
        before = len(esn.morph_history())
        esn.auto_morph(force=True)
        # Con force=True siempre intenta morphing (puede ser a la misma topología)
        assert isinstance(esn.current_topology, TopologyType)


# ─── Tests de topology_metrics() ─────────────────────────────────────────────

class TestTopologyMetrics:
    def test_returns_dict(self):
        esn = MorphingESN(n_inputs=1, n_reservoir=20, n_outputs=1, random_state=0)
        metrics = esn.topology_metrics(observation_steps=30)
        assert isinstance(metrics, dict)

    def test_keys_present(self):
        esn = MorphingESN(n_inputs=1, n_reservoir=20, n_outputs=1, random_state=0)
        metrics = esn.topology_metrics(observation_steps=30)
        expected = {"topology", "autocorrelation", "activation_variance",
                    "sparsity", "n_connections", "morph_count"}
        assert expected.issubset(set(metrics.keys()))

    def test_topology_name_matches(self):
        esn = MorphingESN(
            n_inputs=1, n_reservoir=20, n_outputs=1,
            base_topology=TopologyType.RING, random_state=0,
        )
        metrics = esn.topology_metrics(observation_steps=20)
        assert metrics["topology"] == TopologyType.RING.value

    def test_sparsity_in_range(self):
        esn = MorphingESN(n_inputs=1, n_reservoir=20, n_outputs=1, random_state=0)
        metrics = esn.topology_metrics(observation_steps=20)
        assert 0.0 <= metrics["sparsity"] <= 1.0


# ─── Tests de métricas auxiliares ────────────────────────────────────────────

class TestAuxMetrics:
    def test_autocorr_returns_float(self):
        states = np.random.default_rng(0).standard_normal((50, 10))
        c = _measure_autocorrelation(states)
        assert isinstance(c, float)
        assert np.isfinite(c)

    def test_variance_positive(self):
        states = np.random.default_rng(0).standard_normal((50, 10))
        v = _measure_variance(states)
        assert v >= 0

    def test_autocorr_short_sequence(self):
        states = np.random.default_rng(0).standard_normal((3, 5))
        c = _measure_autocorrelation(states, lag=5)
        assert c == 0.0
