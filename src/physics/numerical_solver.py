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

from typing import Dict
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
    omega: float = 1.8,
) -> np.ndarray:
    """Solve the Pressure Poisson equation by red-black SOR.

    laplacian(p) = (rho / dt) * div(u*)
    Neumann boundary conditions: dp/dn = 0 on all walls.

    Jacobi needs O(N^2) sweeps to relax the longest wavelength on an N x N
    grid; successive over-relaxation with omega -> 2 needs O(N). The red-black
    ordering keeps every sweep vectorized: red points depend only on black
    neighbours and vice versa, so each half-sweep is a single NumPy expression
    that already sees the other colour's updated values (true Gauss-Seidel).

    The returned array is a new array; the caller's `p` is left unchanged.
    """
    if not 0.0 < omega < 2.0:
        raise ValueError("SOR relaxation factor must satisfy 0 < omega < 2")
    p_new = np.array(p, dtype=float, copy=True)
    dx2 = dx * dx
    dy2 = dy * dy
    factor = 0.5 * (dx2 * dy2) / (dx2 + dy2)
    rhs = (rho / dt) * div_u_star

    # Compatibility. With dp/dn = 0 on every wall, the divergence theorem forces
    # the source to integrate to zero, or no solution exists and the relaxation
    # cannot converge at all. Impermeable walls make the *continuous* net flux
    # zero, but central differences on a collocated grid decouple the even and
    # odd nodes, leaving a small nonzero discrete mean. Projecting it out is
    # what makes the residual below a meaningful convergence measure.
    rhs = rhs.copy()
    rhs[1:-1, 1:-1] -= np.mean(rhs[1:-1, 1:-1])

    # Checkerboard masks over the interior nodes.
    ny, nx = p_new.shape
    jj, ii = np.meshgrid(np.arange(ny), np.arange(nx), indexing="ij")
    red = ((ii + jj) % 2 == 0)[1:-1, 1:-1]
    black = ~red

    for _ in range(n_iterations):
        for colour in (red, black):
            gauss_seidel = factor * (
                (p_new[1:-1, 2:] + p_new[1:-1, :-2]) / dx2
                + (p_new[2:, 1:-1] + p_new[:-2, 1:-1]) / dy2
                - rhs[1:-1, 1:-1]
            )
            interior = p_new[1:-1, 1:-1]
            p_new[1:-1, 1:-1] = np.where(
                colour, interior + omega * (gauss_seidel - interior), interior
            )

        # Homogeneous Neumann boundary conditions: dp/dn = 0
        p_new[:, -1] = p_new[:, -2]  # Right wall
        p_new[:, 0] = p_new[:, 1]    # Left wall
        p_new[-1, :] = p_new[-2, :]  # Top wall
        p_new[0, :] = p_new[1, :]    # Bottom wall

    # A pure-Neumann Poisson problem fixes pressure only to a constant.
    # Pinning the mean keeps the reported field from drifting between runs;
    # only the gradient enters the projection, so this changes no velocity.
    return p_new - float(np.mean(p_new))


def poisson_residual(
    p: np.ndarray,
    div_u_star: np.ndarray,
    dx: float,
    dy: float,
    rho: float,
    dt: float,
) -> float:
    """Max interior |laplacian(p) - (rho/dt) div(u*)| for the solved field."""
    lap = np.zeros_like(p)
    lap[1:-1, 1:-1] = (
        (p[1:-1, 2:] - 2.0 * p[1:-1, 1:-1] + p[1:-1, :-2]) / (dx * dx)
        + (p[2:, 1:-1] - 2.0 * p[1:-1, 1:-1] + p[:-2, 1:-1]) / (dy * dy)
    )
    rhs = (rho / dt) * div_u_star
    return float(np.max(np.abs(lap[1:-1, 1:-1] - rhs[1:-1, 1:-1])))


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
    for name, value in (("reynolds", reynolds), ("u_lid", u_lid), ("dt", dt)):
        if not np.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and positive")
    for name, value, minimum in (("nx", nx, 3), ("ny", ny, 3),
                                 ("n_steps", n_steps, 0), ("poisson_iters", poisson_iters, 1)):
        if not isinstance(value, (int, np.integer)) or value < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}")
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
    u[-1, 1:-1] = u_lid
    
    last_div_star = np.zeros_like(u)
    last_p = p

    # Time stepping loop
    for _ in range(n_steps):
        # 1. Compute spatial derivatives for current u, v
        # Central derivatives for advection
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
        v_star[[0, -1], :] = 0.0  # walls impermeable
        v_star[:, [0, -1]] = 0.0
        
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
    u_centerline = np.array([np.interp(0.5 * lx, x, row) for row in u])
    v_centerline = np.array([np.interp(0.5 * ly, y, col) for col in v.T])
    
    # Divergence check
    div_final = np.zeros_like(u)
    div_final[1:-1, 1:-1] = (
        (u[1:-1, 2:] - u[1:-1, :-2]) / (2.0 * dx)
        + (v[2:, 1:-1] - v[:-2, 1:-1]) / (2.0 * dy)
    )
    max_divergence = float(np.max(np.abs(div_final[1:-1, 1:-1])))
    # The lid is discontinuous at the two top corners: u jumps from u_lid to 0
    # across one cell, so |div| there is O(u_lid/dx) no matter how well the
    # Poisson equation is solved. That corner singularity is a property of the
    # problem, not of the projection. Report a corner-excluded measure as well,
    # so a student can tell "the projection failed" from "the corner is singular".
    margin = 3 if min(nx, ny) >= 9 else 1
    max_divergence_interior = float(np.max(np.abs(div_final[margin:-margin, margin:-margin])))

    residual_p = poisson_residual(last_p, last_div_star, dx, dy, rho, dt)

    t_final = n_steps * dt
    cfl = (u_lid * dt / dx) if dx > 0 else float("inf")
    t_advect = lx / max(u_lid, 1e-12)
    t_viscous = (lx * lx) / max(nu, 1e-16)
    ghia_applicable = abs(reynolds - 100.0) < 1e-9
    ghia_rmse = ghia_centerline_rmse(y, u_centerline / u_lid) if ghia_applicable else float("nan")
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
        "max_divergence_interior": max_divergence_interior,
        "poisson_residual": residual_p,
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
