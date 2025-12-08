"""
Proyecto Eón - Echo State Network (ESN)
Implementación minimalista usando solo NumPy

"La Nada es Todo" - El reservoir aleatorio no entrenado contiene
toda la computación necesaria. Solo entrenamos la capa de salida.
"""

import numpy as np
from typing import Optional, Tuple


class EchoStateNetwork:
    """
    Echo State Network para Proyecto Eón.
    
    Filosofía: El reservoir es aleatorio y NUNCA se entrena.
    Solo la matriz de salida (W_out) aprende mediante regresión lineal.
    
    Attributes:
        n_inputs: Número de entradas
        n_reservoir: Número de neuronas en el reservoir
        n_outputs: Número de salidas
        spectral_radius: Radio espectral (controla estabilidad)
        sparsity: Proporción de conexiones cero en el reservoir
        noise: Ruido añadido para regularización
    """
    
    def __init__(
        self,
        n_inputs: int = 1,
        n_reservoir: int = 100,
        n_outputs: int = 1,
        spectral_radius: float = 0.9,
        sparsity: float = 0.9,
        noise: float = 0.001,
        random_state: Optional[int] = None
    ):
        self.n_inputs = n_inputs
        self.n_reservoir = n_reservoir
        self.n_outputs = n_outputs
        self.spectral_radius = spectral_radius
        self.sparsity = sparsity
        self.noise = noise
        
        # Inicializar generador aleatorio
        self.rng = np.random.RandomState(random_state)
        
        # === MOMENTO CERO (Standardized DNA) ===
        import time
        self.birth_time = int(time.time())
        seed = random_state if random_state is not None else self.birth_time
        self.birth_hash = self._generate_hash(seed, self.birth_time)
        
        # Inicializar matrices
        self._initialize_weights()
        
        # Estado del reservoir
        self.state = np.zeros(n_reservoir)
        
        # Matriz de salida (la única que se entrena)
        self.W_out: Optional[np.ndarray] = None

    def _generate_hash(self, seed: int, timestamp: int) -> str:
        """Genera hash de nacimiento estandarizado (compatible con C/JS)."""
        state = seed ^ timestamp
        # LCG constants from C implementation (mixed/simplified)
        # Using a simple Python implementation to mimic the C logic 
        # C: state = (state * 1103515245 + 12345) & 0x7fffffff
        
        bytes_list = []
        curr = state & 0xFFFFFFFF
        for _ in range(16):
            curr = (curr * 1103515245 + 12345) & 0x7fffffff
            bytes_list.append(curr & 0xFF)
            
        return ''.join(f'{b:02x}' for b in bytes_list)
        
    def _initialize_weights(self):
        """Inicializa las matrices de pesos aleatorios."""
        
        # Matriz de entrada: conexiones aleatorias input -> reservoir
        self.W_in = self.rng.uniform(-1, 1, (self.n_reservoir, self.n_inputs))
        
        # Matriz del reservoir: conexiones recurrentes
        # Aplicamos escasez (sparsity) para eficiencia
        W = self.rng.uniform(-1, 1, (self.n_reservoir, self.n_reservoir))
        mask = self.rng.random((self.n_reservoir, self.n_reservoir)) > self.sparsity
        W *= mask
        
        # Escalar al radio espectral deseado para estabilidad
        # El eigenvalor máximo controla la "memoria" del sistema
        eigenvalues = np.abs(np.linalg.eigvals(W))
        if eigenvalues.max() > 0:
            W *= self.spectral_radius / eigenvalues.max()
        
        self.W_reservoir = W
        
    def _update_state(self, input_vector: np.ndarray) -> np.ndarray:
        """
        Actualiza el estado del reservoir dado un input.
        
        Ecuación: state(t+1) = tanh(W_in * input + W_reservoir * state(t) + noise)
        
        Args:
            input_vector: Vector de entrada
            
        Returns:
            Nuevo estado del reservoir
        """
        # Proyección del input
        input_contribution = np.dot(self.W_in, input_vector)
        
        # Recurrencia del reservoir
        reservoir_contribution = np.dot(self.W_reservoir, self.state)
        
        # Ruido para regularización
        noise_contribution = self.noise * self.rng.randn(self.n_reservoir)
        
        # Nuevo estado con no-linealidad tanh
        self.state = np.tanh(input_contribution + reservoir_contribution + noise_contribution)
        
        return self.state
    
    def fit(self, inputs: np.ndarray, outputs: np.ndarray, washout: int = 100) -> 'EchoStateNetwork':
        """
        Entrena SOLO la capa de salida mediante regresión lineal.
        
        El reservoir NUNCA se modifica. Esto es "La Nada es Todo":
        el reservoir aleatorio ya contiene toda la representación necesaria,
        solo necesitamos aprender a leerla.
        
        Args:
            inputs: Secuencia de entrada (T, n_inputs)
            outputs: Secuencia objetivo (T, n_outputs)
            washout: Pasos iniciales a descartar (para que el estado converja)
            
        Returns:
            self (para encadenamiento)
        """
        T = inputs.shape[0]
        
        # Asegurar dimensiones correctas
        if inputs.ndim == 1:
            inputs = inputs.reshape(-1, 1)
        if outputs.ndim == 1:
            outputs = outputs.reshape(-1, 1)
            
        # Recolectar estados del reservoir
        states = np.zeros((T, self.n_reservoir))
        
        # Reset estado inicial
        self.state = np.zeros(self.n_reservoir)
        
        # Pasar todos los inputs por el reservoir
        for t in range(T):
            states[t] = self._update_state(inputs[t])
            
        # Descartar período de "calentamiento" (washout)
        states = states[washout:]
        outputs_train = outputs[washout:]
        
        # Regresión lineal con regularización Ridge
        # W_out = (S^T * S + λI)^(-1) * S^T * Y
        reg = 1e-6  # Regularización
        S = states
        Y = outputs_train
        
        self.W_out = np.dot(
            np.linalg.inv(np.dot(S.T, S) + reg * np.eye(self.n_reservoir)),
            np.dot(S.T, Y)
        )
        
        return self
    
    def predict(self, inputs: np.ndarray, reset_state: bool = False) -> np.ndarray:
        """
        Genera predicciones para una secuencia de entrada.
        
        Args:
            inputs: Secuencia de entrada (T, n_inputs)
            reset_state: Si resetear el estado antes de predecir
            
        Returns:
            Predicciones (T, n_outputs)
        """
        if self.W_out is None:
            raise ValueError("El modelo debe ser entrenado primero con fit()")
            
        T = inputs.shape[0]
        
        if inputs.ndim == 1:
            inputs = inputs.reshape(-1, 1)
            
        if reset_state:
            self.state = np.zeros(self.n_reservoir)
            
        predictions = np.zeros((T, self.n_outputs))
        
        for t in range(T):
            state = self._update_state(inputs[t])
            predictions[t] = np.dot(state, self.W_out)
            
        return predictions
    
    def predict_generative(self, n_steps: int, initial_input: np.ndarray) -> np.ndarray:
        """
        Genera predicciones de forma autónoma (sin entrada externa).
        
        La salida en t se convierte en entrada en t+1.
        Esto demuestra que el modelo ha "aprendido" la dinámica del sistema.
        
        Args:
            n_steps: Número de pasos a generar
            initial_input: Input inicial para comenzar
            
        Returns:
            Secuencia generada (n_steps, n_outputs)
        """
        if self.W_out is None:
            raise ValueError("El modelo debe ser entrenado primero con fit()")
            
        predictions = np.zeros((n_steps, self.n_outputs))
        current_input = initial_input.reshape(1, -1) if initial_input.ndim == 1 else initial_input
        
        for t in range(n_steps):
            state = self._update_state(current_input.flatten())
            output = np.dot(state, self.W_out)
            predictions[t] = output
            current_input = output  # Realimentación
            
        return predictions
    
    def get_memory_footprint(self) -> dict:
        """
        Calcula el uso de memoria del modelo.
        
        Returns:
            Diccionario con estadísticas de memoria
        """
        W_in_bytes = self.W_in.nbytes
        W_reservoir_bytes = self.W_reservoir.nbytes
        W_out_bytes = self.W_out.nbytes if self.W_out is not None else 0
        state_bytes = self.state.nbytes
        
        total = W_in_bytes + W_reservoir_bytes + W_out_bytes + state_bytes
        
        return {
            'W_in': W_in_bytes,
            'W_reservoir': W_reservoir_bytes,
            'W_out': W_out_bytes,
            'state': state_bytes,
            'total_bytes': total,
            'total_kb': total / 1024,
            'total_mb': total / (1024 * 1024)
        }
    
    def reset(self):
        """Resetea el estado del reservoir a ceros."""
        self.state = np.zeros(self.n_reservoir)


def generate_mackey_glass(n_samples: int = 2000, tau: int = 17, delta_t: float = 1.0) -> np.ndarray:
    """
    Genera la serie temporal Mackey-Glass.
    
    Esta es una serie caótica clásica usada para evaluar modelos de predicción.
    Es determinista pero altamente no-lineal.
    
    Args:
        n_samples: Número de muestras a generar
        tau: Parámetro de retardo (17 produce caos)
        delta_t: Paso temporal
        
    Returns:
        Serie temporal Mackey-Glass
    """
    # Inicialización
    history_len = tau
    x_history = np.ones(history_len) * 1.2
    x_t = 1.2
    
    series = np.zeros(n_samples)
    
    for t in range(n_samples):
        # Ecuación de Mackey-Glass
        x_tau = x_history[0]
        dx = delta_t * (0.2 * x_tau / (1.0 + x_tau**10) - 0.1 * x_t)
        x_t = x_t + dx
        
        # Actualizar historia
        x_history = np.roll(x_history, -1)
        x_history[-1] = x_t
        
        series[t] = x_t
        
    return series


if __name__ == "__main__":
    # Ejemplo básico de uso
    print("=== Proyecto Eón - ESN Demo ===\n")
    
    # Generar datos
    print("Generando serie Mackey-Glass...")
    data = generate_mackey_glass(2000)
    
    # Preparar datos de entrenamiento (predecir el siguiente valor)
    X = data[:-1].reshape(-1, 1)
    y = data[1:].reshape(-1, 1)
    
    # División train/test
    train_size = 1500
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]
    
    # Crear y entrenar ESN
    print("Creando ESN con reservoir de 100 neuronas...")
    esn = EchoStateNetwork(
        n_inputs=1,
        n_reservoir=100,
        n_outputs=1,
        spectral_radius=0.9,
        sparsity=0.9,
        random_state=42
    )
    
    print("Entrenando (solo la capa de salida)...")
    esn.fit(X_train, y_train, washout=100)
    
    # Evaluar
    esn.reset()
    predictions = esn.predict(X_test)
    mse = np.mean((predictions - y_test)**2)
    
    print(f"\nResultados:")
    print(f"  MSE en test: {mse:.6f}")
    print(f"  RMSE en test: {np.sqrt(mse):.6f}")
    
    # Memoria
    memory = esn.get_memory_footprint()
    print(f"\nUso de memoria:")
    print(f"  Total: {memory['total_kb']:.2f} KB")
    
    print("\n✓ Demo completada. Ejecute demo_prediction.py para visualización.")
