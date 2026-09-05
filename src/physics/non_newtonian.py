"""Ostwald–de Waele (power-law) constitutive model and laminar pipe flow.

τ = K |γ̇|^{n−1} γ̇
n = 1, K = μ recovers a Newtonian fluid.
n < 1 shear-thinning (pseudoplastic: polymer melts, blood).
n > 1 shear-thickening (dilatant: concentrated slurries).

Wall shear still follows the momentum balance τ_w = (R/2)(−dp/dz)
independent of the constitutive law. The kinematics change.
"""

from typing import Dict

import numpy as np


def power_law_pipe(
    radius: float,
    dp_dz: float,
    K: float,
    n: float,
    rho: float = 1000.0,
    n_points: int = 150,
) -> Dict:
    """Fully developed laminar power-law flow in a circular pipe.

    u(r) = u_max [1 − (r/R)^{(n+1)/n}]
    u_max / u_avg = (3n+1)/(n+1)   (equals 2 when n = 1)
    Q = π n/(3n+1) R³ [R (−dp/dz) / (2K)]^{1/n}
    Metzner–Reed: Re_MR = ρ u^{2−n} D^n / {K 8^{n−1} [(3n+1)/(4n)]^n}
    Laminar Darcy: f_D = 64 / Re_MR.
    """
    n = float(max(n, 0.05))
    K = float(max(K, 1e-12))
    R = float(max(radius, 1e-9))
    pressure_drive = float(-dp_dz)
    r = np.linspace(0.0, R, n_points)
    expo = (n + 1.0) / n
    inner = (R / (2.0 * K)) * pressure_drive
    inner = max(inner, 0.0)
    u_max = (n / (n + 1.0)) * (inner ** (1.0 / n)) * R
    u = u_max * (1.0 - np.power(r / R, expo))
    q = np.pi * n / (3.0 * n + 1.0) * R**3 * (inner ** (1.0 / n))
    area = np.pi * R * R
    u_avg = q / area if area > 0 else 0.0
    tau_wall = 0.5 * R * pressure_drive
    gamma_w = (tau_wall / K) ** (1.0 / n) if tau_wall > 0 else 0.0
    mu_app = K * (gamma_w ** (n - 1.0)) if gamma_w > 0 else K
    D = 2.0 * R
    mr_denom = K * (8.0 ** (n - 1.0)) * (((3.0 * n + 1.0) / (4.0 * n)) ** n)
    re_mr = (rho * (u_avg ** (2.0 - n)) * (D ** n) / mr_denom) if mr_denom > 0 else 0.0
    f_darcy = (64.0 / re_mr) if re_mr > 0 else float("inf")
    return {
        "r": r,
        "r_norm": r / R,
        "u": u,
        "u_max": u_max,
        "u_avg": u_avg,
        "flow_rate": q,
        "tau_wall": tau_wall,
        "gamma_wall": gamma_w,
        "mu_apparent": mu_app,
        "n": n,
        "K": K,
        "re_mr": re_mr,
        "f_darcy": f_darcy,
        "ratio_max_avg": ((3.0 * n + 1.0) / (n + 1.0)),
        "laminar": re_mr < 2100.0,
    }


def power_law_pressure_drop(
    flow_rate: float,
    radius: float,
    length: float,
    K: float,
    n: float,
) -> float:
    """Invert the laminar power-law Q(Δp) relation for |Δp| along a pipe (Pa)."""
    n = float(max(n, 0.05))
    K = float(max(K, 1e-12))
    R = float(max(radius, 1e-9))
    L = float(max(length, 1e-12))
    q = float(abs(flow_rate))
    # Q = π n/(3n+1) R³ [R Δp / (2 K L)]^{1/n}
    coef = np.pi * n / (3.0 * n + 1.0) * R**3
    if coef <= 0 or q <= 0:
        return 0.0
    inner = (q / coef) ** n
    delta_p = inner * (2.0 * K * L / R)
    return float(delta_p)
