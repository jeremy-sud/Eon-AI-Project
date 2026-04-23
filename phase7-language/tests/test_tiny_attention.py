"""
Tests para TinyAttention — Mecanismo de Atención Ultra-Ligero

Cubre: construcción, forward(), atención causal, pesos de atención,
       memoria, summary y AttentionTinyLMv2.
"""
import math
import sys
import os
from pathlib import Path

import pytest
import numpy as np

# ─── Path setup ─────────────────────────────────────────────────────────────
_tests_dir = Path(__file__).parent
_language_dir = _tests_dir.parent
sys.path.insert(0, str(_language_dir))

from tiny_attention import TinyAttention, AttentionTinyLMv2


# ════════════════════════════════════════════════════════════
#  Fixtures
# ════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def attn():
    return TinyAttention(dim=16, random_state=42)


@pytest.fixture(scope="module")
def seq_input():
    rng = np.random.RandomState(0)
    return rng.randn(8, 16)  # 8 tokens, dim=16


# ════════════════════════════════════════════════════════════
#  Construcción
# ════════════════════════════════════════════════════════════

class TestInit:
    def test_default_dim(self):
        a = TinyAttention()
        assert a.dim == 32

    def test_custom_dim(self):
        a = TinyAttention(dim=64)
        assert a.dim == 64

    def test_invalid_dim(self):
        with pytest.raises(ValueError, match="dim"):
            TinyAttention(dim=0)

    def test_invalid_init_scale(self):
        with pytest.raises(ValueError, match="init_scale"):
            TinyAttention(init_scale=-0.1)

    def test_wq_shape(self, attn):
        assert attn.W_q.shape == (16, 16)

    def test_wk_shape(self, attn):
        assert attn.W_k.shape == (16, 16)

    def test_wv_shape(self, attn):
        assert attn.W_v.shape == (16, 16)

    def test_reproducible(self):
        a1 = TinyAttention(dim=8, random_state=1)
        a2 = TinyAttention(dim=8, random_state=1)
        assert np.allclose(a1.W_q, a2.W_q)

    def test_different_seeds_differ(self):
        a1 = TinyAttention(dim=8, random_state=1)
        a2 = TinyAttention(dim=8, random_state=2)
        assert not np.allclose(a1.W_q, a2.W_q)

    def test_scale_is_sqrt_dim(self, attn):
        assert math.isclose(attn._scale, math.sqrt(16), rel_tol=1e-9)


# ════════════════════════════════════════════════════════════
#  forward()
# ════════════════════════════════════════════════════════════

class TestForward:
    def test_output_shape_sequence(self, attn, seq_input):
        out = attn.forward(seq_input)
        assert out.shape == seq_input.shape

    def test_output_finite(self, attn, seq_input):
        out = attn.forward(seq_input)
        assert np.all(np.isfinite(out))

    def test_single_token_input(self, attn):
        x = np.ones(16)
        out = attn.forward(x)
        assert out.shape == (16,)

    def test_wrong_dim_raises(self, attn):
        with pytest.raises(ValueError, match="dimensi"):
            attn.forward(np.ones((5, 8)))

    def test_3d_input_raises(self, attn):
        with pytest.raises(ValueError):
            attn.forward(np.ones((2, 3, 16)))

    def test_output_not_equal_input(self, attn, seq_input):
        """La atención debe transformar la entrada."""
        out = attn.forward(seq_input)
        assert not np.allclose(out, seq_input)

    def test_output_varies_across_tokens(self, attn):
        """Tokens diferentes deben producir salidas diferentes."""
        x = np.eye(16)   # 16 tokens ortogonales
        out = attn.forward(x)
        # No todos los tokens deben tener la misma salida
        assert not np.allclose(out[0], out[1])


# ════════════════════════════════════════════════════════════
#  Atención causal
# ════════════════════════════════════════════════════════════

class TestCausal:
    def test_causal_flag(self):
        a = TinyAttention(dim=8, causal=True, random_state=0)
        assert a.causal is True

    def test_causal_output_shape(self):
        a = TinyAttention(dim=8, causal=True, random_state=0)
        x = np.random.randn(5, 8)
        out = a.forward(x)
        assert out.shape == (5, 8)

    def test_causal_mask_lower_triangular(self):
        a = TinyAttention(dim=8, causal=True, random_state=0)
        mask = a._causal_mask(4)
        # Los elementos superiores deben ser -inf (aprox -1e9)
        assert mask[0, 1] < -1e8
        # Los elementos diagonales e inferiores deben ser 0
        assert mask[1, 1] == 0.0
        assert mask[2, 0] == 0.0

    def test_causal_vs_noncausal_differ(self):
        rng = np.random.RandomState(0)
        x = rng.randn(6, 8)
        a_causal = TinyAttention(dim=8, causal=True, random_state=5)
        a_noncausal = TinyAttention(dim=8, causal=False, random_state=5)
        out_c = a_causal.forward(x)
        out_n = a_noncausal.forward(x)
        assert not np.allclose(out_c, out_n)


# ════════════════════════════════════════════════════════════
#  attention_weights()
# ════════════════════════════════════════════════════════════

class TestAttentionWeights:
    def test_weights_shape(self, attn, seq_input):
        weights = attn.attention_weights(seq_input)
        seq_len = seq_input.shape[0]
        assert weights.shape == (seq_len, seq_len)

    def test_weights_sum_to_one(self, attn, seq_input):
        weights = attn.attention_weights(seq_input)
        row_sums = weights.sum(axis=-1)
        assert np.allclose(row_sums, 1.0, atol=1e-5)

    def test_weights_non_negative(self, attn, seq_input):
        weights = attn.attention_weights(seq_input)
        assert np.all(weights >= 0)


# ════════════════════════════════════════════════════════════
#  Softmax
# ════════════════════════════════════════════════════════════

class TestSoftmax:
    def test_softmax_sums_to_one(self, attn):
        x = np.array([[1.0, 2.0, 3.0], [0.0, -1.0, 2.0]])
        result = attn._softmax(x)
        assert np.allclose(result.sum(axis=-1), 1.0)

    def test_softmax_non_negative(self, attn):
        x = np.random.randn(5, 5)
        assert np.all(attn._softmax(x) >= 0)

    def test_softmax_large_values_stable(self, attn):
        """Debe manejar valores grandes sin overflow."""
        x = np.array([[1000.0, 1001.0, 999.0]])
        result = attn._softmax(x)
        assert np.all(np.isfinite(result))


# ════════════════════════════════════════════════════════════
#  Memoria y summary
# ════════════════════════════════════════════════════════════

class TestMemory:
    def test_memory_bytes_positive(self, attn):
        assert attn.memory_bytes() > 0

    def test_memory_bytes_formula(self, attn):
        expected = 3 * 16 * 16 * 8  # 3 matrices float64 de 16×16
        assert attn.memory_bytes() == expected

    def test_summary_keys(self, attn):
        s = attn.summary()
        assert "dim" in s
        assert "parameters" in s
        assert "memory_bytes" in s
        assert "memory_kb" in s

    def test_summary_parameters(self, attn):
        s = attn.summary()
        assert s["parameters"] == 3 * 16 * 16

    def test_summary_dim(self, attn):
        assert attn.summary()["dim"] == 16
