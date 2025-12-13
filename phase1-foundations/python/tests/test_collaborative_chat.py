"""
Tests para CollaborativeChat - Chat Multi-Nodo
==============================================
"""

import pytest
import numpy as np
from core.collaborative_chat import (
    ChatNode, NodeRole, Intent, ChatMessage,
    CollaborativeChat, NodeContribution, CollaborativeResponse,
    create_collaborative_chat
)


class TestChatNode:
    """Tests para ChatNode individual."""
    
    def test_create_node(self):
        """Test crear nodo con rol específico."""
        node = ChatNode(NodeRole.INTENT, n_reservoir=30, seed=42)
        
        assert node.role == NodeRole.INTENT
        assert node.n_reservoir == 30
        assert len(node.state) == 30
        assert node.node_id.startswith("intent-")
    
    def test_node_roles(self):
        """Test que cada rol crea nodo diferente."""
        roles = [NodeRole.INTENT, NodeRole.RESPONSE, NodeRole.COHERENCE, 
                 NodeRole.SENTIMENT, NodeRole.CONTEXT]
        
        for role in roles:
            node = ChatNode(role, seed=42)
            assert node.role == role
            assert role.value in node.node_id
    
    def test_process_message(self):
        """Test procesar mensaje genera contribución."""
        node = ChatNode(NodeRole.INTENT, seed=42)
        message = ChatMessage(content="Hola, ¿cómo estás?")
        
        contribution = node.process(message)
        
        assert isinstance(contribution, NodeContribution)
        assert contribution.node_id == node.node_id
        assert contribution.role == NodeRole.INTENT
        assert 0 <= contribution.confidence <= 1
        assert contribution.processing_time > 0
    
    def test_intent_detection_greeting(self):
        """Test detectar intención de saludo."""
        node = ChatNode(NodeRole.INTENT, seed=42)
        message = ChatMessage(content="¡Hola! Buenos días")
        
        contribution = node.process(message)
        
        assert contribution.output['intent'] == 'greeting'
        assert contribution.output['scores']['greeting'] > 0
    
    def test_intent_detection_question(self):
        """Test detectar intención de pregunta."""
        node = ChatNode(NodeRole.INTENT, seed=42)
        message = ChatMessage(content="¿Qué hora es?")
        
        contribution = node.process(message)
        
        assert contribution.output['intent'] == 'question'
        assert contribution.output['is_question'] is True
    
    def test_intent_detection_farewell(self):
        """Test detectar intención de despedida."""
        node = ChatNode(NodeRole.INTENT, seed=42)
        message = ChatMessage(content="Adiós, hasta luego")
        
        contribution = node.process(message)
        
        assert contribution.output['intent'] == 'farewell'
    
    def test_intent_detection_command(self):
        """Test detectar intención de comando."""
        node = ChatNode(NodeRole.INTENT, seed=42)
        message = ChatMessage(content="Genera un reporte")
        
        contribution = node.process(message)
        
        assert contribution.output['intent'] == 'command'
    
    def test_intent_detection_technical(self):
        """Test detectar intención técnica."""
        node = ChatNode(NodeRole.INTENT, seed=42)
        message = ChatMessage(content="Hay un error en la función")
        
        contribution = node.process(message)
        
        assert contribution.output['intent'] == 'technical'
    
    def test_response_node_output(self):
        """Test nodo de respuesta genera vector."""
        node = ChatNode(NodeRole.RESPONSE, seed=42)
        message = ChatMessage(content="Cuéntame algo interesante")
        
        contribution = node.process(message)
        
        assert 'response_vector' in contribution.output
        assert 'suggested_length' in contribution.output
        assert 'suggested_formality' in contribution.output
        assert len(contribution.output['response_vector']) == 16
    
    def test_coherence_node_output(self):
        """Test nodo de coherencia evalúa mensaje."""
        node = ChatNode(NodeRole.COHERENCE, seed=42)
        message = ChatMessage(content="Este es un mensaje de prueba")
        
        contribution = node.process(message)
        
        assert 'coherence_score' in contribution.output
        assert 'consistency' in contribution.output
        assert 0 <= contribution.output['coherence_score'] <= 1
    
    def test_sentiment_node_positive(self):
        """Test nodo de sentimiento detecta positivo."""
        node = ChatNode(NodeRole.SENTIMENT, seed=42)
        message = ChatMessage(content="¡Me encanta! Es genial y excelente")
        
        contribution = node.process(message)
        
        assert 'sentiment' in contribution.output
        assert contribution.output['positive_indicators'] > 0
        assert contribution.output['sentiment'] > 0
    
    def test_sentiment_node_negative(self):
        """Test nodo de sentimiento detecta negativo."""
        node = ChatNode(NodeRole.SENTIMENT, seed=42)
        message = ChatMessage(content="Es terrible, lo odio")
        
        contribution = node.process(message)
        
        assert contribution.output['negative_indicators'] > 0
        assert contribution.output['sentiment'] < 0
    
    def test_context_node_stores_patterns(self):
        """Test nodo de contexto almacena patrones."""
        node = ChatNode(NodeRole.CONTEXT, seed=42)
        
        messages = [
            ChatMessage(content="Primer mensaje"),
            ChatMessage(content="Segundo mensaje"),
            ChatMessage(content="Tercer mensaje")
        ]
        
        for msg in messages:
            node.process(msg)
        
        # Verificar que se almacenaron patrones
        contribution = node.process(ChatMessage(content="Cuarto mensaje"))
        assert contribution.output['stored_patterns'] >= 3
    
    def test_node_state_updates(self):
        """Test que el estado del nodo se actualiza."""
        node = ChatNode(NodeRole.INTENT, seed=42)
        initial_state = node.state.copy()
        
        node.process(ChatMessage(content="Mensaje de prueba"))
        
        assert not np.allclose(node.state, initial_state)
    
    def test_node_history_grows(self):
        """Test que el historial crece con cada mensaje."""
        node = ChatNode(NodeRole.INTENT, seed=42)
        assert len(node.history) == 0
        
        for i in range(5):
            node.process(ChatMessage(content=f"Mensaje {i}"))
        
        assert len(node.history) == 5
    
    def test_node_history_limited(self):
        """Test que el historial tiene límite."""
        node = ChatNode(NodeRole.INTENT, seed=42)
        
        for i in range(150):
            node.process(ChatMessage(content=f"Mensaje {i}"))
        
        assert len(node.history) <= 100
    
    def test_reset_state(self):
        """Test resetear estado del nodo."""
        node = ChatNode(NodeRole.INTENT, seed=42)
        node.process(ChatMessage(content="Mensaje"))
        
        node.reset_state()
        
        assert np.allclose(node.state, np.zeros(node.n_reservoir))
        assert len(node.history) == 0
    
    def test_reproducibility_with_seed(self):
        """Test reproducibilidad con misma semilla."""
        node1 = ChatNode(NodeRole.INTENT, seed=123)
        node2 = ChatNode(NodeRole.INTENT, seed=123)
        
        msg = ChatMessage(content="Mensaje de prueba")
        
        contrib1 = node1.process(msg)
        contrib2 = node2.process(msg)
        
        assert contrib1.output == contrib2.output


class TestChatMessage:
    """Tests para ChatMessage."""
    
    def test_create_message(self):
        """Test crear mensaje básico."""
        msg = ChatMessage(content="Hola mundo")
        
        assert msg.content == "Hola mundo"
        assert msg.sender == "user"
        assert msg.timestamp > 0
        assert len(msg.context_hash) == 8
    
    def test_message_with_sender(self):
        """Test mensaje con sender personalizado."""
        msg = ChatMessage(content="Test", sender="bot")
        
        assert msg.sender == "bot"
    
    def test_message_hash_unique(self):
        """Test que mensajes diferentes tienen hash diferente."""
        msg1 = ChatMessage(content="Mensaje 1")
        msg2 = ChatMessage(content="Mensaje 2")
        
        assert msg1.context_hash != msg2.context_hash


class TestCollaborativeChat:
    """Tests para CollaborativeChat."""
    
    def test_create_chat_system(self):
        """Test crear sistema de chat colaborativo."""
        chat = CollaborativeChat(n_reservoir=30, seed=42)
        
        assert len(chat.nodes) == 3  # Intent, Response, Coherence
        assert NodeRole.INTENT in chat.nodes
        assert NodeRole.RESPONSE in chat.nodes
        assert NodeRole.COHERENCE in chat.nodes
    
    def test_process_message_returns_response(self):
        """Test procesar mensaje retorna respuesta colaborativa."""
        chat = CollaborativeChat(seed=42)
        
        response = chat.process_message("Hola, ¿cómo estás?")
        
        assert isinstance(response, CollaborativeResponse)
        assert len(response.content) > 0
        assert len(response.contributions) == 3
        assert response.total_time > 0
    
    def test_contributions_from_all_nodes(self):
        """Test que todos los nodos contribuyen."""
        chat = CollaborativeChat(seed=42)
        
        response = chat.process_message("Test message")
        
        roles = {c.role for c in response.contributions}
        assert NodeRole.INTENT in roles
        assert NodeRole.RESPONSE in roles
        assert NodeRole.COHERENCE in roles
    
    def test_coherence_score_valid(self):
        """Test que coherence_score está en rango válido."""
        chat = CollaborativeChat(seed=42)
        
        response = chat.process_message("Test message")
        
        assert 0 <= response.coherence_score <= 1
    
    def test_greeting_response(self):
        """Test respuesta a saludo."""
        chat = CollaborativeChat(seed=42)
        
        response = chat.process_message("¡Hola!")
        
        assert response.metadata['intent'] == 'greeting'
    
    def test_question_response(self):
        """Test respuesta a pregunta."""
        chat = CollaborativeChat(seed=42)
        
        response = chat.process_message("¿Qué es Python?")
        
        assert response.metadata['intent'] == 'question'
    
    def test_farewell_response(self):
        """Test respuesta a despedida."""
        chat = CollaborativeChat(seed=42)
        
        response = chat.process_message("Adiós")
        
        assert response.metadata['intent'] == 'farewell'
    
    def test_conversation_history_grows(self):
        """Test que el historial crece."""
        chat = CollaborativeChat(seed=42)
        
        chat.process_message("Mensaje 1")
        chat.process_message("Mensaje 2")
        
        assert len(chat.conversation_history) == 2
        assert len(chat.response_history) == 2
    
    def test_add_optional_node(self):
        """Test añadir nodo opcional."""
        chat = CollaborativeChat(seed=42)
        initial_nodes = len(chat.nodes)
        
        chat.add_node(NodeRole.SENTIMENT)
        
        assert len(chat.nodes) == initial_nodes + 1
        assert NodeRole.SENTIMENT in chat.nodes
    
    def test_get_node_states(self):
        """Test obtener estados de nodos."""
        chat = CollaborativeChat(seed=42)
        chat.process_message("Test")
        
        states = chat.get_node_states()
        
        assert 'intent' in states
        assert 'response' in states
        assert 'coherence' in states
        assert states['intent']['history_length'] == 1
    
    def test_reset_chat(self):
        """Test resetear chat."""
        chat = CollaborativeChat(seed=42)
        chat.process_message("Mensaje 1")
        chat.process_message("Mensaje 2")
        
        chat.reset()
        
        assert len(chat.conversation_history) == 0
        assert len(chat.response_history) == 0
    
    def test_conversation_summary(self):
        """Test resumen de conversación."""
        chat = CollaborativeChat(seed=42)
        chat.process_message("Hola")
        chat.process_message("¿Cómo estás?")
        chat.process_message("Adiós")
        
        summary = chat.get_conversation_summary()
        
        assert summary['messages'] == 3
        assert summary['responses'] == 3
        assert 'intents' in summary
    
    def test_on_contribution_callback(self):
        """Test callback de contribución."""
        chat = CollaborativeChat(seed=42)
        contributions = []
        chat.on_contribution = lambda c: contributions.append(c)
        
        chat.process_message("Test")
        
        assert len(contributions) == 3
    
    def test_on_consensus_callback(self):
        """Test callback de consenso."""
        chat = CollaborativeChat(seed=42)
        responses = []
        chat.on_consensus = lambda r: responses.append(r)
        
        chat.process_message("Test")
        
        assert len(responses) == 1
    
    def test_multiple_messages_coherence(self):
        """Test coherencia mejora con múltiples mensajes."""
        chat = CollaborativeChat(seed=42)
        
        # Primera respuesta puede tener menor coherencia
        r1 = chat.process_message("Hola")
        
        # Mensajes subsecuentes
        r2 = chat.process_message("¿Cómo va todo?")
        r3 = chat.process_message("Me alegro")
        
        # La coherencia debe ser válida en todos los casos
        assert 0 <= r1.coherence_score <= 1
        assert 0 <= r2.coherence_score <= 1
        assert 0 <= r3.coherence_score <= 1
    
    def test_metadata_contains_required_fields(self):
        """Test que metadata tiene campos requeridos."""
        chat = CollaborativeChat(seed=42)
        
        response = chat.process_message("Test")
        
        assert 'intent' in response.metadata
        assert 'avg_confidence' in response.metadata
        assert 'nodes_involved' in response.metadata


class TestCreateCollaborativeChat:
    """Tests para función factory create_collaborative_chat."""
    
    def test_create_basic_chat(self):
        """Test crear chat básico."""
        chat = create_collaborative_chat(seed=42)
        
        assert isinstance(chat, CollaborativeChat)
        assert len(chat.nodes) == 3
    
    def test_create_with_sentiment(self):
        """Test crear chat con nodo de sentimiento."""
        chat = create_collaborative_chat(include_sentiment=True, seed=42)
        
        assert NodeRole.SENTIMENT in chat.nodes
        assert len(chat.nodes) == 4
    
    def test_create_with_context(self):
        """Test crear chat con nodo de contexto."""
        chat = create_collaborative_chat(include_context=True, seed=42)
        
        assert NodeRole.CONTEXT in chat.nodes
        assert len(chat.nodes) == 4
    
    def test_create_full_featured(self):
        """Test crear chat con todos los nodos."""
        chat = create_collaborative_chat(
            include_sentiment=True,
            include_context=True,
            seed=42
        )
        
        assert len(chat.nodes) == 5
        assert NodeRole.SENTIMENT in chat.nodes
        assert NodeRole.CONTEXT in chat.nodes
    
    def test_custom_reservoir_size(self):
        """Test tamaño de reservorio personalizado."""
        chat = create_collaborative_chat(n_reservoir=100, seed=42)
        
        for node in chat.nodes.values():
            assert node.n_reservoir == 100


class TestIntegration:
    """Tests de integración del sistema completo."""
    
    def test_full_conversation(self):
        """Test conversación completa."""
        chat = create_collaborative_chat(
            include_sentiment=True,
            include_context=True,
            seed=42
        )
        
        messages = [
            "Hola, buenas tardes",
            "¿Puedes ayudarme con un problema técnico?",
            "Hay un error en mi código Python",
            "Gracias por la ayuda",
            "Adiós"
        ]
        
        responses = []
        for msg in messages:
            r = chat.process_message(msg)
            responses.append(r)
        
        # Verificar todas las respuestas
        assert len(responses) == 5
        
        # Verificar intenciones detectadas
        intents = [r.metadata['intent'] for r in responses]
        assert 'greeting' in intents
        assert 'farewell' in intents
    
    def test_concurrent_nodes_contribute(self):
        """Test que todos los nodos contribuyen correctamente."""
        chat = create_collaborative_chat(
            include_sentiment=True,
            include_context=True,
            seed=42
        )
        
        response = chat.process_message("¡Estoy muy feliz hoy! ¿Cómo estás tú?")
        
        # 5 nodos deben contribuir
        assert len(response.contributions) == 5
        
        # Cada rol debe estar presente
        roles = {c.role for c in response.contributions}
        assert NodeRole.INTENT in roles
        assert NodeRole.RESPONSE in roles
        assert NodeRole.COHERENCE in roles
        assert NodeRole.SENTIMENT in roles
        assert NodeRole.CONTEXT in roles
