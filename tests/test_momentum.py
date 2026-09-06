"""Control-volume momentum results checked against invariants, not memory.

Each test states the physical fact it is pinning. Where a closed-form result
exists (Betz, Borda-Carnot, Belanger) it is re-derived here by an independent
route -- numerically solving the same balance, or differentiating -- so a typo
in the module cannot agree with a typo in the test.
"""

import math

import pytest
from scipy.optimize import brentq, minimize_scalar

from src.physics import momentum as mom

RHO = 1000.0


# --------------------------------------------------------------------------
# Jets
# --------------------------------------------------------------------------
def test_stationary_plate_takes_the_whole_momentum_flux():
    """A jet stopped dead on a normal plate (90 deg turn) delivers rho A V^2."""
    out = mom.jet_on_vane(RHO, 0.01, 20.0, vane_speed=0.0, deflection_deg=90.0)
    assert out["force_x"] == pytest.approx(RHO * 0.01 * 20.0**2)
    assert out["power"] == 0.0  # a stationary vane does no work, whatever the force


def test_reversing_bucket_doubles_the_force_of_a_flat_plate():
    flat = mom.jet_on_vane(RHO, 0.01, 20.0, deflection_deg=90.0)
    bucket = mom.jet_on_vane(RHO, 0.01, 20.0, deflection_deg=180.0)
    assert bucket["force_x"] == pytest.approx(2.0 * flat["force_x"])
    assert bucket["force_y"] == pytest.approx(0.0, abs=1e-9)


def test_pelton_power_peaks_at_half_the_jet_speed():
    """eta = 4U(V-U)/V^2 for a series of reversing buckets: max eta = 1 at U = V/2."""
    v = 20.0

    def negative_power(u):
        return -mom.jet_on_vane(RHO, 0.01, v, vane_speed=u, deflection_deg=180.0)["power"]

    best = minimize_scalar(negative_power, bounds=(0.0, v), method="bounded")
    assert best.x == pytest.approx(v / 2.0, rel=1e-3)
    peak = mom.jet_on_vane(RHO, 0.01, v, vane_speed=v / 2.0, deflection_deg=180.0)
    assert peak["efficiency"] == pytest.approx(1.0, rel=1e-9)
    assert peak["optimum_vane_speed"] == pytest.approx(v / 2.0)


def test_single_vane_peaks_at_one_third_because_it_loses_mass_flow():
    v = 20.0

    def negative_power(u):
        return -mom.jet_on_vane(
            RHO, 0.01, v, vane_speed=u, deflection_deg=180.0, series=False
        )["power"]

    best = minimize_scalar(negative_power, bounds=(0.0, v), method="bounded")
    assert best.x == pytest.approx(v / 3.0, rel=1e-3)
    # And its best efficiency is well under the Pelton wheel's.
    single = mom.jet_on_vane(RHO, 0.01, v, vane_speed=v / 3.0, deflection_deg=180.0, series=False)
    assert single["efficiency"] == pytest.approx(16.0 / 27.0, rel=1e-6)


# --------------------------------------------------------------------------
# Bends
# --------------------------------------------------------------------------
def test_straight_constant_area_pipe_needs_no_anchor():
    """With no turn, no area change and no loss, the two faces cancel exactly."""
    out = mom.bend_force(RHO, 0.1, 0.1, 0.02, 200e3, angle_deg=0.0)
    assert out["force"] == pytest.approx(0.0, abs=1e-6)


def test_return_bend_carries_the_sum_of_both_faces():
    """At 180 degrees the two contributions add rather than cancel."""
    d, q, p1 = 0.1, 0.02, 200e3
    out = mom.bend_force(RHO, d, d, q, p1, angle_deg=180.0)
    a = math.pi * d**2 / 4.0
    u = q / a
    assert out["force_x"] == pytest.approx(2.0 * (p1 * a + RHO * q * u))
    assert out["force_y"] == pytest.approx(0.0, abs=1e-9)


def test_ninety_degree_bend_matches_a_hand_balance():
    d, q, p1 = 0.15, 0.05, 150e3
    out = mom.bend_force(RHO, d, d, q, p1, angle_deg=90.0)
    a = math.pi * d**2 / 4.0
    u = q / a
    # Equal areas and no loss keep p2 = p1, so each face contributes the same.
    assert out["p2_gauge"] == pytest.approx(p1)
    assert out["force_x"] == pytest.approx(p1 * a + RHO * q * u)
    assert out["force_y"] == pytest.approx(-(p1 * a + RHO * q * u))
    assert out["direction_deg"] == pytest.approx(-45.0)


def test_a_loss_lowers_the_outlet_pressure_and_the_anchor_force():
    args = (RHO, 0.15, 0.1, 0.05, 150e3, 90.0)
    ideal = mom.bend_force(*args, loss_k=0.0)
    lossy = mom.bend_force(*args, loss_k=0.9)
    assert lossy["p2_gauge"] < ideal["p2_gauge"]
    assert lossy["force"] < ideal["force"]


# --------------------------------------------------------------------------
# Sudden expansion
# --------------------------------------------------------------------------
def test_expansion_pressure_rises_while_head_is_lost():
    out = mom.sudden_expansion(RHO, 0.05, 0.1, 3.0, p1_gauge=100e3)
    assert out["u_out"] == pytest.approx(3.0 * 0.25)
    assert out["pressure_rise"] > 0  # decelerating flow recovers pressure
    assert out["head_loss"] > 0  # and still dissipates energy


def test_the_bernoulli_defect_is_exactly_the_borda_carnot_loss():
    """Momentum and energy on the same control volume differ by rho g h_L."""
    out = mom.sudden_expansion(RHO, 0.05, 0.09, 4.0)
    assert out["pressure_defect"] == pytest.approx(RHO * mom.G * out["head_loss"])


def test_exit_into_a_large_tank_throws_away_one_velocity_head():
    out = mom.sudden_expansion(RHO, 0.05, 5.0, 3.0)
    assert out["loss_coefficient"] == pytest.approx(1.0, rel=2e-3)
    assert out["head_loss"] == pytest.approx(3.0**2 / (2 * mom.G), rel=2e-3)


def test_expansion_requires_an_expansion():
    with pytest.raises(ValueError):
        mom.sudden_expansion(RHO, 0.1, 0.05, 2.0)


# --------------------------------------------------------------------------
# Hydraulic jump
# --------------------------------------------------------------------------
def test_the_conjugate_depth_is_the_other_root_of_the_momentum_function():
    """Belanger is only a shortcut: solve M(y2) = M(y1) numerically instead."""
    y1, q = 0.3, 2.5
    out = mom.hydraulic_jump(y1, q)
    target = mom.momentum_function(y1, q)
    root = brentq(lambda y: mom.momentum_function(y, q) - target, out["critical_depth"], 10.0)
    assert out["y2"] == pytest.approx(root, rel=1e-9)


def test_a_jump_conserves_momentum_and_destroys_energy():
    out = mom.hydraulic_jump(0.3, 2.5)
    assert out["momentum_2"] == pytest.approx(out["momentum_1"], rel=1e-9)
    assert out["energy_2"] < out["energy_1"]
    # The closed-form loss must agree with the difference it claims to be.
    assert out["energy_loss"] == pytest.approx(out["energy_loss_from_difference"], rel=1e-9)


def test_the_jump_climbs_through_critical_depth():
    out = mom.hydraulic_jump(0.3, 2.5)
    assert out["froude_1"] > 1.0 > out["froude_2"]
    assert out["y1"] < out["critical_depth"] < out["y2"]
    assert out["exists"]


def test_a_subcritical_approach_has_no_jump():
    out = mom.hydraulic_jump(2.0, 2.5)
    assert out["froude_1"] < 1.0
    assert not out["exists"]
    assert out["y2"] < out["y1"]  # the other root is a drop, not a jump


def test_stronger_jumps_dissipate_a_larger_fraction():
    weak = mom.hydraulic_jump(0.5, 2.5)
    strong = mom.hydraulic_jump(0.2, 2.5)
    assert strong["froude_1"] > weak["froude_1"]
    assert strong["loss_fraction"] > weak["loss_fraction"]


# --------------------------------------------------------------------------
# Weirs and gates
# --------------------------------------------------------------------------
def test_weir_powers_of_head_are_what_the_geometry_implies():
    """Doubling H multiplies Q by 2^1.5 (rectangular) and 2^2.5 (V-notch)."""
    rect = [mom.rectangular_weir(h, 1.0, crest_height=0.5, cd=0.62)["discharge"] for h in (0.1, 0.2)]
    vee = [mom.v_notch_weir(h)["discharge"] for h in (0.1, 0.2)]
    assert rect[1] / rect[0] == pytest.approx(2.0**1.5, rel=1e-9)
    assert vee[1] / vee[0] == pytest.approx(2.0**2.5, rel=1e-9)


def test_the_ideal_weir_discharge_is_the_integral_it_claims_to_be():
    """Q_ideal = integral_0^H b sqrt(2 g h) dh, done numerically."""
    h, b = 0.25, 1.5
    steps = 200_000
    dh = h / steps
    integral = sum(
        b * math.sqrt(2 * mom.G * (i + 0.5) * dh) * dh for i in range(steps)
    )
    assert mom.rectangular_weir(h, b)["ideal_discharge"] == pytest.approx(integral, rel=1e-6)


def test_rehbock_raises_cd_as_the_nappe_grows_relative_to_the_crest():
    assert mom.rehbock_cd(0.1, 0.5) == pytest.approx(0.611 + 0.075 * 0.2)
    assert mom.rehbock_cd(0.3, 0.5) > mom.rehbock_cd(0.1, 0.5)


def test_broad_crested_weir_puts_critical_depth_on_the_crest():
    out = mom.broad_crested_weir(0.3, 2.0, cd=1.0)
    q_unit = out["discharge"] / 2.0
    # Fr = 1 on the crest: q = sqrt(g) y_c^(3/2), so y_c = (q^2/g)^(1/3).
    assert (q_unit**2 / mom.G) ** (1 / 3) == pytest.approx(out["critical_depth"], rel=1e-9)
    assert out["critical_depth"] == pytest.approx(2 * 0.3 / 3)


def test_sluice_gate_discharge_satisfies_the_energy_balance_it_came_from():
    out = mom.sluice_gate(2.0, 0.3)
    q = out["unit_discharge"]
    upstream = mom.specific_energy(2.0, q)
    downstream = mom.specific_energy(out["y2"], q)
    assert downstream == pytest.approx(upstream, rel=1e-9)
    assert out["froude_1"] < 1.0 < out["froude_2"]  # the gate forces supercritical flow


def test_the_gate_carries_less_than_the_hydrostatic_thrust():
    out = mom.sluice_gate(2.0, 0.3)
    assert 0.0 < out["force_ratio"] < 1.0
    assert out["gate_force_per_width"] < out["hydrostatic_force_per_width"]


# --------------------------------------------------------------------------
# Rockets
# --------------------------------------------------------------------------
def test_pressure_thrust_vanishes_when_the_nozzle_is_perfectly_expanded():
    matched = mom.rocket_thrust(250.0, 2800.0, exit_pressure=101325.0,
                                ambient_pressure=101325.0, exit_area=0.8)
    assert matched["pressure_thrust"] == pytest.approx(0.0)
    assert matched["effective_exhaust_velocity"] == pytest.approx(2800.0)


def test_the_same_engine_gains_thrust_in_vacuum():
    sea_level = mom.rocket_thrust(250.0, 2800.0, exit_pressure=60e3,
                                  ambient_pressure=101325.0, exit_area=0.8)
    vacuum = mom.rocket_thrust(250.0, 2800.0, exit_pressure=60e3,
                               ambient_pressure=0.0, exit_area=0.8)
    assert vacuum["thrust"] > sea_level["thrust"]
    assert vacuum["thrust"] - sea_level["thrust"] == pytest.approx(101325.0 * 0.8)
    assert vacuum["specific_impulse"] > sea_level["specific_impulse"]


def test_delta_v_is_logarithmic_in_mass_ratio_and_its_inverse_agrees():
    out = mom.tsiolkovsky(3000.0, 500e3, 50e3)
    assert out["delta_v_ideal"] == pytest.approx(3000.0 * math.log(10.0))
    assert mom.rocket_mass_ratio_for(out["delta_v_ideal"], 3000.0) == pytest.approx(10.0)
    # Doubling delta-v squares the mass ratio: the exponential cost.
    assert mom.rocket_mass_ratio_for(2 * out["delta_v_ideal"], 3000.0) == pytest.approx(100.0)


def test_gravity_loss_is_charged_for_the_time_spent_thrusting():
    fast = mom.tsiolkovsky(3000.0, 500e3, 50e3, burn_time=60.0)
    slow = mom.tsiolkovsky(3000.0, 500e3, 50e3, burn_time=180.0)
    assert fast["delta_v_ideal"] == pytest.approx(slow["delta_v_ideal"])
    assert slow["delta_v_net"] < fast["delta_v_net"]
    assert fast["gravity_loss"] == pytest.approx(mom.G0 * 60.0)


# --------------------------------------------------------------------------
# Actuator disc
# --------------------------------------------------------------------------
def test_betz_limit_is_where_the_power_coefficient_actually_peaks():
    """Maximise Cp(a) numerically rather than trusting the quoted 16/27."""
    best = minimize_scalar(
        lambda a: -mom.actuator_disk(1.225, 100.0, 10.0, a)["power_coefficient"],
        bounds=(0.0, 0.5),
        method="bounded",
    )
    assert best.x == pytest.approx(1 / 3, rel=1e-3)
    peak = mom.actuator_disk(1.225, 100.0, 10.0, 1 / 3)
    assert peak["power_coefficient"] == pytest.approx(16 / 27, rel=1e-9)
    assert peak["betz_limit"] == pytest.approx(16 / 27)


def test_half_the_slowdown_happens_upstream_of_the_disc():
    out = mom.actuator_disk(1.225, 100.0, 10.0, 0.2)
    assert out["u_disk"] == pytest.approx(0.5 * (10.0 + out["u_wake"]))


def test_disc_power_is_the_thrust_working_at_the_disc_speed():
    out = mom.actuator_disk(1.225, 100.0, 12.0, 0.25)
    assert out["power"] == pytest.approx(out["thrust"] * out["u_disk"])
    assert out["power_coefficient"] < out["betz_limit"]
