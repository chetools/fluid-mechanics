"""Persistent top KPI bar for fluid mechanics state variables.

Displays real-time Reynolds number, Mach number, flow regime badge,
dynamic pressure head, and active unit system toggle.
"""

import streamlit as st
from src.units import (
    get_unit_system, set_unit_system, calculate_reynolds,
    calculate_mach, flow_regime_label, format_quantity, get_fluid_state
)

def render_top_bar(
    u_ref: float = 2.0,
    l_ref: float = 0.05,
    rho_ref: float = 1000.0,
    mu_ref: float = 1.0e-3,
):
    """Render the persistent top KPI strip with dynamic cards."""
    fluid = get_fluid_state()
    reynolds = calculate_reynolds(rho_ref, u_ref, l_ref, mu_ref)
    mach = calculate_mach(u_ref, speed_of_sound=float(fluid.get("speed_of_sound", 343.0)))
    q_dyn = 0.5 * rho_ref * u_ref**2
    regime_text, badge_class, regime_desc = flow_regime_label(reynolds)
    current_unit = get_unit_system()
    
    col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns([1.3, 1.1, 1.1, 1.1, 1.1])
    
    with col_kpi1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-card-title">Flow Regime State</div>
                <div class="metric-card-value">
                    <span class="pill-badge {badge_class}">{regime_text.split('(')[0].strip()}</span>
                </div>
                <div class="metric-card-sub">Pipe-style Re from sidebar U₀, L</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with col_kpi2:
        re_str = f"{reynolds:,.1f}" if reynolds < 1e5 else f"{reynolds:.2e}"
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-card-title">Reynolds Number</div>
                <div class="metric-card-value">Re = {re_str}</div>
                <div class="metric-card-sub">Inertia / Viscous forces</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with col_kpi3:
        a_sound = float(fluid.get("speed_of_sound", 343.0))
        ma_note = "Ma < 0.3" if mach < 0.3 else "Ma ≥ 0.3 (density varies)"
        mach_status = f"{ma_note} · a = {a_sound:.0f} m/s ({fluid.get('name', 'fluid')})"
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-card-title">Mach Number</div>
                <div class="metric-card-value">Ma = {mach:.3f}</div>
                <div class="metric-card-sub">{mach_status}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with col_kpi4:
        q_str = format_quantity(q_dyn, "pressure")
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-card-title">Dynamic Pressure</div>
                <div class="metric-card-value">{q_str}</div>
                <div class="metric-card-sub">q = ½ ρ u²</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with col_kpi5:
        st.caption("DISPLAY UNITS")
        unit_choice = st.selectbox(
            "Units",
            options=["SI (Metric)", "Nondimensional [-]"],
            index=0 if current_unit == "SI" else 1,
            label_visibility="collapsed",
            key="unit_toggle_select",
            help="Converts displayed metrics and plot axes using sidebar U₀, L, ρ. Sliders stay in SI.",
        )
        selected_unit_sys = "SI" if "SI" in unit_choice else "NONDIM"
        if selected_unit_sys != current_unit:
            set_unit_system(selected_unit_sys)
            st.rerun()
            
        st.caption("Controls stay in SI.")
