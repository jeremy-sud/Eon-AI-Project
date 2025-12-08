"""
Proyecto Eón - Lenguaje Natural Mínimo
======================================

Generación de texto carácter por carácter usando ESN.
Demuestra que un modelo de 1KB puede capturar patrones de lenguaje.

LIMITACIÓN: Esto es una demostración conceptual.
El modelo es demasiado pequeño para lenguaje complejo,
pero puede aprender patrones simples y repetitivos.

(c) 2024 Sistemas Ursol - Jeremy Arias Solano
"""

import sys
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "phase1-foundations" / "python"))

from esn.esn import EchoStateNetwork


class CharTokenizer:
    """
    Tokenizador a nivel de carácter.
    
    Convierte texto <-> vectores one-hot.
    """
    
    def __init__(self, chars: str = None):
        """
        Args:
            chars: Caracteres a incluir (None = autodetectar)
        """
        if chars:
            self.chars = sorted(set(chars))
        else:
            # Caracteres básicos por defecto
            self.chars = list(' abcdefghijklmnopqrstuvwxyz.,!?')
        
        self.char_to_idx = {c: i for i, c in enumerate(self.chars)}
        self.idx_to_char = {i: c for c, i in self.char_to_idx.items()}
        self.vocab_size = len(self.chars)
        
    def encode(self, text: str) -> np.ndarray:
        """Convierte texto a índices."""
        text = text.lower()
        indices = []
        for c in text:
            if c in self.char_to_idx:
                indices.append(self.char_to_idx[c])
            # Caracteres desconocidos se ignoran
        return np.array(indices)
    
    def decode(self, indices: np.ndarray) -> str:
        """Convierte índices a texto."""
        return ''.join(self.idx_to_char.get(int(i), '?') for i in indices)
    
    def to_onehot(self, indices: np.ndarray) -> np.ndarray:
        """Convierte índices a vectores one-hot."""
        onehot = np.zeros((len(indices), self.vocab_size))
        for i, idx in enumerate(indices):
            onehot[i, int(idx)] = 1
        return onehot
    
    def from_onehot(self, onehot: np.ndarray) -> np.ndarray:
        """Convierte one-hot a índices (argmax)."""
        return np.argmax(onehot, axis=1)
    
    def fit(self, text: str):
        """Ajusta el vocabulario al texto."""
        self.chars = sorted(set(text.lower()))
        self.char_to_idx = {c: i for i, c in enumerate(self.chars)}
        self.idx_to_char = {i: c for c, i in self.char_to_idx.items()}
        self.vocab_size = len(self.chars)


class TinyLM:
    """
    Modelo de Lenguaje Minimalista.
    
    Usa un ESN para predecir el siguiente carácter.
    Extremadamente simple, pero demuestra el concepto.
    """
    
    def __init__(self, n_reservoir: int = 64, tokenizer: CharTokenizer = None):
        """
        Args:
            n_reservoir: Neuronas del reservoir
            tokenizer: Tokenizador (se crea uno por defecto)
        """
        self.tokenizer = tokenizer or CharTokenizer()
        self.n_reservoir = n_reservoir
        self.esn = None
        self.is_trained = False
        
    def _create_esn(self):
        """Crea el ESN con el tamaño de vocabulario correcto."""
        self.esn = EchoStateNetwork(
            n_inputs=self.tokenizer.vocab_size,
            n_outputs=self.tokenizer.vocab_size,
            n_reservoir=self.n_reservoir,
            spectral_radius=0.95,
            sparsity=0.9
        )
        
    def train(self, text: str, washout: int = 50) -> float:
        """
        Entrena con un texto.
        
        Args:
            text: Texto de entrenamiento
            washout: Muestras iniciales a descartar
            
        Returns:
            Accuracy de predicción
        """
        # Ajustar tokenizer al texto
        self.tokenizer.fit(text)
        self._create_esn()
        
        # Convertir a secuencia
        indices = self.tokenizer.encode(text)
        
        if len(indices) < washout + 10:
            raise ValueError("Texto demasiado corto")
        
        # One-hot encoding
        onehot = self.tokenizer.to_onehot(indices)
        
        # X = caracteres, Y = siguiente carácter
        X = onehot[:-1]
        Y = onehot[1:]
        
        # Entrenar
        self.esn.fit(X, Y, washout=washout)
        self.is_trained = True
        
        # Calcular accuracy
        predictions = self.esn.predict(X)
        pred_indices = np.argmax(predictions, axis=1)
        real_indices = np.argmax(Y, axis=1)
        
        accuracy = np.mean(pred_indices == real_indices)
        return float(accuracy)
    
    def generate(self, prompt: str, length: int = 50, temperature: float = 0.8) -> str:
        """
        Genera texto a partir de un prompt.
        
        Args:
            prompt: Texto inicial
            length: Caracteres a generar
            temperature: Creatividad (0=determinista, >1=caótico)
            
        Returns:
            Texto generado (prompt + nuevo)
        """
        if not self.is_trained:
            raise RuntimeError("Modelo no entrenado")
        
        # Resetear estado
        self.esn.reset()
        
        # Procesar prompt para inicializar estado
        indices = self.tokenizer.encode(prompt)
        
        # Calentar el reservoir con el prompt
        for idx in indices:
            onehot = np.zeros(self.tokenizer.vocab_size)
            onehot[idx] = 1
            self.esn._update_state(onehot)
        
        # Generar
        generated = list(indices)
        current = indices[-1] if len(indices) > 0 else 0
        
        for _ in range(length):
            # Input actual (one-hot)
            onehot = np.zeros(self.tokenizer.vocab_size)
            onehot[current] = 1
            
            # Actualizar estado y obtener output
            state = self.esn._update_state(onehot)
            output = np.dot(state, self.esn.W_out)
            
            # Aplicar temperatura (softmax con temp)
            output = output / (temperature + 1e-8)
            exp_out = np.exp(output - np.max(output))
            probs = exp_out / np.sum(exp_out)
            
            # Samplear siguiente carácter
            current = np.random.choice(len(probs), p=probs)
            generated.append(current)
        
        return self.tokenizer.decode(np.array(generated))
    
    def get_stats(self) -> Dict:
        """Estadísticas del modelo."""
        return {
            'n_reservoir': self.n_reservoir,
            'vocab_size': self.tokenizer.vocab_size,
            'vocab': ''.join(self.tokenizer.chars[:20]) + '...' if len(self.tokenizer.chars) > 20 else ''.join(self.tokenizer.chars),
            'is_trained': self.is_trained,
            'memory_approx_kb': (self.n_reservoir * self.tokenizer.vocab_size * 2 * 4) / 1024  # W_in + W_out
        }


# Demo
if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║       PROYECTO EÓN - LENGUAJE NATURAL MÍNIMO                  ║
║           "Generación de texto en kilobytes"                  ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Texto de entrenamiento (repetitivo para que aprenda patrones)
    training_text = """
    la inteligencia no se crea, se descubre.
    el conocimiento emerge de la simplicidad.
    la nada es todo, todo es nada.
    el caos contiene el orden.
    """ * 20  # Repetir para más datos
    
    print("[1/3] Creando modelo...")
    model = TinyLM(n_reservoir=64)
    
    print("\n[2/3] Entrenando...")
    accuracy = model.train(training_text, washout=30)
    print(f"      Accuracy: {accuracy:.2%}")
    
    stats = model.get_stats()
    print(f"      Vocabulario: {stats['vocab_size']} caracteres")
    print(f"      Memoria aprox: {stats['memory_approx_kb']:.1f} KB")
    
    print("\n[3/3] Generando texto...")
    
    prompts = ["la inteligencia ", "el conocimiento ", "la nada "]
    
    for prompt in prompts:
        generated = model.generate(prompt, length=40, temperature=0.7)
        print(f"\n      Prompt: \"{prompt}\"")
        print(f"      Output: \"{generated}\"")
    
    print("\n" + "="*60)
    print("NOTA: Este es un modelo minimalista de demostración.")
    print("No pretende competir con GPT, sino mostrar que patrones")
    print("de lenguaje pueden emerger de recursos mínimos.")
    print("="*60)
    
    print("\n✓ Demo completado")
    print("Proyecto Eón - Sistemas Ursol")
