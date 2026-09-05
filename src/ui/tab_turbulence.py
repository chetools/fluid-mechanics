"""UI module for Laminar vs. Turbulent flows: Diagrams, Theory, and Practical Trade-offs."""

import streamlit as st
from src.ui.state import persistent_input
from src.ui.pedagogy import render_plot

from src.svg_diagrams import (
    diagram_reynolds_experiment,
    diagram_laminar_vs_turbulent_profiles,
    diagram_law_of_the_wall,
    render_svg
)
from src.physics.turbulence import velocity_profile_comparison, law_of_the_wall
from src.physics.pipe_flow import (
    friction_factor_churchill,
    laminar_darcy_from_force_balance,
    straw_bundle_comparison,
)
from src.plotting import plot_laminar_turbulent_profiles, plot_law_of_the_wall, plot_straw_bundle
from src.units import get_fluid_state
from src.ui.pedagogy import (
    render_objectives,
    render_what_to_notice,
    render_predict,
    render_self_check,
    render_callout,
    render_prose_and_latex,
    render_symbols,
)

def render_tab_turbulence():
    """Render comprehensive panel comparing laminar and turbulent flows."""
    fluid = get_fluid_state()
    st.markdown(
        """
        Flow regimes govern everything in fluid transport.
        Whether a fluid flows in smooth, orderly parallel sheets (**laminar flow**)
        or chaotic, three-dimensional swirling eddies (**turbulent flow**)
        dictates friction factors, heat and mass transfer coefficients, and pumping energy.

        **Scope.** Re = 2300 / 4000, $\\alpha = 2$, and the $1/7$ power law are
        **circular-pipe** results (Osborne Reynolds' apparatus). They are not
        the transition Re of a lid-driven cavity or a cylinder.
        """
    )
    render_objectives(
        [
            "State that 2300 is a pipe threshold, not a universal law.",
            "Derive $f_D = 64/\\mathrm{Re}$ from a cylindrical force balance and compare it to Moody.",
            "Decide whether packing a pipe with straws to stay laminar actually saves pump kW.",
            "Write Chilton–Colburn with the Fanning factor: $j = f_F/2 = f_D/8$.",
        ]
    )
    
    # -------------------------------------------------------------------------
    # PART 1: The Transition Experiment
    # -------------------------------------------------------------------------
    st.markdown("### 4.1 The Physics of Transition: Osborne Reynolds (1883)")
    st.markdown(
        """
        In his historic 1883 Manchester experiments, Osborne Reynolds injected a thin filament 
        of dyed water into the center of a glass pipe to observe flow structure.
        """
    )
    
    render_svg(diagram_reynolds_experiment())
    
    render_callout(
        r"""
        **The Physical Mechanism of Turbulent Transition**
        
        The Reynolds number represents the dimensionless ratio of **destabilizing inertial forces** to **stabilizing viscous damping**:
        $$\text{Re}_D = \frac{\text{Inertia}}{\text{Viscous Damping}} = \frac{\rho u D}{\mu} \quad \text{(circular pipe)}$$
        - **At low $\text{Re}_D < 2300$ in a pipe:** Viscous forces quench small perturbations. Streamlines stay parallel.
        - **At transitional $\text{Re}_D \in [2300, 4000]$ in a pipe:** Intermittent turbulent slugs or puffs.
        - **At high $\text{Re}_D > 4000$ in a pipe:** $(\mathbf{u}\cdot\nabla)\mathbf{u}$ overwhelms damping. In *three* dimensions, vortex stretching feeds a cascade down to Kolmogorov scales.
        A flat plate, a cylinder, and a lid-driven cavity each have their own critical Re; do not import 2300 there.
        """
    )

    st.markdown("### 4.1b Laminar force balance → $f_D = 64/\\mathrm{Re}$")
    st.markdown(
        r"""
        Tab 1 booked friction as lost mechanical energy. Here we *compute* it
        for fully developed laminar flow in a round pipe, then compare to the
        Moody laminar line (Tab 2).
        """
    )
    with st.expander("🔍 Force balance on a cylindrical fluid core (no skipped algebra)", expanded=False):
        render_prose_and_latex(
            r"""
            Take a coaxial plug of radius $r$ and length $L$. Steady axial flow,
            no acceleration, so $\sum F_z = 0$:
            $$\underbrace{\Delta p \cdot \pi r^2}_{\text{net pressure}}
            = \underbrace{\tau(r)\cdot 2\pi r L}_{\text{shear on the jacket}}$$
            $$\tau(r) = \frac{r}{2}\frac{\Delta p}{L}$$
            At the wall $r = R = D/2$, $\tau_w = (D/4)(\Delta p/L)$.
            Newtonian constitutive law $\tau = \mu (-du/dr)$:
            $$-\mu \frac{du}{dr} = \frac{r}{2}\frac{\Delta p}{L}$$
            Integrate with $u(R)=0$:
            $$u(r) = \frac{1}{4\mu}\frac{\Delta p}{L}(R^2 - r^2)$$
            Mean speed $u_{\mathrm{avg}} = u_{\max}/2 = (D^2/32\mu)(\Delta p/L)$
            (Hagen–Poiseuille). Solve for $\Delta p$ and substitute the **Darcy**
            definition $\Delta p = f_D (L/D)(\rho u^2/2)$:
            $$f_D = \frac{2\Delta p D}{L\rho u^2} = \frac{64\mu}{\rho u D} = \frac{64}{\mathrm{Re}}$$
            Fanning is $f_F = 16/\mathrm{Re} = f_D/4$. Same physics, factor of four.
            """
        )
        render_symbols(
            [
                (r"\Delta p", "pressure drop over length $L$ (Pa)."),
                (r"r", "radius of the coaxial fluid plug (m). Wall is $r=R=D/2$."),
                (r"\tau(r)", r"axial shear on the cylindrical jacket (Pa). At the wall, $\tau_w=(D/4)(\Delta p/L)$."),
                (r"\mu", "dynamic viscosity (Pa·s). Sidebar fluid."),
                (r"u(r)", "axial speed of the Hagen–Poiseuille parabola (m/s)."),
                (r"f_D", r"Darcy friction factor. This force balance gives $f_D=64/\mathrm{Re}$."),
                (r"\mathrm{Re}", r"$\rho u_{\mathrm{avg}} D/\mu$ with $u_{\mathrm{avg}}$ the area-mean speed."),
            ]
        )
    re_cmp = persistent_input(st.select_slider,
        "Compare f_D(Re) at",
        options=[200, 500, 1000, 1500, 2000, 2300, 4000, 1e4],
        value=1000,
        key="lam_f_re",
    )
    f_force = laminar_darcy_from_force_balance(float(re_cmp))
    f_moody = friction_factor_churchill(float(re_cmp), 0.0)
    col_f1, col_f2, col_f3 = st.columns(3)
    col_f1.metric("Force-balance f_D = 64/Re", f"{f_force:.4f}")
    col_f2.metric("Churchill / Moody f_D", f"{f_moody:.4f}")
    col_f3.metric("Relative difference", f"{abs(f_moody - f_force)/f_force*100:.2f} %")
    if re_cmp <= 2300:
        st.success("Below Re = 2300 the two expressions agree: Moody's laminar line *is* the force balance.")
    else:
        st.warning(
            "Above transition the force balance assumed a parabolic, laminar τ(r). "
            "Turbulent eddy stress raises f_D well above 64/Re."
        )

    # -------------------------------------------------------------------------
    # PART 2: Velocity Profile Comparison
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 4.2 Velocity Profile Comparison: Parabolic vs. 1/7th Power Law")
    st.markdown(
        """
        Turbulent momentum exchange by fluctuating eddy eddies ($\\overline{u'v'}$) dramatically 
        flattens the velocity profile across the pipe core while creating an intense velocity gradient 
        immediately adjacent to the wall.
        """
    )
    
    render_svg(diagram_laminar_vs_turbulent_profiles())
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        u_mean_input = persistent_input(st.slider, "Mean Flow Velocity u_avg [m/s]", min_value=0.5, max_value=5.0, value=1.5, step=0.1, key="tab_turbulence_mean_flow_velocity_u_avg_m_s")
    with col_v2:
        re_turb_prof = persistent_input(st.select_slider,
            "Turbulent Reynolds Number",
            options=[5000, 20000, 50000, 100000, 500000, 1000000],
            value=50000, key="tab_turbulence_turbulent_reynolds_number")
        
    prof_res = velocity_profile_comparison(pipe_radius=0.05, u_avg=u_mean_input, reynolds=re_turb_prof)
    
    col_pr1, col_pr2, col_pr3 = st.columns(3)
    col_pr1.metric("Laminar Centerline Apex", f"{prof_res['u_max_lam']:.2f} m/s (2.0 × u_avg)")
    col_pr2.metric("Turbulent Centerline Apex", f"{prof_res['u_max_turb']:.2f} m/s ({prof_res['u_max_turb']/u_mean_input:.2f} × u_avg)")
    col_pr3.metric("Pipe kinetic-energy factor α", f"Laminar: {prof_res['alpha_lam']:.2f} | Turb: {prof_res['alpha_turb']:.2f}")
    st.caption(
        "α = 2 and u_avg/u_max = 1/2 are **circular pipe**. A plane channel has "
        "u_avg/u_max = 2/3 and α = 54/35 ≈ 1.54 (see Tab 7 Couette–Poiseuille)."
    )
    render_what_to_notice("Equal mean velocity: the turbulent profile is blunter, so the wall gradient (and τ_w) is steeper.")
    
    fig_prof = plot_laminar_turbulent_profiles(prof_res)
    render_plot(fig_prof, key="tab_turbulence-fig_prof")
    
    with st.expander("🔍 Engineering Consequence: Kinetic Energy Flux Correction Factor α in Bernoulli's Equation"):
        render_prose_and_latex(
            r"""
            When writing the engineering mechanical energy balance (extended Bernoulli equation), 
            the true kinetic energy flux carried across a pipe cross-section is:
            $$\dot{E}_k = \int \frac{1}{2}\rho u^3 dA = \alpha \left(\frac{1}{2}\rho \bar{u}^3 A\right)$$
            where $\alpha = \frac{1}{A} \int \left(\frac{u}{\bar{u}}\right)^3 dA$ is the **kinetic energy correction factor**:
            * **Laminar Flow:** $\alpha = 2.00$ exactly! Neglecting $\alpha$ introduces a **100% error** in the kinetic head term!
            * **Turbulent Flow:** Because the velocity profile is nearly flat across the core, $\alpha \approx 1.04 \text{ to } 1.08 \approx 1.0$.
            In practical chemical engineering design, engineers assume $\alpha = 1.0$ for turbulent *pipe* calculations, but for laminar *pipe* flows (e.g., polymer extrusions, heavy crude oils), $\alpha = 2.0$ must be used. Do not use α = 2 for a plane slit.
            """
        )
        render_symbols(
            [
                (
                    r"\alpha",
                    r"kinetic-energy correction $\alpha=(1/A)\int(u/\bar{u})^3\,dA$. "
                    "Not an angle, not thermal diffusivity, not Tab 6's angular acceleration $\\alpha_z$. "
                    "Circular pipe: $\\alpha=2$ laminar, $\\alpha\\approx 1.05$ turbulent.",
                ),
                (r"\dot{E}_k", r"true kinetic-energy flux through the cross-section (W)."),
                (r"\bar{u}", r"area-mean speed $Q/A$ (m/s)."),
            ]
        )

    # -------------------------------------------------------------------------
    # PART 3: Law of the Wall
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 4.3 The Universal Law of the Wall")
    render_prose_and_latex(
        """
        The flow near any solid boundary is governed by inner wall variables scaled by the 
        **friction velocity** $u_\\tau = \\sqrt{\\tau_{\\text{wall}} / \\rho}$:
        $$y^+ = \\frac{y u_\\tau}{\\nu}, \\quad u^+ = \\frac{u}{u_\\tau}$$
        """
    )
    
    render_svg(diagram_law_of_the_wall())
    
    st.caption(
        "κ ≈ 0.41 and B ≈ 5.0 are **empirical constants** for a smooth wall, not operating "
        "conditions like Re. Moving them redraws the log law; it does not change the flow you specified."
    )
    show_const = persistent_input(st.checkbox, "Explore literature-constant sensitivity (κ, B)", value=False, key="tab_turbulence_explore_literature_constant_sensitivity_b")
    if show_const:
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            karman_k = persistent_input(st.slider, "von Kármán Constant κ", min_value=0.35, max_value=0.45, value=0.41, step=0.01, key="tab_turbulence_von_k_rm_n_constant")
        with col_w2:
            wall_b = persistent_input(st.slider, "Log-Law Intercept Constant B", min_value=4.0, max_value=6.0, value=5.0, step=0.1, key="tab_turbulence_log_law_intercept_constant_b")
    else:
        karman_k, wall_b = 0.41, 5.0

    wall_res = law_of_the_wall(kappa=karman_k, B=wall_b)
    render_what_to_notice("y⁺ < 5 is linear (viscous sublayer). y⁺ > 30 is the log overlap. The buffer is a blend, not a third law.")
    fig_wall = plot_law_of_the_wall(wall_res)
    render_plot(fig_wall, key="tab_turbulence-fig_wall")

    # -------------------------------------------------------------------------
    # PART 4: Practical ChemE Trade-off
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 4.4 Chemical Engineering Practical Trade-Off: Heat/Mass Transfer vs. Pumping Penalty")
    
    col_to1, col_to2 = st.columns(2)
    with col_to1:
        render_callout(
            """
            **✅ Why We Want Turbulence: Transport Enhancement**
            
            In chemical reactors, bioreactors, and heat exchangers, rapid mixing is essential:
            - **Heat Transfer:** Laminar pipe heat transfer is strictly conduction-limited (Nusselt number $\\text{Nu} = 3.66$). Turbulent heat transfer scales as $\\text{Nu} \\sim \\text{Re}^{0.8} \\cdot \\text{Pr}^{1/3}$ (Dittus–Boelter), increasing heat transfer rates by **10 to 100-fold**!
            - **Mass Transfer:** Turbulent eddy diffusivity $\\epsilon_M$ is 1,000 to 100,000 times larger than molecular diffusion coefficients.
            - **Chilton–Colburn Analogy:** $j_H = j_D = f_F / 2 = f_D / 8$.
              Use the **Fanning** factor here (Tab 2). Writing $f/2$ with a Moody (Darcy) $f$ is a factor-of-four error.
            """
        )
    with col_to2:
        render_callout(
            """
            **⚠️ The Pumping Penalty: Hydraulic Cost**
            
            Turbulence comes at a severe energetic price:
            - **Pressure Drop Scaling:**
              - In laminar flow: $\\Delta p \\propto u^{1.0}$ (linear with velocity).
              - In turbulent flow: $\\Delta p \\propto u^{1.75} \\text{ to } u^{2.0}$ (quadratic with velocity).
            - **Pumping Power:** Power scales as $P = Q \\cdot \\Delta p \\propto u^{3.0}$! Doubling flow velocity in a turbulent line requires **8 times more pump horsepower**.
            - **Process Optimization:** Chemical engineers must balance heat transfer area vs. operating electricity cost.
            """
        )

    render_self_check(
        "turb_self_check_colburn",
        "Chilton–Colburn is j = f/2. Which f is that?",
        ["Darcy f_D (Moody chart)", "Fanning f_F = f_D/4", "Either, they differ only by Re"],
        "Fanning f_F = f_D/4",
        "j_H = f_F/2 = f_D/8. Moody plots Darcy; BSL often uses Fanning.",
    )

    st.markdown("---")
    st.markdown("### 4.5 The straw-pipe question")
    render_prose_and_latex(
        r"""
        Turbulence raises $f_D$ and $\Delta p \propto u^{1.75\text{–}2}$. A natural
        thought: **fill the pipe with $N$ capillary “straws”** so each lumen stays
        laminar ($\mathrm{Re}_d < 2300$), at the **same total** $Q$ and the same
        outer diameter $D$.

        Geometry: packing fraction $\phi$ (hexagonal $\approx 0.91$; we default 0.85),
        $N d^2 = \phi D^2$, so $d = D\sqrt{\phi/N}$. Each straw carries $Q/N$.
        Laminar Hagen–Poiseuille on each lumen:
        $$\Delta p = \frac{128\mu L (Q/N)}{\pi d^4} \propto \frac{N}{\phi^2}$$
        Shrinking $d$ hurts as $d^4$ in the denominator. Staying laminar is not free.
        """
    )
    render_predict(
        "straw_predict",
        "At fixed Q and outer D, adding more straws to keep Re_d laminar will typically…",
        ["cut pump power because f_D = 64/Re is smaller",
         "raise pump power because d⁴ in the denominator beats the laminar f",
         "leave Δp unchanged by dimensional analysis"],
        "raise pump power because d⁴ in the denominator beats the laminar f",
        "Δp_bundle ∝ N/φ² for laminar capillaries. Open-pipe turbulence is expensive, but so is making many tiny tubes.",
    )
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        straw_Q = persistent_input(st.slider, "Total Q [m³/h]", min_value=5.0, max_value=80.0, value=25.0, step=1.0, key="straw_Q")
        straw_D = persistent_input(st.slider, "Outer D [mm]", min_value=40.0, max_value=200.0, value=75.0, step=5.0, key="straw_D")
    with col_s2:
        straw_L = persistent_input(st.slider, "Length L [m]", min_value=10.0, max_value=200.0, value=60.0, step=5.0, key="straw_L")
        straw_phi = persistent_input(st.slider, "Packing fraction φ", min_value=0.5, max_value=0.91, value=0.85, step=0.01, key="straw_phi")
    with col_s3:
        straw_N = persistent_input(st.select_slider,
            "Number of straws N",
            options=[1, 4, 7, 19, 37, 61, 100, 200, 400],
            value=19,
            key="straw_N",
        )
    one = straw_bundle_comparison(
        flow_rate=straw_Q / 3600.0,
        outer_diameter=straw_D / 1000.0,
        length=straw_L,
        density=float(fluid["rho"]),
        viscosity=float(fluid["mu"]),
        n_straws=int(straw_N),
        packing_fraction=float(straw_phi),
    )
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Open-pipe Re_D", f"{one['re_open']:.0f}")
    col_m2.metric("Straw Re_d", f"{one['re_straw']:.0f}")
    col_m3.metric("Open-pipe power", f"{one['power_open']/1000:.2f} kW")
    col_m4.metric("Bundle power", f"{one['power_bundle']/1000:.2f} kW",
                  delta=f"{one['power_ratio']:.2f} × open")
    if one["straw_laminar"] and one["power_ratio"] > 1:
        st.warning(
            "The straws are laminar — and still more expensive. You bought extra wall area "
            "(more τ_w × perimeter) to suppress eddies."
        )
    elif not one["straw_laminar"]:
        st.info("These straws are still turbulent. Increase N or lower Q.")
    n_sweep = [1, 4, 7, 19, 37, 61, 100, 200, 400]
    sweep = [
        straw_bundle_comparison(
            flow_rate=straw_Q / 3600.0,
            outer_diameter=straw_D / 1000.0,
            length=straw_L,
            density=float(fluid["rho"]),
            viscosity=float(fluid["mu"]),
            n_straws=n,
            packing_fraction=float(straw_phi),
        )
        for n in n_sweep
    ]
    render_what_to_notice(
        "Left: bundle power vs N (log). Horizontal = open pipe. Right: Re_d falls through 2300 "
        "while power is already rising. A shell-and-tube exchanger uses many tubes for *area*, "
        "not to dodge turbulence; the hydraulic penalty is paid for heat transfer."
    )
    fig_st = plot_straw_bundle(
        n_sweep,
        sweep[0]["power_open"],
        [s["power_bundle"] for s in sweep],
        [s["re_straw"] for s in sweep],
    )
    render_plot(fig_st, key="tab_turbulence-fig_st")
    render_self_check(
        "straw_self_check",
        "Why doesn’t “keep it laminar with straws” win on pump kW at fixed Q and outer D?",
        [
            "Because laminar f_D is always larger than turbulent f_D",
            "Because Δp ~ μ Q L / d⁴ and d shrinks as 1/√N, so Δp grows with N",
            "Because packing fraction φ cannot exceed 0.5",
        ],
        "Because Δp ~ μ Q L / d⁴ and d shrinks as 1/√N, so Δp grows with N",
        "Hagen–Poiseuille on each lumen: d⁴ in the denominator. More walls, more shear area.",
    )
