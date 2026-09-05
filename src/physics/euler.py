"""Euler's Equation physics and mathematical models.

Contains:
1. 1D differential momentum balance & Venturi nozzle physics
2. Streamline trajectory & Bernoulli invariant evaluation
3. 2D Potential flow past a cylinder & d'Alembert's paradox calculation
"""

from typing import Dict
import numpy as np

def venturi_profile(
    x_span: float = 1.0,
    d_inlet: float = 0.1,
    d_throat: float = 0.04,
    d_outlet: float = 0.1,
    flow_rate: float = 0.02,   # m^3/s
    p_inlet: float = 101325.0, # Pa
    rho: float = 1000.0,       # kg/m^3
    n_points: int = 200,
) -> Dict[str, np.ndarray]:
    """Calculate 1D flow through a converging-diverging Venturi tube.
    
    Geometry: Smooth cosine blend between inlet, throat (at x=0.4L) and outlet.
    Solves 1D mass conservation A(x)*u(x) = Q and Euler momentum p(x) + 0.5*rho*u(x)^2 = const.
    """
    x = np.linspace(0, x_span, n_points)
    x_throat = 0.4 * x_span
    
    # Smooth diameter profile
    d = np.zeros_like(x)
    for i, xi in enumerate(x):
        if xi <= x_throat:
            # Converging section
            s = xi / x_throat
            d[i] = d_inlet - (d_inlet - d_throat) * (0.5 - 0.5 * np.cos(np.pi * s))
        else:
            # Diverging section
            s = (xi - x_throat) / (x_span - x_throat)
            d[i] = d_throat + (d_outlet - d_throat) * (0.5 - 0.5 * np.cos(np.pi * s))
            
    area = 0.25 * np.pi * d**2
    velocity = flow_rate / area
    
    # Material derivative acceleration a = u * du/dx
    du_dx = np.gradient(velocity, x)
    convective_acc = velocity * du_dx
    
    # Euler pressure gradient: dp/dx = - rho * u * du/dx
    dp_dx = - rho * convective_acc
    
    # Bernoulli pressure profile: p(x) = p_inlet + 0.5*rho*(u_inlet^2 - u(x)^2)
    u_inlet = velocity[0]
    p_dyn_inlet = 0.5 * rho * u_inlet**2
    pressure = p_inlet + p_dyn_inlet - 0.5 * rho * velocity**2
    
    # Total head (Bernoulli constant)
    total_pressure = pressure + 0.5 * rho * velocity**2
    
    return {
        "x": x,
        "diameter": d,
        "area": area,
        "velocity": velocity,
        "convective_acc": convective_acc,
        "dp_dx": dp_dx,
        "pressure": pressure,
        "total_pressure": total_pressure,
        "p_throat": pressure[np.argmin(d)],
        "u_throat": velocity[np.argmin(d)],
        "delta_p": pressure[0] - pressure[np.argmin(d)],
        "rho": rho,
        "flow_rate": flow_rate,
        "p_inlet": p_inlet,
        "kinetic": 0.5 * rho * velocity**2,
    }

def cylinder_potential_flow(
    radius: float = 1.0,
    u_inf: float = 5.0,
    rho: float = 1.225,
    p_inf: float = 101325.0,
    grid_size: int = 100,
    box_size: float = 3.0,
) -> Dict[str, np.ndarray]:
    """Calculate 2D potential (inviscid) flow past a circular cylinder.
    
    Uses streamfunction psi = U_inf * (r - R^2/r) * sin(theta).
    Evaluates velocities, pressure coefficient, and rigorously integrates
    surface pressure to demonstrate d'Alembert's paradox (zero drag).
    """
    x = np.linspace(-box_size, box_size, grid_size)
    y = np.linspace(-box_size, box_size, grid_size)
    X, Y = np.meshgrid(x, y)
    
    R_sq = X**2 + Y**2
    R = np.sqrt(R_sq)
    Theta = np.arctan2(Y, X)
    
    # Mask inside cylinder
    inside = R < radius
    
    # Radial and azimuthal velocities
    with np.errstate(divide='ignore', invalid='ignore'):
        ur = u_inf * (1.0 - (radius**2) / R_sq) * np.cos(Theta)
        utheta = -u_inf * (1.0 + (radius**2) / R_sq) * np.sin(Theta)
        
        # Cartesian velocity components:
        # u = ur * cos(theta) - utheta * sin(theta)
        # v = ur * sin(theta) + utheta * cos(theta)
        U = ur * np.cos(Theta) - utheta * np.sin(Theta)
        V = ur * np.sin(Theta) + utheta * np.cos(Theta)
        
        # Streamfunction: psi = U_inf * (r - R^2/r) * sin(theta)
        Psi = u_inf * (R - (radius**2) / R) * np.sin(Theta)
        
        # Velocity magnitude
        V_mag = np.sqrt(U**2 + V**2)
        
        # Pressure via Bernoulli: p + 0.5*rho*V^2 = p_inf + 0.5*rho*u_inf^2
        Pressure = p_inf + 0.5 * rho * (u_inf**2 - V_mag**2)
        Cp = (Pressure - p_inf) / (0.5 * rho * u_inf**2)
        
    # Mask out the interior of the cylinder
    U[inside] = np.nan
    V[inside] = np.nan
    Psi[inside] = 0.0
    Pressure[inside] = np.nan
    Cp[inside] = np.nan
    
    # Surface pressure profile around cylinder (theta from 0 to 2*pi)
    theta_surf = np.linspace(0, 2 * np.pi, 360, endpoint=False)
    # At r = R: ur = 0, utheta = -2 * U_inf * sin(theta)
    cp_surf = 1.0 - 4.0 * (np.sin(theta_surf)**2)
    p_surf = p_inf + 0.5 * rho * u_inf**2 * cp_surf
    
    # Numerical integration of Drag and Lift forces per unit depth
    # dFx = - p * cos(theta) * R * dtheta
    # dFy = - p * sin(theta) * R * dtheta
    d_theta = 2.0 * np.pi / len(theta_surf)
    drag_force = - np.sum(p_surf * np.cos(theta_surf)) * radius * d_theta
    lift_force = - np.sum(p_surf * np.sin(theta_surf)) * radius * d_theta
    
    return {
        "x": x,
        "y": y,
        "X": X,
        "Y": Y,
        "U": U,
        "V": V,
        "Psi": Psi,
        "Pressure": Pressure,
        "Cp": Cp,
        "theta_surf": theta_surf,
        "cp_surf": cp_surf,
        "drag_force": drag_force,
        "lift_force": lift_force,
        "radius": radius,
        "u_inf": u_inf,
        "rho": rho,
    }
