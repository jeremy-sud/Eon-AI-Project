"""
Proyecto Eón - Utilidades Compartidas
=====================================

Módulos de utilidades para evitar código duplicado.
"""

from .matrix_init import (
    create_reservoir_matrix,
    generate_birth_hash,
    compute_spectral_radius
)

__all__ = [
    'create_reservoir_matrix',
    'generate_birth_hash', 
    'compute_spectral_radius'
]
