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
if _python_dir not in sys.path:
    sys.path.insert(0, _python_dir)

from core.aeon_birth import AeonBirth
from core.genesis import get_genesis
from esn.esn import generate_mackey_glass


app = Flask(__name__, static_folder='static')

# Instancia global de Eón
# Inicialización Automática (Singleton)
# Intentamos cargar la instancia persistente o crearla basada en GENESIS
try:
    _genesis_info = get_genesis()
    # Buscamos si existe data guardada, sino creamos una usando el hash de genesis como seed
    try:
        _aeon_instance = AeonBirth.load(_genesis_info.birth_hash, DATA_DIR)
        print(f" [INFO] Instancia cargada: {_aeon_instance.name}")
    except FileNotFoundError:
        print(f" [INFO] Inicializando nueva instancia basada en GENESIS...")
        _aeon_instance = AeonBirth(
            n_reservoir=100,
            name=f"Eon-{_genesis_info.birth_hash[:8]}",
            data_dir=DATA_DIR
        )
        # Forzamos que el ESN use el timestamp real de genesis si es posible,
        # aunque AeonBirth usa su propio tiempo. Para alinearlos:
        # (Esto es una mejora opcional, por ahora basta con que exista)
except Exception as e:
    print(f" [ERROR] Fallo al inicializar Eón: {e}")
    _aeon_instance = None


@app.route('/')
def index():
    """Servir página principal."""
    return send_from_directory('static', 'index.html')

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """Endpoint para configuración de parámetros de IA."""
    if request.method == 'POST':
        data = request.get_json() or {}
        # Aquí guardaríamos la configuración. Por ahora es simulado.
        return jsonify({
            'success': True,
            'message': 'Configuración actualizada',
            'config': data
        })
    else:
        # Valores por defecto simulados
        return jsonify({
            'success': True,
            'config': {
                'temperature': 0.7,
                'spectral_radius': 0.95,
                'leak_rate': 0.1
            }
        })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint preliminar para chat."""
    global _aeon_instance
    data = request.get_json() or {}
    message = data.get('message', '')
    
    # Aquí iría la lógica de procesamiento de lenguaje natural real
    # Por ahora, usamos una respuesta mock o eco si la instancia no está lista
    
    if not _aeon_instance:
        return jsonify({
            'success': False,
            'reply': "Eón no ha nacido. Por favor inicializa el sistema."
        })
        
    return jsonify({
        'success': True,
        'reply': f"Eco: {message} (Procesado por Eón v0.1)"
    })


@app.route('/api/birth', methods=['POST'])
@app.route('/api/birth', methods=['POST'])
def create_birth():
    """Endpoint legado. Retorna el estado actual ya que el nacimiento es inmutable."""
    global _aeon_instance
    if _aeon_instance:
         return jsonify({
            'success': True,
            'message': 'Eón ya existe (Inmutable)',
            'status': _aeon_instance.get_status()
        })
    return jsonify({'success': False, 'error': 'Sistema no inicializado'}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Obtener estado actual."""
    if _aeon_instance is None:
        return jsonify({
            'success': False,
            'error': 'No hay instancia activa. Usa /api/birth primero.'
        }), 404
    
    return jsonify({
        'success': True,
        'status': _aeon_instance.get_status()
    })


@app.route('/api/learn', methods=['POST'])
def learn():
    """Alimentar datos para aprendizaje."""
    global _aeon_instance
    
    if _aeon_instance is None:
        return jsonify({
            'success': False,
            'error': 'No hay instancia activa'
        }), 404
    
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
    """Generar predicción."""
    if _aeon_instance is None:
        return jsonify({
            'success': False,
            'error': 'No hay instancia activa'
        }), 404
    
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
