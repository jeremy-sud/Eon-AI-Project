"""
Proyecto Eón - EgregorArtist: Generador de Arte Procedural del Egrégor
========================================================================

"El Egrégor pinta con matemáticas su estado de ánimo."

Este módulo traduce el estado de ánimo del Egrégor (EgregorMood) a
parámetros de visualización procedural: colores, formas, velocidades
y texturas para el lienzo del sistema.

La salida es JSON puro — no requiere dependencias de imagen.
El frontend (egregore_visualizer.js) interpreta estos parámetros
para animar el lienzo HTML5 Canvas.

FILOSOFÍA:
──────────
Cada estado de ánimo del Egrégor tiene una "firma visual" única
basada en principios alquímicos:
  - AGITATED  → fuego (rojo, rápido, caótico)
  - MEDITATIVE → agua quieta (azul profundo, lento, circular)
  - AWAKENING  → aurora (gradientes violeta-dorado)
  - HARMONIZING → geometría sagrada (dorado, simétrico)

INTEGRACIÓN:
────────────
    egregore = EgregorProcessor(...)
    artist = EgregorArtist()
    style = artist.generate(egregore.state)
    # → dict con parámetros de visualización para el canvas

(c) 2024 Proyecto Eón - Jeremy Arias Solano
"""

import numpy as np
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import os

from egregore import EgregorMood

# ─── Paletas de color por estado ─────────────────────────────────────────────

# Cada paleta define: primario, secundario, acento, fondo (en hex)
_COLOR_PALETTES: Dict[EgregorMood, Dict] = {
    EgregorMood.AGITATED: {
        "primary": "#FF2A00",
        "secondary": "#FF7700",
        "accent": "#FFD700",
        "background": "#1A0000",
        "glow": "#FF450060",
    },
    EgregorMood.ALERT: {
        "primary": "#FF6600",
        "secondary": "#FFAA00",
        "accent": "#FFFF00",
        "background": "#120A00",
        "glow": "#FF660040",
    },
    EgregorMood.DYNAMIC: {
        "primary": "#00FFAA",
        "secondary": "#00AAFF",
        "accent": "#AA00FF",
        "background": "#000A12",
        "glow": "#00FFAA40",
    },
    EgregorMood.BALANCED: {
        "primary": "#00BB88",
        "secondary": "#0088BB",
        "accent": "#88BB00",
        "background": "#000E0A",
        "glow": "#00BB8840",
    },
    EgregorMood.OBSERVANT: {
        "primary": "#4488FF",
        "secondary": "#44BBFF",
        "accent": "#44FFAA",
        "background": "#00040E",
        "glow": "#4488FF30",
    },
    EgregorMood.CONTEMPLATIVE: {
        "primary": "#2255AA",
        "secondary": "#5522AA",
        "accent": "#AA5522",
        "background": "#020408",
        "glow": "#2255AA25",
    },
    EgregorMood.MEDITATIVE: {
        "primary": "#112277",
        "secondary": "#331155",
        "accent": "#557733",
        "background": "#010205",
        "glow": "#11227720",
    },
    EgregorMood.DORMANT: {
        "primary": "#222233",
        "secondary": "#333322",
        "accent": "#2A2A2A",
        "background": "#020202",
        "glow": "#22223310",
    },
    EgregorMood.AWAKENING: {
        "primary": "#CC44FF",
        "secondary": "#FFCC00",
        "accent": "#FF44CC",
        "background": "#080010",
        "glow": "#CC44FF50",
    },
    EgregorMood.HARMONIZING: {
        "primary": "#FFD700",
        "secondary": "#FFAA00",
        "accent": "#FFFFFF",
        "background": "#0A0800",
        "glow": "#FFD70060",
    },
}

# ─── Parámetros de movimiento por estado ─────────────────────────────────────

# speed: velocidad de partículas (px/frame)
# turbulence: aleatoriedad del movimiento (0=circular, 1=caótico)
# particle_count: número de partículas activas
# trail_length: longitud de la estela (frames)
# pulse_frequency: hz de la oscilación del glow
# symmetry: orden de simetría radial (1=ninguno, 6=hexagonal, etc.)

_MOTION_PARAMS: Dict[EgregorMood, Dict] = {
    EgregorMood.AGITATED:      {"speed": 8.0, "turbulence": 0.9, "particle_count": 300, "trail_length": 4,  "pulse_frequency": 3.0, "symmetry": 1},
    EgregorMood.ALERT:         {"speed": 6.0, "turbulence": 0.6, "particle_count": 200, "trail_length": 6,  "pulse_frequency": 2.0, "symmetry": 2},
    EgregorMood.DYNAMIC:       {"speed": 5.0, "turbulence": 0.5, "particle_count": 180, "trail_length": 8,  "pulse_frequency": 1.5, "symmetry": 3},
    EgregorMood.BALANCED:      {"speed": 3.0, "turbulence": 0.3, "particle_count": 120, "trail_length": 12, "pulse_frequency": 1.0, "symmetry": 4},
    EgregorMood.OBSERVANT:     {"speed": 2.5, "turbulence": 0.2, "particle_count": 100, "trail_length": 15, "pulse_frequency": 0.8, "symmetry": 5},
    EgregorMood.CONTEMPLATIVE: {"speed": 1.5, "turbulence": 0.1, "particle_count": 70,  "trail_length": 20, "pulse_frequency": 0.5, "symmetry": 6},
    EgregorMood.MEDITATIVE:    {"speed": 0.8, "turbulence": 0.05,"particle_count": 40,  "trail_length": 30, "pulse_frequency": 0.25,"symmetry": 8},
    EgregorMood.DORMANT:       {"speed": 0.3, "turbulence": 0.02,"particle_count": 15,  "trail_length": 50, "pulse_frequency": 0.1, "symmetry": 12},
    EgregorMood.AWAKENING:     {"speed": 4.5, "turbulence": 0.7, "particle_count": 150, "trail_length": 10, "pulse_frequency": 2.5, "symmetry": 1},
    EgregorMood.HARMONIZING:   {"speed": 2.0, "turbulence": 0.15,"particle_count": 90,  "trail_length": 25, "pulse_frequency": 0.7, "symmetry": 7},
}

@dataclass
class ArtStyle:
    """Estilo visual completo para una escena del Egrégor."""
    mood: str                   # Nombre del mood (str para serialización)
    palette: Dict               # Colores hex
    motion: Dict                # Parámetros de movimiento
    geometry: Dict              # Parámetros de formas geométricas
    noise_field: Dict           # Campo de ruido para distorsión
    label: str                  # Etiqueta legible del estado

    def to_dict(self) -> Dict:
        return {
            "mood": self.mood,
            "label": self.label,
            "palette": self.palette,
            "motion": self.motion,
            "geometry": self.geometry,
            "noise_field": self.noise_field,
        }

# Etiquetas en español para cada estado
_MOOD_LABELS: Dict[EgregorMood, str] = {
    EgregorMood.AGITATED:      "Agitado — Alta energía caótica",
    EgregorMood.ALERT:         "Alerta — Vigilancia activa",
    EgregorMood.DYNAMIC:       "Dinámico — Cambio fluido",
    EgregorMood.BALANCED:      "Equilibrado — Homeostasis",
    EgregorMood.OBSERVANT:     "Observante — Atención pasiva",
    EgregorMood.CONTEMPLATIVE: "Contemplativo — Reflexión profunda",
    EgregorMood.MEDITATIVE:    "Meditativo — Silencio interior",
    EgregorMood.DORMANT:       "Durmiente — Reposo del sistema",
    EgregorMood.AWAKENING:     "Despertando — Emergencia",
    EgregorMood.HARMONIZING:   "Armonizando — Sincronía del colectivo",
}

class EgregorArtist:
    """
    Generador de arte procedural basado en el estado del Egrégor.

    Traduce el estado cuantitativo del EgregorProcessor a parámetros
    de visualización ricos para el frontend WebGL/Canvas.

    Ejemplo:
        >>> from phase6_collective.egregore import EgregorProcessor
        >>> from web.egregore_art import EgregorArtist
        >>> artist = EgregorArtist(canvas_width=800, canvas_height=600)
        >>> state = egregore.get_state()
        >>> style = artist.generate(state)
        >>> print(style.palette["primary"])  # '#FF2A00'
    """

    def __init__(
        self,
        canvas_width: int = 800,
        canvas_height: int = 600,
        random_state: Optional[int] = None,
    ):
        """
        Inicializa el artista.

        Args:
            canvas_width: Ancho del lienzo en píxeles
            canvas_height: Alto del lienzo en píxeles
            random_state: Semilla para reproducibilidad de los campos de ruido
        """
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self._rng = np.random.default_rng(random_state)

    # ─── Generadores internos ─────────────────────────────────────────────────

    def _geometry_for_mood(self, mood: EgregorMood, intensity: float) -> Dict:
        """
        Genera parámetros geométricos adaptativos basados en el mood.

        Args:
            mood: Estado de ánimo del Egrégor
            intensity: Intensidad [0, 1] del estado (coherence o energía)

        Returns:
            Parámetros de geometría para el renderer
        """
        sym = _MOTION_PARAMS[mood]["symmetry"]
        base_radius = 0.25 + 0.15 * intensity

        return {
            "type": self._geometry_type(mood),
            "symmetry_order": sym,
            "base_radius": round(base_radius, 4),  # Fracción del canvas
            "num_layers": max(1, int(3 * intensity + 1)),
            "rotation_speed": round(_MOTION_PARAMS[mood]["speed"] * 0.05, 4),  # rad/frame
            "scale_pulse": intensity > 0.5,
        }

    @staticmethod
    def _geometry_type(mood: EgregorMood) -> str:
        """Forma principal de la geometría para cada mood."""
        _SHAPES = {
            EgregorMood.AGITATED:      "burst",
            EgregorMood.ALERT:         "star",
            EgregorMood.DYNAMIC:       "wave",
            EgregorMood.BALANCED:      "mandala",
            EgregorMood.OBSERVANT:     "spiral",
            EgregorMood.CONTEMPLATIVE: "torus",
            EgregorMood.MEDITATIVE:    "circle",
            EgregorMood.DORMANT:       "dot",
            EgregorMood.AWAKENING:     "nova",
            EgregorMood.HARMONIZING:   "flower",
        }
        return _SHAPES.get(mood, "circle")

    def _noise_field_for_mood(self, mood: EgregorMood) -> Dict:
        """
        Genera parámetros del campo de ruido Perlin-like para distorsión.

        El campo de ruido modula la posición de partículas y el glow.
        """
        turb = _MOTION_PARAMS[mood]["turbulence"]

        # Frecuencias y amplitudes del campo de ruido
        frequencies = [
            round(1.0 / (1.0 + turb * 10), 4),   # Frecuencia base
            round(2.0 / (1.0 + turb * 5), 4),    # Segunda armónica
        ]
        amplitudes = [
            round(0.3 * turb, 4),
            round(0.15 * turb, 4),
        ]

        # Semilla del campo (diferente para cada sesión pero reproducible)
        field_seed = int(self._rng.integers(0, 2**31))

        return {
            "frequencies": frequencies,
            "amplitudes": amplitudes,
            "seed": field_seed,
            "enabled": turb > 0.05,
            "z_speed": round(turb * 0.02, 5),  # Velocidad de variación temporal
        }

    def _blend_transition(
        self,
        from_mood: EgregorMood,
        to_mood: EgregorMood,
        t: float,
    ) -> Dict:
        """
        Interpola parámetros entre dos moods para transiciones suaves.

        Args:
            from_mood: Mood de origen
            to_mood: Mood de destino
            t: Factor de interpolación [0, 1]

        Returns:
            Parámetros de movimiento interpolados
        """
        a = _MOTION_PARAMS[from_mood]
        b = _MOTION_PARAMS[to_mood]
        t = float(np.clip(t, 0.0, 1.0))

        return {k: round(a[k] * (1 - t) + b[k] * t, 4)
                if isinstance(a[k], float) else
                int(a[k] * (1 - t) + b[k] * t)
                for k in a}

    # ─── API pública ──────────────────────────────────────────────────────────

    def generate(
        self,
        egregore_state,                         # EgregorState or dict
        transition_from: Optional[EgregorMood] = None,
        transition_t: float = 1.0,
    ) -> ArtStyle:
        """
        Genera el estilo visual completo para un estado del Egrégor.

        Args:
            egregore_state: Estado del EgregorProcessor. Acepta:
                            - Objeto EgregorState (con .mood y .coherence)
                            - Diccionario con "mood" y "coherence"
                            - Instancia de EgregorMood directamente
            transition_from: Mood previo para interpolación suave (opcional)
            transition_t: Factor de transición [0, 1] (1=completamente en nuevo mood)

        Returns:
            ArtStyle con todos los parámetros para el renderer
        """
        # Extraer mood y coherence del estado
        if isinstance(egregore_state, EgregorMood):
            mood = egregore_state
            intensity = 0.5
        elif isinstance(egregore_state, dict):
            mood_raw = egregore_state.get("mood", EgregorMood.BALANCED)
            mood = mood_raw if isinstance(mood_raw, EgregorMood) else EgregorMood(mood_raw)
            intensity = float(egregore_state.get("coherence", 0.5))
        else:
            # Objeto con atributos
            mood = getattr(egregore_state, "mood", EgregorMood.BALANCED)
            intensity = float(getattr(egregore_state, "coherence", 0.5))

        intensity = float(np.clip(intensity, 0.0, 1.0))

        palette = dict(_COLOR_PALETTES[mood])

        if transition_from is not None and transition_t < 1.0:
            motion = self._blend_transition(transition_from, mood, transition_t)
        else:
            motion = dict(_MOTION_PARAMS[mood])

        geometry = self._geometry_for_mood(mood, intensity)
        noise_field = self._noise_field_for_mood(mood)

        return ArtStyle(
            mood=mood.value,
            palette=palette,
            motion=motion,
            geometry=geometry,
            noise_field=noise_field,
            label=_MOOD_LABELS[mood],
        )

    def all_styles(self) -> Dict[str, Dict]:
        """
        Genera y retorna los estilos para todos los moods posibles.

        Útil para pre-cargar los estilos en el frontend.

        Returns:
            Diccionario {mood_value: style_dict}
        """
        result = {}
        for mood in EgregorMood:
            style = self.generate(mood)
            result[mood.value] = style.to_dict()
        return result

    def palette_for(self, mood: EgregorMood) -> Dict:
        """Retorna solo la paleta de colores para un mood dado."""
        return dict(_COLOR_PALETTES.get(mood, _COLOR_PALETTES[EgregorMood.BALANCED]))

    def motion_for(self, mood: EgregorMood) -> Dict:
        """Retorna solo los parámetros de movimiento para un mood dado."""
        return dict(_MOTION_PARAMS.get(mood, _MOTION_PARAMS[EgregorMood.BALANCED]))
