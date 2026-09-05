"""Tests for Blasius similarity and cylinder outer-flow landmarks."""

import numpy as np

from src.physics.boundary_layer import (
    blasius_similarity_profile,
    blasius_plate,
    cylinder_outer_flow_and_separation,
    BLASIUS_FPP0,
    BLASIUS_DELTA_STAR_COEFF,
    BLASIUS_THETA_COEFF,
)


def test_integral_thicknesses_are_integrated_not_quoted():
    """The panel claims 1.7208 and 0.664 come from integrating f'.

    They must therefore *be* those integrals, and land on the literature values
    without being told them.
    """
    sim = blasius_similarity_profile()
    assert np.isclose(sim["delta_star_coeff"], BLASIUS_DELTA_STAR_COEFF, rtol=2e-3)
    assert np.isclose(sim["theta_coeff"], BLASIUS_THETA_COEFF, rtol=2e-3)
    # The von Karman momentum integral says c_f sqrt(Re_x) = 2 f''(0) equals the
    # theta coefficient exactly. That identity is a check on the whole solve.
    assert np.isclose(sim["cf_coeff"], sim["theta_coeff"], rtol=1e-3)
    assert np.isclose(sim["shape_factor"], 2.59, rtol=5e-3)


def test_blasius_wall_and_freestream():
    sim = blasius_similarity_profile()
    assert np.isclose(sim["f"][0], 0.0, atol=1e-10)
    assert np.isclose(sim["f_prime"][0], 0.0, atol=1e-10)
    assert np.isclose(sim["fpp0"], BLASIUS_FPP0, rtol=1e-6)
    assert sim["fp_inf"] > 0.99
    assert 4.5 < sim["eta_99"] < 5.3


def test_blasius_thickness_scaling():
    nu = 1.0e-6
    u = 1.0
    a = blasius_plate(x=0.5, u_inf=u, nu=nu)
    b = blasius_plate(x=2.0, u_inf=u, nu=nu)
    # δ ∝ √x at the trailing edge
    assert np.isclose(b["delta_L"] / a["delta_L"], np.sqrt(2.0 / 0.5), rtol=0.02)
    assert a["cf_L"] > b["cf_L"]
    assert np.isclose(a["Cf_mean"] * np.sqrt(a["re_L"]), 1.328, rtol=0.01)


def test_cylinder_adverse_after_ninety():
    res = cylinder_outer_flow_and_separation(u_inf=5.0, radius=1.0, rho=1000.0)
    th = res["theta_deg"]
    i90 = int(np.argmin(np.abs(th - 90.0)))
    i60 = int(np.argmin(np.abs(th - 60.0)))
    i120 = int(np.argmin(np.abs(th - 120.0)))
    assert res["dp_ds"][i60] < 0  # favorable
    assert res["dp_ds"][i120] > 0  # adverse
    assert np.isclose(res["cp"][0], 1.0, atol=1e-8)
    assert abs(th[i90] - 90.0) < 1.0
    assert np.isclose(res["laminar_sep_deg"], 104.5)
