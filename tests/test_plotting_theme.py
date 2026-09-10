"""Every figure must build, and every axis must be themed.

`apply_plotly_theme` used to style axes with `update_layout(xaxis=..., yaxis=...)`,
which only reaches the first axis pair. Nine figures use make_subplots, so their
second and third panels silently rendered with Plotly's light defaults — a white
grid and near-black tick labels on the dark #1e293b surface. These tests pin the
template-based fix.
"""

import numpy as np
import plotly.graph_objects as go
import pytest
from plotly.subplots import make_subplots

from src import plotting
from src.theme import GRID, SURFACE, TEXT_MUTED, apply_plotly_theme
from src.physics.boundary_layer import (
    blasius_plate,
    blasius_similarity_profile,
    cylinder_outer_flow_and_separation,
)
from src.physics.euler import cylinder_potential_flow, venturi_profile
from src.physics.exact_solutions import (
    couette_poiseuille_channel,
    hagen_poiseuille_pipe,
    stokes_first_problem,
)
from src.physics.impeller import head_flow_curve, velocity_triangles
from src.physics.gas_dynamics import relief_capacity_curve
from src.physics.non_newtonian import (
    flow_curve,
    power_law_pipe,
    herschel_bulkley_pipe,
    maxwell_startup,
    thixotropic_step,
)
from src.physics.numerical_solver import run_lid_driven_cavity
from src.physics.stress_tensor import compute_cauchy_stress_2d, deform_fluid_element_2d
from src.physics.open_channel import MANNING_N, channel_state, rating_curve
from src.physics.transport_analogy import (
    pohlhausen_theta_gradient,
    sweep_reynolds,
    transport_correlation,
)
from src.physics.turbulence import law_of_the_wall, velocity_profile_comparison


def _figures():
    """One instance of every figure the app renders, with real physics inputs."""
    sim = blasius_similarity_profile()
    return {
        "venturi": plotting.plot_venturi(venturi_profile()),
        "cylinder": plotting.plot_cylinder_potential_flow(cylinder_potential_flow()),
        "channel": plotting.plot_exact_channel_flow(couette_poiseuille_channel()),
        "stokes": plotting.plot_stokes_first_problem(stokes_first_problem()),
        "hagen": plotting.plot_hagen_poiseuille(hagen_poiseuille_pipe()),
        "cavity": plotting.plot_cavity_cfd(
            run_lid_driven_cavity(nx=11, ny=11, n_steps=5, poisson_iters=5)
        ),
        "moody": plotting.plot_moody_chart(re_operating=5e4, eps_d_operating=1e-3, f_operating=0.022),
        "profiles": plotting.plot_laminar_turbulent_profiles(velocity_profile_comparison()),
        "profile_limits": plotting.plot_pipe_profile_limits(velocity_profile_comparison()),
        "wall": plotting.plot_law_of_the_wall(law_of_the_wall()),
        "blasius": plotting.plot_blasius_profile(sim, blasius_plate(x=0.5, u_inf=1.0, nu=1e-6)),
        "separation": plotting.plot_cylinder_separation(cylinder_outer_flow_and_separation()),
        "straws": plotting.plot_straw_bundle([1, 4, 16], 1000.0, [500.0, 2000.0, 8000.0], [900.0, 450.0, 110.0]),
        "impeller": plotting.plot_impeller_head_curve(
            head_flow_curve(2900, 0.045, 0.150, 30.0, 25.0, 0.030, 0.012, 7, q_max=0.06),
            operating_q=0.030,
            operating_h=velocity_triangles(rpm=2900, flow_rate=0.030)["head_euler_m"],
        ),
        "canal": plotting.plot_open_channel_rating(
            rating_curve(3.0, 1.5, MANNING_N["Clean earth canal, straight"], 0.0008, max_depth=3.0),
            channel_state(8.0, 3.0, 1.5, MANNING_N["Clean earth canal, straight"], 0.0008, bank_depth=2.5),
        ),
        "thermal": plotting.plot_thermal_boundary_layers(
            [pohlhausen_theta_gradient(pr) for pr in (0.7, 1.0, 7.0)]
        ),
        "relief": plotting.plot_relief_capacity(
            relief_capacity_curve(12e5, 333.15), operating_ratio=0.084
        ),
        "transport": plotting.plot_transport_correlations(
            [sweep_reynolds("Sphere (Ranz-Marshall)", 7.0),
             sweep_reynolds("Flat plate, laminar (local)", 7.0)],
            transport_correlation("Sphere (Ranz-Marshall)", 100.0, 7.0),
        ),
        "power_law": plotting.plot_power_law_pipe(
            power_law_pipe(radius=0.025, dp_dz=-40.0, K=0.1, n=0.6),
            hagen_poiseuille_pipe(radius=0.025, dp_dx=-40.0, mu=1e-3),
        ),
        "flow_curves": plotting.plot_flow_curves([
            flow_curve("Newtonian", np.logspace(-2, 3, 50), mu=0.05),
            flow_curve("Bingham plastic", np.logspace(-2, 3, 50), tau_y=5.0, mu_p=0.05),
        ]),
        "yield_pipe": plotting.plot_yield_stress_pipe(
            herschel_bulkley_pipe(radius=0.025, dp_dz=-40.0, K=0.02, n=0.7, tau_y=0.2),
            hagen_poiseuille_pipe(radius=0.025, dp_dx=-40.0, mu=1e-3),
        ),
        "thixotropy": plotting.plot_thixotropy(thixotropic_step()),
        "viscoelastic": plotting.plot_viscoelastic_startup(maxwell_startup()),
    }


FIGURE_NAMES = (
    "venturi", "cylinder", "channel", "stokes", "hagen", "cavity",
    "moody", "profiles", "profile_limits", "wall", "blasius", "separation", "straws",
    "impeller", "canal", "thermal", "transport", "relief",
    "power_law", "flow_curves", "yield_pipe", "thixotropy", "viscoelastic",
)


@pytest.fixture(scope="module")
def figures():
    built = _figures()
    assert set(built) == set(FIGURE_NAMES), "update FIGURE_NAMES when adding a figure"
    return built


@pytest.mark.parametrize("name", FIGURE_NAMES)
def test_every_figure_builds_with_data(name, figures):
    figure = figures[name]
    assert isinstance(figure, go.Figure)
    assert len(figure.data) > 0, f"{name} rendered no traces"
    assert figure.layout.title.text is not None, (
        "Plotly 7 shows an 'undefined' title in this app when the text is unset"
    )


@pytest.mark.parametrize("name", FIGURE_NAMES)
def test_figures_carry_the_dark_template(name, figures):
    layout = figures[name].layout.template.layout
    assert layout.paper_bgcolor == SURFACE
    assert layout.xaxis.gridcolor == GRID
    assert layout.yaxis.gridcolor == GRID
    assert layout.yaxis.color == TEXT_MUTED


def test_template_styles_subplot_axes_not_just_the_first_pair():
    """The regression itself: a themed subplot figure must not leave axis 2 light."""
    figure = make_subplots(rows=1, cols=2)
    figure.add_trace(go.Scatter(x=[0, 1], y=[0, 1]), row=1, col=1)
    figure.add_trace(go.Scatter(x=[0, 1], y=[1, 0]), row=1, col=2)
    apply_plotly_theme(figure)

    template = figure.layout.template.layout
    # Plotly applies template.layout.xaxis to xaxis, xaxis2, xaxis3, ... so a
    # single template entry covers axes that update_layout(xaxis=...) misses.
    assert template.xaxis.gridcolor == GRID
    for axis in ("xaxis", "xaxis2", "yaxis", "yaxis2"):
        assert figure.layout[axis].gridcolor is None, (
            f"{axis} hard-codes a grid colour, which would override the template"
        )


def test_plotting_module_does_not_hard_code_axis_colours():
    """Per-figure colour overrides are how the subplot bug came back last time."""
    source = (plotting.__file__)
    with open(source, encoding="utf-8") as handle:
        text = handle.read()
    assert "gridcolor" not in text, (
        "set grid colours in the theme template, not in individual plot functions"
    )


def test_theme_survives_a_second_application():
    figure = go.Figure(go.Scatter(x=[0, 1], y=[0, 1]))
    apply_plotly_theme(figure)
    figure.update_layout(title="kept")
    apply_plotly_theme(figure)
    assert figure.layout.title.text == "kept"
    assert figure.layout.template.layout.paper_bgcolor == SURFACE


def test_mohr_plot_resolves_small_shear_and_keeps_equal_axis_scales():
    fig = plotting.plot_fluid_element_deformation(
        deform_fluid_element_2d(0, 1, 0, 0),
        compute_cauchy_stress_2d(0, 1, 0, 0, mu=.001, p=101300),
    )
    circle = next(t for t in fig.data if t.name == "Mohr's Circle")
    assert max(circle.x) == pytest.approx(.001)
    assert any('0.001 Pa' in t.name for t in fig.data if t.showlegend is not False)
    assert fig.layout.yaxis2.scaleanchor == 'x2'
    assert fig.layout.yaxis2.scaleratio == 1
