"""Unit tests verifying textbook SVG diagram generators."""

import xml.etree.ElementTree as ET
from src.svg_diagrams import (
    diagram_energy_budget,
    diagram_injection_work,
    diagram_model_selection,
    diagram_continuity_streamtube,
    diagram_1d_euler_element,
    diagram_eulerian_vs_lagrangian,
    diagram_streamline_geometry,
    diagram_stress_tensor_cube,
    diagram_kinematic_decomposition,
    diagram_chorin_projection,
    diagram_reynolds_experiment,
    diagram_laminar_vs_turbulent_profiles,
    diagram_law_of_the_wall,
    diagram_null_space_matrix,
    diagram_blasius_plate,
    diagram_npsh,
    diagram_power_law,
    diagram_newtonian_origin,
    diagram_actuator_disc,
    diagram_microstructure_gallery,
    diagram_viscoelastic_effects,
    diagram_deborah_timescales,
    diagram_blasius_scaling,
    diagram_blasius_similarity,
    diagram_canal_section,
    diagram_canal_uniform_flow,
    diagram_asu_flowsheet,
    diagram_relief_valve,
    diagram_transport_analogy,
    diagram_transport_geometries,
    diagram_sphere_forces,
    diagram_sphere_separation,
    diagram_nozzle_information,
    diagram_momentum_control_volume,
    diagram_hydraulic_jump,
    diagram_weir_and_gate,
    diagram_rocket_control_volume,
    diagram_nozzle_expansion_regimes,
    diagram_rocket_pressure_thrust,
    diagram_bell_contour_construction,
    diagram_moc_wave_logic,
    clean_svg
)
from src.svg_impeller import (
    diagram_blade_angles,
    diagram_impeller_meridional,
    diagram_outlet_triangle_true_shape,
)

def test_svg_diagrams_render_valid_xml():
    """Verify all diagram functions return well-formed SVG strings."""
    diagrams = [
        diagram_energy_budget(),
        diagram_injection_work(),
        diagram_model_selection(),
        diagram_continuity_streamtube(),
        diagram_1d_euler_element(),
        diagram_eulerian_vs_lagrangian(),
        diagram_streamline_geometry(),
        diagram_stress_tensor_cube(),
        diagram_kinematic_decomposition(),
        diagram_chorin_projection(),
        diagram_reynolds_experiment(),
        diagram_laminar_vs_turbulent_profiles(),
        diagram_law_of_the_wall(),
        diagram_null_space_matrix(),
        diagram_blasius_plate(),
        diagram_npsh(),
        diagram_power_law(),
        diagram_newtonian_origin(),
        diagram_actuator_disc(),
        diagram_microstructure_gallery(),
        diagram_viscoelastic_effects(),
        diagram_deborah_timescales(),
        diagram_blasius_scaling(),
        diagram_blasius_similarity(),
        diagram_canal_section(),
        diagram_canal_uniform_flow(),
        diagram_asu_flowsheet(),
        diagram_relief_valve(),
        diagram_transport_analogy(),
        diagram_transport_geometries(),
        diagram_sphere_forces(),
        diagram_sphere_separation(),
        diagram_nozzle_information(),
        diagram_momentum_control_volume(),
        diagram_hydraulic_jump(),
        diagram_weir_and_gate(),
        diagram_rocket_control_volume(),
        diagram_nozzle_expansion_regimes(),
        diagram_rocket_pressure_thrust(),
        diagram_bell_contour_construction(),
        diagram_moc_wave_logic(),
        # Generated from the computed geometry, including non-default cases: a
        # near-radial blade and a two-blade rotor exercise the projection and
        # the painter's ordering differently from the defaults.
        diagram_blade_angles(),
        diagram_blade_angles(beta2_deg=85.0, n_blades=2),
        diagram_impeller_meridional(),
        diagram_outlet_triangle_true_shape(),
        diagram_outlet_triangle_true_shape(beta2_deg=80.0, u2=120.0, cm2=30.0, sigma=0.92),
    ]
    
    for svg_str in diagrams:
        assert isinstance(svg_str, str)
        assert "<svg" in svg_str
        assert "</svg>" in svg_str
        assert "viewBox" in svg_str
        root = ET.fromstring(svg_str)
        assert root.tag == "{http://www.w3.org/2000/svg}svg"
        assert not root.findall(".//{http://www.w3.org/2000/svg}b"), "Use SVG tspan, not HTML b, for emphasis"
        
        cleaned = clean_svg(svg_str)
        assert ET.fromstring(cleaned).tag == "{http://www.w3.org/2000/svg}svg"
        assert "\n" not in cleaned
        assert cleaned.startswith("<svg")
        assert cleaned.endswith("</svg>")


def test_renderer_uses_native_image_api(monkeypatch):
    """HTML sanitization strips SVG, so artwork must go through st.image."""
    from contextlib import nullcontext
    from src import svg_diagrams

    images = []
    monkeypatch.setattr(svg_diagrams.st, "container", lambda **kwargs: nullcontext())
    monkeypatch.setattr(svg_diagrams.st, "caption", lambda *args: None)
    monkeypatch.setattr(svg_diagrams.st, "image", lambda image, **kwargs: images.append(image))
    for generator in (diagram_energy_budget, diagram_newtonian_origin, diagram_actuator_disc):
        svg_diagrams.render_svg(generator())
    assert len(images) == 3
    for image in images:
        # Validate the final image payload too: renderer-added attributes can
        # duplicate attributes in a valid source SVG and make browsers reject it.
        root = ET.fromstring(image)
        assert root.tag == "{http://www.w3.org/2000/svg}svg"
        assert root.attrib["role"] == "img"


def test_new_physical_diagrams_state_their_conventions_and_limits():
    def text(svg):
        return " ".join(ET.fromstring(svg).itertext())

    sphere = text(diagram_sphere_forces())
    assert "θ is measured from +U" in sphere
    assert "weight = buoyancy + drag" in sphere
    assert "arrow lengths are schematic" in sphere
    separation = text(diagram_sphere_separation())
    assert "earlier separation" in separation and "later separation" in separation
    assert "Schematic only" in separation
    nozzle = text(diagram_nozzle_information())
    assert "u − a < 0" in nozzle and "u − a = 0" in nozzle
    assert "velocities in the laboratory frame" in nozzle
    assert "the nozzle unchokes" in nozzle
    inject = text(diagram_injection_work())
    assert "Work on the system is positive" in inject
    assert "F on system" in inject
    assert "inward" in inject
    assert "expansion" in inject
    assert "−p" in inject or "-p" in inject
    assert "specific volume" in inject
    assert "velocity" in inject
    assert "True side view" in inject


def test_rocket_nozzle_diagrams_state_the_claims_the_lesson_relies_on():
    """Each of these figures carries a claim the prose leans on; pin the claim.

    A diagram that quietly loses its labels still renders, still parses as XML,
    and still passes every other test in this file while teaching nothing.
    """
    def text(svg):
        return " ".join(ET.fromstring(svg).itertext())

    regimes = text(diagram_nozzle_expansion_regimes())
    # All four regimes must be named, and named by the pressure comparison.
    for label in ("Under-expanded", "Matched", "Over-expanded, still attached",
                  "Over-expanded to separation"):
        assert label in regimes
    assert "the exit pressure never changes, only what meets it" in regimes
    assert "one place in the sky" in regimes
    assert "Side loads" in regimes

    thrust = text(diagram_rocket_pressure_thrust())
    assert "not a push against the air" in thrust
    assert "pressure integral over the inside of the engine" in thrust
    assert "sea level" in thrust and "vacuum" in thrust
    assert "the same force, counted two ways" in thrust.lower()

    bell = text(diagram_bell_contour_construction())
    # The construction is five decisions; losing one silently breaks the recipe.
    for fragment in ("Fix the expansion ratio", "Fix the length", "Round the throat",
                     "Sweep to", "Join N to E"):
        assert fragment in bell
    assert "0.382 r" in bell and "1.5 r" in bell
    assert "meridional section, not a projection" in bell, (
        "angles may only be marked where they are true"
    )

    moc = text(diagram_moc_wave_logic())
    assert "corner sets the total turn" in moc
    assert "axis reflects" in moc
    assert "wall cancels" in moc
    assert "planar minimum-length nozzle" in moc, "the 2D restriction must be visible"


def test_rocket_nozzle_diagram_text_stays_inside_its_viewbox():
    """A label that runs past the viewBox is clipped in half, silently.

    This caught a real one: the three method-of-characteristics formulas were
    placed at x = 806 in a 1000-unit frame and rendered as "K+ = -" with the
    rest cut off. Nothing else notices -- the XML is valid, the currency scan is
    clean, and the figure still draws.

    The width estimate is deliberately crude (a per-character factor, larger for
    the monospace stack), so it is applied only to the figures added with it
    rather than repo-wide, where several older diagrams sit close enough to the
    edge that this approximation would flag them without their being wrong.
    Anchored text is skipped because its x is not its left edge.
    """
    figures = {
        "nozzle_expansion_regimes": diagram_nozzle_expansion_regimes(),
        "rocket_pressure_thrust": diagram_rocket_pressure_thrust(),
        "bell_contour_construction": diagram_bell_contour_construction(),
        "moc_wave_logic": diagram_moc_wave_logic(),
    }
    problems = []
    for name, svg in figures.items():
        root = ET.fromstring(svg)
        width = float(root.get("viewBox").split()[2])
        for node in root.iter("{http://www.w3.org/2000/svg}text"):
            if node.get("x") is None or node.get("text-anchor") in ("middle", "end"):
                continue
            size = float(node.get("font-size", 12))
            monospace = "monospace" in (node.get("font-family") or "")
            content = "".join(node.itertext())
            estimated_end = (
                float(node.get("x")) + len(content) * size * (0.62 if monospace else 0.52)
            )
            if estimated_end > width:
                problems.append(
                    f"{name}: {content[:52]!r} ends near {estimated_end:.0f} "
                    f"in a {width:.0f}-unit frame"
                )
    assert not problems, "text clipped at the right edge:\n" + "\n".join(problems)


def test_kinematic_spin_label_matches_its_component_formula():
    svg = diagram_kinematic_decomposition()
    assert "Anti-symmetric spin Ω_yx" in svg
    assert "½(∂v/∂x - ∂u/∂y)" in svg


def test_generated_impeller_diagram_tracks_its_geometry():
    """The drawing must move when the geometry does, or it is decoration."""
    shallow = diagram_blade_angles(beta2_deg=20.0)
    steep = diagram_blade_angles(beta2_deg=70.0)
    assert shallow != steep
    assert "20&#176;" in shallow and "70&#176;" in steep
    # A shallower blade wraps further around the shaft; the caption reports it.
    import re
    def wrap(svg):
        return float(re.search(r"blade wraps (\d+)&#176; around the shaft", svg).group(1))
    assert wrap(shallow) > wrap(steep)


def test_no_unresolved_format_placeholders_in_diagrams():
    """A doubled brace in an f-string leaks `{name}` into the rendered SVG."""
    import re
    from src import svg_diagrams, svg_impeller

    for module in (svg_diagrams, svg_impeller):
        for name in dir(module):
            if not name.startswith("diagram_"):
                continue
            svg = getattr(module, name)()
            leaked = re.findall(r"\{[a-z_][a-z0-9_]*\}", svg)
            assert not leaked, f"{name} leaked placeholders {leaked}"


def test_no_diagram_contains_a_currency_or_stray_symbol():
    """A numeric entity one off from a subscript letter is a currency sign.

    Unicode provides subscripts for digits and a few lowercase letters only --
    there is none for `w`, and none for capitals. Guessing an entity near the
    subscript block lands in Currency Symbols: U+20A2, one past the last
    subscript letter, is the CRUZEIRO SIGN, which is exactly what a wall
    subscript turned into once already. No diagram in a fluid-mechanics course
    has any business containing a currency symbol, so this is a cheap and total
    guard on that whole class of mistake.
    """
    import html
    import unicodedata

    from src import svg_diagrams, svg_impeller

    offenders = []
    for module in (svg_diagrams, svg_impeller):
        for name in dir(module):
            if not name.startswith("diagram_"):
                continue
            text = html.unescape(getattr(module, name)())
            for char in sorted(set(text)):
                point = ord(char)
                # Currency Symbols block, plus the letterlike/arrow ranges that
                # neighbour the subscript block and read as noise in a figure.
                if 0x20A0 <= point <= 0x20BF:
                    offenders.append(
                        f"{name}: U+{point:04X} {unicodedata.name(char, '?')}"
                    )
    assert not offenders, (
        "Diagrams contain currency symbols, which almost certainly means a "
        "numeric entity was used for a subscript that Unicode does not have. "
        "Use svg_diagrams._sub() instead:\n" + "\n".join(sorted(set(offenders)))
    )
