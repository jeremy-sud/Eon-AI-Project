"""
Proyecto Eón - Oráculo I-Ching Neural
=====================================

Un oráculo que combina la sabiduría milenaria del I-Ching con
la capacidad predictiva de las Echo State Networks.

El I-Ching tiene 64 hexagramas, cada uno compuesto de 6 líneas (bits).
Esta representación binaria es perfecta para redes neuronales.

Concepto:
---------
1. El ESN aprende patrones de transición entre hexagramas
2. Dado un hexagrama actual y una pregunta, predice el siguiente
3. La interpretación combina matemática con tradición

"El universo habla en patrones, no en palabras."

(c) 2024 Proyecto Eón - Jeremy Arias Solano
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Callable
from enum import Enum
import time
import logging
import hashlib

# Path setup
import sys
import os
_current_dir = os.path.dirname(os.path.abspath(__file__))
_python_dir = os.path.dirname(_current_dir)
if _python_dir not in sys.path:
    sys.path.insert(0, _python_dir)

from esn.esn import EchoStateNetwork
from core.archaic_protocol import Hexagram, Trigram, HEXAGRAMS, ArchaicProtocol

logger = logging.getLogger(__name__)


class ConsultationType(Enum):
    """Tipos de consulta al oráculo."""
    SINGLE = "single"           # Un hexagrama
    RELATING = "relating"       # Hexagrama + hexagrama relacionado
    SEQUENCE = "sequence"       # Secuencia de hexagramas
    MEDITATION = "meditation"   # Sin pregunta, estado actual


class LineChange(Enum):
    """Tipos de línea en el I-Ching."""
    OLD_YIN = 6     # ⚋ Yin viejo (cambia a Yang)
    YOUNG_YANG = 7  # ⚊ Yang joven (estable)
    YOUNG_YIN = 8   # ⚋ Yin joven (estable)
    OLD_YANG = 9    # ⚊ Yang viejo (cambia a Yin)


@dataclass
class OracleReading:
    """Resultado de una consulta al oráculo."""
    question: str
    timestamp: float
    
    # Hexagrama principal
    primary_hexagram: Hexagram
    primary_lines: Tuple[int, ...]  # Los 6 valores de línea (6-9)
    
    # Hexagrama relacionado (si hay líneas cambiantes)
    relating_hexagram: Optional[Hexagram] = None
    changing_lines: List[int] = field(default_factory=list)  # Índices 0-5
    
    # Interpretación
    judgment: str = ""
    image: str = ""
    advice: str = ""
    
    # Metadatos
    esn_confidence: float = 0.0
    resonance_score: float = 0.0
    
    def __repr__(self):
        rel = f" → {self.relating_hexagram.number}" if self.relating_hexagram else ""
        return f"OracleReading({self.primary_hexagram.number}{rel}: {self.primary_hexagram.name_spanish})"
    
    def to_dict(self) -> Dict:
        """Serializa la lectura."""
        return {
            "question": self.question,
            "timestamp": self.timestamp,
            "primary": {
                "number": self.primary_hexagram.number,
                "name": self.primary_hexagram.name_spanish,
                "symbol": self.primary_hexagram.symbol,
                "judgment": self.primary_hexagram.judgment,
                "image": self.primary_hexagram.image
            },
            "relating": {
                "number": self.relating_hexagram.number,
                "name": self.relating_hexagram.name_spanish,
                "symbol": self.relating_hexagram.symbol
            } if self.relating_hexagram else None,
            "changing_lines": self.changing_lines,
            "advice": self.advice,
            "confidence": self.esn_confidence,
            "resonance": self.resonance_score
        }


@dataclass
class OracleStats:
    """Estadísticas del oráculo."""
    consultations: int = 0
    total_resonance: float = 0.0
    hexagram_distribution: Dict[int, int] = field(default_factory=dict)
    
    @property
    def avg_resonance(self) -> float:
        return self.total_resonance / self.consultations if self.consultations > 0 else 0.0


class IChingOracle:
    """
    Oráculo Neural basado en ESN y el I-Ching.
    
    Combina:
    - Echo State Network para predicción de patrones
    - 64 hexagramas del I-Ching como estados
    - Interpretación tradicional + neural
    
    El ESN aprende la "dinámica del cambio" - cómo los estados
    tienden a fluir de uno a otro según el contexto.
    
    Example:
        >>> oracle = IChingOracle(reservoir_size=64)
        >>> oracle.train_on_transitions()  # Aprender patrones clásicos
        >>> 
        >>> reading = oracle.consult("¿Debería iniciar este proyecto?")
        >>> print(reading.primary_hexagram.name_spanish)
        >>> print(reading.advice)
    """
    
    def __init__(
        self,
        reservoir_size: int = 64,
        spectral_radius: float = 0.95,
        random_state: Optional[int] = None
    ):
        """
        Inicializa el oráculo.
        
        Args:
            reservoir_size: Tamaño del reservoir (64 = número de hexagramas)
            spectral_radius: Radio espectral del ESN
            random_state: Semilla aleatoria
        """
        self.reservoir_size = reservoir_size
        
        # ESN para predicción de transiciones
        # Input: 6 bits (hexagrama actual) + embedding de pregunta
        # Output: 6 bits (hexagrama predicho)
        self.esn = EchoStateNetwork(
            n_inputs=6 + 8,  # 6 líneas + 8 features de contexto
            n_reservoir=reservoir_size,
            n_outputs=6,
            spectral_radius=spectral_radius,
            random_state=random_state or int(time.time())
        )
        
        # Protocolo para interpretación
        self.protocol = ArchaicProtocol()
        
        # RNG para tiradas
        self.rng = np.random.default_rng(random_state)
        
        # Estadísticas
        self.stats = OracleStats()
        
        # Estado actual
        self.current_state: Optional[np.ndarray] = None
        self.is_trained = False
        
        # Crear lookup table para búsqueda O(1) de hexagramas por bits
        self._hexagram_lookup: Dict[tuple, Hexagram] = {}
        for hexagram in HEXAGRAMS.values():
            bits_key = tuple(hexagram.lines)
            self._hexagram_lookup[bits_key] = hexagram
        
        logger.info(f"IChingOracle inicializado: reservoir={reservoir_size}")
    
    def _question_to_embedding(self, question: str) -> np.ndarray:
        """
        Convierte una pregunta en un embedding de 8 dimensiones.
        
        Usa características simples derivadas del texto:
        - Hash de la pregunta
        - Longitud normalizada
        - Presencia de palabras clave
        """
        embedding = np.zeros(8)
        
        if not question:
            return embedding
        
        # Hash de la pregunta (determina semilla)
        h = hashlib.md5(question.encode()).hexdigest()
        hash_int = int(h[:8], 16)
        
        # Features basadas en hash
        embedding[0] = (hash_int % 256) / 255.0
        embedding[1] = ((hash_int >> 8) % 256) / 255.0
        embedding[2] = ((hash_int >> 16) % 256) / 255.0
        
        # Longitud normalizada
        embedding[3] = min(len(question) / 100, 1.0)
        
        # Palabras clave (categorías)
        question_lower = question.lower()
        
        # Acción/movimiento
        action_words = ['hacer', 'iniciar', 'comenzar', 'empezar', 'actuar', 'mover']
        embedding[4] = 1.0 if any(w in question_lower for w in action_words) else 0.0
        
        # Espera/paciencia
        wait_words = ['esperar', 'aguardar', 'paciencia', 'tiempo', 'momento']
        embedding[5] = 1.0 if any(w in question_lower for w in wait_words) else 0.0
        
        # Relación/otros
        relation_words = ['persona', 'relación', 'amor', 'amigo', 'familia', 'otro']
        embedding[6] = 1.0 if any(w in question_lower for w in relation_words) else 0.0
        
        # Trabajo/dinero
        work_words = ['trabajo', 'dinero', 'negocio', 'proyecto', 'carrera', 'empleo']
        embedding[7] = 1.0 if any(w in question_lower for w in work_words) else 0.0
        
        return embedding
    
    def _hexagram_to_binary(self, hexagram: Hexagram) -> np.ndarray:
        """Convierte hexagrama a array de 6 bits."""
        return np.array(hexagram.lines, dtype=float)
    
    def _binary_to_hexagram(self, binary: np.ndarray) -> Hexagram:
        """Convierte array de 6 bits a hexagrama."""
        # Redondear a 0 o 1
        bits = (binary > 0.5).astype(int)
        
        # Buscar hexagrama por líneas
        target_lines = tuple(bits)
        
        for hex_num, hexagram in HEXAGRAMS.items():
            if hexagram.lines == target_lines:
                return hexagram
        
        # Si no encuentra exacto, usar el más cercano
        return self._find_closest_hexagram(bits)
    
    def _find_closest_hexagram(self, bits: np.ndarray) -> Hexagram:
        """
        Encuentra el hexagrama más cercano a los bits dados.
        
        Usa lookup table para O(1) en coincidencia exacta,
        con fallback a búsqueda lineal para coincidencias parciales.
        """
        # Convertir a enteros binarios (0 o 1)
        binary_bits = tuple(int(b > 0.5) for b in bits)
        
        # Búsqueda O(1) para coincidencia exacta
        if binary_bits in self._hexagram_lookup:
            return self._hexagram_lookup[binary_bits]
        
        # Fallback: búsqueda de menor distancia de Hamming
        min_dist = float('inf')
        closest = HEXAGRAMS[1]
        
        for hexagram in HEXAGRAMS.values():
            hex_bits = np.array(hexagram.lines)
            dist = np.sum(np.abs(bits - hex_bits))
            if dist < min_dist:
                min_dist = dist
                closest = hexagram
        
        return closest
    
    def cast_yarrow_stalks(self) -> Tuple[List[int], List[int]]:
        """
        Simula el método tradicional de tallos de milenrama.
        
        Genera los 6 valores de línea (6, 7, 8, o 9) que determinan
        tanto el hexagrama como las líneas cambiantes.
        
        Returns:
            (line_values, changing_indices)
        """
        line_values = []
        changing = []
        
        for i in range(6):
            # Método simplificado de 3 monedas
            # 3 caras = 9 (yang viejo, cambia)
            # 3 cruces = 6 (yin viejo, cambia)
            # 2 caras + 1 cruz = 8 (yin joven, estable)
            # 1 cara + 2 cruces = 7 (yang joven, estable)
            
            coins = self.rng.integers(0, 2, size=3)  # 0=cruz, 1=cara
            total = np.sum(coins) + 6  # 6, 7, 8, o 9
            
            line_values.append(total)
            
            if total in [6, 9]:  # Líneas viejas cambian
                changing.append(i)
        
        return line_values, changing
    
    def _line_values_to_hexagram(self, line_values: List[int]) -> Tuple[Hexagram, Optional[Hexagram], List[int]]:
        """
        Convierte valores de línea a hexagrama(s).
        
        Args:
            line_values: Lista de 6 valores (6, 7, 8, 9)
            
        Returns:
            (primary_hexagram, relating_hexagram, changing_indices)
        """
        # Hexagrama primario
        primary_bits = []
        changing = []
        
        for i, val in enumerate(line_values):
            if val in [7, 9]:  # Yang
                primary_bits.append(1)
            else:  # Yin (6, 8)
                primary_bits.append(0)
            
            if val in [6, 9]:  # Cambiante
                changing.append(i)
        
        primary = self._find_closest_hexagram(np.array(primary_bits))
        
        # Hexagrama relacionado (si hay líneas cambiantes)
        relating = None
        if changing:
            relating_bits = primary_bits.copy()
            for idx in changing:
                relating_bits[idx] = 1 - relating_bits[idx]  # Invertir
            relating = self._find_closest_hexagram(np.array(relating_bits))
        
        return primary, relating, changing
    
    def train_on_transitions(self, n_sequences: int = 1000, seq_length: int = 10):
        """
        Entrena el ESN en transiciones de hexagramas.
        
        Genera secuencias de consultas simuladas para que el ESN
        aprenda los patrones naturales de cambio.
        
        Args:
            n_sequences: Número de secuencias de entrenamiento
            seq_length: Longitud de cada secuencia
        """
        logger.info(f"Entrenando oráculo con {n_sequences} secuencias...")
        
        X_train = []
        y_train = []
        
        for _ in range(n_sequences):
            # Generar secuencia de hexagramas
            current_hex = HEXAGRAMS[self.rng.integers(1, 65)]
            
            for _ in range(seq_length):
                # Crear input
                hex_bits = self._hexagram_to_binary(current_hex)
                context = self.rng.random(8)  # Contexto aleatorio
                x = np.concatenate([hex_bits, context])
                
                # Simular siguiente hexagrama (con tendencia a relacionados)
                # Los hexagramas tienden a cambiar a sus complementarios
                next_hex = self._predict_natural_transition(current_hex)
                y = self._hexagram_to_binary(next_hex)
                
                X_train.append(x)
                y_train.append(y)
                
                current_hex = next_hex
        
        X_train = np.array(X_train)
        y_train = np.array(y_train)
        
        # Entrenar ESN
        self.esn.fit(X_train, y_train, washout=100)
        self.is_trained = True
        
        logger.info("Oráculo entrenado exitosamente")
    
    def _predict_natural_transition(self, current: Hexagram) -> Hexagram:
        """
        Predice transición natural basada en relaciones del I-Ching.
        
        Reglas simplificadas:
        - Alta probabilidad de mantener similar
        - Tendencia a trigramas complementarios
        - Ocasionalmente salto a opuesto
        """
        # Probabilidades de tipo de transición
        transition_type = self.rng.random()
        
        if transition_type < 0.3:
            # Mantener mismo hexagrama
            return current
        
        elif transition_type < 0.6:
            # Cambiar una línea aleatoria
            bits = list(current.lines)
            idx = self.rng.integers(0, 6)
            bits[idx] = 1 - bits[idx]
            return self._find_closest_hexagram(np.array(bits))
        
        elif transition_type < 0.8:
            # Ir a hexagrama con trigrama complementario
            # Superior → Inferior intercambiados
            new_upper = current.lower
            new_lower = current.upper
            new_lines = new_lower.value + new_upper.value
            return self._find_closest_hexagram(np.array(new_lines))
        
        else:
            # Hexagrama aleatorio
            return HEXAGRAMS[self.rng.integers(1, 65)]
    
    def consult(
        self, 
        question: str = "",
        consultation_type: ConsultationType = ConsultationType.RELATING
    ) -> OracleReading:
        """
        Realiza una consulta al oráculo.
        
        Args:
            question: La pregunta a consultar
            consultation_type: Tipo de lectura (reservado para uso futuro)
            
        Returns:
            OracleReading con el resultado
            
        Note:
            consultation_type será usado en futuras versiones para
            diferentes métodos de interpretación.
        """
        _ = consultation_type  # Reservado para implementación futura
        timestamp = time.time()
        
        # Tirar las monedas/tallos
        line_values, changing_indices = self.cast_yarrow_stalks()
        
        # Obtener hexagramas
        primary, relating, changing = self._line_values_to_hexagram(line_values)
        
        # Si el ESN está entrenado, usar para ajustar predicción
        esn_confidence = 0.0
        if self.is_trained and question:
            # Crear input para ESN
            hex_bits = self._hexagram_to_binary(primary)
            context = self._question_to_embedding(question)
            x = np.concatenate([hex_bits, context]).reshape(1, -1)
            
            # Predecir
            pred = self.esn.predict(x)
            
            # Calcular confianza (similitud con relating)
            if relating:
                relating_bits = self._hexagram_to_binary(relating)
                esn_confidence = 1.0 - np.mean(np.abs(pred.flatten() - relating_bits))
        
        # Calcular resonancia (basada en la pregunta y el hexagrama)
        resonance = self._calculate_resonance(question, primary)
        
        # Generar interpretación
        advice = self._generate_advice(primary, relating, changing, question)
        
        # Crear lectura
        reading = OracleReading(
            question=question,
            timestamp=timestamp,
            primary_hexagram=primary,
            primary_lines=tuple(line_values),
            relating_hexagram=relating,
            changing_lines=changing_indices,
            judgment=primary.judgment,
            image=primary.image,
            advice=advice,
            esn_confidence=esn_confidence,
            resonance_score=resonance
        )
        
        # Actualizar estadísticas
        self._update_stats(reading)
        
        logger.info(f"Consulta: {primary.number} {primary.name_spanish} (resonance={resonance:.2f})")
        
        return reading
    
    def _calculate_resonance(self, question: str, hexagram: Hexagram) -> float:
        """
        Calcula la resonancia entre pregunta y hexagrama.
        
        Basado en:
        - Coincidencia de temas
        - Energía del hexagrama
        - Momento temporal
        """
        base_resonance = 0.5
        
        if not question:
            return base_resonance
        
        question_lower = question.lower()
        
        # Mapeo de hexagramas a temas
        theme_boosts = {
            # Hexagramas de acción
            1: ['crear', 'iniciar', 'fuerza', 'líder', 'cielo'],  # Qian
            51: ['acción', 'movimiento', 'trueno', 'inicio'],      # Zhen
            
            # Hexagramas de espera
            2: ['recibir', 'esperar', 'tierra', 'paciencia'],      # Kun
            5: ['esperar', 'paciencia', 'tiempo', 'nube'],         # Xu
            
            # Hexagramas de relación
            31: ['amor', 'atracción', 'relación', 'sentir'],       # Xian
            32: ['duración', 'matrimonio', 'constancia'],          # Heng
            
            # Hexagramas de trabajo
            14: ['abundancia', 'éxito', 'riqueza', 'posesión'],    # Da You
            42: ['aumento', 'beneficio', 'crecer', 'expandir'],    # Yi
        }
        
        # Buscar coincidencias
        if hexagram.number in theme_boosts:
            keywords = theme_boosts[hexagram.number]
            matches = sum(1 for kw in keywords if kw in question_lower)
            base_resonance += matches * 0.1
        
        # Limitar a rango [0, 1]
        return min(max(base_resonance, 0.0), 1.0)
    
    def _generate_advice(
        self,
        primary: Hexagram,
        relating: Optional[Hexagram],
        changing: List[int],
        question: str
    ) -> str:
        """Genera consejo personalizado basado en la lectura."""
        
        parts = []
        
        # Interpretación principal
        parts.append(f"📖 {primary.name_spanish} ({primary.name_chinese})")
        parts.append(f"El Juicio: {primary.judgment}")
        parts.append(f"La Imagen: {primary.image}")
        
        # Líneas cambiantes
        if changing:
            parts.append(f"\n🔄 Líneas cambiantes: {', '.join(str(i+1) for i in changing)}")
            parts.append("El cambio está en proceso. La situación no es estática.")
        
        # Hexagrama relacionado
        if relating:
            parts.append(f"\n➡️ Evoluciona hacia: {relating.name_spanish}")
            parts.append(f"Tendencia futura: {relating.judgment}")
        
        # Síntesis basada en trigramas
        upper_meaning = primary.upper.meaning
        lower_meaning = primary.lower.meaning
        parts.append(f"\n🌀 Trigramas: {lower_meaning} abajo, {upper_meaning} arriba")
        
        return "\n".join(parts)
    
    def _update_stats(self, reading: OracleReading):
        """Actualiza estadísticas."""
        self.stats.consultations += 1
        self.stats.total_resonance += reading.resonance_score
        
        hex_num = reading.primary_hexagram.number
        if hex_num not in self.stats.hexagram_distribution:
            self.stats.hexagram_distribution[hex_num] = 0
        self.stats.hexagram_distribution[hex_num] += 1
    
    def divine_sequence(self, question: str, n_steps: int = 3) -> List[OracleReading]:
        """
        Genera una secuencia de lecturas para entender evolución.
        
        Útil para preguntas sobre procesos o desarrollo a largo plazo.
        
        Args:
            question: Pregunta inicial
            n_steps: Número de lecturas en la secuencia
            
        Returns:
            Lista de OracleReading mostrando evolución
        """
        readings = []
        
        # Primera lectura
        reading = self.consult(question)
        readings.append(reading)
        
        # Lecturas siguientes basadas en hexagrama relacionado
        for i in range(1, n_steps):
            if reading.relating_hexagram:
                # Usar relating como base para siguiente
                context = f"Continuación de {reading.primary_hexagram.name_spanish}"
            else:
                context = f"Paso {i+1}: {question}"
            
            reading = self.consult(context)
            readings.append(reading)
        
        return readings
    
    def get_hexagram_by_number(self, number: int) -> Optional[Hexagram]:
        """Obtiene hexagrama por número."""
        return HEXAGRAMS.get(number)
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas del oráculo."""
        return {
            "consultations": self.stats.consultations,
            "avg_resonance": self.stats.avg_resonance,
            "is_trained": self.is_trained,
            "top_hexagrams": sorted(
                self.stats.hexagram_distribution.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
    
    def meditate(self) -> OracleReading:
        """
        Consulta meditativa sin pregunta específica.
        
        Útil para reflexión diaria o estado actual.
        """
        return self.consult("", ConsultationType.MEDITATION)


def create_oracle(
    reservoir_size: int = 64,
    pretrained: bool = True,
    random_state: Optional[int] = None
) -> IChingOracle:
    """
    Factory function para crear un oráculo listo para usar.
    
    Args:
        reservoir_size: Tamaño del reservoir
        pretrained: Si True, entrena automáticamente
        random_state: Semilla aleatoria
        
    Returns:
        IChingOracle configurado
    """
    oracle = IChingOracle(
        reservoir_size=reservoir_size,
        random_state=random_state
    )
    
    if pretrained:
        oracle.train_on_transitions(n_sequences=500)
    
    return oracle


# Demo
if __name__ == "__main__":
    print("🔮 Oráculo I-Ching Neural - Proyecto Eón")
    print("=" * 50)
    
    # Crear oráculo
    oracle = create_oracle(reservoir_size=64, pretrained=True, random_state=42)
    
    # Consultas de ejemplo
    questions = [
        "¿Debería iniciar un nuevo proyecto?",
        "¿Cómo será mi relación con mi equipo de trabajo?",
        "¿Es buen momento para tomar decisiones importantes?",
        "",  # Meditación
    ]
    
    for q in questions:
        print("\n" + "─" * 50)
        if q:
            print(f"Pregunta: {q}")
        else:
            print("Meditación silenciosa...")
        
        reading = oracle.consult(q)
        
        print(f"\n{reading.primary_hexagram.symbol} Hexagrama {reading.primary_hexagram.number}: {reading.primary_hexagram.name_spanish}")
        
        if reading.relating_hexagram:
            print(f"➡️ Evoluciona hacia: {reading.relating_hexagram.number} {reading.relating_hexagram.name_spanish}")
        
        print(f"\n📊 Resonancia: {reading.resonance_score:.2%}")
        print(f"🎯 Confianza ESN: {reading.esn_confidence:.2%}")
        
        print(f"\n{reading.advice}")
    
    # Secuencia
    print("\n" + "=" * 50)
    print("📜 Secuencia de 3 lecturas:")
    sequence = oracle.divine_sequence("Mi camino espiritual", n_steps=3)
    
    for i, reading in enumerate(sequence, 1):
        print(f"\n  Paso {i}: {reading.primary_hexagram.number} - {reading.primary_hexagram.name_spanish}")
    
    # Estadísticas
    print("\n" + "=" * 50)
    print(f"📊 Estadísticas: {oracle.get_stats()}")
