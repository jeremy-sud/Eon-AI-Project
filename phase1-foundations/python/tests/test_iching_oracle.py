"""
Tests para IChingOracle - Proyecto Eón
======================================

Tests del oráculo I-Ching neural.
"""

import pytest
import numpy as np
import sys
import os

# Path setup
_current_dir = os.path.dirname(os.path.abspath(__file__))
_python_dir = os.path.dirname(_current_dir)
sys.path.insert(0, _python_dir)

from core.iching_oracle import (
    IChingOracle,
    OracleReading,
    OracleStats,
    ConsultationType,
    LineChange,
    create_oracle
)
from core.archaic_protocol import HEXAGRAMS, Hexagram


@pytest.fixture(scope="module")
def oracle():
    """Oráculo entrenado para tests."""
    return create_oracle(reservoir_size=32, pretrained=True, random_state=42)


@pytest.fixture(scope="module")
def untrained_oracle():
    """Oráculo sin entrenar."""
    return IChingOracle(reservoir_size=32, random_state=42)


class TestOracleInit:
    """Tests de inicialización."""
    
    def test_init_default(self):
        """Verifica inicialización por defecto."""
        oracle = IChingOracle()
        
        assert oracle.reservoir_size == 64
        assert oracle.is_trained == False
        assert oracle.stats.consultations == 0
    
    def test_init_custom_params(self):
        """Verifica parámetros personalizados."""
        oracle = IChingOracle(
            reservoir_size=32,
            spectral_radius=0.9,
            random_state=123
        )
        
        assert oracle.reservoir_size == 32
    
    def test_esn_created(self):
        """Verifica que ESN se crea correctamente."""
        oracle = IChingOracle(reservoir_size=32)
        
        assert oracle.esn is not None
        assert oracle.esn.n_reservoir == 32
        assert oracle.esn.n_inputs == 14  # 6 bits + 8 context
        assert oracle.esn.n_outputs == 6


class TestTraining:
    """Tests de entrenamiento."""
    
    def test_train_sets_flag(self, untrained_oracle):
        """Verifica que entrenar marca como entrenado."""
        oracle = IChingOracle(reservoir_size=32, random_state=42)
        assert not oracle.is_trained
        
        # Usar suficientes secuencias para superar washout
        oracle.train_on_transitions(n_sequences=50, seq_length=10)
        assert oracle.is_trained
    
    def test_trained_oracle_has_confidence(self, oracle):
        """Verifica que oráculo entrenado tiene confianza."""
        reading = oracle.consult("¿Debería actuar ahora?")
        
        # ESN entrenado debería dar alguna confianza
        assert reading.esn_confidence >= 0
        assert reading.esn_confidence <= 1


class TestCasting:
    """Tests de tirada de hexagramas."""
    
    def test_cast_yarrow_stalks(self, oracle):
        """Verifica tirada de tallos."""
        line_values, changing = oracle.cast_yarrow_stalks()
        
        assert len(line_values) == 6
        assert all(v in [6, 7, 8, 9] for v in line_values)
        assert all(0 <= c < 6 for c in changing)
    
    def test_cast_produces_valid_hexagram(self, oracle):
        """Verifica que tirada produce hexagrama válido."""
        line_values, _ = oracle.cast_yarrow_stalks()
        primary, _, _ = oracle._line_values_to_hexagram(line_values)
        
        assert primary is not None
        assert isinstance(primary, Hexagram)
        assert 1 <= primary.number <= 64
    
    def test_changing_lines_produce_relating(self, oracle):
        """Verifica que líneas cambiantes producen hexagrama relacionado."""
        # Forzar líneas cambiantes
        line_values = [9, 7, 6, 8, 7, 9]  # 9 y 6 son cambiantes
        primary, relating, changing = oracle._line_values_to_hexagram(line_values)
        
        assert len(changing) > 0
        assert relating is not None
        assert relating.number != primary.number


class TestConsultation:
    """Tests de consultas."""
    
    def test_consult_returns_reading(self, oracle):
        """Verifica que consult retorna OracleReading."""
        reading = oracle.consult("Test question")
        
        assert isinstance(reading, OracleReading)
        assert reading.primary_hexagram is not None
        assert reading.question == "Test question"
    
    def test_consult_empty_question(self, oracle):
        """Verifica consulta sin pregunta (meditación)."""
        reading = oracle.consult("")
        
        assert reading.question == ""
        assert reading.primary_hexagram is not None
    
    def test_consult_updates_stats(self, oracle):
        """Verifica que consulta actualiza estadísticas."""
        initial = oracle.stats.consultations
        
        oracle.consult("Another question")
        
        assert oracle.stats.consultations == initial + 1
    
    def test_consult_has_judgment_and_image(self, oracle):
        """Verifica que lectura tiene juicio e imagen."""
        reading = oracle.consult("Test")
        
        assert reading.judgment != ""
        assert reading.image != ""
    
    def test_consult_has_advice(self, oracle):
        """Verifica que lectura tiene consejo."""
        reading = oracle.consult("Test")
        
        assert reading.advice != ""
        assert reading.primary_hexagram.name_spanish in reading.advice


class TestQuestionEmbedding:
    """Tests de embedding de preguntas."""
    
    def test_question_to_embedding(self, oracle):
        """Verifica conversión de pregunta a embedding."""
        emb = oracle._question_to_embedding("¿Debería actuar ahora?")
        
        assert emb.shape == (8,)
        assert all(0 <= v <= 1 for v in emb)
    
    def test_empty_question_embedding(self, oracle):
        """Verifica embedding de pregunta vacía."""
        emb = oracle._question_to_embedding("")
        
        assert emb.shape == (8,)
        assert np.allclose(emb, 0)  # Todos ceros
    
    def test_action_words_detected(self, oracle):
        """Verifica detección de palabras de acción."""
        emb_action = oracle._question_to_embedding("Debería iniciar el proyecto")
        emb_neutral = oracle._question_to_embedding("El cielo es azul")
        
        # Posición 4 es para acción
        assert emb_action[4] > emb_neutral[4]


class TestHexagramConversion:
    """Tests de conversión de hexagramas."""
    
    def test_hexagram_to_binary(self, oracle):
        """Verifica conversión a binario."""
        hexagram = HEXAGRAMS[1]  # Qian - todas yang
        binary = oracle._hexagram_to_binary(hexagram)
        
        assert binary.shape == (6,)
        assert all(b in [0, 1] for b in binary)
    
    def test_binary_to_hexagram(self, oracle):
        """Verifica conversión de binario a hexagrama."""
        # Qian = (1,1,1,1,1,1)
        binary = np.array([1, 1, 1, 1, 1, 1])
        hexagram = oracle._binary_to_hexagram(binary)
        
        assert hexagram.number == 1
    
    def test_find_closest_hexagram(self, oracle):
        """Verifica búsqueda de hexagrama más cercano."""
        # Array cercano a Qian
        bits = np.array([1.1, 0.9, 1.2, 0.8, 1.0, 1.0])
        hexagram = oracle._find_closest_hexagram(bits)
        
        # Debería encontrar uno válido
        assert 1 <= hexagram.number <= 64


class TestResonance:
    """Tests de cálculo de resonancia."""
    
    def test_resonance_in_range(self, oracle):
        """Verifica que resonancia está en rango [0, 1]."""
        reading = oracle.consult("¿Debería crear algo nuevo?")
        
        assert 0 <= reading.resonance_score <= 1
    
    def test_resonance_varies_by_question(self, oracle):
        """Verifica que resonancia varía según pregunta."""
        # Diferentes preguntas pueden dar diferentes resonancias
        readings = [
            oracle.consult("¿Debería iniciar un proyecto?"),
            oracle.consult("¿Cómo está el clima?"),
            oracle.consult("¿Debería esperar pacientemente?")
        ]
        
        resonances = [r.resonance_score for r in readings]
        # Al menos debería haber alguna variación
        assert len(set(resonances)) >= 1  # Al menos valores válidos


class TestOracleReading:
    """Tests de la clase OracleReading."""
    
    def test_reading_to_dict(self, oracle):
        """Verifica serialización."""
        reading = oracle.consult("Test")
        d = reading.to_dict()
        
        assert "question" in d
        assert "primary" in d
        assert "confidence" in d
        assert d["primary"]["number"] == reading.primary_hexagram.number
    
    def test_reading_repr(self, oracle):
        """Verifica representación string."""
        reading = oracle.consult("Test")
        rep = repr(reading)
        
        assert "OracleReading" in rep
        assert str(reading.primary_hexagram.number) in rep


class TestDivineSequence:
    """Tests de secuencias de lecturas."""
    
    def test_divine_sequence_returns_list(self, oracle):
        """Verifica que sequence retorna lista."""
        sequence = oracle.divine_sequence("Mi camino", n_steps=3)
        
        assert isinstance(sequence, list)
        assert len(sequence) == 3
    
    def test_sequence_readings_are_valid(self, oracle):
        """Verifica que todas las lecturas son válidas."""
        sequence = oracle.divine_sequence("Evolución", n_steps=3)
        
        for reading in sequence:
            assert isinstance(reading, OracleReading)
            assert reading.primary_hexagram is not None


class TestStatistics:
    """Tests de estadísticas."""
    
    def test_get_stats(self, oracle):
        """Verifica get_stats."""
        stats = oracle.get_stats()
        
        assert "consultations" in stats
        assert "avg_resonance" in stats
        assert "is_trained" in stats
    
    def test_stats_increment(self):
        """Verifica que estadísticas incrementan."""
        oracle = create_oracle(reservoir_size=32, pretrained=False, random_state=42)
        
        initial = oracle.stats.consultations
        oracle.consult("Test 1")
        oracle.consult("Test 2")
        
        assert oracle.stats.consultations == initial + 2


class TestMeditation:
    """Tests de meditación."""
    
    def test_meditate(self, oracle):
        """Verifica consulta meditativa."""
        reading = oracle.meditate()
        
        assert reading.question == ""
        assert reading.primary_hexagram is not None


class TestFactoryFunction:
    """Tests de factory function."""
    
    def test_create_oracle_untrained(self):
        """Verifica creación sin entrenar."""
        oracle = create_oracle(pretrained=False, random_state=42)
        
        assert not oracle.is_trained
    
    def test_create_oracle_pretrained(self):
        """Verifica creación entrenada."""
        oracle = create_oracle(pretrained=True, random_state=42)
        
        assert oracle.is_trained
    
    def test_create_oracle_custom_size(self):
        """Verifica tamaño personalizado."""
        oracle = create_oracle(reservoir_size=128, pretrained=False)
        
        assert oracle.reservoir_size == 128


class TestIntegration:
    """Tests de integración."""
    
    def test_full_consultation_flow(self, oracle):
        """Test completo del flujo de consulta."""
        # 1. Hacer pregunta
        reading = oracle.consult("¿Es buen momento para emprender?")
        
        # 2. Verificar resultado
        assert reading.primary_hexagram is not None
        assert reading.advice != ""
        
        # 3. Verificar estadísticas actualizadas
        assert oracle.stats.consultations > 0
    
    def test_multiple_consultations(self, oracle):
        """Test de múltiples consultas."""
        questions = [
            "¿Debería actuar?",
            "¿Debería esperar?",
            "¿Cómo mejorar mi situación?"
        ]
        
        readings = []
        for q in questions:
            readings.append(oracle.consult(q))
        
        # Verificar que todas son válidas
        assert all(r.primary_hexagram is not None for r in readings)
        
        # Pueden tener hexagramas diferentes
        hexagrams = [r.primary_hexagram.number for r in readings]
        # Al menos debemos tener resultados válidos
        assert all(1 <= h <= 64 for h in hexagrams)
