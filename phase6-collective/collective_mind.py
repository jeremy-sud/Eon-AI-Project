"""
Proyecto Eón - Mente Colectiva
==============================

Sistema de aprendizaje federado ultra-ligero.
Múltiples nodos Eón comparten conocimiento sin centralizar datos.

Arquitectura:
    Nodo A (local) <---> API <---> Nodo B (remoto)
                         |
                   Coordinator
                         |
                    Nodo C ...

El conocimiento viaja como pesos W_out, no como datos raw.

(c) 2024 Sistemas Ursol - Jeremy Arias Solano
"""

import sys
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np

# Path del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "phase1-foundations" / "python"))

from esn.esn import EchoStateNetwork


class AeonNode:
    """
    Un nodo de la Mente Colectiva.
    
    Cada nodo puede:
    - Aprender localmente
    - Exportar sus pesos W_out
    - Importar pesos de otros nodos
    - Mezclar conocimiento (promedio ponderado)
    """
    
    def __init__(self, node_id: str = None, n_reservoir: int = 32):
        """
        Args:
            node_id: Identificador único (auto-generado si None)
            n_reservoir: Tamaño del reservoir
        """
        self.node_id = node_id or self._generate_id()
        self.n_reservoir = n_reservoir
        
        self.esn = EchoStateNetwork(
            n_inputs=1,
            n_outputs=1,
            n_reservoir=n_reservoir,
            spectral_radius=0.9,
            sparsity=0.85
        )
        
        self.created_at = datetime.utcnow().isoformat()
        self.samples_learned = 0
        self.sync_count = 0
        self.last_sync = None
        self.peers: List[str] = []
        
    def _generate_id(self) -> str:
        """Genera ID único basado en timestamp + random."""
        data = f"{time.time()}-{np.random.random()}"
        return hashlib.sha256(data.encode()).hexdigest()[:12]
    
    def train(self, data: np.ndarray, washout: int = 20) -> float:
        """
        Entrena localmente con datos.
        
        Args:
            data: Serie temporal 1D
            washout: Muestras a descartar
            
        Returns:
            MSE del entrenamiento
        """
        X = data[:-1].reshape(-1, 1)
        Y = data[1:].reshape(-1, 1)
        
        self.esn.fit(X, Y, washout=washout)
        self.samples_learned += len(data)
        
        # Calcular MSE
        predictions = self.esn.predict(X)
        mse = np.mean((predictions - Y) ** 2)
        
        return float(mse)
    
    def predict(self, input_value: float) -> float:
        """Predice siguiente valor."""
        self.esn.update(np.array([[input_value]]))
        return float(self.esn.predict(np.array([[input_value]]))[0, 0])
    
    def export_weights(self) -> Dict:
        """
        Exporta pesos W_out para compartir.
        
        Returns:
            dict con metadatos y pesos
        """
        return {
            'node_id': self.node_id,
            'n_reservoir': self.n_reservoir,
            'samples_learned': self.samples_learned,
            'timestamp': datetime.utcnow().isoformat(),
            'W_out': self.esn.W_out.tolist()
        }
    
    def import_weights(self, weights_data: Dict, merge_ratio: float = 0.5) -> bool:
        """
        Importa y mezcla pesos de otro nodo.
        
        Args:
            weights_data: dict del export_weights de otro nodo
            merge_ratio: Peso del conocimiento externo (0-1)
                        0 = ignorar externo, 1 = reemplazar totalmente
        
        Returns:
            True si éxito
        """
        if weights_data['n_reservoir'] != self.n_reservoir:
            raise ValueError(f"Tamaño de reservoir incompatible: "
                           f"{weights_data['n_reservoir']} vs {self.n_reservoir}")
        
        external_weights = np.array(weights_data['W_out'])
        
        # Mezclar: local * (1-ratio) + externo * ratio
        self.esn.W_out = (
            self.esn.W_out * (1 - merge_ratio) +
            external_weights * merge_ratio
        )
        
        self.sync_count += 1
        self.last_sync = datetime.utcnow().isoformat()
        
        if weights_data['node_id'] not in self.peers:
            self.peers.append(weights_data['node_id'])
        
        return True
    
    def status(self) -> Dict:
        """Estado actual del nodo."""
        return {
            'node_id': self.node_id,
            'created_at': self.created_at,
            'n_reservoir': self.n_reservoir,
            'samples_learned': self.samples_learned,
            'sync_count': self.sync_count,
            'last_sync': self.last_sync,
            'peers_count': len(self.peers),
            'peers': self.peers
        }


class CollectiveMind:
    """
    Coordinador de la Mente Colectiva.
    
    Gestiona múltiples nodos y facilita la sincronización.
    """
    
    def __init__(self):
        self.nodes: Dict[str, AeonNode] = {}
        self.sync_history: List[Dict] = []
        
    def create_node(self, node_id: str = None, n_reservoir: int = 32) -> AeonNode:
        """Crea y registra un nuevo nodo."""
        node = AeonNode(node_id, n_reservoir)
        self.nodes[node.node_id] = node
        return node
    
    def get_node(self, node_id: str) -> Optional[AeonNode]:
        """Obtiene un nodo por ID."""
        return self.nodes.get(node_id)
    
    def sync_pair(self, node_a_id: str, node_b_id: str, 
                  bidirectional: bool = True, merge_ratio: float = 0.3) -> Dict:
        """
        Sincroniza conocimiento entre dos nodos.
        
        Args:
            node_a_id: Primer nodo
            node_b_id: Segundo nodo
            bidirectional: Si True, ambos aprenden del otro
            merge_ratio: Peso del conocimiento externo
            
        Returns:
            dict con resultados de la sincronización
        """
        node_a = self.nodes.get(node_a_id)
        node_b = self.nodes.get(node_b_id)
        
        if not node_a or not node_b:
            raise ValueError("Nodo no encontrado")
        
        # A aprende de B
        weights_b = node_b.export_weights()
        node_a.import_weights(weights_b, merge_ratio)
        
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'node_a': node_a_id,
            'node_b': node_b_id,
            'direction': 'bidirectional' if bidirectional else 'a_from_b',
            'merge_ratio': merge_ratio
        }
        
        # B aprende de A (si bidireccional)
        if bidirectional:
            weights_a = node_a.export_weights()
            node_b.import_weights(weights_a, merge_ratio)
        
        self.sync_history.append(result)
        return result
    
    def broadcast_knowledge(self, source_id: str, merge_ratio: float = 0.2):
        """
        Un nodo comparte su conocimiento con todos los demás.
        
        Args:
            source_id: Nodo fuente
            merge_ratio: Peso del conocimiento
        """
        source = self.nodes.get(source_id)
        if not source:
            raise ValueError(f"Nodo {source_id} no encontrado")
        
        weights = source.export_weights()
        
        for node_id, node in self.nodes.items():
            if node_id != source_id:
                node.import_weights(weights, merge_ratio)
    
    def global_status(self) -> Dict:
        """Estado de toda la mente colectiva."""
        return {
            'total_nodes': len(self.nodes),
            'total_samples': sum(n.samples_learned for n in self.nodes.values()),
            'total_syncs': len(self.sync_history),
            'nodes': {nid: n.status() for nid, n in self.nodes.items()}
        }


# Demo
if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║           PROYECTO EÓN - MENTE COLECTIVA                      ║
║        "El conocimiento compartido sin datos centralizados"   ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Crear mente colectiva
    mind = CollectiveMind()
    
    print("[1/4] Creando 3 nodos...")
    node_a = mind.create_node("sensor-cocina", 32)
    node_b = mind.create_node("sensor-sala", 32)
    node_c = mind.create_node("sensor-exterior", 32)
    
    for nid in mind.nodes:
        print(f"      ✓ Nodo: {nid}")
    
    print("\n[2/4] Cada nodo aprende localmente...")
    
    # Simular datos diferentes por sensor
    np.random.seed(42)
    
    # Cocina: mayor temperatura base
    data_cocina = 25 + 3 * np.sin(np.linspace(0, 4*np.pi, 200)) + np.random.normal(0, 0.5, 200)
    mse_a = node_a.train(data_cocina)
    print(f"      Cocina: MSE = {mse_a:.6f}")
    
    # Sala: temperatura intermedia
    data_sala = 22 + 2 * np.sin(np.linspace(0, 4*np.pi, 200)) + np.random.normal(0, 0.3, 200)
    mse_b = node_b.train(data_sala)
    print(f"      Sala: MSE = {mse_b:.6f}")
    
    # Exterior: más variación
    data_exterior = 18 + 8 * np.sin(np.linspace(0, 4*np.pi, 200)) + np.random.normal(0, 1.0, 200)
    mse_c = node_c.train(data_exterior)
    print(f"      Exterior: MSE = {mse_c:.6f}")
    
    print("\n[3/4] Sincronizando conocimiento...")
    
    # Cocina y Sala intercambian
    result = mind.sync_pair("sensor-cocina", "sensor-sala", bidirectional=True, merge_ratio=0.3)
    print(f"      ✓ {result['node_a']} <-> {result['node_b']}")
    
    # Exterior comparte con todos
    mind.broadcast_knowledge("sensor-exterior", merge_ratio=0.2)
    print(f"      ✓ sensor-exterior -> broadcast a todos")
    
    print("\n[4/4] Estado de la Mente Colectiva:")
    status = mind.global_status()
    print(f"      • Nodos: {status['total_nodes']}")
    print(f"      • Muestras totales: {status['total_samples']}")
    print(f"      • Sincronizaciones: {status['total_syncs']}")
    
    for nid, nstatus in status['nodes'].items():
        print(f"\n      [{nid}]")
        print(f"        - Aprendió: {nstatus['samples_learned']} muestras")
        print(f"        - Syncs: {nstatus['sync_count']}")
        print(f"        - Peers: {nstatus['peers']}")
    
    print("\n✓ Mente Colectiva operativa")
    print("Proyecto Eón - Sistemas Ursol")
