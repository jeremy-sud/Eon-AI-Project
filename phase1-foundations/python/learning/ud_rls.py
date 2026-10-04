"""
Proyecto Eón - Recursive Least Squares con Factorización U-D (Bierman-Thornton)
==============================================================================

Algoritmo RLS numéricamente incondicionalmente estable para aprendizaje continuo
en microcontroladores edge y sistemas de cómputo embebido.

Fundamentos Matemáticos:
- Representación P = U * D * U^T donde U es triangular superior unitaria y D > 0 es diagonal.
- Garantía matemática: P permanece estrictamente definida positiva para siempre (P > 0).
- Factor de olvido exponencial beta in (0, 1] para adaptación a deriva de sensores.
- Complejidad: O(M^2) operaciones por muestra, sin cálculo de inversas explícitas.

(c) 2024-2026 SenseLab - Build with Sense
"""

import numpy as np
from typing import Optional, Tuple, Union


class UDFactorizedRLS:
    """
    Algoritmo Recursive Least Squares con Factorización U-D (Bierman-Thornton).
    
    A diferencia del RLS clásico que acumula errores de truncamiento numérico
    haciendo que P pierda su carácter definido positivo (provocando NaN y divergencia),
    la factorización U-D actualiza directamente los factores U y D:
        P(t) = U(t) @ diag(D(t)) @ U(t)^T
    
    Garantiza estabilidad numérica infinita incluso en precisión fija/limitada.
    """
    
    def __init__(
        self,
        n_features: int,
        n_outputs: int = 1,
        forgetting_factor: float = 0.995,
        initial_p_diag: float = 1000.0
    ):
        """
        Args:
            n_features: Dimensión del vector de entrada z(t) (ej: 1 + K + N)
            n_outputs: Dimensión del vector objetivo y(t)
            forgetting_factor: Factor de olvido beta in (0, 1] (típico 0.98 - 0.999)
            initial_p_diag: Varianza a priori inicial (1 / lambda_ridge)
        """
        if not 0.0 < forgetting_factor <= 1.0:
            raise ValueError(f"forgetting_factor debe estar en (0, 1], recibido {forgetting_factor}")
            
        self.n_features = n_features
        self.n_outputs = n_outputs
        self.beta = forgetting_factor
        
        # Pesos entrenables: shape (n_outputs, n_features)
        self.W_out = np.zeros((n_outputs, n_features), dtype=np.float64)
        
        # Factorización U-D: P = U @ D @ U^T
        # U es unitaria triangular superior (diagonal de 1s)
        self.U = np.eye(n_features, dtype=np.float64)
        # D es el vector de elementos diagonales (estrictamente positivos)
        self.D = np.full(n_features, initial_p_diag, dtype=np.float64)
        
        self.step_count: int = 0
        self.total_squared_error: float = 0.0

    def predict(self, z: np.ndarray) -> np.ndarray:
        """
        Predice la salida para un vector de características extendido z.
        
        Args:
            z: Vector de características (n_features,) o (n_features, 1)
            
        Returns:
            Salida predicha (n_outputs,)
        """
        z_flat = np.asarray(z, dtype=np.float64).ravel()
        if len(z_flat) != self.n_features:
            raise ValueError(f"Dimensión incorrecta en predict: esperado {self.n_features}, recibido {len(z_flat)}")
        return self.W_out @ z_flat

    def update(self, z: np.ndarray, y_target: Union[float, np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Paso de actualización online U-D Bierman para una nueva muestra (z, y_target).
        
        Args:
            z: Vector de entrada / estado del reservoir (n_features,)
            y_target: Salida real esperada (n_outputs,) o escalar
            
        Returns:
            Tuple (y_pred, error)
        """
        z_vec = np.asarray(z, dtype=np.float64).ravel()
        if len(z_vec) != self.n_features:
            raise ValueError(f"Dimensión de z incorrecta: esperado {self.n_features}, recibido {len(z_vec)}")
            
        y_vec = np.atleast_1d(np.asarray(y_target, dtype=np.float64))
        if len(y_vec) != self.n_outputs:
            raise ValueError(f"Dimensión de y_target incorrecta: esperado {self.n_outputs}, recibido {len(y_vec)}")
            
        # 1. Predicción a priori y error
        y_pred = self.W_out @ z_vec
        error = y_vec - y_pred
        
        # 2. Algoritmo U-D Bierman-Thornton
        M = self.n_features
        f = self.U.T @ z_vec   # f = U^T @ z
        v = self.D * f         # v = D * f
        alpha = self.beta
        
        b = np.zeros(M, dtype=np.float64)
        
        for j in range(M):
            f_j = f[j]
            v_j = v[j]
            alpha_prev = alpha
            alpha = alpha_prev + f_j * v_j
            
            # Actualización del elemento diagonal D_j garantizada > 0
            self.D[j] = (self.D[j] * alpha_prev) / (self.beta * alpha)
            
            lambda_j = -f_j / alpha_prev
            
            for i in range(j):
                u_ij = self.U[i, j]
                self.U[i, j] = u_ij + lambda_j * b[i]
                b[i] = b[i] + u_ij * v_j
                
            b[j] = v_j
            
        # Ganancia final de Kalman: K = b / alpha
        kalman_gain = b / alpha
            
        # 3. Actualización de pesos W_out = W_out + e * K^T
        self.W_out += np.outer(error, kalman_gain)
        
        self.step_count += 1
        self.total_squared_error += float(np.sum(error ** 2))
        
        return y_pred, error

    def get_reconstructed_p_matrix(self) -> np.ndarray:
        """
        Reconstruye explícitamente P = U @ diag(D) @ U^T para análisis o depuración.
        """
        return self.U @ np.diag(self.D) @ self.U.T

    def get_mse(self) -> float:
        """Retorna el Mean Squared Error acumulado hasta el momento."""
        return self.total_squared_error / max(1, self.step_count)
