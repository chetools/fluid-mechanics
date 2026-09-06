"""UI module for Panel 7: Numerical solution of Navier–Stokes (projection CFD)."""

import streamlit as st
from src.ui.state import persistent_input
from src.ui.pedagogy import render_plot
import numpy as np

from src.svg_diagrams import diagram_chorin_projection, render_svg
from src.physics.numerical_solver import run_lid_driven_cavity, suggested_timestep
from src.plotting import plot_cavity_cfd
from src.ui.pedagogy import (
    render_derivation,
    render_objectives,
    render_what_to_notice,
    render_self_check,
    render_callout,
    render_prose_and_latex,
)


@st.cache_data(show_spinner="Running 2D incompressible Navier–Stokes (transient)...")
def _cached_cavity_simulation(reynolds: float, nx: int, n_steps: int, dt: float, poisson_iters: int):
    return run_lid_driven_cavity(
        reynolds=reynolds, nx=nx, ny=nx, n_steps=n_steps, dt=dt, poisson_iters=poisson_iters
    )


def render_tab_cfd():
    """Chorin's projection method and a lid-driven cavity demo."""
    st.markdown(
        """
        Tabs 2, 4 and 7 gave pipe design, regimes, and exact solutions. When geometry is
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

    st.markdown("### 13.1 The Two Fundamental Mathematical Roadblocks")
    col_rb1, col_rb2 = st.columns(2)
    with col_rb1:
        render_callout(
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
        render_callout(
            """
            **2. The Pressure-Velocity Coupling Dilemma**

            In compressible gas dynamics, pressure satisfies an equation of state $p = \\rho R T$. In **incompressible flow** ($\\rho = \\text{const}$), continuity is purely kinematic: $\\nabla \\cdot \\mathbf{u} = 0$.
            - There is **no time derivative $\\partial p/\\partial t$** in the continuity equation!
            - Pressure acts as an instantaneous **Lagrange multiplier** across the entire field to enforce incompressibility.
            - This converts Navier-Stokes into a mixed **hyperbolic/parabolic-elliptic system**.
            """
        )

    st.markdown("---")
    st.markdown("### 13.2 Chorin's Projection (Fractional Step) Method")
    st.markdown(
        """
        In 1968 Alexandre Chorin invented the **Projection Method**, still the
        backbone of incompressible CFD: advance momentum without pressure, then
        project onto a divergence-free field by solving a Poisson equation.
        """
    )
    render_svg(diagram_chorin_projection())

    with st.expander("🔍 Detailed Algorithmic Derivation: The 3 Steps of Chorin's Projection"):
        render_prose_and_latex(
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
            This is an **elliptic Poisson equation** solved across the grid using iterative relaxation. This app uses **red-black
            successive over-relaxation**: Jacobi needs $O(N^2)$ sweeps to relax the longest wavelength on an
            $N\times N$ grid, while SOR with $\omega\to 2$ needs $O(N)$. The red-black colouring keeps each
            half-sweep a single vectorized array expression while still reading updated neighbours.

            **Step 3: Velocity Correction (Projection)**
            Once pressure $p^{n+1}$ is found, project the intermediate field back onto the divergence-free subspace:
            $$\mathbf{u}^{n+1} = \mathbf{u}^* - \frac{\Delta t}{\rho} \nabla p^{n+1}$$
            """
        )

    render_derivation(
        r"the finite differences, and the two limits that set $\Delta t$",
        [
            (
                "A derivative becomes a difference by Taylor series, and the error is visible",
                r"""
                Expand the neighbours of a grid point in both directions:
                $$u_{i\pm1}=u_i\pm\Delta x\,u'_i+\frac{\Delta x^{2}}{2}u''_i
                \pm\frac{\Delta x^{3}}{6}u'''_i+\dots$$
                **Subtract** them and the even-order terms cancel:
                $$\frac{u_{i+1}-u_{i-1}}{2\Delta x}=u'_i+\frac{\Delta x^{2}}{6}u'''_i+\dots$$
                so a centred first difference is second-order accurate. **Add** them and the
                odd terms cancel:
                $$\frac{u_{i+1}-2u_i+u_{i-1}}{\Delta x^{2}}=u''_i+\frac{\Delta x^{2}}{12}u''''_i+\dots$$
                Those two stencils are the whole spatial discretisation of this solver. Halving
                $\Delta x$ should therefore quarter the truncation error — which is the test to
                run when the grid selector is changed.
                """,
            ),
            (
                "Limit 1 — advection may not outrun the stencil",
                r"""
                The explicit update at node $i$ can only see its immediate neighbours, so in
                one step information can travel at most one cell. Fluid carries information at
                speed $u$, hence
                $$\mathrm{CFL}=\frac{u\,\Delta t}{\Delta x}\le C
                \;\Longrightarrow\;\Delta t\le C\frac{\Delta x}{u}$$
                Violate it and the scheme is asked to reconstruct fluid that came from outside
                its own stencil; it produces oscillations that double each step. This solver
                uses $C=0.25$, well inside the limit, and reports the resulting CFL as a metric
                below.
                """,
            ),
            (
                "Limit 2 — explicit diffusion has its own, harsher, ceiling",
                r"""
                Von Neumann analysis of $\partial u/\partial t=\nu\nabla^{2}u$ with these
                stencils gives, in two dimensions,
                $$\Delta t\le\frac{\Delta x^{2}}{4\nu}$$
                Read it physically: $\Delta x^{2}/\nu$ is the time viscosity needs to diffuse
                across one cell, and an explicit step may not outrun the process it models.
                The **square** is what hurts — halving the grid spacing costs four times as
                many steps — and it is why implicit treatments of the viscous term exist. At
                low $\mathrm{Re}$ this limit binds; at high $\mathrm{Re}$ the CFL one does.
                The app takes the smaller of the two, with a safety factor.
                """,
            ),
            (
                "The consequence you can see in the metrics",
                r"""
                Both limits shrink $\Delta t$ as the grid refines, while the physical time
                needed to reach steady state does **not** shrink. That is why the panel warns
                that a few hundred steps reach $t^{*}=tU/L\ll\mathrm{Re}$: the run is limited
                by stability, not by physics, and comparing it with a steady benchmark is a
                category error.
                """,
            ),
        ],
    )

    render_derivation(
        r"why the Poisson source must have its mean removed",
        [
            (
                "Integrate the pressure equation over the whole cavity",
                r"""
                The projection step requires $\nabla^{2}p=(\rho/\Delta t)\nabla\cdot\mathbf u^{*}$
                on a box whose walls are all impermeable. Integrate both sides over the domain
                and apply the divergence theorem to the left:
                $$\int_V\nabla^{2}p\,dV=\oint_S\nabla p\cdot\mathbf n\,dS$$
                """,
            ),
            (
                "The boundary condition forces that surface integral to vanish",
                r"""
                At an impermeable wall the projection may not move fluid through the boundary,
                which requires $\partial p/\partial n=0$ — the homogeneous Neumann condition
                the solver imposes. Hence the whole surface integral is zero, and therefore
                $$\int_V\frac{\rho}{\Delta t}\nabla\cdot\mathbf u^{*}\,dV=0$$
                **must** hold or the equation has no solution at all. This is the compatibility
                (solvability) condition: with pure Neumann data you may specify the *fluxes*
                or the *source*, but not both independently.
                """,
            ),
            (
                "Discretely it is violated, by a small amount, every step",
                r"""
                The predictor $\mathbf u^{*}$ is built from finite differences and boundary
                values that do not conserve mass exactly, so the discrete sum of
                $\nabla\cdot\mathbf u^{*}$ is close to zero but not equal to it. Asking the
                relaxation to solve an incompatible system makes the mean of $p$ drift without
                bound while the residual stalls. The fix is to subtract the mean before
                solving:
                $$\text{rhs}\;\leftarrow\;\text{rhs}-\overline{\text{rhs}}$$
                which projects the source onto the space where a solution exists.
                """,
            ),
            (
                "Report the correction separately, because it means something different",
                r"""
                The metric labelled *source mean removed* is exactly $\overline{\text{rhs}}$,
                and the *Poisson residual* is the error against the compatible source that was
                actually solved. Adding them together would hide the distinction: one measures
                **how far the predictor is from conserving mass**, the other **how well the
                relaxation converged**. A small residual with a large correction means the
                solver worked perfectly on a slightly wrong problem.
                """,
            ),
            (
                "One more consequence: pressure is only defined up to a constant",
                r"""
                With Neumann conditions everywhere, if $p$ solves the problem then so does
                $p+\text{const}$ — nothing pins the level. The solver subtracts the mean at the
                end so the reported field does not wander between runs. This changes no
                velocity whatsoever, because only $\nabla p$ enters the correction step.
                """,
            ),
        ],
    )

    st.markdown("---")
    st.markdown("### 13.3 Live 2D CFD: Lid-Driven Cavity (transient demo)")
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
        re_slider = persistent_input(st.select_slider,
            "Reynolds Number Re = U·L/ν",
            options=[10.0, 50.0, 100.0, 200.0, 400.0],
            value=100.0, key="tab_cfd_reynolds_number_re_u_l")
    with col_sim2:
        grid_res = persistent_input(st.selectbox, "Grid Resolution", options=["31 x 31 (Fast)", "41 x 41 (Standard)"], index=1, key="tab_cfd_grid_resolution")
        nx_val = 31 if "31" in grid_res else 41
    with col_sim3:
        effort = persistent_input(st.selectbox,
            "Integration effort",
            options=["Quick look (t* ≈ 0.5)", "Longer run (t* ≈ 4)"],
            help="t* = t U/L. Viscous time is Re. Steady Ghia data need t* of order 10+, not 0.5.", key="tab_cfd_integration_effort")

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
    col_sc2.metric(
        "max |∇·u| (off-corner)",
        f"{res_cavity['max_divergence_interior']:.2e}",
        help=(
            "Largest divergence away from the two lid corners. The global maximum, "
            f"{res_cavity['max_divergence']:.2e}, sits at a corner where the lid velocity "
            "jumps from u_lid to 0 across one cell — a singularity of the problem "
            "statement, not a failure of the projection."
        ),
    )
    col_sc3.metric("t* = t U/L", f"{res_cavity['t_final']:.2f}")
    col_sc4.metric("CFL", f"{res_cavity['cfl']:.3f}")

    st.caption(
        f"Δt = {dt_auto:.2e} (CFL and viscous limits) · {n_steps_val} steps · "
        f"Poisson residual {res_cavity['poisson_residual']:.2e} Pa/m² after {poisson_iters} red-black SOR sweeps · "
        f"source mean removed {res_cavity['poisson_compatibility_correction']:+.2e} Pa/m² · "
        f"viscous time L²/ν = {res_cavity['t_viscous']:.1f}. "
        "This 2D run cannot show vortex stretching."
    )
    with st.expander("How to judge this result"):
        st.markdown(
            "1. **Boundary conditions:** the top wall moves; the other walls are stationary and impermeable.\n"
            "2. **Mass conservation:** inspect max |∇·u|. The discrete projection reduces divergence, "
            "but this collocated teaching solver does not enforce it exactly.\n"
            "3. **Pressure solve:** the reported residual measures the equation after subtracting "
            "the source mean to make it compatible with impermeable walls. The separately reported "
            "mean removed measures that adjustment, not iteration error. A small residual alone "
            "does not establish mass conservation or velocity accuracy.\n"
            "4. **Time and grid:** compare integration times and grid sizes separately. "
            "A steady-looking picture can still contain spatial discretization error.\n"
            "5. **Reference:** compare with Ghia only at the same Reynolds number and after spin-up. "
            "The present runs illustrate the algorithm; they are not a converged benchmark validation."
        )

    if res_cavity["ghia_applicable"]:
        if res_cavity["approaching_steady"]:
            st.success(
                f"Re = 100 and t* = {res_cavity['t_final']:.2f}. "
                f"Centerline RMSE vs Ghia et al. (1982) = {res_cavity['ghia_rmse']:.3f}. "
                "A coarse explicit projection code will not match the paper to plotting accuracy."
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
    render_plot(fig_cavity, key="tab_cfd-fig_cavity")

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
