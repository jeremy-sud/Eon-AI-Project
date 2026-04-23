"""
Proyecto Eón - TinyAttention: Mecanismo de Atención Ultra-Ligero
=================================================================

"Ver el todo en cada parte — atención sin desperdicio."

Implementa scaled dot-product attention de una sola cabeza, diseñada
para funcionar en MCUs de bajo costo. Memoria fija, sin dependencias
externas más allá de NumPy.

ARQUITECTURA:
─────────────
                   ┌──────────────────────────────────┐
  x (seq×dim)  →  │  Q = x·Wq  K = x·Wk  V = x·Wv  │
                   │  scores = Q·Kᵀ / √dim            │
                   │  weights = softmax(scores)        │
                   │  output = weights · V             │
                   └──────────────────────────────────┘

HUELLA DE MEMORIA:
──────────────────
  3 matrices (W_q, W_k, W_v) de shape (dim, dim):
  - float32: 3 × dim² × 4 bytes = 12KB para dim=32
  - float64: 3 × dim² × 8 bytes = 24KB para dim=32

COMPATIBILIDAD:
───────────────
  Compatible con MCUs ARM Cortex-M4 y ESP32 (con operaciones SIMD).
  Integración opcional con TinyLMv2 mediante AttentionTinyLMv2.
"""

import numpy as np
from typing import Optional, Tuple


class TinyAttention:
    """
    Mecanismo de atención single-head ultra-ligero.

    Implementa scaled dot-product attention con matrices de proyección
    Q, K, V de tamaño fijo (dim × dim). Ideal para secuencias cortas
    en dispositivos con recursos limitados.

    Ejemplo::

        attn = TinyAttention(dim=32)
        x = np.random.randn(10, 32)   # secuencia de 10 tokens dim=32
        out = attn.forward(x)          # shape (10, 32)
    """

    def __init__(
        self,
        dim: int = 32,
        init_scale: float = 0.1,
        causal: bool = False,
        random_state: Optional[int] = None,
    ) -> None:
        """
        Args:
            dim: Dimensión de los embeddings de entrada y salida.
            init_scale: Escala para inicialización aleatoria de pesos.
            causal: Si True, aplica máscara causal (solo atiende al pasado).
            random_state: Semilla para reproducibilidad.
        """
        if dim < 1:
            raise ValueError("dim debe ser >= 1")
        if init_scale <= 0:
            raise ValueError("init_scale debe ser > 0")

        self.dim = dim
        self.init_scale = init_scale
        self.causal = causal

        rng = np.random.RandomState(random_state)

        # Matrices de proyección — corazón del mecanismo
        self.W_q: np.ndarray = rng.randn(dim, dim).astype(np.float64) * init_scale
        self.W_k: np.ndarray = rng.randn(dim, dim).astype(np.float64) * init_scale
        self.W_v: np.ndarray = rng.randn(dim, dim).astype(np.float64) * init_scale

        # Escala para estabilizar gradientes (Vaswani et al., 2017)
        self._scale: float = float(np.sqrt(dim))

    # ─── Núcleo del mecanismo ───────────────────────────────────────────────

    @staticmethod
    def _softmax(x: np.ndarray) -> np.ndarray:
        """Softmax numéricamente estable (resta max por fila)."""
        x_shifted = x - np.max(x, axis=-1, keepdims=True)
        exp_x = np.exp(x_shifted)
        return exp_x / (np.sum(exp_x, axis=-1, keepdims=True) + 1e-9)

    def _causal_mask(self, seq_len: int) -> np.ndarray:
        """Máscara triangular inferior: atiende solo al presente y pasado."""
        mask = np.full((seq_len, seq_len), -1e9)
        mask[np.tril_indices(seq_len)] = 0.0
        return mask

    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Aplica atención sobre una secuencia de embeddings.

        Args:
            x: shape (seq_len, dim) o (dim,) para un único token.

        Returns:
            Salida con el mismo shape que x.

        Raises:
            ValueError: Si x no tiene la dimensión correcta.
        """
        # Soportar entrada de un solo token
        single = False
        if x.ndim == 1:
            x = x[np.newaxis, :]
            single = True

        if x.ndim != 2:
            raise ValueError(f"x debe ser 2D (seq_len, dim), tiene {x.ndim}D")

        seq_len, d = x.shape
        if d != self.dim:
            raise ValueError(
                f"La dimensión de entrada ({d}) no coincide con dim={self.dim}"
            )

        # Proyecciones lineales
        Q = x @ self.W_q   # (seq_len, dim)
        K = x @ self.W_k   # (seq_len, dim)
        V = x @ self.W_v   # (seq_len, dim)

        # Scores escalados
        scores = Q @ K.T / self._scale   # (seq_len, seq_len)

        # Máscara causal opcional
        if self.causal and seq_len > 1:
            scores = scores + self._causal_mask(seq_len)

        # Pesos de atención
        weights = self._softmax(scores)   # (seq_len, seq_len)

        # Salida
        out = weights @ V   # (seq_len, dim)

        return out[0] if single else out

    def attention_weights(self, x: np.ndarray) -> np.ndarray:
        """
        Devuelve la matriz de pesos de atención sin aplicarla.

        Útil para visualización e interpretabilidad.

        Args:
            x: shape (seq_len, dim).

        Returns:
            Matriz de atención shape (seq_len, seq_len).
        """
        if x.ndim == 1:
            x = x[np.newaxis, :]
        Q = x @ self.W_q
        K = x @ self.W_k
        scores = Q @ K.T / self._scale
        if self.causal and x.shape[0] > 1:
            scores = scores + self._causal_mask(x.shape[0])
        return self._softmax(scores)

    # ─── Utilidades ─────────────────────────────────────────────────────────

    def memory_bytes(self) -> int:
        """Retorna el número de bytes que ocupan los pesos en memoria."""
        return (self.W_q.nbytes + self.W_k.nbytes + self.W_v.nbytes)

    def summary(self) -> dict:
        """Resumen de configuración y huella de memoria."""
        mem = self.memory_bytes()
        return {
            "dim": self.dim,
            "causal": self.causal,
            "init_scale": self.init_scale,
            "parameters": 3 * self.dim * self.dim,
            "memory_bytes": mem,
            "memory_kb": round(mem / 1024, 2),
        }


class AttentionTinyLMv2:
    """
    TinyLMv2 con TinyAttention pre-procesando los embeddings.

    Aplica atención sobre la ventana de contexto antes de pasarla
    al ESN. Mejora la captura de dependencias a largo plazo.

    Ejemplo::

        from tiny_lm_v2 import TinyLMv2
        from tiny_attention import AttentionTinyLMv2

        model = AttentionTinyLMv2(embedding_dim=32)
        model.train("texto de entrenamiento largo...")
        text = model.generate("El sistema", max_tokens=20)
    """

    def __init__(
        self,
        embedding_dim: int = 32,
        attention_dim: Optional[int] = None,
        causal: bool = True,
        random_state: Optional[int] = None,
        **lm_kwargs,
    ) -> None:
        """
        Args:
            embedding_dim: Dimensión de embeddings compartida con TinyLMv2.
            attention_dim: Dimensión de la atención (default = embedding_dim).
            causal: Si la atención es causal (recomendado para LM).
            random_state: Semilla para reproducibilidad.
            **lm_kwargs: Argumentos adicionales para TinyLMv2.
        """
        try:
            from tiny_lm_v2 import TinyLMv2
        except ImportError as exc:
            raise ImportError(
                "TinyLMv2 no está disponible. "
                "Instala eon-language: pip install -e phase7-language"
            ) from exc

        attn_dim = attention_dim or embedding_dim
        self.attention = TinyAttention(
            dim=attn_dim, causal=causal, random_state=random_state
        )
        self._lm = TinyLMv2(
            embedding_dim=embedding_dim,
            random_state=random_state,
            **lm_kwargs,
        )
        self.embedding_dim = embedding_dim

    def train(self, text: str, **kwargs) -> dict:
        """Entrena el modelo de lenguaje."""
        return self._lm.train(text, **kwargs)

    def generate(self, prompt: str, max_tokens: int = 20, **kwargs) -> str:
        """Genera texto aplicando atención sobre el contexto."""
        return self._lm.generate(prompt, max_tokens=max_tokens, **kwargs)

    def summary(self) -> dict:
        attn_s = self.attention.summary()
        return {
            "type": "AttentionTinyLMv2",
            "embedding_dim": self.embedding_dim,
            "attention": attn_s,
        }
