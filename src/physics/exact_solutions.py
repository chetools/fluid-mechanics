"""Exact analytical solutions to the Navier-Stokes equations.

Contains canonical laminar flows where non-linear convective terms vanish identically:
1. Couette flow (pure shear-driven)
2. Plane Poiseuille & Hagen-Poiseuille flow (pressure-driven)
3. Generalized Couette-Poiseuille flow (combined shear + pressure gradient)
4. Stokes' First Problem / Rayleigh Problem (unsteady momentum diffusion)
"""

from typing import Dict, Tuple
import numpy as np
from scipy.special import erfc, erfcinv


def _flux_corrections(u: np.ndarray, coord: np.ndarray, weight: np.ndarray) -> Tuple[float, float]:
    """Kinetic-energy (alpha) and momentum (beta) corrections on a discrete profile.

    alpha = (1/A) int (u/ubar)^3 dA,  beta = (1/A) int (u/ubar)^2 dA,
    with dA = weight d(coord). Undefined when the net flux is ~0 (strong reversal).
    """
    area = float(np.trapezoid(weight, coord))
    flux = float(np.trapezoid(u * weight, coord))
    if area <= 0.0 or abs(flux) < 1e-16 * max(1.0, abs(area)):
        return float("nan"), float("nan")
    shape = u * (area / flux)
    alpha = float(np.trapezoid(shape**3 * weight, coord) / area)
    beta = float(np.trapezoid(shape**2 * weight, coord) / area)
    return alpha, beta


# 1% station of erfc: u/U = erfc(eta) = 0.01 => y = 2 eta sqrt(nu t).
STOKES_ETA_ONE_PERCENT = float(erfcinv(0.01))
STOKES_DELTA_COEFF = 2.0 * STOKES_ETA_ONE_PERCENT

def couette_poiseuille_channel(
    h: float = 0.05,            # Channel height (m)
    u_wall: float = 1.0,        # Top plate velocity (m/s)
    dp_dx: float = -10.0,       # Pressure gradient dp/dx (Pa/m)
    mu: float = 1.0e-3,         # Dynamic viscosity (Pa*s)
    rho: float = 1000.0,        # Density (kg/m^3)
    n_points: int = 150,
) -> Dict[str, np.ndarray]:
    """Calculate generalized Couette-Poiseuille flow between parallel plates.
    
    Governing equation: mu * d^2u/dy^2 = dp/dx
    Boundary conditions: u(0) = 0, u(h) = U_wall
    
    Exact solution:
    u(y) = U_wall * (y/h) + (1 / (2*mu)) * (-dp/dx) * y * (h - y)
    """
    y = np.linspace(0, h, n_points)
    
    # Couette shear component
    u_couette = u_wall * (y / h)
    
    # Poiseuille parabolic pressure-driven component
    u_poiseuille = (1.0 / (2.0 * mu)) * (-dp_dx) * y * (h - y)
    
    # Total velocity
    u_total = u_couette + u_poiseuille
    
    # Shear stress profile tau(y) = mu * du/dy
    # du/dy = U_wall/h + (1/(2*mu))*(-dp_dx)*(h - 2y)
    du_dy = (u_wall / h) + (1.0 / (2.0 * mu)) * (-dp_dx) * (h - 2.0 * y)
    tau = mu * du_dy
    
    # Flow rate per unit depth Q = int_0^h u(y) dy
    q_flow = 0.5 * u_wall * h + (1.0 / (12.0 * mu)) * (-dp_dx) * (h**3)
    u_mean = q_flow / h
    
    # Nondimensional pressure parameter P = (h^2 / (2*mu*U_wall)) * (-dp/dx)
    if u_wall > 0:
        p_param = (h**2 / (2.0 * mu * u_wall)) * (-dp_dx)
    else:
        p_param = np.inf
        
    reynolds = (rho * abs(u_mean) * h) / mu if mu > 0 else np.inf

    # Plane channel: dA = dy (unit depth), A = h. Integrate on a dense grid;
    # the ~150 plot points leave a visible error in the cube. The lesson quotes
    # 54/35 for pure Poiseuille and says wall motion changes alpha, so this
    # must be the integral of the profile the sliders actually set.
    y_int = np.linspace(0.0, h, 4001)
    u_int = u_wall * (y_int / h) + (1.0 / (2.0 * mu)) * (-dp_dx) * y_int * (h - y_int)
    alpha, beta = _flux_corrections(u_int, y_int, np.ones_like(y_int))
    
    return {
        "y": y,
        "y_norm": y / h,
        "u_total": u_total,
        "u_couette": u_couette,
        "u_poiseuille": u_poiseuille,
        "tau": tau,
        "du_dy": du_dy,
        "q_flow": q_flow,
        "u_mean": u_mean,
        "p_param": p_param,
        "reynolds": reynolds,
        "tau_wall_bottom": tau[0],
        "tau_wall_top": tau[-1],
        "alpha": alpha,
        "beta": beta,
    }

def hagen_poiseuille_pipe(
    radius: float = 0.025,      # Pipe radius R (m)
    dp_dx: float = -20.0,       # Axial pressure gradient dp/dz (Pa/m)
    mu: float = 1.0e-3,         # Dynamic viscosity (Pa*s)
    rho: float = 1000.0,        # Density (kg/m^3)
    n_points: int = 150,
) -> Dict[str, np.ndarray]:
    """Calculate Hagen-Poiseuille flow in a circular pipe.
    
    Governing equation: (mu / r) * d/dr (r * du/dr) = dp/dz
    Exact solution: u(r) = (1 / (4*mu)) * (-dp/dz) * (R^2 - r^2)
    """
    r = np.linspace(0, radius, n_points)
    
    # Parabolic velocity profile
    u = (1.0 / (4.0 * mu)) * (-dp_dx) * (radius**2 - r**2)
    
    u_max = u[0]
    u_avg = 0.5 * u_max
    
    # Volumetric flow rate Q = pi * R^4 / (8 * mu) * (-dp/dx)
    flow_rate = (np.pi * radius**4 / (8.0 * mu)) * (-dp_dx)
    
    # Wall shear stress tau_w = (R / 2) * (-dp/dx)
    tau_wall = 0.5 * radius * (-dp_dx)
    
    # Pipe Reynolds number based on diameter D = 2*R
    diameter = 2.0 * radius
    reynolds = (rho * u_avg * diameter) / mu if mu > 0 else np.inf

    # Annular area element dA = 2 pi r dr; the 2 pi cancels in the ratio.
    # Dense grid: the cube of a parabola is not integrated accurately on 150 points.
    r_int = np.linspace(0.0, radius, 4001)
    u_int = (1.0 / (4.0 * mu)) * (-dp_dx) * (radius**2 - r_int**2)
    alpha, beta = _flux_corrections(u_int, r_int, r_int)
    
    return {
        "r": r,
        "r_norm": r / radius,
        "u": u,
        "u_max": u_max,
        "u_avg": u_avg,
        "flow_rate": flow_rate,
        "tau_wall": tau_wall,
        "diameter": diameter,
        "reynolds": reynolds,
        "alpha": alpha,
        "beta": beta,
    }

def stokes_first_problem(
    u_wall: float = 1.0,        # Suddenly started wall velocity (m/s)
    nu: float = 1.0e-5,         # Kinematic viscosity nu = mu/rho (m^2/s)
    times: np.ndarray = None,   # Array of evaluation times (s)
    y_max: float = None,        # Max height (m); default scales with the 1% station
    n_y: int = 200,
) -> Dict[str, np.ndarray]:
    """Calculate Stokes' First Problem (Rayleigh Problem) for unsteady viscous diffusion.
    
    Governing equation: du/dt = nu * d^2u/dy^2
    Boundary conditions: u(0, t > 0) = U_wall, u(y -> inf, t) = 0, u(y, 0) = 0
    Similarity variable: eta = y / (2 * sqrt(nu * t))
    Exact solution: u(y, t) = U_wall * erfc(eta) = U_wall * (1 - erf(eta))
    """
    if times is None:
        times = np.array([0.05, 0.2, 0.5, 1.0, 2.0])
    if y_max is None:
        t_max = float(np.max(times)) if len(times) else 1.0
        # eta = 4 at the top of the frame so the 1% station (eta ≈ 1.82) is
        # on-plot for water *and* glycerin. A fixed 80 mm window hid the
        # glycerin layer (δ ≈ 0.17 m at t = 2 s).
        y_max = 8.0 * np.sqrt(max(float(nu), 1e-16) * max(t_max, 1e-16))
        
    y = np.linspace(0, y_max, n_y)
    profiles = {}
    delta_viscous = {}
    
    for t in times:
        if t <= 0:
            profiles[t] = np.zeros_like(y)
            delta_viscous[t] = 0.0
            continue
            
        eta = y / (2.0 * np.sqrt(nu * t))
        profiles[t] = u_wall * erfc(eta)
        # Definition: u = 0.01 U_wall. Invert the exact erfc profile rather
        # than quoting 3.64.
        delta_viscous[t] = STOKES_DELTA_COEFF * np.sqrt(nu * t)
        
    return {
        "y": y,
        "times": times,
        "profiles": profiles,
        "delta_viscous": delta_viscous,
        "delta_coeff": STOKES_DELTA_COEFF,
        "eta_one_percent": STOKES_ETA_ONE_PERCENT,
        "nu": nu,
        "u_wall": u_wall,
    }
