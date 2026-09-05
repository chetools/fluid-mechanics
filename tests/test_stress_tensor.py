"""Unit tests for stress tensor kinematics, symmetry, and Newtonian constitutive law."""

import numpy as np
import pytest
from src.physics.stress_tensor import (
    decompose_velocity_gradient_2d,
    compute_cauchy_stress_2d,
    deform_fluid_element_2d,
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


@pytest.mark.parametrize('gradient', [(0, -1, 1, 0), (1, 0, 0, -1), (0, 1, 0, 0), (0, 1, 1, 0)])
def test_incompressible_material_geometry_preserves_area(gradient):
    result = deform_fluid_element_2d(*gradient, dt=0.25)
    x, y = result['square_full'].T
    polygon_area = 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    assert polygon_area == pytest.approx(1.0)
    assert result['area_ratio'] == pytest.approx(polygon_area)


def test_finite_rigid_rotation_preserves_lengths_and_internal_grid():
    result = deform_fluid_element_2d(0, -1, 1, 0, dt=0.25)
    rotation = np.array([[np.cos(.25), -np.sin(.25)], [np.sin(.25), np.cos(.25)]])
    assert np.allclose(result['square_full'], result['square_initial'] @ rotation.T)
    assert np.allclose(result['square_rot_only'], result['square_full'])
    assert np.allclose(result['square_strain_only'], result['square_initial'])
    for initial, final in zip(result['internal_lines_init'], result['internal_lines_full']):
        assert np.allclose(final, initial @ rotation.T)
    assert result['shear_angle_deg'] == pytest.approx(0)


def test_finite_simple_shear_angle_matches_geometry():
    result = deform_fluid_element_2d(0, 2, 0, 0, dt=.5)
    assert np.allclose(result['deformation_gradient'], [[1, 1], [0, 1]])
    assert result['shear_angle_deg'] == pytest.approx(45)


def test_dilatation_has_exponential_area_growth():
    result = deform_fluid_element_2d(1, 0, 0, 1, dt=.25)
    assert result['area_ratio'] == pytest.approx(np.exp(.5))


def test_pressure_shifts_mean_without_creating_mohr_radius():
    for gradient in [(0, -1, 1, 0), (0, 1, 0, 0)]:
        low = compute_cauchy_stress_2d(*gradient, p=1e4)
        high = compute_cauchy_stress_2d(*gradient, p=2e5)
        assert high['mohr_center'] - low['mohr_center'] == pytest.approx(-1.9e5)
        assert high['mohr_radius'] == pytest.approx(low['mohr_radius'])
    assert compute_cauchy_stress_2d(0, -1, 1, 0)['mohr_radius'] == 0
