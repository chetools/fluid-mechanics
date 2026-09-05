"""Centrifugal impeller geometry, blade angles and velocity triangles.

Everything a student gets confused about in turbomachinery comes down to one
question: *which two directions is that angle between?* This module fixes the
conventions once, in code, and generates the actual 3D blade surface from them,
so the diagrams cannot drift away from the arithmetic.

Conventions used throughout (stated because the other choice is equally common):

* Cylindrical coordinates (r, theta, z). The shaft is the z axis. Positive
  theta follows the rotation.
* **Blade and flow angles are measured from the TANGENTIAL direction.**
  A radial blade is then beta = 90 deg, and a backswept industrial impeller is
  beta_2 ~ 20-35 deg. Many gas-turbine texts (Dixon, Cumpsty) instead measure
  from the meridional direction, where the same blade reads 90 - beta. The
  complement is reported in every result dictionary as `*_from_meridional` so a
  reader can cross-check against either textbook.
* Absolute velocity C, blade speed U = omega r, relative velocity W, with
  C = U + W. The meridional component C_m is radial in the impeller outlet
  plane; the tangential component is C_theta.

The geometry model: a shrouded radial impeller whose blade camberline is a
logarithmic spiral when beta_1 = beta_2, and otherwise the curve obtained by
integrating the defining relation of the blade angle,

    tan(beta) = dr / (r d(theta))    =>    d(theta) = dr / (r tan(beta))

with beta interpolated linearly in radius. That relation *is* the definition of
the blade angle: it says the blade tangent makes angle beta with the local
tangential direction. Integrating it is what makes the drawn blade the blade the
angles describe.

Model limits: this is blade *geometry* plus one-dimensional mean-line velocity
triangles. There is no blade-to-blade flow solution, no boundary layer, no
secondary flow or jet-wake structure, and no volute. Slip is an empirical
correlation, not a computed flow.
"""

import math
from typing import Dict

import numpy as np

# Wiesner (1967) correlation limit; beyond this radius ratio the fit is amended.
WIESNER_LIMIT_EXPONENT = 8.16


def _positive(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive.")
    return value


def _angle(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or not 0.0 < value < 90.0:
        raise ValueError(f"{name} must lie strictly between 0 and 90 degrees from tangential.")
    return value


def slip_factor(beta2_deg: float, n_blades: int, radius_ratio: float) -> Dict:
    """Wiesner's fit to Busemann's potential-flow slip factor.

        sigma = 1 - sqrt(sin(beta_2b)) / Z^0.7

    Slip is *not* a loss. The fluid in a finite blade passage cannot be turned
    as far as the blade suggests, because a relative eddy -- the counter-rotation
    an inviscid fluid must keep in a passage that is itself rotating -- subtracts
    tangential momentum at the tip. It reduces the work delivered at a given
    speed without producing entropy; friction is a separate, additional effect.

    Fewer blades means a wider passage, a stronger relative eddy, and more slip.
    """
    z = int(n_blades)
    if z < 2:
        raise ValueError("An impeller needs at least two blades.")
    beta2 = math.radians(_angle(beta2_deg, "Outlet blade angle beta_2"))
    sigma = 1.0 - math.sqrt(math.sin(beta2)) / (z ** 0.7)
    # Wiesner's correlation is valid up to a limiting radius ratio; past it the
    # published correction applies. Report the check rather than hiding it.
    limit = math.exp(-WIESNER_LIMIT_EXPONENT * math.sin(beta2) / z)
    corrected = sigma
    if radius_ratio > limit:
        corrected = sigma * (
            1.0 - ((radius_ratio - limit) / (1.0 - limit)) ** 3
        )
    return {
        "sigma": corrected,
        "sigma_uncorrected": sigma,
        "radius_ratio_limit": limit,
        "correction_applied": radius_ratio > limit,
        "n_blades": z,
    }


def blade_camberline(
    r1: float,
    r2: float,
    beta1_deg: float,
    beta2_deg: float,
    n_points: int = 160,
) -> Dict:
    """Integrate d(theta) = dr / (r tan beta) to get the blade camberline.

    Returns theta(r) in radians, measured from the leading edge. The blade wrap
    angle theta(r_2) is a real design output: a heavily backswept blade with a
    small beta wraps much further around the shaft, which is why low-beta
    impellers look like spirals and radial-bladed ones look like spokes.
    """
    r1 = _positive(r1, "Inlet radius r_1")
    r2 = _positive(r2, "Outlet radius r_2")
    if r2 <= r1:
        raise ValueError("Outlet radius must exceed inlet radius for a radial impeller.")
    beta1 = math.radians(_angle(beta1_deg, "Inlet blade angle beta_1"))
    beta2 = math.radians(_angle(beta2_deg, "Outlet blade angle beta_2"))

    radius = np.linspace(r1, r2, n_points)
    beta = np.linspace(beta1, beta2, n_points)
    integrand = 1.0 / (radius * np.tan(beta))
    # Cumulative trapezoid, without importing scipy for four lines of quadrature.
    dtheta = 0.5 * (integrand[1:] + integrand[:-1]) * np.diff(radius)
    theta = np.concatenate([[0.0], np.cumsum(dtheta)])
    return {
        "r": radius,
        "theta": theta,
        "beta": beta,
        "beta_deg": np.degrees(beta),
        "wrap_angle_rad": float(theta[-1]),
        "wrap_angle_deg": float(math.degrees(theta[-1])),
        "arc_length": float(np.sum(np.sqrt(np.diff(radius) ** 2 + (radius[:-1] * dtheta) ** 2))),
    }


def blade_surface_3d(
    r1: float,
    r2: float,
    beta1_deg: float,
    beta2_deg: float,
    b1: float,
    b2: float,
    blade_index: int = 0,
    n_blades: int = 7,
    n_points: int = 160,
    n_span: int = 12,
) -> Dict:
    """Cartesian 3D coordinates of one blade surface.

    The blade is swept from hub to shroud along z. Passage width tapers linearly
    from b_1 at the eye to b_2 at the tip, which is what keeps the meridional
    velocity roughly constant as the flow area 2 pi r b would otherwise grow.
    """
    camber = blade_camberline(r1, r2, beta1_deg, beta2_deg, n_points)
    r = camber["r"]
    offset = 2.0 * math.pi * blade_index / max(int(n_blades), 1)
    theta = camber["theta"] + offset
    width = np.linspace(b1, b2, n_points)
    span = np.linspace(0.0, 1.0, n_span)

    # (n_span, n_points) grids: rows are hub -> shroud, columns leading -> trailing.
    rr = np.tile(r, (n_span, 1))
    tt = np.tile(theta, (n_span, 1))
    zz = np.outer(span, width) - 0.5 * np.tile(width, (n_span, 1))
    return {
        "x": rr * np.cos(tt),
        "y": rr * np.sin(tt),
        "z": zz,
        "r": rr,
        "theta": tt,
        "camber": camber,
    }


def impeller_geometry(
    r1: float = 0.045,
    r2: float = 0.150,
    beta1_deg: float = 30.0,
    beta2_deg: float = 25.0,
    b1: float = 0.030,
    b2: float = 0.012,
    n_blades: int = 7,
    n_points: int = 160,
) -> Dict:
    """Full blade set plus hub and shroud discs, ready to draw."""
    blades = [
        blade_surface_3d(r1, r2, beta1_deg, beta2_deg, b1, b2,
                         blade_index=k, n_blades=n_blades, n_points=n_points)
        for k in range(int(n_blades))
    ]
    disc_theta = np.linspace(0.0, 2.0 * math.pi, 121)
    return {
        "blades": blades,
        "r1": r1,
        "r2": r2,
        "b1": b1,
        "b2": b2,
        "beta1_deg": beta1_deg,
        "beta2_deg": beta2_deg,
        "n_blades": int(n_blades),
        "wrap_angle_deg": blades[0]["camber"]["wrap_angle_deg"],
        "hub_theta": disc_theta,
        "eye_x": r1 * np.cos(disc_theta),
        "eye_y": r1 * np.sin(disc_theta),
        "tip_x": r2 * np.cos(disc_theta),
        "tip_y": r2 * np.sin(disc_theta),
        "inlet_area": 2.0 * math.pi * r1 * b1,
        "outlet_area": 2.0 * math.pi * r2 * b2,
        "radius_ratio": r1 / r2,
    }


def velocity_triangles(
    rpm: float,
    flow_rate: float,
    r1: float = 0.045,
    r2: float = 0.150,
    beta1_deg: float = 30.0,
    beta2_deg: float = 25.0,
    b1: float = 0.030,
    b2: float = 0.012,
    n_blades: int = 7,
    c_theta1: float = 0.0,
    rho: float = 998.2,
    hydraulic_efficiency: float = 1.0,
) -> Dict:
    """Inlet and outlet velocity triangles, Euler head, and the slip correction.

    Steps, in the order a designer performs them:

    1. Blade speed from the shaft:            U = omega r
    2. Meridional velocity from continuity:   C_m = Q / (2 pi r b)
    3. Inlet: with no prerotation, C_theta1 = 0, so W_1 is fixed by U_1 and C_m1
       and the *flow* angle beta_1' = atan(C_m1 / U_1) follows. Matching the
       blade angle to it is the shockless-entry condition; the mismatch is the
       incidence, and it is what makes a pump inefficient off design.
    4. Outlet, ideal: the flow leaves along the blade, so
       C_theta2,ideal = U_2 - C_m2 / tan(beta_2).
    5. Outlet, real: slip subtracts tangential momentum,
       C_theta2 = sigma U_2 - C_m2 / tan(beta_2)   (Wiesner's definition).
    6. Euler work and head follow from the tangential components only.
    """
    rpm = _positive(rpm, "Shaft speed")
    flow_rate = _positive(flow_rate, "Volumetric flow rate")
    r1 = _positive(r1, "Inlet radius")
    r2 = _positive(r2, "Outlet radius")
    b1 = _positive(b1, "Inlet width")
    b2 = _positive(b2, "Outlet width")
    beta1 = math.radians(_angle(beta1_deg, "Inlet blade angle beta_1"))
    beta2 = math.radians(_angle(beta2_deg, "Outlet blade angle beta_2"))
    if r2 <= r1:
        raise ValueError(
            "A centrifugal impeller needs r_2 > r_1: the work comes from the radius change."
        )
    if not 0.0 < hydraulic_efficiency <= 1.0:
        raise ValueError("Hydraulic efficiency must lie in (0, 1].")

    omega = 2.0 * math.pi * rpm / 60.0
    u1, u2 = omega * r1, omega * r2
    a1, a2 = 2.0 * math.pi * r1 * b1, 2.0 * math.pi * r2 * b2
    cm1, cm2 = flow_rate / a1, flow_rate / a2

    # --- inlet ---
    w_theta1 = u1 - c_theta1
    beta1_flow = math.atan2(cm1, w_theta1)
    c1 = math.hypot(c_theta1, cm1)
    w1 = math.hypot(w_theta1, cm1)
    incidence = math.degrees(beta1 - beta1_flow)

    # --- outlet ---
    slip = slip_factor(beta2_deg, n_blades, r1 / r2)
    sigma = slip["sigma"]
    c_theta2_ideal = u2 - cm2 / math.tan(beta2)
    c_theta2 = sigma * u2 - cm2 / math.tan(beta2)
    beta2_flow = math.atan2(cm2, max(u2 - c_theta2, 1e-12))
    c2 = math.hypot(c_theta2, cm2)
    w2 = math.hypot(u2 - c_theta2, cm2)
    alpha2 = math.atan2(cm2, c_theta2) if c_theta2 != 0 else math.pi / 2

    work_ideal = u2 * c_theta2_ideal - u1 * c_theta1
    work = u2 * c_theta2 - u1 * c_theta1
    head_euler = work / 9.81
    head_actual = hydraulic_efficiency * head_euler

    # Degree of reaction: the share of the stage's energy rise that appears as
    # static head inside the rotor rather than as kinetic energy to be recovered
    # downstream in the volute. R rises with backsweep -- a heavily backswept
    # impeller does most of its work as pressure. A radial-bladed impeller has
    # the LOWER reaction: C_theta2 -> sigma U_2 makes C_2 large, so more of the
    # work leaves as kinetic energy and is dumped into the volute as a fast,
    # hard-to-diffuse jet.
    reaction = 1.0 - (c2 ** 2 - c1 ** 2) / (2.0 * work) if work != 0 else float("nan")

    return {
        "omega": omega, "rpm": rpm, "flow_rate": flow_rate,
        "u1": u1, "u2": u2, "cm1": cm1, "cm2": cm2,
        "c_theta1": c_theta1, "c_theta2": c_theta2, "c_theta2_ideal": c_theta2_ideal,
        "c1": c1, "c2": c2, "w1": w1, "w2": w2,
        "inlet_area": a1, "outlet_area": a2,
        "beta1_blade_deg": beta1_deg,
        "beta1_flow_deg": math.degrees(beta1_flow),
        "beta1_flow_from_meridional_deg": 90.0 - math.degrees(beta1_flow),
        "beta2_blade_deg": beta2_deg,
        "beta2_blade_from_meridional_deg": 90.0 - beta2_deg,
        "beta2_flow_deg": math.degrees(beta2_flow),
        "alpha2_deg": math.degrees(alpha2),
        "alpha2_from_meridional_deg": 90.0 - math.degrees(alpha2),
        "incidence_deg": incidence,
        "shockless_entry": abs(incidence) < 1.0,
        "slip_factor": sigma,
        "slip_detail": slip,
        "work_ideal": work_ideal,
        "work": work,
        "head_euler_m": head_euler,
        "head_actual_m": head_actual,
        "hydraulic_efficiency": hydraulic_efficiency,
        "power_w": rho * flow_rate * work,
        "reaction": reaction,
        "rho": rho,
        "n_blades": int(n_blades),
        "r1": r1, "r2": r2, "b1": b1, "b2": b2,
    }


def head_flow_curve(
    rpm: float,
    r1: float,
    r2: float,
    beta1_deg: float,
    beta2_deg: float,
    b1: float,
    b2: float,
    n_blades: int,
    q_max: float,
    n_points: int = 60,
) -> Dict:
    """Ideal Euler head against flow rate: the straight line behind every pump curve.

        H = (sigma U_2^2)/g  -  (U_2 / (g 2 pi r_2 b_2 tan beta_2)) Q

    The slope is set by the blade angle alone. Backswept (beta_2 < 90 deg) gives
    a falling line and a stable pump; radial (90 deg) gives a flat one; forward-
    curved (beta_2 > 90 deg, outside this model's range) gives a rising line that
    can drive surge in a compressor. Real curves bend away from this line because
    friction grows like Q^2 and incidence loss grows away from the design point.
    """
    q = np.linspace(q_max / n_points, q_max, n_points)
    head = np.array([
        velocity_triangles(rpm, float(value), r1, r2, beta1_deg, beta2_deg,
                           b1, b2, n_blades)["head_euler_m"]
        for value in q
    ])
    return {"flow_rate": q, "head": head, "rpm": rpm, "beta2_deg": beta2_deg}


def project_isometric(x, y, z, yaw_deg: float = 35.0, pitch_deg: float = 22.0):
    """Orthographic axonometric projection used by the SVG diagrams.

    Rotate about the vertical axis by `yaw`, tip the result by `pitch`, then drop
    the depth coordinate. Returns (u, v, depth); `depth` orders the painter's
    algorithm so near blades cover far ones. Keeping the projection here means
    the SVG is a real projection of the same geometry the 3D plot draws, not a
    freehand impression of it.
    """
    x, y, z = np.asarray(x, float), np.asarray(y, float), np.asarray(z, float)
    yaw, pitch = math.radians(yaw_deg), math.radians(pitch_deg)
    x1 = x * math.cos(yaw) - y * math.sin(yaw)
    y1 = x * math.sin(yaw) + y * math.cos(yaw)
    u = x1
    v = y1 * math.sin(pitch) - z * math.cos(pitch)
    depth = y1 * math.cos(pitch) + z * math.sin(pitch)
    return u, v, depth
