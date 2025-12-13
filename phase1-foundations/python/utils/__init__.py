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

from .portable_rng import (
    Xorshift32,
    create_portable_rng,
    generate_birth_hash_portable,
    verify_cross_platform_compatibility
)

__all__ = [
    # matrix_init
    'create_reservoir_matrix',
    'generate_birth_hash', 
    'compute_spectral_radius',
    # portable_rng
    'Xorshift32',
    'create_portable_rng',
    'generate_birth_hash_portable',
    'verify_cross_platform_compatibility'
]
