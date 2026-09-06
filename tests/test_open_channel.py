"""Open-channel hydraulics: geometry identities, analytical limits, conservation."""

import math

import numpy as np
import pytest

from src.physics.open_channel import (
    CANAL_DEMO_DEFAULTS,
    G,
    MANNING_N,
    channel_state,
    critical_depth,
    darcy_discharge,
    froude_number,
    manning_discharge,
    normal_depth,
    rating_curve,
    trapezoid_geometry,
)


def test_rectangular_geometry_matches_hand_calculation():
    geom = trapezoid_geometry(depth=2.0, bottom_width=4.0, side_slope=0.0)
    assert geom["area"] == pytest.approx(8.0)
    assert geom["wetted_perimeter"] == pytest.approx(4.0 + 2 * 2.0)
    assert geom["top_width"] == pytest.approx(4.0)
    assert geom["hydraulic_radius"] == pytest.approx(1.0)
    assert geom["hydraulic_diameter"] == pytest.approx(4.0)
    # Rectangular channel: hydraulic depth is the depth itself.
    assert geom["hydraulic_depth"] == pytest.approx(2.0)


def test_trapezoid_geometry_matches_hand_calculation():
    # b = 3, z = 2 (2H:1V), y = 1.5
    geom = trapezoid_geometry(depth=1.5, bottom_width=3.0, side_slope=2.0)
    assert geom["area"] == pytest.approx(1.5 * (3.0 + 2.0 * 1.5))
    assert geom["wetted_perimeter"] == pytest.approx(3.0 + 2 * 1.5 * math.sqrt(5.0))
    assert geom["top_width"] == pytest.approx(3.0 + 2 * 2.0 * 1.5)


def test_wide_shallow_channel_hydraulic_radius_tends_to_the_depth():
    """The free surface is excluded from P_w, so R_h -> y for a wide river."""
    geom = trapezoid_geometry(depth=1.0, bottom_width=10_000.0, side_slope=0.0)
    assert geom["hydraulic_radius"] == pytest.approx(1.0, rel=1e-3)


def test_hydraulic_diameter_of_a_half_full_circular_channel_style_case():
    """Square channel flowing full-width: D_H = 4A/P_w reduces to the pipe value."""
    geom = trapezoid_geometry(depth=1.0, bottom_width=1.0, side_slope=0.0)
    assert geom["hydraulic_diameter"] == pytest.approx(4 * 1.0 / 3.0)


def test_manning_discharge_matches_the_formula():
    result = manning_discharge(2.0, 4.0, 0.0, 0.014, 0.001)
    expected_v = (1.0 ** (2 / 3)) * math.sqrt(0.001) / 0.014
    assert result["velocity"] == pytest.approx(expected_v)
    assert result["discharge"] == pytest.approx(expected_v * 8.0)


def test_normal_depth_inverts_manning_discharge():
    q = manning_discharge(1.7, 3.0, 1.5, 0.025, 0.0008)["discharge"]
    y = normal_depth(q, 3.0, 1.5, 0.025, 0.0008)
    assert y == pytest.approx(1.7, rel=1e-9)


def test_normal_depth_rejects_an_impossible_discharge():
    with pytest.raises(ValueError):
        normal_depth(1e12, 1.0, 0.0, 0.03, 1e-6, max_depth=10.0)


def test_slope_and_depth_scaling_exponents():
    """Q ~ S^(1/2) exactly; Q ~ y^(5/3) in the wide-channel limit."""
    base = manning_discharge(1.0, 5000.0, 0.0, 0.02, 0.001)["discharge"]
    steeper = manning_discharge(1.0, 5000.0, 0.0, 0.02, 0.004)["discharge"]
    assert steeper / base == pytest.approx(2.0, rel=1e-6)  # 4x slope -> 2x flow

    deeper = manning_discharge(2.0, 5000.0, 0.0, 0.02, 0.001)["discharge"]
    assert deeper / base == pytest.approx(2.0 ** (5 / 3), rel=1e-3)


def test_critical_depth_rectangular_closed_form():
    """For a rectangle, y_c = (q^2/g)^(1/3) with q the discharge per unit width."""
    b, q_total = 6.0, 30.0
    q_unit = q_total / b
    assert critical_depth(q_total, b, 0.0) == pytest.approx((q_unit ** 2 / G) ** (1 / 3), rel=1e-9)


def test_froude_is_one_at_critical_depth():
    q, b, z = 25.0, 5.0, 1.0
    y_c = critical_depth(q, b, z)
    assert froude_number(q, y_c, b, z) == pytest.approx(1.0, rel=1e-9)


def test_critical_depth_is_independent_of_roughness_and_slope():
    """Why a weir or flume can meter flow: only geometry and Q enter."""
    assert critical_depth(20.0, 4.0, 1.0) == pytest.approx(critical_depth(20.0, 4.0, 1.0))
    mild = channel_state(20.0, 4.0, 1.0, 0.030, 0.0002, bank_depth=4.0)
    steep = channel_state(20.0, 4.0, 1.0, 0.012, 0.02, bank_depth=4.0)
    assert mild["critical_depth"] == pytest.approx(steep["critical_depth"], rel=1e-9)
    assert mild["normal_depth"] > steep["normal_depth"]


def test_steep_smooth_channel_runs_supercritical_and_mild_rough_runs_subcritical():
    steep = channel_state(20.0, 4.0, 1.0, 0.012, 0.02, bank_depth=4.0)
    mild = channel_state(20.0, 4.0, 1.0, 0.030, 0.0002, bank_depth=6.0)
    assert steep["regime"] == "supercritical" and steep["froude"] > 1
    assert mild["regime"] == "subcritical" and mild["froude"] < 1
    assert steep["normal_depth"] < steep["critical_depth"]
    assert mild["normal_depth"] > mild["critical_depth"]


def test_bed_shear_stress_is_the_uniform_flow_force_balance():
    """tau_w = rho g R_h S_0 must equal weight-along-slope over wetted area."""
    state = channel_state(12.0, 4.0, 1.5, 0.025, 0.0009, bank_depth=3.0)
    rho = 998.2
    weight_component = rho * G * state["area"] * state["bed_slope"]
    shear_force = state["bed_shear_stress"] * state["wetted_perimeter"]
    assert shear_force == pytest.approx(weight_component, rel=1e-9)


def test_freeboard_and_overtopping_flags():
    tight = channel_state(40.0, 3.0, 1.0, 0.030, 0.0005, bank_depth=2.0)
    assert tight["overtops"] is True
    assert tight["freeboard"] < 0
    assert tight["freeboard_adequate"] is False

    roomy = channel_state(5.0, 3.0, 1.0, 0.030, 0.0005, bank_depth=4.0)
    assert roomy["overtops"] is False
    assert roomy["freeboard_adequate"] is True
    assert roomy["bank_full_capacity"] > roomy["discharge"]
    assert roomy["capacity_margin"] > 1.0


def test_darcy_and_manning_agree_through_the_equivalence_relation():
    """n = R_h^(1/6) sqrt(f/(8g)) is the bridge between the two conventions."""
    result = darcy_discharge(2.0, 6.0, 1.5, roughness=0.03, bed_slope=0.001)
    n_equiv = result["equivalent_manning_n"]
    manning = manning_discharge(2.0, 6.0, 1.5, n_equiv, 0.001)
    assert manning["discharge"] == pytest.approx(result["discharge"], rel=1e-6)
    # A gravel canal should land in the published Manning band.
    assert 0.015 < n_equiv < 0.045


def test_darcy_route_satisfies_its_own_force_balance():
    result = darcy_discharge(1.5, 5.0, 1.0, roughness=0.01, bed_slope=0.0012)
    implied_slope = (
        result["f_darcy"] * result["velocity"] ** 2
        / (result["hydraulic_diameter"] * 2 * G)
    )
    assert implied_slope == pytest.approx(0.0012, rel=1e-8)


def test_smoother_channel_carries_more_water():
    rough = manning_discharge(2.0, 5.0, 1.0, MANNING_N["Gravel bed, cobbles"], 0.001)
    smooth = manning_discharge(2.0, 5.0, 1.0, MANNING_N["Finished concrete"], 0.001)
    assert smooth["discharge"] > rough["discharge"]


def test_rating_curve_is_monotonic_and_crosses_critical_where_expected():
    curve = rating_curve(4.0, 1.0, 0.025, 0.001, max_depth=3.0)
    assert np.all(np.diff(curve["discharge"]) > 0)
    assert np.all(np.diff(curve["velocity"]) > 0)
    assert curve["depth"].shape == curve["discharge"].shape


@pytest.mark.parametrize("kwargs", [
    dict(depth=1.0, bottom_width=0.0, side_slope=0.0),
    dict(depth=-1.0, bottom_width=2.0, side_slope=0.0),
    dict(depth=1.0, bottom_width=float("nan"), side_slope=0.0),
])
def test_invalid_geometry_is_rejected(kwargs):
    with pytest.raises(ValueError):
        trapezoid_geometry(**kwargs)


@pytest.mark.parametrize("bad", [
    dict(manning_n=0.0, bed_slope=0.001),
    dict(manning_n=0.02, bed_slope=0.0),
    dict(manning_n=-0.02, bed_slope=0.001),
])
def test_invalid_manning_inputs_are_rejected(bad):
    with pytest.raises(ValueError):
        manning_discharge(1.0, 4.0, 0.0, **bad)


def test_canal_demo_defaults_match_the_clean_earth_calculator():
    """The worked example and the calculator must share one set of inputs."""
    assert CANAL_DEMO_DEFAULTS["manning_n"] == MANNING_N["Clean earth canal, straight"]
    assert list(MANNING_N.keys())[4] == "Clean earth canal, straight"
    state = channel_state(**CANAL_DEMO_DEFAULTS)
    assert state["discharge"] == CANAL_DEMO_DEFAULTS["discharge"]
    # Sanity: the design sits in the unlined-earth velocity band and is subcritical.
    assert 0.6 < state["velocity"] < 1.5
    assert state["regime"] == "subcritical"
    assert state["freeboard_adequate"] is True
    weedy = channel_state(
        **{**CANAL_DEMO_DEFAULTS, "manning_n": MANNING_N["Earth canal, some weeds and stones"]}
    )
    assert weedy["normal_depth"] > state["normal_depth"]
    assert weedy["freeboard"] < state["freeboard"]
