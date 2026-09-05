"""Design system, color palette, and CSS styling for Fluid Mechanics.

Unified single source of truth for UI colors, typography, Plotly styling,
and SVG vector graphics. Follows Tailwind slate dark mode.
"""

# --- Surfaces ---
BACKGROUND = "#0f172a"      # Page background (slate-900)
SURFACE = "#1e293b"         # Cards, plot backgrounds (slate-800)
SURFACE_RAISED = "#334155"  # Hover, active tabs, elevated cards (slate-700)
BORDER = "#334155"          # Subdued borders (slate-700)
BORDER_STRONG = "#475569"   # Highlighted borders (slate-600)
GRID = "#1e293b"            # Plot grid lines

# --- Text ---
TEXT = "#f8fafc"            # Primary text (slate-50)
TEXT_MUTED = "#cbd5e1"      # Secondary text (slate-300)
TEXT_DIM = "#94a3b8"        # Explanations, captions (slate-400)
TEXT_FAINT = "#64748b"      # Footnotes, subtle indicators (slate-500)

# --- Semantic Physical Accents ---
ACCENT = "#38bdf8"          # Primary highlight / Velocity / Streamlines (sky-400)
ACCENT_DEEP = "#0284c7"     # Darker accent (sky-600)
PRESSURE = "#f87171"        # Pressure / Compression (red-400)
PRESSURE_LOW = "#38bdf8"    # Low pressure suction (sky-400)
SHEAR = "#fb923c"           # Shear stress / Viscous friction (orange-400)
VORTICITY = "#a855f7"       # Vorticity / Rotation (purple-400)
SUCCESS = "#34d399"         # Incompressible / Divergence free / Valid (emerald-400)
WARNING = "#facc15"         # Approaching limits / Non-Newtonian (amber-400)
INERTIA = "#60a5fa"         # Inertial convective forces (blue-400)
VISCOUS = "#f472b6"         # Viscous diffusion forces (pink-400)

# Categorical series for multi-trace plots
SERIES = (ACCENT, SHEAR, VORTICITY, SUCCESS, PRESSURE, INERTIA, VISCOUS, WARNING)

# --- Typography ---
FONT_STACK = "Inter, 'Segoe UI', system-ui, -apple-system, sans-serif"
MONO_STACK = "'JetBrains Mono', 'Cascadia Code', Consolas, monospace"

def rgba(hex_color: str, alpha: float) -> str:
    """Convert hex color (#38bdf8) to rgba string with alpha channel."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"

def app_css() -> str:
    """Generate global application CSS stylesheet."""
    return f"""
    <style>
        /* Base typography and body */
        html, body, [class*="css"] {{
            font-family: {FONT_STACK};
            color: {TEXT};
        }}
        
        /* Metric card styling */
        .metric-card {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        }}
        .metric-card-title {{
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: {TEXT_DIM};
            margin-bottom: 4px;
        }}
        .metric-card-value {{
            font-size: 20px;
            font-weight: 700;
            font-family: {MONO_STACK};
            color: {TEXT};
        }}
        .metric-card-sub {{
            font-size: 12px;
            color: {TEXT_MUTED};
            margin-top: 2px;
        }}
        
        /* Formula callout block */
        .formula-card {{
            background: linear-gradient(135deg, {rgba(SURFACE, 0.9)}, {rgba(SURFACE_RAISED, 0.7)});
            border-left: 4px solid {ACCENT};
            border-radius: 0 8px 8px 0;
            padding: 14px 20px;
            margin: 14px 0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }}
        .formula-card-title {{
            font-weight: 700;
            font-size: 15px;
            color: {ACCENT};
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        /* Concept / intuition box */
        .concept-card {{
            background: {rgba(SURFACE, 0.8)};
            border: 1px solid {BORDER};
            border-radius: 8px;
            padding: 16px;
            margin: 12px 0;
        }}
        .concept-card-title {{
            font-weight: 600;
            font-size: 14px;
            color: {SUCCESS};
            margin-bottom: 8px;
        }}
        
        /* Badges */
        .pill-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 600;
            font-family: {MONO_STACK};
            text-transform: uppercase;
        }}
        .pill-incompressible {{
            background: {rgba(SUCCESS, 0.2)};
            color: {SUCCESS};
            border: 1px solid {SUCCESS};
        }}
        .pill-laminar {{
            background: {rgba(ACCENT, 0.2)};
            color: {ACCENT};
            border: 1px solid {ACCENT};
        }}
        .pill-turbulent {{
            background: {rgba(PRESSURE, 0.2)};
            color: {PRESSURE};
            border: 1px solid {PRESSURE};
        }}
        .pill-warning {{
            background: {rgba(WARNING, 0.2)};
            color: {WARNING};
            border: 1px solid {WARNING};
        }}

        /* Expander styling */
        .streamlit-expanderHeader {{
            background-color: {SURFACE} !important;
            border: 1px solid {BORDER} !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            color: {TEXT} !important;
        }}
    </style>
    """

def apply_plotly_theme(fig):
    """Apply consistent dark-mode styling to any Plotly figure."""
    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family=FONT_STACK, color=TEXT, size=12),
        title_font=dict(family=FONT_STACK, color=TEXT, size=14),
        margin=dict(l=45, r=25, t=40, b=40),
        xaxis=dict(
            gridcolor=GRID,
            zerolinecolor=BORDER_STRONG,
            color=TEXT_MUTED,
            tickfont=dict(family=MONO_STACK, size=11),
        ),
        yaxis=dict(
            gridcolor=GRID,
            zerolinecolor=BORDER_STRONG,
            color=TEXT_MUTED,
            tickfont=dict(family=MONO_STACK, size=11),
        ),
        legend=dict(
            bgcolor=rgba(SURFACE, 0.8),
            bordercolor=BORDER,
            borderwidth=1,
            font=dict(size=11, color=TEXT_MUTED),
        )
    )
    return fig
