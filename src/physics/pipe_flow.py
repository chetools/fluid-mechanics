"""Pipe flow physics, friction factor correlations, and Chemical Engineering piping design.

Implements:
1. Darcy-Weisbach & Fanning friction calculations
2. Churchill (1977) continuous correlation across laminar, transition & turbulent regimes
3. Colebrook-White implicit root solve
4. Piping network fittings / minor losses (equivalent lengths & K_L factors)
5. Pump sizing, total dynamic head (TDH), brake horsepower & operating cost
6. Hydraulic diameter for non-circular channels and heat exchanger annuli
"""

from typing import Dict
import numpy as np

# Standard commercial pipe roughness values (in meters)
PIPE_ROUGHNESS = {
    "Commercial Steel / Wrought Iron": 4.5e-5,
    "Drawn Tubing (Copper, Brass, Plastic)": 1.5e-6,
    "Stainless Steel": 1.5e-5,
    "Cast Iron": 2.6e-4,
    "Galvanized Iron": 1.5e-4,
    "Smooth Glass / PVC": 0.0,
}

# Chemical Engineering Standard Fitting K_L factors (Crane Technical Paper 410)
FITTING_K_FACTORS = {
    "90° Standard Elbow": 0.75,
    "90° Long Radius Elbow": 0.45,
    "45° Standard Elbow": 0.35,
    "Tee (Flow through run)": 0.40,
    "Tee (Flow through branch)": 1.50,
    "Gate Valve (Fully Open)": 0.17,
    "Gate Valve (Half Open)": 4.50,
    "Globe Valve (Fully Open)": 6.00,
    "Ball Valve (Fully Open)": 0.05,
    "Check Valve (Swing type)": 2.00,
    "Pipe Inlet (Square edge)": 0.50,
    "Pipe Outlet (Discharge to tank)": 1.00,
}

def friction_factor_churchill(reynolds: float, rel_roughness: float) -> float:
    """Calculate Darcy friction factor f_D using Churchill's (1977) universal correlation.
    
    Valid across laminar, critical/transitional, and fully turbulent rough pipe regimes.
    f_D = 8 * [ (8/Re)^12 + (A + B)^(-1.5) ]^(1/12)
    """
    if reynolds <= 0:
        return float("nan")
    if reynolds < 1.0:
        # Avoid large powers and retain the creeping-flow limit at tiny Re.
        return 64.0 / reynolds
        
    Re = max(reynolds, 1e-4)
    eps_D = max(rel_roughness, 0.0)
    
    # Laminar term
    term_lam = (8.0 / Re)**12
    
    # Turbulent term A
    term_inside_ln = (7.0 / Re)**0.9 + 0.27 * eps_D
    term_inside_ln = max(term_inside_ln, 1e-12)
    A = (2.457 * np.log(1.0 / term_inside_ln))**16
    
    # Transition term B
    B = (37530.0 / Re)**16
    
    f_darcy = 8.0 * ((term_lam + (A + B)**(-1.5))**(1.0 / 12.0))
    return float(f_darcy)

def solve_colebrook_white(reynolds: float, rel_roughness: float, max_iter: int = 50) -> float:
    """Solve Colebrook-White equation for turbulent Darcy friction factor via Newton-Raphson.
    
    1 / sqrt(f) = -2.0 * log10( (eps/D)/3.7 + 2.51 / (Re * sqrt(f)) )
    """
    if reynolds <= 0:
        return float("nan")
    if reynolds < 2300.0:
        return 64.0 / reynolds
        
    eps_D = max(rel_roughness, 0.0)
    # Initial guess from Haaland equation
    f = (-1.8 * np.log10((eps_D / 3.7)**1.11 + 6.9 / reynolds))**(-2)
    
    for _ in range(max_iter):
        sqrt_f = np.sqrt(f)
        arg = (eps_D / 3.7) + (2.51 / (reynolds * sqrt_f))
        F_val = 1.0 / sqrt_f + 2.0 * np.log10(arg)
        # Numerical derivative
        df = -0.5 * (f**(-1.5)) + (2.0 / (np.log(10.0) * arg)) * (-1.255 / (reynolds * (f**1.5)))
        f_next = f - F_val / df
        if abs(f_next - f) < 1e-7:
            return float(f_next)
        f = max(f_next, 1e-5)
        
    return float(f)

def generate_moody_chart_data() -> Dict[str, np.ndarray]:
    """Precompute curves for generating the complete interactive Moody Chart."""
    # Laminar line: Re from 500 to 2300
    re_lam = np.logspace(np.log10(500), np.log10(2300), 50)
    f_lam = 64.0 / re_lam
    
    # Turbulent curves: Re from 3000 to 1e8
    re_turb = np.logspace(np.log10(3000), np.log10(1e8), 120)
    roughness_levels = [0.0, 1e-5, 5e-5, 1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 2e-2, 5e-2]
    
    turb_curves = {}
    for eps in roughness_levels:
        f_vals = np.array([friction_factor_churchill(re, eps) for re in re_turb])
        turb_curves[eps] = f_vals
        
    return {
        "re_lam": re_lam,
        "f_lam": f_lam,
        "re_turb": re_turb,
        "roughness_levels": roughness_levels,
        "turb_curves": turb_curves,
    }

def calculate_cheme_pipe_system(
    flow_rate: float,            # m^3/h
    pipe_diameter_inner: float,  # m
    pipe_length: float,          # m
    roughness: float,            # m
    density: float,              # kg/m^3
    viscosity: float,            # Pa*s
    elevation_gain: float = 0.0, # m
    fittings_counts: Dict[str, int] = None,
    pump_efficiency: float = 0.70,
    electricity_cost_kwh: float = 0.12, # $/kWh
) -> Dict:
    """Calculate complete chemical engineering pipe pressure drop and pump power specs."""
    if fittings_counts is None:
        fittings_counts = {"90° Standard Elbow": 4, "Gate Valve (Fully Open)": 2}
        
    q_m3_s = flow_rate / 3600.0  # convert m^3/h to m^3/s
    area = 0.25 * np.pi * pipe_diameter_inner**2
    velocity = q_m3_s / area if area > 0 else 0.0
    
    # Reynolds number
    reynolds = (density * velocity * pipe_diameter_inner) / viscosity if viscosity > 0 else float("inf")
    rel_roughness = roughness / pipe_diameter_inner
    
    # Friction factors
    f_darcy = friction_factor_churchill(reynolds, rel_roughness)
    f_fanning = f_darcy / 4.0
    
    # Major head loss (pipe skin friction)
    dyn_head = 0.5 * density * velocity**2
    delta_p_major = 0.0 if velocity == 0 else f_darcy * (pipe_length / pipe_diameter_inner) * dyn_head
    h_loss_major = delta_p_major / (density * 9.81)
    
    # Minor head loss (valves & fittings)
    k_total = sum(FITTING_K_FACTORS.get(name, 0.0) * count for name, count in fittings_counts.items())
    delta_p_minor = k_total * dyn_head
    h_loss_minor = delta_p_minor / (density * 9.81)
    
    # Static head loss
    delta_p_static = density * 9.81 * elevation_gain
    h_static = elevation_gain
    
    # Total pressure drop & head
    delta_p_total = delta_p_major + delta_p_minor + delta_p_static
    h_total = h_loss_major + h_loss_minor + h_static
    
    # Pump power
    p_hydraulic_watts = q_m3_s * delta_p_total
    p_shaft_watts = p_hydraulic_watts / pump_efficiency if pump_efficiency > 0 else 0.0
    p_shaft_kw = p_shaft_watts / 1000.0
    p_shaft_hp = p_shaft_kw * 1.34102
    
    # Annual energy consumption and cost (assuming continuous 8000 hrs/yr operation)
    annual_kwh = p_shaft_kw * 8000.0
    annual_cost = annual_kwh * electricity_cost_kwh
    
    return {
        "velocity": velocity,
        "reynolds": reynolds,
        "rel_roughness": rel_roughness,
        "f_darcy": f_darcy,
        "f_fanning": f_fanning,
        "dyn_head": dyn_head,
        "k_total": k_total,
        "delta_p_major": delta_p_major,
        "delta_p_minor": delta_p_minor,
        "delta_p_static": delta_p_static,
        "delta_p_total": delta_p_total,
        "h_loss_major": h_loss_major,
        "h_loss_minor": h_loss_minor,
        "h_total": h_total,
        "p_hydraulic_kw": p_hydraulic_watts / 1000.0,
        "p_shaft_kw": p_shaft_kw,
        "p_shaft_hp": p_shaft_hp,
        "annual_cost": annual_cost,
    }

def hydraulic_diameter(geometry_type: str, dim1: float, dim2: float = 0.0) -> float:
    """Calculate hydraulic diameter D_H = 4 * Area / Wetted_Perimeter.
    
    Types:
    - 'circular': dim1 = Diameter D
    - 'annulus': dim1 = Outer Diameter D_o, dim2 = Inner Diameter D_i
    - 'rectangular': dim1 = Width a, dim2 = Height b
    """
    if geometry_type == "circular":
        return dim1
    elif geometry_type == "annulus":
        # D_H = 4 * (pi/4 * (Do^2 - Di^2)) / (pi * (Do + Di)) = Do - Di
        return dim1 - dim2
    elif geometry_type == "rectangular":
        # D_H = 4 * (a * b) / (2*(a + b)) = 2 * a * b / (a + b)
        return (2.0 * dim1 * dim2) / (dim1 + dim2)
    return dim1


def entrance_length(diameter: float, reynolds: float) -> Dict:
    """Hydrodynamic entrance length L_e for a circular pipe.

    Laminar (Re < 2300): L_e/D ≈ 0.06 Re  (fully developed parabola).
    Turbulent (Re > 4000): L_e/D ≈ 4.4 Re^{1/6}  (White).
    Transition: report both and take the larger (conservative).
    """
    D = float(max(diameter, 1e-12))
    re = float(max(reynolds, 0.0))
    le_d_lam = 0.06 * re
    le_d_turb = 4.4 * (re ** (1.0 / 6.0)) if re > 0 else 0.0
    if re < 2300:
        regime = "laminar"
        le_d = le_d_lam
    elif re > 4000:
        regime = "turbulent"
        le_d = le_d_turb
    else:
        regime = "transitional"
        le_d = max(le_d_lam, le_d_turb)
    return {
        "L_e": le_d * D,
        "L_e_over_D": le_d,
        "L_e_over_D_laminar": le_d_lam,
        "L_e_over_D_turbulent": le_d_turb,
        "regime": regime,
        "reynolds": re,
        "diameter": D,
    }


def npsh_available(
    p_tank_abs: float,
    z_surface: float,
    p_vapor: float,
    density: float,
    viscosity: float,
    suction_length: float,
    suction_diameter: float,
    roughness: float,
    flow_rate_m3s: float,
    fittings_counts: Dict[str, int] = None,
) -> Dict:
    """Available NPSH at a pump suction from a free-surface tank.

    NPSH_A = (P_tank − P_v)/(ρ g) + z − h_f
    z > 0 is a flooded suction (surface above the pump centerline);
    z < 0 is a suction lift. P_tank is absolute. Velocity head at the
    impeller eye is charged to NPSH_R, not to NPSH_A.
    """
    if fittings_counts is None:
        fittings_counts = {}
    g = 9.81
    D = float(max(suction_diameter, 1e-9))
    area = 0.25 * np.pi * D * D
    velocity = flow_rate_m3s / area if area > 0 else 0.0
    reynolds = (density * velocity * D) / viscosity if viscosity > 0 else float("inf")
    rel_rough = roughness / D
    f_d = friction_factor_churchill(reynolds, rel_rough)
    k_total = sum(
        FITTING_K_FACTORS.get(name, 0.0) * count for name, count in fittings_counts.items()
    )
    h_friction = 0.0 if velocity == 0 else f_d * (suction_length / D) * (velocity**2) / (2.0 * g)
    h_minor = k_total * (velocity**2) / (2.0 * g)
    h_f = h_friction + h_minor
    static_abs = (p_tank_abs - p_vapor) / (density * g) if density > 0 else 0.0
    npsh_a = static_abs + z_surface - h_f
    return {
        "npsh_a": npsh_a,
        "static_term": static_abs,
        "z_surface": z_surface,
        "h_friction": h_friction,
        "h_minor": h_minor,
        "h_f": h_f,
        "velocity": velocity,
        "reynolds": reynolds,
        "f_darcy": f_d,
        "k_total": k_total,
        "p_tank_abs": p_tank_abs,
        "p_vapor": p_vapor,
    }


def laminar_darcy_from_force_balance(reynolds: float) -> float:
    """Darcy f_D = 64/Re from a cylindrical force balance + Newton’s law.

    Δp π r² = τ 2π r L  ⇒  τ = (r/2)(−dp/dx).
    τ = μ (−du/dr) integrates to Hagen–Poiseuille, then
    f_D ≡ 2 Δp D / (L ρ u²) = 64/Re.
    """
    if reynolds <= 0:
        return float("nan")
    return 64.0 / reynolds


def straw_bundle_comparison(
    flow_rate: float,
    outer_diameter: float,
    length: float,
    density: float,
    viscosity: float,
    n_straws: int,
    packing_fraction: float = 0.85,
    roughness: float = 0.0,
) -> Dict:
    """Open pipe vs N parallel capillaries that fill the same envelope.

    Same total Q and outer diameter D. Each straw has
    d = D sqrt(φ / N). Δp of a laminar bundle scales ~ N / φ²,
    so packing straws to stay laminar usually *raises* pumping power.
    """
    D = float(max(outer_diameter, 1e-6))
    L = float(max(length, 1e-6))
    Q = float(abs(flow_rate))
    N = int(max(n_straws, 1))
    phi = float(np.clip(packing_fraction, 0.05, 1.0))
    area_open = 0.25 * np.pi * D * D
    u_open = Q / area_open if area_open > 0 else 0.0
    re_open = (density * u_open * D) / viscosity if viscosity > 0 else float("inf")
    f_open = friction_factor_churchill(re_open, roughness / D)
    dp_open = 0.0 if Q == 0 else f_open * (L / D) * 0.5 * density * u_open * u_open

    d = D * np.sqrt(phi / N)
    q_i = Q / N
    area_i = 0.25 * np.pi * d * d
    u_i = q_i / area_i if area_i > 0 else 0.0
    re_i = (density * u_i * d) / viscosity if viscosity > 0 else float("inf")
    f_i = friction_factor_churchill(re_i, 0.0)
    dp_bundle = 0.0 if Q == 0 else f_i * (L / d) * 0.5 * density * u_i * u_i
    dp_lam_exact = (128.0 * viscosity * L * q_i) / (np.pi * d**4) if d > 0 else float("inf")
    return {
        "n_straws": N,
        "packing_fraction": phi,
        "d_straw": d,
        "u_open": u_open,
        "re_open": re_open,
        "f_open": f_open,
        "dp_open": dp_open,
        "power_open": Q * dp_open,
        "u_straw": u_i,
        "re_straw": re_i,
        "f_straw": f_i,
        "dp_bundle": dp_bundle,
        "dp_laminar_exact": dp_lam_exact,
        "power_bundle": Q * dp_bundle,
        "power_ratio": (Q * dp_bundle) / (Q * dp_open) if dp_open > 0 else float("inf"),
        "open_laminar": re_open < 2300,
        "straw_laminar": re_i < 2300,
    }
