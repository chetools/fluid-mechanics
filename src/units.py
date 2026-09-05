"""Unit management and shared fluid state for Fluid Mechanics.

Supports SI display and true nondimensional scaling of *displayed*
metrics and plot axes. Slider widgets stay in SI so stored values do
not jump when the toggle changes. Physics always runs in SI.
"""

from typing import Dict, Optional, Tuple

import streamlit as st

UNIT_KEY = "fluid_mech_unit_system"  # 'SI' or 'NONDIM'
FLUID_KEY = "fluid_mech_fluid_state"

FLUID_PRESETS: Dict[str, Dict] = {
    "Water (20°C)": {
        "rho": 998.2,
        "mu": 1.002e-3,
        "speed_of_sound": 1482.0,
        "vapor_pressure": 2338.8,
        "kind": "liquid",
    },
    "Air (20°C)": {
        "rho": 1.204,
        "mu": 1.825e-5,
        "speed_of_sound": 343.0,
        "vapor_pressure": None,
        "kind": "gas",
    },
    "Glycerin": {
        "rho": 1261.0,
        "mu": 1.412,
        "speed_of_sound": 1904.0,
        "vapor_pressure": 0.1,
        "kind": "liquid",
    },
}

DEFAULT_FLUID = {
    "name": "Water (20°C)",
    "u_ref": 2.0,
    "l_ref": 0.05,
    "rho": 998.2,
    "mu": 1.002e-3,
    "speed_of_sound": 1482.0,
    "vapor_pressure": 2338.8,
    "kind": "liquid",
}

LABELS = {
    "SI": {
        "length": "m",
        "velocity": "m/s",
        "pressure": "Pa",
        "pressure_drop": "Pa",
        "density": "kg/m³",
        "dynamic_viscosity": "Pa·s",
        "kinematic_viscosity": "m²/s",
        "time": "s",
        "shear_stress": "Pa",
        "vorticity": "1/s",
        "flow_rate": "m³/s",
        "acceleration": "m/s²",
    },
    "NONDIM": {
        "length": "x/L [-]",
        "velocity": "u/U₀ [-]",
        "pressure": "p/(ρU₀²) [-]",
        "pressure_drop": "Eu = Δp/(ρU₀²) [-]",
        "density": "ρ/ρ₀ [-]",
        "dynamic_viscosity": "1/Re [-]",
        "kinematic_viscosity": "1/Re [-]",
        "time": "t·U₀/L [-]",
        "shear_stress": "τ/(ρU₀²) [-]",
        "vorticity": "ω·L/U₀ [-]",
        "flow_rate": "Q/(U₀ L²) [-]",
        "acceleration": "a L/U₀² [-]",
    },
}


def init_units():
    """Initialize unit system and fluid state if missing."""
    if UNIT_KEY not in st.session_state:
        st.session_state[UNIT_KEY] = "SI"
    if FLUID_KEY not in st.session_state:
        st.session_state[FLUID_KEY] = dict(DEFAULT_FLUID)


def get_unit_system() -> str:
    """Return currently active unit system ('SI' or 'NONDIM')."""
    init_units()
    return st.session_state[UNIT_KEY]


def set_unit_system(system: str):
    """Set active unit system ('SI' or 'NONDIM')."""
    st.session_state[UNIT_KEY] = system


def is_nondimensional() -> bool:
    """True if active system is Nondimensional."""
    return get_unit_system() == "NONDIM"


def set_fluid_state(
    name: str,
    u_ref: float,
    l_ref: float,
    rho: float,
    mu: float,
    speed_of_sound: float,
    vapor_pressure: Optional[float],
    kind: str,
):
    """Store the sidebar fluid so every lab reads the same properties."""
    st.session_state[FLUID_KEY] = {
        "name": name,
        "u_ref": float(u_ref),
        "l_ref": float(l_ref),
        "rho": float(rho),
        "mu": float(mu),
        "speed_of_sound": float(speed_of_sound),
        "vapor_pressure": None if vapor_pressure is None else float(vapor_pressure),
        "kind": kind,
    }


def get_fluid_state() -> Dict:
    """Return the active fluid dict (sidebar U₀, L, ρ, μ, a)."""
    init_units()
    return st.session_state[FLUID_KEY]


def si_to_display(
    value: float,
    quantity: str,
    system: str = "SI",
    refs: Optional[Dict] = None,
) -> float:
    """Convert an SI value to the requested display system.

    Nondimensional scaling uses the reference fluid. Unknown quantities
    are returned unchanged.
    """
    if system != "NONDIM" or refs is None:
        return value
    u_ref = max(float(refs.get("u_ref", 1.0)), 1e-30)
    l_ref = max(float(refs.get("l_ref", 1.0)), 1e-30)
    rho = max(float(refs.get("rho", 1.0)), 1e-30)
    mu = max(float(refs.get("mu", 1.0)), 1e-30)
    dyn_p = rho * u_ref * u_ref
    if quantity == "length":
        return value / l_ref
    if quantity == "velocity":
        return value / u_ref
    if quantity in ("pressure", "pressure_drop", "shear_stress"):
        return value / dyn_p
    if quantity == "density":
        return value / rho
    if quantity == "dynamic_viscosity":
        return value / mu
    if quantity == "kinematic_viscosity":
        return value / (mu / rho)
    if quantity == "time":
        return value * u_ref / l_ref
    if quantity == "vorticity":
        return value * l_ref / u_ref
    if quantity == "flow_rate":
        return value / (u_ref * l_ref * l_ref)
    if quantity == "acceleration":
        return value * l_ref / (u_ref * u_ref)
    return value


def unit_label(quantity: str) -> str:
    """Get the appropriate display unit label for the active unit system."""
    sys = get_unit_system()
    return LABELS[sys].get(quantity, "")


def format_quantity(value: float, quantity: str, sig_figs: int = 3) -> str:
    """Format an SI value in the active unit system, converting if needed."""
    init_units()
    system = get_unit_system()
    refs = get_fluid_state()
    display = si_to_display(value, quantity, system=system, refs=refs)
    label = unit_label(quantity)
    if abs(display) >= 1e4 or (0 < abs(display) < 1e-2):
        val_str = f"{display:.{sig_figs}e}"
    else:
        val_str = f"{display:.{sig_figs}f}"
    return f"{val_str} {label}".strip()


def calculate_reynolds(rho: float, u: float, l: float, mu: float) -> float:
    """Calculate Reynolds number Re = rho * u * l / mu."""
    if mu <= 0:
        return float("inf")
    return (rho * u * l) / mu


def calculate_mach(u: float, speed_of_sound: float = 343.0) -> float:
    """Calculate Mach number Ma = u / a for the selected fluid's speed of sound."""
    if speed_of_sound <= 0:
        return float("inf")
    return u / speed_of_sound


def calculate_cfl(u: float, dt: float, dx: float) -> float:
    """Calculate Courant-Friedrichs-Lewy (CFL) number u * dt / dx."""
    if dx <= 0:
        return float("inf")
    return u * dt / dx


def flow_regime_label(re: float) -> Tuple[str, str, str]:
    """Return (label, badge_class, description) using *pipe* Re thresholds.

    2300 / 4000 apply to circular pipes (Osborne Reynolds' apparatus),
    not to cavities, cylinders, or boundary layers.
    """
    if re < 1.0:
        return (
            "Creeping / Stokes Flow (Re < 1)",
            "pill-laminar",
            "Pipe-style Re from sidebar U₀, L. Viscous forces dominate. Not a universal geometry threshold.",
        )
    if re < 2300:
        return (
            "Laminar Flow (1 ≤ Re < 2300)",
            "pill-laminar",
            "Pipe-style Re from sidebar U₀, L. 2300 is a circular-pipe threshold, not cavity/cylinder transition.",
        )
    if re < 4000:
        return (
            "Transitional Flow (2300 ≤ Re < 4000)",
            "pill-warning",
            "Pipe-style Re from sidebar U₀, L. Intermittent puffs in a circular pipe; other geometries differ.",
        )
    return (
        "Turbulent Flow (Re ≥ 4000)",
        "pill-turbulent",
        "Pipe-style Re from sidebar U₀, L. Cavity and cylinder transition occur at different Re.",
    )
