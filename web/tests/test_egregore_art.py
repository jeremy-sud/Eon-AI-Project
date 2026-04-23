"""
Tests para EgregorArtist - Proyecto Eón
=========================================

Tests del generador de arte procedural del Egrégor.
"""

import pytest
import sys
import os

_test_dir = os.path.dirname(os.path.abspath(__file__))
_web_dir = os.path.dirname(_test_dir)
_root_dir = os.path.dirname(_web_dir)
_phase6_dir = os.path.join(_root_dir, "phase6-collective")

for _p in (_web_dir, _phase6_dir, _root_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from egregore_art import (
    EgregorArtist,
    ArtStyle,
    EgregorMood,
    _COLOR_PALETTES,
    _MOTION_PARAMS,
    _MOOD_LABELS,
)


@pytest.fixture(scope="module")
def artist():
    return EgregorArtist(canvas_width=800, canvas_height=600, random_state=42)


# ─── Tests de paletas ─────────────────────────────────────────────────────────

class TestColorPalettes:
    def test_all_moods_have_palette(self):
        for mood in EgregorMood:
            assert mood in _COLOR_PALETTES

    def test_palette_has_required_keys(self):
        for mood, palette in _COLOR_PALETTES.items():
            assert "primary" in palette
            assert "secondary" in palette
            assert "accent" in palette
            assert "background" in palette

    def test_colors_are_hex(self):
        for palette in _COLOR_PALETTES.values():
            for key in ("primary", "secondary", "accent", "background"):
                assert palette[key].startswith("#")


# ─── Tests de motion params ───────────────────────────────────────────────────

class TestMotionParams:
    def test_all_moods_have_motion(self):
        for mood in EgregorMood:
            assert mood in _MOTION_PARAMS

    def test_motion_has_required_keys(self):
        required = {"speed", "turbulence", "particle_count", "trail_length",
                    "pulse_frequency", "symmetry"}
        for mood, motion in _MOTION_PARAMS.items():
            assert required.issubset(set(motion.keys()))

    def test_speed_positive(self):
        for motion in _MOTION_PARAMS.values():
            assert motion["speed"] > 0

    def test_turbulence_in_range(self):
        for motion in _MOTION_PARAMS.values():
            assert 0.0 <= motion["turbulence"] <= 1.0

    def test_agitated_faster_than_dormant(self):
        assert _MOTION_PARAMS[EgregorMood.AGITATED]["speed"] > _MOTION_PARAMS[EgregorMood.DORMANT]["speed"]

    def test_meditative_has_high_symmetry(self):
        assert _MOTION_PARAMS[EgregorMood.MEDITATIVE]["symmetry"] >= 8


# ─── Tests de generate() con EgregorMood ─────────────────────────────────────

class TestGenerateFromMood:
    def test_returns_art_style(self, artist):
        style = artist.generate(EgregorMood.BALANCED)
        assert isinstance(style, ArtStyle)

    def test_mood_matches(self, artist):
        style = artist.generate(EgregorMood.AGITATED)
        assert style.mood == "agitated"

    def test_palette_present(self, artist):
        style = artist.generate(EgregorMood.MEDITATIVE)
        assert "primary" in style.palette

    def test_motion_present(self, artist):
        style = artist.generate(EgregorMood.DYNAMIC)
        assert "speed" in style.motion

    def test_geometry_present(self, artist):
        style = artist.generate(EgregorMood.HARMONIZING)
        assert "type" in style.geometry

    def test_noise_field_present(self, artist):
        style = artist.generate(EgregorMood.AWAKENING)
        assert "frequencies" in style.noise_field

    def test_label_not_empty(self, artist):
        style = artist.generate(EgregorMood.CONTEMPLATIVE)
        assert len(style.label) > 0


# ─── Tests de generate() con dict ────────────────────────────────────────────

class TestGenerateFromDict:
    def test_generate_from_dict(self, artist):
        state = {"mood": "alert", "coherence": 0.8}
        style = artist.generate(state)
        assert style.mood == "alert"

    def test_intensity_affects_geometry(self, artist):
        low_style = artist.generate({"mood": "balanced", "coherence": 0.1})
        high_style = artist.generate({"mood": "balanced", "coherence": 0.9})
        # Mayor coherencia → más capas geométricas
        assert high_style.geometry["num_layers"] >= low_style.geometry["num_layers"]

    def test_missing_coherence_defaults(self, artist):
        style = artist.generate({"mood": "dormant"})
        assert style.mood == "dormant"


# ─── Tests de to_dict() ──────────────────────────────────────────────────────

class TestArtStyleToDict:
    def test_to_dict_has_mood(self, artist):
        style = artist.generate(EgregorMood.BALANCED)
        d = style.to_dict()
        assert "mood" in d

    def test_to_dict_has_all_sections(self, artist):
        style = artist.generate(EgregorMood.BALANCED)
        d = style.to_dict()
        assert {"mood", "label", "palette", "motion", "geometry", "noise_field"}.issubset(d.keys())

    def test_to_dict_serializable(self, artist):
        import json
        style = artist.generate(EgregorMood.DYNAMIC)
        # No debe lanzar
        json.dumps(style.to_dict())


# ─── Tests de all_styles() ───────────────────────────────────────────────────

class TestAllStyles:
    def test_returns_all_moods(self, artist):
        all_s = artist.all_styles()
        assert len(all_s) == len(EgregorMood)

    def test_keys_are_mood_values(self, artist):
        all_s = artist.all_styles()
        for mood in EgregorMood:
            assert mood.value in all_s

    def test_each_style_has_palette(self, artist):
        for style_dict in artist.all_styles().values():
            assert "palette" in style_dict


# ─── Tests de transición ─────────────────────────────────────────────────────

class TestTransition:
    def test_transition_t_one_is_target(self, artist):
        style = artist.generate(
            EgregorMood.AGITATED,
            transition_from=EgregorMood.DORMANT,
            transition_t=1.0,
        )
        assert style.motion["speed"] == _MOTION_PARAMS[EgregorMood.AGITATED]["speed"]

    def test_transition_t_zero_is_source(self, artist):
        style = artist.generate(
            EgregorMood.AGITATED,
            transition_from=EgregorMood.DORMANT,
            transition_t=0.0,
        )
        assert abs(style.motion["speed"] - _MOTION_PARAMS[EgregorMood.DORMANT]["speed"]) < 0.01

    def test_transition_midpoint(self, artist):
        source = EgregorMood.DORMANT
        target = EgregorMood.AGITATED
        style = artist.generate(target, transition_from=source, transition_t=0.5)
        expected_speed = (
            _MOTION_PARAMS[source]["speed"] * 0.5 +
            _MOTION_PARAMS[target]["speed"] * 0.5
        )
        assert abs(style.motion["speed"] - expected_speed) < 0.1


# ─── Tests de palette_for() y motion_for() ──────────────────────────────────

class TestHelpers:
    def test_palette_for(self, artist):
        p = artist.palette_for(EgregorMood.AGITATED)
        assert p["primary"] == "#FF2A00"

    def test_motion_for(self, artist):
        m = artist.motion_for(EgregorMood.DORMANT)
        assert m["particle_count"] == 15
