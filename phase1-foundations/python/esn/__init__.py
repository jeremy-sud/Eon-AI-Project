"""ESN Package - Proyecto Eón"""
from .esn import EchoStateNetwork, generate_mackey_glass
from .recursive_esn import RecursiveEchoStateNetwork, MicroReservoir

from .stability_guard import StabilityGuard
from .memory_tuner import compute_memory_capacity, analyze_signal_autocorrelation, auto_tune_esn_parameters

__all__ = [
    'EchoStateNetwork', 
    'generate_mackey_glass',
    'RecursiveEchoStateNetwork',
    'MicroReservoir',
    'StabilityGuard',
    'compute_memory_capacity',
    'analyze_signal_autocorrelation',
    'auto_tune_esn_parameters',
]
