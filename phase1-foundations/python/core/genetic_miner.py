"""
Proyecto Eón - Minado Genético de Reservorios
==============================================

"La evolución no diseña — descubre."

Aplica algoritmos genéticos para encontrar semillas que producen
reservorios con alta resonancia. Cada generación acerca la búsqueda
a regiones más fértiles del espacio de semillas.

PARADIGMA:
──────────
Cada semilla es un cromosoma. El fitness es la resonancia medida
por UniversalMiner. La evolución combina exploración (mutación)
con explotación (crossover de semillas exitosas).
"""

import numpy as np
import time
from typing import Callable, List, Optional, Tuple

from core.universal_miner import (
    UniversalMiner, ExcavationResult, ResonanceType, SeedVault
)

# Optional import for SeedArchaeologist integration
try:
    from core.seed_archaeologist import SeedArchaeologist
    SEED_ARCHAEOLOGIST_AVAILABLE = True
except ImportError:
    SEED_ARCHAEOLOGIST_AVAILABLE = False
    SeedArchaeologist = None


class GeneticMiner:
    """
    Minador de semillas usando algoritmos genéticos.

    Evoluciona una población de semillas candidatas hacia zonas de
    alta resonancia usando selección por torneo, crossover bit-level
    y mutación gaussiana.

    Ejemplo::

        miner = UniversalMiner(n_reservoir=50)

        def fitness(seed):
            result = miner.excavate(start_seed=seed, max_attempts=1)
            return result.resonance

        # Evolución básica
        genetic = GeneticMiner(population_size=30, generations=20)
        result = genetic.evolve(fitness)

        # Evolución con archaeologist (más eficiente)
        vault = SeedVault()
        genetic_smart = GeneticMiner(
            population_size=30, 
            generations=20,
            use_archaeologist=True,
            fertile_bias=0.8
        )
        result = genetic_smart.evolve(fitness, vault)
    """

    # Rango de semillas válidas (uint32)
    _SEED_MIN: int = 0
    _SEED_MAX: int = 2 ** 32 - 1

    def __init__(
        self,
        population_size: int = 50,
        generations: int = 30,
        tournament_size: int = 3,
        crossover_rate: float = 0.7,
        mutation_rate: float = 0.1,
        mutation_scale: float = 0.05,
        elitism: int = 2,
        random_state: Optional[int] = None,
        use_archaeologist: bool = False,
        archaeologist_samples: int = 1000,
        fertile_bias: float = 0.7,
    ):
        """
        Args:
            population_size: Número de individuos por generación (mín 4).
            generations: Número de generaciones a evolucionar (mín 1).
            tournament_size: Participantes por torneo de selección.
            crossover_rate: Probabilidad de crossover entre pares (0, 1].
            mutation_rate: Probabilidad de mutar un individuo [0, 1].
            mutation_scale: Escala relativa de mutación (fracción del rango).
            elitism: Cuántos mejores individuos pasan sin cambios.
            random_state: Semilla para reproducibilidad.
            use_archaeologist: Si usar SeedArchaeologist para guiar evolución.
            archaeologist_samples: Muestras para crear mapa de fertilidad.
            fertile_bias: Fracción de población inicializada en regiones fértiles.
        """
        if population_size < 4:
            raise ValueError("population_size debe ser >= 4")
        if generations < 1:
            raise ValueError("generations debe ser >= 1")
        if not (0.0 < crossover_rate <= 1.0):
            raise ValueError("crossover_rate debe estar en (0, 1]")
        if not (0.0 <= mutation_rate <= 1.0):
            raise ValueError("mutation_rate debe estar en [0, 1]")
        if use_archaeologist and not SEED_ARCHAEOLOGIST_AVAILABLE:
            raise ImportError("SeedArchaeologist no disponible. Instala seed_archaeologist.py")

        self.population_size = population_size
        self.generations = generations
        self.tournament_size = min(tournament_size, population_size)
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.mutation_scale = mutation_scale
        self.elitism = min(elitism, population_size)
        self.use_archaeologist = use_archaeologist
        self.archaeologist_samples = archaeologist_samples
        self.fertile_bias = fertile_bias

        self._rng = np.random.RandomState(random_state)
        self._history: List[dict] = []
        self._archaeologist: Optional[SeedArchaeologist] = None
        self._fertile_regions: List[Tuple[int, int]] = []

    # ─── Inicialización ────────────────────────────────────────────────────

    def _init_population(self, vault: Optional[SeedVault] = None) -> List[int]:
        """Genera población inicial de semillas."""
        if self.use_archaeologist and vault is not None:
            return self._init_population_with_archaeologist(vault)
        else:
            return self._init_population_random()

    def _init_population_random(self) -> List[int]:
        """Genera población inicial completamente aleatoria."""
        seeds = self._rng.randint(
            self._SEED_MIN, self._SEED_MAX + 1, size=self.population_size
        ).tolist()
        return seeds

    def _init_population_with_archaeologist(self, vault: SeedVault) -> List[int]:
        """Genera población inicial usando mapas de fertilidad."""
        # Inicializar arqueólogo si no existe
        if self._archaeologist is None:
            self._archaeologist = SeedArchaeologist(vault, random_state=self._rng.randint(0, 2**32))

        # Crear mapa de fertilidad
        landscape = self._archaeologist.create_landscape_map(
            n_samples=self.archaeologist_samples,
            verbose=False
        )

        # Encontrar regiones fértiles
        self._fertile_regions = self._archaeologist.find_fertile_regions(
            threshold_percentile=75.0,  # Top 25% más fértiles
            min_region_size=5
        )

        seeds = []
        n_fertile = int(self.population_size * self.fertile_bias)
        n_random = self.population_size - n_fertile

        # Generar semillas en regiones fértiles
        if self._fertile_regions:
            for _ in range(n_fertile):
                region = self._rng.choice(self._fertile_regions)
                start, end = region
                seed = self._rng.randint(start, end + 1)
                seeds.append(seed)

        # Generar semillas aleatorias para el resto
        random_seeds = self._rng.randint(
            self._SEED_MIN, self._SEED_MAX + 1, size=n_random
        ).tolist()
        seeds.extend(random_seeds)

        # Mezclar para evitar sesgos
        self._rng.shuffle(seeds)
        return seeds

    # ─── Selección ─────────────────────────────────────────────────────────

    def _tournament_select_one(
        self, population: List[int], scores: List[float]
    ) -> int:
        """Selecciona un individuo mediante torneo (mayor score gana)."""
        idxs = self._rng.choice(
            len(population), size=self.tournament_size, replace=False
        )
        best_idx = idxs[int(np.argmax([scores[i] for i in idxs]))]
        return population[best_idx]

    def _select(
        self, population: List[int], scores: List[float]
    ) -> List[int]:
        """Selecciona population_size padres mediante torneo repetido."""
        return [
            self._tournament_select_one(population, scores)
            for _ in range(self.population_size)
        ]

    # ─── Crossover ─────────────────────────────────────────────────────────

    def _crossover_pair(self, p1: int, p2: int) -> Tuple[int, int]:
        """
        Crossover bit-level de un punto.

        Elige un punto de corte en los 32 bits y mezcla:
        hijo1 = bits altos de p1 + bits bajos de p2
        hijo2 = bits altos de p2 + bits bajos de p1
        """
        point = int(self._rng.randint(1, 31))   # bits 1..30
        mask_low = (1 << point) - 1              # bits 0..point-1
        mask_high = self._SEED_MAX ^ mask_low    # bits point..31

        c1 = (p1 & mask_high) | (p2 & mask_low)
        c2 = (p2 & mask_high) | (p1 & mask_low)
        return c1, c2

    def _crossover(self, parents: List[int]) -> List[int]:
        """Aplica crossover aleatorio a la lista de padres."""
        children: List[int] = []
        shuffled = parents[:]
        self._rng.shuffle(shuffled)

        for i in range(0, len(shuffled) - 1, 2):
            if self._rng.random() < self.crossover_rate:
                c1, c2 = self._crossover_pair(shuffled[i], shuffled[i + 1])
                children.extend([c1, c2])
            else:
                children.extend([shuffled[i], shuffled[i + 1]])

        if len(shuffled) % 2 == 1:
            children.append(shuffled[-1])

        return children[: self.population_size]

    # ─── Mutación ──────────────────────────────────────────────────────────

    def _mutate(self, population: List[int]) -> List[int]:
        """
        Mutación gaussiana.

        Suma un delta ~ N(0, scale) a cada individuo con probabilidad
        mutation_rate. El resultado se recorta al rango [_SEED_MIN, _SEED_MAX].
        """
        scale = int(self._SEED_MAX * self.mutation_scale)
        mutated: List[int] = []
        for seed in population:
            if self._rng.random() < self.mutation_rate:
                delta = int(self._rng.normal(0, scale))
                new_seed = max(self._SEED_MIN, min(self._SEED_MAX, seed + delta))
                mutated.append(new_seed)
            else:
                mutated.append(seed)
        return mutated

    # ─── Ciclo principal ───────────────────────────────────────────────────

    def evolve(
        self,
        fitness_fn: Callable[[int], float],
        vault: Optional[SeedVault] = None,
        verbose: bool = False,
    ) -> ExcavationResult:
        """
        Evoluciona la población para maximizar fitness_fn.

        Args:
            fitness_fn: Función (seed: int) -> float.
                       Mayor valor = mejor semilla.
            vault: SeedVault opcional para integración con archaeologist.
            verbose: Imprime progreso por generación si es True.

        Returns:
            ExcavationResult del mejor individuo encontrado.
        """
        t_start = time.time()
        self._history = []

        population = self._init_population(vault)
        best_seed: int = population[0]
        best_score: float = float("-inf")
        total_evals: int = 0

        for gen in range(self.generations):
            scores = [fitness_fn(s) for s in population]
            total_evals += len(scores)

            gen_best_idx = int(np.argmax(scores))
            gen_best_score = float(scores[gen_best_idx])
            gen_best_seed = population[gen_best_idx]

            if gen_best_score > best_score:
                best_score = gen_best_score
                best_seed = gen_best_seed

            gen_stats = {
                "generation": gen,
                "best_score": gen_best_score,
                "mean_score": float(np.mean(scores)),
                "best_seed": gen_best_seed,
            }
            self._history.append(gen_stats)

            if verbose:
                print(
                    f"Gen {gen:3d}: best={gen_best_score:.6f} "
                    f"mean={gen_stats['mean_score']:.6f} "
                    f"seed={gen_best_seed}"
                )

            # Elitismo: guardar los mejores antes de modificar la población
            sorted_idxs = sorted(
                range(len(scores)), key=lambda i: scores[i], reverse=True
            )
            elite = [population[i] for i in sorted_idxs[: self.elitism]]

            parents = self._select(population, scores)
            children = self._crossover(parents)
            next_pop = self._mutate(children)

            # Reinsertar élite (reemplaza los primeros N individuos)
            next_pop[: self.elitism] = elite
            population = next_pop

        # Evaluación final de la población resultante
        final_scores = [fitness_fn(s) for s in population]
        total_evals += len(final_scores)

        final_best_idx = int(np.argmax(final_scores))
        final_best_score = float(final_scores[final_best_idx])
        if final_best_score > best_score:
            best_score = final_best_score
            best_seed = population[final_best_idx]

        t_elapsed = time.time() - t_start

        # Materializar la matriz del reservoir para la semilla ganadora
        _miner = UniversalMiner(reservoir_size=50)
        result = _miner.excavate(starting_seed=best_seed, max_attempts=1, verbose=False)

        return ExcavationResult(
            sacred_seed=best_seed,
            divine_matrix=result.divine_matrix,
            resonance=best_score,
            resonance_type=result.resonance_type,
            excavation_depth=total_evals,
            excavation_time=t_elapsed,
            eigenspectrum=result.eigenspectrum,
        )

    # ─── Utilidades ────────────────────────────────────────────────────────

    def history(self) -> List[dict]:
        """Estadísticas por generación. Vacío antes de llamar evolve()."""
        return list(self._history)

    def archaeologist_stats(self) -> dict:
        """Estadísticas sobre el uso de SeedArchaeologist."""
        if not self.use_archaeologist:
            return {"enabled": False}
        
        stats = {
            "enabled": True,
            "fertile_regions_found": len(self._fertile_regions),
            "fertile_bias": self.fertile_bias,
            "archaeologist_samples": self.archaeologist_samples,
        }
        
        if self._archaeologist:
            stats["landscape_stats"] = self._archaeologist.landscape_statistics()
        
        return stats

    def convergence_curve(self) -> np.ndarray:
        """
        Array (generations, 2) con columnas [generation, best_score].

        Útil para visualizar la convergencia genética.
        """
        if not self._history:
            return np.empty((0, 2))
        return np.array(
            [(h["generation"], h["best_score"]) for h in self._history]
        )

    def summary(self) -> dict:
        """Resumen del estado del GeneticMiner."""
        if not self._history:
            return {
                "generations_completed": 0,
                "population_size": self.population_size,
                "max_generations": self.generations,
                "best_score": None,
                "best_seed": None,
            }
        last = self._history[-1]
        return {
            "generations_completed": len(self._history),
            "population_size": self.population_size,
            "max_generations": self.generations,
            "best_score": last["best_score"],
            "best_seed": last["best_seed"],
        }
