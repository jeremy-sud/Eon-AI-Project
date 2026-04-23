"""
Tests para CircadianClock - Proyecto Eón
==========================================

Tests del sistema de ciclos circadianos.
"""

import pytest
import numpy as np
import sys
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
_python_dir = os.path.dirname(_current_dir)
sys.path.insert(0, _python_dir)

from core.circadian import (
    CircadianClock,
    CircadianPhase,
    CircadianState,
    _phase_for_fraction,
    _PHASE_BOUNDARIES,
)


# ─── Tests de _phase_for_fraction ────────────────────────────────────────────

class TestPhaseForFraction:
    def test_zero_is_dawn(self):
        assert _phase_for_fraction(0.0) == CircadianPhase.DAWN

    def test_wraps_at_one(self):
        assert _phase_for_fraction(1.0) == _phase_for_fraction(0.0)

    def test_all_fractions_return_enum(self):
        for f in np.linspace(0, 1, 100):
            p = _phase_for_fraction(f)
            assert isinstance(p, CircadianPhase)

    def test_peak_fraction(self):
        # PEAK es [0.10, 0.35)
        assert _phase_for_fraction(0.20) == CircadianPhase.PEAK

    def test_night_fraction(self):
        # NIGHT es [0.70, 0.90)
        assert _phase_for_fraction(0.80) == CircadianPhase.NIGHT

    def test_rem_fraction(self):
        # REM es [0.90, 1.00)
        assert _phase_for_fraction(0.95) == CircadianPhase.REM


# ─── Tests de construcción ───────────────────────────────────────────────────

class TestConstruction:
    def test_valid_construction(self):
        clock = CircadianClock(period_steps=100)
        assert clock.period_steps == 100

    def test_invalid_period(self):
        with pytest.raises(ValueError):
            CircadianClock(period_steps=2)

    def test_invalid_phase_offset(self):
        with pytest.raises(ValueError):
            CircadianClock(period_steps=100, phase_offset=1.5)

    def test_initial_tick_zero(self):
        clock = CircadianClock(period_steps=100)
        assert clock._tick_count == 0

    def test_initial_cycle_count_zero(self):
        clock = CircadianClock(period_steps=100)
        assert clock.cycle_count == 0


# ─── Tests de tick() y state() ───────────────────────────────────────────────

class TestTickAndState:
    def test_tick_returns_state(self):
        clock = CircadianClock(period_steps=100, random_state=0)
        s = clock.tick()
        assert isinstance(s, CircadianState)

    def test_tick_advances_count(self):
        clock = CircadianClock(period_steps=100)
        clock.tick()
        assert clock._tick_count == 1

    def test_tick_n_advances_by_n(self):
        clock = CircadianClock(period_steps=100)
        clock.tick(n=10)
        assert clock._tick_count == 10

    def test_state_does_not_advance(self):
        clock = CircadianClock(period_steps=100)
        clock.tick(5)
        before = clock._tick_count
        clock.state()
        assert clock._tick_count == before

    def test_cycle_fraction_in_range(self):
        clock = CircadianClock(period_steps=200, random_state=0)
        for _ in range(500):
            s = clock.tick()
            assert 0.0 <= s.cycle_fraction < 1.0

    def test_cycle_count_increments(self):
        clock = CircadianClock(period_steps=50, random_state=0)
        for _ in range(50):
            clock.tick()
        assert clock.cycle_count >= 1

    def test_modulators_in_range(self):
        clock = CircadianClock(period_steps=200, random_state=0)
        for _ in range(200):
            s = clock.tick()
            assert 0.0 <= s.learning_rate_mod <= 1.0
            assert 0.0 <= s.forgetting_mod <= 1.0
            assert 0.0 <= s.noise_mod <= 1.0
            assert 0.0 <= s.anomaly_threshold_mod <= 1.0

    def test_oscillator_value_finite(self):
        clock = CircadianClock(period_steps=100, random_state=0)
        for _ in range(100):
            s = clock.tick()
            assert np.isfinite(s.oscillator_value)


# ─── Tests de fases ───────────────────────────────────────────────────────────

class TestPhases:
    def test_all_phases_covered_in_full_cycle(self):
        clock = CircadianClock(period_steps=1000, random_state=0)
        states = clock.full_cycle()
        phases_seen = {s.phase for s in states}
        assert phases_seen == set(CircadianPhase)

    def test_peak_has_high_learning(self):
        """En PEAK la tasa de aprendizaje es mayor que en NIGHT."""
        clock = CircadianClock(period_steps=1000, random_state=0)
        states = clock.full_cycle()

        peak_lr = np.mean([s.learning_rate_mod for s in states
                           if s.phase == CircadianPhase.PEAK])
        night_lr = np.mean([s.learning_rate_mod for s in states
                            if s.phase == CircadianPhase.NIGHT])
        assert peak_lr > night_lr

    def test_night_has_lower_learning_than_peak(self):
        clock = CircadianClock(period_steps=500, random_state=0)
        states = clock.full_cycle()
        peak = [s.learning_rate_mod for s in states
                if s.phase == CircadianPhase.PEAK]
        night = [s.learning_rate_mod for s in states
                 if s.phase == CircadianPhase.NIGHT]
        if peak and night:
            assert np.mean(peak) > np.mean(night)


# ─── Tests de full_cycle() ───────────────────────────────────────────────────

class TestFullCycle:
    def test_length(self):
        clock = CircadianClock(period_steps=100, random_state=0)
        states = clock.full_cycle()
        assert len(states) == 100

    def test_does_not_advance_main_clock(self):
        clock = CircadianClock(period_steps=100, random_state=0)
        clock.tick(10)
        before = clock._tick_count
        clock.full_cycle()
        assert clock._tick_count == before

    def test_all_states_valid(self):
        clock = CircadianClock(period_steps=50, random_state=0)
        for s in clock.full_cycle():
            assert isinstance(s.phase, CircadianPhase)
            assert 0.0 <= s.cycle_fraction < 1.0


# ─── Tests de reset() ────────────────────────────────────────────────────────

class TestReset:
    def test_reset_tick_count(self):
        clock = CircadianClock(period_steps=100, random_state=0)
        clock.tick(50)
        clock.reset()
        assert clock._tick_count == 0

    def test_reset_with_phase_offset(self):
        clock = CircadianClock(period_steps=100, random_state=0)
        clock.reset(phase_offset=0.5)
        assert clock.phase_offset == 0.5

    def test_reset_invalid_offset(self):
        clock = CircadianClock(period_steps=100)
        with pytest.raises(ValueError):
            clock.reset(phase_offset=1.0)


# ─── Tests de callbacks ───────────────────────────────────────────────────────

class TestCallbacks:
    def test_callback_called_on_tick(self):
        clock = CircadianClock(period_steps=100, random_state=0)
        calls = []
        clock.add_callback(lambda s: calls.append(s.phase))
        clock.tick(5)
        assert len(calls) == 1  # tick() llama a state() una vez

    def test_schedule_at_phase_fires(self):
        clock = CircadianClock(period_steps=100, random_state=0)
        fired = []
        clock.schedule_at_phase(CircadianPhase.NIGHT, lambda: fired.append(True))
        for _ in range(100):
            clock.tick()
        assert len(fired) > 0  # Debe haber disparado al menos una vez

    def test_schedule_once(self):
        clock = CircadianClock(period_steps=100, random_state=0)
        fired = []
        clock.schedule_at_phase(
            CircadianPhase.NIGHT,
            lambda: fired.append(True),
            once=True,
        )
        for _ in range(200):
            clock.tick()
        assert len(fired) == 1


# ─── Tests de summary() ──────────────────────────────────────────────────────

class TestSummary:
    def test_summary_keys(self):
        clock = CircadianClock(period_steps=100, random_state=0)
        s = clock.summary()
        assert "tick" in s
        assert "phase" in s
        assert "learning_rate_mod" in s
        assert "cycle_fraction" in s

    def test_tick_in_summary(self):
        clock = CircadianClock(period_steps=100, random_state=0)
        clock.tick(17)
        s = clock.summary()
        assert s["tick"] == 17


# ─── Tests de phase_offset ───────────────────────────────────────────────────

class TestPhaseOffset:
    def test_offset_shifts_phase(self):
        c0 = CircadianClock(period_steps=1000, phase_offset=0.0, random_state=0)
        c_half = CircadianClock(period_steps=1000, phase_offset=0.5, random_state=0)
        s0 = c0.state()
        s_half = c_half.state()
        # Con offset=0.5, deben estar en fases distintas
        assert s0.phase != s_half.phase
