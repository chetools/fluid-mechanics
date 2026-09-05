"""Impeller diagrams projected from the computed 3D geometry.

These figures are *projections of real geometry*, not freehand sketches. The
blade curves come from `src.physics.impeller`, which builds them by integrating
the definition of the blade angle, so an angle drawn here is the same angle the
velocity-triangle arithmetic uses. Change beta_2 and both the picture and the
numbers move together.

They live outside `src.svg_diagrams` because they need NumPy and the physics
layer; the hand-authored schematics there stay dependency-free. Rendering still
goes through `src.svg_diagrams.render_svg`.
"""

import math

import numpy as np

from src.physics.impeller import impeller_geometry, project_isometric
from src.theme import (
    ACCENT,
    BORDER,
    BORDER_STRONG,
    PRESSURE,
    SHEAR,
    SUCCESS,
    SURFACE,
    SURFACE_RAISED,
    TEXT,
    TEXT_DIM,
    TEXT_FAINT,
    TEXT_MUTED,
    VORTICITY,
    WARNING,
)


def _f(value) -> str:
    return f"{float(value):.2f}"


def _points(us, vs) -> str:
    return " ".join(f"{_f(u)},{_f(v)}" for u, v in zip(us, vs))


def _polyline(us, vs, stroke, width=2.0, opacity=1.0, dash="") -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<polyline points="{_points(us, vs)}" fill="none" stroke="{stroke}" '
            f'stroke-width="{width}" stroke-opacity="{opacity}" '
            f'stroke-linejoin="round" stroke-linecap="round"{dash_attr}/>')


def _polygon(us, vs, fill, stroke, opacity) -> str:
    return (f'<polygon points="{_points(us, vs)}" fill="{fill}" fill-opacity="{opacity}" '
            f'stroke="{stroke}" stroke-width="1.2" stroke-linejoin="round"/>')


def _arrow_marker_defs() -> str:
    """Local marker set, so this module does not depend on svg_diagrams internals."""
    heads = [("imp-sky", ACCENT), ("imp-orange", WARNING), ("imp-green", SUCCESS),
             ("imp-purple", VORTICITY), ("imp-red", PRESSURE), ("imp-dim", TEXT_DIM)]
    markers = "".join(
        f'<marker id="{name}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" '
        f'markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M 0 1 L 10 5 L 0 9 z" fill="{colour}"/></marker>'
        for name, colour in heads
    )
    return f"<defs>{markers}</defs>"


def _angle_arc(cx, cy, radius, start_deg, end_deg, colour, width=2.0) -> str:
    """Arc between two screen-space directions, always drawn the short way round."""
    sweep = (end_deg - start_deg) % 360.0
    if sweep > 180.0:
        sweep -= 360.0
    large = 0
    direction = 1 if sweep > 0 else 0
    x0 = cx + radius * math.cos(math.radians(start_deg))
    y0 = cy + radius * math.sin(math.radians(start_deg))
    x1 = cx + radius * math.cos(math.radians(start_deg + sweep))
    y1 = cy + radius * math.sin(math.radians(start_deg + sweep))
    return (f'<path d="M {_f(x0)} {_f(y0)} A {_f(radius)} {_f(radius)} 0 {large} '
            f'{direction} {_f(x1)} {_f(y1)}" fill="none" stroke="{colour}" '
            f'stroke-width="{width}"/>')


def diagram_impeller_3d(
    r1: float = 0.045,
    r2: float = 0.150,
    beta1_deg: float = 30.0,
    beta2_deg: float = 25.0,
    b1: float = 0.030,
    b2: float = 0.012,
    n_blades: int = 7,
    yaw_deg: float = 40.0,
    pitch_deg: float = 27.0,
    z_exaggeration: float = 2.6,
) -> str:
    """Axonometric view of the real blade set, with each angle marked in place.

    Blades are painted far-to-near using the projected depth, so near blades
    occlude far ones and the eye reads a solid wheel instead of a wire tangle.

    The axial coordinate is stretched by `z_exaggeration`, the way a textbook
    cutaway does: a real passage is 12 mm tall on a 300 mm wheel, and drawn to
    true scale the blades collapse into edge-on slivers. Radii, blade curvature
    and every angle in the r-theta plane are untouched, so the wrap angle and
    the blade shape remain exact.
    """
    geom = impeller_geometry(r1=r1, r2=r2, beta1_deg=beta1_deg, beta2_deg=beta2_deg,
                             b1=b1, b2=b2, n_blades=n_blades, n_points=90)
    width, height = 840, 520
    cx, cy, scale = 296.0, 262.0, 186.0 / r2

    def screen(x, y, z):
        u, v, depth = project_isometric(x, y, np.asarray(z) * z_exaggeration,
                                        yaw_deg, pitch_deg)
        return cx + scale * np.asarray(u), cy + scale * np.asarray(v), np.asarray(depth)

    parts = []

    # Hub disc, drawn first so blades sit on top of it.
    theta = geom["hub_theta"]
    hub_u, hub_v, _ = screen(r2 * np.cos(theta), r2 * np.sin(theta),
                             np.full_like(theta, -0.5 * b2))
    parts.append(_polygon(hub_u, hub_v, SURFACE_RAISED, BORDER_STRONG, 0.85))

    # Shroud and eye circles.
    for radius, z_off, colour, dash, opacity in (
        (r2, 0.5 * b2, BORDER_STRONG, "", 0.9),
        (r1, -0.5 * b1, TEXT_FAINT, "5,4", 0.8),
        (r1, 0.5 * b1, TEXT_FAINT, "5,4", 0.8),
    ):
        us, vs, _ = screen(radius * np.cos(theta), radius * np.sin(theta),
                           np.full_like(theta, z_off))
        parts.append(_polyline(us, vs, colour, 1.6, opacity, dash))

    # Blades, far to near.
    drawable = []
    for blade in geom["blades"]:
        u_hub, v_hub, d_hub = screen(blade["x"][0], blade["y"][0], blade["z"][0])
        u_shr, v_shr, _ = screen(blade["x"][-1], blade["y"][-1], blade["z"][-1])
        drawable.append((float(np.mean(d_hub)), u_hub, v_hub, u_shr, v_shr))
    drawable.sort(key=lambda item: item[0])

    for index, (_, u_hub, v_hub, u_shr, v_shr) in enumerate(drawable):
        nearest = index == len(drawable) - 1
        face_u = np.concatenate([u_hub, u_shr[::-1]])
        face_v = np.concatenate([v_hub, v_shr[::-1]])
        # Far blades fade with depth so the wheel reads three-dimensionally,
        # but never below the contrast needed to see the blade shape.
        shade = 0.45 + 0.45 * index / max(len(drawable) - 1, 1)
        parts.append(_polygon(
            face_u, face_v,
            ACCENT if nearest else SURFACE_RAISED,
            ACCENT if nearest else BORDER_STRONG,
            0.55 if nearest else 0.85 * shade,
        ))
        edge = ACCENT if nearest else TEXT_MUTED
        parts.append(_polyline(u_hub, v_hub, edge, 2.6 if nearest else 1.6, 1.0 if nearest else shade))
        parts.append(_polyline(u_shr, v_shr, edge, 2.6 if nearest else 1.6, 1.0 if nearest else shade))

    # Shaft and rotation sense.
    shaft_u, shaft_v, _ = screen(np.zeros(2), np.zeros(2),
                                 np.array([-1.2 * b1, 2.0 * b1]))
    parts.append(_polyline(shaft_u, shaft_v, TEXT_MUTED, 6.0))
    parts.append(f'<text x="{_f(shaft_u[1] - 26)}" y="{_f(shaft_v[1] - 14)}" '
                 f'fill="{TEXT_MUTED}" font-size="13">shaft &#969;</text>')

    # Angles are drawn on the blade nearest the viewer, i.e. the one with the
    # largest projected depth -- the same blade the painter's pass highlighted.
    depths = [float(np.mean(screen(b["x"][0], b["y"][0], b["z"][0])[2])) for b in geom["blades"]]
    near = geom["blades"][int(np.argmax(depths))]
    tip_theta = float(near["theta"][0, -1])
    tip_x, tip_y = r2 * math.cos(tip_theta), r2 * math.sin(tip_theta)

    def direction_on_screen(dx, dy, length):
        u0, v0, _ = screen(np.array([tip_x]), np.array([tip_y]), np.array([0.0]))
        u1, v1, _ = screen(np.array([tip_x + dx * length]), np.array([tip_y + dy * length]),
                           np.array([0.0]))
        return float(u0[0]), float(v0[0]), float(u1[0]), float(v1[0])

    tangential = (-math.sin(tip_theta), math.cos(tip_theta))
    radial = (math.cos(tip_theta), math.sin(tip_theta))
    beta2 = math.radians(beta2_deg)
    # The relative velocity leaves along the blade: beta_2 measured from the
    # direction *opposed* to the blade motion, tilted out by the meridional part.
    relative = (-tangential[0] * math.cos(beta2) + radial[0] * math.sin(beta2),
                -tangential[1] * math.cos(beta2) + radial[1] * math.sin(beta2))

    tip_u, tip_v, _, _ = direction_on_screen(1.0, 0.0, 0.0)
    for label, vector, length, colour, marker in (
        ("U&#8322;", tangential, 0.060, WARNING, "imp-orange"),
        ("W&#8322;", relative, 0.052, SUCCESS, "imp-green"),
        ("C&#8344;&#8322;", radial, 0.040, VORTICITY, "imp-purple"),
    ):
        u0, v0, u1, v1 = direction_on_screen(vector[0], vector[1], length)
        parts.append(f'<line x1="{_f(u0)}" y1="{_f(v0)}" x2="{_f(u1)}" y2="{_f(v1)}" '
                     f'stroke="{colour}" stroke-width="2.8" marker-end="url(#{marker})"/>')
        parts.append(f'<text x="{_f(u1 + 7)}" y="{_f(v1 - 7)}" fill="{colour}" '
                     f'font-size="13.5" font-weight="700">{label}</text>')

    u_t0, v_t0, u_t1, v_t1 = direction_on_screen(-tangential[0], -tangential[1], 0.050)
    parts.append(f'<line x1="{_f(u_t0)}" y1="{_f(v_t0)}" x2="{_f(u_t1)}" y2="{_f(v_t1)}" '
                 f'stroke="{TEXT_DIM}" stroke-width="1.4" stroke-dasharray="5,4"/>')
    u_w0, v_w0, u_w1, v_w1 = direction_on_screen(relative[0], relative[1], 0.052)
    start = math.degrees(math.atan2(v_t1 - v_t0, u_t1 - u_t0))
    end = math.degrees(math.atan2(v_w1 - v_w0, u_w1 - u_w0))
    parts.append(_angle_arc(tip_u, tip_v, 36.0, start, end, SHEAR, 2.2))
    parts.append(f'<text x="{_f(tip_u - 40)}" y="{_f(tip_v + 52)}" fill="{SHEAR}" '
                 f'font-size="14" font-weight="700">&#946;&#8322; = {beta2_deg:.0f}&#176;</text>')

    # Inlet (eye) angle on the same blade's leading edge.
    lead_theta = float(near["theta"][0, 0])
    lead_x, lead_y = r1 * math.cos(lead_theta), r1 * math.sin(lead_theta)
    lu, lv, _ = screen(np.array([lead_x]), np.array([lead_y]), np.array([0.0]))
    parts.append(f'<circle cx="{_f(lu[0])}" cy="{_f(lv[0])}" r="5.5" fill="{PRESSURE}"/>')
    parts.append(f'<line x1="{_f(lu[0])}" y1="{_f(lv[0])}" x2="{_f(lu[0] + 66)}" '
                 f'y2="{_f(lv[0] - 62)}" stroke="{PRESSURE}" stroke-width="1.2" '
                 f'stroke-dasharray="4,3"/>')
    parts.append(f'<text x="{_f(lu[0] + 70)}" y="{_f(lv[0] - 64)}" fill="{PRESSURE}" '
                 f'font-size="12.5" font-weight="600">&#946;&#8321; = {beta1_deg:.0f}&#176; at the eye</text>')

    legend_rows = [
        (WARNING, "U&#8322; = &#969;r&#8322; &#183; blade speed, purely tangential"),
        (SUCCESS, "W&#8322; &#183; relative velocity, leaves along the blade"),
        (VORTICITY, "C&#8344;&#8322; = Q/(2&#960;r&#8322;b&#8322;) &#183; meridional, radial here"),
        (SHEAR, f"&#946;&#8322; from TANGENTIAL ({90 - beta2_deg:.0f}&#176; from meridional)"),
        (PRESSURE, "&#946;&#8321; &#183; inlet blade angle, set for shockless entry"),
    ]
    legend = []
    for index, (colour, text) in enumerate(legend_rows):
        y = 374 + index * 24
        legend.append(f'<rect x="566" y="{y - 9}" width="18" height="4" rx="2" fill="{colour}"/>')
        legend.append(f'<text x="592" y="{y}" fill="{TEXT_MUTED}" font-size="11.5">{text}</text>')

    return f"""
    <svg viewBox="0 0 {width} {height}" width="100%" height="{height}"
         xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_marker_defs()}
        <text x="24" y="28" fill="{ACCENT}" font-size="15" font-weight="bold">Backswept centrifugal impeller &#183; where each angle actually lives</text>
        <text x="24" y="48" fill="{TEXT_DIM}" font-size="12">{n_blades} blades &#183; r&#8321; = {r1 * 1000:.0f} mm, r&#8322; = {r2 * 1000:.0f} mm &#183; &#946;&#8321; = {beta1_deg:.0f}&#176;, &#946;&#8322; = {beta2_deg:.0f}&#176; &#183; blade wraps {geom['wrap_angle_deg']:.0f}&#176; around the shaft</text>
        {"".join(parts)}
        <text x="566" y="346" fill="{TEXT}" font-size="13" font-weight="600">At the trailing edge (tip)</text>
        {"".join(legend)}
        <text x="24" y="{height - 34}" fill="{TEXT_DIM}" font-size="11.5">Axonometric projection of the computed blade surface; axial scale exaggerated {z_exaggeration:.1f}&#215; so the passage is visible.</text>
        <text x="24" y="{height - 16}" fill="{TEXT_DIM}" font-size="11.5">Angles appear foreshortened because the page is not the blade-to-blade plane &#8212; the true-shape figure below shows their real size.</text>
    </svg>
    """


def diagram_impeller_meridional(
    r1: float = 0.045,
    r2: float = 0.150,
    b1: float = 0.030,
    b2: float = 0.012,
    r_hub: float = 0.018,
) -> str:
    """The r-z (meridional) section: where b_1, b_2 and the eye are measured.

    Students routinely confuse this with the blade-to-blade view. They are
    perpendicular cuts through the same wheel: this one contains the shaft axis,
    the other is wrapped around it. This is also the section that shows the
    ninety-degree turn a centrifugal machine makes -- flow enters axially along
    the shaft and leaves radially at the tip, which is exactly why the radius,
    and therefore U = omega r, changes at all.

    Drawn for the upper half only; the wheel is a body of revolution about the
    dash-dot axis. Radii are to scale; the axial direction is stretched so the
    passage heights are legible.
    """
    width, height = 780, 430
    axis_y = 332.0
    x_axis0 = 150.0
    r_scale = 200.0 / r2           # r2 spans 200 px above the shaft axis
    z_scale = r_scale * 2.4        # axial stretch, stated in the caption
    z_inlet = 0.085                # length of the axial approach duct, metres

    def rx(radius):
        """Radius maps to vertical distance above the shaft axis."""
        return axis_y - r_scale * radius

    def zx(z):
        """Axial position maps to horizontal distance."""
        return x_axis0 + z_scale * z

    # Hub and shroud contours: axial at the inlet, radial at the tip.
    hub = (f'M {_f(zx(0))} {_f(rx(r_hub))} '
           f'L {_f(zx(z_inlet * 0.45))} {_f(rx(r_hub))} '
           f'Q {_f(zx(z_inlet))} {_f(rx(r_hub))} {_f(zx(z_inlet))} {_f(rx(r2 * 0.55))} '
           f'L {_f(zx(z_inlet))} {_f(rx(r2))}')
    shroud = (f'M {_f(zx(0))} {_f(rx(r1))} '
              f'L {_f(zx(z_inlet * 0.30))} {_f(rx(r1))} '
              f'Q {_f(zx(z_inlet - b2))} {_f(rx(r1))} '
              f'{_f(zx(z_inlet - b2))} {_f(rx(r2 * 0.62))} '
              f'L {_f(zx(z_inlet - b2))} {_f(rx(r2))}')
    channel = (f'{hub} L {_f(zx(z_inlet - b2))} {_f(rx(r2))} '
               f'L {_f(zx(z_inlet - b2))} {_f(rx(r2 * 0.62))} '
               f'Q {_f(zx(z_inlet - b2))} {_f(rx(r1))} {_f(zx(z_inlet * 0.30))} {_f(rx(r1))} '
               f'L {_f(zx(0))} {_f(rx(r1))} Z')

    return f"""
    <svg viewBox="0 0 {width} {height}" width="100%" height="{height}"
         xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_marker_defs()}
        <text x="24" y="28" fill="{ACCENT}" font-size="15" font-weight="bold">Meridional (r&#8211;z) section &#183; the ninety-degree turn, and where b&#8321; and b&#8322; are measured</text>
        <text x="24" y="48" fill="{TEXT_DIM}" font-size="12">This cut contains the shaft axis. The blade-to-blade view is the perpendicular cut, wrapped around it. Upper half shown; the wheel is a body of revolution.</text>

        <path d="{channel}" fill="{ACCENT}" fill-opacity="0.16"/>
        <path d="{hub}" fill="none" stroke="{TEXT_MUTED}" stroke-width="2.6"/>
        <path d="{shroud}" fill="none" stroke="{TEXT_MUTED}" stroke-width="2.6"/>

        <line x1="60" y1="{_f(axis_y)}" x2="{width - 60}" y2="{_f(axis_y)}"
              stroke="{TEXT_MUTED}" stroke-width="1.8" stroke-dasharray="14,5,3,5"/>
        <text x="{width - 190}" y="{_f(axis_y + 22)}" fill="{TEXT_MUTED}" font-size="12">shaft axis &#183; z</text>

        <line x1="{_f(zx(0) + 8)}" y1="{_f((rx(r1) + rx(r_hub)) / 2)}" x2="{_f(zx(0) + 78)}" y2="{_f((rx(r1) + rx(r_hub)) / 2)}"
              stroke="{VORTICITY}" stroke-width="2.8" marker-end="url(#imp-purple)"/>
        <text x="{_f(zx(0) + 8)}" y="{_f((rx(r1) + rx(r_hub)) / 2 - 16)}" fill="{VORTICITY}" font-size="12" font-weight="600">flow in, axial</text>

        <line x1="{_f(zx(z_inlet) + 14)}" y1="{_f(rx(r2 * 0.94))}" x2="{_f(zx(z_inlet) + 74)}" y2="{_f(rx(r2 * 0.94))}"
              stroke="{VORTICITY}" stroke-width="2.8" marker-end="url(#imp-purple)"/>
        <text x="{_f(zx(z_inlet) + 16)}" y="{_f(rx(r2 * 0.94) - 14)}" fill="{VORTICITY}" font-size="12.5" font-weight="600">out: radial + swirl</text>

        <line x1="{_f(zx(0) + 108)}" y1="{_f(rx(r1))}" x2="{_f(zx(0) + 108)}" y2="{_f(rx(r_hub))}"
              stroke="{WARNING}" stroke-width="2" marker-start="url(#imp-orange)" marker-end="url(#imp-orange)"/>
        <text x="{_f(zx(0) + 116)}" y="{_f((rx(r1) + rx(r_hub)) / 2 + 4)}" fill="{WARNING}" font-size="13" font-weight="700">b&#8321; = {b1 * 1000:.0f} mm</text>

        <line x1="{_f(zx(z_inlet) + 6)}" y1="{_f(rx(r2))}" x2="{_f(zx(z_inlet - b2) - 6)}" y2="{_f(rx(r2))}"
              stroke="{WARNING}" stroke-width="2" marker-start="url(#imp-orange)" marker-end="url(#imp-orange)"/>
        <text x="{_f(zx(z_inlet) - 128)}" y="{_f(rx(r2) - 16)}" fill="{WARNING}" font-size="13" font-weight="700">b&#8322; = {b2 * 1000:.0f} mm</text>

        <line x1="{_f(zx(z_inlet) + 96)}" y1="{_f(axis_y)}" x2="{_f(zx(z_inlet) + 96)}" y2="{_f(rx(r2))}"
              stroke="{SUCCESS}" stroke-width="1.8" marker-start="url(#imp-green)" marker-end="url(#imp-green)"/>
        <text x="{_f(zx(z_inlet) + 104)}" y="{_f((axis_y + rx(r2)) / 2)}" fill="{SUCCESS}" font-size="12.5" font-weight="600">r&#8322; = {r2 * 1000:.0f} mm</text>

        <line x1="{_f(zx(0) - 26)}" y1="{_f(axis_y)}" x2="{_f(zx(0) - 26)}" y2="{_f(rx(r1))}"
              stroke="{SUCCESS}" stroke-width="1.8" marker-start="url(#imp-green)" marker-end="url(#imp-green)"/>
        <text x="{_f(zx(0) - 122)}" y="{_f((axis_y + rx(r1)) / 2 + 4)}" fill="{SUCCESS}" font-size="12.5" font-weight="600">r&#8321; = {r1 * 1000:.0f} mm</text>
        <text x="{_f(zx(0) - 122)}" y="{_f((axis_y + rx(r1)) / 2 + 20)}" fill="{TEXT_DIM}" font-size="11">(the eye)</text>

        <text x="24" y="{height - 34}" fill="{TEXT_DIM}" font-size="11.5">Flow area is 2&#960;rb at every station. b tapers from {b1 * 1000:.0f} to {b2 * 1000:.0f} mm so that 2&#960;rb, and hence C&#8344;, stay roughly constant while r more than triples.</text>
        <text x="24" y="{height - 16}" fill="{TEXT_DIM}" font-size="11.5">Radii to scale; the axial direction is stretched {z_scale / r_scale:.1f}&#215; for legibility. Blades fill the shaded channel and are seen edge-on in this view.</text>
    </svg>
    """


def diagram_outlet_triangle_true_shape(
    beta2_deg: float = 25.0,
    u2: float = 45.0,
    cm2: float = 6.0,
    sigma: float = 0.85,
) -> str:
    """The outlet velocity triangle in true shape, with every angle undistorted.

    The 3D figure shows *where* the angles live; this one shows their true size,
    because here the page is the blade-to-blade plane. Horizontal is tangential
    (the direction the tip moves), vertical is meridional.
    """
    beta2 = math.radians(beta2_deg)
    c_theta2 = sigma * u2 - cm2 / math.tan(beta2)
    c_theta2_ideal = u2 - cm2 / math.tan(beta2)

    width, height = 780, 470
    ox, oy = 96.0, 268.0
    scale = 470.0 / max(u2, 1e-9)

    def pt(tangential, meridional):
        return ox + scale * tangential, oy - scale * meridional

    ux, uy = pt(u2, 0.0)
    cx_, cy_ = pt(c_theta2, cm2)
    ix, iy = pt(c_theta2_ideal, cm2)
    # Angle of W2 at the tip of U2, measured from the -tangential direction.
    w_angle = math.degrees(math.atan2(cm2, u2 - c_theta2))
    alpha2 = math.degrees(math.atan2(cm2, c_theta2))

    return f"""
    <svg viewBox="0 0 {width} {height}" width="100%" height="{height}"
         xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_marker_defs()}
        <text x="24" y="28" fill="{ACCENT}" font-size="15" font-weight="bold">Outlet velocity triangle in true shape (blade-to-blade plane)</text>
        <text x="24" y="48" fill="{TEXT_DIM}" font-size="12">Horizontal: tangential, the direction the tip moves. Vertical: meridional. The triangle closes because C = U + W.</text>

        <line x1="{_f(ox - 40)}" y1="{_f(oy)}" x2="{width - 40}" y2="{_f(oy)}" stroke="{BORDER_STRONG}" stroke-width="1.2" stroke-dasharray="4,4"/>
        <line x1="{_f(ox)}" y1="{_f(oy + 24)}" x2="{_f(ox)}" y2="72" stroke="{BORDER_STRONG}" stroke-width="1.2" stroke-dasharray="4,4"/>
        <text x="{_f(ox + 8)}" y="84" fill="{TEXT_FAINT}" font-size="11.5">meridional</text>

        <line x1="{_f(ox)}" y1="{_f(oy)}" x2="{_f(ux)}" y2="{_f(uy)}" stroke="{WARNING}" stroke-width="3.2" marker-end="url(#imp-orange)"/>
        <text x="{_f(ox + (ux - ox) * 0.36)}" y="{_f(oy + 26)}" fill="{WARNING}" font-size="13.5" font-weight="700">U&#8322; = &#969;r&#8322; = {u2:.1f} m/s</text>

        <line x1="{_f(ux)}" y1="{_f(uy)}" x2="{_f(cx_)}" y2="{_f(cy_)}" stroke="{SUCCESS}" stroke-width="3.2" marker-end="url(#imp-green)"/>
        <text x="{_f((ux + cx_) / 2 + 14)}" y="{_f((uy + cy_) / 2 + 4)}" fill="{SUCCESS}" font-size="13.5" font-weight="700">W&#8322;</text>

        <line x1="{_f(ox)}" y1="{_f(oy)}" x2="{_f(cx_)}" y2="{_f(cy_)}" stroke="{ACCENT}" stroke-width="3.2" marker-end="url(#imp-sky)"/>
        <text x="{_f(ox + (cx_ - ox) * 0.55)}" y="{_f(oy - (oy - cy_) * 0.55 - 16)}" fill="{ACCENT}" font-size="13.5" font-weight="700">C&#8322;</text>

        <line x1="{_f(ix)}" y1="{_f(iy)}" x2="{_f(cx_)}" y2="{_f(cy_)}" stroke="{PRESSURE}" stroke-width="2.6" stroke-dasharray="7,4"/>
        <circle cx="{_f(ix)}" cy="{_f(iy)}" r="4" fill="{PRESSURE}"/>
        <text x="{_f(cx_ + 10)}" y="{_f(cy_ - 30)}" fill="{PRESSURE}" font-size="12.5" font-weight="600">slip: (1&#8722;&#963;)U&#8322; = {(1 - sigma) * u2:.1f} m/s</text>
        <text x="{_f(cx_ + 10)}" y="{_f(cy_ - 14)}" fill="{TEXT_DIM}" font-size="11.5">no friction &#8212; the relative eddy alone</text>

        <line x1="{_f(cx_)}" y1="{_f(cy_)}" x2="{_f(cx_)}" y2="{_f(oy)}" stroke="{VORTICITY}" stroke-width="2.6"/>
        <text x="{_f(cx_ - 96)}" y="{_f((cy_ + oy) / 2 + 22)}" fill="{VORTICITY}" font-size="12.5" font-weight="600">C&#8344;&#8322; = {cm2:.1f} m/s</text>

        <line x1="{_f(ox)}" y1="{_f(oy + 84)}" x2="{_f(cx_)}" y2="{_f(oy + 84)}" stroke="{ACCENT}" stroke-width="1.8" marker-start="url(#imp-sky)" marker-end="url(#imp-sky)"/>
        <text x="{_f(ox + (cx_ - ox) / 2 - 130)}" y="{_f(oy + 104)}" fill="{ACCENT}" font-size="12.5" font-weight="600">C&#952;&#8322; = {c_theta2:.1f} m/s &#8212; the only component that does any work</text>

        {_angle_arc(ux, uy, 44.0, 180.0, 180.0 + w_angle, SHEAR, 2.4)}
        <text x="{_f(ux - 96)}" y="{_f(oy + 26)}" fill="{SHEAR}" font-size="14" font-weight="700">&#946;&#8322; = {beta2_deg:.0f}&#176;</text>
        <text x="{_f(ux - 176)}" y="{_f(oy + 44)}" fill="{TEXT_DIM}" font-size="11.5">between W&#8322; and the &#8722;tangential direction</text>

        {_angle_arc(ox, oy, 86.0, 0.0, -alpha2, ACCENT, 2.2)}
        <text x="{_f(ox + 94)}" y="{_f(oy - 14)}" fill="{ACCENT}" font-size="13" font-weight="700">&#945;&#8322; = {alpha2:.0f}&#176;</text>

        <text x="24" y="{height - 52}" fill="{TEXT}" font-size="12.5">Work per unit mass: w = U&#8322;C&#952;&#8322; &#8722; U&#8321;C&#952;&#8321;. Only the horizontal projection of C&#8322; enters, so a purely radial discharge would do no work at all.</text>
        <text x="24" y="{height - 32}" fill="{TEXT_DIM}" font-size="11.5">Dashed red marks where the flow would arrive if it left exactly along the blade. Slip pulls C&#952;&#8322; back: fewer blades, wider passage, stronger relative eddy.</text>
        <text x="24" y="{height - 14}" fill="{TEXT_DIM}" font-size="11.5">Backswept blades (&#946;&#8322; &lt; 90&#176;) subtract C&#8344;&#8322;/tan&#946;&#8322; from &#963;U&#8322;, which is what tilts the head&#8211;flow line downward and makes the machine stable.</text>
    </svg>
    """
