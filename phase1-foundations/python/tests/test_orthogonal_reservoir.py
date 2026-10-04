"""
Tests para Reservoirs Ortogonales y Cayley Transform (Fase 13 del Roadmap de Ingeniería)
=======================================================================================
"""

import pytest
import numpy as np
from utils.matrix_init import create_orthogonal_reservoir, compute_spectral_radius
from esn.esn import EchoStateNetwork, generate_mackey_glass


def test_orthogonal_reservoir_orthogonality():
    size = 35
    rho_target = 0.88
    W = create_orthogonal_reservoir(size=size, spectral_radius=rho_target, method='cayley')
    
    # W / rho_target debe ser estrictamente ortogonal: Q @ Q^T = I
    Q = W / rho_target
    identity_approx = Q @ Q.T
    diff = np.max(np.abs(identity_approx - np.eye(size)))
    
    assert diff < 1e-10, f"Desviación de ortogonalidad demasiado alta: {diff}"


def test_orthogonal_reservoir_spectral_radius():
    size = 40
    for rho in [0.65, 0.85, 0.95]:
        W = create_orthogonal_reservoir(size=size, spectral_radius=rho, method='cayley')
        computed_rho = compute_spectral_radius(W, method='exact')
        assert np.isclose(computed_rho, rho, atol=1e-5)


def test_orthogonal_reservoir_in_esn_mackey_glass():
    # Probar que un ESN con reservoir ortogonal predice Mackey-Glass con estabilidad
    data = generate_mackey_glass(n_samples=500, tau=17)
    train_data = data[:350]
    test_data = data[350:]
    
    esn = EchoStateNetwork(n_inputs=1, n_reservoir=30, n_outputs=1, spectral_radius=0.9)
    # Reemplazar W_reservoir con matriz ortogonal
    esn.W_reservoir = create_orthogonal_reservoir(size=30, spectral_radius=0.9)
    
    esn.fit(train_data[:-1], train_data[1:], washout=50)
    assert esn.W_out is not None
    assert not np.any(np.isnan(esn.W_out))
    
    preds = esn.predict(test_data[:-1])
    assert not np.any(np.isnan(preds))
    mse = float(np.mean((preds.ravel() - test_data[1:].ravel()) ** 2))
    assert mse < 0.1
