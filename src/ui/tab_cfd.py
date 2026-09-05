"""UI module for Panel 7: Numerical solution of Navier–Stokes (projection CFD)."""

import streamlit as st
import numpy as np

from src.svg_diagrams import diagram_chorin_projection, render_svg
from src.physics.numerical_solver import run_lid_driven_cavity, suggested_timestep
from src.plotting import plot_cavity_cfd
from src.ui.pedagogy import (
    render_objectives,
    render_what_to_notice,
    render_self_check,
)


@st.cache_data(show_spinner="Running 2D incompressible Navier–Stokes (transient)...")
def _cached_cavity_simulation(reynolds: float, nx: int, n_steps: int, dt: float, poisson_iters: int):
    return run_lid_driven_cavity(
        reynolds=reynolds, nx=nx, ny=nx, n_steps=n_steps, dt=dt, poisson_iters=poisson_iters
    )


def render_tab_cfd():
    """Chorin's projection method and a lid-driven cavity demo."""
    st.markdown("## 7. Numerical CFD: Chorin's Projection & the Lid-Driven Cavity")
    st.markdown(
        """
        Tabs 4–6 gave exact solutions, regimes, and pipe design. When geometry is
        not a straight duct, $(\\mathbf{u}\\cdot\\nabla)\\mathbf{u}$ cannot be dropped and
        pressure has no equation of state — that is the CFD problem.
        """
    )
    render_objectives(
        [
            "Name the two reasons incompressible NS is hard: nonlinear advection, and elliptic pressure.",
            "Write the three steps of Chorin's projection (predictor, Poisson, corrector).",
            "Treat the cavity run as a **short-time** demo, not a Ghia validation unless Re = 100 *and* $t^*$ is large.",
        ]
    )

    st.markdown("### 7.1 The Two Fundamental Mathematical Roadblocks")
    col_rb1, col_rb2 = st.columns(2)
    with col_rb1:
        st.info(
            """
            **1. The Non-Linear Convective Term $(\\mathbf{u}\\cdot\\nabla)\\mathbf{u}$**

            Velocity advects itself, so momentum is intrinsically **non-linear**. This yields:
            - **Chaos / turbulence** in 3D at high Re (extreme sensitivity to initial data).
            - **Vortex stretching** $\\boldsymbol{\\omega}\\cdot\\nabla\\mathbf{u}$ — a *three-dimensional* mechanism.
              The lid-driven cavity below is **2D**: vorticity is only $\\omega_z$, and it cannot stretch.
            - **Clay Millennium Prize:** existence and smoothness of 3D Navier–Stokes remains open.
            """
        )
    with col_rb2:
        st.info(
            """
            **2. The Pressure-Velocity Coupling Dilemma**

            In compressible gas dynamics, pressure satisfies an equation of state $p = \\rho R T$. In **incompressible flow** ($\\rho = \\text{const}$), continuity is purely kinematic: $\\nabla \\cdot \\mathbf{u} = 0$.
            - There is **no time derivative $\\partial p/\\partial t$** in the continuity equation!
            - Pressure acts as an instantaneous **Lagrange multiplier** across the entire field to enforce incompressibility.
            - This converts Navier-Stokes into a mixed **hyperbolic/parabolic-elliptic system**.
            """
        )

    st.markdown("---")
    st.markdown("### 7.2 Chorin's Projection (Fractional Step) Method")
    st.markdown(
        """
        In 1968 Alexandre Chorin invented the **Projection Method**, still the
        backbone of incompressible CFD: advance momentum without pressure, then
        project onto a divergence-free field by solving a Poisson equation.
        """
    )
    render_svg(diagram_chorin_projection())

    with st.expander("🔍 Detailed Algorithmic Derivation: The 3 Steps of Chorin's Projection"):
        st.markdown(
            r"""
            **The Helmholtz–Hodge Decomposition:**
            Any vector field $\mathbf{w}$ can be uniquely decomposed into a divergence-free (solenoidal) component $\mathbf{u}$
            and the gradient of a scalar potential $\nabla \phi$:
            $$\mathbf{w} = \mathbf{u} + \nabla \phi, \quad \text{with } \nabla \cdot \mathbf{u} = 0$$

            **Step 1: Intermediate Velocity Predictor ($\mathbf{u}^*$)**
            Advance momentum explicitly using advection and viscous diffusion, omitting the pressure gradient entirely:
            $$\frac{\mathbf{u}^* - \mathbf{u}^n}{\Delta t} = -(\mathbf{u}^n \cdot \nabla)\mathbf{u}^n + \nu \nabla^2 \mathbf{u}^n$$
            Because pressure was omitted, $\mathbf{u}^*$ does **not** satisfy mass conservation ($\nabla \cdot \mathbf{u}^* \neq 0$).

            **Step 2: Pressure Poisson Equation**
            We postulate that the true velocity $\mathbf{u}^{n+1}$ is obtained by subtracting the pressure gradient from $\mathbf{u}^*$:
            $$\mathbf{u}^{n+1} = \mathbf{u}^* - \frac{\Delta t}{\rho} \nabla p^{n+1}$$
            Taking the divergence of both sides:
            $$\nabla \cdot \mathbf{u}^{n+1} = \nabla \cdot \mathbf{u}^* - \frac{\Delta t}{\rho} \nabla^2 p^{n+1}$$
            Demanding exact incompressibility for the next time level ($\nabla \cdot \mathbf{u}^{n+1} = 0$):
            $$\nabla^2 p^{n+1} = \frac{\rho}{\Delta t} \nabla \cdot \mathbf{u}^*$$
            This is an **elliptic Poisson equation** solved across the grid using iterative relaxation (Jacobi / Gauss–Seidel / Multigrid).

            **Step 3: Velocity Correction (Projection)**
            Once pressure $p^{n+1}$ is found, project the intermediate field back onto the divergence-free subspace:
            $$\mathbf{u}^{n+1} = \mathbf{u}^* - \frac{\Delta t}{\rho} \nabla p^{n+1}$$
            """
        )

    st.markdown("---")
    st.markdown("### 7.3 Live 2D CFD: Lid-Driven Cavity (transient demo)")
    st.markdown(
        """
        A unit square has three no-slip walls and a lid at $u = 1$. This is the canonical
        incompressible-CFD test of Ghia, Ghia & Shin (1982) — **but only at Re = 100, and only
        after the field is steady**. A few hundred explicit steps at $\\Delta t \\sim 10^{-3}$
        reach $t^* = t U/L \\ll \\mathrm{Re}$; you are watching spin-up, not the paper.
        """
    )

    col_sim1, col_sim2, col_sim3 = st.columns(3)
    with col_sim1:
        re_slider = st.select_slider(
            "Reynolds Number Re = U·L/ν",
            options=[10.0, 50.0, 100.0, 200.0, 400.0],
            value=100.0,
        )
    with col_sim2:
        grid_res = st.selectbox("Grid Resolution", options=["31 x 31 (Fast)", "41 x 41 (Standard)"], index=1)
        nx_val = 31 if "31" in grid_res else 41
    with col_sim3:
        effort = st.selectbox(
            "Integration effort",
            options=["Quick look (t* ≈ 0.5)", "Longer run (t* ≈ 4)"],
            help="t* = t U/L. Viscous time is Re. Steady Ghia data need t* of order 10+, not 0.5.",
        )

    dt_auto = suggested_timestep(re_slider, nx_val)
    t_target = 0.5 if "Quick" in effort else 4.0
    n_steps_val = max(int(round(t_target / dt_auto)), 40)
    poisson_iters = 40

    res_cavity = _cached_cavity_simulation(
        reynolds=re_slider,
        nx=nx_val,
        n_steps=n_steps_val,
        dt=dt_auto,
        poisson_iters=poisson_iters,
    )

    col_sc1, col_sc2, col_sc3, col_sc4 = st.columns(4)
    col_sc1.metric("Max |u|", f"{np.max(res_cavity['v_mag']):.3f}")
    col_sc2.metric("max |∇·u|", f"{res_cavity['max_divergence']:.2e}")
    col_sc3.metric("t* = t U/L", f"{res_cavity['t_final']:.2f}")
    col_sc4.metric("CFL", f"{res_cavity['cfl']:.3f}")

    st.caption(
        f"Δt = {dt_auto:.2e} (CFL and viscous limits) · {n_steps_val} steps · "
        f"Poisson residual {res_cavity['poisson_residual']:.2e} after {poisson_iters} Jacobi sweeps · "
        f"viscous time L²/ν = {res_cavity['t_viscous']:.1f}. "
        "This 2D run cannot show vortex stretching."
    )

    if res_cavity["ghia_applicable"]:
        if res_cavity["approaching_steady"]:
            st.success(
                f"Re = 100 and t* = {res_cavity['t_final']:.2f}. "
                f"Centerline RMSE vs Ghia et al. (1982) = {res_cavity['ghia_rmse']:.3f}. "
                "A coarse explicit Jacobi code will not match the paper to plotting accuracy."
            )
        else:
            st.warning(
                f"Ghia et al. (1982) Re = 100 overlay is shown for orientation only. "
                f"This run is still spinning up (t* = {res_cavity['t_final']:.2f}, "
                f"RMSE = {res_cavity['ghia_rmse']:.3f}). It is **not** a benchmark match."
            )
    else:
        st.info(
            f"Ghia overlay is hidden: tabulated data in this app are Re = 100 only, "
            f"and you set Re = {re_slider:.0f}."
        )

    render_what_to_notice(
        "Primary vortex should start to fill the box. Corner eddies appear later. "
        "If the Ghia points sit far from the curve, believe t* and the residual, not a 'match' label."
    )
    fig_cavity = plot_cavity_cfd(res_cavity)
    st.plotly_chart(fig_cavity, width="stretch")

    render_self_check(
        "cfd_self_check_time",
        "Why is a 250-step lid-driven cavity at Δt = 0.001 not a Ghia (1982) validation?",
        [
            "Because Ghia used a different lid speed",
            "Because t* = 0.25 is far below the time to reach the steady field they tabulated",
            "Because the projection method cannot compute drag",
        ],
        "Because t* = 0.25 is far below the time to reach the steady field they tabulated",
        "Ghia reported steady Re = 100 (and other Re) solutions. Short explicit runs are spin-up movies.",
    )
