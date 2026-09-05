"""Textbook-grade SVG vector diagram generators for Fluid Mechanics.

Generates responsive, self-contained SVG graphics with crisp arrows,
dimension markers, fluid elements, and mathematical annotations.
All diagrams use colors defined in src/theme.py.
"""

import hashlib
import re
from html import escape

import streamlit as st
from src.theme import (
    SURFACE, SURFACE_RAISED, BORDER, BORDER_STRONG,
    TEXT, TEXT_MUTED, TEXT_DIM, TEXT_FAINT, ACCENT, PRESSURE, SHEAR, VORTICITY,
    SUCCESS, WARNING, INERTIA, VISCOUS, rgba
)

def clean_svg(svg: str) -> str:
    """Flatten an SVG string to a single line without indentation or blank lines.
    
    Prevents markdown parsers from treating indented XML tags as code blocks.
    """
    # Keep separators between attributes split across source lines. Joining with
    # an empty string produces invalid XML such as height="240"xmlns="...".
    return " ".join(line.strip() for line in svg.splitlines() if line.strip())

def render_svg(svg: str, caption: str = ""):
    """Render vector art through Streamlit's image API, outside HTML sanitization."""
    cleaned = clean_svg(svg)
    # Inline SVGs share the page's ID namespace. Isolate markers and clip paths.
    prefix = "fig-" + hashlib.sha256(cleaned.encode()).hexdigest()[:10] + "-"
    ids = re.findall(r'id="([^"]+)"', cleaned)
    for identifier in ids:
        cleaned = cleaned.replace(f'id="{identifier}"', f'id="{prefix}{identifier}"')
        cleaned = cleaned.replace(f'url(#{identifier})', f'url(#{prefix}{identifier})')
    title_match = re.search(r'<text\b[^>]*>(.*?)</text>', cleaned)
    title = re.sub(r'<[^>]+>', '', title_match.group(1)) if title_match else "Fluid mechanics schematic"
    description = caption or "Schematic; not to scale. Read the arrows and labels with the explanation below."
    cleaned = cleaned.replace('<svg ', f'<svg role="img" aria-label="{escape(title, quote=True)}" ', 1)
    cleaned = cleaned.replace('</svg>', f'<desc>{escape(description)}</desc></svg>')
    # The HTML sanitizer removes inline SVG and SVG data URLs. st.image has a
    # dedicated SVG path and does not route image content through that sanitizer.
    with st.container(key=prefix.rstrip("-")):
        st.image(cleaned, width="stretch")
    st.caption(description + " On a narrow screen, scroll the diagram horizontally.")

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
        <marker id="arrow-green" viewBox="0 0 10 10" refX="6" refY="5"
                markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="{SUCCESS}"/>
        </marker>
        <marker id="arrow-purple" viewBox="0 0 10 10" refX="6" refY="5"
                markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="{VORTICITY}"/>
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

def diagram_energy_budget() -> str:
    """A consistent illustrative reservoir-to-reservoir head balance."""
    return f'''
    <svg viewBox="0 0 820 390" width="100%" height="390" xmlns="http://www.w3.org/2000/svg"
         style="background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; font-family: sans-serif;">
      {_arrow_defs()}
      <text x="28" y="34" fill="{TEXT}" font-size="18" font-weight="600">Follow one kilogram of water</text>
      <text x="28" y="57" fill="{TEXT_MUTED}" font-size="13">Two open reservoirs · steady transfer · negligible speed at the free surfaces</text>
      <path d="M 48 100 V 212 H 170 V 100" fill="none" stroke="{TEXT_DIM}" stroke-width="2"/>
      <path d="M 49 151 H 169 V 211 H 49 Z" fill="{rgba(ACCENT,.15)}"/>
      <line x1="49" y1="151" x2="169" y2="151" stroke="{ACCENT}" stroke-width="2"/>
      <text x="62" y="137" fill="{ACCENT}" font-size="14">1 · z = 0 m</text>
      <path d="M 635 78 V 142 H 770 V 78" fill="none" stroke="{TEXT_DIM}" stroke-width="2"/>
      <path d="M 636 105 H 769 V 141 H 636 Z" fill="{rgba(ACCENT,.15)}"/>
      <line x1="636" y1="105" x2="769" y2="105" stroke="{ACCENT}" stroke-width="2"/>
      <text x="644" y="94" fill="{ACCENT}" font-size="14">2 · z = 10 m</text>
      <path d="M 170 186 H 265 M 325 186 H 568 V 127 H 635" fill="none" stroke="{ACCENT}" stroke-width="5"/>
      <circle cx="295" cy="186" r="30" fill="{SURFACE_RAISED}" stroke="{SUCCESS}" stroke-width="2"/>
      <path d="M 282 170 L 312 186 L 282 202 Z" fill="{SUCCESS}"/>
      <line x1="370" y1="186" x2="438" y2="186" stroke="{TEXT}" stroke-width="2" marker-end="url(#arrow-dim)"/>
      <text x="255" y="239" fill="{SUCCESS}" font-size="14">Pump adds 15 m</text>
      <text x="418" y="163" fill="{SHEAR}" font-size="14">Pipe + fittings lose 5 m</text>
      <text x="33" y="278" fill="{TEXT}" font-size="15" font-weight="600">Head budget: 15 m added = 10 m elevation + 5 m dissipated</text>
      <rect x="33" y="296" width="500" height="32" rx="4" fill="{ACCENT}"/>
      <rect x="533" y="296" width="250" height="32" rx="4" fill="{SHEAR}"/>
      <text x="185" y="317" fill="#0f172a" font-size="14" font-weight="600">Elevation: 10 m</text>
      <text x="580" y="317" fill="#0f172a" font-size="14" font-weight="600">Losses: 5 m</text>
      <text x="33" y="355" fill="{TEXT_MUTED}" font-size="13">Both surfaces have the same pressure. Their pressure heads cancel in the balance.</text>
      <text x="33" y="376" fill="{TEXT_MUTED}" font-size="13">Loss of mechanical energy does not mean loss of total energy: dissipation raises internal energy.</text>
    </svg>'''


def diagram_model_selection() -> str:
    """Connect an engineering question to the model and checks it needs."""
    rows = [
        ("Pressure drop in a long pipe", "Head balance + friction factor", "Check regime, entry length, fittings", ACCENT),
        ("Acceleration through a nozzle", "Continuity + Euler / Bernoulli", "Check losses and compressibility", SUCCESS),
        ("Shear near a moving wall", "Viscous momentum + no slip", "Check geometry and constitutive law", SHEAR),
        ("Recirculation in a cavity", "Numerical Navier–Stokes", "Check mass, grid, time, benchmark", VORTICITY),
    ]
    body = ""
    for i, (question, model, check, color) in enumerate(rows):
        y = 94 + 65 * i
        body += f'<rect x="20" y="{y-24}" width="780" height="54" rx="6" fill="{rgba(color,.07)}" stroke="{BORDER}"/>'
        for x, label in ((34, question), (291, model), (545, check)):
            body += f'<text x="{x}" y="{y+7}" fill="{color if x == 291 else TEXT_MUTED}" font-size="12">{escape(label)}</text>'
    return f'''<svg viewBox="0 0 820 352" width="100%" height="352" xmlns="http://www.w3.org/2000/svg"
      style="background: {SURFACE}; border-radius: 12px; border: 1px solid {BORDER}; font-family: sans-serif;">
      <text x="28" y="32" fill="{TEXT}" font-size="18" font-weight="600">Choose the model by the question</text>
      <text x="34" y="57" fill="{ACCENT}" font-size="11">WHAT DO YOU NEED?</text>
      <text x="291" y="57" fill="{ACCENT}" font-size="11">START WITH</text>
      <text x="545" y="57" fill="{ACCENT}" font-size="11">BEFORE TRUSTING THE ANSWER</text>
      {body}
      <text x="28" y="336" fill="{TEXT_DIM}" font-size="12">All four conserve mass and momentum. The assumptions decide which terms and details remain.</text>
    </svg>'''


def diagram_continuity_streamtube() -> str:
    """Steady 1D mass conservation through a contracting streamtube."""
    return f"""
    <svg viewBox="0 0 740 240" width="100%" height="240" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="32" fill="{ACCENT}" font-size="15" font-weight="bold">Steady mass conservation (continuity)</text>
        <text x="24" y="52" fill="{TEXT_DIM}" font-size="12">Same density, smaller area: the mean speed must increase to carry the same flow rate.</text>
        <path d="M 80 75 L 250 75 L 470 105 L 620 105 L 620 155 L 470 155 L 250 185 L 80 185 Z" fill="{rgba(ACCENT, 0.12)}" stroke="{ACCENT}" stroke-width="2"/>
        <line x1="40" y1="130" x2="160" y2="130" stroke="{SUCCESS}" stroke-width="3" marker-end="url(#arrow-sky)"/>
        <line x1="480" y1="130" x2="700" y2="130" stroke="{SUCCESS}" stroke-width="4" marker-end="url(#arrow-sky)"/>
        <text x="90" y="122" fill="{SUCCESS}" font-size="13" font-weight="600">u1</text>
        <text x="88" y="200" fill="{TEXT_MUTED}" font-size="13">A1</text>
        <text x="640" y="122" fill="{SUCCESS}" font-size="13" font-weight="600">u2 &gt; u1</text>
        <text x="600" y="214" fill="{TEXT_MUTED}" font-size="13">A2 &lt; A1</text>
        <text x="200" y="230" fill="{TEXT}" font-size="14" font-family="'JetBrains Mono', monospace">rho A1 u1 = rho A2 u2  (steady)</text>
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
        <text x="570" y="28" fill="{TEXT_DIM}" font-size="13" font-style="italic">Streamtube axis s</text>
        <line x1="640" y1="37" x2="660" y2="94" stroke="{BORDER_STRONG}" stroke-width="1" />
        
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
            <text x="-95" y="75" fill="{TEXT_DIM}" font-size="11">Upstream force</text>

            <!-- Right Pressure Force (p + dp/dx dx)*A -->
            <line x1="290" y1="42" x2="226" y2="42" stroke="{PRESSURE}" stroke-width="3" marker-end="url(#arrow-red)" />
            <text x="235" y="30" fill="{PRESSURE}" font-size="13" font-weight="bold">(p + ∂p/∂x·dx) · A</text>
            <text x="235" y="75" fill="{TEXT_DIM}" font-size="11">Downstream force</text>
            
            <!-- Dimension dx -->
            <line x1="0" y1="105" x2="220" y2="105" stroke="{TEXT_DIM}" stroke-width="1.2"
                  marker-start="url(#arrow-dim)" marker-end="url(#arrow-dim)" />
            <line x1="0" y1="85" x2="0" y2="115" stroke="{BORDER_STRONG}" stroke-width="1" />
            <line x1="220" y1="85" x2="220" y2="115" stroke="{BORDER_STRONG}" stroke-width="1" />
            <text x="130" y="130" fill="{TEXT_MUTED}" font-size="13" font-weight="600">dx</text>
            
            <!-- Flow Acceleration Arrow -->
            <line x1="60" y1="-30" x2="160" y2="-30" stroke="{SUCCESS}" stroke-width="2.5" marker-end="url(#arrow-sky)" />
            <text x="80" y="-40" fill="{SUCCESS}" font-size="12" font-weight="600">a = Du/Dt</text>
        </g>
        
        <!-- Gravity Vector (vertical downward from center) -->
        <g transform="translate(356, 119)">
            <line x1="0" y1="0" x2="0" y2="150" stroke="{SHEAR}" stroke-width="2.5" marker-end="url(#arrow-orange)" />
            <text x="16" y="135" fill="{SHEAR}" font-size="12" font-weight="bold">W = dm · g</text>
            
            <!-- Along-streamline component -->
            <line x1="0" y1="0" x2="-45" y2="9" stroke="{SHEAR}" stroke-width="1.5" stroke-dasharray="4,3" />
            <text x="-150" y="180" fill="{SHEAR}" font-size="12">Along the tube: −dm g sin(θ) = −dm g (dz/dx)</text>
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
        <g transform="translate(95, 340)">
            <line x1="0" y1="0" x2="-50" y2="25" stroke="{BORDER_STRONG}" stroke-width="2" marker-end="url(#arrow-dim)" />
            <text x="-60" y="32" fill="{TEXT_DIM}" font-size="12">x</text>
            <line x1="0" y1="0" x2="60" y2="-15" stroke="{BORDER_STRONG}" stroke-width="2" marker-end="url(#arrow-dim)" />
            <text x="68" y="-12" fill="{TEXT_DIM}" font-size="12">y</text>
            <line x1="0" y1="0" x2="0" y2="-60" stroke="{BORDER_STRONG}" stroke-width="2" marker-end="url(#arrow-dim)" />
            <text x="-5" y="-68" fill="{TEXT_DIM}" font-size="12">z</text>
        </g>
        
        <g transform="translate(0, 80)">
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
        <text x="240" y="95" fill="{SHEAR}" font-size="12" font-weight="bold">τ_zx</text>
        
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
        
        </g>
        <!-- Symmetry note box (bottom right) -->
        <rect x="490" y="270" width="225" height="95" rx="6" fill="{SURFACE_RAISED}" stroke="{BORDER}" />
        <text x="505" y="295" fill="{SUCCESS}" font-size="12" font-weight="bold">Angular Momentum Balance:</text>
        <text x="505" y="315" fill="{TEXT_MUTED}" font-size="12">Absence of point body couples</text>
        <text x="505" y="335" fill="{ACCENT}" font-size="13" font-family="'JetBrains Mono', monospace">
            τ_xy = τ_yx,  τ_xz = τ_zx
        </text>
        <text x="505" y="352" fill="{TEXT_DIM}" font-size="11">6 independent components</text>
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
        <text x="35" y="240" fill="{ACCENT}" font-size="11">Viscous stress = 0</text>
        
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
        <polygon points="412,112 457,128 473,173 428,157" fill="{rgba(SHEAR, 0.2)}" stroke="{SHEAR}" stroke-width="2" />
        <text x="385" y="225" fill="{SHEAR}" font-size="11" font-family="'JetBrains Mono', monospace">½(∂u/∂y + ∂v/∂x)</text>
        <text x="385" y="242" fill="{TEXT_DIM}" font-size="11">Generates shear stress</text>
        
        <!-- 4. Rigid-Body Rotation -->
        <rect x="555" y="15" width="170" height="250" rx="6" fill="{SURFACE_RAISED}" stroke="{BORDER}" />
        <text x="565" y="38" fill="{TEXT}" font-size="12" font-weight="bold">4. Rigid Rotation</text>
        <text x="565" y="55" fill="{TEXT_DIM}" font-size="11">Anti-symmetric spin Ω_xy</text>
        <!-- Square rotating without changing angles -->
        <rect x="610" y="120" width="45" height="45" fill="none" stroke="{BORDER_STRONG}" stroke-dasharray="3,3" />
        <g transform="translate(632, 142) rotate(22)">
            <rect x="-22" y="-22" width="44" height="44" fill="{rgba(VORTICITY, 0.2)}" stroke="{VORTICITY}" stroke-width="2" />
        </g>
        <text x="565" y="225" fill="{VORTICITY}" font-size="11" font-family="'JetBrains Mono', monospace">½(∂v/∂x - ∂u/∂y)</text>
        <text x="565" y="242" fill="{SUCCESS}" font-size="11" font-weight="bold">Viscous stress = 0</text>
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
        <text x="535" y="130" fill="{SUCCESS}" font-size="11" font-weight="bold">Check the residual ∇·uⁿ⁺¹</text>
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
    turbulent_path = "M " + " L ".join(
        f"{485 + 145 * (1 - abs((y - 150) / 60)) ** (1 / 7):.2f},{y}"
        for y in range(90, 211)
    )
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
        <path d="M 120 90 Q 440 150 120 210" fill="none" stroke="{SUCCESS}" stroke-width="3" />
        <!-- Velocity arrows -->
        <line x1="120" y1="150" x2="275" y2="150" stroke="{SUCCESS}" stroke-width="2" marker-end="url(#arrow-sky)" />
        <line x1="120" y1="120" x2="235" y2="120" stroke="{SUCCESS}" stroke-width="1.5" marker-end="url(#arrow-sky)" />
        <line x1="120" y1="180" x2="235" y2="180" stroke="{SUCCESS}" stroke-width="1.5" marker-end="url(#arrow-sky)" />
        
        <text x="40" y="240" fill="{TEXT_MUTED}" font-size="12">u_avg / u_max = <tspan font-weight="bold">0.50</tspan> (Parabolic profile)</text>
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
        <path d="{turbulent_path}" fill="none" stroke="{PRESSURE}" stroke-width="3" />
        <!-- Velocity arrows -->
        <line x1="485" y1="150" x2="625" y2="150" stroke="{PRESSURE}" stroke-width="2" marker-end="url(#arrow-red)" />
        <line x1="485" y1="120" x2="615" y2="120" stroke="{PRESSURE}" stroke-width="1.5" marker-end="url(#arrow-red)" />
        <line x1="485" y1="180" x2="615" y2="180" stroke="{PRESSURE}" stroke-width="1.5" marker-end="url(#arrow-red)" />
        
        <text x="405" y="240" fill="{TEXT_MUTED}" font-size="12">u_avg / u_max ≈ <tspan font-weight="bold">0.82</tspan> (Blunt core)</text>
        <text x="405" y="260" fill="{PRESSURE}" font-size="12">Wall shear needs the near-wall model.</text>
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
        <text x="240" y="185" fill="{TEXT_MUTED}" font-size="12">u⁺ ≈ y⁺; molecular viscous stress dominates</text>
        
        <!-- 2. Buffer layer: 5 <= y+ <= 30 -->
        <rect x="40" y="125" width="660" height="40" fill="{rgba(SHEAR, 0.15)}" stroke="{SHEAR}" stroke-width="1" stroke-dasharray="3,3" />
        <text x="55" y="150" fill="{SHEAR}" font-size="12" font-weight="bold">2. Buffer Layer (5 ≤ y⁺ ≤ 30):</text>
        <text x="240" y="150" fill="{TEXT_MUTED}" font-size="12">Viscous and turbulent stresses are both important</text>
        
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
        <text x="50" y="250" fill="{TEXT}" font-size="12">NPSH_A must exceed NPSH_R with a suitable margin; equality is not a no-cavitation guarantee.</text>
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
        <path d="M 80 200 Q 250 195 340 48" fill="none" stroke="{PRESSURE}" stroke-width="2.5"/>
        <text x="200" y="55" fill="{PRESSURE}" font-size="12">n &gt; 1 thickening</text>
        <text x="400" y="90" fill="{TEXT}" font-size="13">Pipe momentum: τ_w = (R/2)(−dp/dz)</text>
        <text x="400" y="112" fill="{TEXT_DIM}" font-size="12">independent of K, n.</text>
        <text x="400" y="140" fill="{TEXT}" font-size="13">u_max/u_avg = (3n+1)/(n+1)</text>
        <text x="400" y="164" fill="{TEXT_DIM}" font-size="12">n = 1: ratio 2 (Hagen–Poiseuille).</text>
        <text x="400" y="181" fill="{TEXT_DIM}" font-size="12">Smaller n gives a flatter core.</text>
        <text x="400" y="196" fill="{TEXT_DIM}" font-size="12">Re_MR &lt; ~2100: f_D = 64/Re_MR.</text>
    </svg>
    """


# =============================================================================
# Blasius: the scaling argument and the similarity collapse
# =============================================================================

def diagram_blasius_scaling() -> str:
    """Prandtl's order-of-magnitude balance, drawn as a competition of two terms."""
    return f"""
    <svg viewBox="0 0 780 400" width="100%" height="400" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="28" fill="{ACCENT}" font-size="15" font-weight="bold">Why &#948; &#8764; &#8730;(&#957;x/U) &#183; the whole boundary layer in one balance</text>
        <text x="24" y="48" fill="{TEXT_DIM}" font-size="12">Not a derivation of the profile &#8212; a derivation of its thickness, from two terms that must be the same size.</text>

        <rect x="34" y="72" width="340" height="128" rx="8" fill="{rgba(INERTIA, 0.10)}" stroke="{INERTIA}" stroke-width="1.6"/>
        <text x="50" y="98" fill="{INERTIA}" font-size="13.5" font-weight="700">Inertia: carrying momentum downstream</text>
        <text x="50" y="126" fill="{TEXT}" font-size="14" font-family="'JetBrains Mono', monospace">u &#8706;u/&#8706;x  &#8764;  U &#183; U/x  =  U&#178;/x</text>
        <text x="50" y="152" fill="{TEXT_DIM}" font-size="11.5">Speed changes from 0 to U over the streamwise length x,</text>
        <text x="50" y="170" fill="{TEXT_DIM}" font-size="11.5">while the parcel itself travels at about U.</text>
        <text x="50" y="190" fill="{TEXT_DIM}" font-size="11.5">The long direction sets this scale.</text>

        <rect x="406" y="72" width="340" height="128" rx="8" fill="{rgba(VISCOUS, 0.10)}" stroke="{VISCOUS}" stroke-width="1.6"/>
        <text x="422" y="98" fill="{VISCOUS}" font-size="13.5" font-weight="700">Viscosity: diffusing it away from the wall</text>
        <text x="422" y="126" fill="{TEXT}" font-size="14" font-family="'JetBrains Mono', monospace">&#957; &#8706;&#178;u/&#8706;y&#178;  &#8764;  &#957; U/&#948;&#178;</text>
        <text x="422" y="152" fill="{TEXT_DIM}" font-size="11.5">The same change from 0 to U, but across the thin</text>
        <text x="422" y="170" fill="{TEXT_DIM}" font-size="11.5">direction &#948;. Two derivatives means &#948; is squared &#8212;</text>
        <text x="422" y="190" fill="{TEXT_DIM}" font-size="11.5">which is why a thin layer wins so decisively.</text>

        <line x1="374" y1="136" x2="406" y2="136" stroke="{WARNING}" stroke-width="2.5"/>
        <text x="378" y="128" fill="{WARNING}" font-size="18" font-weight="700">&#8776;</text>

        <rect x="140" y="226" width="500" height="66" rx="8" fill="{rgba(SUCCESS, 0.12)}" stroke="{SUCCESS}" stroke-width="2"/>
        <text x="164" y="256" fill="{TEXT}" font-size="15" font-family="'JetBrains Mono', monospace">U&#178;/x &#8776; &#957;U/&#948;&#178;   &#8658;   &#948;&#178; &#8776; &#957;x/U   &#8658;   &#948; &#8776; &#8730;(&#957;x/U)</text>
        <text x="164" y="280" fill="{SUCCESS}" font-size="13" font-weight="600">&#948;/x &#8776; 1/&#8730;Re&#8339;   &#8212; the layer is thin exactly when Re&#8339; is large</text>

        <text x="34" y="326" fill="{TEXT}" font-size="12.5">Three consequences follow before any equation is solved:</text>
        <text x="34" y="348" fill="{TEXT_DIM}" font-size="12">&#183; &#948; grows like &#8730;x, not like x. Doubling the distance thickens the layer by only 41%.</text>
        <text x="34" y="368" fill="{TEXT_DIM}" font-size="12">&#183; Higher Re makes the layer *thinner*, never absent: viscosity is never negligible at the wall itself.</text>
        <text x="34" y="388" fill="{TEXT_DIM}" font-size="12">&#183; &#948; &#8810; x justifies dropping &#8706;&#178;u/&#8706;x&#178; against &#8706;&#178;u/&#8706;y&#178;, and makes &#8706;p/&#8706;y &#8776; 0 &#8212; the two approximations that reduce Navier&#8211;Stokes to Prandtl.</text>
    </svg>
    """


def diagram_blasius_similarity() -> str:
    """Three stations, three different curves, one universal shape after rescaling."""
    return f"""
    <svg viewBox="0 0 780 400" width="100%" height="400" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="28" fill="{ACCENT}" font-size="15" font-weight="bold">Similarity: three profiles become one</text>
        <text x="24" y="48" fill="{TEXT_DIM}" font-size="12">The plate has no built-in length, so the only thickness available is &#8730;(&#957;x/U). Measure y in those units and the station label disappears.</text>

        <text x="60" y="84" fill="{TEXT_MUTED}" font-size="13" font-weight="600">Raw: u(y) at three stations</text>
        <line x1="70" y1="300" x2="330" y2="300" stroke="{TEXT}" stroke-width="2.5"/>
        <text x="150" y="322" fill="{TEXT_MUTED}" font-size="11.5">plate wall</text>
        <line x1="70" y1="300" x2="70" y2="100" stroke="{TEXT_MUTED}" stroke-width="1.4"/>
        <text x="34" y="106" fill="{TEXT_DIM}" font-size="11.5">y</text>

        <path d="M 100 300 Q 106 262 118 240" fill="none" stroke="{ACCENT}" stroke-width="2.4"/>
        <text x="104" y="232" fill="{ACCENT}" font-size="11">x&#8321;</text>
        <path d="M 180 300 Q 194 240 216 200" fill="none" stroke="{SHEAR}" stroke-width="2.4"/>
        <text x="200" y="192" fill="{SHEAR}" font-size="11">x&#8322; = 4x&#8321;</text>
        <path d="M 270 300 Q 292 218 322 158" fill="none" stroke="{VORTICITY}" stroke-width="2.4"/>
        <text x="296" y="150" fill="{VORTICITY}" font-size="11">x&#8323; = 9x&#8321;</text>
        <text x="80" y="348" fill="{TEXT_DIM}" font-size="11.5">Thicknesses in the ratio 1 : 2 : 3,</text>
        <text x="80" y="366" fill="{TEXT_DIM}" font-size="11.5">because &#948; &#8733; &#8730;x.</text>

        <line x1="360" y1="90" x2="360" y2="370" stroke="{BORDER_STRONG}" stroke-width="1.4" stroke-dasharray="6,5"/>
        <text x="372" y="196" fill="{WARNING}" font-size="13" font-weight="700">&#951; = y&#8730;(U/&#957;x)</text>
        <line x1="372" y1="210" x2="424" y2="210" stroke="{WARNING}" stroke-width="2.2" marker-end="url(#arrow-orange)"/>

        <text x="470" y="84" fill="{TEXT_MUTED}" font-size="13" font-weight="600">Rescaled: one curve f&#8242;(&#951;)</text>
        <line x1="470" y1="300" x2="730" y2="300" stroke="{TEXT}" stroke-width="2.5"/>
        <line x1="470" y1="300" x2="470" y2="100" stroke="{TEXT_MUTED}" stroke-width="1.4"/>
        <text x="444" y="106" fill="{TEXT_DIM}" font-size="11.5">&#951;</text>
        <text x="700" y="322" fill="{TEXT_DIM}" font-size="11.5">u/U</text>
        <path d="M 470 300 C 500 296 540 268 566 214 C 586 172 594 140 596 118" fill="none" stroke="{SUCCESS}" stroke-width="3.2"/>
        <line x1="596" y1="118" x2="596" y2="100" stroke="{SUCCESS}" stroke-width="3.2" stroke-dasharray="4,4"/>
        <line x1="596" y1="112" x2="700" y2="112" stroke="{TEXT_FAINT}" stroke-width="1.2" stroke-dasharray="5,4"/>
        <text x="614" y="106" fill="{TEXT_MUTED}" font-size="11.5">u/U &#8594; 1</text>
        <circle cx="596" cy="118" r="4" fill="{SUCCESS}"/>
        <text x="540" y="330" fill="{SUCCESS}" font-size="12" font-weight="600">&#951; &#8776; 4.91 where u = 0.99U</text>
        <text x="470" y="352" fill="{TEXT_DIM}" font-size="11.5">All three collapse. The PDE in (x, y) has become</text>
        <text x="470" y="370" fill="{TEXT_DIM}" font-size="11.5">an ODE in &#951; alone: f&#8243;&#8242; + &#189; f f&#8243; = 0.</text>
    </svg>
    """


# =============================================================================
# Open channels: cross-section, uniform-flow force balance, flood freeboard
# =============================================================================

def diagram_canal_section() -> str:
    """Trapezoidal canal cross-section with every symbol the calculator uses."""
    return f"""
    <svg viewBox="0 0 780 420" width="100%" height="420" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="28" fill="{ACCENT}" font-size="15" font-weight="bold">Trapezoidal canal &#183; cross-section looking downstream</text>
        <text x="24" y="48" fill="{TEXT_DIM}" font-size="12">Side slope z is the horizontal run per unit rise: a 2:1 bank has z = 2. The free surface is NOT part of the wetted perimeter.</text>

        <path d="M 150 320 L 630 320 L 690 200 L 90 200 Z" fill="{rgba(ACCENT, 0.20)}" stroke="none"/>
        <line x1="90" y1="200" x2="690" y2="200" stroke="{ACCENT}" stroke-width="2.5"/>
        <text x="300" y="192" fill="{ACCENT}" font-size="12.5" font-weight="600">free surface &#183; top width T = b + 2zy</text>

        <path d="M 120 260 L 150 320 L 630 320 L 660 260" fill="none" stroke="{SHEAR}" stroke-width="4"/>
        <path d="M 60 140 L 150 320 L 630 320 L 720 140" fill="none" stroke="{TEXT_MUTED}" stroke-width="2.5"/>
        <text x="250" y="344" fill="{SHEAR}" font-size="12.5" font-weight="700">wetted perimeter P<tspan dy="3" font-size="9">w</tspan><tspan dy="-3"></tspan> = b + 2y&#8730;(1+z&#178;) &#183; the only surface carrying shear</text>

        <line x1="150" y1="352" x2="630" y2="352" stroke="{SUCCESS}" stroke-width="1.8" marker-start="url(#arrow-dim)" marker-end="url(#arrow-dim)"/>
        <text x="356" y="372" fill="{SUCCESS}" font-size="13" font-weight="700">bottom width b</text>

        <line x1="700" y1="320" x2="700" y2="200" stroke="{WARNING}" stroke-width="1.8" marker-start="url(#arrow-dim)" marker-end="url(#arrow-dim)"/>
        <text x="710" y="264" fill="{WARNING}" font-size="13" font-weight="700">y</text>
        <text x="708" y="282" fill="{TEXT_DIM}" font-size="11">depth</text>

        <line x1="740" y1="200" x2="740" y2="140" stroke="{PRESSURE}" stroke-width="1.8" marker-start="url(#arrow-dim)" marker-end="url(#arrow-dim)"/>
        <text x="700" y="130" fill="{PRESSURE}" font-size="12.5" font-weight="700">freeboard</text>
        <line x1="60" y1="140" x2="720" y2="140" stroke="{PRESSURE}" stroke-width="2" stroke-dasharray="8,5"/>
        <text x="70" y="132" fill="{PRESSURE}" font-size="12.5" font-weight="600">top of bank &#8212; above this the canal overtops</text>

        <path d="M 690 200 L 660 200 L 660 260" fill="none" stroke="{VORTICITY}" stroke-width="1.6"/>
        <text x="600" y="228" fill="{VORTICITY}" font-size="12" font-weight="600">1 vertical</text>
        <text x="600" y="246" fill="{VORTICITY}" font-size="12" font-weight="600">z horizontal</text>

        <text x="34" y="404" fill="{TEXT_DIM}" font-size="12">A = y(b + zy) &#183; R&#8341; = A/P<tspan dy="3" font-size="9">w</tspan><tspan dy="-3"></tspan> &#183; D&#8341; = 4R&#8341; &#8212; the same hydraulic diameter chapter 2.4 uses for a duct, which is why one friction factor serves both.</text>
    </svg>
    """


def diagram_canal_uniform_flow() -> str:
    """Longitudinal view: the bed slope IS the driving head."""
    # There is no Unicode subscript "w", so the wall subscript is a tspan.
    w = '<tspan dy="3" font-size="9">w</tspan><tspan dy="-3"></tspan>'
    return f"""
    <svg viewBox="0 0 780 452" width="100%" height="452" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="28" fill="{ACCENT}" font-size="15" font-weight="bold">Uniform (normal) flow &#183; gravity along the slope balances wall shear</text>
        <text x="24" y="48" fill="{TEXT_DIM}" font-size="12">Depth is constant along the channel, so the bed, the water surface and the energy grade line are all parallel: S&#8320; = S&#8348; = S&#8337;.</text>

        <line x1="60" y1="96" x2="720" y2="180" stroke="{PRESSURE}" stroke-width="2" stroke-dasharray="9,5"/>
        <text x="440" y="142" fill="{PRESSURE}" font-size="12" font-weight="600">energy grade line, slope S&#8337;</text>
        <line x1="60" y1="132" x2="720" y2="216" stroke="{ACCENT}" stroke-width="2.5"/>
        <text x="470" y="180" fill="{ACCENT}" font-size="12" font-weight="600">water surface, slope S&#8348;</text>
        <path d="M 60 132 L 720 216 L 720 296 L 60 212 Z" fill="{rgba(ACCENT, 0.16)}"/>
        <line x1="60" y1="212" x2="720" y2="296" stroke="{SHEAR}" stroke-width="4"/>
        <text x="470" y="290" fill="{SHEAR}" font-size="12" font-weight="600">bed, slope S&#8320;</text>

        <line x1="60" y1="96" x2="60" y2="212" stroke="{TEXT_FAINT}" stroke-width="1.2" stroke-dasharray="4,4"/>
        <line x1="720" y1="180" x2="720" y2="296" stroke="{TEXT_FAINT}" stroke-width="1.2" stroke-dasharray="4,4"/>
        <text x="66" y="88" fill="{TEXT_DIM}" font-size="11">velocity head V&#178;/2g</text>

        <line x1="150" y1="143" x2="150" y2="223" stroke="{WARNING}" stroke-width="1.8" marker-start="url(#arrow-dim)" marker-end="url(#arrow-dim)"/>
        <text x="130" y="188" fill="{WARNING}" font-size="12.5" font-weight="700">y</text>
        <line x1="630" y1="205" x2="630" y2="285" stroke="{WARNING}" stroke-width="1.8" marker-start="url(#arrow-dim)" marker-end="url(#arrow-dim)"/>
        <text x="640" y="248" fill="{WARNING}" font-size="12.5" font-weight="700">y</text>

        <line x1="310" y1="180" x2="410" y2="193" stroke="{SUCCESS}" stroke-width="3" marker-end="url(#arrow-green)"/>
        <text x="246" y="177" fill="{SUCCESS}" font-size="12.5" font-weight="700">&#961;gAL&#183;S&#8320;</text>
        <line x1="410" y1="219" x2="310" y2="206" stroke="{PRESSURE}" stroke-width="3" marker-end="url(#arrow-red)"/>
        <text x="238" y="224" fill="{PRESSURE}" font-size="12.5" font-weight="700">&#964;{w}P{w}L</text>

        <text x="24" y="326" fill="{TEXT_DIM}" font-size="11.5">Green drives (the component of the water&#8217;s weight along the slope); red resists (shear on the wetted wall). The depth is the same at both stations &#8212; that is</text>
        <text x="24" y="342" fill="{TEXT_DIM}" font-size="11.5">exactly what &#8220;uniform&#8221; means, and it is why the two must cancel exactly.</text>

        <rect x="130" y="360" width="530" height="52" rx="8" fill="{rgba(SUCCESS, 0.12)}" stroke="{SUCCESS}" stroke-width="1.6"/>
        <text x="158" y="392" fill="{TEXT}" font-size="14.5" font-family="'JetBrains Mono', monospace">&#961;gALS&#8320; = &#964;{w}P{w}L   &#8658;   &#964;{w} = &#961;gR&#8341;S&#8320;</text>

        <text x="24" y="438" fill="{TEXT_DIM}" font-size="11.5">Same form as &#964;{w} = (D/4)(&#8722;dp/dx) in a pipe, with the pressure gradient replaced by the bed slope and D/4 replaced by R&#8341;. That is the whole reason D&#8341; = 4R&#8341;.</text>
    </svg>
    """


# =============================================================================
# Cryogenic air separation: where the compressor and the expander sit
# =============================================================================

def diagram_asu_flowsheet() -> str:
    """Linde-type double-column air separation unit, drawn as an energy story."""
    box = f'fill="{SURFACE_RAISED}" stroke="{BORDER_STRONG}" stroke-width="1.6" rx="6"'
    return f"""
    <svg viewBox="0 0 900 470" width="100%" height="470" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="28" fill="{ACCENT}" font-size="15" font-weight="bold">Cryogenic air separation (Linde double column) &#183; the turbomachinery in context</text>
        <text x="24" y="48" fill="{TEXT_DIM}" font-size="12">Air in at ambient, oxygen and nitrogen out at &#8722;180&#176;C. Every joule of cold in this plant is paid for by the compressors and released by the expander.</text>

        <line x1="26" y1="140" x2="72" y2="140" stroke="{ACCENT}" stroke-width="3" marker-end="url(#arrow-sky)"/>
        <text x="26" y="130" fill="{TEXT_MUTED}" font-size="11.5">air, 1 atm, 20&#176;C</text>

        <rect x="76" y="112" width="104" height="58" {box}/>
        <text x="90" y="136" fill="{PRESSURE}" font-size="12.5" font-weight="700">MAC</text>
        <text x="90" y="152" fill="{TEXT_DIM}" font-size="10.5">main air compr.</text>
        <text x="90" y="164" fill="{TEXT_DIM}" font-size="10.5">3&#8211;4 stages, ~6 bar</text>

        <line x1="180" y1="141" x2="212" y2="141" stroke="{ACCENT}" stroke-width="2.6" marker-end="url(#arrow-sky)"/>
        <rect x="216" y="112" width="96" height="58" {box}/>
        <text x="230" y="136" fill="{ACCENT}" font-size="12.5" font-weight="700">intercoolers</text>
        <text x="230" y="152" fill="{TEXT_DIM}" font-size="10.5">reject the heat of</text>
        <text x="230" y="164" fill="{TEXT_DIM}" font-size="10.5">compression to water</text>

        <line x1="312" y1="141" x2="344" y2="141" stroke="{ACCENT}" stroke-width="2.6" marker-end="url(#arrow-sky)"/>
        <rect x="348" y="112" width="104" height="58" {box}/>
        <text x="362" y="136" fill="{WARNING}" font-size="12.5" font-weight="700">prepurifier</text>
        <text x="362" y="152" fill="{TEXT_DIM}" font-size="10.5">removes H&#8322;O, CO&#8322;,</text>
        <text x="362" y="164" fill="{TEXT_DIM}" font-size="10.5">C&#8322;H&#8322; &#8212; they freeze</text>

        <line x1="452" y1="141" x2="484" y2="141" stroke="{ACCENT}" stroke-width="2.6" marker-end="url(#arrow-sky)"/>
        <rect x="488" y="96" width="120" height="90" {box}/>
        <text x="502" y="124" fill="{SUCCESS}" font-size="12.5" font-weight="700">main exchanger</text>
        <text x="502" y="142" fill="{TEXT_DIM}" font-size="10.5">brazed aluminium,</text>
        <text x="502" y="156" fill="{TEXT_DIM}" font-size="10.5">approach ~2 K</text>
        <text x="502" y="174" fill="{TEXT_DIM}" font-size="10.5">cools 293 K &#8594; ~100 K</text>

        <rect x="76" y="228" width="104" height="58" {box}/>
        <text x="90" y="252" fill="{PRESSURE}" font-size="12.5" font-weight="700">BAC</text>
        <text x="90" y="268" fill="{TEXT_DIM}" font-size="10.5">booster, to ~30 bar</text>
        <text x="90" y="280" fill="{TEXT_DIM}" font-size="10.5">feeds the expander</text>
        <line x1="128" y1="170" x2="128" y2="228" stroke="{ACCENT}" stroke-width="2.2" marker-end="url(#arrow-sky)"/>

        <line x1="180" y1="257" x2="236" y2="257" stroke="{ACCENT}" stroke-width="2.6" marker-end="url(#arrow-sky)"/>
        <rect x="240" y="228" width="128" height="58" fill="{rgba(VORTICITY, 0.16)}" stroke="{VORTICITY}" stroke-width="2.2" rx="6"/>
        <text x="254" y="252" fill="{VORTICITY}" font-size="12.5" font-weight="700">TURBOEXPANDER</text>
        <text x="254" y="268" fill="{TEXT_DIM}" font-size="10.5">radial inflow, ~40 000 rpm</text>
        <text x="254" y="280" fill="{TEXT_DIM}" font-size="10.5">exports work &#8658; makes cold</text>

        <line x1="368" y1="257" x2="424" y2="257" stroke="{VORTICITY}" stroke-width="2.6" marker-end="url(#arrow-purple)"/>
        <text x="374" y="248" fill="{VORTICITY}" font-size="11">cold gas</text>

        <rect x="640" y="76" width="150" height="150" fill="{rgba(ACCENT, 0.10)}" stroke="{ACCENT}" stroke-width="2" rx="6"/>
        <text x="654" y="100" fill="{ACCENT}" font-size="12.5" font-weight="700">LP column ~1.4 bar</text>
        <text x="654" y="118" fill="{TEXT_DIM}" font-size="10.5">GAN overhead, ~77 K</text>
        <text x="654" y="136" fill="{TEXT_DIM}" font-size="10.5">LOX sump, ~90 K</text>
        <rect x="640" y="242" width="150" height="112" fill="{rgba(PRESSURE, 0.10)}" stroke="{PRESSURE}" stroke-width="2" rx="6"/>
        <text x="654" y="266" fill="{PRESSURE}" font-size="12.5" font-weight="700">HP column ~5.5 bar</text>
        <text x="654" y="284" fill="{TEXT_DIM}" font-size="10.5">raises the N&#8322; dew point</text>
        <text x="654" y="300" fill="{TEXT_DIM}" font-size="10.5">enough to boil the LOX</text>
        <text x="654" y="318" fill="{TEXT_DIM}" font-size="10.5">above it</text>
        <rect x="640" y="226" width="150" height="16" fill="{SUCCESS}" fill-opacity="0.30" stroke="{SUCCESS}" stroke-width="1.6"/>
        <text x="796" y="238" fill="{SUCCESS}" font-size="11" font-weight="600">condenser&#8211;reboiler</text>

        <line x1="608" y1="141" x2="640" y2="141" stroke="{ACCENT}" stroke-width="2.6" marker-end="url(#arrow-sky)"/>
        <line x1="424" y1="257" x2="640" y2="257" stroke="{VORTICITY}" stroke-width="2.6" marker-end="url(#arrow-purple)"/>
        <line x1="812" y1="110" x2="866" y2="110" stroke="{ACCENT}" stroke-width="2.6" marker-end="url(#arrow-sky)"/>
        <text x="800" y="100" fill="{ACCENT}" font-size="11.5" font-weight="600">GAN</text>
        <line x1="812" y1="196" x2="866" y2="196" stroke="{WARNING}" stroke-width="2.6" marker-end="url(#arrow-orange)"/>
        <text x="800" y="188" fill="{WARNING}" font-size="11.5" font-weight="600">LOX / GOX</text>

        <rect x="34" y="368" width="836" height="86" rx="8" fill="{rgba(SUCCESS, 0.08)}" stroke="{BORDER_STRONG}" stroke-width="1.4"/>
        <text x="52" y="392" fill="{TEXT}" font-size="12.5" font-weight="600">The energy story, in one line each:</text>
        <text x="52" y="412" fill="{TEXT_DIM}" font-size="11.5">&#183; The compressors do the work. Intercooling exists because compressing cold gas costs less &#8212; w = &#8747;v dp, and v = RT/p.</text>
        <text x="52" y="430" fill="{TEXT_DIM}" font-size="11.5">&#183; The expander makes the cold. It removes energy as shaft work, so the gas cools far more than a valve at the same pressure drop.</text>
        <text x="52" y="448" fill="{TEXT_DIM}" font-size="11.5">&#183; The columns do the separating; they need only the temperature difference the condenser&#8211;reboiler provides. Schematic &#8212; not a design flowsheet.</text>
    </svg>
    """



def _sub(text: str) -> str:
    """A subscript of arbitrary text, as a tspan pair.

    Unicode has subscripts only for digits and a handful of lowercase letters.
    There is none for ``w``, none for capitals, and the entities nearby are
    wildly unrelated -- U+20A2, one past the last subscript letter, is the
    CRUZEIRO SIGN. Reaching for a numeric entity and hoping is how a wall
    subscript becomes a currency symbol, so anything Unicode does not actually
    provide goes through here instead.
    """
    return f'<tspan dy="3" font-size="9">{text}</tspan><tspan dy="-3"></tspan>'


# =============================================================================
# Transport analogy: one equation, three quantities
# =============================================================================

def diagram_transport_analogy() -> str:
    """The same boundary layer, three times, with the diffusivity swapped."""
    d_ab = f"D{_sub('AB')}"
    wall = _sub("w")
    panels = [
        (60, "MOMENTUM", INERTIA, "u", "u/U&#8734;", "&#957; = &#956;/&#961;",
         "&#957; &#8706;&#178;u/&#8706;y&#178;", "no slip: u = 0",
         f"wall shear &#964;{wall}"),
        (330, "HEAT", PRESSURE, "T", "&#952;", "&#945; = k/(&#961;c&#8346;)",
         "&#945; &#8706;&#178;T/&#8706;y&#178;", f"T = T{wall}",
         f"wall flux q{wall}"),
        (600, "SPECIES", SUCCESS, "c", "c*", d_ab,
         f"{d_ab} &#8706;&#178;c/&#8706;y&#178;", f"c = c{wall}",
         f"wall flux N{wall}"),
    ]
    blocks = []
    for x, title, colour, sym, scaled, diff, term, wall_bc, flux in panels:
        blocks.append(f"""
        <rect x="{x}" y="70" width="238" height="212" rx="8" fill="{rgba(colour, 0.07)}" stroke="{colour}" stroke-width="1.6"/>
        <text x="{x + 16}" y="94" fill="{colour}" font-size="12.5" font-weight="700">{title}</text>
        <line x1="{x + 16}" y1="248" x2="{x + 222}" y2="248" stroke="{TEXT}" stroke-width="2.5"/>
        <text x="{x + 16}" y="266" fill="{TEXT_DIM}" font-size="10.5">{wall_bc}</text>
        <path d="M {x + 30} 248 C {x + 44} 214 {x + 66} 196 {x + 96} 190 L {x + 96} 176" fill="none" stroke="{colour}" stroke-width="2.6"/>
        <line x1="{x + 96}" y1="176" x2="{x + 210}" y2="176" stroke="{colour}" stroke-width="1.6" stroke-dasharray="5,4"/>
        <text x="{x + 132}" y="170" fill="{colour}" font-size="11">{scaled} &#8594; 1</text>
        <text x="{x + 26}" y="126" fill="{TEXT}" font-size="11.5" font-family="'JetBrains Mono', monospace">u &#8706;{sym}/&#8706;x + v &#8706;{sym}/&#8706;y</text>
        <text x="{x + 26}" y="145" fill="{TEXT}" font-size="11.5" font-family="'JetBrains Mono', monospace">&#160;&#160;= {term}</text>
        <text x="{x + 122}" y="238" fill="{colour}" font-size="12.5" font-weight="700">{diff}</text>
        <text x="{x + 122}" y="254" fill="{TEXT_DIM}" font-size="10">m&#178;/s</text>
        <text x="{x + 16}" y="{282 + 18}" fill="{TEXT_DIM}" font-size="10.5">gives the {flux}</text>
        """)
    return f"""
    <svg viewBox="0 0 880 440" width="100%" height="440" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="28" fill="{ACCENT}" font-size="15" font-weight="bold">One equation, three transported quantities</text>
        <text x="24" y="48" fill="{TEXT_DIM}" font-size="12">Identical left-hand sides. Identical structure on the right. Only the diffusivity changes &#8212; and all three diffusivities are m&#178;/s.</text>
        {"".join(blocks)}
        <rect x="60" y="312" width="778" height="52" rx="8" fill="{rgba(WARNING, 0.10)}" stroke="{WARNING}" stroke-width="1.6"/>
        <text x="80" y="334" fill="{TEXT}" font-size="12.5">Non-dimensionalise and the only fluid property left is a <tspan font-weight="700">ratio of diffusivities</tspan>:</text>
        <text x="80" y="354" fill="{TEXT}" font-size="13" font-family="'JetBrains Mono', monospace">Pr = &#957;/&#945;&#160;&#160;&#160;&#160;Sc = &#957;/{d_ab}&#160;&#160;&#160;&#160;Le = &#945;/{d_ab} = Sc/Pr</text>
        <text x="24" y="388" fill="{TEXT_DIM}" font-size="11.5">Air: Pr &#8776; 0.71, Sc &#8776; 0.6&#8211;0.7, so Le &#8776; 1 &#8212; heat and species spread at nearly the same rate, and the analogy is excellent.</text>
        <text x="24" y="406" fill="{TEXT_DIM}" font-size="11.5">Water: Pr &#8776; 7, Sc &#8776; 700, so Le &#8776; 100 &#8212; heat outruns species by two orders of magnitude. The analogy still holds; the numbers simply differ.</text>
        <text x="24" y="426" fill="{TEXT_DIM}" font-size="11.5">Liquid metals: Pr &#8776; 0.01 &#8212; heat outruns momentum, the thermal layer is far thicker than the velocity layer, and Pr^(1/3) fits fail.</text>
    </svg>
    """


def diagram_transport_geometries() -> str:
    """Correlation gallery: the same function, six cases, both transport modes."""
    x_sub = "&#8339;"          # U+2093, the real subscript x
    cards = [
        (24, 78, "Flat plate, laminar", ACCENT,
         f"Nu{x_sub} = 0.332 Re{x_sub}^&#189; Pr^&#8531;",
         f"Sh{x_sub} = 0.332 Re{x_sub}^&#189; Sc^&#8531;",
         "derived, not fitted &#183; 0.332 is Blasius f&#8243;(0)"),
        (300, 78, "Pipe, turbulent", SHEAR,
         "Nu = 0.023 Re^0.8 Pr^0.4",
         "Sh = 0.023 Re^0.8 Sc^0.4",
         "Dittus&#8211;Boelter &#183; Re &gt; 10&#8308;, L/D &gt; 10"),
        (576, 78, "Sphere", SUCCESS,
         "Nu = 2 + 0.6 Re^&#189; Pr^&#8531;",
         "Sh = 2 + 0.6 Re^&#189; Sc^&#8531;",
         "Ranz&#8211;Marshall &#183; the 2 is the conduction floor"),
        (24, 246, "Cylinder in crossflow", VORTICITY,
         "Nu = 0.193 Re^0.618 Pr^&#8531;",
         "Sh = 0.193 Re^0.618 Sc^&#8531;",
         "Hilpert &#183; constants change band by band"),
        (300, 246, "Packed bed", WARNING,
         "Nu = 2 + 1.1 Re^0.6 Pr^&#8531;",
         "Sh = 2 + 1.1 Re^0.6 Sc^&#8531;",
         f"Wakao &#183; superficial velocity, d{_sub('p')}"),
        (576, 246, "Pipe, laminar", TEXT_MUTED,
         "Nu = 3.66",
         "Sh = 3.66",
         "constant &#183; conduction across the profile"),
    ]
    blocks = []
    for x, y, name, colour, heat, mass, note in cards:
        blocks.append(f"""
        <rect x="{x}" y="{y}" width="256" height="150" rx="8" fill="{rgba(colour, 0.06)}" stroke="{colour}" stroke-width="1.5"/>
        <text x="{x + 16}" y="{y + 24}" fill="{colour}" font-size="12.5" font-weight="700">{name}</text>
        <rect x="{x + 14}" y="{y + 36}" width="228" height="34" rx="5" fill="{rgba(PRESSURE, 0.12)}"/>
        <text x="{x + 24}" y="{y + 58}" fill="{TEXT}" font-size="11.5" font-family="'JetBrains Mono', monospace">{heat}</text>
        <rect x="{x + 14}" y="{y + 76}" width="228" height="34" rx="5" fill="{rgba(SUCCESS, 0.12)}"/>
        <text x="{x + 24}" y="{y + 98}" fill="{TEXT}" font-size="11.5" font-family="'JetBrains Mono', monospace">{mass}</text>
        <text x="{x + 16}" y="{y + 132}" fill="{TEXT_DIM}" font-size="10.5">{note}</text>
        """)
    return f"""
    <svg viewBox="0 0 880 470" width="100%" height="470" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="28" fill="{ACCENT}" font-size="15" font-weight="bold">The same correlation, read twice</text>
        <text x="24" y="48" fill="{TEXT_DIM}" font-size="12">Red band: heat. Green band: mass. Every second line is the first with Pr replaced by Sc and Nu by Sh &#8212; nothing else changes.</text>
        {"".join(blocks)}
        <text x="24" y="428" fill="{TEXT}" font-size="12.5">This is why a wind-tunnel heat-transfer measurement predicts an evaporation rate, and why naphthalene sublimation is used to map heat-transfer coefficients.</text>
        <text x="24" y="450" fill="{TEXT_DIM}" font-size="11.5">It fails where the two problems stop matching: high mass-transfer rates that distort the velocity profile, chemical reaction, and geometries where form drag dominates skin friction.</text>
    </svg>
    """


def diagram_relief_valve() -> str:
    """A relief device, with the three pressures that decide whether it chokes."""
    zero = _sub("0")
    return f"""
    <svg viewBox="0 0 880 430" width="100%" height="430" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="28" fill="{ACCENT}" font-size="15" font-weight="bold">Pressure relief &#183; why the throat cannot hear the tailpipe</text>
        <text x="24" y="48" fill="{TEXT_DIM}" font-size="12">Once the throat reaches Mach 1, information cannot travel upstream against it. Capacity is then fixed by p{zero} and T{zero} alone.</text>

        <rect x="40" y="120" width="180" height="190" rx="10" fill="{rgba(PRESSURE, 0.12)}" stroke="{PRESSURE}" stroke-width="2.4"/>
        <text x="60" y="150" fill="{PRESSURE}" font-size="13" font-weight="700">PROTECTED VESSEL</text>
        <text x="60" y="176" fill="{TEXT}" font-size="13" font-family="'JetBrains Mono', monospace">p{zero}, T{zero}</text>
        <text x="60" y="198" fill="{TEXT_DIM}" font-size="11">stagnation state</text>
        <text x="60" y="222" fill="{TEXT_DIM}" font-size="11">at relieving conditions</text>
        <text x="60" y="248" fill="{TEXT_DIM}" font-size="11">(set pressure + overpressure,</text>
        <text x="60" y="264" fill="{TEXT_DIM}" font-size="11">not the normal operating point)</text>

        <line x1="220" y1="215" x2="292" y2="215" stroke="{ACCENT}" stroke-width="10"/>
        <text x="228" y="200" fill="{TEXT_DIM}" font-size="10.5">inlet line</text>
        <text x="196" y="330" fill="{WARNING}" font-size="10.5">inlet line loss must stay below 3% of the set pressure, or the valve chatters</text>

        <path d="M 292 186 L 330 208 L 330 222 L 292 244 Z" fill="{rgba(SHEAR, 0.30)}" stroke="{SHEAR}" stroke-width="2.4"/>
        <text x="300" y="168" fill="{SHEAR}" font-size="12.5" font-weight="700">throat</text>
        <text x="286" y="276" fill="{SHEAR}" font-size="12" font-weight="700">M = 1</text>
        <text x="270" y="292" fill="{TEXT_DIM}" font-size="10.5">area A, coefficient K&#8340;</text>

        <path d="M 330 208 L 430 176 L 430 254 L 330 222 Z" fill="{rgba(ACCENT, 0.10)}" stroke="{ACCENT}" stroke-width="2"/>
        <line x1="430" y1="215" x2="560" y2="215" stroke="{ACCENT}" stroke-width="10"/>
        <text x="446" y="200" fill="{TEXT_DIM}" font-size="10.5">tailpipe / flare header</text>

        <rect x="560" y="170" width="150" height="92" rx="8" fill="{SURFACE_RAISED}" stroke="{BORDER_STRONG}" stroke-width="1.8"/>
        <text x="576" y="196" fill="{TEXT}" font-size="12.5" font-weight="700">BACK PRESSURE</text>
        <text x="576" y="218" fill="{TEXT_DIM}" font-size="11">superimposed (header)</text>
        <text x="576" y="236" fill="{TEXT_DIM}" font-size="11">+ built-up (own flow)</text>
        <text x="576" y="254" fill="{TEXT_DIM}" font-size="11">= total p&#8342;</text>

        <line x1="330" y1="322" x2="330" y2="352" stroke="{TEXT_FAINT}" stroke-width="1.4" stroke-dasharray="4,3"/>
        <line x1="640" y1="272" x2="640" y2="352" stroke="{TEXT_FAINT}" stroke-width="1.4" stroke-dasharray="4,3"/>
        <line x1="330" y1="352" x2="640" y2="352" stroke="{VORTICITY}" stroke-width="2" marker-start="url(#arrow-purple)" marker-end="url(#arrow-purple)"/>
        <text x="360" y="344" fill="{VORTICITY}" font-size="11.5">no signal can travel this way while M = 1 at the throat</text>

        <rect x="40" y="368" width="800" height="48" rx="8" fill="{rgba(SUCCESS, 0.10)}" stroke="{SUCCESS}" stroke-width="1.6"/>
        <text x="60" y="390" fill="{TEXT}" font-size="13" font-family="'JetBrains Mono', monospace">G = p{zero} &#8730;(&#947;/RT{zero}) &#183; (2/(&#947;+1))^((&#947;+1)/2(&#947;&#8722;1))&#160;&#160;&#160;&#8658;&#160;&#160;&#160;A = W / (K&#8340; G)</text>
        <text x="60" y="408" fill="{TEXT_DIM}" font-size="11">p&#8342; appears nowhere: that is the design fact. Capacity rises with p{zero}, and falls as &#8730;T{zero} rises &#8212; a hot relief case passes less.</text>
    </svg>
    """
