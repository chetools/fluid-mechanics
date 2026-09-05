"""Unit tests verifying textbook SVG diagram generators."""

import pytest
from src.svg_diagrams import (
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
    clean_svg
)

def test_svg_diagrams_render_valid_xml():
    """Verify all diagram functions return well-formed SVG strings."""
    diagrams = [
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
    ]
    
    for svg_str in diagrams:
        assert isinstance(svg_str, str)
        assert "<svg" in svg_str
        assert "</svg>" in svg_str
        assert "viewBox" in svg_str
        
        cleaned = clean_svg(svg_str)
        assert "\n" not in cleaned
        assert cleaned.startswith("<svg")
        assert cleaned.endswith("</svg>")
