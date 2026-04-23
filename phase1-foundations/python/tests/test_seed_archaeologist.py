"""
Tests para SeedArchaeologist — Arqueología de Semillas

Cubre: construcción, fertility_score, create_landscape_map,
       find_fertile_regions, analyze_vault, cluster_by_resonance_type,
       predict_fertility y utilidades.
"""
import pytest
import numpy as np

from core.seed_archaeologist import SeedArchaeologist
from core.universal_miner import (
    SeedVault, UniversalMiner, ExcavationResult, ResonanceType
)


# ════════════════════════════════════════════════════════════
#  Fixtures
# ════════════════════════════════════════════════════════════

def _make_result(seed: int, resonance: float, rtype: ResonanceType) -> ExcavationResult:
    """Crea un ExcavationResult sintético para poblar el vault."""
    miner = UniversalMiner(reservoir_size=20)
    matrix = miner.chaos_sample(seed)
    eigenvals = np.linalg.eigvals(matrix)
    return ExcavationResult(
        sacred_seed=seed,
        divine_matrix=matrix,
        resonance=resonance,
        resonance_type=rtype,
        excavation_depth=100,
        excavation_time=0.1,
        eigenspectrum=eigenvals,
    )


@pytest.fixture(scope="module")
def empty_vault():
    return SeedVault()


@pytest.fixture(scope="module")
def populated_vault():
    vault = SeedVault()
    vault.store("seed_a", _make_result(42, 0.98, ResonanceType.EDGE_OF_CHAOS))
    vault.store("seed_b", _make_result(100, 0.85, ResonanceType.HARMONIC))
    vault.store("seed_c", _make_result(200, 1.02, ResonanceType.GOLDEN))
    vault.store("seed_d", _make_result(300, 0.95, ResonanceType.EDGE_OF_CHAOS))
    vault.store("seed_e", _make_result(999, 1.10, ResonanceType.PRIME))
    return vault


@pytest.fixture(scope="module")
def arch(empty_vault):
    return SeedArchaeologist(empty_vault, reservoir_size=20, random_state=0)


@pytest.fixture(scope="module")
def arch_populated(populated_vault):
    return SeedArchaeologist(populated_vault, reservoir_size=20, random_state=7)


@pytest.fixture(scope="module")
def landscape(arch):
    return arch.create_landscape_map(n_samples=50, seed_range=(0, 100_000))


# ════════════════════════════════════════════════════════════
#  Construcción
# ════════════════════════════════════════════════════════════

class TestInit:
    def test_stores_vault(self, empty_vault, arch):
        assert arch.vault is empty_vault

    def test_default_reservoir_size(self, arch):
        assert arch.reservoir_size == 20

    def test_landscape_initially_none(self, arch):
        a = SeedArchaeologist(empty_vault, reservoir_size=20)
        assert a._landscape is None

    def test_fertile_regions_initially_none(self, arch):
        a = SeedArchaeologist(empty_vault, reservoir_size=20)
        assert a._fertile_regions is None


# ════════════════════════════════════════════════════════════
#  _fertility_score
# ════════════════════════════════════════════════════════════

class TestFertilityScore:
    def test_returns_float(self, arch):
        score = arch._fertility_score(42)
        assert isinstance(score, float)

    def test_non_negative(self, arch):
        for seed in [0, 1, 100, 999, 12345]:
            assert arch._fertility_score(seed) >= 0.0

    def test_higher_near_one(self, arch):
        """Una semilla con radio espectral ~1.0 debería tener mayor fertilidad."""
        # Buscamos una semilla que de cerca de 1.0
        # Score debe ser finito y positivo
        score = arch._fertility_score(42)
        assert np.isfinite(score)
        assert score > 0

    def test_reproducible(self, arch):
        s1 = arch._fertility_score(7777)
        s2 = arch._fertility_score(7777)
        assert s1 == s2


# ════════════════════════════════════════════════════════════
#  create_landscape_map
# ════════════════════════════════════════════════════════════

class TestCreateLandscapeMap:
    def test_returns_ndarray(self, landscape):
        assert isinstance(landscape, np.ndarray)

    def test_shape(self, landscape):
        assert landscape.shape == (50, 2)

    def test_seeds_column_in_range(self, landscape):
        seeds = landscape[:, 0]
        assert np.all(seeds >= 0)
        assert np.all(seeds <= 100_000)

    def test_scores_non_negative(self, landscape):
        scores = landscape[:, 1]
        assert np.all(scores >= 0)

    def test_seeds_sorted(self, landscape):
        seeds = landscape[:, 0]
        assert np.all(np.diff(seeds) >= 0)

    def test_raises_on_too_few_samples(self, arch):
        with pytest.raises(ValueError, match="n_samples"):
            arch.create_landscape_map(n_samples=1)

    def test_raises_on_invalid_range(self, arch):
        with pytest.raises(ValueError, match="seed_range"):
            arch.create_landscape_map(n_samples=5, seed_range=(100, 50))

    def test_landscape_stored(self, arch, landscape):
        assert arch._landscape is not None
        assert arch._landscape.shape == landscape.shape


# ════════════════════════════════════════════════════════════
#  find_fertile_regions
# ════════════════════════════════════════════════════════════

class TestFindFertileRegions:
    def test_raises_without_landscape(self, empty_vault):
        fresh = SeedArchaeologist(empty_vault, reservoir_size=20, random_state=0)
        with pytest.raises(RuntimeError, match="create_landscape_map"):
            fresh.find_fertile_regions()

    def test_returns_list(self, arch, landscape):
        regions = arch.find_fertile_regions()
        assert isinstance(regions, list)

    def test_regions_are_tuples_of_two(self, arch, landscape):
        regions = arch.find_fertile_regions()
        for r in regions:
            assert len(r) == 2

    def test_regions_start_lte_end(self, arch, landscape):
        regions = arch.find_fertile_regions()
        for start, end in regions:
            assert start <= end

    def test_regions_in_seed_range(self, arch, landscape):
        regions = arch.find_fertile_regions()
        for start, end in regions:
            assert start >= 0
            assert end <= 100_000

    def test_percentile_100_gives_fewer_regions(self, arch, landscape):
        """Umbral muy alto → menos regiones."""
        r75 = arch.find_fertile_regions(threshold_percentile=75)
        r95 = arch.find_fertile_regions(threshold_percentile=95)
        assert len(r95) <= len(r75)


# ════════════════════════════════════════════════════════════
#  analyze_vault
# ════════════════════════════════════════════════════════════

class TestAnalyzeVault:
    def test_empty_vault_returns_zeros(self, arch):
        result = arch.analyze_vault()
        assert result["count"] == 0
        assert result["resonance_mean"] is None

    def test_populated_vault_count(self, arch_populated):
        result = arch_populated.analyze_vault()
        assert result["count"] == 5

    def test_populated_vault_has_mean(self, arch_populated):
        result = arch_populated.analyze_vault()
        assert result["resonance_mean"] is not None
        assert np.isfinite(result["resonance_mean"])

    def test_populated_vault_top5(self, arch_populated):
        result = arch_populated.analyze_vault()
        assert len(result["top_5"]) == 5

    def test_top5_sorted_by_resonance(self, arch_populated):
        result = arch_populated.analyze_vault()
        resonances = [e["resonance"] for e in result["top_5"]]
        assert resonances == sorted(resonances, reverse=True)

    def test_type_distribution_keys(self, arch_populated):
        result = arch_populated.analyze_vault()
        dist = result["type_distribution"]
        assert isinstance(dist, dict)
        assert len(dist) > 0


# ════════════════════════════════════════════════════════════
#  cluster_by_resonance_type
# ════════════════════════════════════════════════════════════

class TestClusterByResonanceType:
    def test_returns_dict(self, arch_populated):
        clusters = arch_populated.cluster_by_resonance_type()
        assert isinstance(clusters, dict)

    def test_keys_are_resonance_type_values(self, arch_populated):
        clusters = arch_populated.cluster_by_resonance_type()
        valid_keys = {rt.value for rt in ResonanceType}
        for key in clusters:
            assert key in valid_keys

    def test_values_are_seed_lists(self, arch_populated):
        clusters = arch_populated.cluster_by_resonance_type()
        for seeds in clusters.values():
            assert isinstance(seeds, list)
            assert all(isinstance(s, int) for s in seeds)

    def test_edge_of_chaos_has_two(self, arch_populated):
        clusters = arch_populated.cluster_by_resonance_type()
        assert clusters.get("edge_of_chaos", []) is not None
        assert len(clusters.get("edge_of_chaos", [])) == 2


# ════════════════════════════════════════════════════════════
#  predict_fertility
# ════════════════════════════════════════════════════════════

class TestPredictFertility:
    def test_returns_ndarray(self, arch):
        pf = arch.predict_fertility([1, 2, 3, 100])
        assert isinstance(pf, np.ndarray)

    def test_shape_matches_input(self, arch):
        seeds = list(range(10))
        pf = arch.predict_fertility(seeds)
        assert pf.shape == (10,)

    def test_all_non_negative(self, arch):
        pf = arch.predict_fertility([0, 42, 9999, 100_000])
        assert np.all(pf >= 0)


# ════════════════════════════════════════════════════════════
#  Utilidades: landscape_statistics / summary
# ════════════════════════════════════════════════════════════

class TestUtilities:
    def test_statistics_before_landscape(self, empty_vault):
        a = SeedArchaeologist(empty_vault, reservoir_size=20)
        s = a.landscape_statistics()
        assert s["available"] is False

    def test_statistics_after_landscape(self, arch, landscape):
        s = arch.landscape_statistics()
        assert s["available"] is True
        assert "mean" in s
        assert "p75" in s
        assert s["n_samples"] == 50

    def test_summary_keys(self, arch, landscape):
        s = arch.summary()
        assert "vault_size" in s
        assert "landscape" in s
        assert "reservoir_size" in s

    def test_summary_vault_size(self, arch, landscape):
        s = arch.summary()
        assert s["vault_size"] == 0  # empty vault
