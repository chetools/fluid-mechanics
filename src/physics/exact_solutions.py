"""Exact analytical solutions to the Navier-Stokes equations.

Contains canonical laminar flows where non-linear convective terms vanish identically:
1. Couette flow (pure shear-driven)
2. Plane Poiseuille & Hagen-Poiseuille flow (pressure-driven)
3. Generalized Couette-Poiseuille flow (combined shear + pressure gradient)
4. Stokes' First Problem / Rayleigh Problem (unsteady momentum diffusion)
"""

from typing import Dict
import numpy as np
from scipy.special import erfc

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
    }

def stokes_first_problem(
    u_wall: float = 1.0,        # Suddenly started wall velocity (m/s)
    nu: float = 1.0e-5,         # Kinematic viscosity nu = mu/rho (m^2/s)
    times: np.ndarray = None,   # Array of evaluation times (s)
    y_max: float = 0.08,        # Max height (m)
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
        
    y = np.linspace(0, y_max, n_y)
    profiles = {}
    delta_viscous = {}  # Penetration thickness where u = 0.01 * U_wall (eta ~ 1.82 => y ~ 3.64 * sqrt(nu*t))
    
    for t in times:
        if t <= 0:
            profiles[t] = np.zeros_like(y)
            delta_viscous[t] = 0.0
            continue
            
        eta = y / (2.0 * np.sqrt(nu * t))
        profiles[t] = u_wall * erfc(eta)
        delta_viscous[t] = 3.64 * np.sqrt(nu * t)
        
    return {
        "y": y,
        "times": times,
        "profiles": profiles,
        "delta_viscous": delta_viscous,
        "nu": nu,
        "u_wall": u_wall,
    }
