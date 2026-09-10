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
    Laminar Fanning: f_F = 16 / Re_MR  (Darcy f_D = 4 f_F = 64 / Re_MR).
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
    f_fanning = (16.0 / re_mr) if re_mr > 0 else float("inf")
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
        "f_fanning": f_fanning,
        "f_darcy": 4.0 * f_fanning,
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


# =============================================================================
# Flow curves: one apparent viscosity for every constitutive model
# =============================================================================
#
# A "Newtonian" fluid is not a fluid with a special viscosity; it is a fluid
# whose microstructure is isotropic and relaxes far faster than the flow
# deforms it, so the stress can only depend on the *instantaneous* strain rate
# and can only do so linearly. Each model below is what survives when one of
# those two conditions is broken, so each carries the structural reason with
# it rather than being a curve fit floating free of a mechanism.

MODEL_INFO = {
    "Newtonian": {
        "law": r"\tau = \mu\,\dot\gamma",
        "params": ("mu",),
        "mechanism": (
            "Momentum is carried across the shear planes by molecules that lose "
            "memory of the flow between collisions. The structure the flow "
            "distorts is rebuilt before the next layer slides past, so doubling "
            "the strain rate doubles the momentum flux and nothing else."
        ),
        "examples": "Water, air, light oils, glycerin, most small-molecule liquids.",
    },
    "Power law (Ostwald-de Waele)": {
        "law": r"\tau = K\,\dot\gamma^{\,n}",
        "params": ("K", "n"),
        "mechanism": (
            "Shear aligns and disentangles long molecules faster than Brownian "
            "motion can re-randomise them (n < 1), or forces particles into "
            "load-bearing clusters that jam (n > 1). The structure now depends "
            "on how hard it is being sheared, so the viscosity does too."
        ),
        "examples": "Polymer melts and solutions, paper pulp (n<1); dense cornstarch suspensions (n>1).",
    },
    "Bingham plastic": {
        "law": r"\tau = \tau_y + \mu_p\,\dot\gamma \quad (\tau > \tau_y)",
        "params": ("tau_y", "mu_p"),
        "mechanism": (
            "Attractive particles percolate into a network that spans the fluid. "
            "Below the stress that breaks its bonds the material stores the "
            "deformation elastically and does not flow at all; above it, the "
            "broken fragments are carried in a nearly Newtonian suspension."
        ),
        "examples": "Drilling mud, toothpaste, sewage sludge, fresh concrete.",
    },
    "Herschel-Bulkley": {
        "law": r"\tau = \tau_y + K\,\dot\gamma^{\,n}",
        "params": ("tau_y", "K", "n"),
        "mechanism": (
            "The same percolated network as a Bingham plastic, but the broken "
            "fragments themselves keep aligning as the shear rate rises. A yield "
            "stress and shear thinning are separate structural facts, and most "
            "real pastes have both."
        ),
        "examples": "Tomato ketchup, mayonnaise, cosmetic creams, food purees.",
    },
    "Casson": {
        "law": r"\sqrt{\tau} = \sqrt{\tau_y} + \sqrt{\mu_c\,\dot\gamma}",
        "params": ("tau_y", "mu_c"),
        "mechanism": (
            "Particles aggregate into rouleaux or flocs whose size shrinks as the "
            "stress rises. The square-root form comes from that progressive "
            "break-up rather than from an all-or-nothing yield event."
        ),
        "examples": "Blood, molten chocolate, printing inks.",
    },
    "Carreau-Yasuda": {
        "law": r"\mu = \mu_\infty + (\mu_0-\mu_\infty)\left[1+(\lambda\dot\gamma)^a\right]^{(n-1)/a}",
        "params": ("mu_0", "mu_inf", "lam", "n", "a"),
        "mechanism": (
            "A power law cannot be true at both ends: as the strain rate goes to "
            "zero it predicts infinite viscosity, and there is nothing left to "
            "align at very high rates. Carreau-Yasuda keeps two Newtonian "
            "plateaux and bridges them with a power-law region whose onset is set "
            "by the relaxation time lambda - the shear rate at which the flow "
            "starts to outrun the microstructure is 1/lambda."
        ),
        "examples": "Polymer solutions over a wide rate range, blood, molten plastics.",
    },
}


def flow_curve(model: str, gamma_dot, **params) -> Dict:
    """Shear stress and apparent viscosity of one model over a strain-rate sweep.

    ``mu_app = tau / gamma_dot`` is the slope of the *chord* from the origin, not
    the local tangent, which is why a yield-stress fluid's apparent viscosity
    diverges as the strain rate goes to zero: a finite stress divided by an
    ever-smaller rate. That divergence is physical, not a modelling artefact --
    the material is a solid down there.
    """
    g = np.asarray(gamma_dot, dtype=float)
    g_safe = np.maximum(g, 1e-12)
    if model == "Newtonian":
        tau = params["mu"] * g
    elif model == "Power law (Ostwald-de Waele)":
        tau = params["K"] * np.power(g_safe, params["n"])
    elif model == "Bingham plastic":
        tau = params["tau_y"] + params["mu_p"] * g
    elif model == "Herschel-Bulkley":
        tau = params["tau_y"] + params["K"] * np.power(g_safe, params["n"])
    elif model == "Casson":
        tau = (np.sqrt(params["tau_y"]) + np.sqrt(params["mu_c"] * g_safe)) ** 2
    elif model == "Carreau-Yasuda":
        a = params.get("a", 2.0)
        lam = params["lam"]
        bracket = 1.0 + np.power(lam * g_safe, a)
        mu = params["mu_inf"] + (params["mu_0"] - params["mu_inf"]) * np.power(
            bracket, (params["n"] - 1.0) / a
        )
        tau = mu * g
    else:
        raise ValueError(f"unknown constitutive model: {model!r}")
    tau = np.asarray(tau, dtype=float)
    return {
        "model": model,
        "gamma_dot": g,
        "tau": tau,
        "mu_app": tau / g_safe,
        "params": dict(params),
    }


# =============================================================================
# Laminar pipe flow with a yield stress: Herschel-Bulkley and its special cases
# =============================================================================

def herschel_bulkley_pipe(
    radius: float,
    dp_dz: float,
    K: float,
    n: float,
    tau_y: float = 0.0,
    rho: float = 1000.0,
    n_points: int = 400,
) -> Dict:
    """Fully developed laminar pipe flow of a Herschel-Bulkley fluid.

    The momentum balance still gives ``tau(r) = (r/2)(-dp/dz)`` for any material,
    so the stress rises linearly from zero on the axis to ``tau_w`` at the wall.
    A yield stress therefore selects a *radius*: inside
    ``r_plug = 2 tau_y/(-dp/dz)`` the material is never stressed enough to yield
    and moves as an unsheared solid plug. Outside it,

        -du/dr = [(tau(r) - tau_y)/K]^{1/n}

    integrates inward from the no-slip wall. ``tau_y = 0`` recovers the power law
    and ``tau_y = 0, n = 1`` recovers Hagen-Poiseuille.
    """
    n = float(max(n, 0.05))
    K = float(max(K, 1e-12))
    R = float(max(radius, 1e-9))
    tau_y = float(max(tau_y, 0.0))
    G = float(-dp_dz)  # driving pressure gradient, positive for flow in +z
    r = np.linspace(0.0, R, n_points)
    tau_r = 0.5 * r * G
    tau_w = 0.5 * R * G
    if G <= 0.0 or tau_w <= tau_y:
        # Nothing yields anywhere: the whole cross-section is a static solid.
        zeros = np.zeros_like(r)
        return {
            "r": r, "r_norm": r / R, "u": zeros, "tau_r": tau_r,
            "u_max": 0.0, "u_avg": 0.0, "flow_rate": 0.0,
            "tau_wall": tau_w, "tau_y": tau_y, "r_plug": R, "plug_fraction": 1.0,
            "n": n, "K": K, "gamma_wall": 0.0, "mu_apparent": float("inf"),
            "bingham_number": float("inf"), "re_mr": 0.0,
            "f_fanning": float("inf"), "f_darcy": float("inf"),
            "ratio_max_avg": float("nan"),
            "flowing": False, "laminar": True,
        }
    r_plug = min(2.0 * tau_y / G, R)
    excess_w = tau_w - tau_y
    excess_r = np.maximum(tau_r - tau_y, 0.0)
    expo = (n + 1.0) / n
    pref = (2.0 / G) * (n / (n + 1.0)) * K ** (-1.0 / n)
    u = pref * (excess_w**expo - np.power(excess_r, expo))
    u_max = float(u[0])
    q = float(np.trapezoid(u * 2.0 * np.pi * r, r))
    area = np.pi * R * R
    u_avg = q / area
    gamma_w = (excess_w / K) ** (1.0 / n)
    mu_app = tau_w / gamma_w if gamma_w > 0 else float("inf")
    D = 2.0 * R
    # Metzner-Reed uses the power-law part only; with a yield stress it is a
    # guide, so it is reported next to the Bingham number rather than alone.
    mr_denom = K * (8.0 ** (n - 1.0)) * (((3.0 * n + 1.0) / (4.0 * n)) ** n)
    re_mr = (rho * (u_avg ** (2.0 - n)) * (D**n) / mr_denom) if mr_denom > 0 else 0.0
    # Yield stress / viscous stress, using the stated shear-rate scale U/D.
    bn = (tau_y / (K * (u_avg / D) ** n)) if u_avg > 0 else float("inf")
    # The power-law-only Re_MR omits yield stress: 16/Re_MR is not the
    # Herschel-Bulkley friction factor. Use the actual wall momentum balance.
    f_fanning = tau_w / (0.5 * rho * u_avg**2) if u_avg > 0 else float("inf")
    return {
        "r": r, "r_norm": r / R, "u": u, "tau_r": tau_r,
        "u_max": u_max, "u_avg": u_avg, "flow_rate": q,
        "tau_wall": tau_w, "tau_y": tau_y,
        "r_plug": r_plug, "plug_fraction": r_plug / R,
        "n": n, "K": K, "gamma_wall": float(gamma_w), "mu_apparent": float(mu_app),
        "bingham_number": float(bn), "re_mr": float(re_mr),
        "f_fanning": f_fanning, "f_darcy": 4.0 * f_fanning,
        "ratio_max_avg": (u_max / u_avg) if u_avg > 0 else float("inf"),
        "flowing": True, "laminar": re_mr < 2100.0,
    }


def buckingham_reiner_flow(radius: float, dp_dz: float, mu_p: float, tau_y: float) -> float:
    """Closed-form laminar flow rate of a Bingham plastic, for verification.

    Q = (pi R^4 G / 8 mu_p) [1 - (4/3) xi + (1/3) xi^4],  xi = tau_y/tau_w.

    This exists so the numerically integrated profile above can be checked
    against an independent analytical result instead of against memory.
    """
    R = float(max(radius, 1e-9))
    G = float(-dp_dz)
    tau_w = 0.5 * R * G
    if tau_w <= tau_y or G <= 0:
        return 0.0
    xi = tau_y / tau_w
    return float(
        np.pi * R**4 * G / (8.0 * mu_p) * (1.0 - (4.0 / 3.0) * xi + (xi**4) / 3.0)
    )


# =============================================================================
# Time in the constitutive law: thixotropy and viscoelasticity
# =============================================================================

def thixotropic_step(
    gamma_hi: float = 50.0,
    gamma_lo: float = 1.0,
    k_build: float = 0.25,
    k_break: float = 0.05,
    mu_inf: float = 0.05,
    structure_gain: float = 20.0,
    t_hold: float = 30.0,
    n_points: int = 400,
) -> Dict:
    """Structure kinetics under a step up and back down in shear rate.

    A structure parameter ``lam`` in [0, 1] measures how much of the network is
    intact. Brownian motion rebuilds it and flow breaks it::

        dlam/dt = k_build (1 - lam) - k_break * lam * gamma_dot

    so at a fixed shear rate it relaxes exponentially to
    ``lam_eq = k_build/(k_build + k_break*gamma_dot)`` with time constant
    ``1/(k_build + k_break*gamma_dot)``. The apparent viscosity is
    ``mu = mu_inf (1 + structure_gain * lam)``.

    This is the whole content of thixotropy: the stress depends on the shear
    *history*, because rebuilding takes time. Reversing the step does not
    retrace the same curve - the hysteresis loop a rheometer draws.
    """
    t_hold = float(max(t_hold, 1e-6))
    half = max(n_points // 2, 2)
    t1 = np.linspace(0.0, t_hold, half)
    t2 = np.linspace(t_hold, 2.0 * t_hold, half)[1:]

    def relax(t_local, g, lam0):
        rate = k_build + k_break * g
        lam_eq = k_build / rate if rate > 0 else 1.0
        return lam_eq + (lam0 - lam_eq) * np.exp(-rate * t_local), lam_eq

    lam_start = k_build / (k_build + k_break * gamma_lo)
    lam1, lam_eq_hi = relax(t1, gamma_hi, lam_start)
    lam2, lam_eq_lo = relax(t2 - t_hold, gamma_lo, lam1[-1])
    t = np.concatenate([t1, t2])
    lam = np.concatenate([lam1, lam2])
    gamma = np.concatenate([np.full_like(t1, gamma_hi), np.full_like(t2, gamma_lo)])
    mu = mu_inf * (1.0 + structure_gain * lam)
    return {
        "t": t, "gamma_dot": gamma, "structure": lam, "mu_app": mu, "tau": mu * gamma,
        "structure_start": float(lam_start),
        "lam_eq_high": float(lam_eq_hi), "lam_eq_low": float(lam_eq_lo),
        "tau_build_high": float(1.0 / (k_build + k_break * gamma_hi)),
        "tau_build_low": float(1.0 / (k_build + k_break * gamma_lo)),
        "t_hold": float(t_hold),
    }


def maxwell_startup(
    gamma_dot: float = 10.0,
    relax_time: float = 0.5,
    mu: float = 5.0,
    t_end: float = 3.0,
    n_points: int = 300,
) -> Dict:
    """Startup of steady shear for an upper-convected Maxwell fluid.

    Stretched polymer chains take a time ``lambda`` to relax, so the stress does
    not appear instantly with the strain rate::

        tau(t) = mu * gamma_dot * (1 - exp(-t/lambda))

    The same stretching also pulls *along* the streamlines, producing a first
    normal stress difference that a Newtonian fluid does not have at all::

        N1 = 2 mu lambda gamma_dot^2 = 2 Wi tau,   Wi = lambda * gamma_dot

    N1 is the rod-climbing force: tension along curved streamlines squeezes the
    fluid inward and up a rotating rod. It grows with the *square* of the shear
    rate, which is why the effect seems to appear all at once.
    """
    lam = float(max(relax_time, 1e-9))
    t = np.linspace(0.0, float(max(t_end, 1e-6)), n_points)
    tau = mu * gamma_dot * (1.0 - np.exp(-t / lam))
    tau_ss = mu * gamma_dot
    n1_ss = 2.0 * mu * lam * gamma_dot**2
    wi = lam * gamma_dot
    return {
        "t": t, "tau": tau, "tau_steady": float(tau_ss),
        "tau_newtonian": np.full_like(t, tau_ss),
        "n1_steady": float(n1_ss), "weissenberg": float(wi),
        "relax_time": lam, "gamma_dot": float(gamma_dot),
        "n1_over_tau": float(2.0 * wi),
    }


def timescale_numbers(relax_time: float, gamma_dot: float, flow_time: float) -> Dict:
    """Weissenberg and Deborah numbers, and what each one compares.

    Wi = relax_time * gamma_dot compares the relaxation time with the time the
    flow needs to impose one unit of strain: it asks whether the microstructure
    is *distorted*. De = relax_time / flow_time compares it with the time a
    parcel spends in the equipment: it asks whether the material has time to
    *forget*. A steady viscometric flow can have large Wi and zero De; a fast
    contraction can have large De at modest Wi.
    """
    lam = float(max(relax_time, 0.0))
    wi = lam * float(gamma_dot)
    de = lam / float(max(flow_time, 1e-12))
    return {
        "weissenberg": wi,
        "deborah": de,
        "regime": (
            "solid-like: the structure cannot relax within the process"
            if de > 1.0
            else "liquid-like: the structure relaxes faster than the process"
        ),
        "distorted": wi > 1.0,
    }
