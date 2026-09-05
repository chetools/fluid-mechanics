"""Unit tests for stress tensor kinematics, symmetry, and Newtonian constitutive law."""

import numpy as np
import pytest
from src.physics.stress_tensor import (
    decompose_velocity_gradient_2d,
    compute_cauchy_stress_2d,
    deform_fluid_element_2d
)

def test_velocity_gradient_decomposition():
    """Verify L = D + Omega, D is symmetric, and Omega is anti-symmetric."""
    dudx, dudy = 1.2, -0.8
    dvdx, dvdy = 0.5, -1.2
    
    res = decompose_velocity_gradient_2d(dudx, dudy, dvdx, dvdy)
    L = res["L"]
    D = res["D"]
    Omega = res["Omega"]
    
    # L = D + Omega
    assert np.allclose(L, D + Omega)
    
    # D is symmetric: D = D^T
    assert np.allclose(D, D.T)
    
    # Omega is anti-symmetric: Omega = -Omega^T
    assert np.allclose(Omega, -Omega.T)
    
    # Diagonal of Omega must be zero
    assert np.isclose(Omega[0, 0], 0.0)
    assert np.isclose(Omega[1, 1], 0.0)

def test_pure_rotation_has_zero_strain():
    """Verify pure rigid body rotation produces exactly zero strain tensor D."""
    omega = 3.5
    # Velocity field u = -omega*y, v = omega*x => dudy = -omega, dvdx = omega
    res = decompose_velocity_gradient_2d(dudx=0.0, dudy=-omega, dvdx=omega, dvdy=0.0)
    
    assert np.allclose(res["D"], 0.0)
    assert np.isclose(res["vorticity_z"], 2.0 * omega)

def test_cauchy_stress_symmetry_and_mohr_circle():
    """Verify Cauchy stress tensor symmetry and Mohr's circle calculations."""
    res = compute_cauchy_stress_2d(
        dudx=0.0, dudy=10.0, dvdx=0.0, dvdy=0.0,
        mu=1.0e-3, p=101325.0
    )
    sigma = res["sigma"]
    
    # Stress tensor symmetry: sigma_xy = sigma_yx
    assert np.isclose(sigma[0, 1], sigma[1, 0])
    
    # Viscous shear stress tau_xy = mu * dudy = 1.0e-3 * 10.0 = 0.01 Pa
    assert np.isclose(res["tau"][0, 1], 1.0e-3 * 10.0)
    
    # Mohr's circle principal stresses
    center = res["mohr_center"]
    radius = res["mohr_radius"]
    p_stresses = res["principal_stresses"]
    assert np.isclose(p_stresses[0], center + radius)
    assert np.isclose(p_stresses[1], center - radius)
