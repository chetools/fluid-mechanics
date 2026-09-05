"""UI module for Laminar vs. Turbulent flows: Diagrams, Theory, and Practical Trade-offs."""

import streamlit as st
import numpy as np

from src.svg_diagrams import (
    diagram_reynolds_experiment,
    diagram_laminar_vs_turbulent_profiles,
    diagram_law_of_the_wall,
    render_svg
)
from src.physics.turbulence import velocity_profile_comparison, law_of_the_wall
from src.plotting import plot_laminar_turbulent_profiles, plot_law_of_the_wall
from src.ui.pedagogy import render_objectives, render_what_to_notice, render_self_check

def render_tab_turbulence():
    """Render comprehensive panel comparing laminar and turbulent flows."""
    st.markdown("## 5. Laminar vs. Turbulent Flows: Physics, Profiles & Practical Implications")
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
            "Use α = 2 in laminar *pipe* Bernoulli; α ≈ 1.05 when turbulent.",
            "Read y⁺ sublayers; treat κ and B as literature constants.",
            "Write Chilton–Colburn with the Fanning factor: j = f_F/2 = f_D/8.",
        ]
    )
    
    # -------------------------------------------------------------------------
    # PART 1: The Transition Experiment
    # -------------------------------------------------------------------------
    st.markdown("### 5.1 The Physics of Transition: Osborne Reynolds (1883)")
    st.markdown(
        """
        In his historic 1883 Manchester experiments, Osborne Reynolds injected a thin filament 
        of dyed water into the center of a glass pipe to observe flow structure.
        """
    )
    
    render_svg(diagram_reynolds_experiment())
    
    st.info(
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

    # -------------------------------------------------------------------------
    # PART 2: Velocity Profile Comparison
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 5.2 Velocity Profile Comparison: Parabolic vs. 1/7th Power Law")
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
        u_mean_input = st.slider("Mean Flow Velocity u_avg [m/s]", min_value=0.5, max_value=5.0, value=1.5, step=0.1)
    with col_v2:
        re_turb_prof = st.select_slider(
            "Turbulent Reynolds Number",
            options=[5000, 20000, 50000, 100000, 500000, 1000000],
            value=50000
        )
        
    prof_res = velocity_profile_comparison(pipe_radius=0.05, u_avg=u_mean_input, reynolds=re_turb_prof)
    
    col_pr1, col_pr2, col_pr3 = st.columns(3)
    col_pr1.metric("Laminar Centerline Apex", f"{prof_res['u_max_lam']:.2f} m/s (2.0 × u_avg)")
    col_pr2.metric("Turbulent Centerline Apex", f"{prof_res['u_max_turb']:.2f} m/s ({prof_res['u_max_turb']/u_mean_input:.2f} × u_avg)")
    col_pr3.metric("Pipe kinetic-energy factor α", f"Laminar: {prof_res['alpha_lam']:.2f} | Turb: {prof_res['alpha_turb']:.2f}")
    st.caption(
        "α = 2 and u_avg/u_max = 1/2 are **circular pipe**. A plane channel has "
        "u_avg/u_max = 2/3 and α = 54/35 ≈ 1.54 (see Tab 4 Couette–Poiseuille)."
    )
    render_what_to_notice("Equal mean velocity: the turbulent profile is blunter, so the wall gradient (and τ_w) is steeper.")
    
    fig_prof = plot_laminar_turbulent_profiles(prof_res)
    st.plotly_chart(fig_prof, width="stretch")
    
    with st.expander("🔍 Engineering Consequence: Kinetic Energy Flux Correction Factor α in Bernoulli's Equation"):
        st.markdown(
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

    # -------------------------------------------------------------------------
    # PART 3: Law of the Wall
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 5.3 The Universal Law of the Wall")
    st.markdown(
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
    show_const = st.checkbox("Explore literature-constant sensitivity (κ, B)", value=False)
    if show_const:
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            karman_k = st.slider("von Kármán Constant κ", min_value=0.35, max_value=0.45, value=0.41, step=0.01)
        with col_w2:
            wall_b = st.slider("Log-Law Intercept Constant B", min_value=4.0, max_value=6.0, value=5.0, step=0.1)
    else:
        karman_k, wall_b = 0.41, 5.0

    wall_res = law_of_the_wall(kappa=karman_k, B=wall_b)
    render_what_to_notice("y⁺ < 5 is linear (viscous sublayer). y⁺ > 30 is the log overlap. The buffer is a blend, not a third law.")
    fig_wall = plot_law_of_the_wall(wall_res)
    st.plotly_chart(fig_wall, width="stretch")

    # -------------------------------------------------------------------------
    # PART 4: Practical ChemE Trade-off
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 5.4 Chemical Engineering Practical Trade-Off: Heat/Mass Transfer vs. Pumping Penalty")
    
    col_to1, col_to2 = st.columns(2)
    with col_to1:
        st.info(
            """
            **✅ Why We Want Turbulence: Transport Enhancement**
            
            In chemical reactors, bioreactors, and heat exchangers, rapid mixing is essential:
            - **Heat Transfer:** Laminar pipe heat transfer is strictly conduction-limited (Nusselt number $\\text{Nu} = 3.66$). Turbulent heat transfer scales as $\\text{Nu} \\sim \\text{Re}^{0.8} \\cdot \\text{Pr}^{1/3}$ (Dittus–Boelter), increasing heat transfer rates by **10 to 100-fold**!
            - **Mass Transfer:** Turbulent eddy diffusivity $\\epsilon_M$ is 1,000 to 100,000 times larger than molecular diffusion coefficients.
            - **Chilton–Colburn Analogy:** $j_H = j_D = f_F / 2 = f_D / 8$.
              Use the **Fanning** factor here (Tab 6). Writing $f/2$ with a Moody (Darcy) $f$ is a factor-of-four error.
            """
        )
    with col_to2:
        st.info(
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
