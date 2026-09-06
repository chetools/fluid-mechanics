"""Panel 1: Why fluid mechanics for ChemE, energy Bernoulli, friction as heat."""

import streamlit as st

from src.units import get_fluid_state
from src.svg_diagrams import diagram_energy_budget, render_svg
from src.ui.pedagogy import (
    render_derivation,
    render_objectives,
    render_what_to_notice,
    render_checklist,
    render_self_check,
    render_latex,
    render_prose_and_latex,
    render_symbols,
)


def render_tab_cheme_energy():
    """Plant-level motivation and Bernoulli from a steady energy balance."""
    fluid = get_fluid_state()
    st.markdown(
        """
        A chemical plant is a **network of moving fluids**: feed and product lines,
        reflux and bottoms, cooling water, steam condensate, slurry transfers.
        The questions that size equipment and set the electricity bill are almost
        always the same:
        """
    )
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        with st.container(border=True):
            st.markdown("**Pipe flow**")
            st.markdown("What $\\Delta p$ does this transfer line require? How does pipe diameter change the speed and losses?")
    with col_b:
        with st.container(border=True):
            st.markdown("**Pumping**")
            st.markdown("How many kW of shaft work, and will the suction cavitate (NPSH)?")
    with col_c:
        with st.container(border=True):
            st.markdown("**Transport vs cost**")
            st.markdown("Turbulence mixes and transfers heat; it also dissipates mechanical energy as **heat**.")
    st.caption(
        f"Sidebar fluid **{fluid['name']}** (ρ = {fluid['rho']:.4g} kg/m³, μ = {fluid['mu']:.3e} Pa·s) "
        "feeds the incompressible and external-flow labs. Gas chapters have separate thermodynamic inputs. Tab 2 turns this energy story into a pipe/pump calculation."
    )
    render_objectives(
        [
            "State why $\\Delta p$, pump kW, and NPSH are the ChemE fluid-mechanics triad.",
            "Derive Bernoulli from a **steady mechanical energy balance**, not from Euler.",
            "Identify viscosity as **frictional heating**: irreversible conversion of $p/\\rho + u^2/2 + gz$ into internal energy.",
        ]
    )

    st.markdown("### 1.1 Where the energy goes in a plant line")
    render_svg(diagram_energy_budget(), "Illustrative head balance: the pump supplies both the elevation rise and the pipe losses. Geometry is schematic; the head-budget bar is proportional.")
    st.markdown(
        r"""
        Between two stations on a pipe (feed tank $\to$ pump discharge, or pump $\to$
        column feed nozzle) a fluid carries three *mechanical* stores of energy per
        unit mass, plus whatever shaft work we add:
        """
    )
    render_latex(
        r"\underbrace{\frac{p}{\rho}}_{\text{flow work / pressure energy}}"
        r" + \underbrace{\frac{\alpha u^{2}}{2}}_{\text{kinetic}}"
        r" + \underbrace{g z}_{\text{potential}}"
        r" + \underbrace{w_{\mathrm{shaft}}}_{\text{pump (in)}}"
    )
    st.markdown(
        r"""
        **What is $\alpha$?** It is the **kinetic-energy correction factor**, not an
        angle, not thermal diffusivity, and not the angular acceleration $\alpha_z$
        of Tab 6. Mean speed $\bar{u}$ undercounts the true kinetic-energy flux
        unless the profile is a plug. By definition:
        """
    )
    render_latex(
        r"\alpha = \frac{1}{A}\int_A \left(\frac{u}{\bar{u}}\right)^3\,dA"
        r"\qquad \bar{u} = \frac{1}{A}\int_A u\,dA"
    )
    render_symbols(
        [
            (r"p", "static pressure (Pa). Flow work per unit mass is $p/\\rho$."),
            (r"\rho", "mass density (kg/m³). Sidebar fluid."),
            (r"u", "local axial speed (m/s). $\\bar{u}$ (also $u_{\\mathrm{avg}}$) is the area-mean speed $Q/A$."),
            (
                r"\alpha",
                "kinetic-energy correction: $\\alpha=(1/A)\\int(u/\\bar{u})^3\\,dA$. "
                "Circular pipe: $\\alpha=2$ exactly if laminar (parabola); "
                r"$\alpha\approx 1.06$ if turbulent (Tab 4 integrates the profile); "
                "$\\alpha=1$ only for a uniform plug. Plane channel: $\\alpha=54/35\\approx 1.54$ (Tab 7).",
            ),
            (r"g", r"gravitational acceleration, $9.81\,\mathrm{m/s^2}$."),
            (r"z", "elevation of the station above a chosen datum (m)."),
            (
                r"w_{\mathrm{shaft}}",
                "shaft work **per unit mass** (J/kg). Positive when a pump *adds* energy to the fluid.",
            ),
            (r"A", "cross-sectional area of the pipe (m²), not Churchill's auxiliary $A$ in Tab 2."),
        ]
    )
    st.markdown(
        r"""
        In a steady inviscid flow with no pump or turbine, the sum of pressure,
        kinetic, and potential energy is constant along a streamline.
        A smooth wall alone does not eliminate friction. A stationary no-slip wall
        does no boundary work because its velocity is zero; viscous deformation
        within the fluid converts mechanical energy into internal energy.
        We account for it as a lost mechanical head $h_f$ (and fittings $h_{\mathrm{minor}}$).
        Divide every term by $g$ to get **metres of head**:
        """
    )
    render_latex(
        r"\frac{p_1}{\rho g} + \alpha_1\frac{u_1^2}{2g} + z_1 + h_{\mathrm{shaft}}"
        r" = \frac{p_2}{\rho g} + \alpha_2\frac{u_2^2}{2g} + z_2 + h_f + h_{\mathrm{minor}}"
    )
    render_symbols(
        [
            (r"h_{\mathrm{shaft}}", r"pump head $w_{\mathrm{shaft}}/g$ (m). Left-hand side: we add it."),
            (r"h_f", r"major (skin-friction) head loss (m). Darcy–Weisbach: $h_f = f_D (L/D) u^2/(2g)$."),
            (r"h_{\mathrm{minor}}", r"fitting / entrance / exit head loss (m), $\sum K_L\, u^2/(2g)$."),
            (r"\text{subscripts }1,2", "upstream and downstream stations on the same streamtube."),
        ]
    )
    st.markdown(
        r"""
        This is the **engineering mechanical energy equation** (extended Bernoulli).
        Tab 2 evaluates every term for a real transfer line. Tab 4 shows that in
        laminar pipe flow a force balance *computes* $h_f$ exactly ($f_D = 64/\mathrm{Re}$).
        """
    )

    st.markdown("### 1.2 Derivation: steady energy balance on a streamtube")
    with st.expander("From the first law to Bernoulli, without skipping the friction term", expanded=False):
        st.markdown("**Step 1 — First law for an open system (steady).**")
        st.markdown(
            "For a control volume with one inlet and one outlet, no accumulation:"
        )
        render_latex(
            r"\dot{m}\left(h + \frac{\alpha\bar{u}^2}{2} + gz\right)_{\mathrm{in}}"
            r" + \dot{W}_{\mathrm{shaft}} + \dot{Q}"
            r" = \dot{m}\left(h + \frac{\alpha\bar{u}^2}{2} + gz\right)_{\mathrm{out}}"
        )
        render_symbols(
            [
                (r"\dot{m}", "mass flow rate (kg/s). Steady: one $\\dot{m}$ in and out."),
                (
                    r"h",
                    r"specific enthalpy (J/kg). $h = \hat{u}_{\mathrm{int}} + p/\rho$ already contains flow work.",
                ),
                (r"\hat{u}_{\mathrm{int}}", "specific internal energy (J/kg). Not the velocity $u$."),
                (r"\dot{W}_{\mathrm{shaft}}", r"shaft power (W). Per unit mass: $w_{\mathrm{shaft}}=\dot{W}_{\mathrm{shaft}}/\dot{m}$."),
                (r"\dot{Q}", "heat transfer rate **into** the control volume (W)."),
            ]
        )

        st.markdown("**Step 2 — Incompressible liquid.**")
        render_prose_and_latex(
            r"""
$\rho$ is constant, so $\Delta h = c_p\Delta T + \Delta p/\rho$
(the $p/\rho$ piece is mechanical; $c_p\Delta T$ is thermal).
            """
        )
        render_symbols(
            [
                (r"c_p", r"specific heat at constant pressure (J/(kg·K)). Water $\approx 4180$."),
                (r"\Delta T", "bulk temperature rise from dissipation and wall heat (K)."),
            ]
        )

        st.markdown("**Step 3 — Split heat and dissipation.**")
        render_prose_and_latex(
            r"""
            Let $q_{\mathrm{heat}}=\dot{Q}/\dot{m}$ be heat supplied per kilogram.
            Substitute the enthalpy change from Step 2 into Step 1 and collect
            the thermal terms on the outlet side:
            $$e_f=c_p(T_2-T_1)-q_{\mathrm{heat}}.$$
            For the steady incompressible transfer considered here, this is the
            mechanical energy converted into internal energy per kilogram.
            In an insulated pipe, $q_{\mathrm{heat}}=0$, so $e_f=c_p\Delta T$.
            Heat loss through the wall can remove that energy without a measurable
            temperature rise; the mechanical loss is still present.
            """
        )
        st.markdown(
            r"""
            Wall heat $\dot{Q}$ and *internally generated* friction both change
            internal energy. Isolate the mechanical part by defining the
            **lost work** (dissipation) per unit mass $e_f \ge 0$:
            """
        )
        render_latex(
            r"\frac{p_1}{\rho} + \frac{\alpha_1\bar{u}_1^2}{2} + gz_1 + w_{\mathrm{shaft}}"
            r" = \frac{p_2}{\rho} + \frac{\alpha_2\bar{u}_2^2}{2} + gz_2 + e_f"
        )
        st.markdown(
            r"Divide by $g$ to get metres of head. $e_f/g = h_f + h_{\mathrm{minor}}$."
        )
        render_symbols(
            [
                (
                    r"e_f",
                    r"lost mechanical work per unit mass (J/kg), $e_f\ge 0$. "
                    r"In head units: $e_f/g = h_f + h_{\mathrm{minor}}$.",
                ),
            ]
        )

        st.markdown("**Step 4 — Where viscosity lives.**")
        st.markdown(
            r"""
            The local dissipation rate is the contraction $\Phi$ of viscous stress
            with the velocity gradient. For an incompressible Newtonian fluid:
            """
        )
        render_latex(
            r"\Phi = \boldsymbol{\tau}:\nabla\mathbf{u} = 2\mu\,\mathbf{D}:\mathbf{D} \ge 0"
        )
        render_prose_and_latex(
            r"""
Integrated over the pipe volume it *is* $\dot{m}\,e_f$.
No viscosity $\Rightarrow$ $\Phi = 0$ $\Rightarrow$ $e_f = 0$ $\Rightarrow$
classical Bernoulli (Tab 5 will recover the same statement from Euler).
Viscosity is not an extra force we forgot: it is the mechanism that
**turns organized kinetic/pressure energy into random molecular energy (heat).**
            """
        )
        render_symbols(
            [
                (r"\Phi", r"viscous dissipation function (W/m³). Volume integral equals $\dot{m}\,e_f$."),
                (r"\boldsymbol{\tau}", "viscous (deviatoric) stress tensor (Pa)."),
                (r"\mathbf{D}", r"strain-rate tensor $\tfrac12(\nabla\mathbf{u}+(\nabla\mathbf{u})^T)$ (1/s)."),
                (r"\mu", "dynamic viscosity (Pa·s). Sidebar fluid. $\\Phi=0$ if $\\mu=0$."),
            ]
        )

        st.markdown("**Step 5 — Ideal limit.**")
        st.markdown(
            r"Steady, incompressible, $w_{\mathrm{shaft}}=0$, $e_f=0$, $\alpha=1$ (plug profile):"
        )
        render_latex(
            r"p + \tfrac12\rho u^2 + \rho g z = \text{constant along the tube.}"
        )

    render_derivation(
        r"where $\Phi=2\mu\,\mathbf D:\mathbf D$ comes from, and why $e_f$ cannot be negative",
        [
            (
                "Make an energy equation out of the momentum equation",
                r"""
                Nothing new needs to be postulated: take Cauchy's momentum equation (Tab 6)
                and form its scalar product with the velocity itself.
                $$\mathbf u\cdot\left(\rho\frac{D\mathbf u}{Dt}\right)
                =\rho\frac{D}{Dt}\left(\tfrac12u^{2}\right)$$
                because $\mathbf u\cdot d\mathbf u=d(\tfrac12u^{2})$. The left-hand side is
                now the rate of change of **kinetic energy per unit volume** following the
                fluid — force dotted with velocity is power, which is the whole trick.
                """,
            ),
            (
                "Split the stress work into transport and conversion",
                r"""
                The right-hand side carries $\mathbf u\cdot(\nabla\cdot\boldsymbol\sigma)$,
                and the product rule for tensors separates it into two physically different
                things:
                $$\mathbf u\cdot(\nabla\cdot\boldsymbol\sigma)
                =\underbrace{\nabla\cdot(\boldsymbol\sigma\cdot\mathbf u)}_{\text{work carried across the boundary}}
                -\underbrace{\boldsymbol\sigma:\nabla\mathbf u}_{\text{converted inside}}$$
                The first term is a divergence, so over a control volume it becomes a surface
                integral: energy handed **through** the boundary by pressure and shear. It
                moves energy around and creates none. Everything irreversible must therefore
                live in the second term.
                """,
            ),
            (
                "Insert the Newtonian stress and discard what incompressibility kills",
                r"""
                With $\boldsymbol\sigma=-p\mathbf I+\boldsymbol\tau$:
                $$\boldsymbol\sigma:\nabla\mathbf u
                =-p\,(\nabla\cdot\mathbf u)+\boldsymbol\tau:\nabla\mathbf u$$
                The first piece is reversible compression work — squeeze a gas and you can get
                the work back — and for an incompressible fluid it is identically zero. What
                survives is the viscous part alone.
                """,
            ),
            (
                r"Only $\mathbf D$ contributes, which is Tab 6's claim in energy form",
                r"""
                Substituting $\boldsymbol\tau=2\mu\mathbf D$ and splitting the velocity
                gradient into its symmetric and antisymmetric parts:
                $$\boldsymbol\tau:\nabla\mathbf u
                =2\mu\,\mathbf D:(\mathbf D+\boldsymbol\Omega)
                =2\mu\,\mathbf D:\mathbf D$$
                because the double contraction of a **symmetric** tensor with an
                **antisymmetric** one is always zero: every term $D_{ij}\Omega_{ij}$ is
                cancelled by $D_{ji}\Omega_{ji}=-D_{ij}\Omega_{ij}$. So rigid rotation does no
                viscous work — the energetic statement of the geometric argument in §6.2, and
                the two must agree.
                """,
            ),
            (
                "Read the sign, and notice the second law arriving unannounced",
                r"""
                $$\Phi=2\mu\,\mathbf D:\mathbf D=2\mu\sum_{i,j}D_{ij}^{2}\;\ge\;0$$
                It is a sum of **squares** times a positive viscosity, so it cannot be
                negative for any flow whatsoever. Mechanical energy can be converted into
                internal energy but never recovered from it. That one-way arrow was not
                assumed anywhere in this derivation; it fell out of the constitutive law, and
                it is why $e_f\ge0$ and why a "negative friction loss" in a calculation is
                always an error rather than a discovery.
                """,
            ),
            (
                "Integrate over the pipe and recover the term the plant engineer books",
                r"""
                Integrating $\Phi$ over the volume between the two stations gives the total
                rate at which the line destroys mechanical energy, which is precisely what
                Step 3 defined:
                $$\int_V\Phi\,dV=\dot m\,e_f=\dot m\,g\left(h_f+h_{\text{minor}}\right)
                = Q\,\Delta p_f$$
                Set $\mu=0$ and every term vanishes at once: $\Phi=0$, $e_f=0$, and the
                mechanical energy equation collapses to classical Bernoulli. Viscosity is not
                a force somebody forgot to include — it is the mechanism that moves energy
                from the organised column ($p/\rho$, $u^{2}/2$, $gz$) into the disorganised one.
                """,
            ),
        ],
    )

    render_checklist(
        "When the plant Bernoulli applies",
        [
            ("Steady mass flow", True, "One $\\dot{m}$ in and out. Startup transients need the unsteady term."),
            ("Incompressible (or low Ma)", True, f"Sidebar fluid: {fluid['name']}."),
            ("Friction booked as $h_f$, not ignored", True, "That is the ChemE difference from textbook inviscid Bernoulli."),
            ("Shaft work signed correctly", True, "Pump: $h_{\\mathrm{shaft}}>0$ on the left (we add energy). Turbine: opposite."),
        ],
    )

    st.markdown("### 1.3 Frictional heating is usually small in temperature, large in kW")
    render_prose_and_latex(
        r"""
        Order of magnitude: $e_f \approx c_p \Delta T$ if the pipe is adiabatic.
        A 100 kPa frictional drop in water is $e_f = \Delta p/\rho \approx 100$ J/kg,
        so $\Delta T \approx 0.024\,\mathrm{K}$. You will not feel it on the pipe wall.
        The *power* $\dot{m}\,e_f = Q\,\Delta p$ is the pump bill — tens of kW on a
        long header. That is why ChemE fluid mechanics is an energy subject first,
        and a tensor subject later (Tabs 5–7).
        """
    )
    render_what_to_notice(
        "Next: Tab 2 sizes $h_f$ with Darcy–Weisbach and a pump. "
        "Tab 3 explains why one Moody chart covers every Newtonian fluid. "
        "Tab 4 derives $f=64/\\mathrm{Re}$ from a force balance and asks whether packing the pipe with straws would beat turbulence."
    )
    render_self_check(
        "energy_self_check_friction",
        "In a well-insulated water line, frictional Δp becomes…",
        [
            "a large temperature rise (tens of °C)",
            "a tiny ΔT but a pump power Q·Δp that can dominate OPEX",
            "a change in density that invalidates Bernoulli",
        ],
        "a tiny ΔT but a pump power Q·Δp that can dominate OPEX",
        "e_f = Δp/ρ ~ 100 J/kg per 100 kPa; c_p of water is 4180 J/(kg·K). The money is in kW, not in °C.",
    )
