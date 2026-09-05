"""Impeller geometry and velocity triangles: conventions, closure, known limits."""

import math

import numpy as np
import pytest

from src.physics.impeller import (
    blade_camberline,
    blade_surface_3d,
    head_flow_curve,
    impeller_geometry,
    project_isometric,
    slip_factor,
    velocity_triangles,
)


def test_camberline_with_constant_angle_is_a_logarithmic_spiral():
    """beta constant => theta = ln(r/r1)/tan(beta). This is the angle's definition."""
    camber = blade_camberline(0.05, 0.15, 30.0, 30.0, n_points=4000)
    expected = np.log(camber["r"] / 0.05) / math.tan(math.radians(30.0))
    assert np.allclose(camber["theta"], expected, rtol=1e-6, atol=1e-9)


def test_camberline_slope_reproduces_the_blade_angle_it_was_built_from():
    """Differentiate the drawn curve and recover beta: tan(beta) = dr/(r dtheta)."""
    camber = blade_camberline(0.05, 0.15, 40.0, 20.0, n_points=4000)
    r, theta = camber["r"], camber["theta"]
    r_mid = 0.5 * (r[1:] + r[:-1])
    beta_measured = np.degrees(np.arctan2(np.diff(r), r_mid * np.diff(theta)))
    beta_expected = 0.5 * (camber["beta_deg"][1:] + camber["beta_deg"][:-1])
    assert np.allclose(beta_measured, beta_expected, atol=0.05)


def test_shallower_blade_angle_wraps_further_around_the_shaft():
    shallow = blade_camberline(0.05, 0.15, 20.0, 20.0)["wrap_angle_deg"]
    steep = blade_camberline(0.05, 0.15, 70.0, 70.0)["wrap_angle_deg"]
    assert shallow > steep > 0


def test_blade_surface_lies_on_the_camberline_radii():
    blade = blade_surface_3d(0.05, 0.15, 30.0, 25.0, 0.03, 0.012, blade_index=2, n_blades=7)
    radius = np.hypot(blade["x"], blade["y"])
    assert np.allclose(radius[0], blade["camber"]["r"])
    assert radius.min() == pytest.approx(0.05)
    assert radius.max() == pytest.approx(0.15)


def test_blades_are_evenly_spaced_around_the_shaft():
    geom = impeller_geometry(n_blades=6)
    leading_angles = sorted(
        math.atan2(blade["y"][0, 0], blade["x"][0, 0]) % (2 * math.pi)
        for blade in geom["blades"]
    )
    gaps = np.diff(leading_angles)
    assert np.allclose(gaps, 2 * math.pi / 6, atol=1e-9)


def test_passage_width_tapers_from_b1_to_b2():
    blade = blade_surface_3d(0.05, 0.15, 30.0, 25.0, 0.030, 0.012)
    leading_span = blade["z"][-1, 0] - blade["z"][0, 0]
    trailing_span = blade["z"][-1, -1] - blade["z"][0, -1]
    assert leading_span == pytest.approx(0.030)
    assert trailing_span == pytest.approx(0.012)


def test_velocity_triangle_closes():
    """C = U + W component by component is the whole content of the triangle."""
    result = velocity_triangles(rpm=2900, flow_rate=0.030)
    w_theta2 = result["u2"] - result["c_theta2"]
    assert result["w2"] == pytest.approx(math.hypot(w_theta2, result["cm2"]))
    assert result["c2"] == pytest.approx(math.hypot(result["c_theta2"], result["cm2"]))
    # Rothalpy identity W^2 = C^2 + U^2 - 2 U C_theta
    assert result["w2"] ** 2 == pytest.approx(
        result["c2"] ** 2 + result["u2"] ** 2 - 2 * result["u2"] * result["c_theta2"]
    )


def test_meridional_velocity_is_continuity():
    result = velocity_triangles(rpm=2900, flow_rate=0.030, r2=0.15, b2=0.012)
    assert result["cm2"] == pytest.approx(0.030 / (2 * math.pi * 0.15 * 0.012))
    assert result["cm1"] == pytest.approx(0.030 / result["inlet_area"])


def test_blade_angle_conventions_are_complementary():
    result = velocity_triangles(rpm=2900, flow_rate=0.030, beta2_deg=25.0)
    assert result["beta2_blade_deg"] + result["beta2_blade_from_meridional_deg"] == pytest.approx(90.0)
    assert result["alpha2_deg"] + result["alpha2_from_meridional_deg"] == pytest.approx(90.0)


def test_shockless_entry_is_detected_when_the_blade_matches_the_flow():
    """Choose beta_1 to equal atan(C_m1/U_1) and the incidence must vanish."""
    trial = velocity_triangles(rpm=2900, flow_rate=0.030, beta1_deg=30.0)
    matched_beta1 = trial["beta1_flow_deg"]
    result = velocity_triangles(rpm=2900, flow_rate=0.030, beta1_deg=matched_beta1)
    assert result["incidence_deg"] == pytest.approx(0.0, abs=1e-9)
    assert result["shockless_entry"] is True


def test_zero_flow_limit_gives_the_shutoff_head():
    """As Q -> 0, C_m -> 0 and H -> sigma U_2^2 / g."""
    result = velocity_triangles(rpm=2900, flow_rate=1e-9)
    expected = result["slip_factor"] * result["u2"] ** 2 / 9.81
    assert result["head_euler_m"] == pytest.approx(expected, rel=1e-4)


def test_slip_reduces_work_below_the_ideal_blade_congruent_value():
    result = velocity_triangles(rpm=2900, flow_rate=0.030)
    assert 0.0 < result["slip_factor"] < 1.0
    assert result["work"] < result["work_ideal"]
    assert result["c_theta2"] < result["c_theta2_ideal"]


def test_more_blades_means_less_slip():
    few = slip_factor(25.0, 4, 0.3)["sigma"]
    many = slip_factor(25.0, 12, 0.3)["sigma"]
    assert many > few


def test_backswept_blade_gives_a_falling_head_curve():
    curve = head_flow_curve(2900, 0.045, 0.150, 30.0, 25.0, 0.030, 0.012, 7, q_max=0.06)
    assert np.all(np.diff(curve["head"]) < 0)


def test_nearly_radial_blade_gives_a_nearly_flat_head_curve():
    backswept = head_flow_curve(2900, 0.045, 0.150, 30.0, 20.0, 0.030, 0.012, 7, q_max=0.06)
    radial = head_flow_curve(2900, 0.045, 0.150, 30.0, 88.0, 0.030, 0.012, 7, q_max=0.06)
    drop_backswept = backswept["head"][0] - backswept["head"][-1]
    drop_radial = radial["head"][0] - radial["head"][-1]
    assert drop_radial < 0.2 * drop_backswept


def test_head_scales_with_the_square_of_speed_at_matched_flow_coefficient():
    """Affinity law: double the speed and double the flow, head goes up 4x."""
    base = velocity_triangles(rpm=1450, flow_rate=0.015)
    doubled = velocity_triangles(rpm=2900, flow_rate=0.030)
    assert doubled["head_euler_m"] / base["head_euler_m"] == pytest.approx(4.0, rel=1e-9)


def test_power_is_rho_q_work():
    result = velocity_triangles(rpm=2900, flow_rate=0.030, rho=998.2)
    assert result["power_w"] == pytest.approx(998.2 * 0.030 * result["work"])


def test_isometric_projection_preserves_lengths_along_the_view_plane():
    """A pure rotation cannot stretch anything; only the dropped axis is lost."""
    x = np.array([0.0, 1.0]); y = np.array([0.0, 0.0]); z = np.array([0.0, 0.0])
    u, v, depth = project_isometric(x, y, z, yaw_deg=0.0, pitch_deg=0.0)
    assert math.hypot(u[1] - u[0], v[1] - v[0]) == pytest.approx(1.0)
    # A point further from the viewer must sort behind one nearer.
    _, _, d = project_isometric([0, 0], [0, 1], [0, 0], yaw_deg=0.0, pitch_deg=0.0)
    assert d[1] > d[0]


@pytest.mark.parametrize("kwargs", [
    dict(beta2_deg=0.0), dict(beta2_deg=90.0), dict(beta1_deg=-5.0),
    dict(rpm=0.0), dict(flow_rate=0.0), dict(r2=0.01), dict(hydraulic_efficiency=0.0),
])
def test_invalid_impeller_inputs_are_rejected(kwargs):
    base = dict(rpm=2900, flow_rate=0.030)
    base.update(kwargs)
    with pytest.raises(ValueError):
        velocity_triangles(**base)


def test_inlet_radius_must_be_smaller_than_outlet():
    with pytest.raises(ValueError):
        blade_camberline(0.15, 0.05, 30.0, 25.0)
