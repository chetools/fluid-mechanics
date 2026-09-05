"""Unit tests for 2D Lid-Driven Cavity CFD solver."""

import numpy as np
import pytest
from src.physics.numerical_solver import run_lid_driven_cavity, suggested_timestep

def test_lid_driven_cavity_solver():
    """Verify 2D Chorin Projection solver executes cleanly and respects boundary conditions."""
    res = run_lid_driven_cavity(
        reynolds=100.0,
        nx=25,
        ny=25,
        u_lid=1.0,
        n_steps=40,
        dt=0.001,
        poisson_iters=25,
    )
    
    # Boundary conditions check:
    # Top lid horizontal velocity is u_lid (interior moving lid)
    assert np.allclose(res["u"][-1, 1:-1], 1.0)
    # Bottom wall is zero
    assert np.allclose(res["u"][0, :], 0.0)
    # Side walls are zero
    assert np.allclose(res["u"][:, 0], 0.0)
    assert np.allclose(res["u"][:, -1], 0.0)
    # Vertical velocities on all walls are zero
    assert np.allclose(res["v"][-1, :], 0.0)
    assert np.allclose(res["v"][0, :], 0.0)
    assert np.allclose(res["v"][:, 0], 0.0)
    assert np.allclose(res["v"][:, -1], 0.0)
    
    # Solver must maintain finite bounded values (no numerical blow-up)
    assert np.all(np.isfinite(res["u"]))
    assert np.all(np.isfinite(res["v"]))
    assert np.all(np.isfinite(res["p"]))
    assert np.all(np.isfinite(res["vorticity"]))
    assert np.isclose(res["t_final"], 40 * 0.001)
    assert res["ghia_applicable"] is True
    assert np.isfinite(res["ghia_rmse"])
    # 40 steps is spin-up: must not look like a converged Ghia profile.
    assert res["ghia_rmse"] > 0.05
    assert res["approaching_steady"] is False


def test_ghia_overlay_only_at_re_100():
    res = run_lid_driven_cavity(reynolds=50.0, nx=21, ny=21, n_steps=20, dt=0.001, poisson_iters=10)
    assert res["ghia_applicable"] is False
    assert np.isnan(res["ghia_rmse"])


def test_suggested_timestep_respects_viscous_limit():
    dt_re10 = suggested_timestep(10.0, nx=41)
    dt_re100 = suggested_timestep(100.0, nx=41)
    assert dt_re10 < dt_re100
    assert dt_re10 > 0.0


def test_predictor_preserves_interior_vertical_momentum(monkeypatch):
    """Capture the predictor with a pressure pulse, then no pressure correction."""
    import src.physics.numerical_solver as solver

    calls = 0

    def pressure_pulse(p, *args, **kwargs):
        nonlocal calls
        p[:] = 0.0
        if calls == 0:
            p[3, 3] = 1.0
        calls += 1
        return p

    monkeypatch.setattr(solver, "solve_pressure_poisson", pressure_pulse)
    result = solver.run_lid_driven_cavity(nx=7, ny=7, n_steps=2, dt=0.001)
    # The first pressure correction creates v; the next predictor must retain it.
    assert np.max(np.abs(result["v"][1:-1, 1:-1])) > 0.002


def test_lid_drives_flow_from_first_step():
    initial = run_lid_driven_cavity(nx=9, ny=9, n_steps=0)
    assert np.all(initial["u"][-1, 1:-1] == 1.0)
    stepped = run_lid_driven_cavity(nx=9, ny=9, n_steps=1)
    assert np.max(np.abs(stepped["u"][1:-1, 1:-1])) > 0


def test_ghia_error_is_independent_of_lid_speed_scale():
    common = dict(nx=10, ny=10, n_steps=10)
    unit = run_lid_driven_cavity(u_lid=1.0, dt=0.001, **common)
    scaled = run_lid_driven_cavity(u_lid=2.0, dt=0.0005, **common)
    assert scaled["ghia_rmse"] == pytest.approx(unit["ghia_rmse"])
    assert np.allclose(unit["u_centerline"], (unit["u"][:, 4] + unit["u"][:, 5]) / 2)
    assert np.allclose(unit["v_centerline"], (unit["v"][4, :] + unit["v"][5, :]) / 2)


@pytest.mark.parametrize("kwargs", [
    {"reynolds": 0}, {"u_lid": 0}, {"dt": float("nan")},
    {"nx": 2}, {"ny": 3.5}, {"n_steps": -1}, {"poisson_iters": 0},
])
def test_invalid_solver_parameters(kwargs):
    with pytest.raises(ValueError):
        run_lid_driven_cavity(**kwargs)


def _jacobi_reference(p, div, dx, dy, rho, dt, n):
    """The previous fixed-count Jacobi relaxation, kept as a convergence baseline."""
    p = np.array(p, dtype=float)
    p_new = p.copy()
    dx2, dy2 = dx * dx, dy * dy
    factor = 0.5 * dx2 * dy2 / (dx2 + dy2)
    rhs = (rho / dt) * div
    for _ in range(n):
        p_new[1:-1, 1:-1] = factor * (
            (p[1:-1, 2:] + p[1:-1, :-2]) / dx2
            + (p[2:, 1:-1] + p[:-2, 1:-1]) / dy2
            - rhs[1:-1, 1:-1]
        )
        p_new[:, -1] = p_new[:, -2]
        p_new[:, 0] = p_new[:, 1]
        p_new[-1, :] = p_new[-2, :]
        p_new[0, :] = p_new[1, :]
        p[:] = p_new
    return p


def _poisson_case(n=41):
    from src.physics.numerical_solver import solve_pressure_poisson  # noqa: F401
    dx = dy = 1.0 / (n - 1)
    rng = np.random.default_rng(0)
    div = np.zeros((n, n))
    div[1:-1, 1:-1] = rng.normal(0.0, 1e-3, (n - 2, n - 2))
    div[1:-1, 1:-1] -= div[1:-1, 1:-1].mean()
    return np.zeros((n, n)), div, dx, dy, 1.0, 1e-3


def test_sor_converges_and_beats_jacobi():
    from src.physics.numerical_solver import poisson_residual, solve_pressure_poisson

    p0, div, dx, dy, rho, dt = _poisson_case()
    sor = solve_pressure_poisson(p0, div, dx, dy, rho, dt, n_iterations=1000)
    jac = _jacobi_reference(p0, div, dx, dy, rho, dt, 1000)
    r_sor = poisson_residual(sor, div, dx, dy, rho, dt)
    r_jac = poisson_residual(jac, div, dx, dy, rho, dt)
    assert r_sor < 1e-8, f"SOR did not converge: residual {r_sor:.3e}"
    assert r_sor < r_jac / 1000.0, f"SOR {r_sor:.3e} is not clearly better than Jacobi {r_jac:.3e}"


def test_poisson_solve_does_not_mutate_the_caller_array():
    from src.physics.numerical_solver import solve_pressure_poisson

    p0, div, dx, dy, rho, dt = _poisson_case(n=15)
    before = p0.copy()
    solve_pressure_poisson(p0, div, dx, dy, rho, dt, n_iterations=20)
    assert np.array_equal(p0, before)


@pytest.mark.parametrize("omega", [0.0, 2.0, -1.0, 2.5])
def test_invalid_relaxation_factor(omega):
    from src.physics.numerical_solver import solve_pressure_poisson

    p0, div, dx, dy, rho, dt = _poisson_case(n=9)
    with pytest.raises(ValueError):
        solve_pressure_poisson(p0, div, dx, dy, rho, dt, n_iterations=5, omega=omega)


def test_corner_singularity_is_reported_separately():
    """max |div u| is dominated by the lid corners; the off-corner measure is not."""
    res = run_lid_driven_cavity(reynolds=100.0, nx=41, ny=41, n_steps=100, dt=1e-3, poisson_iters=40)
    assert res["max_divergence_interior"] < res["max_divergence"]
    assert res["max_divergence_interior"] < 0.5 * res["max_divergence"]


def test_poisson_residual_separates_compatibility_from_iteration_error():
    from src.physics.numerical_solver import (
        compatible_poisson_rhs, poisson_residual, solve_pressure_poisson,
    )
    p0, div, dx, dy, rho, dt = _poisson_case(n=15)
    div[1:-1, 1:-1] += 0.25
    before = div.copy()
    rhs, correction = compatible_poisson_rhs(div, rho, dt)
    assert correction == pytest.approx(250.0)
    assert rhs[1:-1, 1:-1].mean() == pytest.approx(0, abs=1e-12)
    assert poisson_residual(p0, div, dx, dy, rho, dt) > 0.1
    p = solve_pressure_poisson(p0, div, dx, dy, rho, dt, n_iterations=1000)
    assert poisson_residual(p, div, dx, dy, rho, dt) < 1e-8
    assert np.array_equal(div, before)


def test_unstarted_cavity_reports_zero_compatibility_correction():
    result = run_lid_driven_cavity(nx=9, ny=9, n_steps=0)
    assert result['poisson_residual'] == 0
    assert result['poisson_compatibility_correction'] == 0
