"""Unit tests for turbulence velocity profiles and Law of the Wall."""

import numpy as np
from src.physics.turbulence import velocity_profile_comparison, law_of_the_wall

def test_velocity_profiles_laminar_vs_turbulent():
    """Verify laminar parabolic apex and turbulent blunt apex and kinetic energy factors."""
    u_mean = 2.0
    res = velocity_profile_comparison(pipe_radius=0.05, u_avg=u_mean, reynolds=50000.0)
    
    # Laminar centerline velocity must be exactly 2 * u_avg
    assert np.isclose(res["u_laminar"][0], 2.0 * u_mean)
    # Laminar wall velocity must be zero
    assert np.isclose(res["u_laminar"][-1], 0.0)
    # Laminar kinetic energy factor must be 2.0
    assert np.isclose(res["alpha_lam"], 2.0)
    
    # Turbulent centerline velocity must be flatter (< 2.0 * u_avg)
    assert res["u_turbulent"][0] < res["u_laminar"][0]
    assert np.isclose(res["u_turbulent"][-1], 0.0)
    # Turbulent alpha ~ 1.05
    assert 1.0 < res["alpha_turb"] < 1.15

def test_law_of_the_wall_sublayers():
    """Verify viscous sublayer linear slope and log-law logarithmic behavior."""
    res = law_of_the_wall(kappa=0.41, B=5.0)
    y_plus = res["y_plus"]
    
    # In viscous sublayer (y+ = 1): u+ = y+ = 1.0
    idx_1 = np.argmin(np.abs(y_plus - 1.0))
    assert np.isclose(res["u_plus_composite"][idx_1], 1.0, atol=0.05)
    
    # In log-law region (y+ = 100): u+ = (1/0.41)*ln(100) + 5.0 = 16.23
    idx_100 = np.argmin(np.abs(y_plus - 100.0))
    expected_log = (1.0 / 0.41) * np.log(100.0) + 5.0
    assert np.isclose(res["u_plus_composite"][idx_100], expected_log, rtol=0.02)
