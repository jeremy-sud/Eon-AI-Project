"""
Proyecto Eón - Sistema Egrégor (Mente Grupal)
=============================================

Implementación del concepto místico de Egrégor como una variable
de estado global emergente del colectivo de nodos Eón.

Concepto:
---------
Un Egrégor es una entidad psíquica autónoma creada por la suma
de pensamientos de un grupo. En nuestro contexto, es el "Estado
de Ánimo" emergente del sistema colectivo.

Arquitectura:
------------
    Nodo A ───┐
    Nodo B ───┼──→ EgregorProcessor ──→ EgregorState
    Nodo C ───┘           ↓
                    "Estado de Ánimo"
                          ↓
                Broadcast a todos los nodos
                          ↓
                Homeostasis Cibernética
                (nodos ajustan comportamiento)

"La suma es mayor que las partes" - Gestalt

(c) 2024 Sistemas Ursol - Jeremy Arias Solano
"""

import time
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
import numpy as np


class EgregorMood(Enum):
    """
    Estados de ánimo del Egrégor (Mente Colectiva).
    
    Cada estado representa una cualidad emergente del sistema.
    Los nombres reflejan la naturaleza mística del concepto.
    """
    # Estados de alta energía/actividad
    AGITATED = "agitated"       # Mucho ruido, calor, actividad
    ALERT = "alert"             # Actividad significativa, preparado
    DYNAMIC = "dynamic"         # Cambios frecuentes pero controlados
    
    # Estados neutros/transicionales
    BALANCED = "balanced"       # Equilibrio homeostático
    OBSERVANT = "observant"     # Atento pero sin acción
    
    # Estados de baja energía/calma
    CONTEMPLATIVE = "contemplative"  # Actividad baja, reflexivo
    MEDITATIVE = "meditative"   # Silencio y estabilidad profunda
    DORMANT = "dormant"         # Mínima actividad, casi inactivo
    
    # Estados especiales
    AWAKENING = "awakening"     # Transición de dormant a activo
    HARMONIZING = "harmonizing" # Proceso de sincronización activo


@dataclass
class NodeSensorData:
    """Datos de sensores de un nodo individual."""
    node_id: str
    timestamp: float
    
    # Métricas de actividad
    temperature: Optional[float] = None     # Celsius
    noise_level: Optional[float] = None     # dB o 0-1 normalizado
    motion_intensity: Optional[float] = None  # 0-1
    light_level: Optional[float] = None     # Lux o 0-1
    
    # Métricas del propio nodo
    processing_load: float = 0.0            # 0-1, carga CPU/memoria
    sample_rate: float = 1.0                # Hz, frecuencia de muestreo
    prediction_error: float = 0.0           # MSE reciente
    will_alignment: float = 1.0             # Alineación con True Will


@dataclass
class EgregorState:
    """
    Estado actual del Egrégor.
    
    Representa la "mente colectiva" como una variable de estado emergente.
    Ningún humano controla esto directamente - emerge de la suma vectorial
    de todos los estados de los nodos.
    """
    mood: EgregorMood = EgregorMood.BALANCED
    intensity: float = 0.5                  # 0-1, fuerza del estado
    confidence: float = 0.5                 # 0-1, certeza del estado
    
    # Vector de características emergentes
    energy_level: float = 0.5               # 0-1, energía colectiva
    coherence: float = 0.5                  # 0-1, sincronización entre nodos
    stability: float = 0.5                  # 0-1, estabilidad temporal
    entropy: float = 0.5                    # 0-1, caos/orden del sistema
    
    # Metadatos
    node_count: int = 0
    timestamp: float = field(default_factory=time.time)
    
    # Recomendaciones homeostáticas
    recommended_sample_rate: float = 1.0    # Hz sugerido para nodos
    recommended_merge_ratio: float = 0.5    # Ratio de mezcla sugerido
    
    def to_dict(self) -> Dict:
        """Serializa el estado para transmisión."""
        return {
            "mood": self.mood.value,
            "intensity": round(self.intensity, 3),
            "confidence": round(self.confidence, 3),
            "energy_level": round(self.energy_level, 3),
            "coherence": round(self.coherence, 3),
            "stability": round(self.stability, 3),
            "entropy": round(self.entropy, 3),
            "node_count": self.node_count,
            "timestamp": self.timestamp,
            "recommended_sample_rate": round(self.recommended_sample_rate, 2),
            "recommended_merge_ratio": round(self.recommended_merge_ratio, 2),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EgregorState":
        """Deserializa desde dict."""
        return cls(
            mood=EgregorMood(data["mood"]),
            intensity=data["intensity"],
            confidence=data["confidence"],
            energy_level=data["energy_level"],
            coherence=data["coherence"],
            stability=data["stability"],
            entropy=data["entropy"],
            node_count=data["node_count"],
            timestamp=data["timestamp"],
            recommended_sample_rate=data.get("recommended_sample_rate", 1.0),
            recommended_merge_ratio=data.get("recommended_merge_ratio", 0.5),
        )
    
    def get_homeostatic_actions(self) -> Dict[str, any]:
        """
        Genera acciones homeostáticas basadas en el estado actual.
        
        Implementa el feedback loop: el Egrégor "guía" a los nodos
        para mantener el equilibrio del sistema.
        """
        actions = {
            "adjust_sample_rate": self.recommended_sample_rate,
            "adjust_merge_ratio": self.recommended_merge_ratio,
            "should_reduce_activity": False,
            "should_increase_activity": False,
            "synchronization_pulse": False,
        }
        
        # Si el sistema está agitado, calmar
        if self.mood in [EgregorMood.AGITATED, EgregorMood.ALERT]:
            actions["should_reduce_activity"] = True
            actions["adjust_sample_rate"] = max(0.1, self.recommended_sample_rate * 0.5)
        
        # Si está dormido, despertar
        elif self.mood == EgregorMood.DORMANT:
            actions["should_increase_activity"] = True
            actions["adjust_sample_rate"] = min(10.0, self.recommended_sample_rate * 2.0)
        
        # Si la coherencia es baja, sincronizar
        if self.coherence < 0.3:
            actions["synchronization_pulse"] = True
        
        return actions


class EgregorProcessor:
    """
    Procesador del Egrégor.
    
    Se suscribe a todos los datos de sensores, los normaliza,
    y calcula el Estado de Ánimo emergente del sistema colectivo.
    
    Implementa:
    1. Agregación vectorial de estados de nodos
    2. Cálculo de métricas emergentes
    3. Determinación de mood basado en umbrales
    4. Generación de recomendaciones homeostáticas
    """
    
    # Umbrales para determinación de mood
    ENERGY_THRESHOLDS = {
        "very_high": 0.8,
        "high": 0.6,
        "neutral": 0.4,
        "low": 0.2,
    }
    
    # Ventana de tiempo para calcular estabilidad (segundos)
    STABILITY_WINDOW = 60.0
    
    # Peso de cada métrica en el cálculo de energía
    ENERGY_WEIGHTS = {
        "temperature": 0.15,
        "noise_level": 0.25,
        "motion_intensity": 0.25,
        "processing_load": 0.20,
        "prediction_error": 0.15,
    }
    
    def __init__(self, decay_time: float = 30.0):
        """
        Args:
            decay_time: Tiempo (s) para que datos antiguos pierdan relevancia
        """
        self.decay_time = decay_time
        
        # Datos de nodos activos
        self.node_data: Dict[str, NodeSensorData] = {}
        
        # Historial para calcular estabilidad y tendencias
        self.state_history: List[EgregorState] = []
        self.max_history = 100
        
        # Estado actual
        self.current_state = EgregorState()
        
        # Callbacks para notificaciones
        self._state_callbacks: List[callable] = []
    
    def register_callback(self, callback: callable) -> None:
        """Registra callback para cambios de estado."""
        self._state_callbacks.append(callback)
    
    def update_node_data(self, data: NodeSensorData) -> None:
        """
        Actualiza datos de un nodo.
        
        Args:
            data: Datos del sensor del nodo
        """
        self.node_data[data.node_id] = data
        
        # Limpiar nodos antiguos
        self._cleanup_stale_nodes()
    
    def _cleanup_stale_nodes(self) -> None:
        """Elimina nodos que no han reportado en decay_time."""
        current_time = time.time()
        stale_nodes = [
            node_id for node_id, data in self.node_data.items()
            if current_time - data.timestamp > self.decay_time * 2
        ]
        for node_id in stale_nodes:
            del self.node_data[node_id]
    
    def _calculate_decay_weight(self, timestamp: float) -> float:
        """Calcula peso basado en antigüedad del dato."""
        age = time.time() - timestamp
        return np.exp(-age / self.decay_time)
    
    def _aggregate_energy(self) -> float:
        """
        Calcula nivel de energía agregado de todos los nodos.
        
        Returns:
            Energía normalizada 0-1
        """
        if not self.node_data:
            return 0.5
        
        weighted_sum = 0.0
        weight_total = 0.0
        
        for data in self.node_data.values():
            decay = self._calculate_decay_weight(data.timestamp)
            
            # Calcular energía de este nodo
            node_energy = 0.0
            component_count = 0
            
            if data.temperature is not None:
                # Normalizar temperatura (asumiendo 0-50°C)
                temp_norm = np.clip(data.temperature / 50.0, 0, 1)
                node_energy += temp_norm * self.ENERGY_WEIGHTS["temperature"]
                component_count += 1
            
            if data.noise_level is not None:
                node_energy += data.noise_level * self.ENERGY_WEIGHTS["noise_level"]
                component_count += 1
            
            if data.motion_intensity is not None:
                node_energy += data.motion_intensity * self.ENERGY_WEIGHTS["motion_intensity"]
                component_count += 1
            
            node_energy += data.processing_load * self.ENERGY_WEIGHTS["processing_load"]
            node_energy += data.prediction_error * self.ENERGY_WEIGHTS["prediction_error"]
            component_count += 2
            
            if component_count > 0:
                weighted_sum += node_energy * decay
                weight_total += decay
        
        if weight_total > 0:
            return np.clip(weighted_sum / weight_total, 0, 1)
        return 0.5
    
    def _calculate_coherence(self) -> float:
        """
        Calcula coherencia (sincronización) entre nodos.
        
        Alta coherencia = nodos reportando valores similares
        Baja coherencia = alta varianza entre nodos
        
        Returns:
            Coherencia normalizada 0-1
        """
        if len(self.node_data) < 2:
            return 1.0  # Un solo nodo siempre es coherente consigo mismo
        
        # Recopilar métricas normalizadas de cada nodo
        node_vectors = []
        
        for data in self.node_data.values():
            decay = self._calculate_decay_weight(data.timestamp)
            if decay < 0.1:
                continue
            
            vector = [
                data.processing_load,
                data.prediction_error,
                data.will_alignment,
            ]
            
            if data.temperature is not None:
                vector.append(np.clip(data.temperature / 50.0, 0, 1))
            if data.noise_level is not None:
                vector.append(data.noise_level)
            if data.motion_intensity is not None:
                vector.append(data.motion_intensity)
            
            if len(vector) >= 3:
                node_vectors.append(vector[:6])  # Máx 6 componentes
        
        if len(node_vectors) < 2:
            return 1.0
        
        # Calcular varianza promedio
        min_len = min(len(v) for v in node_vectors)
        truncated = [v[:min_len] for v in node_vectors]
        arr = np.array(truncated)
        
        variances = np.var(arr, axis=0)
        avg_variance = np.mean(variances)
        
        # Convertir varianza a coherencia (menor varianza = mayor coherencia)
        coherence = np.exp(-avg_variance * 5)
        return float(np.clip(coherence, 0, 1))
    
    def _calculate_stability(self) -> float:
        """
        Calcula estabilidad temporal del sistema.
        
        Alta estabilidad = estados recientes similares
        Baja estabilidad = cambios rápidos de estado
        
        Returns:
            Estabilidad normalizada 0-1
        """
        if len(self.state_history) < 3:
            return 0.5
        
        # Últimos estados dentro de la ventana
        current_time = time.time()
        recent = [
            s for s in self.state_history[-20:]
            if current_time - s.timestamp < self.STABILITY_WINDOW
        ]
        
        if len(recent) < 2:
            return 0.5
        
        # Calcular varianza de energía en el tiempo
        energies = [s.energy_level for s in recent]
        variance = np.var(energies)
        
        # Contar cambios de mood
        mood_changes = sum(
            1 for i in range(1, len(recent))
            if recent[i].mood != recent[i-1].mood
        )
        mood_change_rate = mood_changes / len(recent)
        
        # Estabilidad inversamente proporcional a varianza y cambios
        stability = np.exp(-variance * 10) * np.exp(-mood_change_rate * 3)
        return float(np.clip(stability, 0, 1))
    
    def _calculate_entropy(self) -> float:
        """
        Calcula entropía (caos/orden) del sistema.
        
        Alta entropía = sistema caótico, impredecible
        Baja entropía = sistema ordenado, predecible
        
        Returns:
            Entropía normalizada 0-1
        """
        if not self.node_data:
            return 0.5
        
        # Entropía basada en:
        # 1. Diversidad de dominios activos (will_alignment)
        # 2. Varianza de errores de predicción
        # 3. Distribución de cargas
        
        alignments = [d.will_alignment for d in self.node_data.values()]
        errors = [d.prediction_error for d in self.node_data.values()]
        loads = [d.processing_load for d in self.node_data.values()]
        
        # Shannon entropy aproximada
        def approx_entropy(values: List[float]) -> float:
            if len(values) < 2:
                return 0.0
            arr = np.array(values)
            arr = np.clip(arr, 0.01, 0.99)  # Evitar log(0)
            # Normalizar como distribución
            arr = arr / np.sum(arr)
            return float(-np.sum(arr * np.log2(arr + 1e-10)))
        
        h_alignment = approx_entropy(alignments) if alignments else 0
        h_errors = approx_entropy(errors) if errors else 0
        h_loads = approx_entropy(loads) if loads else 0
        
        # Combinar y normalizar
        max_entropy = np.log2(max(len(self.node_data), 2))
        combined = (h_alignment + h_errors + h_loads) / 3
        entropy = np.clip(combined / max(max_entropy, 1), 0, 1)
        
        return float(entropy)
    
    def _determine_mood(
        self, 
        energy: float, 
        coherence: float, 
        stability: float,
        _entropy: float  # Reserved for future entropy-based mood adjustments
    ) -> Tuple[EgregorMood, float]:
        """
        Determina el mood del Egrégor basado en métricas.
        
        Returns:
            (mood, confidence)
        """
        # Lógica de decisión - confidence se asigna en cada rama
        
        # Alta energía + baja estabilidad = Agitado
        if energy > 0.7 and stability < 0.4:
            mood = EgregorMood.AGITATED
            confidence = min(energy, 1 - stability)
        
        # Alta energía + alta estabilidad = Alerta
        elif energy > 0.6 and stability > 0.5:
            mood = EgregorMood.ALERT
            confidence = (energy + stability) / 2
        
        # Energía media + alta coherencia = Dinámico
        elif 0.4 < energy < 0.7 and coherence > 0.6:
            mood = EgregorMood.DYNAMIC
            confidence = coherence
        
        # Muy baja energía = Dormido
        elif energy < 0.15:
            mood = EgregorMood.DORMANT
            confidence = 1 - energy * 5
        
        # Baja energía + alta estabilidad = Meditativo
        elif energy < 0.3 and stability > 0.7:
            mood = EgregorMood.MEDITATIVE
            confidence = stability
        
        # Baja energía + estabilidad media = Contemplativo
        elif energy < 0.4:
            mood = EgregorMood.CONTEMPLATIVE
            confidence = 0.6
        
        # Baja coherencia = Armonizando
        elif coherence < 0.3:
            mood = EgregorMood.HARMONIZING
            confidence = 1 - coherence
        
        # Transición de dormido (energía subiendo)
        elif (len(self.state_history) > 0 and 
              self.state_history[-1].mood == EgregorMood.DORMANT and
              energy > 0.2):
            mood = EgregorMood.AWAKENING
            confidence = 0.7
        
        # Default: Balanceado
        else:
            mood = EgregorMood.BALANCED
            confidence = 0.5
        
        return mood, float(np.clip(confidence, 0, 1))
    
    def _calculate_recommendations(
        self,
        _mood: EgregorMood,  # Reserved for mood-specific adjustments
        energy: float,
        coherence: float,
        stability: float
    ) -> Tuple[float, float]:
        """
        Calcula recomendaciones homeostáticas.
        
        Returns:
            (recommended_sample_rate, recommended_merge_ratio)
        """
        # Base sample rate
        base_rate = 1.0
        
        # Ajustar por energía (homeostasis)
        if energy > 0.7:
            # Sistema agitado: bajar frecuencia para calmar
            rate_factor = 0.5
        elif energy < 0.2:
            # Sistema dormido: subir frecuencia para despertar
            rate_factor = 2.0
        else:
            rate_factor = 1.0
        
        # Ajustar por estabilidad
        if stability < 0.3:
            # Sistema inestable: reducir cambios
            rate_factor *= 0.7
        
        sample_rate = np.clip(base_rate * rate_factor, 0.1, 10.0)
        
        # Merge ratio basado en coherencia
        if coherence > 0.7:
            # Alta coherencia: nodos pueden compartir más
            merge_ratio = 0.6
        elif coherence < 0.3:
            # Baja coherencia: proteger conocimiento local
            merge_ratio = 0.2
        else:
            merge_ratio = 0.4
        
        return float(sample_rate), float(merge_ratio)
    
    def process(self) -> EgregorState:
        """
        Procesa todos los datos actuales y genera nuevo estado.
        
        Este es el método principal que debe llamarse periódicamente.
        
        Returns:
            Estado actualizado del Egrégor
        """
        # Calcular métricas emergentes
        energy = self._aggregate_energy()
        coherence = self._calculate_coherence()
        stability = self._calculate_stability()
        entropy = self._calculate_entropy()
        
        # Determinar mood
        mood, confidence = self._determine_mood(energy, coherence, stability, entropy)
        
        # Calcular recomendaciones
        sample_rate, merge_ratio = self._calculate_recommendations(
            mood, energy, coherence, stability
        )
        
        # Crear nuevo estado
        new_state = EgregorState(
            mood=mood,
            intensity=energy,
            confidence=confidence,
            energy_level=energy,
            coherence=coherence,
            stability=stability,
            entropy=entropy,
            node_count=len(self.node_data),
            timestamp=time.time(),
            recommended_sample_rate=sample_rate,
            recommended_merge_ratio=merge_ratio,
        )
        
        # Guardar en historial
        self.state_history.append(new_state)
        if len(self.state_history) > self.max_history:
            self.state_history = self.state_history[-self.max_history:]
        
        # Detectar cambio significativo
        if (self.current_state.mood != new_state.mood or
            abs(self.current_state.energy_level - new_state.energy_level) > 0.2):
            # Notificar callbacks
            for callback in self._state_callbacks:
                try:
                    callback(new_state)
                except Exception:
                    pass
        
        self.current_state = new_state
        return new_state
    
    def get_state(self) -> EgregorState:
        """Retorna el estado actual sin procesar."""
        return self.current_state
    
    def get_summary(self) -> str:
        """
        Genera un resumen legible del estado del Egrégor.
        
        Returns:
            String con resumen del estado
        """
        s = self.current_state
        return (
            f"Egrégor [{s.mood.value.upper()}]\n"
            f"  Intensidad: {s.intensity:.1%}\n"
            f"  Energía: {s.energy_level:.1%}\n"
            f"  Coherencia: {s.coherence:.1%}\n"
            f"  Estabilidad: {s.stability:.1%}\n"
            f"  Entropía: {s.entropy:.1%}\n"
            f"  Nodos activos: {s.node_count}\n"
            f"  → Sample Rate recomendado: {s.recommended_sample_rate:.1f} Hz\n"
            f"  → Merge Ratio recomendado: {s.recommended_merge_ratio:.1%}"
        )


def demo_egregore():
    """Demostración del sistema Egrégor."""
    print("=" * 60)
    print("  EGRÉGOR - Mente Grupal Emergente")
    print("  'La suma es mayor que las partes'")
    print("=" * 60)
    print()
    
    processor = EgregorProcessor(decay_time=30.0)
    
    # Simular nodos reportando datos
    print("Simulando nodos reportando datos...\n")
    
    # Escenario 1: Sistema calmado
    print("--- Escenario 1: Sistema Calmado ---")
    for i in range(3):
        data = NodeSensorData(
            node_id=f"node_{i}",
            timestamp=time.time(),
            temperature=22.0 + i * 0.5,
            noise_level=0.1,
            motion_intensity=0.05,
            processing_load=0.2,
            prediction_error=0.05,
            will_alignment=0.9,
        )
        processor.update_node_data(data)
    
    processor.process()
    print(processor.get_summary())
    print()
    
    # Escenario 2: Sistema agitado
    print("--- Escenario 2: Sistema Agitado ---")
    for i in range(5):
        data = NodeSensorData(
            node_id=f"node_{i}",
            timestamp=time.time(),
            temperature=35.0 + i * 2,
            noise_level=0.8,
            motion_intensity=0.9,
            processing_load=0.85,
            prediction_error=0.6,
            will_alignment=0.4,
        )
        processor.update_node_data(data)
    
    state = processor.process()
    print(processor.get_summary())
    print()
    print("Acciones homeostáticas:")
    actions = state.get_homeostatic_actions()
    for key, value in actions.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    demo_egregore()
