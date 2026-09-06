"""Momentum, heat and mass transfer as one problem in three costumes.

The boundary-layer equations for the three transported quantities are the same
equation with the diffusivity swapped:

    momentum   u du/dx + v du/dy = nu    d2u/dy2      nu    = mu / rho
    energy     u dT/dx + v dT/dy = alpha d2T/dy2      alpha = k / (rho cp)
    species    u dc/dx + v dc/dy = D_AB  d2c/dy2      D_AB  = mass diffusivity

All three diffusivities carry units of m^2/s and play identical roles. That is
the whole basis of the analogy: solve one problem non-dimensionally and you have
solved all three, provided the boundary conditions match too.

Non-dimensionalising leaves ratios of diffusivities as the only fluid property
that can appear:

    Pr = nu / alpha        momentum vs heat
    Sc = nu / D_AB         momentum vs mass
    Le = alpha / D_AB      heat vs mass = Sc / Pr

and the wall flux appears as a dimensionless gradient:

    Nu = h L / k           heat
    Sh = k_c L / D_AB      mass

Because the equations are identical, **the correlation function is identical**:
whatever Nu = f(Re, Pr) holds for a geometry, Sh = f(Re, Sc) holds for the same
geometry with the same f. This module stores each correlation once and evaluates
it for either transport mode, which is the analogy expressed as code rather than
as a claim.

Model limits, all of which the analogy needs and none of which it announces:
constant properties, no viscous dissipation, no form drag in the friction
comparison (Chilton-Colburn relates j to *skin* friction only), low mass-transfer
rates so the blowing velocity does not distort the velocity profile, and no
chemical reaction. Ranges of validity are attached to each correlation and are
reported rather than silently extrapolated.
"""

import math
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Correlations. Each is Nu = coefficient * Re^m * Pr^n (+ offset), with the
# offset carrying the conduction/diffusion limit where one exists.
#
# The same entry serves mass transfer with Pr -> Sc and Nu -> Sh. Storing it
# once is the point: the two modes cannot drift apart.
# ---------------------------------------------------------------------------
CORRELATIONS: Dict[str, Dict] = {
    "Flat plate, laminar (local)": dict(
        offset=0.0, coefficient=0.332, re_exponent=0.5, pr_exponent=1.0 / 3.0,
        re_range=(1e3, 5e5), pr_range=(0.6, 50.0),
        length_scale="distance x from the leading edge",
        source="Blasius similarity solution with a thermal layer",
        note=(
            "The 0.332 is f''(0) from the Blasius solution of chapter 7 -- the very "
            "same number that gives c_f = 0.664/sqrt(Re_x). Heat transfer on a flat "
            "plate is not an empirical fit; it is the momentum solution reused."
        ),
    ),
    "Flat plate, laminar (average)": dict(
        offset=0.0, coefficient=0.664, re_exponent=0.5, pr_exponent=1.0 / 3.0,
        re_range=(1e3, 5e5), pr_range=(0.6, 50.0),
        length_scale="plate length L",
        source="integral of the local laminar result",
        note="Exactly twice the local value at x = L, for the same reason C_F = 2 c_f(L).",
    ),
    "Flat plate, turbulent (local)": dict(
        offset=0.0, coefficient=0.0296, re_exponent=0.8, pr_exponent=1.0 / 3.0,
        re_range=(5e5, 1e7), pr_range=(0.6, 60.0),
        length_scale="distance x from the leading edge",
        source="Colburn analogy applied to the 1/7-power turbulent layer",
        note="Re^0.8 rather than Re^0.5: turbulent mixing carries far more than diffusion.",
    ),
    "Pipe, turbulent (Dittus-Boelter)": dict(
        offset=0.0, coefficient=0.023, re_exponent=0.8, pr_exponent=0.4,
        re_range=(1e4, 1.2e5), pr_range=(0.7, 160.0),
        length_scale="pipe diameter D",
        source="Dittus and Boelter (1930)",
        note=(
            "Pr exponent 0.4 for heating the fluid, 0.3 for cooling it; this module "
            "uses 0.4. Needs L/D > 10 for fully developed flow and moderate "
            "wall-to-bulk property variation -- use Sieder-Tate when the viscosity "
            "changes strongly across the layer."
        ),
    ),
    "Pipe, laminar (constant wall T)": dict(
        offset=3.66, coefficient=0.0, re_exponent=0.0, pr_exponent=0.0,
        re_range=(0.0, 2300.0), pr_range=(0.1, 1e4),
        length_scale="pipe diameter D",
        source="analytical Graetz solution, fully developed",
        note=(
            "Constant, and independent of Re and Pr: fully developed laminar pipe "
            "transport is pure conduction across the profile. 4.36 for constant wall "
            "flux instead of constant wall temperature."
        ),
    ),
    "Sphere (Ranz-Marshall)": dict(
        offset=2.0, coefficient=0.6, re_exponent=0.5, pr_exponent=1.0 / 3.0,
        re_range=(1.0, 7.6e4), pr_range=(0.6, 380.0),
        length_scale="sphere diameter d",
        source="Ranz and Marshall (1952)",
        note=(
            "The 2 is exact and is the whole reason this correlation is worth "
            "knowing: a motionless sphere in an infinite stagnant medium still has "
            "Nu = 2 by pure conduction. No amount of slowing the flow drops transport "
            "below that floor -- which is why fine droplets evaporate at a rate set by "
            "diffusion, not by the wind."
        ),
    ),
    "Cylinder in crossflow (Hilpert)": dict(
        offset=0.0, coefficient=0.193, re_exponent=0.618, pr_exponent=1.0 / 3.0,
        re_range=(4e3, 4e4), pr_range=(0.6, 50.0),
        length_scale="cylinder diameter d",
        source="Hilpert (1933), coefficients for 4e3 < Re < 4e4",
        note=(
            "Piecewise in Re: the coefficient and exponent both change as the wake "
            "structure changes. This entry covers one band only; outside it the "
            "constants are different, not merely extrapolated."
        ),
    ),
    "Packed bed (Wakao)": dict(
        offset=2.0, coefficient=1.1, re_exponent=0.6, pr_exponent=1.0 / 3.0,
        re_range=(3.0, 1e4), pr_range=(0.6, 1e4),
        length_scale="particle diameter d_p, superficial velocity",
        source="Wakao and Kaguei (1982)",
        note=(
            "Carries the same conduction floor of 2 as a single sphere. Uses the "
            "superficial velocity, not the interstitial one; mixing those up is a "
            "factor of the void fraction."
        ),
    ),
}


def _positive(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive.")
    return value


def diffusivities(
    rho: float = 998.2,
    mu: float = 1.002e-3,
    k_thermal: float = 0.598,
    cp: float = 4182.0,
    d_ab: float = 1.5e-9,
) -> Dict:
    """The three diffusivities and the ratios that compare them.

    Defaults are liquid water at 20 C with a typical small-molecule diffusivity.
    Every value is m^2/s, which is the point: momentum, heat and species all
    spread by the same mathematics, at different rates.
    """
    rho = _positive(rho, "Density")
    mu = _positive(mu, "Viscosity")
    k_thermal = _positive(k_thermal, "Thermal conductivity")
    cp = _positive(cp, "Specific heat")
    d_ab = _positive(d_ab, "Mass diffusivity")

    nu = mu / rho
    alpha = k_thermal / (rho * cp)
    return {
        "nu": nu,
        "alpha": alpha,
        "d_ab": d_ab,
        "prandtl": nu / alpha,
        "schmidt": nu / d_ab,
        "lewis": alpha / d_ab,
        "rho": rho, "mu": mu, "k_thermal": k_thermal, "cp": cp,
    }


def transport_correlation(
    geometry: str,
    reynolds: float,
    property_number: float,
    mode: str = "heat",
) -> Dict:
    """Evaluate Nu (heat) or Sh (mass) for a geometry.

    `property_number` is Pr for heat and Sc for mass. The arithmetic is
    identical -- that identity IS the analogy -- so this function does not
    branch on `mode` except to name things.
    """
    if geometry not in CORRELATIONS:
        raise ValueError(f"Unknown geometry {geometry!r}. Choose from {sorted(CORRELATIONS)}.")
    if mode not in ("heat", "mass"):
        raise ValueError("mode must be 'heat' or 'mass'.")
    reynolds = _positive(reynolds, "Reynolds number")
    property_number = _positive(property_number, "Prandtl/Schmidt number")

    spec = CORRELATIONS[geometry]
    value = spec["offset"] + spec["coefficient"] * (
        reynolds ** spec["re_exponent"]
    ) * (property_number ** spec["pr_exponent"])

    re_low, re_high = spec["re_range"]
    pr_low, pr_high = spec["pr_range"]
    warnings: List[str] = []
    if not re_low <= reynolds <= re_high:
        warnings.append(
            f"Re = {reynolds:.3g} is outside the correlation's range "
            f"[{re_low:.3g}, {re_high:.3g}]."
        )
    if not pr_low <= property_number <= pr_high:
        label = "Pr" if mode == "heat" else "Sc"
        warnings.append(
            f"{label} = {property_number:.3g} is outside the correlation's range "
            f"[{pr_low:.3g}, {pr_high:.3g}]."
        )

    return {
        "geometry": geometry,
        "mode": mode,
        "value": value,
        "symbol": "Nu" if mode == "heat" else "Sh",
        "property_symbol": "Pr" if mode == "heat" else "Sc",
        "reynolds": reynolds,
        "property_number": property_number,
        "in_range": not warnings,
        "warnings": warnings,
        **{key: spec[key] for key in
           ("offset", "coefficient", "re_exponent", "pr_exponent",
            "length_scale", "source", "note")},
    }


def analogy_pair(
    geometry: str,
    reynolds: float,
    prandtl: float,
    schmidt: float,
) -> Dict:
    """Heat and mass side by side, plus the ratio the analogy predicts.

    Since Nu = C Re^m Pr^n and Sh = C Re^m Sc^n share C and m, their ratio is
    (Sc/Pr)^n = Le^n whenever the offset term is zero. Reporting the measured
    ratio next to Le^n shows exactly how much of the analogy survives the
    conduction floor.
    """
    heat = transport_correlation(geometry, reynolds, prandtl, "heat")
    mass = transport_correlation(geometry, reynolds, schmidt, "mass")
    lewis = schmidt / prandtl
    exponent = CORRELATIONS[geometry]["pr_exponent"]
    predicted = lewis ** exponent if CORRELATIONS[geometry]["offset"] == 0.0 else float("nan")
    return {
        "heat": heat,
        "mass": mass,
        "lewis": lewis,
        "ratio": mass["value"] / heat["value"],
        "ratio_from_lewis": predicted,
        "offset_breaks_pure_power_law": CORRELATIONS[geometry]["offset"] != 0.0,
    }


def chilton_colburn(
    reynolds: float,
    prandtl: float,
    schmidt: Optional[float] = None,
    friction_factor_darcy: Optional[float] = None,
    nusselt: Optional[float] = None,
) -> Dict:
    """The j-factors, and the friction factor they are supposed to equal.

        j_H = St  Pr^(2/3),   St  = Nu / (Re Pr)
        j_D = St_m Sc^(2/3),  St_m = Sh / (Re Sc)
        j_H = j_D = f_F / 2 = f_D / 8

    The last equality is the analogy's strongest and most abused claim. It holds
    against **skin friction only**. On a bluff body most of the drag is form
    drag, which transports no heat and no species, so f_D/8 badly over-predicts
    j and the comparison is meaningless. Reported here so the failure is visible
    rather than assumed away.
    """
    reynolds = _positive(reynolds, "Reynolds number")
    prandtl = _positive(prandtl, "Prandtl number")
    result: Dict[str, float] = {"reynolds": reynolds, "prandtl": prandtl}

    if nusselt is not None:
        stanton = nusselt / (reynolds * prandtl)
        result["stanton"] = stanton
        result["j_h"] = stanton * prandtl ** (2.0 / 3.0)
    if schmidt is not None:
        result["schmidt"] = schmidt
    if friction_factor_darcy is not None:
        friction_factor_darcy = _positive(friction_factor_darcy, "Darcy friction factor")
        result["friction_factor_darcy"] = friction_factor_darcy
        result["friction_factor_fanning"] = friction_factor_darcy / 4.0
        result["j_from_friction"] = friction_factor_darcy / 8.0
        if "j_h" in result:
            result["analogy_ratio"] = result["j_h"] / result["j_from_friction"]
    return result


def sweep_reynolds(
    geometry: str,
    property_number: float,
    mode: str = "heat",
    n_points: int = 60,
) -> Dict:
    """Correlation curve across its own stated validity range, for plotting."""
    spec = CORRELATIONS[geometry]
    re_low, re_high = spec["re_range"]
    re_low = max(re_low, 1e-2)
    step = (re_high / re_low) ** (1.0 / (n_points - 1))
    reynolds = [re_low * step ** index for index in range(n_points)]
    values = [
        transport_correlation(geometry, re, property_number, mode)["value"]
        for re in reynolds
    ]
    return {
        "geometry": geometry,
        "reynolds": reynolds,
        "values": values,
        "symbol": "Nu" if mode == "heat" else "Sh",
        "property_number": property_number,
    }


def pohlhausen_theta_gradient(prandtl: float, eta_max: float = 12.0,
                              n_points: int = 400) -> Dict:
    """Solve the thermal boundary layer on the Blasius velocity field.

    This is where the 0.332 Re^(1/2) Pr^(1/3) correlation actually comes from,
    and it is a derivation rather than a fit.

    With the same similarity variable eta = y sqrt(U/(nu x)) that collapsed the
    momentum problem, and a scaled temperature theta = (T - T_w)/(T_inf - T_w),
    the boundary-layer energy equation

        u dT/dx + v dT/dy = alpha d2T/dy2

    becomes an ODE carrying the Blasius f as a known coefficient:

        theta'' + (Pr/2) f theta' = 0,    theta(0) = 0,  theta(inf) = 1

    Only Pr appears. Momentum enters solely through f, which is why the thermal
    problem is a rider on the momentum solution rather than a separate one.

    The energy equation is **linear and homogeneous** in theta, so it need not be
    shot. Integrate once with theta'(0) = 1 to get an unnormalised thetatilde;
    the boundary condition at infinity then fixes

        theta'(0) = 1 / thetatilde(inf)

    exactly, in a single pass. The wall flux follows:

        Nu_x = h x / k = theta'(0) sqrt(Re_x)

    Replace Pr by Sc and the identical solution gives Sh_x, because the species
    equation is the same equation.
    """
    import numpy as np
    from scipy.integrate import solve_ivp

    from src.physics.boundary_layer import BLASIUS_FPP0

    prandtl = _positive(prandtl, "Prandtl/Schmidt number")

    def rhs(_eta, state):
        f, fp, fpp, theta, thetap = state
        return [fp, fpp, -0.5 * f * fpp, thetap, -0.5 * prandtl * f * thetap]

    solution = solve_ivp(
        rhs, (0.0, eta_max), [0.0, 0.0, BLASIUS_FPP0, 0.0, 1.0],
        t_eval=np.linspace(0.0, eta_max, n_points), rtol=1e-10, atol=1e-12,
    )
    theta_tilde = solution.y[3]
    gradient = 1.0 / float(theta_tilde[-1])
    theta = theta_tilde * gradient
    # Thermal layer edge, by the same 99% convention used for the velocity layer
    # of *this* integration — not a quoted 4.91.
    eta = solution.t
    fp = solution.y[1]
    index = int(np.argmax(theta >= 0.99)) if bool(np.any(theta >= 0.99)) else len(theta) - 1
    idx_vel = int(np.argmax(fp >= 0.99)) if bool(np.any(fp >= 0.99)) else len(fp) - 1
    eta_vel_99 = float(eta[idx_vel])
    return {
        "prandtl": prandtl,
        "theta_gradient": gradient,          # theta'(0); Nu_x = this * sqrt(Re_x)
        "power_law_estimate": 0.332 * prandtl ** (1.0 / 3.0),
        "eta": eta,
        "theta": theta,
        "f_prime": fp,                       # u/U, for plotting beside theta
        "eta_thermal_99": float(eta[index]),
        "eta_velocity_99": eta_vel_99,
        "thickness_ratio": float(eta[index]) / eta_vel_99,   # delta_t / delta
    }
