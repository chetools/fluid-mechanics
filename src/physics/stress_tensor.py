"""Stress tensor and constitutive equations physics module.

Written to read as mathematics (explicit indices and contractions).
Computes:
1. Velocity gradient tensor L = grad(u)
2. Strain-rate tensor D and spin tensor Omega
3. Newtonian viscous stress tau and total Cauchy stress sigma
4. 2D fluid parcel kinematic deformation and Mohr's circle of stress
"""

from typing import Dict
import numpy as np
from scipy.linalg import expm

def decompose_velocity_gradient_2d(
    dudx: float, dudy: float,
    dvdx: float, dvdy: float
) -> Dict[str, np.ndarray]:
    """Decompose 2D velocity gradient tensor into symmetric strain rate and anti-symmetric rotation.
    
    L_ij = D_ij + Omega_ij
    D_ij = 0.5 * (L_ij + L_ji)      (Strain-rate tensor: causes friction & dissipation)
    Omega_ij = 0.5 * (L_ij - L_ji)  (Spin tensor: causes rigid rotation, zero stress)
    """
    L = np.array([
        [dudx, dudy],
        [dvdx, dvdy]
    ], dtype=float)
    
    # Symmetric strain-rate tensor D = 0.5 * (L + L^T)
    D = 0.5 * (L + L.T)
    
    # Anti-symmetric spin / rotation tensor Omega = 0.5 * (L - L^T)
    Omega = 0.5 * (L - L.T)
    
    # Volumetric dilation rate theta = div(u) = tr(D)
    dilation = np.trace(D)
    
    # Vorticity vector component in z: omega_z = dv/dx - du/dy = 2 * Omega_21
    vorticity_z = dvdx - dudy
    
    # Deviatoric strain rate tensor D_prime = D - 0.5 * tr(D) * I (in 2D)
    D_dev = D - 0.5 * dilation * np.eye(2)
    
    # Eigenvalues & principal axes of D
    eigenvalues, eigenvectors = np.linalg.eigh(D)
    
    return {
        "L": L,
        "D": D,
        "Omega": Omega,
        "dilation": dilation,
        "vorticity_z": vorticity_z,
        "D_dev": D_dev,
        "principal_strains": eigenvalues,
        "principal_axes": eigenvectors,
    }

def compute_cauchy_stress_2d(
    dudx: float, dudy: float,
    dvdx: float, dvdy: float,
    mu: float = 1.0e-3,       # Dynamic viscosity (Pa*s)
    p: float = 101325.0,      # Thermodynamic pressure (Pa)
    bulk_viscosity_ratio: float = 0.0, # Stokes' hypothesis implies 0
) -> Dict[str, np.ndarray]:
    """Calculate the complete Cauchy stress tensor for a Newtonian fluid.
    
    sigma_ij = -p * delta_ij + tau_ij
    tau_ij = 2 * mu * D_ij + lambda * (div u) * delta_ij
    Stokes' hypothesis: 3*lambda + 2*mu = 0 => lambda = -2/3*mu
    """
    decomp = decompose_velocity_gradient_2d(dudx, dudy, dvdx, dvdy)
    D = decomp["D"]
    div_u = decomp["dilation"]
    
    # Second coefficient of viscosity lambda
    # bulk viscosity zeta = lambda + 2/3 * mu => lambda = zeta - 2/3 * mu
    zeta = bulk_viscosity_ratio * mu
    lam = zeta - (2.0 / 3.0) * mu
    
    # Deviatoric viscous stress tensor tau
    tau = 2.0 * mu * D + lam * div_u * np.eye(2)
    
    # Total Cauchy stress tensor sigma = -p*I + tau
    sigma = -p * np.eye(2) + tau
    
    # Mohr's circle for stress
    # Center = (sigma_xx + sigma_yy) / 2
    # Radius = sqrt(((sigma_xx - sigma_yy)/2)^2 + tau_xy^2)
    sig_avg = 0.5 * (sigma[0, 0] + sigma[1, 1])
    sig_diff = 0.5 * (sigma[0, 0] - sigma[1, 1])
    tau_xy = sigma[0, 1]
    radius = np.sqrt(sig_diff**2 + tau_xy**2)
    
    sig_1 = sig_avg + radius
    sig_2 = sig_avg - radius
    
    # Maximum in-plane shear stress
    tau_max = radius
    
    return {
        "D": D,
        "tau": tau,
        "sigma": sigma,
        "mohr_center": sig_avg,
        "mohr_radius": radius,
        "principal_stresses": np.array([sig_1, sig_2]),
        "max_shear": tau_max,
    }

def deform_fluid_element_2d(
    dudx: float, dudy: float,
    dvdx: float, dvdy: float,
    dt: float = 0.1,
    n_points_per_side: int = 25,
) -> Dict[str, np.ndarray]:
    """Compute the physical geometric deformation of a square fluid parcel over dt.
    
    Initial geometry: unit square centered at origin [-0.5, 0.5]^2.
    For a spatially and temporally constant gradient, dx/dt = L x has the
    exact solution x(t) = exp(L t) x(0). D-only and Omega-only outlines are
    separate hypothetical flows, not additive finite-displacement components.
    """
    decomp = decompose_velocity_gradient_2d(dudx, dudy, dvdx, dvdy)
    L = decomp["L"]
    D = decomp["D"]
    Omega = decomp["Omega"]
    
    # Create perimeter of initial square
    s = np.linspace(-0.5, 0.5, n_points_per_side)
    bottom = np.column_stack([s, -0.5 * np.ones_like(s)])
    right = np.column_stack([0.5 * np.ones_like(s), s])
    top = np.column_stack([s[::-1], 0.5 * np.ones_like(s)])
    left = np.column_stack([-0.5 * np.ones_like(s), s[::-1]])
    square_initial = np.vstack([bottom, right, top, left, bottom[0]])
    
    # Internal grid lines to visualize interior shearing
    internal_lines_init = []
    for val in [-0.25, 0.0, 0.25]:
        internal_lines_init.append(np.column_stack([s, val * np.ones_like(s)]))
        internal_lines_init.append(np.column_stack([val * np.ones_like(s), s]))
        
    deformation_gradient = expm(L * dt)
    strain_gradient = expm(D * dt)
    rotation_gradient = expm(Omega * dt)
    square_full = square_initial @ deformation_gradient.T
    
    # Pure strain deformation (using D):
    square_strain_only = square_initial @ strain_gradient.T
    
    # Pure rotation (using Omega):
    square_rot_only = square_initial @ rotation_gradient.T
    
    internal_lines_full = [
        line @ deformation_gradient.T
        for line in internal_lines_init
    ]
    
    # Actual change in angle between initially orthogonal material directions.
    edge_x, edge_y = deformation_gradient[:, 0], deformation_gradient[:, 1]
    cosine = np.dot(edge_x, edge_y) / (np.linalg.norm(edge_x) * np.linalg.norm(edge_y))
    shear_angle_deg = 90.0 - np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))
    
    # Rotation of the Omega-only flow, not the polar rotation of the full map.
    rot_angle_deg = np.degrees(0.5 * (dvdx - dudy) * dt)
    
    # det(exp(L dt)) = exp(tr(L) dt): incompressible flow preserves area.
    area_ratio = np.linalg.det(deformation_gradient)
    
    return {
        "square_initial": square_initial,
        "square_full": square_full,
        "square_strain_only": square_strain_only,
        "square_rot_only": square_rot_only,
        "internal_lines_init": internal_lines_init,
        "internal_lines_full": internal_lines_full,
        "shear_angle_deg": shear_angle_deg,
        "rot_angle_deg": rot_angle_deg,
        "area_ratio": area_ratio,
        "deformation_gradient": deformation_gradient,
    }
