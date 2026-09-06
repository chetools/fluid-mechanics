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

def diagram_sphere_forces() -> str:
    """True-plane sphere traction geometry, separate from a settling free body."""
    return f'''
    <svg viewBox="0 0 880 420" width="100%" height="420" xmlns="http://www.w3.org/2000/svg"
         style="background:{SURFACE};font-family:Inter,sans-serif">
      {_arrow_defs()}
      <text x="24" y="30" fill="{TEXT}" font-size="17" font-weight="bold">Local surface traction and the net force are different pictures</text>
      <rect x="16" y="48" width="432" height="350" rx="8" fill="{SURFACE_RAISED}"/>
      <rect x="460" y="48" width="404" height="350" rx="8" fill="{SURFACE_RAISED}"/>
      <text x="32" y="74" fill="{ACCENT}" font-size="14">Fixed sphere · fluid flows to the right</text>
      <line x1="38" y1="115" x2="133" y2="115" stroke="{ACCENT}" stroke-width="3" marker-end="url(#arrow-sky)"/>
      <text x="45" y="103" fill="{ACCENT}" font-size="13">U, positive flow axis</text>
      <circle cx="193" cy="229" r="75" fill="{rgba(ACCENT,.10)}" stroke="{ACCENT}" stroke-width="2"/>
      <line x1="193" y1="229" x2="302" y2="229" stroke="{TEXT_DIM}" stroke-dasharray="4,3"/>
      <line x1="193" y1="229" x2="246" y2="176" stroke="{TEXT_DIM}" stroke-dasharray="4,3"/>
      <path d="M 224 229 A 31 31 0 0 0 215 207" fill="none" stroke="{TEXT}" stroke-width="1.5"/>
      <text x="233" y="219" fill="{TEXT}" font-size="15">θ</text>
      <text x="205" y="187" fill="{TEXT_DIM}" font-size="12">a</text>
      <circle cx="193" cy="229" r="3" fill="{TEXT}"/>
      <circle cx="246" cy="176" r="4" fill="{TEXT}"/>
      <line x1="246" y1="176" x2="282" y2="140" stroke="{TEXT_DIM}" stroke-width="2" marker-end="url(#arrow-dim)"/>
      <text x="288" y="136" fill="{TEXT_DIM}" font-size="12">n outward</text>
      <line x1="246" y1="176" x2="216" y2="206" stroke="{PRESSURE}" stroke-width="3" marker-end="url(#arrow-red)"/>
      <text x="116" y="160" fill="{PRESSURE}" font-size="12">−p n inward</text>
      <line x1="246" y1="176" x2="282" y2="212" stroke="{SHEAR}" stroke-width="3" marker-end="url(#arrow-orange)"/>
      <text x="292" y="194" fill="{SHEAR}" font-size="12">Viscous traction</text>
      <text x="292" y="211" fill="{SHEAR}" font-size="12">tangent at wall</text>
      <text x="32" y="333" fill="{TEXT}" font-size="12">θ is measured from +U, in this true meridional plane.</text>
      <text x="32" y="354" fill="{TEXT_DIM}" font-size="12">Integrate axial projections over the whole surface.</text>
      <text x="32" y="375" fill="{TEXT_DIM}" font-size="12">Stokes drag: pressure contributes ⅓, viscosity ⅔.</text>
      <text x="476" y="74" fill="{ACCENT}" font-size="14">Settling sphere · forces on the particle</text>
      <circle cx="643" cy="216" r="43" fill="{rgba(ACCENT,.10)}" stroke="{ACCENT}" stroke-width="2"/>
      <line x1="626" y1="216" x2="626" y2="125" stroke="{ACCENT}" stroke-width="3" marker-end="url(#arrow-sky)"/>
      <text x="488" y="122" fill="{ACCENT}" font-size="12">Buoyancy ρgV</text>
      <line x1="661" y1="216" x2="661" y2="150" stroke="{SHEAR}" stroke-width="3" marker-end="url(#arrow-orange)"/>
      <text x="684" y="148" fill="{SHEAR}" font-size="12">Drag F<tspan baseline-shift="sub" font-size="9">D</tspan></text>
      <line x1="643" y1="216" x2="643" y2="300" stroke="{PRESSURE}" stroke-width="3" marker-end="url(#arrow-red)"/>
      <text x="666" y="295" fill="{PRESSURE}" font-size="12">Weight ρ<tspan baseline-shift="sub" font-size="9">p</tspan>gV</text>
      <line x1="778" y1="195" x2="778" y2="256" stroke="{SUCCESS}" stroke-width="2" marker-end="url(#arrow-green)"/>
      <text x="738" y="180" fill="{SUCCESS}" font-size="12">U<tspan baseline-shift="sub" font-size="9">t</tspan> downward</text>
      <text x="476" y="333" fill="{TEXT}" font-size="12">At terminal speed: weight = buoyancy + drag.</text>
      <text x="476" y="354" fill="{TEXT_DIM}" font-size="12">Shown: ρ<tspan baseline-shift="sub" font-size="9">p</tspan> &gt; ρ; a lighter particle rises.</text>
      <text x="476" y="375" fill="{TEXT_DIM}" font-size="12">Separate free body; arrow lengths are schematic.</text>
    </svg>'''


def diagram_sphere_separation() -> str:
    """Schematic separation locations; not a computed flow or universal threshold."""
    panels = []
    for offset, title, sx, sy, wake_y, color in (
        (0, "Laminar boundary layer · earlier separation", 214, 136, 120, PRESSURE),
        (436, "Turbulent boundary layer · later separation", 259, 157, 165, SUCCESS),
    ):
        panels.append(f'''
        <g transform="translate({offset},0)">
          <rect x="16" y="50" width="416" height="280" rx="8" fill="{SURFACE_RAISED}"/>
          <text x="28" y="75" fill="{color}" font-size="13">{title}</text>
          <line x1="40" y1="201" x2="111" y2="201" stroke="{ACCENT}" stroke-width="3" marker-end="url(#arrow-sky)"/>
          <text x="46" y="183" fill="{ACCENT}" font-size="12">U</text>
          <path d="M {sx} {sy} Q 299 {wake_y} 406 {wake_y} L 406 {402-wake_y} Q 299 {402-wake_y} {sx} {402-sy} Z"
                fill="{rgba(color,.12)}"/>
          <circle cx="210" cy="201" r="65" fill="{SURFACE}" stroke="{ACCENT}" stroke-width="2"/>
          <path d="M {sx} {sy} Q 299 {wake_y} 406 {wake_y} M {sx} {402-sy} Q 299 {402-wake_y} 406 {402-wake_y}"
                fill="none" stroke="{color}" stroke-width="2" stroke-dasharray="5,3"/>
          <circle cx="{sx}" cy="{sy}" r="4" fill="{color}"/>
          <circle cx="{sx}" cy="{402-sy}" r="4" fill="{color}"/>
          <text x="284" y="205" fill="{color}" font-size="12">Wake</text>
          <text x="30" y="307" fill="{TEXT_DIM}" font-size="12">Dots mark separation; dashed curves bound the wake.</text>
        </g>''')
    return f'''
    <svg viewBox="0 0 880 410" width="100%" height="410" xmlns="http://www.w3.org/2000/svg"
         style="background:{SURFACE};font-family:Inter,sans-serif">
      {_arrow_defs()}
      <text x="24" y="30" fill="{TEXT}" font-size="17" font-weight="bold">Drag crisis: more near-wall momentum can mean a narrower wake</text>
      {''.join(panels)}
      <text x="24" y="357" fill="{TEXT}" font-size="13">A turbulent boundary layer transports momentum toward the wall and can resist separation longer.</text>
      <text x="24" y="380" fill="{TEXT_DIM}" font-size="12">Pressure drag can fall more than skin friction rises. Schematic only: roughness and free-stream turbulence matter.</text>
    </svg>'''


def diagram_nozzle_information() -> str:
    """Upstream acoustic characteristic in a converging nozzle, in the lab frame."""
    return f'''
    <svg viewBox="0 0 880 420" width="100%" height="420" xmlns="http://www.w3.org/2000/svg"
         style="background:{SURFACE};font-family:Inter,sans-serif">
      {_arrow_defs()}
      <text x="24" y="30" fill="{TEXT}" font-size="17" font-weight="bold">Choking closes the upstream acoustic path at the throat</text>
      <text x="24" y="55" fill="{TEXT_DIM}" font-size="12">Steady ideal gas · smooth converging nozzle · fixed reservoir state · velocities in the laboratory frame</text>
      <text x="30" y="88" fill="{ACCENT}" font-size="14">Unchoked: M &lt; 1 throughout</text>
      <path d="M 40 109 L 160 109 Q 240 109 317 143 L 388 143 M 40 209 L 160 209 Q 240 209 317 175 L 388 175"
            fill="none" stroke="{TEXT_DIM}" stroke-width="4"/>
      <text x="47" y="140" fill="{TEXT}" font-size="12">Reservoir</text>
      <text x="47" y="160" fill="{TEXT_DIM}" font-size="12">p₀, T₀</text>
      <line x1="173" y1="154" x2="233" y2="154" stroke="{ACCENT}" stroke-width="2" marker-end="url(#arrow-sky)"/>
      <text x="188" y="142" fill="{ACCENT}" font-size="12">u &gt; 0</text>
      <line x1="378" y1="165" x2="300" y2="165" stroke="{SUCCESS}" stroke-width="3" marker-end="url(#arrow-green)"/>
      <text x="301" y="127" fill="{SUCCESS}" font-size="12">u − a &lt; 0</text>
      <text x="319" y="220" fill="{TEXT_DIM}" font-size="12">Exit / throat</text>
      <text x="414" y="149" fill="{TEXT}" font-size="13">Back pressure p<tspan baseline-shift="sub" font-size="10">b</tspan></text>
      <text x="414" y="175" fill="{SUCCESS}" font-size="13">A pressure disturbance can travel upstream.</text>
      <text x="414" y="199" fill="{TEXT_DIM}" font-size="12">Exit pressure matches p<tspan baseline-shift="sub" font-size="9">b</tspan> in this ideal subsonic model.</text>
      <text x="30" y="255" fill="{ACCENT}" font-size="14">Choked: M = 1 at the exit</text>
      <path d="M 40 276 L 160 276 Q 240 276 317 310 L 388 310 M 40 376 L 160 376 Q 240 376 317 342 L 388 342"
            fill="none" stroke="{TEXT_DIM}" stroke-width="4"/>
      <text x="47" y="307" fill="{TEXT}" font-size="12">Same p₀, T₀</text>
      <line x1="173" y1="321" x2="233" y2="321" stroke="{ACCENT}" stroke-width="2" marker-end="url(#arrow-sky)"/>
      <text x="182" y="309" fill="{ACCENT}" font-size="12">Flow →</text>
      <line x1="388" y1="305" x2="388" y2="347" stroke="{WARNING}" stroke-width="3"/>
      <circle cx="388" cy="326" r="4" fill="{WARNING}"/>
      <text x="302" y="291" fill="{WARNING}" font-size="12">u − a = 0</text>
      <text x="316" y="385" fill="{TEXT_DIM}" font-size="12">Sonic exit: p*</text>
      <path d="M 395 310 Q 419 298 437 294 M 395 342 Q 419 354 437 358" fill="none" stroke="{ACCENT}" stroke-dasharray="4,3"/>
      <text x="458" y="295" fill="{TEXT}" font-size="13">Lower p<tspan baseline-shift="sub" font-size="10">b</tspan> further: the jet adjusts outside.</text>
      <text x="458" y="321" fill="{WARNING}" font-size="13">Upstream-going sound stalls at the sonic throat.</text>
      <text x="458" y="346" fill="{TEXT_DIM}" font-size="12">While choked, ideal mass flow stays fixed; p* can exceed p<tspan baseline-shift="sub" font-size="9">b</tspan>.</text>
      <text x="458" y="371" fill="{TEXT_DIM}" font-size="12">Raise p<tspan baseline-shift="sub" font-size="9">b</tspan> enough and the nozzle unchokes.</text>
    </svg>'''


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


def diagram_injection_work() -> str:
    """True side view: W_on = F dx = -p ΔV because positive ΔV is expansion."""
    return f'''
    <svg viewBox="0 0 880 520" width="100%" height="520" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
      {_arrow_defs()}
      <text x="24" y="28" fill="{ACCENT}" font-size="16" font-weight="bold">Work on the system is positive, so volume change enters with a minus</text>
      <text x="24" y="48" fill="{TEXT_DIM}" font-size="12">True side view of a piston-cylinder. Height is area A (unit depth). Lengths schematic; the signs are the point.</text>

      <rect x="16" y="60" width="848" height="248" rx="8" fill="{SURFACE_RAISED}"/>
      <text x="32" y="84" fill="{ACCENT}" font-size="13" font-weight="700">1 · Force &#215; distance, with the two arrows drawn</text>

      <rect x="48" y="100" width="500" height="12" fill="url(#hatch-wall)" stroke="{TEXT_DIM}"/>
      <rect x="48" y="252" width="500" height="12" fill="url(#hatch-wall)" stroke="{TEXT_DIM}"/>
      <line x1="48" y1="112" x2="548" y2="112" stroke="{TEXT}" stroke-width="2"/>
      <line x1="48" y1="252" x2="548" y2="252" stroke="{TEXT}" stroke-width="2"/>
      <line x1="48" y1="112" x2="48" y2="252" stroke="{TEXT}" stroke-width="2"/>

      <rect x="50" y="112" width="310" height="140" fill="{rgba(ACCENT, 0.14)}" stroke="{ACCENT}" stroke-width="1"/>
      <text x="140" y="188" fill="{ACCENT}" font-size="14" font-weight="700">system (fluid)</text>

      <rect x="360" y="112" width="44" height="140" fill="{rgba(PRESSURE, 0.35)}" stroke="{PRESSURE}" stroke-width="2"/>
      <text x="366" y="188" fill="{PRESSURE}" font-size="12" font-weight="700">piston</text>
      <rect x="404" y="168" width="70" height="28" fill="{SURFACE_RAISED}" stroke="{PRESSURE}" stroke-width="2"/>

      <line x1="360" y1="112" x2="360" y2="252" stroke="{SUCCESS}" stroke-width="1.5" stroke-dasharray="5,4"/>
      <rect x="360" y="112" width="80" height="140" fill="none" stroke="{SUCCESS}" stroke-width="1.5" stroke-dasharray="5,4"/>
      <text x="448" y="130" fill="{SUCCESS}" font-size="12">expanded</text>
      <text x="448" y="146" fill="{SUCCESS}" font-size="12">position</text>

      <line x1="348" y1="168" x2="250" y2="168" stroke="{PRESSURE}" stroke-width="3" marker-end="url(#arrow-red)"/>
      <text x="258" y="158" fill="{PRESSURE}" font-size="13" font-weight="700">F on system = pA, inward</text>

      <line x1="382" y1="230" x2="430" y2="230" stroke="{SUCCESS}" stroke-width="3" marker-end="url(#arrow-green)"/>
      <text x="390" y="222" fill="{SUCCESS}" font-size="12" font-weight="700">+&#916;x, expansion</text>

      <line x1="32" y1="112" x2="32" y2="252" stroke="{TEXT_DIM}" stroke-width="1.5" marker-start="url(#arrow-dim)" marker-end="url(#arrow-dim)"/>
      <text x="18" y="188" fill="{TEXT}" font-size="13">A</text>

      <line x1="360" y1="276" x2="440" y2="276" stroke="{TEXT_DIM}" stroke-width="1.5" marker-start="url(#arrow-dim)" marker-end="url(#arrow-dim)"/>
      <text x="384" y="296" fill="{SUCCESS}" font-size="13">+&#916;x</text>
      <text x="448" y="280" fill="{TEXT_DIM}" font-size="12">&#916;V = +A &#916;x</text>

      <text x="570" y="118" fill="{TEXT}" font-size="13" font-weight="700">Work on the system = F · (displacement of F)</text>
      <text x="570" y="148" fill="{TEXT}" font-size="13">F on the fluid points in. Positive &#916;x is out.</text>
      <text x="570" y="168" fill="{TEXT}" font-size="13">The arrows oppose, so the product is negative:</text>
      <text x="570" y="200" fill="{TEXT}" font-size="15" font-family="'JetBrains Mono', monospace">W_on = (pA)(−&#916;x)</text>
      <text x="570" y="228" fill="{TEXT}" font-size="15" font-family="'JetBrains Mono', monospace">     = −p (A &#916;x)</text>
      <text x="570" y="256" fill="{TEXT}" font-size="15" font-family="'JetBrains Mono', monospace">     = −p &#916;V</text>
      <text x="570" y="286" fill="{TEXT_DIM}" font-size="12">&#916;V &gt; 0 means the system grew. Expansion:</text>
      <text x="570" y="304" fill="{TEXT_DIM}" font-size="12">the fluid does work on the piston, W_on &lt; 0.</text>

      <rect x="16" y="320" width="420" height="180" rx="8" fill="{SURFACE_RAISED}"/>
      <rect x="444" y="320" width="420" height="180" rx="8" fill="{SURFACE_RAISED}"/>

      <text x="32" y="344" fill="{ACCENT}" font-size="13" font-weight="700">2 · Compression: &#916;V is negative</text>
      <rect x="48" y="358" width="280" height="10" fill="url(#hatch-wall)" stroke="{TEXT_DIM}"/>
      <rect x="48" y="456" width="280" height="10" fill="url(#hatch-wall)" stroke="{TEXT_DIM}"/>
      <line x1="48" y1="368" x2="328" y2="368" stroke="{TEXT}" stroke-width="2"/>
      <line x1="48" y1="456" x2="328" y2="456" stroke="{TEXT}" stroke-width="2"/>
      <line x1="48" y1="368" x2="48" y2="456" stroke="{TEXT}" stroke-width="2"/>
      <rect x="50" y="368" width="200" height="88" fill="{rgba(ACCENT, 0.14)}"/>
      <rect x="250" y="368" width="36" height="88" fill="{rgba(PRESSURE, 0.35)}" stroke="{PRESSURE}" stroke-width="2"/>
      <line x1="286" y1="368" x2="286" y2="456" stroke="{SUCCESS}" stroke-width="1.5" stroke-dasharray="5,4"/>
      <text x="294" y="400" fill="{SUCCESS}" font-size="11">was here</text>
      <line x1="268" y1="412" x2="210" y2="412" stroke="{PRESSURE}" stroke-width="3" marker-end="url(#arrow-red)"/>
      <line x1="268" y1="440" x2="210" y2="440" stroke="{SHEAR}" stroke-width="3" marker-end="url(#arrow-orange)"/>
      <text x="160" y="404" fill="{PRESSURE}" font-size="12">F still in</text>
      <text x="142" y="452" fill="{SHEAR}" font-size="12">piston moves in</text>
      <text x="32" y="486" fill="{TEXT}" font-size="12">Now force and displacement are parallel: W_on &gt; 0.</text>

      <text x="460" y="344" fill="{ACCENT}" font-size="13" font-weight="700">3 · Per kilogram that is the +p/&#961; term</text>
      <text x="460" y="372" fill="{TEXT}" font-size="13" font-family="'JetBrains Mono', monospace">W_on = −p &#916;V</text>
      <text x="460" y="396" fill="{TEXT}" font-size="13">Push in one kilogram: the system volume falls</text>
      <text x="460" y="416" fill="{TEXT}" font-size="13">by that kilogram's volume, &#916;V = −1/&#961;.</text>
      <text x="460" y="444" fill="{TEXT}" font-size="15" font-family="'JetBrains Mono', monospace">W_on/m = −p (−1/&#961;) = p/&#961;</text>
      <text x="460" y="470" fill="{TEXT}" font-size="12">1/&#961; is specific volume (m³/kg). Thermodynamics</text>
      <text x="460" y="488" fill="{TEXT}" font-size="12">calls it v; here v is a velocity, so we keep 1/&#961;.</text>
    </svg>'''


def diagram_model_selection() -> str:
    """Connect an engineering question to the model and checks it needs."""
    rows = [
        ("Pressure drop in a long pipe", "Head balance + friction factor", "Check regime, entry length, fittings", ACCENT),
        ("Acceleration through a nozzle", "Continuity + Euler / Bernoulli", "Check losses and compressibility", SUCCESS),
        ("Shear near a moving wall", "Viscous momentum + no slip", "Check geometry and constitutive law", SHEAR),
        ("Force on a control volume", "Reynolds transport theorem", "Check where the surface is cut", PRESSURE),
        ("Shaft work in a rotor", "Euler turbomachinery equation", "Check absolute vs relative velocity", WARNING),
        ("Nozzle or shock in a gas", "Isentropic relations + normal shock", "Check choking and stagnation losses", INERTIA),
        ("Recirculation in a cavity", "Numerical Navier–Stokes", "Check mass, grid, time, benchmark", VORTICITY),
    ]
    body = ""
    for i, (question, model, check, color) in enumerate(rows):
        y = 94 + 65 * i
        body += f'<rect x="20" y="{y-24}" width="780" height="54" rx="6" fill="{rgba(color,.07)}" stroke="{BORDER}"/>'
        for x, label in ((34, question), (291, model), (545, check)):
            body += f'<text x="{x}" y="{y+7}" fill="{color if x == 291 else TEXT_MUTED}" font-size="12">{escape(label)}</text>'
    last_y = 94 + 65 * (len(rows) - 1)
    caption_y = last_y + 47
    viewbox_height = caption_y + 16
    return f'''<svg viewBox="0 0 820 {viewbox_height}" width="100%" height="{viewbox_height}" xmlns="http://www.w3.org/2000/svg"
      style="background: {SURFACE}; border-radius: 12px; border: 1px solid {BORDER}; font-family: sans-serif;">
      <text x="28" y="32" fill="{TEXT}" font-size="18" font-weight="600">Choose the model by the question</text>
      <text x="34" y="57" fill="{ACCENT}" font-size="11">WHAT DO YOU NEED?</text>
      <text x="291" y="57" fill="{ACCENT}" font-size="11">START WITH</text>
      <text x="545" y="57" fill="{ACCENT}" font-size="11">BEFORE TRUSTING THE ANSWER</text>
      {body}
      <text x="28" y="{caption_y}" fill="{TEXT_DIM}" font-size="12">All rows conserve mass and momentum. The assumptions decide which terms and details remain.</text>
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
        <text x="565" y="55" fill="{TEXT_DIM}" font-size="11">Anti-symmetric spin Ω_yx</text>
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
    # The 1/7 law has a cusp at r = 0 because it uses |r|; the real profile is
    # smooth there. Round |r/R| as sqrt((r/R)^2 + eps^2) so the nose is blunt
    # instead of pointed, at the cost of ~2 px of centreline velocity.
    def _turb_x(y: float) -> float:
        t = (y - 150.0) / 60.0
        s = (t * t + 0.12**2) ** 0.5
        return 485 + 145 * (1 - min(s, 1.0)) ** (1 / 7)

    turbulent_path = "M " + " L ".join(
        f"{_turb_x(y):.2f},{y}" for y in range(90, 211)
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
        <text x="400" y="196" fill="{TEXT_DIM}" font-size="12">Re_MR &lt; ~2100: f_F = 16/Re_MR (Darcy f_D = 64/Re_MR).</text>
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

        <path d="M 90 200 L 150 320 L 630 320 L 690 200" fill="none" stroke="{SHEAR}" stroke-width="4"/>
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
         "T_w const &#183; 4.36 if q_w const"),
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
        <text x="24" y="48" fill="{TEXT_DIM}" font-size="12">Once the throat reaches Mach 1, information cannot travel upstream against it. Ideal choked capacity uses a fixed area, coefficient, gas and upstream state.</text>

        <rect x="40" y="120" width="180" height="190" rx="10" fill="{rgba(PRESSURE, 0.12)}" stroke="{PRESSURE}" stroke-width="2.4"/>
        <text x="60" y="150" fill="{PRESSURE}" font-size="13" font-weight="700">PROTECTED VESSEL</text>
        <text x="60" y="176" fill="{TEXT}" font-size="13" font-family="'JetBrains Mono', monospace">p{zero}, T{zero}</text>
        <text x="60" y="198" fill="{TEXT_DIM}" font-size="11">stagnation state</text>
        <text x="60" y="222" fill="{TEXT_DIM}" font-size="11">at relieving conditions</text>
        <text x="60" y="248" fill="{TEXT_DIM}" font-size="11">(set pressure + overpressure,</text>
        <text x="60" y="264" fill="{TEXT_DIM}" font-size="11">not the normal operating point)</text>

        <line x1="220" y1="215" x2="292" y2="215" stroke="{ACCENT}" stroke-width="10"/>
        <text x="228" y="200" fill="{TEXT_DIM}" font-size="10.5">inlet line</text>
        <text x="196" y="330" fill="{WARNING}" font-size="10.5">Inlet losses and valve lift need separate checks; this model uses fixed effective area.</text>

        <path d="M 292 186 L 330 208 L 330 222 L 292 244 Z" fill="{rgba(SHEAR, 0.30)}" stroke="{SHEAR}" stroke-width="2.4"/>
        <text x="300" y="168" fill="{SHEAR}" font-size="12.5" font-weight="700">throat</text>
        <text x="286" y="276" fill="{SHEAR}" font-size="12" font-weight="700">M = 1</text>
        <text x="270" y="292" fill="{TEXT_DIM}" font-size="10.5">area A, coefficient K{_sub("d")}</text>

        <path d="M 330 208 L 430 176 L 430 254 L 330 222 Z" fill="{rgba(ACCENT, 0.10)}" stroke="{ACCENT}" stroke-width="2"/>
        <line x1="430" y1="215" x2="560" y2="215" stroke="{ACCENT}" stroke-width="10"/>
        <text x="446" y="200" fill="{TEXT_DIM}" font-size="10.5">tailpipe / flare header</text>

        <rect x="560" y="170" width="150" height="92" rx="8" fill="{SURFACE_RAISED}" stroke="{BORDER_STRONG}" stroke-width="1.8"/>
        <text x="576" y="196" fill="{TEXT}" font-size="12.5" font-weight="700">BACK PRESSURE</text>
        <text x="576" y="218" fill="{TEXT_DIM}" font-size="11">superimposed (header)</text>
        <text x="576" y="236" fill="{TEXT_DIM}" font-size="11">+ built-up (own flow)</text>
        <text x="576" y="254" fill="{TEXT_DIM}" font-size="11">= total p{_sub("b")}</text>

        <line x1="330" y1="322" x2="330" y2="352" stroke="{TEXT_FAINT}" stroke-width="1.4" stroke-dasharray="4,3"/>
        <line x1="640" y1="272" x2="640" y2="352" stroke="{TEXT_FAINT}" stroke-width="1.4" stroke-dasharray="4,3"/>
        <line x1="640" y1="352" x2="330" y2="352" stroke="{VORTICITY}" stroke-width="2" stroke-dasharray="5,3" marker-end="url(#arrow-purple)"/>
        <text x="360" y="344" fill="{VORTICITY}" font-size="11.5">Upstream acoustic propagation is blocked at the sonic throat.</text>

        <rect x="40" y="368" width="800" height="48" rx="8" fill="{rgba(SUCCESS, 0.10)}" stroke="{SUCCESS}" stroke-width="1.6"/>
        <text x="60" y="390" fill="{TEXT}" font-size="13" font-family="'JetBrains Mono', monospace">G = p{zero} &#8730;(&#947;/RT{zero}) &#183; (2/(&#947;+1))^((&#947;+1)/(2(&#947;&#8722;1)))&#160;&#160;&#160;&#8658;&#160;&#160;&#160;A = W / (K{_sub("d")} G)</text>
        <text x="60" y="408" fill="{TEXT_DIM}" font-size="11">Back pressure drops out only while flow stays choked; real valve and piping effects are separate.</text>
    </svg>
    """


# =============================================================================
# Newtonian and non-Newtonian fluids: why the linear law holds, and what breaks it
# =============================================================================

def diagram_newtonian_origin() -> str:
    """Where tau = mu du/dy comes from, and the two assumptions hiding in it."""
    gamma = "&#947;&#775;"      # gamma with a dot above
    return f"""
    <svg viewBox="0 0 880 430" width="100%" height="430" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="30" fill="{TEXT}" font-size="17" font-weight="bold">A Newtonian fluid is not a fluid with a special viscosity &#8212; it is one with nothing to remember</text>
        <text x="24" y="52" fill="{TEXT_DIM}" font-size="12">Left: the momentum bookkeeping that makes the law linear. Right: the two facts about the microstructure that let it be written at all.</text>

        <rect x="16" y="68" width="440" height="342" rx="8" fill="{SURFACE_RAISED}"/>
        <text x="34" y="94" fill="{ACCENT}" font-size="13.5" font-weight="700">Momentum crossing a plane between two layers</text>

        <line x1="60" y1="120" x2="410" y2="120" stroke="{BORDER_STRONG}" stroke-width="3"/>
        <line x1="60" y1="330" x2="410" y2="330" stroke="{BORDER_STRONG}" stroke-width="3"/>
        <line x1="60" y1="225" x2="410" y2="225" stroke="{TEXT_DIM}" stroke-width="1.4" stroke-dasharray="6,4"/>
        <text x="316" y="218" fill="{TEXT_DIM}" font-size="11.5">imaginary plane, area A</text>

        <line x1="80" y1="140" x2="200" y2="140" stroke="{ACCENT}" stroke-width="2.5" marker-end="url(#arrow-sky)"/>
        <line x1="80" y1="180" x2="168" y2="180" stroke="{ACCENT}" stroke-width="2.5" marker-end="url(#arrow-sky)"/>
        <line x1="80" y1="225" x2="140" y2="225" stroke="{ACCENT}" stroke-width="2.5" marker-end="url(#arrow-sky)"/>
        <line x1="80" y1="270" x2="112" y2="270" stroke="{ACCENT}" stroke-width="2.5" marker-end="url(#arrow-sky)"/>
        <text x="212" y="145" fill="{ACCENT}" font-size="12">u(y): faster above</text>

        <circle cx="250" cy="196" r="7" fill="{rgba(SUCCESS,0.35)}" stroke="{SUCCESS}" stroke-width="1.6"/>
        <circle cx="292" cy="256" r="7" fill="{rgba(PRESSURE,0.35)}" stroke="{PRESSURE}" stroke-width="1.6"/>
        <path d="M 250 196 Q 264 226 292 252" fill="none" stroke="{SUCCESS}" stroke-width="2" marker-end="url(#arrow-green)"/>
        <path d="M 292 256 Q 274 228 252 202" fill="none" stroke="{PRESSURE}" stroke-width="2" marker-end="url(#arrow-red)"/>
        <text x="306" y="196" fill="{SUCCESS}" font-size="11.5">a fast molecule drops down</text>
        <text x="306" y="212" fill="{SUCCESS}" font-size="11.5">and speeds the slow layer up</text>
        <text x="306" y="276" fill="{PRESSURE}" font-size="11.5">a slow one rises</text>
        <text x="306" y="292" fill="{PRESSURE}" font-size="11.5">and drags the fast layer back</text>

        <text x="34" y="366" fill="{TEXT}" font-size="12.5">Each crossing carries momentum m&#183;&#916;u, and &#916;u across one mean free path is (du/dy)&#8467;.</text>
        <text x="34" y="386" fill="{TEXT}" font-size="12.5">The crossing rate is set by thermal speed, which the flow does not change, so the flux is</text>
        <text x="34" y="406" fill="{SUCCESS}" font-size="14" font-family="'JetBrains Mono', monospace">&#964; = &#956; du/dy &#8212; strictly proportional, with &#956; a property of the fluid alone.</text>

        <rect x="472" y="68" width="392" height="150" rx="8" fill="{rgba(SUCCESS,0.10)}" stroke="{SUCCESS}" stroke-width="1.6"/>
        <text x="490" y="94" fill="{SUCCESS}" font-size="13.5" font-weight="700">Assumption 1 &#183; nothing to orient</text>
        <text x="490" y="118" fill="{TEXT}" font-size="12">The molecules are small and round on the scale of the flow.</text>
        <text x="490" y="138" fill="{TEXT}" font-size="12">Shear cannot line them up, stretch them or pack them into</text>
        <text x="490" y="158" fill="{TEXT}" font-size="12">chains, so the fluid looks the same at every shear rate and</text>
        <text x="490" y="178" fill="{TEXT}" font-size="12">&#956; cannot depend on {gamma}.</text>
        <text x="490" y="204" fill="{TEXT_DIM}" font-size="11.5">Break it and you get shear thinning, thickening or a yield stress.</text>

        <rect x="472" y="232" width="392" height="150" rx="8" fill="{rgba(VORTICITY,0.10)}" stroke="{VORTICITY}" stroke-width="1.6"/>
        <text x="490" y="258" fill="{VORTICITY}" font-size="13.5" font-weight="700">Assumption 2 &#183; no memory</text>
        <text x="490" y="282" fill="{TEXT}" font-size="12">Any distortion relaxes in about 10&#8315;&#185;&#178; s, which is far shorter</text>
        <text x="490" y="302" fill="{TEXT}" font-size="12">than the time any flow takes to deform a parcel. By the time</text>
        <text x="490" y="322" fill="{TEXT}" font-size="12">the next layer slides past, the structure is already restored,</text>
        <text x="490" y="342" fill="{TEXT}" font-size="12">so &#964; can depend on the strain rate *now* and on nothing else.</text>
        <text x="490" y="368" fill="{TEXT_DIM}" font-size="11.5">Break it and you get elasticity, normal stresses and thixotropy.</text>

        <text x="472" y="406" fill="{WARNING}" font-size="12.5">Both assumptions are about the microstructure, not about the equations. That is why a "non-Newtonian" fluid is a structural fact.</text>
    </svg>
    """


def diagram_microstructure_gallery() -> str:
    """Four departures from Newtonian behaviour, each drawn as its structure."""
    return f"""
    <svg viewBox="0 0 900 560" width="100%" height="560" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="30" fill="{TEXT}" font-size="17" font-weight="bold">What the fluid is made of, and what shear does to it</text>
        <text x="24" y="52" fill="{TEXT_DIM}" font-size="12">In each card: the structure at rest on the left, the same structure under strong shear on the right.</text>

        <rect x="16" y="68" width="428" height="222" rx="8" fill="{SURFACE_RAISED}"/>
        <text x="34" y="94" fill="{SHEAR}" font-size="13.5" font-weight="700">Shear thinning (pseudoplastic) &#183; n &lt; 1</text>
        <path d="M 46 128 q 14 -18 26 0 q 14 18 26 0 q 12 -20 24 -2" fill="none" stroke="{SHEAR}" stroke-width="2"/>
        <path d="M 52 158 q 16 16 30 -2 q 12 -16 26 4" fill="none" stroke="{SHEAR}" stroke-width="2"/>
        <path d="M 44 190 q 20 -14 34 4 q 12 12 26 -6" fill="none" stroke="{SHEAR}" stroke-width="2"/>
        <text x="54" y="216" fill="{TEXT_DIM}" font-size="11.5">at rest: random coils, entangled</text>
        <line x1="176" y1="160" x2="216" y2="160" stroke="{TEXT_DIM}" stroke-width="2" marker-end="url(#arrow-dim)"/>
        <text x="168" y="146" fill="{TEXT_DIM}" font-size="11">shear</text>
        <line x1="238" y1="126" x2="336" y2="122" stroke="{SHEAR}" stroke-width="2"/>
        <line x1="242" y1="152" x2="342" y2="150" stroke="{SHEAR}" stroke-width="2"/>
        <line x1="236" y1="180" x2="338" y2="176" stroke="{SHEAR}" stroke-width="2"/>
        <text x="240" y="216" fill="{TEXT_DIM}" font-size="11.5">aligned, disentangled: they slide</text>
        <text x="34" y="244" fill="{TEXT}" font-size="12">Shear orients the chains faster than Brownian motion can re-randomise them,</text>
        <text x="34" y="262" fill="{TEXT}" font-size="12">so there is less entanglement left to resist. Paint, blood, polymer melts.</text>
        <text x="34" y="282" fill="{SUCCESS}" font-size="11.5">Useful: it pumps like a thin liquid and sits still on the wall like a thick one.</text>

        <rect x="456" y="68" width="428" height="222" rx="8" fill="{SURFACE_RAISED}"/>
        <text x="474" y="94" fill="{PRESSURE}" font-size="13.5" font-weight="700">Shear thickening (dilatant) &#183; n &gt; 1</text>
        <circle cx="500" cy="130" r="8" fill="{rgba(PRESSURE,0.3)}" stroke="{PRESSURE}"/>
        <circle cx="534" cy="158" r="8" fill="{rgba(PRESSURE,0.3)}" stroke="{PRESSURE}"/>
        <circle cx="498" cy="186" r="8" fill="{rgba(PRESSURE,0.3)}" stroke="{PRESSURE}"/>
        <circle cx="546" cy="120" r="8" fill="{rgba(PRESSURE,0.3)}" stroke="{PRESSURE}"/>
        <circle cx="560" cy="192" r="8" fill="{rgba(PRESSURE,0.3)}" stroke="{PRESSURE}"/>
        <text x="486" y="216" fill="{TEXT_DIM}" font-size="11.5">at rest: dispersed, lubricated</text>
        <line x1="596" y1="160" x2="636" y2="160" stroke="{TEXT_DIM}" stroke-width="2" marker-end="url(#arrow-dim)"/>
        <text x="590" y="146" fill="{TEXT_DIM}" font-size="11">shear</text>
        <circle cx="672" cy="134" r="8" fill="{rgba(PRESSURE,0.5)}" stroke="{PRESSURE}"/>
        <circle cx="694" cy="150" r="8" fill="{rgba(PRESSURE,0.5)}" stroke="{PRESSURE}"/>
        <circle cx="716" cy="166" r="8" fill="{rgba(PRESSURE,0.5)}" stroke="{PRESSURE}"/>
        <circle cx="738" cy="182" r="8" fill="{rgba(PRESSURE,0.5)}" stroke="{PRESSURE}"/>
        <line x1="666" y1="128" x2="744" y2="188" stroke="{PRESSURE}" stroke-width="2.5" stroke-dasharray="4,3"/>
        <text x="672" y="216" fill="{TEXT_DIM}" font-size="11.5">hydroclusters carry the load</text>
        <text x="474" y="244" fill="{TEXT}" font-size="12">Squeezed together faster than the liquid can drain from between them, the</text>
        <text x="474" y="262" fill="{TEXT}" font-size="12">particles touch and form force chains &#8212; and a packed bed must dilate to shear.</text>
        <text x="474" y="282" fill="{WARNING}" font-size="11.5">Hazard: a pump that thickens under its own shear can stall. Cornstarch, dense slurries.</text>

        <rect x="16" y="304" width="428" height="240" rx="8" fill="{SURFACE_RAISED}"/>
        <text x="34" y="330" fill="{VORTICITY}" font-size="13.5" font-weight="700">Yield stress &#183; a solid until you push hard enough</text>
        <circle cx="70" cy="372" r="6" fill="{rgba(VORTICITY,0.4)}" stroke="{VORTICITY}"/>
        <circle cx="112" cy="360" r="6" fill="{rgba(VORTICITY,0.4)}" stroke="{VORTICITY}"/>
        <circle cx="150" cy="386" r="6" fill="{rgba(VORTICITY,0.4)}" stroke="{VORTICITY}"/>
        <circle cx="96" cy="404" r="6" fill="{rgba(VORTICITY,0.4)}" stroke="{VORTICITY}"/>
        <circle cx="140" cy="424" r="6" fill="{rgba(VORTICITY,0.4)}" stroke="{VORTICITY}"/>
        <circle cx="60" cy="418" r="6" fill="{rgba(VORTICITY,0.4)}" stroke="{VORTICITY}"/>
        <line x1="70" y1="372" x2="112" y2="360" stroke="{VORTICITY}" stroke-width="1.6"/>
        <line x1="112" y1="360" x2="150" y2="386" stroke="{VORTICITY}" stroke-width="1.6"/>
        <line x1="70" y1="372" x2="96" y2="404" stroke="{VORTICITY}" stroke-width="1.6"/>
        <line x1="96" y1="404" x2="140" y2="424" stroke="{VORTICITY}" stroke-width="1.6"/>
        <line x1="96" y1="404" x2="60" y2="418" stroke="{VORTICITY}" stroke-width="1.6"/>
        <line x1="150" y1="386" x2="140" y2="424" stroke="{VORTICITY}" stroke-width="1.6"/>
        <text x="46" y="452" fill="{TEXT_DIM}" font-size="11.5">bonded network spans the sample</text>
        <line x1="196" y1="396" x2="236" y2="396" stroke="{TEXT_DIM}" stroke-width="2" marker-end="url(#arrow-dim)"/>
        <text x="184" y="382" fill="{TEXT_DIM}" font-size="11">&#964; &gt; &#964;_y</text>
        <circle cx="272" cy="366" r="6" fill="{rgba(VORTICITY,0.4)}" stroke="{VORTICITY}"/>
        <circle cx="312" cy="384" r="6" fill="{rgba(VORTICITY,0.4)}" stroke="{VORTICITY}"/>
        <circle cx="352" cy="360" r="6" fill="{rgba(VORTICITY,0.4)}" stroke="{VORTICITY}"/>
        <circle cx="290" cy="418" r="6" fill="{rgba(VORTICITY,0.4)}" stroke="{VORTICITY}"/>
        <circle cx="344" cy="416" r="6" fill="{rgba(VORTICITY,0.4)}" stroke="{VORTICITY}"/>
        <text x="266" y="452" fill="{TEXT_DIM}" font-size="11.5">bonds broken: fragments flow</text>
        <text x="34" y="478" fill="{TEXT}" font-size="12">Below &#964;_y the network stores the deformation elastically and springs back;</text>
        <text x="34" y="496" fill="{TEXT}" font-size="12">it is a solid, and no viscosity describes it. Toothpaste, mud, ketchup, sludge.</text>
        <text x="34" y="518" fill="{WARNING}" font-size="11.5">Design consequence: a line can be *restarted* only if the pump can exceed &#964;_y</text>
        <text x="34" y="536" fill="{WARNING}" font-size="11.5">everywhere at once &#8212; a pressure requirement that has nothing to do with flow rate.</text>

        <rect x="456" y="304" width="428" height="240" rx="8" fill="{SURFACE_RAISED}"/>
        <text x="474" y="330" fill="{INERTIA}" font-size="13.5" font-weight="700">Thixotropy &#183; broken fast, rebuilt slowly</text>
        <line x1="486" y1="430" x2="854" y2="430" stroke="{TEXT_MUTED}" stroke-width="1.5"/>
        <line x1="486" y1="430" x2="486" y2="352" stroke="{TEXT_MUTED}" stroke-width="1.5"/>
        <text x="784" y="446" fill="{TEXT_DIM}" font-size="11.5">time</text>
        <text x="462" y="358" fill="{TEXT_DIM}" font-size="11.5">&#955;</text>
        <path d="M 486 360 L 560 360 L 566 418 L 660 418" fill="none" stroke="{INERTIA}" stroke-width="2.5"/>
        <path d="M 660 418 Q 730 414 800 372" fill="none" stroke="{INERTIA}" stroke-width="2.5"/>
        <text x="500" y="352" fill="{TEXT_DIM}" font-size="11">at rest</text>
        <text x="576" y="410" fill="{PRESSURE}" font-size="11">sheared: breaks in seconds</text>
        <text x="690" y="366" fill="{SUCCESS}" font-size="11">rest: rebuilds in minutes</text>
        <text x="474" y="478" fill="{TEXT}" font-size="12">The structure is the same one that gives a yield stress, but building it back</text>
        <text x="474" y="496" fill="{TEXT}" font-size="12">takes real time. The stress then depends on the shear *history*, not just on</text>
        <text x="474" y="514" fill="{TEXT}" font-size="12">the present strain rate &#8212; so a rheometer sweeping up and down draws a loop.</text>
        <text x="474" y="536" fill="{TEXT_DIM}" font-size="11.5">Stirred yoghurt, bentonite drilling mud, non-drip paint.</text>
    </svg>
    """


def diagram_viscoelastic_effects() -> str:
    """Rod climbing and die swell: what a tension along the streamlines does."""
    return f"""
    <svg viewBox="0 0 880 420" width="100%" height="420" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="30" fill="{TEXT}" font-size="17" font-weight="bold">Elastic memory has a direction: stretched chains pull along the streamline</text>
        <text x="24" y="52" fill="{TEXT_DIM}" font-size="12">A Newtonian fluid can only push normally (pressure) and drag tangentially. A stretched polymer adds a tension the flow direction chooses.</text>

        <rect x="16" y="68" width="284" height="330" rx="8" fill="{SURFACE_RAISED}"/>
        <text x="34" y="94" fill="{SUCCESS}" font-size="13.5" font-weight="700">Newtonian: the surface dips</text>
        <rect x="52" y="150" width="212" height="180" rx="4" fill="none" stroke="{BORDER_STRONG}" stroke-width="2"/>
        <path d="M 52 190 Q 158 236 264 190 L 264 330 L 52 330 Z" fill="{rgba(ACCENT,0.16)}" stroke="{ACCENT}" stroke-width="2"/>
        <rect x="150" y="104" width="16" height="180" fill="{BORDER_STRONG}"/>
        <path d="M 132 116 A 26 12 0 1 1 184 116" fill="none" stroke="{TEXT}" stroke-width="2" marker-end="url(#arrow-dim)"/>
        <text x="190" y="112" fill="{TEXT_DIM}" font-size="11.5">&#937;</text>
        <line x1="98" y1="216" x2="70" y2="216" stroke="{PRESSURE}" stroke-width="2.5" marker-end="url(#arrow-red)"/>
        <line x1="218" y1="216" x2="246" y2="216" stroke="{PRESSURE}" stroke-width="2.5" marker-end="url(#arrow-red)"/>
        <text x="34" y="356" fill="{TEXT}" font-size="12">Inertia throws the fluid outwards;</text>
        <text x="34" y="374" fill="{TEXT}" font-size="12">the free surface falls at the rod.</text>
        <text x="34" y="392" fill="{TEXT_DIM}" font-size="11.5">Only &#964; and p act &#8212; nothing pulls inward.</text>

        <rect x="312" y="68" width="284" height="330" rx="8" fill="{SURFACE_RAISED}"/>
        <text x="330" y="94" fill="{VISCOUS}" font-size="13.5" font-weight="700">Viscoelastic: it climbs the rod</text>
        <rect x="348" y="150" width="212" height="180" rx="4" fill="none" stroke="{BORDER_STRONG}" stroke-width="2"/>
        <path d="M 348 214 Q 400 214 428 168 Q 446 140 468 168 Q 496 214 560 214 L 560 330 L 348 330 Z" fill="{rgba(VISCOUS,0.16)}" stroke="{VISCOUS}" stroke-width="2"/>
        <rect x="446" y="104" width="16" height="180" fill="{BORDER_STRONG}"/>
        <path d="M 428 116 A 26 12 0 1 1 480 116" fill="none" stroke="{TEXT}" stroke-width="2" marker-end="url(#arrow-dim)"/>
        <text x="486" y="112" fill="{TEXT_DIM}" font-size="11.5">&#937;</text>
        <line x1="376" y1="252" x2="430" y2="252" stroke="{VORTICITY}" stroke-width="2.5" marker-end="url(#arrow-purple)"/>
        <line x1="532" y1="252" x2="478" y2="252" stroke="{VORTICITY}" stroke-width="2.5" marker-end="url(#arrow-purple)"/>
        <text x="330" y="356" fill="{TEXT}" font-size="12">Chains stretched around the rod act</text>
        <text x="330" y="374" fill="{TEXT}" font-size="12">like hoops under tension N&#8321;. Curved</text>
        <text x="330" y="392" fill="{TEXT}" font-size="12">streamlines squeeze inward &#8212; and up.</text>

        <rect x="608" y="68" width="256" height="330" rx="8" fill="{SURFACE_RAISED}"/>
        <text x="626" y="94" fill="{WARNING}" font-size="13.5" font-weight="700">Die swell (extrudate swell)</text>
        <rect x="636" y="126" width="118" height="58" fill="url(#hatch-wall)" stroke="{BORDER_STRONG}" stroke-width="1.5"/>
        <rect x="636" y="146" width="118" height="18" fill="{rgba(VISCOUS,0.3)}"/>
        <path d="M 754 146 Q 782 140 790 128 L 790 182 Q 782 170 754 164 Z" fill="{rgba(VISCOUS,0.3)}" stroke="{VISCOUS}" stroke-width="2"/>
        <line x1="800" y1="128" x2="800" y2="182" stroke="{TEXT_DIM}" stroke-width="1.5" marker-start="url(#arrow-dim)" marker-end="url(#arrow-dim)"/>
        <text x="808" y="160" fill="{TEXT_DIM}" font-size="11.5">D</text>
        <line x1="694" y1="196" x2="694" y2="212" stroke="{TEXT_DIM}" stroke-width="1"/>
        <text x="640" y="228" fill="{TEXT_DIM}" font-size="11.5">the melt leaves wider than the die</text>
        <text x="626" y="262" fill="{TEXT}" font-size="12">Inside the die the chains are</text>
        <text x="626" y="280" fill="{TEXT}" font-size="12">stretched along the flow. Once the</text>
        <text x="626" y="298" fill="{TEXT}" font-size="12">wall stops holding them they recoil,</text>
        <text x="626" y="316" fill="{TEXT}" font-size="12">shortening the jet and fattening it.</text>
        <text x="626" y="344" fill="{TEXT_DIM}" font-size="11.5">A Newtonian jet only contracts slightly,</text>
        <text x="626" y="362" fill="{TEXT_DIM}" font-size="11.5">and for an entirely different reason</text>
        <text x="626" y="380" fill="{TEXT_DIM}" font-size="11.5">(rearranging its velocity profile).</text>
    </svg>
    """


def diagram_deborah_timescales() -> str:
    """The relaxation time against the process time, on one logarithmic line."""
    return f"""
    <svg viewBox="0 0 880 320" width="100%" height="320" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="30" fill="{TEXT}" font-size="17" font-weight="bold">Solid or liquid is not a property of the material alone &#8212; De = &#955; / t_process decides</text>
        <text x="24" y="52" fill="{TEXT_DIM}" font-size="12">Same material, different process time, different answer. Glass flows and water is a solid, if you choose the clock to make it so.</text>

        <line x1="64" y1="150" x2="836" y2="150" stroke="{TEXT_MUTED}" stroke-width="2"/>
        <text x="64" y="182" fill="{TEXT_DIM}" font-size="11.5">10&#8315;&#185;&#178; s</text>
        <text x="248" y="182" fill="{TEXT_DIM}" font-size="11.5">10&#8315;&#8310; s</text>
        <text x="432" y="182" fill="{TEXT_DIM}" font-size="11.5">1 s</text>
        <text x="616" y="182" fill="{TEXT_DIM}" font-size="11.5">10&#8310; s (&#8776; 12 days)</text>
        <text x="790" y="182" fill="{TEXT_DIM}" font-size="11.5">10&#185;&#178; s</text>
        <text x="380" y="206" fill="{TEXT_DIM}" font-size="12">relaxation time &#955; of the microstructure (logarithmic)</text>

        <line x1="80" y1="150" x2="80" y2="132" stroke="{SUCCESS}" stroke-width="2"/>
        <circle cx="80" cy="150" r="5" fill="{SUCCESS}"/>
        <text x="62" y="124" fill="{SUCCESS}" font-size="11.5">water</text>
        <line x1="330" y1="150" x2="330" y2="120" stroke="{ACCENT}" stroke-width="2"/>
        <circle cx="330" cy="150" r="5" fill="{ACCENT}"/>
        <text x="286" y="112" fill="{ACCENT}" font-size="11.5">dilute polymer</text>
        <line x1="466" y1="150" x2="466" y2="132" stroke="{VISCOUS}" stroke-width="2"/>
        <circle cx="466" cy="150" r="5" fill="{VISCOUS}"/>
        <text x="436" y="124" fill="{VISCOUS}" font-size="11.5">polymer melt</text>
        <line x1="700" y1="150" x2="700" y2="120" stroke="{WARNING}" stroke-width="2"/>
        <circle cx="700" cy="150" r="5" fill="{WARNING}"/>
        <text x="668" y="112" fill="{WARNING}" font-size="11.5">pitch, glacier ice</text>

        <rect x="64" y="228" width="374" height="76" rx="8" fill="{rgba(SUCCESS,0.10)}" stroke="{SUCCESS}" stroke-width="1.5"/>
        <text x="82" y="252" fill="{SUCCESS}" font-size="13" font-weight="700">De &#8810; 1 &#183; liquid-like</text>
        <text x="82" y="274" fill="{TEXT}" font-size="12">The structure relaxes many times over during the process,</text>
        <text x="82" y="292" fill="{TEXT}" font-size="12">so it never notices the flow. Use a viscous model.</text>

        <rect x="462" y="228" width="374" height="76" rx="8" fill="{rgba(PRESSURE,0.10)}" stroke="{PRESSURE}" stroke-width="1.5"/>
        <text x="480" y="252" fill="{PRESSURE}" font-size="13" font-weight="700">De &#8811; 1 &#183; solid-like</text>
        <text x="480" y="274" fill="{TEXT}" font-size="12">The process finishes before the structure can respond,</text>
        <text x="480" y="292" fill="{TEXT}" font-size="12">so the deformation is stored, not dissipated.</text>
    </svg>
    """


# =============================================================================
# Control-volume momentum: what crosses the boundary is the whole answer
# =============================================================================

def diagram_momentum_control_volume() -> str:
    """A reducing bend: the four boundary terms, and the reaction that balances them."""
    return f"""
    <svg viewBox="0 0 880 500" width="100%" height="500" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="26" fill="{ACCENT}" font-size="15" font-weight="bold">Momentum on a control volume &#183; only the boundary appears in the balance</text>
        <text x="24" y="46" fill="{TEXT_DIM}" font-size="12">The interior may separate, swirl and dissipate; none of that enters the balance. Momentum counts only the boundary.</text>

        <path d="M 100 110 L 380 110 Q 500 110 500 230 L 500 360 L 440 360 L 440 230 Q 440 170 380 170 L 100 170 Z"
              fill="{rgba(ACCENT, 0.16)}" stroke="{ACCENT}" stroke-width="2"/>
        <rect x="80" y="72" width="470" height="300" rx="10" fill="none" stroke="{WARNING}" stroke-width="2" stroke-dasharray="10,6"/>
        <text x="82" y="66" fill="{WARNING}" font-size="12.5" font-weight="700">control surface &#183; you choose where it cuts</text>

        <line x1="34" y1="140" x2="92" y2="140" stroke="{ACCENT}" stroke-width="3" marker-end="url(#arrow-sky)"/>
        <text x="30" y="128" fill="{ACCENT}" font-size="12.5" font-weight="700">inlet 1</text>

        <line x1="120" y1="140" x2="205" y2="140" stroke="{PRESSURE}" stroke-width="3.5" marker-end="url(#arrow-red)"/>
        <text x="122" y="132" fill="{PRESSURE}" font-size="13" font-weight="700">p{_sub("1")}A{_sub("1")}</text>
        <line x1="250" y1="140" x2="335" y2="140" stroke="{SUCCESS}" stroke-width="3.5" marker-end="url(#arrow-green)"/>
        <text x="252" y="132" fill="{SUCCESS}" font-size="13" font-weight="700">m&#775;u{_sub("1")}</text>
        <text x="100" y="196" fill="{TEXT_DIM}" font-size="11.5">pressure pushes in &#183; the flow carries momentum in</text>

        <line x1="455" y1="378" x2="455" y2="432" stroke="{PRESSURE}" stroke-width="3.5" marker-end="url(#arrow-red)"/>
        <text x="400" y="452" fill="{PRESSURE}" font-size="13" font-weight="700">p{_sub("2")}A{_sub("2")}</text>
        <line x1="520" y1="378" x2="520" y2="432" stroke="{SUCCESS}" stroke-width="3.5" marker-end="url(#arrow-green)"/>
        <text x="500" y="452" fill="{SUCCESS}" font-size="13" font-weight="700">m&#775;u{_sub("2")}</text>
        <text x="380" y="474" fill="{ACCENT}" font-size="12.5" font-weight="700">outlet 2 &#183; both terms leave</text>

        <circle cx="480" cy="230" r="6" fill="{VORTICITY}"/>
        <line x1="480" y1="230" x2="350" y2="230" stroke="{VORTICITY}" stroke-width="4" marker-end="url(#arrow-purple)"/>
        <text x="150" y="226" fill="{VORTICITY}" font-size="13" font-weight="700">R &#8212; what the anchor holds</text>
        <text x="150" y="246" fill="{TEXT_DIM}" font-size="11.5">equal and opposite to the force on the fluid</text>

        <path d="M 386 286 q 20 -24 40 0 q 20 24 40 0" fill="none" stroke="{TEXT_FAINT}" stroke-width="2"/>
        <text x="100" y="330" fill="{TEXT_FAINT}" font-size="11.5">separation and swirl inside &#8212; unknown,</text>
        <text x="100" y="348" fill="{TEXT_FAINT}" font-size="11.5">and never needed</text>

        <rect x="590" y="96" width="266" height="150" rx="8" fill="{rgba(SUCCESS, 0.12)}" stroke="{SUCCESS}" stroke-width="1.6"/>
        <text x="608" y="128" fill="{TEXT}" font-size="14" font-family="'JetBrains Mono', monospace">&#931;F = m&#775;u{_sub("2")} &#8722; m&#775;u{_sub("1")}</text>
        <text x="608" y="156" fill="{TEXT_DIM}" font-size="12">steady flow, one inlet, one outlet.</text>
        <text x="608" y="180" fill="{TEXT_DIM}" font-size="12">A vector equation: write one scalar</text>
        <text x="608" y="198" fill="{TEXT_DIM}" font-size="12">line per direction, in gauge pressure,</text>
        <text x="608" y="216" fill="{TEXT_DIM}" font-size="12">so the atmosphere cancels itself.</text>
        <text x="608" y="238" fill="{TEXT_DIM}" font-size="12">The force on the bend is &#8722;R.</text>

        <text x="590" y="290" fill="{TEXT}" font-size="12.5" font-weight="700">Where to cut it</text>
        <text x="590" y="312" fill="{TEXT_DIM}" font-size="11.5">Across a plane where the flow is</text>
        <text x="590" y="330" fill="{TEXT_DIM}" font-size="11.5">parallel, so the pressure is uniform</text>
        <text x="590" y="348" fill="{TEXT_DIM}" font-size="11.5">and one velocity describes the face.</text>
        <text x="590" y="366" fill="{TEXT_DIM}" font-size="11.5">Never through a jet, an eddy, or a</text>
        <text x="590" y="384" fill="{TEXT_DIM}" font-size="11.5">section that is still turning.</text>
    </svg>
    """


def diagram_hydraulic_jump() -> str:
    """The free-surface shock: momentum survives it, energy does not."""
    return f"""
    <svg viewBox="0 0 860 460" width="100%" height="460" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="28" fill="{ACCENT}" font-size="15" font-weight="bold">Hydraulic jump &#183; a shock with a free surface</text>
        <text x="24" y="48" fill="{TEXT_DIM}" font-size="12">Fast shallow supercritical flow cannot slow down smoothly. It jumps, and the jump grinds the surplus energy into turbulence and heat.</text>

        <line x1="60" y1="112" x2="380" y2="112" stroke="{PRESSURE}" stroke-width="2" stroke-dasharray="9,5"/>
        <line x1="470" y1="168" x2="800" y2="168" stroke="{PRESSURE}" stroke-width="2" stroke-dasharray="9,5"/>
        <path d="M 380 112 q 45 8 90 56" fill="none" stroke="{PRESSURE}" stroke-width="2" stroke-dasharray="4,4"/>
        <text x="62" y="104" fill="{PRESSURE}" font-size="12" font-weight="600">energy grade line E{_sub("1")}</text>
        <text x="640" y="160" fill="{PRESSURE}" font-size="12" font-weight="600">E{_sub("2")} &lt; E{_sub("1")}</text>
        <line x1="424" y1="112" x2="424" y2="168" stroke="{WARNING}" stroke-width="2.5" marker-start="url(#arrow-dim)" marker-end="url(#arrow-dim)"/>
        <text x="434" y="140" fill="{WARNING}" font-size="12.5" font-weight="700">&#916;E = (y{_sub("2")}&#8722;y{_sub("1")})&#179;/(4y{_sub("1")}y{_sub("2")})</text>

        <path d="M 60 300 L 350 300 Q 420 300 450 250 Q 480 210 540 210 L 800 210 L 800 360 L 60 360 Z" fill="{rgba(ACCENT, 0.20)}"/>
        <path d="M 60 300 L 350 300 Q 420 300 450 250 Q 480 210 540 210 L 800 210" fill="none" stroke="{ACCENT}" stroke-width="2.5"/>
        <line x1="60" y1="360" x2="800" y2="360" stroke="{SHEAR}" stroke-width="4"/>
        <text x="300" y="384" fill="{SHEAR}" font-size="12">horizontal bed &#8212; over this short reach, bed friction is negligible</text>

        <path d="M 400 268 q 22 -26 42 -6 M 430 250 q 22 -26 44 -8 M 462 232 q 20 -24 40 -8" fill="none" stroke="{TEXT_FAINT}" stroke-width="2"/>
        <text x="360" y="212" fill="{TEXT_FAINT}" font-size="11.5">roller: violent, unsteady, unmodelled</text>

        <line x1="120" y1="300" x2="120" y2="360" stroke="{WARNING}" stroke-width="1.8" marker-start="url(#arrow-dim)" marker-end="url(#arrow-dim)"/>
        <text x="128" y="336" fill="{WARNING}" font-size="12.5" font-weight="700">y{_sub("1")}</text>
        <line x1="700" y1="210" x2="700" y2="360" stroke="{WARNING}" stroke-width="1.8" marker-start="url(#arrow-dim)" marker-end="url(#arrow-dim)"/>
        <text x="710" y="292" fill="{WARNING}" font-size="12.5" font-weight="700">y{_sub("2")}</text>

        <line x1="150" y1="330" x2="270" y2="330" stroke="{SUCCESS}" stroke-width="3.5" marker-end="url(#arrow-green)"/>
        <text x="150" y="322" fill="{SUCCESS}" font-size="12.5" font-weight="700">u{_sub("1")} &#183; Fr{_sub("1")} &gt; 1</text>
        <line x1="560" y1="290" x2="640" y2="290" stroke="{SUCCESS}" stroke-width="3.5" marker-end="url(#arrow-green)"/>
        <text x="556" y="282" fill="{SUCCESS}" font-size="12.5" font-weight="700">u{_sub("2")} &#183; Fr{_sub("2")} &lt; 1</text>

        <rect x="86" y="252" width="30" height="108" fill="{rgba(PRESSURE,0.22)}" stroke="{PRESSURE}" stroke-width="1.4"/>
        <text x="24" y="246" fill="{PRESSURE}" font-size="12" font-weight="700">&#189;&#961;gy{_sub("1")}&#178;</text>
        <rect x="760" y="210" width="30" height="150" fill="{rgba(PRESSURE,0.22)}" stroke="{PRESSURE}" stroke-width="1.4"/>
        <text x="748" y="200" fill="{PRESSURE}" font-size="12" font-weight="700">&#189;&#961;gy{_sub("2")}&#178;</text>

        <rect x="150" y="396" width="560" height="50" rx="8" fill="{rgba(SUCCESS,0.12)}" stroke="{SUCCESS}" stroke-width="1.6"/>
        <text x="172" y="426" fill="{TEXT}" font-size="14" font-family="'JetBrains Mono', monospace">M = q&#178;/(gy) + y&#178;/2 is equal on both sides &#8658; y{_sub("2")}/y{_sub("1")} = &#189;(&#8730;(1+8Fr{_sub("1")}&#178;) &#8722; 1)</text>
    </svg>
    """


def diagram_weir_and_gate() -> str:
    """Two structures that set the flow by controlling geometry, not roughness."""
    return f"""
    <svg viewBox="0 0 880 430" width="100%" height="430" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="28" fill="{ACCENT}" font-size="15" font-weight="bold">Weir and sluice gate &#183; one measured depth is enough</text>
        <text x="24" y="48" fill="{TEXT_DIM}" font-size="12">Neither device needs the channel roughness: the geometry sets the flow, so one head reading fixes the discharge.</text>

        <rect x="16" y="64" width="424" height="352" rx="8" fill="{SURFACE_RAISED}"/>
        <text x="34" y="90" fill="{ACCENT}" font-size="13.5" font-weight="700">Sharp-crested weir &#183; energy over the crest</text>

        <path d="M 40 150 L 250 150 Q 288 150 300 176 Q 320 226 352 300 L 40 300 Z" fill="{rgba(ACCENT,0.20)}"/>
        <path d="M 40 150 L 250 150 Q 288 150 300 176 Q 320 226 352 300" fill="none" stroke="{ACCENT}" stroke-width="2.5"/>
        <rect x="286" y="196" width="16" height="104" fill="url(#hatch-wall)" stroke="{BORDER_STRONG}" stroke-width="1.6"/>
        <line x1="40" y1="300" x2="410" y2="300" stroke="{SHEAR}" stroke-width="3.5"/>

        <line x1="120" y1="150" x2="120" y2="196" stroke="{WARNING}" stroke-width="1.8" marker-start="url(#arrow-dim)" marker-end="url(#arrow-dim)"/>
        <text x="128" y="178" fill="{WARNING}" font-size="12.5" font-weight="700">H</text>
        <line x1="120" y1="196" x2="120" y2="300" stroke="{TEXT_DIM}" stroke-width="1.6" marker-start="url(#arrow-dim)" marker-end="url(#arrow-dim)"/>
        <text x="128" y="252" fill="{TEXT_DIM}" font-size="12.5" font-weight="700">P</text>
        <line x1="60" y1="196" x2="286" y2="196" stroke="{TEXT_FAINT}" stroke-width="1.4" stroke-dasharray="5,4"/>
        <text x="176" y="190" fill="{TEXT_FAINT}" font-size="11">crest level</text>

        <line x1="316" y1="212" x2="342" y2="212" stroke="{SUCCESS}" stroke-width="2.5" marker-end="url(#arrow-green)"/>
        <line x1="326" y1="244" x2="362" y2="244" stroke="{SUCCESS}" stroke-width="2.5" marker-end="url(#arrow-green)"/>
        <line x1="334" y1="276" x2="378" y2="276" stroke="{SUCCESS}" stroke-width="2.5" marker-end="url(#arrow-green)"/>
        <text x="330" y="330" fill="{SUCCESS}" font-size="12" font-weight="700">u(h) = &#8730;(2gh)</text>
        <text x="330" y="348" fill="{TEXT_DIM}" font-size="11">deeper strips run faster</text>

        <text x="34" y="382" fill="{TEXT}" font-size="12.5">Integrate that over the nappe: Q = &#8532;C{_sub("d")}b&#8730;(2g)&#183;H&#179;&#8725;&#178;.</text>
        <text x="34" y="402" fill="{TEXT_DIM}" font-size="11.5">The &#8532; and the 3/2 are the integral; C{_sub("d")} carries contraction and viscosity.</text>

        <rect x="452" y="64" width="412" height="352" rx="8" fill="{SURFACE_RAISED}"/>
        <text x="470" y="90" fill="{ACCENT}" font-size="13.5" font-weight="700">Sluice gate &#183; momentum gives the load on the gate</text>

        <path d="M 470 140 L 660 140 L 660 258 L 840 258 L 840 300 L 470 300 Z" fill="{rgba(ACCENT,0.20)}"/>
        <path d="M 470 140 L 660 140" fill="none" stroke="{ACCENT}" stroke-width="2.5"/>
        <path d="M 676 258 L 840 258" fill="none" stroke="{ACCENT}" stroke-width="2.5"/>
        <line x1="470" y1="300" x2="840" y2="300" stroke="{SHEAR}" stroke-width="3.5"/>
        <rect x="660" y="96" width="16" height="162" fill="url(#hatch-wall)" stroke="{BORDER_STRONG}" stroke-width="1.6"/>
        <text x="612" y="90" fill="{TEXT_DIM}" font-size="11.5">gate</text>

        <line x1="520" y1="140" x2="520" y2="300" stroke="{WARNING}" stroke-width="1.8" marker-start="url(#arrow-dim)" marker-end="url(#arrow-dim)"/>
        <text x="528" y="226" fill="{WARNING}" font-size="12.5" font-weight="700">y{_sub("1")}</text>
        <line x1="690" y1="258" x2="690" y2="300" stroke="{VORTICITY}" stroke-width="1.8" marker-start="url(#arrow-dim)" marker-end="url(#arrow-dim)"/>
        <text x="698" y="284" fill="{VORTICITY}" font-size="12" font-weight="700">a</text>
        <line x1="790" y1="258" x2="790" y2="300" stroke="{SUCCESS}" stroke-width="1.8" marker-start="url(#arrow-dim)" marker-end="url(#arrow-dim)"/>
        <text x="798" y="284" fill="{SUCCESS}" font-size="12" font-weight="700">y{_sub("2")} = C{_sub("c")}a</text>

        <rect x="494" y="180" width="26" height="120" fill="{rgba(PRESSURE,0.22)}" stroke="{PRESSURE}" stroke-width="1.4"/>
        <text x="470" y="172" fill="{PRESSURE}" font-size="11.5" font-weight="700">&#189;&#961;gy{_sub("1")}&#178;</text>
        <line x1="700" y1="180" x2="676" y2="180" stroke="{PRESSURE}" stroke-width="3.5" marker-end="url(#arrow-red)"/>
        <text x="706" y="176" fill="{PRESSURE}" font-size="12" font-weight="700">F on gate</text>

        <text x="470" y="354" fill="{TEXT}" font-size="12.5">Energy: q = y{_sub("1")}y{_sub("2")}&#8730;(2g/(y{_sub("1")}+y{_sub("2")})).  Momentum then gives F.</text>
        <text x="470" y="376" fill="{TEXT_DIM}" font-size="11.5">F is well below &#189;&#961;gy{_sub("1")}&#178;: the flow leaves carrying momentum, and the gate</text>
        <text x="470" y="394" fill="{TEXT_DIM}" font-size="11.5">is only charged for the difference.</text>
    </svg>
    """


def diagram_rocket_control_volume() -> str:
    """A control volume whose mass is falling, and the two terms of thrust."""
    return f"""
    <svg viewBox="0 0 880 470" width="100%" height="470" xmlns="http://www.w3.org/2000/svg"
         style="background-color: {SURFACE}; border-radius: 8px; border: 1px solid {BORDER}; font-family: Inter, sans-serif;">
        {_arrow_defs()}
        <text x="24" y="26" fill="{ACCENT}" font-size="15" font-weight="bold">Rocket &#183; a control volume that loses mass, and gets pushed for it</text>
        <text x="24" y="46" fill="{TEXT_DIM}" font-size="12">Nothing is pushing against the outside air. The thrust is the momentum the nozzle throws backwards, plus the pressure the exit plane fails to match.</text>

        <rect x="150" y="76" width="180" height="282" rx="10" fill="none" stroke="{WARNING}" stroke-width="2" stroke-dasharray="10,6"/>
        <text x="150" y="70" fill="{WARNING}" font-size="12.5" font-weight="700">control volume, moving with the rocket</text>

        <path d="M 222 130 q 18 -36 36 0 Z" fill="{rgba(ACCENT,0.30)}" stroke="{ACCENT}" stroke-width="2"/>
        <rect x="222" y="130" width="36" height="150" fill="{rgba(ACCENT,0.22)}" stroke="{ACCENT}" stroke-width="2"/>
        <path d="M 222 280 L 258 280 L 278 344 L 202 344 Z" fill="{rgba(ACCENT,0.22)}" stroke="{ACCENT}" stroke-width="2"/>

        <line x1="190" y1="190" x2="190" y2="250" stroke="{TEXT_MUTED}" stroke-width="3" marker-end="url(#arrow-dim)"/>
        <text x="60" y="216" fill="{TEXT_MUTED}" font-size="12.5" font-weight="700">weight m(t)g</text>
        <text x="60" y="234" fill="{TEXT_DIM}" font-size="11.5">m is falling</text>

        <line x1="300" y1="250" x2="300" y2="168" stroke="{VORTICITY}" stroke-width="4" marker-end="url(#arrow-purple)"/>
        <text x="336" y="196" fill="{VORTICITY}" font-size="12.5" font-weight="700">F = m&#775;v{_sub("e")} + (p{_sub("e")}&#8722;p{_sub("a")})A{_sub("e")}</text>
        <text x="336" y="240" fill="{TEXT_DIM}" font-size="11.5">mass m(t), falling at m&#775;</text>
        <text x="336" y="258" fill="{TEXT_DIM}" font-size="11.5">the chamber is unmodelled</text>

        <line x1="240" y1="352" x2="240" y2="428" stroke="{SUCCESS}" stroke-width="4" marker-end="url(#arrow-green)"/>
        <text x="258" y="404" fill="{SUCCESS}" font-size="13" font-weight="700">m&#775;v{_sub("e")} &#183; momentum thrust</text>
        <line x1="170" y1="352" x2="170" y2="404" stroke="{PRESSURE}" stroke-width="3.5" marker-end="url(#arrow-red)"/>
        <text x="24" y="446" fill="{PRESSURE}" font-size="12.5" font-weight="700">(p{_sub("e")} &#8722; p{_sub("a")})A{_sub("e")} &#183; the atmosphere missing at the exit plane</text>

        <rect x="478" y="88" width="378" height="152" rx="8" fill="{rgba(SUCCESS,0.12)}" stroke="{SUCCESS}" stroke-width="1.6"/>
        <text x="498" y="116" fill="{SUCCESS}" font-size="13" font-weight="700">Newton on the shrinking mass</text>
        <text x="498" y="142" fill="{TEXT}" font-size="13" font-family="'JetBrains Mono', monospace">m dv/dt = &#8722;c dm/dt &#8722; mg &#8722; D</text>
        <text x="498" y="170" fill="{TEXT}" font-size="12">Divide by m and integrate: the mass can only</text>
        <text x="498" y="188" fill="{TEXT}" font-size="12">appear as dm/m, so the answer is a logarithm.</text>
        <text x="498" y="218" fill="{TEXT}" font-size="13" font-family="'JetBrains Mono', monospace">&#916;v = c&#183;ln(m&#8320;/m{_sub("f")}) &#8722; g&#183;t{_sub("b")} &#8722; drag</text>

        <rect x="478" y="258" width="378" height="176" rx="8" fill="{rgba(PRESSURE,0.10)}" stroke="{PRESSURE}" stroke-width="1.5"/>
        <text x="498" y="286" fill="{PRESSURE}" font-size="13" font-weight="700">What the logarithm costs you</text>
        <text x="498" y="312" fill="{TEXT}" font-size="12">Doubling &#916;v does not double the propellant:</text>
        <text x="498" y="330" fill="{TEXT}" font-size="12">it squares the mass ratio, m&#8320;/m{_sub("f")} = exp(&#916;v/c).</text>
        <text x="498" y="358" fill="{TEXT}" font-size="12">A long, gentle burn also pays g&#183;t{_sub("b")} to gravity,</text>
        <text x="498" y="376" fill="{TEXT}" font-size="12">which is why a launcher leaves the pad hard</text>
        <text x="498" y="394" fill="{TEXT}" font-size="12">and turns downrange as soon as it can.</text>
        <text x="498" y="420" fill="{TEXT_DIM}" font-size="11.5">Vacuum thrust exceeds sea-level thrust by p&#8336;A{_sub("e")}.</text>
    </svg>
    """


# =============================================================================
# Rocket nozzles: the atmosphere, the plume, and how the contour is drawn
# =============================================================================

def _nozzle_half_walls(px: float, py: float) -> str:
    """One small bell in outline, throat at px+44, exit at px+124.

    Shared by the four regime panels so that the *only* difference between them
    is the plume, which is the entire point of that figure.
    """
    upper = (f"M {px + 8} {py - 30} L {px + 44} {py - 12} "
             f"Q {px + 74} {py - 34} {px + 124} {py - 28}")
    lower = (f"M {px + 8} {py + 30} L {px + 44} {py + 12} "
             f"Q {px + 74} {py + 34} {px + 124} {py + 28}")
    return (f'<path d="{upper}" fill="none" stroke="{TEXT_MUTED}" stroke-width="4" '
            f'stroke-linecap="round"/>'
            f'<path d="{lower}" fill="none" stroke="{TEXT_MUTED}" stroke-width="4" '
            f'stroke-linecap="round"/>'
            f'<line x1="{px + 44}" y1="{py - 12}" x2="{px + 44}" y2="{py + 12}" '
            f'stroke="{WARNING}" stroke-width="1.4" stroke-dasharray="3,3"/>'
            f'<line x1="{px + 8}" y1="{py}" x2="{px + 210}" y2="{py}" '
            f'stroke="{TEXT_FAINT}" stroke-width="1" stroke-dasharray="7,5"/>')


def diagram_nozzle_expansion_regimes() -> str:
    """The same nozzle in four atmospheres, and what the plume does about it.

    The exit pressure is a property of the *nozzle*: area ratio and chamber
    state fix it, and it does not care what is outside. The ambient pressure is
    a property of the *altitude*. Everything in this figure is the mismatch
    between those two numbers being settled outside the nozzle, or -- in the
    last panel -- forcing its way back inside.

    Each caption is pre-split into drawn lines. Wrapping text after a `_sub`
    substitution would cut a `<tspan>` in half and produce markup that is no
    longer well formed.
    """
    layout = (
        (60, 130, PRESSURE, "Under-expanded", "p&#8337; &gt; p&#8336;",
         ("High altitude, or too small an area ratio. The jet is still",
          "above ambient when it leaves, so it keeps expanding: a",
          "Prandtl&#8211;Meyer fan opens from each lip and the plume balloons."),
         "The unused pressure is thrust you did not collect."),
        (500, 130, SUCCESS, "Matched", "p&#8337; = p&#8336;",
         ("The design point, and the only one at which the plume leaves",
          "straight. Thrust is maximal for this chamber at this altitude,",
          "because dF/dA&#8337; = (p&#8337; &#8722; p&#8336;) is exactly zero here."),
         "One altitude only: a fixed nozzle is matched at one place in the sky."),
        (60, 350, WARNING, "Over-expanded, still attached", "p&#8337; &lt; p&#8336;",
         ("Sea level with a large bell. The jet is squeezed back to ambient",
          "by oblique shocks from the lips, which reflect and cross &#8212; the",
          "shock diamonds you can see in a first-stage exhaust."),
         "The last of the bell is pushed backwards, so C&#8347; drops."),
        (500, 350, PRESSURE, "Over-expanded to separation", "p&#8337; &#8810; p&#8336;",
         ("Push further and the boundary layer cannot survive the adverse",
          "gradient. The shock jumps inside, the flow tears off the wall,",
          "and the separation line wanders asymmetrically."),
         "Side loads here have damaged real engines. Do not design into it."),
    )
    panels = []
    for px, py, colour, title, relation, body, sting in layout:
        block = [_nozzle_half_walls(px, py)]
        block.append(
            f'<text x="{px + 8}" y="{py - 58}" fill="{colour}" font-size="13.5" '
            f'font-weight="bold">{title}</text>')
        block.append(
            f'<text x="{px + 8}" y="{py - 41}" fill="{TEXT}" font-size="12.5" '
            f'font-family="JetBrains Mono, monospace">{relation}</text>')
        if title.startswith("Under"):
            block.append(
                f'<path d="M {px + 124} {py - 28} Q {px + 168} {py - 62} {px + 214} {py - 52} '
                f'M {px + 124} {py + 28} Q {px + 168} {py + 62} {px + 214} {py + 52}" '
                f'fill="none" stroke="{colour}" stroke-width="2.4"/>')
            for k in range(4):
                block.append(
                    f'<line x1="{px + 124}" y1="{py - 28}" '
                    f'x2="{px + 150 + 16 * k}" y2="{py - 6 + 12 * k}" '
                    f'stroke="{rgba(colour, 0.55)}" stroke-width="1"/>')
                block.append(
                    f'<line x1="{px + 124}" y1="{py + 28}" '
                    f'x2="{px + 150 + 16 * k}" y2="{py + 6 - 12 * k}" '
                    f'stroke="{rgba(colour, 0.55)}" stroke-width="1"/>')
            block.append(
                f'<text x="{px + 148}" y="{py - 58}" fill="{colour}" font-size="11">'
                f'expansion fans</text>')
        elif title == "Matched":
            block.append(
                f'<path d="M {px + 124} {py - 28} L {px + 214} {py - 28} '
                f'M {px + 124} {py + 28} L {px + 214} {py + 28}" fill="none" '
                f'stroke="{colour}" stroke-width="2.4"/>')
            block.append(
                f'<text x="{px + 134}" y="{py - 36}" fill="{colour}" font-size="11">'
                f'parallel plume, no waves</text>')
        elif title.startswith("Over-expanded, still"):
            block.append(
                f'<path d="M {px + 124} {py - 28} Q {px + 158} {py - 12} {px + 214} {py - 20} '
                f'M {px + 124} {py + 28} Q {px + 158} {py + 12} {px + 214} {py + 20}" '
                f'fill="none" stroke="{colour}" stroke-width="2.4"/>')
            block.append(
                f'<path d="M {px + 124} {py - 28} L {px + 162} {py} L {px + 200} {py - 24} '
                f'M {px + 124} {py + 28} L {px + 162} {py} L {px + 200} {py + 24}" '
                f'fill="none" stroke="{PRESSURE}" stroke-width="2"/>')
            block.append(
                f'<text x="{px + 138}" y="{py - 40}" fill="{PRESSURE}" font-size="11">'
                f'oblique shocks, crossing</text>')
        else:
            block.append(
                f'<line x1="{px + 92}" y1="{py - 22}" x2="{px + 92}" y2="{py + 22}" '
                f'stroke="{PRESSURE}" stroke-width="3"/>')
            block.append(
                f'<path d="M {px + 92} {py - 22} Q {px + 130} {py - 14} {px + 214} {py - 18} '
                f'M {px + 92} {py + 22} Q {px + 130} {py + 16} {px + 214} {py + 22}" '
                f'fill="none" stroke="{colour}" stroke-width="2.4"/>')
            block.append(
                f'<path d="M {px + 96} {py - 32} q 12 -6 24 -2 M {px + 96} {py + 32} '
                f'q 12 6 24 2" fill="none" stroke="{VORTICITY}" stroke-width="1.6" '
                f'stroke-dasharray="3,2"/>')
            # Both labels sit clear of the wall and the plume, with a leader
            # back to the feature they name.
            block.append(
                f'<line x1="{px + 146}" y1="{py - 32}" x2="{px + 98}" y2="{py - 24}" '
                f'stroke="{rgba(PRESSURE, 0.7)}" stroke-width="1"/>')
            block.append(
                f'<text x="{px + 150}" y="{py - 30}" fill="{PRESSURE}" font-size="11">'
                f'shock inside the bell</text>')
            block.append(
                f'<text x="{px + 104}" y="{py + 50}" fill="{VORTICITY}" font-size="11">'
                f'ambient air drawn back in</text>')
        for offset, text in ((62, body[0]), (78, body[1]), (94, body[2])):
            block.append(
                f'<text x="{px + 8}" y="{py + offset}" fill="{TEXT_MUTED}" '
                f'font-size="11.5">{text}</text>')
        block.append(
            f'<text x="{px + 8}" y="{py + 112}" fill="{colour}" font-size="11.5" '
            f'font-style="italic">{sting}</text>')
        panels.append("".join(block))

    return f'''
    <svg viewBox="0 0 940 500" width="100%" height="500" xmlns="http://www.w3.org/2000/svg"
         style="background:{SURFACE};border:1px solid {BORDER};border-radius:10px;font-family:Inter,sans-serif">
      {_arrow_defs()}
      <text x="24" y="30" fill="{TEXT}" font-size="17" font-weight="bold">One nozzle, four atmospheres &#183; the exit pressure never changes, only what meets it</text>
      <text x="24" y="50" fill="{TEXT_DIM}" font-size="12">Steady ideal gas &#183; the area ratio alone fixes p&#8337;/p&#8330; &#183; schematic plumes, angles not to scale</text>
      {"".join(panels)}
    </svg>'''


def diagram_rocket_pressure_thrust() -> str:
    """Where thrust is applied: unbalanced pressure on the inside of the engine.

    The control-volume figure of chapter 10 shows *that* the pressure term
    survives; this shows *where* the force acts. They are the same statement,
    and a reader who has seen only the first often believes the exhaust pushes
    on something behind the vehicle.
    """
    def bell(px: float, py: float) -> str:
        upper = (f"M {px} {py - 46} L {px + 22} {py - 46} L {px + 62} {py - 16} "
                 f"Q {px + 96} {py - 46} {px + 156} {py - 40}")
        lower = (f"M {px} {py + 46} L {px + 22} {py + 46} L {px + 62} {py + 16} "
                 f"Q {px + 96} {py + 46} {px + 156} {py + 40}")
        return (f'<path d="{upper}" fill="none" stroke="{TEXT_MUTED}" stroke-width="5" '
                f'stroke-linecap="round"/>'
                f'<path d="{lower}" fill="none" stroke="{TEXT_MUTED}" stroke-width="5" '
                f'stroke-linecap="round"/>'
                f'<line x1="{px}" y1="{py - 46}" x2="{px}" y2="{py + 46}" '
                f'stroke="{TEXT_MUTED}" stroke-width="5" stroke-linecap="round"/>')

    halves = []
    for px, ambient_arrows, colour, marker, ambient_label in (
            (70, 6, PRESSURE, "red", "sea level: p&#8336; = 101 kPa pushes back"),
            (540, 0, SUCCESS, "green", "vacuum: p&#8336; = 0, nothing pushes back")):
        py = 190
        block = [bell(px, py)]
        for x_off, y_off, dx, dy in ((26, 44, 0, 16), (48, 30, 10, 14),
                                     (78, 30, 8, 15), (112, 38, 4, 16),
                                     (144, 40, 2, 16)):
            block.append(
                f'<line x1="{px + x_off}" y1="{py - y_off}" '
                f'x2="{px + x_off - dx}" y2="{py - y_off - dy}" stroke="{PRESSURE}" '
                f'stroke-width="2" marker-end="url(#arrow-red)"/>')
            block.append(
                f'<line x1="{px + x_off}" y1="{py + y_off}" '
                f'x2="{px + x_off - dx}" y2="{py + y_off + dy}" stroke="{PRESSURE}" '
                f'stroke-width="2" marker-end="url(#arrow-red)"/>')
        block.append(
            f'<line x1="{px + 4}" y1="{py}" x2="{px - 34}" y2="{py}" '
            f'stroke="{PRESSURE}" stroke-width="4" marker-end="url(#arrow-red)"/>')
        # Clear of the wall-pressure arrows, whose tips reach py - 60.
        block.append(
            f'<text x="{px + 22}" y="{py - 96}" fill="{PRESSURE}" font-size="11.5">'
            f'gas pressure on the metal, everywhere</text>')
        block.append(
            f'<text x="{px + 22}" y="{py - 81}" fill="{PRESSURE}" font-size="11.5">'
            f'the atmosphere does not reach</text>')
        for k in range(ambient_arrows):
            y = py - 40 + 16 * k
            block.append(
                f'<line x1="{px + 202}" y1="{y}" x2="{px + 166}" y2="{y}" '
                f'stroke="{colour}" stroke-width="2" marker-end="url(#arrow-{marker})"/>')
        if not ambient_arrows:
            block.append(
                f'<text x="{px + 170}" y="{py + 4}" fill="{SUCCESS}" font-size="12">'
                f'&#8212; nothing &#8212;</text>')
        block.append(
            f'<line x1="{px + 156}" y1="{py - 40}" x2="{px + 156}" y2="{py + 40}" '
            f'stroke="{ACCENT}" stroke-width="2" stroke-dasharray="5,4"/>')
        block.append(
            f'<text x="{px + 88}" y="{py + 76}" fill="{ACCENT}" font-size="12">exit plane A{_sub("e")}</text>')
        block.append(
            f'<text x="{px + 4}" y="{py + 104}" fill="{colour}" font-size="12.5" '
            f'font-weight="bold">{ambient_label}</text>')
        halves.append("".join(block))

    return f'''
    <svg viewBox="0 0 1000 470" width="100%" height="470" xmlns="http://www.w3.org/2000/svg"
         style="background:{SURFACE};border:1px solid {BORDER};border-radius:10px;font-family:Inter,sans-serif">
      {_arrow_defs()}
      <text x="24" y="30" fill="{TEXT}" font-size="17" font-weight="bold">Thrust is a pressure integral over the inside of the engine, not a push against the air</text>
      <text x="24" y="50" fill="{TEXT_DIM}" font-size="12">Same engine, same chamber, same mass flow. The only difference between the two halves is what presses on the exit plane from outside.</text>
      <line x1="505" y1="72" x2="505" y2="320" stroke="{BORDER_STRONG}" stroke-width="1.5" stroke-dasharray="6,6"/>
      {"".join(halves)}
      <rect x="60" y="336" width="880" height="116" rx="8" fill="{rgba(ACCENT, 0.10)}" stroke="{ACCENT}" stroke-width="1.5"/>
      <text x="80" y="362" fill="{ACCENT}" font-size="13" font-weight="bold">The same force, counted two ways</text>
      <text x="80" y="388" fill="{TEXT}" font-size="12.5" font-family="JetBrains Mono, monospace">F = &#8747;(p &#8722; p{_sub("a")}) dA{_sub("axial")}  over every wetted surface   =   m&#775;v{_sub("e")} + (p{_sub("e")} &#8722; p{_sub("a")})A{_sub("e")}</text>
      <text x="80" y="414" fill="{TEXT_MUTED}" font-size="12">Left: add up the axial component of pressure on the metal &#8212; that is where the force is physically applied, and it is why a bell is a</text>
      <text x="80" y="432" fill="{TEXT_MUTED}" font-size="12">thrust-producing structure rather than a duct. Right: chapter 10&#8217;s control volume, which has already done that integral for you.</text>
    </svg>'''


def diagram_bell_contour_construction() -> str:
    """The draughtsman's recipe for a Rao bell, step by step and to scale.

    Every number on this figure is either a decision (the expansion ratio, the
    percentage bell) or a convention (the two throat arc radii). The only curve
    that is *computed* is the parabola, and it is fixed the moment its two end
    tangents are chosen.
    """
    ox, oy = 90, 300          # throat, on the axis of the drawing
    scale = 46.0              # pixels per throat radius
    rt = scale
    exit_r = 3.4 * scale      # about eps = 11.6, chosen so the figure fits
    bell_len = 5.1 * scale
    cone_len = 6.4 * scale
    arc_up, arc_down = 1.5 * scale, 0.382 * scale

    # Each body is pre-split into its two drawn lines. Wrapping after the
    # subscript substitution would cut a `<tspan>` in half and produce markup
    # that is no longer well formed, which is exactly how this figure first
    # failed its XML check.
    steps = (
        ("1", "Fix the expansion ratio",
         "&#949; = A{e}/A{t} sets r{e} = r{t}&#8730;&#949;.",
         "The exit radius is now not negotiable."),
        ("2", "Fix the length",
         "Draw the 15&#176; reference cone, then keep a stated",
         "fraction of its length. 80% is the usual choice."),
        ("3", "Round the throat",
         "Arc of 1.5 r{t} upstream, 0.382 r{t} downstream.",
         "Workshop convention, not a derivation."),
        ("4", "Sweep to &#952;n",
         "Follow the downstream arc until the wall angle",
         "reaches &#952;n. That end point is N."),
        ("5", "Join N to E",
         "One parabola, tangent to &#952;n at N and &#952;e at E:",
         "the quadratic B&#233;zier through their intersection."),
    )
    lines = []
    for index, (number, title, first, second) in enumerate(steps):
        y = 96 + 60 * index
        lines.append(
            f'<circle cx="628" cy="{y - 5}" r="11" fill="{rgba(ACCENT, 0.25)}" '
            f'stroke="{ACCENT}" stroke-width="1.5"/>')
        lines.append(
            f'<text x="628" y="{y}" fill="{ACCENT}" font-size="12" font-weight="bold" '
            f'text-anchor="middle">{number}</text>')
        lines.append(
            f'<text x="650" y="{y - 8}" fill="{TEXT}" font-size="13" '
            f'font-weight="bold">{title}</text>')
        for offset, text in ((10, first), (26, second)):
            text = text.replace("{e}", _sub("e")).replace("{t}", _sub("t"))
            lines.append(
                f'<text x="650" y="{y + offset}" fill="{TEXT_MUTED}" '
                f'font-size="11.5">{text}</text>')

    return f'''
    <svg viewBox="0 0 1000 420" width="100%" height="420" xmlns="http://www.w3.org/2000/svg"
         style="background:{SURFACE};border:1px solid {BORDER};border-radius:10px;font-family:Inter,sans-serif">
      {_arrow_defs()}
      <text x="24" y="30" fill="{TEXT}" font-size="17" font-weight="bold">Drawing the bell &#183; five decisions and one curve</text>
      <text x="24" y="50" fill="{TEXT_DIM}" font-size="12">Upper half only, drawn to scale. Angles are true here because this is a meridional section, not a projection.</text>

      <line x1="{ox - 70}" y1="{oy}" x2="{ox + cone_len + 40}" y2="{oy}" stroke="{TEXT_FAINT}" stroke-width="1.2" stroke-dasharray="8,5"/>
      <text x="{ox + cone_len + 46}" y="{oy + 5}" fill="{TEXT_FAINT}" font-size="11">axis</text>

      <path d="M {ox - 70} {oy - 2.6 * scale} L {ox - 34} {oy - 2.6 * scale} L {ox - arc_up * 0.5} {oy - 1.62 * scale} A {arc_up} {arc_up} 0 0 1 {ox} {oy - rt}"
            fill="none" stroke="{TEXT_MUTED}" stroke-width="4" stroke-linecap="round"/>
      <text x="{ox - 66}" y="{oy - 2.6 * scale - 12}" fill="{TEXT_MUTED}" font-size="11">chamber &#183; 1.5 r{_sub("t")} arc</text>

      <line x1="{ox}" y1="{oy}" x2="{ox}" y2="{oy - rt - 18}" stroke="{WARNING}" stroke-width="1.4" stroke-dasharray="4,3"/>
      <text x="{ox - 6}" y="{oy - rt - 24}" fill="{WARNING}" font-size="11.5" text-anchor="middle">throat r{_sub("t")}</text>

      <line x1="{ox}" y1="{oy - rt}" x2="{ox + cone_len}" y2="{oy - exit_r}" stroke="{SHEAR}" stroke-width="2" stroke-dasharray="7,5"/>
      <text x="{ox + cone_len + 8}" y="{oy - exit_r - 3}" fill="{SHEAR}" font-size="11.5">15&#176; reference cone &#183; step 2 keeps 80% of its length</text>

      <path d="M {ox} {oy - rt} A {arc_down} {arc_down} 0 0 1 {ox + 0.36 * scale} {oy - rt - 0.14 * scale}"
            fill="none" stroke="{VORTICITY}" stroke-width="4"/>
      <circle cx="{ox + 0.36 * scale}" cy="{oy - rt - 0.14 * scale}" r="4.5" fill="{VORTICITY}"/>
      <text x="{ox + 0.74 * scale}" y="{oy - 0.83 * scale}" fill="{VORTICITY}" font-size="11.5">N &#183; 0.382 r{_sub("t")} arc ends at &#952;n</text>

      <path d="M {ox + 0.36 * scale} {oy - rt - 0.14 * scale} Q {ox + 2.55 * scale} {oy - 2.86 * scale} {ox + bell_len} {oy - exit_r}"
            fill="none" stroke="{ACCENT}" stroke-width="4.5"/>
      <line x1="{ox + 0.36 * scale}" y1="{oy - rt - 0.14 * scale}" x2="{ox + 2.55 * scale}" y2="{oy - 2.86 * scale}" stroke="{rgba(ACCENT, 0.5)}" stroke-width="1.4" stroke-dasharray="4,3"/>
      <line x1="{ox + 2.55 * scale}" y1="{oy - 2.86 * scale}" x2="{ox + bell_len}" y2="{oy - exit_r}" stroke="{rgba(ACCENT, 0.5)}" stroke-width="1.4" stroke-dasharray="4,3"/>
      <circle cx="{ox + 2.55 * scale}" cy="{oy - 2.86 * scale}" r="4" fill="none" stroke="{ACCENT}" stroke-width="2"/>
      <text x="{ox + 2.75 * scale}" y="{oy - 2.78 * scale}" fill="{ACCENT}" font-size="11.5">tangents meet: the B&#233;zier control point</text>

      <circle cx="{ox + bell_len}" cy="{oy - exit_r}" r="4.5" fill="{SUCCESS}"/>
      <text x="{ox + bell_len - 34}" y="{oy - exit_r - 14}" fill="{SUCCESS}" font-size="11.5">E &#183; exit at &#952;e</text>
      <line x1="{ox + bell_len}" y1="{oy - exit_r}" x2="{ox + bell_len}" y2="{oy}" stroke="{SUCCESS}" stroke-width="1.4" stroke-dasharray="4,3"/>
      <text x="{ox + bell_len + 8}" y="{oy - exit_r / 2}" fill="{SUCCESS}" font-size="11.5">r{_sub("e")}</text>

      <line x1="{ox}" y1="{oy + 26}" x2="{ox + bell_len}" y2="{oy + 26}" stroke="{TEXT_DIM}" stroke-width="1.4" marker-start="url(#arrow-dim)" marker-end="url(#arrow-dim)"/>
      <text x="{ox + bell_len / 2}" y="{oy + 42}" fill="{TEXT_DIM}" font-size="11.5" text-anchor="middle">L = 0.8 &#215; cone length</text>

      {"".join(lines)}
    </svg>'''


def diagram_moc_wave_logic() -> str:
    """Why a wall that cancels its own waves is the shape you want.

    The computed characteristic mesh in the lesson shows *where* the waves go.
    This shows the three rules that put them there, each stated as a physical
    requirement rather than as a step in a recipe.
    """
    # Two drawn lines per rule, pre-split for the same reason as the bell
    # figure: a `<tspan>` subscript must never straddle a line break.
    rules = (
        (SUCCESS, "1 &#183; The corner sets the total turn",
         "A sonic stream turned through an angle &#952; reaches the Mach number whose "
         "Prandtl&#8211;Meyer angle is &#952;. So the wall turns away",
         "from the axis by &#957;(M{e})/2 to expand the gas, then turns back through the "
         "same angle so the exhaust leaves axial.",
         "&#952;{max} = &#957;(M{e}) / 2"),
        (ACCENT, "2 &#183; The axis reflects, because symmetry forbids crossing it",
         "A wave arriving at the centreline meets its own mirror image. The flow angle "
         "there must be zero, so the wave cannot",
         "pass through: it reflects, and the reflected wave carries the same strength "
         "back out as the opposite family.",
         "on the axis: K{plus} = &#8722;K{minus}"),
        (WARNING, "3 &#183; The wall cancels, because that is what you are designing it to do",
         "A reflected wave arriving at the wall would bounce again and ruin the uniform "
         "exit. Instead the contour is bent to exactly",
         "the local flow direction, so the wave is absorbed. Doing that at every "
         "arriving wave is the contour.",
         "at the wall: &#952;{wall} = &#952;{flow}"),
    )

    def _subscripts(text: str) -> str:
        for token, label in (("{e}", "e"), ("{max}", "max"), ("{plus}", "+"),
                             ("{minus}", "&#8722;"), ("{wall}", "wall"),
                             ("{flow}", "flow")):
            text = text.replace(token, _sub(label))
        return text

    blocks = []
    for index, (colour, title, first, second, formula) in enumerate(rules):
        y = 262 + 74 * index
        blocks.append(
            f'<rect x="24" y="{y - 20}" width="6" height="60" rx="3" fill="{colour}"/>')
        blocks.append(
            f'<text x="44" y="{y - 4}" fill="{colour}" font-size="13" '
            f'font-weight="bold">{title}</text>')
        for offset, text in ((14, first), (30, second)):
            blocks.append(
                f'<text x="44" y="{y + offset}" fill="{TEXT_MUTED}" '
                f'font-size="11.5">{_subscripts(text)}</text>')
        blocks.append(
            f'<text x="742" y="{y + 14}" fill="{colour}" font-size="12.5" '
            f'font-family="JetBrains Mono, monospace">{_subscripts(formula)}</text>')

    fan = []
    for k in range(6):
        fan.append(
            f'<line x1="150" y1="96" x2="{300 + 46 * k}" y2="190" stroke="{rgba(SUCCESS, 0.8)}" stroke-width="1.6"/>')
        fan.append(
            f'<line x1="{300 + 46 * k}" y1="190" x2="{452 + 46 * k}" y2="{120 - 4 * k}" stroke="{rgba(ACCENT, 0.8)}" stroke-width="1.6"/>')

    return f'''
    <svg viewBox="0 0 1000 500" width="100%" height="500" xmlns="http://www.w3.org/2000/svg"
         style="background:{SURFACE};border:1px solid {BORDER};border-radius:10px;font-family:Inter,sans-serif">
      {_arrow_defs()}
      <text x="24" y="30" fill="{TEXT}" font-size="17" font-weight="bold">Method of characteristics &#183; three rules, and the contour is the consequence</text>
      <text x="24" y="50" fill="{TEXT_DIM}" font-size="12">Upper half of a planar minimum-length nozzle</text>
      <line x1="120" y1="190" x2="720" y2="190" stroke="{TEXT_FAINT}" stroke-width="1.2" stroke-dasharray="8,5"/>
      <text x="726" y="194" fill="{TEXT_FAINT}" font-size="11">axis of symmetry</text>
      <path d="M 120 96 L 150 96 Q 300 40 700 66" fill="none" stroke="{TEXT_MUTED}" stroke-width="5" stroke-linecap="round"/>
      <circle cx="150" cy="96" r="6" fill="{WARNING}"/>
      <text x="112" y="84" fill="{WARNING}" font-size="12">sharp corner: the whole expansion happens here</text>
      {"".join(fan)}
      <text x="186" y="152" fill="{SUCCESS}" font-size="11.5">C&#8722; waves out</text>
      <text x="452" y="178" fill="{ACCENT}" font-size="11.5">C+ waves reflected off the axis</text>
      <text x="500" y="44" fill="{WARNING}" font-size="11.5">absorbed at the wall &#8212; nothing bounces back</text>
      <line x1="700" y1="66" x2="700" y2="190" stroke="{SUCCESS}" stroke-width="2" stroke-dasharray="5,4"/>
      <text x="708" y="128" fill="{SUCCESS}" font-size="11.5">uniform, axial,</text>
      <text x="708" y="144" fill="{SUCCESS}" font-size="11.5">M = M{_sub("e")} everywhere</text>
      <text x="24" y="230" fill="{TEXT}" font-size="14" font-weight="bold">Why those waves go where they do</text>
      {"".join(blocks)}
    </svg>'''
