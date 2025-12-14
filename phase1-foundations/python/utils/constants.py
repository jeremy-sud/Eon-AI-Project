"""
Proyecto Eón - Constantes Globales
==================================

Constantes compartidas entre todos los módulos para garantizar
consistencia y facilitar el mantenimiento.

(c) 2024 Sistemas Ursol - Jeremy Arias Solano
"""

# ============================================================================
# CONSTANTES NUMÉRICAS
# ============================================================================

# Epsilon para evitar división por cero y problemas de estabilidad numérica
# Usado en: log, división, normalización
EPSILON = 1e-10

# Epsilon para comparaciones de punto flotante
FLOAT_TOLERANCE = 1e-8

# Regularización por defecto para Ridge Regression
DEFAULT_REGULARIZATION = 1e-6


# ============================================================================
# LÍMITES DE ESN
# ============================================================================

# Radio espectral máximo permitido (>1 puede causar inestabilidad)
MAX_SPECTRAL_RADIUS = 2.0

# Tamaño máximo de reservoir recomendado (para eficiencia)
MAX_RESERVOIR_SIZE = 10000

# Período de washout mínimo recomendado
MIN_WASHOUT = 10


# ============================================================================
# CONFIGURACIÓN DE RED
# ============================================================================

# Tamaño de buffer por defecto para streaming
DEFAULT_BUFFER_SIZE = 1000

# Tamaño máximo de historial de chat
MAX_CHAT_HISTORY = 100

# Cooldown por defecto para alertas de anomalía (segundos)
DEFAULT_ANOMALY_COOLDOWN = 5.0


# ============================================================================
# UMBRALES DE DETECCIÓN
# ============================================================================

# Z-score para detección de anomalías
ANOMALY_THRESHOLD_SIGMA = 3.0
WARNING_THRESHOLD_SIGMA = 2.0
CRITICAL_THRESHOLD_SIGMA = 5.0

# Umbral de saturación de estado (para advertencias)
STATE_SATURATION_THRESHOLD = 0.9


# ============================================================================
# FORMATO DE ARCHIVOS
# ============================================================================

# Versión del formato de guardado de Eón
SAVE_FORMAT_VERSION = "2.0"

# Extensiones de archivo
ESN_STATE_EXTENSION = ".npz"
METADATA_EXTENSION = ".json"
LEGACY_STATE_EXTENSION = ".pkl"
