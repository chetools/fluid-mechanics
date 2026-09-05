"""Plotly interactive visualization suite for Fluid Mechanics.

Creates consistent dark-themed figures styled with src/theme.py.
"""

from typing import Dict
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.theme import (
    apply_plotly_theme, SURFACE, SURFACE_RAISED, BORDER_STRONG,
    TEXT, TEXT_MUTED, TEXT_DIM, ACCENT, PRESSURE, SHEAR, VORTICITY, SUCCESS, WARNING, INERTIA, SERIES, rgba
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
            name="Pure Strain D (No Rotation)"
        ),
        row=1, col=1
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
    center = stress_res["mohr_center"] / 1000.0  # kPa
    radius = stress_res["mohr_radius"] / 1000.0
    sig_1 = stress_res["principal_stresses"][0] / 1000.0
    sig_2 = stress_res["principal_stresses"][1] / 1000.0
    
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
            name=f"Mean Stress σ_avg = {center:.2f} kPa"
        ),
        row=1, col=2
    )
    # Principal stress markers
    fig.add_trace(
        go.Scatter(
            x=[sig_1, sig_2], y=[0, 0],
            mode="markers", marker=dict(size=10, color=SUCCESS, symbol="diamond"),
            name="Principal Stresses (σ₁, σ₂)"
        ),
        row=1, col=2
    )
    # Max shear stress marker
    fig.add_trace(
        go.Scatter(
            x=[center, center], y=[-radius, radius],
            mode="lines+markers", line=dict(color=SHEAR, width=1.5, dash="dash"),
            marker=dict(size=8, color=SHEAR),
            name=f"Max In-Plane Shear τ_max = {radius:.2f} kPa"
        ),
        row=1, col=2
    )
    
    fig.update_xaxes(title_text="x displacement", scaleanchor="y", scaleratio=1, row=1, col=1)
    fig.update_yaxes(title_text="y displacement", row=1, col=1)
    fig.update_xaxes(title_text="Normal Stress σ [kPa]", row=1, col=2)
    fig.update_yaxes(title_text="Shear Stress τ [kPa]", row=1, col=2)
    
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
        title="Stokes' First Problem: viscous penetration δ(t) ≈ 3.64 √(ν t) (dotted)",
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
    f_operating: float = 0.022
) -> go.Figure:
    """Create complete interactive Moody Diagram with dynamic operating point."""
    from src.physics.pipe_flow import generate_moody_chart_data
    data = generate_moody_chart_data()
    
    fig = go.Figure()
    
    # 1. Laminar Line f = 64/Re
    fig.add_trace(
        go.Scatter(
            x=data["re_lam"], y=data["f_lam"],
            mode="lines", line=dict(color=SUCCESS, width=3),
            name="Laminar (f = 64/Re)"
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
            text=[f"  Operating Point: Re = {re_operating:,.0f}, f = {f_operating:.4f}"],
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
        title_text="Darcy Friction Factor f_D [-]",
        range=[np.log10(0.007), np.log10(0.11)],
        dtick=np.log10(2)
    )
    
    fig.update_layout(
        title="Interactive Moody Diagram (Darcy Friction Factor f_D)",
        height=540,
        legend=dict(x=0.02, y=0.05, bgcolor=rgba(SURFACE, 0.85))
    )
    return apply_plotly_theme(fig)

def plot_laminar_turbulent_profiles(prof_res: Dict[str, np.ndarray]) -> go.Figure:
    """Create radial velocity profile comparison: Laminar vs. Turbulent."""
    r_norm = prof_res["r_norm"]
    # Mirror coordinates to show full pipe diameter from -R to +R
    r_full = np.concatenate([-r_norm[::-1], r_norm])
    u_lam_full = np.concatenate([prof_res["u_laminar"][::-1], prof_res["u_laminar"]])
    u_turb_full = np.concatenate([prof_res["u_turbulent"][::-1], prof_res["u_turbulent"]])
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(
            x=u_lam_full, y=r_full,
            mode="lines", line=dict(color=SUCCESS, width=3),
            name=f"Laminar Parabolic (Apex = {prof_res['u_max_lam']:.2f} m/s, α = {prof_res['alpha_lam']:.2f})"
        )
    )
    fig.add_trace(
        go.Scatter(
            x=u_turb_full, y=r_full,
            mode="lines", line=dict(color=PRESSURE, width=3),
            name=f"Turbulent 1/{int(prof_res['n_exp'])}th Law (Apex = {prof_res['u_max_turb']:.2f} m/s, α = {prof_res['alpha_turb']:.2f})"
        )
    )
    
    # Pipe wall reference lines at r/R = -1 and +1
    fig.add_hline(y=1.0, line=dict(color=TEXT_MUTED, width=2, dash="dash"), annotation_text="Top Pipe Wall (r = +R)")
    fig.add_hline(y=-1.0, line=dict(color=TEXT_MUTED, width=2, dash="dash"), annotation_text="Bottom Pipe Wall (r = -R)")
    fig.add_hline(y=0.0, line=dict(color=BORDER_STRONG, width=1, dash="dot"), annotation_text="Centerline")
    
    fig.update_layout(
        title="Pipe Radial Velocity Profile Comparison u(r) at Equal Mean Velocity",
        xaxis_title="Local Velocity u(r) [m/s]",
        yaxis_title="Normalized Radial Position r/R [-]",
        height=460
    )
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
            name="Universal Composite Profile"
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
        annotation_text="δ₉₉ (η ≈ 4.91)",
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
