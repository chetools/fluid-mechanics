"""Turbulence physics, velocity profile models, and boundary layer theory.

Implements:
1. Laminar Hagen-Poiseuille vs. Turbulent power-law radial velocity profiles
2. Universal Law of the Wall (viscous sublayer, buffer layer, log-law region)
3. Kinetic energy (alpha) and momentum (beta) correction factors
4. Chemical engineering transport trade-offs (Reynolds / Chilton-Colburn analogy)
"""

from typing import Dict
import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.optimize import brentq


def smooth_pipe_profile(reynolds: float = 50000.0, n_points: int = 8001) -> Dict:
    """A physically constrained mean-profile sketch, not a calibrated pipe correlation.

    Steady, fully developed Newtonian flow in a smooth circular pipe. Total
    shear is linear in radius. Use a simple damped eddy viscosity E = nu_t/nu:
      d/R = (1-eta**2)*(1+2*eta**2)/6,
      E = 0.41*Re_tau*(d/R)*(1-exp(-Re_tau*(d/R)/26))**2.
    The chosen effective mixing scale equals y/R to leading order at the wall
    and is even and bounded through the core. It is an illustrative closure,
    not the five-parameter Cantwell model, DNS, or an engineering friction fit.
    Retain molecular viscosity, integrate from the no-slip wall, and solve
    Re_D = 2 Re_tau U_bulk+ for the requested bulk Reynolds number. At eta=0
    symmetry gives zero gradient; at eta=1 molecular viscosity gives finite shear.
    Low-Re outputs are mathematical continuations, not a transition prediction.
    """
    if not np.isfinite(reynolds) or reynolds <= 0:
        raise ValueError("Bulk Reynolds number must be finite and positive.")
    if n_points < 3:
        raise ValueError("At least three radial points are required.")
    eta = 0.5 * (1.0 - np.cos(np.linspace(0.0, np.pi, n_points)))
    distance = (1.0 - eta**2) * (1.0 + 2.0 * eta**2) / 6.0

    def at_friction_re(re_tau):
        damping = -np.expm1(-re_tau * distance / 26.0)
        eddy_ratio = 0.41 * re_tau * distance * damping**2
        # S = -d(u/u_tau)/d(eta), from the linear total-shear balance.
        # Finite core eddy viscosity gives a parabolic centreline expansion.
        shear = re_tau * eta / (1.0 + eddy_ratio)
        u_plus = -cumulative_trapezoid(shear[::-1], eta[::-1], initial=0.0)[::-1]
        bulk_plus = 2.0 * np.trapezoid(u_plus * eta, eta)
        return u_plus, bulk_plus, shear, eddy_ratio

    re_tau = brentq(lambda rt: 2.0 * rt * at_friction_re(rt)[1] - reynolds,
                    1e-8, max(reynolds, 1.0), xtol=1e-10)
    u_plus, bulk_plus, shear, eddy_ratio = at_friction_re(re_tau)
    shape = u_plus / bulk_plus
    return {
        "eta": eta, "u_over_mean": shape,
        "gradient_over_mean": -shear / bulk_plus,
        "shear_plus": shear, "eddy_viscosity_ratio": eddy_ratio,
        "re_tau": re_tau, "bulk_plus": bulk_plus,
        "u_tau_over_mean": 1.0 / bulk_plus,
        "alpha": float(2.0 * np.trapezoid(shape**3 * eta, eta)),
        "beta": float(2.0 * np.trapezoid(shape**2 * eta, eta)),
    }

def velocity_profile_comparison(
    pipe_radius: float = 0.05,
    u_avg: float = 1.5,
    reynolds: float = 50000.0,
    n_points: int = 501,
    include_smooth: bool = True,
) -> Dict[str, np.ndarray]:
    """Compare normalized radial velocity profiles for laminar and turbulent flow.
    
    Laminar: u(r) = 2 * u_avg * (1 - (r/R)^2)
    Power-law approximation: u(r) = u_max * (1 - r/R)^(1/n), with n(Re) ~ 7.
    Its nonzero centre slope and infinite wall slope are retained, not rounded.
    A separate damped eddy-viscosity sketch respects both boundary gradients.
    Historical alpha_turb/beta_turb fields remain integrals of the power law.
    """
    r = pipe_radius * 0.5 * (1.0 - np.cos(np.linspace(0.0, np.pi, n_points)))
    r_norm = r / pipe_radius
    
    # 1. Laminar profile
    u_max_lam = 2.0 * u_avg
    u_laminar = u_max_lam * (1.0 - r_norm**2)
    
    # 2. Turbulent power-law profile exponent n(Re)
    # Empirical relation: n ~ 6 for Re=4000, 7 for Re=1e5, 10 for Re=3e6
    if reynolds < 10000:
        n_exp = 6.0
    elif reynolds < 200000:
        n_exp = 7.0
    elif reynolds < 1000000:
        n_exp = 8.8
    else:
        n_exp = 10.0
        
    ratio_avg_max = (2.0 * n_exp**2) / ((n_exp + 1.0) * (2.0 * n_exp + 1.0))
    u_max_turb = u_avg / ratio_avg_max
    u_turbulent = u_max_turb * ((1.0 - r_norm)**(1.0 / n_exp))
    
    # Kinetic-energy (alpha) and momentum (beta) correction factors, integrated
    # over the annular area element from the *same* profiles that are plotted:
    #   alpha = (1/A) int (u/ubar)^3 dA,  beta = (1/A) int (u/ubar)^2 dA,
    #   dA = 2 pi r dr  ->  (1/A) int ... dA = 2 int_0^1 ... eta d(eta)
    # The panel derives alpha = 2 for the parabola and ~1.06 for the 1/7 law and
    # says these numbers come from integrating the profile, so they must.
    # Closed-form approximations such as 1 + 3/(2 n^2) understate the turbulent
    # correction by nearly half at n = 7 (1.031 against the true 1.058).
    # Integrate on a grid of its own: the turbulent profile has an infinite
    # slope at the wall, so the ~150 points that draw a smooth curve leave a
    # visible error in the third moment.
    eta = np.linspace(0.0, 1.0, 20001)
    shapes = {
        "lam": 2.0 * (1.0 - eta**2),                      # u/u_avg, parabola
        "turb": (1.0 - eta) ** (1.0 / n_exp) / ratio_avg_max,
    }

    def _flux_correction(shape: np.ndarray, power: int) -> float:
        return float(2.0 * np.trapezoid(shape**power * eta, eta))

    alpha_lam = _flux_correction(shapes["lam"], 3)
    beta_lam = _flux_correction(shapes["lam"], 2)
    alpha_turb = _flux_correction(shapes["turb"], 3)
    beta_turb = _flux_correction(shapes["turb"], 2)

    result = {
        "r": r,
        "r_norm": r_norm,
        "u_laminar": u_laminar,
        "u_turbulent": u_turbulent,
        "u_max_lam": u_max_lam,
        "u_max_turb": u_max_turb,
        "ratio_lam": 0.5,
        "ratio_turb": ratio_avg_max,
        "alpha_lam": alpha_lam,
        "alpha_turb": alpha_turb,
        "beta_lam": beta_lam,
        "beta_turb": beta_turb,
        "n_exp": n_exp,
        "reynolds": float(reynolds),
    }
    if not include_smooth:
        return result
    smooth = smooth_pipe_profile(float(reynolds))
    result.update({
        "u_smooth": u_avg * np.interp(r_norm, smooth["eta"], smooth["u_over_mean"]),
        "u_max_smooth": u_avg * smooth["u_over_mean"][0],
        "alpha_smooth": smooth["alpha"],
        "beta_smooth": smooth["beta"],
        "re_tau_smooth": smooth["re_tau"],
        "smooth_wall_gradient": u_avg / pipe_radius * smooth["gradient_over_mean"][-1],
    })
    return result


def pipe_kinetic_correction(reynolds: float) -> Dict[str, float]:
    """Regime-aware alpha/beta from the same profiles Tab 4 plots and integrates.

    Laminar (Re < 2300): Hagen–Poiseuille parabola.
    Turbulent (Re > 4000): 1/n power law at this Re.
    Transition: no unique profile; alpha/beta are left unset so a caption
    cannot invent a number such as 1.3.
    """
    prof = velocity_profile_comparison(reynolds=float(reynolds), include_smooth=False)
    re = float(reynolds)
    out = {
        "alpha_lam": float(prof["alpha_lam"]),
        "beta_lam": float(prof["beta_lam"]),
        "alpha_turb": float(prof["alpha_turb"]),
        "beta_turb": float(prof["beta_turb"]),
        "n_exp": float(prof["n_exp"]),
        "reynolds": re,
    }
    if re < 2300.0:
        out.update(alpha=out["alpha_lam"], beta=out["beta_lam"], regime="laminar")
    elif re > 4000.0:
        out.update(alpha=out["alpha_turb"], beta=out["beta_turb"], regime="turbulent")
    else:
        out.update(alpha=float("nan"), beta=float("nan"), regime="transitional")
    return out


def _spalding_y_plus(u_plus: np.ndarray, kappa: float, B: float) -> np.ndarray:
    """Spalding's implicit wall law: y+ as a function of u+."""
    ku = kappa * u_plus
    return u_plus + np.exp(-kappa * B) * (
        np.exp(ku) - 1.0 - ku - 0.5 * ku**2 - (ku**3) / 6.0
    )


def law_of_the_wall(
    kappa: float = 0.41,
    B: float = 5.0,
    y_plus_max: float = 1000.0,
    n_points: int = 250,
) -> Dict[str, np.ndarray]:
    """Universal Law of the Wall: viscous and log limits, Spalding composite.

    Viscous sublayer: u+ = y+  (for y+ < 5)
    Log-law layer: u+ = (1/kappa) * ln(y+) + B  (for y+ > 30)
    Buffer: Spalding's implicit interpolation that matches both limits,
    inverted for u+(y+) by Newton:
    y+ = u+ + e^(-kappa B) [ e^(kappa u+) - 1 - kappa u+ - (kappa u+)^2/2 - (kappa u+)^3/6 ]
    This is a blend, not a third physical law.
    """
    y_plus = np.logspace(np.log10(0.1), np.log10(y_plus_max), n_points)
    
    # Pure linear viscous sublayer
    u_plus_viscous = y_plus.copy()
    
    # Pure logarithmic overlap law
    with np.errstate(divide='ignore', invalid='ignore'):
        u_plus_log = (1.0 / kappa) * np.log(y_plus) + B

    # Invert Spalding y+(u+) at every y+. Seed with the min of the two limits.
    u = np.minimum(y_plus, np.maximum(u_plus_log, 0.1))
    exp_m_kB = np.exp(-kappa * B)
    for _ in range(16):
        ku = kappa * u
        y_of_u = u + exp_m_kB * (np.exp(ku) - 1.0 - ku - 0.5 * ku**2 - (ku**3) / 6.0)
        dy_du = 1.0 + exp_m_kB * (
            kappa * np.exp(ku) - kappa - kappa**2 * u - 0.5 * kappa**3 * u**2
        )
        u = np.maximum(u - (y_of_u - y_plus) / dy_du, 0.0)
    u_plus_composite = u
            
    return {
        "y_plus": y_plus,
        "u_plus_viscous": u_plus_viscous,
        "u_plus_log": u_plus_log,
        "u_plus_composite": u_plus_composite,
        "kappa": kappa,
        "B": B,
    }
