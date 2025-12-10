"""
Proyecto Eón - Recursive Echo State Network
============================================

Implementación del principio hermético "Como es Arriba, es Abajo".

El microcosmos refleja al macrocosmos: cada "neurona" del reservoir
es en sí misma un pequeño reservoir (un mini-Eón).

Arquitectura Fractal:
                    ┌─────────────────┐
                    │   Nivel Macro   │  ← Procesa patrones lentos (minutos)
                    │  (10 sub-ESN)   │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │  Mini-ESN 1   │ │  Mini-ESN 2   │ │  Mini-ESN N   │
    │ (8 neuronas)  │ │ (8 neuronas)  │ │ (8 neuronas)  │
    │               │ │               │ │               │  ← Procesan patrones
    │ Escala: 1x    │ │ Escala: 2x    │ │ Escala: Nx    │     rápidos (μs)
    └───────────────┘ └───────────────┘ └───────────────┘

Ventaja: Procesa patrones a múltiples escalas temporales
         usando el mismo código recursivo.

"Quod est inferius est sicut quod est superius"
                    - La Tabla Esmeralda

(c) 2024 Sistemas Ursol - Jeremy Arias Solano
"""

import numpy as np
from typing import Optional, List, Tuple, Literal
from dataclasses import dataclass


@dataclass
class FractalLevel:
    """Configuración de un nivel en la jerarquía fractal."""
    n_units: int           # Número de unidades (sub-ESNs o neuronas)
    n_internal: int        # Neuronas internas por unidad (0 = neurona simple)
    time_scale: float      # Escala temporal (1.0 = normal, 2.0 = 2x más lento)
    spectral_radius: float # Radio espectral para este nivel
    sparsity: float        # Escasez de conexiones


class MicroReservoir:
    """
    Un micro-reservoir que actúa como una "neurona compleja".
    
    Este es el nivel "Abajo" del principio hermético:
    una neurona que internamente es un pequeño ESN.
    
    Procesa patrones a una escala temporal específica.
    """
    
    def __init__(
        self,
        n_inputs: int,
        n_internal: int = 8,
        time_scale: float = 1.0,
        spectral_radius: float = 0.9,
        sparsity: float = 0.8,
        rng: Optional[np.random.RandomState] = None
    ):
        """
        Args:
            n_inputs: Dimensión de entrada
            n_internal: Neuronas internas del micro-reservoir
            time_scale: Escala temporal (mayor = más lento, más memoria)
            spectral_radius: Radio espectral
            sparsity: Escasez de conexiones
            rng: Generador aleatorio
        """
        self.n_inputs = n_inputs
        self.n_internal = n_internal
        self.time_scale = time_scale
        self.spectral_radius = spectral_radius
        self.sparsity = sparsity
        self.rng = rng or np.random.RandomState()
        
        # Pesos internos
        self.W_in = self.rng.uniform(-1, 1, (n_internal, n_inputs))
        
        # Matriz recurrente interna
        W = self.rng.uniform(-1, 1, (n_internal, n_internal))
        mask = self.rng.random((n_internal, n_internal)) > sparsity
        W *= mask
        
        # Escalar al radio espectral
        eigenvalues = np.abs(np.linalg.eigvals(W))
        if eigenvalues.max() > 0:
            W *= spectral_radius / eigenvalues.max()
        
        self.W_internal = W
        
        # Estado interno
        self.state = np.zeros(n_internal)
        
        # Acumulador para escala temporal
        # Permite que este micro-reservoir "piense más lento"
        self._accumulated_input = np.zeros(n_inputs)
        self._accumulation_count = 0
        self._update_threshold = max(1, int(time_scale))
    
    def update(self, input_vec: np.ndarray, noise: float = 0.001) -> np.ndarray:
        """
        Actualiza el estado del micro-reservoir.
        
        Si time_scale > 1, acumula inputs antes de actualizar
        (procesa patrones más lentos).
        
        Args:
            input_vec: Vector de entrada
            noise: Nivel de ruido
            
        Returns:
            Estado actual (puede no cambiar si está acumulando)
        """
        # Acumular input para escala temporal
        self._accumulated_input += input_vec
        self._accumulation_count += 1
        
        # Solo actualizar cuando alcanzamos el umbral
        if self._accumulation_count >= self._update_threshold:
            avg_input = self._accumulated_input / self._accumulation_count
            
            # Ecuación estándar del reservoir
            input_contribution = np.dot(self.W_in, avg_input)
            internal_contribution = np.dot(self.W_internal, self.state)
            noise_contribution = noise * self.rng.randn(self.n_internal)
            
            self.state = np.tanh(
                input_contribution + internal_contribution + noise_contribution
            )
            
            # Reset acumuladores
            self._accumulated_input = np.zeros(self.n_inputs)
            self._accumulation_count = 0
        
        return self.state
    
    def get_output(self) -> float:
        """
        Retorna un valor escalar como "salida" de esta neurona.
        
        Usa la media del estado interno como señal agregada.
        """
        return float(np.mean(self.state))
    
    def reset(self) -> None:
        """Resetea el estado interno."""
        self.state = np.zeros(self.n_internal)
        self._accumulated_input = np.zeros(self.n_inputs)
        self._accumulation_count = 0


class RecursiveEchoStateNetwork:
    """
    Echo State Network Recursivo/Fractal.
    
    Implementa el principio hermético "Como es Arriba, es Abajo":
    cada unidad del reservoir puede ser un micro-reservoir.
    
    Arquitectura:
    - Nivel Superior (Macro): Conexiones entre unidades
    - Nivel Inferior (Micro): Cada unidad es un mini-ESN
    
    Esto permite procesar patrones a múltiples escalas temporales:
    - Las unidades con time_scale=1 capturan patrones rápidos
    - Las unidades con time_scale=10 capturan patrones lentos
    
    Ventajas:
    1. Memoria multi-escala natural
    2. Jerarquía emergente sin supervisión
    3. Mismo código recursivo para todos los niveles
    4. Eficiente: solo entrena W_out (como ESN normal)
    """
    
    def __init__(
        self,
        n_inputs: int = 1,
        n_outputs: int = 1,
        n_macro_units: int = 10,
        n_micro_neurons: int = 8,
        time_scales: Optional[List[float]] = None,
        spectral_radius: float = 0.9,
        macro_spectral_radius: float = 0.95,
        sparsity: float = 0.8,
        macro_sparsity: float = 0.7,
        noise: float = 0.001,
        random_state: Optional[int] = None
    ):
        """
        Args:
            n_inputs: Dimensión de entrada
            n_outputs: Dimensión de salida
            n_macro_units: Número de unidades macro (cada una es un micro-ESN)
            n_micro_neurons: Neuronas por micro-ESN
            time_scales: Escalas temporales para cada unidad (None = automático)
            spectral_radius: Radio espectral de micro-reservoirs
            macro_spectral_radius: Radio espectral de conexiones macro
            sparsity: Escasez en micro-reservoirs
            macro_sparsity: Escasez en conexiones macro
            noise: Nivel de ruido
            random_state: Semilla aleatoria
        """
        self.n_inputs = n_inputs
        self.n_outputs = n_outputs
        self.n_macro_units = n_macro_units
        self.n_micro_neurons = n_micro_neurons
        self.noise = noise
        
        # Generador aleatorio
        self.rng = np.random.RandomState(random_state)
        
        # === NIVEL MICRO (Abajo) ===
        # Crear micro-reservoirs con diferentes escalas temporales
        if time_scales is None:
            # Distribución logarítmica de escalas (1, 2, 4, 8, ...)
            time_scales = [2 ** (i * 0.5) for i in range(n_macro_units)]
        
        self.time_scales = time_scales[:n_macro_units]
        
        self.micro_reservoirs: List[MicroReservoir] = []
        for i in range(n_macro_units):
            scale = self.time_scales[i] if i < len(self.time_scales) else 1.0
            micro = MicroReservoir(
                n_inputs=n_inputs,
                n_internal=n_micro_neurons,
                time_scale=scale,
                spectral_radius=spectral_radius,
                sparsity=sparsity,
                rng=np.random.RandomState(self.rng.randint(0, 2**31))
            )
            self.micro_reservoirs.append(micro)
        
        # === NIVEL MACRO (Arriba) ===
        # Conexiones entre micro-reservoirs
        # Cada micro-reservoir también recibe input de otros
        self.W_macro = self.rng.uniform(-1, 1, (n_macro_units, n_macro_units))
        mask = self.rng.random((n_macro_units, n_macro_units)) > macro_sparsity
        self.W_macro *= mask
        
        # Escalar al radio espectral macro
        eigenvalues = np.abs(np.linalg.eigvals(self.W_macro))
        if eigenvalues.max() > 0:
            self.W_macro *= macro_spectral_radius / eigenvalues.max()
        
        # Estado macro (salidas de cada micro-reservoir)
        self.macro_state = np.zeros(n_macro_units)
        
        # === CAPA DE SALIDA (única que se entrena) ===
        # Usa estados de todos los niveles
        self.n_total_state = n_macro_units * (n_micro_neurons + 1)
        self.W_out: Optional[np.ndarray] = None
        
        # Metadatos
        import time
        self.birth_time = int(time.time())
        self._calculate_birth_hash()
    
    def _calculate_birth_hash(self) -> None:
        """Genera hash de nacimiento."""
        state = self.rng.randint(0, 2**31) ^ self.birth_time
        bytes_list = []
        curr = state & 0xFFFFFFFF
        for _ in range(16):
            curr = (curr * 1103515245 + 12345) & 0x7fffffff
            bytes_list.append(curr & 0xFF)
        self.birth_hash = ''.join(f'{b:02x}' for b in bytes_list)
    
    def _get_full_state(self) -> np.ndarray:
        """
        Obtiene el estado completo de todos los niveles.
        
        Combina:
        - Estados internos de cada micro-reservoir
        - Estado macro (agregado)
        
        Esto es la "lectura" del sistema fractal completo.
        """
        states = []
        
        for i, micro in enumerate(self.micro_reservoirs):
            # Estado interno del micro-reservoir
            states.append(micro.state)
            # Salida agregada (conexión al nivel macro)
            states.append(np.array([self.macro_state[i]]))
        
        return np.concatenate(states)
    
    def _update_state(self, input_vector: np.ndarray) -> np.ndarray:
        """
        Actualiza el estado de toda la red fractal.
        
        1. Calcula influencia macro (entre micro-reservoirs)
        2. Actualiza cada micro-reservoir con input + influencia macro
        3. Actualiza estado macro
        
        Args:
            input_vector: Vector de entrada
            
        Returns:
            Estado completo (todos los niveles)
        """
        # 1. Influencia macro: cada micro-reservoir recibe señales de otros
        macro_influence = np.dot(self.W_macro, self.macro_state)
        
        # 2. Actualizar cada micro-reservoir
        new_macro_state = np.zeros(self.n_macro_units)
        
        for i, micro in enumerate(self.micro_reservoirs):
            # El input al micro incluye: entrada externa + influencia de otros
            combined_input = input_vector + macro_influence[i] * 0.1
            
            # Actualizar micro-reservoir
            micro.update(combined_input, self.noise)
            
            # Obtener salida agregada para nivel macro
            new_macro_state[i] = micro.get_output()
        
        self.macro_state = new_macro_state
        
        return self._get_full_state()
    
    def fit(
        self, 
        inputs: np.ndarray, 
        outputs: np.ndarray, 
        washout: int = 100
    ) -> 'RecursiveEchoStateNetwork':
        """
        Entrena SOLO la capa de salida.
        
        El principio "La Nada es Todo" aplica a todos los niveles:
        los micro-reservoirs nunca se entrenan, solo W_out.
        
        Args:
            inputs: Secuencia de entrada (T, n_inputs)
            outputs: Secuencia objetivo (T, n_outputs)
            washout: Pasos iniciales a descartar
            
        Returns:
            self
        """
        T = inputs.shape[0]
        
        if inputs.ndim == 1:
            inputs = inputs.reshape(-1, 1)
        if outputs.ndim == 1:
            outputs = outputs.reshape(-1, 1)
        
        # Recolectar estados de todos los niveles
        states = np.zeros((T, self.n_total_state))
        
        # Reset
        self.reset()
        
        # Pasar todos los inputs
        for t in range(T):
            states[t] = self._update_state(inputs[t])
        
        # Descartar washout
        states = states[washout:]
        outputs_train = outputs[washout:]
        
        # Regresión Ridge
        reg = 1e-6
        S = states
        Y = outputs_train
        
        self.W_out = np.dot(
            np.linalg.inv(np.dot(S.T, S) + reg * np.eye(self.n_total_state)),
            np.dot(S.T, Y)
        )
        
        return self
    
    def predict(self, inputs: np.ndarray, reset_state: bool = False) -> np.ndarray:
        """
        Genera predicciones.
        
        Args:
            inputs: Secuencia de entrada
            reset_state: Si resetear antes de predecir
            
        Returns:
            Predicciones
        """
        if self.W_out is None:
            raise ValueError("Modelo no entrenado")
        
        T = inputs.shape[0]
        
        if inputs.ndim == 1:
            inputs = inputs.reshape(-1, 1)
        
        if reset_state:
            self.reset()
        
        predictions = np.zeros((T, self.n_outputs))
        
        for t in range(T):
            state = self._update_state(inputs[t])
            predictions[t] = np.dot(state, self.W_out)
        
        return predictions
    
    def predict_generative(self, n_steps: int, initial_input: np.ndarray) -> np.ndarray:
        """Genera secuencia de forma autónoma."""
        if self.W_out is None:
            raise ValueError("Modelo no entrenado")
        
        predictions = np.zeros((n_steps, self.n_outputs))
        current_input = initial_input.reshape(-1)
        
        for t in range(n_steps):
            state = self._update_state(current_input)
            output = np.dot(state, self.W_out)
            predictions[t] = output
            current_input = output.flatten()
        
        return predictions
    
    def reset(self) -> None:
        """Resetea todos los niveles."""
        self.macro_state = np.zeros(self.n_macro_units)
        for micro in self.micro_reservoirs:
            micro.reset()
    
    def get_memory_footprint(self) -> dict:
        """Calcula uso de memoria."""
        micro_bytes = sum(
            m.W_in.nbytes + m.W_internal.nbytes + m.state.nbytes
            for m in self.micro_reservoirs
        )
        macro_bytes = self.W_macro.nbytes + self.macro_state.nbytes
        w_out_bytes = self.W_out.nbytes if self.W_out is not None else 0
        
        total = micro_bytes + macro_bytes + w_out_bytes
        
        return {
            'micro_reservoirs_bytes': micro_bytes,
            'macro_level_bytes': macro_bytes,
            'W_out_bytes': w_out_bytes,
            'total_bytes': total,
            'total_kb': total / 1024,
            'n_parameters': self.n_total_state * self.n_outputs if self.W_out is not None else 0
        }
    
    def get_architecture_summary(self) -> str:
        """Resumen de la arquitectura fractal."""
        lines = [
            "╔══════════════════════════════════════════════════════════╗",
            "║     RECURSIVE ESN - 'Como es Arriba, es Abajo'          ║",
            "╠══════════════════════════════════════════════════════════╣",
            f"║ Nivel MACRO: {self.n_macro_units} unidades                              ║",
            f"║ Nivel MICRO: {self.n_micro_neurons} neuronas/unidad                      ║",
            f"║ Estado Total: {self.n_total_state} dimensiones                        ║",
            "╠══════════════════════════════════════════════════════════╣",
            "║ Escalas Temporales:                                      ║",
        ]
        
        for i, scale in enumerate(self.time_scales[:5]):
            lines.append(f"║   Unidad {i}: {scale:.2f}x                                       ║"[:62] + "║")
        
        if len(self.time_scales) > 5:
            lines.append(f"║   ... ({len(self.time_scales) - 5} más)                                         ║"[:62] + "║")
        
        lines.append("╚══════════════════════════════════════════════════════════╝")
        
        return "\n".join(lines)


def demo_recursive_esn():
    """Demostración del ESN Recursivo."""
    from esn import generate_mackey_glass
    
    print("=" * 60)
    print("  RECURSIVE ESN - 'Como es Arriba, es Abajo'")
    print("  Arquitectura Fractal para Multi-Escala Temporal")
    print("=" * 60)
    print()
    
    # Generar datos
    print("Generando serie Mackey-Glass...")
    data = generate_mackey_glass(2000)
    
    X = data[:-1].reshape(-1, 1)
    y = data[1:].reshape(-1, 1)
    
    train_size = 1500
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]
    
    # Crear ESN Recursivo
    print("\nCreando RecursiveEchoStateNetwork...")
    resn = RecursiveEchoStateNetwork(
        n_inputs=1,
        n_outputs=1,
        n_macro_units=10,
        n_micro_neurons=8,
        time_scales=[1, 1.5, 2, 3, 4, 6, 8, 12, 16, 24],
        random_state=42
    )
    
    print(resn.get_architecture_summary())
    print()
    
    # Entrenar
    print("Entrenando (solo W_out, como siempre)...")
    resn.fit(X_train, y_train, washout=100)
    
    # Evaluar
    resn.reset()
    predictions = resn.predict(X_test)
    mse = np.mean((predictions - y_test) ** 2)
    
    print(f"\nResultados:")
    print(f"  MSE: {mse:.6f}")
    print(f"  RMSE: {np.sqrt(mse):.6f}")
    
    # Comparar con ESN normal
    from esn import EchoStateNetwork
    
    print("\nComparación con ESN estándar (100 neuronas):")
    esn = EchoStateNetwork(n_inputs=1, n_outputs=1, n_reservoir=100, random_state=42)
    esn.fit(X_train, y_train, washout=100)
    esn.reset()
    esn_predictions = esn.predict(X_test)
    esn_mse = np.mean((esn_predictions - y_test) ** 2)
    print(f"  ESN estándar MSE: {esn_mse:.6f}")
    print(f"  RecursiveESN MSE: {mse:.6f}")
    
    # Memoria
    memory = resn.get_memory_footprint()
    print(f"\nUso de memoria RecursiveESN:")
    print(f"  Micro-reservoirs: {memory['micro_reservoirs_bytes'] / 1024:.2f} KB")
    print(f"  Nivel macro: {memory['macro_level_bytes'] / 1024:.2f} KB")
    print(f"  Total: {memory['total_kb']:.2f} KB")


if __name__ == "__main__":
    demo_recursive_esn()
