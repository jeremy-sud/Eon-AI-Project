"""
Tests para NeuralWatermark — Firma Neuronal LSB

Cubre: generación de firma, embed, verify, impacto en MSE,
       robustez y utilidades.
"""
import copy
import math
import pytest
import numpy as np

from esn.esn import EchoStateNetwork
from utils.watermark import NeuralWatermark, extract_owner


# ════════════════════════════════════════════════════════════
#  Fixtures
# ════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def trained_esn():
    """ESN pequeño entrenado con señal sinusoidal."""
    rng = np.random.RandomState(0)
    T = 500
    t = np.linspace(0, 10 * np.pi, T)
    signal = np.sin(t).reshape(-1, 1)
    esn = EchoStateNetwork(
        n_inputs=1, n_reservoir=300, n_outputs=1,
        spectral_radius=0.9, random_state=42
    )
    esn.fit(signal[:-1], signal[1:], washout=50)
    return esn


@pytest.fixture(scope="module")
def wm():
    return NeuralWatermark("test@eon-project.org")


@pytest.fixture(scope="module")
def signed_esn(wm, trained_esn):
    return wm.embed(trained_esn)


# ════════════════════════════════════════════════════════════
#  Construcción
# ════════════════════════════════════════════════════════════

class TestInit:
    def test_stores_owner_id(self):
        wm = NeuralWatermark("alice@example.com")
        assert wm.owner_id == "alice@example.com"

    def test_empty_owner_raises(self):
        with pytest.raises(ValueError, match="owner_id"):
            NeuralWatermark("")

    def test_signature_is_256_bits(self):
        wm = NeuralWatermark("owner")
        assert wm.signature.shape == (256,)

    def test_signature_values_binary(self):
        wm = NeuralWatermark("owner")
        assert set(wm.signature.tolist()).issubset({0, 1})

    def test_signature_reproducible(self):
        s1 = NeuralWatermark("same@owner.com").signature
        s2 = NeuralWatermark("same@owner.com").signature
        assert np.array_equal(s1, s2)

    def test_different_owners_different_signatures(self):
        s1 = NeuralWatermark("alice@x.com").signature
        s2 = NeuralWatermark("bob@x.com").signature
        assert not np.array_equal(s1, s2)


# ════════════════════════════════════════════════════════════
#  embed()
# ════════════════════════════════════════════════════════════

class TestEmbed:
    def test_returns_esn_instance(self, wm, trained_esn):
        result = wm.embed(trained_esn)
        assert isinstance(result, EchoStateNetwork)

    def test_does_not_modify_original(self, wm, trained_esn):
        original_wout = trained_esn.W_out.copy()
        wm.embed(trained_esn)
        assert np.array_equal(trained_esn.W_out, original_wout)

    def test_wout_shape_preserved(self, wm, trained_esn, signed_esn):
        assert signed_esn.W_out.shape == trained_esn.W_out.shape

    def test_wout_changes_in_signed(self, wm, trained_esn, signed_esn):
        # Al menos algunos bits deben cambiar
        assert not np.array_equal(trained_esn.W_out, signed_esn.W_out)

    def test_raises_on_untrained_esn(self, wm):
        esn = EchoStateNetwork(n_reservoir=300, random_state=0)
        with pytest.raises(ValueError, match="entrenado"):
            wm.embed(esn)

    def test_raises_on_too_small_wout(self, wm):
        esn = EchoStateNetwork(n_inputs=1, n_reservoir=10, n_outputs=1,
                               random_state=0)
        rng = np.random.RandomState(0)
        T = 200
        X = np.sin(np.linspace(0, 6, T)).reshape(-1, 1)
        esn.fit(X[:-1], X[1:], washout=10)
        with pytest.raises(ValueError, match="elementos"):
            wm.embed(esn)

    def test_wout_values_are_finite(self, signed_esn):
        assert np.all(np.isfinite(signed_esn.W_out))

    def test_wout_values_close_to_original(self, trained_esn, signed_esn):
        # Los cambios LSB deben ser extremadamente pequeños
        diff = np.abs(trained_esn.W_out - signed_esn.W_out)
        assert np.max(diff) < 1e-13


# ════════════════════════════════════════════════════════════
#  verify()
# ════════════════════════════════════════════════════════════

class TestVerify:
    def test_detects_own_signature(self, wm, signed_esn):
        found, owner = wm.verify(signed_esn)
        assert found is True
        assert owner == wm.owner_id

    def test_rejects_unmarked_esn(self, wm, trained_esn):
        found, owner = wm.verify(trained_esn)
        assert found is False
        assert owner == "unknown"

    def test_rejects_different_owner(self, signed_esn):
        other_wm = NeuralWatermark("other@owner.com")
        found, owner = other_wm.verify(signed_esn)
        assert found is False
        assert owner == "unknown"

    def test_returns_unknown_for_untrained(self, wm):
        esn = EchoStateNetwork(n_reservoir=300, random_state=0)
        found, owner = wm.verify(esn)
        assert found is False
        assert owner == "unknown"

    def test_round_trip_multiple_owners(self, trained_esn):
        owners = ["alice", "bob", "carol"]
        watermarks = [NeuralWatermark(o) for o in owners]
        for wm_i in watermarks:
            signed = wm_i.embed(trained_esn)
            found, owner = wm_i.verify(signed)
            assert found is True
            assert owner == wm_i.owner_id
            # Los otros propietarios no deben detectarlo
            for wm_j in watermarks:
                if wm_j.owner_id != wm_i.owner_id:
                    found_j, _ = wm_j.verify(signed)
                    assert not found_j

    def test_signed_copy_still_verifies(self, wm, signed_esn):
        """Una copia profunda del modelo firmado debe seguir siendo verificable."""
        esn_copy = copy.deepcopy(signed_esn)
        found, owner = wm.verify(esn_copy)
        assert found is True


# ════════════════════════════════════════════════════════════
#  Impacto en MSE
# ════════════════════════════════════════════════════════════

class TestMSEImpact:
    def test_mse_delta_is_small(self, wm, trained_esn):
        """El impacto en MSE debe ser < 0.1%."""
        rng = np.random.RandomState(1)
        T = 200
        test_inputs = np.sin(np.linspace(0, 6, T)).reshape(-1, 1)
        delta = wm.mse_delta(trained_esn, test_inputs)
        assert abs(delta) < 0.1  # menos del 0.1%

    def test_mse_delta_raises_on_untrained(self, wm):
        esn = EchoStateNetwork(n_reservoir=300, random_state=0)
        X = np.zeros((10, 1))
        with pytest.raises(ValueError):
            wm.mse_delta(esn, X)


# ════════════════════════════════════════════════════════════
#  info() y extract_owner()
# ════════════════════════════════════════════════════════════

class TestInfo:
    def test_info_keys(self, wm):
        info = wm.info()
        assert "owner_id" in info
        assert "signature_bits" in info
        assert "signature_hex" in info
        assert "algorithm" in info

    def test_info_signature_bits(self, wm):
        assert wm.info()["signature_bits"] == 256

    def test_info_hex_is_64_chars(self, wm):
        assert len(wm.info()["signature_hex"]) == 64


class TestExtractOwner:
    def test_finds_correct_owner(self, trained_esn):
        owners = ["alice", "bob"]
        watermarks = [NeuralWatermark(o) for o in owners]
        signed = watermarks[1].embed(trained_esn)
        found = extract_owner(signed, watermarks)
        assert found == "bob"

    def test_returns_none_for_unmarked(self, trained_esn):
        watermarks = [NeuralWatermark("alice"), NeuralWatermark("bob")]
        result = extract_owner(trained_esn, watermarks)
        assert result is None
