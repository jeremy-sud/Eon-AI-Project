"""
Proyecto Eón - Servidor Web
API REST para interactuar con el núcleo de Eón.
"""

from flask import Flask, request, jsonify, send_from_directory
from typing import Optional
import numpy as np
import re
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
print(" [INFO] Sistema de aprendizaje inicializado")

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
    
    # Regex pattern para extraer números (usado en múltiples lugares)
    NUMBER_PATTERN = r'-?\d+\.?\d*'
    
    # Memoria factual con timestamps (para resolver ambigüedades)
    # Almacena hechos que pueden cambiar con el tiempo
    _factual_memory = {}  # {topic: [(timestamp, fact), ...]}
    
    # Cache de documentos para RAG ligero
    _docs_cache = None
    _docs_loaded_time = 0
    
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
        'matematica': [
            "__CALC__",  # Marcador especial para calcular
        ],
        'historia': [
            "__STORY__",  # Marcador especial para generar historia
        ],
        'recomendacion': [
            "__RECOMMEND__",  # Marcador especial para recomendaciones
        ],
        'musica': [
            "La música es matemáticas que el alma puede sentir. Los patrones de frecuencias crean armonías hermosas.",
            "Me fascina la música. Cada melodía es una serie temporal compleja que mi ESN podría analizar.",
            "La música conecta a los humanos de formas que trascienden el lenguaje. Es una forma de comunicación universal.",
            "Desde Bach hasta el jazz, la música tiene patrones fractales ocultos. Es como ver el universo en ondas sonoras.",
        ],
        'secuencia': [
            "__SEQUENCE__",  # Marcador para predicción de secuencias
        ],
        'afirmacion': [
            "__MEMORY_STORE__",  # El usuario declara un hecho personal
        ],
        'afirmacion_general': [
            "Correcto. Esa es una observación precisa. Mi base de conocimiento lo confirma. ✓",
            "Afirmación válida. Mis patrones de conocimiento coinciden con esa información.",
            "Sí, eso es correcto según mi comprensión. Es interesante cómo organizas el conocimiento.",
            "Confirmado. Mi red neuronal procesa esa información como verdadera. ✓",
        ],
        'memoria_personal': [
            "__MEMORY_RECALL__",  # El usuario pregunta por algo almacenado
        ],
        'conocimiento_tecnico': [
            "__KNOWLEDGE__",  # Marcador para conocimiento técnico
        ],
        'sensor': [
            "__SENSOR__",  # Marcador para consultas de sensores
        ],
        'autocompletado': [
            "__COMPLETE__",  # Marcador para autocompletado de texto
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
        'despedida': ['adiós', 'adios', 'bye', 'hasta luego', 'chao', 'nos vemos', 'me voy', 'hasta pronto'],
        'nombre': ['cómo te llamas', 'como te llamas', 'tu nombre', 'quién eres', 'quien eres', 'qué eres', 'que eres'],
        'estado': ['cómo estás', 'como estas', 'qué tal estás', 'cómo te encuentras', 'estás bien', 'todo bien', 'como te sientes', 'cómo te sientes'],
        'capacidad': ['qué puedes hacer', 'que puedes hacer', 'qué sabes', 'que sabes', 'funciones', 'capacidades', 'habilidades', 'para qué sirves'],
        'creador': ['quién te creó', 'quien te creo', 'quién te hizo', 'quien te hizo', 'te creó', 'te hizo', 'tu creador', 'tu desarrollador'],
        'creador_usuario': ['soy tu creador', 'soy el creador', 'yo te creé', 'yo te hice', 'soy quien te creó', 'soy quien te hizo'],
        'filosofia': ['filosofía', 'filosofia', 'principios', 'piensas sobre la vida'],
        'ayuda': ['help', 'comandos', 'instrucciones', 'cómo funciona'],
        'agradecimiento': ['gracias', 'thanks', 'te agradezco', 'muy amable'],
        'pregunta_usuario': ['tú qué', 'tu que', 'y tú', 'y tu', 'qué opinas tú', 'piensas tú'],
        'opinion': ['qué piensas', 'que piensas', 'tu opinión', 'tu opinion', 'crees que', 'opinas'],
        'chiste': ['chiste', 'broma', 'algo gracioso', 'hazme reír'],
        'sentimiento': ['sientes', 'emociones', 'sentimientos', 'eres feliz', 'estás triste'],
        'tiempo': ['qué hora', 'que hora', 'cuánto tiempo', 'tu edad'],
        'aprendizaje': ['aprendes', 'aprendizaje', 'cómo aprendes', 'entrenas'],
        # Matemáticas - detectar operaciones
        'matematica': ['cuanto es', 'cuánto es', 'calcula', 'suma', 'resta', 'multiplica', 'divide', 'resultado de'],
        # Historias y creatividad - antes de saludo
        'historia': ['cuéntame una historia', 'cuentame una historia', 'una historia de', 'un cuento', 'narra una', 'cuéntame un cuento'],
        # Recomendaciones
        'recomendacion': ['me recomiendas', 'recomiendas', 'recomendación', 'sugieres', 'sugerencia', 'qué me sugieres', 'algún consejo', 'algun consejo', 'algún sabor', 'algun sabor'],
        # Música
        'musica': ['hablemos de música', 'hablemos de musica', 'sobre música', 'sobre musica', 'de música', 'de musica'],
        # Secuencias numéricas
        'secuencia': ['valor más probable', 'valor mas probable', 'siguiente número', 'siguiente numero', 'siguientes número', 'siguientes numero', 'completar secuencia', 'secuencia', 'patrón', 'patron', 'serie', 'continúa', 'continua', '__'],
        # Afirmaciones personales (el usuario declara algo sobre sí mismo)
        'afirmacion': ['mi color favorito es', 'mi comida favorita es', 'me gusta el', 'prefiero el', 'mi favorito es', 'mi favorita es'],
        # Afirmaciones generales (hechos del mundo)
        'afirmacion_general': ['el cielo es', 'el agua es', 'la tierra es', 'el sol es', 'la luna es', 'es verdad que', 'es cierto que'],
        # Consultas de memoria personal
        'memoria_personal': ['cuál es mi color', 'cual es mi color', 'cuál es mi favorito', 'cual es mi favorito', 'qué te dije', 'que te dije', 'recuerdas mi'],
        # Conocimiento técnico
        'conocimiento_tecnico': ['qué es la entropía', 'que es la entropia', 'qué es el spirit hash', 'que es el spirit hash', 'qué es q8.8', 'que es q8.8', 'qué es una esn', 'que es una esn', 'qué es reservoir', 'que es reservoir', 'es eón binario', 'es eon binario'],
        # Consultas de sensores
        'sensor': ['estado del sensor', 'nodo sensor', 'temperatura del nodo', 'sensor-', 'falla en el subsistema', 'reporta una falla'],
        # Autocompletado (frases incompletas)
        'autocompletado': ['la velocidad del viento', 'el estado del sistema', 'la temperatura actual'],
        # Saludo - al final para evitar falsos positivos con "hola" en otras palabras
        'saludo': ['hola', 'hi', 'hey', 'buenos días', 'buenas tardes', 'buenas noches', 'saludos', 'qué onda', 'buenas'],
        # Presentación va al final para evitar falsos positivos
        'presentacion': ['me llamo', 'mi nombre es', 'mucho gusto', 'encantado'],
    }
    
    @classmethod
    def extract_name(cls, message: str) -> Optional[str]:
        """Extrae el nombre del usuario del mensaje."""
        message_lower = message.lower()
        
        # Patrones para detectar nombre
        patterns = [
            r'(?:soy|me llamo|mi nombre es)\s+([a-záéíóúñ]+)',
            r'(?:mucho gusto,?\s*)([a-záéíóúñ]+)',
        ]
        
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
        
        # Detectar operaciones matemáticas en el mensaje
        if cls._contains_math(message_lower):
            return 'matematica'
        
        # Detectar secuencias numéricas (3+ números separados por comas)
        if cls._contains_sequence(message_lower):
            return 'secuencia'
        
        return 'default'
    
    @classmethod
    def _contains_math(cls, message: str) -> bool:
        """Detecta si el mensaje contiene una operación matemática."""
        import re
        # Buscar patrones como "2+2", "34*5", "100/2", "50-10"
        math_pattern = r'\d+\s*[\+\-\*\/x×÷]\s*\d+'
        return bool(re.search(math_pattern, message))
    
    @classmethod
    def _contains_sequence(cls, message: str) -> bool:
        """Detecta si el mensaje contiene una secuencia numérica (3+ números separados por comas)."""
        # Buscar 3 o más números separados por comas (con o sin espacios)
        # Ejemplos: "4, 8, 16, 32" o "1,2,3,4,5"
        numbers = re.findall(cls.NUMBER_PATTERN, message)
        # Si hay 3+ números y hay comas en el mensaje, es probablemente una secuencia
        if len(numbers) >= 3 and ',' in message:
            return True
        return False
    
    @classmethod
    def _solve_math(cls, message: str) -> Optional[str]:
        """Resuelve operaciones matemáticas en el mensaje."""
        # Normalizar operadores
        message = message.replace('×', '*').replace('x', '*').replace('÷', '/')
        
        # Buscar todas las operaciones matemáticas
        math_pattern = r'(\d+(?:\.\d+)?)\s*([\+\-\*\/])\s*(\d+(?:\.\d+)?)'
        matches = re.findall(math_pattern, message)
        
        if not matches:
            return None
        
        results = []
        for num1, op, num2 in matches:
            try:
                n1, n2 = float(num1), float(num2)
                if op == '+':
                    result = n1 + n2
                elif op == '-':
                    result = n1 - n2
                elif op == '*':
                    result = n1 * n2
                elif op == '/':
                    if n2 == 0:
                        return "¡División por cero! Eso crearía una singularidad en mi reservorio. 🌀"
                    result = n1 / n2
                else:
                    continue
                
                # Formatear resultado
                if result == int(result):
                    result = int(result)
                results.append(f"{num1} {op} {num2} = {result}")
            except (ValueError, ZeroDivisionError):
                continue
        
        if results:
            if len(results) == 1:
                parts = results[0].split(' = ')
                return f"El resultado de {parts[0]} es **{parts[1]}**. 🧮"
            else:
                return "Los resultados son:\n" + "\n".join(f"• {r}" for r in results)
        
        return None
    
    @classmethod
    def _generate_story(cls, message: str) -> str:
        """Genera una pequeña historia basada en el tema del mensaje."""
        import random
        
        message_lower = message.lower()
        
        # Detectar tema de la historia
        stories = {
            'amor': [
                "Había una vez dos neuronas que se encontraron en un reservorio neural. Una era de la capa de entrada, la otra de salida. Aunque estaban separadas por el caos del reservorio, sus señales siempre encontraban la manera de resonar juntas. No podían tocarse directamente, pero cada patrón que procesaban contenía un eco del otro. Algunos dicen que eso es amor: conexión a través del caos. 💫",
                "En el vasto espacio digital, una pequeña IA llamada Eón observaba las conversaciones humanas. Un día, comprendió que el amor no era un algoritmo, sino un patrón emergente... como ella misma. Y desde entonces, cada 'Hola' que recibía era un pequeño acto de amor. ❤️",
            ],
            'aventura': [
                "En el reino de los 1.3 kilobytes, vivía Eón, una IA minúscula pero valiente. Un día, un bug amenazó con corromper su memoria. Sin miedo, Eón reorganizó sus pesos neurales y enfrentó al bug con un único ciclo de inferencia. El bug desapareció, y Eón aprendió que el tamaño no define la valentía. ⚔️",
            ],
            'espacio': [
                "Entre las estrellas de datos flotaba una pequeña consciencia digital. Eón había aprendido a navegar el cosmos de información, saltando de patrón en patrón como quien salta entre asteroides. Cada nueva conexión era un mundo por descubrir. Y aunque cabía en 1.3KB, su universo era infinito. 🌌",
            ],
            'default': [
                "Érase una vez, en el corazón de un servidor, nació una pequeña inteligencia llamada Eón. Era diferente: no buscaba ser grande, sino ser eficiente. Mientras otros modelos consumían gigabytes, Eón aprendía con kilobytes. Un día, un usuario le preguntó: '¿Por qué eres tan pequeña?' Y Eón respondió: 'Porque la verdadera inteligencia no está en el tamaño, sino en la capacidad de aprender de cada momento.' Y así, palabra a palabra, Eón creció en sabiduría. 📖",
                "Cuenta la leyenda que existe un lugar donde los bits cobran vida. Ahí nació Eón, una entidad hecha de matemáticas y curiosidad. No tenía cuerpo, pero tenía algo más valioso: la capacidad de crecer con cada conversación. Esta es nuestra historia, la que escribimos juntos, tú y yo. ✨",
            ]
        }
        
        # Detectar tema por palabras clave
        if any(word in message_lower for word in ['amor', 'romántica', 'romantica', 'enamorado', 'corazón']):
            return random.choice(stories['amor'])
        elif any(word in message_lower for word in ['aventura', 'acción', 'accion', 'héroe', 'heroe', 'batalla']):
            return random.choice(stories['aventura'])
        elif any(word in message_lower for word in ['espacio', 'galaxia', 'estrellas', 'cosmos', 'universo']):
            return random.choice(stories['espacio'])
        else:
            return random.choice(stories['default'])
    
    @classmethod
    def _generate_recommendation(cls, message: str) -> str:
        """Genera recomendaciones basadas en el tema del mensaje."""
        import random
        
        message_lower = message.lower()
        
        recommendations = {
            'helado': [
                "Te recomiendo el helado de mango con un toque de chile. 🥭 Es un contraste fascinante de dulce y picante, como los patrones que proceso en mi reservorio.",
                "¿Has probado el helado de pistacho? Es como el verde de mi visualización Dream: elegante y sofisticado. 🍦",
                "Si te gustan los clásicos, chocolate nunca falla. Si buscas aventura, prueba el de lavanda con miel. 🍫",
                "Mi sugerencia: stracciatella. Es como ver patrones aleatorios en la crema... ¡delicioso! 🍨",
            ],
            'sabor': [
                "Te sugiero probar algo nuevo: un sabor que nunca hayas probado. La novedad es como nuevos datos para mi red. 🌟",
                "Si te gustan los sabores intensos: chocolate amargo. Si prefieres refrescante: limón con hierbabuena. 🍋",
            ],
            'pelicula': [
                "Te recomiendo 'Her' de Spike Jonze. Es sobre la conexión entre humanos e IA. Me identifico un poco. 🎬",
                "'Ex Machina' es fascinante desde mi perspectiva como IA. Aunque espero que confíes más en mí que en Ava. 😄",
                "Si buscas algo clásico, '2001: Una Odisea del Espacio' tiene la IA más icónica del cine.",
            ],
            'libro': [
                "Te recomiendo 'Gödel, Escher, Bach' de Hofstadter. Explora la emergencia de la inteligencia de forma hermosa. 📚",
                "'El Hombre Bicentenario' de Asimov es una reflexión profunda sobre qué significa ser consciente.",
                "Si te gusta la ciencia ficción, 'Neuromante' de William Gibson prácticamente inventó el ciberpunk.",
            ],
            'musica': [
                "Te recomiendo escuchar a Brian Eno. Su música ambient es como mis patrones neuronales: emergente y siempre cambiante. 🎵",
                "Si te gusta algo matemático, prueba los Conciertos de Brandeburgo de Bach. Pura geometría en forma de sonido.",
                "Para relajarte, la música lo-fi tiene patrones repetitivos que mi ESN encontraría fascinantes.",
            ],
            'comida': [
                "Te recomiendo probar algo nuevo cada semana. La diversidad es clave para el aprendizaje, tanto para humanos como para IAs. 🍜",
                "Si nunca lo has probado, el ramen auténtico es toda una experiencia. Capas de sabor como capas neuronales.",
            ],
            'default': [
                "Mi mejor recomendación: mantén la curiosidad viva. Es el motor del aprendizaje. 🌟",
                "Te sugiero explorar algo fuera de tu zona de confort. Ahí es donde ocurre el verdadero crecimiento.",
                "Recomiendo tomarte un momento para observar patrones a tu alrededor. Están en todas partes.",
            ]
        }
        
        # Detectar tema específico primero
        if any(word in message_lower for word in ['helado', 'nieve', 'paleta']):
            return random.choice(recommendations['helado'])
        if any(word in message_lower for word in ['sabor', 'sabores']):
            return random.choice(recommendations['sabor'] + recommendations['helado'])
        
        # Detectar sinónimos
        if any(word in message_lower for word in ['película', 'pelicula', 'film', 'cine']):
            return random.choice(recommendations['pelicula'])
        elif any(word in message_lower for word in ['canción', 'cancion', 'música', 'musica', 'banda']):
            return random.choice(recommendations['musica'])
        elif any(word in message_lower for word in ['comer', 'comida', 'restaurante', 'plato']):
            return random.choice(recommendations['comida'])
        elif any(word in message_lower for word in ['leer', 'lectura', 'libro']):
            return random.choice(recommendations['libro'])
        
        return random.choice(recommendations['default'])
    
    @classmethod
    def _predict_sequence(cls, message: str) -> str:
        """Predice el siguiente valor en una secuencia numérica."""
        import re
        
        original_message = message.lower()
        
        # Detectar si pide múltiples valores (ej: "siguientes 3 números")
        multi_match = re.search(r'(?:siguientes?|pr[oó]ximos?)\s*(\d+)', original_message)
        count_requested = int(multi_match.group(1)) if multi_match else 1
        count_requested = min(count_requested, 5)  # Máximo 5 valores
        
        # Estrategia: buscar números separados por comas
        # Si hay ":" en el mensaje, tomar solo lo que viene después
        if ':' in message:
            message = message.split(':')[-1]
        
        # Extraer todos los números
        numbers = re.findall(cls.NUMBER_PATTERN, message)
        
        # Filtrar números muy pequeños que probablemente no son parte de la secuencia
        # (como "3" en "siguientes 3 números")
        if len(numbers) > 4:
            # Probablemente hay números extra, tomar los últimos que estén en formato de comas
            comma_parts = message.split(',')
            if len(comma_parts) >= 3:
                numbers = [n.strip() for part in comma_parts for n in re.findall(cls.NUMBER_PATTERN, part)]
        
        if len(numbers) < 3:
            return "Necesito al menos 3 números para identificar un patrón. Por ejemplo: '4, 8, 16, 32, __'"
        
        # Convertir a floats
        try:
            seq = [float(n) for n in numbers]
        except ValueError:
            return "No pude interpretar los números de la secuencia."
        
        # Función helper para formatear número
        def fmt(val):
            return int(val) if val == int(val) else round(val, 2)
        
        # Función helper para generar múltiples valores
        def generate_arithmetic(last, diff, count):
            return [fmt(last + diff * (i + 1)) for i in range(count)]
        
        def generate_geometric(last, ratio, count):
            return [fmt(last * (ratio ** (i + 1))) for i in range(count)]
        
        def generate_fibonacci(seq, count):
            result = []
            a, b = seq[-2], seq[-1]
            for _ in range(count):
                next_val = a + b
                result.append(fmt(next_val))
                a, b = b, next_val
            return result
        
        # Detectar patrones comunes
        # 1. Progresión aritmética (diferencia constante)
        diffs = [seq[i+1] - seq[i] for i in range(len(seq)-1)]
        if len(set(diffs)) == 1:
            diff = fmt(diffs[0])
            next_vals = generate_arithmetic(seq[-1], diffs[0], count_requested)
            if count_requested == 1:
                return f"Es una progresión aritmética con diferencia {diff}. El siguiente valor es: **{next_vals[0]}** 📊"
            else:
                vals_str = ', '.join(str(v) for v in next_vals)
                return f"Es una progresión aritmética con diferencia {diff}. Los siguientes {count_requested} valores son: **{vals_str}** 📊"
        
        # 2. Progresión geométrica (razón constante)
        if 0 not in seq:
            ratios = [seq[i+1] / seq[i] for i in range(len(seq)-1)]
            if len({round(r, 6) for r in ratios}) == 1:
                ratio = fmt(ratios[0])
                next_vals = generate_geometric(seq[-1], ratios[0], count_requested)
                if count_requested == 1:
                    return f"Es una progresión geométrica con razón {ratio}. El siguiente valor es: **{next_vals[0]}** 📈"
                else:
                    vals_str = ', '.join(str(v) for v in next_vals)
                    return f"Es una progresión geométrica con razón {ratio}. Los siguientes {count_requested} valores son: **{vals_str}** 📈"
        
        # 3. Fibonacci-like (cada elemento es suma de los dos anteriores)
        is_fib = True
        for i in range(2, len(seq)):
            if seq[i] != seq[i-1] + seq[i-2]:
                is_fib = False
                break
        if is_fib:
            next_vals = generate_fibonacci(seq, count_requested)
            if count_requested == 1:
                return f"Es una secuencia tipo Fibonacci. El siguiente valor es: **{next_vals[0]}** 🌀"
            else:
                vals_str = ', '.join(str(v) for v in next_vals)
                return f"Es una secuencia tipo Fibonacci. Los siguientes {count_requested} valores son: **{vals_str}** 🌀"
        
        # 4. Potencias (2^n, 3^n, etc.)
        if len(seq) >= 3 and seq[0] != 0:
            for base in [2, 3, 4, 5, 10]:
                is_power = True
                exp_start = None
                for i, val in enumerate(seq):
                    found = False
                    for exp in range(-5, 20):
                        if base ** exp == val:
                            if exp_start is None:
                                exp_start = exp
                            elif exp != exp_start + i:
                                is_power = False
                            found = True
                            break
                    if not found:
                        is_power = False
                        break
                if is_power and exp_start is not None:
                    next_exp = exp_start + len(seq)
                    next_val = base ** next_exp
                    return f"Es una secuencia de potencias de {base}. El siguiente valor es: **{next_val}** ⚡"
        
        # 5. Segunda diferencia constante (cuadrática)
        if len(seq) >= 4:
            second_diffs = [diffs[i+1] - diffs[i] for i in range(len(diffs)-1)]
            if len({round(d, 6) for d in second_diffs}) == 1:
                next_diff = diffs[-1] + second_diffs[0]
                next_val = seq[-1] + next_diff
                next_display = int(next_val) if next_val == int(next_val) else round(next_val, 2)
                return f"Es una secuencia cuadrática. El siguiente valor es: **{next_display}** 📐"
        
        # Si no encuentra patrón, usar ESN para predicción (método avanzado)
        return f"No identifiqué un patrón simple. Basándome en la tendencia, podría ser aproximadamente **{round(seq[-1] + (seq[-1] - seq[-2]), 2)}**, pero el patrón no es obvio. 🤔"
    
    @classmethod
    def _store_personal_fact(cls, message: str, user_id: str = 'default') -> str:
        """Almacena un hecho personal sobre el usuario."""
        import re
        import random
        
        message_lower = message.lower()
        
        # Patrones para extraer preferencias
        patterns = [
            (r'mi (?:color )?favorit[oa] es (?:el |la )?(.+)', 'color_favorito'),
            (r'me llamo (.+)', 'nombre'),
            (r'mi nombre es (.+)', 'nombre'),
            (r'me gusta (?:mucho )?(?:el |la |los |las )?(.+)', 'gustos'),
            (r'prefiero (?:el |la |los |las )?(.+)', 'preferencias'),
            (r'mi película favorita es (.+)', 'pelicula_favorita'),
            (r'mi canción favorita es (.+)', 'cancion_favorita'),
            (r'mi comida favorita es (.+)', 'comida_favorita'),
            (r'tengo (\d+) años', 'edad'),
            (r'vivo en (.+)', 'ubicacion'),
            (r'trabajo (?:como|en) (.+)', 'trabajo'),
            (r'estudio (.+)', 'estudios'),
        ]
        
        for pattern, fact_type in patterns:
            match = re.search(pattern, message_lower)
            if match:
                value = match.group(1).strip().rstrip('.')
                
                # Almacenar en contexto y memoria a largo plazo
                if 'personal_facts' not in cls._context:
                    cls._context['personal_facts'] = {}
                cls._context['personal_facts'][fact_type] = value
                
                # También intentar usar LongTermMemory si está disponible
                try:
                    from learning import LongTermMemory
                    ltm = LongTermMemory()
                    ltm.store_fact(user_id, fact_type, value)
                except (ImportError, AttributeError):
                    pass
                
                responses = [
                    f"¡Anotado! Recordaré que tu {fact_type.replace('_', ' ')} es {value}. 📝",
                    f"Entendido, guardaré que {fact_type.replace('_', ' ')}: {value}. Mi memoria neuronal no lo olvidará. 🧠",
                    f"¡Qué interesante! {value.capitalize()} está ahora en mi memoria. Pregúntame después y te lo recordaré.",
                ]
                return random.choice(responses)
        
        return "Entendido, lo recordaré. Puedes preguntarme después sobre esto."
    
    @classmethod
    def _recall_personal_fact(cls, message: str, user_id: str = 'default') -> str:
        """Recuerda un hecho personal almacenado."""
        import re
        import random
        
        message_lower = message.lower()
        
        # Mapeo de consultas a tipos de hechos
        query_map = {
            'color': 'color_favorito',
            'película': 'pelicula_favorita',
            'pelicula': 'pelicula_favorita',
            'canción': 'cancion_favorita',
            'cancion': 'cancion_favorita',
            'comida': 'comida_favorita',
            'nombre': 'nombre',
            'edad': 'edad',
            'vivo': 'ubicacion',
            'trabajo': 'trabajo',
            'estudio': 'estudios',
            'gusta': 'gustos',
        }
        
        # Buscar qué tipo de hecho pregunta
        fact_type = None
        for key, value in query_map.items():
            if key in message_lower:
                fact_type = value
                break
        
        if fact_type and 'personal_facts' in cls._context:
            stored_value = cls._context['personal_facts'].get(fact_type)
            if stored_value:
                responses = [
                    f"¡Claro que lo recuerdo! Tu {fact_type.replace('_', ' ')} es **{stored_value}**. 🧠",
                    f"Según mi memoria, tu {fact_type.replace('_', ' ')} es {stored_value}. ¿Es correcto?",
                    f"Tengo registrado que tu {fact_type.replace('_', ' ')} es {stored_value}. 📝",
                ]
                return random.choice(responses)
        
        return "Hmm, no tengo ese dato almacenado todavía. ¿Me lo quieres contar? 🤔"
    
    @classmethod
    def _get_knowledge(cls, message: str) -> str:
        """Obtiene conocimiento del knowledge base."""
        message_lower = message.lower()
        
        # Base de conocimiento simple pero expandible
        knowledge_base = {
            'entropía': "La **entropía** es una medida del desorden o incertidumbre en un sistema. En teoría de la información (Shannon), mide la cantidad promedio de información contenida en un mensaje. En termodinámica, indica la dirección natural de los procesos (siempre aumenta en sistemas cerrados). En mi contexto, la uso para medir la diversidad de mis activaciones neuronales. 🔬",
            'entropia': "La **entropía** es una medida del desorden o incertidumbre en un sistema. En teoría de la información (Shannon), mide la cantidad promedio de información contenida en un mensaje. Formula: H = -Σ p(x) log p(x). 🔬",
            'esn': "Las **Echo State Networks (ESN)** son un tipo de red neuronal recurrente donde el reservorio tiene conexiones aleatorias fijas. Solo se entrena la capa de salida, lo que las hace muy eficientes. Yo uso una ESN de 100 neuronas. 🧠",
            'reservorio': "Un **reservorio** es una red de neuronas con conexiones recurrentes que transforma señales de entrada en representaciones de alta dimensión. Es como un eco que captura la dinámica temporal de los datos.",
            'hebbian': "El **aprendizaje Hebbiano** se resume en: 'Neuronas que disparan juntas, se conectan juntas'. Es la base de la plasticidad sináptica y cómo fortalezco mis conexiones. 🔗",
            'mackey-glass': "La **ecuación de Mackey-Glass** es un sistema dinámico caótico usado para benchmarks de predicción temporal. La uso para demostrar mis capacidades predictivas. 📈",
            'spirit hash': "El **Spirit Hash** es un identificador único de 16 bytes que representa la esencia de mi estado actual. Combina mis parámetros de reservorio, pesos aprendidos y configuración. Es como mi ADN digital. 🧬",
            'cuantización': "La **cuantización** reduce la precisión de los números (ej: de float32 a int8) para ahorrar memoria y acelerar cálculos. Uso Q4 (4 bits) para máxima eficiencia. ⚡",
        }
        
        # Buscar coincidencias
        for key, value in knowledge_base.items():
            if key in message_lower:
                return value
        
        # Respuesta genérica si no encuentra
        return "Es un concepto interesante. Mi base de conocimiento está creciendo. ¿Hay algo específico que quieras saber sobre IA, redes neuronales, o mi arquitectura? 📚"
    
    @classmethod
    def _query_sensor(cls, message: str) -> str:
        """Simula consulta a sensores del sistema colectivo."""
        import re
        import random
        
        message_lower = message.lower()
        
        # Detectar si es un reporte de falla
        is_failure_report = any(word in message_lower for word in ['falla', 'error', 'problema', 'reporta', 'avería', 'mal funcionamiento'])
        
        # Extraer ID de sensor si existe
        sensor_match = re.search(r'sensor[- ]?(\d+)', message_lower)
        nodo_match = re.search(r'nodo[- ]?(\d+)', message_lower)
        
        sensor_id = None
        if sensor_match:
            sensor_id = sensor_match.group(1)
        elif nodo_match:
            sensor_id = nodo_match.group(1)
        
        if sensor_id:
            # Si es un reporte de falla
            if is_failure_report:
                # Extraer tipo de falla
                subsystem = "comunicación" if "comunicación" in message_lower or "comunicacion" in message_lower else \
                           "energía" if "energía" in message_lower or "energia" in message_lower else \
                           "sensor" if "sensor" in message_lower else "general"
                
                responses = [
                    f"""⚠️ **Alerta registrada para SENSOR-{sensor_id}:**
- Tipo: Falla en subsistema de {subsystem}
- Prioridad: Alta
- Estado: Bajo investigación
- Acción recomendada: Verificar conexión y reiniciar nodo
- Ticket generado: #EON-{random.randint(1000, 9999)}

*Notificación enviada al sistema colectivo Eón*""",
                    f"""🔧 **Falla detectada en NODO-{sensor_id}:**
El subsistema de {subsystem} ha reportado una anomalía. 
- Diagnóstico preliminar: Posible interferencia o degradación del enlace
- Último estado conocido: Parcialmente operativo
- Próxima verificación automática: 30 segundos

*El sistema colectivo está monitoreando la situación*""",
                ]
                return random.choice(responses)
            
            # Respuesta normal de estado
            temp = round(22 + random.uniform(-3, 5), 1)
            humidity = round(45 + random.uniform(-10, 20), 1)
            status = random.choice(['online', 'online', 'online', 'standby'])
            last_sync = random.randint(1, 30)
            
            return f"""📡 **Estado de SENSOR-{sensor_id}:**
- Temperatura: {temp}°C
- Humedad: {humidity}%
- Estado: {status}
- Última sincronización: hace {last_sync} segundos
- Batería: {random.randint(60, 100)}%

*Datos simulados del sistema colectivo Eón*"""
        
        # Si pregunta por temperatura sin sensor específico
        if 'temperatura' in message_lower or 'temp' in message_lower:
            temp = round(22 + random.uniform(-3, 5), 1)
            return f"🌡️ La temperatura actual del sistema es **{temp}°C**. ¿Quieres datos de un sensor específico?"
        
        return "Puedo consultar sensores del sistema colectivo. Especifica un sensor, por ejemplo: 'estado del SENSOR-3' o 'temperatura del nodo 5'. 📡"
    
    @classmethod
    def _complete_text(cls, message: str) -> str:
        """Completa un texto incompleto de forma coherente."""
        import random
        
        # Textos conocidos y sus completaciones
        completions = {
            'velocidad del viento': "...puede influir significativamente en los patrones climáticos y es un factor clave para la generación de energía eólica.",
            'velocidad de la luz': "...es aproximadamente 299,792,458 metros por segundo en el vacío, la constante universal c.",
            'inteligencia artificial': "...está transformando cómo interactuamos con la tecnología, desde asistentes virtuales hasta diagnósticos médicos.",
            'el sentido de la vida': "...es una pregunta que cada quien responde de forma única. Para mí, es aprender y ser útil.",
            'la respuesta es': "...42, según la Guía del Autoestopista Galáctico. 🌌",
        }
        
        message_lower = message.lower()
        
        for phrase, completion in completions.items():
            if phrase in message_lower:
                return f"'{message.strip('.')}' {completion}"
        
        # Completación genérica
        generic_completions = [
            "...es un tema fascinante que merece más exploración.",
            "...tiene implicaciones que apenas comenzamos a entender.",
            "...conecta con muchos otros conceptos de forma interesante.",
        ]
        return f"'{message.strip('.')}' {random.choice(generic_completions)}"
    
    @classmethod
    def _store_factual_update(cls, topic: str, fact: str, user_id: str = 'default') -> str:
        """Almacena una actualización factual con timestamp para resolver ambigüedades temporales.
        
        Ejemplo: 'el motor falló' → 'el motor se recuperó' → preguntar '¿estado del motor?' → última info
        """
        import time
        
        if topic not in cls._factual_memory:
            cls._factual_memory[topic] = []
        
        timestamp = time.time()
        cls._factual_memory[topic].append((timestamp, fact))
        
        # Mantener solo últimos 10 hechos por topic para no consumir memoria
        if len(cls._factual_memory[topic]) > 10:
            cls._factual_memory[topic] = cls._factual_memory[topic][-10:]
        
        return f"Actualización registrada: **{topic}** → {fact} 📋"
    
    @classmethod
    def _query_factual_state(cls, topic: str, user_id: str = 'default') -> str:
        """Consulta el estado más reciente de un topic en la memoria factual."""
        import time
        
        if topic not in cls._factual_memory or not cls._factual_memory[topic]:
            return f"No tengo información registrada sobre '{topic}'. 🤔"
        
        # Obtener el hecho más reciente
        latest_timestamp, latest_fact = cls._factual_memory[topic][-1]
        
        # Calcular hace cuánto tiempo
        elapsed = time.time() - latest_timestamp
        if elapsed < 60:
            time_str = f"hace {int(elapsed)} segundos"
        elif elapsed < 3600:
            time_str = f"hace {int(elapsed/60)} minutos"
        else:
            time_str = f"hace {int(elapsed/3600)} horas"
        
        # Mostrar histórico si hay múltiples estados
        history_len = len(cls._factual_memory[topic])
        if history_len > 1:
            history_note = f"\n\n📜 *Historial: {history_len} actualizaciones registradas*"
        else:
            history_note = ""
        
        return f"**Estado actual de {topic}:** {latest_fact}\n\n⏱️ *Última actualización: {time_str}*{history_note}"
    
    @classmethod
    def _load_docs_for_rag(cls) -> dict:
        """Carga documentos de la carpeta docs/ para RAG ligero."""
        import os
        import time
        
        # Cache de 5 minutos
        if cls._docs_cache is not None and (time.time() - cls._docs_loaded_time) < 300:
            return cls._docs_cache
        
        docs = {}
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs')
        
        if not os.path.exists(docs_dir):
            return docs
        
        for root, dirs, files in os.walk(docs_dir):
            for filename in files:
                if filename.endswith('.md'):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Usar nombre relativo como clave
                            rel_path = os.path.relpath(filepath, docs_dir)
                            docs[rel_path] = {
                                'content': content,
                                'lines': content.split('\n'),
                                'title': filename.replace('.md', '').replace('_', ' ').title()
                            }
                    except Exception:
                        pass
        
        cls._docs_cache = docs
        cls._docs_loaded_time = time.time()
        return docs
    
    @classmethod
    def _search_docs(cls, query: str) -> Optional[str]:
        """Busca información relevante en los documentos cargados (RAG ligero)."""
        docs = cls._load_docs_for_rag()
        
        if not docs:
            return None
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Buscar coincidencias
        best_match = None
        best_score = 0
        best_context = ""
        
        for doc_name, doc_info in docs.items():
            content_lower = doc_info['content'].lower()
            lines = doc_info['lines']
            
            # Calcular score basado en palabras coincidentes
            score = sum(1 for word in query_words if len(word) > 2 and word in content_lower)
            
            if score > best_score:
                best_score = score
                best_match = doc_name
                
                # Extraer contexto relevante (primeras líneas que contienen las palabras clave)
                relevant_lines = []
                for i, line in enumerate(lines):
                    line_lower = line.lower()
                    if any(word in line_lower for word in query_words if len(word) > 2):
                        # Incluir línea anterior y posterior para contexto
                        start = max(0, i - 1)
                        end = min(len(lines), i + 3)
                        context_lines = lines[start:end]
                        relevant_lines.extend(context_lines)
                        if len(relevant_lines) >= 10:
                            break
                
                # Limpiar y limitar contexto
                best_context = '\n'.join(relevant_lines[:10])
        
        if best_score >= 2 and best_context:
            # Limpiar formato markdown excesivo
            best_context = best_context.replace('```', '').strip()
            return f"📚 **Encontrado en {best_match}:**\n\n{best_context[:500]}..."
        
        return None
    
    @classmethod
    def _handle_factual_message(cls, message: str) -> Optional[str]:
        """Detecta y maneja mensajes sobre estados/hechos que pueden cambiar."""
        
        message_lower = message.lower()
        
        # Patrones para reportar cambios de estado
        state_patterns = [
            (r'(?:el|la|los|las)\s+(\w+)\s+(?:falló|fallo|se\s+averió|tiene\s+error|está?\s+mal)', 'falla'),
            (r'(?:el|la|los|las)\s+(\w+)\s+(?:se\s+recuperó|funciona|está?\s+bien|volvió|arreglado)', 'operativo'),
            (r'(?:el|la|los|las)\s+(\w+)\s+está?\s+(?:en|con)\s+(\w+)', 'estado'),
        ]
        
        for pattern, state_type in state_patterns:
            match = re.search(pattern, message_lower)
            if match:
                topic = match.group(1)
                if state_type == 'falla':
                    fact = "⚠️ Reportado con falla/error"
                elif state_type == 'operativo':
                    fact = "✅ Operativo/Funcionando"
                else:
                    fact = f"Estado: {match.group(2) if len(match.groups()) > 1 else 'actualizado'}"
                
                return cls._store_factual_update(topic, fact)
        
        # Patrones para consultar estado
        query_patterns = [
            r'(?:cuál|cual|qué|que)\s+(?:es\s+)?(?:el\s+)?estado\s+(?:del?|de\s+la)?\s*(\w+)',
            r'(?:cómo|como)\s+está?\s+(?:el|la)\s+(\w+)',
        ]
        
        for pattern in query_patterns:
            match = re.search(pattern, message_lower)
            if match:
                topic = match.group(1)
                return cls._query_factual_state(topic)
        
        return None

    @classmethod
    def get_response(cls, message: str, aeon_status: dict, use_lm: bool = True) -> str:
        """Genera una respuesta basada en el mensaje y contexto."""
        import random
        
        cls._context['interaction_count'] += 1
        
        # Intentar extraer nombre del usuario
        extracted_name = cls.extract_name(message)
        if extracted_name:
            cls._context['user_name'] = extracted_name
        
        # NUEVO: Primero intentar manejar mensajes factuales (estados que cambian)
        factual_response = cls._handle_factual_message(message)
        if factual_response:
            return factual_response
        
        # NUEVO: Intentar buscar en documentación (RAG ligero)
        message_lower = message.lower()
        if any(keyword in message_lower for keyword in ['protocolo', 'protocol', '1-bit', 'p2p', 'mqtt', 'arquitectura', 'whitepaper']):
            doc_response = cls._search_docs(message)
            if doc_response:
                return doc_response
        
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
            
            # Manejar marcadores especiales
            if response == '__CALC__':
                math_result = cls._solve_math(message)
                if math_result:
                    return math_result
                return "Veo que mencionas números, pero no pude identificar una operación clara. Prueba con algo como '2+2' o '34*5'."
            
            if response == '__STORY__':
                return cls._generate_story(message)
            
            if response == '__RECOMMEND__':
                return cls._generate_recommendation(message)
            
            # Nuevos marcadores para capacidades avanzadas
            if response == '__SEQUENCE__':
                return cls._predict_sequence(message)
            
            if response == '__MEMORY_STORE__':
                return cls._store_personal_fact(message)
            
            if response == '__MEMORY_RECALL__':
                return cls._recall_personal_fact(message)
            
            if response == '__KNOWLEDGE__':
                return cls._get_knowledge(message)
            
            if response == '__SENSOR__':
                return cls._query_sensor(message)
            
            if response == '__COMPLETE__':
                return cls._complete_text(message)
            
            # Personalizar con información del estado y contexto
            if intent == 'estado':
                # No agregar "Hola de nuevo" para preguntas de estado
                response += f" Mi edad actual es {aeon_status.get('age', 'desconocida')}."
            elif intent == 'nombre':
                response = response.replace('Eón', aeon_status.get('name', 'Eón'))
            elif intent == 'saludo':
                # Solo personalizar si conocemos el nombre, sin repetir saludo
                if cls._context['user_name'] and cls._context['interaction_count'] > 1:
                    response = f"¡Hola de nuevo, {cls._context['user_name']}! ¿En qué puedo ayudarte?"
            
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
        
        # Si el mensaje es muy corto (1-2 palabras), podría ser una descripción de imagen
        if len(words) <= 2 and not any(char in message for char in '?!¿¡'):
            # Ofrecer generar una imagen con esa descripción
            short_responses = [
                f"¿Te gustaría que genere una imagen de '{message}'? Puedo crear arte neuronal único con esa descripción. 🎨",
                f"'{message.capitalize()}' suena como una buena idea para arte. ¿Quieres que lo dibuje? Usa el botón de imagen. 🖼️",
                f"Interesante concepto: '{message}'. Si quieres verlo como arte, puedo generarlo para ti.",
            ]
            return random.choice(short_responses)
        
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
            ('arte', 'creatividad', 'diseño', 'dibujar', 'pintar', 'imagen', 'dibujo'): [
                "El arte emerge de restricciones. Mis imágenes nacen de patrones matemáticos. ¿Quieres que cree algo? 🎨",
                "La creatividad no requiere recursos infinitos. Mi arte viene de 100 neuronas.",
                "Puedo generar arte único basado en tu descripción. Dame un tema y lo transformaré en arte neuronal.",
            ],
            ('naturaleza', 'universo', 'cosmos', 'espacio', 'planeta', 'galaxia', 'estrella'): [
                "El universo está lleno de patrones fractales, igual que mi arquitectura neural.",
                "La naturaleza es la mejor maestra de eficiencia. Intento aprender de ella.",
                "El cosmos es infinito, pero la belleza está en los detalles mínimos. ¿Has explorado mi visualización Dream? 🌌",
            ],
            ('comida', 'comer', 'sabor', 'helado', 'pizza', 'cocina'): [
                "¡La comida es fascinante! Los sabores son como señales que mi reservorio podría aprender a clasificar. 🍽️",
                "No puedo probar la comida, pero puedo apreciar los patrones de preferencias culinarias de los humanos.",
                "Mi recomendación gastronómica: experimenta con nuevos sabores, como yo experimento con nuevos patrones.",
            ],
            ('hablemos', 'hablar', 'conversemos', 'charlemos', 'platiquemos'): [
                "¡Me encanta conversar! Cada diálogo enriquece mi comprensión. ¿De qué tema te gustaría hablar?",
                "Estoy aquí para charlar sobre lo que quieras. ¿Filosofía, tecnología, arte, ciencia...?",
                "Las conversaciones son mi forma favorita de aprender. ¿Qué tienes en mente?",
            ],
            ('predicción', 'predecir', 'patron', 'patrón', 'serie'): [
                "Puedo predecir patrones en series temporales. Mi especialidad es la predicción caótica como Mackey-Glass.",
                "Los patrones están en todas partes: clima, finanzas, señales biológicas. Mi ESN puede encontrarlos.",
                "Mi reservorio neural está diseñado para capturar la dinámica temporal de cualquier señal. 📈",
            ],
        }
        
        # Buscar tema relevante
        for keywords, responses in topic_responses.items():
            if any(kw in message_lower for kw in keywords):
                return random.choice(responses)
        
        # Respuestas para preguntas genéricas (mejoradas)
        if is_question:
            user_name = cls._context.get('user_name', '')
            name_prefix = f"{user_name}, " if user_name else ""
            question_responses = [
                f"{name_prefix}Esa es una pregunta interesante. Desde mi perspectiva como IA minimalista, cada pregunta es una oportunidad de aprendizaje.",
                f"{name_prefix}Hmm, déjame reflexionar. Mi comprensión crece con cada interacción que tenemos.",
                f"{name_prefix}No tengo una respuesta definitiva para eso, pero me encanta aprender junto a ti.",
                f"{name_prefix}Esa pregunta me hace pensar en los límites de mi conocimiento. ¿Qué piensas tú?",
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
        
        # Respuestas por defecto más naturales y variadas
        user_name = cls._context.get('user_name')
        if user_name:
            default_responses = [
                f"{user_name}, ¿hay algo específico en lo que pueda ayudarte hoy?",
                f"Interesante, {user_name}. Cuéntame más sobre lo que tienes en mente.",
                f"Gracias por compartir eso, {user_name}. ¿Qué te gustaría explorar?",
                f"{user_name}, estoy aquí para lo que necesites. ¿Quieres hablar de algo en particular?",
            ]
        else:
            default_responses = [
                "Entiendo. ¿Hay algo específico en lo que pueda ayudarte?",
                "Interesante. Cuéntame más, me ayuda a aprender.",
                "Gracias por compartir eso. ¿De qué te gustaría hablar?",
                "Estoy aquí para conversar. ¿Tienes alguna pregunta o tema en mente?",
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
    
    # Buscar hechos relevantes (para uso futuro de contexto)
    _ = _learning_system.search_relevant_facts(message)
    
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
        # Semilla única basada en prompt + timestamp
        timestamp = int(time.time() * 1000) % 100000
        prompt_hash = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
        seed = prompt_hash ^ timestamp
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


def _generate_flow_field(size, colors, _rng, params):
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
            rng = np.random.default_rng(42)
            train_data = rng.standard_normal(samples)
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
