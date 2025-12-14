"""
Proyecto Eón - Chat Multi-Nodo Colaborativo
============================================

Sistema de chat distribuido donde múltiples nodos ESN especializados
colaboran para generar respuestas coherentes:

- Nodo A (Intent): Analiza la intención del mensaje
- Nodo B (Response): Genera la respuesta base
- Nodo C (Coherence): Valida y refina la coherencia

Cada nodo tiene un rol específico y contribuye al resultado final.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Callable, Tuple, Any
import numpy as np
import hashlib
import time

# Importar constantes globales
try:
    from utils.constants import EPSILON
except ImportError:
    EPSILON = 1e-10


class NodeRole(Enum):
    """Roles especializados de nodos en el chat colaborativo."""
    INTENT = "intent"           # Análisis de intención
    RESPONSE = "response"       # Generación de respuesta
    COHERENCE = "coherence"     # Validación de coherencia
    SENTIMENT = "sentiment"     # Análisis de sentimiento
    CONTEXT = "context"         # Gestión de contexto


class Intent(Enum):
    """Intenciones detectables en mensajes."""
    GREETING = "greeting"
    QUESTION = "question"
    STATEMENT = "statement"
    COMMAND = "command"
    FAREWELL = "farewell"
    EMOTIONAL = "emotional"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    UNKNOWN = "unknown"


@dataclass
class NodeContribution:
    """Contribución de un nodo al procesamiento."""
    node_id: str
    role: NodeRole
    output: Any
    confidence: float
    processing_time: float
    metadata: Dict = field(default_factory=dict)


@dataclass
class ChatMessage:
    """Mensaje en el chat colaborativo."""
    content: str
    timestamp: float = field(default_factory=time.time)
    sender: str = "user"
    intent: Optional[Intent] = None
    sentiment: float = 0.0  # -1 a 1
    context_hash: str = ""
    
    def __post_init__(self):
        if not self.context_hash:
            self.context_hash = hashlib.md5(
                f"{self.content}{self.timestamp}".encode()
            ).hexdigest()[:8]


@dataclass
class CollaborativeResponse:
    """Respuesta generada colaborativamente."""
    content: str
    contributions: List[NodeContribution]
    coherence_score: float
    total_time: float
    consensus_reached: bool
    metadata: Dict = field(default_factory=dict)


class ChatNode:
    """
    Nodo ESN especializado para procesamiento de chat.
    
    Cada nodo tiene un rol específico y procesa mensajes
    de acuerdo a su especialización.
    """
    
    def __init__(
        self,
        role: NodeRole,
        n_reservoir: int = 50,
        spectral_radius: float = 0.9,
        seed: Optional[int] = None
    ):
        """
        Inicializa un nodo de chat.
        
        Args:
            role: Rol especializado del nodo
            n_reservoir: Tamaño del reservorio
            spectral_radius: Radio espectral de la matriz W
            seed: Semilla para reproducibilidad
        """
        self.role = role
        self.n_reservoir = n_reservoir
        self.spectral_radius = spectral_radius
        
        # Generar ID único
        self.node_id = f"{role.value}-{hashlib.md5(str(seed or time.time()).encode()).hexdigest()[:6]}"
        
        # RNG local
        self.rng = np.random.default_rng(seed)
        
        # Inicializar reservorio
        self._init_reservoir()
        
        # Estado interno
        self.state = np.zeros(n_reservoir)
        self.history: List[np.ndarray] = []
        self.is_trained = False
        
        # Patrones aprendidos (específicos del rol)
        self.learned_patterns: Dict[str, np.ndarray] = {}
    
    def _init_reservoir(self):
        """Inicializa las matrices del reservorio."""
        # Matriz de reservorio W
        W = self.rng.standard_normal((self.n_reservoir, self.n_reservoir))
        eigenvalues = np.linalg.eigvals(W)
        max_eigenvalue = np.max(np.abs(eigenvalues))
        if max_eigenvalue > 0:
            self.W = W * (self.spectral_radius / max_eigenvalue)
        else:
            self.W = W * self.spectral_radius
        
        # Matriz de entrada Win (dimensión flexible)
        self.Win_base = self.rng.uniform(-1, 1, (self.n_reservoir, 1))
        
        # Leak rate
        self.leak_rate = 0.3
    
    def _encode_text(self, text: str) -> np.ndarray:
        """
        Codifica texto a vector numérico.
        
        Usa una codificación simple basada en caracteres ASCII
        y características estadísticas del texto.
        """
        if not text:
            return np.zeros(32)
        
        # Características básicas
        features = []
        
        # Longitud normalizada
        features.append(min(len(text) / 500, 1.0))
        
        # Proporción de mayúsculas
        upper_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        features.append(upper_ratio)
        
        # Proporción de signos de puntuación
        punct = ".,!?;:'\"-"
        punct_ratio = sum(1 for c in text if c in punct) / max(len(text), 1)
        features.append(punct_ratio)
        
        # Número de palabras normalizado
        words = text.split()
        features.append(min(len(words) / 100, 1.0))
        
        # Longitud promedio de palabra
        avg_word_len = np.mean([len(w) for w in words]) if words else 0
        features.append(min(avg_word_len / 15, 1.0))
        
        # Presencia de signos especiales
        features.append(1.0 if '?' in text else 0.0)
        features.append(1.0 if '!' in text else 0.0)
        features.append(1.0 if any(c.isdigit() for c in text) else 0.0)
        
        # Hash-based features (8 features)
        text_hash = hashlib.sha256(text.encode()).digest()
        for i in range(8):
            features.append(text_hash[i] / 255.0)
        
        # Bag of characters (primeros 16 caracteres normalizados)
        chars = [ord(c) / 127.0 for c in text[:16]]
        chars.extend([0.0] * (16 - len(chars)))
        features.extend(chars)
        
        return np.array(features[:32])
    
    def process(self, message: ChatMessage) -> NodeContribution:
        """
        Procesa un mensaje según el rol del nodo.
        
        Args:
            message: Mensaje a procesar
            
        Returns:
            Contribución del nodo
        """
        start_time = time.time()
        
        # Codificar mensaje
        input_vec = self._encode_text(message.content)
        
        # Expandir Win si es necesario
        if self.Win_base.shape[1] != len(input_vec):
            self.Win_base = self.rng.uniform(-1, 1, (self.n_reservoir, len(input_vec)))
        
        # Actualizar estado del reservorio
        pre_activation = np.dot(self.W, self.state) + np.dot(self.Win_base, input_vec)
        new_state = np.tanh(pre_activation)
        self.state = (1 - self.leak_rate) * self.state + self.leak_rate * new_state
        
        # Guardar en historial
        self.history.append(self.state.copy())
        if len(self.history) > 100:
            self.history.pop(0)
        
        # Procesar según rol
        if self.role == NodeRole.INTENT:
            output = self._detect_intent(message, input_vec)
        elif self.role == NodeRole.RESPONSE:
            output = self._generate_response_vector(message, input_vec)
        elif self.role == NodeRole.COHERENCE:
            output = self._evaluate_coherence(message, input_vec)
        elif self.role == NodeRole.SENTIMENT:
            output = self._analyze_sentiment(message, input_vec)
        elif self.role == NodeRole.CONTEXT:
            output = self._manage_context(message, input_vec)
        else:
            output = self.state[:10].tolist()
        
        # Calcular confianza basada en activación del reservorio
        activation_strength = np.mean(np.abs(self.state))
        confidence = min(activation_strength * 2, 1.0)
        
        processing_time = time.time() - start_time
        
        return NodeContribution(
            node_id=self.node_id,
            role=self.role,
            output=output,
            confidence=confidence,
            processing_time=processing_time,
            metadata={
                'state_norm': float(np.linalg.norm(self.state)),
                'history_len': len(self.history)
            }
        )
    
    def _detect_intent(self, message: ChatMessage, input_vec: np.ndarray) -> Dict:
        """Detecta la intención del mensaje."""
        text_lower = message.content.lower().strip()
        
        # Patrones de intención
        greeting_patterns = ['hola', 'hello', 'hi', 'buenos', 'buenas', 'saludos', 'hey']
        question_patterns = ['?', 'qué', 'que', 'cómo', 'como', 'cuál', 'cual', 'por qué', 'porqué', 'dónde', 'donde', 'cuándo', 'cuando', 'quién', 'quien']
        farewell_patterns = ['adiós', 'adios', 'bye', 'chao', 'hasta luego', 'nos vemos']
        command_patterns = ['haz', 'hazme', 'genera', 'crea', 'muestra', 'dime', 'explica']
        emotional_patterns = ['siento', 'amo', 'odio', 'feliz', 'triste', 'enojado', 'miedo', 'alegre']
        technical_patterns = ['código', 'codigo', 'función', 'funcion', 'error', 'bug', 'python', 'variable', 'clase', 'método', 'metodo']
        creative_patterns = ['imagina', 'inventa', 'sueña', 'historia', 'cuento', 'poema', 'arte']
        
        # Calcular scores
        scores = {}
        scores['greeting'] = sum(1 for p in greeting_patterns if p in text_lower)
        scores['question'] = sum(1 for p in question_patterns if p in text_lower)
        scores['farewell'] = sum(1 for p in farewell_patterns if p in text_lower)
        scores['command'] = sum(1 for p in command_patterns if p in text_lower)
        scores['emotional'] = sum(1 for p in emotional_patterns if p in text_lower)
        scores['technical'] = sum(1 for p in technical_patterns if p in text_lower)
        scores['creative'] = sum(1 for p in creative_patterns if p in text_lower)
        scores['statement'] = 1 if not any(scores.values()) else 0
        
        # Determinar intención dominante
        max_score = max(scores.values())
        if max_score == 0:
            detected_intent = Intent.UNKNOWN
        else:
            intent_map = {
                'greeting': Intent.GREETING,
                'question': Intent.QUESTION,
                'farewell': Intent.FAREWELL,
                'command': Intent.COMMAND,
                'emotional': Intent.EMOTIONAL,
                'technical': Intent.TECHNICAL,
                'creative': Intent.CREATIVE,
                'statement': Intent.STATEMENT
            }
            dominant = max(scores, key=scores.get)
            detected_intent = intent_map.get(dominant, Intent.UNKNOWN)
        
        # Usar estado del reservorio para ajustar confianza
        reservoir_confidence = np.mean(np.abs(self.state[:10]))
        
        return {
            'intent': detected_intent.value,
            'scores': scores,
            'confidence': min(max_score / 3 + reservoir_confidence, 1.0),
            'is_question': '?' in message.content
        }
    
    def _generate_response_vector(self, message: ChatMessage, input_vec: np.ndarray) -> Dict:
        """Genera un vector de respuesta base."""
        # Usar estado del reservorio como base para generar respuesta
        response_state = self.state[:16]
        
        # Características de la respuesta sugerida
        suggested_length = int(20 + np.abs(response_state[0]) * 100)
        suggested_formality = float(np.tanh(response_state[1]))  # -1 casual, +1 formal
        suggested_emotion = float(np.tanh(response_state[2]))    # -1 negativo, +1 positivo
        
        # Keywords sugeridas basadas en activación
        top_activations = np.argsort(np.abs(self.state))[-5:]
        
        # Calcular entropía correctamente excluyendo valores cercanos a cero
        abs_state = np.abs(self.state)
        nonzero_mask = abs_state > EPSILON
        if np.any(nonzero_mask):
            p = abs_state[nonzero_mask]
            p = p / np.sum(p)  # Normalizar a distribución de probabilidad
            state_entropy = float(-np.sum(p * np.log(p)))
        else:
            state_entropy = 0.0
        
        return {
            'response_vector': response_state.tolist(),
            'suggested_length': suggested_length,
            'suggested_formality': suggested_formality,
            'suggested_emotion': suggested_emotion,
            'top_activations': top_activations.tolist(),
            'state_entropy': state_entropy
        }
    
    def _evaluate_coherence(self, message: ChatMessage, input_vec: np.ndarray) -> Dict:
        """Evalúa la coherencia del mensaje con el contexto."""
        # Coherencia basada en similitud con estados anteriores
        if len(self.history) < 2:
            coherence_score = 0.5
            consistency = 0.5
        else:
            # Similitud con estado anterior
            prev_state = self.history[-2]
            similarity = np.dot(self.state, prev_state) / (
                np.linalg.norm(self.state) * np.linalg.norm(prev_state) + EPSILON
            )
            coherence_score = (similarity + 1) / 2  # Normalizar a [0, 1]
            
            # Consistencia a lo largo del historial
            if len(self.history) > 5:
                recent_states = np.array(self.history[-5:])
                variance = np.mean(np.var(recent_states, axis=0))
                consistency = float(1 / (1 + variance))
            else:
                consistency = 0.5
        
        return {
            'coherence_score': float(coherence_score),
            'consistency': float(consistency),
            'state_stability': float(1 - np.std(self.state)),
            'needs_clarification': coherence_score < 0.3
        }
    
    def _analyze_sentiment(self, message: ChatMessage, input_vec: np.ndarray) -> Dict:
        """Analiza el sentimiento del mensaje."""
        text_lower = message.content.lower()
        
        # Diccionario simple de sentimiento
        positive_words = ['bueno', 'bien', 'genial', 'excelente', 'gracias', 'amor', 'feliz', 'alegre', 'me gusta', 'increíble', 'fantástico']
        negative_words = ['malo', 'mal', 'terrible', 'horrible', 'odio', 'triste', 'enojado', 'peor', 'no me gusta', 'problema', 'error']
        
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)
        
        # Sentimiento combinado con estado del reservorio
        base_sentiment = (pos_count - neg_count) / max(pos_count + neg_count, 1)
        reservoir_sentiment = float(np.tanh(np.mean(self.state[:5])))
        
        combined_sentiment = 0.7 * base_sentiment + 0.3 * reservoir_sentiment
        
        return {
            'sentiment': float(np.clip(combined_sentiment, -1, 1)),
            'positive_indicators': pos_count,
            'negative_indicators': neg_count,
            'intensity': float(abs(combined_sentiment)),
            'is_neutral': abs(combined_sentiment) < 0.2
        }
    
    def _manage_context(self, message: ChatMessage, input_vec: np.ndarray) -> Dict:
        """Gestiona el contexto de la conversación."""
        # Extraer topics mencionados
        words = message.content.lower().split()
        
        # Actualizar patrones aprendidos
        context_key = message.context_hash
        self.learned_patterns[context_key] = self.state.copy()
        
        # Limitar patrones almacenados
        if len(self.learned_patterns) > 50:
            oldest_key = list(self.learned_patterns.keys())[0]
            del self.learned_patterns[oldest_key]
        
        # Encontrar contextos similares
        similar_contexts = []
        for key, pattern in self.learned_patterns.items():
            if key != context_key:
                similarity = np.dot(self.state, pattern) / (
                    np.linalg.norm(self.state) * np.linalg.norm(pattern) + 1e-10
                )
                if similarity > 0.5:
                    similar_contexts.append({
                        'key': key,
                        'similarity': float(similarity)
                    })
        
        return {
            'context_key': context_key,
            'stored_patterns': len(self.learned_patterns),
            'similar_contexts': similar_contexts[:5],
            'word_count': len(words),
            'unique_words': len(set(words))
        }
    
    def reset_state(self):
        """Resetea el estado del nodo."""
        self.state = np.zeros(self.n_reservoir)
        self.history.clear()


class CollaborativeChat:
    """
    Sistema de chat colaborativo multi-nodo.
    
    Coordina múltiples nodos ESN especializados para generar
    respuestas coherentes y contextualmente apropiadas.
    """
    
    def __init__(
        self,
        n_reservoir: int = 50,
        spectral_radius: float = 0.9,
        seed: Optional[int] = None
    ):
        """
        Inicializa el sistema de chat colaborativo.
        
        Args:
            n_reservoir: Tamaño del reservorio para cada nodo
            spectral_radius: Radio espectral
            seed: Semilla base para reproducibilidad
        """
        self.n_reservoir = n_reservoir
        self.spectral_radius = spectral_radius
        
        # RNG para generar seeds de nodos
        rng = np.random.default_rng(seed)
        
        # Crear nodos especializados
        self.nodes: Dict[NodeRole, ChatNode] = {
            NodeRole.INTENT: ChatNode(NodeRole.INTENT, n_reservoir, spectral_radius, int(rng.integers(0, 2**31))),
            NodeRole.RESPONSE: ChatNode(NodeRole.RESPONSE, n_reservoir, spectral_radius, int(rng.integers(0, 2**31))),
            NodeRole.COHERENCE: ChatNode(NodeRole.COHERENCE, n_reservoir, spectral_radius, int(rng.integers(0, 2**31))),
        }
        
        # Nodos opcionales (se pueden añadir después)
        self._optional_roles = [NodeRole.SENTIMENT, NodeRole.CONTEXT]
        
        # Historial de conversación
        self.conversation_history: List[ChatMessage] = []
        self.response_history: List[CollaborativeResponse] = []
        
        # Templates de respuesta
        self._response_templates = self._init_templates()
        
        # Callbacks para extensibilidad
        self.on_contribution: Optional[Callable[[NodeContribution], None]] = None
        self.on_consensus: Optional[Callable[[CollaborativeResponse], None]] = None
    
    def _init_templates(self) -> Dict[str, List[str]]:
        """Inicializa templates de respuesta por intención."""
        return {
            'greeting': [
                "¡Hola! ¿En qué puedo ayudarte hoy?",
                "¡Saludos! Estoy aquí para asistirte.",
                "¡Bienvenido! ¿Cómo puedo ser útil?"
            ],
            'farewell': [
                "¡Hasta pronto! Fue un placer conversar.",
                "¡Adiós! Que tengas un excelente día.",
                "Nos vemos. Recuerda que siempre estaré aquí."
            ],
            'question': [
                "Interesante pregunta. Déjame pensar...",
                "Esa es una buena consulta. Considerando el contexto...",
                "Me preguntas sobre algo relevante. Mi análisis indica..."
            ],
            'command': [
                "Entendido. Procesando tu solicitud...",
                "Claro, trabajando en eso...",
                "Por supuesto. Ejecutando..."
            ],
            'emotional': [
                "Entiendo cómo te sientes. ",
                "Aprecio que compartas eso conmigo. ",
                "Tus emociones son válidas. "
            ],
            'technical': [
                "Desde un punto de vista técnico, ",
                "Analizando los aspectos técnicos, ",
                "En términos de implementación, "
            ],
            'creative': [
                "Imaginando posibilidades... ",
                "Explorando ideas creativas... ",
                "Dejando fluir la creatividad... "
            ],
            'statement': [
                "Comprendo. ",
                "Interesante observación. ",
                "Tomo nota de eso. "
            ],
            'unknown': [
                "Hmm, procesando tu mensaje... ",
                "Déjame analizar eso... ",
                "Considerando lo que dices... "
            ]
        }
    
    def add_node(self, role: NodeRole, seed: Optional[int] = None):
        """
        Añade un nodo opcional al sistema.
        
        Args:
            role: Rol del nodo a añadir
            seed: Semilla para el nodo
        """
        if role not in self.nodes:
            self.nodes[role] = ChatNode(
                role, self.n_reservoir, self.spectral_radius, seed
            )
    
    def process_message(self, content: str, sender: str = "user") -> CollaborativeResponse:
        """
        Procesa un mensaje a través de todos los nodos colaborativos.
        
        Args:
            content: Contenido del mensaje
            sender: Identificador del remitente
            
        Returns:
            Respuesta colaborativa generada
        """
        start_time = time.time()
        
        # Crear mensaje
        message = ChatMessage(content=content, sender=sender)
        self.conversation_history.append(message)
        
        # Recolectar contribuciones de todos los nodos
        contributions: List[NodeContribution] = []
        
        for role, node in self.nodes.items():
            contribution = node.process(message)
            contributions.append(contribution)
            
            if self.on_contribution:
                self.on_contribution(contribution)
        
        # Extraer información clave de las contribuciones
        intent_data = None
        response_data = None
        coherence_data = None
        
        for contrib in contributions:
            if contrib.role == NodeRole.INTENT:
                intent_data = contrib.output
                message.intent = Intent(intent_data['intent'])
            elif contrib.role == NodeRole.RESPONSE:
                response_data = contrib.output
            elif contrib.role == NodeRole.COHERENCE:
                coherence_data = contrib.output
        
        # Generar respuesta combinando contribuciones
        response_content = self._generate_response(
            message, intent_data, response_data, coherence_data
        )
        
        # Calcular métricas de consenso
        avg_confidence = np.mean([c.confidence for c in contributions])
        coherence_score = coherence_data['coherence_score'] if coherence_data else 0.5
        consensus_reached = avg_confidence > 0.4 and coherence_score > 0.3
        
        total_time = time.time() - start_time
        
        # Crear respuesta colaborativa
        response = CollaborativeResponse(
            content=response_content,
            contributions=contributions,
            coherence_score=coherence_score,
            total_time=total_time,
            consensus_reached=consensus_reached,
            metadata={
                'intent': intent_data['intent'] if intent_data else 'unknown',
                'avg_confidence': float(avg_confidence),
                'nodes_involved': len(contributions)
            }
        )
        
        self.response_history.append(response)
        
        if self.on_consensus:
            self.on_consensus(response)
        
        return response
    
    def _generate_response(
        self,
        message: ChatMessage,
        intent_data: Optional[Dict],
        response_data: Optional[Dict],
        coherence_data: Optional[Dict]
    ) -> str:
        """Genera la respuesta final combinando contribuciones."""
        # Determinar intención
        intent = intent_data['intent'] if intent_data else 'unknown'
        
        # Seleccionar template base
        templates = self._response_templates.get(intent, self._response_templates['unknown'])
        
        # Usar estado del reservorio para seleccionar template
        if response_data:
            idx = int(abs(response_data['response_vector'][0]) * len(templates)) % len(templates)
        else:
            idx = 0
        
        base_response = templates[idx]
        
        # Añadir contenido contextual basado en coherencia
        if coherence_data and coherence_data.get('needs_clarification'):
            base_response += "¿Podrías darme más detalles? "
        
        # Personalizar según longitud sugerida
        if response_data:
            if response_data['suggested_length'] > 80:
                base_response += "Permíteme elaborar un poco más sobre esto."
            elif response_data['suggested_formality'] > 0.5:
                base_response = base_response.replace("!", ".")
        
        return base_response
    
    def get_node_states(self) -> Dict[str, Dict]:
        """Obtiene el estado actual de todos los nodos."""
        states = {}
        for role, node in self.nodes.items():
            states[role.value] = {
                'node_id': node.node_id,
                'state_norm': float(np.linalg.norm(node.state)),
                'history_length': len(node.history),
                'learned_patterns': len(node.learned_patterns),
                'is_trained': node.is_trained
            }
        return states
    
    def reset(self):
        """Resetea el estado de todos los nodos."""
        for node in self.nodes.values():
            node.reset_state()
        self.conversation_history.clear()
        self.response_history.clear()
    
    def get_conversation_summary(self) -> Dict:
        """Obtiene un resumen de la conversación actual."""
        if not self.conversation_history:
            return {'messages': 0, 'intents': {}, 'avg_coherence': 0}
        
        intents = {}
        for msg in self.conversation_history:
            if msg.intent:
                intent_name = msg.intent.value
                intents[intent_name] = intents.get(intent_name, 0) + 1
        
        avg_coherence = np.mean([r.coherence_score for r in self.response_history]) if self.response_history else 0
        
        return {
            'messages': len(self.conversation_history),
            'responses': len(self.response_history),
            'intents': intents,
            'avg_coherence': float(avg_coherence),
            'consensus_rate': sum(1 for r in self.response_history if r.consensus_reached) / max(len(self.response_history), 1)
        }


def create_collaborative_chat(
    n_reservoir: int = 50,
    include_sentiment: bool = False,
    include_context: bool = False,
    seed: Optional[int] = None
) -> CollaborativeChat:
    """
    Función de conveniencia para crear un sistema de chat colaborativo.
    
    Args:
        n_reservoir: Tamaño del reservorio para cada nodo
        include_sentiment: Si incluir nodo de análisis de sentimiento
        include_context: Si incluir nodo de gestión de contexto
        seed: Semilla para reproducibilidad
        
    Returns:
        Sistema CollaborativeChat configurado
    """
    rng = np.random.default_rng(seed)
    
    chat = CollaborativeChat(
        n_reservoir=n_reservoir,
        seed=int(rng.integers(0, 2**31))
    )
    
    if include_sentiment:
        chat.add_node(NodeRole.SENTIMENT, int(rng.integers(0, 2**31)))
    
    if include_context:
        chat.add_node(NodeRole.CONTEXT, int(rng.integers(0, 2**31)))
    
    return chat
