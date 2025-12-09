
import os
import json
import time
import pickle
import numpy as np
from datetime import datetime
from esn.esn import EchoStateNetwork

class AeonBirth:
    """
    Wrapper para EchoStateNetwork que maneja el ciclo de vida,
    persistencia y metadatos de una instancia de Eón.
    """
    
    def __init__(self, n_reservoir=100, name="Eon-Instance", data_dir="data"):
        self.name = name
        self.data_dir = data_dir
        self.created_at = time.time()
        self.samples_learned = 0
        
        # Crear instancia de ESN
        self.esn = EchoStateNetwork(
            n_reservoir=n_reservoir,
            random_state=int(self.created_at)
        )
        
        # Guardar inmediatamente para "registrar nacimiento"
        self.save()

    @property
    def birth_hash(self):
        return self.esn.birth_hash

    @property
    def age(self):
        return self._format_age(time.time() - self.created_at)

    def _format_age(self, seconds):
        if seconds < 60: return f"{seconds:.1f}s"
        if seconds < 3600: return f"{seconds/60:.1f}m"
        return f"{seconds/3600:.1f}h"

    def get_status(self):
        mem = self.esn.get_memory_footprint()
        return {
            'name': self.name,
            'birth_timestamp': self.created_at * 1000, # MS for JS
            'birth_hash': self.birth_hash,
            'age': self.age,
            'total_samples_learned': self.samples_learned,
            'memory_kb': mem['total_kb']
        }

    def learn(self, data):
        # Adaptar para que ESN aprenda (fit output layer)
        # Asumimos tarea de predicción next-step por defecto
        # data: array 1D
        
        data = np.array(data)
        if len(data) < 10:
             return {'error': 'Not enough data'}

        X = data[:-1].reshape(-1, 1)
        y = data[1:].reshape(-1, 1)
        
        # Entrenar
        self.esn.fit(X, y, washout=min(50, len(X)//10))
        self.samples_learned += len(X)
        self.save()
        
        return {
            'samples_learned': self.samples_learned,
            'mse': 0.0 # Placeholder, calculating MSE on train requires predict
        }

    def predict(self, input_data):
        input_data = np.array(input_data).reshape(-1, 1)
        if self.esn.W_out is None:
            # Si no está entrenado, respuestas aleatorias o error
            # Para la demo, devolvemos ruido suave o ceros
            return np.zeros(len(input_data))
            
        return self.esn.predict(input_data).flatten()

    def save(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        safe_name = "".join(x for x in self.name if x.isalnum() or x in "-_")
        path = os.path.join(self.data_dir, f"{safe_name}_birth.json")
        state_path = os.path.join(self.data_dir, f"{safe_name}_state.pkl")
        
        # Guardar metadata JSON
        meta = {
            'name': self.name,
            'created_at': self.created_at,
            'samples_learned': self.samples_learned,
            'n_reservoir': self.esn.n_reservoir
        }
        with open(path, 'w') as f:
            json.dump(meta, f, indent=2)
            
        # Guardar objeto ESN completo (pickle por simplicidad en prototipo)
        with open(state_path, 'wb') as f:
            pickle.dump(self.esn, f)

    @classmethod
    def load(cls, name, data_dir):
        safe_name = "".join(x for x in name if x.isalnum() or x in "-_")
        path = os.path.join(data_dir, f"{safe_name}_birth.json")
        state_path = os.path.join(data_dir, f"{safe_name}_state.pkl")
        
        if not os.path.exists(path) or not os.path.exists(state_path):
            raise FileNotFoundError(f"Instance {name} not found")
            
        with open(path, 'r') as f:
            meta = json.load(f)
            
        # Crear instancia vacía
        instance = cls.__new__(cls)
        instance.name = meta['name']
        instance.created_at = meta['created_at']
        instance.samples_learned = meta.get('samples_learned', 0)
        instance.data_dir = data_dir
        
        with open(state_path, 'rb') as f:
            instance.esn = pickle.load(f)
            
        return instance
