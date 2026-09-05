"""Unit tests for pipe flow friction factor and Chemical Engineering piping models."""

import numpy as np
import pytest
from src.physics.pipe_flow import (
    friction_factor_churchill,
    solve_colebrook_white,
    calculate_cheme_pipe_system,
    hydraulic_diameter,
    entrance_length,
    npsh_available,
    laminar_darcy_from_force_balance,
    straw_bundle_comparison,
)

def test_churchill_laminar_asymptote():
    """Verify Churchill correlation strictly matches f = 64/Re for laminar flow."""
    re_test = 1000.0
    f_churchill = friction_factor_churchill(re_test, rel_roughness=0.0)
    f_exact = 64.0 / re_test
    assert np.isclose(f_churchill, f_exact, rtol=1e-3)

def test_colebrook_white_and_churchill_agreement():
    """Verify Colebrook-White and Churchill agree in turbulent regime."""
    re_turb = 100000.0
    eps_d = 0.001
    
    f_cw = solve_colebrook_white(re_turb, eps_d)
    f_ch = friction_factor_churchill(re_turb, eps_d)
    
    # Both formulations agree within 3%
    assert np.isclose(f_cw, f_ch, rtol=0.03)

def test_cheme_piping_system():
    """Verify piping system calculations for pressure drop and pump power."""
    res = calculate_cheme_pipe_system(
        flow_rate=30.0,
        pipe_diameter_inner=0.08,
        pipe_length=50.0,
        roughness=4.5e-5,
        density=1000.0,
        viscosity=1.0e-3,
        elevation_gain=10.0,
    )
    
    assert res["velocity"] > 0.0
    assert res["reynolds"] > 4000.0
    assert res["delta_p_total"] > 0.0
    assert res["p_shaft_kw"] > 0.0
    assert res["annual_cost"] > 0.0


def test_pipe_pressure_drop_tracks_sidebar_viscosity():
    """Glycerin-like μ must raise Δp versus water at the same Q and geometry."""
    common = dict(
        flow_rate=25.0,
        pipe_diameter_inner=0.075,
        pipe_length=60.0,
        roughness=4.5e-5,
        elevation_gain=0.0,
    )
    water = calculate_cheme_pipe_system(density=998.2, viscosity=1.002e-3, **common)
    glyc = calculate_cheme_pipe_system(density=1261.0, viscosity=1.412, **common)
    assert glyc["reynolds"] < water["reynolds"]
    assert glyc["delta_p_major"] > water["delta_p_major"]

def test_hydraulic_diameter_geometries():
    """Verify hydraulic diameter formulas for circular, annulus, and rectangular ducts."""
    # Circular: D_H = D
    assert np.isclose(hydraulic_diameter("circular", 0.1), 0.1)
    
    # Annulus: D_H = D_o - D_i
    assert np.isclose(hydraulic_diameter("annulus", 0.15, 0.10), 0.05)
    
    # Square duct (a = b = 0.2): D_H = a = 0.2
    assert np.isclose(hydraulic_diameter("rectangular", 0.2, 0.2), 0.2)


def test_entrance_length_laminar_and_turbulent():
    lam = entrance_length(0.05, 1000.0)
    assert lam["regime"] == "laminar"
    assert np.isclose(lam["L_e_over_D"], 60.0)
    turb = entrance_length(0.05, 1.0e5)
    assert turb["regime"] == "turbulent"
    assert turb["L_e_over_D"] < lam["L_e_over_D"]


def test_laminar_darcy_matches_churchill_below_2300():
    re = 800.0
    f_bal = laminar_darcy_from_force_balance(re)
    f_ch = friction_factor_churchill(re, 0.0)
    assert np.isclose(f_bal, 64.0 / re)
    assert np.isclose(f_bal, f_ch, rtol=1e-3)


def test_straw_bundle_n1_phi1_matches_open_pipe():
    kwargs = dict(
        flow_rate=0.01,
        outer_diameter=0.08,
        length=50.0,
        density=1000.0,
        viscosity=1e-3,
        roughness=0.0,
    )
    open1 = straw_bundle_comparison(n_straws=1, packing_fraction=1.0, **kwargs)
    many = straw_bundle_comparison(n_straws=100, packing_fraction=0.85, **kwargs)
    assert np.isclose(open1["dp_open"], open1["dp_bundle"], rtol=0.02)
    assert many["d_straw"] < open1["d_straw"]
    assert many["power_ratio"] > 1.0


def test_npsh_flooded_versus_lift():
    common = dict(
        p_tank_abs=101325.0,
        p_vapor=2338.8,
        density=998.2,
        viscosity=1.002e-3,
        suction_length=5.0,
        suction_diameter=0.08,
        roughness=4.5e-5,
        flow_rate_m3s=0.01,
        fittings_counts={"Pipe Inlet (Square edge)": 1},
    )
    flooded = npsh_available(z_surface=4.0, **common)
    lift = npsh_available(z_surface=-4.0, **common)
    assert flooded["npsh_a"] - lift["npsh_a"] == 8.0
    assert flooded["npsh_a"] > lift["npsh_a"]
    assert flooded["static_term"] > 9.0
