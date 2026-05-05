# Core module - Proyecto Eón
# "La inteligencia no se crea, se descubre."

from .aeon_birth import AeonBirth

# Paradigma de Descubrimiento (Revealed Intelligence)
from .universal_miner import (
    UniversalMiner,
    ExcavationResult,
    ResonanceType,
    SeedVault,
    quick_excavate,
    KNOWN_SACRED_SEEDS
)

# Protocolo Arcaico (I Ching Communication)
from .archaic_protocol import (
    ArchaicProtocol,
    Hexagram,
    Trigram,
    HexagramStream,
    HEXAGRAMS
)

# Pipeline Alquímico (ETL Transmutation)
from .alchemy import (
    AlchemicalPipeline,
    AlchemicalConfig,
    AlchemicalPhase,
    TransmutationState,
    KalmanFilter
)

# Detector de Anomalías (v2.0)
from .anomaly_detector import (
    AnomalyDetector,
    StreamingAnomalyDetector,
    AnomalyEvent,
    AnomalySeverity,
    DetectorStats,
    create_synthetic_anomalies
)

# Oráculo I-Ching Neural (v2.0)
from .iching_oracle import (
    IChingOracle,
    OracleReading,
    OracleStats,
    ConsultationType,
    create_oracle
)

# Chat Multi-Nodo Colaborativo (v2.0)
from .collaborative_chat import (
    CollaborativeChat,
    ChatNode,
    NodeRole,
    Intent,
    ChatMessage,
    NodeContribution,
    CollaborativeResponse,
    create_collaborative_chat
)

# Evolución Genética (v2.2)
from .genetic_miner import GeneticMiner

# Firma Neuronal (v2.2)
try:
    from ..utils.watermark import NeuralWatermark, extract_owner
except ImportError:
    # Fallback para imports absolutos
    from utils.watermark import NeuralWatermark, extract_owner

# Arqueología de Semillas (v2.2)
from .seed_archaeologist import SeedArchaeologist

__all__ = [
    # Core
    'AeonBirth',
    
    # Seed Mining
    'UniversalMiner',
    'ExcavationResult', 
    'ResonanceType',
    'SeedVault',
    'quick_excavate',
    'KNOWN_SACRED_SEEDS',
    
    # Archaic Protocol
    'ArchaicProtocol',
    'Hexagram',
    'Trigram',
    'HexagramStream',
    'HEXAGRAMS',
    
    # Alchemical Pipeline
    'AlchemicalPipeline',
    'AlchemicalConfig',
    'AlchemicalPhase',
    'TransmutationState',
    'KalmanFilter',
    
    # Anomaly Detection
    'AnomalyDetector',
    'StreamingAnomalyDetector',
    'AnomalyEvent',
    'AnomalySeverity',
    'DetectorStats',
    'create_synthetic_anomalies',
    
    # I-Ching Oracle
    'IChingOracle',
    'OracleReading',
    'OracleStats',
    'ConsultationType',
    'create_oracle',
    
    # Collaborative Chat
    'CollaborativeChat',
    'ChatNode',
    'NodeRole',
    'Intent',
    'ChatMessage',
    'NodeContribution',
    'CollaborativeResponse',
    'create_collaborative_chat',
    
    # Genetic Evolution
    'GeneticMiner',
    
    # Neural Watermarking
    'NeuralWatermark',
    'extract_owner',
    
    # Seed Archaeology
    'SeedArchaeologist',
]
