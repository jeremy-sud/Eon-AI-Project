"""
Tests para QuantumSyncProtocol - Proyecto Eón
===============================================

Tests del protocolo de sincronización determinista entre nodos.
"""

import pytest
import numpy as np
import sys
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
_phase6_dir = os.path.dirname(_current_dir)
if _phase6_dir not in sys.path:
    sys.path.insert(0, _phase6_dir)

from quantum_sync import (
    QuantumSyncProtocol,
    SyncState,
    SyncStats,
    _compute_state_hash,
)


# ─── Tests de _compute_state_hash ────────────────────────────────────────────

class TestComputeStateHash:
    def test_returns_32_char_hex(self):
        v = np.array([0.1, 0.2, 0.3])
        h = _compute_state_hash(v)
        assert len(h) == 32
        assert all(c in "0123456789abcdef" for c in h)

    def test_same_input_same_hash(self):
        v = np.array([1.0, -1.0, 0.5])
        assert _compute_state_hash(v) == _compute_state_hash(v)

    def test_different_input_different_hash(self):
        v1 = np.array([1.0, 2.0, 3.0])
        v2 = np.array([1.0, 2.0, 3.1])
        assert _compute_state_hash(v1) != _compute_state_hash(v2)


# ─── Tests de construcción ───────────────────────────────────────────────────

class TestConstruction:
    def test_basic_construction(self):
        proto = QuantumSyncProtocol(shared_seed=42, reservoir_size=50)
        assert proto.shared_seed == 42
        assert proto.reservoir_size == 50

    def test_default_node_id(self):
        proto = QuantumSyncProtocol(shared_seed=1, reservoir_size=10)
        assert proto.node_id == "node_0"

    def test_initial_epoch_zero(self):
        proto = QuantumSyncProtocol(shared_seed=1, reservoir_size=10)
        assert proto._epoch == 0

    def test_initial_stats_zero(self):
        proto = QuantumSyncProtocol(shared_seed=1, reservoir_size=10)
        assert proto.stats.total_syncs == 0


# ─── Tests de _derive_seed ───────────────────────────────────────────────────

class TestDeriveSeed:
    def test_deterministic(self):
        proto = QuantumSyncProtocol(shared_seed=42, reservoir_size=10)
        s1 = proto._derive_seed(epoch=5, timestamp=1700000000)
        s2 = proto._derive_seed(epoch=5, timestamp=1700000000)
        assert s1 == s2

    def test_different_epoch_different_seed(self):
        proto = QuantumSyncProtocol(shared_seed=42, reservoir_size=10)
        s1 = proto._derive_seed(epoch=1, timestamp=1700000000)
        s2 = proto._derive_seed(epoch=2, timestamp=1700000000)
        assert s1 != s2

    def test_different_timestamp_different_seed(self):
        proto = QuantumSyncProtocol(shared_seed=42, reservoir_size=10)
        s1 = proto._derive_seed(epoch=1, timestamp=1700000000)
        s2 = proto._derive_seed(epoch=1, timestamp=1700000001)
        assert s1 != s2

    def test_seed_positive(self):
        proto = QuantumSyncProtocol(shared_seed=42, reservoir_size=10)
        for e in range(10):
            s = proto._derive_seed(epoch=e, timestamp=1700000000 + e)
            assert s >= 0

    def test_different_shared_seeds_diverge(self):
        p1 = QuantumSyncProtocol(shared_seed=1, reservoir_size=10)
        p2 = QuantumSyncProtocol(shared_seed=2, reservoir_size=10)
        s1 = p1._derive_seed(epoch=1, timestamp=1000)
        s2 = p2._derive_seed(epoch=1, timestamp=1000)
        assert s1 != s2


# ─── Tests del principio de "entrelazamiento" ────────────────────────────────

class TestEntanglement:
    def test_same_seed_same_state(self):
        """Nodos con la misma semilla producen estados idénticos."""
        proto_a = QuantumSyncProtocol(shared_seed=42, reservoir_size=30)
        proto_b = QuantumSyncProtocol(shared_seed=42, reservoir_size=30)

        state_a = proto_a.sync_state(epoch=1, timestamp=1700000000)
        state_b = proto_b.sync_state(epoch=1, timestamp=1700000000)

        np.testing.assert_array_almost_equal(
            state_a.state_vector, state_b.state_vector
        )

    def test_same_seed_same_hash(self):
        proto_a = QuantumSyncProtocol(shared_seed=99, reservoir_size=20)
        proto_b = QuantumSyncProtocol(shared_seed=99, reservoir_size=20)

        s_a = proto_a.sync_state(epoch=3, timestamp=1000)
        s_b = proto_b.sync_state(epoch=3, timestamp=1000)

        assert s_a.state_hash == s_b.state_hash

    def test_different_seeds_different_states(self):
        proto_a = QuantumSyncProtocol(shared_seed=1, reservoir_size=20)
        proto_b = QuantumSyncProtocol(shared_seed=2, reservoir_size=20)

        s_a = proto_a.sync_state(epoch=1, timestamp=500)
        s_b = proto_b.sync_state(epoch=1, timestamp=500)

        assert s_a.state_hash != s_b.state_hash

    def test_different_epochs_different_states(self):
        proto_a = QuantumSyncProtocol(shared_seed=42, reservoir_size=20)
        proto_b = QuantumSyncProtocol(shared_seed=42, reservoir_size=20)

        s_a = proto_a.sync_state(epoch=1, timestamp=1000)
        s_b = proto_b.sync_state(epoch=2, timestamp=1000)

        assert s_a.state_hash != s_b.state_hash


# ─── Tests de sync_state() ───────────────────────────────────────────────────

class TestSyncState:
    def test_returns_sync_state(self):
        proto = QuantumSyncProtocol(shared_seed=0, reservoir_size=10)
        s = proto.sync_state(epoch=1, timestamp=1000)
        assert isinstance(s, SyncState)

    def test_state_vector_shape(self):
        proto = QuantumSyncProtocol(shared_seed=0, reservoir_size=25)
        s = proto.sync_state(epoch=1, timestamp=1000)
        assert s.state_vector.shape == (25,)

    def test_state_vector_finite(self):
        proto = QuantumSyncProtocol(shared_seed=0, reservoir_size=20)
        s = proto.sync_state(epoch=1, timestamp=1000)
        assert np.isfinite(s.state_vector).all()

    def test_autoincrement_epoch(self):
        proto = QuantumSyncProtocol(shared_seed=0, reservoir_size=10)
        s1 = proto.sync_state()
        s2 = proto.sync_state()
        assert s2.epoch == s1.epoch + 1

    def test_stats_incremented(self):
        proto = QuantumSyncProtocol(shared_seed=0, reservoir_size=10)
        proto.sync_state(epoch=1, timestamp=1000)
        assert proto.stats.total_syncs == 1


# ─── Tests de verify_sync() ──────────────────────────────────────────────────

class TestVerifySync:
    def test_matching_hashes_returns_true(self):
        proto = QuantumSyncProtocol(shared_seed=42, reservoir_size=20)
        s = proto.sync_state(epoch=1, timestamp=1000)
        assert proto.verify_sync(s.state_hash, s.state_hash) is True

    def test_mismatching_hashes_returns_false(self):
        proto = QuantumSyncProtocol(shared_seed=42, reservoir_size=20)
        s = proto.sync_state(epoch=1, timestamp=1000)
        assert proto.verify_sync(s.state_hash, "deadbeef" * 4) is False

    def test_success_counter_incremented(self):
        proto = QuantumSyncProtocol(shared_seed=42, reservoir_size=20)
        s = proto.sync_state(epoch=1, timestamp=1000)
        proto.verify_sync(s.state_hash, s.state_hash)
        assert proto.stats.successful_verifications == 1

    def test_failure_counter_incremented(self):
        proto = QuantumSyncProtocol(shared_seed=42, reservoir_size=20)
        s = proto.sync_state(epoch=1, timestamp=1000)
        proto.verify_sync(s.state_hash, "wrong" * 6 + "00")
        assert proto.stats.failed_verifications == 1

    def test_cross_node_verification(self):
        """Dos nodos con la misma seed verifican correctamente."""
        a = QuantumSyncProtocol(shared_seed=7, reservoir_size=20, node_id="A")
        b = QuantumSyncProtocol(shared_seed=7, reservoir_size=20, node_id="B")

        epoch, ts = 5, 1700100000
        sa = a.sync_state(epoch=epoch, timestamp=ts)
        sb = b.sync_state(epoch=epoch, timestamp=ts)

        assert a.verify_sync(sa.state_hash, sb.state_hash) is True


# ─── Tests de sync_payload() ─────────────────────────────────────────────────

class TestSyncPayload:
    def test_payload_keys(self):
        proto = QuantumSyncProtocol(shared_seed=0, reservoir_size=10)
        payload = proto.sync_payload(epoch=1, timestamp=500)
        assert {"epoch", "timestamp", "hash", "node_id"}.issubset(set(payload.keys()))

    def test_payload_no_state_vector(self):
        """El payload mínimo no incluye el vector de estado completo."""
        proto = QuantumSyncProtocol(shared_seed=0, reservoir_size=10)
        payload = proto.sync_payload(epoch=1, timestamp=500)
        assert "state_vector" not in payload

    def test_payload_hash_matches_sync_state(self):
        proto_a = QuantumSyncProtocol(shared_seed=77, reservoir_size=15)
        proto_b = QuantumSyncProtocol(shared_seed=77, reservoir_size=15)

        payload_a = proto_a.sync_payload(epoch=2, timestamp=9999)
        sb = proto_b.sync_state(epoch=2, timestamp=9999)

        assert payload_a["hash"] == sb.state_hash


# ─── Tests de recover_state() ────────────────────────────────────────────────

class TestRecoverState:
    def test_recover_matches_original(self):
        proto = QuantumSyncProtocol(shared_seed=42, reservoir_size=20)
        s = proto.sync_state(epoch=3, timestamp=1234)
        recovered = proto.recover_state(epoch=3, timestamp=1234)
        np.testing.assert_array_almost_equal(s.state_vector, recovered)

    def test_recover_shape(self):
        proto = QuantumSyncProtocol(shared_seed=1, reservoir_size=15)
        v = proto.recover_state(epoch=1, timestamp=100)
        assert v.shape == (15,)


# ─── Tests de overhead ────────────────────────────────────────────────────────

class TestOverhead:
    def test_bytes_saved_positive(self):
        proto = QuantumSyncProtocol(shared_seed=42, reservoir_size=100)
        proto.sync_state(epoch=1, timestamp=1000)
        assert proto.stats.bytes_saved > 0

    def test_bytes_sent_is_overhead(self):
        proto = QuantumSyncProtocol(shared_seed=42, reservoir_size=100)
        proto.sync_state(epoch=1, timestamp=1000)
        assert proto.stats.bytes_sent == QuantumSyncProtocol.SYNC_OVERHEAD_BYTES

    def test_overhead_vs_full_state(self):
        """El overhead debe ser menor que transmitir el estado completo."""
        n = 100
        proto = QuantumSyncProtocol(shared_seed=42, reservoir_size=n)
        proto.sync_state(epoch=1, timestamp=1000)
        full_state_bytes = n * 4  # float32
        assert QuantumSyncProtocol.SYNC_OVERHEAD_BYTES < full_state_bytes


# ─── Tests de summary() e history() ─────────────────────────────────────────

class TestSummaryAndHistory:
    def test_summary_keys(self):
        proto = QuantumSyncProtocol(shared_seed=0, reservoir_size=10, node_id="test")
        s = proto.summary()
        assert "node_id" in s
        assert "shared_seed" in s
        assert "current_epoch" in s

    def test_history_length(self):
        proto = QuantumSyncProtocol(shared_seed=0, reservoir_size=10)
        for i in range(5):
            proto.sync_state(epoch=i + 1, timestamp=1000 + i)
        h = proto.history(last_n=3)
        assert len(h) == 3

    def test_history_epoch_order(self):
        proto = QuantumSyncProtocol(shared_seed=0, reservoir_size=10)
        for i in range(1, 4):
            proto.sync_state(epoch=i, timestamp=1000 + i)
        h = proto.history(last_n=10)
        epochs = [item["epoch"] for item in h]
        assert epochs == sorted(epochs)
