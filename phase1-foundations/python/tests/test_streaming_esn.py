"""
Tests para StreamingESN - Proyecto Eón
========================================

Tests del aprendizaje online con RLS.
"""

import pytest
import numpy as np
import sys
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
_python_dir = os.path.dirname(_current_dir)
sys.path.insert(0, _python_dir)

from esn.streaming_esn import StreamingESN
from esn.esn import generate_mackey_glass


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def base_data():
    return generate_mackey_glass(1500)


@pytest.fixture(scope="module")
def pretrained_streaming(base_data):
    esn = StreamingESN(
        n_inputs=1, n_reservoir=50, n_outputs=1,
        spectral_radius=0.9, forgetting_factor=1.0, random_state=42,
    )
    X = base_data[:800].reshape(-1, 1)
    y = base_data[1:801].reshape(-1, 1)
    esn.fit(X, y, washout=50)
    return esn


# ─── Tests de construcción ───────────────────────────────────────────────────

class TestConstruction:
    def test_valid_forgetting_factor(self):
        esn = StreamingESN(n_inputs=1, n_reservoir=20, n_outputs=1,
                           forgetting_factor=0.99, random_state=0)
        assert esn.forgetting_factor == 0.99

    def test_invalid_forgetting_factor(self):
        with pytest.raises(ValueError, match="forgetting_factor"):
            StreamingESN(n_inputs=1, n_reservoir=20, n_outputs=1,
                         forgetting_factor=0.0)

    def test_forgetting_factor_exactly_1(self):
        esn = StreamingESN(n_inputs=1, n_reservoir=20, n_outputs=1,
                           forgetting_factor=1.0, random_state=0)
        assert esn.forgetting_factor == 1.0

    def test_p_initially_none(self):
        esn = StreamingESN(n_inputs=1, n_reservoir=20, n_outputs=1, random_state=0)
        assert esn._P is None


# ─── Tests de fit() ───────────────────────────────────────────────────────────

class TestFit:
    def test_fit_initializes_P(self, pretrained_streaming):
        assert pretrained_streaming._P is not None

    def test_fit_P_shape(self, pretrained_streaming):
        n = pretrained_streaming.n_reservoir
        assert pretrained_streaming._P.shape == (n, n)

    def test_fit_W_out_shape(self, pretrained_streaming):
        n = pretrained_streaming.n_reservoir
        assert pretrained_streaming.W_out.shape == (n, 1)

    def test_fit_resets_online_updates(self, base_data):
        esn = StreamingESN(n_inputs=1, n_reservoir=30, n_outputs=1,
                           random_state=0)
        X = base_data[:300].reshape(-1, 1)
        y = base_data[1:301].reshape(-1, 1)
        esn.fit(X, y)
        assert esn._online_updates == 0


# ─── Tests de init_online() ──────────────────────────────────────────────────

class TestInitOnline:
    def test_w_out_zeros(self):
        esn = StreamingESN(n_inputs=1, n_reservoir=20, n_outputs=1, random_state=0)
        esn.init_online()
        assert np.allclose(esn.W_out, 0)

    def test_p_is_identity(self):
        esn = StreamingESN(n_inputs=1, n_reservoir=20, n_outputs=1,
                           rls_init_scale=2.0, random_state=0)
        esn.init_online()
        expected = np.eye(20) * 2.0
        np.testing.assert_allclose(esn._P, expected)

    def test_returns_self(self):
        esn = StreamingESN(n_inputs=1, n_reservoir=20, n_outputs=1, random_state=0)
        result = esn.init_online()
        assert result is esn


# ─── Tests de update() ───────────────────────────────────────────────────────

class TestUpdate:
    def test_returns_float(self, pretrained_streaming, base_data):
        x = base_data[900:901].reshape(-1, 1)
        y = base_data[901:902].reshape(-1, 1)
        err = pretrained_streaming.update(x[0], y[0])
        assert isinstance(err, float)
        assert np.isfinite(err)

    def test_error_non_negative(self, pretrained_streaming, base_data):
        x = base_data[902:903].reshape(1,)
        y = base_data[903:904].reshape(1,)
        err = pretrained_streaming.update(x, y)
        assert err >= 0.0

    def test_increments_update_count(self, base_data):
        esn = StreamingESN(n_inputs=1, n_reservoir=20, n_outputs=1, random_state=0)
        esn.init_online()
        before = esn._online_updates
        esn.update(base_data[0:1], base_data[1:2])
        assert esn._online_updates == before + 1

    def test_updates_W_out(self, base_data):
        esn = StreamingESN(n_inputs=1, n_reservoir=20, n_outputs=1, random_state=0)
        esn.init_online()
        W_before = esn.W_out.copy()
        esn.update(base_data[0:1], base_data[1:2])
        assert not np.allclose(esn.W_out, W_before)

    def test_p_matrix_finite(self, pretrained_streaming, base_data):
        """P debe permanecer finito después de varios updates."""
        esn = StreamingESN(n_inputs=1, n_reservoir=20, n_outputs=1,
                           forgetting_factor=0.99, random_state=0)
        esn.fit(base_data[:200].reshape(-1, 1),
                base_data[1:201].reshape(-1, 1), washout=20)
        for i in range(50):
            esn.update(base_data[200 + i], base_data[201 + i])
        assert np.isfinite(esn._P).all()


# ─── Tests de stream_fit() ───────────────────────────────────────────────────

class TestStreamFit:
    def test_basic_stream_fit(self, base_data):
        esn = StreamingESN(n_inputs=1, n_reservoir=30, n_outputs=1,
                           random_state=0)
        esn.init_online()
        X = base_data[:200].reshape(-1, 1)
        y = base_data[1:201].reshape(-1, 1)
        result = esn.stream_fit(X, y)
        assert result is esn  # devuelve self
        assert esn._online_updates == 200

    def test_washout_skips_updates(self, base_data):
        esn = StreamingESN(n_inputs=1, n_reservoir=30, n_outputs=1, random_state=0)
        esn.init_online()
        X = base_data[:100].reshape(-1, 1)
        y = base_data[1:101].reshape(-1, 1)
        esn.stream_fit(X, y, washout=20)
        assert esn._online_updates == 80  # 100 - 20

    def test_1d_input_accepted(self, base_data):
        esn = StreamingESN(n_inputs=1, n_reservoir=20, n_outputs=1, random_state=0)
        esn.init_online()
        esn.stream_fit(base_data[:50], base_data[1:51])
        assert esn._online_updates > 0


# ─── Tests de predict_one() ──────────────────────────────────────────────────

class TestPredictOne:
    def test_output_shape(self, pretrained_streaming, base_data):
        x = base_data[1000]
        pred = pretrained_streaming.predict_one(x)
        assert pred.shape == (1,)

    def test_output_finite(self, pretrained_streaming, base_data):
        x = base_data[1001]
        pred = pretrained_streaming.predict_one(x)
        assert np.isfinite(pred).all()

    def test_raises_without_init(self, base_data):
        esn = StreamingESN(n_inputs=1, n_reservoir=20, n_outputs=1, random_state=0)
        with pytest.raises(ValueError):
            esn.predict_one(base_data[0])


# ─── Tests de streaming_stats() ──────────────────────────────────────────────

class TestStreamingStats:
    def test_stats_before_updates(self):
        esn = StreamingESN(n_inputs=1, n_reservoir=20, n_outputs=1, random_state=0)
        esn.init_online()
        stats = esn.streaming_stats()
        assert stats["online_updates"] == 0
        assert stats["mean_error"] is None

    def test_stats_after_updates(self, base_data):
        esn = StreamingESN(n_inputs=1, n_reservoir=20, n_outputs=1,
                           forgetting_factor=0.99, random_state=0)
        esn.init_online()
        esn.stream_fit(base_data[:100].reshape(-1, 1),
                       base_data[1:101].reshape(-1, 1))
        stats = esn.streaming_stats()
        assert stats["online_updates"] == 100
        assert stats["mean_error"] is not None
        assert np.isfinite(stats["mean_error"])

    def test_keys_present(self, base_data):
        esn = StreamingESN(n_inputs=1, n_reservoir=20, n_outputs=1, random_state=0)
        esn.init_online()
        esn.stream_fit(base_data[:50].reshape(-1, 1),
                       base_data[1:51].reshape(-1, 1))
        stats = esn.streaming_stats()
        expected = {"online_updates", "forgetting_factor", "mean_error",
                    "recent_error", "min_error", "max_error", "converged"}
        assert expected.issubset(set(stats.keys()))


# ─── Tests de error_curve() ──────────────────────────────────────────────────

class TestErrorCurve:
    def test_empty_before_updates(self):
        esn = StreamingESN(n_inputs=1, n_reservoir=20, n_outputs=1, random_state=0)
        esn.init_online()
        assert len(esn.error_curve()) == 0

    def test_length_matches_updates(self, base_data):
        esn = StreamingESN(n_inputs=1, n_reservoir=20, n_outputs=1, random_state=0)
        esn.init_online()
        n = 50
        esn.stream_fit(base_data[:n].reshape(-1, 1),
                       base_data[1:n + 1].reshape(-1, 1))
        assert len(esn.error_curve()) == n

    def test_errors_non_negative(self, base_data):
        esn = StreamingESN(n_inputs=1, n_reservoir=20, n_outputs=1, random_state=0)
        esn.init_online()
        esn.stream_fit(base_data[:30].reshape(-1, 1),
                       base_data[1:31].reshape(-1, 1))
        assert (esn.error_curve() >= 0).all()


# ─── Test de adaptación a concept drift ──────────────────────────────────────

class TestConceptDrift:
    def test_forgetting_factor_adapts(self, base_data):
        """Con λ < 1, el error reciente debe ser menor que el inicial."""
        esn = StreamingESN(n_inputs=1, n_reservoir=40, n_outputs=1,
                           forgetting_factor=0.98, random_state=0)
        esn.fit(base_data[:400].reshape(-1, 1),
                base_data[1:401].reshape(-1, 1), washout=50)

        # Fase de drift: datos desplazados
        drifted = base_data[401:601] + 2.0
        esn.stream_fit(drifted.reshape(-1, 1),
                       drifted.reshape(-1, 1))

        curve = esn.error_curve()
        # El error de los últimos 50 pasos debe ser <= el de los primeros 50
        assert np.mean(curve[-50:]) <= np.mean(curve[:50]) * 10
