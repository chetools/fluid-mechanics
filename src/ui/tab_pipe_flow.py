"""UI module for Pipe Flow and Chemical Engineering piping applications."""

import streamlit as st
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
    CHANNEL_ROUGHNESS,
    MANNING_N,
    channel_state,
    rating_curve,
)
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
            "Never confuse Darcy $f_D$ with Fanning $f_F = f_D/4$.",
            "Read a Moody operating point and see $f(Re, \\varepsilon/D)$.",
            "Write the mechanical energy equation, then size a pump from $\\Delta p$ and $\\eta$.",
            "Compute $D_H$ for an annulus or duct and reuse the same $f$.",
            "Compute $\\mathrm{NPSH}_A$ at a pump suction and compare it to $\\mathrm{NPSH}_R$.",
            "Check that $L > L_e$ before trusting fully developed Darcy.",
        ]
    )

    # -------------------------------------------------------------------------
    # PART 1: The Darcy-Weisbach Equation & Friction Factors
    # -------------------------------------------------------------------------
    st.markdown("### 2.1 Frictional Head Loss: Darcy vs. Fanning")
    st.markdown(
        """
        The fundamental equation for frictional pressure drop in a circular pipe is the
        **Darcy–Weisbach equation**:
        """
    )

    render_latex(r"\Delta p_f = f_D \frac{L}{D} \left(\frac{1}{2}\rho u^2\right)")
    render_latex(r"h_f = \frac{\Delta p_f}{\rho g} = f_D \frac{L}{D} \frac{u^2}{2g}")
    render_latex(r"f_F = \frac{\tau_{\mathrm{wall}}}{\frac{1}{2}\rho u^2} = \frac{f_D}{4}")
    render_symbols(
        [
            (r"\Delta p_f", "frictional pressure drop along the pipe (Pa)."),
            (r"f_D", "Darcy friction factor (dimensionless). Moody charts plot this. Laminar circular pipe: $f_D=64/\\mathrm{Re}$."),
            (r"f_F", r"Fanning friction factor. ChemE texts (BSL, Perry) often use this. $f_F=f_D/4$; laminar: $f_F=16/\mathrm{Re}$."),
            (r"L", "pipe length (m)."),
            (r"D", "inner diameter (m)."),
            (r"\rho", "mass density (kg/m³). Sidebar fluid."),
            (r"u", r"area-mean speed $\bar{u}=Q/A$ (m/s)."),
            (r"h_f", r"frictional head loss (m). $h_f=\Delta p_f/(\rho g)$."),
            (r"\tau_{\mathrm{wall}}", r"wall shear stress (Pa). $f_F=\tau_w/(\tfrac12\rho u^2)$."),
            (r"g", r"gravitational acceleration, $9.81\,\mathrm{m/s^2}$."),
        ]
    )

    with st.expander("⚠️ Chemical Engineering Nomenclature Alert: Darcy vs. Fanning Friction Factors", expanded=False):
        st.markdown(
            r"""
            One of the most frequent traps in chemical engineering calculations is the confusion between
            **Darcy ($f_D$)** and **Fanning ($f_F$)** friction factors:
            * **Darcy friction factor ($f_D$)**: Used predominantly in mechanical and civil engineering (and in the standard Moody diagram).
              * Laminar flow: $f_D = \frac{64}{Re}$.
            * **Fanning friction factor ($f_F$)**: Used extensively in chemical engineering textbooks (e.g., *Bird, Stewart, & Lightfoot (BSL)*, *Perry's Chemical Engineers' Handbook*).
              * Laminar flow: $f_F = \frac{16}{Re}$.
              * Relation: $f_D = 4 f_F$.
            * Always check whether your design equation has a factor of 4 or not!

            The Chilton–Colburn analogy in Tab 4 is $j_H = j_D = f_F/2 = f_D/8$, **not** $f_D/2$.
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
        Circular pipe: $\alpha=2$ exactly if laminar; $\alpha\approx 1.05$ if turbulent (Tab 4).
        $h_{\mathrm{shaft}}$ is the pump head this lab solves for.
        $h_f$ is Darcy–Weisbach; $h_{\mathrm{minor}}=\sum K_L\,u^2/(2g)$.
        For two large tanks, $u_1\approx u_2\approx 0$ and an outlet $K_L=1$ already dumps
        the exit kinetic head — do not add $\alpha u^2/2g$ on top of that $K_L$.
        """
    )

    # -------------------------------------------------------------------------
    # PART 2: The Interactive Moody Chart
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 2.2 The Moody Diagram & Churchill (1977) Correlation")
    st.markdown(
        r"""
        In 1944, Lewis Ferry Moody plotted the **Darcy** friction factor as a function of Reynolds number
        and relative roughness $\varepsilon/D$.

        * **Laminar Zone ($\mathrm{Re} < 2300$, circular pipe):** Independent of roughness! $f_D = 64/\mathrm{Re}$.
        * **Critical Zone ($2000 < \mathrm{Re} < 4000$):** Flow is intermittently turbulent; highly sensitive.
        * **Wholly Turbulent Rough Pipe Zone:** Viscous sublayer is thinner than wall asperities; $f_D$ becomes independent of $\mathrm{Re}$ and depends solely on $\varepsilon/D$.
        """
    )
    st.markdown(
        r"""
        The live diamond uses **Churchill's 1977 explicit Darcy formula** — one expression
        from laminar through transition into fully rough turbulence, so we never switch
        correlations by hand. Colebrook–White is the implicit turbulent cousin
        (a root find for $f_D$); Churchill recovers it without iterating.
        S. W. Churchill, *Chem. Eng.* **84**(24) 91–92 (1977).
        """
    )
    render_latex(
        r"A_{\mathrm{Ch}} = \left[2.457\ln\frac{1}{(7/\mathrm{Re})^{0.9}+0.27\,\varepsilon/D}\right]^{16}"
    )
    render_latex(r"B_{\mathrm{Ch}} = \left(\frac{37530}{\mathrm{Re}}\right)^{16}")
    render_latex(
        r"f_D = 8\left[\left(\frac{8}{\mathrm{Re}}\right)^{12} + (A_{\mathrm{Ch}}+B_{\mathrm{Ch}})^{-3/2}\right]^{1/12}"
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
                r"laminar weight. When $\mathrm{Re}\ll 2300$ this term dominates and $f_D\to 64/\mathrm{Re}$.",
            ),
            (
                r"B_{\mathrm{Ch}}",
                r"transition weight. Large near $\mathrm{Re}\sim 10^3$, then vanishes.",
            ),
            (r"f_D", "Darcy friction factor returned by this formula and plotted on the Moody chart."),
        ]
    )
    render_predict(
        "moody_predict",
        "In fully rough turbulent flow, increasing Re at fixed ε/D will make f_D…",
        ["keep falling as 64/Re", "become almost independent of Re", "jump discontinuously to zero"],
        "become almost independent of Re",
        "The wholly rough regime is a horizontal Moody line: skin friction is set by ε/D, not viscosity.",
    )

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        re_pipe_input = st.select_slider(
            "Operating Reynolds Number Re",
            options=[800, 1500, 2100, 3000, 5000, 10000, 50000, 100000, 500000, 1000000, 10000000],
            value=50000
        )
    with col_m2:
        eps_d_input = st.select_slider(
            "Relative Pipe Roughness ε/D",
            options=[0.0, 1e-5, 5e-5, 1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 2e-2, 5e-2],
            value=1e-3,
            format_func=lambda x: "Smooth (0.0)" if x == 0.0 else f"{x:.0e}"
        )

    f_op = friction_factor_churchill(re_pipe_input, eps_d_input)

    col_k1, col_k2, col_k3 = st.columns(3)
    col_k1.metric("Operating Re", f"{re_pipe_input:,.0f}")
    col_k2.metric("Darcy Friction Factor f_D", f"{f_op:.4f}")
    col_k3.metric("Fanning Friction Factor f_F = f_D/4", f"{f_op/4.0:.4f}")

    render_what_to_notice("The diamond is (Re, f_D). Laminar is 64/Re; the shaded band is the pipe transition, not a law for cavities.")
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
        flow_rate_m3h = st.slider("Flow Rate Q [m³/h]", min_value=1.0, max_value=100.0, value=25.0, step=1.0)
        pipe_d_mm = st.slider("Pipe Inner Diameter [mm]", min_value=25.0, max_value=200.0, value=75.0, step=5.0)
    with col_pipe2:
        pipe_len_m = st.slider("Pipe Length L [m]", min_value=5.0, max_value=250.0, value=60.0, step=5.0)
        elevation_m = st.slider("Static Elevation Gain Δz [m]", min_value=0.0, max_value=50.0, value=12.0, step=1.0)
    with col_pipe3:
        pipe_mat = st.selectbox("Commercial Pipe Material", options=list(PIPE_ROUGHNESS.keys()), index=0)
        pump_eff = st.slider("Pump Mechanical Efficiency η", min_value=0.40, max_value=0.90, value=0.72, step=0.02)

    st.markdown("#### Fittings & Valves Inventory (Minor Losses)")
    col_fit1, col_fit2, col_fit3 = st.columns(3)
    with col_fit1:
        n_elbows = st.number_input("90° Standard Elbows", min_value=0, max_value=20, value=4)
        n_tees = st.number_input("Tees (Flow through branch)", min_value=0, max_value=10, value=1)
    with col_fit2:
        n_gate_valves = st.number_input("Gate Valves (Open)", min_value=0, max_value=10, value=2)
        n_globe_valves = st.number_input("Globe Valves (Open)", min_value=0, max_value=10, value=1)
    with col_fit3:
        n_check_valves = st.number_input("Check Valves (Swing type)", min_value=0, max_value=5, value=1)
        elec_cost_rate = st.number_input("Electricity Cost [$/kWh]", min_value=0.05, max_value=0.40, value=0.12, step=0.01)

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
    alpha = 2.0 if re_line < 2300 else (1.3 if re_line < 4000 else 1.05)
    g = 9.81
    kinetic_head = alpha * sys_res["velocity"] ** 2 / (2.0 * g)

    col_pk1, col_pk2, col_pk3, col_pk4 = st.columns(4)
    col_pk1.metric("Flow Velocity", format_quantity(float(sys_res["velocity"]), "velocity"), help="Economic range is typically 1.0 to 2.5 m/s")
    col_pk2.metric("Total Pressure Drop", f"{sys_res['delta_p_total']/1000.0:.1f} kPa")
    col_pk3.metric("Required Pump Power", f"{sys_res['p_shaft_kw']:.2f} kW ({sys_res['p_shaft_hp']:.1f} HP)")
    col_pk4.metric("Annual Power Cost", f"${sys_res['annual_cost']:,.0f} / yr")

    st.caption(
        f"Re_D = {re_line:,.0f} ({fluid['name']}) · f_D = {sys_res['f_darcy']:.4f} · "
        f"f_F = {sys_res['f_fanning']:.4f} · α = {alpha:.2f} → α u²/2g = {kinetic_head:.2f} m "
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
            f"exceeds this pipe L = {pipe_len_m:.0f} m. Darcy–Weisbach assumes fully developed flow."
        )
    else:
        st.caption(
            f"Entrance length L_e ≈ {ent['L_e']:.1f} m = {ent['L_e_over_D']:.1f} D ({ent['regime']}). "
            "Laminar: 0.06 Re. Turbulent: 4.4 Re^{1/6} (White). Fully developed Darcy applies after L_e."
        )

    render_what_to_notice("Bars split major (skin), minor (K_L), and static lift. Switch the sidebar to Glycerin: Re collapses, f_D → 64/Re, power jumps.")
    fig_head = plot_cheme_head_loss_breakdown(sys_res)
    render_plot(fig_head, key="tab_pipe_flow-fig_head")

    render_self_check(
        "pipe_self_check_fanning",
        "A ChemE handbook gives f = 16/Re in laminar flow. Which friction factor is that?",
        ["Darcy f_D", "Fanning f_F", "Fanning times 4"],
        "Fanning f_F",
        "f_F = 16/Re and f_D = 64/Re = 4 f_F. Moody charts almost always plot Darcy.",
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
    render_svg(diagram_npsh())
    if fluid.get("kind") == "gas":
        st.info("NPSH is a liquid-vapor limit. It is not defined for the sidebar gas.")
    else:
        pv_default = float(fluid["vapor_pressure"]) if fluid.get("vapor_pressure") is not None else 2338.8
        col_n1, col_n2, col_n3 = st.columns(3)
        with col_n1:
            p_tank_kpa = st.number_input(
                "Tank pressure (absolute) [kPa]",
                min_value=20.0, max_value=300.0, value=101.3, step=1.0, key="npsh_ptank",
            )
            z_s = st.slider(
                "z surface above pump [m] (+ flooded)",
                min_value=-8.0, max_value=12.0, value=2.0, step=0.5, key="npsh_z",
            )
        with col_n2:
            L_suc = st.slider("Suction pipe L [m]", min_value=1.0, max_value=40.0, value=8.0, step=1.0, key="npsh_L")
            D_suc_mm = st.slider("Suction ID [mm]", min_value=25.0, max_value=200.0, value=pipe_d_mm, step=5.0, key="npsh_D")
        with col_n3:
            p_v_kpa = st.number_input(
                "Vapor pressure P_v [kPa]",
                min_value=0.0, max_value=50.0, value=pv_default / 1000.0, step=0.1, key="npsh_pv",
                help=f"Sidebar {fluid['name']} default is {pv_default/1000:.2f} kPa at 20 °C.",
            )
            npsh_r = st.number_input(
                "NPSH_R from pump curve [m]",
                min_value=0.5, max_value=12.0, value=3.0, step=0.1, key="npsh_r",
            )
        n_suc_elbows = st.number_input("Suction 90° elbows", min_value=0, max_value=8, value=2, key="npsh_elb")
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
    use_pl = st.checkbox("Compare power-law Δp_major to Newtonian", value=False, key="pipe_pl_toggle")
    if use_pl:
        n_des = st.slider("n (design)", min_value=0.3, max_value=1.5, value=0.7, step=0.05, key="pipe_pl_n")
        k_des = st.number_input(
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
        Then $\mathrm{Re}_{D_H} = \rho u D_H/\mu$ and the same $f_D(\mathrm{Re}, \varepsilon/D_H)$ goes into Darcy–Weisbach.
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
    geom = st.radio("Geometry", ["Annulus", "Rectangular duct"], horizontal=True)
    if geom == "Annulus":
        c1, c2 = st.columns(2)
        with c1:
            d_o = st.number_input("Outer diameter D_o [m]", min_value=0.02, max_value=0.5, value=0.10, step=0.01)
        with c2:
            d_i = st.number_input("Inner diameter D_i [m]", min_value=0.01, max_value=0.49, value=0.06, step=0.01)
        if d_i >= d_o:
            st.error("Need D_i < D_o.")
        else:
            d_h = hydraulic_diameter("annulus", d_o, d_i)
            st.metric("D_H = D_o − D_i", f"{d_h:.4f} m")
    else:
        c1, c2 = st.columns(2)
        with c1:
            a_duct = st.number_input("Width a [m]", min_value=0.02, max_value=2.0, value=0.40, step=0.02)
        with c2:
            b_duct = st.number_input("Height b [m]", min_value=0.02, max_value=2.0, value=0.20, step=0.02)
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
        $$S_0 = f_D\frac{1}{D_H}\frac{V^2}{2g}
        \quad\Longrightarrow\quad V = \sqrt{\frac{2g D_H S_0}{f_D}}$$
        with $f_D$ from Churchill exactly as in section 2.2. Dimensionally consistent,
        roughness in metres, valid in any unit system and at any Reynolds number. The solve
        is implicit because $f_D$ depends on $V$.

        **Route B — Manning–Strickler, the one civil practice actually uses.**
        $$V = \frac{1}{n}R_h^{2/3}S_0^{1/2},
        \qquad Q = VA = \frac{1}{n}A R_h^{2/3} S_0^{1/2}$$
        This is an empirical fit, not a derivation. Its $n$ carries units of s/m$^{1/3}$, so
        the tabulated values below are SI-only; imperial practice inserts a 1.486 conversion
        factor rather than changing $n$.

        **The bridge.** Equating the two gives
        $$n = R_h^{1/6}\sqrt{\frac{f_D}{8g}}$$
        which is why Manning survives: in fully rough turbulent flow $f_D$ is nearly constant,
        so $n$ varies only as $R_h^{1/6}$ — a weak enough dependence to hide inside a
        tabulated constant. Manning is therefore reliable in rough, fully turbulent channels
        and unreliable in smooth or small ones, where $f_D$ still depends on Reynolds number.
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
    render_prose_and_latex(
        r"""
        **Brief.** Carry a design flow of $Q = 8\ \mathrm{m^3/s}$ in an unlined earth canal.
        Trial section: bottom width $b = 3\ \mathrm{m}$, side slopes 1.5H:1V ($z = 1.5$,
        near the stable angle for compacted earth), bed slope $S_0 = 0.0008$, Manning
        $n = 0.022$ for a clean straight earth channel, banks built to 2.5 m above the
        invert. These are the calculator's defaults below, so every number here can be
        reproduced without changing an input.

        **Work it by hand, in this order.**

        1. **Geometry at a trial depth $y$.** $A = y(b+zy)$,
           $P_w = b + 2y\sqrt{1+z^2}$, $R_h = A/P_w$. At $y = 1.359$ m:
           $A = 1.359(3 + 1.5\times1.359) = 6.85\ \mathrm{m^2}$,
           $P_w = 3 + 2(1.359)\sqrt{1+2.25} = 7.90\ \mathrm{m}$,
           $R_h = 0.867\ \mathrm{m}$.
        2. **Manning.** $V = (1/0.022)(0.867)^{2/3}(0.0008)^{1/2} = 1.17\ \mathrm{m/s}$,
           so $Q = 1.17 \times 6.85 = 8.0\ \mathrm{m^3/s}$. The trial depth was right. In
           practice you iterate on $y$ — which is exactly what the solver below does, with
           a bracketed root find that always converges because $Q(y)$ is monotonic.
        3. **Check the velocity against scour and siltation.** Unlined earth canals are kept
           between roughly 0.6 and 1.5 m/s: slower and suspended sediment settles out and
           silts the channel up, faster and the bed erodes. 1.17 m/s sits comfortably in the
           middle. **This check, not the head loss, usually sets the design** — which is the
           sharpest difference between canal design and pipe design.
        4. **Check the regime.** $T = 7.08\ \mathrm{m}$, $D_h = A/T = 0.967\ \mathrm{m}$,
           $\mathrm{Fr} = 1.17/\sqrt{9.81\times0.967} = 0.38$. Subcritical, as an irrigation
           canal should be — supercritical flow over erodible earth is a scour problem
           waiting to happen. Critical depth is 0.78 m, well below the normal depth of
           1.36 m, which says the same thing a second way.
        5. **Check the freeboard.** Bank at 2.5 m, water at 1.36 m, so freeboard is 1.14 m
           against a requirement of about $\max(0.3\ \mathrm{m},\ 0.2y_n) = 0.30\ \mathrm{m}$.
           Ample.
        6. **Check the flood case.** Filled to the top of bank at 2.5 m the same section
           would carry $27.2\ \mathrm{m^3/s}$ — 3.4 times the design flow. **That margin,
           not the design point, is the answer to "will it flood".**
        7. **Check the bed shear.** $\tau_w = \rho g R_h S_0 = 998 \times 9.81 \times 0.867
           \times 0.0008 = 6.8\ \mathrm{Pa}$. Compare against the permissible tractive stress
           for the bed material — roughly 3–5 Pa for fine sand, 15–20 Pa for stiff clay.
           Sand would scour here; compacted clay would hold.
        """
    )
    render_callout(
        """
        **And now the failure mode.** Let the weeds grow so $n$ rises from 0.022 to 0.030 —
        entirely routine for an unmaintained earth canal by late summer, and only one row
        down the material list in the calculator below. The normal depth for the *same*
        8 m³/s rises from 1.36 m to 1.59 m, and the freeboard falls from 1.14 m to 0.91 m.
        Nothing about the canal changed except its roughness. Let it go further, to the
        0.040 of a weed-choked winding channel, and the depth reaches 1.84 m. Now put a
        storm event on top of a weedy channel and the two effects compound. Real canal
        failures are almost never a wrong Manning calculation; they are a right calculation
        done with last year's $n$.
        """,
        title="Why maintenance is a hydraulic parameter",
    )

    st.markdown("#### 2.5.4 Canal and channel calculator")
    ch1, ch2, ch3 = st.columns(3)
    ch_q = ch1.number_input("Design discharge Q [m³/s]", min_value=0.01, max_value=5000.0,
                            value=8.0, step=0.5, key="canal_q")
    ch_b = ch1.number_input("Bottom width b [m]", min_value=0.0, max_value=200.0,
                            value=3.0, step=0.5, key="canal_b")
    ch_z = ch2.number_input("Side slope z (horizontal per 1 vertical)", min_value=0.0,
                            max_value=6.0, value=1.5, step=0.25, key="canal_z")
    ch_slope = ch2.number_input("Bed slope S₀ [m/m]", min_value=1e-6, max_value=0.2,
                                value=0.0008, step=0.0002, format="%.5f", key="canal_s")
    ch_material = ch3.selectbox("Channel surface", list(MANNING_N.keys()), index=4, key="canal_mat")
    ch_bank = ch3.number_input("Bank height above invert [m]", min_value=0.05, max_value=60.0,
                               value=2.5, step=0.1, key="canal_bank")

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
                    f"f_D = {darcy['f_darcy']:.4f} at Re = {darcy['reynolds']:.2e}, hence "
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
