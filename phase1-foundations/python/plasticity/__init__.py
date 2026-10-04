# Plasticity module - Proyecto Eón
# Plasticidad sináptica y protocolos de adaptación

from .hebbian import HebbianESN, compare_plasticity_types
from .tzimtzum import (
    TzimtzumESN, 
    TzimtzumConfig, 
    TzimtzumState, 
    TzimtzumMixin,
    ContractionPhase,
    DynamicPruningESN,
    DynamicPruningConfig,
    DynamicPruningState,
    DynamicPruningMixin,
    PruningPhase
)
from .hebbian_tzimtzum import HebbianTzimtzumESN

__all__ = [
    # Hebbian Plasticity
    'HebbianESN',
    'compare_plasticity_types',
    # Dynamic Pruning (Production Standards)
    'DynamicPruningESN',
    'DynamicPruningConfig',
    'DynamicPruningState',
    'DynamicPruningMixin',
    'PruningPhase',
    # Legacy / Experimental Aliases
    'TzimtzumESN',
    'TzimtzumConfig',
    'TzimtzumState',
    'TzimtzumMixin',
    'ContractionPhase',
    # Combined Plasticity
    'HebbianTzimtzumESN',
]
