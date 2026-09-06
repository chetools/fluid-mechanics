"""Unit tests for turbulence velocity profiles and Law of the Wall."""

import math
import numpy as np
from src.physics.turbulence import (
    velocity_profile_comparison,
    law_of_the_wall,
    pipe_kinetic_correction,
    _spalding_y_plus,
)

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

def test_correction_factors_are_the_profile_integrals():
    """The panel derives these by integrating u^3 over annuli, so they must be that.

    The parabola gives alpha = 2 and beta = 4/3 exactly; the 1/7 power law gives
    the closed-form values below. An earlier approximation, 1 + 3/(2 n^2),
    returned 1.031 instead of 1.058 -- a 50% error in the correction itself.
    """
    res = velocity_profile_comparison(u_avg=1.5, reynolds=50000.0)
    n = res["n_exp"]
    assert np.isclose(res["alpha_lam"], 2.0, rtol=1e-6)
    assert np.isclose(res["beta_lam"], 4.0 / 3.0, rtol=1e-6)

    exact_alpha = (n + 1) ** 3 * (2 * n + 1) ** 3 / (4 * n**4 * (3 + n) * (3 + 2 * n))
    exact_beta = (n + 1) ** 2 * (2 * n + 1) ** 2 / (2 * n**2 * (2 + n) * (2 + 2 * n))
    assert np.isclose(res["alpha_turb"], exact_alpha, rtol=1e-4)
    assert np.isclose(res["beta_turb"], exact_beta, rtol=1e-4)

    # Blunter profile, smaller correction: the ordering must survive any refit.
    assert res["alpha_turb"] < res["alpha_lam"]
    assert res["beta_turb"] < res["beta_lam"]


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


def test_composite_wall_law_is_spalding_not_a_linear_blend():
    """The docstring and plot claim Spalding; invert y+(u+) and recover y+."""
    kappa, B = 0.41, 5.0
    res = law_of_the_wall(kappa=kappa, B=B)
    y_of_u = _spalding_y_plus(res["u_plus_composite"], kappa, B)
    assert np.allclose(y_of_u, res["y_plus"], rtol=1e-5, atol=1e-5)
    # A linear blend between (5,5) and (30, log(30)) would miss Spalding in the buffer.
    idx_15 = np.argmin(np.abs(res["y_plus"] - 15.0))
    u_linear = 5.0 + (15.0 - 5.0) / 25.0 * ((1.0 / kappa) * np.log(30.0) + B - 5.0)
    assert abs(res["u_plus_composite"][idx_15] - u_linear) > 0.2


def test_pipe_kinetic_correction_picks_the_integrated_profile():
    lam = pipe_kinetic_correction(1000.0)
    assert lam["regime"] == "laminar"
    assert np.isclose(lam["alpha"], 2.0, rtol=1e-6)
    turb = pipe_kinetic_correction(5e4)
    assert turb["regime"] == "turbulent"
    assert 1.05 < turb["alpha"] < 1.08
    trans = pipe_kinetic_correction(3000.0)
    assert trans["regime"] == "transitional"
    assert math.isnan(trans["alpha"])
