"""The momentum/heat/mass analogy, and the Blasius-derived flat-plate result."""

import math

import pytest

from src.physics.boundary_layer import BLASIUS_FPP0
from src.physics.transport_analogy import (
    CORRELATIONS,
    analogy_pair,
    chilton_colburn,
    diffusivities,
    pohlhausen_theta_gradient,
    sweep_reynolds,
    transport_correlation,
)


def test_diffusivities_all_have_the_same_units_and_expected_water_values():
    d = diffusivities()
    assert d["nu"] == pytest.approx(1.002e-3 / 998.2)
    assert d["alpha"] == pytest.approx(0.598 / (998.2 * 4182.0))
    # Water at 20 C: Pr near 7, Sc for a small molecule in the hundreds to low
    # thousands, so Le = Sc/Pr is large -- heat outruns species by ~2 orders.
    assert 6.0 < d["prandtl"] < 8.0
    assert 500 < d["schmidt"] < 900
    assert d["lewis"] == pytest.approx(d["schmidt"] / d["prandtl"])


def test_prandtl_schmidt_lewis_are_consistent_by_construction():
    d = diffusivities(rho=1.2, mu=1.8e-5, k_thermal=0.026, cp=1005.0, d_ab=2.0e-5)
    assert d["prandtl"] == pytest.approx(d["nu"] / d["alpha"])
    assert d["schmidt"] == pytest.approx(d["nu"] / d["d_ab"])
    assert d["lewis"] == pytest.approx(d["alpha"] / d["d_ab"])
    # Air: Pr and Sc are both near 0.7, so Le is near 1 -- heat and species
    # spread at nearly the same rate. That is why the analogy is so good in gases.
    assert 0.6 < d["prandtl"] < 0.8
    assert 0.5 < d["lewis"] < 1.6


# --------------------------------------------------------------------------
# The flat plate result, derived rather than fitted
# --------------------------------------------------------------------------

def test_at_prandtl_one_the_thermal_gradient_equals_blasius_fpp0():
    """Pr = 1 makes the energy equation *identical* to the momentum equation.

    theta'' + (Pr/2) f theta' = 0 with Pr = 1 is the equation f'' satisfies, and
    both have the same boundary conditions after scaling. So theta'(0) must come
    out as f''(0) = 0.332057, and it does -- which is the cleanest possible
    statement that heat transfer here is the momentum solution reused.
    """
    result = pohlhausen_theta_gradient(1.0)
    assert result["theta_gradient"] == pytest.approx(BLASIUS_FPP0, rel=1e-4)


@pytest.mark.parametrize("prandtl", [0.6, 0.7, 1.0, 7.0, 10.0, 50.0, 100.0])
def test_the_cube_root_power_law_matches_the_solved_ode(prandtl):
    """0.332 Pr^(1/3) is an approximation to the ODE, good to ~2% for Pr >= 0.6."""
    result = pohlhausen_theta_gradient(prandtl)
    assert result["theta_gradient"] == pytest.approx(
        0.332 * prandtl ** (1 / 3), rel=0.025
    )


def test_thermal_layer_thickness_ratio_follows_prandtl_to_the_minus_third():
    """delta_t/delta ~ Pr^(-1/3): a high-Pr fluid has a thin thermal layer."""
    for prandtl in (0.7, 7.0, 50.0):
        ratio = pohlhausen_theta_gradient(prandtl)["thickness_ratio"]
        assert ratio == pytest.approx(prandtl ** (-1 / 3), rel=0.25)
    thin = pohlhausen_theta_gradient(50.0)["thickness_ratio"]
    thick = pohlhausen_theta_gradient(0.7)["thickness_ratio"]
    assert thin < thick


def test_prandtl_one_thermal_layer_matches_the_velocity_layer():
    """At Pr = 1 the energy equation is the differentiated Blasius equation."""
    result = pohlhausen_theta_gradient(1.0)
    assert result["thickness_ratio"] == pytest.approx(1.0, rel=1e-3)
    assert result["eta_thermal_99"] == pytest.approx(result["eta_velocity_99"], rel=1e-3)


def test_higher_prandtl_gives_a_steeper_wall_gradient():
    gradients = [pohlhausen_theta_gradient(pr)["theta_gradient"] for pr in (0.7, 7.0, 70.0)]
    assert gradients[0] < gradients[1] < gradients[2]


def test_theta_profile_satisfies_its_boundary_conditions():
    result = pohlhausen_theta_gradient(7.0)
    assert result["theta"][0] == pytest.approx(0.0, abs=1e-12)
    assert result["theta"][-1] == pytest.approx(1.0, rel=1e-6)
    assert result["f_prime"][-1] == pytest.approx(1.0, rel=1e-3)


# --------------------------------------------------------------------------
# The analogy itself
# --------------------------------------------------------------------------

def test_heat_and_mass_use_literally_the_same_correlation():
    """Swapping Pr for Sc must give the identical number: that IS the analogy."""
    heat = transport_correlation("Sphere (Ranz-Marshall)", 100.0, 5.0, "heat")
    mass = transport_correlation("Sphere (Ranz-Marshall)", 100.0, 5.0, "mass")
    assert heat["value"] == pytest.approx(mass["value"])
    assert heat["symbol"] == "Nu" and mass["symbol"] == "Sh"


def test_flat_plate_laminar_reproduces_the_blasius_coefficient():
    result = transport_correlation("Flat plate, laminar (local)", 1e5, 1.0, "heat")
    assert result["value"] == pytest.approx(0.332 * math.sqrt(1e5))
    # And the coefficient is the Blasius wall gradient, to three figures.
    assert result["coefficient"] == pytest.approx(BLASIUS_FPP0, abs=5e-4)


def test_average_plate_result_is_twice_the_local_one():
    local = transport_correlation("Flat plate, laminar (local)", 1e5, 7.0)["value"]
    mean = transport_correlation("Flat plate, laminar (average)", 1e5, 7.0)["value"]
    assert mean == pytest.approx(2.0 * local)


def test_sphere_and_packed_bed_keep_the_conduction_floor():
    """Nu -> 2 as Re -> 0: a still sphere still conducts."""
    for geometry in ("Sphere (Ranz-Marshall)", "Packed bed (Wakao)"):
        tiny = transport_correlation(geometry, 1e-6, 1.0)["value"]
        assert tiny == pytest.approx(2.0, abs=1e-2)


def test_laminar_pipe_is_independent_of_reynolds_and_prandtl():
    a = transport_correlation("Pipe, laminar (constant wall T)", 500.0, 1.0)["value"]
    b = transport_correlation("Pipe, laminar (constant wall T)", 2000.0, 100.0)["value"]
    assert a == pytest.approx(3.66) and b == pytest.approx(3.66)


def test_out_of_range_inputs_are_reported_not_silently_extrapolated():
    result = transport_correlation("Pipe, turbulent (Dittus-Boelter)", 500.0, 7.0)
    assert not result["in_range"]
    assert any("Re" in warning for warning in result["warnings"])
    ok = transport_correlation("Pipe, turbulent (Dittus-Boelter)", 5e4, 7.0)
    assert ok["in_range"] and ok["warnings"] == []


def test_analogy_ratio_is_lewis_to_the_correlation_exponent():
    """Sh/Nu = (Sc/Pr)^n whenever the correlation is a pure power law."""
    pair = analogy_pair("Flat plate, laminar (local)", 1e4, prandtl=7.0, schmidt=700.0)
    assert not pair["offset_breaks_pure_power_law"]
    assert pair["ratio"] == pytest.approx(pair["ratio_from_lewis"], rel=1e-9)
    assert pair["ratio_from_lewis"] == pytest.approx(100.0 ** (1 / 3), rel=1e-9)


def test_conduction_floor_breaks_the_pure_power_law_ratio():
    pair = analogy_pair("Sphere (Ranz-Marshall)", 100.0, prandtl=7.0, schmidt=700.0)
    assert pair["offset_breaks_pure_power_law"]
    assert math.isnan(pair["ratio_from_lewis"])
    assert pair["ratio"] > 1.0


def test_chilton_colburn_relates_j_to_fanning_over_two():
    result = chilton_colburn(reynolds=1e5, prandtl=7.0, nusselt=500.0,
                             friction_factor_fanning=0.0045)
    assert result["stanton"] == pytest.approx(500.0 / (1e5 * 7.0))
    assert result["j_h"] == pytest.approx(result["stanton"] * 7.0 ** (2 / 3))
    assert result["j_from_friction"] == pytest.approx(0.0045 / 2.0)
    assert result["friction_factor_darcy"] == pytest.approx(0.0045 * 4.0)


def test_sweep_stays_inside_the_declared_range():
    curve = sweep_reynolds("Sphere (Ranz-Marshall)", 7.0)
    low, high = CORRELATIONS["Sphere (Ranz-Marshall)"]["re_range"]
    assert curve["reynolds"][0] == pytest.approx(low)
    assert curve["reynolds"][-1] == pytest.approx(high)
    assert all(b >= a for a, b in zip(curve["values"], curve["values"][1:]))


@pytest.mark.parametrize("geometry", sorted(CORRELATIONS))
def test_every_correlation_is_documented_and_evaluable(geometry):
    spec = CORRELATIONS[geometry]
    for key in ("length_scale", "source", "note", "re_range", "pr_range"):
        assert spec[key], f"{geometry} is missing {key}"
    mid_re = math.sqrt(max(spec["re_range"][0], 1e-3) * spec["re_range"][1])
    mid_pr = math.sqrt(spec["pr_range"][0] * spec["pr_range"][1])
    result = transport_correlation(geometry, mid_re, mid_pr)
    assert result["value"] > 0


@pytest.mark.parametrize("kwargs", [
    dict(geometry="Nonexistent", reynolds=1e4, property_number=1.0),
    dict(geometry="Sphere (Ranz-Marshall)", reynolds=0.0, property_number=1.0),
    dict(geometry="Sphere (Ranz-Marshall)", reynolds=1e4, property_number=-1.0),
])
def test_invalid_inputs_rejected(kwargs):
    with pytest.raises(ValueError):
        transport_correlation(**kwargs)


def test_invalid_mode_rejected():
    with pytest.raises(ValueError):
        transport_correlation("Sphere (Ranz-Marshall)", 100.0, 1.0, mode="charge")
