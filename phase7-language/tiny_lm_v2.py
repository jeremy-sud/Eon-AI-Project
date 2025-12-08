"""
Proyecto Eón - TinyLM v2: Modelo de Lenguaje Mejorado
=====================================================

Versión mejorada con:
- Tokenización por palabras (no caracteres)
- Embeddings densos
- Reservoir más grande (256 neuronas)
- Greedy/Beam decoding

(c) 2024 Sistemas Ursol - Jeremy Arias Solano
"""

import sys
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import Counter

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "phase1-foundations" / "python"))

from esn.esn import EchoStateNetwork


class WordTokenizer:
    """
    Tokenizador a nivel de palabra con embeddings simples.
    """
    
    def __init__(self, vocab_size: int = 500, embedding_dim: int = 32):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.word_to_idx: Dict[str, int] = {}
        self.idx_to_word: Dict[int, str] = {}
        self.embeddings: Optional[np.ndarray] = None
        
        # Tokens especiales
        self.PAD = "<PAD>"
        self.UNK = "<UNK>"
        self.BOS = "<BOS>"
        self.EOS = "<EOS>"
        
    def fit(self, text: str):
        """Construye vocabulario y embeddings."""
        # Tokenizar
        words = self._tokenize(text)
        
        # Contar frecuencias
        counter = Counter(words)
        
        # Tokens especiales + más frecuentes
        vocab = [self.PAD, self.UNK, self.BOS, self.EOS]
        vocab += [w for w, _ in counter.most_common(self.vocab_size - len(vocab))]
        
        self.word_to_idx = {w: i for i, w in enumerate(vocab)}
        self.idx_to_word = {i: w for w, i in self.word_to_idx.items()}
        self.actual_vocab_size = len(vocab)
        
        # Crear embeddings aleatorios (en un modelo real serían aprendidos)
        np.random.seed(42)
        self.embeddings = np.random.randn(self.actual_vocab_size, self.embedding_dim) * 0.1
        # Hacer PAD = ceros
        self.embeddings[0] = 0
        
    def _tokenize(self, text: str) -> List[str]:
        """Tokeniza texto en palabras."""
        # Normalizar
        text = text.lower()
        # Separar puntuación
        for p in '.,!?;:\n':
            text = text.replace(p, f' {p} ')
        return text.split()
    
    def encode(self, text: str) -> np.ndarray:
        """Convierte texto a índices."""
        words = self._tokenize(text)
        unk_idx = self.word_to_idx[self.UNK]
        return np.array([self.word_to_idx.get(w, unk_idx) for w in words])
    
    def decode(self, indices: np.ndarray) -> str:
        """Convierte índices a texto."""
        words = [self.idx_to_word.get(int(i), self.UNK) for i in indices]
        # Limpiar tokens especiales
        words = [w for w in words if w not in [self.PAD, self.BOS, self.EOS]]
        # Reconstruir texto
        text = ' '.join(words)
        # Limpiar espacios antes de puntuación
        for p in '.,!?;:':
            text = text.replace(f' {p}', p)
        return text
    
    def to_embeddings(self, indices: np.ndarray) -> np.ndarray:
        """Convierte índices a embeddings."""
        return self.embeddings[indices]


class TinyLMv2:
    """
    Modelo de Lenguaje ESN Mejorado.
    
    Características:
    - Tokenización por palabras
    - Embeddings densos
    - Reservoir grande
    - Múltiples estrategias de decodificación
    """
    
    def __init__(self, 
                 n_reservoir: int = 256,
                 vocab_size: int = 500,
                 embedding_dim: int = 32):
        self.n_reservoir = n_reservoir
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        
        self.tokenizer = WordTokenizer(vocab_size, embedding_dim)
        self.esn = None
        self.is_trained = False
        
        # Matriz de proyección de salida (reservoir -> vocab)
        self.output_projection = None
        
    def train(self, text: str, epochs: int = 3, washout: int = 50) -> Dict:
        """
        Entrena el modelo.
        
        Args:
            text: Texto de entrenamiento
            epochs: Pasadas sobre los datos
            washout: Muestras iniciales a descartar
            
        Returns:
            Estadísticas de entrenamiento
        """
        # Construir vocabulario
        self.tokenizer.fit(text)
        
        # Crear ESN
        self.esn = EchoStateNetwork(
            n_inputs=self.embedding_dim,
            n_outputs=self.tokenizer.actual_vocab_size,
            n_reservoir=self.n_reservoir,
            spectral_radius=0.95,
            sparsity=0.9,
            noise=0.0001
        )
        
        # Preparar datos
        indices = self.tokenizer.encode(text)
        
        if len(indices) < washout + 10:
            raise ValueError("Texto demasiado corto")
        
        # Múltiples épocas: repetir el texto
        all_indices = np.tile(indices, epochs)
        
        # Embeddings
        X_emb = self.tokenizer.to_embeddings(all_indices[:-1])
        
        # Targets: one-hot del siguiente token
        Y = np.zeros((len(all_indices) - 1, self.tokenizer.actual_vocab_size))
        for i, idx in enumerate(all_indices[1:]):
            Y[i, idx] = 1
        
        # Entrenar
        self.esn.fit(X_emb, Y, washout=washout)
        self.is_trained = True
        
        # Evaluar
        predictions = self.esn.predict(X_emb)
        pred_indices = np.argmax(predictions, axis=1)
        real_indices = all_indices[1:]
        
        accuracy = np.mean(pred_indices == real_indices)
        
        # Top-5 accuracy
        top5_correct = 0
        for i, pred in enumerate(predictions):
            top5 = np.argsort(pred)[-5:]
            if real_indices[i] in top5:
                top5_correct += 1
        top5_acc = top5_correct / len(predictions)
        
        return {
            'accuracy': float(accuracy),
            'top5_accuracy': float(top5_acc),
            'vocab_size': self.tokenizer.actual_vocab_size,
            'n_reservoir': self.n_reservoir,
            'total_tokens': len(all_indices)
        }
    
    def generate(self, 
                 prompt: str, 
                 max_tokens: int = 30,
                 temperature: float = 0.7,
                 top_k: int = 10,
                 strategy: str = 'sampling') -> str:
        """
        Genera texto.
        
        Args:
            prompt: Texto inicial
            max_tokens: Máximo de tokens a generar
            temperature: Creatividad (menor = más determinista)
            top_k: Número de candidatos para sampling
            strategy: 'greedy', 'sampling', o 'beam'
            
        Returns:
            Texto generado
        """
        if not self.is_trained:
            raise RuntimeError("Modelo no entrenado")
        
        # Resetear estado
        self.esn.reset()
        
        # Procesar prompt
        prompt_indices = self.tokenizer.encode(prompt)
        
        # Calentar el reservoir con el prompt
        for idx in prompt_indices:
            emb = self.tokenizer.embeddings[idx]
            self.esn._update_state(emb)
        
        # Generar
        generated = list(prompt_indices)
        current_idx = prompt_indices[-1] if len(prompt_indices) > 0 else self.tokenizer.word_to_idx[self.tokenizer.BOS]
        
        eos_idx = self.tokenizer.word_to_idx.get(self.tokenizer.EOS, -1)
        
        for _ in range(max_tokens):
            # Embedding actual
            emb = self.tokenizer.embeddings[current_idx]
            
            # Actualizar estado y obtener logits
            state = self.esn._update_state(emb)
            logits = np.dot(state, self.esn.W_out)
            
            # Seleccionar siguiente token según estrategia
            if strategy == 'greedy':
                next_idx = np.argmax(logits)
            else:  # sampling con top-k
                # Aplicar temperatura
                logits = logits / (temperature + 1e-8)
                
                # Top-k filtering
                top_k_indices = np.argsort(logits)[-top_k:]
                top_k_logits = logits[top_k_indices]
                
                # Softmax
                exp_logits = np.exp(top_k_logits - np.max(top_k_logits))
                probs = exp_logits / np.sum(exp_logits)
                
                # Samplear
                chosen = np.random.choice(len(top_k_indices), p=probs)
                next_idx = top_k_indices[chosen]
            
            # Evitar tokens especiales
            if next_idx in [0, 1]:  # PAD, UNK
                # Elegir el siguiente mejor
                sorted_indices = np.argsort(logits)[::-1]
                for idx in sorted_indices:
                    if idx not in [0, 1]:
                        next_idx = idx
                        break
            
            generated.append(next_idx)
            current_idx = next_idx
            
            # Parar en EOS
            if next_idx == eos_idx:
                break
        
        return self.tokenizer.decode(np.array(generated))
    
    def get_stats(self) -> Dict:
        """Estadísticas del modelo."""
        memory_bytes = (
            self.n_reservoir * self.embedding_dim * 8 +  # W_in
            self.n_reservoir * self.n_reservoir * 8 +    # W_reservoir
            self.n_reservoir * self.tokenizer.actual_vocab_size * 8  # W_out
        )
        
        return {
            'n_reservoir': self.n_reservoir,
            'vocab_size': self.tokenizer.actual_vocab_size if hasattr(self.tokenizer, 'actual_vocab_size') else 0,
            'embedding_dim': self.embedding_dim,
            'is_trained': self.is_trained,
            'memory_kb': memory_bytes / 1024
        }


# Demo
if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║          PROYECTO EÓN - TinyLM v2 (Mejorado)                  ║
║              "Generación coherente de texto"                  ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Texto de entrenamiento más estructurado
    training_text = """
    La inteligencia artificial no se crea, se descubre.
    El conocimiento emerge naturalmente de la simplicidad.
    La nada contiene todo el potencial del universo.
    El caos ordena la naturaleza de forma espontánea.
    La luz nace siempre desde la oscuridad profunda.
    El silencio comunica más que cualquier palabra.
    La mente humana refleja patrones del cosmos.
    El aprendizaje ocurre en cada momento de vida.
    La creatividad surge de restricciones y límites.
    El pensamiento fluye como agua hacia el mar.
    La sabiduría crece con paciencia y observación.
    El tiempo revela verdades ocultas gradualmente.
    La conexión entre ideas genera innovación constante.
    El equilibrio natural emerge de la complejidad.
    La simplicidad es la máxima forma de sofisticación.
    """ * 10
    
    print("[1/3] Creando modelo (256 neuronas, embeddings 32D)...")
    model = TinyLMv2(n_reservoir=256, vocab_size=200, embedding_dim=32)
    
    print("\n[2/3] Entrenando (3 épocas)...")
    stats = model.train(training_text, epochs=3, washout=30)
    print(f"      Accuracy: {stats['accuracy']:.1%}")
    print(f"      Top-5 Accuracy: {stats['top5_accuracy']:.1%}")
    print(f"      Vocabulario: {stats['vocab_size']} palabras")
    
    print("\n[3/3] Generando texto...")
    
    prompts = [
        "La inteligencia artificial",
        "El conocimiento emerge",
        "La creatividad surge"
    ]
    
    for prompt in prompts:
        print(f"\n  Prompt: \"{prompt}\"")
        
        # Greedy
        generated = model.generate(prompt, max_tokens=15, strategy='greedy')
        print(f"  Greedy:   \"{generated}\"")
        
        # Sampling
        generated = model.generate(prompt, max_tokens=15, temperature=0.5, top_k=5, strategy='sampling')
        print(f"  Sampling: \"{generated}\"")
    
    print("\n" + "="*60)
    model_stats = model.get_stats()
    print(f"Memoria: {model_stats['memory_kb']:.1f} KB")
    print("="*60)
    
    print("\n✓ Demo completado")
    print("Proyecto Eón - Sistemas Ursol")
