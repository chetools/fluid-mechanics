"""Numerical solver for 2D Incompressible Navier-Stokes equations.

Implements Chorin's Projection (Fractional Step) Method for the canonical
Lid-Driven Cavity benchmark problem.

Steps:
1. Predictor step: intermediate velocity field u*, v* from advection & diffusion
2. Pressure Poisson equation: laplacian(p) = (rho / dt) * div(u*)
3. Corrector step: project onto divergence-free subspace u^(n+1) = u* - (dt/rho)*grad(p)
4. Streamfunction & Vorticity calculation
5. Benchmark comparison with Ghia et al. (1982)
"""

from typing import Dict, Tuple
import numpy as np

# Classical literature benchmark data from Ghia, Ghia & Shin (1982) for Re=100
GHIA_RE100_Y = np.array([
    1.0000, 0.9766, 0.9688, 0.9609, 0.9531, 0.8516, 0.7344, 0.6172,
    0.5000, 0.4531, 0.2813, 0.1719, 0.1016, 0.0703, 0.0625, 0.0547, 0.0000
])
GHIA_RE100_U = np.array([
    1.0000, 0.8412, 0.7887, 0.7372, 0.6872, 0.2315, 0.0033, -0.1364,
    -0.2058, -0.2109, -0.1566, -0.1015, -0.0643, -0.0478, -0.0419, -0.0372, 0.0000
])


def suggested_timestep(
    reynolds: float,
    nx: int,
    u_lid: float = 1.0,
    lx: float = 1.0,
) -> float:
    """Explicit-step Δt limited by CFL and viscous diffusion.

    dt_CFL = 0.25 dx / U,  dt_visc = 0.15 dx² / ν.
    """
    dx = lx / max(nx - 1, 1)
    nu = (u_lid * lx) / max(reynolds, 1e-12)
    dt_cfl = 0.25 * dx / max(u_lid, 1e-12)
    dt_diff = 0.15 * dx * dx / max(nu, 1e-16)
    return float(min(dt_cfl, dt_diff))


def ghia_centerline_rmse(y: np.ndarray, u_centerline: np.ndarray) -> float:
    """RMSE of u(x=0.5, y) against Ghia et al. (1982) Re = 100 data."""
    u_at_ghia = np.interp(GHIA_RE100_Y, y, u_centerline)
    return float(np.sqrt(np.mean((u_at_ghia - GHIA_RE100_U) ** 2)))

def solve_pressure_poisson(
    p: np.ndarray,
    div_u_star: np.ndarray,
    dx: float,
    dy: float,
    rho: float,
    dt: float,
    n_iterations: int = 50,
) -> np.ndarray:
    """Solve the Pressure Poisson equation using vectorized Jacobi relaxation.
    
    laplacian(p) = (rho / dt) * div(u*)
    Neumann boundary conditions: dp/dn = 0 on all walls.
    """
    p_new = p.copy()
    dx2 = dx * dx
    dy2 = dy * dy
    factor = 0.5 * (dx2 * dy2) / (dx2 + dy2)
    rhs = (rho / dt) * div_u_star
    
    for _ in range(n_iterations):
        p_new[1:-1, 1:-1] = factor * (
            (p[1:-1, 2:] + p[1:-1, :-2]) / dx2
            + (p[2:, 1:-1] + p[:-2, 1:-1]) / dy2
            - rhs[1:-1, 1:-1]
        )
        
        # Homogeneous Neumann boundary conditions: dp/dn = 0
        p_new[:, -1] = p_new[:, -2]  # Right wall
        p_new[:, 0] = p_new[:, 1]    # Left wall
        p_new[-1, :] = p_new[-2, :]  # Top wall
        p_new[0, :] = p_new[1, :]    # Bottom wall
        
        p[:] = p_new
        
    return p

def solve_streamfunction(
    vorticity: np.ndarray,
    dx: float,
    dy: float,
    n_iterations: int = 60,
) -> np.ndarray:
    """Solve Poisson equation for streamfunction: laplacian(psi) = -omega_z.
    
    Dirichlet boundary conditions: psi = 0 on all 4 boundaries.
    """
    psi = np.zeros_like(vorticity)
    dx2 = dx * dx
    dy2 = dy * dy
    factor = 0.5 * (dx2 * dy2) / (dx2 + dy2)
    
    for _ in range(n_iterations):
        psi[1:-1, 1:-1] = factor * (
            (psi[1:-1, 2:] + psi[1:-1, :-2]) / dx2
            + (psi[2:, 1:-1] + psi[:-2, 1:-1]) / dy2
            + vorticity[1:-1, 1:-1]
        )
        # Boundaries stay 0.0 (impermeable walls)
        
    return psi

def run_lid_driven_cavity(
    reynolds: float = 100.0,
    nx: int = 41,
    ny: int = 41,
    u_lid: float = 1.0,
    n_steps: int = 250,
    dt: float = 0.001,
    poisson_iters: int = 40,
) -> Dict[str, np.ndarray]:
    """Simulate 2D Incompressible Lid-Driven Cavity flow via Chorin's Projection Method.
    
    Domain: [0, 1] x [0, 1]
    Top wall moves rightward with velocity u = u_lid.
    Other three walls are no-slip (u = 0, v = 0).
    """
    lx, ly = 1.0, 1.0
    dx = lx / (nx - 1)
    dy = ly / (ny - 1)
    
    # Grid coordinates
    x = np.linspace(0, lx, nx)
    y = np.linspace(0, ly, ny)
    X, Y = np.meshgrid(x, y)
    
    # Fluid properties: rho = 1.0, nu = u_lid * L / Re
    rho = 1.0
    nu = (u_lid * lx) / reynolds
    
    # Initialize fields
    u = np.zeros((ny, nx), dtype=float)
    v = np.zeros((ny, nx), dtype=float)
    p = np.zeros((ny, nx), dtype=float)
    
    last_div_star = np.zeros_like(u)
    last_p = p

    # Time stepping loop
    for _ in range(n_steps):
        # 1. Compute spatial derivatives for current u, v
        # Upwind/central derivatives for advection
        du_dx = (u[1:-1, 2:] - u[1:-1, :-2]) / (2.0 * dx)
        du_dy = (u[2:, 1:-1] - u[:-2, 1:-1]) / (2.0 * dy)
        dv_dx = (v[1:-1, 2:] - v[1:-1, :-2]) / (2.0 * dx)
        dv_dy = (v[2:, 1:-1] - v[:-2, 1:-1]) / (2.0 * dy)
        
        # Laplacians for viscous diffusion
        d2u_dx2 = (u[1:-1, 2:] - 2.0 * u[1:-1, 1:-1] + u[1:-1, :-2]) / (dx**2)
        d2u_dy2 = (u[2:, 1:-1] - 2.0 * u[1:-1, 1:-1] + u[:-2, 1:-1]) / (dy**2)
        d2v_dx2 = (v[1:-1, 2:] - 2.0 * v[1:-1, 1:-1] + v[1:-1, :-2]) / (dx**2)
        d2v_dy2 = (v[2:, 1:-1] - 2.0 * v[1:-1, 1:-1] + v[:-2, 1:-1]) / (dy**2)
        
        # 2. Predictor step: intermediate velocities u*, v*
        u_star = u.copy()
        v_star = v.copy()
        
        u_star[1:-1, 1:-1] = u[1:-1, 1:-1] + dt * (
            - (u[1:-1, 1:-1] * du_dx + v[1:-1, 1:-1] * du_dy)
            + nu * (d2u_dx2 + d2u_dy2)
        )
        v_star[1:-1, 1:-1] = v[1:-1, 1:-1] + dt * (
            - (u[1:-1, 1:-1] * dv_dx + v[1:-1, 1:-1] * dv_dy)
            + nu * (d2v_dx2 + d2v_dy2)
        )
        
        # Enforce intermediate boundary conditions
        u_star[-1, :] = u_lid
        u_star[0, :] = 0.0
        u_star[:, 0] = 0.0
        u_star[:, -1] = 0.0
        v_star[:, :] = 0.0  # walls impermeable
        
        # 3. Compute divergence of u*
        div_u_star = np.zeros_like(u)
        div_u_star[1:-1, 1:-1] = (
            (u_star[1:-1, 2:] - u_star[1:-1, :-2]) / (2.0 * dx)
            + (v_star[2:, 1:-1] - v_star[:-2, 1:-1]) / (2.0 * dy)
        )
        
        # 4. Solve Pressure Poisson equation
        p = solve_pressure_poisson(p, div_u_star, dx, dy, rho, dt, n_iterations=poisson_iters)
        
        # 5. Corrector step: Project velocity
        u[1:-1, 1:-1] = u_star[1:-1, 1:-1] - (dt / rho) * (p[1:-1, 2:] - p[1:-1, :-2]) / (2.0 * dx)
        v[1:-1, 1:-1] = v_star[1:-1, 1:-1] - (dt / rho) * (p[2:, 1:-1] - p[:-2, 1:-1]) / (2.0 * dy)
        
        # 6. Re-apply exact physical boundary conditions
        u[-1, :] = u_lid  # Moving top lid
        u[0, :] = 0.0     # Bottom wall
        u[:, 0] = 0.0     # Left wall
        u[:, -1] = 0.0    # Right wall
        
        v[-1, :] = 0.0
        v[0, :] = 0.0
        v[:, 0] = 0.0
        v[:, -1] = 0.0

        last_div_star = div_u_star
        last_p = p

    # Velocity magnitude
    v_mag = np.sqrt(u**2 + v**2)
    
    # Vorticity omega_z = dv/dx - du/dy
    vorticity = np.zeros_like(u)
    vorticity[1:-1, 1:-1] = (
        (v[1:-1, 2:] - v[1:-1, :-2]) / (2.0 * dx)
        - (u[2:, 1:-1] - u[:-2, 1:-1]) / (2.0 * dy)
    )
    
    # Streamfunction psi
    psi = solve_streamfunction(vorticity, dx, dy)
    
    # Centerline velocity profiles for benchmark verification
    mid_x_idx = nx // 2
    mid_y_idx = ny // 2
    u_centerline = u[:, mid_x_idx]
    v_centerline = v[mid_y_idx, :]
    
    # Divergence check
    div_final = np.zeros_like(u)
    div_final[1:-1, 1:-1] = (
        (u[1:-1, 2:] - u[1:-1, :-2]) / (2.0 * dx)
        + (v[2:, 1:-1] - v[:-2, 1:-1]) / (2.0 * dy)
    )
    max_divergence = float(np.max(np.abs(div_final[1:-1, 1:-1])))

    dx2 = dx * dx
    dy2 = dy * dy
    lap_p = np.zeros_like(last_p)
    lap_p[1:-1, 1:-1] = (
        (last_p[1:-1, 2:] - 2.0 * last_p[1:-1, 1:-1] + last_p[1:-1, :-2]) / dx2
        + (last_p[2:, 1:-1] - 2.0 * last_p[1:-1, 1:-1] + last_p[:-2, 1:-1]) / dy2
    )
    poisson_rhs = (rho / dt) * last_div_star
    poisson_residual = float(np.max(np.abs(lap_p[1:-1, 1:-1] - poisson_rhs[1:-1, 1:-1])))

    t_final = n_steps * dt
    cfl = (u_lid * dt / dx) if dx > 0 else float("inf")
    t_advect = lx / max(u_lid, 1e-12)
    t_viscous = (lx * lx) / max(nu, 1e-16)
    ghia_applicable = abs(reynolds - 100.0) < 1e-9
    ghia_rmse = ghia_centerline_rmse(y, u_centerline) if ghia_applicable else float("nan")
    # A few lid-crossing times; viscous time is Re (when U = L = 1).
    approaching_steady = t_final >= 8.0 * t_advect

    return {
        "x": x,
        "y": y,
        "X": X,
        "Y": Y,
        "u": u,
        "v": v,
        "v_mag": v_mag,
        "p": p,
        "vorticity": vorticity,
        "psi": psi,
        "u_centerline": u_centerline,
        "v_centerline": v_centerline,
        "max_divergence": max_divergence,
        "poisson_residual": poisson_residual,
        "ghia_y": GHIA_RE100_Y,
        "ghia_u": GHIA_RE100_U,
        "ghia_applicable": ghia_applicable,
        "ghia_rmse": ghia_rmse,
        "reynolds": reynolds,
        "dt": dt,
        "n_steps": n_steps,
        "t_final": t_final,
        "cfl": cfl,
        "t_advect": t_advect,
        "t_viscous": t_viscous,
        "approaching_steady": approaching_steady,
        "nx": nx,
        "ny": ny,
    }
