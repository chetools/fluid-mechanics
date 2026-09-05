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


def diagram_blade_angles(
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
    """Two panels: the wheel in space, and the blade angles at true size.

    Split the way turbomachinery texts split it, and for the same reason. The
    left panel is an axonometric projection: it shows how the blades sit in
    space, and it is honest about nothing else, because a projection foreshortens
    each direction by a different amount and an angle drawn on it is not the
    angle it names. The right panel looks straight down the shaft, where the
    r-theta plane is undistorted, so beta_1 and beta_2 appear at TRUE size.

    Blades in the left panel are painted far-to-near by projected depth, so near
    blades occlude far ones and the eye reads a solid wheel rather than a wire
    tangle. Its axial coordinate is stretched by `z_exaggeration`, the way a
    cutaway does: a real passage is 12 mm tall on a 300 mm wheel and would
    otherwise collapse to an edge-on sliver. Radii, blade curvature and every
    r-theta angle are untouched, so the wrap angle and blade shape stay exact.

    The velocity triangle is deliberately absent from both panels; it belongs to
    `diagram_outlet_triangle_true_shape`, where it can be drawn closed and to
    scale.
    """
    geom = impeller_geometry(r1=r1, r2=r2, beta1_deg=beta1_deg, beta2_deg=beta2_deg,
                             b1=b1, b2=b2, n_blades=n_blades, n_points=90)
    width, height = 880, 522
    cx, cy, scale = 232.0, 208.0, 120.0 / r2

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

    # --- panel 2: plan view, looking straight down the shaft ------------------
    #
    # This is where the blade angles are marked, and the reason is geometric
    # rather than aesthetic. An axonometric view foreshortens every direction by
    # a different amount, so an angle drawn on it is not the angle it names -- a
    # 25 degree blade can easily project as 50. Looking straight down the shaft
    # leaves the r-theta plane undistorted, so beta appears at TRUE size, which
    # is why every pump textbook marks blade angles on a plan view.
    #
    # A blade angle is then pure geometry: the angle at one point between the
    # tangent to the circle and the tangent to the blade camberline. Both rays
    # are real curves on the wheel, so both are drawn.
    plan_cx, plan_cy = 604.0, 216.0
    plan_scale = 116.0 / r2
    # A plan view of an axisymmetric wheel may be spun freely, so spin it until
    # the annotated blade's trailing edge sits at the lower right, where the
    # marks have room. A rigid rotation preserves every angle, so nothing the
    # figure asserts changes.
    plan_rot = math.radians(-32.0) - float(geom["blades"][0]["theta"][0, -1])
    rot_cos, rot_sin = math.cos(plan_rot), math.sin(plan_rot)

    def plan(x, y):
        x, y = np.asarray(x), np.asarray(y)
        xr = x * rot_cos - y * rot_sin
        yr = x * rot_sin + y * rot_cos
        return plan_cx + plan_scale * xr, plan_cy - plan_scale * yr

    plan_parts = []
    circle_theta = geom["hub_theta"]
    for radius, colour, dash in ((r2, BORDER_STRONG, ""), (r1, TEXT_FAINT, "5,4")):
        cu, cv = plan(radius * np.cos(circle_theta), radius * np.sin(circle_theta))
        plan_parts.append(_polyline(cu, cv, colour, 1.5, 0.9, dash))

    annotated = 0
    for index, blade in enumerate(geom["blades"]):
        bu, bv = plan(blade["x"][0], blade["y"][0])
        highlight = index == annotated
        plan_parts.append(_polyline(bu, bv, ACCENT if highlight else TEXT_FAINT,
                                    3.0 if highlight else 1.4,
                                    1.0 if highlight else 0.5))

    # Rotation sense. The camberline integrates to increasing theta with
    # increasing radius, so the wheel must turn towards DECREASING theta for the
    # blades to trail backwards -- which is what "backswept" means.
    # Rotation sense. This has to be unambiguous, because every angle in the
    # figure is measured against it. The camberline integrates to increasing
    # theta with increasing radius, so the wheel must turn towards DECREASING
    # theta for the blades to trail -- which is what "backswept" means. The
    # plan view flips y, so decreasing theta reads CLOCKWISE on the page.
    #
    # Drawn by sampling the arc rather than with an SVG arc command: the
    # large-arc and sweep flags are easy to get subtly wrong, and a polyline
    # with marker-end orients its own arrowhead from the last segment, so the
    # arrow cannot disagree with the path.
    theta_tip_world = float(geom["blades"][0]["theta"][0, -1])
    sweep = np.linspace(theta_tip_world + math.radians(214.0),
                        theta_tip_world + math.radians(140.0), 40)
    spin_r = r2 * 1.05
    su, sv = plan(spin_r * np.cos(sweep), spin_r * np.sin(sweep))
    plan_parts.append(f'<polyline points="{_points(su, sv)}" fill="none" '
                      f'stroke="{TEXT_MUTED}" stroke-width="2.4" '
                      f'marker-end="url(#imp-dim)"/>')
    mid_u, mid_v = plan(spin_r * 1.20 * math.cos(sweep[len(sweep) // 2]),
                        spin_r * 1.20 * math.sin(sweep[len(sweep) // 2]))
    plan_parts.append(f'<text x="{_f(mid_u)}" y="{_f(mid_v)}" fill="{TEXT_MUTED}" '
                      f'font-size="12" font-weight="700" text-anchor="middle" '
                      f'dominant-baseline="middle">&#969;</text>')
    plan_parts.append(f'<text x="{_f(mid_u)}" y="{_f(mid_v + 15)}" fill="{TEXT_MUTED}" '
                      f'font-size="10.5" text-anchor="middle">wheel turns this way</text>')

    def plan_edge(theta_edge, radius, beta_deg, colour, name, ray_px, label_gap):
        """Circle tangent, blade tangent, and beta between them -- at true size."""
        beta = math.radians(beta_deg)
        t_hat = (-math.sin(theta_edge), math.cos(theta_edge))
        r_hat = (math.cos(theta_edge), math.sin(theta_edge))
        # tan(beta) = dr / (r dtheta), so the camberline tangent carries cos(beta)
        # along t_hat and sin(beta) along r_hat: the angle to t_hat is beta.
        b_hat = (t_hat[0] * math.cos(beta) + r_hat[0] * math.sin(beta),
                 t_hat[1] * math.cos(beta) + r_hat[1] * math.sin(beta))
        world = ray_px / plan_scale

        def at(vec, length):
            u, v = plan(radius * math.cos(theta_edge) + vec[0] * length,
                        radius * math.sin(theta_edge) + vec[1] * length)
            return float(u), float(v)

        here = at((0.0, 0.0), 0.0)
        back = at(t_hat, -world * 0.40)
        # The two rays are only beta apart, so their end labels would collide if
        # both stopped at the same radius. Run the circle tangent further out.
        fwd = at(t_hat, world * 1.62)
        tip_blade = at(b_hat, world)

        out = [
            f'<line x1="{_f(back[0])}" y1="{_f(back[1])}" x2="{_f(fwd[0])}" y2="{_f(fwd[1])}" '
            f'stroke="{TEXT_MUTED}" stroke-width="1.5" stroke-dasharray="6,4"/>',
            f'<line x1="{_f(here[0])}" y1="{_f(here[1])}" x2="{_f(tip_blade[0])}" '
            f'y2="{_f(tip_blade[1])}" stroke="{colour}" stroke-width="3"/>',
        ]
        start = math.degrees(math.atan2(fwd[1] - here[1], fwd[0] - here[0]))
        end = math.degrees(math.atan2(tip_blade[1] - here[1], tip_blade[0] - here[0]))
        out.append(_angle_mark(here[0], here[1], start, end, colour,
                               f"{name} = {beta_deg:.0f}&#176;", radius=34.0,
                               label_gap=label_gap, ray_len=0.0))
        out.append(f'<circle cx="{_f(here[0])}" cy="{_f(here[1])}" r="4" fill="{colour}"/>')
        return out, fwd, tip_blade

    blade0 = geom["blades"][annotated]
    tip_marks, tip_tan, tip_blade_end = plan_edge(
        float(blade0["theta"][0, -1]), r2, beta2_deg, SHEAR, "&#946;&#8322;", 74.0, 24.0)
    eye_marks, eye_tan, eye_blade_end = plan_edge(
        float(blade0["theta"][0, 0]), r1, beta1_deg, PRESSURE, "&#946;&#8321;", 58.0, 20.0)
    plan_parts.extend(tip_marks)
    plan_parts.extend(eye_marks)
    plan_parts.append(f'<text x="{_f(tip_tan[0] + 6)}" y="{_f(tip_tan[1] + 4)}" '
                      f'fill="{TEXT_MUTED}" font-size="10.5">tangent to the tip circle,</text>')
    plan_parts.append(f'<text x="{_f(tip_tan[0] + 6)}" y="{_f(tip_tan[1] + 17)}" '
                      f'fill="{TEXT_MUTED}" font-size="10.5">against the motion</text>')

    # The blade speed itself, drawn at the tip. beta_2 is measured from the
    # tangential direction OPPOSING U_2, which is the same reference the
    # true-shape triangle uses -- showing U_2 here is what makes that visible
    # instead of merely stated.
    theta_t = float(blade0["theta"][0, -1])
    t_hat_tip = (-math.sin(theta_t), math.cos(theta_t))
    u_world = 62.0 / plan_scale
    ux0, uy0 = plan(r2 * math.cos(theta_t), r2 * math.sin(theta_t))
    ux1, uy1 = plan(r2 * math.cos(theta_t) - t_hat_tip[0] * u_world,
                    r2 * math.sin(theta_t) - t_hat_tip[1] * u_world)
    plan_parts.append(f'<line x1="{_f(ux0)}" y1="{_f(uy0)}" x2="{_f(ux1)}" y2="{_f(uy1)}" '
                      f'stroke="{WARNING}" stroke-width="3" marker-end="url(#imp-orange)"/>')
    plan_parts.append(f'<text x="{_f(ux1 - 6)}" y="{_f(uy1 + 14)}" fill="{WARNING}" '
                      f'font-size="12" font-weight="700" text-anchor="end">U&#8322;</text>')
    plan_parts.append(f'<text x="{_f(ux1 - 6)}" y="{_f(uy1 + 27)}" fill="{WARNING}" '
                      f'font-size="10.5" text-anchor="end">blade motion</text>')
    plan_parts.append(f'<text x="{_f(tip_blade_end[0] + 8)}" y="{_f(tip_blade_end[1] + 14)}" '
                      f'fill="{SHEAR}" font-size="10.5">tangent to the blade</text>')
    plan_parts.append(f'<text x="{_f(eye_blade_end[0] - 6)}" y="{_f(eye_blade_end[1] - 8)}" '
                      f'fill="{PRESSURE}" font-size="10.5" text-anchor="end">blade at the eye</text>')

    legend_rows = [
        (SHEAR, f"&#946;&#8322; = {beta2_deg:.0f}&#176; at the tip &#183; between the tangent to the tip circle and the tangent to the blade"),
        (PRESSURE, f"&#946;&#8321; = {beta1_deg:.0f}&#176; at the eye &#183; the same construction at the inlet, set for shockless entry"),
    ]
    legend = []
    for index, (colour, text) in enumerate(legend_rows):
        y = 434 + index * 22
        legend.append(f'<rect x="34" y="{y - 9}" width="18" height="4" rx="2" fill="{colour}"/>')
        legend.append(f'<text x="60" y="{y}" fill="{TEXT_MUTED}" font-size="11.5">{text}</text>')

    return f"""
    <svg viewBox="0 0 {width} {height}" width="100%" height="{height}"
         xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_marker_defs()}
        <text x="24" y="28" fill="{ACCENT}" font-size="15" font-weight="bold">Blade angles on the wheel &#183; where &#946;&#8321; and &#946;&#8322; actually live</text>
        <text x="24" y="48" fill="{TEXT_DIM}" font-size="12">{n_blades} blades &#183; r&#8321; = {r1 * 1000:.0f} mm, r&#8322; = {r2 * 1000:.0f} mm &#183; &#946;&#8321; = {beta1_deg:.0f}&#176;, &#946;&#8322; = {beta2_deg:.0f}&#176; &#183; blade wraps {geom['wrap_angle_deg']:.0f}&#176; around the shaft</text>
        <text x="34" y="78" fill="{TEXT_MUTED}" font-size="12.5" font-weight="600">How it sits in space</text>
        <text x="34" y="96" fill="{TEXT_DIM}" font-size="11">axonometric &#183; angles foreshortened here</text>
        <text x="472" y="78" fill="{TEXT_MUTED}" font-size="12.5" font-weight="600">Plan view, looking down the shaft</text>
        <text x="472" y="96" fill="{TEXT_DIM}" font-size="11">the r&#8211;&#952; plane is undistorted &#183; angles at TRUE size</text>
        <line x1="452" y1="66" x2="452" y2="360" stroke="{BORDER}" stroke-width="1"/>
        {"".join(parts)}
        {"".join(plan_parts)}
        <line x1="24" y1="372" x2="{width - 24}" y2="372" stroke="{BORDER}" stroke-width="1"/>
        <text x="34" y="392" fill="{TEXT}" font-size="12.5" font-weight="600">A blade angle is pure geometry: two tangents at one point on the wheel</text><text x="34" y="410" fill="{TEXT_DIM}" font-size="11.5">The blades trail backwards against the rotation &#8212; that is what &#8220;backswept&#8221; means, and it is why &#946; is measured from the tangent opposing U&#8322;.</text>
        {"".join(legend)}
        <text x="24" y="{height - 30}" fill="{TEXT_DIM}" font-size="11.5">Left: axonometric projection of the computed blade surface, axial scale exaggerated {z_exaggeration:.1f}&#215; so the passage is visible. It shows the shape, not the angles.</text>
        <text x="24" y="{height - 12}" fill="{TEXT_DIM}" font-size="11.5">The velocity triangle is a separate matter and is drawn below in true shape, where U&#8322;, W&#8322; and C&#8322; close head to tail and &#945;&#8322; can be measured.</text>
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
            f'genuinely is this flat, and &#945;&#8322; genuinely is this shallow.</text>'
            f'<text x="24" y="100" fill="{WARNING}" font-size="11.5">'
            f'The discharge is almost purely tangential &#8212; which is exactly what makes '
            f'the volute hard to design.</text>'
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
