"""Panel 1: Why fluid mechanics for ChemE, energy Bernoulli, friction as heat."""

import streamlit as st

from src.units import get_fluid_state
from src.ui.pedagogy import (
    render_objectives,
    render_what_to_notice,
    render_checklist,
    render_self_check,
)


def render_tab_cheme_energy():
    """Plant-level motivation and Bernoulli from a steady energy balance."""
    fluid = get_fluid_state()
    st.markdown("## 1. Why Fluid Mechanics for Chemical Engineers")
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
            st.markdown("What $\\Delta p$ does this transfer line take? Is the velocity in the 1–3 m/s economic band?")
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
        "feeds every later lab. This panel is the energy story; Tab 2 turns it into a pipe/pump calculation."
    )
    render_objectives(
        [
            "State why $\\Delta p$, pump kW, and NPSH are the ChemE fluid-mechanics triad.",
            "Derive Bernoulli from a **steady mechanical energy balance**, not from Euler.",
            "Identify viscosity as **frictional heating**: irreversible conversion of $p/\\rho + u^2/2 + gz$ into internal energy.",
        ]
    )

    st.markdown("### 1.1 Where the energy goes in a plant line")
    st.markdown(
        r"""
        Between two stations on a pipe (feed tank $\to$ pump discharge, or pump $\to$
        column feed nozzle) a fluid carries three *mechanical* stores of energy per
        unit mass, plus whatever shaft work we add:
        $$\underbrace{\frac{p}{\rho}}_{\text{flow work / pressure energy}}
        + \underbrace{\frac{\alpha u^2}{2}}_{\text{kinetic}}
        + \underbrace{g z}_{\text{potential}}
        + \underbrace{w_{\mathrm{shaft}}}_{\text{pump (in)}}
        $$
        In a *perfectly smooth, inviscid* line those four quantities are conserved.
        Real walls do work against the fluid by shear. That work does not vanish:
        it appears as a temperature rise (usually millikelvin) — **frictional heating**.
        We account for it as a lost mechanical head $h_f$ (and fittings $h_{\mathrm{minor}}$):
        """
    )
    st.latex(
        r"\frac{p_1}{\rho g} + \alpha_1\frac{u_1^2}{2g} + z_1 + h_{\mathrm{shaft}}"
        r" = \frac{p_2}{\rho g} + \alpha_2\frac{u_2^2}{2g} + z_2 + h_f + h_{\mathrm{minor}}"
    )
    st.markdown(
        r"""
        This is the **engineering mechanical energy equation** (extended Bernoulli).
        Tab 2 evaluates every term for a real transfer line. Tab 4 shows that in
        laminar pipe flow a force balance *computes* $h_f$ exactly ($f_D = 64/\mathrm{Re}$).
        """
    )

    st.markdown("### 1.2 Derivation: steady energy balance on a streamtube")
    with st.expander("🔍 From the first law to Bernoulli, without skipping the friction term", expanded=True):
        st.markdown(
            r"""
            **Step 1 — First law for an open system (steady).**
            For a control volume with one inlet and one outlet, no accumulation:
            $$\dot{m}\left(h + \frac{u^2}{2} + gz\right)_{\mathrm{in}}
            + \dot{W}_{\mathrm{shaft}} + \dot{Q}
            = \dot{m}\left(h + \frac{u^2}{2} + gz\right)_{\mathrm{out}}$$
            Enthalpy $h = \hat{u}_{\mathrm{int}} + p/\rho$ already contains flow work.

            **Step 2 — Incompressible liquid.**
            $\rho$ is constant, so $\Delta h = c_p\Delta T + \Delta p/\rho$
            (the $p/\rho$ piece is mechanical; $c_p\Delta T$ is thermal).

            **Step 3 — Split heat and dissipation.**
            Wall heat $\dot{Q}$ and *internally generated* friction both change
            internal energy. Isolate the mechanical part by defining the
            **lost work** (dissipation) per unit mass $e_f \ge 0$:
            $$\frac{p_1}{\rho} + \frac{u_1^2}{2} + gz_1 + w_{\mathrm{shaft}}
            = \frac{p_2}{\rho} + \frac{u_2^2}{2} + gz_2 + e_f$$
            Divide by $g$ to get metres of head. $e_f/g = h_f + h_{\mathrm{minor}}$.

            **Step 4 — Where viscosity lives.**
            The local dissipation rate is the contraction
            $\Phi = \boldsymbol{\tau}:\nabla\mathbf{u} = 2\mu\,\mathbf{D}:\mathbf{D} \ge 0$
            for a Newtonian fluid. Integrated over the pipe volume it *is* $\dot{m}\,e_f$.
            No viscosity $\Rightarrow$ $\Phi = 0$ $\Rightarrow$ $e_f = 0$ $\Rightarrow$
            classical Bernoulli (Tab 5 will recover the same statement from Euler).
            Viscosity is not an extra force we forgot: it is the mechanism that
            **turns organized kinetic/pressure energy into random molecular energy (heat).**

            **Step 5 — Ideal limit.**
            Steady, incompressible, $w_{\mathrm{shaft}}=0$, $e_f=0$, $\alpha=1$:
            $$p + \tfrac12\rho u^2 + \rho g z = \text{constant along the tube.}$$
            """
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
    st.markdown(
        r"""
        Order of magnitude: $e_f \approx c_p \Delta T$ if the pipe is adiabatic.
        A 100 kPa frictional drop in water is $e_f = \Delta p/\rho \approx 100$ J/kg,
        so $\Delta T \approx 0.024\,\mathrm{K}$. You will not feel it on the pipe wall.
        The *power* $\dot{m}\,e_f = Q\,\Delta p$ is the pump bill — tens of kW on a
        long header. That is why ChemE fluid mechanics is an energy subject first,
        and a tensor subject later (Tabs 5–8).
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
