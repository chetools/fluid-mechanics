"""Laminar boundary layers: Blasius flat plate and cylinder separation.

Blasius is the missing punchline of d'Alembert: viscosity lives in a thin
layer of thickness δ ~ x / sqrt(Re_x). On a cylinder the inviscid outer
flow turns adverse after 90°, and a laminar boundary layer separates near
105° (Schlichting) — which Euler cannot see.
"""

from typing import Dict

import numpy as np
from scipy.integrate import solve_ivp

# Howarth / Schlichting: f''(0) such that f'(∞) → 1
BLASIUS_FPP0 = 0.3320573362151963
# η where u/U ≈ 0.99 for the Blasius profile
BLASIUS_ETA_99 = 4.91
BLASIUS_DELTA_STAR_COEFF = 1.7208  # δ*/x * sqrt(Re_x)
BLASIUS_THETA_COEFF = 0.664       # θ/x * sqrt(Re_x) = cf * sqrt(Re_x)
LAMINAR_CYLINDER_SEP_DEG = 104.5


def _blasius_rhs(_eta: float, y: np.ndarray) -> list:
    """y = [f, f', f''];  2 f''' + f f'' = 0  ⇔  f''' = −½ f f''."""
    f, fp, fpp = y
    return [fp, fpp, -0.5 * f * fpp]


def blasius_similarity_profile(eta_max: float = 8.0, n_points: int = 250) -> Dict:
    """Integrate the Blasius equation from the wall to η_max.

    f(0) = f'(0) = 0, f''(0) = 0.33206, f'(∞) → 1.
    η = y sqrt(U / (ν x)),  u/U = f'(η).
    """
    sol = solve_ivp(
        _blasius_rhs,
        (0.0, eta_max),
        [0.0, 0.0, BLASIUS_FPP0],
        t_eval=np.linspace(0.0, eta_max, n_points),
        rtol=1e-8,
        atol=1e-10,
    )
    eta = sol.t
    f, fp, fpp = sol.y
    idx_99 = int(np.argmax(fp >= 0.99)) if np.any(fp >= 0.99) else len(fp) - 1
    return {
        "eta": eta,
        "f": f,
        "f_prime": fp,
        "f_double_prime": fpp,
        "eta_99": float(eta[idx_99]),
        "fpp0": float(fpp[0]),
        "fp_inf": float(fp[-1]),
    }


def blasius_plate(
    x: float,
    u_inf: float,
    nu: float,
    n_x: int = 80,
) -> Dict:
    """Dimensional Blasius thicknesses and skin friction along a flat plate.

    x is the plate length used for Re_L; profiles are also returned vs station.
    """
    x = max(float(x), 1e-6)
    nu = max(float(nu), 1e-16)
    u_inf = max(float(u_inf), 1e-12)
    x_arr = np.linspace(x / n_x, x, n_x)
    re_x = u_inf * x_arr / nu
    sqrt_re = np.sqrt(re_x)
    delta = BLASIUS_ETA_99 * x_arr / sqrt_re
    delta_star = BLASIUS_DELTA_STAR_COEFF * x_arr / sqrt_re
    theta = BLASIUS_THETA_COEFF * x_arr / sqrt_re
    cf = BLASIUS_THETA_COEFF / sqrt_re  # local c_f = 0.664 / sqrt(Re_x)
    re_l = u_inf * x / nu
    cf_mean = 1.328 / np.sqrt(re_l)
    drag_per_width = 0.5 * (1.0) * u_inf**2 * x * cf_mean  # per unit depth, ρ later
    return {
        "x": x_arr,
        "re_x": re_x,
        "delta": delta,
        "delta_star": delta_star,
        "theta": theta,
        "cf": cf,
        "re_L": re_l,
        "delta_L": float(delta[-1]),
        "delta_star_L": float(delta_star[-1]),
        "theta_L": float(theta[-1]),
        "cf_L": float(cf[-1]),
        "Cf_mean": float(cf_mean),
        "x_L": x,
        "u_inf": u_inf,
        "nu": nu,
        "drag_coeff_times_dynp_width": float(drag_per_width),
    }


def cylinder_outer_flow_and_separation(
    u_inf: float = 5.0,
    radius: float = 1.0,
    rho: float = 1000.0,
    n_theta: int = 181,
) -> Dict:
    """Inviscid cylinder outer flow: U_e, C_p, dp/ds, and separation landmarks.

    U_e = 2 U_∞ sin θ. Bernoulli: C_p = 1 − 4 sin²θ.
    dp/ds = −ρ U_e dU_e/ds. Adverse after θ = 90°.
    Laminar separation on a circular cylinder is empirically ~104.5°.
    """
    theta = np.linspace(0.0, np.pi, n_theta)
    ue = 2.0 * u_inf * np.sin(theta)
    cp = 1.0 - 4.0 * np.sin(theta) ** 2
    due_ds = 2.0 * u_inf * np.cos(theta) / max(radius, 1e-12)
    dp_ds = -rho * ue * due_ds
    return {
        "theta": theta,
        "theta_deg": np.degrees(theta),
        "u_e": ue,
        "cp": cp,
        "dp_ds": dp_ds,
        "adverse_start_deg": 90.0,
        "laminar_sep_deg": LAMINAR_CYLINDER_SEP_DEG,
        "u_inf": u_inf,
        "radius": radius,
        "rho": rho,
    }
