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
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np

# Path del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "phase1-foundations" / "python"))

from esn.esn import EchoStateNetwork
from egregore import EgregorProcessor, EgregorState, NodeSensorData, EgregorMood


# =============================================================================
# SISTEMA DE VOLUNTAD VERDADERA (THELEMA)
# =============================================================================
# "Hacer tu Voluntad será el todo de la Ley"
# Cada nodo tiene una órbita única y no debe desviarse de ella.
# =============================================================================

class DataDomain(Enum):
    """Dominios de datos que un nodo puede procesar."""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    AUDIO = "audio"
    MOTION = "motion"
    LIGHT = "light"
    PRESSURE = "pressure"
    VIBRATION = "vibration"
    VOLTAGE = "voltage"
    TIMESERIES = "timeseries"
    GENERIC = "generic"


class TrueWillVector:
    """
    Vector de Voluntad Verdadera (Thelema).
    
    Cada nodo desarrolla una "Voluntad" basada en:
    - Lo que nació procesando (genesis domain)
    - Lo que ha aprendido mejor (experiencia)
    - Su inercia hacia ciertos tipos de datos
    
    La Voluntad determina qué tareas acepta/rechaza.
    
    Filosofía:
    ---------
    "Cada estrella tiene su órbita. No hay colisión si cada una
    sigue su camino. La fricción del sistema se minimiza cuando
    cada nodo hace SOLO lo que nació para hacer."
    
    Implementación:
    --------------
    - affinity[domain] ∈ [0, 1]: Afinidad hacia un dominio
    - inertia: Resistencia a cambiar de dominio
    - cost_function: Penalización por tareas fuera de voluntad
    """
    
    def __init__(self, genesis_domain: DataDomain = DataDomain.GENERIC):
        """
        Args:
            genesis_domain: Dominio inicial/nativo del nodo
        """
        self.genesis_domain = genesis_domain
        
        # Afinidad por cada dominio [0-1]
        # El dominio genesis comienza con afinidad máxima
        self.affinity: Dict[DataDomain, float] = {
            domain: 0.1 for domain in DataDomain
        }
        self.affinity[genesis_domain] = 1.0
        
        # Inercia: resistencia al cambio (aumenta con experiencia)
        self.inertia: float = 0.5
        
        # Historial de procesamiento por dominio
        self.processing_history: Dict[DataDomain, int] = {
            domain: 0 for domain in DataDomain
        }
        self.processing_history[genesis_domain] = 1
        
        # Métricas de éxito por dominio (MSE promedio)
        self.success_metrics: Dict[DataDomain, List[float]] = {
            domain: [] for domain in DataDomain
        }
        
        # Umbrales de rechazo
        self.rejection_threshold: float = 0.3  # Rechaza si afinidad < esto
        self.high_cost_threshold: float = 0.5  # Costo alto si afinidad < esto
    
    def calculate_true_will_vector(self) -> Dict[str, float]:
        """
        Calcula el vector de Voluntad Verdadera normalizado.
        
        Retorna un diccionario con la "fuerza de voluntad" hacia cada dominio.
        La suma de todos los valores = 1.0
        
        Returns:
            Dict[domain_name, will_strength]
        """
        # Combinar afinidad con experiencia
        will_vector = {}
        total = 0.0
        
        for domain in DataDomain:
            # Experiencia normalizada
            total_processing = sum(self.processing_history.values())
            experience = self.processing_history[domain] / max(1, total_processing)
            
            # Éxito promedio (menor MSE = mayor éxito)
            if self.success_metrics[domain]:
                avg_mse = np.mean(self.success_metrics[domain][-10:])  # Últimos 10
                success = 1.0 / (1.0 + avg_mse)  # Inversamente proporcional
            else:
                success = 0.5 if domain == self.genesis_domain else 0.1
            
            # Voluntad = afinidad * (1 + experiencia) * éxito
            will = self.affinity[domain] * (1 + experience) * success
            will_vector[domain.value] = will
            total += will
        
        # Normalizar
        if total > 0:
            for key in will_vector:
                will_vector[key] /= total
        
        return will_vector
    
    def evaluate_task_cost(self, requested_domain: DataDomain) -> Tuple[float, str]:
        """
        Evalúa el costo de procesar una tarea en un dominio específico.
        
        Retorna:
        - cost: 0.0 (alineado) a 1.0 (máxima resistencia)
        - decision: "accept", "high_priority", "low_priority", "reject"
        
        Args:
            requested_domain: Dominio de la tarea solicitada
            
        Returns:
            (cost, decision)
        """
        affinity = self.affinity[requested_domain]
        
        # Costo base inversamente proporcional a afinidad
        base_cost = 1.0 - affinity
        
        # Modificar por inercia (nodos con mucha inercia resisten más)
        adjusted_cost = base_cost * (1 + self.inertia)
        adjusted_cost = min(1.0, adjusted_cost)
        
        # Determinar decisión
        if affinity >= self.high_cost_threshold:
            decision = "accept" if affinity >= 0.8 else "high_priority"
        elif affinity >= self.rejection_threshold:
            decision = "low_priority"
        else:
            decision = "reject"
        
        return adjusted_cost, decision
    
    def should_accept_task(self, requested_domain: DataDomain) -> bool:
        """
        Decisión binaria: ¿debería este nodo aceptar esta tarea?
        
        Basado en el principio Thelemático: "Cada estrella en su órbita."
        Un nodo no debe desviarse de su Voluntad Verdadera.
        """
        _, decision = self.evaluate_task_cost(requested_domain)
        return decision != "reject"
    
    def record_processing(self, domain: DataDomain, mse: float) -> None:
        """
        Registra el procesamiento de datos en un dominio.
        
        Esto actualiza la afinidad y experiencia del nodo.
        
        Args:
            domain: Dominio procesado
            mse: Error cuadrático medio del procesamiento
        """
        # Incrementar experiencia
        self.processing_history[domain] += 1
        
        # Registrar métrica de éxito
        self.success_metrics[domain].append(mse)
        
        # Actualizar afinidad basada en éxito
        if mse < 0.1:  # Muy exitoso
            self.affinity[domain] = min(1.0, self.affinity[domain] + 0.05)
        elif mse < 0.3:  # Aceptable
            self.affinity[domain] = min(1.0, self.affinity[domain] + 0.02)
        elif mse > 0.7:  # Malo - reducir afinidad
            self.affinity[domain] = max(0.0, self.affinity[domain] - 0.03)
        
        # Aumentar inercia con experiencia total
        total_exp = sum(self.processing_history.values())
        self.inertia = min(0.95, 0.5 + (total_exp / 1000))
    
    def get_specialization(self) -> Tuple[DataDomain, float]:
        """
        Retorna el dominio de especialización del nodo y su nivel.
        
        Returns:
            (domain, specialization_level)
        """
        max_affinity = 0.0
        specialized_domain = self.genesis_domain
        
        for domain, affinity in self.affinity.items():
            if affinity > max_affinity:
                max_affinity = affinity
                specialized_domain = domain
        
        return specialized_domain, max_affinity
    
    def export_will(self) -> Dict:
        """Exporta el vector de voluntad para sincronización."""
        return {
            'genesis_domain': self.genesis_domain.value,
            'affinity': {d.value: v for d, v in self.affinity.items()},
            'inertia': self.inertia,
            'will_vector': self.calculate_true_will_vector(),
            'specialization': {
                'domain': self.get_specialization()[0].value,
                'level': self.get_specialization()[1]
            },
            'processing_history': {d.value: v for d, v in self.processing_history.items()}
        }


class AeonNode:
    """
    Un nodo de la Mente Colectiva.
    
    Cada nodo puede:
    - Aprender localmente
    - Exportar sus pesos W_out
    - Importar pesos de otros nodos
    - Mezclar conocimiento (promedio ponderado)
    - Calcular su Voluntad Verdadera (Thelema)
    - Aceptar/rechazar tareas según su especialización
    """
    
    def __init__(self, node_id: str = None, n_reservoir: int = 32,
                 genesis_domain: DataDomain = DataDomain.GENERIC):
        """
        Args:
            node_id: Identificador único (auto-generado si None)
            n_reservoir: Tamaño del reservoir
            genesis_domain: Dominio nativo del nodo (para Thelema)
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
        
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.samples_learned = 0
        self.sync_count = 0
        self.last_sync = None
        self.peers: List[str] = []
        
        # Sistema de Voluntad Verdadera (Thelema)
        self.true_will = TrueWillVector(genesis_domain)
        
    def _generate_id(self) -> str:
        """Genera ID único basado en timestamp + random."""
        rng = np.random.default_rng(int(time.time() * 1000) % (2**32))
        data = f"{time.time()}-{rng.random()}"
        return hashlib.sha256(data.encode()).hexdigest()[:12]
    
    def train(self, data: np.ndarray, washout: int = 20,
              domain: DataDomain = DataDomain.TIMESERIES) -> float:
        """
        Entrena localmente con datos.
        
        Args:
            data: Serie temporal 1D
            washout: Muestras a descartar
            domain: Dominio de los datos (para Thelema)
            
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
        
        # Registrar en sistema Thelema
        self.true_will.record_processing(domain, float(mse))
        
        return float(mse)
    
    def evaluate_task(self, domain: DataDomain) -> Tuple[bool, float, str]:
        """
        Evalúa si este nodo debería aceptar una tarea en un dominio específico.
        
        Implementa el principio de "Voluntad Verdadera" (Thelema):
        - Si la tarea está alineada con la Voluntad del nodo → acepta
        - Si está desalineada → rechaza o baja prioridad
        
        Args:
            domain: Dominio de la tarea solicitada
            
        Returns:
            (should_accept, cost, decision)
        """
        cost, decision = self.true_will.evaluate_task_cost(domain)
        should_accept = self.true_will.should_accept_task(domain)
        return should_accept, cost, decision
    
    def calculate_true_will_vector(self) -> Dict[str, float]:
        """
        Calcula el vector de Voluntad Verdadera del nodo.
        
        Este vector representa la "órbita natural" del nodo:
        qué tipos de datos procesa mejor y debería seguir procesando.
        
        Returns:
            Dict con fuerza de voluntad por dominio (suma = 1.0)
        """
        return self.true_will.calculate_true_will_vector()
    
    def get_specialization(self) -> Tuple[str, float]:
        """Retorna el dominio de especialización y su nivel."""
        domain, level = self.true_will.get_specialization()
        return domain.value, level
    
    def predict(self, input_value: float) -> float:
        """Predice siguiente valor."""
        input_arr = np.array([[input_value]])
        return float(self.esn.predict(input_arr)[0, 0])
    
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
            'timestamp': datetime.now(timezone.utc).isoformat(),
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
        self.last_sync = datetime.now(timezone.utc).isoformat()
        
        if weights_data['node_id'] not in self.peers:
            self.peers.append(weights_data['node_id'])
        
        return True
    
    def status(self) -> Dict:
        """Estado actual del nodo, incluyendo Voluntad Verdadera."""
        spec_domain, spec_level = self.get_specialization()
        return {
            'node_id': self.node_id,
            'created_at': self.created_at,
            'n_reservoir': self.n_reservoir,
            'samples_learned': self.samples_learned,
            'sync_count': self.sync_count,
            'last_sync': self.last_sync,
            'peers_count': len(self.peers),
            'peers': self.peers,
            # Thelema: Voluntad Verdadera
            'true_will': {
                'genesis_domain': self.true_will.genesis_domain.value,
                'specialization': spec_domain,
                'specialization_level': spec_level,
                'inertia': self.true_will.inertia,
                'will_vector': self.calculate_true_will_vector()
            }
        }
    
    def export_weights_1bit(self, scale: float = 0.5) -> Dict:
        """
        Exporta pesos W_out con cuantización 1-bit (Protocolo Eón).
        
        Solo se transmite el signo de cada peso, logrando compresión 17x.
        
        Args:
            scale: Magnitud para reconstrucción (default: 0.5)
            
        Returns:
            dict con metadatos y payload binario
        """
        w_out = self.esn.W_out.flatten()
        
        # Cuantizar a 1-bit (solo signos)
        n_weights = len(w_out)
        n_bytes = (n_weights + 7) // 8
        payload = bytearray(n_bytes)
        
        for i, w in enumerate(w_out):
            if w >= 0:
                byte_idx = i // 8
                bit_idx = i % 8
                payload[byte_idx] |= (1 << bit_idx)
        
        # Construir paquete según protocolo
        return {
            'magic': 'EON',
            'type': 0x01,  # W_OUT_UPDATE
            'seed': hash(self.node_id) & 0xFFFFFFFF,
            'count': n_weights,
            'scale': scale,
            'payload': bytes(payload),
            'node_id': self.node_id,
            'samples_learned': self.samples_learned,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            # Estadísticas de compresión
            'original_bytes': n_weights * 4,  # float32
            'compressed_bytes': n_bytes + 10,  # payload + header
            'compression_ratio': (n_weights * 4) / (n_bytes + 10)
        }
    
    def import_weights_1bit(self, packet: Dict, merge_ratio: float = 0.5) -> bool:
        """
        Importa pesos cuantizados 1-bit y los mezcla con los locales.
        
        Args:
            packet: Paquete del export_weights_1bit
            merge_ratio: Peso del conocimiento externo (0-1)
            
        Returns:
            True si éxito
        """
        if packet.get('magic') != 'EON':
            raise ValueError("Paquete inválido: magic incorrecto")
        
        n_weights = packet['count']
        scale = packet.get('scale', 0.5)
        payload = packet['payload']
        
        # Verificar tamaño
        expected_bytes = (n_weights + 7) // 8
        if len(payload) != expected_bytes:
            raise ValueError(f"Payload size mismatch: {len(payload)} vs {expected_bytes}")
        
        # Dequantizar
        external_weights = np.zeros(n_weights)
        for i in range(n_weights):
            byte_idx = i // 8
            bit_idx = i % 8
            if payload[byte_idx] & (1 << bit_idx):
                external_weights[i] = scale
            else:
                external_weights[i] = -scale
        
        # Reshape para coincidir con W_out
        external_weights = external_weights.reshape(self.esn.W_out.shape)
        
        # Mezclar
        self.esn.W_out = (
            self.esn.W_out * (1 - merge_ratio) +
            external_weights * merge_ratio
        )
        
        self.sync_count += 1
        self.last_sync = datetime.now(timezone.utc).isoformat()
        
        if packet.get('node_id') and packet['node_id'] not in self.peers:
            self.peers.append(packet['node_id'])
        
        return True
    
    # =========================================================================
    # INTEGRACIÓN CON EGRÉGOR (Mente Grupal)
    # =========================================================================
    
    def generate_sensor_data(
        self, 
        temperature: Optional[float] = None,
        noise_level: Optional[float] = None,
        motion_intensity: Optional[float] = None,
        light_level: Optional[float] = None
    ) -> NodeSensorData:
        """
        Genera datos del sensor para reportar al Egrégor.
        
        Combina métricas externas (sensores físicos) con métricas
        internas del nodo (carga, error, alineación con Will).
        
        Args:
            temperature: Temperatura ambiente (°C)
            noise_level: Nivel de ruido (0-1)
            motion_intensity: Intensidad de movimiento (0-1)
            light_level: Nivel de luz (0-1)
            
        Returns:
            NodeSensorData para el EgregorProcessor
        """
        # Calcular métricas internas
        _, spec_level = self.get_specialization()
        
        # Error de predicción reciente (de las métricas de Thelema)
        recent_errors = self.true_will.success_metrics.get(
            self.true_will.genesis_domain, []
        )
        avg_error = float(np.mean(recent_errors[-5:])) if recent_errors else 0.1
        
        return NodeSensorData(
            node_id=self.node_id,
            timestamp=time.time(),
            temperature=temperature,
            noise_level=noise_level,
            motion_intensity=motion_intensity,
            light_level=light_level,
            processing_load=min(1.0, self.samples_learned / 10000),
            sample_rate=1.0,  # Se ajusta por Egrégor
            prediction_error=avg_error,
            will_alignment=spec_level,
        )
    
    def apply_egregore_recommendations(self, state: EgregorState) -> Dict:
        """
        Aplica las recomendaciones homeostáticas del Egrégor.
        
        Implementa el feedback loop: cuando el Egrégor está "Agitado",
        el nodo reduce su actividad para "calmar" al sistema.
        
        Args:
            state: Estado actual del Egrégor
            
        Returns:
            Dict con las acciones tomadas
        """
        actions_taken = {
            "sample_rate_adjusted": False,
            "merge_ratio_adjusted": False,
            "activity_reduced": False,
            "activity_increased": False,
        }
        
        recommendations = state.get_homeostatic_actions()
        
        # Ajustar ratio de mezcla (afecta import_weights)
        # Aplicar ratio de mezcla del Egrégor
        self._egregore_merge_ratio = recommendations["adjust_merge_ratio"]
        actions_taken["merge_ratio_adjusted"] = True
        
        # Responder a recomendaciones de actividad
        if recommendations["should_reduce_activity"]:
            # El nodo puede pausar procesamiento no crítico
            actions_taken["activity_reduced"] = True
        
        if recommendations["should_increase_activity"]:
            actions_taken["activity_increased"] = True
        
        actions_taken["sample_rate_adjusted"] = True
        actions_taken["recommended_rate"] = recommendations["adjust_sample_rate"]
        
        return actions_taken


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
            'timestamp': datetime.now(timezone.utc).isoformat(),
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


class EgregorCoordinator:
    """
    Coordinador del Egrégor para la Mente Colectiva.
    
    Integra el EgregorProcessor con CollectiveMind para crear
    un sistema de feedback homeostático completo.
    
    Arquitectura:
        Nodos ──┐
                ├──→ EgregorProcessor ──→ EgregorState
                │           ↓
        Nodos ──┘    Broadcast MQTT
                          ↓
                Todos los nodos ajustan comportamiento
    """
    
    def __init__(self, collective_mind: CollectiveMind):
        """
        Args:
            collective_mind: Instancia de CollectiveMind a coordinar
        """
        self.mind = collective_mind
        self.processor = EgregorProcessor(decay_time=30.0)
        
        # Historial de estados para análisis
        self.state_history: List[Dict] = []
        self.max_history = 1000
        
        # Callbacks para notificar cambios de estado
        self.processor.register_callback(self._on_state_change)
    
    def _on_state_change(self, new_state: EgregorState) -> None:
        """Callback cuando el estado del Egrégor cambia significativamente."""
        self.state_history.append({
            "timestamp": new_state.timestamp,
            "mood": new_state.mood.value,
            "energy": new_state.energy_level,
            "coherence": new_state.coherence,
        })
        
        if len(self.state_history) > self.max_history:
            self.state_history = self.state_history[-self.max_history:]
    
    def collect_and_process(
        self,
        external_sensors: Optional[Dict[str, Dict]] = None
    ) -> EgregorState:
        """
        Recolecta datos de todos los nodos y procesa el estado del Egrégor.
        
        Args:
            external_sensors: Dict opcional con datos de sensores externos
                             por node_id: {"temperature": 25, "noise": 0.3, ...}
        
        Returns:
            Estado actual del Egrégor
        """
        external_sensors = external_sensors or {}
        
        # Recolectar datos de cada nodo
        for node_id, node in self.mind.nodes.items():
            ext = external_sensors.get(node_id, {})
            
            sensor_data = node.generate_sensor_data(
                temperature=ext.get("temperature"),
                noise_level=ext.get("noise_level"),
                motion_intensity=ext.get("motion_intensity"),
                light_level=ext.get("light_level"),
            )
            
            self.processor.update_node_data(sensor_data)
        
        # Procesar y obtener nuevo estado
        return self.processor.process()
    
    def apply_homeostasis(self) -> Dict[str, Dict]:
        """
        Aplica las recomendaciones del Egrégor a todos los nodos.
        
        Implementa el feedback loop completo:
        Estado Egrégor → Recomendaciones → Ajuste de Nodos
        
        Returns:
            Dict con acciones tomadas por cada nodo
        """
        state = self.processor.get_state()
        results = {}
        
        for node_id, node in self.mind.nodes.items():
            actions = node.apply_egregore_recommendations(state)
            results[node_id] = actions
        
        return results
    
    def get_egregore_state(self) -> EgregorState:
        """Retorna el estado actual del Egrégor sin procesar."""
        return self.processor.get_state()
    
    def get_summary(self) -> str:
        """Resumen del estado del Egrégor y la mente colectiva."""
        state = self.processor.get_state()
        mind_status = self.mind.global_status()
        
        return (
            f"═══ EGRÉGOR + MENTE COLECTIVA ═══\n"
            f"Estado: {state.mood.value.upper()}\n"
            f"Nodos activos: {state.node_count}\n"
            f"Energía: {state.energy_level:.1%}\n"
            f"Coherencia: {state.coherence:.1%}\n"
            f"Estabilidad: {state.stability:.1%}\n"
            f"───────────────────────────────\n"
            f"Muestras totales: {mind_status['total_samples']}\n"
            f"Sincronizaciones: {mind_status['total_syncs']}\n"
            f"───────────────────────────────\n"
            f"→ Sample Rate: {state.recommended_sample_rate:.1f} Hz\n"
            f"→ Merge Ratio: {state.recommended_merge_ratio:.1%}"
        )
    
    def generate_mqtt_payload(self) -> Dict:
        """
        Genera payload para publicar el estado del Egrégor via MQTT.
        
        Topic sugerido: eon/egregore/state
        
        Returns:
            Dict serializable para MQTT
        """
        state = self.processor.get_state()
        return {
            "type": "EGREGORE_STATE",
            "version": 1,
            **state.to_dict()
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
    rng = np.random.default_rng(42)
    
    # Cocina: mayor temperatura base
    data_cocina = 25 + 3 * np.sin(np.linspace(0, 4*np.pi, 200)) + rng.normal(0, 0.5, 200)
    mse_a = node_a.train(data_cocina)
    print(f"      Cocina: MSE = {mse_a:.6f}")
    
    # Sala: temperatura intermedia
    data_sala = 22 + 2 * np.sin(np.linspace(0, 4*np.pi, 200)) + rng.normal(0, 0.3, 200)
    mse_b = node_b.train(data_sala)
    print(f"      Sala: MSE = {mse_b:.6f}")
    
    # Exterior: más variación
    data_exterior = 18 + 8 * np.sin(np.linspace(0, 4*np.pi, 200)) + rng.normal(0, 1.0, 200)
    mse_c = node_c.train(data_exterior)
    print(f"      Exterior: MSE = {mse_c:.6f}")
    
    print("\n[3/4] Sincronizando conocimiento...")
    
    # Cocina y Sala intercambian
    result = mind.sync_pair("sensor-cocina", "sensor-sala", bidirectional=True, merge_ratio=0.3)
    print(f"      ✓ {result['node_a']} <-> {result['node_b']}")
    
    # Exterior comparte con todos
    mind.broadcast_knowledge("sensor-exterior", merge_ratio=0.2)
    print("      ✓ sensor-exterior -> broadcast a todos")
    
    # === DEMO PROTOCOLO 1-BIT ===
    print("\n[5/6] Demostración Protocolo 1-Bit:")
    
    # Simular que sensor-cocina actualiza sus pesos y los transmite
    packet_1bit = node_a.export_weights_1bit(scale=0.5)
    
    print("      📡 SENSOR-COCINA exporta conocimiento:")
    print(f"         • Magic: {packet_1bit['magic']}")
    print(f"         • Tipo: W_OUT_UPDATE (0x{packet_1bit['type']:02x})")
    print(f"         • Pesos: {packet_1bit['count']}")
    print(f"         • Bytes originales: {packet_1bit['original_bytes']} (float32)")
    print(f"         • Bytes comprimidos: {packet_1bit['compressed_bytes']} (1-bit)")
    print(f"         • Ratio de compresión: {packet_1bit['compression_ratio']:.1f}x")
    
    # Simular transmisión por MQTT/LoRa (aquí es instantáneo)
    print("\n      📤 Transmitiendo via MQTT topic 'eon/hive/update'...")
    
    # sensor-sala recibe y fusiona
    print("      📥 SENSOR-SALA recibe paquete...")
    node_b.import_weights_1bit(packet_1bit, merge_ratio=0.4)
    print("         ✓ Pesos fusionados con ratio 0.4")
    print(f"         ✓ Syncs: {node_b.sync_count}, Peers: {node_b.peers}")
    
    # Verificar que el conocimiento se transfirió
    print("\n[6/6] Verificación de transferencia de conocimiento:")
    
    # Predecir con sensor-sala después de recibir conocimiento de cocina
    test_value = 24.0  # Temperatura típica de cocina
    pred_before = node_c.predict(test_value)  # exterior (no recibió 1-bit)
    pred_after = node_b.predict(test_value)   # sala (recibió 1-bit)
    
    print(f"      • Predicción SALA (con 1-bit): {pred_after:.4f}")
    print(f"      • Predicción EXTERIOR (sin 1-bit): {pred_before:.4f}")
    print(f"      • Diferencia: {abs(pred_after - pred_before):.4f}")
    
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
