"""
Tests para web/learning.py - Sistema de Aprendizaje Continuo.

Cobertura: OnlineLearner, LongTermMemory, EonLearningSystem
"""

import pytest
import numpy as np
import os
import sys
import json
import tempfile
import time

# Path setup
_current_dir = os.path.dirname(os.path.abspath(__file__))
_web_dir = os.path.dirname(_current_dir)
sys.path.insert(0, _web_dir)

from learning import OnlineLearner, LongTermMemory, EonLearningSystem


class TestOnlineLearner:
    """Tests para aprendizaje online de W_out."""
    
    def test_initialization(self):
        """Verifica inicialización correcta."""
        learner = OnlineLearner(n_reservoir=50, n_outputs=2)
        assert learner.n_reservoir == 50
        assert learner.n_outputs == 2
        assert learner.samples_learned == 0
        
    def test_correlation_matrix_shape(self):
        """Verifica forma de matriz de correlación."""
        learner = OnlineLearner(n_reservoir=100)
        assert learner._correlation_matrix.shape == (100, 100)
        
    def test_update_increments_samples(self):
        """Verifica que update incrementa contador."""
        learner = OnlineLearner(n_reservoir=50, n_outputs=1)
        state = np.random.randn(50)
        target = np.array([0.5])
        
        learner.update(state, target)
        assert learner.samples_learned == 1
        
        learner.update(state, target)
        assert learner.samples_learned == 2
        
    def test_update_with_feedback_weight(self):
        """Verifica actualización con peso de feedback."""
        learner = OnlineLearner(n_reservoir=50, n_outputs=1)
        state = np.random.randn(50)
        target = np.array([1.0])
        
        # Con feedback reforzado
        learner.update(state, target, feedback_weight=2.0)
        assert learner.samples_learned == 1
        
    def test_get_output_weights_shape(self):
        """Verifica forma de pesos de salida."""
        learner = OnlineLearner(n_reservoir=50, n_outputs=3)
        
        # Añadir algunas muestras
        for _ in range(10):
            state = np.random.randn(50)
            target = np.random.randn(3)
            learner.update(state, target)
            
        weights = learner.get_output_weights()
        assert weights.shape == (50, 3)
        
    def test_get_stats(self):
        """Verifica estadísticas del aprendizaje."""
        learner = OnlineLearner(n_reservoir=50)
        
        for _ in range(5):
            learner.update(np.random.randn(50), np.array([0.5]))
            
        stats = learner.get_stats()
        assert 'samples_learned' in stats
        assert stats['samples_learned'] == 5
        assert 'correlation_norm' in stats


class TestLongTermMemory:
    """Tests para memoria a largo plazo."""
    
    @pytest.fixture
    def temp_memory_file(self):
        """Crea archivo temporal para memoria."""
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)
            
    def test_initialization_creates_structure(self, temp_memory_file):
        """Verifica que se crea estructura de memoria."""
        memory = LongTermMemory(temp_memory_file)
        assert 'users' in memory.memory
        assert 'facts' in memory.memory
        assert 'summaries' in memory.memory
        
    def test_remember_user(self, temp_memory_file):
        """Verifica que recuerda usuarios."""
        memory = LongTermMemory(temp_memory_file)
        
        user = memory.remember_user('Jeremy', {'is_creator': True})
        assert user['name'] == 'Jeremy'
        assert user['is_creator'] is True
        assert user['interaction_count'] == 1
        
    def test_remember_user_increments_count(self, temp_memory_file):
        """Verifica que incrementa contador de interacciones."""
        memory = LongTermMemory(temp_memory_file)
        
        memory.remember_user('Alice')
        memory.remember_user('Alice')
        memory.remember_user('Alice')
        
        user = memory.get_user('Alice')
        assert user['interaction_count'] == 3
        
    def test_get_user_case_insensitive(self, temp_memory_file):
        """Verifica que búsqueda es case-insensitive."""
        memory = LongTermMemory(temp_memory_file)
        
        memory.remember_user('Bob')
        assert memory.get_user('bob') is not None
        assert memory.get_user('BOB') is not None
        
    def test_get_known_users(self, temp_memory_file):
        """Verifica listado de usuarios conocidos."""
        memory = LongTermMemory(temp_memory_file)
        
        memory.remember_user('Alice')
        memory.remember_user('Bob')
        memory.remember_user('Charlie')
        
        users = memory.get_known_users()
        assert len(users) == 3
        assert 'alice' in users
        
    def test_learn_fact(self, temp_memory_file):
        """Verifica aprendizaje de hechos."""
        memory = LongTermMemory(temp_memory_file)
        
        result = memory.learn_fact('El cielo es azul', source='test')
        assert result is True
        assert len(memory.memory['facts']) == 1
        
    def test_learn_fact_avoids_duplicates(self, temp_memory_file):
        """Verifica que evita hechos duplicados."""
        memory = LongTermMemory(temp_memory_file)
        
        memory.learn_fact('Python es genial')
        result = memory.learn_fact('Python es genial')
        
        # Debería retornar False por duplicado
        assert result is False
        assert len(memory.memory['facts']) == 1
        
    def test_search_facts(self, temp_memory_file):
        """Verifica búsqueda de hechos."""
        memory = LongTermMemory(temp_memory_file)
        
        memory.learn_fact('Python es un lenguaje de programación')
        memory.learn_fact('JavaScript se usa en web')
        memory.learn_fact('Python tiene NumPy para cálculos')
        
        results = memory.search_facts('Python', limit=5)
        # Debería encontrar al menos los hechos con Python
        assert len(results) >= 1
        
    def test_persistence(self, temp_memory_file):
        """Verifica que memoria persiste entre instancias."""
        memory1 = LongTermMemory(temp_memory_file)
        memory1.remember_user('TestUser')
        memory1.learn_fact('Dato persistente')
        
        # Nueva instancia debe cargar datos
        memory2 = LongTermMemory(temp_memory_file)
        assert memory2.get_user('testuser') is not None
        assert len(memory2.memory['facts']) == 1


class TestEonLearningSystem:
    """Tests para el sistema completo de aprendizaje."""
    
    @pytest.fixture
    def temp_dir(self):
        """Crea directorio temporal para datos."""
        import tempfile
        import shutil
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        shutil.rmtree(tmpdir, ignore_errors=True)
        
    def test_initialization(self, temp_dir):
        """Verifica inicialización del sistema."""
        system = EonLearningSystem(data_dir=temp_dir)
        assert system.learner is not None
        assert system.memory is not None
        
    def test_process_conversation_updates_stats(self, temp_dir):
        """Verifica que procesar conversación actualiza estadísticas."""
        system = EonLearningSystem(data_dir=temp_dir)
        
        result = system.process_conversation(
            user_message="Hola",
            bot_response="¡Hola! ¿Cómo estás?",
            intent="saludo"
        )
        
        assert isinstance(result, dict)
        assert 'learned_from_chat' in result
        
    def test_feedback_system_exists(self, temp_dir):
        """Verifica que el sistema de feedback existe."""
        system = EonLearningSystem(data_dir=temp_dir)
        
        assert system.feedback is not None
        
    def test_memory_integration(self, temp_dir):
        """Verifica integración con memoria."""
        system = EonLearningSystem(data_dir=temp_dir)
        
        # Registrar usuario a través de process_conversation
        system.process_conversation(
            user_message="Soy Carlos",
            bot_response="¡Hola Carlos!",
            intent="presentacion",
            user_name="Carlos"
        )
        
        # Debería estar en memoria
        user = system.memory.get_user('carlos')
        assert user is not None
        
    def test_consolidation_engine_exists(self, temp_dir):
        """Verifica que el motor de consolidación existe."""
        system = EonLearningSystem(data_dir=temp_dir)
        
        assert system.consolidation is not None


class TestIntegration:
    """Tests de integración del sistema de aprendizaje."""
    
    @pytest.fixture
    def temp_dir(self):
        """Crea directorio temporal."""
        import tempfile
        import shutil
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        shutil.rmtree(tmpdir, ignore_errors=True)
        
    def test_full_learning_cycle(self, temp_dir):
        """Test de ciclo completo de aprendizaje."""
        system = EonLearningSystem(data_dir=temp_dir)
        
        # 1. Usuario se presenta
        result = system.process_conversation(
            user_message="Soy Carlos",
            bot_response="¡Hola Carlos! Encantado de conocerte.",
            intent="presentacion",
            user_name="Carlos"
        )
        
        assert isinstance(result, dict)
        
        # 2. Aprender un hecho
        system.memory.learn_fact("Carlos es programador")
        
        # 3. Buscar hechos
        facts = system.memory.search_facts('Carlos')
        assert isinstance(facts, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
