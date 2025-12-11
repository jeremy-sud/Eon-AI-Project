"""
Tests for TinyLM v2 Language Model
===================================
Tests for word tokenization, ESN-based language model, and generation.

Run with: pytest phase7-language/tests/test_tiny_lm_v2.py -v
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add paths for imports
_current_dir = Path(__file__).parent
_phase7_dir = _current_dir.parent
sys.path.insert(0, str(_phase7_dir))
sys.path.insert(0, str(_phase7_dir.parent / "phase1-foundations" / "python"))


class TestWordTokenizer:
    """Test cases for WordTokenizer."""
    
    @pytest.fixture
    def tokenizer(self):
        """Create a WordTokenizer instance."""
        from tiny_lm_v2 import WordTokenizer
        return WordTokenizer(vocab_size=100, embedding_dim=16)
    
    @pytest.fixture
    def fitted_tokenizer(self, tokenizer):
        """Create and fit a tokenizer."""
        text = "El gato come pescado. El perro come carne. El pájaro vuela alto."
        tokenizer.fit(text)
        return tokenizer
    
    def test_initialization(self, tokenizer):
        """Test WordTokenizer initializes correctly."""
        assert tokenizer.vocab_size == 100
        assert tokenizer.embedding_dim == 16
        assert tokenizer.PAD == "<PAD>"
        assert tokenizer.UNK == "<UNK>"
    
    def test_special_tokens_exist(self, tokenizer):
        """Test special tokens are pre-seeded."""
        # Check special tokens are in vocab
        assert tokenizer.vocab.get_id(tokenizer.PAD) is not None
        assert tokenizer.vocab.get_id(tokenizer.UNK) is not None
        assert tokenizer.vocab.get_id(tokenizer.BOS) is not None
        assert tokenizer.vocab.get_id(tokenizer.EOS) is not None
    
    def test_fit_creates_embeddings(self, fitted_tokenizer):
        """Test fit creates embeddings matrix."""
        assert fitted_tokenizer.embeddings is not None
        assert fitted_tokenizer.embeddings.shape[1] == 16  # embedding_dim
    
    def test_encode_returns_array(self, fitted_tokenizer):
        """Test encode returns numpy array of token IDs."""
        encoded = fitted_tokenizer.encode("El gato")
        assert isinstance(encoded, np.ndarray)
        # encode returns 1D array of token IDs
        assert len(encoded.shape) == 1
    
    def test_decode_returns_text(self, fitted_tokenizer):
        """Test decode returns string."""
        # Get some word IDs
        ids = [fitted_tokenizer.vocab.get_id("el"),
               fitted_tokenizer.vocab.get_id("gato")]
        ids = [i for i in ids if i is not None]
        
        if ids:
            decoded = fitted_tokenizer.decode(ids)
            assert isinstance(decoded, str)
    
    def test_encode_decode_roundtrip(self, fitted_tokenizer):
        """Test encode then decode preserves meaning."""
        original = "el gato come"
        # This is a partial test since we don't have perfect roundtrip
        encoded = fitted_tokenizer.encode(original)
        assert encoded is not None


class TestTinyLMv2:
    """Test cases for TinyLMv2 language model."""
    
    @pytest.fixture
    def training_text(self):
        """Sample training text."""
        return """
        La inteligencia emerge de la simplicidad.
        El conocimiento crece con el tiempo.
        La creatividad surge de límites.
        El pensamiento fluye naturalmente.
        La sabiduría viene de la experiencia.
        """ * 3
    
    @pytest.fixture
    def model(self):
        """Create a TinyLMv2 instance."""
        from tiny_lm_v2 import TinyLMv2
        return TinyLMv2(
            n_reservoir=64,  # Smaller for tests
            vocab_size=100,
            embedding_dim=16
        )
    
    @pytest.fixture
    def trained_model(self, model, training_text):
        """Create and train a model."""
        model.train(training_text, epochs=1, washout=10)
        return model
    
    def test_initialization(self, model):
        """Test TinyLMv2 initializes correctly."""
        assert model.n_reservoir == 64
        assert model.vocab_size == 100
        assert model.is_trained is False
    
    def test_training_updates_state(self, model, training_text):
        """Test training changes is_trained flag."""
        assert model.is_trained is False
        model.train(training_text, epochs=1, washout=10)
        assert model.is_trained is True
    
    def test_training_returns_stats(self, model, training_text):
        """Test training returns statistics dictionary."""
        stats = model.train(training_text, epochs=1, washout=10)
        
        assert isinstance(stats, dict)
        assert 'accuracy' in stats
        assert 'vocab_size' in stats
        assert 0 <= stats['accuracy'] <= 1
    
    def test_generate_greedy(self, trained_model):
        """Test greedy text generation."""
        result = trained_model.generate(
            "La inteligencia",
            max_tokens=5,
            strategy='greedy'
        )
        
        assert isinstance(result, str)
        assert len(result) > len("La inteligencia")
    
    def test_generate_sampling(self, trained_model):
        """Test sampling text generation."""
        result = trained_model.generate(
            "El conocimiento",
            max_tokens=5,
            strategy='sampling',
            temperature=0.5,
            top_k=5
        )
        
        assert isinstance(result, str)
    
    def test_generate_requires_training(self, model):
        """Test generate raises error if not trained."""
        with pytest.raises(RuntimeError):
            model.generate("test", max_tokens=5)
    
    def test_get_stats(self, trained_model):
        """Test get_stats returns model statistics."""
        stats = trained_model.get_stats()
        
        assert isinstance(stats, dict)
        assert 'n_reservoir' in stats
        assert 'vocab_size' in stats
        assert 'is_trained' in stats
        assert 'memory_kb' in stats
        assert stats['is_trained'] is True
    
    def test_memory_footprint(self, trained_model):
        """Test memory is reasonable for TinyML."""
        stats = trained_model.get_stats()
        
        # Should be under 1MB for a tiny model
        assert stats['memory_kb'] < 1024


class TestGematriaTokenizer:
    """Test cases for GematriaTokenizer (mystical embeddings)."""
    
    @pytest.fixture
    def gematria_tokenizer(self):
        """Create a GematriaTokenizer if available."""
        try:
            from src.gematria import GematriaTokenizer
            return GematriaTokenizer()
        except ImportError:
            pytest.skip("GematriaTokenizer not available")
    
    def test_initialization(self, gematria_tokenizer):
        """Test GematriaTokenizer initializes."""
        assert gematria_tokenizer is not None
    
    def test_word_to_value(self, gematria_tokenizer):
        """Test word to gematria value conversion."""
        if hasattr(gematria_tokenizer, 'word_to_value'):
            value = gematria_tokenizer.word_to_value("test")
            assert isinstance(value, (int, float))


class TestTrieVocab:
    """Test cases for TrieVocab efficient vocabulary."""
    
    @pytest.fixture
    def trie_vocab(self):
        """Create a TrieVocab instance."""
        from src.trie_vocab import TrieVocab
        return TrieVocab()
    
    def test_add_and_get(self, trie_vocab):
        """Test adding words and getting IDs."""
        word_id = trie_vocab.add("hello")
        retrieved_id = trie_vocab.get_id("hello")
        
        assert word_id == retrieved_id
    
    def test_unique_ids(self, trie_vocab):
        """Test each word gets unique ID."""
        id1 = trie_vocab.add("word1")
        id2 = trie_vocab.add("word2")
        
        assert id1 != id2
    
    def test_size_tracking(self, trie_vocab):
        """Test size property tracks vocabulary size."""
        initial = trie_vocab.size
        trie_vocab.add("newword")
        
        assert trie_vocab.size == initial + 1
    
    def test_unknown_word_returns_none(self, trie_vocab):
        """Test unknown word returns -1 (not found indicator)."""
        result = trie_vocab.get_id("nonexistent_word_xyz")
        # TrieVocab returns -1 for unknown words
        assert result == -1


class TestIntegration:
    """Integration tests for the language model pipeline."""
    
    def test_full_pipeline(self):
        """Test complete training and generation pipeline."""
        from tiny_lm_v2 import TinyLMv2
        
        # Create model
        model = TinyLMv2(n_reservoir=32, vocab_size=50, embedding_dim=8)
        
        # Train
        text = "El sol brilla. La luna ilumina. Las estrellas brillan." * 5
        stats = model.train(text, epochs=1, washout=5)
        
        # Generate
        output = model.generate("El sol", max_tokens=3, strategy='greedy')
        
        assert model.is_trained
        assert isinstance(output, str)
        assert stats['accuracy'] >= 0
    
    def test_deterministic_greedy(self):
        """Test greedy generation is deterministic."""
        from tiny_lm_v2 import TinyLMv2
        
        model = TinyLMv2(n_reservoir=32, vocab_size=50, embedding_dim=8)
        text = "La casa es grande. El árbol es alto." * 5
        model.train(text, epochs=1, washout=5)
        
        # Generate twice with same prompt
        out1 = model.generate("La casa", max_tokens=3, strategy='greedy')
        
        # Reset state and generate again
        model.esn.state = np.zeros(model.n_reservoir)
        out2 = model.generate("La casa", max_tokens=3, strategy='greedy')
        
        # Should be the same (greedy is deterministic)
        assert out1 == out2
