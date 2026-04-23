"""
Proyecto Eón - Arqueología de Semillas (Seed Archaeology)
==========================================================

"El mapa del tesoro no es el tesoro — pero nos lleva a él."

Estudia el paisaje topológico del espacio de semillas para identificar
regiones donde es más probable encontrar reservorios resonantes.

PARADIGMA:
──────────
No todas las semillas son iguales. Existen "islas de fertilidad" —
regiones donde la densidad de semillas exitosas es mayor. Este módulo
genera mapas de fertilidad y encuentra esas regiones para guiar
excavaciones futuras.

MÉTODO:
───────
1. Muestreo: evaluar n_samples semillas uniformemente distribuidas
2. Scoring: fertilidad = 1 / (|radio_espectral - 1.0| + ε)
3. Agrupación: clustering 1D por contigüidad y percentil
4. Resultados: rangos [inicio, fin] de alta fertilidad
"""

import time
from typing import List, Optional, Tuple

import numpy as np

from core.universal_miner import (
    ExcavationResult, ResonanceType, SeedVault, UniversalMiner,
)


# Fertilidad: cuán cerca está el radio espectral de 1.0 (borde del caos)
_FERTILITY_EPS: float = 1e-4
_SEED_MAX: int = 2 ** 32 - 1


class SeedArchaeologist:
    """
    Estudia el paisaje del espacio de semillas.

    Genera mapas de fertilidad para identificar regiones donde
    las semillas tienen mayor probabilidad de producir reservorios
    resonantes, reduciendo el tiempo de excavación.

    Ejemplo::

        from core.universal_miner import SeedVault, UniversalMiner
        from core.seed_archaeologist import SeedArchaeologist

        vault = SeedVault()
        # (llenar vault con excavaciones previas)

        arch = SeedArchaeologist(vault, reservoir_size=50)
        landscape = arch.create_landscape_map(n_samples=1000)
        regions = arch.find_fertile_regions()
        print(regions)  # [(1234, 5678), (9000, 11000), ...]
    """

    def __init__(
        self,
        vault: SeedVault,
        reservoir_size: int = 50,
        sparsity: float = 0.1,
        random_state: Optional[int] = None,
    ) -> None:
        """
        Args:
            vault: SeedVault con excavaciones previas (puede estar vacío).
            reservoir_size: Tamaño del reservoir para evaluaciones rápidas.
            sparsity: Esparsidad usada en evaluaciones.
            random_state: Semilla para reproducibilidad del muestreo.
        """
        self.vault = vault
        self.reservoir_size = reservoir_size
        self.sparsity = sparsity
        self._rng = np.random.RandomState(random_state)

        self._landscape: Optional[np.ndarray] = None  # shape (n, 2): [seed, score]
        self._fertile_regions: Optional[List[Tuple[int, int]]] = None

        # Miner interno para evaluaciones rápidas
        self._miner = UniversalMiner(
            reservoir_size=reservoir_size, sparsity=sparsity
        )

    # ─── Evaluación rápida ─────────────────────────────────────────────────

    def _fertility_score(self, seed: int) -> float:
        """
        Calcula la fertilidad de una semilla.

        Fertilidad = 1 / (|radio_espectral - 1.0| + ε)

        Las semillas cuyo radio espectral está cerca de 1.0
        (borde del caos) tienen mayor fertilidad.
        """
        matrix = self._miner.chaos_sample(seed)
        resonance, _ = self._miner.measure_resonance(matrix)
        if not np.isfinite(resonance):
            return 0.0
        return 1.0 / (abs(resonance - 1.0) + _FERTILITY_EPS)

    # ─── Paisaje de fertilidad ──────────────────────────────────────────────

    def create_landscape_map(
        self,
        n_samples: int = 1000,
        seed_range: Optional[Tuple[int, int]] = None,
        verbose: bool = False,
    ) -> np.ndarray:
        """
        Muestrea el espacio de semillas y crea un mapa de fertilidad.

        Args:
            n_samples: Número de semillas a evaluar.
            seed_range: Rango (start, end) a muestrear. Default: [0, 2^32-1].
            verbose: Muestra progreso cada 10% si es True.

        Returns:
            np.ndarray shape (n_samples, 2) con columnas [seed, fertility_score].
            Las filas están ordenadas por seed (ascendente).
        """
        if n_samples < 2:
            raise ValueError("n_samples debe ser >= 2")

        lo, hi = seed_range if seed_range else (0, _SEED_MAX)
        if lo >= hi:
            raise ValueError("seed_range[0] debe ser < seed_range[1]")

        seeds = np.sort(
            self._rng.randint(lo, hi + 1, size=n_samples)
        ).tolist()

        t_start = time.time()
        results = []
        checkpoint = max(1, n_samples // 10)

        for i, seed in enumerate(seeds):
            score = self._fertility_score(seed)
            results.append([float(seed), score])
            if verbose and (i + 1) % checkpoint == 0:
                elapsed = time.time() - t_start
                pct = (i + 1) / n_samples * 100
                print(f"  {pct:.0f}%  [{i + 1}/{n_samples}]  "
                      f"elapsed={elapsed:.1f}s")

        self._landscape = np.array(results, dtype=np.float64)
        self._fertile_regions = None  # invalidar cache
        return self._landscape

    # ─── Regiones fértiles ─────────────────────────────────────────────────

    def find_fertile_regions(
        self,
        threshold_percentile: float = 75.0,
        min_region_size: int = 3,
    ) -> List[Tuple[int, int]]:
        """
        Identifica rangos de semillas prometedores.

        Agrupa semillas con fertilidad por encima del percentil dado
        y devuelve rangos contiguos [inicio, fin].

        Args:
            threshold_percentile: Percentil de fertilidad como umbral (0-100).
            min_region_size: Mínimo de semillas contiguas para formar región.

        Returns:
            Lista de tuplas (seed_start, seed_end) ordenadas por seed_start.
        """
        if self._landscape is None:
            raise RuntimeError(
                "Llama a create_landscape_map() primero."
            )

        seeds = self._landscape[:, 0].astype(np.int64)
        scores = self._landscape[:, 1]

        threshold = float(np.percentile(scores, threshold_percentile))
        above = scores >= threshold

        # Agrupar semillas contiguas (en el array, no en espacio de seeds)
        regions: List[Tuple[int, int]] = []
        in_region = False
        region_start: int = 0
        region_count: int = 0

        for i, flag in enumerate(above):
            if flag:
                if not in_region:
                    in_region = True
                    region_start = i
                    region_count = 1
                else:
                    region_count += 1
            else:
                if in_region:
                    if region_count >= min_region_size:
                        s_start = int(seeds[region_start])
                        s_end = int(seeds[i - 1])
                        regions.append((s_start, s_end))
                    in_region = False
                    region_count = 0

        # Cerrar la última región si termina en el borde
        if in_region and region_count >= min_region_size:
            regions.append((int(seeds[region_start]), int(seeds[-1])))

        self._fertile_regions = regions
        return regions

    # ─── Análisis del vault ─────────────────────────────────────────────────

    def analyze_vault(self) -> dict:
        """
        Analiza las semillas almacenadas en el SeedVault.

        Returns:
            Dict con estadísticas: count, resonance_stats, type_distribution,
            y las 5 mejores semillas por resonancia.
        """
        names = self.vault.list_seeds()
        if not names:
            return {
                "count": 0,
                "resonance_mean": None,
                "resonance_std": None,
                "type_distribution": {},
                "top_5": [],
            }

        entries = [
            (name, self.vault.retrieve(name))
            for name in names
            if self.vault.retrieve(name) is not None
        ]

        resonances = np.array([e.resonance for _, e in entries])
        type_counts: dict = {}
        for _, e in entries:
            key = e.resonance_type.value
            type_counts[key] = type_counts.get(key, 0) + 1

        # Top 5 por resonancia
        sorted_entries = sorted(entries, key=lambda x: x[1].resonance, reverse=True)
        top5 = [
            {"name": name, "seed": e.sacred_seed, "resonance": e.resonance}
            for name, e in sorted_entries[:5]
        ]

        return {
            "count": len(entries),
            "resonance_mean": float(np.mean(resonances)),
            "resonance_std": float(np.std(resonances)),
            "resonance_min": float(np.min(resonances)),
            "resonance_max": float(np.max(resonances)),
            "type_distribution": type_counts,
            "top_5": top5,
        }

    def cluster_by_resonance_type(self) -> dict:
        """
        Agrupa las semillas del vault por tipo de resonancia.

        Returns:
            Dict[ResonanceType.value, List[int]] — semillas por tipo.
        """
        names = self.vault.list_seeds()
        clusters: dict = {}
        for name in names:
            result = self.vault.retrieve(name)
            if result is None:
                continue
            key = result.resonance_type.value
            if key not in clusters:
                clusters[key] = []
            clusters[key].append(result.sacred_seed)
        return clusters

    # ─── Predicción de fertilidad ──────────────────────────────────────────

    def predict_fertility(self, seeds: List[int]) -> np.ndarray:
        """
        Predice la fertilidad de una lista de semillas.

        Args:
            seeds: Lista de semillas a evaluar.

        Returns:
            np.ndarray de shape (len(seeds),) con puntuaciones de fertilidad.
        """
        return np.array([self._fertility_score(s) for s in seeds])

    # ─── Utilidades ────────────────────────────────────────────────────────

    def landscape_statistics(self) -> dict:
        """Estadísticas del mapa de fertilidad actual."""
        if self._landscape is None:
            return {"available": False}

        scores = self._landscape[:, 1]
        return {
            "available": True,
            "n_samples": len(scores),
            "mean": float(np.mean(scores)),
            "std": float(np.std(scores)),
            "min": float(np.min(scores)),
            "max": float(np.max(scores)),
            "p25": float(np.percentile(scores, 25)),
            "p50": float(np.percentile(scores, 50)),
            "p75": float(np.percentile(scores, 75)),
            "p90": float(np.percentile(scores, 90)),
        }

    def summary(self) -> dict:
        """Resumen del estado del arqueólogo."""
        stats = self.landscape_statistics()
        return {
            "vault_size": len(self.vault.list_seeds()),
            "landscape": stats,
            "fertile_regions_found": (
                len(self._fertile_regions)
                if self._fertile_regions is not None
                else None
            ),
            "reservoir_size": self.reservoir_size,
        }
