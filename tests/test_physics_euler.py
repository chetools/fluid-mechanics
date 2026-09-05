"""Unit tests for Euler's Equation physics and models."""

import numpy as np
import pytest
from src.physics.euler import venturi_profile, cylinder_potential_flow

def test_venturi_conservation_of_mass_and_bernoulli():
    """Verify continuity and Bernoulli invariant conservation across the nozzle."""
    res = venturi_profile(
        x_span=1.0,
        d_inlet=0.1,
        d_throat=0.04,
        d_outlet=0.1,
        flow_rate=0.02,
        p_inlet=101325.0,
        rho=1000.0,
        n_points=100,
    )
    
    # Continuity: A(x) * u(x) == Q
    q_calculated = res["area"] * res["velocity"]
    assert np.allclose(q_calculated, 0.02, rtol=1e-5)
    
    # Throat must have maximum velocity and minimum pressure
    throat_idx = np.argmin(res["diameter"])
    assert np.argmax(res["velocity"]) == throat_idx
    assert np.argmin(res["pressure"]) == throat_idx
    
    # Total pressure H = p + 0.5*rho*u^2 must be constant throughout
    total_p = res["total_pressure"]
    assert np.allclose(total_p, total_p[0], rtol=1e-5)

def test_cylinder_potential_flow_and_dalembert_paradox():
    """Verify cylinder potential flow surface pressure and d'Alembert zero drag."""
    u_inf = 5.0
    radius = 1.0
    rho = 1.225
    p_inf = 101325.0
    
    res = cylinder_potential_flow(
        radius=radius,
        u_inf=u_inf,
        rho=rho,
        p_inf=p_inf,
        grid_size=60,
        box_size=3.0,
    )
    
    # Surface pressure coefficient Cp(theta) = 1 - 4*sin^2(theta)
    theta = res["theta_surf"]
    cp_expected = 1.0 - 4.0 * (np.sin(theta)**2)
    assert np.allclose(res["cp_surf"], cp_expected, atol=1e-5)
    
    # Stagnation points at theta = 0, pi (Cp = 1.0)
    assert np.isclose(res["cp_surf"][0], 1.0, atol=1e-5)
    
    # Top and bottom points at theta = pi/2, 3pi/2 (Cp = -3.0)
    mid_idx = len(theta) // 4
    assert np.isclose(res["cp_surf"][mid_idx], -3.0, atol=1e-2)
    
    # d'Alembert's Paradox: Drag and Lift must integrate to zero
    assert abs(res["drag_force"]) < 1e-4
    assert abs(res["lift_force"]) < 1e-4
