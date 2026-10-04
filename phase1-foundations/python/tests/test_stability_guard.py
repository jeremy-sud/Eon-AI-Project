"""
Tests para StabilityGuard (Fase 13 del Roadmap de Ingeniería)
============================================================
"""

import pytest
import numpy as np
from esn.stability_guard import StabilityGuard


def test_stability_guard_normal_state():
    guard = StabilityGuard(spectral_radius_target=0.90, spectral_radius_max=0.95)
    state = np.random.uniform(-0.5, 0.5, 30)
    is_stable, metrics = guard.check_state(state)
    assert is_stable is True
    assert metrics["saturation_ratio"] == 0.0
    assert metrics["contraction_events"] == 0.0


def test_stability_guard_saturation_detection():
    guard = StabilityGuard(saturation_threshold=0.99, max_saturation_ratio=0.5)
    # Crear estado con 80% de neuronas saturadas
    state = np.full(30, 0.995)
    state[:6] = 0.1
    is_stable, metrics = guard.check_state(state)
    assert is_stable is False
    assert metrics["saturation_ratio"] > 0.5
    assert metrics["saturation_events"] == 1


def test_stability_guard_nan_inf_detection():
    guard = StabilityGuard()
    state_nan = np.array([0.1, np.nan, 0.3])
    with pytest.raises(FloatingPointError):
        guard.check_state(state_nan)

    state_inf = np.array([0.1, np.inf, 0.3])
    with pytest.raises(FloatingPointError):
        guard.check_state(state_inf)


def test_stability_guard_weight_contraction():
    guard = StabilityGuard(spectral_radius_target=0.90, spectral_radius_max=0.95)
    # Matriz inestable con rho = 1.8
    W_unstable = np.eye(20) * 1.8
    W_stab, was_contracted, rho = guard.check_and_stabilize_weights(W_unstable)
    
    assert was_contracted is True
    assert np.isclose(rho, 0.90, atol=1e-4)
    assert guard.contraction_events == 1


def test_stability_guard_state_damping():
    guard = StabilityGuard(damping_factor=0.8)
    state = np.array([1.0, -1.0, 0.5])
    damped = guard.stabilize_state(state)
    assert np.all(np.abs(damped) < np.abs(state))
