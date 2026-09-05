"""UI module for Panel 1: Euler's Equation (1D to 3D), Streamlines & Bernoulli."""

import streamlit as st
from src.ui.state import persistent_input
from src.ui.pedagogy import render_plot

from src.svg_diagrams import (
    diagram_continuity_streamtube,
    diagram_1d_euler_element,
    diagram_eulerian_vs_lagrangian,
    diagram_streamline_geometry,
    render_svg
)
from src.physics.euler import venturi_profile, cylinder_potential_flow
from src.plotting import plot_venturi, plot_cylinder_potential_flow
from src.units import format_quantity, get_fluid_state, is_nondimensional
from src.ui.pedagogy import (
    render_objectives,
    render_what_to_notice,
    render_checklist,
    render_predict,
    render_self_check,
    render_prose_and_latex,
    render_callout,
)


def render_tab_euler():
    """Render comprehensive educational panel for Euler's Equation."""
    fluid = get_fluid_state()
    st.markdown(
        """
        Euler’s equation is the momentum balance for an **inviscid fluid**
        ($\\mu = 0$). It is *not* a complete description of real liquids:
        the cylinder lab at the end of this panel is the reason we will need
        Navier–Stokes.
        """
    )
    render_objectives(
        [
            "Write steady continuity $A u = Q$ and use it before momentum.",
            "Derive 1D Euler from $\\sum dF = dm\\, a$ without skipping algebra.",
            "State the Bernoulli assumptions and watch $p$ trade against $\\tfrac12\\rho u^2$.",
            "See d'Alembert's paradox: inviscid surface pressure integrates to **theoretical** zero drag.",
        ]
    )

    # -------------------------------------------------------------------------
    # PART 0: Continuity
    # -------------------------------------------------------------------------
    st.markdown("### 5.1 Mass Conservation (Continuity) Comes First")
    render_prose_and_latex(
        r"""
        Momentum without mass conservation is incomplete. For a **steady** streamtube,
        mass does not accumulate inside:
        $$\dot{m} = \rho A u = \text{constant along the tube}$$
        If density is constant (incompressible), volume flux is conserved: $A_1 u_1 = A_2 u_2 = Q$.
        That is the only reason a Venturi throat is *faster* than the inlet.
        """
    )
    render_svg(diagram_continuity_streamtube())

    with st.expander("🔍 Reynolds transport vs. the differential statement", expanded=False):
        render_prose_and_latex(
            r"""
            For a fixed control volume, mass conservation is the Reynolds transport theorem
            applied to $B = m$:
            $$\frac{d}{dt}\int_{\mathrm{CV}} \rho\, dV + \int_{\mathrm{CS}} \rho\, \mathbf{u}\cdot\mathbf{n}\, dA = 0$$
            Shrinking the CV to a point gives the differential continuity equation
            $$\frac{\partial \rho}{\partial t} + \nabla \cdot (\rho \mathbf{u}) = 0$$
            and for $\rho = \mathrm{const}$, $\nabla \cdot \mathbf{u} = 0$.
            The 1D streamtube statement $A u = Q$ is this idea with one inlet and one outlet.
            """
        )

    # -------------------------------------------------------------------------
    # PART 1: 1D Elementary Derivation
    # -------------------------------------------------------------------------
    st.markdown("### 5.2 Elementary 1D Derivation from First Principles")
    st.markdown(
        """
        Consider an infinitesimal fluid parcel of length $dx$ and cross-sectional area $A$
        moving along a streamtube inclined at an angle $\\theta$ relative to the horizontal.
        """
    )

    render_svg(diagram_1d_euler_element())

    render_callout(
        """
        **Physical Force Inventory on the Fluid Parcel**

        Every fluid particle accelerates strictly according to Newton's Second Law: $dm \\cdot a = \\sum dF$. Three distinct forces act on our parcel:

        1. **Upstream Pressure Force:** Pushes forward on the left face with magnitude $F_{\\text{left}} = p \\cdot A$.
        2. **Downstream Pressure Resistance:** Opposes motion on the right face. Because pressure varies with space, the pressure at $x + dx$ is given by Taylor expansion $p + \\frac{\\partial p}{\\partial x}dx$, yielding $F_{\\text{right}} = -\\left(p + \\frac{\\partial p}{\\partial x}dx\\right) A$.
        3. **Gravity Force (Weight Component):** Gravity acts downward. The component opposing flow along the inclined axis is $F_{\\text{grav}} = -dm \\cdot g \\sin\\theta = -dm \\cdot g \\frac{dz}{dx}$.
        """
    )

    with st.expander("🔍 Step-by-Step Algebraic Proof: From Newton's Second Law to 1D Euler", expanded=False):
        render_prose_and_latex(
            r"""
            **Step 1: Write Newton's Second Law**
            $$dm \cdot a_x = \sum dF_x$$

            **Step 2: Express parcel mass**
            The parcel mass is the density times volume:
            $$dm = \rho \cdot dV = \rho \cdot A \, dx$$

            **Step 3: Sum the applied forces**
            $$\sum dF_x = \underbrace{p A}_{\text{left face}} - \underbrace{\left(p + \frac{\partial p}{\partial x}dx\right)A}_{\text{right face}} - \underbrace{\rho A dx \cdot g \sin\theta}_{\text{weight component}}$$

            Expanding the right-face pressure term:
            $$\sum dF_x = p A - p A - \frac{\partial p}{\partial x}A \, dx - \rho A dx \cdot g \frac{\partial z}{\partial x}$$
            $$\sum dF_x = -\frac{\partial p}{\partial x}A \, dx - \rho g \frac{\partial z}{\partial x}A \, dx$$

            **Step 4: Equate mass times acceleration to the net force**
            $$(\rho A \, dx) a_x = -\frac{\partial p}{\partial x}A \, dx - \rho g \frac{\partial z}{\partial x}A \, dx$$

            **Step 5: Divide both sides by the parcel volume $(A \, dx)$**
            $$\rho a_x = -\frac{\partial p}{\partial x} - \rho g \frac{\partial z}{\partial x}$$

            Dividing through by density $\rho$:
            $$a_x = -\frac{1}{\rho}\frac{\partial p}{\partial x} - g \frac{\partial z}{\partial x}$$
            """
        )

    st.markdown(":blue[**1D Euler Momentum Equation:**]")
    st.latex(r"\rho \frac{Du}{Dt} = -\frac{\partial p}{\partial x} - \rho g \frac{\partial z}{\partial x}")

    # -------------------------------------------------------------------------
    # PART 2: The Material Derivative
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 5.3 The Material (Substantial) Derivative $\\frac{D}{Dt}$")
    st.markdown(
        """
        Why can we not simply write $a_x = \\frac{\\partial u}{\\partial t}$?
        Because fluid particles **move while their velocity changes**!
        """
    )

    render_svg(diagram_eulerian_vs_lagrangian())

    col_analogy1, col_analogy2 = st.columns(2)
    with col_analogy1:
        render_callout(
            """
            **Eulerian Viewpoint (The Sensor on the Bridge)**

            You stand on a bridge and hold a thermometer in the river at fixed coordinate $\\mathbf{x}_0$.
            You measure $\\frac{\\partial T}{\\partial t}$: how water temperature at that exact location changes as day turns to night.
            If the flow is steady, $\\frac{\\partial T}{\\partial t} = 0$, even if upstream water is ice-cold and downstream water is boiling.
            """
        )
    with col_analogy2:
        render_callout(
            """
            **Lagrangian Viewpoint (The Fish Swimming Along)**

            A fish drifts with the current along trajectory $\\mathbf{X}(t)$.
            Even in steady flow ($\\frac{\\partial T}{\\partial t} = 0$), as the fish drifts from cold into warm water,
            it experiences temperature change because it moves across spatial gradients:
            $u \\frac{\\partial T}{\\partial x}$. This is **advective / convective rate of change**!
            """
        )

    st.markdown(":blue[**The Material Derivative Operator:**]")
    st.latex(r"\frac{D}{Dt} = \underbrace{\frac{\partial}{\partial t}}_{\text{Local / Unsteady Rate}} + \underbrace{(\mathbf{u} \cdot \nabla)}_{\text{Advective / Convective Transport}}")
    st.latex(r"\text{For velocity: } \quad \frac{D\mathbf{u}}{Dt} = \frac{\partial \mathbf{u}}{\partial t} + (\mathbf{u}\cdot\nabla)\mathbf{u} = \frac{\partial \mathbf{u}}{\partial t} + u\frac{\partial \mathbf{u}}{\partial x} + v\frac{\partial \mathbf{u}}{\partial y} + w\frac{\partial \mathbf{u}}{\partial z}")

    with st.expander("🔍 Multivariable Calculus Proof: Multidimensional Chain Rule"):
        render_prose_and_latex(
            r"""
            Let $\mathbf{u} = \mathbf{u}(x, y, z, t)$ be the velocity field.
            As a specific fluid parcel travels along its pathline, its coordinates vary with time:
            $$x = X(t), \quad y = Y(t), \quad z = Z(t)$$
            where $\frac{dX}{dt} = u$, $\frac{dY}{dt} = v$, and $\frac{dZ}{dt} = w$.

            By the multivariable chain rule, the total time derivative experienced by the parcel is:
            $$\frac{d\mathbf{u}}{dt} = \frac{\partial \mathbf{u}}{\partial t} \frac{dt}{dt} + \frac{\partial \mathbf{u}}{\partial x}\frac{dX}{dt} + \frac{\partial \mathbf{u}}{\partial y}\frac{dY}{dt} + \frac{\partial \mathbf{u}}{\partial z}\frac{dZ}{dt}$$
            Substituting $\frac{dX}{dt} = u, \frac{dY}{dt} = v, \frac{dZ}{dt} = w$:
            $$\frac{D\mathbf{u}}{Dt} = \frac{\partial \mathbf{u}}{\partial t} + u \frac{\partial \mathbf{u}}{\partial x} + v \frac{\partial \mathbf{u}}{\partial y} + w \frac{\partial \mathbf{u}}{\partial z} = \frac{\partial \mathbf{u}}{\partial t} + (\mathbf{u}\cdot\nabla)\mathbf{u}$$
            This proves why fluid acceleration contains the quadratic, non-linear advection term $(\mathbf{u}\cdot\nabla)\mathbf{u}$.
            """
        )

    # -------------------------------------------------------------------------
    # PART 3: 3D Vector Euler Equation
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 5.4 Generalization to the 3D Vector Euler Equation")
    render_prose_and_latex(
        r"""
        Applying the momentum balance independently along all three Cartesian axes $(x, y, z)$
        for an infinitesimal control volume $dx \times dy \times dz$ yields:
        $$\rho \left(\frac{\partial u}{\partial t} + u\frac{\partial u}{\partial x} + v\frac{\partial u}{\partial y} + w\frac{\partial u}{\partial z}\right) = -\frac{\partial p}{\partial x} + \rho g_x$$
        $$\rho \left(\frac{\partial v}{\partial t} + u\frac{\partial v}{\partial x} + v\frac{\partial v}{\partial y} + w\frac{\partial v}{\partial z}\right) = -\frac{\partial p}{\partial y} + \rho g_y$$
        $$\rho \left(\frac{\partial w}{\partial t} + u\frac{\partial w}{\partial x} + v\frac{\partial w}{\partial y} + w\frac{\partial w}{\partial z}\right) = -\frac{\partial p}{\partial z} + \rho g_z$$
        """
    )
    st.markdown(":blue[**3D Vector Euler Equation:**]")
    st.latex(r"\frac{\partial \mathbf{u}}{\partial t} + (\mathbf{u}\cdot\nabla)\mathbf{u} = -\frac{1}{\rho}\nabla p + \mathbf{g}")

    # -------------------------------------------------------------------------
    # PART 4: Connection to Bernoulli & Streamline Theory
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 5.5 Connection to Bernoulli: Integration along a Streamline")
    st.markdown(
        """
        What is a **streamline**? A streamline is an instantaneous curve that is everywhere
        tangent to the velocity vector $\\mathbf{u}$.
        """
    )
    render_svg(diagram_streamline_geometry())

    with st.expander("🔍 Mathematical Derivation: Integrating Euler along a Streamline to Obtain Bernoulli"):
        render_prose_and_latex(
            r"""
            For steady flow ($\partial \mathbf{u}/\partial t = 0$), Euler's equation is:
            $$(\mathbf{u}\cdot\nabla)\mathbf{u} = -\frac{1}{\rho}\nabla p - g \nabla z$$

            Let $d\mathbf{s} = (dx, dy, dz)$ be an infinitesimal displacement **along a streamline**,
            so $d\mathbf{s} \parallel \mathbf{u}$ and $\mathbf{u} \times d\mathbf{s} = \mathbf{0}$.

            Take the scalar product of Euler's equation with $d\mathbf{s}$:
            $$(\mathbf{u}\cdot\nabla)\mathbf{u} \cdot d\mathbf{s} = -\frac{1}{\rho}\nabla p \cdot d\mathbf{s} - g \nabla z \cdot d\mathbf{s}$$

            Use the identity $(\mathbf{u}\cdot\nabla)\mathbf{u} = \nabla\left(\frac{1}{2}u^2\right) - \mathbf{u} \times (\nabla \times \mathbf{u})$.
            The rotational term drops **because $d\mathbf{s}$ is parallel to $\mathbf{u}$**:
            $$\bigl(\mathbf{u} \times \boldsymbol{\omega}\bigr)\cdot d\mathbf{s}
            = \boldsymbol{\omega}\cdot\bigl(d\mathbf{s}\times\mathbf{u}\bigr) = 0$$
            (It is *not* $\mathbf{u}\times\mathbf{u}$; that would be a different identity.)

            Then $\nabla(\tfrac12 u^2)\cdot d\mathbf{s} = d(\tfrac12 u^2)$, $\nabla p\cdot d\mathbf{s} = dp$, $\nabla z\cdot d\mathbf{s} = dz$:
            $$d\left(\frac{1}{2}u^2\right) + \frac{dp}{\rho} + g \, dz = 0$$

            For an incompressible fluid ($\rho = \text{const}$), integrate:
            $$p + \frac{1}{2}\rho u^2 + \rho g z = C \quad \text{along a streamline}$$
            **Bernoulli's equation is Euler integrated along a streamline**, under the assumptions below.
            """
        )

    render_checklist(
        "Bernoulli assumption checklist (this panel's labs)",
        [
            ("Steady", True, "Venturi and cylinder are set up as $\\partial/\\partial t = 0$."),
            ("Inviscid ($\\mu = 0$)", True, "No frictional recovery loss in the diffuser. Real Venturis lose some $H$."),
            ("Incompressible", True, "Uses sidebar $\\rho$. Cavitation is the lab's way of leaving this assumption."),
            ("Along a streamline (or irrotational)", True, "1D streamtube; potential flow around the cylinder."),
            ("No shaft work / no heat as work", True, "Pumps appear in Tab 2; friction as heat is Tab 1."),
        ],
    )

    render_self_check(
        "euler_self_check_bernoulli",
        "Along a horizontal inviscid streamtube, if speed doubles, static pressure…",
        [
            "stays constant because $H$ is constant",
            "falls so that $p + \\tfrac12\\rho u^2$ stays constant",
            "rises because faster fluid hits harder",
        ],
        "falls so that $p + \\tfrac12\\rho u^2$ stays constant",
        "H = p + ½ρu² is the invariant (z = 0). Faster fluid has larger kinetic term, so p must drop.",
    )

    # -------------------------------------------------------------------------
    # PART 5: Interactive Visualizations (Both Demos)
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 5.6 Interactive Physical Laboratories")
    st.caption(
        f"Both labs use the sidebar fluid **{fluid['name']}** "
        f"(ρ = {fluid['rho']:.4g} kg/m³). Sliders remain in SI."
    )

    demo_tab1, demo_tab2 = st.tabs([
        "🔬 Demo A: 1D Venturi Tube & Manometer Lab",
        "🌊 Demo B: 2D Cylinder Potential Flow & d'Alembert's Paradox"
    ])

    with demo_tab1:
        st.markdown(
            """
            Mass conservation ($A_1 u_1 = A_2 u_2$) forces the throat to accelerate.
            Euler then requires a static-pressure drop. Worked check: inlet $D_1 = 0.10\\,\\mathrm{m}$,
            so $u_1 = Q / (\\pi D_1^2/4)$ and $u_\\mathrm{throat} = Q / (\\pi D_t^2/4)$.
            """
        )
        render_predict(
            "venturi_predict",
            "If you shrink the throat at fixed Q, throat static pressure will…",
            ["rise", "fall", "stay equal to the inlet"],
            "fall",
            "Continuity raises u at the throat; Bernoulli trades p against ½ρu². The dashed H line stays flat (inviscid, horizontal).",
        )
        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            d_throat = persistent_input(st.slider, "Throat Diameter [m]", min_value=0.02, max_value=0.08, value=0.04, step=0.005, key="tab_euler_throat_diameter_m")
        with col_v2:
            q_flow = persistent_input(st.slider, "Flow Rate Q [m³/s]", min_value=0.005, max_value=0.05, value=0.02, step=0.005, key="tab_euler_flow_rate_q_m_s")
        with col_v3:
            p_inlet_kpa = persistent_input(st.slider, "Inlet Pressure [kPa]", min_value=50.0, max_value=300.0, value=150.0, step=10.0, key="tab_euler_inlet_pressure_kpa")

        res_venturi = venturi_profile(
            d_throat=d_throat,
            flow_rate=q_flow,
            p_inlet=p_inlet_kpa * 1000.0,
            rho=float(fluid["rho"]),
        )

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Throat Velocity", format_quantity(res_venturi['u_throat'], 'velocity'))
        if is_nondimensional():
            col_m2.metric("Throat Static Pressure", format_quantity(float(res_venturi['p_throat']), 'pressure'))
            col_m3.metric("Throat Pressure Drop Δp", format_quantity(float(res_venturi['delta_p']), 'pressure_drop'))
        else:
            col_m2.metric("Throat Static Pressure", f"{res_venturi['p_throat']/1000.0:.1f} kPa")
            col_m3.metric("Throat Pressure Drop Δp", f"{res_venturi['delta_p']/1000.0:.1f} kPa")

        p_vap = fluid.get("vapor_pressure")
        if p_vap is not None and res_venturi["p_throat"] < p_vap:
            st.warning(
                f"Throat pressure is below the vapor pressure of {fluid['name']} "
                f"({p_vap/1000.0:.2f} kPa). This lab's incompressible Bernoulli model is no longer valid — "
                "cavitation would form."
            )
        elif fluid.get("kind") == "gas":
            st.caption("Cavitation is a liquid-vapor warning; it is not applied to gases.")

        render_what_to_notice(
            "The dashed invariant $H = p + \\tfrac12\\rho u^2$ is flat. Static $p$ and kinetic $\\tfrac12\\rho u^2$ trade. "
            "A real diffuser would drop $H$ slightly; Euler cannot see that loss."
        )
        fig_venturi = plot_venturi(res_venturi)
        render_plot(fig_venturi, key="tab_euler-fig_venturi")

    with demo_tab2:
        st.markdown(
            """
            In 1752, d'Alembert showed that for inviscid, steady potential flow
            past any closed body, **the integrated pressure drag is exactly zero**.
            Surface speed is $u_\\theta = 2 U_\\infty \\sin\\theta$, so
            $C_p = 1 - 4\\sin^2\\theta$.
            """
        )
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            u_inf = persistent_input(st.slider, "Freestream Velocity U∞ [m/s]", min_value=1.0, max_value=15.0, value=5.0, step=1.0, key="tab_euler_freestream_velocity_u_m_s")
        with col_c2:
            cyl_radius = persistent_input(st.slider, "Cylinder Radius R [m]", min_value=0.5, max_value=2.0, value=1.0, step=0.1, key="tab_euler_cylinder_radius_r_m")

        res_cyl = cylinder_potential_flow(
            radius=cyl_radius,
            u_inf=u_inf,
            rho=float(fluid["rho"]),
        )

        col_d1, col_d2, col_d3 = st.columns(3)
        col_d1.metric(
            "Pressure-force quadrature (drag)",
            f"{res_cyl['drag_force']:.2e} N/m",
            help="Theory: identically 0. This is a discrete integral of p n·e_x, so expect ~1e-12 residual, not a physical drag.",
        )
        col_d2.metric("Pressure-force quadrature (lift)", f"{res_cyl['lift_force']:.2e} N/m")
        col_d3.metric("Max Surface Velocity", format_quantity(2.0 * u_inf, "velocity") + " (θ = ±90°)")

        render_what_to_notice(
            "Fore–aft $C_p$ is symmetric: $C_p(0°)=C_p(180°)=+1$. No wake, no separation. "
            "That is why the integral is theoretically zero — viscosity is missing (Tab 6)."
        )
        fig_cyl = plot_cylinder_potential_flow(res_cyl)
        render_plot(fig_cyl, key="tab_euler-fig_cyl")

        render_callout(
            """
            **Why does d'Alembert's Paradox happen?**

            Inviscid Euler equations omit viscosity ($\\mu = 0$). Without viscosity:
            * No friction exists to enforce the **no-slip condition** ($u_{\\text{wall}} = 0$) at the solid surface.
            * The flow negotiates the rear of the cylinder with perfect fore-and-aft symmetry without boundary layer separation.
            * High pressure at the front stagnation point ($C_p = +1$) is perfectly balanced by high pressure at the rear stagnation point ($C_p = +1$), yielding **zero net drag**.

            To capture realistic drag, separation, and a wake, we **must incorporate viscous stresses** — Navier–Stokes in Tab 6, and a boundary-layer story in Tab 7.
            """
        )
