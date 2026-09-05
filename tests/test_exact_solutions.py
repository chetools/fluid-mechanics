"""Unit tests for exact analytical solutions to the Navier-Stokes equations."""

import numpy as np
from src.physics.exact_solutions import (
    couette_poiseuille_channel,
    stokes_first_problem
)

def test_pure_couette_flow():
    """Verify pure shear Couette flow has linear profile and constant shear stress."""
    h = 0.05
    u_wall = 2.0
    res = couette_poiseuille_channel(h=h, u_wall=u_wall, dp_dx=0.0, mu=1.0e-3, n_points=101)
    
    # Boundary conditions
    assert np.isclose(res["u_total"][0], 0.0)
    assert np.isclose(res["u_total"][-1], u_wall)
    
    # Centerline velocity must be exactly U_wall / 2
    mid_idx = len(res["y"]) // 2
    assert np.isclose(res["u_total"][mid_idx], u_wall / 2.0, atol=1e-3)
    
    # Shear stress must be constant tau = mu * U_wall / h
    tau_expected = 1.0e-3 * u_wall / h
    assert np.allclose(res["tau"], tau_expected, rtol=1e-4)

def test_pure_poiseuille_flow():
    """Verify pure pressure-driven Poiseuille flow has parabolic profile."""
    h = 0.04
    dp_dx = -20.0
    mu = 1.0e-3
    res = couette_poiseuille_channel(h=h, u_wall=0.0, dp_dx=dp_dx, mu=mu)
    
    # Zero velocity at both walls
    assert np.isclose(res["u_total"][0], 0.0)
    assert np.isclose(res["u_total"][-1], 0.0)
    
    # Max velocity at centerline y = h/2: u_max = (h^2 / (8*mu)) * (-dp/dx)
    u_max_expected = (h**2 / (8.0 * mu)) * (-dp_dx)
    mid_idx = len(res["y"]) // 2
    assert np.isclose(res["u_total"][mid_idx], u_max_expected, rtol=1e-3)

def test_stokes_first_problem_similarity():
    """Verify Stokes' first problem boundary conditions and diffusion expansion."""
    times = np.array([0.1, 0.5, 1.0])
    res = stokes_first_problem(u_wall=1.5, nu=1.0e-5, times=times)
    
    for t in times:
        prof = res["profiles"][t]
        # At wall y=0: u = U_wall
        assert np.isclose(prof[0], 1.5)
        # Far from wall: u -> 0
        assert np.isclose(prof[-1], 0.0, atol=1e-3)
        
    # Penetration thickness must grow monotonically with time: delta ~ sqrt(t)
    deltas = [res["delta_viscous"][t] for t in times]
    assert deltas[0] < deltas[1] < deltas[2]
