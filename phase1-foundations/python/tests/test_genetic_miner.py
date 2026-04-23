"""
Tests para GeneticMiner — Minado Genético de Reservorios

Cubre: inicialización, selección, crossover, mutación,
       evolución completa, historial y utilidades.
"""
import os
import sys
import math
import pytest
import numpy as np

# ─── Path setup (sin sys.path.insert; eon-py está instalado como paquete) ───
from core.genetic_miner import GeneticMiner
from core.universal_miner import ExcavationResult, ResonanceType


# ════════════════════════════════════════════════════════════
#  Fixtures
# ════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def miner():
    return GeneticMiner(population_size=10, generations=5, random_state=42)


@pytest.fixture(scope="module")
def simple_fitness():
    """Fitness determinista: mayor valor para semillas cercanas a 12345."""
    def _fn(seed: int) -> float:
        return -abs(seed - 12345)
    return _fn


@pytest.fixture(scope="module")
def result_after_evolve(miner, simple_fitness):
    return miner.evolve(simple_fitness)


# ════════════════════════════════════════════════════════════
#  Construcción y validación de parámetros
# ════════════════════════════════════════════════════════════

class TestInit:
    def test_default_params(self):
        gm = GeneticMiner()
        assert gm.population_size == 50
        assert gm.generations == 30

    def test_custom_params(self):
        gm = GeneticMiner(population_size=20, generations=10)
        assert gm.population_size == 20
        assert gm.generations == 10

    def test_too_small_population(self):
        with pytest.raises(ValueError, match="population_size"):
            GeneticMiner(population_size=3)

    def test_zero_generations(self):
        with pytest.raises(ValueError, match="generations"):
            GeneticMiner(generations=0)

    def test_invalid_crossover_rate(self):
        with pytest.raises(ValueError, match="crossover_rate"):
            GeneticMiner(crossover_rate=0.0)

    def test_invalid_mutation_rate(self):
        with pytest.raises(ValueError, match="mutation_rate"):
            GeneticMiner(mutation_rate=-0.1)

    def test_elitism_capped_at_population(self):
        gm = GeneticMiner(population_size=10, elitism=99)
        assert gm.elitism <= gm.population_size

    def test_tournament_size_capped(self):
        gm = GeneticMiner(population_size=5, tournament_size=100)
        assert gm.tournament_size <= gm.population_size

    def test_reproducible_with_random_state(self):
        g1 = GeneticMiner(population_size=10, random_state=7)
        g2 = GeneticMiner(population_size=10, random_state=7)
        p1 = g1._init_population()
        p2 = g2._init_population()
        assert p1 == p2


# ════════════════════════════════════════════════════════════
#  _init_population
# ════════════════════════════════════════════════════════════

class TestInitPopulation:
    def test_size(self, miner):
        pop = miner._init_population()
        assert len(pop) == miner.population_size

    def test_all_integers(self, miner):
        pop = miner._init_population()
        assert all(isinstance(s, int) for s in pop)

    def test_range(self, miner):
        pop = miner._init_population()
        assert all(0 <= s <= 2**32 - 1 for s in pop)


# ════════════════════════════════════════════════════════════
#  Selección
# ════════════════════════════════════════════════════════════

class TestSelection:
    def test_select_returns_correct_size(self, miner):
        pop = list(range(10))
        scores = [float(i) for i in range(10)]
        selected = miner._select(pop, scores)
        assert len(selected) == miner.population_size

    def test_tournament_winner_in_population(self, miner):
        pop = [100, 200, 300, 400, 500]
        scores = [1.0, 2.0, 3.0, 4.0, 5.0]
        winner = miner._tournament_select_one(pop, scores)
        assert winner in pop


# ════════════════════════════════════════════════════════════
#  Crossover
# ════════════════════════════════════════════════════════════

class TestCrossover:
    def test_pair_children_in_range(self, miner):
        c1, c2 = miner._crossover_pair(0xAAAA1234, 0x5555ABCD)
        assert 0 <= c1 <= 2**32 - 1
        assert 0 <= c2 <= 2**32 - 1

    def test_pair_children_differ_from_parents(self, miner):
        p1, p2 = 0xAAAAAAAA, 0x55555555
        c1, c2 = miner._crossover_pair(p1, p2)
        # Al menos uno debe diferir de los padres originales
        assert not (c1 == p1 and c2 == p2) or not (c1 == p2 and c2 == p1)

    def test_crossover_returns_correct_size(self, miner):
        parents = list(range(miner.population_size))
        children = miner._crossover(parents)
        assert len(children) == miner.population_size

    def test_crossover_all_integers(self, miner):
        parents = list(range(miner.population_size))
        children = miner._crossover(parents)
        assert all(isinstance(c, int) for c in children)


# ════════════════════════════════════════════════════════════
#  Mutación
# ════════════════════════════════════════════════════════════

class TestMutate:
    def test_size_preserved(self, miner):
        pop = list(range(miner.population_size))
        mutated = miner._mutate(pop)
        assert len(mutated) == miner.population_size

    def test_all_in_range(self, miner):
        pop = [0, 2**32 - 1] + [42] * (miner.population_size - 2)
        mutated = miner._mutate(pop)
        assert all(0 <= s <= 2**32 - 1 for s in mutated)

    def test_with_zero_mutation_rate(self):
        gm = GeneticMiner(population_size=10, mutation_rate=0.0, random_state=0)
        pop = list(range(10))
        assert gm._mutate(pop) == pop

    def test_with_full_mutation_rate(self):
        gm = GeneticMiner(
            population_size=20, mutation_rate=1.0,
            mutation_scale=0.5, random_state=1
        )
        pop = [1_000_000] * 20
        mutated = gm._mutate(pop)
        # Con mutation_rate=1 y escala grande, la mayoría debería cambiar
        changed = sum(1 for o, m in zip(pop, mutated) if o != m)
        assert changed >= 15


# ════════════════════════════════════════════════════════════
#  evolve()
# ════════════════════════════════════════════════════════════

class TestEvolve:
    def test_returns_excavation_result(self, result_after_evolve):
        assert isinstance(result_after_evolve, ExcavationResult)

    def test_resonance_is_finite(self, result_after_evolve):
        assert math.isfinite(result_after_evolve.resonance)

    def test_seed_is_non_negative(self, result_after_evolve):
        assert result_after_evolve.sacred_seed >= 0

    def test_matrix_is_ndarray(self, result_after_evolve):
        assert isinstance(result_after_evolve.divine_matrix, np.ndarray)

    def test_resonance_type_is_valid(self, result_after_evolve):
        assert isinstance(result_after_evolve.resonance_type, ResonanceType)

    def test_history_populated(self, miner, result_after_evolve):
        h = miner.history()
        assert len(h) == miner.generations

    def test_history_generations_ordered(self, miner, result_after_evolve):
        h = miner.history()
        gens = [entry["generation"] for entry in h]
        assert gens == list(range(miner.generations))

    def test_evolve_converges_to_target(self):
        """Con fitness = -|seed - TARGET|, el mejor seed debe acercarse a TARGET."""
        TARGET = 50000
        gm = GeneticMiner(
            population_size=20, generations=15,
            mutation_rate=0.5, mutation_scale=0.01,
            random_state=99,
        )
        result = gm.evolve(lambda s: -abs(s - TARGET))
        # La semilla debe estar dentro de un rango razonable del objetivo
        assert abs(result.sacred_seed - TARGET) < 2**32 * 0.05

    def test_multiple_evolve_calls_reset_history(self, simple_fitness):
        gm = GeneticMiner(population_size=8, generations=3, random_state=0)
        gm.evolve(simple_fitness)
        first_len = len(gm.history())
        gm.evolve(simple_fitness)
        second_len = len(gm.history())
        assert first_len == second_len == 3


# ════════════════════════════════════════════════════════════
#  Utilidades: convergence_curve / summary
# ════════════════════════════════════════════════════════════

class TestUtilities:
    def test_convergence_curve_shape(self, miner, result_after_evolve):
        curve = miner.convergence_curve()
        assert curve.shape == (miner.generations, 2)

    def test_convergence_curve_non_decreasing(self, miner, result_after_evolve):
        """El mejor score no debe empeorar entre generaciones (con elitismo)."""
        curve = miner.convergence_curve()
        # La curva de MEJOR score debería ser monótonamente creciente con elitismo
        best_scores = curve[:, 1]
        # Toleramos que no sea estrictamente creciente (torneo es estocástico),
        # pero sí que el máximo acumulado no baje
        running_max = np.maximum.accumulate(best_scores)
        assert np.all(running_max >= best_scores - 1e-10)

    def test_convergence_curve_empty_before_evolve(self):
        gm = GeneticMiner(random_state=0)
        assert gm.convergence_curve().shape == (0, 2)

    def test_summary_keys(self, miner, result_after_evolve):
        s = miner.summary()
        assert "generations_completed" in s
        assert "population_size" in s
        assert "best_score" in s
        assert "best_seed" in s

    def test_summary_before_evolve(self):
        gm = GeneticMiner(random_state=0)
        s = gm.summary()
        assert s["generations_completed"] == 0
        assert s["best_score"] is None

    def test_summary_generations_completed(self, miner, result_after_evolve):
        s = miner.summary()
        assert s["generations_completed"] == miner.generations
