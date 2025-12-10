# Plasticity module - Proyecto Eón
# Plasticidad sináptica y protocolos de adaptación

from .hebbian import HebbianESN, compare_plasticity_types
from .tzimtzum import (
    TzimtzumESN, 
    TzimtzumConfig, 
    TzimtzumState, 
    TzimtzumMixin,
    ContractionPhase
)
from .hebbian_tzimtzum import HebbianTzimtzumESN

__all__ = [
    # Hebbian
    'HebbianESN',
    'compare_plasticity_types',
    # Tzimtzum
    'TzimtzumESN',
    'TzimtzumConfig',
    'TzimtzumState',
    'TzimtzumMixin',
    'ContractionPhase',
    # Combined
    'HebbianTzimtzumESN',
]
