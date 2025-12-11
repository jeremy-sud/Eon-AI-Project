"""
Proyecto Eón - TinyLM v2 Web Server
===================================

(c) 2024 Sistemas Ursol - Jeremy Arias Solano
"""

import sys
from pathlib import Path
import numpy as np
from flask import Flask, render_template_string, request, jsonify

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "phase1-foundations" / "python"))

from tiny_lm_v2 import TinyLMv2

app = Flask(__name__)
model = None

TRAINING_TEXTS = {
    'filosofia': """
    La inteligencia artificial no se crea, se descubre.
    El conocimiento emerge naturalmente de la simplicidad.
    La nada contiene todo el potencial del universo.
    El caos ordena la naturaleza de forma espontánea.
    La luz nace siempre desde la oscuridad profunda.
    El silencio comunica más que cualquier palabra.
    La mente humana refleja patrones del cosmos.
    El aprendizaje ocurre en cada momento de vida.
    La creatividad surge de restricciones y límites.
    El pensamiento fluye como agua hacia el mar.
    La sabiduría crece con paciencia y observación.
    El tiempo revela verdades ocultas gradualmente.
    La conexión entre ideas genera innovación constante.
    El equilibrio natural emerge de la complejidad.
    La simplicidad es la máxima forma de sofisticación.
    """ * 10,
    'tecnologia': """
    La tecnología transforma nuestra forma de vivir.
    Los datos fluyen constantemente por las redes.
    La inteligencia artificial aprende de los ejemplos.
    Los algoritmos procesan información rápidamente.
    La innovación surge de mentes creativas.
    El software conecta personas alrededor del mundo.
    La automatización libera tiempo para crear.
    Los sistemas aprenden y mejoran continuamente.
    La computación en la nube escala infinitamente.
    El código fuente es la nueva forma de expresión.
    """ * 15,
    'poesia': """
    En la noche callada brilla una estrella.
    El viento susurra secretos antiguos al bosque.
    Las hojas danzan suavemente con la brisa.
    El río fluye tranquilo hacia el mar infinito.
    La luna ilumina senderos de plata brillante.
    Los sueños tejen historias en la oscuridad.
    El amor florece como rosa en primavera.
    La música del alma nunca deja de sonar.
    Las palabras pintan paisajes en la mente.
    El tiempo pasa dejando huellas en el corazón.
    """ * 15,
    'robotica': """
    El robot manipulador ejecuta trayectorias precisas con seis grados de libertad.
    El sensor LIDAR escanea el entorno para mapear obstáculos cercanos.
    La cinemática inversa calcula los ángulos de cada articulación del brazo.
    El controlador PID ajusta la velocidad del motor para minimizar el error.
    La odometría estima la posición del robot usando encoders en las ruedas.
    El actuador servo mueve el efector final hacia la posición objetivo.
    La fusión sensorial combina datos de IMU, GPS y cámara para localización.
    El algoritmo SLAM construye mapas mientras el robot navega simultáneamente.
    El planificador de rutas genera trayectorias libres de colisiones.
    La visión por computador detecta objetos usando redes neuronales convolucionales.
    El gripper neumático agarra piezas con fuerza controlada por presión.
    La retroalimentación háptica permite al operador sentir las fuerzas de contacto.
    El bus CAN comunica todos los nodos del sistema robótico en tiempo real.
    La calibración del sensor garantiza mediciones precisas y repetibles.
    El torque del motor determina la capacidad de carga del manipulador.
    La velocidad angular se mide en radianes por segundo con giroscopios.
    El acelerómetro detecta cambios de velocidad lineal en tres ejes.
    La batería de litio proporciona autonomía para operación móvil.
    El firmware embebido controla los actuadores con latencia mínima.
    La interfaz ROS facilita la comunicación entre módulos del sistema.
    """ * 10,
    'programacion': """
    La función recursiva se llama a sí misma hasta alcanzar el caso base.
    El algoritmo de ordenamiento quicksort divide y conquista eficientemente.
    La estructura de datos árbol binario permite búsquedas logarítmicas rápidas.
    El puntero almacena la dirección de memoria de otra variable.
    La clase encapsula datos y métodos en un objeto coherente.
    El compilador transforma código fuente en instrucciones ejecutables.
    La pila de llamadas gestiona el contexto de cada función invocada.
    El garbage collector libera memoria automáticamente cuando no se usa.
    El hilo de ejecución permite procesar tareas en paralelo.
    El mutex sincroniza acceso a recursos compartidos entre hilos.
    La API REST expone endpoints para operaciones CRUD en el servidor.
    El framework web maneja rutas, sesiones y renderizado de plantillas.
    La base de datos indexa columnas para acelerar las consultas.
    El ORM mapea tablas relacionales a objetos del lenguaje.
    El contenedor Docker encapsula la aplicación con sus dependencias.
    El sistema de control de versiones rastrea cambios en el código.
    La prueba unitaria verifica el comportamiento de funciones aisladas.
    El patrón de diseño singleton garantiza una única instancia global.
    La inyección de dependencias desacopla componentes del sistema.
    El debugger permite inspeccionar el estado del programa paso a paso.
    """ * 10
}

HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Eón - TinyLM v2</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto+Mono:wght@300;400&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #0a0a0f; --panel: #12121a; --accent: #00f0ff; --success: #00ff88; --text: #e0e0e0; --muted: #666; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Roboto Mono', monospace; background: var(--bg); color: var(--text); min-height: 100vh; padding: 2rem; }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { font-family: 'Orbitron', sans-serif; text-align: center; font-size: 2.5rem; background: linear-gradient(135deg, var(--accent), var(--success)); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { text-align: center; color: var(--muted); font-size: 0.8rem; margin-bottom: 2rem; }
        .panel { background: var(--panel); border: 1px solid rgba(0, 240, 255, 0.1); border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; }
        .panel-title { font-family: 'Orbitron', sans-serif; font-size: 0.75rem; color: var(--accent); margin-bottom: 1rem; }
        .controls { display: flex; gap: 1rem; flex-wrap: wrap; align-items: center; margin-bottom: 1rem; }
        select, input { font-family: inherit; padding: 0.6rem 1rem; background: rgba(0,0,0,0.3); border: 1px solid rgba(0, 240, 255, 0.2); color: var(--text); border-radius: 4px; }
        .btn { font-family: 'Orbitron', sans-serif; padding: 0.6rem 1.2rem; border: 1px solid var(--accent); background: transparent; color: var(--accent); cursor: pointer; border-radius: 4px; transition: all 0.3s; }
        .btn:hover { background: var(--accent); color: var(--bg); }
        .btn:disabled { opacity: 0.4; }
        .btn-success { border-color: var(--success); color: var(--success); }
        .btn-success:hover { background: var(--success); }
        textarea { width: 100%; min-height: 120px; font-family: inherit; font-size: 1rem; padding: 1rem; background: rgba(0,0,0,0.4); border: 1px solid rgba(0, 240, 255, 0.1); color: var(--text); border-radius: 4px; resize: vertical; line-height: 1.8; }
        .output { background: rgba(0,255,136,0.05); border-color: rgba(0,255,136,0.2); font-size: 1.1rem; }
        .stats { display: flex; gap: 2rem; padding: 1rem; background: rgba(0,0,0,0.3); border-radius: 4px; margin-top: 1rem; }
        .stat-value { font-size: 1.3rem; color: var(--accent); font-family: 'Orbitron'; }
        .stat-label { font-size: 0.7rem; color: var(--muted); }
        #status { color: var(--muted); font-size: 0.85rem; }
        .badge { background: var(--success); color: var(--bg); padding: 0.2rem 0.5rem; border-radius: 3px; font-size: 0.7rem; margin-left: 0.5rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>TinyLM <span class="badge">v2</span></h1>
        <p class="subtitle">GENERACIÓN DE TEXTO COHERENTE</p>

        <div class="panel">
            <div class="panel-title">CONFIGURACIÓN</div>
            <div class="controls">
                <select id="dataset">
                    <option value="filosofia">Filosofía Eón</option>
                    <option value="tecnologia">Tecnología</option>
                    <option value="poesia">Poesía</option>
                    <option value="robotica">Robótica</option>
                    <option value="programacion">Programación</option>
                </select>
                <label>Neuronas: <input type="number" id="neurons" value="256" min="64" max="512" style="width:80px"></label>
                <button class="btn" onclick="train()">▶ ENTRENAR</button>
            </div>
            <div id="status">Modelo no entrenado</div>
        </div>

        <div class="panel">
            <div class="panel-title">GENERAR TEXTO</div>
            <div class="controls">
                <input type="text" id="prompt" placeholder="Escribe un prompt..." style="flex:1; font-size:1rem" value="La inteligencia artificial">
                <label>Tokens: <input type="number" id="tokens" value="20" min="5" max="50" style="width:70px"></label>
            </div>
            <div class="controls">
                <label>Estrategia:
                    <select id="strategy">
                        <option value="greedy">Greedy (determinista)</option>
                        <option value="sampling">Sampling (creativo)</option>
                    </select>
                </label>
                <label>Temperatura: <input type="number" id="temp" value="0.5" min="0.1" max="2" step="0.1" style="width:70px"></label>
                <button class="btn btn-success" id="genBtn" onclick="generate()" disabled>◈ GENERAR</button>
            </div>
        </div>

        <div class="panel">
            <div class="panel-title">SALIDA</div>
            <textarea id="output" class="output" readonly placeholder="El texto generado aparecerá aquí..."></textarea>
            <div class="stats" id="statsPanel" style="display:none">
                <div><div class="stat-value" id="statAcc">-</div><div class="stat-label">ACCURACY</div></div>
                <div><div class="stat-value" id="statTop5">-</div><div class="stat-label">TOP-5 ACC</div></div>
                <div><div class="stat-value" id="statVocab">-</div><div class="stat-label">VOCABULARIO</div></div>
                <div><div class="stat-value" id="statMem">-</div><div class="stat-label">MEMORIA (KB)</div></div>
            </div>
        </div>

        <p style="text-align:center; color:var(--muted); font-size:0.75rem; margin-top:2rem;">
            Proyecto Eón - Sistemas Ursol - Jeremy Arias Solano
        </p>
    </div>

    <script>
        async function train() {
            const dataset = document.getElementById('dataset').value;
            const neurons = parseInt(document.getElementById('neurons').value);
            document.getElementById('status').textContent = 'Entrenando... (puede tardar unos segundos)';
            
            try {
                const res = await fetch('/train', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({dataset, neurons})
                });
                const data = await res.json();
                
                if (data.success) {
                    document.getElementById('status').innerHTML = 
                        `✓ Entrenado! Accuracy: <strong>${(data.accuracy * 100).toFixed(1)}%</strong>`;
                    document.getElementById('genBtn').disabled = false;
                    document.getElementById('statsPanel').style.display = 'flex';
                    document.getElementById('statAcc').textContent = (data.accuracy * 100).toFixed(1) + '%';
                    document.getElementById('statTop5').textContent = (data.top5_accuracy * 100).toFixed(1) + '%';
                    document.getElementById('statVocab').textContent = data.vocab_size;
                    document.getElementById('statMem').textContent = data.memory_kb.toFixed(0);
                } else {
                    document.getElementById('status').textContent = 'Error: ' + data.error;
                }
            } catch (e) {
                document.getElementById('status').textContent = 'Error: ' + e.message;
            }
        }

        async function generate() {
            const prompt = document.getElementById('prompt').value;
            const tokens = parseInt(document.getElementById('tokens').value);
            const strategy = document.getElementById('strategy').value;
            const temp = parseFloat(document.getElementById('temp').value);
            
            document.getElementById('output').value = 'Generando...';
            
            try {
                const res = await fetch('/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({prompt, max_tokens: tokens, strategy, temperature: temp})
                });
                const data = await res.json();
                
                if (data.success) {
                    document.getElementById('output').value = data.text;
                } else {
                    document.getElementById('output').value = 'Error: ' + data.error;
                }
            } catch (e) {
                document.getElementById('output').value = 'Error: ' + e.message;
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/train', methods=['POST'])
def train():
    global model
    try:
        data = request.json
        dataset = data.get('dataset', 'filosofia')
        neurons = data.get('neurons', 256)
        
        text = TRAINING_TEXTS.get(dataset, TRAINING_TEXTS['filosofia'])
        
        model = TinyLMv2(n_reservoir=neurons, vocab_size=200, embedding_dim=32)
        stats = model.train(text, epochs=3, washout=30)
        
        model_stats = model.get_stats()
        
        return jsonify({
            'success': True,
            'accuracy': stats['accuracy'],
            'top5_accuracy': stats['top5_accuracy'],
            'vocab_size': stats['vocab_size'],
            'memory_kb': model_stats['memory_kb']
        })
    except (ValueError, KeyError, TypeError, np.linalg.LinAlgError) as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/generate', methods=['POST'])
def generate_text():
    global model
    try:
        if model is None or not model.is_trained:
            return jsonify({'success': False, 'error': 'Modelo no entrenado'})
        
        data = request.json
        prompt = data.get('prompt', '')
        max_tokens = data.get('max_tokens', 20)
        strategy = data.get('strategy', 'greedy')
        temperature = data.get('temperature', 0.5)
        
        text = model.generate(
            prompt, 
            max_tokens=max_tokens, 
            strategy=strategy,
            temperature=temperature,
            top_k=5
        )
        
        return jsonify({'success': True, 'text': text})
    except (ValueError, KeyError, IndexError, TypeError) as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════════╗
║              PROYECTO EÓN - TinyLM v2 Web                     ║
║              http://localhost:5001                            ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=5001, debug=False)
