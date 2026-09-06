"""UI module for Pipe Flow and Chemical Engineering piping applications."""

import streamlit as st
from src.ui.state import persistent_input
from src.ui.pedagogy import render_plot

from src.physics.pipe_flow import (
    calculate_cheme_pipe_system,
    PIPE_ROUGHNESS,
    hydraulic_diameter,
    friction_factor_churchill,
    entrance_length,
    npsh_available,
)
from src.physics.non_newtonian import power_law_pressure_drop
from src.physics.open_channel import (
    CANAL_DEMO_DEFAULTS,
    CHANNEL_ROUGHNESS,
    MANNING_N,
    channel_state,
    rating_curve,
)
from src.physics.turbulence import pipe_kinetic_correction
from src.svg_diagrams import (
    diagram_canal_section,
    diagram_canal_uniform_flow,
    diagram_npsh,
    render_svg,
)
from src.plotting import (
    plot_cheme_head_loss_breakdown,
    plot_moody_chart,
    plot_npsh_station,
    plot_open_channel_rating,
)
from src.units import format_quantity, get_fluid_state
from src.ui.pedagogy import (
    render_derivation,
    render_objectives,
    render_what_to_notice,
    render_predict,
    render_self_check,
    render_prose_and_latex,
    render_callout,
    render_latex,
    render_symbols,
)


def render_tab_pipe_flow():
    """Render practical pipe flow, Moody chart, and ChemE piping lab."""
    fluid = get_fluid_state()
    st.markdown(
        """
        In industrial chemical plants, piping networks transport liquids and gases across
        reactor loops, columns, and exchangers. Frictional pressure drop sizes pumps,
        sets OPEX, and (with NPSH) protects against cavitation.

        This panel uses the **sidebar fluid** ({name}, ρ = {rho:.4g} kg/m³, μ = {mu:.3e} Pa·s).
        Tab 4 explains why Re = 2300 is a *pipe* threshold; Tab 1's Bernoulli is the
        inviscid core of the mechanical energy equation used here.
        """.format(name=fluid["name"], rho=fluid["rho"], mu=fluid["mu"])
    )
    render_objectives(
        [
            "Work in Fanning $f_F$, and convert with $f_D = 4 f_F$ when a chart or text is Darcy.",
            "Read a Moody operating point and see $f(Re, \\varepsilon/D)$.",
            "Write the mechanical energy equation, then size a pump from $\\Delta p$ and $\\eta$.",
            "Compute $D_H$ for an annulus or duct and reuse the same $f$.",
            "Compute $\\mathrm{NPSH}_A$ at a pump suction and compare it to $\\mathrm{NPSH}_R$.",
            "Check that $L > L_e$ before trusting a fully developed friction factor.",
        ]
    )

    # -------------------------------------------------------------------------
    # PART 1: Frictional head loss and the Fanning friction factor
    # -------------------------------------------------------------------------
    st.markdown("### 2.1 Frictional Head Loss: the Fanning Friction Factor")
    st.markdown(
        """
        This course works in the **Fanning** friction factor $f_F$ throughout — the
        chemical engineering convention, and the one that *is* the dimensionless wall
        shear stress. Frictional pressure drop in a circular pipe (Darcy–Weisbach,
        written in Fanning form):
        """
    )

    render_latex(r"f_F = \frac{\tau_{\mathrm{wall}}}{\frac{1}{2}\rho u^2}")
    render_latex(r"\Delta p_f = 4 f_F \frac{L}{D} \left(\frac{1}{2}\rho u^2\right)")
    render_latex(r"h_f = \frac{\Delta p_f}{\rho g} = 4 f_F \frac{L}{D} \frac{u^2}{2g}")
    render_latex(r"f_D \equiv 4 f_F \qquad \text{(the Darcy factor, if your chart or text uses it)}")
    render_symbols(
        [
            (r"\Delta p_f", "frictional pressure drop along the pipe (Pa)."),
            (r"f_F", r"Fanning friction factor (dimensionless) — the convention used everywhere in this app, as in BSL and Perry. Laminar circular pipe: $f_F=16/\mathrm{Re}$."),
            (r"f_D", "Darcy (Moody) friction factor, $f_D=4f_F$. Published Moody charts are almost always in this. Laminar circular pipe: $f_D=64/\\mathrm{Re}$."),
            (r"L", "pipe length (m)."),
            (r"D", "inner diameter (m)."),
            (r"\rho", "mass density (kg/m³). Sidebar fluid."),
            (r"u", r"area-mean speed $\bar{u}=Q/A$ (m/s)."),
            (r"h_f", r"frictional head loss (m). $h_f=\Delta p_f/(\rho g)$."),
            (r"\tau_{\mathrm{wall}}", r"wall shear stress (Pa). $f_F=\tau_w/(\tfrac12\rho u^2)$."),
            (r"g", r"gravitational acceleration, $9.81\,\mathrm{m/s^2}$."),
        ]
    )

    render_derivation(
        r"The friction factor: a momentum balance plus one definition",
        [
            (
                "Momentum balance on the whole pipe, not on a fluid particle",
                r"""
                Take the entire column of fluid between two sections a distance $L$ apart, in
                fully developed flow. "Fully developed" means the velocity profile is the same
                at both ends, so the momentum flux in equals the momentum flux out and the
                fluid does not accelerate. Newton's second law therefore reduces to a statics
                problem: the pressure force pushing must equal the wall shear holding back.
                $$\underbrace{\Delta p_f\cdot\frac{\pi D^{2}}{4}}_{\text{pressure, on the area}}
                =\underbrace{\tau_w\cdot\pi D L}_{\text{shear, on the perimeter}}$$
                Note carefully which geometry each force uses: pressure acts on the
                cross-**section**, friction on the wetted **perimeter**. That mismatch is the
                whole reason diameter appears at all.
                """,
            ),
            (
                "Solve for the pressure drop and look at the geometry factor",
                r"""
                $$\Delta p_f=\frac{4L}{D}\,\tau_w$$
                This is exact — no turbulence model, no laminar assumption, no correlation.
                The group $4/D$ is the surface-to-volume ratio of a cylinder, so a pipe of
                half the diameter suffers twice the pressure drop *at the same wall stress*,
                purely because it offers twice as much wall per unit of fluid carried.
                """,
            ),
            (
                r"The problem: nobody can measure $\tau_w$",
                r"""
                $\tau_w$ depends on the velocity profile at the wall, which depends on the
                turbulence, which is what we cannot compute. So the engineering move is to
                **define** a dimensionless stress by dividing by the dynamic pressure — the
                natural scale for a momentum-driven stress, from Bernoulli:
                $$f_F\equiv\frac{\tau_w}{\tfrac12\rho \bar u^{2}}$$
                This is the **Fanning** friction factor. Nothing has been solved; the unknown
                has been repackaged as a dimensionless number that experiments can chart
                against $\mathrm{Re}$ and $\varepsilon/D$ once and for all pipes.
                """,
            ),
            (
                "Substitute the definition back into the balance",
                r"""
                $$\Delta p_f=\frac{4L}{D}\cdot f_F\cdot\frac{\rho\bar u^{2}}{2}
                =\underbrace{(4f_F)}_{\textstyle f_D}\frac{L}{D}\frac{\rho\bar u^{2}}{2}$$
                The factor of four is nothing but the $4$ from the surface-to-volume ratio in
                Step 2. Leave it on display and the friction factor stays **Fanning**;
                absorb it for tidiness and it becomes **Darcy**. **That is the entire
                origin of the Darcy/Fanning confusion** — two communities chose to put the
                same $4$ in different places, and $f_D=4f_F$ forever after. This course
                leaves it on display:
                $$\boxed{\Delta p_f=4f_F\frac{L}{D}\frac{\rho\bar u^{2}}{2}},
                \qquad h_f=\frac{\Delta p_f}{\rho g}=4f_F\frac{L}{D}\frac{\bar u^{2}}{2g}$$
                """,
            ),
            (
                "What has actually been established, and what has not",
                r"""
                Darcy–Weisbach is a definition wrapped around an exact force balance: it is
                true for laminar, turbulent, smooth and rough pipes alike, and it predicts
                nothing on its own. Every piece of physics sits in $f_F(\mathrm{Re},
                \varepsilon/D)$ — computed exactly for laminar flow in Tab 4
                ($f_F=16/\mathrm{Re}$), and measured for turbulent flow, which is what the
                Moody chart below plots. Dividing by $\rho g$ converts a pressure to a **head**
                in metres of the flowing fluid, which is the currency pumps are sold in.
                """,
            ),
        ],
    )

    with st.expander("⚠️ Nomenclature Alert: Fanning (used here) vs. Darcy (used almost everywhere else)", expanded=False):
        st.markdown(
            r"""
            Two friction factors are in circulation and they differ by exactly a factor of
            four. **This app reports Fanning $f_F$ everywhere**, the Moody chart included.
            * **Fanning $f_F$** — the chemical engineering convention: *Bird, Stewart &
              Lightfoot*, *Perry's Chemical Engineers' Handbook*, *McCabe, Smith & Harriott*,
              and drilling / non-Newtonian pipeline hydraulics. It is the wall shear stress
              made dimensionless, $f_F=\tau_w/(\tfrac12\rho u^2)$, so it drops straight into
              the Chilton–Colburn analogy and into any wall-stress argument.
              * Laminar flow: $f_F = \dfrac{16}{Re}$.
            * **Darcy $f_D$** (Darcy–Weisbach, also called the Moody or Blasius factor) —
              the convention in:
              * **civil / environmental engineering** — water distribution, sewers, open
                channels, hydrology (this is why Manning's $n$ maps to $f_D$);
              * **mechanical engineering, HVAC and general piping design** — Crane TP-410,
                ASHRAE duct design, the published Moody chart;
              * **petroleum and gas pipeline engineering** — Weymouth, Panhandle, AGA;
              * **aerospace and gas dynamics** — Fanno-line tables are printed as
                $f_D L^*/D$, which Tab 6 writes as the identical $4 f_F L^*/D$.
              * Laminar flow: $f_D = \dfrac{64}{Re}$, and $f_D = 4 f_F$.

            Always check whether the design equation you copied carries the factor of 4.
            The quick tell is the laminar line: **64/Re is Darcy, 16/Re is Fanning.**

            The Chilton–Colburn analogy in Tab 4 is $j_H = j_D = f_F/2 = f_D/8$, **not** $f_F/8$.
            """
        )

    st.markdown("### 2.1b Mechanical energy (extended Bernoulli)")
    st.markdown(
        r"""
        Integrating the steady momentum equation along a streamline *and then adding*
        viscous dissipation and shaft work gives the engineering mechanical energy equation
        between stations 1 and 2:
        """
    )
    render_latex(
        r"\frac{p_1}{\rho g} + \alpha_1\frac{u_1^2}{2g} + z_1 + h_{\mathrm{shaft}}"
        r" = \frac{p_2}{\rho g} + \alpha_2\frac{u_2^2}{2g} + z_2 + h_f + h_{\mathrm{minor}}"
    )
    st.markdown(
        r"""
        **$\alpha$ is the kinetic-energy correction**
        $\alpha=(1/A)\int(u/\bar{u})^3\,dA$, not an angle.
        Circular pipe: $\alpha=2$ exactly if laminar; $\alpha\approx 1.06$ if turbulent
        (Tab 4 integrates the profile — do not round it back to a table).
        $h_{\mathrm{shaft}}$ is the pump head this lab solves for.
        $h_f=4f_F(L/D)u^2/(2g)$ from §2.1; $h_{\mathrm{minor}}=\sum K_L\,u^2/(2g)$.
        For two large tanks, $u_1\approx u_2\approx 0$ and an outlet $K_L=1$ already dumps
        the exit kinetic head — do not add $\alpha u^2/2g$ on top of that $K_L$.
        """
    )

    render_derivation(
        r"minor losses: why $K_L u^{2}/2g$, and the one case that can be derived exactly",
        [
            (
                "Where the energy actually goes in a fitting",
                r"""
                An elbow, a valve or an expansion loses head not by wall friction — they are
                far too short for that — but because the flow **separates**. Fluid cannot turn
                a sharp corner, so it detaches, forms a recirculating eddy, and that eddy
                grinds the kinetic energy it was given into heat. The loss is therefore
                proportional to the kinetic energy available to be wasted, which is why every
                fitting is charged as a multiple of the velocity head:
                $$h_{\text{minor}}=K_L\frac{\bar u^{2}}{2g}$$
                $K_L$ is measured, not derived, for almost every fitting. But one geometry is
                simple enough to solve exactly, and it is worth doing because it shows the
                mechanism.
                """,
            ),
            (
                "Sudden expansion: momentum on the control volume",
                r"""
                A pipe of area $A_1$ discharges abruptly into one of area $A_2$. Take the
                control volume from the expansion plane to a section downstream where the flow
                has refilled the larger pipe. The jet issues into a region of nearly stagnant,
                recirculating fluid, so the pressure across the whole face at the plane is
                effectively $p_1$ acting on the full area $A_2$:
                $$(p_1-p_2)A_2=\dot m\,(u_2-u_1)=\rho A_2u_2(u_2-u_1)
                \;\Longrightarrow\;\frac{p_1-p_2}{\rho}=u_2(u_2-u_1)$$
                Momentum is used here rather than energy precisely because momentum does not
                care that the interior is a violent mess — the same reasoning as the shock in
                Tab 12.
                """,
            ),
            (
                "Energy on the same control volume, and subtract",
                r"""
                The mechanical energy equation over the same two sections **defines** the loss:
                $$g\,h_L=\frac{p_1-p_2}{\rho}+\frac{u_1^{2}-u_2^{2}}{2}$$
                Substitute the momentum result and watch it collapse to a perfect square:
                $$g\,h_L=u_2^{2}-u_1u_2+\frac{u_1^{2}-u_2^{2}}{2}
                =\frac{u_1^{2}-2u_1u_2+u_2^{2}}{2}=\frac{(u_1-u_2)^{2}}{2}$$
                $$\boxed{h_L=\frac{(u_1-u_2)^{2}}{2g}}$$
                This is the Borda–Carnot loss, and its form is deeply physical: what is
                dissipated is the kinetic energy of the **velocity difference** — the relative
                motion between the jet and the slower fluid it must mix with. If there were no
                velocity difference there would be no loss.
                """,
            ),
            (
                r"Read off $K_L$, and explain the exit fitting",
                r"""
                Continuity gives $u_2=u_1A_1/A_2$, so in terms of the *upstream* velocity head
                $$h_L=\left(1-\frac{A_1}{A_2}\right)^{2}\frac{u_1^{2}}{2g}
                \;\Longrightarrow\; K_L=\left(1-\frac{A_1}{A_2}\right)^{2}$$
                Now let $A_2\to\infty$: a pipe discharging into a large tank. Then $K_L\to1$,
                and the fitting throws away **exactly one velocity head**. That is the
                justification for the $K_L=1$ outlet in the fittings list below, and it is why
                adding $\alpha\bar u^{2}/2g$ on top of it would count the same energy twice.
                """,
            ),
            (
                "Why the other fittings are tabulated instead",
                r"""
                An elbow or a globe valve separates in a geometry no control volume can be
                drawn around cleanly, so its $K_L$ comes from measurement. The equivalent-length
                method ($L_e/D$) is the same information in different clothing: setting
                $K_L=4f_F L_e/D$ converts one to the other. Both are approximations at the
                $\pm25\%$ level, and both depend on Reynolds number more than their tabulation
                admits.
                """,
            ),
        ],
    )

    render_derivation(
        r"from head loss to pump kilowatts and dollars",
        [
            (
                "The energy equation already contains the pump term",
                r"""
                Rearrange the mechanical energy equation above for the one unknown a designer
                actually buys:
                $$h_{\text{shaft}}
                =\underbrace{(z_2-z_1)}_{\text{static lift}}
                +\underbrace{\frac{p_2-p_1}{\rho g}}_{\text{vessel pressures}}
                +\underbrace{h_f+h_{\text{minor}}}_{\text{friction}}
                +\underbrace{\frac{\alpha_2u_2^{2}-\alpha_1u_1^{2}}{2g}}_{\text{usually zero}}$$
                Between two large tanks the last term vanishes because both surfaces are
                effectively still. Notice the static lift is **independent of flow rate** while
                friction grows roughly as $Q^{2}$: that is the shape of the system curve the
                pump must intersect.
                """,
            ),
            (
                "Head is energy per unit weight, so power needs a weight flow rate",
                r"""
                $h_{\text{shaft}}$ is joules per newton of fluid. Multiply by newtons per
                second — the weight flow rate $\rho g Q$ — to get watts:
                $$P_{\text{hydraulic}}=\rho g Q\,h_{\text{shaft}}=Q\,\Delta p_{\text{total}}$$
                The two forms are identical; the second is often quicker because $Q\Delta p$
                has obvious units of $\mathrm{m^{3}/s}\times\mathrm{Pa}=\mathrm{W}$.
                """,
            ),
            (
                "Efficiency divides, it does not multiply",
                r"""
                The pump and motor deliver less to the fluid than they draw, so the shaft
                power is larger:
                $$P_{\text{shaft}}=\frac{\rho g Q\,h_{\text{shaft}}}{\eta}$$
                Getting this the wrong way round is a common and expensive slip. Annual cost
                follows by multiplying by running hours and tariff:
                $$\text{cost}=P_{\text{shaft}}\times\text{hours}\times\text{\$/kWh}$$
                Because $h_f\propto Q^{2}$ in turbulent flow, $P\propto Q^{3}$ (Tab 4), and
                because $h_f\propto D^{-5}$ at fixed $Q$, a modest increase in pipe diameter
                is nearly always cheaper over a plant's life than the pump it saves. The lab
                below is built to let you test exactly that trade.
                """,
            ),
        ],
    )

    # -------------------------------------------------------------------------
    # PART 2: The Interactive Moody Chart
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 2.2 The Moody Diagram & Churchill (1977) Correlation")
    render_prose_and_latex(
        r"""
        In 1944, Lewis Ferry Moody plotted the friction factor against Reynolds number and
        relative roughness $\varepsilon/D$. **The chart below is drawn in Fanning $f_F$;
        Moody's original and most reprints of it are in Darcy $f_D = 4f_F$, so every
        ordinate here is one quarter of the textbook value.**

        * **Laminar Zone ($\mathrm{Re} < 2300$, circular pipe):** Independent of roughness! $f_F = 16/\mathrm{Re}$.
        * **Critical Zone ($2000 < \mathrm{Re} < 4000$):** Flow is intermittently turbulent; highly sensitive.
        * **Wholly Turbulent Rough Pipe Zone:** Viscous sublayer is thinner than wall asperities; $f_F$ becomes independent of $\mathrm{Re}$ and depends solely on $\varepsilon/D$.
        """
    )
    st.markdown(
        r"""
        The live diamond uses **Churchill's 1977 explicit formula** — one expression
        from laminar through transition into fully rough turbulence, so we never switch
        correlations by hand. Churchill published it in Darcy form, so the code divides the
        result by four before plotting. Colebrook–White is the implicit turbulent cousin
        (a root find for $f_D$); Churchill recovers it without iterating.
        S. W. Churchill, *Chem. Eng.* **84**(24) 91–92 (1977).
        """
    )
    render_latex(
        r"A_{\mathrm{Ch}} = \left[2.457\ln\frac{1}{(7/\mathrm{Re})^{0.9}+0.27\,\varepsilon/D}\right]^{16}"
    )
    render_latex(r"B_{\mathrm{Ch}} = \left(\frac{37530}{\mathrm{Re}}\right)^{16}")
    render_latex(
        r"f_F = \frac{f_D}{4} = 2\left[\left(\frac{8}{\mathrm{Re}}\right)^{12} + (A_{\mathrm{Ch}}+B_{\mathrm{Ch}})^{-3/2}\right]^{1/12}"
    )
    render_symbols(
        [
            (r"\mathrm{Re}", r"Reynolds number $\rho u D/\mu$ (dimensionless). Circular pipe, inner $D$."),
            (r"\varepsilon", r"equivalent sand-grain roughness (m). Commercial steel $\approx 45\,\mu\mathrm{m}$."),
            (r"\varepsilon/D", "relative roughness (dimensionless). The Moody family parameter."),
            (
                r"A_{\mathrm{Ch}},\ B_{\mathrm{Ch}}",
                "Churchill's auxiliary groups (dimensionless). "
                "**Not** area $A$ and **not** the strain-rate tensor. "
                "In the 1977 paper they are called $A$ and $B$; the subscript Ch avoids that clash. "
                r"$A_{\mathrm{Ch}}=(2.457\ln(1/x))^{16}$ is identical to $(-2.457\ln x)^{16}$.",
            ),
            (
                r"(8/\mathrm{Re})^{12}",
                r"laminar weight. When $\mathrm{Re}\ll 2300$ this term dominates and $f_F\to 16/\mathrm{Re}$.",
            ),
            (
                r"B_{\mathrm{Ch}}",
                r"transition weight. Large near $\mathrm{Re}\sim 10^3$, then vanishes.",
            ),
            (r"f_F", "Fanning friction factor returned by this formula and plotted on the Moody chart. Churchill's own expression returns $f_D=4f_F$."),
        ]
    )
    render_predict(
        "moody_predict",
        "In fully rough turbulent flow, increasing Re at fixed ε/D will make f_F…",
        ["keep falling as 16/Re", "become almost independent of Re", "jump discontinuously to zero"],
        "become almost independent of Re",
        "The wholly rough regime is a horizontal Moody line: skin friction is set by ε/D, not viscosity.",
    )

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        re_pipe_input = persistent_input(st.select_slider,
            "Operating Reynolds Number Re",
            options=[800, 1500, 2100, 3000, 5000, 10000, 50000, 100000, 500000, 1000000, 10000000],
            value=50000, key="tab_pipe_flow_operating_reynolds_number_re")
    with col_m2:
        eps_d_input = persistent_input(st.select_slider,
            "Relative Pipe Roughness ε/D",
            options=[0.0, 1e-5, 5e-5, 1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 2e-2, 5e-2],
            value=1e-3,
            format_func=lambda x: "Smooth (0.0)" if x == 0.0 else f"{x:.0e}", key="tab_pipe_flow_relative_pipe_roughness_d")

    f_op = friction_factor_churchill(re_pipe_input, eps_d_input)

    col_k1, col_k2, col_k3 = st.columns(3)
    col_k1.metric("Operating Re", f"{re_pipe_input:,.0f}")
    col_k2.metric("Fanning Friction Factor f_F", f"{f_op:.4f}")
    col_k3.metric("Darcy Friction Factor f_D = 4 f_F", f"{f_op * 4.0:.4f}")

    render_what_to_notice("The diamond is (Re, f_F). Laminar is 16/Re; the shaded band is the pipe transition, not a law for cavities.")
    fig_moody = plot_moody_chart(re_pipe_input, eps_d_input, f_op)
    render_plot(fig_moody, key="tab_pipe_flow-fig_moody")

    # -------------------------------------------------------------------------
    # PART 3: Practical ChemE Piping Network & Pump Sizing Lab
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 2.3 Practical ChemE Piping Network & Pump Sizing Lab")
    st.markdown(
        """
        Design an industrial transfer line between two chemical process units.
        Select the pipe geometry, commercial material, fitting counts, and flow rate
        to determine total pressure drop, required pump motor power, and annual electrical operating cost.
        """
    )

    col_pipe1, col_pipe2, col_pipe3 = st.columns(3)
    with col_pipe1:
        flow_rate_m3h = persistent_input(st.slider, "Flow Rate Q [m³/h]", min_value=1.0, max_value=100.0, value=25.0, step=1.0, key="tab_pipe_flow_flow_rate_q_m_h")
        pipe_d_mm = persistent_input(st.slider, "Pipe Inner Diameter [mm]", min_value=25.0, max_value=200.0, value=75.0, step=5.0, key="tab_pipe_flow_pipe_inner_diameter_mm")
    with col_pipe2:
        pipe_len_m = persistent_input(st.slider, "Pipe Length L [m]", min_value=5.0, max_value=250.0, value=60.0, step=5.0, key="tab_pipe_flow_pipe_length_l_m")
        elevation_m = persistent_input(st.slider, "Static Elevation Gain Δz [m]", min_value=0.0, max_value=50.0, value=12.0, step=1.0, key="tab_pipe_flow_static_elevation_gain_z_m")
    with col_pipe3:
        pipe_mat = persistent_input(st.selectbox, "Commercial Pipe Material", options=list(PIPE_ROUGHNESS.keys()), index=0, key="tab_pipe_flow_commercial_pipe_material")
        pump_eff = persistent_input(st.slider, "Pump Mechanical Efficiency η", min_value=0.40, max_value=0.90, value=0.72, step=0.02, key="tab_pipe_flow_pump_mechanical_efficiency")

    st.markdown("#### Fittings & Valves Inventory (Minor Losses)")
    col_fit1, col_fit2, col_fit3 = st.columns(3)
    with col_fit1:
        n_elbows = persistent_input(st.number_input, "90° Standard Elbows", min_value=0, max_value=20, value=4, key="tab_pipe_flow_90_standard_elbows")
        n_tees = persistent_input(st.number_input, "Tees (Flow through branch)", min_value=0, max_value=10, value=1, key="tab_pipe_flow_tees_flow_through_branch")
    with col_fit2:
        n_gate_valves = persistent_input(st.number_input, "Gate Valves (Open)", min_value=0, max_value=10, value=2, key="tab_pipe_flow_gate_valves_open")
        n_globe_valves = persistent_input(st.number_input, "Globe Valves (Open)", min_value=0, max_value=10, value=1, key="tab_pipe_flow_globe_valves_open")
    with col_fit3:
        n_check_valves = persistent_input(st.number_input, "Check Valves (Swing type)", min_value=0, max_value=5, value=1, key="tab_pipe_flow_check_valves_swing_type")
        elec_cost_rate = persistent_input(st.number_input, "Electricity Cost [$/kWh]", min_value=0.05, max_value=0.40, value=0.12, step=0.01, key="tab_pipe_flow_electricity_cost_kwh")

    fittings_dict = {
        "90° Standard Elbow": n_elbows,
        "Tee (Flow through branch)": n_tees,
        "Gate Valve (Fully Open)": n_gate_valves,
        "Globe Valve (Fully Open)": n_globe_valves,
        "Check Valve (Swing type)": n_check_valves,
        "Pipe Inlet (Square edge)": 1,
        "Pipe Outlet (Discharge to tank)": 1,
    }

    roughness_val = PIPE_ROUGHNESS[pipe_mat]
    pipe_d_m = pipe_d_mm / 1000.0

    sys_res = calculate_cheme_pipe_system(
        flow_rate=flow_rate_m3h,
        pipe_diameter_inner=pipe_d_m,
        pipe_length=pipe_len_m,
        roughness=roughness_val,
        density=float(fluid["rho"]),
        viscosity=float(fluid["mu"]),
        elevation_gain=elevation_m,
        fittings_counts=fittings_dict,
        pump_efficiency=pump_eff,
        electricity_cost_kwh=elec_cost_rate,
    )

    re_line = float(sys_res["reynolds"])
    corr = pipe_kinetic_correction(re_line)
    g = 9.81
    u_line = float(sys_res["velocity"])

    col_pk1, col_pk2, col_pk3, col_pk4 = st.columns(4)
    col_pk1.metric("Flow Velocity", format_quantity(u_line, "velocity"), help="Economic range is typically 1.0 to 2.5 m/s")
    col_pk2.metric("Total Pressure Drop", f"{sys_res['delta_p_total']/1000.0:.1f} kPa")
    col_pk3.metric("Required Pump Power", f"{sys_res['p_shaft_kw']:.2f} kW ({sys_res['p_shaft_hp']:.1f} HP)")
    col_pk4.metric("Annual Power Cost", f"${sys_res['annual_cost']:,.0f} / yr")

    if corr["regime"] == "transitional":
        h_lam = corr["alpha_lam"] * u_line ** 2 / (2.0 * g)
        h_turb = corr["alpha_turb"] * u_line ** 2 / (2.0 * g)
        alpha_caption = (
            f"transition (2300 < Re < 4000): no unique profile — "
            f"α_lam = {corr['alpha_lam']:.3f} → {h_lam:.2f} m, "
            f"α_turb = {corr['alpha_turb']:.3f} → {h_turb:.2f} m"
        )
    else:
        kinetic_head = corr["alpha"] * u_line ** 2 / (2.0 * g)
        n_note = f", 1/{int(corr['n_exp'])} law" if corr["regime"] == "turbulent" else ""
        alpha_caption = (
            f"α = {corr['alpha']:.3f} ({corr['regime']}{n_note}, integrated) "
            f"→ α u²/2g = {kinetic_head:.2f} m"
        )
    st.caption(
        f"Re_D = {re_line:,.0f} ({fluid['name']}) · f_F = {sys_res['f_fanning']:.4f} · "
        f"f_D = 4 f_F = {sys_res['f_darcy']:.4f} · {alpha_caption} "
        "(shown for the energy equation; outlet K_L = 1 already accounts for exit kinetic dump)."
    )

    if sys_res["velocity"] > 3.0:
        st.warning("⚠️ Warning: Flow velocity exceeds 3.0 m/s! High risk of pipe erosion, noise, and excessive friction losses.")
    elif sys_res["velocity"] < 0.6:
        st.info("ℹ️ Note: Flow velocity is below 0.6 m/s. May result in particle settling or oversized piping CAPEX.")

    ent = entrance_length(pipe_d_m, re_line)
    if ent["L_e"] > pipe_len_m:
        st.warning(
            f"Entrance length L_e ≈ {ent['L_e']:.1f} m ({ent['regime']}, L_e/D = {ent['L_e_over_D']:.0f}) "
            f"exceeds this pipe L = {pipe_len_m:.0f} m. The friction factor assumes fully developed flow."
        )
    else:
        st.caption(
            f"Entrance length L_e ≈ {ent['L_e']:.1f} m = {ent['L_e_over_D']:.1f} D ({ent['regime']}). "
            "Laminar: 0.06 Re. Turbulent: 4.4 Re^{1/6} (White). The fully developed f_F applies after L_e."
        )

    render_what_to_notice("Bars split major (skin), minor (K_L), and static lift. Switch the sidebar to Glycerin: Re collapses, f_F → 16/Re, power jumps.")
    fig_head = plot_cheme_head_loss_breakdown(sys_res)
    render_plot(fig_head, key="tab_pipe_flow-fig_head")

    render_self_check(
        "pipe_self_check_fanning",
        "A civil engineering handbook gives f = 64/Re in laminar flow. Which friction factor is that?",
        ["Darcy f_D", "Fanning f_F", "Fanning divided by 4"],
        "Darcy f_D",
        "f_F = 16/Re (used here) and f_D = 64/Re = 4 f_F. Published Moody charts almost always plot Darcy.",
    )

    # -------------------------------------------------------------------------
    # NPSH station
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 2.3b NPSH Station (pump suction)")
    render_prose_and_latex(
        r"""
        Tab 5's cavitation warning at a Venturi throat is the same physics at a pump eye.
        From a free-surface tank, **available** net positive suction head is
        $$\mathrm{NPSH}_A = \frac{P_{\mathrm{tank}} - P_v}{\rho g} + z - h_f$$
        $z>0$ flooded suction, $z<0$ suction lift. Impeller-eye velocity head is charged
        to the manufacturer's $\mathrm{NPSH}_R$, not to $\mathrm{NPSH}_A$. Cavitate if
        $\mathrm{NPSH}_A < \mathrm{NPSH}_R$.
        """
    )
    render_symbols(
        [
            (r"\mathrm{NPSH}_A", "available net positive suction head at the pump eye (m of fluid)."),
            (r"\mathrm{NPSH}_R", "required NPSH from the pump curve (m). A pump property, not a pipe property."),
            (r"P_{\mathrm{tank}}", "absolute pressure on the free surface (Pa)."),
            (r"P_v", "liquid vapor pressure at bulk temperature (Pa). Sidebar default at 20 °C."),
            (r"z", "free-surface elevation above the pump eye (m). $z>0$ flooded; $z<0$ suction lift."),
            (r"h_f", "head loss in the suction line, major + minor (m)."),
        ]
    )
    render_derivation(
        r"$\mathrm{NPSH}_A$ from the energy equation, and why the velocity head disappears",
        [
            (
                "State what is being protected against",
                r"""
                Cavitation happens when the local absolute pressure falls to the liquid's
                vapour pressure $P_v$ and bubbles form; they collapse violently a moment later
                in the higher pressure inside the impeller, pitting the metal. So the quantity
                to track is not pressure but the **margin above vapour pressure** at the worst
                point in the system, which is the pump eye.
                """,
            ),
            (
                "Define the margin as a total head, not a static one",
                r"""
                $$\mathrm{NPSH}_A\equiv\frac{p_{\text{eye}}+\tfrac12\rho u_{\text{eye}}^{2}-P_v}{\rho g}$$
                The kinetic term is included deliberately: the fluid arriving at the eye still
                carries that energy, and the pressure dip that actually causes cavitation
                happens *inside* the impeller, as the blade accelerates the flow further. How
                deep that internal dip goes is a property of the impeller, so it is charged to
                the manufacturer's $\mathrm{NPSH}_R$ — which is why $\mathrm{NPSH}_A$ is
                written on stagnation head and the two can be compared at all.
                """,
            ),
            (
                "Apply the mechanical energy equation from the tank surface to the eye",
                r"""
                Station 1 is the free surface, where the velocity is negligible and the
                pressure is $P_{\text{tank}}$; station 2 is the eye, a height $z$ below it:
                $$\frac{P_{\text{tank}}}{\rho g}+0+z
                =\frac{p_{\text{eye}}}{\rho g}+\frac{u_{\text{eye}}^{2}}{2g}+0+h_f$$
                Rearranged, the whole left-hand group of the definition appears:
                $$\frac{p_{\text{eye}}}{\rho g}+\frac{u_{\text{eye}}^{2}}{2g}
                =\frac{P_{\text{tank}}}{\rho g}+z-h_f$$
                """,
            ),
            (
                "Subtract the vapour-pressure head",
                r"""
                $$\boxed{\mathrm{NPSH}_A=\frac{P_{\text{tank}}-P_v}{\rho g}+z-h_f}$$
                The velocity head has vanished from the final expression — not because it was
                neglected, but because the definition and the energy equation contained it on
                opposite sides. This is the step most often got wrong, in both directions.
                """,
            ),
            (
                "Read each term as a design lever",
                r"""
                $(P_{\text{tank}}-P_v)/\rho g$ says a hot liquid is dangerous: $P_v$ rises
                steeply with temperature, so the same pump that is safe on cold water cavitates
                on hot condensate. $z$ says flooded suction ($z>0$) is the cheapest insurance
                there is, and it enters one-for-one. $-h_f$ says every metre of suction line,
                every elbow, and every partly shut suction valve is spent directly out of the
                margin — which is why suction lines are drawn short, straight and one size
                larger than the discharge. Cavitation occurs when
                $\mathrm{NPSH}_A<\mathrm{NPSH}_R$; the calculator below reports both.
                """,
            ),
        ],
    )
    render_svg(diagram_npsh())
    if fluid.get("kind") == "gas":
        st.info("NPSH is a liquid-vapor limit. It is not defined for the sidebar gas.")
    else:
        pv_default = float(fluid["vapor_pressure"]) if fluid.get("vapor_pressure") is not None else 2338.8
        col_n1, col_n2, col_n3 = st.columns(3)
        with col_n1:
            p_tank_kpa = persistent_input(st.number_input,
                "Tank pressure (absolute) [kPa]",
                min_value=20.0, max_value=300.0, value=101.3, step=1.0, key="npsh_ptank",
            )
            z_s = persistent_input(st.slider,
                "z surface above pump [m] (+ flooded)",
                min_value=-8.0, max_value=12.0, value=2.0, step=0.5, key="npsh_z",
            )
        with col_n2:
            L_suc = persistent_input(st.slider, "Suction pipe L [m]", min_value=1.0, max_value=40.0, value=8.0, step=1.0, key="npsh_L")
            D_suc_mm = persistent_input(st.slider, "Suction ID [mm]", min_value=25.0, max_value=200.0, value=pipe_d_mm, step=5.0, key="npsh_D")
        with col_n3:
            p_v_kpa = persistent_input(st.number_input,
                "Vapor pressure P_v [kPa]",
                min_value=0.0, max_value=50.0, value=pv_default / 1000.0, step=0.1, key="npsh_pv",
                help=f"Sidebar {fluid['name']} default is {pv_default/1000:.2f} kPa at 20 °C.",
            )
            npsh_r = persistent_input(st.number_input,
                "NPSH_R from pump curve [m]",
                min_value=0.5, max_value=12.0, value=3.0, step=0.1, key="npsh_r",
            )
        n_suc_elbows = persistent_input(st.number_input, "Suction 90° elbows", min_value=0, max_value=8, value=2, key="npsh_elb")
        q_m3s = flow_rate_m3h / 3600.0
        npsh = npsh_available(
            p_tank_abs=p_tank_kpa * 1000.0,
            z_surface=z_s,
            p_vapor=p_v_kpa * 1000.0,
            density=float(fluid["rho"]),
            viscosity=float(fluid["mu"]),
            suction_length=L_suc,
            suction_diameter=D_suc_mm / 1000.0,
            roughness=roughness_val,
            flow_rate_m3s=q_m3s,
            fittings_counts={"90° Standard Elbow": n_suc_elbows, "Pipe Inlet (Square edge)": 1},
        )
        margin = npsh["npsh_a"] - npsh_r
        col_a1, col_a2, col_a3 = st.columns(3)
        col_a1.metric("NPSH_A", f"{npsh['npsh_a']:.2f} m")
        col_a2.metric("NPSH_R", f"{npsh_r:.2f} m")
        col_a3.metric("Margin", f"{margin:.2f} m")
        if margin < 0:
            st.warning(
                "NPSH_A < NPSH_R: the eye pressure would fall below P_v. "
                "Raise the tank, shorten/enlarge the suction line, or cool the liquid (lower P_v)."
            )
        elif margin < 0.5:
            st.info("Margin under 0.5 m is thin. Plant practice usually keeps 0.5–1 m extra.")
        st.caption(
            f"Suction u = {npsh['velocity']:.2f} m/s · Re = {npsh['reynolds']:.0f} · "
            f"h_f = {npsh['h_f']:.2f} m · (P−P_v)/ρg = {npsh['static_term']:.2f} m. "
            "Lower the suction line into a lift (z < 0) and watch NPSH_A collapse."
        )
        render_what_to_notice(
            "The first three bars sum (approximately) to NPSH_A. NPSH_R is a pump property, not a pipe property."
        )
        fig_npsh = plot_npsh_station(npsh["npsh_a"], npsh_r, npsh)
        render_plot(fig_npsh, key="tab_pipe_flow-fig_npsh")
        render_predict(
            "npsh_predict",
            "Raising the tank surface (larger +z) at fixed Q and P_tank will…",
            ["leave NPSH_A unchanged", "increase NPSH_A one-for-one with z", "decrease NPSH_R"],
            "increase NPSH_A one-for-one with z",
            "NPSH_A = (P−P_v)/ρg + z − h_f. Flooded suction is the cheapest cavitation insurance.",
        )

    st.markdown("#### Laminar power-law Δp (same Q, D, L)")
    st.caption(
        "From Tab 6's Ostwald–de Waele lab. Only valid while Re_MR is laminar; "
        "Churchill/Moody stay Newtonian."
    )
    use_pl = persistent_input(st.checkbox, "Compare power-law Δp_major to Newtonian", value=False, key="pipe_pl_toggle")
    if use_pl:
        n_des = persistent_input(st.slider, "n (design)", min_value=0.3, max_value=1.5, value=0.7, step=0.05, key="pipe_pl_n")
        k_des = persistent_input(st.number_input,
            "K [Pa·sⁿ]", min_value=1e-4, max_value=20.0,
            value=max(float(fluid["mu"]), 0.01), format="%.4f", key="pipe_pl_K",
        )
        q_m3s = flow_rate_m3h / 3600.0
        dp_pl = power_law_pressure_drop(q_m3s, pipe_d_m / 2.0, pipe_len_m, k_des, n_des)
        st.metric(
            "Power-law |Δp_major|",
            f"{dp_pl/1000:.1f} kPa",
            delta=f"{(dp_pl - sys_res['delta_p_major'])/1000:.1f} kPa vs Newtonian major",
        )

    # -------------------------------------------------------------------------
    # PART 4: Hydraulic Diameter for Non-Circular Geometries
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 2.4 Non-Circular Ducts & Heat Exchanger Annuli")
    render_prose_and_latex(
        r"""
        For non-circular cross sections (e.g., shell-and-tube or double-pipe heat exchanger annuli,
        rectangular HVAC ducts), friction factor correlations are evaluated using the **hydraulic diameter**:
        $$D_H = \frac{4 \times \text{Cross-Sectional Area}}{\text{Wetted Perimeter}} = \frac{4 A}{P_w}$$
        Then $\mathrm{Re}_{D_H} = \rho u D_H/\mu$ and the same $f_F(\mathrm{Re}, \varepsilon/D_H)$ goes into $\Delta p_f = 4f_F(L/D_H)(\rho u^2/2)$.
        """
    )
    render_symbols(
        [
            (r"D_H", r"hydraulic diameter (m). $D_H=4A/P_w$. For a circle, $D_H=D$."),
            (r"A", "wetted cross-sectional area (m²). Not Churchill's $A_{\\mathrm{Ch}}$."),
            (r"P_w", "wetted perimeter (m)."),
            (r"D_o,\ D_i", r"annulus outer and inner diameters (m). Then $D_H=D_o-D_i$."),
            (r"a,\ b", r"rectangular duct width and height (m). $D_H=2ab/(a+b)$."),
        ]
    )

    col_hd1, col_hd2 = st.columns(2)
    with col_hd1:
        render_callout(
            """
            **Double-Pipe Heat Exchanger Annulus**

            Fluid flows in the annular gap between outer pipe inner diameter $D_o$ and inner pipe outer diameter $D_i$:
            - Area: $A = \\frac{\\pi}{4}(D_o^2 - D_i^2)$
            - Wetted perimeter: $P_w = \\pi(D_o + D_i)$
            - **Hydraulic diameter:** $D_H = \\frac{4 A}{P_w} = D_o - D_i$
            """
        )
    with col_hd2:
        render_callout(
            """
            **Rectangular Duct ($a \\times b$)**

            For duct width $a$ and height $b$:
            - Area: $A = a \\cdot b$
            - Wetted perimeter: $P_w = 2(a + b)$
            - **Hydraulic diameter:** $D_H = \\frac{4 a b}{2(a + b)} = \\frac{2 a b}{a + b}$
            - *For a square duct ($a = b$):* $D_H = a$.
            """
        )

    st.markdown("#### Hydraulic-diameter calculator")
    geom = persistent_input(st.radio, "Geometry", ["Annulus", "Rectangular duct"], horizontal=True, key="tab_pipe_flow_geometry")
    if geom == "Annulus":
        c1, c2 = st.columns(2)
        with c1:
            d_o = persistent_input(st.number_input, "Outer diameter D_o [m]", min_value=0.02, max_value=0.5, value=0.10, step=0.01, key="tab_pipe_flow_outer_diameter_d_o_m")
        with c2:
            d_i = persistent_input(st.number_input, "Inner diameter D_i [m]", min_value=0.01, max_value=0.49, value=0.06, step=0.01, key="tab_pipe_flow_inner_diameter_d_i_m")
        if d_i >= d_o:
            st.error("Need D_i < D_o.")
        else:
            d_h = hydraulic_diameter("annulus", d_o, d_i)
            st.metric("D_H = D_o − D_i", f"{d_h:.4f} m")
    else:
        c1, c2 = st.columns(2)
        with c1:
            a_duct = persistent_input(st.number_input, "Width a [m]", min_value=0.02, max_value=2.0, value=0.40, step=0.02, key="tab_pipe_flow_width_a_m")
        with c2:
            b_duct = persistent_input(st.number_input, "Height b [m]", min_value=0.02, max_value=2.0, value=0.20, step=0.02, key="tab_pipe_flow_height_b_m")
        d_h = hydraulic_diameter("rectangular", a_duct, b_duct)
        st.metric("D_H = 2ab/(a+b)", f"{d_h:.4f} m")

    # -------------------------------------------------------------------------
    # PART 5: Open channels — canals, ditches, culverts, rivers
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 2.5 Open Channels: Canals, Ditches and Flooding")
    render_objectives(
        [
            "Derive $\\tau_w = \\rho g R_h S_0$ and see it is the pipe force balance with the slope as the driving head.",
            "Use Manning's equation, and say honestly what its $n$ is and is not.",
            "Find the normal depth for a given discharge, and the critical depth that does not care about roughness.",
            "Read a Froude number, and decide whether a canal has enough freeboard to survive a flood.",
        ]
    )
    render_prose_and_latex(
        r"""
        Section 2.4 introduced $D_H = 4A/P_w$ as a way to reuse pipe correlations on odd
        cross-sections. An open channel is the case that explains *why the 4 is there*, and
        it is the most common flow in civil engineering: irrigation canals, roadside ditches,
        storm sewers running part-full, spillways and rivers.

        One thing changes from a pipe: there is a **free surface** at atmospheric pressure.
        A pipe is driven by a pressure gradient you impose with a pump. A canal has no pump
        and no pressure difference along it — the surface is at atmosphere everywhere. What
        drives it is **gravity acting down the bed slope**, and the flow arranges its own
        depth until friction exactly balances that pull.
        """
    )
    render_svg(diagram_canal_uniform_flow())
    render_prose_and_latex(
        r"""
        **Uniform (normal) flow, step by step.** Take a slice of channel of length $L$
        carrying constant depth $y$. Because the depth does not change, the flow does not
        accelerate, so the forces on the slice must sum to zero. The two hydrostatic end
        pressures are equal and cancel. That leaves the weight component along the slope
        against the shear on the wetted wall:
        $$\rho g A L \sin\theta = \tau_w P_w L$$
        For the small slopes of real channels $\sin\theta \approx \tan\theta = S_0$, so
        $$\tau_w = \rho g \frac{A}{P_w} S_0 = \rho g R_h S_0,
        \qquad R_h \equiv \frac{A}{P_w}$$
        Now compare with the pipe result of chapter 4, $\tau_w = (D/4)(-dp/dx)$. They are the
        same equation: $(-dp/dx)/(\rho g)$ has become the bed slope, and $D/4$ has become
        $R_h$. **That correspondence is the definition of hydraulic diameter**, and it is why
        $D_H = 4R_h$ rather than $2R_h$ or $R_h$ — the 4 exists exactly so that a circular
        pipe running full returns $D_H = D$.
        """
    )
    render_symbols(
        [
            (r"y", "flow depth (m), measured from the invert to the free surface."),
            (r"S_0", r"bed slope, dimensionless (m fall per m run). A 1:1000 canal has $S_0 = 0.001$."),
            (r"R_h", r"hydraulic radius $A/P_w$ (m). Note $D_H = 4R_h$, so $R_h$ is NOT a radius of anything."),
            (r"P_w", "wetted perimeter (m). The free surface is excluded — air exerts no useful shear."),
            (r"T", "top width at the free surface (m)."),
            (r"D_h", r"hydraulic depth $A/T$ (m). This, not $y$, is the length in the Froude number."),
            (r"n", r"Manning roughness, units s/m$^{1/3}$. Not dimensionless, and SI-only as tabulated here."),
        ]
    )
    render_svg(diagram_canal_section())

    st.markdown("#### 2.5.1 Two ways to close the friction, and what to make of both")
    render_prose_and_latex(
        r"""
        The force balance gives $\tau_w$ but not the velocity. Something must relate them.

        **Route A — Darcy–Weisbach, the one this course has been using.** Set the friction
        slope equal to the bed slope in uniform flow and use $D_H = 4R_h$:
        $$S_0 = 4f_F\frac{1}{D_H}\frac{V^2}{2g}
        \quad\Longrightarrow\quad V = \sqrt{\frac{2g D_H S_0}{4f_F}}$$
        with $f_F$ from Churchill exactly as in section 2.2 (civil texts write the same thing
        with $f_D = 4f_F$ and no leading 4). Dimensionally consistent, roughness in metres,
        valid in any unit system and at any Reynolds number. The solve is implicit because
        $f_F$ depends on $V$.

        **Route B — Manning–Strickler, the one civil practice actually uses.**
        $$V = \frac{1}{n}R_h^{2/3}S_0^{1/2},
        \qquad Q = VA = \frac{1}{n}A R_h^{2/3} S_0^{1/2}$$
        This is an empirical fit, not a derivation. Its $n$ carries units of s/m$^{1/3}$, so
        the tabulated values below are SI-only; imperial practice inserts a 1.486 conversion
        factor rather than changing $n$.

        **The bridge.** Equating the two gives
        $$n = R_h^{1/6}\sqrt{\frac{f_F}{2g}} \;=\; R_h^{1/6}\sqrt{\frac{f_D}{8g}}$$
        which is why Manning survives: in fully rough turbulent flow $f_F$ is nearly constant,
        so $n$ varies only as $R_h^{1/6}$ — a weak enough dependence to hide inside a
        tabulated constant. Manning is therefore reliable in rough, fully turbulent channels
        and unreliable in smooth or small ones, where $f_F$ still depends on Reynolds number.
        """
    )
    render_callout(
        """
        **What Manning's $n$ really is.** It is not a material property. It is a
        catch-all for wall roughness, cross-section irregularity, vegetation, bends,
        obstructions and sediment, fitted to field measurements. Published values carry
        roughly $\\pm 20\\%$ uncertainty even for a well-described channel, and a canal's
        $n$ changes seasonally as weeds grow. Since $Q \\propto 1/n$, that uncertainty passes
        straight into the answer — so a canal designed with no margin for a rising $n$ is a
        canal designed to flood in late summer. This is the dominant error in almost every
        open-channel calculation; the arithmetic is never the problem.
        """,
        title="The honest caveat about n",
    )

    st.markdown("#### 2.5.2 Normal depth, critical depth, and which one controls")
    render_prose_and_latex(
        r"""
        **Normal depth** $y_n$ is the depth at which Manning's discharge equals the actual
        discharge — the depth the channel settles at, far from any structure. Since $Q(y)$
        increases monotonically, a bracketed root find always converges. Note the exponents:
        for a wide channel $Q \propto y^{5/3}$ but $Q \propto S_0^{1/2}$. **Quadrupling the
        slope only doubles the capacity, while a 50% deeper channel roughly doubles it.**
        That asymmetry is why canals are widened and deepened rather than steepened — and
        steepening is limited anyway by scour.

        **Critical depth** $y_c$ is where specific energy $E = y + V^2/2g$ is a minimum:
        $$\frac{dE}{dy} = 0 \quad\Longrightarrow\quad \frac{Q^2 T}{gA^3} = 1
        \quad\Longleftrightarrow\quad \mathrm{Fr} \equiv \frac{V}{\sqrt{gD_h}} = 1$$
        For a rectangular channel this collapses to $y_c = (q^2/g)^{1/3}$ with $q = Q/b$.
        **Critical depth depends only on geometry and discharge — not on roughness or
        slope.** That independence is exactly what makes a weir, flume or spillway crest
        usable as a flow meter: force the flow through critical and the depth alone tells
        you $Q$, whatever the channel is made of.

        **The Froude number is a wave-speed comparison.** A shallow-water surface wave travels
        at $\sqrt{gD_h}$ relative to the water. If $\mathrm{Fr} < 1$ (**subcritical**,
        $y_n > y_c$), waves outrun the flow upstream: a downstream gate or culvert can raise
        the water level here, so *control is from downstream*. If $\mathrm{Fr} > 1$
        (**supercritical**, $y_n < y_c$), nothing propagates upstream, control is from
        upstream, and any return to subcritical happens abruptly through a **hydraulic jump**
        that dissipates energy violently. Stilling basins below spillways exist to force that
        jump to happen where the concrete can take it.
        """
    )
    render_derivation(
        r"critical depth: differentiating the specific energy, with one geometric fact",
        [
            (
                "Specific energy is the energy the flow has, measured from the bed",
                r"""
                At a section, each kilogram carries pressure head (which for a free surface at
                depth $y$ is just $y$, by hydrostatics) plus velocity head. Writing
                $V=Q/A(y)$ and holding $Q$ fixed:
                $$E(y)=y+\frac{V^{2}}{2g}=y+\frac{Q^{2}}{2gA(y)^{2}}$$
                The two terms pull in opposite directions as the depth changes: deep slow flow
                is nearly all potential ($E\to y$), shallow fast flow is nearly all kinetic
                ($E\to\infty$ as $A\to0$). Something in between must be a minimum.
                """,
            ),
            (
                r"The geometric fact: $dA/dy=T$",
                r"""
                Raise the surface by $dy$ in a channel of any shape. The area gained is a thin
                strip of height $dy$ spanning the **top width** $T$:
                $$dA=T\,dy\;\Longrightarrow\;\frac{dA}{dy}=T$$
                This one line is what lets the derivation handle trapezoids, circles and
                natural river sections without new algebra for each.
                """,
            ),
            (
                "Differentiate and set to zero",
                r"""
                $$\frac{dE}{dy}=1-\frac{Q^{2}}{gA^{3}}\frac{dA}{dy}
                =1-\frac{Q^{2}T}{gA^{3}}
                \;\Longrightarrow\;\boxed{\frac{Q^{2}T}{gA^{3}}=1\ \text{at }y=y_c}$$
                """,
            ),
            (
                "Recognise the group as a Froude number",
                r"""
                Divide numerator and denominator by $A^{2}$ and use the hydraulic depth
                $D_h=A/T$:
                $$\frac{Q^{2}T}{gA^{3}}=\frac{(Q/A)^{2}}{g(A/T)}=\frac{V^{2}}{gD_h}=\mathrm{Fr}^{2}$$
                So minimum specific energy and $\mathrm{Fr}=1$ are the *same condition*, not
                two facts to memorise. For a rectangular channel, $A=by$, $T=b$ and $q=Q/b$
                reduce it to $y_c=(q^{2}/g)^{1/3}$.
                """,
            ),
            (
                "Why the same number is also a wave speed",
                r"""
                A long surface wave in shallow water travels at $c=\sqrt{gD_h}$ relative to the
                water, so $\mathrm{Fr}=V/c$ compares how fast the flow moves with how fast news
                can travel through it — precisely the role $M=u/a$ plays in Tab 12. Below
                critical, waves outrun the flow and a downstream gate controls the depth here;
                above critical, nothing reaches upstream, and the return to subcritical must
                happen discontinuously in a hydraulic jump. The hydraulic jump is the free-
                surface analogue of a shock wave, down to the fact that momentum is conserved
                across it while energy is not.
                """,
            ),
            (
                "Why roughness is missing, and why that is useful",
                r"""
                Nothing in this derivation mentioned $n$, $f_F$ or $S_0$ — only $Q$ and the
                cross-section. Critical depth is therefore a property of geometry and discharge
                alone. That is exactly what makes a weir or flume a flow meter: force the flow
                through critical, measure one depth, and read $Q$ without knowing anything
                about how rough the channel is.
                """,
            ),
        ],
    )

    render_predict(
        "canal_predict_slope",
        "An earth canal carries 8 m³/s. Regrading doubles its bed slope. Its capacity at the same depth rises by about…",
        ["100%", "41%", "26%"],
        "41%",
        "Q ∝ S₀^(1/2), so doubling the slope multiplies capacity by √2 ≈ 1.41. Slope is a "
        "weak lever; cross-section is a strong one. Steeper also means faster, which risks "
        "scouring the bed.",
    )

    st.markdown("#### 2.5.3 Worked example: an irrigation canal")
    demo = channel_state(**CANAL_DEMO_DEFAULTS)
    weedy = channel_state(**{**CANAL_DEMO_DEFAULTS, "manning_n": MANNING_N["Earth canal, some weeds and stones"]})
    choked = channel_state(**{**CANAL_DEMO_DEFAULTS, "manning_n": MANNING_N["Natural stream, clean and winding"]})
    yn, A, Pw, Rh = demo["normal_depth"], demo["area"], demo["wetted_perimeter"], demo["hydraulic_radius"]
    V, Fr, yc = demo["velocity"], demo["froude"], demo["critical_depth"]
    T, Dh = demo["top_width"], demo["hydraulic_depth"]
    fb, fb_req = demo["freeboard"], demo["required_freeboard"]
    Qb, margin = demo["bank_full_capacity"], demo["capacity_margin"]
    tau = demo["bed_shear_stress"]
    n0 = CANAL_DEMO_DEFAULTS["manning_n"]
    n1, n2 = weedy["manning_n"], choked["manning_n"]
    render_prose_and_latex(
        rf"""
        **Brief.** Carry a design flow of $Q = {CANAL_DEMO_DEFAULTS['discharge']:.0f}\ \mathrm{{m^3/s}}$ in an unlined earth canal.
        Trial section: bottom width $b = {CANAL_DEMO_DEFAULTS['bottom_width']:.0f}\ \mathrm{{m}}$, side slopes 1.5H:1V ($z = {CANAL_DEMO_DEFAULTS['side_slope']}$,
        near the stable angle for compacted earth), bed slope $S_0 = {CANAL_DEMO_DEFAULTS['bed_slope']}$, Manning
        $n = {n0}$ for a clean straight earth channel, banks built to {CANAL_DEMO_DEFAULTS['bank_depth']} m above the
        invert. These are the calculator's defaults below, so every number here is
        **recomputed from those defaults**, not typed.

        **Work it by hand, in this order.**

        1. **Geometry at a trial depth $y$.** $A = y(b+zy)$,
           $P_w = b + 2y\sqrt{{1+z^2}}$, $R_h = A/P_w$. At $y = {yn:.3f}$ m:
           $A = {A:.2f}\ \mathrm{{m^2}}$,
           $P_w = {Pw:.2f}\ \mathrm{{m}}$,
           $R_h = {Rh:.3f}\ \mathrm{{m}}$.
        2. **Manning.** $V = {V:.2f}\ \mathrm{{m/s}}$,
           so $Q = {V:.2f} \times {A:.2f} = {CANAL_DEMO_DEFAULTS['discharge']:.1f}\ \mathrm{{m^3/s}}$. The trial depth was right. In
           practice you iterate on $y$ — which is exactly what the solver below does, with
           a bracketed root find that always converges because $Q(y)$ is monotonic.
        3. **Check the velocity against scour and siltation.** Unlined earth canals are kept
           between roughly 0.6 and 1.5 m/s: slower and suspended sediment settles out and
           silts the channel up, faster and the bed erodes. {V:.2f} m/s sits comfortably in the
           middle. **This check, not the head loss, usually sets the design** — which is the
           sharpest difference between canal design and pipe design.
        4. **Check the regime.** $T = {T:.2f}\ \mathrm{{m}}$, $D_h = A/T = {Dh:.3f}\ \mathrm{{m}}$,
           $\mathrm{{Fr}} = {Fr:.2f}$. Subcritical, as an irrigation
           canal should be — supercritical flow over erodible earth is a scour problem
           waiting to happen. Critical depth is {yc:.2f} m, well below the normal depth of
           {yn:.2f} m, which says the same thing a second way.
        5. **Check the freeboard.** Bank at {CANAL_DEMO_DEFAULTS['bank_depth']} m, water at {yn:.2f} m, so freeboard is {fb:.2f} m
           against a requirement of about $\max(0.3\ \mathrm{{m}},\ 0.2y_n) = {fb_req:.2f}\ \mathrm{{m}}$.
           Ample.
        6. **Check the flood case.** Filled to the top of bank at {CANAL_DEMO_DEFAULTS['bank_depth']} m the same section
           would carry ${Qb:.1f}\ \mathrm{{m^3/s}}$ — {margin:.1f} times the design flow. **That margin,
           not the design point, is the answer to "will it flood".**
        7. **Check the bed shear.** $\tau_w = \rho g R_h S_0 = {tau:.1f}\ \mathrm{{Pa}}$. Compare against the permissible tractive stress
           for the bed material. Chow's table gives roughly 1.3 Pa for noncolloidal fine
           sand and about 12 Pa for stiff colloidal clay, so sand would scour badly here
           while compacted clay would hold comfortably.
        """
    )
    render_callout(
        rf"""
        **And now the failure mode.** Let the weeds grow so $n$ rises from {n0} to {n1:.3f} —
        entirely routine for an unmaintained earth canal by late summer, and only one row
        down the material list in the calculator below. The normal depth for the *same*
        {CANAL_DEMO_DEFAULTS['discharge']:.0f} m³/s rises from {yn:.2f} m to {weedy['normal_depth']:.2f} m, and the freeboard falls from {fb:.2f} m to {weedy['freeboard']:.2f} m.
        Nothing about the canal changed except its roughness. Let it go further, to the
        {n2:.3f} of a weed-choked winding channel, and the depth reaches {choked['normal_depth']:.2f} m. Now put a
        storm event on top of a weedy channel and the two effects compound. Real canal
        failures are almost never a wrong Manning calculation; they are a right calculation
        done with last year's $n$.
        """,
        title="Why maintenance is a hydraulic parameter",
    )

    st.markdown("#### 2.5.4 Canal and channel calculator")
    ch1, ch2, ch3 = st.columns(3)
    ch_q = persistent_input(ch1.number_input, "Design discharge Q [m³/s]", min_value=0.01, max_value=5000.0,
                            value=CANAL_DEMO_DEFAULTS["discharge"], step=0.5, key="canal_q")
    ch_b = persistent_input(ch1.number_input, "Bottom width b [m]", min_value=0.0, max_value=200.0,
                            value=CANAL_DEMO_DEFAULTS["bottom_width"], step=0.5, key="canal_b")
    ch_z = persistent_input(ch2.number_input, "Side slope z (horizontal per 1 vertical)", min_value=0.0,
                            max_value=6.0, value=CANAL_DEMO_DEFAULTS["side_slope"], step=0.25, key="canal_z")
    ch_slope = persistent_input(ch2.number_input, "Bed slope S₀ [m/m]", min_value=1e-6, max_value=0.2,
                                value=CANAL_DEMO_DEFAULTS["bed_slope"], step=0.0002, format="%.5f", key="canal_s")
    ch_material = persistent_input(ch3.selectbox, "Channel surface", list(MANNING_N.keys()), index=4, key="canal_mat")
    ch_bank = persistent_input(ch3.number_input, "Bank height above invert [m]", min_value=0.05, max_value=60.0,
                               value=CANAL_DEMO_DEFAULTS["bank_depth"], step=0.1, key="canal_bank")

    if ch_b == 0.0 and ch_z == 0.0:
        st.error("A channel needs a bottom width, a side slope, or both.")
    else:
        try:
            state = channel_state(
                discharge=ch_q, bottom_width=ch_b, side_slope=ch_z,
                manning_n=MANNING_N[ch_material], bed_slope=ch_slope,
                bank_depth=ch_bank, roughness=CHANNEL_ROUGHNESS[ch_material],
            )
        except ValueError as exc:
            st.error(str(exc))
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Normal depth y_n", f"{state['normal_depth']:.3f} m")
            c2.metric("Mean velocity V", f"{state['velocity']:.3f} m/s")
            c3.metric("Froude number", f"{state['froude']:.3f}", state["regime"])
            c4.metric("Critical depth y_c", f"{state['critical_depth']:.3f} m")

            d1, d2, d3, d4 = st.columns(4)
            d1.metric("Hydraulic radius R_h", f"{state['hydraulic_radius']:.3f} m")
            d2.metric("D_H = 4R_h", f"{state['hydraulic_diameter']:.3f} m")
            d3.metric("Bank-full capacity", f"{state['bank_full_capacity']:.2f} m³/s")
            d4.metric("Capacity margin", f"{state['capacity_margin']:.2f}×")

            if state["overtops"]:
                st.error(
                    f"**Overtopping.** The normal depth {state['normal_depth']:.2f} m exceeds "
                    f"the bank height {ch_bank:.2f} m. This section cannot carry "
                    f"{ch_q:.2f} m³/s within its banks — it floods. Bank-full capacity is "
                    f"{state['bank_full_capacity']:.2f} m³/s. Widen the section, deepen it, "
                    "raise the banks, or reduce the flow."
                )
            elif not state["freeboard_adequate"]:
                st.warning(
                    f"**Freeboard {state['freeboard']:.2f} m is below the customary minimum of "
                    f"{state['required_freeboard']:.2f} m** (the larger of 0.3 m and 0.2 y_n). "
                    "The canal does not overtop at the design flow, but there is no allowance "
                    "for wind waves, superelevation on bends, sediment build-up, settlement, "
                    "or a rising Manning n as vegetation establishes."
                )
            else:
                st.success(
                    f"Freeboard {state['freeboard']:.2f} m against a customary minimum of "
                    f"{state['required_freeboard']:.2f} m, and bank-full capacity is "
                    f"{state['capacity_margin']:.2f}× the design flow."
                )

            if state["velocity"] < 0.6:
                st.info(
                    f"Velocity {state['velocity']:.2f} m/s is below about 0.6 m/s. Suspended "
                    "sediment will settle out, and the channel will silt up and lose capacity."
                )
            elif state["velocity"] > 1.5 and "concrete" not in ch_material.lower() and "Glass" not in ch_material:
                st.info(
                    f"Velocity {state['velocity']:.2f} m/s exceeds about 1.5 m/s, the usual "
                    "non-scouring limit for unlined earth. Expect bed erosion unless the "
                    "channel is lined or armoured."
                )

            st.caption(
                f"Bed shear stress τ_w = ρgR_hS₀ = {state['bed_shear_stress']:.2f} Pa · "
                f"shear velocity u* = {state['shear_velocity']:.4f} m/s · "
                f"wetted perimeter {state['wetted_perimeter']:.2f} m · "
                f"top width {state['top_width']:.2f} m · "
                f"flow area {state['area']:.2f} m². "
                f"Manning n = {MANNING_N[ch_material]:.3f} s/m^(1/3)."
            )

            darcy = state["darcy"]
            if darcy is not None:
                st.caption(
                    f"**Darcy cross-check at the same depth:** with ε = "
                    f"{CHANNEL_ROUGHNESS[ch_material] * 1000:.0f} mm, Churchill gives "
                    f"f_F = {darcy['f_fanning']:.4f} (f_D = {darcy['f_darcy']:.4f}) at Re = {darcy['reynolds']:.2e}, hence "
                    f"Q = {darcy['discharge']:.2f} m³/s versus Manning's {ch_q:.2f} m³/s. "
                    f"The Darcy route implies n = {darcy['equivalent_manning_n']:.4f} against "
                    f"the tabulated {MANNING_N[ch_material]:.3f}. Disagreement of this size is "
                    "normal and honest: the two conventions carry independent empirical "
                    "roughness estimates, and neither is more 'exact' than the other. It is a "
                    "useful measure of how much the roughness input really controls the answer."
                )

            render_what_to_notice(
                "Move the bed slope and watch the normal depth fall only slowly — the S₀^(1/2) "
                "in Manning is a weak lever. Then move the roughness one row down the list and "
                "watch the depth jump. Roughness, not slope, is what floods a canal."
            )
            fig_canal = plot_open_channel_rating(
                rating_curve(ch_b, ch_z, MANNING_N[ch_material], ch_slope,
                             max_depth=max(ch_bank * 1.25, state["normal_depth"] * 1.4)),
                state,
            )
            render_plot(fig_canal, "canal-rating")
            st.caption(
                "Left: the rating curve, with the design point, the top of bank and the "
                "critical depth. Where the design point sits below the bank line, the canal "
                "contains the flow. Right: Froude number against depth — a channel can cross "
                "between regimes as the flow changes, and the crossing is where hydraulic "
                "jumps live."
            )

    render_self_check(
        "canal_self_check_control",
        "A canal runs subcritical (Fr = 0.34). A new culvert is built 500 m downstream and "
        "partially blocks the flow. What happens at your section?",
        [
            "Nothing — the disturbance travels downstream only",
            "The water level rises, because subcritical flow is controlled from downstream",
            "The flow becomes supercritical",
        ],
        "The water level rises, because subcritical flow is controlled from downstream",
        "At Fr < 1 surface waves travel faster than the flow, so they propagate upstream and "
        "a downstream restriction backs water up. This is the backwater curve, and it is why "
        "subcritical channels must be surveyed downstream before their depth can be predicted. "
        "In supercritical flow nothing propagates upstream and the culvert would not be felt "
        "at all until a hydraulic jump formed.",
    )
    st.caption(
        "Model limits: steady uniform (normal) flow in a straight prismatic channel, rigid "
        "boundaries, no sediment transport, no bends, structures or lateral inflow. Backwater "
        "profiles, hydraulic jumps and unsteady flood routing are separate calculations and "
        "are not solved here. Manning's n values follow Chow (1959) and are engineering "
        "estimates with roughly ±20% spread."
    )
