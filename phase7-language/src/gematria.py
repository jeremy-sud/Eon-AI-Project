"""
Gematria Embedding Layer - Resonancia Matemática para Tokens

Implementa un sistema de embeddings basado en principios gemátricos:
- Hash por suma de bytes (valor numérico del token)
- Agrupación por resonancia matemática
- Reducción numérica a dígitos sagrados (1-9)
- Embeddings por entropía de Shannon

"Todo número es infinito; no hay diferencia" - Liber AL vel Legis I:4

Autor: Eon Project AI
"""

import math
from typing import Optional
import numpy as np


class GematriaEmbeddingLayer:
    """
    Capa de embeddings basada en Gematria Algorítmica.
    
    Agrupa tokens no por similitud semántica, sino por resonancia
    matemática usando suma de bytes, entropía y reducción numérica.
    """
    
    # Números sagrados y sus propiedades resonantes
    SACRED_NUMBERS = {
        1: "Unidad, Kether, el punto",
        2: "Dualidad, Chokmah, la línea",
        3: "Trinidad, Binah, el triángulo",
        4: "Estabilidad, Chesed, el cuadrado",
        5: "Cambio, Geburah, el pentágono",
        6: "Armonía, Tiphareth, el hexágono",
        7: "Misterio, Netzach, el heptágono",
        8: "Regeneración, Hod, el octógono",
        9: "Completitud, Yesod, el eneágono",
    }
    
    # Número de buckets por defecto: 93 = valor de Thelema en gematria griega
    DEFAULT_BUCKETS = 93
    
    def __init__(
        self,
        embedding_dim: int = 32,
        n_buckets: int = DEFAULT_BUCKETS,
        use_entropy: bool = True,
        use_numeric_reduction: bool = True
    ):
        """
        Inicializa la capa de embeddings gemátricos.
        
        Args:
            embedding_dim: Dimensión de los embeddings
            n_buckets: Número de buckets para resonancia (93 por defecto)
            use_entropy: Usar entropía de Shannon en embeddings
            use_numeric_reduction: Aplicar reducción numérica (1-9)
        """
        self.embedding_dim = embedding_dim
        self.n_buckets = n_buckets
        self.use_entropy = use_entropy
        self.use_numeric_reduction = use_numeric_reduction
        
        # Matriz de embeddings: cada bucket tiene su embedding
        # Inicializada con semilla basada en 418 (Abrahadabra)
        rng = np.random.default_rng(seed=418)
        self.bucket_embeddings = rng.normal(
            0, 0.1, (n_buckets, embedding_dim)
        ).astype(np.float32)
        
        # Cache de valores gemátricos calculados
        self._gematria_cache: dict[str, int] = {}
        self._entropy_cache: dict[str, float] = {}
    
    def calculate_gematria(self, token: str) -> int:
        """
        Calcula el valor gemátrico de un token (suma de bytes UTF-8).
        
        Args:
            token: Token a evaluar
            
        Returns:
            Valor gemátrico (suma de todos los bytes)
        """
        if token in self._gematria_cache:
            return self._gematria_cache[token]
        
        # Suma de bytes UTF-8
        value = sum(token.encode('utf-8'))
        self._gematria_cache[token] = value
        return value
    
    def numeric_reduction(self, value: int) -> int:
        """
        Reduce un número a un dígito (1-9) sumando sus dígitos.
        
        Esta es la técnica clásica de reducción numérica en numerología.
        Ejemplo: 418 -> 4+1+8 = 13 -> 1+3 = 4
        
        Args:
            value: Número a reducir
            
        Returns:
            Dígito entre 1 y 9
        """
        if value == 0:
            return 9  # 0 se considera como 9 (completitud)
        
        while value > 9:
            value = sum(int(d) for d in str(value))
        
        return value
    
    def calculate_entropy(self, token: str) -> float:
        """
        Calcula la entropía de Shannon del token.
        
        Mide la "información" contenida en el patrón de caracteres.
        
        Args:
            token: Token a evaluar
            
        Returns:
            Entropía en bits
        """
        if token in self._entropy_cache:
            return self._entropy_cache[token]
        
        if not token:
            return 0.0
        
        # Contar frecuencias de caracteres
        freq: dict[str, int] = {}
        for char in token:
            freq[char] = freq.get(char, 0) + 1
        
        # Calcular probabilidades y entropía
        length = len(token)
        entropy = 0.0
        for count in freq.values():
            p = count / length
            if p > 0:
                entropy -= p * math.log2(p)
        
        self._entropy_cache[token] = entropy
        return entropy
    
    def get_bucket(self, token: str) -> int:
        """
        Asigna un token a un bucket de resonancia.
        
        Args:
            token: Token a clasificar
            
        Returns:
            Índice del bucket (0 a n_buckets-1)
        """
        gematria = self.calculate_gematria(token)
        
        if self.use_numeric_reduction:
            # Combina gematria completo con reducción numérica
            reduced = self.numeric_reduction(gematria)
            # El bucket se basa en gematria pero modulado por reducción
            bucket = (gematria + reduced * 10) % self.n_buckets
        else:
            bucket = gematria % self.n_buckets
        
        return bucket
    
    def embed(self, token: str) -> np.ndarray:
        """
        Genera el embedding para un token usando Gematria.
        
        El embedding combina:
        1. El embedding base del bucket
        2. Modulación por entropía (si está habilitada)
        3. Proyección por reducción numérica
        
        Args:
            token: Token a embeber
            
        Returns:
            Vector de embedding (embedding_dim,)
        """
        bucket = self.get_bucket(token)
        embedding = self.bucket_embeddings[bucket].copy()
        
        if self.use_entropy:
            entropy = self.calculate_entropy(token)
            # Modular embedding por entropía (escala 0-1 normalizada)
            max_entropy = math.log2(max(len(set(token)), 1) + 1)
            if max_entropy > 0:
                entropy_factor = entropy / max_entropy
            else:
                entropy_factor = 0.5
            
            # Aplicar como transformación sinusoidal
            phase = entropy_factor * math.pi
            modulation = np.sin(
                np.linspace(0, math.pi * 2, self.embedding_dim) + phase
            ).astype(np.float32)
            embedding = embedding * (1 + 0.3 * modulation)
        
        if self.use_numeric_reduction:
            # Añadir "color" basado en el dígito sagrado
            gematria = self.calculate_gematria(token)
            sacred_digit = self.numeric_reduction(gematria)
            
            # Cada dígito sagrado activa diferentes dimensiones
            sacred_mask = np.zeros(self.embedding_dim, dtype=np.float32)
            step = self.embedding_dim // 9
            start = (sacred_digit - 1) * step
            end = start + step
            sacred_mask[start:end] = 0.5
            embedding = embedding + sacred_mask
        
        return embedding
    
    def embed_sequence(self, tokens: list[str]) -> np.ndarray:
        """
        Embebe una secuencia de tokens.
        
        Args:
            tokens: Lista de tokens
            
        Returns:
            Matriz de embeddings (n_tokens, embedding_dim)
        """
        embeddings = np.array([self.embed(t) for t in tokens])
        return embeddings
    
    def resonance_distance(self, token1: str, token2: str) -> float:
        """
        Calcula la "distancia de resonancia" entre dos tokens.
        
        Dos tokens con el mismo bucket tienen distancia 0.
        La distancia máxima es 1.0.
        
        Args:
            token1: Primer token
            token2: Segundo token
            
        Returns:
            Distancia normalizada (0-1)
        """
        bucket1 = self.get_bucket(token1)
        bucket2 = self.get_bucket(token2)
        
        # Distancia circular (los buckets forman un círculo)
        diff = abs(bucket1 - bucket2)
        circular_diff = min(diff, self.n_buckets - diff)
        
        return circular_diff / (self.n_buckets / 2)
    
    def find_resonant_tokens(
        self, 
        token: str, 
        vocabulary: list[str],
        max_distance: float = 0.1
    ) -> list[tuple[str, float]]:
        """
        Encuentra tokens que "resuenan" con el token dado.
        
        Args:
            token: Token de referencia
            vocabulary: Lista de tokens a buscar
            max_distance: Distancia máxima para considerar resonancia
            
        Returns:
            Lista de (token, distancia) ordenada por distancia
        """
        resonant = []
        
        for candidate in vocabulary:
            if candidate == token:
                continue
            
            distance = self.resonance_distance(token, candidate)
            if distance <= max_distance:
                resonant.append((candidate, distance))
        
        return sorted(resonant, key=lambda x: x[1])
    
    def get_sacred_properties(self, token: str) -> dict:
        """
        Obtiene las propiedades sagradas de un token.
        
        Args:
            token: Token a analizar
            
        Returns:
            Diccionario con propiedades gemátricas
        """
        gematria = self.calculate_gematria(token)
        reduced = self.numeric_reduction(gematria)
        entropy = self.calculate_entropy(token)
        bucket = self.get_bucket(token)
        
        return {
            "token": token,
            "gematria": gematria,
            "sacred_digit": reduced,
            "sacred_meaning": self.SACRED_NUMBERS.get(reduced, "Desconocido"),
            "entropy": round(entropy, 4),
            "bucket": bucket,
            "resonance_key": f"{reduced}-{bucket % 10}"
        }


class GematriaTokenizer:
    """
    Tokenizador que usa Gematria para embeddings.
    
    Compatible con WordTokenizer pero usa GematriaEmbeddingLayer
    para generar embeddings basados en resonancia matemática.
    """
    
    # Tokens especiales con valores gemátricos significativos
    PAD_TOKEN = "<PAD>"
    UNK_TOKEN = "<UNK>"
    BOS_TOKEN = "<BOS>"
    EOS_TOKEN = "<EOS>"
    
    # Aliases para compatibilidad con WordTokenizer
    PAD = PAD_TOKEN
    UNK = UNK_TOKEN
    BOS = BOS_TOKEN
    EOS = EOS_TOKEN
    
    def __init__(
        self,
        embedding_dim: int = 32,
        n_buckets: int = 93,
        min_freq: int = 2
    ):
        """
        Inicializa el tokenizador gemátrico.
        
        Args:
            embedding_dim: Dimensión de embeddings
            n_buckets: Buckets de resonancia
            min_freq: Frecuencia mínima para incluir palabra
        """
        self.embedding_dim = embedding_dim
        self.n_buckets = n_buckets
        self.min_freq = min_freq
        
        # Vocabulario
        self.word2idx: dict[str, int] = {
            self.PAD_TOKEN: 0,
            self.UNK_TOKEN: 1,
            self.BOS_TOKEN: 2,
            self.EOS_TOKEN: 3,
        }
        self.idx2word: dict[int, str] = {v: k for k, v in self.word2idx.items()}
        
        # Capa de embeddings gemátricos
        self.gematria = GematriaEmbeddingLayer(
            embedding_dim=embedding_dim,
            n_buckets=n_buckets
        )
        
        # Embeddings calculados
        self._embeddings: Optional[np.ndarray] = None
    
    def _tokenize(self, text: str) -> list[str]:
        """
        Tokeniza texto en palabras (compatible con WordTokenizer).
        
        Args:
            text: Texto a tokenizar
            
        Returns:
            Lista de tokens
        """
        text = text.lower()
        for p in '.,!?;:\n':
            text = text.replace(p, f' {p} ')
        return text.split()
    
    @property
    def vocab_size(self) -> int:
        """Tamaño del vocabulario."""
        return len(self.word2idx)
    
    @property
    def actual_vocab_size(self) -> int:
        """Alias para compatibilidad con WordTokenizer."""
        return self.vocab_size
    
    def fit(self, texts: list[str] | str) -> None:
        """
        Construye vocabulario desde textos.
        
        Args:
            texts: Lista de textos o un texto único de entrenamiento
        """
        from collections import Counter
        
        # Normalizar entrada a lista
        if isinstance(texts, str):
            texts = [texts]
        
        # Contar palabras
        word_counts: Counter[str] = Counter()
        for text in texts:
            words = self._tokenize(text)
            word_counts.update(words)
        
        # Añadir palabras con frecuencia mínima
        for word, count in word_counts.most_common():
            if count >= self.min_freq and word not in self.word2idx:
                idx = len(self.word2idx)
                self.word2idx[word] = idx
                self.idx2word[idx] = word
        
        # Pre-calcular embeddings
        self._build_embeddings()
    
    def _build_embeddings(self) -> None:
        """Pre-calcula embeddings para todo el vocabulario."""
        self._embeddings = np.zeros(
            (self.vocab_size, self.embedding_dim),
            dtype=np.float32
        )
        
        for word, idx in self.word2idx.items():
            self._embeddings[idx] = self.gematria.embed(word)
    
    def encode(self, text: str, add_special: bool = False) -> np.ndarray:
        """
        Codifica texto a índices.
        
        Compatible con WordTokenizer (add_special=False por defecto).
        
        Args:
            text: Texto a codificar
            add_special: Añadir BOS/EOS (False por defecto para compatibilidad)
            
        Returns:
            Array de índices
        """
        words = self._tokenize(text)
        indices = [self.word2idx.get(w, self.word2idx[self.UNK_TOKEN]) for w in words]
        
        if add_special:
            indices = [self.word2idx[self.BOS_TOKEN]] + indices + [self.word2idx[self.EOS_TOKEN]]
        
        return np.array(indices)
    
    def decode(self, indices: list[int], skip_special: bool = True) -> str:
        """
        Decodifica índices a texto.
        
        Args:
            indices: Lista de índices
            skip_special: Omitir tokens especiales
            
        Returns:
            Texto decodificado
        """
        special = {
            self.word2idx[self.PAD_TOKEN],
            self.word2idx[self.UNK_TOKEN],
            self.word2idx[self.BOS_TOKEN],
            self.word2idx[self.EOS_TOKEN],
        }
        
        words = []
        for idx in indices:
            if skip_special and idx in special:
                continue
            words.append(self.idx2word.get(idx, self.UNK_TOKEN))
        
        return " ".join(words)
    
    def to_embeddings(self, indices: list[int] | np.ndarray) -> np.ndarray:
        """
        Convierte índices a embeddings.
        
        Args:
            indices: Lista de índices o ndarray
            
        Returns:
            Matriz de embeddings (n, embedding_dim)
        """
        if self._embeddings is None:
            self._build_embeddings()
        
        # Asegurar que _embeddings no es None después de construir
        assert self._embeddings is not None
        return self._embeddings[indices]
    
    def analyze_text(self, text: str) -> list[dict]:
        """
        Analiza las propiedades gemátricas de un texto.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Lista de propiedades por palabra
        """
        words = text.lower().split()
        return [self.gematria.get_sacred_properties(w) for w in words]


def demo_gematria():
    """Demostración del sistema de Gematria."""
    print("=" * 60)
    print("  GEMATRIA EMBEDDING LAYER - Demo")
    print("  'Todo número es infinito; no hay diferencia'")
    print("=" * 60)
    print()
    
    # Crear capa de embeddings
    gematria = GematriaEmbeddingLayer()
    
    # Palabras de ejemplo
    words = ["thelema", "agape", "love", "will", "light", "wisdom"]
    
    print("Análisis Gemátrico:")
    print("-" * 50)
    for word in words:
        props = gematria.get_sacred_properties(word)
        print(f"  {word}:")
        print(f"    Gematria: {props['gematria']}")
        print(f"    Dígito Sagrado: {props['sacred_digit']} ({props['sacred_meaning']})")
        print(f"    Entropía: {props['entropy']} bits")
        print(f"    Bucket: {props['bucket']}")
        print()
    
    # Encontrar resonancias
    print("Resonancias con 'thelema':")
    print("-" * 50)
    resonant = gematria.find_resonant_tokens("thelema", words, max_distance=0.3)
    for word, dist in resonant:
        print(f"  {word}: distancia {dist:.3f}")
    print()
    
    # Demo del tokenizador
    print("Tokenizador Gemátrico:")
    print("-" * 50)
    tokenizer = GematriaTokenizer(embedding_dim=16, n_buckets=93)
    
    # Entrenar con textos de ejemplo
    texts = [
        "Do what thou wilt shall be the whole of the Law",
        "Love is the law love under will",
        "Every man and every woman is a star",
    ]
    tokenizer.fit(texts)
    
    print(f"  Vocabulario: {tokenizer.vocab_size} palabras")
    
    # Analizar una frase
    test = "love is the law"
    analysis = tokenizer.analyze_text(test)
    print(f"\n  Análisis de '{test}':")
    for props in analysis:
        print(f"    {props['token']}: gematria={props['gematria']}, "
              f"sagrado={props['sacred_digit']}")
    
    # Mostrar embeddings
    indices = tokenizer.encode(test, add_special=False)
    embeddings = tokenizer.to_embeddings(indices)
    print(f"\n  Embeddings shape: {embeddings.shape}")
    print(f"  Primer embedding (primeros 8 valores): {embeddings[0][:8]}")


if __name__ == "__main__":
    demo_gematria()
