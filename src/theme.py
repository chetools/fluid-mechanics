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
        
        .stMainBlockContainer {{ max-width: 1240px; padding-top: 2.4rem; padding-bottom: 4rem; }}
        .stMarkdown p, .stMarkdown li {{ line-height: 1.7; }}
        .stMarkdown h2 {{ font-size: clamp(1.55rem, 2.6vw, 2.1rem); letter-spacing: -0.03em; }}
        .stMarkdown h3 {{ font-size: 1.25rem; margin-top: 1.2rem; letter-spacing: -0.015em; }}
        .course-intro {{ padding: 1.6rem 1.8rem; border: 1px solid {BORDER};
            border-radius: 16px; background: linear-gradient(115deg, #162d43, {BACKGROUND}); }}
        .course-intro h1 {{ font-size: clamp(1.8rem, 3.4vw, 2.8rem); line-height: 1.15;
            letter-spacing: -0.045em; padding: .6rem 0; font-weight: 650; }}
        .course-intro p {{ color: {TEXT_MUTED}; max-width: 650px; margin: .4rem 0 1rem; }}
        .chapter-eyebrow {{ font-size: .7rem; font-weight: 700; letter-spacing: .13em;
            color: {ACCENT}; margin-top: .3rem; }}
        .course-route {{ display: flex; flex-wrap: wrap; gap: .6rem 1.4rem;
            color: {TEXT_MUTED}; font-size: .75rem; }}
        [role="tablist"] {{ flex-wrap: wrap; gap: .3rem; height: auto;
            border-bottom: 1px solid {BORDER}; padding: .4rem 0; }}
        [role="tab"] {{ height: auto; min-height: 42px; padding: .55rem .7rem;
            border-radius: 7px; white-space: normal; }}
        [role="tab"][aria-selected="true"] {{ background: {rgba(ACCENT, 0.12)}; }}
        [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{ display: none; }}
        /* Chapter navigation is a radio group, not st.tabs, because st.tabs
           renders every panel body on every run (see the comment in app.py).
           These rules give the radio the same wrapping-tab appearance.
           Selectors use data-testid / data-selected, which are stable, rather
           than the generated st-emotion-cache class names, which are not. */
        .st-key-chapter_nav [role="radiogroup"] {{ display: flex; flex-wrap: wrap;
            gap: .3rem; border-bottom: 1px solid {BORDER}; padding: .4rem 0; }}
        .st-key-chapter_nav [data-testid="stRadioOption"] {{ min-height: 42px;
            padding: .55rem .7rem; border-radius: 7px; white-space: normal;
            margin: 0; cursor: pointer; display: flex; align-items: center;
            transition: background .12s ease; }}
        .st-key-chapter_nav [data-testid="stRadioOption"]:hover {{
            background: {rgba(ACCENT, 0.07)}; }}
        .st-key-chapter_nav [data-testid="stRadioOption"][data-selected="true"] {{
            background: {rgba(ACCENT, 0.12)}; }}
        .st-key-chapter_nav [data-testid="stRadioOption"][data-selected="true"] p {{
            color: {ACCENT}; font-weight: 600; }}
        /* Hide the radio dot: these read as chapter tabs, not as a form control.
           The accessible <input type=radio> is untouched, so keyboard and screen
           reader behaviour is unchanged. */
        .st-key-chapter_nav [data-testid="stRadioOption"] > div > div > div:first-child {{
            display: none; }}
        .st-key-chapter_nav [data-testid="stRadioOption"]:focus-within {{
            outline: 2px solid {ACCENT}; outline-offset: 1px; }}
        [data-testid="stExpander"] {{ border-color: {BORDER}; background: {rgba(SURFACE, 0.3)}; }}
        [data-testid="stExpander"] summary p {{ font-weight: 600; }}
        [data-testid="stMetricValue"] {{ font-size: clamp(1.25rem, 2vw, 1.8rem); overflow-wrap: anywhere; }}
        [data-testid="stLatex"] {{ overflow-x: auto; overflow-y: hidden; padding: .3rem 0; }}
        [class*="st-key-fig-"] [data-testid="stImage"] {{ overflow-x: auto; margin: .7rem 0; border-radius: 12px; }}
        [class*="st-key-fig-"] img {{ display: block; width: 100%; min-width: 880px;
            height: auto; max-width: 960px; margin: 0 auto; }}
        .diagram-frame:focus-visible {{ outline: 2px solid {ACCENT}; outline-offset: 2px; }}
        [class*="st-key-plot-"] {{ overflow-x: auto; }}
        [class*="st-key-plot-"] [data-testid="stElementContainer"] {{ min-width: 960px; }}
        @media (max-width: 700px) {{
            .stMainBlockContainer {{ padding-left: 1rem; padding-right: 1rem; }}
            .course-intro {{ padding: 1rem; }}
            [role="tab"] {{ padding: .4rem .55rem; }}
            .st-key-chapter_nav [data-testid="stRadioOption"] {{ padding: .4rem .55rem; }}
            .metric-card {{ min-height: 0 !important; }}
        }}

        /* Metric card styling */
        .metric-card {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 8px;
            min-height: 114px;
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
            font-size: clamp(16px, 1.7vw, 20px);
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

_TEMPLATE_NAME = "fluidmech-dark"


def _axis_style() -> dict:
    """Axis styling shared by every axis in a figure, including subplot axes."""
    return dict(
        gridcolor=GRID,
        zerolinecolor=BORDER_STRONG,
        color=TEXT_MUTED,
        linecolor=BORDER_STRONG,
        tickfont=dict(family=MONO_STACK, size=11),
    )


def _build_template():
    """Register the dark template once, instead of merging dicts per figure.

    A template applies to *every* axis (xaxis2, yaxis3, ...), whereas
    update_layout(xaxis=...) only reaches the first axis pair. Nine figures in
    src/plotting.py use make_subplots, so the template is what keeps their
    second and third panels from falling back to Plotly's light defaults.
    """
    import plotly.graph_objects as go
    import plotly.io as pio

    if _TEMPLATE_NAME in pio.templates:
        return _TEMPLATE_NAME
    pio.templates[_TEMPLATE_NAME] = go.layout.Template(
        layout=dict(
            paper_bgcolor=SURFACE,
            plot_bgcolor=SURFACE,
            colorway=list(SERIES),
            font=dict(family=FONT_STACK, color=TEXT, size=12),
            title=dict(font=dict(family=FONT_STACK, color=TEXT, size=14)),
            margin=dict(l=55, r=35, t=60, b=85),
            xaxis=_axis_style(),
            yaxis=_axis_style(),
            legend=dict(
                orientation="h", y=-0.22, x=0, xanchor="left", yanchor="top",
                bgcolor=rgba(SURFACE, 0.8),
                bordercolor=BORDER,
                borderwidth=1,
                font=dict(size=11, color=TEXT_MUTED),
            ),
        )
    )
    return _TEMPLATE_NAME


def apply_plotly_theme(fig):
    """Apply consistent dark-mode styling to any Plotly figure.

    Styling lives in a registered template so it reaches subplot axes too.
    The explicit title assignment stays: Plotly 7 renders an `undefined`
    title in this app when the text is left unset.
    """
    fig.update_layout(template=_build_template())
    fig.update_layout(
        title=dict(text=fig.layout.title.text or "")
    )
    # Scene axes (3D figures) are not covered by the 2D axis template entries.
    if any(key.startswith("scene") for key in fig.layout):
        fig.update_scenes(
            xaxis=dict(backgroundcolor=SURFACE, gridcolor=BORDER, color=TEXT_MUTED, showbackground=True),
            yaxis=dict(backgroundcolor=SURFACE, gridcolor=BORDER, color=TEXT_MUTED, showbackground=True),
            zaxis=dict(backgroundcolor=SURFACE, gridcolor=BORDER, color=TEXT_MUTED, showbackground=True),
        )
    return fig
