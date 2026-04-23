"""
Proyecto Eón - Protocolo de Sincronización Cuántica-Simulada
=============================================================

"Dos espejos que se reflejan, sin necesidad de mensajes."

Implementa sincronización "instantánea" entre nodos Eón usando
semillas compartidas en vez de comunicación explícita de estado.

PRINCIPIO:
──────────
Si dos nodos comparten la misma semilla y procesan la misma
secuencia de timestamps, sus estados internos son IDÉNTICOS.
Esto elimina la necesidad de transmitir el estado completo
del reservoir (n² floats) por la red.

En su lugar, solo se intercambia:
  - El timestamp actual (8 bytes)
  - Un hash de verificación (16 bytes)

PROCESO:
────────
1. Los nodos acuerdan una `shared_seed` en el setup inicial
2. En cada epoch, calculan el estado deterministamente desde
   el timestamp usando `chaos_sample(seed ^ epoch ^ timestamp)`
3. Para verificar sincronía, comparan hashes del estado

OVERHEAD: ~24 bytes/sync (vs miles de bytes para transmitir W)

(c) 2024 Proyecto Eón - Jeremy Arias Solano
"""

import numpy as np
import hashlib
import time
import logging
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SyncState:
    """Estado de sincronización de un nodo."""
    epoch: int
    timestamp: int
    state_hash: str              # Hash del estado del reservoir
    state_vector: np.ndarray     # Estado calculado deterministamente
    sync_verified: bool = False  # Si se verificó contra otro nodo

    def to_dict(self) -> Dict:
        return {
            "epoch": self.epoch,
            "timestamp": self.timestamp,
            "state_hash": self.state_hash,
            "sync_verified": self.sync_verified,
        }


@dataclass
class SyncStats:
    """Estadísticas de sincronización."""
    total_syncs: int = 0
    successful_verifications: int = 0
    failed_verifications: int = 0
    bytes_saved: int = 0     # vs transmitir el estado completo
    bytes_sent: int = 0

    @property
    def success_rate(self) -> float:
        total = self.successful_verifications + self.failed_verifications
        return self.successful_verifications / total if total > 0 else 0.0

    def to_dict(self) -> Dict:
        return {
            "total_syncs": self.total_syncs,
            "successful_verifications": self.successful_verifications,
            "failed_verifications": self.failed_verifications,
            "success_rate": round(self.success_rate, 4),
            "bytes_saved": self.bytes_saved,
            "bytes_sent": self.bytes_sent,
        }


def _compute_state_hash(state: np.ndarray) -> str:
    """
    Calcula un hash MD5 del vector de estado.

    Args:
        state: Vector del reservoir (n_reservoir,)

    Returns:
        Hash hexadecimal de 32 caracteres
    """
    # Usar float32 para compatibilidad cross-platform
    state_bytes = state.astype(np.float32).tobytes()
    return hashlib.md5(state_bytes).hexdigest()


class QuantumSyncProtocol:
    """
    Protocolo de sincronización determinista para nodos Eón.

    Usa semillas compartidas para reproducir estados idénticos
    en múltiples nodos sin transmitir el estado completo.

    El nombre "cuántica" es una metáfora: dos nodos con la misma
    semilla están "entrelazados" — si uno calcula su estado, el
    otro puede predecir exactamente cuál es ese estado.

    Ejemplo:
        >>> # En nodo A
        >>> proto_a = QuantumSyncProtocol(shared_seed=42, reservoir_size=100)
        >>> state_a = proto_a.sync_state(epoch=1, timestamp=1700000000)
        >>>
        >>> # En nodo B (mismo shared_seed)
        >>> proto_b = QuantumSyncProtocol(shared_seed=42, reservoir_size=100)
        >>> state_b = proto_b.sync_state(epoch=1, timestamp=1700000000)
        >>>
        >>> # Los estados son idénticos sin ninguna comunicación
        >>> assert np.allclose(state_a.state_vector, state_b.state_vector)
        >>>
        >>> # Verificar sincronía (solo 24 bytes de overhead)
        >>> ok = proto_a.verify_sync(state_a.state_hash, state_b.state_hash)
        >>> assert ok
    """

    # Bytes de overhead por sincronización (epoch + timestamp + hash)
    SYNC_OVERHEAD_BYTES = 8 + 8 + 16  # = 32 bytes

    def __init__(
        self,
        shared_seed: int,
        reservoir_size: int = 100,
        node_id: str = "node_0",
        sparsity: float = 0.1,
    ):
        """
        Inicializa el protocolo.

        Args:
            shared_seed: Semilla compartida entre todos los nodos del cluster
            reservoir_size: Dimensión del reservorio (debe ser la misma en todos los nodos)
            node_id: Identificador único del nodo (para logging)
            sparsity: Densidad de conexiones en el reservoir compartido
        """
        self.shared_seed = int(shared_seed)
        self.reservoir_size = reservoir_size
        self.node_id = node_id
        self.sparsity = sparsity

        self._epoch: int = 0
        self._history: List[SyncState] = []
        self.stats = SyncStats()

    # ─── Generación determinista de estado ────────────────────────────────────

    def _derive_seed(self, epoch: int, timestamp: int) -> int:
        """
        Deriva una semilla de trabajo a partir de shared_seed, epoch y timestamp.

        La derivación es determinista: los mismos inputs producen
        siempre la misma semilla. Todos los nodos con la misma
        shared_seed obtendrán el mismo resultado.

        Args:
            epoch: Número de epoch de sincronización
            timestamp: Timestamp Unix (segundos)

        Returns:
            Semilla derivada (int positivo de 32 bits)
        """
        # Mezcla bit a bit (no usamos hash criptográfico por velocidad)
        combined = self.shared_seed ^ (epoch * 2654435761) ^ (timestamp * 1103515245)
        # Asegurar positivo y 32-bit
        return int(combined & 0x7FFFFFFF)

    def _chaos_sample(self, seed: int) -> np.ndarray:
        """
        Genera un vector de estado deterministico desde una semilla.

        Replica el paradigma de "chaos_sample" del UniversalMiner:
        el estado no se genera — se revela desde la semilla.

        Args:
            seed: Semilla derivada

        Returns:
            Vector de estado normalizado (n_reservoir,)
        """
        rng = np.random.default_rng(seed)
        # Simular activaciones del reservoir: combinación de capas
        W = rng.standard_normal((self.reservoir_size, self.reservoir_size))
        mask = rng.random((self.reservoir_size, self.reservoir_size)) > (1.0 - self.sparsity)
        W *= mask

        # Normalizar radio espectral
        try:
            eigs = np.abs(np.linalg.eigvals(W))
            if eigs.max() > 1e-10:
                W = W * (0.9 / eigs.max())
        except np.linalg.LinAlgError:
            pass

        # Propagar un vector de activación inicial
        x = rng.standard_normal(self.reservoir_size)
        x = x / (np.linalg.norm(x) + 1e-12)
        for _ in range(5):  # Warm-up corto
            x = np.tanh(W @ x)

        return x

    # ─── API pública ──────────────────────────────────────────────────────────

    def sync_state(
        self,
        epoch: Optional[int] = None,
        timestamp: Optional[int] = None,
    ) -> SyncState:
        """
        Calcula el estado sincronizado para un epoch y timestamp dados.

        Si no se proporcionan, usa el epoch interno incrementado y
        el timestamp Unix actual.

        Args:
            epoch: Número de sincronización (None → autoincremento)
            timestamp: Timestamp Unix en segundos (None → ahora)

        Returns:
            SyncState con el vector de estado y su hash
        """
        if epoch is None:
            self._epoch += 1
            epoch = self._epoch
        if timestamp is None:
            timestamp = int(time.time())

        seed = self._derive_seed(epoch, timestamp)
        state_vec = self._chaos_sample(seed)
        state_hash = _compute_state_hash(state_vec)

        s = SyncState(
            epoch=epoch,
            timestamp=timestamp,
            state_hash=state_hash,
            state_vector=state_vec,
        )
        self._history.append(s)
        self.stats.total_syncs += 1

        # Calcular bytes ahorrados vs transmitir estado completo
        full_state_bytes = self.reservoir_size * 4  # float32
        self.stats.bytes_saved += full_state_bytes - self.SYNC_OVERHEAD_BYTES
        self.stats.bytes_sent += self.SYNC_OVERHEAD_BYTES

        logger.debug(
            f"[{self.node_id}] sync_state epoch={epoch} "
            f"timestamp={timestamp} hash={state_hash[:8]}..."
        )
        return s

    def verify_sync(self, local_hash: str, remote_hash: str) -> bool:
        """
        Verifica que dos nodos estén sincronizados comparando hashes.

        No requiere transmitir el vector de estado completo.

        Args:
            local_hash: Hash calculado por este nodo
            remote_hash: Hash recibido del nodo remoto

        Returns:
            True si los hashes coinciden (nodos sincronizados)
        """
        ok = local_hash == remote_hash

        if ok:
            self.stats.successful_verifications += 1
            if self._history:
                self._history[-1].sync_verified = True
        else:
            self.stats.failed_verifications += 1
            logger.warning(
                f"[{self.node_id}] Fallo de sincronización: "
                f"local={local_hash[:8]}... remote={remote_hash[:8]}..."
            )

        return ok

    def sync_payload(
        self,
        epoch: Optional[int] = None,
        timestamp: Optional[int] = None,
    ) -> Dict:
        """
        Genera el payload mínimo de sincronización para transmitir a otro nodo.

        El otro nodo solo necesita este payload para verificar sincronía.

        Returns:
            Diccionario con epoch, timestamp y hash (no incluye el vector de estado)
        """
        state = self.sync_state(epoch=epoch, timestamp=timestamp)
        return {
            "epoch": state.epoch,
            "timestamp": state.timestamp,
            "hash": state.state_hash,
            "node_id": self.node_id,
        }

    def recover_state(self, epoch: int, timestamp: int) -> np.ndarray:
        """
        Recupera el vector de estado para un epoch/timestamp específico.

        Útil para re-sincronizar después de una desconexión.

        Args:
            epoch: Epoch de la sincronización a recuperar
            timestamp: Timestamp de la sincronización

        Returns:
            Vector de estado (n_reservoir,)
        """
        seed = self._derive_seed(epoch, timestamp)
        return self._chaos_sample(seed)

    def history(self, last_n: int = 10) -> List[Dict]:
        """Devuelve los últimos n registros de sincronización."""
        return [s.to_dict() for s in self._history[-last_n:]]

    def summary(self) -> Dict:
        """Resumen del protocolo de sincronización."""
        return {
            "node_id": self.node_id,
            "shared_seed": self.shared_seed,
            "reservoir_size": self.reservoir_size,
            "current_epoch": self._epoch,
            **self.stats.to_dict(),
        }
