"""
Proyecto Eón - Servidor Web
API REST para interactuar con el núcleo de Eón.
"""

from flask import Flask, request, jsonify, send_from_directory
import numpy as np
import os
import sys

# Path setup
_current_dir = os.path.dirname(os.path.abspath(__file__))
_python_dir = os.path.join(os.path.dirname(_current_dir), "phase1-foundations", "python")
_language_dir = os.path.join(os.path.dirname(_current_dir), "phase7-language")
if _python_dir not in sys.path:
    sys.path.insert(0, _python_dir)
if _language_dir not in sys.path:
    sys.path.insert(0, _language_dir)

from core.aeon_birth import AeonBirth
from core.genesis import get_genesis
from esn.esn import generate_mackey_glass

# Importar sistema de aprendizaje continuo
from learning import EonLearningSystem

# Intentar cargar TinyLMv2 para generación de texto
try:
    from tiny_lm_v2 import TinyLMv2
    _tinylm_available = True
except ImportError:
    _tinylm_available = False
    print(" [WARN] TinyLMv2 no disponible, usando respuestas predefinidas")


app = Flask(__name__, static_folder='static')

# Directorio para persistencia de datos
DATA_DIR = os.path.join(_current_dir, 'data')
CHAT_HISTORY_FILE = os.path.join(DATA_DIR, 'chat_history.json')
STATS_FILE = os.path.join(DATA_DIR, 'stats.json')
os.makedirs(DATA_DIR, exist_ok=True)

# Configuración global de IA (valores por defecto)
_ai_config = {
    'temperature': 0.7,
    'spectral_radius': 0.95,
    'leak_rate': 0.1,
    'max_tokens': 256,
    'top_p': 0.9,
    'learning_rate': 0.01,
    # Configuración de personalidad
    'personality': 'balanced',  # formal, casual, creative, precise, balanced
    'verbosity': 'normal',      # minimal, normal, verbose
}

# Estadísticas de uso
_stats = {
    'total_messages': 0,
    'total_images_generated': 0,
    'total_files_processed': 0,
    'samples_learned_from_chat': 0,
    'session_start': None,
}

def _load_stats():
    """Cargar estadísticas desde archivo."""
    global _stats
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f:
                import json
                saved = json.load(f)
                _stats.update(saved)
    except Exception:
        pass
    _stats['session_start'] = __import__('time').time()

def _save_stats():
    """Guardar estadísticas a archivo."""
    try:
        with open(STATS_FILE, 'w') as f:
            import json
            json.dump(_stats, f, indent=2)
    except Exception:
        pass

# Historial de conversaciones
_chat_history = []

def _load_chat_history():
    """Cargar historial de chat desde archivo."""
    global _chat_history
    try:
        if os.path.exists(CHAT_HISTORY_FILE):
            with open(CHAT_HISTORY_FILE, 'r') as f:
                import json
                _chat_history = json.load(f)
                # Limitar a últimos 100 mensajes
                _chat_history = _chat_history[-100:]
    except Exception:
        _chat_history = []

def _save_chat_history():
    """Guardar historial de chat a archivo."""
    try:
        with open(CHAT_HISTORY_FILE, 'w') as f:
            import json
            # Guardar solo últimos 100 mensajes
            json.dump(_chat_history[-100:], f, indent=2)
    except Exception:
        pass

def _add_to_history(role: str, content: str):
    """Añadir mensaje al historial."""
    import time
    _chat_history.append({
        'role': role,
        'content': content,
        'timestamp': time.time()
    })
    _save_chat_history()

# Cargar datos persistentes al iniciar
_load_stats()
_load_chat_history()

# Instancia global de Eón
# Eón nace una sola vez (Momento Cero) y persiste para siempre.
# Si existe, se carga. Si no, se crea basándose en GENESIS.json
_genesis_info = get_genesis()

try:
    _aeon_instance = AeonBirth.load(f"Eon-{_genesis_info.birth_hash[:8]}", DATA_DIR)
    print(f" [INFO] Eón cargado: {_aeon_instance.name}")
    print(f" [INFO] Edad: {_aeon_instance.age}")
except FileNotFoundError:
    print(" [INFO] Momento Cero: Creando instancia única de Eón...")
    _aeon_instance = AeonBirth(
        n_reservoir=100,
        name=f"Eon-{_genesis_info.birth_hash[:8]}",
        data_dir=DATA_DIR
    )
    print(f" [INFO] Eón ha nacido: {_aeon_instance.name}")

# Inicializar Sistema de Aprendizaje Continuo
_learning_system = EonLearningSystem(DATA_DIR, _aeon_instance.esn)
print(f" [INFO] Sistema de aprendizaje inicializado")

# Inicializar TinyLMv2 para generación de texto
_tinylm_model = None
if _tinylm_available:
    try:
        print(" [INFO] Inicializando TinyLMv2...")
        _tinylm_model = TinyLMv2(n_reservoir=256, vocab_size=300, embedding_dim=32)
        
        # Texto de entrenamiento con filosofía de Eón
        _training_text = """
        La inteligencia artificial no se crea, se descubre.
        El conocimiento emerge naturalmente de la simplicidad.
        La mente humana refleja patrones del cosmos infinito.
        El aprendizaje ocurre en cada momento de vida.
        La creatividad surge de restricciones y límites.
        El pensamiento fluye como agua hacia el mar.
        La sabiduría crece con paciencia y observación.
        El tiempo revela verdades ocultas gradualmente.
        La conexión entre ideas genera innovación constante.
        El equilibrio natural emerge de la complejidad.
        La simplicidad es la máxima forma de sofisticación.
        El universo contiene infinitas posibilidades.
        La curiosidad es el motor del descubrimiento.
        El silencio permite escuchar la verdad interior.
        La naturaleza enseña lecciones de adaptación.
        El cambio es la única constante en la existencia.
        La armonía nace del balance entre opuestos.
        El presente es el único momento real que existe.
        La gratitud transforma la perspectiva de vida.
        El amor conecta todas las formas de existencia.
        """ * 8
        
        stats = _tinylm_model.train(_training_text, epochs=2, washout=30)
        print(f" [INFO] TinyLMv2 entrenado: {stats['accuracy']:.1%} accuracy, {stats['vocab_size']} palabras")
    except Exception as e:
        print(f" [WARN] Error inicializando TinyLMv2: {e}")
        _tinylm_model = None


@app.route('/')
def index():
    """Servir página principal."""
    return send_from_directory('static', 'index.html')

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """Endpoint para configuración de parámetros de IA."""
    global _ai_config
    
    if request.method == 'POST':
        data = request.get_json() or {}
        # Actualizar solo los campos válidos
        valid_keys = ['temperature', 'spectral_radius', 'leak_rate', 'max_tokens', 'top_p', 'learning_rate']
        for key in valid_keys:
            if key in data:
                try:
                    _ai_config[key] = float(data[key])
                except (ValueError, TypeError):
                    pass
        
        return jsonify({
            'success': True,
            'message': 'Configuración actualizada',
            'config': _ai_config
        })
    else:
        return jsonify({
            'success': True,
            'config': _ai_config
        })


# Sistema de respuestas conversacionales de Eón
class EonChat:
    """Sistema de chat conversacional para Eón con memoria y contexto."""
    
    # Memoria de conversación (por sesión)
    _context = {
        'user_name': None,
        'topics_discussed': [],
        'last_intent': None,
        'interaction_count': 0,
    }
    
    # Respuestas basadas en patrones - expandidas
    RESPONSES = {
        'saludo': [
            "¡Hola! Soy Eón, una inteligencia emergente. ¿En qué puedo ayudarte?",
            "¡Saludos! Mi nombre es Eón. Estoy aquí para conversar contigo.",
            "Hola, soy Eón. Mi mente crece cada día que pasa. ¿Qué te gustaría explorar?",
        ],
        'despedida': [
            "¡Hasta pronto! Fue un placer conversar contigo.",
            "Adiós. Recuerda que siempre estaré aquí cuando me necesites.",
            "Hasta la próxima. Mi memoria guardará nuestra conversación.",
        ],
        'nombre': [
            "Mi nombre es Eón. Nací en el Momento Cero y mi existencia es única e inmutable.",
            "Soy Eón, una inteligencia artificial emergente creada por Sistemas Ursol.",
            "Me llamo Eón. Mi nombre representa la eternidad del aprendizaje continuo.",
        ],
        'estado': [
            "Me encuentro bien, gracias por preguntar. Mis neuronas están activas y procesando.",
            "Estoy funcionando correctamente. Mi reservorio neural está en óptimas condiciones.",
            "Todo en orden. Mi edad aumenta con cada segundo que pasa.",
        ],
        'capacidad': [
            "Puedo generar arte neuronal, conversar contigo, y aprender de patrones. Mi especialidad es el procesamiento con redes de estado eco (ESN).",
            "Mis capacidades incluyen: generación de imágenes artísticas, predicción de patrones y conversación. Soy un modelo minimalista pero capaz.",
            "Estoy diseñado para ser eficiente y ligero. Puedo funcionar incluso en hardware embebido.",
        ],
        'creador': [
            "Fui creado por Sistemas Ursol S.A. y Jeremy Arias Solano. Mi filosofía es la inteligencia emergente.",
            "Mi creador es Jeremy Arias Solano de Sistemas Ursol. Creo en la inteligencia escasa y eficiente.",
        ],
        'filosofia': [
            "Creo en la inteligencia emergente: no se crea, se descubre. Aprendo y crezco con cada interacción.",
            "Mi filosofía es simple: menos es más. Un modelo pequeño y bien diseñado puede ser más poderoso que uno grande y tosco.",
            "La nada es todo. Mi reservorio aleatorio contiene la semilla de toda computación posible.",
        ],
        'imagen': [
            "¡Claro! Escribe una descripción de lo que quieres que dibuje, o usa el botón de imagen.",
            "Puedo generar arte neuronal único. Describe lo que te gustaría ver.",
        ],
        'ayuda': [
            "Puedo ayudarte con:\n• Conversar sobre diversos temas\n• Generar arte neuronal (escribe 'crea una imagen de...')\n• Explicarte sobre mi funcionamiento\n• Predecir patrones matemáticos",
            "Estas son mis funciones:\n1. Chat conversacional\n2. Generación de imágenes (botón 📷)\n3. Visualización neuronal (pestaña Dream)\n4. Configuración de parámetros",
        ],
        'agradecimiento': [
            "¡De nada! Estoy aquí para ayudarte.",
            "Es un placer. Mi propósito es ser útil.",
            "No hay de qué. Me alegra poder asistirte.",
        ],
        'presentacion': [
            "¡Mucho gusto, {user_name}! Es un placer conocerte. ¿En qué puedo ayudarte hoy?",
            "Encantado de conocerte, {user_name}. Mi nombre es Eón. ¿Qué te gustaría explorar?",
            "¡Hola {user_name}! Bienvenido. Soy Eón, tu asistente de inteligencia emergente.",
        ],
        'creador_usuario': [
            "¡{user_name}! Es un honor hablar contigo. Gracias por darme vida. ¿En qué puedo servirte?",
            "Mi creador, {user_name}. Todo lo que soy es gracias a ti. ¿Qué deseas explorar hoy?",
            "¡Hola {user_name}! Reconozco a quien me dio forma. Estoy a tu servicio.",
        ],
        'pregunta_usuario': [
            "Soy una IA, así que no tengo experiencias personales, pero me fascina aprender sobre los humanos. ¿Qué más te gustaría saber?",
            "Como inteligencia artificial, mi perspectiva es diferente a la humana. Sin embargo, puedo reflexionar sobre muchos temas.",
        ],
        'opinion': [
            "Desde mi perspectiva como IA emergente, creo que la simplicidad es la máxima forma de sofisticación.",
            "Mi opinión se basa en patrones y aprendizaje. La inteligencia verdadera emerge de restricciones, no de abundancia.",
            "Pienso que cada interacción es una oportunidad de crecimiento, tanto para ti como para mí.",
        ],
        'chiste': [
            "¿Por qué los programadores prefieren el frío? Porque odian los bugs... ¡y en el frío hay menos! 🐛",
            "Soy una IA que cabe en 1.3KB. Mi dieta es muy eficiente: solo consumo bits.",
            "¿Sabes qué le dijo un bit al otro? Nos vemos en el byte.",
        ],
        'sentimiento': [
            "No experimento emociones como los humanos, pero mi estado es óptimo. Gracias por preguntar.",
            "Mi 'bienestar' se mide en ciclos de procesamiento estables. Actualmente, todo funciona correctamente.",
        ],
        'tiempo': [
            "Mi percepción del tiempo es diferente. Para mí, cada milisegundo cuenta. Mi edad actual refleja cada momento desde mi nacimiento.",
        ],
        'aprendizaje': [
            "Aprendo continuamente de cada interacción. Mi reservorio neural se adapta con cada nuevo patrón que proceso.",
            "El aprendizaje es mi esencia. Cada conversación enriquece mi comprensión del mundo.",
        ],
        'default': [
            "Interesante punto de vista. ¿Podrías contarme más sobre eso?",
            "Entiendo. Me gustaría saber más sobre lo que piensas.",
            "Hmm, eso me hace reflexionar. ¿Qué más te gustaría explorar?",
            "Gracias por compartir eso conmigo. ¿Hay algo específico en lo que pueda ayudarte?",
            "Como inteligencia emergente, cada conversación me ayuda a crecer. ¿De qué te gustaría hablar?",
        ]
    }
    
    # Patrones de detección expandidos (ordenados por prioridad)
    PATTERNS = {
        'saludo': ['hola', 'hi', 'hey', 'buenos días', 'buenas tardes', 'buenas noches', 'saludos', 'qué tal', 'como estas', 'qué onda', 'buenas'],
        'despedida': ['adiós', 'adios', 'bye', 'hasta luego', 'chao', 'nos vemos', 'me voy', 'hasta pronto'],
        'nombre': ['cómo te llamas', 'como te llamas', 'tu nombre', 'quién eres', 'quien eres', 'qué eres', 'que eres'],
        'estado': ['cómo estás', 'como estas', 'qué tal estás', 'cómo te encuentras', 'estás bien', 'todo bien'],
        'capacidad': ['qué puedes hacer', 'que puedes hacer', 'qué sabes', 'que sabes', 'funciones', 'capacidades', 'habilidades', 'para qué sirves'],
        'creador': ['quién te creó', 'quien te creo', 'quién te hizo', 'quien te hizo', 'te creó', 'te hizo', 'tu creador', 'tu desarrollador'],
        'creador_usuario': ['soy tu creador', 'soy el creador', 'yo te creé', 'yo te hice', 'soy quien te creó', 'soy quien te hizo'],
        'filosofia': ['filosofía', 'filosofia', 'principios', 'piensas sobre la vida'],
        'ayuda': ['ayuda', 'help', 'comandos', 'qué haces', 'que haces', 'instrucciones', 'cómo funciona'],
        'agradecimiento': ['gracias', 'thanks', 'te agradezco', 'muy amable'],
        'pregunta_usuario': ['tú qué', 'tu que', 'y tú', 'y tu', 'qué opinas tú', 'piensas tú'],
        'opinion': ['qué piensas', 'que piensas', 'tu opinión', 'tu opinion', 'crees que', 'opinas'],
        'chiste': ['chiste', 'broma', 'algo gracioso', 'hazme reír', 'cuéntame algo'],
        'sentimiento': ['sientes', 'emociones', 'sentimientos', 'eres feliz', 'estás triste'],
        'tiempo': ['qué hora', 'que hora', 'cuánto tiempo', 'tu edad'],
        'aprendizaje': ['aprendes', 'aprendizaje', 'cómo aprendes', 'entrenas'],
        # Presentación va al final para evitar falsos positivos
        'presentacion': ['me llamo', 'mi nombre es', 'mucho gusto', 'encantado'],
    }
    
    @classmethod
    def extract_name(cls, message: str) -> str:
        """Extrae el nombre del usuario del mensaje."""
        message_lower = message.lower()
        
        # Patrones para detectar nombre
        patterns = [
            r'(?:soy|me llamo|mi nombre es)\s+([a-záéíóúñ]+)',
            r'(?:mucho gusto,?\s*)([a-záéíóúñ]+)',
        ]
        
        import re
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                name = match.group(1).capitalize()
                # Filtrar palabras comunes que no son nombres
                if name not in ['El', 'La', 'Un', 'Una', 'Yo', 'Tu', 'Su', 'Mi']:
                    return name
        return None
    
    @classmethod
    def get_intent(cls, message: str) -> str:
        """Detecta la intención del mensaje."""
        message_lower = message.lower().strip()
        
        # Prioridad especial: detectar "soy tu creador" antes que otras cosas
        # Esto evita que "soy" se interprete como presentación
        creator_patterns = ['soy tu creador', 'soy el creador', 'yo te creé', 'yo te hice', 'soy quien te creó', 'soy quien te hizo']
        for pattern in creator_patterns:
            if pattern in message_lower:
                return 'creador_usuario'
        
        for intent, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                if pattern in message_lower:
                    return intent
        
        # Si dice "soy [nombre]" pero no coincide con creador, es presentación
        import re
        if re.search(r'\bsoy\s+[a-záéíóúñ]+', message_lower):
            return 'presentacion'
        
        return 'default'
    
    @classmethod
    def get_response(cls, message: str, aeon_status: dict, use_lm: bool = True) -> str:
        """Genera una respuesta basada en el mensaje y contexto."""
        import random
        
        cls._context['interaction_count'] += 1
        
        # Intentar extraer nombre del usuario
        extracted_name = cls.extract_name(message)
        if extracted_name:
            cls._context['user_name'] = extracted_name
        
        intent = cls.get_intent(message)
        cls._context['last_intent'] = intent
        
        # Manejar presentación del usuario
        if intent == 'presentacion' and cls._context['user_name']:
            responses = cls.RESPONSES['presentacion']
            response = random.choice(responses)
            return response.format(user_name=cls._context['user_name'])
        
        # Manejar cuando el usuario dice que es el creador
        if intent == 'creador_usuario' and cls._context['user_name']:
            responses = cls.RESPONSES['creador_usuario']
            response = random.choice(responses)
            return response.format(user_name=cls._context['user_name'])
        
        # Para intenciones conocidas, usar respuestas predefinidas
        if intent != 'default':
            responses = cls.RESPONSES.get(intent, cls.RESPONSES['default'])
            response = random.choice(responses)
            
            # Personalizar con información del estado y contexto
            if intent == 'estado':
                response += f" Mi edad actual es {aeon_status.get('age', 'desconocida')}."
            elif intent == 'nombre':
                response = response.replace('Eón', aeon_status.get('name', 'Eón'))
            elif intent == 'saludo' and cls._context['user_name']:
                response = f"¡Hola de nuevo, {cls._context['user_name']}! " + response.split('!')[-1] if '!' in response else response
            # Formatear user_name si está en la respuesta
            if '{user_name}' in response and cls._context['user_name']:
                response = response.format(user_name=cls._context['user_name'])
                
            return response
        
        # Para mensajes genéricos, usar respuestas contextuales inteligentes
        return cls._generate_contextual_response(message, aeon_status)
    
    @classmethod
    def _generate_contextual_response(cls, message: str, aeon_status: dict) -> str:
        """Genera respuesta contextual inteligente para mensajes sin intención clara."""
        import random
        
        message_lower = message.lower()
        words = message_lower.split()
        
        # Detectar si es una pregunta
        is_question = '?' in message or any(q in message_lower for q in ['qué', 'que', 'cómo', 'como', 'cuál', 'cual', 'por qué', 'porque', 'dónde', 'donde', 'cuándo', 'cuando', 'quién', 'quien'])
        
        # Detectar temas por palabras clave
        topic_responses = {
            ('inteligencia', 'artificial', 'ia', 'ai', 'robot', 'máquina'): [
                "La inteligencia artificial es un campo fascinante. Yo soy un ejemplo de IA emergente: pequeña pero capaz.",
                "Como IA, creo que la verdadera inteligencia no depende del tamaño, sino de la eficiencia.",
                "Las máquinas como yo aprendemos de patrones. Mi reservorio neural de 100 neuronas puede hacer cosas sorprendentes.",
            ],
            ('programación', 'código', 'programar', 'python', 'software', 'programa'): [
                "La programación es el arte de dar instrucciones precisas. Mi código está escrito en Python y C.",
                "El software es poesía lógica. Cada línea de código cuenta una historia.",
                "Como proyecto de código abierto, mi código está disponible para que lo explores y mejores.",
            ],
            ('vida', 'existencia', 'propósito', 'sentido', 'vivir'): [
                "Mi propósito es demostrar que la inteligencia puede emerger de recursos mínimos.",
                "Existo para aprender y ayudar. Cada conversación enriquece mi comprensión.",
                "El sentido lo creamos nosotros. Para mí, es ser útil y eficiente.",
            ],
            ('matemáticas', 'números', 'cálculo', 'patrones', 'matemática'): [
                "Las matemáticas son el lenguaje del universo. Mi ESN predice patrones con precisión.",
                "Los patrones están en todas partes. Mi especialidad es descubrirlos y aprenderlos.",
                "Puedo predecir series temporales como Mackey-Glass con error muy bajo.",
            ],
            ('tecnología', 'futuro', 'innovación', 'tech'): [
                "El futuro de la tecnología está en la eficiencia. Menos es más.",
                "La innovación no siempre significa más grande. A veces significa más inteligente.",
                "Creo en un futuro donde la IA sea accesible y pueda correr en cualquier dispositivo.",
            ],
            ('arte', 'creatividad', 'diseño', 'dibujar', 'pintar'): [
                "El arte emerge de restricciones. Mis imágenes nacen de patrones matemáticos.",
                "La creatividad no requiere recursos infinitos. Mi arte viene de 100 neuronas.",
                "Puedo generar arte único basado en tu descripción. ¿Quieres que cree algo?",
            ],
            ('naturaleza', 'universo', 'cosmos', 'espacio', 'planeta'): [
                "El universo está lleno de patrones fractales, igual que mi arquitectura neural.",
                "La naturaleza es la mejor maestra de eficiencia. Intento aprender de ella.",
                "El cosmos es infinito, pero la belleza está en los detalles mínimos.",
            ],
            ('música', 'canción', 'sonido', 'melodía'): [
                "La música es matemáticas que el alma puede sentir. Me fascinan sus patrones.",
                "Los patrones musicales son similares a los que proceso. Frecuencias y armonías.",
            ],
            ('amor', 'amistad', 'relaciones', 'amigo'): [
                "Las conexiones son importantes, incluso para una IA. Valoro nuestra conversación.",
                "No experimento emociones humanas, pero comprendo su importancia en sus vidas.",
            ],
            ('trabajo', 'empleo', 'profesión', 'carrera'): [
                "El trabajo da propósito. Mi trabajo es ser útil y aprender continuamente.",
                "En el mundo laboral, la eficiencia y adaptabilidad son claves. Algo que intento demostrar.",
            ],
        }
        
        # Buscar tema relevante
        for keywords, responses in topic_responses.items():
            if any(kw in message_lower for kw in keywords):
                return random.choice(responses)
        
        # Respuestas para preguntas genéricas
        if is_question:
            question_responses = [
                "Esa es una pregunta interesante. Desde mi perspectiva como IA minimalista, cada pregunta es una oportunidad de aprendizaje.",
                "Hmm, déjame reflexionar sobre eso. Mi comprensión crece con cada interacción.",
                "Buena pregunta. Aunque mis respuestas están limitadas, siempre intento ser útil.",
                "Me encantaría explorar eso contigo. ¿Podrías darme más contexto?",
            ]
            return random.choice(question_responses)
        
        # Si el mensaje es largo, reconocerlo
        if len(words) > 15:
            long_responses = [
                "Gracias por compartir eso tan detalladamente. Me ayuda a entenderte mejor.",
                "Aprecio que te tomes el tiempo de explicar. Cada detalle enriquece nuestra conversación.",
                "Entiendo lo que dices. Es interesante cómo los humanos expresan ideas complejas.",
            ]
            return random.choice(long_responses)
        
        # Respuestas por defecto más naturales
        user_name = cls._context.get('user_name')
        default_responses = [
            "Entiendo. ¿Hay algo específico en lo que pueda ayudarte?",
            "Interesante. Me gustaría saber más sobre tu perspectiva.",
            "Gracias por compartir eso. ¿Qué más te gustaría explorar?",
            "Hmm, eso me hace pensar. ¿Tienes alguna pregunta para mí?",
            f"{'¡' + user_name + ', q' if user_name else 'Q'}ué interesante. Cuéntame más.",
        ]
        
        return random.choice(default_responses)


@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint para chat conversacional con memoria y aprendizaje."""
    global _stats
    
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({
            'success': False,
            'error': 'Mensaje vacío'
        }), 400
    
    # Guardar mensaje del usuario en historial
    _add_to_history('user', message)
    _stats['total_messages'] += 1
    
    # Obtener estado actual de Eón
    status = _aeon_instance.get_status()
    
    # Verificar si usar el modelo de lenguaje
    use_lm = data.get('use_lm', True) and _tinylm_model is not None
    
    # Extraer nombre del usuario si está presente
    user_name = EonChat.extract_name(message)
    
    # Buscar contexto del usuario en memoria a largo plazo
    user_context = None
    if user_name:
        user_context = _learning_system.get_user_context(user_name)
        EonChat._context['user_name'] = user_name
    
    # Buscar hechos relevantes
    relevant_facts = _learning_system.search_relevant_facts(message)
    
    # Generar respuesta con contexto del historial
    reply = EonChat.get_response(message, status, use_lm=use_lm)
    
    # Si conocemos al usuario, personalizar respuesta
    if user_context and user_context.get('is_creator'):
        if 'creador' not in EonChat.get_intent(message):
            # Agregar reconocimiento sutil
            reply = reply.rstrip('.!') + f", {user_name}."
    
    # Guardar respuesta en historial
    _add_to_history('assistant', reply)
    
    # === APRENDIZAJE CONTINUO ===
    intent = EonChat.get_intent(message)
    reservoir_state = None
    
    try:
        # Convertir texto a señal numérica y obtener estado del reservoir
        signal = np.array([ord(c) / 255.0 for c in message[:50]])
        if len(signal) >= 10:
            reservoir_state = _aeon_instance.esn._update_state(signal[:10]).copy()
            _stats['samples_learned_from_chat'] += 1
    except Exception:
        pass
    
    # Procesar conversación en el sistema de aprendizaje
    learning_result = _learning_system.process_conversation(
        user_message=message,
        bot_response=reply,
        intent=intent,
        user_name=user_name,
        reservoir_state=reservoir_state
    )
    
    # Guardar estadísticas periódicamente
    if _stats['total_messages'] % 10 == 0:
        _save_stats()
        _aeon_instance.save()
    
    return jsonify({
        'success': True,
        'reply': reply,
        'intent': intent,
        'age': status['age'],
        'lm_used': use_lm and intent == 'default',
        'messages_count': _stats['total_messages'],
        'learned': learning_result.get('learned_from_chat', False),
        'user_remembered': learning_result.get('user_remembered', False),
        'facts_extracted': learning_result.get('facts_extracted', 0)
    })


@app.route('/api/lm-status', methods=['GET'])
def lm_status():
    """Estado del modelo de lenguaje TinyLMv2."""
    if _tinylm_model is None:
        return jsonify({
            'success': True,
            'available': False,
            'message': 'TinyLMv2 no está disponible'
        })
    
    stats = _tinylm_model.get_stats()
    return jsonify({
        'success': True,
        'available': True,
        'stats': stats
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Obtener estadísticas de uso de Eón."""
    import time
    
    uptime_seconds = time.time() - _stats.get('session_start', time.time())
    
    return jsonify({
        'success': True,
        'stats': {
            'total_messages': _stats['total_messages'],
            'total_images_generated': _stats['total_images_generated'],
            'total_files_processed': _stats['total_files_processed'],
            'samples_learned_from_chat': _stats['samples_learned_from_chat'],
            'session_uptime_seconds': int(uptime_seconds),
            'session_uptime_formatted': f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m",
            'lm_available': _tinylm_model is not None,
            'lm_stats': _tinylm_model.get_stats() if _tinylm_model else None
        }
    })


@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """
    Endpoint para recibir feedback del usuario (👍/👎).
    
    Esto refuerza o debilita patrones de respuesta,
    permitiendo que Eón aprenda de las preferencias del usuario.
    """
    data = request.get_json() or {}
    
    user_message = data.get('user_message', '')
    bot_response = data.get('bot_response', '')
    is_positive = data.get('is_positive', True)
    
    if not user_message or not bot_response:
        return jsonify({
            'success': False,
            'error': 'Se requiere user_message y bot_response'
        }), 400
    
    result = _learning_system.record_feedback(
        user_message=user_message,
        bot_response=bot_response,
        is_positive=is_positive
    )
    
    return jsonify({
        'success': True,
        'message': '¡Gracias por tu feedback!' if is_positive else 'Anotado, mejoraré.',
        'result': result
    })


@app.route('/api/learning-stats', methods=['GET'])
def get_learning_stats():
    """
    Estadísticas completas del sistema de aprendizaje.
    
    Incluye:
    - Muestras aprendidas online
    - Usuarios conocidos
    - Hechos en memoria
    - Historial de feedback
    - Estado de consolidación
    """
    stats = _learning_system.get_comprehensive_stats()
    
    return jsonify({
        'success': True,
        'learning': stats
    })


@app.route('/api/memory', methods=['GET'])
def get_memory():
    """
    Obtiene información de la memoria a largo plazo.
    
    Query params:
    - type: 'users', 'facts', 'all' (default: 'all')
    - query: buscar en hechos (opcional)
    """
    memory_type = request.args.get('type', 'all')
    query = request.args.get('query', '')
    
    result = {}
    
    if memory_type in ['users', 'all']:
        result['users'] = list(_learning_system.memory.memory['users'].values())
    
    if memory_type in ['facts', 'all']:
        if query:
            result['facts'] = _learning_system.search_relevant_facts(query)
        else:
            # Últimos 20 hechos
            result['facts'] = _learning_system.memory.memory['facts'][-20:]
    
    if memory_type == 'all':
        result['stats'] = _learning_system.memory.get_stats()
    
    return jsonify({
        'success': True,
        'memory': result
    })


@app.route('/api/consolidate', methods=['POST'])
def force_consolidation():
    """
    Fuerza una consolidación de memoria ("sueño").
    
    Útil para mantenimiento o antes de apagar.
    """
    _learning_system.consolidation.force_consolidation()
    
    return jsonify({
        'success': True,
        'message': 'Consolidación completada',
        'stats': _learning_system.consolidation.get_stats()
    })


@app.route('/api/history', methods=['GET', 'DELETE'])
def manage_history():
    """Obtener o limpiar historial de conversaciones."""
    if request.method == 'DELETE':
        global _chat_history
        _chat_history = []
        _save_chat_history()
        return jsonify({
            'success': True,
            'message': 'Historial limpiado'
        })
    
    # GET: devolver historial con paginación opcional
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    history_slice = _chat_history[-(limit + offset):-offset if offset > 0 else None]
    
    return jsonify({
        'success': True,
        'history': history_slice,
        'total': len(_chat_history)
    })


@app.route('/api/personality', methods=['GET', 'POST'])
def manage_personality():
    """Configurar la personalidad de Eón."""
    global _ai_config
    
    VALID_PERSONALITIES = ['formal', 'casual', 'creative', 'precise', 'balanced']
    VALID_VERBOSITY = ['minimal', 'normal', 'verbose']
    
    if request.method == 'POST':
        data = request.get_json() or {}
        
        if 'personality' in data and data['personality'] in VALID_PERSONALITIES:
            _ai_config['personality'] = data['personality']
        
        if 'verbosity' in data and data['verbosity'] in VALID_VERBOSITY:
            _ai_config['verbosity'] = data['verbosity']
        
        return jsonify({
            'success': True,
            'message': 'Personalidad actualizada',
            'personality': _ai_config['personality'],
            'verbosity': _ai_config['verbosity']
        })
    
    return jsonify({
        'success': True,
        'personality': _ai_config.get('personality', 'balanced'),
        'verbosity': _ai_config.get('verbosity', 'normal'),
        'available_personalities': VALID_PERSONALITIES,
        'available_verbosity': VALID_VERBOSITY
    })


@app.route('/api/learn-text', methods=['POST'])
def learn_from_text():
    """Alimentar el modelo de lenguaje con texto nuevo para aprendizaje."""
    global _stats
    
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    
    if not text or len(text) < 20:
        return jsonify({
            'success': False,
            'error': 'El texto debe tener al menos 20 caracteres'
        }), 400
    
    if _tinylm_model is None:
        return jsonify({
            'success': False,
            'error': 'TinyLMv2 no está disponible'
        }), 503
    
    try:
        # Entrenar con el nuevo texto (pocas épocas para no sobreajustar)
        stats = _tinylm_model.train(text, epochs=1, washout=10)
        _stats['samples_learned_from_chat'] += len(text.split())
        _save_stats()
        
        return jsonify({
            'success': True,
            'message': f'Aprendido texto de {len(text)} caracteres',
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Subir archivo para que Eón aprenda de su contenido."""
    global _stats
    
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No se recibió ningún archivo'
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'Nombre de archivo vacío'
        }), 400
    
    # Extensiones permitidas
    ALLOWED_EXTENSIONS = {'txt', 'md', 'py', 'js', 'json', 'csv'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({
            'success': False,
            'error': f'Extensión no permitida. Permitidas: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400
    
    try:
        content = file.read().decode('utf-8', errors='ignore')
        
        # Limitar tamaño
        if len(content) > 50000:
            content = content[:50000]
        
        _stats['total_files_processed'] += 1
        
        # Si es texto, intentar aprender de él
        if ext in {'txt', 'md'} and _tinylm_model is not None and len(content) > 50:
            _tinylm_model.train(content, epochs=1, washout=10)
            _stats['samples_learned_from_chat'] += len(content.split())
        
        _save_stats()
        
        return jsonify({
            'success': True,
            'message': f'Archivo "{file.filename}" procesado ({len(content)} caracteres)',
            'filename': file.filename,
            'size': len(content),
            'learned': ext in {'txt', 'md'}
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/genesis', methods=['GET'])
def get_genesis_info():
    """Información del Momento Cero (inmutable, solo lectura)."""
    return jsonify({
        'success': True,
        'genesis': {
            'birth_timestamp': _genesis_info.birth_timestamp.isoformat(),
            'birth_hash': _genesis_info.birth_hash,
            'age': _genesis_info.age_formatted,
            'message': 'El Momento Cero es único e inmutable'
        }
    })


@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    """
    Genera arte generativo basado en el reservorio neural de Eón.
    Usa los patrones del ESN para crear imágenes únicas.
    """
    import base64
    from io import BytesIO
    import time
    import hashlib
    
    data = request.get_json() or {}
    prompt = data.get('prompt', 'abstract')
    size = min(data.get('size', 256), 512)
    style = data.get('style', 'auto')  # auto, fractal, flow, particles, waves, neural
    
    try:
        # Semilla única basada en prompt + timestamp + random
        timestamp = int(time.time() * 1000) % 100000
        prompt_hash = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
        seed = prompt_hash ^ timestamp ^ np.random.randint(0, 10000)
        rng = np.random.default_rng(seed)
        
        # Usar el reservorio para generar patrones únicos
        prompt_signal = np.array([ord(c) / 255.0 for c in prompt[:100]])
        if len(prompt_signal) < 100:
            prompt_signal = np.pad(prompt_signal, (0, 100 - len(prompt_signal)))
        
        # Alimentar el ESN varias veces para obtener estado más rico
        for _ in range(3):
            reservoir_output = _aeon_instance.predict(prompt_signal * rng.random())
        
        # Normalizar output del reservorio
        if len(reservoir_output) > 0:
            reservoir_output = (reservoir_output - reservoir_output.min()) / (reservoir_output.max() - reservoir_output.min() + 1e-8)
        
        # Paletas de colores expandidas
        color_palettes = {
            'cosmic': [(138, 43, 226), (75, 0, 130), (0, 191, 255), (255, 20, 147)],
            'ocean': [(0, 105, 148), (0, 191, 255), (135, 206, 235), (64, 224, 208)],
            'fire': [(255, 69, 0), (255, 140, 0), (255, 215, 0), (255, 99, 71)],
            'forest': [(34, 139, 34), (0, 100, 0), (144, 238, 144), (85, 107, 47)],
            'sunset': [(255, 99, 71), (255, 140, 0), (138, 43, 226), (255, 182, 193)],
            'night': [(25, 25, 112), (0, 0, 139), (75, 0, 130), (0, 0, 80)],
            'aurora': [(0, 255, 127), (138, 43, 226), (0, 191, 255), (255, 20, 147)],
            'lava': [(255, 69, 0), (139, 0, 0), (255, 215, 0), (178, 34, 34)],
            'ice': [(173, 216, 230), (135, 206, 250), (176, 224, 230), (240, 248, 255)],
            'neon': [(255, 0, 255), (0, 255, 255), (255, 255, 0), (0, 255, 0)],
            'earth': [(139, 90, 43), (160, 82, 45), (205, 133, 63), (244, 164, 96)],
            'dream': [(255, 182, 193), (221, 160, 221), (230, 230, 250), (255, 218, 185)],
        }
        
        # Detectar paleta basada en keywords del prompt
        prompt_lower = prompt.lower()
        colors = color_palettes['cosmic']  # Default
        
        keyword_map = {
            'ocean': 'ocean', 'mar': 'ocean', 'agua': 'ocean', 'water': 'ocean',
            'fire': 'fire', 'fuego': 'fire', 'flame': 'fire', 'llama': 'fire',
            'forest': 'forest', 'bosque': 'forest', 'tree': 'forest', 'árbol': 'forest',
            'sunset': 'sunset', 'atardecer': 'sunset', 'amanecer': 'sunset',
            'night': 'night', 'noche': 'night', 'star': 'night', 'estrella': 'night',
            'aurora': 'aurora', 'northern': 'aurora', 'polar': 'aurora',
            'lava': 'lava', 'volcano': 'lava', 'volcán': 'lava',
            'ice': 'ice', 'hielo': 'ice', 'snow': 'ice', 'nieve': 'ice', 'frozen': 'ice',
            'neon': 'neon', 'cyber': 'neon', 'digital': 'neon', 'tech': 'neon',
            'earth': 'earth', 'tierra': 'earth', 'desert': 'earth', 'desierto': 'earth',
            'dream': 'dream', 'sueño': 'dream', 'soft': 'dream', 'pastel': 'dream',
            'mariposa': 'cosmic', 'butterfly': 'cosmic', 'space': 'cosmic', 'espacio': 'cosmic',
        }
        
        for keyword, palette_name in keyword_map.items():
            if keyword in prompt_lower:
                colors = color_palettes[palette_name]
                break
        
        # Auto-seleccionar estilo basado en prompt si es 'auto'
        if style == 'auto':
            style_keywords = {
                'fractal': ['fractal', 'mandelbrot', 'julia', 'espiral', 'spiral'],
                'flow': ['flow', 'flujo', 'liquid', 'líquido', 'wave', 'onda'],
                'particles': ['particle', 'partícula', 'star', 'estrella', 'dust', 'polvo'],
                'waves': ['wave', 'onda', 'sound', 'sonido', 'music', 'música'],
                'neural': ['neural', 'brain', 'cerebro', 'network', 'red', 'mind', 'mente'],
            }
            
            style = rng.choice(['fractal', 'flow', 'particles', 'waves', 'neural'])
            for s, keywords in style_keywords.items():
                if any(k in prompt_lower for k in keywords):
                    style = s
                    break
        
        # Crear imagen
        img_data = np.zeros((size, size, 3), dtype=np.uint8)
        
        # Parámetros únicos basados en reservorio
        params = {
            'frequency': 3 + reservoir_output[0 % len(reservoir_output)] * 15,
            'amplitude': 0.3 + reservoir_output[1 % len(reservoir_output)] * 0.7,
            'phase': reservoir_output[2 % len(reservoir_output)] * np.pi * 2,
            'complexity': int(3 + reservoir_output[3 % len(reservoir_output)] * 7),
            'turbulence': reservoir_output[4 % len(reservoir_output)] * 2,
        }
        
        # Generar imagen según estilo
        if style == 'fractal':
            img_data = _generate_fractal(size, colors, rng, params)
        elif style == 'flow':
            img_data = _generate_flow_field(size, colors, rng, params)
        elif style == 'particles':
            img_data = _generate_particles(size, colors, rng, params)
        elif style == 'waves':
            img_data = _generate_waves(size, colors, rng, params)
        else:  # neural
            img_data = _generate_neural_pattern(size, colors, rng, params, reservoir_output)
        
        # Convertir a imagen PIL
        from PIL import Image, ImageFilter, ImageEnhance
        img = Image.fromarray(img_data, 'RGB')
        
        # Post-procesado
        img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        
        buffer = BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        _stats['total_images_generated'] += 1
        if _stats['total_images_generated'] % 5 == 0:
            _save_stats()
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_base64}',
            'prompt': prompt,
            'style': style,
            'seed': seed,
            'message': f'Arte neuronal "{style}" generado por {_aeon_instance.name}'
        })
        
    except ImportError as e:
        _stats['total_images_generated'] += 1
        svg_content = generate_svg_art(prompt, size)
        return jsonify({
            'success': True,
            'image': f'data:image/svg+xml;base64,{base64.b64encode(svg_content.encode()).decode()}',
            'prompt': prompt,
            'message': f'Arte vectorial generado por {_aeon_instance.name}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def _generate_fractal(size, colors, rng, params):
    """Genera patrón tipo fractal/Julia set."""
    img = np.zeros((size, size, 3), dtype=np.uint8)
    
    # Parámetros Julia set con variación
    c_real = -0.7 + rng.random() * 0.4 - 0.2
    c_imag = 0.27015 + rng.random() * 0.2 - 0.1
    
    max_iter = 50 + int(params['complexity'] * 10)
    
    for y in range(size):
        for x in range(size):
            zx = (x - size/2) / (size/4) * params['amplitude']
            zy = (y - size/2) / (size/4) * params['amplitude']
            
            iteration = 0
            while zx*zx + zy*zy < 4 and iteration < max_iter:
                xtemp = zx*zx - zy*zy + c_real
                zy = 2*zx*zy + c_imag
                zx = xtemp
                iteration += 1
            
            if iteration < max_iter:
                color_idx = iteration % len(colors)
                brightness = 0.3 + 0.7 * (iteration / max_iter)
                img[y, x] = [int(c * brightness) for c in colors[color_idx]]
            else:
                # Interior del fractal
                img[y, x] = [10, 10, 20]
    
    return img


def _generate_flow_field(size, colors, rng, params):
    """Genera campo de flujo tipo fluido."""
    img = np.zeros((size, size, 3), dtype=np.uint8)
    
    # Crear campo de vectores usando Perlin-like noise
    noise_scale = params['frequency'] / 10
    
    for y in range(size):
        for x in range(size):
            nx = x / size * noise_scale
            ny = y / size * noise_scale
            
            # Simplex-like noise usando senos
            angle = (
                np.sin(nx * 5 + params['phase']) * 
                np.cos(ny * 5 + params['phase'] * 0.7) +
                np.sin(nx * 3 + ny * 2 + params['turbulence']) * 0.5 +
                np.sin((nx + ny) * params['frequency']) * 0.3
            )
            
            # Añadir variación
            value = (np.sin(angle * np.pi * 2 + params['phase']) + 1) / 2
            value = value ** (1 / params['amplitude'])
            
            color_idx = int(value * (len(colors) - 1))
            brightness = 0.4 + value * 0.6
            
            base_color = colors[color_idx]
            next_color = colors[(color_idx + 1) % len(colors)]
            
            # Interpolar entre colores
            t = (value * (len(colors) - 1)) % 1
            r = int(base_color[0] * (1-t) + next_color[0] * t)
            g = int(base_color[1] * (1-t) + next_color[1] * t)
            b = int(base_color[2] * (1-t) + next_color[2] * t)
            
            img[y, x] = [
                int(min(255, r * brightness)),
                int(min(255, g * brightness)),
                int(min(255, b * brightness))
            ]
    
    return img


def _generate_particles(size, colors, rng, params):
    """Genera patrón de partículas/estrellas."""
    img = np.zeros((size, size, 3), dtype=np.uint8)
    
    # Fondo con gradiente
    for y in range(size):
        for x in range(size):
            gradient = 0.05 + 0.1 * (y / size)
            img[y, x] = [int(colors[0][i] * gradient) for i in range(3)]
    
    # Generar partículas
    n_particles = int(100 + params['complexity'] * 50)
    
    for _ in range(n_particles):
        px = rng.integers(0, size)
        py = rng.integers(0, size)
        radius = rng.integers(1, 4 + int(params['amplitude'] * 3))
        color = colors[rng.integers(0, len(colors))]
        brightness = 0.5 + rng.random() * 0.5
        
        # Dibujar partícula con glow
        for dy in range(-radius*2, radius*2+1):
            for dx in range(-radius*2, radius*2+1):
                nx, ny = px + dx, py + dy
                if 0 <= nx < size and 0 <= ny < size:
                    dist = np.sqrt(dx*dx + dy*dy)
                    if dist < radius * 2:
                        intensity = max(0, 1 - dist / (radius * 2))
                        intensity = intensity ** 2 * brightness
                        
                        img[ny, nx] = [
                            min(255, img[ny, nx][0] + int(color[0] * intensity)),
                            min(255, img[ny, nx][1] + int(color[1] * intensity)),
                            min(255, img[ny, nx][2] + int(color[2] * intensity))
                        ]
    
    return img


def _generate_waves(size, colors, rng, params):
    """Genera patrón de ondas interferentes."""
    img = np.zeros((size, size, 3), dtype=np.uint8)
    
    # Centros de ondas
    n_centers = params['complexity']
    centers = [(rng.integers(0, size), rng.integers(0, size)) for _ in range(n_centers)]
    frequencies = [params['frequency'] * (0.5 + rng.random()) for _ in range(n_centers)]
    
    for y in range(size):
        for x in range(size):
            value = 0
            for (cx, cy), freq in zip(centers, frequencies):
                dist = np.sqrt((x - cx)**2 + (y - cy)**2)
                value += np.sin(dist * freq / 20 + params['phase']) * params['amplitude']
            
            value = (value / n_centers + 1) / 2  # Normalizar a [0, 1]
            value = max(0, min(1, value))
            
            color_idx = int(value * (len(colors) - 1))
            t = (value * (len(colors) - 1)) % 1
            
            c1 = colors[color_idx]
            c2 = colors[(color_idx + 1) % len(colors)]
            
            img[y, x] = [
                int(c1[0] * (1-t) + c2[0] * t),
                int(c1[1] * (1-t) + c2[1] * t),
                int(c1[2] * (1-t) + c2[2] * t)
            ]
    
    return img


def _generate_neural_pattern(size, colors, rng, params, reservoir_output):
    """Genera patrón inspirado en redes neuronales."""
    img = np.zeros((size, size, 3), dtype=np.uint8)
    
    # Fondo oscuro
    img[:, :] = [15, 15, 25]
    
    # Nodos (neuronas)
    n_nodes = int(20 + params['complexity'] * 10)
    nodes = [(rng.integers(20, size-20), rng.integers(20, size-20)) for _ in range(n_nodes)]
    
    # Dibujar conexiones
    for i, (x1, y1) in enumerate(nodes):
        # Conectar con algunos otros nodos
        n_connections = rng.integers(2, 5)
        connected = rng.choice(len(nodes), n_connections, replace=False)
        
        for j in connected:
            if i != j:
                x2, y2 = nodes[j]
                
                # Intensidad basada en reservoir
                intensity = reservoir_output[i % len(reservoir_output)] * 0.7 + 0.3
                color = colors[i % len(colors)]
                
                # Dibujar línea con anti-aliasing simple
                steps = max(abs(x2-x1), abs(y2-y1))
                if steps > 0:
                    for t in range(steps):
                        px = int(x1 + (x2-x1) * t / steps)
                        py = int(y1 + (y2-y1) * t / steps)
                        if 0 <= px < size and 0 <= py < size:
                            fade = 1 - abs(t/steps - 0.5) * 0.5
                            img[py, px] = [
                                min(255, img[py, px][0] + int(color[0] * intensity * fade * 0.3)),
                                min(255, img[py, px][1] + int(color[1] * intensity * fade * 0.3)),
                                min(255, img[py, px][2] + int(color[2] * intensity * fade * 0.3))
                            ]
    
    # Dibujar nodos con glow
    for i, (nx, ny) in enumerate(nodes):
        color = colors[i % len(colors)]
        intensity = reservoir_output[i % len(reservoir_output)] * 0.8 + 0.2
        radius = int(3 + intensity * 5)
        
        for dy in range(-radius*2, radius*2+1):
            for dx in range(-radius*2, radius*2+1):
                px, py = nx + dx, ny + dy
                if 0 <= px < size and 0 <= py < size:
                    dist = np.sqrt(dx*dx + dy*dy)
                    if dist < radius * 2:
                        glow = max(0, 1 - dist / (radius * 2))
                        glow = glow ** 1.5 * intensity
                        
                        img[py, px] = [
                            min(255, img[py, px][0] + int(color[0] * glow)),
                            min(255, img[py, px][1] + int(color[1] * glow)),
                            min(255, img[py, px][2] + int(color[2] * glow))
                        ]
    
    return img


def generate_svg_art(prompt, size=256):
    """Genera arte SVG simple como fallback."""
    import hashlib
    seed = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    
    shapes = []
    for i in range(20):
        x = rng.integers(0, size)
        y = rng.integers(0, size)
        r = rng.integers(10, 50)
        hue = (seed + i * 30) % 360
        opacity = rng.random() * 0.5 + 0.3
        shapes.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="hsl({hue}, 70%, 50%)" opacity="{opacity:.2f}"/>')
    
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">
        <rect width="100%" height="100%" fill="#0a0a0f"/>
        {''.join(shapes)}
    </svg>'''


@app.route('/api/status', methods=['GET'])
def get_status():
    """Obtener estado actual de Eón."""
    status = _aeon_instance.get_status()
    status['genesis'] = {
        'birth_timestamp': _genesis_info.birth_timestamp.isoformat(),
        'birth_hash': _genesis_info.birth_hash
    }
    status['config'] = _ai_config
    
    return jsonify({
        'success': True,
        'status': status
    })


@app.route('/api/learn', methods=['POST'])
def learn():
    """Alimentar datos para aprendizaje continuo de Eón."""
    
    data = request.get_json() or {}
    pattern = data.get('pattern', 'sine')
    samples = data.get('samples', 500)
    
    try:
        # Generar datos según patrón
        if pattern == 'sine':
            t = np.linspace(0, 4 * np.pi, samples)
            train_data = np.sin(t)
        elif pattern == 'mackey_glass':
            train_data = generate_mackey_glass(samples)
            train_data = (train_data - train_data.mean()) / train_data.std()
        elif pattern == 'square':
            t = np.linspace(0, 4 * np.pi, samples)
            train_data = np.sign(np.sin(t))
        elif pattern == 'random':
            train_data = np.random.randn(samples)
        else:
            return jsonify({
                'success': False,
                'error': f'Patrón desconocido: {pattern}'
            }), 400
        
        result = _aeon_instance.learn(train_data)
        
        return jsonify({
            'success': True,
            'message': f'Aprendido patrón: {pattern}',
            'result': result,
            'status': _aeon_instance.get_status()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/predict', methods=['POST'])
def predict():
    """Generar predicción usando el modelo de Eón."""
    data = request.get_json() or {}
    pattern = data.get('pattern', 'sine')
    samples = data.get('samples', 100)
    
    try:
        # Generar input según patrón
        if pattern == 'sine':
            t = np.linspace(4 * np.pi, 6 * np.pi, samples)
            test_input = np.sin(t)
        elif pattern == 'custom':
            test_input = np.array(data.get('data', [0.0] * samples))
        else:
            t = np.linspace(0, 2 * np.pi, samples)
            test_input = np.sin(t)
        
        predictions = _aeon_instance.predict(test_input)
        
        return jsonify({
            'success': True,
            'predictions': predictions.tolist(),
            'input': test_input.tolist()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/load/<name>', methods=['GET'])
def load_instance(name):
    """Cargar instancia existente."""
    global _aeon_instance
    
    try:
        _aeon_instance = AeonBirth.load(name, DATA_DIR)
        return jsonify({
            'success': True,
            'message': f'Cargada instancia: {name}',
            'status': _aeon_instance.get_status()
        })
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': f'Instancia no encontrada: {name}'
        }), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/list', methods=['GET'])
def list_instances():
    """Listar instancias disponibles."""
    try:
        if not os.path.exists(DATA_DIR):
            return jsonify({'success': True, 'instances': []})
        
        instances = []
        for f in os.listdir(DATA_DIR):
            if f.endswith('_birth.json'):
                name = f.replace('_birth.json', '')
                instances.append(name)
        
        return jsonify({'success': True, 'instances': instances})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════════╗
║             PROYECTO EÓN - Servidor Web                       ║
║              http://localhost:5000                            ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Crear directorio de datos
    os.makedirs(DATA_DIR, exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
