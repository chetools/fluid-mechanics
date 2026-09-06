"""Tests for the constitutive models of chapter 7."""

import numpy as np
import pytest

from src.physics.non_newtonian import (
    MODEL_INFO,
    buckingham_reiner_flow,
    flow_curve,
    herschel_bulkley_pipe,
    maxwell_startup,
    power_law_pipe,
    power_law_pressure_drop,
    thixotropic_step,
    timescale_numbers,
)
from src.physics.exact_solutions import hagen_poiseuille_pipe


def test_power_law_recovers_hagen_poiseuille_at_n1():
    R = 0.025
    dp = -20.0
    mu = 1.0e-3
    pl = power_law_pipe(radius=R, dp_dz=dp, K=mu, n=1.0, rho=1000.0)
    hp = hagen_poiseuille_pipe(radius=R, dp_dx=dp, mu=mu, rho=1000.0)
    assert np.isclose(pl["u_max"], hp["u_max"], rtol=1e-6)
    assert np.isclose(pl["u_avg"], hp["u_avg"], rtol=1e-6)
    assert np.isclose(pl["ratio_max_avg"], 2.0)
    assert np.isclose(pl["tau_wall"], hp["tau_wall"], rtol=1e-8)


def test_shear_thinning_is_blunter_than_newtonian():
    common = dict(radius=0.025, dp_dz=-40.0, K=0.1, rho=1000.0)
    thin = power_law_pipe(n=0.5, **common)
    newt = power_law_pipe(n=1.0, **common)
    thick = power_law_pipe(n=1.4, **common)
    assert thin["ratio_max_avg"] < newt["ratio_max_avg"] < thick["ratio_max_avg"]


def test_power_law_pressure_drop_inverts_q():
    R, L, K, n = 0.04, 20.0, 0.2, 0.7
    dp = -1500.0
    pl = power_law_pipe(radius=R, dp_dz=dp / L, K=K, n=n)
    dp_back = power_law_pressure_drop(pl["flow_rate"], R, L, K, n)
    assert np.isclose(dp_back, abs(dp), rtol=1e-5)


# --- Herschel-Bulkley pipe flow -----------------------------------------


def test_herschel_bulkley_reduces_to_hagen_poiseuille():
    """No yield stress and n = 1 must return chapter 7's parabola exactly."""
    R, dp, mu = 0.025, -40.0, 1e-3
    hb = herschel_bulkley_pipe(radius=R, dp_dz=dp, K=mu, n=1.0, tau_y=0.0)
    hp = hagen_poiseuille_pipe(radius=R, dp_dx=dp, mu=mu)
    assert hb["plug_fraction"] == 0.0
    assert np.isclose(hb["u_max"], hp["u_max"], rtol=1e-6)
    assert np.isclose(hb["flow_rate"], hp["flow_rate"], rtol=1e-4)
    assert np.isclose(hb["ratio_max_avg"], 2.0, rtol=1e-4)


def test_herschel_bulkley_reduces_to_the_power_law():
    common = dict(radius=0.025, dp_dz=-40.0, K=0.1, n=0.6)
    hb = herschel_bulkley_pipe(tau_y=0.0, **common)
    pl = power_law_pipe(**common)
    assert np.isclose(hb["u_max"], pl["u_max"], rtol=1e-6)
    assert np.isclose(hb["flow_rate"], pl["flow_rate"], rtol=1e-4)


@pytest.mark.parametrize("tau_y", [0.05, 0.2, 0.45])
def test_bingham_flow_rate_matches_buckingham_reiner(tau_y):
    """The integrated profile is checked against an independent closed form."""
    R, dp, mu_p = 0.025, -40.0, 0.02
    hb = herschel_bulkley_pipe(radius=R, dp_dz=dp, K=mu_p, n=1.0, tau_y=tau_y)
    assert np.isclose(hb["flow_rate"], buckingham_reiner_flow(R, dp, mu_p, tau_y), rtol=1e-4)


def test_plug_radius_is_where_the_stress_line_crosses_the_yield_stress():
    R, dp, tau_y = 0.025, -40.0, 0.2
    hb = herschel_bulkley_pipe(radius=R, dp_dz=dp, K=0.02, n=1.0, tau_y=tau_y)
    # tau_w = R |dp/dz| / 2, and the plug fraction is tau_y / tau_w.
    assert np.isclose(hb["tau_wall"], 0.5 * R * abs(dp))
    assert np.isclose(hb["plug_fraction"], tau_y / hb["tau_wall"])
    # Doubling the gradient halves the plug: the stress profile steepens.
    steeper = herschel_bulkley_pipe(radius=R, dp_dz=2 * dp, K=0.02, n=1.0, tau_y=tau_y)
    assert np.isclose(steeper["plug_fraction"], 0.5 * hb["plug_fraction"])


def test_the_plug_really_is_unsheared():
    hb = herschel_bulkley_pipe(radius=0.025, dp_dz=-40.0, K=0.02, n=1.0, tau_y=0.2)
    inside = hb["u"][hb["r_norm"] < hb["plug_fraction"] - 1e-3]
    assert inside.size > 5
    assert np.allclose(inside, inside[0], rtol=0, atol=1e-12)


def test_no_flow_below_the_yield_stress():
    """tau_w <= tau_y is a hard stop, not a very small flow."""
    hb = herschel_bulkley_pipe(radius=0.025, dp_dz=-10.0, K=0.02, n=1.0, tau_y=5.0)
    assert hb["flowing"] is False
    assert hb["flow_rate"] == 0.0
    assert hb["plug_fraction"] == 1.0
    assert buckingham_reiner_flow(0.025, -10.0, 0.02, 5.0) == 0.0


def test_wall_shear_ignores_the_constitutive_law():
    """The momentum balance is material-independent; only kinematics change."""
    common = dict(radius=0.025, dp_dz=-40.0)
    stresses = {
        herschel_bulkley_pipe(K=K, n=n, tau_y=t, **common)["tau_wall"]
        for K, n, t in [(1e-3, 1.0, 0.0), (0.5, 0.4, 0.0), (0.02, 1.0, 0.2), (2.0, 1.6, 0.1)]
    }
    assert len(stresses) == 1


# --- flow curves ---------------------------------------------------------


def test_flow_curve_covers_every_documented_model():
    """MODEL_INFO is the gallery the chapter renders; each entry must evaluate."""
    g = np.logspace(-2, 3, 40)
    defaults = {
        "mu": 0.05, "K": 2.0, "n": 0.5, "tau_y": 5.0, "mu_p": 0.05, "mu_c": 0.05,
        "mu_0": 10.0, "mu_inf": 0.01, "lam": 1.0, "a": 2.0,
    }
    for model, info in MODEL_INFO.items():
        params = {name: defaults[name] for name in info["params"]}
        curve = flow_curve(model, g, **params)
        assert np.all(np.isfinite(curve["tau"]))
        assert np.all(curve["tau"] > 0)
        assert np.allclose(curve["mu_app"], curve["tau"] / g)


def test_newtonian_is_the_only_flat_apparent_viscosity():
    g = np.logspace(-2, 3, 60)
    newt = flow_curve("Newtonian", g, mu=0.05)["mu_app"]
    thin = flow_curve("Power law (Ostwald-de Waele)", g, K=2.0, n=0.5)["mu_app"]
    thick = flow_curve("Power law (Ostwald-de Waele)", g, K=2.0, n=1.5)["mu_app"]
    assert np.allclose(newt, newt[0])
    assert thin[-1] < thin[0]
    assert thick[-1] > thick[0]


def test_yield_stress_apparent_viscosity_diverges_at_low_shear():
    g = np.logspace(-4, 3, 80)
    mu_app = flow_curve("Bingham plastic", g, tau_y=5.0, mu_p=0.05)["mu_app"]
    assert mu_app[0] > 1e4 * mu_app[-1]


def test_carreau_has_both_newtonian_plateaux():
    """The point of the model: it stops being a power law at both ends.

    The high-shear plateau is approached slowly — the excess over mu_inf decays
    as gamma_dot^(n-1), so reaching it needs several more decades than the
    low-shear one, which is why the sweep runs to 1e9 rather than 1e5.
    """
    g = np.logspace(-4, 9, 400)
    curve = flow_curve("Carreau-Yasuda", g, mu_0=10.0, mu_inf=0.01, lam=1.0, n=0.4, a=2.0)
    assert np.isclose(curve["mu_app"][0], 10.0, rtol=1e-3)
    assert np.isclose(curve["mu_app"][-1], 0.01, rtol=1e-2)
    # Monotone, and bracketed by the two plateaux everywhere in between.
    assert np.all(np.diff(curve["mu_app"]) < 0)
    assert np.all((curve["mu_app"] > 0.01) & (curve["mu_app"] <= 10.0))


def test_unknown_model_is_refused_rather_than_guessed():
    with pytest.raises(ValueError):
        flow_curve("Bird-Carreau-ish", np.array([1.0]), mu=1.0)


# --- time-dependent behaviour -------------------------------------------


def test_thixotropic_structure_breaks_faster_than_it_rebuilds():
    res = thixotropic_step(gamma_hi=50.0, gamma_lo=1.0, k_build=0.25, k_break=0.05)
    assert res["tau_build_low"] > res["tau_build_high"]
    assert res["lam_eq_high"] < res["lam_eq_low"]
    # The structure decays toward its high-shear equilibrium, then recovers.
    hold = res["t"] <= res["t_hold"]
    assert res["structure"][hold][-1] < res["structure"][0]
    assert res["structure"][-1] > res["structure"][hold][-1]


def test_thixotropy_makes_the_same_shear_rate_give_two_stresses():
    """The signature of a history-dependent fluid, stated as a test."""
    res = thixotropic_step(gamma_hi=80.0, gamma_lo=1.0, t_hold=20.0)
    after = res["t"] > res["t_hold"]
    tau_immediately_after = res["tau"][after][0]
    tau_before = res["mu_app"][0] * res["gamma_dot"][after][0]
    assert tau_immediately_after < tau_before


def test_maxwell_startup_approaches_the_viscous_stress():
    res = maxwell_startup(gamma_dot=10.0, relax_time=0.5, mu=5.0, t_end=5.0)
    assert res["tau"][0] == 0.0
    assert np.isclose(res["tau"][-1], res["tau_steady"], rtol=1e-3)
    # One relaxation time reaches 1 - 1/e of the steady value.
    at_lambda = np.interp(res["relax_time"], res["t"], res["tau"])
    assert np.isclose(at_lambda / res["tau_steady"], 1 - np.exp(-1.0), rtol=1e-3)


def test_normal_stress_is_quadratic_in_shear_rate():
    slow = maxwell_startup(gamma_dot=5.0, relax_time=0.5, mu=5.0)
    fast = maxwell_startup(gamma_dot=10.0, relax_time=0.5, mu=5.0)
    assert np.isclose(fast["n1_steady"] / slow["n1_steady"], 4.0)
    assert np.isclose(fast["n1_over_tau"], 2.0 * fast["weissenberg"])


def test_weissenberg_and_deborah_are_independent():
    """Same Wi, different De: the two numbers ask different questions."""
    slow_process = timescale_numbers(relax_time=0.5, gamma_dot=10.0, flow_time=100.0)
    fast_process = timescale_numbers(relax_time=0.5, gamma_dot=10.0, flow_time=0.1)
    assert slow_process["weissenberg"] == fast_process["weissenberg"] == 5.0
    assert slow_process["deborah"] < 1.0 < fast_process["deborah"]
    assert "liquid-like" in slow_process["regime"]
    assert "solid-like" in fast_process["regime"]
