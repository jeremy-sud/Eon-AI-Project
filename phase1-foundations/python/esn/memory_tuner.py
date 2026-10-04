"""
Proyecto Eón - Optimizador de Capacidad de Memoria y Sintonización Analítica
===========================================================================

Herramientas analíticas para medir y maximizar la Memory Capacity (MC) de Jaeger
y auto-sintonizar hiperparámetros (alpha, rho, s_in) según las propiedades
espectrales de las señales temporales del edge.

Fundamentos Matemáticos:
- Capacidad de memoria lineal: MC = sum_{k=1}^infty r^2(u(t-k), y_k(t)) <= N
- Acoplamiento de constante de fuga con autocorrelacion: alpha_opt = 1 - exp(-dt / tau_corr)

(c) 2024-2026 SenseLab - Build with Sense
"""

import numpy as np
from typing import Dict, Tuple, Optional, Any

try:
    from utils.matrix_init import ridge_regression
except ImportError:
    def ridge_regression(X: np.ndarray, Y: np.ndarray, alpha: float = 1e-6) -> np.ndarray:
        XtX = X.T @ X + alpha * np.eye(X.shape[1])
        XtY = X.T @ Y
        return np.linalg.solve(XtX, XtY).T


def compute_memory_capacity(
    esn: Any,
    n_steps: int = 1500,
    max_delay: int = 50,
    washout: int = 200,
    ridge_lambda: float = 1e-6,
    rng: Optional[np.random.Generator] = None
) -> Tuple[float, np.ndarray]:
    """
    Calcula la Capacidad de Memoria (Memory Capacity - MC) exacta de Jaeger.
    
    Evalúa qué tan bien el reservoir puede reconstruir entradas pasadas u(t-k)
    para diferentes retardos k mediante regresión lineal sobre los estados del reservoir.
    
    Teorema de Jaeger: Para cualquier reservoir con N neuronas, MC <= N.
    
    Args:
        esn: Instancia de EchoStateNetwork (debe implementar update o fit/predict)
        n_steps: Pasos de tiempo para la evaluación (típico 1000 - 3000)
        max_delay: Máximo retardo k a evaluar (típico <= N)
        washout: Pasos transitorios a descartar
        ridge_lambda: Parámetro de regularización ridge
        rng: Generador de números aleatorios
        
    Returns:
        Tuple (total_mc, mc_per_delay_array)
    """
    if rng is None:
        rng = np.random.default_rng(42)
        
    # 1. Generar señal aleatoria i.i.d. uniforme en [-1, 1]
    u = rng.uniform(-1.0, 1.0, size=(n_steps, 1))
    
    # 2. Recolectar estados del reservoir
    states = []
    # Reiniciar estado interno si existe
    if hasattr(esn, 'state'):
        esn.state = np.zeros(esn.n_reservoir)
        
    for t in range(n_steps):
        input_t = u[t] # (1,)
        if hasattr(esn, '_update_state'):
            new_state = esn._update_state(input_t)
            states.append(new_state.copy())
        elif hasattr(esn, 'update'):
            esn.update(float(input_t[0]))
            states.append(esn.state.copy())
        else:
            # Fallback usando ecuación canónica leaky integrator
            if t == 0:
                x = np.zeros(esn.n_reservoir)
            u_val = input_t[0]
            W_in = getattr(esn, 'W_in')
            W_res = getattr(esn, 'W_reservoir', getattr(esn, 'W', None))
            pre = W_in @ np.array([u_val]) + W_res @ x
            leak = getattr(esn, 'leak_rate', 1.0)
            x = (1.0 - leak) * x + leak * np.tanh(pre)
            states.append(x.copy())
            
    X_all = np.array(states) # (n_steps, N)
    
    # Descartar washout y considerar el retardo máximo
    valid_start = max(washout, max_delay)
    X = X_all[valid_start:]
    N_valid = len(X)
    
    # Añadir columna de bias para la regresión
    X_ext = np.hstack([np.ones((N_valid, 1)), X])
    
    mc_profile = np.zeros(max_delay)
    
    # 3. Evaluar para cada retardo k
    for k in range(1, max_delay + 1):
        target = u[valid_start - k : n_steps - k]
        
        # Ajustar pesos lineales W_out para predecir u(t-k)
        W_k = ridge_regression(X_ext, target, regularization=ridge_lambda)
        y_pred = X_ext @ W_k
        
        # Coeficiente de determinación r^2
        var_target = np.var(target)
        var_pred = np.var(y_pred)
        
        if var_target > 1e-12 and var_pred > 1e-12:
            cov = np.cov(target.ravel(), y_pred.ravel())[0, 1]
            r2 = (cov ** 2) / (var_target * var_pred)
            mc_profile[k - 1] = float(np.clip(r2, 0.0, 1.0))
        else:
            mc_profile[k - 1] = 0.0
            
    total_mc = float(np.sum(mc_profile))
    return total_mc, mc_profile


def analyze_signal_autocorrelation(signal: np.ndarray, max_lags: int = 50) -> Dict[str, Any]:
    """
    Analiza la autocorrelación temporal y el contenido frecuencial de una señal.
    
    Args:
        signal: Array 1D con la serie temporal del sensor
        max_lags: Lags temporales a evaluar
        
    Returns:
        Diccionario con métricas: tau_corr, acf, dominant_frequency, snr_est
    """
    sig = signal.ravel()
    N = len(sig)
    if N < 10:
        raise ValueError("Señal demasiado corta para análisis de autocorrelación.")
        
    sig_centered = sig - np.mean(sig)
    var = np.var(sig_centered)
    
    if var < 1e-12:
        return {
            "tau_corr": 1.0,
            "acf": np.ones(max_lags),
            "dominant_period": 1.0,
            "variance": 0.0
        }
        
    # Calcular autocorrelación normalizada
    max_l = min(max_lags, N // 2)
    acf = np.zeros(max_l)
    for lag in range(max_l):
        if lag == 0:
            acf[0] = 1.0
        else:
            acf[lag] = np.mean(sig_centered[:-lag] * sig_centered[lag:]) / var
            
    # Estimar tiempo de correlación tau_corr (lag donde ACF cae por debajo de 1/e)
    threshold = 1.0 / np.e
    tau_corr = 1.0
    for lag in range(1, max_l):
        if acf[lag] < threshold:
            tau_corr = float(lag)
            break
    else:
        tau_corr = float(max_l)
        
    # Periodo dominante vía FFT
    fft_vals = np.abs(np.fft.rfft(sig_centered))
    freqs = np.fft.rfftfreq(N)
    # Ignorar componente continua (index 0)
    if len(fft_vals) > 1:
        dom_idx = 1 + np.argmax(fft_vals[1:])
        dom_freq = freqs[dom_idx]
        dom_period = 1.0 / dom_freq if dom_freq > 0 else float(N)
    else:
        dom_period = float(N)
        
    return {
        "tau_corr": tau_corr,
        "acf": acf,
        "dominant_period": float(dom_period),
        "variance": float(var)
    }


def auto_tune_esn_parameters(
    signal: np.ndarray,
    n_reservoir: int = 50,
    dt: float = 1.0
) -> Dict[str, Any]:
    """
    Sintoniza analíticamente los hiperparámetros óptimos para un ESN
    en función de la dinámica temporal del sensor.
    
    Args:
        signal: Muestra representativa de la serie temporal (sensor)
        n_reservoir: Número de neuronas planificadas en el microcontrolador
        dt: Intervalo de muestreo temporal
        
    Returns:
        Diccionario con configuración recomendada para despliegue edge:
        (leak_rate, spectral_radius, input_scale, washout, recommended_reservoir)
    """
    analysis = analyze_signal_autocorrelation(signal)
    tau_corr = analysis["tau_corr"]
    
    # 1. Leak rate acoplado a la inercia temporal
    # Senales rápidas (tau_corr pequeño) -> alpha alto (cercano a 1)
    # Senales lentas (tau_corr grande) -> alpha bajo (cercano a 0)
    leak_rate = float(np.clip(1.0 - np.exp(-dt / max(1.0, tau_corr)), 0.05, 1.0))
    
    # 2. Spectral radius: Para retención de memoria larga conviene rho proximo a 0.95-0.99
    # Para señales de alta frecuencia o impulsivas conviene rho mas bajo (0.7-0.85)
    if tau_corr > 10:
        spectral_radius = 0.95
    elif tau_corr > 3:
        spectral_radius = 0.90
    else:
        spectral_radius = 0.75
        
    # 3. Escalamiento de entrada según desviación estándar de la señal
    std_sig = np.sqrt(analysis["variance"])
    if std_sig > 1e-6:
        # Se busca que el argumento de tanh opere mayoritariamente en la zona casi lineal [-1, 1]
        input_scale = float(np.clip(0.5 / std_sig, 0.01, 2.0))
    else:
        input_scale = 1.0
        
    # 4. Washout proporcional al tiempo de memoria
    washout = int(min(150, max(30, int(tau_corr * 4))))
    
    return {
        "leak_rate": round(leak_rate, 4),
        "spectral_radius": spectral_radius,
        "input_scale": round(input_scale, 4),
        "washout": washout,
        "n_reservoir": n_reservoir,
        "signal_tau_corr": tau_corr,
        "signal_dominant_period": analysis["dominant_period"]
    }
