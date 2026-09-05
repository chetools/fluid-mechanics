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


def _angle_mark(cx, cy, start_deg, end_deg, colour, label, radius=48.0,
                ray_len=None, label_gap=26.0, sub=None) -> str:
    """A textbook angle mark: a vertex, two construction rays, an arc, a label.

    An arc floating beside a vector does not say which two directions it spans.
    Drawing both bounding rays from the vertex does, so every angle in these
    figures is marked the traditional way: thin dashed rays out to just past the
    arc, a filled wedge to catch the eye, and the label on the bisector inside
    the wedge where it cannot be read as belonging to the neighbouring angle.

    Angles are screen-space degrees (SVG y points down). `sub` adds a smaller
    second line under the label, for naming the two directions being spanned.
    """
    sweep = (end_deg - start_deg) % 360.0
    if sweep > 180.0:
        sweep -= 360.0
    if ray_len is None:
        ray_len = radius + 18.0

    def point(distance, degrees):
        return (cx + distance * math.cos(math.radians(degrees)),
                cy + distance * math.sin(math.radians(degrees)))

    parts = []
    # The two bounding rays. Dashed so they read as construction, not as vectors.
    for degrees in (start_deg, start_deg + sweep):
        x, y = point(ray_len, degrees)
        parts.append(f'<line x1="{_f(cx)}" y1="{_f(cy)}" x2="{_f(x)}" y2="{_f(y)}" '
                     f'stroke="{colour}" stroke-width="1.3" stroke-dasharray="4,3" '
                     f'stroke-opacity="0.75"/>')

    # Shaded wedge, so a narrow angle is still visible.
    x0, y0 = point(radius, start_deg)
    x1, y1 = point(radius, start_deg + sweep)
    direction = 1 if sweep > 0 else 0
    parts.append(f'<path d="M {_f(cx)} {_f(cy)} L {_f(x0)} {_f(y0)} '
                 f'A {_f(radius)} {_f(radius)} 0 0 {direction} {_f(x1)} {_f(y1)} Z" '
                 f'fill="{colour}" fill-opacity="0.16" stroke="none"/>')
    parts.append(_angle_arc(cx, cy, radius, start_deg, end_deg, colour, 2.2))
    parts.append(f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="3" fill="{colour}"/>')

    # Label on the bisector, pushed out far enough to clear the arc.
    bisector = start_deg + sweep / 2.0
    lx, ly = point(radius + label_gap, bisector)
    anchor = "start" if math.cos(math.radians(bisector)) >= 0 else "end"
    parts.append(f'<text x="{_f(lx)}" y="{_f(ly)}" fill="{colour}" font-size="14" '
                 f'font-weight="700" text-anchor="{anchor}" '
                 f'dominant-baseline="middle">{label}</text>')
    if sub:
        parts.append(f'<text x="{_f(lx)}" y="{_f(ly + 16)}" fill="{TEXT_DIM}" '
                     f'font-size="10.5" text-anchor="{anchor}" '
                     f'dominant-baseline="middle">{sub}</text>')
    return "".join(parts)


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
    width, height = 1000, 520
    cx, cy, scale = 286.0, 258.0, 182.0 / r2

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

    # Which blade carries the annotation. It must be on the near side (so the
    # marks are not drawn behind the wheel) *and* have its tip projecting to the
    # right, where there is open canvas: cramming a velocity triangle and two
    # angle marks against the left edge made them illegible.
    tip_screen = []
    for blade in geom["blades"]:
        u_tip, _, d_tip = screen(blade["x"][0, -1:], blade["y"][0, -1:], blade["z"][0, -1:])
        tip_screen.append((float(u_tip[0]), float(d_tip[0])))
    median_depth = float(np.median([d for _, d in tip_screen]))
    front = [i for i, (_, d) in enumerate(tip_screen) if d >= median_depth]
    near_index = max(front, key=lambda i: tip_screen[i][0])
    near = geom["blades"][near_index]
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

    # The absolute velocity closes the triangle: C = U + W. It has to be drawn
    # here too, because alpha_2 is the angle between C and the tangential
    # direction and an angle cannot be marked against a ray that is not there.
    # Magnitudes use the same representative C_m2/U_2 ratio as the true-shape
    # figure, so the two pictures show the same triangle.
    cm_over_u = 0.36
    absolute = (tangential[0] + (radial[0] * cm_over_u - tangential[0] * cm_over_u / math.tan(beta2)),
                tangential[1] + (radial[1] * cm_over_u - tangential[1] * cm_over_u / math.tan(beta2)))
    absolute_norm = math.hypot(*absolute) or 1.0
    absolute = (absolute[0] / absolute_norm, absolute[1] / absolute_norm)

    tip_u, tip_v, _, _ = direction_on_screen(1.0, 0.0, 0.0)
    for label, vector, length, colour, marker in (
        ("U&#8322;", tangential, 0.082, WARNING, "imp-orange"),
        ("W&#8322;", relative, 0.072, SUCCESS, "imp-green"),
        ("C&#8344;&#8322;", radial, 0.052, VORTICITY, "imp-purple"),
        ("C&#8322;", absolute, 0.078, ACCENT, "imp-sky"),
    ):
        u0, v0, u1, v1 = direction_on_screen(vector[0], vector[1], length)
        parts.append(f'<line x1="{_f(u0)}" y1="{_f(v0)}" x2="{_f(u1)}" y2="{_f(v1)}" '
                     f'stroke="{colour}" stroke-width="2.8" marker-end="url(#{marker})"/>')
        parts.append(f'<text x="{_f(u1 + 7)}" y="{_f(v1 - 7)}" fill="{colour}" '
                     f'font-size="13.5" font-weight="700">{label}</text>')

    u_t0, v_t0, u_t1, v_t1 = direction_on_screen(-tangential[0], -tangential[1], 0.068)
    u_w0, v_w0, u_w1, v_w1 = direction_on_screen(relative[0], relative[1], 0.072)
    start = math.degrees(math.atan2(v_t1 - v_t0, u_t1 - u_t0))
    end = math.degrees(math.atan2(v_w1 - v_w0, u_w1 - u_w0))
    parts.append(_angle_mark(tip_u, tip_v, start, end, SHEAR,
                             f"&#946;&#8322; = {beta2_deg:.0f}&#176;",
                             radius=46.0, label_gap=40.0))

    # alpha_2, between C_2 and the +tangential direction, marked at the same vertex.
    u_a0, v_a0, u_a1, v_a1 = direction_on_screen(absolute[0], absolute[1], 0.078)
    u_p0, v_p0, u_p1, v_p1 = direction_on_screen(tangential[0], tangential[1], 0.082)
    parts.append(_angle_mark(
        tip_u, tip_v,
        math.degrees(math.atan2(v_p1 - v_p0, u_p1 - u_p0)),
        math.degrees(math.atan2(v_a1 - v_a0, u_a1 - u_a0)),
        ACCENT, "&#945;&#8322;", radius=84.0, label_gap=22.0))

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
        (ACCENT, "C&#8322; = U&#8322; + W&#8322; &#183; absolute velocity, what the volute sees"),
        (SHEAR, f"&#946;&#8322; &#183; W&#8322; from &#8722;tangential ({90 - beta2_deg:.0f}&#176; from meridional)"),
        (ACCENT, "&#945;&#8322; &#183; C&#8322; from +tangential &#183; the flow angle"),
        (PRESSURE, "&#946;&#8321; &#183; inlet blade angle, set for shockless entry"),
    ]
    legend = []
    for index, (colour, text) in enumerate(legend_rows):
        y = 328 + index * 24
        legend.append(f'<rect x="716" y="{y - 9}" width="18" height="4" rx="2" fill="{colour}"/>')
        legend.append(f'<text x="742" y="{y}" fill="{TEXT_MUTED}" font-size="11.5">{text}</text>')

    return f"""
    <svg viewBox="0 0 {width} {height}" width="100%" height="{height}"
         xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_marker_defs()}
        <text x="24" y="28" fill="{ACCENT}" font-size="15" font-weight="bold">Backswept centrifugal impeller &#183; where each angle actually lives</text>
        <text x="24" y="48" fill="{TEXT_DIM}" font-size="12">{n_blades} blades &#183; r&#8321; = {r1 * 1000:.0f} mm, r&#8322; = {r2 * 1000:.0f} mm &#183; &#946;&#8321; = {beta1_deg:.0f}&#176;, &#946;&#8322; = {beta2_deg:.0f}&#176; &#183; blade wraps {geom['wrap_angle_deg']:.0f}&#176; around the shaft</text>
        {"".join(parts)}
        <text x="716" y="300" fill="{TEXT}" font-size="13" font-weight="600">At the trailing edge (tip)</text>
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

    width, height = 780, 578
    ox, oy = 96.0, 250.0
    scale = 470.0 / max(u2, 1e-9)

    def pt(tangential, meridional):
        return ox + scale * tangential, oy - scale * meridional

    ux, uy = pt(u2, 0.0)
    cx_, cy_ = pt(c_theta2, cm2)
    ix, iy = pt(c_theta2_ideal, cm2)
    # Two different angles live at the tip of U2, and conflating them is the
    # classic error this whole section warns about:
    #   beta_2  (blade) - set by the metal, measured to the no-slip ideal tip;
    #   beta_2' (flow)  - where the fluid actually goes, once slip has pulled
    #                     C_theta2 back. Slip IS the difference between them.
    flow_coefficient = cm2 / u2 if u2 else 0.0
    beta2_flow = math.degrees(math.atan2(cm2, u2 - c_theta2))
    beta2_blade_check = math.degrees(math.atan2(cm2, u2 - c_theta2_ideal))
    alpha2 = math.degrees(math.atan2(cm2, c_theta2))

    # At a low flow coefficient the triangle really is this flat, and the wedges
    # really are slivers. Say so rather than exaggerating the meridional axis,
    # which would make every angle in the figure a lie.
    flat_note = ""
    if flow_coefficient < 0.12:
        flat_note = (
            f'<text x="24" y="84" fill="{WARNING}" font-size="11.5">'
            f'At this flow coefficient C&#8344;&#8322;/U&#8322; = {flow_coefficient:.2f} the triangle '
            f'genuinely is this flat and &#945;&#8322; genuinely is this shallow: the discharge is '
            f'almost purely tangential, which is exactly what makes the volute hard to design.'
            f'</text>'
        )

    return f"""
    <svg viewBox="0 0 {width} {height}" width="100%" height="{height}"
         xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_marker_defs()}
        <text x="24" y="28" fill="{ACCENT}" font-size="15" font-weight="bold">Outlet velocity triangle in true shape (blade-to-blade plane)</text>
        <text x="24" y="48" fill="{TEXT_DIM}" font-size="12">Horizontal: tangential, the direction the tip moves. Vertical: meridional. The triangle closes because C = U + W.</text>
        <text x="24" y="66" fill="{TEXT_FAINT}" font-size="11.5">Each angle is marked the usual way: a dot at the vertex, dashed rays along the two directions it spans, and the value inside the wedge. No angular exaggeration.</text>
        {flat_note}

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
        <text x="{_f(cx_ - 7)}" y="{_f(cy_ + 18)}" fill="{VORTICITY}" font-size="12" font-weight="700" text-anchor="end">C&#8344;&#8322;</text>

        <line x1="{_f(ox)}" y1="{_f(oy + 84)}" x2="{_f(cx_)}" y2="{_f(oy + 84)}" stroke="{ACCENT}" stroke-width="1.8" marker-start="url(#imp-sky)" marker-end="url(#imp-sky)"/>
        <text x="{_f(ox + (cx_ - ox) / 2 - 130)}" y="{_f(oy + 104)}" fill="{ACCENT}" font-size="12.5" font-weight="600">C&#952;&#8322; = {c_theta2:.1f} m/s &#8212; the only component that does any work</text>

        <line x1="{_f(ux)}" y1="{_f(uy)}" x2="{_f(ix)}" y2="{_f(iy)}" stroke="{SUCCESS}" stroke-width="2" stroke-dasharray="7,4" stroke-opacity="0.75"/>
        <text x="{_f(ix - 10)}" y="{_f(iy + 20)}" fill="{SUCCESS}" font-size="11" fill-opacity="0.85" text-anchor="end">blade direction</text>

        {_angle_mark(ux, uy, 180.0, 180.0 + beta2_blade_check, SHEAR,
                     f"&#946;&#8322; = {beta2_deg:.0f}&#176;", radius=104.0, label_gap=32.0)}

        {_angle_mark(ux, uy, 180.0, 180.0 + beta2_flow, SUCCESS,
                     f"&#946;&#8322;&#8242; = {beta2_flow:.1f}&#176;", radius=44.0, label_gap=24.0)}

        {_angle_mark(ox, oy, 0.0, -alpha2, ACCENT,
                     f"&#945;&#8322; = {alpha2:.1f}&#176;", radius=92.0, label_gap=30.0)}

        <text x="24" y="{height - 130}" fill="{TEXT}" font-size="12.5" font-weight="600">Each angle, and the two rays it is measured between:</text>
        <rect x="24" y="{height - 120}" width="14" height="3.5" rx="1.5" fill="{ACCENT}"/>
        <text x="46" y="{height - 112}" fill="{TEXT_MUTED}" font-size="11.5">&#945;&#8322; = {alpha2:.1f}&#176; &#183; from the +tangential ray to C&#8322;, at the tail of the triangle &#183; the angle the volute must accept</text>
        <rect x="24" y="{height - 102}" width="14" height="3.5" rx="1.5" fill="{SUCCESS}"/>
        <text x="46" y="{height - 94}" fill="{TEXT_MUTED}" font-size="11.5">&#946;&#8322;&#8242; = {beta2_flow:.1f}&#176; &#183; from the &#8722;tangential ray to W&#8322;, at the tip of U&#8322; &#183; the FLOW angle, where the fluid actually goes</text>
        <rect x="24" y="{height - 84}" width="14" height="3.5" rx="1.5" fill="{SHEAR}"/>
        <text x="46" y="{height - 76}" fill="{TEXT_MUTED}" font-size="11.5">&#946;&#8322; = {beta2_deg:.0f}&#176; &#183; from the same &#8722;tangential ray to the blade direction &#183; the BLADE angle, set by the metal</text>
        <rect x="24" y="{height - 66}" width="14" height="3.5" rx="1.5" fill="{VORTICITY}"/>
        <text x="46" y="{height - 58}" fill="{TEXT_MUTED}" font-size="11.5">C&#8344;&#8322; = {cm2:.1f} m/s &#183; the meridional component, the vertical purple line &#183; it does no work</text>
        <text x="24" y="{height - 34}" fill="{TEXT}" font-size="12.5">Work per unit mass: w = U&#8322;C&#952;&#8322; &#8722; U&#8321;C&#952;&#8321;. Only the horizontal projection of C&#8322; enters, so a purely radial discharge would do no work at all.</text>
        <text x="24" y="{height - 14}" fill="{TEXT_DIM}" font-size="11.5">The gap between the two &#946; arcs is slip: the fluid does not leave along the blade. Substituting one angle for the other is the classic turbomachinery error.</text>
    </svg>
    """
