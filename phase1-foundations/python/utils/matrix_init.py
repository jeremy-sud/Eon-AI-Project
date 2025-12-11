"""
Proyecto Eón - Inicialización de Matrices y Utilidades
======================================================

Funciones compartidas para evitar código duplicado en el motor ESN.

(c) 2024 Sistemas Ursol - Jeremy Arias Solano
"""

import numpy as np
from typing import Optional


def generate_birth_hash(seed: int, timestamp: int) -> str:
    """
    Genera hash de nacimiento estandarizado (compatible con C/JS).
    
    Usa el mismo algoritmo LCG que la implementación en C para garantizar
    que la misma semilla produzca el mismo hash en todas las plataformas.
    
    Args:
        seed: Semilla del generador aleatorio
        timestamp: Timestamp del nacimiento
        
    Returns:
        Hash hexadecimal de 32 caracteres
    """
    state = seed ^ timestamp
    bytes_list = []
    curr = state & 0xFFFFFFFF
    
    for _ in range(16):
        # LCG constants from C implementation
        curr = (curr * 1103515245 + 12345) & 0x7fffffff
        bytes_list.append(curr & 0xFF)
    
    return ''.join(f'{b:02x}' for b in bytes_list)


def compute_spectral_radius(
    W: np.ndarray,
    method: str = 'auto',
    max_iter: int = 100,
    tol: float = 1e-6,
    rng: Optional[np.random.Generator] = None
) -> float:
    """
    Calcula el radio espectral (máximo eigenvalor absoluto) de una matriz.
    
    Para matrices pequeñas (<50x50) usa cálculo exacto.
    Para matrices grandes usa power iteration (O(n²) por iteración vs O(n³) exacto).
    
    Args:
        W: Matriz cuadrada
        method: 'exact', 'power', o 'auto' (elige según tamaño)
        max_iter: Iteraciones máximas para power iteration
        tol: Tolerancia de convergencia
        rng: Generador aleatorio para vector inicial
        
    Returns:
        Radio espectral estimado
    """
    n = W.shape[0]
    
    if method == 'auto':
        method = 'exact' if n < 50 else 'power'
    
    if method == 'exact':
        eigenvalues = np.abs(np.linalg.eigvals(W))
        return eigenvalues.max() if len(eigenvalues) > 0 else 0.0
    
    # Power iteration para matrices grandes
    if rng is None:
        rng = np.random.default_rng()
    
    v = rng.standard_normal(n)
    v /= np.linalg.norm(v)
    
    eigenvalue = 0.0
    for _ in range(max_iter):
        w = W @ v
        new_eigenvalue = np.linalg.norm(w)
        
        if new_eigenvalue < 1e-10:
            return 0.0
        
        if abs(new_eigenvalue - eigenvalue) < tol:
            break
        
        eigenvalue = new_eigenvalue
        v = w / new_eigenvalue
    
    return eigenvalue


def create_reservoir_matrix(
    size: int,
    spectral_radius: float,
    sparsity: float,
    rng: np.random.Generator,
    method: str = 'auto'
) -> np.ndarray:
    """
    Crea una matriz de reservoir con radio espectral especificado.
    
    Esta función centraliza la lógica de creación de matrices que estaba
    duplicada en esn.py, recursive_esn.py y hebbian.py.
    
    Args:
        size: Tamaño de la matriz (size x size)
        spectral_radius: Radio espectral deseado (típicamente 0.9-0.99)
        sparsity: Proporción de conexiones cero (0.9 = 90% ceros)
        rng: Generador aleatorio NumPy
        method: Método para calcular spectral radius ('exact', 'power', 'auto')
        
    Returns:
        Matriz de reservoir normalizada
    """
    # Generar matriz aleatoria
    W = rng.uniform(-1, 1, (size, size))
    
    # Aplicar sparsity (máscara de conexiones)
    mask = rng.random((size, size)) > sparsity
    W *= mask
    
    # Calcular y normalizar spectral radius
    current_radius = compute_spectral_radius(W, method=method, rng=rng)
    
    if current_radius > 0:
        W *= spectral_radius / current_radius
    
    return W


def validate_esn_parameters(
    n_inputs: int,
    n_reservoir: int,
    n_outputs: int,
    spectral_radius: float,
    sparsity: float,
    noise: float
) -> None:
    """
    Valida parámetros de ESN y lanza excepciones con mensajes claros.
    
    Args:
        n_inputs: Número de entradas
        n_reservoir: Número de neuronas en el reservoir
        n_outputs: Número de salidas
        spectral_radius: Radio espectral
        sparsity: Escasez de conexiones
        noise: Nivel de ruido
        
    Raises:
        ValueError: Si algún parámetro es inválido
    """
    if n_inputs < 1:
        raise ValueError(f"n_inputs debe ser >= 1, recibido: {n_inputs}")
    
    if n_reservoir < 1:
        raise ValueError(f"n_reservoir debe ser >= 1, recibido: {n_reservoir}")
    
    if n_outputs < 1:
        raise ValueError(f"n_outputs debe ser >= 1, recibido: {n_outputs}")
    
    if not 0 < spectral_radius <= 2.0:
        raise ValueError(
            f"spectral_radius debe estar en (0, 2.0], recibido: {spectral_radius}. "
            "Valores típicos: 0.9-0.99"
        )
    
    if not 0 <= sparsity < 1:
        raise ValueError(
            f"sparsity debe estar en [0, 1), recibido: {sparsity}. "
            "Valor típico: 0.9 (90% de conexiones son cero)"
        )
    
    if noise < 0:
        raise ValueError(f"noise debe ser >= 0, recibido: {noise}")


def validate_training_data(
    inputs: np.ndarray,
    outputs: np.ndarray,
    n_inputs: int,
    n_outputs: int,
    washout: int
) -> tuple:
    """
    Valida y normaliza datos de entrenamiento.
    
    Args:
        inputs: Array de entradas
        outputs: Array de salidas objetivo
        n_inputs: Número de entradas esperadas
        n_outputs: Número de salidas esperadas
        washout: Período de washout
        
    Returns:
        Tupla (inputs_normalized, outputs_normalized)
        
    Raises:
        ValueError: Si las dimensiones no coinciden
    """
    # Normalizar dimensiones
    if inputs.ndim == 1:
        inputs = inputs.reshape(-1, 1)
    if outputs.ndim == 1:
        outputs = outputs.reshape(-1, 1)
    
    # Validar dimensiones de entrada
    if inputs.shape[1] != n_inputs:
        raise ValueError(
            f"Dimensión de entrada incorrecta: esperado {n_inputs}, "
            f"recibido {inputs.shape[1]}"
        )
    
    # Validar dimensiones de salida
    if outputs.shape[1] != n_outputs:
        raise ValueError(
            f"Dimensión de salida incorrecta: esperado {n_outputs}, "
            f"recibido {outputs.shape[1]}"
        )
    
    # Validar número de muestras
    if inputs.shape[0] != outputs.shape[0]:
        raise ValueError(
            f"inputs y outputs deben tener mismo número de muestras: "
            f"{inputs.shape[0]} vs {outputs.shape[0]}"
        )
    
    # Validar washout
    if washout >= inputs.shape[0]:
        raise ValueError(
            f"washout ({washout}) debe ser menor que número de muestras ({inputs.shape[0]})"
        )
    
    return inputs, outputs


def check_numerical_stability(state: np.ndarray, context: str = "reservoir") -> None:
    """
    Verifica estabilidad numérica del estado y advierte sobre problemas.
    
    Args:
        state: Estado del reservoir
        context: Contexto para mensajes de error
        
    Raises:
        RuntimeError: Si hay NaN o Inf
    """
    import warnings
    
    if np.any(np.isnan(state)):
        raise RuntimeError(
            f"Estado del {context} contiene NaN. "
            "Considera reducir spectral_radius o aumentar regularización."
        )
    
    if np.any(np.isinf(state)):
        raise RuntimeError(
            f"Estado del {context} contiene Inf. "
            "Revisa los valores de entrada."
        )
    
    # Advertir si estado está saturado (>90% en valores extremos de tanh)
    saturation = np.mean(np.abs(state) > 0.99)
    if saturation > 0.9:
        warnings.warn(
            f"Estado del {context} saturado ({saturation:.1%}). "
            "Considera reducir spectral_radius.",
            RuntimeWarning
        )


def ridge_regression(
    states: np.ndarray,
    targets: np.ndarray,
    regularization: float = 1e-6
) -> np.ndarray:
    """
    Calcula W_out usando Ridge Regression (más estable que inversión directa).
    
    Usa np.linalg.solve en lugar de np.linalg.inv que es:
    - Más estable numéricamente
    - Más rápido (O(n³/3) vs O(n³))
    
    Args:
        states: Estados del reservoir (T x n_reservoir)
        targets: Objetivos (T x n_outputs)
        regularization: Factor de regularización
        
    Returns:
        Matriz de pesos de salida W_out
    """
    n_features = states.shape[1]
    
    # A = S^T @ S + λI
    A = states.T @ states + regularization * np.eye(n_features)
    
    # B = S^T @ Y
    B = states.T @ targets
    
    # Resolver sistema lineal (más eficiente que inv)
    return np.linalg.solve(A, B)
