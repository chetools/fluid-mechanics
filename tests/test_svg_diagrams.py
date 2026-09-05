"""Unit tests verifying textbook SVG diagram generators."""

import xml.etree.ElementTree as ET
from src.svg_diagrams import (
    diagram_energy_budget,
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
    diagram_blasius_scaling,
    diagram_blasius_similarity,
    diagram_canal_section,
    diagram_canal_uniform_flow,
    diagram_asu_flowsheet,
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
        diagram_blasius_scaling(),
        diagram_blasius_similarity(),
        diagram_canal_section(),
        diagram_canal_uniform_flow(),
        diagram_asu_flowsheet(),
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
    svg_diagrams.render_svg(diagram_energy_budget())
    assert len(images) == 1
    assert ET.fromstring(images[0]).tag == "{http://www.w3.org/2000/svg}svg"


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
