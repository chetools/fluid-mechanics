"""Unit tests for SI ↔ nondimensional display conversion (no Streamlit session)."""

import numpy as np

from src.units import si_to_display, calculate_mach, FLUID_PRESETS


def test_si_to_display_is_identity_in_si():
    refs = {"u_ref": 2.0, "l_ref": 0.05, "rho": 1000.0, "mu": 1e-3}
    assert si_to_display(3.2, "velocity", system="SI", refs=refs) == 3.2
    assert si_to_display(1500.0, "pressure", system="SI", refs=refs) == 1500.0


def test_si_to_display_scales_with_reference_fluid():
    refs = {"u_ref": 2.0, "l_ref": 0.5, "rho": 1000.0, "mu": 1e-3}
    assert np.isclose(si_to_display(4.0, "velocity", system="NONDIM", refs=refs), 2.0)
    assert np.isclose(si_to_display(1.0, "length", system="NONDIM", refs=refs), 2.0)
    # q = ρ U² = 4000 Pa → Δp = 4000 Pa is Eu = 1
    assert np.isclose(si_to_display(4000.0, "pressure", system="NONDIM", refs=refs), 1.0)
    assert np.isclose(si_to_display(0.25, "time", system="NONDIM", refs=refs), 1.0)


def test_mach_uses_fluid_speed_of_sound():
    assert np.isclose(calculate_mach(2.0, speed_of_sound=343.0), 2.0 / 343.0)
    water_a = FLUID_PRESETS["Water (20°C)"]["speed_of_sound"]
    assert np.isclose(calculate_mach(2.0, speed_of_sound=water_a), 2.0 / water_a)
    assert calculate_mach(2.0, speed_of_sound=water_a) < calculate_mach(2.0, speed_of_sound=343.0)
