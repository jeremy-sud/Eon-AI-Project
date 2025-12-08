"""
Proyecto Eón - Cuantización Extrema
Reduce la precisión de los pesos para demostrar que la inteligencia
reside en la estructura, no en la precisión numérica.

"Menos es Más" - La mayoría de bits son ruido, no información.
"""

import numpy as np
from typing import Tuple, Dict
import sys
sys.path.append('..')
from esn.esn import EchoStateNetwork, generate_mackey_glass


class QuantizedESN:
    """
    ESN con pesos cuantizados a precisión reducida.
    
    Soporta:
    - 8-bit: Rango [-128, 127]
    - 4-bit: Rango [-8, 7]
    - Binario (1-bit): Solo {-1, +1}
    """
    
    def __init__(self, esn: EchoStateNetwork, bits: int = 8):
        """
        Crea una versión cuantizada de una ESN entrenada.
        
        Args:
            esn: ESN entrenada original
            bits: Bits de precisión (8, 4, 2, o 1)
        """
        if esn.W_out is None:
            raise ValueError("La ESN debe estar entrenada antes de cuantizar")
            
        self.original_esn = esn
        self.bits = bits
        self.n_reservoir = esn.n_reservoir
        self.n_inputs = esn.n_inputs
        self.n_outputs = esn.n_outputs
        
        # Diccionario para parámetros de cuantización
        self.quant_params: Dict[str, dict] = {}
        
        # Cuantizar matrices
        self.W_in_q = self._quantize(esn.W_in, 'W_in')
        self.W_reservoir_q = self._quantize(esn.W_reservoir, 'W_reservoir')
        self.W_out_q = self._quantize(esn.W_out, 'W_out')
        
        # Estado (mantiene precisión float para operaciones)
        self.state = np.zeros(self.n_reservoir)
        
    def _quantize(self, weights: np.ndarray, name: str) -> np.ndarray:
        """
        Cuantiza una matriz de pesos y guarda parámetros para decuantización.
        
        Args:
            weights: Matriz de pesos float
            name: Nombre de la matriz (para guardar params)
            
        Returns:
            Pesos cuantizados
        """
        if self.bits == 1:
            # Cuantización binaria: sign con escalado
            scale = np.abs(weights).mean()
            self.quant_params[name] = {'scale': scale, 'offset': 0.0}
            return np.sign(weights).astype(np.int8)
        
        # Calcular rango según bits
        if self.bits == 8:
            q_min, q_max = -128, 127
            dtype = np.int8
        elif self.bits == 4:
            q_min, q_max = -8, 7
            dtype = np.int8
        elif self.bits == 2:
            q_min, q_max = -2, 1
            dtype = np.int8
        else:
            raise ValueError(f"Bits no soportados: {self.bits}")
        
        # Escalar al rango cuantizado
        w_min, w_max = weights.min(), weights.max()
        
        if w_max - w_min < 1e-10:
            self.quant_params[name] = {'scale': 1.0, 'offset': 0.0}
            return np.zeros_like(weights, dtype=dtype)
        
        scale = (w_max - w_min) / (q_max - q_min)
        offset = w_min - q_min * scale
        
        # Guardar parámetros
        self.quant_params[name] = {'scale': scale, 'offset': offset}
        
        # Cuantizar
        quantized = np.round((weights - offset) / scale).astype(dtype)
        quantized = np.clip(quantized, q_min, q_max)
        
        return quantized
    
    def _dequantize(self, weights_q: np.ndarray, name: str) -> np.ndarray:
        """Convierte pesos cuantizados a float para operaciones."""
        params = self.quant_params[name]
        
        if self.bits == 1:
            return weights_q.astype(np.float32) * params['scale']
        
        return weights_q.astype(np.float32) * params['scale'] + params['offset']
    
    def _update_state(self, input_vector: np.ndarray) -> np.ndarray:
        """Actualiza el estado usando pesos cuantizados."""
        # Decuantizar para operaciones
        W_in = self._dequantize(self.W_in_q, 'W_in')
        W_res = self._dequantize(self.W_reservoir_q, 'W_reservoir')
        
        input_contribution = np.dot(W_in, input_vector)
        reservoir_contribution = np.dot(W_res, self.state)
        
        self.state = np.tanh(input_contribution + reservoir_contribution)
        return self.state
    
    def predict(self, inputs: np.ndarray, reset_state: bool = False) -> np.ndarray:
        """Genera predicciones con el modelo cuantizado."""
        T = inputs.shape[0]
        
        if inputs.ndim == 1:
            inputs = inputs.reshape(-1, 1)
            
        if reset_state:
            self.state = np.zeros(self.n_reservoir)
            
        W_out = self._dequantize(self.W_out_q, 'W_out')
        predictions = np.zeros((T, self.n_outputs))
        
        for t in range(T):
            state = self._update_state(inputs[t])
            predictions[t] = np.dot(state, W_out)
            
        return predictions
    
    def reset(self):
        """Resetea el estado."""
        self.state = np.zeros(self.n_reservoir)
    
    def get_memory_footprint(self) -> dict:
        """Calcula uso de memoria del modelo cuantizado."""
        W_in_bytes = self.W_in_q.nbytes
        W_reservoir_bytes = self.W_reservoir_q.nbytes
        W_out_bytes = self.W_out_q.nbytes
        
        # Memoria teórica con empaquetamiento
        if self.bits == 4:
            theoretical_bytes = (W_in_bytes + W_reservoir_bytes + W_out_bytes) // 2
        elif self.bits == 1:
            theoretical_bytes = (W_in_bytes + W_reservoir_bytes + W_out_bytes) // 8
        else:
            theoretical_bytes = W_in_bytes + W_reservoir_bytes + W_out_bytes
        
        return {
            'W_in': W_in_bytes,
            'W_reservoir': W_reservoir_bytes,
            'W_out': W_out_bytes,
            'actual_bytes': W_in_bytes + W_reservoir_bytes + W_out_bytes,
            'theoretical_bytes': theoretical_bytes,
            'actual_kb': (W_in_bytes + W_reservoir_bytes + W_out_bytes) / 1024,
            'theoretical_kb': theoretical_bytes / 1024,
            'compression_ratio': (self.original_esn.get_memory_footprint()['total_bytes'] / 
                                 max(1, theoretical_bytes))
        }


def compare_quantization_levels(esn: EchoStateNetwork, X_test: np.ndarray, y_test: np.ndarray):
    """
    Compara el rendimiento en diferentes niveles de cuantización.
    """
    results = []
    
    # Rendimiento original (float64)
    esn.reset()
    pred_original = esn.predict(X_test)
    mse_original = np.mean((pred_original - y_test)**2)
    mem_original = esn.get_memory_footprint()
    
    results.append({
        'bits': 64,
        'name': 'Original (float64)',
        'mse': mse_original,
        'memory_kb': mem_original['total_kb'],
        'accuracy_retained': 100.0
    })
    
    # Cuantizaciones
    for bits in [8, 4, 1]:
        q_esn = QuantizedESN(esn, bits=bits)
        q_esn.reset()
        
        pred_q = q_esn.predict(X_test)
        mse_q = np.mean((pred_q - y_test)**2)
        mem_q = q_esn.get_memory_footprint()
        
        # Precisión retenida (1 - incremento relativo de MSE)
        if mse_original > 1e-10:
            accuracy_retained = max(0, min(100, (1 - (mse_q - mse_original) / mse_original) * 100))
        else:
            accuracy_retained = 100.0 if mse_q < 1e-10 else 0.0
        
        results.append({
            'bits': bits,
            'name': f'{bits}-bit' if bits > 1 else 'Binario (1-bit)',
            'mse': mse_q,
            'memory_kb': mem_q['theoretical_kb'],
            'accuracy_retained': accuracy_retained,
            'compression': mem_q['compression_ratio']
        })
    
    return results


def demo_quantization():
    """Demostración de cuantización extrema."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║          PROYECTO EÓN - Cuantización Extrema                  ║
║         "Menos es Más" - Los bits son ruido                   ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    print("[1/4] Preparando datos...")
    data = generate_mackey_glass(3000)
    data = (data - data.mean()) / data.std()
    
    X = data[:-1].reshape(-1, 1)
    y = data[1:].reshape(-1, 1)
    
    train_size = 2000
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]
    
    print("[2/4] Entrenando ESN original...")
    esn = EchoStateNetwork(
        n_inputs=1,
        n_reservoir=100,
        n_outputs=1,
        spectral_radius=0.9,
        random_state=42
    )
    esn.fit(X_train, y_train, washout=100)
    
    print("[3/4] Comparando niveles de cuantización...")
    results = compare_quantization_levels(esn, X_test, y_test)
    
    print("\n[4/4] Resultados:")
    print("-" * 70)
    print(f"{'Modelo':<20} {'MSE':<12} {'Memoria (KB)':<14} {'Precisión (%)':<14}")
    print("-" * 70)
    
    for r in results:
        print(f"{r['name']:<20} {r['mse']:<12.6f} {r['memory_kb']:<14.2f} {r['accuracy_retained']:<14.1f}")
    
    print("-" * 70)
    
    best_8bit = next(r for r in results if r['bits'] == 8)
    best_binary = next(r for r in results if r['bits'] == 1)
    
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                      CONCLUSIONES                             ║
╠═══════════════════════════════════════════════════════════════╣
║  • 8-bit retiene {best_8bit['accuracy_retained']:.1f}% precisión con 8x menos memoria     ║
║  • Binario retiene {best_binary['accuracy_retained']:.1f}% precisión con 64x menos memoria   ║
╚═══════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    demo_quantization()
