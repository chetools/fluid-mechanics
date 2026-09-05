"""Open-channel (canal, ditch, culvert, sewer) hydraulics.

A pressurised pipe and an open canal are the same momentum balance with one
difference: the canal has a free surface, so the driving head is *geometric*.
In steady uniform flow the water surface is parallel to the bed, the depth does
not change along the channel, and gravity along the slope exactly balances wall
shear:

    rho g A L S_0  =  tau_w P_w L      =>      tau_w = rho g R_h S_0

with R_h = A / P_w the hydraulic radius. That is the same force balance that
gives tau_w = (D/4)(-dp/dx) in a pipe, with (-dp/dx)/(rho g) replaced by the bed
slope S_0 and D/4 replaced by R_h. Hence D_H = 4 R_h: the hydraulic diameter of
chapter 2.4 is defined the way it is precisely so a canal and a pipe share one
friction factor.

Two conventions coexist in practice and both are supported here:

* Darcy-Weisbach with the Moody/Churchill friction factor and D_H = 4 R_h.
  Dimensionally consistent, roughness in metres, valid in any unit system.
* Manning-Strickler, V = (1/n) R_h^(2/3) S^(1/2). An empirical fit that is
  standard in civil practice. Manning's n is NOT dimensionless: the formula as
  written carries units of s/m^(1/3), so these n values are for SI only.

The two agree when  n = R_h^(1/6) sqrt(f/(8 g)), which is why Manning works at
all: in fully rough turbulent flow f is nearly constant, so f ~ R_h^(1/3) is a
weak, slowly varying correction that n absorbs.

Model limits: steady uniform (normal) flow in a prismatic channel, no sediment
transport, no bends or structures, rigid boundaries, and freshwater density.
Backwater curves, hydraulic jumps and unsteady flood routing are not solved.
"""

import math
from typing import Dict

import numpy as np
from scipy.optimize import brentq

from src.physics.pipe_flow import friction_factor_churchill

G = 9.81

# Manning roughness coefficient n [s/m^(1/3)], typical design values.
# Chow, "Open-Channel Hydraulics" (1959), Table 5-6; USGS WSP 1849 for streams.
# These are engineering estimates with roughly +/-20% spread, not properties.
MANNING_N = {
    "Glass / smooth plastic flume": 0.010,
    "Finished concrete": 0.012,
    "Unfinished concrete": 0.014,
    "Corrugated metal culvert": 0.024,
    "Clean earth canal, straight": 0.022,
    "Earth canal, some weeds and stones": 0.030,
    "Gravel bed, cobbles": 0.035,
    "Natural stream, clean and winding": 0.040,
    "Floodplain, heavy brush and timber": 0.100,
}

# Equivalent sand-grain roughness for the Darcy route [m].
CHANNEL_ROUGHNESS = {
    "Glass / smooth plastic flume": 3.0e-6,
    "Finished concrete": 3.0e-4,
    "Unfinished concrete": 3.0e-3,
    "Corrugated metal culvert": 3.0e-2,
    "Clean earth canal, straight": 3.0e-2,
    "Earth canal, some weeds and stones": 8.0e-2,
    "Gravel bed, cobbles": 1.5e-1,
    "Natural stream, clean and winding": 3.0e-1,
    "Floodplain, heavy brush and timber": 1.0,
}


def _positive(value: float, name: str, allow_zero: bool = False) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0 or (value == 0 and not allow_zero):
        raise ValueError(
            f"{name} must be finite and {'nonnegative' if allow_zero else 'positive'}."
        )
    return value


def trapezoid_geometry(depth: float, bottom_width: float, side_slope: float = 0.0) -> Dict:
    """Wetted geometry of a trapezoidal channel at a given depth.

    `side_slope` z is the horizontal run per unit vertical rise: a 2:1 bank has
    z = 2. z = 0 is a rectangular flume; bottom_width = 0 with z > 0 is a
    triangular ditch.

        A   = y (b + z y)                 flow area
        P_w = b + 2 y sqrt(1 + z^2)       wetted perimeter (the free surface is NOT wetted)
        T   = b + 2 z y                   top (surface) width
        R_h = A / P_w                     hydraulic radius
        D_h = A / T                       hydraulic *depth*, the length scale for Froude

    The free surface carries no shear worth counting against the water, so it is
    excluded from P_w. That single modelling choice is what makes R_h of a wide
    shallow river tend to the depth y rather than to something like y/2.
    """
    y = _positive(depth, "Flow depth", allow_zero=True)
    b = _positive(bottom_width, "Bottom width", allow_zero=True)
    z = _positive(side_slope, "Side slope z", allow_zero=True)
    if b == 0 and z == 0:
        raise ValueError("A channel needs a bottom width, a side slope, or both.")
    area = y * (b + z * y)
    perimeter = b + 2.0 * y * math.sqrt(1.0 + z * z)
    top_width = b + 2.0 * z * y
    return {
        "depth": y,
        "bottom_width": b,
        "side_slope": z,
        "area": area,
        "wetted_perimeter": perimeter,
        "top_width": top_width,
        "hydraulic_radius": area / perimeter if perimeter > 0 else 0.0,
        "hydraulic_diameter": 4.0 * area / perimeter if perimeter > 0 else 0.0,
        "hydraulic_depth": area / top_width if top_width > 0 else 0.0,
    }


def manning_discharge(
    depth: float,
    bottom_width: float,
    side_slope: float,
    manning_n: float,
    bed_slope: float,
) -> Dict:
    """Uniform-flow discharge from Manning-Strickler.

        V = (1/n) R_h^(2/3) S_0^(1/2),   Q = V A

    Note the exponents: Q grows like y^(5/3) for a wide channel but only like
    S_0^(1/2). Doubling the slope buys 41% more capacity; deepening the channel
    by 50% buys about 100%. That asymmetry is why canals are widened and
    deepened rather than steepened.
    """
    n = _positive(manning_n, "Manning n")
    slope = _positive(bed_slope, "Bed slope")
    geom = trapezoid_geometry(depth, bottom_width, side_slope)
    velocity = (geom["hydraulic_radius"] ** (2.0 / 3.0)) * math.sqrt(slope) / n
    discharge = velocity * geom["area"]
    return {**geom, "manning_n": n, "bed_slope": slope,
            "velocity": velocity, "discharge": discharge}


def darcy_discharge(
    depth: float,
    bottom_width: float,
    side_slope: float,
    roughness: float,
    bed_slope: float,
    rho: float = 998.2,
    mu: float = 1.002e-3,
) -> Dict:
    """Uniform-flow discharge from Darcy-Weisbach with D_H = 4 R_h.

    Sets the friction slope equal to the bed slope and solves

        S_0 = f_D V^2 / (D_H 2 g)

    for V. f_D comes from Churchill at Re = rho V D_H / mu, so the solve is
    implicit and is closed by fixed-point iteration (f varies weakly with V).
    This is the route that stays valid outside Manning's fully-rough range.
    """
    slope = _positive(bed_slope, "Bed slope")
    eps = _positive(roughness, "Roughness", allow_zero=True)
    rho = _positive(rho, "Density")
    mu = _positive(mu, "Viscosity")
    geom = trapezoid_geometry(depth, bottom_width, side_slope)
    d_h = geom["hydraulic_diameter"]
    if d_h <= 0:
        return {**geom, "velocity": 0.0, "discharge": 0.0, "f_darcy": float("nan"),
                "reynolds": 0.0, "equivalent_manning_n": float("nan")}

    velocity = math.sqrt(2.0 * G * d_h * slope / 0.02)  # seed with f = 0.02
    f_darcy = 0.02
    for _ in range(60):
        reynolds = rho * velocity * d_h / mu
        f_darcy = friction_factor_churchill(reynolds, eps / d_h)
        updated = math.sqrt(2.0 * G * d_h * slope / f_darcy)
        if abs(updated - velocity) < 1e-12 * max(1.0, updated):
            velocity = updated
            break
        velocity = updated
    reynolds = rho * velocity * d_h / mu
    return {
        **geom,
        "velocity": velocity,
        "discharge": velocity * geom["area"],
        "f_darcy": f_darcy,
        "reynolds": reynolds,
        "roughness": eps,
        "bed_slope": slope,
        # Manning's n that reproduces this Darcy result, from
        # n = R_h^(1/6) sqrt(f/(8 g)).
        "equivalent_manning_n": (geom["hydraulic_radius"] ** (1.0 / 6.0))
        * math.sqrt(f_darcy / (8.0 * G)),
    }


def normal_depth(
    discharge: float,
    bottom_width: float,
    side_slope: float,
    manning_n: float,
    bed_slope: float,
    max_depth: float = 100.0,
) -> float:
    """Depth y_n at which Manning's uniform discharge equals the given Q.

    Q(y) is strictly increasing, so a bracketed solve is unconditionally safe.
    This is the design question: "how deep will the water actually run?"
    """
    q_target = _positive(discharge, "Discharge")

    def residual(y: float) -> float:
        return manning_discharge(y, bottom_width, side_slope, manning_n, bed_slope)["discharge"] - q_target

    upper = 0.05
    while upper < max_depth and residual(upper) < 0:
        upper *= 2.0
    if residual(upper) < 0:
        raise ValueError(
            "This channel cannot carry that discharge at any reasonable depth. "
            "Widen it, steepen it, or reduce the flow."
        )
    return float(brentq(residual, 1e-9, upper, xtol=1e-12, rtol=1e-12))


def critical_depth(discharge: float, bottom_width: float, side_slope: float,
                   max_depth: float = 100.0) -> float:
    """Depth at which the specific energy is minimum and Fr = 1.

    Critical flow satisfies  Q^2 T / (g A^3) = 1. It depends only on geometry
    and discharge -- not on roughness or slope. That independence is what makes
    a critical-flow section (a weir, a flume, a spillway crest) usable as a
    flow meter.
    """
    q = _positive(discharge, "Discharge")

    def residual(y: float) -> float:
        geom = trapezoid_geometry(y, bottom_width, side_slope)
        return q * q * geom["top_width"] / (G * geom["area"] ** 3) - 1.0

    lower, upper = 1e-9, 0.05
    while upper < max_depth and residual(upper) > 0:
        upper *= 2.0
    return float(brentq(residual, lower, upper, xtol=1e-12, rtol=1e-12))


def froude_number(discharge: float, depth: float, bottom_width: float,
                  side_slope: float) -> float:
    """Fr = V / sqrt(g D_h), with D_h = A/T the hydraulic depth.

    Fr compares the flow speed to the speed of a shallow-water surface wave.
    Fr < 1 (subcritical, "tranquil"): a disturbance travels upstream, so a
    downstream gate or culvert controls the depth here. Fr > 1 (supercritical,
    "rapid"): nothing propagates upstream, control is from the upstream end, and
    any return to subcritical happens through a hydraulic jump.
    """
    geom = trapezoid_geometry(depth, bottom_width, side_slope)
    if geom["area"] <= 0 or geom["hydraulic_depth"] <= 0:
        return float("inf")
    velocity = discharge / geom["area"]
    return velocity / math.sqrt(G * geom["hydraulic_depth"])


def channel_state(
    discharge: float,
    bottom_width: float,
    side_slope: float,
    manning_n: float,
    bed_slope: float,
    bank_depth: float,
    roughness: float | None = None,
    rho: float = 998.2,
    mu: float = 1.002e-3,
) -> Dict:
    """Full uniform-flow design state, including a bank-full flood check.

    `bank_depth` is the depth from the invert to the top of bank. The freeboard
    is bank_depth - y_n. A canal is *not* designed to run at exactly bank-full:
    wind setup, wave run-up, bends (superelevation), sediment build-up and
    settlement all eat freeboard, and design codes typically require a fifth of
    the depth or a fixed 0.3-0.6 m, whichever is larger.
    """
    y_n = normal_depth(discharge, bottom_width, side_slope, manning_n, bed_slope)
    uniform = manning_discharge(y_n, bottom_width, side_slope, manning_n, bed_slope)
    y_c = critical_depth(discharge, bottom_width, side_slope)
    froude = froude_number(discharge, y_n, bottom_width, side_slope)
    capacity = manning_discharge(bank_depth, bottom_width, side_slope, manning_n, bed_slope)
    bank = _positive(bank_depth, "Bank depth")
    freeboard = bank - y_n
    # Common canal-design rule of thumb; see USBR Design of Small Canal Structures.
    required_freeboard = max(0.3, 0.2 * y_n)
    shear_stress = rho * G * uniform["hydraulic_radius"] * bed_slope
    shear_velocity = math.sqrt(shear_stress / rho)

    darcy = None
    if roughness is not None:
        darcy = darcy_discharge(y_n, bottom_width, side_slope, roughness, bed_slope, rho, mu)

    if froude > 1.05:
        regime = "supercritical"
    elif froude < 0.95:
        regime = "subcritical"
    else:
        regime = "near critical"

    return {
        "discharge": discharge,
        "normal_depth": y_n,
        "critical_depth": y_c,
        "froude": froude,
        "regime": regime,
        "velocity": uniform["velocity"],
        "area": uniform["area"],
        "wetted_perimeter": uniform["wetted_perimeter"],
        "top_width": uniform["top_width"],
        "hydraulic_radius": uniform["hydraulic_radius"],
        "hydraulic_diameter": uniform["hydraulic_diameter"],
        "hydraulic_depth": uniform["hydraulic_depth"],
        "bank_depth": bank,
        "bank_full_capacity": capacity["discharge"],
        "capacity_margin": capacity["discharge"] / discharge if discharge > 0 else float("inf"),
        "freeboard": freeboard,
        "required_freeboard": required_freeboard,
        "freeboard_adequate": freeboard >= required_freeboard,
        "overtops": y_n > bank,
        "bed_shear_stress": shear_stress,
        "shear_velocity": shear_velocity,
        "manning_n": manning_n,
        "bed_slope": bed_slope,
        "darcy": darcy,
    }


def rating_curve(
    bottom_width: float,
    side_slope: float,
    manning_n: float,
    bed_slope: float,
    max_depth: float,
    n_points: int = 120,
) -> Dict:
    """Depth-discharge rating curve, plus the critical-depth locus.

    Where the two curves cross, the normal depth *is* the critical depth: that
    bed slope is the critical slope. Below it the channel runs subcritical, above
    it supercritical -- the same channel, the same roughness, only the slope
    changed.
    """
    depths = np.linspace(max(max_depth / n_points, 1e-6), max_depth, n_points)
    discharge = np.array([
        manning_discharge(y, bottom_width, side_slope, manning_n, bed_slope)["discharge"]
        for y in depths
    ])
    velocity = np.array([
        manning_discharge(y, bottom_width, side_slope, manning_n, bed_slope)["velocity"]
        for y in depths
    ])
    froude = np.array([
        froude_number(q, y, bottom_width, side_slope) if q > 0 else 0.0
        for q, y in zip(discharge, depths)
    ])
    return {
        "depth": depths,
        "discharge": discharge,
        "velocity": velocity,
        "froude": froude,
        "bottom_width": bottom_width,
        "side_slope": side_slope,
        "manning_n": manning_n,
        "bed_slope": bed_slope,
    }
