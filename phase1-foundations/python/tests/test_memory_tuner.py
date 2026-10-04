"""
Tests para Memory Tuner y Capacidad de Memoria (Fase 13 del Roadmap de Ingeniería)
==================================================================================
"""

import pytest
import numpy as np
from esn.esn import EchoStateNetwork
from esn.memory_tuner import (
    compute_memory_capacity,
    analyze_signal_autocorrelation,
    auto_tune_esn_parameters
)


def test_autocorrelation_analysis():
    t = np.linspace(0, 50, 500)
    sig = np.sin(0.2 * t)
    analysis = analyze_signal_autocorrelation(sig, max_lags=40)
    
    assert "tau_corr" in analysis
    assert "dominant_period" in analysis
    assert analysis["tau_corr"] > 1.0
    assert analysis["variance"] > 0.1


def test_auto_tune_esn_parameters():
    t = np.linspace(0, 50, 500)
    sig = np.sin(0.1 * t)
    params = auto_tune_esn_parameters(sig, n_reservoir=40, dt=1.0)
    
    assert 0.0 < params["leak_rate"] <= 1.0
    assert 0.5 <= params["spectral_radius"] <= 0.99
    assert params["input_scale"] > 0.0
    assert params["washout"] >= 30
    assert params["n_reservoir"] == 40


def test_memory_capacity_bounds():
    N = 25
    esn = EchoStateNetwork(
        n_inputs=1,
        n_reservoir=N,
        n_outputs=1,
        spectral_radius=0.9,
        leak_rate=0.3,
        random_state=42
    )
    total_mc, mc_profile = compute_memory_capacity(
        esn,
        n_steps=500,
        max_delay=15,
        washout=50
    )
    
    # Límite superior de Jaeger: MC <= N
    assert total_mc > 0.0
    assert total_mc <= float(N)
    assert len(mc_profile) == 15
    # La memoria típicamente decae para retardos más grandes
    assert mc_profile[0] >= mc_profile[-1]
