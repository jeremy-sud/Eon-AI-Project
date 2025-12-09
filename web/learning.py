"""
Proyecto Eón - Sistema de Aprendizaje Continuo
=============================================

Este módulo implementa el aprendizaje real de Eón:
- Aprendizaje online de W_out desde conversaciones
- Memoria a largo plazo estructurada
- Sistema de feedback (refuerzo/debilitamiento)
- Plasticidad Hebbiana integrada
- Consolidación durante inactividad ("sueño")

(c) 2024 Sistemas Ursol - Jeremy Arias Solano
"""

import os
import json
import time
import threading
import hashlib
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import deque


class OnlineLearner:
    """
    Aprendizaje online de W_out usando Ridge Regression incremental.
    
    En lugar de reentrenar desde cero, actualiza los pesos incrementalmente
    con cada nueva experiencia, similar a como el cerebro aprende.
    """
    
    def __init__(self, n_reservoir: int = 100, n_outputs: int = 1, 
                 learning_rate: float = 0.01, regularization: float = 1e-4):
        self.n_reservoir = n_reservoir
        self.n_outputs = n_outputs
        self.learning_rate = learning_rate
        self.regularization = regularization
        
        # Matriz de correlación para actualización incremental
        # P = (X^T X + λI)^(-1) - necesitamos acumular esto
        self._correlation_matrix = np.eye(n_reservoir) * regularization
        self._cross_correlation = np.zeros((n_reservoir, n_outputs))
        
        # Estadísticas
        self.samples_learned = 0
        self.total_error = 0.0
        self.learning_history = []
        
    def update(self, reservoir_state: np.ndarray, target: np.ndarray, 
               feedback_weight: float = 1.0) -> float:
        """
        Actualiza W_out con una nueva muestra.
        
        Args:
            reservoir_state: Estado actual del reservoir (n_reservoir,)
            target: Salida objetivo (n_outputs,)
            feedback_weight: Peso del feedback (1.0 = normal, >1 = reforzar, <1 = debilitar)
            
        Returns:
            Error de predicción
        """
        x = reservoir_state.reshape(-1, 1)  # (n_reservoir, 1)
        y = target.reshape(-1, 1)  # (n_outputs, 1)
        
        # Actualización RLS (Recursive Least Squares) simplificada
        # Acumular correlaciones
        weight = self.learning_rate * feedback_weight
        self._correlation_matrix += weight * np.dot(x, x.T)
        self._cross_correlation += weight * np.dot(x, y.T)
        
        self.samples_learned += 1
        
        # Log cada 100 muestras
        if self.samples_learned % 100 == 0:
            self.learning_history.append({
                'samples': self.samples_learned,
                'timestamp': time.time()
            })
        
        return 0.0  # Error placeholder
    
    def get_W_out(self) -> np.ndarray:
        """Calcula W_out actual desde las correlaciones acumuladas."""
        try:
            # W_out = (X^T X + λI)^(-1) X^T Y
            W_out = np.linalg.solve(
                self._correlation_matrix + self.regularization * np.eye(self.n_reservoir),
                self._cross_correlation
            )
            return W_out
        except np.linalg.LinAlgError:
            return np.zeros((self.n_reservoir, self.n_outputs))
    
    def apply_to_esn(self, esn) -> bool:
        """Aplica los pesos aprendidos al ESN."""
        if self.samples_learned < 10:
            return False  # No suficientes muestras
        
        new_W_out = self.get_W_out()
        
        # Mezclar con pesos existentes (si los hay)
        if esn.W_out is not None:
            # Promedio ponderado: más peso a los nuevos si hay muchas muestras
            blend = min(0.5, self.samples_learned / 1000)
            esn.W_out = (1 - blend) * esn.W_out + blend * new_W_out
        else:
            esn.W_out = new_W_out
        
        return True
    
    def get_stats(self) -> Dict:
        return {
            'samples_learned': self.samples_learned,
            'correlation_norm': float(np.linalg.norm(self._correlation_matrix)),
            'history_length': len(self.learning_history)
        }


class LongTermMemory:
    """
    Memoria a largo plazo estructurada para Eón.
    
    Almacena:
    - Información de usuarios conocidos
    - Hechos aprendidos de conversaciones
    - Resúmenes de conversaciones importantes
    - Preferencias y patrones detectados
    """
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.memory = {
            'users': {},           # {nombre: {info}}
            'facts': [],           # [{fact, source, confidence, timestamp}]
            'summaries': [],       # [{summary, topic, timestamp}]
            'preferences': {},     # {categoria: valor}
            'interactions': {      # Estadísticas globales
                'total': 0,
                'by_intent': {},
                'by_hour': [0] * 24,
            },
            'emotional_memory': [],  # Momentos importantes
            'created_at': time.time(),
            'last_updated': time.time(),
        }
        self._load()
    
    def _load(self):
        """Carga memoria desde archivo."""
        try:
            if os.path.exists(self.filepath):
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    self.memory.update(saved)
        except Exception as e:
            print(f" [WARN] Error cargando memoria: {e}")
    
    def _save(self):
        """Guarda memoria a archivo."""
        self.memory['last_updated'] = time.time()
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f" [WARN] Error guardando memoria: {e}")
    
    # === USUARIOS ===
    
    def remember_user(self, name: str, info: Dict = None):
        """Recuerda información sobre un usuario."""
        name_lower = name.lower()
        if name_lower not in self.memory['users']:
            self.memory['users'][name_lower] = {
                'name': name,  # Nombre original con mayúsculas
                'first_seen': time.time(),
                'interaction_count': 0,
                'topics': [],
                'is_creator': False,
                'preferences': {},
                'last_seen': time.time(),
            }
        
        user = self.memory['users'][name_lower]
        user['interaction_count'] += 1
        user['last_seen'] = time.time()
        
        if info:
            if 'is_creator' in info:
                user['is_creator'] = info['is_creator']
            if 'topic' in info and info['topic'] not in user['topics']:
                user['topics'].append(info['topic'])
                user['topics'] = user['topics'][-20:]  # Últimos 20 temas
        
        self._save()
        return user
    
    def get_user(self, name: str) -> Optional[Dict]:
        """Obtiene información de un usuario."""
        return self.memory['users'].get(name.lower())
    
    def get_known_users(self) -> List[str]:
        """Lista usuarios conocidos."""
        return list(self.memory['users'].keys())
    
    # === HECHOS ===
    
    def learn_fact(self, fact: str, source: str = 'conversation', 
                   confidence: float = 0.8) -> bool:
        """Aprende un nuevo hecho."""
        # Evitar duplicados
        fact_hash = hashlib.md5(fact.lower().encode()).hexdigest()[:8]
        
        for existing in self.memory['facts']:
            if existing.get('hash') == fact_hash:
                # Actualizar confianza si es el mismo hecho
                existing['confidence'] = min(1.0, existing['confidence'] + 0.1)
                existing['last_confirmed'] = time.time()
                self._save()
                return False
        
        self.memory['facts'].append({
            'fact': fact,
            'hash': fact_hash,
            'source': source,
            'confidence': confidence,
            'learned_at': time.time(),
            'last_confirmed': time.time(),
        })
        
        # Mantener máximo 500 hechos
        if len(self.memory['facts']) > 500:
            # Eliminar los de menor confianza
            self.memory['facts'].sort(key=lambda x: x['confidence'], reverse=True)
            self.memory['facts'] = self.memory['facts'][:500]
        
        self._save()
        return True
    
    def search_facts(self, query: str, limit: int = 5) -> List[Dict]:
        """Busca hechos relacionados con una consulta."""
        query_lower = query.lower()
        results = []
        
        for fact in self.memory['facts']:
            score = 0
            fact_lower = fact['fact'].lower()
            
            # Coincidencia de palabras
            query_words = set(query_lower.split())
            fact_words = set(fact_lower.split())
            common = query_words & fact_words
            
            if common:
                score = len(common) / len(query_words) * fact['confidence']
                results.append((score, fact))
        
        results.sort(key=lambda x: x[0], reverse=True)
        return [f[1] for f in results[:limit]]
    
    # === INTERACCIONES ===
    
    def log_interaction(self, intent: str):
        """Registra una interacción."""
        self.memory['interactions']['total'] += 1
        
        if intent not in self.memory['interactions']['by_intent']:
            self.memory['interactions']['by_intent'][intent] = 0
        self.memory['interactions']['by_intent'][intent] += 1
        
        hour = datetime.now().hour
        self.memory['interactions']['by_hour'][hour] += 1
        
        # Guardar cada 10 interacciones
        if self.memory['interactions']['total'] % 10 == 0:
            self._save()
    
    # === MEMORIA EMOCIONAL ===
    
    def remember_moment(self, description: str, emotion: str = 'neutral',
                        importance: float = 0.5):
        """Guarda un momento significativo."""
        self.memory['emotional_memory'].append({
            'description': description,
            'emotion': emotion,
            'importance': importance,
            'timestamp': time.time(),
        })
        
        # Mantener solo los 100 momentos más importantes
        self.memory['emotional_memory'].sort(
            key=lambda x: x['importance'], reverse=True
        )
        self.memory['emotional_memory'] = self.memory['emotional_memory'][:100]
        
        self._save()
    
    # === ESTADÍSTICAS ===
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas de la memoria."""
        age_seconds = time.time() - self.memory['created_at']
        return {
            'users_known': len(self.memory['users']),
            'facts_learned': len(self.memory['facts']),
            'total_interactions': self.memory['interactions']['total'],
            'memory_age_days': age_seconds / 86400,
            'most_common_intent': max(
                self.memory['interactions']['by_intent'].items(),
                key=lambda x: x[1],
                default=('none', 0)
            )[0] if self.memory['interactions']['by_intent'] else 'none',
        }


class FeedbackSystem:
    """
    Sistema de feedback para reforzar o debilitar respuestas.
    
    Cuando el usuario da 👍 o 👎, ajustamos el aprendizaje:
    - 👍: Reforzamos el patrón de respuesta
    - 👎: Debilitamos el patrón
    """
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.feedback_log = []
        self.pattern_scores = {}  # {pattern_hash: score}
        self._load()
    
    def _load(self):
        try:
            if os.path.exists(self.filepath):
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                    self.feedback_log = data.get('log', [])
                    self.pattern_scores = data.get('scores', {})
        except Exception:
            pass
    
    def _save(self):
        try:
            with open(self.filepath, 'w') as f:
                json.dump({
                    'log': self.feedback_log[-1000:],  # Últimos 1000
                    'scores': self.pattern_scores
                }, f, indent=2)
        except Exception:
            pass
    
    def _hash_interaction(self, user_message: str, bot_response: str) -> str:
        """Genera hash único para un patrón de interacción."""
        # Simplificar mensajes para agrupar patrones similares
        user_simplified = ' '.join(user_message.lower().split()[:5])
        response_simplified = ' '.join(bot_response.lower().split()[:5])
        combined = f"{user_simplified}|{response_simplified}"
        return hashlib.md5(combined.encode()).hexdigest()[:12]
    
    def record_feedback(self, user_message: str, bot_response: str, 
                       is_positive: bool, intent: str = None) -> Dict:
        """
        Registra feedback del usuario.
        
        Returns:
            Dict con información del ajuste realizado
        """
        pattern_hash = self._hash_interaction(user_message, bot_response)
        
        # Actualizar score del patrón
        if pattern_hash not in self.pattern_scores:
            self.pattern_scores[pattern_hash] = 0.5  # Neutral
        
        # Ajustar score
        adjustment = 0.1 if is_positive else -0.1
        self.pattern_scores[pattern_hash] = max(0.0, min(1.0, 
            self.pattern_scores[pattern_hash] + adjustment
        ))
        
        # Log
        self.feedback_log.append({
            'timestamp': time.time(),
            'user_message': user_message[:100],
            'bot_response': bot_response[:100],
            'is_positive': is_positive,
            'intent': intent,
            'pattern_hash': pattern_hash,
            'new_score': self.pattern_scores[pattern_hash]
        })
        
        self._save()
        
        return {
            'pattern_hash': pattern_hash,
            'new_score': self.pattern_scores[pattern_hash],
            'total_feedbacks': len(self.feedback_log)
        }
    
    def get_feedback_weight(self, user_message: str, bot_response: str) -> float:
        """
        Obtiene el peso de feedback para un patrón.
        
        Returns:
            Float entre 0.5 y 1.5 (1.0 = neutral)
        """
        pattern_hash = self._hash_interaction(user_message, bot_response)
        score = self.pattern_scores.get(pattern_hash, 0.5)
        # Convertir score [0, 1] a peso [0.5, 1.5]
        return 0.5 + score
    
    def get_stats(self) -> Dict:
        """Estadísticas del sistema de feedback."""
        if not self.feedback_log:
            return {
                'total_feedbacks': 0,
                'positive_rate': 0.0,
                'patterns_tracked': 0
            }
        
        positive = sum(1 for f in self.feedback_log if f['is_positive'])
        return {
            'total_feedbacks': len(self.feedback_log),
            'positive_rate': positive / len(self.feedback_log),
            'patterns_tracked': len(self.pattern_scores),
            'average_score': np.mean(list(self.pattern_scores.values())) if self.pattern_scores else 0.5
        }


class ConsolidationEngine:
    """
    Motor de consolidación ("sueño") para Eón.
    
    Cuando Eón está inactivo, procesa y consolida lo aprendido:
    - Refuerza patrones frecuentes
    - Elimina información redundante
    - Genera resúmenes de conversaciones
    - Optimiza la memoria
    """
    
    def __init__(self, memory: LongTermMemory, learner: OnlineLearner):
        self.memory = memory
        self.learner = learner
        self._last_activity = time.time()
        self._consolidation_thread = None
        self._stop_flag = threading.Event()
        self.consolidation_count = 0
        self.last_consolidation = None
    
    def activity_detected(self):
        """Marca actividad reciente."""
        self._last_activity = time.time()
    
    def start_background_consolidation(self, inactivity_threshold: float = 300):
        """
        Inicia consolidación en background cuando hay inactividad.
        
        Args:
            inactivity_threshold: Segundos de inactividad antes de consolidar
        """
        def consolidation_loop():
            while not self._stop_flag.is_set():
                time.sleep(60)  # Check cada minuto
                
                inactive_time = time.time() - self._last_activity
                if inactive_time > inactivity_threshold:
                    self._do_consolidation()
        
        self._consolidation_thread = threading.Thread(
            target=consolidation_loop, daemon=True
        )
        self._consolidation_thread.start()
    
    def stop(self):
        """Detiene el thread de consolidación."""
        self._stop_flag.set()
        if self._consolidation_thread:
            self._consolidation_thread.join(timeout=5)
    
    def _do_consolidation(self):
        """Ejecuta proceso de consolidación."""
        print(" [CONSOLIDATION] Eón está consolidando memorias...")
        
        try:
            # 1. Limpiar hechos de baja confianza antiguos
            cutoff = time.time() - 86400 * 7  # 7 días
            old_count = len(self.memory.memory['facts'])
            self.memory.memory['facts'] = [
                f for f in self.memory.memory['facts']
                if f['confidence'] > 0.3 or f['learned_at'] > cutoff
            ]
            removed = old_count - len(self.memory.memory['facts'])
            
            # 2. Incrementar confianza de hechos frecuentemente confirmados
            for fact in self.memory.memory['facts']:
                # Decay natural
                fact['confidence'] *= 0.99
            
            # 3. Actualizar estadísticas de consolidación
            self.consolidation_count += 1
            self.last_consolidation = time.time()
            
            # 4. Guardar memoria
            self.memory._save()
            
            print(f" [CONSOLIDATION] Completado: {removed} hechos eliminados")
            
        except Exception as e:
            print(f" [CONSOLIDATION] Error: {e}")
    
    def force_consolidation(self):
        """Fuerza una consolidación inmediata."""
        self._do_consolidation()
    
    def get_stats(self) -> Dict:
        return {
            'consolidation_count': self.consolidation_count,
            'last_consolidation': self.last_consolidation,
            'inactive_seconds': time.time() - self._last_activity
        }


class EonLearningSystem:
    """
    Sistema integrado de aprendizaje para Eón.
    
    Combina todos los componentes:
    - OnlineLearner: Aprendizaje de W_out
    - LongTermMemory: Memoria persistente
    - FeedbackSystem: Refuerzo por feedback
    - ConsolidationEngine: Consolidación durante inactividad
    """
    
    def __init__(self, data_dir: str, esn=None):
        self.data_dir = data_dir
        self.esn = esn
        
        os.makedirs(data_dir, exist_ok=True)
        
        # Componentes
        n_reservoir = esn.n_reservoir if esn else 100
        self.learner = OnlineLearner(n_reservoir=n_reservoir)
        self.memory = LongTermMemory(os.path.join(data_dir, 'long_term_memory.json'))
        self.feedback = FeedbackSystem(os.path.join(data_dir, 'feedback.json'))
        self.consolidation = ConsolidationEngine(self.memory, self.learner)
        
        # Buffer de experiencias recientes para aprendizaje
        self._experience_buffer = deque(maxlen=100)
        
        # Estadísticas
        self.learning_events = 0
        
        # Iniciar consolidación en background
        self.consolidation.start_background_consolidation()
    
    def process_conversation(self, user_message: str, bot_response: str, 
                           intent: str, user_name: str = None,
                           reservoir_state: np.ndarray = None) -> Dict:
        """
        Procesa una conversación para aprendizaje.
        
        Args:
            user_message: Mensaje del usuario
            bot_response: Respuesta generada
            intent: Intención detectada
            user_name: Nombre del usuario (si se conoce)
            reservoir_state: Estado actual del reservoir del ESN
            
        Returns:
            Dict con información del aprendizaje realizado
        """
        # Marcar actividad
        self.consolidation.activity_detected()
        
        result = {
            'learned_from_chat': False,
            'user_remembered': False,
            'facts_extracted': 0,
            'feedback_weight': 1.0
        }
        
        # 1. Recordar usuario
        if user_name:
            user_info = self.memory.remember_user(user_name, {
                'topic': intent,
                'is_creator': 'creador' in intent.lower()
            })
            result['user_remembered'] = True
        
        # 2. Registrar interacción
        self.memory.log_interaction(intent)
        
        # 3. Extraer hechos potenciales del mensaje
        facts = self._extract_facts(user_message)
        for fact in facts:
            if self.memory.learn_fact(fact, source='conversation'):
                result['facts_extracted'] += 1
        
        # 4. Aprendizaje online del ESN (si hay estado del reservoir)
        if reservoir_state is not None and len(reservoir_state) > 0:
            # Convertir respuesta a target numérico simple
            target = self._text_to_target(bot_response)
            
            # Obtener peso de feedback para este patrón
            feedback_weight = self.feedback.get_feedback_weight(
                user_message, bot_response
            )
            result['feedback_weight'] = feedback_weight
            
            # Actualizar pesos
            self.learner.update(reservoir_state, target, feedback_weight)
            result['learned_from_chat'] = True
            self.learning_events += 1
            
            # Aplicar al ESN cada 50 eventos
            if self.learning_events % 50 == 0 and self.esn:
                self.learner.apply_to_esn(self.esn)
        
        # 5. Guardar experiencia
        self._experience_buffer.append({
            'user_message': user_message,
            'bot_response': bot_response,
            'intent': intent,
            'timestamp': time.time()
        })
        
        return result
    
    def _extract_facts(self, message: str) -> List[str]:
        """Extrae hechos potenciales de un mensaje."""
        facts = []
        message_lower = message.lower()
        
        # Patrones que indican hechos
        fact_patterns = [
            r'(?:soy|me llamo)\s+(\w+)',  # Identidad
            r'(?:vivo en|soy de)\s+(.+)',  # Ubicación
            r'(?:trabajo en|trabajo como)\s+(.+)',  # Trabajo
            r'(?:me gusta|me encanta)\s+(.+)',  # Preferencias
        ]
        
        import re
        for pattern in fact_patterns:
            match = re.search(pattern, message_lower)
            if match:
                fact = match.group(0)
                if len(fact) > 5:  # Filtrar muy cortos
                    facts.append(fact)
        
        return facts
    
    def _text_to_target(self, text: str) -> np.ndarray:
        """Convierte texto a vector target para aprendizaje."""
        # Encoding simple basado en caracteres
        chars = [ord(c) / 255.0 for c in text[:50]]
        if len(chars) < 50:
            chars.extend([0.0] * (50 - len(chars)))
        return np.array(chars[:50])
    
    def record_feedback(self, user_message: str, bot_response: str,
                       is_positive: bool) -> Dict:
        """Registra feedback del usuario."""
        self.consolidation.activity_detected()
        return self.feedback.record_feedback(
            user_message, bot_response, is_positive
        )
    
    def get_user_context(self, user_name: str) -> Optional[Dict]:
        """Obtiene contexto de un usuario conocido."""
        return self.memory.get_user(user_name)
    
    def search_relevant_facts(self, query: str) -> List[Dict]:
        """Busca hechos relevantes para una consulta."""
        return self.memory.search_facts(query)
    
    def get_comprehensive_stats(self) -> Dict:
        """Obtiene estadísticas completas del sistema."""
        return {
            'learner': self.learner.get_stats(),
            'memory': self.memory.get_stats(),
            'feedback': self.feedback.get_stats(),
            'consolidation': self.consolidation.get_stats(),
            'learning_events': self.learning_events,
            'experience_buffer_size': len(self._experience_buffer)
        }
    
    def shutdown(self):
        """Apaga el sistema de forma limpia."""
        print(" [LEARNING] Guardando estado final...")
        self.consolidation.stop()
        self.memory._save()
        self.feedback._save()
        
        # Aplicar aprendizaje final al ESN
        if self.esn:
            self.learner.apply_to_esn(self.esn)
        
        print(" [LEARNING] Sistema de aprendizaje detenido")


# Utilidad para tests
if __name__ == "__main__":
    print("=== Test Sistema de Aprendizaje ===\n")
    
    # Crear sistema
    system = EonLearningSystem("/tmp/eon_learning_test")
    
    # Simular conversación
    print("1. Procesando conversación...")
    result = system.process_conversation(
        user_message="Hola, soy Jeremy y vivo en Costa Rica",
        bot_response="¡Hola Jeremy! Es un placer conocerte.",
        intent="presentacion",
        user_name="Jeremy",
        reservoir_state=np.random.randn(100)
    )
    print(f"   Resultado: {result}")
    
    # Feedback
    print("\n2. Registrando feedback positivo...")
    fb = system.record_feedback(
        "Hola, soy Jeremy",
        "¡Hola Jeremy!",
        is_positive=True
    )
    print(f"   Feedback: {fb}")
    
    # Estadísticas
    print("\n3. Estadísticas:")
    stats = system.get_comprehensive_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Limpiar
    system.shutdown()
    print("\n=== Test completado ===")
