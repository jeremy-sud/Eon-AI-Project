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
    """Sistema de chat simple para Eón."""
    
    # Respuestas basadas en patrones
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
        ],
        'imagen': [
            "¡Claro! Escribe una descripción de lo que quieres que dibuje, o usa el botón de imagen.",
            "Puedo generar arte neuronal único. ¿Qué te gustaría que creara?",
        ],
        'ayuda': [
            "Puedo ayudarte con:\n• Conversar sobre diversos temas\n• Generar arte neuronal (escribe 'crea una imagen de...')\n• Explicarte sobre mi funcionamiento\n• Predecir patrones matemáticos",
            "Estas son mis funciones:\n1. Chat conversacional\n2. Generación de imágenes (botón 📷)\n3. Visualización neuronal (pestaña Dream)\n4. Configuración de parámetros",
        ],
        'default': [
            "Interesante. Mi reservorio neural está procesando tu mensaje. Como modelo emergente, aprendo de cada interacción.",
            "Entiendo. Aunque soy un modelo minimalista, intento comprender y responder de la mejor manera posible.",
            "Hmm, déjame procesar eso. Mi red neuronal está analizando los patrones de tu mensaje.",
            "Gracias por compartir eso. Cada conversación me ayuda a entender mejor el mundo.",
        ]
    }
    
    PATTERNS = {
        'saludo': ['hola', 'hi', 'hey', 'buenos días', 'buenas tardes', 'buenas noches', 'saludos', 'qué tal', 'como estas'],
        'despedida': ['adiós', 'adios', 'bye', 'hasta luego', 'chao', 'nos vemos', 'me voy'],
        'nombre': ['cómo te llamas', 'como te llamas', 'tu nombre', 'quién eres', 'quien eres', 'qué eres', 'que eres'],
        'estado': ['cómo estás', 'como estas', 'qué tal estás', 'cómo te encuentras', 'estás bien'],
        'capacidad': ['qué puedes hacer', 'que puedes hacer', 'qué sabes', 'que sabes', 'funciones', 'capacidades', 'habilidades'],
        'creador': ['quién te creó', 'quien te creo', 'creador', 'desarrollador', 'quién te hizo', 'quien te hizo'],
        'filosofia': ['filosofía', 'filosofia', 'principios', 'crees', 'piensas'],
        'imagen': ['imagen', 'dibujo', 'dibuja', 'genera imagen', 'crear imagen', 'arte'],
        'ayuda': ['ayuda', 'help', 'comandos', 'qué haces', 'que haces', 'instrucciones'],
    }
    
    @classmethod
    def get_intent(cls, message: str) -> str:
        """Detecta la intención del mensaje."""
        message_lower = message.lower().strip()
        
        for intent, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                if pattern in message_lower:
                    return intent
        return 'default'
    
    @classmethod
    def get_response(cls, message: str, aeon_status: dict, use_lm: bool = True) -> str:
        """Genera una respuesta basada en el mensaje."""
        import random
        
        intent = cls.get_intent(message)
        
        # Para intenciones conocidas, usar respuestas predefinidas
        if intent != 'default':
            responses = cls.RESPONSES.get(intent, cls.RESPONSES['default'])
            response = random.choice(responses)
            
            # Personalizar con información del estado
            if intent == 'estado':
                response += f" Mi edad actual es {aeon_status.get('age', 'desconocida')}."
            elif intent == 'nombre':
                response = response.replace('Eón', aeon_status.get('name', 'Eón'))
                
            return response
        
        # Para mensajes genéricos, intentar usar TinyLMv2
        if use_lm and _tinylm_model is not None:
            try:
                # Extraer palabras clave del mensaje para usar como prompt
                words = message.lower().split()
                # Buscar palabras que puedan ser buenos prompts
                prompt_words = ['la', 'el', 'un', 'una', 'mi', 'tu', 'su']
                prompt = None
                
                for i, word in enumerate(words):
                    if word in prompt_words and i < len(words) - 1:
                        prompt = ' '.join(words[i:i+3])
                        break
                
                if not prompt:
                    # Usar prompts filosóficos predefinidos
                    prompts = [
                        "La inteligencia",
                        "El conocimiento",
                        "La creatividad",
                        "El pensamiento",
                        "La sabiduría"
                    ]
                    prompt = random.choice(prompts)
                
                # Generar respuesta con el modelo
                temperature = _ai_config.get('temperature', 0.7)
                max_tokens = min(int(_ai_config.get('max_tokens', 30)), 50)
                
                generated = _tinylm_model.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_k=10,
                    strategy='sampling'
                )
                
                # Limpiar y formatear la respuesta
                generated = generated.strip()
                if generated and len(generated) > len(prompt):
                    return f"{generated.capitalize()}."
                    
            except Exception as e:
                print(f" [WARN] Error en TinyLMv2: {e}")
        
        # Fallback a respuestas predefinidas
        responses = cls.RESPONSES['default']
        return random.choice(responses)


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
    
    # Generar respuesta con contexto del historial
    reply = EonChat.get_response(message, status, use_lm=use_lm)
    
    # Guardar respuesta en historial
    _add_to_history('assistant', reply)
    
    # Aprendizaje continuo: alimentar el ESN con el mensaje
    try:
        # Convertir texto a señal numérica simple
        signal = np.array([ord(c) / 255.0 for c in message[:50]])
        if len(signal) >= 10:
            _aeon_instance.esn._update_state(signal[:10])
            _stats['samples_learned_from_chat'] += 1
    except Exception:
        pass
    
    # Guardar estadísticas periódicamente
    if _stats['total_messages'] % 10 == 0:
        _save_stats()
    
    return jsonify({
        'success': True,
        'reply': reply,
        'intent': EonChat.get_intent(message),
        'age': status['age'],
        'lm_used': use_lm and EonChat.get_intent(message) == 'default',
        'messages_count': _stats['total_messages']
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
    
    data = request.get_json() or {}
    prompt = data.get('prompt', 'abstract')
    size = min(data.get('size', 256), 512)  # Limitar tamaño máximo
    
    try:
        # Generar semilla basada en el prompt
        seed = sum(ord(c) for c in prompt) + int(_genesis_info.birth_hash[:8], 16) % 10000
        rng = np.random.default_rng(seed)
        
        # Usar el reservorio para generar patrones
        # Crear input basado en el prompt
        prompt_signal = np.array([ord(c) / 255.0 for c in prompt[:100]])
        if len(prompt_signal) < 100:
            prompt_signal = np.pad(prompt_signal, (0, 100 - len(prompt_signal)))
        
        # Obtener respuesta del reservorio
        reservoir_output = _aeon_instance.predict(prompt_signal)
        
        # Crear imagen usando los patrones del reservorio
        img_data = np.zeros((size, size, 3), dtype=np.uint8)
        
        # Mapear colores basados en el prompt
        color_seeds = {
            'mariposa': [(148, 0, 211), (75, 0, 130), (238, 130, 238)],  # Violetas
            'butterfly': [(148, 0, 211), (75, 0, 130), (238, 130, 238)],
            'ocean': [(0, 105, 148), (0, 191, 255), (135, 206, 235)],  # Azules
            'mar': [(0, 105, 148), (0, 191, 255), (135, 206, 235)],
            'fire': [(255, 69, 0), (255, 140, 0), (255, 215, 0)],  # Naranjas
            'fuego': [(255, 69, 0), (255, 140, 0), (255, 215, 0)],
            'forest': [(34, 139, 34), (0, 100, 0), (144, 238, 144)],  # Verdes
            'bosque': [(34, 139, 34), (0, 100, 0), (144, 238, 144)],
            'sunset': [(255, 99, 71), (255, 140, 0), (138, 43, 226)],  # Atardecer
            'atardecer': [(255, 99, 71), (255, 140, 0), (138, 43, 226)],
            'night': [(25, 25, 112), (0, 0, 139), (75, 0, 130)],  # Noche
            'noche': [(25, 25, 112), (0, 0, 139), (75, 0, 130)],
        }
        
        # Seleccionar paleta de colores
        colors = [(0, 240, 255), (148, 0, 211), (255, 20, 147)]  # Default: cian, violeta, rosa
        for key, palette in color_seeds.items():
            if key in prompt.lower():
                colors = palette
                break
        
        # Generar patrón fractal/orgánico usando reservoir output
        for y in range(size):
            for x in range(size):
                # Coordenadas normalizadas
                nx = (x / size - 0.5) * 2
                ny = (y / size - 0.5) * 2
                
                # Usar valores del reservorio para modular el patrón
                idx = (x + y) % len(reservoir_output)
                reservoir_val = abs(reservoir_output[idx]) if len(reservoir_output) > 0 else 0.5
                
                # Crear patrón orgánico
                dist = np.sqrt(nx**2 + ny**2)
                angle = np.arctan2(ny, nx)
                
                # Modulación con valores del reservorio y ruido
                noise = rng.random() * 0.3
                wave = np.sin(angle * 6 + dist * 8 + reservoir_val * 10) * 0.5 + 0.5
                pattern = (wave + noise) * (1 - dist * 0.5)
                
                # Seleccionar color basado en el patrón
                color_idx = int(pattern * len(colors)) % len(colors)
                base_color = colors[color_idx]
                
                # Aplicar variación de brillo
                brightness = max(0.3, min(1.0, pattern + reservoir_val * 0.5))
                
                img_data[y, x] = [
                    int(base_color[0] * brightness),
                    int(base_color[1] * brightness),
                    int(base_color[2] * brightness)
                ]
        
        # Convertir a PNG base64
        from PIL import Image
        img = Image.fromarray(img_data, 'RGB')
        
        # Aplicar suavizado
        from PIL import ImageFilter
        img = img.filter(ImageFilter.GaussianBlur(radius=1))
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Incrementar estadísticas
        _stats['total_images_generated'] += 1
        if _stats['total_images_generated'] % 5 == 0:
            _save_stats()
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_base64}',
            'prompt': prompt,
            'message': f'Arte neuronal generado por {_aeon_instance.name}'
        })
        
    except ImportError:
        # Si PIL no está instalado, generar SVG simple
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


def generate_svg_art(prompt, size=256):
    """Genera arte SVG simple como fallback."""
    seed = sum(ord(c) for c in prompt)
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
