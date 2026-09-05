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
