"""Plotly interactive visualization suite for Fluid Mechanics.

Creates consistent dark-themed figures styled with src/theme.py.
"""

from typing import Dict, List
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.theme import (
    apply_plotly_theme, SURFACE, SURFACE_RAISED, BORDER_STRONG,
    TEXT, TEXT_MUTED, TEXT_DIM, ACCENT, PRESSURE, SHEAR, VORTICITY, SUCCESS, WARNING, INERTIA, VISCOUS, SERIES, rgba
)
from src.units import unit_label, is_nondimensional

def plot_venturi(res: Dict[str, np.ndarray]) -> go.Figure:
    """Create 3-panel Venturi nozzle visualization: Geometry, Velocity, and Pressure."""
    nondim = is_nondimensional()
    x = res["x"]
    x_span = float(x[-1] - x[0]) if len(x) > 1 else 1.0
    x_plot = x / x_span if nondim else x
    x_lbl = "Normalized Position x/L [-]" if nondim else f"Position x [{unit_label('length')}]"
    
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=(
            "1. Venturi Tube Geometry & Cross-Sectional Area A(x)",
            "2. Fluid Velocity u(x) & Material Acceleration u·(du/dx)",
            "3. Bernoulli terms: static p, kinetic ½ρu², invariant H"
        )
    )
    
    # 1. Geometry: upper and lower wall contours
    d_half = 0.5 * res["diameter"]
    if nondim:
        d_half_plot = d_half / d_half[0]
        y_geom_lbl = "r/R₀ [-]"
    else:
        d_half_plot = d_half
        y_geom_lbl = f"Radius [{unit_label('length')}]"
        
    fig.add_trace(
        go.Scatter(
            x=x_plot, y=d_half_plot,
            mode="lines", line=dict(color=ACCENT, width=2.5),
            name="Upper Wall",
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=x_plot, y=-d_half_plot,
            mode="lines", line=dict(color=ACCENT, width=2.5),
            fill="tonexty", fillcolor=rgba(ACCENT, 0.1),
            name="Lower Wall",
        ),
        row=1, col=1
    )
    # Throat marker
    throat_idx = np.argmin(d_half_plot)
    fig.add_trace(
        go.Scatter(
            x=[x_plot[throat_idx], x_plot[throat_idx]],
            y=[-d_half_plot[throat_idx], d_half_plot[throat_idx]],
            mode="lines+markers",
            line=dict(color=PRESSURE, width=2, dash="dash"),
            marker=dict(size=8, color=PRESSURE),
            name="Throat Minimum",
        ),
        row=1, col=1
    )
    
    # 2. Velocity and Acceleration
    u_inlet = res["velocity"][0] if res["velocity"][0] != 0 else 1.0
    u_plot = res["velocity"] / u_inlet if nondim else res["velocity"]
    u_unit = "u/u_inlet [-]" if nondim else unit_label("velocity")
    
    fig.add_trace(
        go.Scatter(
            x=x_plot, y=u_plot,
            mode="lines", line=dict(color=SUCCESS, width=2.5),
            name=f"Velocity u ({u_unit})",
        ),
        row=2, col=1
    )
    a_plot = res["convective_acc"] * x_span / (u_inlet**2) if nondim else res["convective_acc"]
    a_name = "u·(du/dx) · L/u² [-]" if nondim else "u·(du/dx) [m/s²]"
    fig.add_trace(
        go.Scatter(
            x=x_plot, y=a_plot,
            mode="lines", line=dict(color=INERTIA, width=1.5, dash="dot"),
            name=a_name,
        ),
        row=2, col=1
    )
    
    # 3. Static, kinetic, and total Bernoulli terms (horizontal lab: z = 0)
    rho = float(res.get("rho", 1000.0))
    kinetic = res.get("kinetic", 0.5 * rho * res["velocity"]**2)
    q_ref = 0.5 * rho * (u_inlet**2)
    if q_ref == 0:
        q_ref = 1.0
    if nondim:
        p_ref = res["pressure"][0]
        p_plot = (res["pressure"] - p_ref) / q_ref
        k_plot = (kinetic - kinetic[0]) / q_ref
        p_tot_plot = (res["total_pressure"] - p_ref) / q_ref
        p_unit = "(· − p₀)/q₀ [-]"
    else:
        p_plot = res["pressure"] / 1000.0
        k_plot = kinetic / 1000.0
        p_tot_plot = res["total_pressure"] / 1000.0
        p_unit = "kPa"
        
    fig.add_trace(
        go.Scatter(
            x=x_plot, y=p_plot,
            mode="lines", line=dict(color=PRESSURE, width=2.5),
            name=f"Static p ({p_unit})",
        ),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=x_plot, y=k_plot,
            mode="lines", line=dict(color=ACCENT, width=2.0, dash="dash"),
            name="Kinetic ½ρu²",
        ),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=x_plot, y=p_tot_plot,
            mode="lines", line=dict(color=TEXT_MUTED, width=1.5, dash="dash"),
            name="H = p + ½ρu² (flat if inviscid)",
        ),
        row=3, col=1
    )
    
    fig.update_xaxes(title_text=x_lbl, row=3, col=1)
    fig.update_yaxes(title_text=y_geom_lbl, row=1, col=1)
    fig.update_yaxes(title_text=u_unit, row=2, col=1)
    fig.update_yaxes(title_text=p_unit, row=3, col=1)
    
    fig.update_layout(height=650, showlegend=True)
    return apply_plotly_theme(fig)

def plot_cylinder_potential_flow(res: Dict[str, np.ndarray]) -> go.Figure:
    """Create 2-panel figure: 2D Streamlines + Pressure Contour, and Surface Cp(theta)."""
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.6, 0.4],
        subplot_titles=(
            "2D Inviscid Streamlines & Pressure Field (Euler)",
            "Surface Pressure Coefficient Cp(θ) — d'Alembert Paradox"
        ),
        horizontal_spacing=0.1
    )
    
    # Left: 2D contour of Cp with streamfunction isolines, scaled by R
    R = float(res.get("radius", 1.0)) or 1.0
    x = res["x"] / R
    y = res["y"] / R
    Cp = res["Cp"]
    Psi = res["Psi"]
    
    # Pressure coefficient background heatmap
    fig.add_trace(
        go.Contour(
            x=x, y=y, z=Cp,
            colorscale="RdBu_r",
            contours=dict(start=-3.0, end=1.0, size=0.25, showlines=False),
            colorbar=dict(title="Cp [-]", x=0.55, len=0.8),
            showscale=True,
            name="Cp Field"
        ),
        row=1, col=1
    )
    
    # Streamlines overlay
    fig.add_trace(
        go.Contour(
            x=x, y=y, z=Psi,
            colorscale=[[0, rgba(TEXT, 0.6)], [1, rgba(TEXT, 0.6)]],
            contours=dict(start=-15, end=15, size=0.8, coloring="none", showlines=True),
            line=dict(width=1.2, color=TEXT),
            showscale=False,
            name="Streamlines Ψ"
        ),
        row=1, col=1
    )
    
    # Cylinder circle patch
    theta_circle = np.linspace(0, 2*np.pi, 100)
    fig.add_trace(
        go.Scatter(
            x=np.cos(theta_circle), y=np.sin(theta_circle),
            mode="lines", fill="toself",
            fillcolor=SURFACE_RAISED, line=dict(color=ACCENT, width=3),
            name="Cylinder Wall"
        ),
        row=1, col=1
    )
    
    # Right: Surface Cp(theta)
    theta_deg = np.degrees(res["theta_surf"])
    fig.add_trace(
        go.Scatter(
            x=theta_deg, y=res["cp_surf"],
            mode="lines", line=dict(color=PRESSURE, width=3),
            name="Cp(θ) = 1 - 4 sin²(θ)"
        ),
        row=1, col=2
    )
    
    # Theoretical zero drag line
    fig.add_trace(
        go.Scatter(
            x=[0, 360], y=[0, 0],
            mode="lines", line=dict(color=BORDER_STRONG, width=1.5, dash="dash"),
            name="Zero Reference"
        ),
        row=1, col=2
    )
    
    fig.update_xaxes(title_text="x/R [-]", range=[-3.05, 3.05], constrain="domain", row=1, col=1)
    fig.update_yaxes(title_text="y/R [-]", range=[-3.05, 3.05], row=1, col=1)
    fig.update_xaxes(title_text="Angle θ around Cylinder [deg]", tickvals=[0, 90, 180, 270, 360], row=1, col=2)
    fig.update_yaxes(title_text="Pressure Coefficient Cp [-]", row=1, col=2)
    
    fig.update_layout(height=520)
    return apply_plotly_theme(fig)

def plot_fluid_element_deformation(
    deform_res: Dict[str, np.ndarray],
    stress_res: Dict[str, np.ndarray]
) -> go.Figure:
    """Create side-by-side interactive deformation and Mohr's Circle visualization."""
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.55, 0.45],
        subplot_titles=(
            "Fluid Parcel Deformation (Initial vs. Deformed)",
            "Mohr's Circle of Stress (2D In-Plane)"
        ),
        horizontal_spacing=0.12
    )
    
    # 1. Parcel Deformation (Left)
    sq_init = deform_res["square_initial"]
    sq_full = deform_res["square_full"]
    sq_strain = deform_res["square_strain_only"]
    sq_rotation = deform_res["square_rot_only"]
    
    # Initial square
    fig.add_trace(
        go.Scatter(
            x=sq_init[:, 0], y=sq_init[:, 1],
            mode="lines", line=dict(color=TEXT_DIM, width=1.5, dash="dash"),
            name="Initial Parcel (t₀)"
        ),
        row=1, col=1
    )
    # Deformed parcel
    fig.add_trace(
        go.Scatter(
            x=sq_full[:, 0], y=sq_full[:, 1],
            mode="lines", fill="toself",
            fillcolor=rgba(SHEAR, 0.18),
            line=dict(color=SHEAR, width=3),
            name="Deformed Parcel (t₀ + Δt)"
        ),
        row=1, col=1
    )
    # Strain-only parcel (demonstrating pure deformation without rotation)
    fig.add_trace(
        go.Scatter(
            x=sq_strain[:, 0], y=sq_strain[:, 1],
            mode="lines", line=dict(color=SUCCESS, width=1.8, dash="dot"),
            name="D-only comparison"
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=sq_rotation[:, 0], y=sq_rotation[:, 1],
            mode="lines", line=dict(color=PRESSURE, width=1.8, dash="dashdot"),
            name="Ω-only rotation"
        ), row=1, col=1,
    )
    # Internal grid lines
    for line in deform_res["internal_lines_full"]:
        fig.add_trace(
            go.Scatter(
                x=line[:, 0], y=line[:, 1],
                mode="lines", line=dict(color=rgba(TEXT_MUTED, 0.3), width=1),
                showlegend=False
            ),
            row=1, col=1
        )
        
    # 2. Mohr's Circle (Right)
    # Plot deviations in Pa instead of burying millipascal shear beneath a
    # ~100 kPa pressure offset. The separate mean restores the total stress.
    mean_kpa = stress_res["mohr_center"] / 1000.0
    center = 0.0
    radius = stress_res["mohr_radius"]
    sig_1, sig_2 = radius, -radius
    
    th_circle = np.linspace(0, 2*np.pi, 200)
    x_circle = center + radius * np.cos(th_circle)
    y_circle = radius * np.sin(th_circle)
    
    fig.add_trace(
        go.Scatter(
            x=x_circle, y=y_circle,
            mode="lines", line=dict(color=ACCENT, width=2.5),
            name="Mohr's Circle"
        ),
        row=1, col=2
    )
    # Center dot
    fig.add_trace(
        go.Scatter(
            x=[center], y=[0],
            mode="markers", marker=dict(size=8, color=TEXT),
            name=f"Mean σ = {mean_kpa:.3f} kPa"
        ),
        row=1, col=2
    )
    # Principal stress markers
    fig.add_trace(
        go.Scatter(
            x=[sig_1, sig_2], y=[0, 0],
            mode="markers", marker=dict(size=10, color=SUCCESS, symbol="diamond"),
            name="Principal stress deviations"
        ),
        row=1, col=2
    )
    # Max shear stress marker
    fig.add_trace(
        go.Scatter(
            x=[center, center], y=[-radius, radius],
            mode="lines+markers", line=dict(color=SHEAR, width=1.5, dash="dash"),
            marker=dict(size=8, color=SHEAR),
            name=f"Max shear = {radius:.3g} Pa"
        ),
        row=1, col=2
    )
    
    fig.update_xaxes(title_text="x position [initial side lengths]", scaleanchor="y", scaleratio=1, row=1, col=1)
    fig.update_yaxes(title_text="y position", row=1, col=1)
    limit = max(1.3 * radius, 1e-3)
    fig.update_xaxes(title_text="σ − σ_mean [Pa]", range=[-limit, limit], constrain="domain", row=1, col=2)
    fig.update_yaxes(title_text="Shear τ [Pa]", range=[-limit, limit], scaleanchor="x2", scaleratio=1, row=1, col=2)
    
    fig.update_layout(height=480)
    return apply_plotly_theme(fig)

def plot_exact_channel_flow(res: Dict[str, np.ndarray]) -> go.Figure:
    """Create 2-panel plot for Couette-Poiseuille channel: Velocity Profile and Shear Stress."""
    nondim = is_nondimensional()
    y_plot = res["y_norm"] if nondim else res["y"]
    y_lbl = "Normalized Height y/h [-]" if nondim else f"Height y [{unit_label('length')}]"
    
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.55, 0.45],
        subplot_titles=(
            "Velocity Profile u(y) Decomposition",
            "Shear Stress Distribution τ(y) = μ·(du/dy)"
        ),
        horizontal_spacing=0.12
    )
    
    # Velocity Decomposition
    u_wall = float(res["u_couette"][-1]) if len(res["u_couette"]) else 0.0
    u_scale = u_wall if (nondim and abs(u_wall) > 1e-12) else (1.0 if not nondim else max(np.max(np.abs(res["u_total"])), 1e-12))
    u_tot = res["u_total"] / u_scale if nondim else res["u_total"]
    u_couette = res["u_couette"] / u_scale if nondim else res["u_couette"]
    u_pois = res["u_poiseuille"] / u_scale if nondim else res["u_poiseuille"]
    u_unit = "Velocity [m/s]" if not nondim else "u/U_wall [-]"
    
    fig.add_trace(
        go.Scatter(
            x=u_tot, y=y_plot,
            mode="lines", line=dict(color=SUCCESS, width=3),
            name="Total Velocity u(y)"
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=u_couette, y=y_plot,
            mode="lines", line=dict(color=ACCENT, width=2, dash="dash"),
            name="Couette Linear Shear"
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=u_pois, y=y_plot,
            mode="lines", line=dict(color=PRESSURE, width=2, dash="dot"),
            name="Poiseuille Parabolic"
        ),
        row=1, col=1
    )
    
    # Reversal: interior u = 0 when an adverse pressure gradient beats the moving wall
    u_dim = res["u_total"]
    interior = u_dim[1:-1]
    y_int = y_plot[1:-1]
    sign_change = np.where(np.diff(np.sign(interior)))[0]
    if len(sign_change):
        i0 = int(sign_change[0])
        fig.add_hline(
            y=float(y_int[i0]),
            line=dict(color=WARNING, width=1.5, dash="dash"),
            annotation_text="u = 0 (reversal)",
            row=1, col=1,
        )

    # Shear Stress
    tau_plot = res["tau"]
    fig.add_trace(
        go.Scatter(
            x=tau_plot, y=y_plot,
            mode="lines", line=dict(color=SHEAR, width=2.5),
            name="Shear Stress τ(y)"
        ),
        row=1, col=2
    )
    
    fig.update_xaxes(title_text=u_unit, row=1, col=1)
    fig.update_yaxes(title_text=y_lbl, row=1, col=1)
    fig.update_xaxes(title_text=f"Shear Stress [{unit_label('shear_stress')}]", row=1, col=2)
    fig.update_yaxes(title_text=y_lbl, row=1, col=2)
    
    fig.update_layout(height=450)
    return apply_plotly_theme(fig)

def plot_stokes_first_problem(res: Dict[str, np.ndarray]) -> go.Figure:
    """Create Rayleigh Problem diffusion plot showing boundary layer growth over time."""
    y = res["y"]
    fig = go.Figure()
    
    for i, t in enumerate(res["times"]):
        color = SERIES[i % len(SERIES)]
        u_prof = res["profiles"][t]
        delta = res["delta_viscous"][t]
        
        fig.add_trace(
            go.Scatter(
                x=u_prof, y=y,
                mode="lines", line=dict(color=color, width=2.5),
                name=f"t = {t:.2f} s (δ ≈ {delta*1000:.1f} mm)"
            )
        )
        fig.add_hline(
            y=delta,
            line=dict(color=color, width=1, dash="dot"),
            opacity=0.45,
        )
        
    fig.update_layout(
        title=(
            f"Stokes' First Problem: viscous penetration "
            f"δ(t) = {float(res.get('delta_coeff', 3.643)):.3f} √(ν t) (1% of U, dotted)"
        ),
        xaxis_title="Velocity u(y, t) [m/s]",
        yaxis_title="Distance from Wall y [m]",
        height=450
    )
    return apply_plotly_theme(fig)


def plot_hagen_poiseuille(res: Dict[str, np.ndarray]) -> go.Figure:
    """Round-pipe Hagen–Poiseuille profile u(r) with mean-velocity marker."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=res["u"], y=res["r_norm"],
            mode="lines", line=dict(color=SUCCESS, width=3),
            name="u(r) = (R² − r²) (−dp/dz) / (4μ)",
        )
    )
    fig.add_vline(
        x=float(res["u_avg"]),
        line=dict(color=ACCENT, width=1.5, dash="dash"),
        annotation_text=f"u_avg = u_max / 2 = {res['u_avg']:.3f} m/s",
    )
    fig.update_layout(
        title="Hagen–Poiseuille pipe flow (circular; α = 2 exactly)",
        xaxis_title="Axial velocity u(r) [m/s]",
        yaxis_title="r / R [-]",
        height=420,
    )
    return apply_plotly_theme(fig)

def plot_cavity_cfd(res: Dict[str, np.ndarray]) -> go.Figure:
    """Create 3-panel visualization for 2D Lid-Driven Cavity CFD simulation."""
    ghia_ok = bool(res.get("ghia_applicable", False))
    profile_title = (
        "Centerline velocity · Re = 100"
        if ghia_ok
        else "Centerline velocity"
    )
    fig = make_subplots(
        rows=1, cols=3,
        column_widths=[0.38, 0.34, 0.28],
        subplot_titles=(
            "Speed & streamlines",
            "Vorticity",
            profile_title,
        ),
        horizontal_spacing=0.08
    )
    
    x = res["x"]
    y = res["y"]
    
    # 1. Streamlines & Velocity magnitude
    fig.add_trace(
        go.Contour(
            x=x, y=y, z=res["v_mag"],
            colorscale="Viridis",
            contours=dict(start=0, end=1.0, size=0.05, showlines=False),
            colorbar=dict(title="|u| [-]", x=0.34, len=0.8),
            showscale=True,
            name="Speed |u|"
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Contour(
            x=x, y=y, z=res["psi"],
            colorscale=[[0, rgba(TEXT, 0.8)], [1, rgba(TEXT, 0.8)]],
            contours=dict(start=-0.12, end=0.02, size=0.01, coloring="none", showlines=True),
            line=dict(width=1.2, color=TEXT),
            showscale=False,
            name="Streamlines Ψ"
        ),
        row=1, col=1
    )
    
    # 2. Vorticity contour
    fig.add_trace(
        go.Contour(
            x=x, y=y, z=res["vorticity"],
            colorscale="RdBu_r",
            contours=dict(start=-15, end=15, size=1.5, showlines=False),
            colorbar=dict(title="ω_z [-]", x=0.68, len=0.8),
            showscale=True,
            name="Vorticity ω_z"
        ),
        row=1, col=2
    )
    
    # 3. Centerline velocity vs Benchmark
    fig.add_trace(
        go.Scatter(
            x=res["u_centerline"], y=y,
            mode="lines", line=dict(color=ACCENT, width=3),
            name="CFD Simulation (x = 0.5)"
        ),
        row=1, col=3
    )
    if ghia_ok:
        fig.add_trace(
            go.Scatter(
                x=res["ghia_u"], y=res["ghia_y"],
                mode="markers",
                marker=dict(size=7, color=PRESSURE, symbol="circle-open", line=dict(width=2)),
                name="Ghia et al. (1982) Re = 100 (steady)",
            ),
            row=1, col=3,
        )
    
    # No scaleanchor: Streamlit fullscreen writes layout.width/height and
    # a constrained cartesian subplot collapses on revert.
    fig.update_xaxes(title_text="x/L [-]", range=[-0.02, 1.02], constrain="domain", row=1, col=1)
    fig.update_yaxes(title_text="y/L [-]", range=[-0.02, 1.02], row=1, col=1)
    fig.update_xaxes(title_text="x/L [-]", range=[-0.02, 1.02], constrain="domain", row=1, col=2)
    fig.update_yaxes(title_text="y/L [-]", range=[-0.02, 1.02], row=1, col=2)
    fig.update_xaxes(title_text="Horizontal Velocity u [-]", row=1, col=3)
    fig.update_yaxes(title_text="Height y/L [-]", row=1, col=3)
    
    fig.update_layout(height=480)
    return apply_plotly_theme(fig)

def plot_moody_chart(
    re_operating: float = 50000.0,
    eps_d_operating: float = 0.001,
    f_operating: float = 0.0055
) -> go.Figure:
    """Interactive Moody diagram in Fanning f_F, with a dynamic operating point."""
    from src.physics.pipe_flow import generate_moody_chart_data
    data = generate_moody_chart_data()
    
    fig = go.Figure()
    
    # 1. Laminar Line f_F = 16/Re
    fig.add_trace(
        go.Scatter(
            x=data["re_lam"], y=data["f_lam"],
            mode="lines", line=dict(color=SUCCESS, width=3),
            name="Laminar (f_F = 16/Re)"
        )
    )
    
    # 2. Critical transition zone shading
    fig.add_vrect(
        x0=2000, x1=4000,
        fillcolor=rgba(WARNING, 0.15),
        line_width=0,
        annotation_text="Critical Transition",
        annotation_position="top left",
        annotation_font=dict(color=WARNING, size=10)
    )
    
    # 3. Turbulent curves for various roughness levels
    for eps in data["roughness_levels"]:
        f_curve = data["turb_curves"][eps]
        label = "Smooth Pipe (ε/D = 0)" if eps == 0.0 else f"ε/D = {eps:.0e}"
        is_smooth = (eps == 0.0)
        color = ACCENT if is_smooth else rgba(TEXT_MUTED, 0.45)
        width = 2.5 if is_smooth else 1.2
        
        fig.add_trace(
            go.Scatter(
                x=data["re_turb"], y=f_curve,
                mode="lines",
                line=dict(color=color, width=width),
                name=label,
                showlegend=(is_smooth or eps in [1e-4, 1e-3, 1e-2, 5e-2])
            )
        )
        
    # 4. Operating point indicator
    fig.add_trace(
        go.Scatter(
            x=[re_operating], y=[f_operating],
            mode="markers+text",
            marker=dict(size=14, color=PRESSURE, symbol="diamond", line=dict(width=2, color=TEXT)),
            text=[f"  Operating Point: Re = {re_operating:,.0f}, f_F = {f_operating:.4f}"],
            textposition="top right",
            textfont=dict(color=PRESSURE, size=12, family="'JetBrains Mono', monospace"),
            name="Current Operating Point"
        )
    )
    
    fig.update_xaxes(
        type="log",
        title_text="Reynolds Number Re = ρ·u·D / μ [-]",
        range=[np.log10(500), np.log10(1e8)],
        dtick=1
    )
    fig.update_yaxes(
        type="log",
        title_text="Fanning Friction Factor f_F [-]  (Darcy f_D = 4 f_F)",
        range=[np.log10(0.007 / 4.0), np.log10(0.11 / 4.0)],
        dtick=np.log10(2)
    )
    
    fig.update_layout(
        title="Interactive Moody Diagram (Fanning Friction Factor f_F = f_D / 4)",
        height=540,
        legend=dict(x=0.02, y=0.05, bgcolor=rgba(SURFACE, 0.85))
    )
    return apply_plotly_theme(fig)

def plot_laminar_turbulent_profiles(prof_res: Dict[str, np.ndarray]) -> go.Figure:
    """Keep the power-law cusp visible alongside a smooth mean-profile sketch."""
    r_norm = prof_res["r_norm"]
    # Mirror coordinates to show full pipe diameter from -R to +R
    r_full = np.concatenate([-r_norm[:0:-1], r_norm])
    u_lam_full = np.concatenate([prof_res["u_laminar"][:0:-1], prof_res["u_laminar"]])
    u_turb_full = np.concatenate([prof_res["u_turbulent"][:0:-1], prof_res["u_turbulent"]])
    u_smooth_full = np.concatenate([prof_res["u_smooth"][:0:-1], prof_res["u_smooth"]])
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=u_lam_full, y=r_full,
            mode="lines", line=dict(color=SUCCESS, width=3),
            name=f"Laminar reference (α = {prof_res['alpha_lam']:.3f})"
        )
    )
    fig.add_trace(
        go.Scatter(
            x=u_turb_full, y=r_full,
            mode="lines", line=dict(color=PRESSURE, width=2.5, dash="dash"),
            name=f"1/{prof_res['n_exp']:g} power-law approximation (α = {prof_res['alpha_turb']:.3f})"
        )
    )
    fig.add_trace(go.Scatter(
        x=u_smooth_full, y=r_full, mode="lines",
        line=dict(color=ACCENT, width=3),
        name=f"Smooth mean sketch (α = {prof_res['alpha_smooth']:.3f})",
    ))
    
    # Pipe wall reference lines at r/R = -1 and +1
    fig.add_hline(y=1.0, line=dict(color=TEXT_MUTED, width=2, dash="dash"), annotation_text="Top pipe wall (s = +R)")
    fig.add_hline(y=-1.0, line=dict(color=TEXT_MUTED, width=2, dash="dash"), annotation_text="Bottom pipe wall (s = −R)")
    fig.add_hline(y=0.0, line=dict(color=BORDER_STRONG, width=1, dash="dot"), annotation_text="Centerline")
    
    fig.update_layout(
        title="Pipe profiles at equal area-mean velocity",
        xaxis_title="Local Velocity u(r) [m/s]",
        yaxis_title="Signed position across diameter s/R [-]",
        height=560,
        legend=dict(orientation="h", y=-0.22, x=0.0),
        margin=dict(b=140),
        xaxis=dict(range=[0, 1.08 * prof_res["u_max_lam"]]),
    )
    return apply_plotly_theme(fig)


def plot_pipe_profile_limits(prof_res: Dict) -> go.Figure:
    """Resolve the two places where the power law fails without hiding either."""
    eta = prof_res["r_norm"]
    mean = prof_res["u_max_lam"] / 2.0
    fig = make_subplots(rows=1, cols=2, subplot_titles=(
        "Core: a smooth maximum", "Wall: finite slope and no slip"))
    for field, color, dash, name in (
        ("u_turbulent", PRESSURE, "dash", f"1/{prof_res['n_exp']:g} power law"),
        ("u_smooth", ACCENT, "solid", "Smooth mean sketch"),
    ):
        core = eta <= 0.2
        core_x = np.concatenate([-eta[core][:0:-1], eta[core]])
        core_u = np.concatenate([prof_res[field][core][:0:-1], prof_res[field][core]]) / mean
        fig.add_trace(go.Scatter(x=core_x, y=core_u, mode="lines", name=name,
                                line=dict(color=color, dash=dash)), row=1, col=1)
        distance = 1.0 - eta
        near = distance * prof_res["re_tau_smooth"] <= 5.0
        fig.add_trace(go.Scatter(x=distance[near][::-1], y=prof_res[field][near][::-1] / mean,
                                mode="lines", name=name, showlegend=False,
                                line=dict(color=color, dash=dash)), row=1, col=2)
    fig.update_xaxes(title_text="Signed position s/R", row=1, col=1)
    fig.update_yaxes(title_text="u / mean velocity", row=1, col=1)
    fig.update_xaxes(title_text="Distance from wall y/R", tickformat=".1e", row=1, col=2)
    fig.update_yaxes(title_text="u / mean velocity", row=1, col=2)
    fig.update_layout(title="Why the centre and wall need a different model", height=440,
                      legend=dict(orientation="h", y=-0.3), margin=dict(b=110))
    return apply_plotly_theme(fig)

def plot_law_of_the_wall(wall_res: Dict[str, np.ndarray]) -> go.Figure:
    """Create semi-log Universal Law of the Wall plot."""
    y_plus = wall_res["y_plus"]
    
    fig = go.Figure()
    
    # Viscous sublayer linear line u+ = y+
    idx_visc = y_plus <= 8.0
    fig.add_trace(
        go.Scatter(
            x=y_plus[idx_visc], y=wall_res["u_plus_viscous"][idx_visc],
            mode="lines", line=dict(color=ACCENT, width=2.5, dash="dash"),
            name="Viscous Sublayer (u⁺ = y⁺)"
        )
    )
    
    # Log-law line u+ = (1/kappa)*ln(y+) + B
    idx_log = y_plus >= 20.0
    fig.add_trace(
        go.Scatter(
            x=y_plus[idx_log], y=wall_res["u_plus_log"][idx_log],
            mode="lines", line=dict(color=SHEAR, width=2.5, dash="dash"),
            name=f"Log-Law Overlap (κ = {wall_res['kappa']}, B = {wall_res['B']})"
        )
    )
    
    # Continuous composite curve
    fig.add_trace(
        go.Scatter(
            x=y_plus, y=wall_res["u_plus_composite"],
            mode="lines", line=dict(color=SUCCESS, width=3),
            name="Spalding composite"
        )
    )
    
    # Sublayer vertical region boundaries
    fig.add_vrect(x0=0.1, x1=5.0, fillcolor=rgba(ACCENT, 0.12), line_width=0, annotation_text="Viscous (y⁺<5)")
    fig.add_vrect(x0=5.0, x1=30.0, fillcolor=rgba(WARNING, 0.12), line_width=0, annotation_text="Buffer (5≤y⁺≤30)")
    fig.add_vrect(x0=30.0, x1=1000.0, fillcolor=rgba(VORTICITY, 0.12), line_width=0, annotation_text="Log-Law (y⁺>30)")
    
    fig.update_xaxes(
        type="log",
        title_text="Dimensionless Wall Distance y⁺ = y·u_τ / ν [-]",
        range=[np.log10(0.1), np.log10(1000.0)]
    )
    fig.update_yaxes(
        title_text="Dimensionless Velocity u⁺ = u / u_τ [-]",
        range=[0, 30]
    )
    
    fig.update_layout(
        title="Universal Law of the Wall (Turbulent Boundary Layer Decomposition)",
        height=460
    )
    return apply_plotly_theme(fig)

def plot_cheme_head_loss_breakdown(sys_res: Dict) -> go.Figure:
    """Create head loss and pressure drop breakdown chart for chemical piping network."""
    labels = ["Pipe Skin Friction (Major)", "Valves & Fittings (Minor)", "Static Elevation Gain"]
    values = [
        sys_res["delta_p_major"] / 1000.0,
        sys_res["delta_p_minor"] / 1000.0,
        sys_res["delta_p_static"] / 1000.0
    ]
    colors = [ACCENT, SHEAR, SUCCESS]
    
    fig = go.Figure(
        data=[
            go.Bar(
                x=labels, y=values,
                marker=dict(color=colors),
                text=[f"{v:.1f} kPa" for v in values],
                textposition="auto"
            )
        ]
    )
    fig.update_layout(
        title="Piping System Pressure Drop Breakdown [kPa]",
        yaxis_title="Pressure Drop [kPa]",
        height=380
    )
    return apply_plotly_theme(fig)


def plot_blasius_profile(sim: Dict, plate: Dict) -> go.Figure:
    """Blasius similarity profile and dimensional growth of δ, δ*, θ."""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "Blasius profile u/U = f′(η)",
            "Thickness growth along the plate",
        ),
        horizontal_spacing=0.12,
    )
    fig.add_trace(
        go.Scatter(
            x=sim["f_prime"], y=sim["eta"],
            mode="lines", line=dict(color=SUCCESS, width=3),
            name="u/U = f′(η)",
        ),
        row=1, col=1,
    )
    fig.add_hline(
        y=float(sim["eta_99"]),
        line=dict(color=ACCENT, width=1.5, dash="dash"),
        annotation_text=f"δ₉₉ (η = {float(sim['eta_99']):.2f})",
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=plate["x"], y=plate["delta"] * 1000.0,
            mode="lines", line=dict(color=ACCENT, width=2.5),
            name="δ₉₉ [mm]",
        ),
        row=1, col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=plate["x"], y=plate["delta_star"] * 1000.0,
            mode="lines", line=dict(color=SUCCESS, width=2, dash="dash"),
            name="δ* [mm]",
        ),
        row=1, col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=plate["x"], y=plate["theta"] * 1000.0,
            mode="lines", line=dict(color=SHEAR, width=2, dash="dot"),
            name="θ [mm]",
        ),
        row=1, col=2,
    )
    fig.update_xaxes(title_text="u / U_∞ [-]", range=[0, 1.05], row=1, col=1)
    fig.update_yaxes(title_text="η = y √(U / (ν x)) [-]", row=1, col=1)
    fig.update_xaxes(title_text="Distance from leading edge x [m]", row=1, col=2)
    fig.update_yaxes(title_text="Thickness [mm]", row=1, col=2)
    fig.update_layout(height=440)
    return apply_plotly_theme(fig)


def plot_cylinder_separation(res: Dict) -> go.Figure:
    """Inviscid C_p and dp/ds on a cylinder with adverse-gradient and separation marks."""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "Inviscid C_p(θ) — Euler stays attached",
            "Outer-flow dp/ds (adverse after 90°)",
        ),
        horizontal_spacing=0.12,
    )
    th = res["theta_deg"]
    fig.add_trace(
        go.Scatter(
            x=th, y=res["cp"],
            mode="lines", line=dict(color=PRESSURE, width=3),
            name="C_p = 1 − 4 sin²θ",
        ),
        row=1, col=1,
    )
    fig.add_vline(x=90.0, line=dict(color=WARNING, width=1.5, dash="dash"), row=1, col=1)
    fig.add_vline(
        x=float(res["laminar_sep_deg"]),
        line=dict(color=SHEAR, width=2, dash="dot"),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=th, y=res["dp_ds"],
            mode="lines", line=dict(color=ACCENT, width=2.5),
            name="dp/ds",
        ),
        row=1, col=2,
    )
    fig.add_hline(y=0.0, line=dict(color=BORDER_STRONG, width=1, dash="dot"), row=1, col=2)
    fig.add_vline(x=90.0, line=dict(color=WARNING, width=1.5, dash="dash"),
                  annotation_text="adverse starts", row=1, col=2)
    fig.add_vline(
        x=float(res["laminar_sep_deg"]),
        line=dict(color=SHEAR, width=2, dash="dot"),
        annotation_text="laminar sep. ~105°",
        row=1, col=2,
    )
    fig.update_xaxes(title_text="θ from front stagnation [deg]", range=[0, 180], row=1, col=1)
    fig.update_yaxes(title_text="C_p [-]", row=1, col=1)
    fig.update_xaxes(title_text="θ from front stagnation [deg]", range=[0, 180], row=1, col=2)
    fig.update_yaxes(title_text="dp/ds [Pa/m]", row=1, col=2)
    fig.update_layout(height=430)
    return apply_plotly_theme(fig)


def plot_power_law_pipe(res: Dict, newtonian: Dict = None) -> go.Figure:
    """Power-law u(r) with optional Newtonian Hagen–Poiseuille overlay."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=res["u"], y=res["r_norm"],
            mode="lines", line=dict(color=SHEAR, width=3),
            name=f"Power-law n = {res['n']:.2f}",
        )
    )
    if newtonian is not None:
        fig.add_trace(
            go.Scatter(
                x=newtonian["u"], y=newtonian["r_norm"],
                mode="lines", line=dict(color=SUCCESS, width=2, dash="dash"),
                name="Newtonian n = 1 (same τ_w)",
            )
        )
    fig.add_vline(
        x=float(res["u_avg"]),
        line=dict(color=ACCENT, width=1.5, dash="dash"),
        annotation_text=f"u_avg = {res['u_avg']:.3f} m/s",
    )
    fig.update_layout(
        title="Laminar power-law pipe profile (same wall shear as the Newtonian overlay)",
        xaxis_title="Axial velocity u(r) [m/s]",
        yaxis_title="r / R [-]",
        height=420,
    )
    return apply_plotly_theme(fig)


def plot_npsh_station(npsh_a: float, npsh_r: float, parts: Dict) -> go.Figure:
    """Bar breakdown of NPSH_A terms versus required NPSH."""
    labels = ["(P_tank − P_v)/ρg", "z (flooded +, lift −)", "−h_f suction", "NPSH_A", "NPSH_R"]
    values = [
        parts["static_term"],
        parts["z_surface"],
        -parts["h_f"],
        npsh_a,
        npsh_r,
    ]
    colors = [ACCENT, SUCCESS, SHEAR, SUCCESS if npsh_a >= npsh_r else PRESSURE, WARNING]
    fig = go.Figure(
        data=[
            go.Bar(
                x=labels, y=values,
                marker=dict(color=colors),
                text=[f"{v:.2f} m" for v in values],
                textposition="auto",
            )
        ]
    )
    fig.update_layout(
        title="NPSH station (metres of fluid)",
        yaxis_title="Head [m]",
        height=380,
    )
    return apply_plotly_theme(fig)


def plot_straw_bundle(n_list, power_open, power_bundle, re_straw) -> go.Figure:
    """Pumping power vs straw count at fixed Q and outer diameter."""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Pumping power at fixed Q", "Straw Reynolds number"),
        horizontal_spacing=0.12,
    )
    fig.add_trace(
        go.Scatter(
            x=n_list, y=np.array(power_bundle) / 1000.0,
            mode="lines+markers", line=dict(color=PRESSURE, width=3),
            name="Bundle (N straws)",
        ),
        row=1, col=1,
    )
    fig.add_hline(
        y=float(power_open) / 1000.0,
        line=dict(color=SUCCESS, width=2, dash="dash"),
        annotation_text="open pipe",
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=n_list, y=re_straw,
            mode="lines+markers", line=dict(color=ACCENT, width=3),
            name="Re_d",
        ),
        row=1, col=2,
    )
    fig.add_hline(y=2300.0, line=dict(color=WARNING, width=1.5, dash="dash"),
                  annotation_text="pipe laminar limit", row=1, col=2)
    fig.update_xaxes(title_text="Number of straws N", type="log", row=1, col=1)
    fig.update_yaxes(title_text="Pump power Q·Δp [kW]", row=1, col=1)
    fig.update_xaxes(title_text="Number of straws N", type="log", row=1, col=2)
    fig.update_yaxes(title_text="Re_d (each straw)", type="log", row=1, col=2)
    fig.update_layout(height=420)
    return apply_plotly_theme(fig)


def plot_impeller_head_curve(curve: Dict, operating_q: float, operating_h: float) -> go.Figure:
    """Ideal Euler head against flow rate, with the current operating point marked.

    The straight line is the theory; a measured pump curve bends below it. Showing
    only the line would be misleading, so the caption in the UI says which is which.
    """
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=curve["flow_rate"] * 3600.0, y=curve["head"],
            mode="lines", line=dict(color=ACCENT, width=3),
            name=f"Euler head, beta_2 = {curve['beta2_deg']:.0f} deg",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[operating_q * 3600.0], y=[operating_h],
            mode="markers", marker=dict(color=WARNING, size=13, symbol="diamond"),
            name="Operating point",
        )
    )
    fig.add_hline(
        y=float(curve["head"][0]),
        line=dict(color=TEXT_MUTED, width=1.4, dash="dot"),
        annotation_text="approaching shutoff head",
    )
    fig.update_xaxes(title_text="Volumetric flow rate Q [m3/h]")
    fig.update_yaxes(title_text="Euler head H [m]")
    fig.update_layout(title="", height=380)
    return apply_plotly_theme(fig)


def plot_open_channel_rating(curve: Dict, state: Dict) -> go.Figure:
    """Depth-discharge rating curve, velocity, and the Froude regime split."""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Rating curve: how deep for a given flow", "Froude number and regime"),
        horizontal_spacing=0.12,
    )
    fig.add_trace(
        go.Scatter(
            x=curve["discharge"], y=curve["depth"],
            mode="lines", line=dict(color=ACCENT, width=3), name="Normal depth",
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=[state["discharge"]], y=[state["normal_depth"]],
            mode="markers", marker=dict(color=WARNING, size=13, symbol="diamond"),
            name="Design point",
        ),
        row=1, col=1,
    )
    fig.add_hline(
        y=state["bank_depth"], line=dict(color=PRESSURE, width=2, dash="dash"),
        annotation_text="top of bank", row=1, col=1,
    )
    fig.add_hline(
        y=state["critical_depth"], line=dict(color=SUCCESS, width=1.8, dash="dot"),
        annotation_text="critical depth", row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=curve["depth"], y=curve["froude"],
            mode="lines", line=dict(color=VORTICITY, width=3), name="Fr",
        ),
        row=1, col=2,
    )
    fig.add_hline(
        y=1.0, line=dict(color=SUCCESS, width=2, dash="dash"),
        annotation_text="Fr = 1, critical", row=1, col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=[state["normal_depth"]], y=[state["froude"]],
            mode="markers", marker=dict(color=WARNING, size=13, symbol="diamond"),
            showlegend=False,
        ),
        row=1, col=2,
    )
    fig.update_xaxes(title_text="Discharge Q [m3/s]", row=1, col=1)
    fig.update_yaxes(title_text="Depth y [m]", row=1, col=1)
    fig.update_xaxes(title_text="Depth y [m]", row=1, col=2)
    fig.update_yaxes(title_text="Froude number [-]", row=1, col=2)
    fig.update_layout(title="", height=420)
    return apply_plotly_theme(fig)


def plot_thermal_boundary_layers(profiles: List[Dict]) -> go.Figure:
    """Velocity and thermal profiles on one similarity axis, for several Pr.

    The velocity profile is the same curve every time -- momentum does not know
    about Pr. Only the thermal profile moves, and it is the ratio of the two
    thicknesses that Pr names.
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Profiles vs the similarity variable",
                        "Wall gradient: solved ODE vs the Pr^(1/3) fit"),
        horizontal_spacing=0.13,
    )
    fig.add_trace(
        go.Scatter(
            x=profiles[0]["f_prime"], y=profiles[0]["eta"],
            mode="lines", line=dict(color=TEXT_MUTED, width=4, dash="dash"),
            name="u/U (any Pr)",
        ),
        row=1, col=1,
    )
    for index, profile in enumerate(profiles):
        fig.add_trace(
            go.Scatter(
                x=profile["theta"], y=profile["eta"],
                mode="lines", line=dict(color=SERIES[index % len(SERIES)], width=2.6),
                name=f"theta, Pr = {profile['prandtl']:g}",
            ),
            row=1, col=1,
        )
    prandtl = [p["prandtl"] for p in profiles]
    fig.add_trace(
        go.Scatter(
            x=prandtl, y=[p["theta_gradient"] for p in profiles],
            mode="markers", marker=dict(color=ACCENT, size=11),
            name="solved ODE",
        ),
        row=1, col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=prandtl, y=[p["power_law_estimate"] for p in profiles],
            mode="lines", line=dict(color=WARNING, width=2.4, dash="dot"),
            name="0.332 Pr^(1/3)",
        ),
        row=1, col=2,
    )
    fig.update_xaxes(title_text="u/U and theta [-]", row=1, col=1)
    fig.update_yaxes(title_text="eta = y sqrt(U / nu x)", row=1, col=1)
    fig.update_xaxes(title_text="Prandtl (or Schmidt) number", type="log", row=1, col=2)
    fig.update_yaxes(title_text="theta'(0)", type="log", row=1, col=2)
    fig.update_layout(title="", height=430)
    return apply_plotly_theme(fig)


def plot_transport_correlations(curves: List[Dict], operating: Dict = None) -> go.Figure:
    """Nu (or Sh) against Re for several geometries, each over its own range."""
    fig = go.Figure()
    for index, curve in enumerate(curves):
        fig.add_trace(
            go.Scatter(
                x=curve["reynolds"], y=curve["values"],
                mode="lines", line=dict(color=SERIES[index % len(SERIES)], width=3),
                name=curve["geometry"],
            )
        )
    if operating:
        fig.add_trace(
            go.Scatter(
                x=[operating["reynolds"]], y=[operating["value"]],
                mode="markers", marker=dict(color=WARNING, size=14, symbol="diamond"),
                name="your case",
            )
        )
    fig.update_xaxes(title_text="Reynolds number", type="log")
    fig.update_yaxes(title_text="Nusselt or Sherwood number", type="log")
    fig.update_layout(title="", height=430)
    return apply_plotly_theme(fig)


def plot_relief_capacity(curve: Dict, operating_ratio: float = None) -> go.Figure:
    """Mass flux against back-pressure ratio: the choking plateau.

    The flat portion is the whole message. A relief device operating on it
    cannot be persuaded to pass more by lowering the downstream pressure.
    """
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=curve["ratio"], y=curve["mass_flux"],
            mode="lines", line=dict(color=ACCENT, width=3.5),
            name="mass flux G",
        )
    )
    fig.add_vrect(
        x0=min(curve["ratio"]), x1=curve["critical_ratio"],
        fillcolor=SUCCESS, opacity=0.10, line_width=0,
        annotation_text="choked: capacity fixed by p0 and T0 alone",
        annotation_position="top left",
    )
    fig.add_vline(
        x=curve["critical_ratio"],
        line=dict(color=WARNING, width=2, dash="dash"),
        annotation_text=f"critical {curve['critical_ratio']:.3f}",
    )
    if operating_ratio is not None:
        index = min(
            range(len(curve["ratio"])),
            key=lambda i: abs(curve["ratio"][i] - operating_ratio),
        )
        fig.add_trace(
            go.Scatter(
                x=[curve["ratio"][index]], y=[curve["mass_flux"][index]],
                mode="markers", marker=dict(color=PRESSURE, size=14, symbol="diamond"),
                name="your case",
            )
        )
    fig.update_xaxes(title_text="Back pressure / upstream stagnation pressure [-]")
    fig.update_yaxes(title_text="Mass flux G [kg/(s m2)]")
    fig.update_layout(title="", height=400)
    return apply_plotly_theme(fig)


def plot_flow_curves(curves: List[Dict], log_axes: bool = True) -> go.Figure:
    """Rheograms: shear stress and apparent viscosity against strain rate.

    Both panels are drawn from the same curves because they answer different
    questions. tau(gamma_dot) shows what the material *resists* with; the
    apparent viscosity tau/gamma_dot shows how that resistance would be
    mislabelled if someone insisted on quoting a single viscosity. A Newtonian
    fluid is the only one whose second panel is flat.
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "Flow curve: shear stress τ(γ̇)",
            "Apparent viscosity μ_app = τ/γ̇",
        ),
        horizontal_spacing=0.11,
    )
    for index, curve in enumerate(curves):
        color = SERIES[index % len(SERIES)]
        fig.add_trace(
            go.Scatter(
                x=curve["gamma_dot"], y=curve["tau"],
                mode="lines", line=dict(color=color, width=3),
                name=curve["model"], legendgroup=curve["model"],
            ),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=curve["gamma_dot"], y=curve["mu_app"],
                mode="lines", line=dict(color=color, width=3),
                name=curve["model"], legendgroup=curve["model"], showlegend=False,
            ),
            row=1, col=2,
        )
    axis_type = "log" if log_axes else "linear"
    fig.update_xaxes(title_text="Shear rate γ̇ [1/s]", type=axis_type, row=1, col=1)
    fig.update_xaxes(title_text="Shear rate γ̇ [1/s]", type=axis_type, row=1, col=2)
    fig.update_yaxes(title_text="τ [Pa]", type=axis_type, row=1, col=1)
    fig.update_yaxes(title_text="μ_app [Pa·s]", type=axis_type, row=1, col=2)
    fig.update_layout(
        title="Two views of the same material: stress, and the viscosity it would be given",
        height=440,
        legend=dict(orientation="h", yanchor="bottom", y=-0.34, xanchor="left", x=0),
    )
    return apply_plotly_theme(fig)


def plot_yield_stress_pipe(res: Dict, newtonian: Dict = None) -> go.Figure:
    """Pipe profile with the unyielded plug marked, beside the linear τ(r).

    The right panel is the reason the left one has a flat core: the momentum
    balance fixes τ(r) as a straight line for *every* fluid, so a yield stress
    is a horizontal cut across that line, and where it cuts is a radius.
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "Velocity profile u(r)",
            "Shear stress τ(r) = (r/2)(−dp/dz) — the same line for any fluid",
        ),
        horizontal_spacing=0.12,
    )
    fig.add_trace(
        go.Scatter(
            x=res["u"], y=res["r_norm"],
            mode="lines", line=dict(color=SHEAR, width=3),
            name=f"n = {res['n']:.2f}, τ_y = {res['tau_y']:.3g} Pa",
        ),
        row=1, col=1,
    )
    if newtonian is not None:
        fig.add_trace(
            go.Scatter(
                x=newtonian["u"], y=newtonian["r_norm"],
                mode="lines", line=dict(color=SUCCESS, width=2, dash="dash"),
                name="Newtonian, same τ_w",
            ),
            row=1, col=1,
        )
    plug = float(res["plug_fraction"])
    if plug > 1e-6:
        fig.add_hrect(
            y0=0.0, y1=plug,
            fillcolor=rgba(VORTICITY, 0.18), line_width=0,
            annotation_text=f"unyielded plug, r/R < {plug:.2f}",
            annotation_position="top left",
            row=1, col=1,
        )
    fig.add_trace(
        go.Scatter(
            x=res["tau_r"], y=res["r_norm"],
            mode="lines", line=dict(color=ACCENT, width=3),
            name="τ(r)", showlegend=False,
        ),
        row=1, col=2,
    )
    if res["tau_y"] > 0:
        fig.add_vline(
            x=float(res["tau_y"]),
            line=dict(color=VORTICITY, width=2, dash="dot"),
            annotation_text=f"τ_y = {res['tau_y']:.3g} Pa",
            row=1, col=2,
        )
    fig.add_vline(
        x=float(res["tau_wall"]),
        line=dict(color=PRESSURE, width=1.5, dash="dash"),
        annotation_text=f"τ_w = {res['tau_wall']:.3g} Pa",
        row=1, col=2,
    )
    fig.update_xaxes(title_text="Axial velocity u(r) [m/s]", row=1, col=1)
    fig.update_xaxes(title_text="Shear stress τ [Pa]", row=1, col=2)
    fig.update_yaxes(title_text="r / R [-]", row=1, col=1)
    fig.update_yaxes(title_text="r / R [-]", row=1, col=2)
    fig.update_layout(
        title="A yield stress turns a stress threshold into a radius",
        height=440,
        legend=dict(orientation="h", yanchor="bottom", y=-0.32, xanchor="left", x=0),
    )
    return apply_plotly_theme(fig)


def plot_thixotropy(res: Dict) -> go.Figure:
    """Structure and stress following a step up and back down in shear rate."""
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.07,
        subplot_titles=(
            "Imposed shear rate γ̇(t) — a step up, then back down",
            "Intact structure λ(t) — broken quickly, rebuilt slowly",
            "Measured stress τ(t) — the same γ̇ gives two different stresses",
        ),
    )
    fig.add_trace(
        go.Scatter(x=res["t"], y=res["gamma_dot"], mode="lines",
                   line=dict(color=ACCENT, width=2.5, shape="hv"), name="γ̇"),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=res["t"], y=res["structure"], mode="lines",
                   line=dict(color=VORTICITY, width=3), name="λ"),
        row=2, col=1,
    )
    fig.add_trace(
        go.Scatter(x=res["t"], y=res["tau"], mode="lines",
                   line=dict(color=SHEAR, width=3), name="τ"),
        row=3, col=1,
    )
    for row in (1, 2, 3):
        fig.add_vline(
            x=float(res["t_hold"]),
            line=dict(color=TEXT_DIM, width=1.5, dash="dot"),
            row=row, col=1,
        )
    fig.update_xaxes(title_text="Time t [s]", row=3, col=1)
    fig.update_yaxes(title_text="γ̇ [1/s]", row=1, col=1)
    fig.update_yaxes(title_text="λ [-]", row=2, col=1)
    fig.update_yaxes(title_text="τ [Pa]", row=3, col=1)
    fig.update_layout(
        title="Thixotropy: the stress depends on what the sample was doing a minute ago",
        height=620, showlegend=False,
    )
    return apply_plotly_theme(fig)


def plot_viscoelastic_startup(res: Dict) -> go.Figure:
    """Stress growth on startup, and the normal stress the same stretching makes."""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "Startup of steady shear: τ(t)",
            "Steady state: shear stress vs first normal stress difference",
        ),
        horizontal_spacing=0.12,
    )
    fig.add_trace(
        go.Scatter(x=res["t"], y=res["tau"], mode="lines",
                   line=dict(color=VISCOUS, width=3), name="Viscoelastic (Maxwell)"),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=res["t"], y=res["tau_newtonian"], mode="lines",
                   line=dict(color=SUCCESS, width=2, dash="dash"),
                   name="Newtonian: instantaneous"),
        row=1, col=1,
    )
    fig.add_vline(
        x=float(res["relax_time"]),
        line=dict(color=TEXT_DIM, width=1.5, dash="dot"),
        annotation_text=f"λ = {res['relax_time']:.2g} s",
        row=1, col=1,
    )
    fig.add_trace(
        go.Bar(
            x=["τ (shear)", "N₁ (along streamlines)"],
            y=[res["tau_steady"], res["n1_steady"]],
            marker=dict(color=[SHEAR, VORTICITY]),
            text=[f"{res['tau_steady']:.3g} Pa", f"{res['n1_steady']:.3g} Pa"],
            textposition="auto", showlegend=False,
        ),
        row=1, col=2,
    )
    fig.update_xaxes(title_text="Time t [s]", row=1, col=1)
    fig.update_yaxes(title_text="τ [Pa]", row=1, col=1)
    fig.update_yaxes(title_text="Stress [Pa]", row=1, col=2)
    fig.update_layout(
        title=f"Elastic memory: Wi = λγ̇ = {res['weissenberg']:.2f}, N₁/τ = 2Wi = {res['n1_over_tau']:.2f}",
        height=430,
        legend=dict(orientation="h", yanchor="bottom", y=-0.32, xanchor="left", x=0),
    )
    return apply_plotly_theme(fig)


# =============================================================================
# Rocket nozzles: contour geometry, the characteristic mesh, and altitude
# =============================================================================

def plot_moc_nozzle(moc: Dict, mirror: bool = True) -> go.Figure:
    """The method-of-characteristics mesh that produced a wall contour.

    Three things are meant to be legible at once: the fan of waves leaving the
    sharp throat corner, their reflection off the axis of symmetry, and their
    cancellation at the wall -- which is the wall's design condition, not a
    consequence of it. The wall points are coloured by local Mach number so the
    expansion can be read along the contour.
    """
    fig = go.Figure()

    wave_x, wave_y = [], []
    for (x0, y0), (x1, y1) in moc["waves"]:
        wave_x.extend([x0, x1, None])
        wave_y.extend([y0, y1, None])
    fig.add_trace(
        go.Scatter(x=wave_x, y=wave_y, mode="lines",
                   line=dict(color=rgba(TEXT_DIM, 0.55), width=1),
                   name="characteristics", hoverinfo="skip")
    )
    if mirror:
        fig.add_trace(
            go.Scatter(x=wave_x, y=[None if y is None else -y for y in wave_y],
                       mode="lines", line=dict(color=rgba(TEXT_DIM, 0.22), width=1),
                       name="mirror image", hoverinfo="skip", showlegend=False)
        )

    wall_x = [point["x"] for point in moc["wall"]]
    wall_y = [point["y"] for point in moc["wall"]]
    wall_m = [point["mach"] for point in moc["wall"]]
    fig.add_trace(
        go.Scatter(
            x=wall_x, y=wall_y, mode="lines+markers",
            line=dict(color=ACCENT, width=3.5),
            marker=dict(size=9, color=wall_m, colorscale="Turbo", showscale=True,
                        colorbar=dict(title="wall M", thickness=12)),
            name="contour", customdata=wall_m,
            hovertemplate="x=%{x:.3f}, r=%{y:.3f}<br>M=%{customdata:.3f}<extra></extra>",
        )
    )
    if mirror:
        fig.add_trace(
            go.Scatter(x=wall_x, y=[-y for y in wall_y], mode="lines",
                       line=dict(color=rgba(ACCENT, 0.45), width=3.5),
                       name="contour (mirrored)", showlegend=False, hoverinfo="skip")
        )
    fig.add_hline(y=0, line=dict(color=TEXT_DIM, width=1, dash="dashdot"))
    fig.add_annotation(
        x=0, y=moc["wall"][0]["y"], ax=40, ay=-34,
        text=f"sharp corner turns the flow {np.degrees(moc['theta_max']):.1f}° at once",
        showarrow=True, arrowcolor=WARNING, font=dict(color=WARNING, size=11),
    )
    fig.add_annotation(
        x=moc["length"], y=moc["exit_half_height"], ax=-56, ay=-28,
        text=f"exit: M = {moc['design_mach']:.2f}, wall back to axial",
        showarrow=True, arrowcolor=SUCCESS, font=dict(color=SUCCESS, size=11),
    )
    fig.update_xaxes(title_text="Axial distance from the throat / throat half-height")
    fig.update_yaxes(title_text="y / throat half-height")
    fig.update_layout(
        title=f"Minimum-length planar nozzle · {len(moc['wall']) - 1} waves · "
              f"half-height ratio {moc['achieved_area_ratio']:.3f} against the "
              f"ideal {moc['ideal_area_ratio']:.3f}",
        height=470,
        legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="left", x=0),
    )
    return apply_plotly_theme(fig)


def plot_nozzle_geometry(bell: Dict, cone: Dict, converging: Dict = None) -> go.Figure:
    """Bell against cone at equal expansion ratio, with the bell's construction.

    Both walls end at the same exit radius, so the only visible differences are
    the ones that matter: the bell is shorter, it turns hard immediately after
    the throat, and it arrives at the exit nearly axial while the cone is still
    throwing gas sideways at its full half-angle.
    """
    fig = go.Figure()
    if converging is not None:
        fig.add_trace(
            go.Scatter(x=converging["x"], y=converging["r"], mode="lines",
                       line=dict(color=TEXT_MUTED, width=3), name="converging section")
        )
        fig.add_trace(
            go.Scatter(x=converging["x"], y=[-r for r in converging["r"]], mode="lines",
                       line=dict(color=TEXT_MUTED, width=3), showlegend=False,
                       hoverinfo="skip")
        )
    for contour, color, label in ((cone, SHEAR, f"{cone['half_angle_deg']:.0f}° cone"),
                                  (bell, ACCENT,
                                   f"{100 * bell['length_fraction']:.0f}% bell")):
        fig.add_trace(
            go.Scatter(x=contour["x"], y=contour["r"], mode="lines",
                       line=dict(color=color, width=3.5), name=label)
        )
        fig.add_trace(
            go.Scatter(x=contour["x"], y=[-r for r in contour["r"]], mode="lines",
                       line=dict(color=rgba(color, 0.45), width=3.5),
                       showlegend=False, hoverinfo="skip")
        )
    attach, control = bell["attachment_point"], bell["control_point"]
    fig.add_trace(
        go.Scatter(
            x=[attach[0], control[0], bell["x"][-1]],
            y=[attach[1], control[1], bell["r"][-1]],
            mode="lines+markers+text",
            line=dict(color=VORTICITY, width=1.5, dash="dot"),
            marker=dict(color=VORTICITY, size=9, symbol="x"),
            text=["N · arc ends at θn", "tangents meet", "E · exit at θe"],
            textposition="top center", textfont=dict(color=VORTICITY, size=11),
            name="Bezier control polygon",
        )
    )
    fig.add_hline(y=0, line=dict(color=TEXT_DIM, width=1, dash="dashdot"))
    fig.add_vline(x=0, line=dict(color=WARNING, width=1.5, dash="dash"),
                  annotation_text="throat", annotation_position="bottom right")
    fig.update_xaxes(title_text="Axial distance from the throat / throat radius")
    fig.update_yaxes(title_text="r / throat radius", scaleanchor="x", scaleratio=1)
    fig.update_layout(
        title=f"Same exit area in {100 * bell['length'] / bell['cone_length']:.0f}% "
              "of the length: the bell buys back the cone's divergence loss",
        height=470,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="left", x=0),
    )
    return apply_plotly_theme(fig)


def plot_nozzle_expansion(march: Dict, ambient_pressures: Dict = None) -> go.Figure:
    """Mach and static pressure along the wall, with the ambient lines that
    decide whether the same nozzle is over- or under-expanded.

    The pressure curve belongs to the nozzle alone. Each horizontal ambient line
    belongs to an altitude. Where a line sits above the exit pressure the plume
    is squeezed back by shocks; below it, the plume keeps expanding into the sky.
    """
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.09,
        subplot_titles=("Mach number along the contour",
                        "Static pressure, against the ambient it has to meet"),
    )
    fig.add_trace(
        go.Scatter(x=march["x"], y=march["mach"], mode="lines",
                   line=dict(color=ACCENT, width=3), name="M(x)"),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=march["x"], y=[p / 1000 for p in march["pressure"]],
                   mode="lines", line=dict(color=PRESSURE, width=3), name="p(x)"),
        row=2, col=1,
    )
    if ambient_pressures:
        for (label, pressure), color in zip(ambient_pressures.items(),
                                            (WARNING, SUCCESS, VORTICITY, INERTIA)):
            # A shape on a log axis is positioned in *log10* of the data value.
            # Passing kPa directly asks Plotly for y = 10^101, which drags the
            # axis range out to 10^110 and flattens the real curve onto the
            # floor of the panel.
            fig.add_hline(
                y=np.log10(pressure / 1000), row=2, col=1,
                line=dict(color=color, width=1.8, dash="dot"),
                annotation_text=label, annotation_position="top left",
                annotation_font=dict(color=color, size=11),
            )
    fig.update_yaxes(title_text="M [-]", row=1, col=1)
    fig.update_yaxes(title_text="p [kPa abs]", type="log", row=2, col=1)
    fig.update_xaxes(title_text="Axial distance from the throat / throat radius",
                     row=2, col=1)
    fig.update_layout(
        title="", height=530,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="left", x=0),
    )
    return apply_plotly_theme(fig)


def plot_thrust_vs_altitude(sweeps: Dict[str, Dict],
                            matched_altitudes: Dict[str, float] = None) -> go.Figure:
    """One nozzle per curve, flown from the pad to vacuum.

    Nothing inside any engine changes along its curve. Every rise is the
    atmosphere getting out of the way of the exit plane, which is why the
    steepest curve belongs to the largest exit area.
    """
    fig = make_subplots(
        rows=1, cols=2, horizontal_spacing=0.11,
        subplot_titles=("Thrust", "Specific impulse"),
    )
    for (label, sweep), color in zip(sweeps.items(), SERIES):
        altitude_km = [a / 1000 for a in sweep["altitude"]]
        fig.add_trace(
            go.Scatter(x=altitude_km, y=[t / 1000 for t in sweep["thrust"]],
                       mode="lines", line=dict(color=color, width=3), name=label),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(x=altitude_km, y=sweep["specific_impulse"], mode="lines",
                       line=dict(color=color, width=3), name=label,
                       showlegend=False),
            row=1, col=2,
        )
        separated = [a / 1000 for a, flag in
                     zip(sweep["altitude"], sweep["separation_predicted"]) if flag]
        if separated:
            fig.add_vrect(
                x0=min(separated), x1=max(separated), row=1, col=1,
                fillcolor=PRESSURE, opacity=0.12, line_width=0,
                annotation_text="separation predicted", annotation_position="top left",
                annotation_font=dict(color=PRESSURE, size=10),
            )
    for label, altitude in (matched_altitudes or {}).items():
        fig.add_vline(x=altitude / 1000, row=1, col=1,
                      line=dict(color=SUCCESS, width=1.5, dash="dash"),
                      annotation_text=label,
                      annotation_font=dict(color=SUCCESS, size=10))
    fig.update_xaxes(title_text="Altitude [km]", row=1, col=1)
    fig.update_xaxes(title_text="Altitude [km]", row=1, col=2)
    fig.update_yaxes(title_text="Thrust [kN]", row=1, col=1)
    fig.update_yaxes(title_text="Isp [s]", row=1, col=2)
    fig.update_layout(
        title="", height=440,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="left", x=0),
    )
    return apply_plotly_theme(fig)


def plot_thrust_coefficient_map(curves: List[Dict], operating: Dict = None) -> go.Figure:
    """C_F against expansion ratio, one curve per pressure ratio p_c/p_a.

    Each curve has a genuine maximum, and the locus of those maxima is exactly
    the matched-exit condition p_e = p_a. Left of its peak a nozzle is
    under-expanded and simply leaving pressure unused; right of it the nozzle is
    over-expanded and the last of the bell is being pushed backwards.
    """
    fig = go.Figure()
    for curve, color in zip(curves, SERIES):
        fig.add_trace(
            go.Scatter(x=curve["expansion_ratio"], y=curve["thrust_coefficient"],
                       mode="lines", line=dict(color=color, width=3),
                       name=curve["label"])
        )
        if curve.get("optimum") is not None:
            fig.add_trace(
                go.Scatter(x=[curve["optimum"][0]], y=[curve["optimum"][1]],
                           mode="markers",
                           marker=dict(color=color, size=13, symbol="circle-open",
                                       line=dict(width=3)),
                           name=f"{curve['label']} matched", showlegend=False)
            )
    optima = [c["optimum"] for c in curves if c.get("optimum") is not None]
    if len(optima) > 1:
        fig.add_trace(
            go.Scatter(x=[o[0] for o in optima], y=[o[1] for o in optima],
                       mode="lines", line=dict(color=SUCCESS, width=2, dash="dash"),
                       name="locus of pe = pa")
        )
    if operating is not None:
        fig.add_trace(
            go.Scatter(x=[operating["expansion_ratio"]],
                       y=[operating["thrust_coefficient"]],
                       mode="markers",
                       marker=dict(color=WARNING, size=15, symbol="diamond"),
                       name="your engine")
        )
    fig.update_xaxes(title_text="Expansion ratio A_e/A_t [-]", type="log")
    # Far past its optimum a sea-level curve dives towards zero and below, which
    # is arithmetically true and visually useless: it compresses every peak into
    # the top centimetre of the frame. Clip the view to the region where the
    # comparison lives. Deep over-expansion has separated long before this
    # anyway, which is the point the lesson makes beside the figure.
    peaks = [max(curve["thrust_coefficient"]) for curve in curves]
    fig.update_yaxes(
        title_text="Thrust coefficient C_F = F/(p_c A_t) [-]",
        range=[0.9, max(peaks) + 0.1] if peaks else None,
    )
    fig.update_layout(
        title="", height=450,
        legend=dict(orientation="h", yanchor="bottom", y=-0.32, xanchor="left", x=0),
    )
    return apply_plotly_theme(fig)
