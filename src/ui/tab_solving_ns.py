"""UI module for Panel 4: Exact NS solutions and laminar boundary layers."""

import streamlit as st

from src.svg_diagrams import diagram_blasius_plate, render_svg
from src.physics.exact_solutions import (
    couette_poiseuille_channel,
    hagen_poiseuille_pipe,
    stokes_first_problem,
)
from src.physics.boundary_layer import blasius_similarity_profile, blasius_plate, cylinder_outer_flow_and_separation
from src.plotting import (
    plot_exact_channel_flow,
    plot_stokes_first_problem,
    plot_hagen_poiseuille,
    plot_blasius_profile,
    plot_cylinder_separation,
)
from src.units import format_quantity, get_fluid_state
from src.ui.pedagogy import (
    render_objectives,
    render_what_to_notice,
    render_predict,
    render_self_check,
)


def render_tab_solving_ns():
    """Exact solutions plus Blasius / cylinder separation."""
    fluid = get_fluid_state()
    st.markdown("## 7. Exact Solutions & Laminar Boundary Layers")
    st.markdown(
        """
        Except for a handful of highly symmetric cases, **no general closed-form
        Navier–Stokes solution exists**. Here the convective term vanishes or is
        absorbed into a similarity variable. The Blasius plate is the payoff of
        d'Alembert's paradox from Tab 5: viscosity lives in a thin layer, and
        an adverse outer gradient separates it. Projection CFD is Tab 8.
        """
    )
    render_objectives(
        [
            "Recover Couette–Poiseuille and Hagen–Poiseuille by dropping $(\\mathbf{u}\\cdot\\nabla)\\mathbf{u}$.",
            "Watch viscous momentum diffuse as $\\delta \\sim \\sqrt{\\nu t}$.",
            "State $\\delta/x \\approx 4.91/\\sqrt{\\mathrm{Re}_x}$ and $c_f = 0.664/\\sqrt{\\mathrm{Re}_x}$.",
            "Mark where the cylinder outer flow becomes adverse (90°) and where a laminar BL separates (~105°).",
        ]
    )

    st.markdown("### 7.1 Exact Analytical Solutions (When Non-Linearity Vanishes)")
    st.markdown(
        """
        When flow geometry forces streamlines to be straight and parallel ($v = w = 0$),
        the non-linear term vanishes identically: $(\\mathbf{u}\\cdot\\nabla)\\mathbf{u} = u \\frac{\\partial u}{\\partial x} = 0$.
        The partial differential equation simplifies to an ordinary differential equation.
        Viscosity $\\mu$ and density $\\rho$ come from the **sidebar fluid**.
        """
    )

    exact_tab1, exact_tab2, exact_tab3 = st.tabs([
        "📏 1. Couette–Poiseuille Channel",
        "🔵 2. Hagen–Poiseuille Pipe",
        "⏱️ 3. Stokes' First Problem (Rayleigh diffusion)",
    ])

    with exact_tab1:
        st.markdown(
            """
            Superposition of **shear-driven Couette flow** (top plate at $U_{wall}$)
            and **pressure-driven Poiseuille flow** ($dp/dx$).
            Bottom-wall reversal when the nondimensional pressure parameter
            $P = h^2(-dp/dx)/(2\\mu U_{wall}) < -1$.
            """
        )
        render_predict(
            "couette_predict",
            "If you drive a strong *adverse* pressure gradient (dp/dx > 0) against a moving lid, near y = 0 the velocity will…",
            ["stay positive", "reverse (u < 0)", "become turbulent automatically"],
            "reverse (u < 0)",
            "The parabola leans backward. When P < −1 the bottom-wall shear changes sign and a reversed layer appears.",
        )
        col_cp1, col_cp2, col_cp3 = st.columns(3)
        with col_cp1:
            u_wall = st.slider("Top Wall Velocity U_wall [m/s]", min_value=0.0, max_value=3.0, value=1.0, step=0.2)
        with col_cp2:
            dp_dx = st.slider("Pressure Gradient dp/dx [Pa/m]", min_value=-50.0, max_value=20.0, value=-15.0, step=5.0)
        with col_cp3:
            ch_height = st.slider("Channel Height h [m]", min_value=0.01, max_value=0.1, value=0.05, step=0.01)

        res_cp = couette_poiseuille_channel(
            h=ch_height,
            u_wall=u_wall,
            dp_dx=dp_dx,
            mu=float(fluid["mu"]),
            rho=float(fluid["rho"]),
        )

        col_cpm1, col_cpm2, col_cpm3 = st.columns(3)
        col_cpm1.metric("Flow Rate Q", format_quantity(float(res_cp["q_flow"]), "flow_rate"))
        col_cpm2.metric("Mean Velocity", format_quantity(float(res_cp["u_mean"]), "velocity"))
        col_cpm3.metric("Bottom Wall Shear τ₀", format_quantity(float(res_cp["tau_wall_bottom"]), "shear_stress"))

        if res_cp["p_param"] < -1.0:
            st.info(
                "Adverse pressure gradient is strong enough for near-wall reversal "
                f"(P = {res_cp['p_param']:.2f} < −1). Look for u = 0 inside the gap."
            )
        st.caption(
            f"μ = {fluid['mu']:.3e} Pa·s from **{fluid['name']}**. "
            "Plane-channel kinetic-energy factor is α = 54/35 ≈ 1.54, not the pipe value 2."
        )
        render_what_to_notice("Green = total u(y). Dashed = linear Couette. Dotted = parabolic Poiseuille.")
        fig_cp = plot_exact_channel_flow(res_cp)
        st.plotly_chart(fig_cp, width="stretch")

        with st.expander("🔍 Step-by-Step Derivation of Couette-Poiseuille Flow", expanded=True):
            st.markdown(
                r"""
                For steady, fully developed 2D flow between infinite parallel plates:
                $$\mathbf{u} = (u(y), 0, 0)$$
                Continuity equation: $\frac{\partial u}{\partial x} + \frac{\partial v}{\partial y} = \frac{\partial u}{\partial x} = 0 \implies u = u(y)$.

                Evaluating the convective acceleration term:
                $$(\mathbf{u}\cdot\nabla)\mathbf{u} = u\frac{\partial u}{\partial x} + v\frac{\partial u}{\partial y} = u(0) + 0\left(\frac{du}{dy}\right) = 0$$

                The $x$-momentum equation simplifies to:
                $$\mu \frac{d^2 u}{dy^2} = \frac{dp}{dx} = \text{const}$$

                Integrating twice with respect to $y$:
                $$\frac{du}{dy} = \frac{1}{\mu}\frac{dp}{dx} y + C_1$$
                $$u(y) = \frac{1}{2\mu}\frac{dp}{dx} y^2 + C_1 y + C_2$$

                Applying no-slip boundary conditions:
                * At $y = 0$: $u(0) = 0 \implies C_2 = 0$
                * At $y = h$: $u(h) = U_{\text{wall}} \implies U_{\text{wall}} = \frac{1}{2\mu}\frac{dp}{dx} h^2 + C_1 h \implies C_1 = \frac{U_{\text{wall}}}{h} - \frac{1}{2\mu}\frac{dp}{dx} h$

                Substituting $C_1$ and $C_2$ back:
                $$u(y) = \underbrace{U_{\text{wall}}\frac{y}{h}}_{\text{Couette linear shear}} + \underbrace{\frac{1}{2\mu}\left(-\frac{dp}{dx}\right) y (h - y)}_{\text{Poiseuille parabolic profile}}$$
                """
            )

    with exact_tab2:
        st.markdown(
            r"""
            Hagen–Poiseuille is the **circular-pipe** cousin of plane Poiseuille — the profile
            ChemE students actually use. Axisymmetric NS with $u_z(r)$ only:
            $$u(r) = \frac{1}{4\mu}\left(-\frac{dp}{dz}\right)(R^2 - r^2), \qquad
            Q = \frac{\pi R^4}{8\mu}\left(-\frac{dp}{dz}\right), \qquad
            \frac{u_\mathrm{avg}}{u_\mathrm{max}} = \frac12, \quad \alpha = 2$$
            """
        )
        col_hp1, col_hp2 = st.columns(2)
        with col_hp1:
            hp_radius = st.slider("Pipe radius R [m]", min_value=0.005, max_value=0.05, value=0.025, step=0.005)
        with col_hp2:
            hp_dp = st.slider("Axial gradient dp/dz [Pa/m]", min_value=-80.0, max_value=-1.0, value=-20.0, step=1.0)

        res_hp = hagen_poiseuille_pipe(
            radius=hp_radius,
            dp_dx=hp_dp,
            mu=float(fluid["mu"]),
            rho=float(fluid["rho"]),
        )
        col_h1, col_h2, col_h3 = st.columns(3)
        col_h1.metric("u_max (centerline)", format_quantity(float(res_hp["u_max"]), "velocity"))
        col_h2.metric("u_avg = u_max / 2", format_quantity(float(res_hp["u_avg"]), "velocity"))
        col_h3.metric("Pipe Re (ρ u_avg D / μ)", f"{res_hp['reynolds']:.1f}")
        st.caption(
            f"Q = {res_hp['flow_rate']:.3e} m³/s · τ_wall = {res_hp['tau_wall']:.3f} Pa · "
            f"μ from {fluid['name']}. Switch the sidebar to Glycerin and watch Q collapse."
        )
        render_what_to_notice("Parabola in a round pipe; mean velocity is half the apex (not 2/3 — that is a plane channel).")
        fig_hp = plot_hagen_poiseuille(res_hp)
        st.plotly_chart(fig_hp, width="stretch")

    with exact_tab3:
        st.markdown(
            """
            In **Stokes' First Problem** (the Rayleigh Problem), a flat wall in fluid at rest
            is impulsively accelerated to velocity $U_0$ at $t = 0$.
            Viscous shear diffuses like heat: $\\frac{\\partial u}{\\partial t} = \\nu \\frac{\\partial^2 u}{\\partial y^2}$.
            """
        )
        nu_fluid = float(fluid["mu"]) / float(fluid["rho"])
        st.caption(f"ν = μ/ρ = {nu_fluid:.3e} m²/s from **{fluid['name']}**. Dotted horizontals are δ ≈ 3.64 √(ν t).")
        override = st.checkbox("Override ν (compare fluids)", value=False)
        if override:
            nu_val = st.select_slider(
                "Kinematic Viscosity ν = μ/ρ [m²/s]",
                options=[1.0e-5, 2.0e-5, 5.0e-5, 1.0e-4, 5.0e-4, 1.0e-3],
                value=5.0e-5,
                format_func=lambda v: f"{v:.1e} m²/s"
            )
        else:
            nu_val = nu_fluid
        res_stokes = stokes_first_problem(nu=nu_val)
        render_what_to_notice("Double ν and δ grows by √2, not 2. Viscosity is momentum diffusivity.")
        fig_stokes = plot_stokes_first_problem(res_stokes)
        st.plotly_chart(fig_stokes, width="stretch")

        with st.expander("🔍 Mathematical Derivation: Self-Similar Solution via Error Function"):
            st.markdown(
                r"""
                Governing diffusion PDE:
                $$\frac{\partial u}{\partial t} = \nu \frac{\partial^2 u}{\partial y^2}$$
                Boundary conditions: $u(0, t) = U_0$, $u(\infty, t) = 0$, $u(y, 0) = 0$.

                Define the dimensionless similarity variable:
                $$\eta = \frac{y}{2\sqrt{\nu t}}$$
                Assuming $u(y, t) = U_0 f(\eta)$, we evaluate derivatives using the chain rule:
                $$\frac{\partial \eta}{\partial t} = -\frac{y}{4 t \sqrt{\nu t}} = -\frac{\eta}{2t}, \quad \frac{\partial \eta}{\partial y} = \frac{1}{2\sqrt{\nu t}}$$
                $$\frac{\partial u}{\partial t} = U_0 f'(\eta)\left(-\frac{\eta}{2t}\right), \quad \frac{\partial^2 u}{\partial y^2} = U_0 f''(\eta)\frac{1}{4\nu t}$$
                Substituting into the PDE:
                $$-U_0 \frac{\eta}{2t} f'(\eta) = \nu U_0 \frac{1}{4\nu t} f''(\eta) \implies f''(\eta) + 2\eta f'(\eta) = 0$$
                Integrating once: $\frac{f''}{f'} = -2\eta \implies \ln f' = -\eta^2 + \ln C_1 \implies f'(\eta) = C_1 e^{-\eta^2}$.
                Integrating again:
                $$f(\eta) = C_1 \int_0^\eta e^{-s^2} ds + C_2 = C_1 \frac{\sqrt{\pi}}{2}\operatorname{erf}(\eta) + C_2$$
                Applying boundary conditions $f(0) = 1 \implies C_2 = 1$ and $f(\infty) = 0 \implies C_1 = -\frac{2}{\sqrt{\pi}}$:
                $$u(y, t) = U_0 \left[1 - \operatorname{erf}\left(\frac{y}{2\sqrt{\nu t}}\right)\right] = U_0 \operatorname{erfc}\left(\frac{y}{2\sqrt{\nu t}}\right)$$
                The viscous boundary layer penetrates to depth $\delta(t) \approx 3.64\sqrt{\nu t}$, proving that **viscosity is pure momentum diffusion**!
                """
            )

    render_self_check(
        "exact_self_check_pipe_apex",
        "In Hagen–Poiseuille pipe flow, u_avg / u_max is…",
        ["2/3 (that is a plane channel)", "1/2", "1 (slug flow)"],
        "1/2",
        "Circular pipe: u_avg = u_max/2 and α = 2. Plane channel: u_avg = (2/3) u_max and α = 54/35.",
    )

    # -------------------------------------------------------------------------
    # PART 2: Blasius
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 7.2 Blasius Flat-Plate Boundary Layer")
    st.markdown(
        r"""
        A uniform stream $U_\infty$ meets a thin plate at $x = 0$. Far from the wall the
        flow is inviscid; at the wall $u = 0$. Prandtl's 1904 scaling reduces NS to
        $$f''' + \tfrac12 f f'' = 0, \qquad
        \eta = y\sqrt{U_\infty/(\nu x)}, \qquad u/U_\infty = f'(\eta)$$
        with $f(0)=f'(0)=0$ and $f'(\infty)=1$. The layer is thin:
        $\delta/x \approx 4.91/\sqrt{\mathrm{Re}_x}$, so as $\mathrm{Re}\to\infty$
        Euler is recovered *outside* the layer — but the wall still feels drag
        $c_f = 0.664/\sqrt{\mathrm{Re}_x}$.
        """
    )
    render_svg(diagram_blasius_plate())
    render_predict(
        "blasius_predict",
        "At fixed U_∞, doubling distance x from the leading edge makes δ…",
        ["double", "grow by √2", "stay constant (similarity)"],
        "grow by √2",
        "δ ~ x / √(U x / ν) = √(ν x / U), so δ ∝ √x. Double x, multiply δ by √2.",
    )
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        bl_u = st.slider("Freestream U_∞ [m/s]", min_value=0.2, max_value=10.0, value=1.0, step=0.2, key="blasius_u")
    with col_b2:
        bl_x = st.slider("Plate length L [m]", min_value=0.05, max_value=2.0, value=0.5, step=0.05, key="blasius_L")
    nu_bl = float(fluid["mu"]) / float(fluid["rho"])
    sim = blasius_similarity_profile()
    plate = blasius_plate(x=bl_x, u_inf=bl_u, nu=nu_bl)
    col_bm1, col_bm2, col_bm3, col_bm4 = st.columns(4)
    col_bm1.metric("Re_L", f"{plate['re_L']:.3e}")
    col_bm2.metric("δ₉₉ at trailing edge", f"{plate['delta_L']*1000:.2f} mm")
    col_bm3.metric("δ/L", f"{plate['delta_L']/bl_x:.4f}")
    col_bm4.metric("C_F (mean)", f"{plate['Cf_mean']:.4e}")
    st.caption(
        f"ν = {nu_bl:.3e} m²/s ({fluid['name']}). "
        f"f''(0) = {sim['fpp0']:.5f} (Howarth), f'(η_max) = {sim['fp_inf']:.4f} → 1. "
        "Stokes' first problem (above) is *unsteady* diffusion from a wall; Blasius is *steady* growth from a leading edge."
    )
    render_what_to_notice(
        "Left: u/U rises from 0 to 1 by η ≈ 5. Right: δ, δ*, θ all grow like √x. "
        "Drag is not zero — that is d'Alembert resolved for a plate."
    )
    fig_bl = plot_blasius_profile(sim, plate)
    st.plotly_chart(fig_bl, width="stretch")

    with st.expander("🔍 Blasius ODE and the standard coefficients"):
        st.markdown(
            r"""
            Stream function $\psi = \sqrt{\nu x U_\infty}\, f(\eta)$ converts the BL equations
            into $2f''' + f f'' = 0$. Numerical shooting with $f''(0) \approx 0.33206$
            enforces $f'(\infty)=1$. Integrating the profile:
            $$\frac{\delta_{99}}{x} \approx \frac{4.91}{\sqrt{\mathrm{Re}_x}},\quad
            \frac{\delta^*}{x} = \frac{1.721}{\sqrt{\mathrm{Re}_x}},\quad
            \frac{\theta}{x} = \frac{0.664}{\sqrt{\mathrm{Re}_x}} = c_f$$
            Mean drag on one side of a plate of length $L$: $C_F = 1.328 / \sqrt{\mathrm{Re}_L}$.
            """
        )

    # -------------------------------------------------------------------------
    # PART 3: Cylinder separation
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 7.3 Cylinder: Adverse Gradient and Laminar Separation")
    st.markdown(
        r"""
        Tab 5's potential cylinder has $U_e = 2 U_\infty \sin\theta$ and $C_p = 1-4\sin^2\theta$.
        Speed *falls* after the shoulder, so $dp/ds = -\rho U_e dU_e/ds$ is **adverse**
        for $\theta > 90^\circ$. A real laminar boundary layer cannot climb that hill
        and separates near $104.5^\circ$ (Schlichting). The wake destroys fore–aft
        $C_p$ symmetry: **that is the drag Euler set to zero**.
        """
    )
    col_cy1, col_cy2 = st.columns(2)
    with col_cy1:
        sep_u = st.slider("U_∞ [m/s]", min_value=1.0, max_value=15.0, value=5.0, step=1.0, key="sep_u")
    with col_cy2:
        sep_r = st.slider("Cylinder R [m]", min_value=0.5, max_value=2.0, value=1.0, step=0.1, key="sep_R")
    sep = cylinder_outer_flow_and_separation(
        u_inf=sep_u, radius=sep_r, rho=float(fluid["rho"])
    )
    st.caption(
        "Dashed line: adverse gradient begins (θ = 90°). Dotted: empirical laminar separation (~105°). "
        "This plot is the *inviscid outer* flow; it does not compute the BL. Euler integrates the same C_p to zero drag."
    )
    render_what_to_notice(
        "C_p is still fore–aft symmetric (Euler). dp/ds changes sign at 90°. "
        "A viscous layer would leave the wall near 105° and never recover the rear stagnation pressure."
    )
    fig_sep = plot_cylinder_separation(sep)
    st.plotly_chart(fig_sep, width="stretch")

    render_self_check(
        "blasius_self_check_sep",
        "Why does potential flow past a cylinder predict zero drag, while a real laminar cylinder does not?",
        [
            "Because the real fluid is compressible",
            "Because the boundary layer separates in the adverse gradient and the rear C_p never returns to +1",
            "Because f''(0) is 0.332 instead of zero",
        ],
        "Because the boundary layer separates in the adverse gradient and the rear C_p never returns to +1",
        "Euler has no no-slip layer, so it cannot separate. Drag on a real cylinder is mostly pressure drag from the wake.",
    )


