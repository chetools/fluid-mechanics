"""UI module for chapter 8: Exact NS solutions and laminar boundary layers."""

import math
import streamlit as st
from src.ui.state import persistent_input
from src.ui.pedagogy import render_plot

from src.svg_diagrams import (
    diagram_blasius_plate,
    diagram_blasius_scaling,
    diagram_blasius_similarity,
    render_svg,
)
from src.physics.exact_solutions import (
    couette_poiseuille_channel,
    hagen_poiseuille_pipe,
    stokes_first_problem,
)
from src.physics.boundary_layer import (
    blasius_similarity_profile,
    blasius_plate,
    blasius_integral_coefficients,
    cylinder_outer_flow_and_separation,
)
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
    render_callout,
    render_derivation,
    render_prose_and_latex,
)


def render_tab_solving_ns():
    """Exact solutions plus Blasius / cylinder separation."""
    fluid = get_fluid_state()
    bl_coeff = blasius_integral_coefficients()
    st.markdown(
        """
        Except for a handful of highly symmetric cases, **no general closed-form
        Navier–Stokes solution exists**. Here the convective term vanishes or is
        absorbed into a similarity variable. The Blasius plate is the payoff of
        d'Alembert's paradox from Tab 5: viscosity lives in a thin layer, and
        an adverse outer gradient separates it. Projection CFD is Tab 13.
        """
    )
    render_objectives(
        [
            "Recover Couette–Poiseuille and Hagen–Poiseuille by dropping $(\\mathbf{u}\\cdot\\nabla)\\mathbf{u}$.",
            "Watch viscous momentum diffuse as $\\delta \\sim \\sqrt{\\nu t}$.",
            rf"State $\delta/x \approx {bl_coeff['eta_99']:.2f}/\sqrt{{\mathrm{{Re}}_x}}$ and $c_f = {bl_coeff['cf_coeff']:.3f}/\sqrt{{\mathrm{{Re}}_x}}$ from the integrated profile.",
            "Mark where the cylinder outer flow becomes adverse (90°) and where a laminar BL separates (~105°).",
        ]
    )

    st.markdown("### 8.1 Exact Analytical Solutions (When Non-Linearity Vanishes)")
    st.markdown(
        """
        For fully developed parallel flow ($v = w = 0$ and $\\partial u/\\partial x = 0$),
        the non-linear term vanishes identically: $(\\mathbf{u}\\cdot\\nabla)\\mathbf{u} = u \\frac{\\partial u}{\\partial x} = 0$.
        With the additional assumption of steady flow, the momentum equation becomes
        an ordinary differential equation across the gap or radius. Stokes' first
        problem below is unsteady and instead retains a diffusion PDE.
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
            u_wall = persistent_input(st.slider, "Top Wall Velocity U_wall [m/s]", min_value=0.0, max_value=3.0, value=1.0, step=0.2, key="tab_solving_ns_top_wall_velocity_u_wall_m_s")
        with col_cp2:
            dp_dx = persistent_input(st.slider, "Pressure Gradient dp/dx [Pa/m]", min_value=-50.0, max_value=20.0, value=-15.0, step=5.0, key="tab_solving_ns_pressure_gradient_dp_dx_pa_m")
        with col_cp3:
            ch_height = persistent_input(st.slider, "Channel Height h [m]", min_value=0.01, max_value=0.1, value=0.05, step=0.01, key="tab_solving_ns_channel_height_h_m")

        res_cp = couette_poiseuille_channel(
            h=ch_height,
            u_wall=u_wall,
            dp_dx=dp_dx,
            mu=float(fluid["mu"]),
            rho=float(fluid["rho"]),
        )

        col_cpm1, col_cpm2, col_cpm3, col_cpm4 = st.columns(4)
        col_cpm1.metric("Q per unit depth", f"{float(res_cp['q_flow']):.3e} m²/s")
        col_cpm2.metric("Mean Velocity", format_quantity(float(res_cp["u_mean"]), "velocity"))
        if math.isfinite(res_cp["alpha"]):
            col_cpm3.metric("α = (1/h)∫(u/ū)³ dy", f"{res_cp['alpha']:.3f}")
        else:
            col_cpm3.metric("α = (1/h)∫(u/ū)³ dy", "undefined")
        col_cpm4.metric("Bottom Wall Shear τ₀", format_quantity(float(res_cp["tau_wall_bottom"]), "shear_stress"))

        if res_cp["p_param"] < -1.0:
            st.info(
                "Adverse pressure gradient is strong enough for near-wall reversal "
                f"(P = {res_cp['p_param']:.2f} < −1). Look for u = 0 inside the gap."
            )
        if math.isfinite(res_cp["alpha"]):
            st.caption(
                f"μ = {fluid['mu']:.3e} Pa·s from **{fluid['name']}**. "
                f"α = {res_cp['alpha']:.3f} and β = {res_cp['beta']:.3f} are integrated on "
                "the green profile above (plane channel, dA = dy). Q is per unit depth "
                "(m²/s), not m³/s. Pure Poiseuille is "
                "54/35 ≈ 1.543; pure Couette is 2. Wall motion plus a pressure gradient "
                "is neither."
            )
        else:
            st.caption(
                f"μ = {fluid['mu']:.3e} Pa·s from **{fluid['name']}**. "
                "Q is per unit depth (m²/s). "
                "α is undefined when the net flux is ~0: there is no ū to scale by."
            )
        render_what_to_notice("Green = total u(y). Dashed = linear Couette. Dotted = parabolic Poiseuille.")
        fig_cp = plot_exact_channel_flow(res_cp)
        render_plot(fig_cp, key="tab_solving_ns-fig_cp")

        render_derivation(
            r"Couette–Poiseuille: superposition because the leftover ODE is linear",
            [
                (
                    "Fully developed parallel flow kills the convective term identically",
                    r"""
                    Steady flow between infinite plates with $\mathbf u=(u(y),0,0)$:
                    continuity is $\partial u/\partial x=0$, so $u=u(y)$ only. Then
                    $$(\mathbf u\cdot\nabla)\mathbf u
                    = u\frac{\partial u}{\partial x}+v\frac{\partial u}{\partial y}=0$$
                    — not approximated, genuinely zero, because the only non-zero velocity
                    does not vary in the direction it points.
                    """,
                ),
                (
                    "What remains is a linear ordinary differential equation",
                    r"""
                    The $x$-momentum equation collapses to
                    $$\mu\frac{d^2 u}{dy^2}=\frac{dp}{dx}=\text{const}$$
                    Linear in $u$, so any two solutions may be added. That is the whole
                    licence for writing Couette plus Poiseuille rather than solving a new
                    problem when both a moving wall and a pressure gradient are present.
                    """,
                ),
                (
                    "Integrate twice, then let no-slip fix both constants",
                    r"""
                    $$\frac{du}{dy}=\frac{1}{\mu}\frac{dp}{dx}y+C_1,\qquad
                    u(y)=\frac{1}{2\mu}\frac{dp}{dx}y^2+C_1 y+C_2$$
                    $u(0)=0$ forces $C_2=0$. $u(h)=U_{\mathrm{wall}}$ fixes $C_1$, and
                    $$u(y)=\underbrace{U_{\mathrm{wall}}\frac{y}{h}}_{\text{Couette}}
                    +\underbrace{\frac{1}{2\mu}\left(-\frac{dp}{dx}\right)y(h-y)}_{\text{Poiseuille}}$$
                    """,
                ),
                (
                    "The kinetic-energy correction is an integral of *this* profile",
                    r"""
                    For a plane channel the area element is $dy$, not $2\pi r\,dr$, so
                    $$\alpha=\frac{1}{h}\int_0^h\left(\frac{u}{\bar u}\right)^3 dy$$
                    Pure Poiseuille ($U_{\mathrm{wall}}=0$) gives $\alpha=54/35$; pure Couette
                    ($dp/dx=0$) gives $\alpha=2$. The metric above integrates the green
                    curve you actually set, so moving the sliders moves $\alpha$.
                    """,
                ),
            ],
        )

    with exact_tab2:
        render_prose_and_latex(
            r"""
            Hagen–Poiseuille is the **circular-pipe** cousin of plane Poiseuille — the profile
            ChemE students actually use. Axisymmetric NS with $u_z(r)$ only:
            $$u(r) = \frac{1}{4\mu}\left(-\frac{dp}{dz}\right)(R^2 - r^2), \qquad
            Q = \frac{\pi R^4}{8\mu}\left(-\frac{dp}{dz}\right), \qquad
            \frac{u_\mathrm{avg}}{u_\mathrm{max}} = \frac12, \quad \alpha = 2$$
            $\alpha=(1/A)\int(u/\bar{u})^3\,dA$ is the kinetic-energy correction (Tab 1),
            not an angle: the parabola forces $\alpha=2$ in a circular pipe.
            """
        )
        render_derivation(
            r"Hagen–Poiseuille straight out of Navier–Stokes in cylindrical coordinates",
            [
                (
                    "Say what the flow is, and let the assumptions kill terms",
                    r"""
                    Fully developed, steady, axisymmetric, no swirl: the velocity is
                    $\mathbf u=(0,0,u_z(r))$. Continuity in cylindrical coordinates then
                    reduces to $\partial u_z/\partial z=0$, confirming the profile cannot
                    change downstream. The convective term is
                    $$(\mathbf u\cdot\nabla)\mathbf u
                    = u_z\frac{\partial u_z}{\partial z}\mathbf e_z=\mathbf 0$$
                    — identically zero, because the only non-zero velocity component varies
                    only in the one direction it does *not* point. This is the whole reason an
                    exact solution exists: the nonlinearity is not approximated away, it is
                    genuinely absent.
                    """,
                ),
                (
                    "What is left is an ordinary differential equation",
                    r"""
                    The axial component of the viscous term in cylindrical coordinates is
                    $\nu\frac{1}{r}\frac{d}{dr}\left(r\frac{du_z}{dr}\right)$, and the
                    remaining balance is
                    $$\frac{1}{r}\frac{d}{dr}\left(r\frac{du_z}{dr}\right)
                    =\frac{1}{\mu}\frac{dp}{dz}$$
                    The left side depends only on $r$ and the right only on $z$, so both must
                    equal the **same constant** — which is why a fully developed pipe has a
                    uniform pressure gradient, rather than an assumption that it does. The
                    $\frac{1}{r}\frac{d}{dr}(r\cdot)$ form is not decoration: it is the
                    divergence in a geometry where the area of a shell grows with radius.
                    """,
                ),
                (
                    "Integrate twice, and reject one constant on physical grounds",
                    r"""
                    With $G=-dp/dz>0$:
                    $$r\frac{du_z}{dr}=-\frac{G}{2\mu}r^{2}+C_1
                    \;\Longrightarrow\;
                    u_z=-\frac{G}{4\mu}r^{2}+C_1\ln r+C_2$$
                    $C_1$ must vanish: $\ln r\to-\infty$ on the axis, and an infinite
                    centreline velocity is not physical. Equivalently, symmetry demands
                    $du_z/dr=0$ at $r=0$. No-slip $u_z(R)=0$ then fixes $C_2$:
                    $$\boxed{u_z(r)=\frac{G}{4\mu}\left(R^{2}-r^{2}\right)}$$
                    the same parabola Tab 4 obtained from a force balance on a plug — two
                    independent routes to one answer, which is the check that both are right.
                    """,
                ),
                (
                    "Integrate the profile over annuli for the flow rate",
                    r"""
                    $$Q=\int_0^R u_z(r)\,2\pi r\,dr
                    =\frac{2\pi G}{4\mu}\int_0^R\left(R^{2}r-r^{3}\right)dr
                    =\frac{\pi G}{2\mu}\left(\frac{R^{4}}{2}-\frac{R^{4}}{4}\right)
                    =\frac{\pi R^{4}}{8\mu}G$$
                    The **fourth power** of radius is the single most consequential result in
                    this course: halving a capillary's bore cuts its throughput sixteenfold at
                    the same driving pressure. It is why arteries narrow catastrophically
                    rather than gracefully, and why Tab 4's straw bundle loses.
                    """,
                ),
                (
                    "Read off the two ratios the metrics report",
                    r"""
                    $\bar u=Q/(\pi R^{2})=GR^{2}/(8\mu)$ while $u_{\max}=GR^{2}/(4\mu)$, so
                    $\bar u/u_{\max}=1/2$ exactly — a property of the parabola, not a
                    measurement. Feeding the same parabola through the kinetic-energy integral
                    of Tab 4 gives $\alpha=2$. Both numbers are **circular-pipe** results: the
                    plane channel of the previous sub-tab has $2/3$ and $54/35$ instead,
                    because its area element is $dy$ rather than $2\pi r\,dr$.
                    """,
                ),
            ],
        )
        col_hp1, col_hp2 = st.columns(2)
        with col_hp1:
            hp_radius = persistent_input(st.slider, "Pipe radius R [m]", min_value=0.005, max_value=0.05, value=0.025, step=0.005, key="tab_solving_ns_pipe_radius_r_m")
        with col_hp2:
            hp_dp = persistent_input(st.slider, "Axial gradient dp/dz [Pa/m]", min_value=-80.0, max_value=-1.0, value=-20.0, step=1.0, key="tab_solving_ns_axial_gradient_dp_dz_pa_m")

        res_hp = hagen_poiseuille_pipe(
            radius=hp_radius,
            dp_dx=hp_dp,
            mu=float(fluid["mu"]),
            rho=float(fluid["rho"]),
        )
        col_h1, col_h2, col_h3, col_h4 = st.columns(4)
        col_h1.metric("u_max (centerline)", format_quantity(float(res_hp["u_max"]), "velocity"))
        col_h2.metric("u_avg = u_max / 2", format_quantity(float(res_hp["u_avg"]), "velocity"))
        col_h3.metric("α (annular integral)", f"{res_hp['alpha']:.3f}")
        col_h4.metric("Pipe Re (ρ u_avg D / μ)", f"{res_hp['reynolds']:.1f}")
        st.caption(
            f"Q = {res_hp['flow_rate']:.3e} m³/s · τ_wall = {res_hp['tau_wall']:.3f} Pa · "
            f"α = {res_hp['alpha']:.3f}, β = {res_hp['beta']:.3f} integrated on the parabola "
            f"(exactly 2 and 4/3). μ from {fluid['name']}. Switch the sidebar to Glycerin "
            "and watch Q collapse."
        )
        render_what_to_notice("Parabola in a round pipe; mean velocity is half the apex (not 2/3 — that is a plane channel).")
        fig_hp = plot_hagen_poiseuille(res_hp)
        render_plot(fig_hp, key="tab_solving_ns-fig_hp")

    with exact_tab3:
        st.markdown(
            """
            In **Stokes' First Problem** (the Rayleigh Problem), a flat wall in fluid at rest
            is impulsively accelerated to velocity $U_0$ at $t = 0$.
            Viscous shear diffuses like heat: $\\frac{\\partial u}{\\partial t} = \\nu \\frac{\\partial^2 u}{\\partial y^2}$.
            """
        )
        nu_fluid = float(fluid["mu"]) / float(fluid["rho"])
        st.caption(
            f"ν = μ/ρ = {nu_fluid:.3e} m²/s from **{fluid['name']}**. "
            "Dotted horizontals are the 1% station of the erfc profile, "
            r"$\delta=2\,\mathrm{erfcinv}(0.01)\sqrt{\nu t}$."
        )
        override = persistent_input(st.checkbox, "Override ν (compare fluids)", value=False, key="tab_solving_ns_override_compare_fluids")
        if override:
            nu_val = persistent_input(st.select_slider,
                "Kinematic Viscosity ν = μ/ρ [m²/s]",
                options=[1.0e-5, 2.0e-5, 5.0e-5, 1.0e-4, 5.0e-4, 1.0e-3],
                value=5.0e-5,
                format_func=lambda v: f"{v:.1e} m²/s", key="tab_solving_ns_kinematic_viscosity_m_s")
        else:
            nu_val = nu_fluid
        res_stokes = stokes_first_problem(nu=nu_val)
        render_what_to_notice("Double ν and δ grows by √2, not 2. Viscosity is momentum diffusivity.")
        fig_stokes = plot_stokes_first_problem(res_stokes)
        render_plot(fig_stokes, key="tab_solving_ns-fig_stokes")

        render_derivation(
            r"Stokes' first problem: why the profile is an error function",
            [
                (
                    "No convection, only diffusion — and that is geometry, not modelling",
                    r"""
                    An infinite plate in $x$ is impulsively set to $U_0$. Nothing varies
                    with $x$, so $(\mathbf u\cdot\nabla)\mathbf u=0$ and the Navier–Stokes
                    $x$-momentum equation is the heat equation
                    $$\frac{\partial u}{\partial t}=\nu\frac{\partial^2 u}{\partial y^2}$$
                    with $u(0,t)=U_0$, $u(\infty,t)=0$, $u(y,0)=0$. Viscosity is the
                    diffusivity of momentum; $\nu$ has units $\mathrm{m}^2/\mathrm{s}$.
                    """,
                ),
                (
                    "The problem has only one dimensionless combination of $y$ and $t$",
                    r"""
                    The list $y,t,\nu$ has two dimensions (length, time), so one group:
                    $\eta=y/(2\sqrt{\nu t})$. The 2 is a convention that makes the ODE
                    below look like the derivative of a Gaussian. Seek $u=U_0 f(\eta)$.
                    """,
                ),
                (
                    "The chain rule turns the PDE into an ODE",
                    r"""
                    $\partial\eta/\partial t=-\eta/(2t)$ and $\partial\eta/\partial y=1/(2\sqrt{\nu t})$,
                    so
                    $$\frac{\partial u}{\partial t}=U_0 f'\left(-\frac{\eta}{2t}\right),\qquad
                    \frac{\partial^2 u}{\partial y^2}=U_0 f''\frac{1}{4\nu t}$$
                    Substitute: $f''+2\eta f'=0$.
                    """,
                ),
                (
                    "Integrate to the error function, then apply the two ends",
                    r"""
                    $f'/f'=-2\eta$ integrates to $f'=C_1 e^{-\eta^2}$, then
                    $$f(\eta)=C_1\frac{\sqrt{\pi}}{2}\operatorname{erf}(\eta)+C_2$$
                    $f(0)=1$ gives $C_2=1$; $f(\infty)=0$ gives $C_1=-2/\sqrt{\pi}$:
                    $$u(y,t)=U_0\operatorname{erfc}\left(\frac{y}{2\sqrt{\nu t}}\right)$$
                    """,
                ),
                (
                    r"The dotted $\delta$ is a station of this profile, not a new constant",
                    rf"""
                    Define the edge as $u=0.01\,U_0$, so $\operatorname{{erfc}}(\eta)=0.01$.
                    Then $\eta=\operatorname{{erfcinv}}(0.01)={res_stokes['eta_one_percent']:.4f}$ and
                    $$\delta(t)={res_stokes['delta_coeff']:.3f}\sqrt{{\nu t}}$$
                    The coefficient is $2\operatorname{{erfcinv}}(0.01)$, inverted from the
                    exact solution, not a quoted $3.64$.
                    """,
                ),
            ],
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
    st.markdown("### 8.2 Blasius Flat-Plate Boundary Layer")
    render_objectives(
        [
            "Say why a *thin* layer lets you delete two terms from Navier–Stokes, and which two.",
            "Build the similarity variable $\\eta$ from the scaling argument, not by being told it.",
            "Read $f''(0) = 0.332$ as a wall shear stress, and $\\delta^*$ as a displacement of the outer flow.",
            "Explain why $\\delta \\propto \\sqrt{x}$ and $c_f \\propto 1/\\sqrt{x}$ are the *same* statement.",
        ]
    )
    render_prose_and_latex(
        r"""
        A uniform stream $U_\infty$ meets a thin plate at $x = 0$. Far from the wall the
        flow is inviscid; at the wall $u = 0$. Between those two facts sits the whole of
        Prandtl's 1904 insight, and it resolves the paradox chapter 5 left open: how a
        fluid can be *effectively* inviscid almost everywhere and still exert drag.
        """
    )
    render_svg(diagram_blasius_plate())

    st.markdown("#### Step 0 · The question, and why Euler cannot answer it")
    render_prose_and_latex(
        r"""
        Euler's equation has no viscosity, so it cannot impose $u = 0$ at a wall. It gets
        one boundary condition per surface — no penetration — and is content with fluid
        sliding along the plate at full speed. That solution has **zero shear stress
        everywhere**, hence zero drag, which is wrong for every real plate ever tested.

        The resolution is not that Euler is wrong. It is that the viscous term
        $\nu\nabla^2\mathbf{u}$ carries the highest derivative, so dropping it lowers the
        order of the equation and loses a boundary condition. Whenever the highest
        derivative in a differential equation is multiplied by a small parameter, the
        solution develops a **thin region where that term is not small** — a boundary
        layer. The small parameter here is $1/\mathrm{Re}$.
        """
    )
    render_callout(
        """
        **The pattern, in one sentence.** $\\nu \\to 0$ does not make the viscous term
        disappear; it squeezes it into a layer thin enough that $\\nu \\partial^2 u/\\partial y^2$
        stays finite. The layer must therefore get *thinner* as $\\nu$ falls — precisely
        fast enough to keep the two terms comparable. Step 1 turns that sentence into $\\delta(x)$.
        """
    )

    st.markdown("#### Step 1 · How thick? A balance of two terms")
    render_svg(diagram_blasius_scaling())
    render_prose_and_latex(
        r"""
        Inside the layer, streamwise momentum is carried downstream by inertia and removed
        sideways by viscosity. Estimate each with the only scales available — $U_\infty$ for
        velocity, $x$ along the plate, $\delta$ across it:
        $$u\frac{\partial u}{\partial x} \sim \frac{U_\infty^2}{x},
        \qquad \nu\frac{\partial^2 u}{\partial y^2} \sim \frac{\nu U_\infty}{\delta^2}$$
        The layer's edge is *defined* as the place where these balance — inside, viscosity
        matters; outside, it does not. Setting them equal:
        $$\frac{U_\infty^2}{x} \sim \frac{\nu U_\infty}{\delta^2}
        \quad\Longrightarrow\quad \delta \sim \sqrt{\frac{\nu x}{U_\infty}}
        = \frac{x}{\sqrt{\mathrm{Re}_x}}$$

        **Why the square root, physically.** Viscosity is a diffusivity, with units m²/s.
        A diffusing quantity spreads a distance $\sqrt{\nu t}$ in time $t$ — the same law
        that governs heat spreading into a wall, or ink in still water. A fluid parcel that
        entered at the leading edge has been near the plate for a time $t \approx x/U_\infty$.
        Substituting gives $\delta \sim \sqrt{\nu x / U_\infty}$ immediately. **Blasius is
        Stokes' first problem carried downstream by the flow**: the moving plate of §8.1
        replaced by a stationary plate and a moving observer.
        """
    )
    render_predict(
        "blasius_predict",
        "At fixed U_∞, doubling distance x from the leading edge makes δ…",
        ["double", "grow by √2", "stay constant (similarity)"],
        "grow by √2",
        "δ ~ √(νx/U), so δ ∝ √x. Double x, multiply δ by √2 ≈ 1.41. "
        "Equivalently: the diffusion time doubled, and diffusion depth goes as the square root of time.",
    )

    st.markdown("#### Step 2 · What thinness buys: the Prandtl equations")
    render_prose_and_latex(
        r"""
        With $\delta/x \sim \mathrm{Re}_x^{-1/2} \ll 1$, compare derivatives across and along
        the layer. Any quantity changes by roughly the same amount in both directions, but
        over lengths differing by the factor $\delta/x$:
        $$\frac{\partial^2 u/\partial x^2}{\partial^2 u/\partial y^2}
        \sim \frac{U_\infty/x^2}{U_\infty/\delta^2} = \left(\frac{\delta}{x}\right)^2
        \sim \frac{1}{\mathrm{Re}_x}$$
        At $\mathrm{Re}_x = 10^5$ that ratio is $10^{-5}$: streamwise diffusion is
        negligible. **Deletion 1.**

        Continuity fixes the size of the wall-normal velocity. If $u$ changes by $U_\infty$
        over $x$, then $\partial v/\partial y \sim U_\infty/x$, so $v \sim U_\infty\delta/x$
        — small, but *not* zero, and not negligible: $v\,\partial u/\partial y \sim
        (U_\infty \delta/x)(U_\infty/\delta) = U_\infty^2/x$, the same size as
        $u\,\partial u/\partial x$. The transverse velocity is small yet fully active.

        The $y$-momentum equation, scaled the same way, gives $\partial p/\partial y \sim
        \rho U_\infty^2 \delta / x^2$. Compare it with $\partial p/\partial x \sim
        \rho U_\infty^2 / x$: the *gradient* across the layer is smaller by one factor of
        $\delta/x$. What matters, though, is the pressure **change**, and that picks up a
        second factor because the layer is only $\delta$ thick:
        $$\Delta p\big|_{\text{across}} \sim \frac{\partial p}{\partial y}\,\delta
        \sim \rho U_\infty^2\left(\frac{\delta}{x}\right)^{2},
        \qquad \Delta p\big|_{\text{along}} \sim \frac{\partial p}{\partial x}\,x
        \sim \rho U_\infty^2$$
        so the pressure difference from wall to edge is smaller than the streamwise
        variation by $(\delta/x)^2 \sim 1/\mathrm{Re}_x$. So **pressure does not vary across
        the layer. Deletion 2.**
        $$\boxed{\;u\frac{\partial u}{\partial x} + v\frac{\partial u}{\partial y}
        = -\frac{1}{\rho}\frac{dp}{dx} + \nu\frac{\partial^2 u}{\partial y^2},
        \qquad \frac{\partial p}{\partial y} = 0\;}$$
        """
    )
    render_callout(
        """
        **Deletion 2 is the one that does the work.** Because $p$ does not change across the
        layer, the wall feels whatever pressure the *inviscid outer flow* dictates. The
        boundary layer stops being a coupled problem: solve Euler outside, hand the
        resulting $p(x)$ down, and integrate the layer with it. For a flat plate at zero
        incidence the outer flow is uniform, so $dp/dx = 0$ and the equation above loses its
        pressure term entirely. Chapter 8.3 shows what happens when $dp/dx > 0$ instead.
        """,
        title="Why the boundary layer became solvable",
    )

    st.markdown("#### Step 3 · Two equations, one unknown: the stream function")
    render_prose_and_latex(
        r"""
        Continuity $\partial u/\partial x + \partial v/\partial y = 0$ is satisfied
        *identically* by any $\psi$ with
        $$u = \frac{\partial \psi}{\partial y}, \qquad v = -\frac{\partial \psi}{\partial x}$$
        because mixed partials commute. This is not a trick; it is the statement that an
        incompressible plane flow has one degree of freedom, not two. Two unknowns become
        one, and one of the two governing equations is discharged for free.
        """
    )

    st.markdown("#### Step 4 · Similarity: guessing the right variable, and why it must exist")
    render_svg(diagram_blasius_similarity())
    render_prose_and_latex(
        r"""
        A semi-infinite plate has **no built-in length**. Nothing in the problem statement
        says "10 cm". So the profile at station $x$ cannot depend on $x$ except through
        whatever thickness the flow itself manufactures — and step 1 already found the only
        candidate, $\sqrt{\nu x/U_\infty}$. Measure $y$ in those units:
        $$\eta \equiv y\sqrt{\frac{U_\infty}{\nu x}} = \frac{y}{\delta(x)}\ \text{(up to a constant)}$$
        and the profile must collapse onto a single curve:
        $$\frac{u}{U_\infty} = f'(\eta)$$
        The scaling for $\psi$ follows from $u = \partial\psi/\partial y$: since $u \sim U_\infty$
        and $y \sim \sqrt{\nu x/U_\infty}$, we need $\psi \sim U_\infty\sqrt{\nu x/U_\infty}
        = \sqrt{\nu x U_\infty}$. Hence
        $$\psi = \sqrt{\nu x U_\infty}\, f(\eta)$$
        with $f$ dimensionless. Writing the velocity as $f'$ rather than $f$ is a
        convenience that makes exactly this work out.
        """
    )
    render_what_to_notice(
        "This is dimensional analysis (chapter 3) doing structural work: the *absence* of a "
        "length scale is a fact about the problem, and it collapses a PDE in two variables "
        "into an ODE in one. Whenever a problem has no intrinsic scale, look for similarity."
    )

    with st.expander("🔍 Step 5 · Grinding out the substitution, term by term"):
        render_prose_and_latex(
            r"""
            Nothing subtle here — just the chain rule, kept in full. First the derivatives
            of $\eta$ itself:
            $$\frac{\partial \eta}{\partial y} = \sqrt{\frac{U_\infty}{\nu x}},
            \qquad \frac{\partial \eta}{\partial x} = -\frac{1}{2}\frac{\eta}{x}$$

            **The streamwise velocity.**
            $$u = \frac{\partial \psi}{\partial y}
            = \sqrt{\nu x U_\infty}\, f'(\eta)\frac{\partial \eta}{\partial y}
            = \sqrt{\nu x U_\infty}\, f'(\eta) \sqrt{\frac{U_\infty}{\nu x}}
            = U_\infty f'(\eta)$$
            The dimensional factors cancel exactly, which is the check that the scaling for
            $\psi$ was chosen correctly.

            **The transverse velocity.** Differentiate the product, remembering that $\eta$
            depends on $x$ too:
            $$v = -\frac{\partial \psi}{\partial x}
            = -\left[\frac{1}{2}\sqrt{\frac{\nu U_\infty}{x}}f
            + \sqrt{\nu x U_\infty}\, f' \left(-\frac{\eta}{2x}\right)\right]
            = \frac{1}{2}\sqrt{\frac{\nu U_\infty}{x}}\left(\eta f' - f\right)$$
            Note $v > 0$: the layer *pushes fluid outward* as it thickens. That is the
            displacement effect quantified in step 8.

            **The three derivatives the equation needs.**
            $$\frac{\partial u}{\partial x} = U_\infty f''\frac{\partial\eta}{\partial x}
            = -\frac{U_\infty \eta}{2x}f''$$
            $$\frac{\partial u}{\partial y} = U_\infty f''\sqrt{\frac{U_\infty}{\nu x}},
            \qquad \frac{\partial^2 u}{\partial y^2} = \frac{U_\infty^2}{\nu x}f'''$$

            **Assemble**, with $dp/dx = 0$:
            $$\underbrace{U_\infty f'\left(-\frac{U_\infty\eta}{2x}f''\right)}_{u\,\partial u/\partial x}
            + \underbrace{\frac{1}{2}\sqrt{\frac{\nu U_\infty}{x}}(\eta f' - f)\cdot U_\infty f''\sqrt{\frac{U_\infty}{\nu x}}}_{v\,\partial u/\partial y}
            = \underbrace{\nu\frac{U_\infty^2}{\nu x}f'''}_{\nu\,\partial^2 u/\partial y^2}$$
            Every term carries $U_\infty^2/x$. Divide it out:
            $$-\frac{\eta}{2}f'f'' + \frac{1}{2}(\eta f' - f)f'' = f'''$$
            The $\tfrac{1}{2}\eta f'f''$ terms cancel — the cancellation that makes the
            method work at all — leaving
            $$\boxed{\;f''' + \tfrac{1}{2} f f'' = 0\;}\qquad\text{(equivalently } 2f''' + ff'' = 0\text{)}$$
            The $x$ and $y$ that appeared in every intermediate line are gone. A nonlinear
            PDE in two variables has become a nonlinear ODE in one.
            """
        )

    st.markdown("#### Step 6 · Boundary conditions, and the missing third one")
    render_prose_and_latex(
        r"""
        Two conditions come straight from the physics at the wall, one from the free stream:
        $$\underbrace{f(0) = 0}_{v = 0:\ \text{no through-flow}},\qquad
        \underbrace{f'(0) = 0}_{u = 0:\ \text{no slip}},\qquad
        \underbrace{f'(\infty) = 1}_{u \to U_\infty}$$
        A third-order ODE needs three conditions, and it has three — but they are split
        between two ends of the domain. That is a **boundary-value problem**, and it cannot
        simply be integrated forward from $\eta = 0$, because $f''(0)$ is unknown.

        The standard remedy is **shooting**: guess $f''(0)$, integrate to large $\eta$, and
        compare $f'(\infty)$ with 1. The residual is monotone in the guess, so a root find
        converges quickly. Howarth's value
        $$f''(0) = 0.332057\ldots$$
        is that unique shooting parameter — not a fitted constant. This app takes
        Howarth's number as the initial condition of an IVP and integrates it; it does
        **not** re-shoot on every rerun. The checks that the integration is right are
        $f'(\eta_{\max})\to 1$ in the metrics below, and that $\theta$ and $2f''(0)$
        agree, which is the momentum integral.
        """
    )

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        bl_u = persistent_input(st.slider, "Freestream U_∞ [m/s]", min_value=0.2, max_value=10.0, value=1.0, step=0.2, key="blasius_u")
    with col_b2:
        bl_x = persistent_input(st.slider, "Plate length L [m]", min_value=0.05, max_value=2.0, value=0.5, step=0.05, key="blasius_L")
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
        f"Wall shear at the trailing edge τ_w = "
        f"{sim['fpp0'] * float(fluid['rho']) * bl_u**2 / plate['re_L']**0.5:.4g} Pa. "
        "Laminar theory only: transition on a smooth plate begins near Re_x ≈ 5×10⁵."
    )
    st.caption(
        f"The integral thicknesses are **integrated from the profile above**, not quoted: "
        f"δ*/x·√Re = ∫(1−f′)dη = {sim['delta_star_coeff']:.4f}, "
        f"θ/x·√Re = ∫f′(1−f′)dη = {sim['theta_coeff']:.4f}, "
        f"shape factor H = {sim['shape_factor']:.3f}. "
        f"The momentum integral demands c_f·√Re = 2f''(0) = {sim['cf_coeff']:.4f} equal that "
        f"θ coefficient; the two agree to {abs(sim['cf_coeff'] - sim['theta_coeff']):.1e}, "
        "which is a check on the whole solve rather than a coincidence."
    )
    if plate["re_L"] > 5e5:
        st.warning(
            f"Re_L = {plate['re_L']:.2e} exceeds the usual transition range (≈5×10⁵). "
            "A real plate at these conditions is turbulent over much of its length, where "
            "δ grows like x^(4/5) and drag is several times the Blasius value. The curves "
            "below are the laminar solution regardless — read them as theory, not prediction."
        )
    render_what_to_notice(
        "Left: u/U rises from 0 to 1 by η ≈ 5, with no inflection point inside the layer. "
        "At the wall the curvature is exactly zero, because f''' = -(1/2) f f'' and f(0) = 0 "
        "— the marginal case that dp/dx = 0 buys you, and the reason 8.3's adverse "
        "gradient is so destructive. Above the wall the profile bends over monotonically. "
        f"Right: δ, δ* and θ all grow like √x, holding fixed ratios "
        f"1 : {sim['delta_star_coeff']/sim['eta_99']:.2f} : {sim['theta_coeff']/sim['eta_99']:.3f}."
    )
    fig_bl = plot_blasius_profile(sim, plate)
    render_plot(fig_bl, key="tab_solving_ns-fig_bl")

    st.markdown("#### Step 7 · Reading the answer: f″(0) is the drag")
    fpp_s = f"{sim['fpp0']:.3f}"
    cf_s = f"{sim['cf_coeff']:.3f}"
    cf_mean_s = f"{2.0 * sim['cf_coeff']:.3f}"
    ds_s = f"{sim['delta_star_coeff']:.3f}"
    th_s = f"{sim['theta_coeff']:.3f}"
    H_s = f"{sim['shape_factor']:.2f}"
    eta99_s = f"{sim['eta_99']:.2f}"
    render_prose_and_latex(
        rf"""
        Wall shear stress is $\tau_w = \mu(\partial u/\partial y)|_{{y=0}}$. Using step 5's
        derivative at $\eta = 0$:
        $$\tau_w = \mu U_\infty f''(0)\sqrt{{\frac{{U_\infty}}{{\nu x}}}}
        = {fpp_s}\,\rho U_\infty^2\,\mathrm{{Re}}_x^{{-1/2}}$$
        so the local skin-friction coefficient is
        $$c_f \equiv \frac{{\tau_w}}{{\tfrac12 \rho U_\infty^2}} = \frac{{{cf_s}}}{{\sqrt{{\mathrm{{Re}}_x}}}}$$
        Integrating $\tau_w$ over a plate of length $L$ doubles the coefficient — the
        $x^{{-1/2}}$ integrates to $2x^{{1/2}}$ — giving the mean
        $$C_F = \frac{{{cf_mean_s}}}{{\sqrt{{\mathrm{{Re}}_L}}}}$$
        The numbers are $f''(0)$ and $2f''(0)$ from the integration above, not a table.

        **Three readings of the same result.** (i) $\tau_w \propto x^{{-1/2}}$: shear is
        *infinite* at the leading edge and decays downstream, because the velocity gradient
        is squeezed into an ever-thinner layer near $x = 0$. The singularity is integrable,
        so the total drag is finite; it also signals that boundary-layer theory itself fails
        in the first millimetre, where $\delta \not\ll x$. (ii) Drag grows like $\sqrt{{L}}$,
        not $L$: the back of a plate contributes less than the front. (iii) $c_f$ falls with
        Reynolds number but total drag $\propto U_\infty^{{3/2}}$ still rises — laminar skin
        friction is *sub*-quadratic in speed, unlike pressure drag.
        """
    )

    st.markdown("#### Step 8 · δ, δ* and θ: three thicknesses that mean different things")
    render_prose_and_latex(
        rf"""
        $\delta_{{99}}$ is a convention — the height where $u = 0.99U_\infty$, here
        $\eta={eta99_s}$ — and the
        approach to the free stream is exponential, so any threshold is arbitrary. Two
        integral thicknesses are not arbitrary, because each answers a physical question.

        **Displacement thickness** $\delta^*$ answers: *by how much must the wall be moved
        outward so that an inviscid flow carries the same mass?*
        $$\delta^* = \int_0^\infty\left(1 - \frac{{u}}{{U_\infty}}\right)dy = \frac{{{ds_s}\,x}}{{\sqrt{{\mathrm{{Re}}_x}}}}$$
        The slow fluid near the wall represents a mass-flow deficit; the outer flow is pushed
        aside by exactly $\delta^*$. This is how a boundary layer talks *back* to the
        inviscid solution — a wing's effective shape is its geometry plus $\delta^*$, and
        near separation that correction stops being small.

        **Momentum thickness** $\theta$ answers: *by how much must the wall be moved outward
        to account for the momentum deficit?*
        $$\theta = \int_0^\infty \frac{{u}}{{U_\infty}}\left(1 - \frac{{u}}{{U_\infty}}\right)dy
        = \frac{{{th_s}\,x}}{{\sqrt{{\mathrm{{Re}}_x}}}}$$
        The von Kármán momentum integral makes this exact and general:
        $\tau_w = \rho U_\infty^2 \, d\theta/dx$ for zero pressure gradient. So
        **$\theta$ is the drag, accumulated**: total drag per unit width up to $x$ equals
        $\rho U_\infty^2 \theta(x)$, no solution needed. The numerical coincidence
        $\theta/x = c_f = {th_s}/\sqrt{{\mathrm{{Re}}_x}}$ is that identity in disguise.

        Their ratio is the **shape factor** $H = \delta^*/\theta = {ds_s}/{th_s} = {H_s}$ for
        Blasius. $H$ is a health check on a boundary layer: it **rises as the
        profile becomes *less* full** — more retarded near the wall, carrying proportionally
        less momentum — and laminar separation is approached around $H \approx 3.5$. Turbulent layers run near $H \approx 1.4$ — far more
        resistant to separation, which is the whole point of chapter 9's drag crisis.
        """
    )
    render_derivation(
        r"the von Kármán momentum integral: drag from a control volume, with no profile at all",
        [
            (
                "Draw a box that contains the whole layer",
                r"""
                Take a control volume of unit width from the leading edge to station $x$,
                and from the plate up to a height $h>\delta(x)$ where the flow is still
                undisturbed. Steady, incompressible, and — for a flat plate — pressure is
                uniform everywhere, so pressure exerts **no net force** on the box. The only
                horizontal force acting on the fluid is the plate's shear, and the only thing
                to compute is what momentum does.
                """,
            ),
            (
                "Mass conservation: fluid must escape through the top",
                r"""
                In through the left face: $\rho U_\infty h$. Out through the right face:
                $\int_0^h\rho u\,dy$, which is **less**, because the layer has slowed some of
                it. The difference has to leave through the top:
                $$\dot m_{\text{top}}=\rho\int_0^h\left(U_\infty-u\right)dy$$
                This is the same mass-flow deficit that $\delta^{*}$ measures, and it is
                physically the outward push a growing boundary layer gives the outer flow.
                """,
            ),
            (
                "Momentum balance, remembering what the escaping fluid carries",
                r"""
                Fluid leaving through the top is outside the layer, so it carries streamwise
                velocity $U_\infty$. With $D$ the drag the plate exerts on the fluid
                (backwards, hence the minus sign):
                $$-D=\underbrace{\int_0^h\rho u^{2}dy}_{\text{out, right}}
                +\underbrace{U_\infty\dot m_{\text{top}}}_{\text{out, top}}
                -\underbrace{\rho U_\infty^{2}h}_{\text{in, left}}$$
                Substituting $\dot m_{\text{top}}$, the $\rho U_\infty^{2}h$ terms cancel and
                what remains collapses into a single integral:
                $$-D=\rho\int_0^h u\left(u-U_\infty\right)dy
                \;\Longrightarrow\;
                \boxed{D(x)=\rho\int_0^\infty u\left(U_\infty-u\right)dy=\rho U_\infty^{2}\,\theta(x)}$$
                """,
            ),
            (
                "Differentiate to recover the local shear",
                r"""
                $D(x)$ is the accumulated drag up to $x$, so its derivative is the local wall
                stress:
                $$\tau_w=\frac{dD}{dx}=\rho U_\infty^{2}\frac{d\theta}{dx}$$
                Nothing in this derivation used the Blasius solution, the similarity variable,
                or even the assumption that the layer is laminar. It is a control-volume
                identity, valid for a turbulent layer too — which is exactly why $\theta$, not
                $\delta_{99}$, is the thickness engineers track.
                """,
            ),
            (
                "Check it against the solution we already have",
                rf"""
                Blasius gives $\theta={th_s}\,x/\sqrt{{\mathrm{{Re}}_x}}$, so
                $d\theta/dx={fpp_s}/\sqrt{{\mathrm{{Re}}_x}}$ and
                $\tau_w={fpp_s}\rho U_\infty^{{2}}\mathrm{{Re}}_x^{{-1/2}}$ — identical to Step 7's
                result from $\mu\,\partial u/\partial y$ at the wall. The apparent coincidence
                $\theta/x=c_f$ is this identity, not a numerological accident. The
                coefficients ${ds_s}$ and ${th_s}$ themselves are numerical integrals of the
                computed $f'(\eta)$; the app integrates them rather than quoting them.
                """,
            ),
        ],
    )

    render_self_check(
        "blasius_self_check_theta",
        "A plate's laminar boundary layer has θ = 0.4 mm at the trailing edge, in water "
        "(ρ = 1000 kg/m³) at U∞ = 2 m/s. Drag per unit width on that side is…",
        ["about 1.6 N/m", "about 0.8 N/m", "cannot be found without solving the profile"],
        "about 1.6 N/m",
        "The momentum integral gives D' = ρU∞²θ = 1000 × 4 × 0.0004 = 1.6 N/m directly. "
        "This needs no profile at all — it is a control-volume result, and it is why θ is "
        "the thickness engineers actually track.",
    )
    render_callout(
        """
        **Model limits.** Steady, two-dimensional, incompressible, constant properties,
        zero pressure gradient, smooth plate, no free-stream turbulence, and $x$ far enough
        from the leading edge that $\\delta \\ll x$. Transition on a smooth plate typically
        begins near $\\mathrm{Re}_x \\approx 5\\times10^5$ but roughness or free-stream
        turbulence can bring it forward by an order of magnitude. Nothing here applies once
        the layer separates — that is chapter 8.3.
        """
    )

    # -------------------------------------------------------------------------
    # PART 3: Cylinder separation
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 8.3 Cylinder: Adverse Gradient and Laminar Separation")
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
        sep_u = persistent_input(st.slider, "U_∞ [m/s]", min_value=1.0, max_value=15.0, value=5.0, step=1.0, key="sep_u")
    with col_cy2:
        sep_r = persistent_input(st.slider, "Cylinder R [m]", min_value=0.5, max_value=2.0, value=1.0, step=0.1, key="sep_R")
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
    render_plot(fig_sep, key="tab_solving_ns-fig_sep")

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


