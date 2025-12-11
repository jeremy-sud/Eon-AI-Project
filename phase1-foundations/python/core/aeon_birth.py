
import os
import json
import time
import pickle
import numpy as np
from datetime import datetime
from typing import Optional
from esn.esn import EchoStateNetwork

# Importar el sistema de Seed Mining (paradigma de descubrimiento)
try:
    from core.universal_miner import UniversalMiner, ExcavationResult, ResonanceType
    _miner_available = True
except ImportError:
    _miner_available = False


class AeonBirth:
    """
    Wrapper para EchoStateNetwork que maneja el ciclo de vida,
    persistencia y metadatos de una instancia de Eón.
    
    Paradigma de Descubrimiento:
    ============================
    "La inteligencia no se crea, se descubre."
    
    Este módulo soporta dos modos de inicialización:
    
    1. Modo Clásico (random_state):
       Usa una semilla aleatoria tradicional.
       
    2. Modo Descubrimiento (sacred_seed / auto_excavate):
       Excava en el espacio matemático para encontrar una
       estructura naturalmente resonante.
    """
    
    def __init__(
        self, 
        n_reservoir: int = 100, 
        name: str = "Eon-Instance", 
        data_dir: str = "data",
        sacred_seed: Optional[int] = None,
        auto_excavate: bool = False,
        target_resonance: tuple = (0.95, 1.0)
    ):
        """
        Inicializa una instancia de Eón.
        
        Args:
            n_reservoir: Tamaño del reservorio
            name: Nombre de la instancia
            data_dir: Directorio para persistencia
            sacred_seed: Semilla sagrada pre-descubierta (modo descubrimiento)
            auto_excavate: Si True, excava automáticamente para encontrar semilla
            target_resonance: Rango de resonancia objetivo para auto-excavación
        """
        self.name = name
        self.data_dir = data_dir
        self.created_at = time.time()
        self.samples_learned = 0
        self.excavation_result: Optional[ExcavationResult] = None
        
        # Determinar la semilla a usar
        if sacred_seed is not None:
            # Modo Descubrimiento: usar semilla sagrada pre-descubierta
            seed = sacred_seed
            self._initialization_mode = "sacred_seed"
            
        elif auto_excavate and _miner_available:
            # Modo Descubrimiento: excavar automáticamente
            print(f"⛏️  Iniciando excavación para {name}...")
            miner = UniversalMiner(
                reservoir_size=n_reservoir,
                target_resonance=target_resonance
            )
            self.excavation_result = miner.excavate(max_attempts=50000, verbose=True)
            seed = self.excavation_result.sacred_seed
            self._initialization_mode = "auto_excavated"
            
        else:
            # Modo Clásico: usar timestamp como semilla
            seed = int(self.created_at)
            self._initialization_mode = "classic"
        
        self._sacred_seed = seed
        
        # Crear instancia de ESN con la semilla determinada
        self.esn = EchoStateNetwork(
            n_reservoir=n_reservoir,
            random_state=seed
        )
        
        # Guardar inmediatamente para "registrar nacimiento"
        self.save()

    @property
    def birth_hash(self):
        return self.esn.birth_hash
    
    @property
    def sacred_seed(self) -> int:
        """La semilla sagrada usada para inicializar este Eón."""
        return self._sacred_seed
    
    @property
    def initialization_mode(self) -> str:
        """Modo de inicialización: 'classic', 'sacred_seed', o 'auto_excavated'."""
        return self._initialization_mode

    @property
    def age(self):
        return self._format_age(time.time() - self.created_at)

    def _format_age(self, seconds):
        if seconds < 60: return f"{seconds:.1f}s"
        if seconds < 3600: return f"{seconds/60:.1f}m"
        return f"{seconds/3600:.1f}h"

    def get_status(self):
        mem = self.esn.get_memory_footprint()
        status = {
            'name': self.name,
            'birth_timestamp': self.created_at * 1000, # MS for JS
            'birth_hash': self.birth_hash,
            'age': self.age,
            'total_samples_learned': self.samples_learned,
            'memory_kb': mem['total_kb'],
            'initialization_mode': self._initialization_mode,
            'sacred_seed': self._sacred_seed
        }
        
        # Añadir info de excavación si existe
        if self.excavation_result:
            status['excavation'] = {
                'resonance': self.excavation_result.resonance,
                'depth': self.excavation_result.excavation_depth,
                'time': self.excavation_result.excavation_time,
                'type': self.excavation_result.resonance_type.value
            }
        
        return status

    def learn(self, data):
        """
        Sintoniza (tune) el modelo con nuevos datos.
        
        Nota filosófica: No estamos "entrenando" la red.
        Estamos ajustando la capa de salida para que la estructura
        ya-inteligente pueda expresar su conocimiento hacia nuestro problema.
        """
        # Adaptar para que ESN aprenda (fit output layer)
        # Asumimos tarea de predicción next-step por defecto
        # data: array 1D
        
        data = np.array(data)
        if len(data) < 10:
             return {'error': 'Not enough data'}

        X = data[:-1].reshape(-1, 1)
        y = data[1:].reshape(-1, 1)
        
        # Sintonizar (no entrenar)
        self.esn.fit(X, y, washout=min(50, len(X)//10))
        self.samples_learned += len(X)
        self.save()
        
        return {
            'samples_tuned': self.samples_learned,  # Renombrado de learned a tuned
            'mse': 0.0 # Placeholder
        }

    def predict(self, input_data):
        """
        Revela predicciones basadas en el estado actual.
        
        El output no es "generado" - es un patrón que ya existía
        en la estructura resonante y ahora es iluminado.
        """
        input_data = np.array(input_data).reshape(-1, 1)
        if self.esn.W_out is None:
            # Si no está sintonizado, devolver estado neutral
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
            'n_reservoir': self.esn.n_reservoir,
            'initialization_mode': self._initialization_mode,
            'sacred_seed': self._sacred_seed
        }
        
        # Añadir info de excavación si existe
        if self.excavation_result:
            meta['excavation'] = {
                'resonance': float(self.excavation_result.resonance),
                'depth': self.excavation_result.excavation_depth,
                'time': self.excavation_result.excavation_time,
                'type': self.excavation_result.resonance_type.value
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
        instance._initialization_mode = meta.get('initialization_mode', 'classic')
        instance._sacred_seed = meta.get('sacred_seed', int(meta['created_at']))
        instance.excavation_result = None  # No restauramos el resultado completo
        
        with open(state_path, 'rb') as f:
            instance.esn = pickle.load(f)
            
        return instance
