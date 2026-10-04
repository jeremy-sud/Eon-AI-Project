import os
import sys
_current_dir = os.path.dirname(os.path.abspath(__file__))
_python_dir = os.path.dirname(_current_dir)
if _python_dir not in sys.path:
    sys.path.insert(0, _python_dir)

import pytest
import numpy as np
from learning.ud_rls import UDFactorizedRLS


def test_ud_rls_convergence():
    rng = np.random.default_rng(123)
    n_features = 4
    w_true = np.array([1.5, -2.0, 0.5, 3.2])
    
    rls = UDFactorizedRLS(n_features=n_features, n_outputs=1, forgetting_factor=0.99)
    
    for _ in range(400):
        z = rng.standard_normal(n_features)
        y = np.dot(w_true, z) + 0.005 * rng.standard_normal()
        rls.update(z, y)
        
    assert np.allclose(w_true, rls.W_out[0], atol=0.05)


def test_ud_rls_strictly_positive_definite():
    rng = np.random.default_rng(456)
    n_features = 6
    rls = UDFactorizedRLS(n_features=n_features, n_outputs=1, forgetting_factor=0.98)
    
    for _ in range(200):
        z = rng.standard_normal(n_features)
        y = z[0] - z[1]
        rls.update(z, y)
        
    # Elementos de D deben ser estrictamente positivos
    assert np.all(rls.D > 0.0)
    
    # Matriz P = U @ D @ U^T debe tener eigenvalores estrictamente positivos
    P = rls.get_reconstructed_p_matrix()
    eigs = np.linalg.eigvalsh(P)
    assert np.all(eigs > 0.0)


def test_ud_rls_multi_output():
    rng = np.random.default_rng(789)
    n_features = 3
    n_outputs = 2
    W_true = np.array([
        [1.0, -1.0, 2.0],
        [0.5, 0.5, -0.5]
    ])
    
    rls = UDFactorizedRLS(n_features=n_features, n_outputs=n_outputs, forgetting_factor=0.99)
    
    for _ in range(300):
        z = rng.standard_normal(n_features)
        y = W_true @ z + 0.01 * rng.standard_normal(n_outputs)
        rls.update(z, y)
        
    assert np.allclose(W_true, rls.W_out, atol=0.08)
