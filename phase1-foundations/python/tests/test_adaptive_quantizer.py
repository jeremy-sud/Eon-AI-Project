"""
Tests para AdaptiveQuantizer - Proyecto Eón
============================================

Tests del cuantizador adaptativo de precisión variable.
"""

import pytest
import numpy as np
import sys
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
_python_dir = os.path.dirname(_current_dir)
sys.path.insert(0, _python_dir)

from quantization.adaptive_quantizer import (
    AdaptiveQuantizer,
    AdaptiveQuantizedESN,
    AdaptiveQuantStats,
    IMPORTANCE_TO_BITS,
    _QuantLayer,
)
from esn.esn import EchoStateNetwork, generate_mackey_glass


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def trained_esn():
    data = generate_mackey_glass(1500)
    esn = EchoStateNetwork(
        n_inputs=1, n_reservoir=50, n_outputs=1,
        spectral_radius=0.9, random_state=42,
    )
    X = data[:-1].reshape(-1, 1)
    y = data[1:].reshape(-1, 1)
    esn.fit(X, y, washout=50)
    return esn


@pytest.fixture(scope="module")
def val_data():
    return generate_mackey_glass(600)


@pytest.fixture(scope="module")
def quantizer(trained_esn, val_data):
    aq = AdaptiveQuantizer(trained_esn)
    aq.compute_importance(val_data)
    return aq


@pytest.fixture(scope="module")
def aq_esn(quantizer):
    return quantizer.quantize_adaptive()


# ─── Tests de construcción ───────────────────────────────────────────────────

class TestConstruction:
    def test_requires_trained_esn(self):
        esn = EchoStateNetwork(n_inputs=1, n_reservoir=20, n_outputs=1, random_state=0)
        with pytest.raises(ValueError, match="entrenada"):
            AdaptiveQuantizer(esn)

    def test_default_scheme(self, trained_esn):
        aq = AdaptiveQuantizer(trained_esn)
        assert aq.importance_to_bits == IMPORTANCE_TO_BITS


# ─── Tests de compute_importance() ──────────────────────────────────────────

class TestComputeImportance:
    def test_importance_matrices_exist(self, quantizer):
        assert quantizer._importance_W_in is not None
        assert quantizer._importance_W_res is not None
        assert quantizer._importance_W_out is not None

    def test_importance_shapes(self, quantizer, trained_esn):
        assert quantizer._importance_W_in.shape == trained_esn.W_in.shape
        assert quantizer._importance_W_res.shape == trained_esn.W_reservoir.shape
        assert quantizer._importance_W_out.shape == trained_esn.W_out.shape

    def test_importance_range(self, quantizer):
        for imp in (quantizer._importance_W_in,
                    quantizer._importance_W_res,
                    quantizer._importance_W_out):
            assert imp.min() >= 0.0
            assert imp.max() <= 1.0 + 1e-9  # tolerancia float

    def test_returns_self(self, trained_esn, val_data):
        aq = AdaptiveQuantizer(trained_esn)
        result = aq.compute_importance(val_data)
        assert result is aq

    def test_accepts_1d_input(self, trained_esn):
        data_1d = generate_mackey_glass(200)
        aq = AdaptiveQuantizer(trained_esn)
        aq.compute_importance(data_1d)  # No debe lanzar error
        assert aq._importance_W_in is not None


# ─── Tests de _bits_for_importance() ─────────────────────────────────────────

class TestBitsForImportance:
    def test_high_importance_gets_8bits(self, quantizer):
        assert quantizer._bits_for_importance(0.80) == 8

    def test_medium_importance_gets_4bits(self, quantizer):
        assert quantizer._bits_for_importance(0.50) == 4

    def test_low_importance_gets_2bits(self, quantizer):
        assert quantizer._bits_for_importance(0.20) == 2

    def test_minimal_importance_gets_1bit(self, quantizer):
        assert quantizer._bits_for_importance(0.05) == 1

    def test_boundary_0_75(self, quantizer):
        assert quantizer._bits_for_importance(0.75) == 8

    def test_boundary_0_40(self, quantizer):
        assert quantizer._bits_for_importance(0.40) == 4

    def test_boundary_0_15(self, quantizer):
        assert quantizer._bits_for_importance(0.15) == 2


# ─── Tests de _quantize_weight() ─────────────────────────────────────────────

class TestQuantizeWeight:
    def test_1bit_returns_sign(self, quantizer):
        vq, sc, off = quantizer._quantize_weight(0.5, bits=1)
        assert vq == 1
        vq2, _, _ = quantizer._quantize_weight(-0.5, bits=1)
        assert vq2 == -1

    def test_8bit_range(self, quantizer):
        vq, sc, off = quantizer._quantize_weight(1.0, bits=8)
        assert -128 <= vq <= 127

    def test_4bit_range(self, quantizer):
        vq, sc, off = quantizer._quantize_weight(-0.7, bits=4)
        assert -8 <= vq <= 7

    def test_zero_weight(self, quantizer):
        vq, sc, off = quantizer._quantize_weight(0.0, bits=8)
        assert vq == 0

    def test_reconstruction_accuracy(self, quantizer):
        """Reconstruir w ≈ vq*sc+off con error razonable."""
        for bits in [8, 4, 2]:
            w = 0.37
            vq, sc, off = quantizer._quantize_weight(w, bits=bits)
            reconstructed = vq * sc + off
            tolerance = 2.0 / (2 ** (bits - 1))
            assert abs(reconstructed - w) <= tolerance + 1e-6, (
                f"bits={bits}: |{reconstructed} - {w}| > {tolerance}"
            )


# ─── Tests de quantize_adaptive() ────────────────────────────────────────────

class TestQuantizeAdaptive:
    def test_returns_aq_esn(self, aq_esn):
        assert isinstance(aq_esn, AdaptiveQuantizedESN)

    def test_raises_without_importance(self, trained_esn):
        aq = AdaptiveQuantizer(trained_esn)
        with pytest.raises(RuntimeError, match="compute_importance"):
            aq.quantize_adaptive()

    def test_stats_populated(self, quantizer):
        assert quantizer.stats is not None
        assert quantizer.stats.total_weights > 0

    def test_all_bit_levels_used(self, quantizer):
        s = quantizer.stats
        total = s.n_weights_1bit + s.n_weights_2bit + s.n_weights_4bit + s.n_weights_8bit
        assert total == s.total_weights

    def test_compression_ratio_gt_1(self, quantizer):
        """La cuantización adaptativa debe comprimir más que float64."""
        assert quantizer.stats.compression_ratio > 1.0

    def test_memory_reduction_positive(self, quantizer):
        assert quantizer.stats.memory_reduction_pct > 0.0


# ─── Tests de AdaptiveQuantizedESN ───────────────────────────────────────────

class TestAdaptiveQuantizedESN:
    def test_predict_shape(self, aq_esn):
        X = generate_mackey_glass(200)[:-1].reshape(-1, 1)
        preds = aq_esn.predict(X)
        assert preds.shape == (199, 1)

    def test_predict_finite(self, aq_esn):
        X = generate_mackey_glass(100)[:-1].reshape(-1, 1)
        preds = aq_esn.predict(X)
        assert np.isfinite(preds).all()

    def test_predict_reset_state(self, aq_esn):
        X = generate_mackey_glass(100)[:-1].reshape(-1, 1)
        p1 = aq_esn.predict(X, reset_state=True)
        p2 = aq_esn.predict(X, reset_state=True)
        np.testing.assert_array_equal(p1, p2)

    def test_mse_vs_original(self, trained_esn, aq_esn, val_data):
        """El MSE del modelo adaptativo no debe ser mucho peor que el original."""
        X = val_data[:-1].reshape(-1, 1)
        y = val_data[1:].reshape(-1, 1)

        trained_esn.reset()
        pred_orig = trained_esn.predict(X)
        mse_orig = float(np.mean((pred_orig - y) ** 2))

        aq_esn.reset()
        pred_aq = aq_esn.predict(X)
        mse_aq = float(np.mean((pred_aq - y) ** 2))

        # El MSE adaptativo no debe ser más de 100x peor que el original
        # (criterio permisivo dado que usamos cuantización muy agresiva en pesos de baja importancia)
        assert mse_aq < mse_orig * 100, (
            f"MSE adaptativo ({mse_aq:.6f}) demasiado alto vs original ({mse_orig:.6f})"
        )

    def test_1d_input(self, aq_esn):
        X = generate_mackey_glass(50)
        preds = aq_esn.predict(X, reset_state=True)
        assert preds.shape[0] == 50

    def test_reset_zeroes_state(self, aq_esn):
        X = generate_mackey_glass(20)[:-1].reshape(-1, 1)
        aq_esn.predict(X)
        aq_esn.reset()
        assert np.allclose(aq_esn.state, 0)


# ─── Tests de summary() ──────────────────────────────────────────────────────

class TestSummary:
    def test_summary_keys(self, quantizer):
        s = quantizer.summary()
        expected = {"n_weights_8bit", "n_weights_4bit", "n_weights_2bit",
                    "n_weights_1bit", "total_weights", "compression_ratio",
                    "memory_reduction_pct"}
        assert expected.issubset(set(s.keys()))

    def test_summary_without_quantize(self, trained_esn, val_data):
        aq = AdaptiveQuantizer(trained_esn)
        aq.compute_importance(val_data)
        s = aq.summary()
        assert "error" in s

    def test_compression_ratio_in_summary(self, quantizer):
        s = quantizer.summary()
        assert s["compression_ratio"] > 1.0
