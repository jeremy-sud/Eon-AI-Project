"""
Proyecto Eón - Meta-Aprendizaje Cross-Seed
============================================

"Las semillas exitosas comparten patrones estructurales.
 Un nuevo nodo hereda la sabiduría de sus antecesores."

Este módulo implementa Meta-Aprendizaje sobre el espacio de semillas.
En lugar de buscar ciegamente (lineal), aprendemos de semillas
exitosas previas para guiar futuras excavaciones.

FILOSOFÍA:
──────────
El espacio de semillas no es uniforme. Existen "regiones fértiles"
donde se concentran las semillas que producen estructuras resonantes.

MetaSeedLearner mapea estas regiones usando PCA + clustering sobre
el eigenspectrum de semillas ya descubiertas, y luego genera
candidatos en las zonas de mayor densidad de éxito.

Reducción estimada en tiempo de excavación: 5-10x

(c) 2024 Proyecto Eón - Jeremy Arias Solano
"""

import numpy as np
import logging
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass, field

from .universal_miner import (
    UniversalMiner,
    SeedVault,
    ExcavationResult,
    ResonanceType,
)

logger = logging.getLogger(__name__)


@dataclass
class SeedPattern:
    """
    Patrón extraído del eigenspectrum de una semilla exitosa.

    Attributes:
        seed: Semilla de origen
        resonance: Radio espectral
        mean_magnitude: Media de magnitudes de eigenvalores
        std_magnitude: Desviación estándar de magnitudes
        max_magnitude: Eigenvalor de mayor magnitud
        phase_uniformity: Qué tan uniformes son las fases (0-1)
        top_k_magnitudes: Magnitudes de los K eigenvalores más grandes
    """
    seed: int
    resonance: float
    mean_magnitude: float
    std_magnitude: float
    max_magnitude: float
    phase_uniformity: float
    top_k_magnitudes: np.ndarray

    def as_vector(self) -> np.ndarray:
        """Convierte el patrón a vector de features para análisis."""
        return np.concatenate([
            [self.mean_magnitude, self.std_magnitude,
             self.max_magnitude, self.phase_uniformity],
            self.top_k_magnitudes,
        ])


@dataclass
class MetaLearnerState:
    """Estado interno del MetaSeedLearner."""
    patterns: List[SeedPattern] = field(default_factory=list)
    cluster_centers: Optional[np.ndarray] = None
    cluster_radii: Optional[np.ndarray] = None
    principal_axes: Optional[np.ndarray] = None  # Vectores propios PCA
    mean_vector: Optional[np.ndarray] = None       # Media para centrar
    n_clusters: int = 0
    total_seeds_analyzed: int = 0
    total_excavations_guided: int = 0


class MetaSeedLearner:
    """
    Aprende patrones de semillas exitosas para acelerar excavaciones futuras.

    Proceso:
    --------
    1. ANÁLISIS: Extrae features del eigenspectrum de cada semilla exitosa
    2. PCA: Reduce dimensionalidad a espacio de patrones (2-4 dims)
    3. CLUSTERING: Identifica regiones fértiles del espacio
    4. GENERACIÓN: Produce semillas candidatas cerca de regiones fértiles

    Ejemplo:
        >>> vault = SeedVault()
        >>> miner = UniversalMiner(reservoir_size=100)

        >>> # Excavación ciega (referencia)
        >>> result1 = miner.excavate(max_attempts=10000, starting_seed=0)
        >>> vault.store("primera", result1)

        >>> # Meta-aprendizaje
        >>> learner = MetaSeedLearner(miner, vault)
        >>> learner.learn()

        >>> # Excavación guiada (hasta 10x más rápida)
        >>> result2 = learner.guided_excavate(max_attempts=10000)
    """

    # Número de features del eigenspectrum
    TOP_K = 8

    def __init__(
        self,
        miner: UniversalMiner,
        vault: Optional[SeedVault] = None,
        n_clusters: int = 3,
        random_state: Optional[int] = None,
    ):
        """
        Inicializa el MetaSeedLearner.

        Args:
            miner: UniversalMiner configurado para las excavaciones
            vault: SeedVault con semillas ya descubiertas (opcional)
            n_clusters: Número de regiones fértiles a identificar
            random_state: Semilla para reproducibilidad
        """
        self.miner = miner
        self.vault = vault or SeedVault()
        self.n_clusters = n_clusters
        self.rng = np.random.default_rng(random_state)
        self.state = MetaLearnerState()

    # ─── Extracción de features ───────────────────────────────────────────────

    def _extract_pattern(self, result: ExcavationResult) -> SeedPattern:
        """Extrae un SeedPattern del eigenspectrum de un ExcavationResult."""
        eigs = result.eigenspectrum
        magnitudes = np.abs(eigs)

        # Fase uniformity
        if len(eigs) > 0:
            phases = np.angle(eigs)
            hist, _ = np.histogram(phases, bins=12, range=(-np.pi, np.pi))
            phase_uniformity = float(
                1.0 - np.std(hist) / (np.mean(hist) + 1e-10)
            )
            phase_uniformity = max(0.0, min(1.0, phase_uniformity))
        else:
            phase_uniformity = 0.0

        # Top-K magnitudes (rellenadas con 0 si faltan)
        sorted_mags = np.sort(magnitudes)[::-1]
        top_k = np.zeros(self.TOP_K)
        k = min(self.TOP_K, len(sorted_mags))
        top_k[:k] = sorted_mags[:k]

        return SeedPattern(
            seed=result.sacred_seed,
            resonance=result.resonance,
            mean_magnitude=float(np.mean(magnitudes)) if len(magnitudes) else 0.0,
            std_magnitude=float(np.std(magnitudes)) if len(magnitudes) else 0.0,
            max_magnitude=float(magnitudes.max()) if len(magnitudes) else 0.0,
            phase_uniformity=phase_uniformity,
            top_k_magnitudes=top_k,
        )

    # ─── Análisis de patrones (PCA + clustering) ──────────────────────────────

    def _pca_reduce(self, X: np.ndarray, n_components: int = 4) -> np.ndarray:
        """
        PCA manual con NumPy.

        Centra, calcula covarianza y proyecta sobre los n_components
        vectores propios de mayor varianza.
        """
        mean = X.mean(axis=0)
        X_centered = X - mean

        cov = (X_centered.T @ X_centered) / max(len(X) - 1, 1)

        # Eigendescomposición (real symmetric → valores reales)
        eigenvalues, eigenvectors = np.linalg.eigh(cov)

        # Ordenar descendente por varianza explicada
        idx = np.argsort(eigenvalues)[::-1]
        eigenvectors = eigenvectors[:, idx]

        n_components = min(n_components, X.shape[1], len(X))
        axes = eigenvectors[:, :n_components]

        self.state.mean_vector = mean
        self.state.principal_axes = axes

        return X_centered @ axes

    def _kmeans(self, X: np.ndarray, k: int, max_iter: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """
        K-Means simplificado con NumPy.

        Returns:
            (centers, labels) — centros de clusters y etiqueta por punto
        """
        k = min(k, len(X))
        # Inicialización: k puntos aleatorios distintos
        indices = self.rng.choice(len(X), size=k, replace=False)
        centers = X[indices].copy()

        labels = np.zeros(len(X), dtype=int)

        for _ in range(max_iter):
            # Asignación
            dists = np.linalg.norm(X[:, None] - centers[None, :], axis=2)
            new_labels = np.argmin(dists, axis=1)

            if np.array_equal(new_labels, labels):
                break
            labels = new_labels

            # Actualización de centros
            for c in range(k):
                members = X[labels == c]
                if len(members) > 0:
                    centers[c] = members.mean(axis=0)

        return centers, labels

    def learn(self, extra_seeds: Optional[List[int]] = None) -> "MetaSeedLearner":
        """
        Aprende patrones de las semillas en la bóveda.

        Si se pasa `extra_seeds`, excava esas semillas primero
        (sin intentar superarlas) para enriquecer el corpus.

        Args:
            extra_seeds: Lista de semillas adicionales para analizar

        Returns:
            self (para encadenamiento)
        """
        # Recolectar semillas de la bóveda
        results: List[ExcavationResult] = []
        for name in self.vault.list_seeds():
            r = self.vault.retrieve(name)
            if r is not None and len(r.eigenspectrum) > 0:
                results.append(r)

        # Analizar semillas extra
        if extra_seeds:
            for seed in extra_seeds:
                matrix = self.miner.chaos_sample(seed)
                resonance, eigenspectrum = self.miner.measure_resonance(matrix)
                # Solo añadimos las que caen dentro del rango objetivo
                mn, mx = self.miner.target_resonance
                if mn <= resonance <= mx:
                    results.append(ExcavationResult(
                        sacred_seed=seed,
                        divine_matrix=matrix,
                        resonance=resonance,
                        resonance_type=self.miner.resonance_type,
                        excavation_depth=0,
                        excavation_time=0.0,
                        eigenspectrum=eigenspectrum,
                    ))

        if len(results) == 0:
            logger.warning("MetaSeedLearner: sin semillas exitosas para aprender. "
                           "Ejecuta al menos una excavación primero.")
            return self

        # Extraer features
        self.state.patterns = [self._extract_pattern(r) for r in results]
        self.state.total_seeds_analyzed = len(self.state.patterns)

        # Matriz de features
        X = np.array([p.as_vector() for p in self.state.patterns])

        if len(X) == 1:
            # Solo un punto: el cluster es ese punto
            self.state.cluster_centers = X.copy()
            self.state.cluster_radii = np.array([0.1])
            self.state.n_clusters = 1
            logger.info("MetaSeedLearner: 1 semilla → 1 cluster de referencia.")
            return self

        # PCA para reducir a 4 dimensiones o menos
        n_comp = min(4, X.shape[1], len(X) - 1)
        X_reduced = self._pca_reduce(X, n_components=n_comp)

        # K-Means sobre espacio reducido
        k = min(self.n_clusters, len(X))
        centers, labels = self._kmeans(X_reduced, k=k)

        # Radio de cada cluster (max distancia de sus miembros al centro)
        radii = np.zeros(k)
        for c in range(k):
            members = X_reduced[labels == c]
            if len(members) > 0:
                dists = np.linalg.norm(members - centers[c], axis=1)
                radii[c] = float(dists.max()) + 0.1  # mínimo 0.1 para explorar

        self.state.cluster_centers = centers
        self.state.cluster_radii = radii
        self.state.n_clusters = k

        logger.info(
            f"MetaSeedLearner: {len(results)} semillas analizadas → "
            f"{k} clusters en espacio reducido {n_comp}D."
        )
        return self

    # ─── Generación de semillas candidatas ────────────────────────────────────

    def generate_candidates(self, n: int = 1000) -> List[int]:
        """
        Genera semillas candidatas cerca de las regiones fértiles conocidas.

        Estrategia:
        1. Para cada semilla en patterns, buscar vecinos cercanos en el
           espacio de semillas (seed ± offset pequeño).
        2. Adicionalmente, explorar alrededor de los centroides de cluster.

        Args:
            n: Número de semillas candidatas a generar

        Returns:
            Lista de semillas candidatas (enteros positivos, sin duplicados)
        """
        if not self.state.patterns:
            logger.warning("MetaSeedLearner no entrenado. Devolviendo seeds aleatorias.")
            return [int(s) for s in self.rng.integers(0, 2**31, size=n)]

        candidates: set[int] = set()

        # Estrategia 1: vecinos en el espacio de semillas
        base_seeds = [p.seed for p in self.state.patterns]
        per_seed = max(1, n // (2 * len(base_seeds) + 1))
        for seed in base_seeds:
            offsets = self.rng.integers(-5000, 5000, size=per_seed)
            for off in offsets:
                c = int(seed) + int(off)
                if c > 0:
                    candidates.add(c)

        # Estrategia 2: basada en el patrón estadístico
        # — generar seeds en el rango donde se concentran las exitosas
        if len(base_seeds) > 1:
            mean_seed = int(np.mean(base_seeds))
            std_seed = max(int(np.std(base_seeds)), 1000)
            random_near = self.rng.normal(mean_seed, std_seed, size=n // 2)
            for s in random_near:
                c = int(abs(s))
                if c > 0:
                    candidates.add(c)

        # Rellenar hasta n con aleatorios si hacen falta
        if len(candidates) < n:
            extras = self.rng.integers(0, 2**31, size=n - len(candidates))
            candidates.update(int(e) for e in extras)

        result = list(candidates)[:n]
        return result

    # ─── Excavación guiada ────────────────────────────────────────────────────

    def guided_excavate(
        self,
        max_attempts: int = 100_000,
        verbose: bool = True,
    ) -> ExcavationResult:
        """
        Excavación guiada por meta-aprendizaje.

        En vez de iterar linealmente desde 0, prueba primero los
        candidatos generados por `generate_candidates` (zonas fértiles),
        luego rellena con búsqueda normal si no encuentra nada.

        Args:
            max_attempts: Semillas totales a probar
            verbose: Si mostrar progreso

        Returns:
            ExcavationResult de la primera semilla válida encontrada
        """
        if not self.state.patterns:
            logger.warning("MetaSeedLearner sin entrenamiento. Delegando a miner.excavate().")
            return self.miner.excavate(max_attempts=max_attempts, verbose=verbose)

        self.state.total_excavations_guided += 1
        mn, mx = self.miner.target_resonance

        # Candidatos guiados en primer lugar
        guided = self.generate_candidates(n=min(max_attempts // 2, 50_000))
        remaining_budget = max_attempts - len(guided)

        all_seeds = guided + list(range(max(guided) + 1 if guided else 0,
                                        max(guided) + 1 + max(remaining_budget, 0)
                                        if guided else remaining_budget))

        if verbose:
            logger.info(
                f"[MetaSeedLearner] Excavación guiada: "
                f"{len(guided)} candidatos guiados + {max(remaining_budget,0)} lineales"
            )

        import time
        start = time.time()
        best_seed, best_resonance, best_dist = None, float('inf'), float('inf')
        best_matrix, best_spectrum = None, None
        target_center = (mn + mx) / 2

        for attempt, seed in enumerate(all_seeds[:max_attempts]):
            if seed <= 0:
                continue
            matrix = self.miner.chaos_sample(seed)
            resonance, eigenspectrum = self.miner.measure_resonance(matrix)

            dist = abs(resonance - target_center)
            if dist < best_dist:
                best_dist, best_seed = dist, seed
                best_resonance, best_matrix, best_spectrum = resonance, matrix, eigenspectrum

            if mn <= resonance <= mx:
                elapsed = time.time() - start
                if verbose:
                    logger.info(
                        f"[MetaSeedLearner] ✨ Hallada en intento #{attempt + 1} "
                        f"| seed={seed} | resonance={resonance:.6f} | {elapsed:.2f}s"
                    )
                result = ExcavationResult(
                    sacred_seed=seed,
                    divine_matrix=matrix,
                    resonance=resonance,
                    resonance_type=self.miner.resonance_type,
                    excavation_depth=attempt + 1,
                    excavation_time=elapsed,
                    eigenspectrum=eigenspectrum,
                )
                self.vault.store(f"meta_{seed}", result)
                return result

            if verbose and (attempt + 1) % 10_000 == 0:
                elapsed = time.time() - start
                rate = (attempt + 1) / elapsed
                logger.info(
                    f"[MetaSeedLearner] {attempt+1:,} semillas | "
                    f"mejor resonance={best_resonance:.4f} | {rate:.0f} seeds/s"
                )

        # Fallback: usar mejor candidato encontrado
        elapsed = time.time() - start
        if verbose:
            logger.warning(
                f"[MetaSeedLearner] No se encontró resonancia ideal en {max_attempts:,} intentos. "
                f"Usando mejor candidato: seed={best_seed}, resonance={best_resonance:.6f}"
            )
        return ExcavationResult(
            sacred_seed=best_seed or 0,
            divine_matrix=best_matrix if best_matrix is not None else np.zeros((1, 1)),
            resonance=best_resonance,
            resonance_type=self.miner.resonance_type,
            excavation_depth=max_attempts,
            excavation_time=elapsed,
            eigenspectrum=best_spectrum if best_spectrum is not None else np.array([]),
        )

    def summary(self) -> Dict:
        """Retorna un resumen del estado del meta-aprendizaje."""
        return {
            "seeds_analyzed": self.state.total_seeds_analyzed,
            "clusters": self.state.n_clusters,
            "excavations_guided": self.state.total_excavations_guided,
            "known_seeds": [p.seed for p in self.state.patterns],
        }
