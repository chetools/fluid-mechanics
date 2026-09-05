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
    "src.physics.pipe_network",
    "src.physics.open_channel",
    "src.physics.gas_dynamics",
    "src.physics.turbulence",
    "src.physics.dimensional_analysis",
    "src.physics.boundary_layer",
    "src.physics.transport_analogy",
    "src.physics.non_newtonian",
    "src.physics.impeller",
    "src.svg_impeller",
    "src.plotting",
    "src.ui.state",
    "src.ui.pedagogy",
    "src.ui.learning_path",
    "src.ui.top_bar",
    "src.ui.tab_cheme_energy",
    "src.ui.tab_pipe_flow",
    "src.ui.pipe_network_lab",
    "src.ui.tab_external_flow",
    "src.ui.tab_turbomachinery",
    "src.ui.tab_compressible",
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
    # This body runs only when the on-disk sources changed. Cached *data* is
    # keyed on each function's own arguments and body, so a payload whose
    # producer changed shape in another module stays cached across the reload
    # and reaches new UI code missing its new keys. Drop it with the reload.
    st.cache_data.clear()
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
from src.ui.state import persistent_input
from src.ui.top_bar import render_top_bar
from src.ui.pedagogy import render_concept_map
from src.ui.learning_path import render_chapter_header, render_chapter_recap
from src.ui.tab_cheme_energy import render_tab_cheme_energy
from src.ui.tab_pipe_flow import render_tab_pipe_flow
from src.ui.tab_dimensional_analysis import render_tab_dimensional_analysis
from src.ui.tab_turbulence import render_tab_turbulence
from src.ui.tab_euler import render_tab_euler
from src.ui.tab_stress_ns import render_tab_stress_ns
from src.ui.tab_solving_ns import render_tab_solving_ns
from src.ui.tab_cfd import render_tab_cfd
from src.ui.tab_reference import render_tab_reference
from src.ui.pipe_network_lab import render_network_lab
from src.ui.tab_external_flow import render_tab_external_flow
from src.ui.tab_turbomachinery import render_tab_turbomachinery
from src.ui.tab_compressible import render_tab_compressible

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
    st.caption("Shared by liquid, external-flow and incompressible labs. Gas-machine and compressible labs have separate thermodynamic inputs.")
    u_ref = persistent_input(st.number_input, "Reference Velocity U₀ [m/s]", min_value=0.1, max_value=50.0, value=2.0, step=0.5, key="app_reference_velocity_u_m_s")
    l_ref = persistent_input(st.number_input, "Characteristic Length L [m]", min_value=0.001, max_value=5.0, value=0.05, step=0.01, key="app_characteristic_length_l_m")
    fluid_preset = persistent_input(st.selectbox, "Fluid Preset", options=["Water (20°C)", "Air (20°C)", "Glycerin", "Custom"], key="app_fluid_preset")

    if fluid_preset == "Custom":
        rho_ref = persistent_input(st.number_input, "Density ρ [kg/m³]", min_value=0.1, max_value=20000.0, value=1000.0, key="app_density_kg_m")
        mu_ref = persistent_input(st.number_input,
            "Dynamic Viscosity μ [Pa·s]", min_value=1e-6, max_value=10.0, value=1e-3, format="%.2e", key="app_dynamic_viscosity_pa_s")
        a_sound = persistent_input(st.number_input,
            "Speed of sound a [m/s]", min_value=50.0, max_value=5000.0, value=1482.0, step=10.0, key="app_speed_of_sound_a_m_s")
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

# A short orientation before the controls and chapter navigation.
st.markdown('''<div class="course-intro"><div class="chapter-eyebrow">THE FLUID MECHANICS LAB</div>
<h1>From a pressure drop<br>to the equations of motion.</h1>
<p>Twelve connected lessons. Build the physical picture, follow the mathematics,
then test your prediction in a live experiment.</p>
<div class="course-route"><span>01 · Plant balances</span><span>02 · Scaling &amp; regimes</span>
<span>03 · Local momentum</span><span>04 · External flow</span><span>05 · Gas &amp; shaft work</span><span>06 · CFD verification</span></div></div>''', unsafe_allow_html=True)
st.caption("Start at chapter 1, or choose a chapter below. Detailed proofs unfold on demand. Open the sidebar to change the shared fluid.")

# Render persistent top KPI strip
render_top_bar(u_ref=u_ref, l_ref=l_ref, rho_ref=rho_ref, mu_ref=mu_ref)

# Difficulty order that still tells a plant story:
# energy → pipe design → experiments/Π → laminar f & straws → Euler → tensors → BL → CFD
#
# One chapter is rendered at a time, and this is not a cosmetic choice.
# `st.tabs` executes every panel body on every script run, so all twelve
# chapters — every Plotly figure, every SVG, every solver call — were rebuilt
# whenever any widget moved. Once the course grew past roughly a hundred
# elements the browser stopped finishing the render: the script completed in
# Python (AppTest saw all 103 metrics, no exception) while the page stalled
# part-way through chapter 9 with the running indicator still showing. That was
# reproduced on a freshly started server and confirmed by bisection — skipping
# chapters 1–6 let chapter 9 render to completion. Rendering one chapter is the
# fix; see docs/DEVELOPMENT_NOTES.md before changing it back.
CHAPTERS = (
    ("1 · Energy", 1, lambda: render_tab_cheme_energy()),
    ("2 · Pipes", 2, lambda: (render_tab_pipe_flow(), render_network_lab())),
    ("3 · Scaling", 3, lambda: render_tab_dimensional_analysis()),
    ("4 · Turbulence", 4, lambda: render_tab_turbulence()),
    ("5 · Euler", 5, lambda: render_tab_euler()),
    ("6 · Stress & NS", 6, lambda: render_tab_stress_ns()),
    ("7 · Exact flows", 7, lambda: render_tab_solving_ns()),
    ("8 · External flow", 8, lambda: render_tab_external_flow()),
    ("9 · Turbomachinery", 9, lambda: render_tab_turbomachinery()),
    ("10 · Compressible", 10, lambda: render_tab_compressible()),
    ("11 · CFD", 11, lambda: render_tab_cfd()),
    ("12 · Reference", 12, lambda: render_tab_reference()),
)

selected = st.radio(
    "Chapter",
    options=[label for label, _, _ in CHAPTERS],
    horizontal=True,
    label_visibility="collapsed",
    key="chapter_nav",
)

for label, number, render in CHAPTERS:
    if label == selected:
        render_chapter_header(number)
        render()
        render_chapter_recap(number)
        break
