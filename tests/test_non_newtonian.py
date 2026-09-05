"""Tests for Ostwald–de Waele pipe flow."""

import numpy as np

from src.physics.non_newtonian import power_law_pipe, power_law_pressure_drop
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
