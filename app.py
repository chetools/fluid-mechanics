"""Fluid Mechanics: From Euler's Equation to Navier-Stokes.

Interactive educational platform with step-by-step physical derivations,
textbook-quality vector schematics, exact analytical solutions, and a live
2D Incompressible Navier-Stokes CFD solver.

Modeled after the pedagogical and visual rigor of the reference distillation project.
"""

import hashlib
import importlib
import sys
from pathlib import Path

import streamlit as st

# --- Streamlit stale-module reload guard ---
_MODULE_RELOAD_ORDER = (
    "src.theme",
    "src.units",
    "src.svg_diagrams",
    "src.physics.euler",
    "src.physics.stress_tensor",
    "src.physics.exact_solutions",
    "src.physics.numerical_solver",
    "src.physics.pipe_flow",
    "src.physics.turbulence",
    "src.physics.dimensional_analysis",
    "src.physics.boundary_layer",
    "src.physics.non_newtonian",
    "src.plotting",
    "src.ui.pedagogy",
    "src.ui.top_bar",
    "src.ui.tab_cheme_energy",
    "src.ui.tab_pipe_flow",
    "src.ui.tab_dimensional_analysis",
    "src.ui.tab_turbulence",
    "src.ui.tab_euler",
    "src.ui.tab_stress_ns",
    "src.ui.tab_solving_ns",
    "src.ui.tab_cfd",
    "src.ui.tab_reference",
)


def _source_fingerprint() -> str:
    root = Path(__file__).resolve().parent
    hasher = hashlib.sha256()
    hasher.update((root / "app.py").read_bytes())
    for name in _MODULE_RELOAD_ORDER:
        path = root / (name.replace(".", "/") + ".py")
        if path.is_file():
            hasher.update(path.read_bytes())
    return hasher.hexdigest()


@st.cache_resource
def _refresh_source_modules(fingerprint: str) -> int:
    reloaded = 0
    for name in _MODULE_RELOAD_ORDER:
        try:
            if name not in sys.modules:
                importlib.import_module(name)
            importlib.reload(sys.modules[name])
            reloaded += 1
        except Exception:
            pass
    return reloaded


_refresh_source_modules(_source_fingerprint())

import src.theme as theme
import src.units as units
from src.ui.top_bar import render_top_bar
from src.ui.pedagogy import render_concept_map
from src.ui.tab_cheme_energy import render_tab_cheme_energy
from src.ui.tab_pipe_flow import render_tab_pipe_flow
from src.ui.tab_dimensional_analysis import render_tab_dimensional_analysis
from src.ui.tab_turbulence import render_tab_turbulence
from src.ui.tab_euler import render_tab_euler
from src.ui.tab_stress_ns import render_tab_stress_ns
from src.ui.tab_solving_ns import render_tab_solving_ns
from src.ui.tab_cfd import render_tab_cfd
from src.ui.tab_reference import render_tab_reference

st.set_page_config(
    page_title="Fluid Mechanics: Euler to Navier-Stokes",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom Tailwind slate dark theme CSS
st.markdown(theme.app_css(), unsafe_allow_html=True)

# Initialize unit system state
units.init_units()

# Sidebar controls & information
with st.sidebar:
    st.markdown("### 🌊 Fluid Mechanics Simulator")
    st.markdown(
        """
        **Interactive Educational Platform**
        
        *From first-principles Euler to incompressible Navier–Stokes.*
        """
    )
    st.markdown("---")

    st.markdown("#### Global Physical Properties")
    st.caption("These properties feed **every** lab (Venturi, Couette, pipes, Mach).")
    u_ref = st.number_input("Reference Velocity U₀ [m/s]", min_value=0.1, max_value=50.0, value=2.0, step=0.5)
    l_ref = st.number_input("Characteristic Length L [m]", min_value=0.001, max_value=5.0, value=0.05, step=0.01)
    fluid_preset = st.selectbox("Fluid Preset", options=["Water (20°C)", "Air (20°C)", "Glycerin", "Custom"])

    if fluid_preset == "Custom":
        rho_ref = st.number_input("Density ρ [kg/m³]", min_value=0.1, max_value=20000.0, value=1000.0)
        mu_ref = st.number_input(
            "Dynamic Viscosity μ [Pa·s]", min_value=1e-6, max_value=10.0, value=1e-3, format="%.2e"
        )
        a_sound = st.number_input(
            "Speed of sound a [m/s]", min_value=50.0, max_value=5000.0, value=1482.0, step=10.0
        )
        kind = "liquid"
        vapor_pressure = None
    else:
        preset = units.FLUID_PRESETS[fluid_preset]
        rho_ref = preset["rho"]
        mu_ref = preset["mu"]
        a_sound = preset["speed_of_sound"]
        kind = preset["kind"]
        vapor_pressure = preset["vapor_pressure"]
        st.caption(
            f"ρ = {rho_ref:g} kg/m³ · μ = {mu_ref:.3e} Pa·s · a = {a_sound:.0f} m/s "
            f"({fluid_preset})"
        )

    units.set_fluid_state(
        name=fluid_preset,
        u_ref=u_ref,
        l_ref=l_ref,
        rho=rho_ref,
        mu=mu_ref,
        speed_of_sound=a_sound,
        vapor_pressure=vapor_pressure,
        kind=kind,
    )

    st.markdown("---")
    render_concept_map()
    st.markdown("---")
    st.markdown(
        """
        <div style="font-size: 11px; color: #94a3b8;">
            <b>Pedagogical Principles:</b><br>
            • Every step derived without skipping algebra.<br>
            • Physical intuition and geometric diagrams first.<br>
            • Display units convert; sliders stay in SI.<br>
            • Code written directly to read as mathematics.
        </div>
        """,
        unsafe_allow_html=True
    )

# Render persistent top KPI strip
render_top_bar(u_ref=u_ref, l_ref=l_ref, rho_ref=rho_ref, mu_ref=mu_ref)

# Difficulty order that still tells a plant story:
# energy → pipe design → experiments/Π → laminar f & straws → Euler → tensors → BL → CFD
tab_energy, tab_pipe, tab_dim, tab_turb, tab_euler, tab_stress, tab_exact, tab_cfd, tab_ref = st.tabs([
    "🏭 1. ChemE Energy & Bernoulli",
    "🚰 2. Pipe Flow & Pumping",
    "📐 3. Dimensional Analysis",
    "🌪️ 4. Laminar f, Turbulence & Straws",
    "⚗️ 5. Euler (1D → 3D)",
    "🧱 6. Stress & Navier–Stokes",
    "📏 7. Exact Solutions & BL",
    "💻 8. CFD (Projection)",
    "📖 9. Reference & Audit",
])

with tab_energy:
    if hasattr(render_tab_cheme_energy, "__call__"):
        render_tab_cheme_energy()

with tab_pipe:
    render_tab_pipe_flow()

with tab_dim:
    render_tab_dimensional_analysis()

with tab_turb:
    render_tab_turbulence()

with tab_euler:
    render_tab_euler()

with tab_stress:
    render_tab_stress_ns()

with tab_exact:
    render_tab_solving_ns()

with tab_cfd:
    render_tab_cfd()

with tab_ref:
    render_tab_reference()
