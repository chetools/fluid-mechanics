"""UI module for Pipe Flow and Chemical Engineering piping applications."""

import streamlit as st

from src.physics.pipe_flow import (
    calculate_cheme_pipe_system,
    PIPE_ROUGHNESS,
    hydraulic_diameter,
    friction_factor_churchill,
    entrance_length,
    npsh_available,
)
from src.physics.non_newtonian import power_law_pressure_drop
from src.svg_diagrams import diagram_npsh, render_svg
from src.plotting import plot_moody_chart, plot_cheme_head_loss_breakdown, plot_npsh_station
from src.units import format_quantity, get_fluid_state
from src.ui.pedagogy import (
    render_objectives,
    render_what_to_notice,
    render_predict,
    render_self_check,
)


def render_tab_pipe_flow():
    """Render practical pipe flow, Moody chart, and ChemE piping lab."""
    fluid = get_fluid_state()
    st.markdown("## 6. Pipe Flow & Practical Chemical Engineering Applications")
    st.markdown(
        """
        In industrial chemical plants, piping networks transport liquids and gases across
        reactor loops, columns, and exchangers. Frictional pressure drop sizes pumps,
        sets OPEX, and (with NPSH) protects against cavitation.

        This panel uses the **sidebar fluid** ({name}, ρ = {rho:.4g} kg/m³, μ = {mu:.3e} Pa·s).
        Tab 5 explains why Re = 2300 is a *pipe* threshold; Tab 1's Bernoulli is the
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
    st.markdown("### 6.1 Frictional Head Loss: Darcy vs. Fanning")
    st.markdown(
        """
        The fundamental equation for frictional pressure drop in a circular pipe is the
        **Darcy–Weisbach equation**:
        """
    )

    st.latex(r"\Delta p_f = f_D \frac{L}{D} \left(\frac{1}{2}\rho u^2\right)")
    st.latex(r"h_f = \frac{\Delta p_f}{\rho g} = f_D \frac{L}{D} \frac{u^2}{2g}")
    st.latex(r"\text{Fanning Friction Factor: } \quad f_F = \frac{\tau_{\text{wall}}}{\frac{1}{2}\rho u^2} = \frac{f_D}{4}")

    with st.expander("⚠️ Chemical Engineering Nomenclature Alert: Darcy vs. Fanning Friction Factors", expanded=True):
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

            The Chilton–Colburn analogy in Tab 5 is $j_H = j_D = f_F/2 = f_D/8$, **not** $f_D/2$.
            """
        )

    st.markdown("### 6.1b Mechanical energy (extended Bernoulli)")
    st.markdown(
        r"""
        Integrating the steady momentum equation along a streamline *and then adding*
        viscous dissipation and shaft work gives the engineering mechanical energy equation
        between stations 1 and 2:
        $$\frac{p_1}{\rho g} + \alpha_1\frac{u_1^2}{2g} + z_1 + h_{\mathrm{shaft}}
        = \frac{p_2}{\rho g} + \alpha_2\frac{u_2^2}{2g} + z_2 + h_f + h_{\mathrm{minor}}$$
        * $\alpha = 2$ exactly in laminar pipe flow; $\alpha \approx 1.05$ when turbulent (Tab 5).
        * $h_{\mathrm{shaft}}$ is the pump head this lab solves for.
        * $h_f$ is Darcy–Weisbach; $h_{\mathrm{minor}} = \sum K_L\, u^2/(2g)$.
        * For two large tanks, $u_1 \approx u_2 \approx 0$ and an outlet $K_L = 1$ already dumps the exit kinetic head — do not add $\alpha u^2/2g$ on top of that $K_L$.
        """
    )

    # -------------------------------------------------------------------------
    # PART 2: The Interactive Moody Chart
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 6.2 The Moody Diagram & Colebrook–White Correlation")
    st.markdown(
        """
        In 1944, Lewis Ferry Moody plotted the **Darcy** friction factor as a function of Reynolds number
        and relative roughness $\\varepsilon/D$.

        * **Laminar Zone ($Re < 2300$, circular pipe):** Independent of roughness! $f_D = 64/Re$.
        * **Critical Zone ($2000 < Re < 4000$):** Flow is intermittently turbulent; highly sensitive.
        * **Wholly Turbulent Rough Pipe Zone:** Viscous sublayer is thinner than wall asperities; $f$ becomes independent of $Re$ and depends solely on $\\varepsilon/D$.
        """
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
    st.plotly_chart(fig_moody, width="stretch")

    # -------------------------------------------------------------------------
    # PART 3: Practical ChemE Piping Network & Pump Sizing Lab
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 6.3 Practical ChemE Piping Network & Pump Sizing Lab")
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
    st.plotly_chart(fig_head, width="stretch")

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
    st.markdown("### 6.3b NPSH Station (pump suction)")
    st.markdown(
        r"""
        Tab 1's cavitation warning at a Venturi throat is the same physics at a pump eye.
        From a free-surface tank, **available** net positive suction head is
        $$\mathrm{NPSH}_A = \frac{P_{\mathrm{tank}} - P_v}{\rho g} + z - h_f$$
        $z>0$ flooded suction, $z<0$ suction lift. Impeller-eye velocity head is charged
        to the manufacturer's $\mathrm{NPSH}_R$, not to $\mathrm{NPSH}_A$. Cavitate if
        $\mathrm{NPSH}_A < \mathrm{NPSH}_R$.
        """
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
        st.plotly_chart(fig_npsh, width="stretch")
        render_predict(
            "npsh_predict",
            "Raising the tank surface (larger +z) at fixed Q and P_tank will…",
            ["leave NPSH_A unchanged", "increase NPSH_A one-for-one with z", "decrease NPSH_R"],
            "increase NPSH_A one-for-one with z",
            "NPSH_A = (P−P_v)/ρg + z − h_f. Flooded suction is the cheapest cavitation insurance.",
        )

    st.markdown("#### Laminar power-law Δp (same Q, D, L)")
    st.caption(
        "From Tab 3's Ostwald–de Waele lab. Only valid while Re_MR is laminar; "
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
    st.markdown("### 6.4 Non-Circular Ducts & Heat Exchanger Annuli")
    st.markdown(
        r"""
        For non-circular cross sections (e.g., shell-and-tube or double-pipe heat exchanger annuli,
        rectangular HVAC ducts), friction factor correlations are evaluated using the **hydraulic diameter**:
        $$D_H = \frac{4 \times \text{Cross-Sectional Area}}{\text{Wetted Perimeter}} = \frac{4 A}{P_w}$$
        Then $\mathrm{Re}_{D_H} = \rho u D_H/\mu$ and the same $f_D(\mathrm{Re}, \varepsilon/D_H)$ goes into Darcy–Weisbach.
        """
    )

    col_hd1, col_hd2 = st.columns(2)
    with col_hd1:
        st.info(
            """
            **Double-Pipe Heat Exchanger Annulus**

            Fluid flows in the annular gap between outer pipe inner diameter $D_o$ and inner pipe outer diameter $D_i$:
            - Area: $A = \\frac{\\pi}{4}(D_o^2 - D_i^2)$
            - Wetted perimeter: $P_w = \\pi(D_o + D_i)$
            - **Hydraulic diameter:** $D_H = \\frac{4 A}{P_w} = D_o - D_i$
            """
        )
    with col_hd2:
        st.info(
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
