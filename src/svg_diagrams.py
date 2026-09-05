"""Textbook-grade SVG vector diagram generators for Fluid Mechanics.

Generates responsive, self-contained SVG graphics with crisp arrows,
dimension markers, fluid elements, and mathematical annotations.
All diagrams use colors defined in src/theme.py.
"""

import streamlit as st
from src.theme import (
    SURFACE, SURFACE_RAISED, BORDER, BORDER_STRONG,
    TEXT, TEXT_MUTED, TEXT_DIM, ACCENT, ACCENT_DEEP,
    PRESSURE, SHEAR, VORTICITY, SUCCESS, WARNING, rgba
)

def clean_svg(svg: str) -> str:
    """Flatten an SVG string to a single line without indentation or blank lines.
    
    Prevents markdown parsers from treating indented XML tags as code blocks.
    """
    return "".join(line.strip() for line in svg.splitlines() if line.strip())

def render_svg(svg: str, caption: str = ""):
    """Render an SVG directly to Streamlit using st.html, avoiding markdown code blocks."""
    cleaned = clean_svg(svg)
    if hasattr(st, "html"):
        st.html(cleaned)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)
    if caption:
        st.caption(caption)

def _arrow_defs() -> str:
    """Standard SVG marker definitions for arrows and dimension heads."""
    return f"""
    <defs>
        <marker id="arrow-sky" viewBox="0 0 10 10" refX="6" refY="5"
                markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="{ACCENT}"/>
        </marker>
        <marker id="arrow-red" viewBox="0 0 10 10" refX="6" refY="5"
                markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="{PRESSURE}"/>
        </marker>
        <marker id="arrow-orange" viewBox="0 0 10 10" refX="6" refY="5"
                markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="{SHEAR}"/>
        </marker>
        <marker id="arrow-dim" viewBox="0 0 10 10" refX="5" refY="5"
                markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M 0 2 L 8 5 L 0 8 z" fill="{TEXT_DIM}"/>
        </marker>
        <pattern id="hatch-wall" width="10" height="10" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
            <line x1="0" y1="0" x2="0" y2="10" stroke="{BORDER_STRONG}" stroke-width="1.5" />
        </pattern>
    </defs>
    """

def diagram_continuity_streamtube() -> str:
    """Steady 1D mass conservation through a contracting streamtube."""
    return f"""
    <svg viewBox="0 0 740 240" width="100%" height="240" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="32" fill="{ACCENT}" font-size="15" font-weight="bold">Steady mass conservation (continuity)</text>
        <text x="24" y="52" fill="{TEXT_DIM}" font-size="12">No accumulation: mass in = mass out. For incompressible flow, volume flux is conserved.</text>
        <path d="M 80 80 L 280 100 L 280 160 L 80 180 Z" fill="{rgba(ACCENT, 0.12)}" stroke="{ACCENT}" stroke-width="2"/>
        <path d="M 280 100 L 620 70 L 620 190 L 280 160 Z" fill="{rgba(ACCENT, 0.08)}" stroke="{ACCENT}" stroke-width="2"/>
        <line x1="40" y1="130" x2="160" y2="130" stroke="{SUCCESS}" stroke-width="3" marker-end="url(#arrow-sky)"/>
        <line x1="480" y1="130" x2="700" y2="130" stroke="{SUCCESS}" stroke-width="4" marker-end="url(#arrow-sky)"/>
        <text x="90" y="122" fill="{SUCCESS}" font-size="13" font-weight="600">u1</text>
        <text x="88" y="200" fill="{TEXT_MUTED}" font-size="13">A1</text>
        <text x="640" y="122" fill="{SUCCESS}" font-size="13" font-weight="600">u2 &gt; u1</text>
        <text x="600" y="214" fill="{TEXT_MUTED}" font-size="13">A2 &lt; A1</text>
        <text x="200" y="230" fill="{TEXT}" font-size="14" font-family="'JetBrains Mono', monospace">rho A1 u1 = rho A2 u2  (steady)</text>
        <text x="455" y="52" fill="{TEXT_DIM}" font-size="12">Same rho: A u = Q = const along the tube</text>
    </svg>
    """


def diagram_1d_euler_element() -> str:
    """Differential 1D fluid element momentum balance diagram.
    
    Shows pressure forces on left/right faces, gravity vector at angle theta,
    flow acceleration direction, and elemental length dx.
    """
    return f"""
    <svg viewBox="0 0 740 320" width="100%" height="320" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        
        <!-- Streamline axis inclined -->
        <line x1="60" y1="230" x2="680" y2="90" stroke="{BORDER_STRONG}" stroke-dasharray="6,4" stroke-width="1.5" />
        <text x="640" y="80" fill="{TEXT_DIM}" font-size="13" font-style="italic">Streamtube axis s</text>
        
        <!-- Inclination angle indicator -->
        <line x1="70" y1="230" x2="200" y2="230" stroke="{TEXT_DIM}" stroke-dasharray="3,3" stroke-width="1" />
        <path d="M 150 230 A 80 80 0 0 0 145 212" fill="none" stroke="{TEXT_MUTED}" stroke-width="1.5" />
        <text x="160" y="222" fill="{TEXT_MUTED}" font-size="13" font-weight="600">θ</text>
        
        <!-- Fluid Element Box (inclined 12 deg) -->
        <g transform="translate(240, 100) rotate(-11.5)">
            <!-- Element Body -->
            <rect x="0" y="0" width="220" height="85" rx="4"
                  fill="{rgba(ACCENT, 0.12)}" stroke="{ACCENT}" stroke-width="2.5" />
            
            <!-- Center of mass dot -->
            <circle cx="110" cy="42" r="4" fill="{TEXT}" />
            <text x="118" y="38" fill="{TEXT}" font-size="12" font-weight="600">dm = ρ·A·dx</text>
            
            <!-- Cross section A text -->
            <text x="10" y="50" fill="{ACCENT}" font-size="13" font-weight="600">Area A</text>
            
            <!-- Left Pressure Force (p * A) -->
            <line x1="-70" y1="42" x2="-6" y2="42" stroke="{PRESSURE}" stroke-width="3" marker-end="url(#arrow-red)" />
            <text x="-95" y="30" fill="{PRESSURE}" font-size="13" font-weight="bold">p · A</text>
            <text x="-95" y="46" fill="{TEXT_DIM}" font-size="11">Upstream Force</text>

            <!-- Right Pressure Force (p + dp/dx dx)*A -->
            <line x1="290" y1="42" x2="226" y2="42" stroke="{PRESSURE}" stroke-width="3" marker-end="url(#arrow-red)" />
            <text x="235" y="30" fill="{PRESSURE}" font-size="13" font-weight="bold">(p + ∂p/∂x·dx) · A</text>
            <text x="235" y="46" fill="{TEXT_DIM}" font-size="11">Downstream Resistance</text>
            
            <!-- Dimension dx -->
            <line x1="0" y1="105" x2="220" y2="105" stroke="{TEXT_DIM}" stroke-width="1.2"
                  marker-start="url(#arrow-dim)" marker-end="url(#arrow-dim)" />
            <line x1="0" y1="85" x2="0" y2="115" stroke="{BORDER_STRONG}" stroke-width="1" />
            <line x1="220" y1="85" x2="220" y2="115" stroke="{BORDER_STRONG}" stroke-width="1" />
            <text x="100" y="122" fill="{TEXT_MUTED}" font-size="13" font-weight="600">dx</text>
            
            <!-- Flow Acceleration Arrow -->
            <line x1="60" y1="-30" x2="160" y2="-30" stroke="{SUCCESS}" stroke-width="2.5" marker-end="url(#arrow-sky)" />
            <text x="80" y="-40" fill="{SUCCESS}" font-size="12" font-weight="600">a = Du/Dt</text>
        </g>
        
        <!-- Gravity Vector (vertical downward from center) -->
        <g transform="translate(370, 160)">
            <line x1="0" y1="0" x2="0" y2="90" stroke="{SHEAR}" stroke-width="2.5" marker-end="url(#arrow-orange)" />
            <text x="10" y="55" fill="{SHEAR}" font-size="12" font-weight="bold">W = dm · g</text>
            
            <!-- Along-streamline component -->
            <line x1="0" y1="0" x2="-45" y2="9" stroke="{SHEAR}" stroke-width="1.5" stroke-dasharray="4,3" />
            <text x="-120" y="35" fill="{SHEAR}" font-size="11">-dm·g·sin(θ) = -dm·g·(dz/dx)</text>
        </g>
    </svg>
    """

def diagram_eulerian_vs_lagrangian() -> str:
    """Side-by-side comparison of Eulerian (field) vs. Lagrangian (particle) frames."""
    return f"""
    <svg viewBox="0 0 740 280" width="100%" height="280" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        
        <!-- Left Panel: Eulerian -->
        <rect x="20" y="20" width="335" height="240" rx="6" fill="{SURFACE_RAISED}" stroke="{BORDER}" stroke-width="1" />
        <text x="40" y="48" fill="{ACCENT}" font-size="15" font-weight="bold">Eulerian Framework (Field Observer)</text>
        <text x="40" y="68" fill="{TEXT_DIM}" font-size="12">Fixed sensor in space recording fluid rushing past</text>
        
        <!-- Fixed sensor probe -->
        <line x1="80" y1="140" x2="290" y2="140" stroke="{BORDER_STRONG}" stroke-dasharray="4,4" stroke-width="1.5" />
        <circle cx="185" cy="140" r="10" fill="{rgba(ACCENT, 0.2)}" stroke="{ACCENT}" stroke-width="2" />
        <line x1="185" y1="140" x2="185" y2="210" stroke="{TEXT_MUTED}" stroke-width="2" />
        <rect x="165" y="210" width="40" height="15" rx="3" fill="{BORDER_STRONG}" />
        <text x="145" y="120" fill="{ACCENT}" font-size="13" font-weight="bold">Probe at x₀ = (x, y, z)</text>
        <text x="145" y="170" fill="{TEXT_MUTED}" font-size="12">Measures: u(x₀, t)</text>
        
        <!-- River velocity passing probe -->
        <line x1="60" y1="110" x2="130" y2="110" stroke="{ACCENT}" stroke-width="2" marker-end="url(#arrow-sky)" />
        <line x1="220" y1="110" x2="310" y2="110" stroke="{ACCENT}" stroke-width="2" marker-end="url(#arrow-sky)" />
        
        <text x="40" y="242" fill="{TEXT_MUTED}" font-size="12" font-family="'JetBrains Mono', monospace">
            Rate of change: ∂u/∂t (local only)
        </text>
        
        <!-- Right Panel: Lagrangian -->
        <rect x="385" y="20" width="335" height="240" rx="6" fill="{SURFACE_RAISED}" stroke="{BORDER}" stroke-width="1" />
        <text x="405" y="48" fill="{SUCCESS}" font-size="15" font-weight="bold">Lagrangian Framework (Material Observer)</text>
        <text x="405" y="68" fill="{TEXT_DIM}" font-size="12">Sensors ride aboard a specific fluid parcel</text>
        
        <!-- Trajectory curve -->
        <path d="M 420 180 Q 500 160 560 120 T 680 90" fill="none" stroke="{SUCCESS}" stroke-width="2" stroke-dasharray="5,4" />
        
        <!-- Parcel at t1 -->
        <circle cx="470" cy="165" r="14" fill="{rgba(SUCCESS, 0.25)}" stroke="{SUCCESS}" stroke-width="2" />
        <text x="463" y="170" fill="{TEXT}" font-size="11" font-weight="bold">t₁</text>
        <line x1="470" y1="165" x2="510" y2="152" stroke="{SUCCESS}" stroke-width="2" marker-end="url(#arrow-sky)" />
        
        <!-- Parcel at t2 (accelerated) -->
        <circle cx="585" cy="110" r="14" fill="{rgba(SUCCESS, 0.25)}" stroke="{SUCCESS}" stroke-width="2" />
        <text x="578" y="115" fill="{TEXT}" font-size="11" font-weight="bold">t₂</text>
        <line x1="585" y1="110" x2="650" y2="95" stroke="{SUCCESS}" stroke-width="2.5" marker-end="url(#arrow-sky)" />
        
        <text x="405" y="225" fill="{TEXT_DIM}" font-size="12">Follows parcel trajectory: X(t), V(t)</text>
        <text x="405" y="244" fill="{SUCCESS}" font-size="12" font-family="'JetBrains Mono', monospace">
            Total Rate: Du/Dt = ∂u/∂t + (u·∇)u
        </text>
    </svg>
    """

def diagram_streamline_geometry() -> str:
    """Streamline definition showing tangent velocity vector and zero normal flux."""
    return f"""
    <svg viewBox="0 0 740 260" width="100%" height="260" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        
        <!-- Streamlines -->
        <path d="M 60 210 C 220 200, 360 140, 680 70" fill="none" stroke="{ACCENT}" stroke-width="3" />
        <path d="M 60 170 C 220 160, 360 100, 680 30" fill="none" stroke="{rgba(ACCENT, 0.4)}" stroke-width="1.5" stroke-dasharray="4,4" />
        <path d="M 60 250 C 220 240, 360 180, 680 110" fill="none" stroke="{rgba(ACCENT, 0.4)}" stroke-width="1.5" stroke-dasharray="4,4" />
        
        <text x="540" y="60" fill="{ACCENT}" font-size="13" font-weight="600">Streamline Ψ = C</text>
        
        <!-- Specific point on streamline -->
        <g transform="translate(360, 137)">
            <circle cx="0" cy="0" r="5" fill="{TEXT}" />
            <text x="-15" y="-12" fill="{TEXT}" font-size="12" font-weight="bold">Point P(x, y, z)</text>
            
            <!-- Velocity Vector Tangent -->
            <line x1="0" y1="0" x2="130" y2="-40" stroke="{ACCENT}" stroke-width="3" marker-end="url(#arrow-sky)" />
            <text x="140" y="-35" fill="{ACCENT}" font-size="14" font-weight="bold">u (Velocity Vector)</text>
            
            <!-- Arc displacement vector ds -->
            <line x1="0" y1="0" x2="70" y2="-21.5" stroke="{SUCCESS}" stroke-width="2" marker-end="url(#arrow-dim)" />
            <text x="45" y="-30" fill="{SUCCESS}" font-size="12" font-weight="600">ds (Tangent)</text>
            
            <!-- Unit normal vector -->
            <line x1="0" y1="0" x2="35" y2="114" stroke="{PRESSURE}" stroke-width="2" marker-end="url(#arrow-red)" />
            <text x="45" y="100" fill="{PRESSURE}" font-size="13" font-weight="600">n (Normal: u·n = 0)</text>
        </g>
        
        <!-- Mathematical Callout -->
        <rect x="40" y="30" width="300" height="70" rx="6" fill="{SURFACE_RAISED}" stroke="{BORDER}" />
        <text x="55" y="52" fill="{TEXT_MUTED}" font-size="12" font-weight="600">Streamline Tangency Condition:</text>
        <text x="55" y="74" fill="{ACCENT}" font-size="13" font-family="'JetBrains Mono', monospace">
            dx / u = dy / v = dz / w
        </text>
        <text x="55" y="90" fill="{SUCCESS}" font-size="11">Zero mass crosses any streamline</text>
    </svg>
    """

def diagram_stress_tensor_cube() -> str:
    """3D perspective isometric cube of an infinitesimal fluid parcel showing normal & shear stresses."""
    return f"""
    <svg viewBox="0 0 740 400" width="100%" height="400" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        
        <!-- Title & coordinate system -->
        <text x="30" y="35" fill="{TEXT}" font-size="15" font-weight="bold">Cauchy Stress Tensor σ_ij on Differential Element</text>
        <text x="30" y="55" fill="{TEXT_DIM}" font-size="12">First index i = face normal direction, second index j = force action direction</text>
        
        <!-- Global Coordinate Axes (bottom left) -->
        <g transform="translate(60, 340)">
            <line x1="0" y1="0" x2="50" y2="25" stroke="{BORDER_STRONG}" stroke-width="2" marker-end="url(#arrow-dim)" />
            <text x="55" y="32" fill="{TEXT_DIM}" font-size="12">x</text>
            <line x1="0" y1="0" x2="60" y2="-15" stroke="{BORDER_STRONG}" stroke-width="2" marker-end="url(#arrow-dim)" />
            <text x="68" y="-12" fill="{TEXT_DIM}" font-size="12">y</text>
            <line x1="0" y1="0" x2="0" y2="-60" stroke="{BORDER_STRONG}" stroke-width="2" marker-end="url(#arrow-dim)" />
            <text x="-5" y="-68" fill="{TEXT_DIM}" font-size="12">z</text>
        </g>
        
        <!-- 3D Cube faces (isometric projection) -->
        <!-- Center origin: (370, 220) -->
        <!-- Top face -->
        <polygon points="370,120 490,70 370,20 250,70"
                 fill="{rgba(SURFACE_RAISED, 0.9)}" stroke="{BORDER_STRONG}" stroke-width="2" />
        <!-- Right face (y face) -->
        <polygon points="370,120 490,70 490,210 370,260"
                 fill="{rgba(SURFACE, 0.95)}" stroke="{BORDER_STRONG}" stroke-width="2" />
        <!-- Front-left face (x face) -->
        <polygon points="370,120 250,70 250,210 370,260"
                 fill="{rgba(SURFACE_RAISED, 0.5)}" stroke="{BORDER_STRONG}" stroke-width="2" />
                 
        <!-- === TOP FACE (+z face) STRESSES === -->
        <!-- Normal stress sigma_zz (vertical up) -->
        <line x1="370" y1="70" x2="370" y2="-5" stroke="{PRESSURE}" stroke-width="3" marker-end="url(#arrow-red)" />
        <text x="380" y="5" fill="{PRESSURE}" font-size="13" font-weight="bold">σ_zz (Normal)</text>
        
        <!-- Shear stress tau_zx (along x face edge) -->
        <line x1="370" y1="70" x2="310" y2="95" stroke="{SHEAR}" stroke-width="2.5" marker-end="url(#arrow-orange)" />
        <text x="270" y="115" fill="{SHEAR}" font-size="12" font-weight="bold">τ_zx</text>
        
        <!-- Shear stress tau_zy (along y face edge) -->
        <line x1="370" y1="70" x2="430" y2="45" stroke="{SHEAR}" stroke-width="2.5" marker-end="url(#arrow-orange)" />
        <text x="440" y="50" fill="{SHEAR}" font-size="12" font-weight="bold">τ_zy</text>
        
        <!-- === FRONT-LEFT FACE (+x face) STRESSES === -->
        <!-- Normal stress sigma_xx (out along x) -->
        <line x1="310" y1="165" x2="210" y2="207" stroke="{PRESSURE}" stroke-width="3" marker-end="url(#arrow-red)" />
        <text x="135" y="215" fill="{PRESSURE}" font-size="13" font-weight="bold">σ_xx (Normal)</text>
        
        <!-- Shear stress tau_xy (tangent rightwards) -->
        <line x1="310" y1="165" x2="365" y2="142" stroke="{SHEAR}" stroke-width="2.5" marker-end="url(#arrow-orange)" />
        <text x="350" y="130" fill="{SHEAR}" font-size="12" font-weight="bold">τ_xy</text>
        
        <!-- Shear stress tau_xz (tangent upwards) -->
        <line x1="310" y1="165" x2="310" y2="105" stroke="{SHEAR}" stroke-width="2.5" marker-end="url(#arrow-orange)" />
        <text x="275" y="125" fill="{SHEAR}" font-size="12" font-weight="bold">τ_xz</text>
        
        <!-- === RIGHT FACE (+y face) STRESSES === -->
        <!-- Normal stress sigma_yy (out along y) -->
        <line x1="430" y1="165" x2="530" y2="123" stroke="{PRESSURE}" stroke-width="3" marker-end="url(#arrow-red)" />
        <text x="540" y="125" fill="{PRESSURE}" font-size="13" font-weight="bold">σ_yy (Normal)</text>
        
        <!-- Shear stress tau_yx (tangent leftwards) -->
        <line x1="430" y1="165" x2="375" y2="188" stroke="{SHEAR}" stroke-width="2.5" marker-end="url(#arrow-orange)" />
        <text x="385" y="210" fill="{SHEAR}" font-size="12" font-weight="bold">τ_yx</text>
        
        <!-- Shear stress tau_yz (tangent upwards) -->
        <line x1="430" y1="165" x2="430" y2="105" stroke="{SHEAR}" stroke-width="2.5" marker-end="url(#arrow-orange)" />
        <text x="440" y="125" fill="{SHEAR}" font-size="12" font-weight="bold">τ_yz</text>
        
        <!-- Symmetry note box (bottom right) -->
        <rect x="490" y="270" width="225" height="95" rx="6" fill="{SURFACE_RAISED}" stroke="{BORDER}" />
        <text x="505" y="295" fill="{SUCCESS}" font-size="12" font-weight="bold">Angular Momentum Balance:</text>
        <text x="505" y="315" fill="{TEXT_MUTED}" font-size="12">Absence of point body couples</text>
        <text x="505" y="335" fill="{ACCENT}" font-size="13" font-family="'JetBrains Mono', monospace">
            τ_xy = τ_yx,  τ_xz = τ_zx
        </text>
        <text x="505" y="352" fill="{TEXT_DIM}" font-size="11">Reduces 9 components to 6 independent</text>
    </svg>
    """

def diagram_kinematic_decomposition() -> str:
    """Decomposition of fluid motion: Translation + Linear Dilation + Angular Shear + Rigid Rotation."""
    return f"""
    <svg viewBox="0 0 740 280" width="100%" height="280" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        
        <!-- 4 Columns -->
        <!-- 1. Translation -->
        <rect x="15" y="15" width="165" height="250" rx="6" fill="{SURFACE_RAISED}" stroke="{BORDER}" />
        <text x="25" y="38" fill="{TEXT}" font-size="12" font-weight="bold">1. Pure Translation</text>
        <text x="25" y="55" fill="{TEXT_DIM}" font-size="11">Uniform velocity u₀</text>
        <!-- Square moving intact -->
        <rect x="35" y="120" width="45" height="45" fill="none" stroke="{BORDER_STRONG}" stroke-dasharray="3,3" />
        <line x1="80" y1="142" x2="110" y2="142" stroke="{TEXT_MUTED}" stroke-width="2" marker-end="url(#arrow-dim)" />
        <rect x="110" y="120" width="45" height="45" fill="{rgba(ACCENT, 0.2)}" stroke="{ACCENT}" stroke-width="2" />
        <text x="35" y="240" fill="{ACCENT}" font-size="11" font-family="'JetBrains Mono', monospace">Stress = 0</text>
        
        <!-- 2. Linear Extension (Dilation) -->
        <rect x="195" y="15" width="165" height="250" rx="6" fill="{SURFACE_RAISED}" stroke="{BORDER}" />
        <text x="205" y="38" fill="{TEXT}" font-size="12" font-weight="bold">2. Elongation / Strain</text>
        <text x="205" y="55" fill="{TEXT_DIM}" font-size="11">Normal strain rate D_xx</text>
        <!-- Square stretching into rectangle -->
        <rect x="235" y="120" width="45" height="45" fill="none" stroke="{BORDER_STRONG}" stroke-dasharray="3,3" />
        <rect x="220" y="130" width="75" height="25" fill="{rgba(PRESSURE, 0.2)}" stroke="{PRESSURE}" stroke-width="2" />
        <text x="205" y="225" fill="{PRESSURE}" font-size="11" font-family="'JetBrains Mono', monospace">∂u/∂x, ∂v/∂y</text>
        <text x="205" y="242" fill="{TEXT_DIM}" font-size="11">Generates normal stress</text>
        
        <!-- 3. Angular Shearing -->
        <rect x="375" y="15" width="165" height="250" rx="6" fill="{SURFACE_RAISED}" stroke="{BORDER}" />
        <text x="385" y="38" fill="{TEXT}" font-size="12" font-weight="bold">3. Angular Shearing</text>
        <text x="385" y="55" fill="{TEXT_DIM}" font-size="11">Symmetric rate D_xy</text>
        <!-- Square distorting into rhombus -->
        <rect x="420" y="120" width="45" height="45" fill="none" stroke="{BORDER_STRONG}" stroke-dasharray="3,3" />
        <polygon points="430,120 480,120 460,165 410,165" fill="{rgba(SHEAR, 0.2)}" stroke="{SHEAR}" stroke-width="2" />
        <text x="385" y="225" fill="{SHEAR}" font-size="11" font-family="'JetBrains Mono', monospace">½(∂u/∂y + ∂v/∂x)</text>
        <text x="385" y="242" fill="{TEXT_DIM}" font-size="11">Generates shear stress</text>
        
        <!-- 4. Rigid-Body Rotation -->
        <rect x="555" y="15" width="170" height="250" rx="6" fill="{SURFACE_RAISED}" stroke="{BORDER}" />
        <text x="565" y="38" fill="{TEXT}" font-size="12" font-weight="bold">4. Rigid-Body Rotation</text>
        <text x="565" y="55" fill="{TEXT_DIM}" font-size="11">Anti-symmetric spin Ω_xy</text>
        <!-- Square rotating without changing angles -->
        <rect x="610" y="120" width="45" height="45" fill="none" stroke="{BORDER_STRONG}" stroke-dasharray="3,3" />
        <g transform="translate(632, 142) rotate(22)">
            <rect x="-22" y="-22" width="44" height="44" fill="{rgba(VORTICITY, 0.2)}" stroke="{VORTICITY}" stroke-width="2" />
        </g>
        <text x="565" y="225" fill="{VORTICITY}" font-size="11" font-family="'JetBrains Mono', monospace">½(∂v/∂x - ∂u/∂y)</text>
        <text x="565" y="242" fill="{SUCCESS}" font-size="11" font-weight="bold">Stress = 0 (No friction)</text>
    </svg>
    """

def diagram_chorin_projection() -> str:
    """Flowchart of Chorin's Fractional Step / Projection Method."""
    return f"""
    <svg viewBox="0 0 740 180" width="100%" height="180" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        
        <!-- Step 1: Predictor -->
        <rect x="20" y="35" width="200" height="110" rx="6" fill="{SURFACE_RAISED}" stroke="{ACCENT}" stroke-width="2" />
        <text x="35" y="60" fill="{ACCENT}" font-size="13" font-weight="bold">1. Advection-Diffusion</text>
        <text x="35" y="80" fill="{TEXT_MUTED}" font-size="11">Ignore pressure, solve:</text>
        <text x="35" y="105" fill="{TEXT}" font-size="12" font-family="'JetBrains Mono', monospace">
            u* = uⁿ + Δt[-u·∇u + ν∇²u]
        </text>
        <text x="35" y="130" fill="{PRESSURE}" font-size="11">Notice: ∇·u* ≠ 0 (leaks mass)</text>
        
        <!-- Arrow 1 to 2 -->
        <line x1="220" y1="90" x2="265" y2="90" stroke="{TEXT_MUTED}" stroke-width="2.5" marker-end="url(#arrow-dim)" />
        
        <!-- Step 2: Pressure Poisson -->
        <rect x="270" y="35" width="200" height="110" rx="6" fill="{SURFACE_RAISED}" stroke="{PRESSURE}" stroke-width="2" />
        <text x="285" y="60" fill="{PRESSURE}" font-size="13" font-weight="bold">2. Pressure Poisson</text>
        <text x="285" y="80" fill="{TEXT_MUTED}" font-size="11">Enforce incompressibility:</text>
        <text x="285" y="105" fill="{TEXT}" font-size="12" font-family="'JetBrains Mono', monospace">
            ∇²pⁿ⁺¹ = (ρ/Δt) ∇·u*
        </text>
        <text x="285" y="130" fill="{TEXT_DIM}" font-size="11">Elliptic solver (Jacobi / FFT)</text>
        
        <!-- Arrow 2 to 3 -->
        <line x1="470" y1="90" x2="515" y2="90" stroke="{TEXT_MUTED}" stroke-width="2.5" marker-end="url(#arrow-dim)" />
        
        <!-- Step 3: Projection Corrector -->
        <rect x="520" y="35" width="200" height="110" rx="6" fill="{SURFACE_RAISED}" stroke="{SUCCESS}" stroke-width="2" />
        <text x="535" y="60" fill="{SUCCESS}" font-size="13" font-weight="bold">3. Divergence Projection</text>
        <text x="535" y="80" fill="{TEXT_MUTED}" font-size="11">Correct velocity field:</text>
        <text x="535" y="105" fill="{TEXT}" font-size="12" font-family="'JetBrains Mono', monospace">
            uⁿ⁺¹ = u* - (Δt/ρ) ∇pⁿ⁺¹
        </text>
        <text x="535" y="130" fill="{SUCCESS}" font-size="11" font-weight="bold">Result: ∇·uⁿ⁺¹ = 0 (exact)</text>
    </svg>
    """

def diagram_reynolds_experiment() -> str:
    """Osborne Reynolds' 1883 dye streak transition experiment."""
    return f"""
    <svg viewBox="0 0 740 320" width="100%" height="320" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        
        <text x="30" y="35" fill="{TEXT}" font-size="15" font-weight="bold">Osborne Reynolds' 1883 Pipe Flow Experiment</text>
        <text x="30" y="55" fill="{TEXT_DIM}" font-size="12">Demonstrating the transition from orderly laminar streamline flow to turbulent eddy bursts</text>
        
        <!-- Header water tank -->
        <rect x="30" y="80" width="140" height="190" rx="4" fill="{rgba(SURFACE_RAISED, 0.8)}" stroke="{BORDER_STRONG}" stroke-width="2" />
        <text x="45" y="110" fill="{ACCENT}" font-size="13" font-weight="bold">Constant-Head Tank</text>
        <line x1="30" y1="125" x2="170" y2="125" stroke="{ACCENT}" stroke-dasharray="4,4" stroke-width="1.5" />
        <text x="45" y="145" fill="{TEXT_MUTED}" font-size="11">Water Level</text>
        
        <!-- Dye reservoir & needle -->
        <circle cx="100" cy="180" r="22" fill="{rgba(PRESSURE, 0.25)}" stroke="{PRESSURE}" stroke-width="2" />
        <text x="85" y="185" fill="{PRESSURE}" font-size="12" font-weight="bold">Dye</text>
        <path d="M 122 180 L 195 180" fill="none" stroke="{PRESSURE}" stroke-width="3" />
        <polygon points="195,177 205,180 195,183" fill="{PRESSURE}" />
        
        <!-- Glass pipe bellmouth inlet and tube -->
        <path d="M 170 145 C 190 145, 195 165, 205 165 L 700 165" fill="none" stroke="{TEXT_MUTED}" stroke-width="2.5" />
        <path d="M 170 215 C 190 215, 195 195, 205 195 L 700 195" fill="none" stroke="{TEXT_MUTED}" stroke-width="2.5" />
        
        <!-- Regime 1: Laminar smooth filament -->
        <line x1="205" y1="180" x2="340" y2="180" stroke="{PRESSURE}" stroke-width="3.5" />
        <text x="220" y="155" fill="{SUCCESS}" font-size="11" font-weight="bold">Laminar (Re &lt; 2300)</text>
        <text x="220" y="215" fill="{TEXT_DIM}" font-size="10">Smooth razor-thin filament</text>
        <line x1="340" y1="165" x2="340" y2="195" stroke="{BORDER}" stroke-dasharray="3,3" />
        
        <!-- Regime 2: Transition waviness -->
        <path d="M 340 180 Q 360 172 380 180 T 420 180 T 460 180" fill="none" stroke="{PRESSURE}" stroke-width="3" />
        <text x="365" y="155" fill="{SHEAR}" font-size="11" font-weight="bold">Transition</text>
        <text x="365" y="215" fill="{TEXT_DIM}" font-size="10">Sinuous wave instability</text>
        <line x1="460" y1="165" x2="460" y2="195" stroke="{BORDER}" stroke-dasharray="3,3" />
        
        <!-- Regime 3: Turbulent mixing cloud -->
        <path d="M 460 180 C 480 168, 500 192, 520 175 C 540 166, 560 194, 590 172 C 620 190, 650 170, 700 180"
              fill="none" stroke="{PRESSURE}" stroke-width="2.5" />
        <!-- Turbulent cloud swirls -->
        <circle cx="530" cy="180" r="9" fill="none" stroke="{rgba(PRESSURE, 0.6)}" stroke-width="1.5" />
        <circle cx="580" cy="182" r="12" fill="none" stroke="{rgba(PRESSURE, 0.6)}" stroke-width="1.5" />
        <circle cx="640" cy="178" r="11" fill="none" stroke="{rgba(PRESSURE, 0.6)}" stroke-width="1.5" />
        <text x="510" y="155" fill="{PRESSURE}" font-size="11" font-weight="bold">Turbulent (Re &gt; 4000)</text>
        <text x="510" y="215" fill="{TEXT_DIM}" font-size="10">Complete cross-sectional mixing</text>
        
        <!-- Control valve at outlet -->
        <polygon points="695,160 715,180 695,200 715,160 695,180 715,200" fill="{TEXT_MUTED}" />
        <text x="680" y="235" fill="{TEXT_DIM}" font-size="11">Flow Valve</text>
        
        <!-- Dimensionless Number callout -->
        <rect x="220" y="245" width="460" height="55" rx="6" fill="{SURFACE_RAISED}" stroke="{BORDER}" />
        <text x="240" y="268" fill="{ACCENT}" font-size="12" font-weight="bold">The Reynolds Number Criterion:</text>
        <text x="240" y="288" fill="{TEXT_MUTED}" font-size="12" font-family="'JetBrains Mono', monospace">
            Re = (ρ · u_avg · D) / μ = (Inertia Forces) / (Viscous Damping)
        </text>
    </svg>
    """

def diagram_laminar_vs_turbulent_profiles() -> str:
    """Side-by-side comparison of laminar parabolic vs turbulent blunt velocity profiles."""
    return f"""
    <svg viewBox="0 0 740 300" width="100%" height="300" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        
        <!-- Left Panel: Laminar Poiseuille -->
        <rect x="20" y="20" width="335" height="260" rx="6" fill="{SURFACE_RAISED}" stroke="{BORDER}" />
        <text x="40" y="48" fill="{SUCCESS}" font-size="14" font-weight="bold">Laminar Poiseuille Flow (Re &lt; 2300)</text>
        <text x="40" y="68" fill="{TEXT_DIM}" font-size="11">Parabolic profile: u(r) = u_max · (1 - (r/R)²)</text>
        
        <!-- Pipe walls -->
        <line x1="50" y1="90" x2="330" y2="90" stroke="{TEXT_MUTED}" stroke-width="3" />
        <line x1="50" y1="210" x2="330" y2="210" stroke="{TEXT_MUTED}" stroke-width="3" />
        <line x1="50" y1="150" x2="330" y2="150" stroke="{BORDER_STRONG}" stroke-dasharray="4,4" stroke-width="1" />
        <text x="55" y="145" fill="{TEXT_DIM}" font-size="10">Centerline</text>
        
        <!-- Parabolic profile curve -->
        <path d="M 120 90 Q 280 150 120 210" fill="none" stroke="{SUCCESS}" stroke-width="3" />
        <!-- Velocity arrows -->
        <line x1="120" y1="150" x2="275" y2="150" stroke="{SUCCESS}" stroke-width="2" marker-end="url(#arrow-sky)" />
        <line x1="120" y1="120" x2="235" y2="120" stroke="{SUCCESS}" stroke-width="1.5" marker-end="url(#arrow-sky)" />
        <line x1="120" y1="180" x2="235" y2="180" stroke="{SUCCESS}" stroke-width="1.5" marker-end="url(#arrow-sky)" />
        
        <text x="40" y="240" fill="{TEXT_MUTED}" font-size="12">u_avg / u_max = <b>0.50</b> (Sharp apex)</text>
        <text x="40" y="260" fill="{SHEAR}" font-size="12">Wall shear: τ_w = 4μ · u_avg / R</text>
        
        <!-- Right Panel: Turbulent Power-Law -->
        <rect x="385" y="20" width="335" height="260" rx="6" fill="{SURFACE_RAISED}" stroke="{BORDER}" />
        <text x="405" y="48" fill="{PRESSURE}" font-size="14" font-weight="bold">Turbulent Flow (Re &gt; 4000)</text>
        <text x="405" y="68" fill="{TEXT_DIM}" font-size="11">Blunt 1/7th power-law: u(r) ≈ u_max · (1 - r/R)^(1/7)</text>
        
        <!-- Pipe walls -->
        <line x1="415" y1="90" x2="695" y2="90" stroke="{TEXT_MUTED}" stroke-width="3" />
        <line x1="415" y1="210" x2="695" y2="210" stroke="{TEXT_MUTED}" stroke-width="3" />
        <line x1="415" y1="150" x2="695" y2="150" stroke="{BORDER_STRONG}" stroke-dasharray="4,4" stroke-width="1" />
        <text x="420" y="145" fill="{TEXT_DIM}" font-size="10">Centerline</text>
        
        <!-- Blunt profile curve with steep wall gradients -->
        <path d="M 485 90 C 590 95, 630 140, 630 150 C 630 160, 590 205, 485 210" fill="none" stroke="{PRESSURE}" stroke-width="3" />
        <!-- Velocity arrows -->
        <line x1="485" y1="150" x2="625" y2="150" stroke="{PRESSURE}" stroke-width="2" marker-end="url(#arrow-red)" />
        <line x1="485" y1="120" x2="615" y2="120" stroke="{PRESSURE}" stroke-width="1.5" marker-end="url(#arrow-red)" />
        <line x1="485" y1="180" x2="615" y2="180" stroke="{PRESSURE}" stroke-width="1.5" marker-end="url(#arrow-red)" />
        
        <text x="405" y="240" fill="{TEXT_MUTED}" font-size="12">u_avg / u_max ≈ <b>0.82</b> (Flat plug-like core)</text>
        <text x="405" y="260" fill="{PRESSURE}" font-size="12">Steep wall gradient → <b>High friction factor</b></text>
    </svg>
    """

def diagram_law_of_the_wall() -> str:
    """Schematic of the 3 turbulent boundary layer sublayers."""
    return f"""
    <svg viewBox="0 0 740 240" width="100%" height="240" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        
        <text x="30" y="32" fill="{TEXT}" font-size="15" font-weight="bold">Universal Law of the Wall: Boundary Layer Sublayers</text>
        
        <!-- Bottom Wall -->
        <rect x="40" y="195" width="660" height="20" fill="url(#hatch-wall)" stroke="{BORDER_STRONG}" />
        <line x1="40" y1="195" x2="700" y2="195" stroke="{TEXT}" stroke-width="3" />
        <text x="340" y="210" fill="{TEXT_MUTED}" font-size="11" font-weight="bold">Solid Pipe Wall (y = 0, u = 0)</text>
        
        <!-- 1. Viscous sublayer: y+ < 5 -->
        <rect x="40" y="165" width="660" height="30" fill="{rgba(ACCENT, 0.15)}" stroke="{ACCENT}" stroke-width="1" stroke-dasharray="3,3" />
        <text x="55" y="185" fill="{ACCENT}" font-size="12" font-weight="bold">1. Viscous Sublayer (y⁺ &lt; 5):</text>
        <text x="240" y="185" fill="{TEXT_MUTED}" font-size="12">u⁺ = y⁺  (Pure molecular shear, zero turbulent eddies)</text>
        
        <!-- 2. Buffer layer: 5 <= y+ <= 30 -->
        <rect x="40" y="125" width="660" height="40" fill="{rgba(SHEAR, 0.15)}" stroke="{SHEAR}" stroke-width="1" stroke-dasharray="3,3" />
        <text x="55" y="150" fill="{SHEAR}" font-size="12" font-weight="bold">2. Buffer Layer (5 ≤ y⁺ ≤ 30):</text>
        <text x="240" y="150" fill="{TEXT_MUTED}" font-size="12">Viscous shear and Reynolds turbulent shear are equal</text>
        
        <!-- 3. Log-law layer: y+ > 30 -->
        <rect x="40" y="55" width="660" height="70" fill="{rgba(VORTICITY, 0.15)}" stroke="{VORTICITY}" stroke-width="1" stroke-dasharray="3,3" />
        <text x="55" y="85" fill="{VORTICITY}" font-size="12" font-weight="bold">3. Logarithmic Overlap Region (y⁺ &gt; 30):</text>
        <text x="55" y="110" fill="{TEXT}" font-size="13" font-family="'JetBrains Mono', monospace">
            u⁺ = (1/κ) · ln(y⁺) + B       (von Kármán κ ≈ 0.41, B ≈ 5.0)
        </text>
    </svg>
    """

def diagram_null_space_matrix() -> str:
    """Linear algebra illustration of dimensional matrix mapping A * x = 0."""
    return f"""
    <svg viewBox="0 0 740 220" width="100%" height="220" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        
        <text x="30" y="32" fill="{TEXT}" font-size="15" font-weight="bold">Linear Algebra Solution: The Null-Space Method</text>
        <text x="30" y="52" fill="{TEXT_DIM}" font-size="12">Finding dimensionless invariants as the kernel basis: ker(A) = {{ x | A·x = 0 }}</text>
        
        <!-- Matrix A -->
        <rect x="40" y="70" width="220" height="120" rx="6" fill="{SURFACE_RAISED}" stroke="{ACCENT}" stroke-width="2" />
        <text x="55" y="95" fill="{ACCENT}" font-size="13" font-weight="bold">Dimensional Matrix A (m × n)</text>
        <text x="55" y="120" fill="{TEXT_MUTED}" font-size="11">Rows: Base Dimensions [M, L, T]</text>
        <text x="55" y="140" fill="{TEXT_MUTED}" font-size="11">Cols: Physical Variables [q₁, q₂, ..., qₙ]</text>
        <text x="55" y="170" fill="{TEXT_DIM}" font-size="11">Rank: r = rank(A) ≤ min(m, n)</text>
        
        <!-- Multiplication symbol -->
        <text x="280" y="135" fill="{TEXT}" font-size="22" font-weight="bold">·</text>
        
        <!-- Vector x -->
        <rect x="310" y="70" width="130" height="120" rx="6" fill="{SURFACE_RAISED}" stroke="{SHEAR}" stroke-width="2" />
        <text x="325" y="95" fill="{SHEAR}" font-size="13" font-weight="bold">Exponent Vector x</text>
        <text x="325" y="120" fill="{TEXT_MUTED}" font-size="11">[a₁, a₂, ..., aₙ]ᵀ</text>
        <text x="325" y="150" fill="{TEXT_DIM}" font-size="11">Dimensionless powers:</text>
        <text x="325" y="170" fill="{SHEAR}" font-size="11">q₁ᵃ¹ · q₂ᵃ² ··· qₙᵃⁿ</text>
        
        <!-- Equals symbol -->
        <text x="460" y="135" fill="{TEXT}" font-size="22" font-weight="bold">=</text>
        
        <!-- Zero vector -->
        <rect x="490" y="70" width="80" height="120" rx="6" fill="{SURFACE_RAISED}" stroke="{SUCCESS}" stroke-width="2" />
        <text x="515" y="95" fill="{SUCCESS}" font-size="13" font-weight="bold">0</text>
        <text x="510" y="120" fill="{TEXT_MUTED}" font-size="11">[0, 0, 0]ᵀ</text>
        <text x="500" y="150" fill="{TEXT_DIM}" font-size="10">Zero net</text>
        <text x="500" y="170" fill="{SUCCESS}" font-size="10">dimensions</text>
        
        <!-- Arrow to Rank-Nullity result -->
        <line x1="585" y1="130" x2="620" y2="130" stroke="{TEXT_MUTED}" stroke-width="2" marker-end="url(#arrow-dim)" />
        
        <rect x="630" y="70" width="85" height="120" rx="6" fill="{rgba(ACCENT, 0.2)}" stroke="{ACCENT}" stroke-width="2" />
        <text x="640" y="95" fill="{ACCENT}" font-size="12" font-weight="bold">Nullity</text>
        <text x="640" y="120" fill="{TEXT}" font-size="14" font-weight="bold">p = n - r</text>
        <text x="640" y="150" fill="{TEXT_DIM}" font-size="10">Linearly</text>
        <text x="640" y="170" fill="{TEXT_DIM}" font-size="10">independent</text>
        <text x="640" y="185" fill="{ACCENT}" font-size="10">Π Groups!</text>
    </svg>
    """


def diagram_blasius_plate() -> str:
    """Flat-plate laminar boundary layer growing as x / sqrt(Re_x)."""
    return f"""
    <svg viewBox="0 0 740 240" width="100%" height="240" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="28" fill="{ACCENT}" font-size="15" font-weight="bold">Blasius laminar boundary layer on a flat plate</text>
        <text x="24" y="48" fill="{TEXT_DIM}" font-size="12">No-slip at the wall; inviscid U_∞ outside. Thickness δ ~ x / √Re_x.</text>
        <rect x="60" y="190" width="640" height="18" fill="url(#hatch-wall)" stroke="{BORDER_STRONG}"/>
        <line x1="60" y1="190" x2="700" y2="190" stroke="{TEXT}" stroke-width="3"/>
        <text x="330" y="222" fill="{TEXT_MUTED}" font-size="12">Plate wall (u = 0)</text>
        <path d="M 80 190 Q 220 150 400 120 T 680 70" fill="none" stroke="{ACCENT}" stroke-width="2.5"/>
        <text x="500" y="68" fill="{ACCENT}" font-size="13" font-weight="600">δ(x) ≈ 4.91 x / √Re_x</text>
        <line x1="80" y1="100" x2="200" y2="100" stroke="{SUCCESS}" stroke-width="2" marker-end="url(#arrow-sky)"/>
        <text x="88" y="92" fill="{SUCCESS}" font-size="12">U_∞</text>
        <line x1="520" y1="100" x2="640" y2="100" stroke="{SUCCESS}" stroke-width="2" marker-end="url(#arrow-sky)"/>
        <text x="70" y="175" fill="{TEXT_MUTED}" font-size="11">leading edge</text>
        <text x="24" y="70" fill="{TEXT_DIM}" font-size="12" font-family="'JetBrains Mono', monospace">c_f = 0.664 / √Re_x     C_F = 1.328 / √Re_L</text>
    </svg>
    """


def diagram_npsh() -> str:
    """Open tank, suction line, and pump centerline for NPSH_A."""
    return f"""
    <svg viewBox="0 0 740 260" width="100%" height="260" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="28" fill="{ACCENT}" font-size="15" font-weight="bold">NPSH_A from a free-surface tank</text>
        <text x="24" y="48" fill="{TEXT_DIM}" font-size="12">NPSH_A = (P_tank − P_v)/ρg + z − h_f. z &gt; 0 flooded; z &lt; 0 suction lift.</text>
        <rect x="50" y="70" width="160" height="140" rx="4" fill="{rgba(ACCENT, 0.12)}" stroke="{ACCENT}" stroke-width="2"/>
        <line x1="50" y1="110" x2="210" y2="110" stroke="{SUCCESS}" stroke-width="2" stroke-dasharray="6,3"/>
        <text x="70" y="100" fill="{SUCCESS}" font-size="12">free surface P_tank</text>
        <text x="85" y="155" fill="{TEXT_MUTED}" font-size="12">liquid</text>
        <line x1="210" y1="180" x2="480" y2="180" stroke="{ACCENT}" stroke-width="8"/>
        <text x="280" y="170" fill="{TEXT_DIM}" font-size="12">suction line L, D, fittings</text>
        <rect x="480" y="150" width="90" height="60" rx="8" fill="{SURFACE_RAISED}" stroke="{SHEAR}" stroke-width="2"/>
        <text x="498" y="185" fill="{SHEAR}" font-size="13" font-weight="bold">pump</text>
        <line x1="70" y1="110" x2="70" y2="180" stroke="{WARNING}" stroke-width="1.5" marker-start="url(#arrow-dim)" marker-end="url(#arrow-dim)"/>
        <text x="78" y="150" fill="{WARNING}" font-size="12">z</text>
        <text x="590" y="175" fill="{TEXT_MUTED}" font-size="12">centerline</text>
        <text x="50" y="250" fill="{TEXT}" font-size="12" font-family="'JetBrains Mono', monospace">Cavitate if NPSH_A &lt; NPSH_R</text>
    </svg>
    """


def diagram_power_law() -> str:
    """Newtonian vs shear-thinning vs shear-thickening τ(γ̇)."""
    return f"""
    <svg viewBox="0 0 740 230" width="100%" height="230" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="28" fill="{ACCENT}" font-size="15" font-weight="bold">Ostwald–de Waele: τ = K |γ̇|^{{n−1}} γ̇</text>
        <line x1="80" y1="200" x2="360" y2="200" stroke="{TEXT_MUTED}" stroke-width="1.5"/>
        <line x1="80" y1="200" x2="80" y2="50" stroke="{TEXT_MUTED}" stroke-width="1.5"/>
        <text x="330" y="216" fill="{TEXT_DIM}" font-size="12">shear rate γ̇</text>
        <text x="24" y="70" fill="{TEXT_DIM}" font-size="12">τ</text>
        <path d="M 80 200 L 340 70" fill="none" stroke="{SUCCESS}" stroke-width="2.5"/>
        <text x="300" y="80" fill="{SUCCESS}" font-size="12">n = 1 Newtonian</text>
        <path d="M 80 200 Q 180 170 340 150" fill="none" stroke="{SHEAR}" stroke-width="2.5"/>
        <text x="250" y="145" fill="{SHEAR}" font-size="12">n &lt; 1 thinning</text>
        <path d="M 80 200 Q 200 90 340 48" fill="none" stroke="{PRESSURE}" stroke-width="2.5"/>
        <text x="200" y="55" fill="{PRESSURE}" font-size="12">n &gt; 1 thickening</text>
        <text x="400" y="90" fill="{TEXT}" font-size="13">Pipe momentum: τ_w = (R/2)(−dp/dz)</text>
        <text x="400" y="112" fill="{TEXT_DIM}" font-size="12">independent of K, n.</text>
        <text x="400" y="140" fill="{TEXT}" font-size="13">Kinematics change: u_max/u_avg = (3n+1)/(n+1)</text>
        <text x="400" y="168" fill="{TEXT_DIM}" font-size="12">n=1 → 2 (Hagen–Poiseuille). n→0 → flatter core.</text>
        <text x="400" y="196" fill="{TEXT_DIM}" font-size="12">Re_MR &lt; ~2100: f_D = 64/Re_MR.</text>
    </svg>
    """

