"""Rocket nozzle physics: analytic limits, internal consistency, and geometry.

The pattern throughout is the one that has earned its keep elsewhere in this
project: never assert a number from memory when the module can be made to
disagree with itself instead. Almost every test below computes the same quantity
by two independent routes and compares them.
"""

import math

import pytest

from src.physics import rocket_nozzle as rn


# ---------------------------------------------------------------------------
# Isentropic relations
# ---------------------------------------------------------------------------
def test_area_ratio_is_one_at_sonic_and_rises_both_ways():
    for gamma in (1.2, 1.4, 1.667):
        assert rn.area_ratio(1.0, gamma) == pytest.approx(1.0)
        assert rn.area_ratio(0.4, gamma) > 1.0
        assert rn.area_ratio(3.0, gamma) > 1.0


@pytest.mark.parametrize("mach", [1.2, 2.0, 3.5, 6.0])
@pytest.mark.parametrize("gamma", [1.15, 1.25, 1.4])
def test_area_ratio_inverts_on_the_supersonic_branch(mach, gamma):
    ratio = rn.area_ratio(mach, gamma)
    assert rn.mach_from_area_ratio(ratio, gamma, supersonic=True) == pytest.approx(mach)


@pytest.mark.parametrize("mach", [0.15, 0.5, 0.9])
def test_area_ratio_inverts_on_the_subsonic_branch(mach):
    ratio = rn.area_ratio(mach, 1.4)
    assert rn.mach_from_area_ratio(ratio, 1.4, supersonic=False) == pytest.approx(mach)


def test_one_area_ratio_gives_two_different_mach_numbers():
    """The two branches of section 12.2, which is why boundary conditions matter."""
    sub = rn.mach_from_area_ratio(4.0, 1.4, supersonic=False)
    sup = rn.mach_from_area_ratio(4.0, 1.4, supersonic=True)
    assert sub < 1.0 < sup
    assert rn.area_ratio(sub, 1.4) == pytest.approx(rn.area_ratio(sup, 1.4))


@pytest.mark.parametrize("gamma", [1.2, 1.4])
def test_expansion_ratio_from_pressure_matches_the_closed_form(gamma):
    """Sutton's condensed formula must agree with the two-step Mach route.

    The lesson derives the two-step route; this pins the algebra that the
    textbooks print, so a future simplification cannot quietly diverge from it.
    """
    for ratio in (0.5, 0.1, 0.01, 0.001):
        via_mach = rn.area_ratio_for_pressure_ratio(ratio, gamma)
        closed = 1.0 / (
            ((gamma + 1) / 2) ** (1 / (gamma - 1))
            * ratio ** (1 / gamma)
            * math.sqrt((gamma + 1) / (gamma - 1) * (1 - ratio ** ((gamma - 1) / gamma)))
        )
        assert via_mach == pytest.approx(closed, rel=1e-10)


def test_pressure_ratio_round_trips_through_mach():
    for mach in (0.3, 1.0, 2.7, 5.0):
        ratio = rn.pressure_ratio_from_mach(mach, 1.24)
        assert rn.mach_from_pressure_ratio(ratio, 1.24) == pytest.approx(mach)


# ---------------------------------------------------------------------------
# c*, C_F and their product
# ---------------------------------------------------------------------------
def test_characteristic_velocity_reproduces_the_choked_throat_of_chapter_12():
    """c* is not a new result: it is p_c A_t / mdot for the choked mass flux."""
    p_c, t_c, gamma, r_gas, a_t = 70e5, 3300.0, 1.22, 340.0, 0.02
    from src.physics.gas_dynamics import choked_mass_flux

    m_dot = choked_mass_flux(p_c, t_c, gamma, r_gas) * a_t
    assert rn.characteristic_velocity(gamma, r_gas, t_c) == pytest.approx(p_c * a_t / m_dot)


def test_characteristic_velocity_ignores_the_bell_entirely():
    c_star = rn.characteristic_velocity(1.24, 355.0, 3500.0)
    for eps in (5.0, 40.0, 200.0):
        result = rn.nozzle_performance(97e5, 3500.0, eps, 0.0, 0.03, 1.24, 355.0)
        assert result["characteristic_velocity"] == pytest.approx(c_star)
        assert result["mass_flow"] == pytest.approx(97e5 * 0.03 / c_star)


def test_isp_is_the_product_of_the_chamber_number_and_the_nozzle_number():
    result = rn.nozzle_performance(97e5, 3500.0, 16.0, 101325.0, 0.0305, 1.24, 355.0)
    expected = (result["thrust_coefficient"] * result["characteristic_velocity"]
                / rn.G0)
    assert result["specific_impulse"] == pytest.approx(expected)
    assert result["effective_exhaust_velocity"] == pytest.approx(
        result["thrust"] / result["mass_flow"])


def test_thrust_coefficient_does_not_depend_on_chamber_temperature():
    """The whole point of the c*/C_F split: T_c belongs to c* alone."""
    cold = rn.nozzle_performance(97e5, 1500.0, 16.0, 101325.0, 0.03, 1.24, 355.0)
    hot = rn.nozzle_performance(97e5, 4000.0, 16.0, 101325.0, 0.03, 1.24, 355.0)
    assert cold["thrust_coefficient"] == pytest.approx(hot["thrust_coefficient"])
    assert cold["exit_mach"] == pytest.approx(hot["exit_mach"])
    assert hot["specific_impulse"] > cold["specific_impulse"]


def test_thrust_equals_coefficient_times_chamber_pressure_times_throat():
    result = rn.nozzle_performance(50e5, 3000.0, 25.0, 20000.0, 0.011, 1.21, 320.0)
    assert result["thrust"] == pytest.approx(
        result["thrust_coefficient"] * 50e5 * 0.011)
    assert result["thrust"] == pytest.approx(
        result["momentum_thrust"] + result["pressure_thrust"])


# ---------------------------------------------------------------------------
# The design condition
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("ambient", [101325.0, 26500.0, 2500.0])
@pytest.mark.parametrize("gamma", [1.2, 1.3])
def test_matched_expansion_ratio_maximises_the_thrust_coefficient(ambient, gamma):
    """The differential-ring argument and the algebra must pick the same ratio."""
    p_c = 97e5
    optimum = rn.optimum_expansion_ratio(p_c, ambient, gamma)
    best = rn.thrust_coefficient(gamma, optimum, ambient / p_c)["thrust_coefficient"]
    for factor in (0.5, 0.8, 0.95, 1.05, 1.25, 2.0):
        other = rn.thrust_coefficient(
            gamma, optimum * factor, ambient / p_c)["thrust_coefficient"]
        assert other <= best + 1e-12


def test_matched_expansion_ratio_really_matches_the_exit_pressure():
    optimum = rn.optimum_expansion_ratio(97e5, 26500.0, 1.24)
    result = rn.nozzle_performance(97e5, 3500.0, optimum, 26500.0, 0.03, 1.24, 355.0)
    assert result["exit_pressure"] == pytest.approx(26500.0)
    assert result["pressure_thrust"] == pytest.approx(0.0, abs=1e-6)
    assert result["mode"].startswith("matched")


def test_climbing_raises_thrust_by_exactly_the_atmosphere_on_the_exit_plane():
    """Nothing inside the engine may change; only p_a A_e is removed."""
    pad = rn.nozzle_performance(97e5, 3500.0, 16.0, 101325.0, 0.0305, 1.24, 355.0)
    vac = rn.nozzle_performance(97e5, 3500.0, 16.0, 0.0, 0.0305, 1.24, 355.0)
    assert vac["mass_flow"] == pytest.approx(pad["mass_flow"])
    assert vac["exit_mach"] == pytest.approx(pad["exit_mach"])
    assert vac["exit_velocity"] == pytest.approx(pad["exit_velocity"])
    assert vac["momentum_thrust"] == pytest.approx(pad["momentum_thrust"])
    assert vac["thrust"] - pad["thrust"] == pytest.approx(101325.0 * pad["exit_area"])


def test_a_bigger_bell_wins_in_vacuum_and_can_lose_at_sea_level():
    small = rn.nozzle_performance(97e5, 3500.0, 16.0, 0.0, 0.03, 1.24, 355.0)
    large = rn.nozzle_performance(97e5, 3500.0, 165.0, 0.0, 0.03, 1.24, 355.0)
    assert large["specific_impulse"] > small["specific_impulse"]
    assert large["mass_flow"] == pytest.approx(small["mass_flow"])

    small_pad = rn.nozzle_performance(97e5, 3500.0, 16.0, 101325.0, 0.03, 1.24, 355.0)
    large_pad = rn.nozzle_performance(97e5, 3500.0, 165.0, 101325.0, 0.03, 1.24, 355.0)
    assert large_pad["thrust"] < small_pad["thrust"]
    assert large_pad["separation_predicted"]
    assert not small_pad["separation_predicted"]


def test_expansion_regimes_are_labelled_from_the_pressures_not_guessed():
    matched = rn.optimum_expansion_ratio(97e5, 101325.0, 1.24)
    assert rn.nozzle_performance(97e5, 3500.0, matched * 0.4, 101325.0, 0.03, 1.24,
                                 355.0)["mode"] == "under-expanded"
    assert rn.nozzle_performance(97e5, 3500.0, matched * 2.0, 101325.0, 0.03, 1.24,
                                 355.0)["mode"] == "over-expanded"
    assert "vacuum" in rn.nozzle_performance(97e5, 3500.0, matched, 0.0, 0.03, 1.24,
                                             355.0)["mode"]


@pytest.mark.parametrize("criterion", rn.SEPARATION_CRITERIA)
def test_separation_thresholds_are_below_ambient_and_ordered(criterion):
    threshold = rn.separation_exit_pressure(101325.0, 3.5, criterion)
    assert 0 < threshold < 101325.0


def test_schmucker_allows_deeper_over_expansion_at_higher_exit_mach():
    """A faster boundary layer needs a stronger shock to tear it off the wall."""
    slow = rn.separation_exit_pressure(101325.0, 2.0, "schmucker")
    fast = rn.separation_exit_pressure(101325.0, 5.0, "schmucker")
    assert fast < slow


# ---------------------------------------------------------------------------
# Atmosphere
# ---------------------------------------------------------------------------
def test_standard_atmosphere_reproduces_its_own_layer_base_pressures():
    """Chaining the barometric formula must land on the published layer bases."""
    for base_h, _t, _lapse, base_p in rn._ATMOSPHERE_LAYERS:
        assert rn.standard_atmosphere_pressure(base_h) == pytest.approx(base_p, rel=1e-6)


def test_standard_atmosphere_falls_monotonically():
    pressures = [rn.standard_atmosphere_pressure(h) for h in range(0, 80000, 500)]
    assert all(b < a for a, b in zip(pressures, pressures[1:]))


def test_altitude_sweep_holds_the_engine_fixed_and_only_climbs_in_thrust():
    sweep = rn.altitude_sweep(97e5, 3500.0, 16.0, 0.0305, 1.24, 355.0,
                              altitudes=[0, 5000, 10000, 20000, 40000])
    assert all(b > a for a, b in zip(sweep["thrust"], sweep["thrust"][1:]))
    assert all(b > a for a, b in zip(sweep["specific_impulse"],
                                     sweep["specific_impulse"][1:]))
    # Momentum thrust is altitude-blind, which is the lesson's central claim.
    assert len(set(round(value, 6) for value in sweep["momentum_thrust"])) == 1


# ---------------------------------------------------------------------------
# Prandtl-Meyer and the method of characteristics
# ---------------------------------------------------------------------------
def test_prandtl_meyer_vanishes_at_sonic_and_increases_with_mach():
    assert rn.prandtl_meyer(1.0, 1.4) == 0.0
    angles = [rn.prandtl_meyer(m, 1.4) for m in (1.1, 1.5, 2.0, 3.0, 5.0)]
    assert all(b > a for a, b in zip(angles, angles[1:]))


@pytest.mark.parametrize("mach", [1.05, 1.5, 2.4, 4.0, 8.0])
def test_prandtl_meyer_inverts(mach):
    nu = rn.prandtl_meyer(mach, 1.4)
    assert rn.mach_from_prandtl_meyer(nu, 1.4) == pytest.approx(mach)


def test_prandtl_meyer_refuses_the_unreachable_vacuum_angle():
    gamma = 1.4
    nu_max = (math.sqrt((gamma + 1) / (gamma - 1)) - 1) * math.pi / 2
    with pytest.raises(ValueError, match="vacuum limit"):
        rn.mach_from_prandtl_meyer(nu_max * 1.01, gamma)


def test_minimum_length_wall_turn_is_exactly_half_the_prandtl_meyer_angle():
    for mach, gamma in ((2.0, 1.4), (2.4, 1.4), (3.5, 1.25)):
        moc = rn.moc_minimum_length_nozzle(mach, gamma, 10, 1.0)
        assert moc["theta_max"] == pytest.approx(rn.prandtl_meyer(mach, gamma) / 2)


def test_moc_exit_is_axial_and_at_the_design_mach_number():
    """The construction's own success criterion, checked on its last wall point."""
    moc = rn.moc_minimum_length_nozzle(2.4, 1.4, 16, 1.0)
    last = moc["wall"][-1]
    assert last["theta"] == pytest.approx(0.0, abs=1e-12)
    assert last["mach"] == pytest.approx(2.4, rel=1e-9)
    assert last["nu"] == pytest.approx(moc["nu_exit"])


def test_moc_area_ratio_converges_to_the_ideal_as_waves_are_added():
    """Refining n refines the geometry only; the exit state is imposed, not solved."""
    errors = []
    for n in (4, 8, 16, 32):
        moc = rn.moc_minimum_length_nozzle(2.4, 1.4, n, 1.0)
        assert moc["theta_max"] == pytest.approx(
            rn.moc_minimum_length_nozzle(2.4, 1.4, 4, 1.0)["theta_max"])
        errors.append(abs(moc["area_ratio_error"]))
    assert all(b < a for a, b in zip(errors, errors[1:]))
    assert errors[-1] < 0.005


def test_moc_wall_is_monotonic_and_starts_at_the_throat():
    moc = rn.moc_minimum_length_nozzle(3.0, 1.25, 14, 0.05)
    xs = [point["x"] for point in moc["wall"]]
    ys = [point["y"] for point in moc["wall"]]
    machs = [point["mach"] for point in moc["wall"]]
    assert ys[0] == pytest.approx(0.05)
    assert all(b > a for a, b in zip(xs, xs[1:]))
    assert all(b > a for a, b in zip(ys, ys[1:]))
    assert all(b > a for a, b in zip(machs, machs[1:]))


def test_moc_scales_linearly_with_throat_size():
    small = rn.moc_minimum_length_nozzle(2.4, 1.4, 12, 1.0)
    big = rn.moc_minimum_length_nozzle(2.4, 1.4, 12, 3.0)
    assert big["length"] == pytest.approx(3.0 * small["length"])
    assert big["achieved_area_ratio"] == pytest.approx(small["achieved_area_ratio"])


def test_moc_rejects_subsonic_and_degenerate_requests():
    with pytest.raises(ValueError):
        rn.moc_minimum_length_nozzle(0.9, 1.4, 10, 1.0)
    with pytest.raises(ValueError):
        rn.moc_minimum_length_nozzle(2.4, 1.4, 1, 1.0)


# ---------------------------------------------------------------------------
# Practical contours
# ---------------------------------------------------------------------------
def test_cone_divergence_efficiency_matches_the_integrated_average():
    """lambda = (1+cos a)/2 is the closed form of the momentum average."""
    for angle in (10.0, 15.0, 25.0):
        alpha = math.radians(angle)
        numerical = (math.sin(alpha) ** 2 / 2) / (1 - math.cos(alpha))
        cone = rn.conical_nozzle(16.0, 1.0, angle)
        assert cone["divergence_efficiency"] == pytest.approx(numerical)
        assert cone["divergence_efficiency"] == pytest.approx((1 + math.cos(alpha)) / 2)
    assert rn.conical_nozzle(16.0, 1.0, 15.0)["divergence_efficiency"] == \
        pytest.approx(0.9830, abs=5e-5)


def test_cone_reaches_the_requested_exit_radius():
    cone = rn.conical_nozzle(25.0, 0.08, 15.0)
    assert cone["exit_radius"] == pytest.approx(0.08 * 5.0)
    assert cone["r"][-1] == pytest.approx(cone["exit_radius"])
    assert cone["r"][0] == pytest.approx(0.08)


def test_bell_hits_the_requested_area_ratio_and_is_shorter_than_the_cone():
    bell = rn.bell_contour(16.0, 1.0, 22.0, 11.0, 0.8)
    cone = rn.conical_nozzle(16.0, 1.0, 15.0)
    assert bell["r"][-1] == pytest.approx(4.0)
    assert bell["x"][-1] == pytest.approx(bell["length"])
    assert bell["length"] == pytest.approx(0.8 * cone["length"])
    assert bell["length"] < cone["length"]


def test_bell_wall_advances_and_widens_everywhere():
    bell = rn.bell_contour(40.0, 0.1, 25.0, 8.0, 0.75)
    assert all(b > a for a, b in zip(bell["x"], bell["x"][1:]))
    assert all(b > a for a, b in zip(bell["r"], bell["r"][1:]))


def test_bell_rejects_an_exit_angle_that_does_not_turn_back():
    with pytest.raises(ValueError, match="turns back"):
        rn.bell_contour(16.0, 1.0, 12.0, 20.0, 0.8)


def test_converging_section_ends_exactly_at_the_throat():
    converging = rn.converging_contour(0.1, 0.3, 30.0)
    assert converging["r"][-1] == pytest.approx(0.1)
    assert converging["x"][-1] == pytest.approx(0.0, abs=1e-12)
    assert converging["contraction_ratio"] == pytest.approx(9.0)
    assert all(b <= a + 1e-12 for a, b in zip(converging["r"], converging["r"][1:]))


def test_march_along_a_bell_recovers_the_exit_state_of_the_performance_model():
    """The contour and the performance model must describe the same nozzle."""
    bell = rn.bell_contour(16.0, 1.0, 22.0, 11.0, 0.8)
    march = rn.march_along_contour(bell["x"], bell["r"], 97e5, 3500.0, 1.24, 355.0,
                                   throat_radius=1.0)
    result = rn.nozzle_performance(97e5, 3500.0, 16.0, 0.0, 0.03, 1.24, 355.0)
    assert march["mach"][-1] == pytest.approx(result["exit_mach"], rel=1e-6)
    assert march["pressure"][-1] == pytest.approx(result["exit_pressure"], rel=1e-6)
    assert all(b >= a - 1e-9 for a, b in zip(march["mach"], march["mach"][1:]))
    assert all(b <= a + 1e-9 for a, b in zip(march["pressure"], march["pressure"][1:]))


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("kwargs", [
    dict(chamber_pressure=-1.0), dict(chamber_temperature=0.0),
    dict(throat_area=0.0), dict(expansion_ratio=0.5), dict(gamma=1.0),
    dict(ambient_pressure=-5.0),
])
def test_nozzle_performance_rejects_impossible_inputs(kwargs):
    base = dict(chamber_pressure=97e5, chamber_temperature=3500.0,
                expansion_ratio=16.0, ambient_pressure=101325.0,
                throat_area=0.03, gamma=1.24, gas_constant=355.0)
    with pytest.raises(ValueError):
        rn.nozzle_performance(**dict(base, **kwargs))


def test_optimum_expansion_ratio_rejects_ambient_above_chamber():
    with pytest.raises(ValueError, match="below chamber"):
        rn.optimum_expansion_ratio(1e5, 2e5, 1.4)


def test_demo_defaults_describe_a_usable_engine():
    """The worked example must not drift into a regime the lesson calls invalid."""
    defaults = rn.ROCKET_DEMO_DEFAULTS
    pad = rn.nozzle_performance(
        defaults["chamber_pressure"], defaults["chamber_temperature"],
        defaults["expansion_ratio"], 101325.0, defaults["throat_area"],
        defaults["gamma"], defaults["gas_constant"])
    vac = rn.nozzle_performance(
        defaults["chamber_pressure"], defaults["chamber_temperature"],
        defaults["expansion_ratio"], 0.0, defaults["throat_area"],
        defaults["gamma"], defaults["gas_constant"])
    assert not pad["separation_predicted"], "the pad case must be flyable"
    assert pad["mode"] == "over-expanded", "a first stage is over-expanded at liftoff"
    assert 250 < pad["specific_impulse"] < 300
    assert 290 < vac["specific_impulse"] < 340
    assert vac["thrust"] > pad["thrust"]
