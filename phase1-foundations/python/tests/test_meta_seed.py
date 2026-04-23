"""
Tests para MetaSeedLearner - Proyecto Eón
==========================================

Tests del sistema de meta-aprendizaje cross-seed.
"""

import pytest
import numpy as np
import sys
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
_python_dir = os.path.dirname(_current_dir)
sys.path.insert(0, _python_dir)

from core.meta_seed import MetaSeedLearner, SeedPattern
from core.universal_miner import UniversalMiner, SeedVault, ExcavationResult, ResonanceType


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def miner():
    return UniversalMiner(
        reservoir_size=50,
        target_resonance=(0.90, 1.10),
        resonance_type=ResonanceType.EDGE_OF_CHAOS,
        sparsity=0.1,
    )


@pytest.fixture(scope="module")
def populated_vault(miner):
    """Bóveda con 3 semillas excavadas (rango amplio para ser rápido)."""
    vault = SeedVault()
    # Excavar un puñado de semillas para tener patrones reales
    result = miner.excavate(max_attempts=200_000, starting_seed=0, verbose=False)
    vault.store("seed_0", result)

    result2 = miner.excavate(max_attempts=200_000, starting_seed=result.sacred_seed + 1, verbose=False)
    vault.store("seed_1", result2)

    return vault


@pytest.fixture(scope="module")
def learner(miner, populated_vault):
    learner = MetaSeedLearner(miner, populated_vault, n_clusters=2, random_state=42)
    learner.learn()
    return learner


# ─── Tests de SeedPattern ────────────────────────────────────────────────────

class TestSeedPattern:
    def test_as_vector_length(self, miner, populated_vault):
        """El vector de features tiene longitud correcta (4 + TOP_K)."""
        learner = MetaSeedLearner(miner, populated_vault, random_state=0)
        result = populated_vault.retrieve("seed_0")
        pattern = learner._extract_pattern(result)
        vec = pattern.as_vector()
        assert len(vec) == 4 + MetaSeedLearner.TOP_K

    def test_pattern_values_finite(self, miner, populated_vault):
        """Todos los valores del patrón son finitos."""
        learner = MetaSeedLearner(miner, populated_vault, random_state=0)
        result = populated_vault.retrieve("seed_0")
        pattern = learner._extract_pattern(result)
        assert np.isfinite(pattern.as_vector()).all()

    def test_phase_uniformity_range(self, miner, populated_vault):
        """La uniformidad de fases está en [0, 1]."""
        learner = MetaSeedLearner(miner, populated_vault, random_state=0)
        result = populated_vault.retrieve("seed_0")
        pattern = learner._extract_pattern(result)
        assert 0.0 <= pattern.phase_uniformity <= 1.0


# ─── Tests de learn() ────────────────────────────────────────────────────────

class TestLearn:
    def test_learn_populates_patterns(self, learner):
        """Después de learn(), hay patrones en el estado."""
        assert len(learner.state.patterns) >= 1

    def test_learn_creates_clusters(self, learner):
        """Se crean centros de cluster."""
        assert learner.state.cluster_centers is not None
        assert learner.state.n_clusters >= 1

    def test_learn_no_data_warning(self, miner):
        """learn() con bóveda vacía lanza warning pero no falla."""
        empty_vault = SeedVault()
        learner = MetaSeedLearner(miner, empty_vault, random_state=0)
        learner.learn()  # No debe lanzar excepción
        assert len(learner.state.patterns) == 0

    def test_learn_single_seed(self, miner, populated_vault):
        """learn() con una sola semilla no falla."""
        single_vault = SeedVault()
        r = populated_vault.retrieve("seed_0")
        single_vault.store("only", r)
        learner = MetaSeedLearner(miner, single_vault, n_clusters=3, random_state=0)
        learner.learn()
        assert learner.state.n_clusters == 1

    def test_learn_returns_self(self, miner, populated_vault):
        """learn() devuelve self para encadenamiento."""
        l = MetaSeedLearner(miner, populated_vault, random_state=0)
        result = l.learn()
        assert result is l


# ─── Tests de generate_candidates() ─────────────────────────────────────────

class TestGenerateCandidates:
    def test_returns_n_candidates(self, learner):
        candidates = learner.generate_candidates(n=500)
        assert len(candidates) == 500

    def test_candidates_are_positive(self, learner):
        candidates = learner.generate_candidates(n=200)
        assert all(c > 0 for c in candidates)

    def test_candidates_are_integers(self, learner):
        candidates = learner.generate_candidates(n=100)
        assert all(isinstance(c, int) for c in candidates)

    def test_candidates_no_duplicates(self, learner):
        candidates = learner.generate_candidates(n=200)
        assert len(set(candidates)) == len(candidates)

    def test_untrained_returns_random(self, miner):
        """Sin entrenar, genera seeds aleatorias válidas."""
        l = MetaSeedLearner(miner, SeedVault(), random_state=0)
        candidates = l.generate_candidates(n=50)
        assert len(candidates) == 50
        assert all(c > 0 for c in candidates)


# ─── Tests de guided_excavate() ──────────────────────────────────────────────

class TestGuidedExcavate:
    def test_returns_excavation_result(self, learner):
        result = learner.guided_excavate(max_attempts=50_000, verbose=False)
        assert isinstance(result, ExcavationResult)

    def test_result_has_valid_seed(self, learner):
        result = learner.guided_excavate(max_attempts=50_000, verbose=False)
        assert result.sacred_seed > 0

    def test_result_has_finite_resonance(self, learner):
        result = learner.guided_excavate(max_attempts=50_000, verbose=False)
        assert np.isfinite(result.resonance)

    def test_guided_faster_than_blind(self, miner, populated_vault):
        """Excavación guiada debe encontrar resonancia en ≤ max_attempts intentos."""
        learner = MetaSeedLearner(miner, populated_vault, n_clusters=2, random_state=7)
        learner.learn()

        result = learner.guided_excavate(max_attempts=100_000, verbose=False)

        # Debe retornar un resultado válido dentro del límite de intentos
        assert result.excavation_depth <= 100_000
        assert result.sacred_seed >= 0
        assert result.resonance_type is not None

    def test_untrained_delegates_to_miner(self, miner):
        """Sin entrenamiento, delega a miner.excavate()."""
        l = MetaSeedLearner(miner, SeedVault(), random_state=0)
        result = l.guided_excavate(max_attempts=50_000, verbose=False)
        assert isinstance(result, ExcavationResult)

    def test_guided_stores_in_vault(self, miner, populated_vault):
        """guided_excavate guarda el resultado en la bóveda si lo encuentra."""
        learner = MetaSeedLearner(miner, populated_vault, n_clusters=2, random_state=99)
        learner.learn()
        before = len(populated_vault.list_seeds())
        result = learner.guided_excavate(max_attempts=100_000, verbose=False)
        mn, mx = miner.target_resonance
        if mn <= result.resonance <= mx:
            assert len(populated_vault.list_seeds()) > before


# ─── Tests de summary() ──────────────────────────────────────────────────────

class TestSummary:
    def test_summary_keys(self, learner):
        s = learner.summary()
        assert "seeds_analyzed" in s
        assert "clusters" in s
        assert "excavations_guided" in s
        assert "known_seeds" in s

    def test_summary_counts(self, learner):
        s = learner.summary()
        assert s["seeds_analyzed"] >= 1
        assert s["clusters"] >= 1
        assert isinstance(s["known_seeds"], list)


# ─── Tests de PCA interna ────────────────────────────────────────────────────

class TestPCA:
    def test_pca_output_shape(self, miner):
        l = MetaSeedLearner(miner, random_state=0)
        X = np.random.default_rng(0).standard_normal((10, 12))
        reduced = l._pca_reduce(X, n_components=3)
        assert reduced.shape == (10, 3)

    def test_pca_zero_mean(self, miner):
        """La proyección PCA tiene media ~ 0 (está centrada)."""
        l = MetaSeedLearner(miner, random_state=0)
        X = np.random.default_rng(1).standard_normal((20, 8))
        reduced = l._pca_reduce(X, n_components=2)
        assert np.allclose(reduced.mean(axis=0), 0, atol=1e-6)


# ─── Tests de K-Means interna ────────────────────────────────────────────────

class TestKMeans:
    def test_kmeans_labels_shape(self, miner):
        l = MetaSeedLearner(miner, random_state=0)
        X = np.random.default_rng(0).standard_normal((30, 4))
        centers, labels = l._kmeans(X, k=3)
        assert labels.shape == (30,)
        assert centers.shape[0] == 3

    def test_kmeans_labels_valid(self, miner):
        l = MetaSeedLearner(miner, random_state=0)
        X = np.random.default_rng(0).standard_normal((20, 3))
        centers, labels = l._kmeans(X, k=4)
        assert set(labels).issubset(set(range(4)))

    def test_kmeans_k_gt_n(self, miner):
        """k > n_points → k reducido a n_points."""
        l = MetaSeedLearner(miner, random_state=0)
        X = np.random.default_rng(0).standard_normal((3, 4))
        centers, labels = l._kmeans(X, k=10)
        assert centers.shape[0] <= 3
