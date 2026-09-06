"""Fluid Mechanics.

Twelve chapters in six parts: vector schematics, exact analytical solutions
and a live 2D incompressible CFD solver.

src/ui/learning_path.py names the parts and chapters; this module only
arranges them.
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
from src.ui.learning_path import (
    chapter_labels,
    render_chapter_header,
    render_chapter_recap,
    render_concept_map,
)
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
    page_title="Fluid Mechanics",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom Tailwind slate dark theme CSS
st.markdown(theme.app_css(), unsafe_allow_html=True)

# Initialize unit system state
units.init_units()

# Sidebar controls & information.
with st.sidebar:
    st.markdown("### 🌊 Fluid Mechanics")
    st.markdown("---")

    st.markdown("#### Shared fluid")
    st.caption(
        "Sets ρ, μ, a and vapour pressure for the liquid, incompressible and "
        "external-flow labs. The gas-machine and compressible chapters take their "
        "own thermodynamic inputs and ignore this."
    )
    fluid_preset = persistent_input(st.selectbox, "Fluid preset", options=["Water (20°C)", "Air (20°C)", "Glycerin", "Custom"], key="app_fluid_preset")

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

    st.markdown("#### Display units")
    unit_choice = persistent_input(
        st.selectbox,
        "Show quantities as",
        options=["SI (metric)", "Nondimensional [-]"],
        key="unit_toggle_select",
        help=(
            "Nondimensional mode divides displayed metrics and plot axes by the "
            "reference scales below. Every slider stays in SI."
        ),
    )
    # Set it, but do NOT st.rerun() here. The sidebar runs before every chapter,
    # so the new system is already in force for this pass. Rerunning from this
    # point aborts the script before the chapter radio is instantiated, and
    # Streamlit then garbage-collects the state of a widget that no completed
    # run created -- which silently threw the reader back to chapter 1.
    selected_unit_sys = "SI" if "SI" in unit_choice else "NONDIM"
    if selected_unit_sys != units.get_unit_system():
        units.set_unit_system(selected_unit_sys)

    with st.expander("Reference scales for nondimensional display", expanded=False):
        st.caption(
            "These two numbers scale the *display* only. No lab reads them: every "
            "chapter builds its own velocity and length from its own inputs."
        )
        u_ref = persistent_input(st.number_input, "Reference velocity U₀ [m/s]", min_value=0.1, max_value=50.0, value=2.0, step=0.5, key="app_reference_velocity_u_m_s")
        l_ref = persistent_input(st.number_input, "Reference length L [m]", min_value=0.001, max_value=5.0, value=0.05, step=0.01, key="app_characteristic_length_l_m")

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
            <b>Conventions</b><br>
            • Equations are derived from a stated balance.<br>
            • The physical picture and the geometry come before the algebra.<br>
            • Claimed constants are computed, not quoted.<br>
            • Display units convert; sliders stay in SI.
        </div>
        """,
        unsafe_allow_html=True
    )

# The only genuinely global state, stated once, instead of a strip of KPI cards
# computing a Reynolds number from reference scales that no chapter reads.
_units_note = (
    "SI" if units.get_unit_system() == "SI"
    else f"nondimensional on U₀ = {u_ref:g} m/s, L = {l_ref:g} m"
)
st.caption(
    f"**Shared fluid:** {fluid_preset} · ρ = {rho_ref:g} kg/m³ · μ = {mu_ref:.3e} Pa·s "
    f"· a = {a_sound:.0f} m/s · **display:** {_units_note}. Change it in the sidebar."
)

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
#
# The labels come from src.ui.learning_path, which also names the six parts and
# titles each chapter, so the navigation, the banner route and the chapter
# headings cannot drift apart.
RENDERERS = (
    lambda: render_tab_cheme_energy(),
    lambda: (render_tab_pipe_flow(), render_network_lab()),
    lambda: render_tab_dimensional_analysis(),
    lambda: render_tab_turbulence(),
    lambda: render_tab_euler(),
    lambda: render_tab_stress_ns(),
    lambda: render_tab_solving_ns(),
    lambda: render_tab_external_flow(),
    lambda: render_tab_turbomachinery(),
    lambda: render_tab_compressible(),
    lambda: render_tab_cfd(),
    lambda: render_tab_reference(),
)
CHAPTERS = tuple(
    (label, number, render)
    for number, (label, render) in enumerate(zip(chapter_labels(), RENDERERS), 1)
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
