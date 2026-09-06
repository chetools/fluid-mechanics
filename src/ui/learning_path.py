"""A consistent reading guide for the twelve lessons.

This module is the single source of truth for how the chapters are named and
divided. The navigation, the chapter header and the sidebar map all read it.
They used to carry three different sets of names and two different numberings
for the same twelve chapters -- a landing banner counted "01..06" while the
navigation beneath it counted 1..12, so "04 · External flow" in one was
chapter 8 in the other.
"""

from typing import List, Tuple

import streamlit as st

from src.ui.pedagogy import render_latex, render_prose_and_latex


# Six parts of two chapters each. Part names must not repeat: the old data had
# "SOLUTIONS & VERIFICATION" on both part 4 and part 6, and part 4 itself
# carried two different names on its two chapters.
PARTS: Tuple[Tuple[int, str, Tuple[int, int]], ...] = (
    (1, "Plant balances", (1, 2)),
    (2, "Scaling & regimes", (3, 4)),
    (3, "Local momentum", (5, 6)),
    (4, "Viscous solutions & drag", (7, 8)),
    (5, "Work & thermodynamics", (9, 10)),
    (6, "Computation & reference", (11, 12)),
)

# Short labels for the horizontal chapter navigation. Kept separate from the
# lesson titles because a twelve-option radio needs one or two words, while a
# chapter heading can afford a full title.
NAV_LABELS: Tuple[str, ...] = (
    "Energy", "Pipes", "Scaling", "Turbulence",
    "Euler", "Stress & NS", "Exact flows", "External flow",
    "Turbomachinery", "Compressible", "CFD", "Reference",
)

# title, question, prerequisites, route, core equation, interpretation, experiment
LESSONS = [
    (
        "Energy & Bernoulli",
        "Where does a pump's energy go?",
        "Conservation of energy; pressure and flow rate.",
        "Energy stores → injection work p/ρ → head balance → first-law derivation → heating example",
        r"H_1 + h_p = H_2 + h_L,\qquad H = \frac{p}{\rho g} + \frac{\alpha\bar{u}^2}{2g} + z",
        "A pump adds mechanical head. Elevation and pressure can store it; friction converts it into internal energy. Every term here is a length.",
        "For water, compare a 100 kPa frictional drop at 10 and 20 m³/h. The temperature rise stays about 0.024 K; hydraulic power doubles from 0.278 to 0.556 kW. Flow rate matters even when pressure drop is held fixed.",
    ),
    (
        "Pipe flow & pumping",
        "How much pressure and power will a transfer line need?",
        "Chapter 1: mechanical head; mean speed is Q/A.",
        "Darcy & Fanning → friction chart → pump sizing → suction head → schedules → network solver → open channels",
        r"h_L = \left(f_D\frac{L}{D}+\sum K\right)\frac{\bar{u}^2}{2g},\qquad P_{\mathrm{shaft}}=\frac{\rho g Q h_p}{\eta_p}",
        "Find velocity first, then Reynolds number, then friction factor. Add static head after calculating losses. NPSH is a separate check on the pump inlet.",
        "Keep flow rate, length, fluid, and fittings fixed; increase the pipe diameter. Observe the lower speed and pressure loss. Then raise the suction tank by 1 m: available NPSH should rise by exactly 1 m. For a canal at fixed depth, section and Manning roughness, quadrupling bed slope doubles capacity because Q grows as the square root of slope. The calculator instead holds discharge fixed: quadruple its slope and observe a lower normal depth.",
    ),
    (
        "Dimensional analysis",
        "When can one experiment describe many different fluids and pipes?",
        "Chapter 2: pressure loss and Reynolds number; powers of M, L, and T.",
        "Why scale → Buckingham's method → matrix kernel → named groups → information",
        r"\frac{\Delta p}{\rho\bar{u}^2}=\Phi\!\left(\frac{\rho\bar{u}D}{\mu},\frac{\varepsilon}{D},\frac{L}{D}\right)",
        "Seven dimensional variables of rank three give four independent groups: one response and three inputs. Dimensional analysis constrains the relationship; experiments or physics must still determine it.",
        "Choose the pipe-pressure-drop preset. Identify Eu as the response and Re, ε/D, L/D as inputs. Inspect the raw SVD basis: different-looking dimensionless products can describe the same space.",
    ),
    (
        "Laminar flow & turbulence",
        "Would many small laminar pipes cost less to pump through?",
        "Chapters 2–3: Darcy friction factor, fixed flow rate, and Reynolds number.",
        "Dye experiment → laminar force balance → profiles → wall layers → straw bundle",
        r"f_D=\frac{64}{\mathrm{Re}},\qquad \Delta p=\frac{128\mu LQ}{\pi D^4}\quad\text{(fully developed laminar pipe)}",
        "Laminar describes orderly motion, not necessarily low pumping cost. At fixed flow rate, a small diameter has a strong fourth-power penalty in laminar flow.",
        "In the straw lab, increase the number of straws while keeping total flow and outer diameter fixed. Read both plots: individual Reynolds number falls while pumping power can rise. Check whether each straw is actually laminar before using the exact laminar formula.",
    ),
    (
        "Euler & fluid acceleration",
        "Can a steady flow still accelerate?",
        "Chapter 1: Bernoulli; Newton's second law and the chain rule.",
        "Continuity → small-element force balance → material derivative → Euler → Venturi",
        r"\frac{D\mathbf{u}}{Dt}=\frac{\partial\mathbf{u}}{\partial t}+(\mathbf{u}\cdot\nabla)\mathbf{u}=-\frac{\nabla p}{\rho}+\mathbf{g}",
        "A fixed sensor can see an unchanging velocity while a moving parcel speeds up along its path. Pressure gradients and gravity supply the acceleration in this inviscid model.",
        "Narrow the Venturi throat at fixed inlet conditions. Use continuity to predict the speed increase, then Bernoulli to predict the pressure decrease. A low throat pressure is an ideal-model result; check the displayed validity warnings.",
    ),
    (
        "Stress & Navier–Stokes",
        "Which part of a fluid's motion produces viscous stress?",
        "Chapter 5: local momentum; matrix transpose and velocity gradients.",
        "Surface traction → Cauchy balance → deformation vs rotation → viscosity → Navier–Stokes",
        r"\boldsymbol{\sigma}=-p\mathbf{I}+2\mu\mathbf{D},\qquad \mathbf{D}=\tfrac12\left(\nabla\mathbf{u}+(\nabla\mathbf{u})^T\right)",
        "For an incompressible Newtonian fluid, pressure acts normally and viscous stress responds to deformation rate. Rigid rotation changes orientation without deforming the parcel.",
        "Compare Pure rotation with Simple shear in the deformation lab. Rotation gives D = 0 and zero viscous stress even though vorticity is nonzero. Simple shear contains both strain and spin. Then select Pure shear (symmetric): D is nonzero but Ω is zero. All three preserve area because their divergence is zero.",
    ),
    (
        "Exact flows & boundary layers",
        "Which assumptions make Navier–Stokes solvable by hand?",
        "Chapter 6: viscous momentum balance, no-slip walls, and derivatives.",
        "Channel & pipe profiles → transient diffusion → Prandtl scaling → similarity → Blasius → adverse gradients",
        r"0=-\frac{dp}{dx}+\mu\frac{d^2u}{dy^2}\quad\text{(steady, fully developed plane channel)}",
        "Use geometry and boundary conditions before integrating. Fully developed parallel flow removes convection; steady flow also removes the time derivative. Transient Stokes flow keeps the time derivative.",
        "Set the channel pressure gradient to zero to recover a straight Couette profile. Set wall speed to zero with a favorable gradient to recover a parabola. In the Stokes lab, quadrupling time should double the diffusion depth — the same square root that makes the Blasius layer grow as the square root of distance.",
    ),
    (
        "External flow & drag",
        "How do viscosity and separation set the force on an object?",
        "Chapters 3 and 7: Reynolds number and boundary layers.",
        "Surface forces → Stokes derivation → settling → finite inertia → drag crisis",
        r"F_D=\tfrac12\rho U^2C_D A,\qquad C_D=24/Re\quad(Re\ll1)",
        "Drag combines pressure and shear. A turbulent boundary layer can delay separation and reduce total drag on a bluff body.",
        "Double sphere diameter at fixed speed. Stokes drag doubles, but predicted settling speed quadruples; check the terminal Reynolds number before accepting that prediction.",
    ),
    (
        "Turbomachinery & shaft work",
        "How does a rotating blade heat a gas or extract work from it?",
        "Chapters 1 and 5: energy, momentum and velocity components.",
        "Angular momentum → blade geometry and angles → velocity triangles → Euler work → efficiency → intercooling → air separation plant",
        r"\Delta h_0=U_2C_{\theta2}-U_1C_{\theta1}",
        "Changing angular momentum exchanges shaft work. Compression raises stagnation temperature; an adiabatic turbine lowers it by exporting work.",
        "Switch the machine from compressor to turbine at the same high/low pressure ratio. Lower the efficiency: compression becomes hotter, while expansion produces less cooling and less work. Then in the impeller lab raise the outlet blade angle towards 90 degrees and watch the head curve flatten — that is the surge risk a real compressor is designed away from.",
    ),
    (
        "Compressible flows",
        "Why can lowering downstream pressure stop increasing gas flow?",
        "Chapters 1, 5 and 9: conservation laws, ideal-gas energy and stagnation properties.",
        "Sound speed → mass, momentum and energy → nozzle → choking → shocks → friction and heating",
        r"\frac{dA}{A}=(M^2-1)\frac{du}{u},\qquad h_0=h+u^2/2",
        "Density, speed and temperature change together. Sonic conditions constrain mass flow; irreversibility can destroy stagnation pressure even when stagnation temperature is conserved.",
        "Lower nozzle back pressure through the sonic threshold. Mass flow plateaus. Then double exit diameter: the ideal choked mass flow quadruples because area quadruples.",
    ),
    (
        "Numerical solution & verification",
        "How does a numerical solver enforce mass conservation?",
        "Chapters 6–7: momentum balance, boundary conditions, and transient flow.",
        "Coupled equations → predictor → pressure solve → correction → residuals & benchmark",
        r"\mathbf{u}^{n+1}=\mathbf{u}^{*}-\frac{\Delta t}{\rho}\nabla p^{n+1}",
        "Pressure corrects the predicted velocity to reduce divergence. Finite grids and incomplete pressure solves leave a residual: a plausible vortex is not sufficient evidence of numerical accuracy.",
        "At Re = 100, compare Quick look with Longer run. Read elapsed nondimensional time, divergence, and benchmark error together. Change the grid as a separate experiment; longer integration alone is not a grid-convergence study.",
    ),
    (
        "Reference & model selection",
        "Which model's assumptions fit the problem in front of you?",
        "Use this chapter whenever a symbol or assumption is unfamiliar.",
        "Model map → symbols & units → tensor notation → assumptions and failure modes",
        r"\text{physical question}\ \longrightarrow\ \text{assumptions}\ \longrightarrow\ \text{model}\ \longrightarrow\ \text{checks}",
        "Choose the simplest model that retains the physics needed for your question. A correct calculation with unsuitable assumptions can still give the wrong answer.",
        "For a long pipe, a narrowing nozzle, and a moving-wall cavity, name the useful model and its boundary conditions. Explain why a circular-pipe Reynolds threshold cannot classify all three flows.",
    ),
]


def part_for(number: int) -> Tuple[int, str, Tuple[int, int]]:
    """The part a chapter belongs to. Raises rather than guessing."""
    for part in PARTS:
        first, last = part[2]
        if first <= number <= last:
            return part
    raise ValueError(f"chapter {number} is not in any part; check PARTS")


def chapter_label(number: int) -> str:
    """The navigation label, e.g. '7 · Exact flows'."""
    return f"{number} · {NAV_LABELS[number - 1]}"


def chapter_labels() -> List[str]:
    return [chapter_label(n) for n in range(1, len(LESSONS) + 1)]


def render_chapter_header(number: int) -> None:
    title, question, prereq, route, equation, idea, _ = LESSONS[number - 1]
    part_number, part_name, _span = part_for(number)
    st.markdown(
        f'<div class="chapter-eyebrow">CHAPTER {number:02d} / {len(LESSONS):02d}'
        f' · PART {part_number} · {part_name.upper()}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"## {number}. {title}")
    st.markdown(f"**{question}**")
    st.caption(f"Start with: {prereq}")
    with st.container(border=True):
        st.markdown("**The central idea**")
        render_latex(equation)
        st.markdown(idea)
    st.caption(f"Reading order: {route}")


def render_chapter_recap(number: int) -> None:
    _title, _question, _prereq, _route, _equation, idea, experiment = LESSONS[number - 1]
    st.divider()
    with st.container(border=True, key=f"chapter-recap-{number}"):
        st.markdown("### Put it together")
        st.markdown("**One experiment to try**")
        render_prose_and_latex(experiment)
        st.markdown(f"**Take away:** {idea}")
        if number < len(LESSONS):
            next_title, next_question = LESSONS[number][0], LESSONS[number][1]
            st.caption(f"Continue with {number + 1}. {next_title} — {next_question}")


def render_concept_map() -> None:
    """The sidebar map: parts, chapters, and what each chapter asks.

    Built from LESSONS so it cannot invent a thirteenth name for a chapter,
    which is what the previous hand-written copy of this list did.
    """
    st.markdown("**Chapters** · easier plant story → harder mathematics")
    for part_number, part_name, (first, last) in PARTS:
        st.markdown(f"**Part {part_number} · {part_name}**")
        for number in range(first, last + 1):
            st.caption(f"{chapter_label(number)} — {LESSONS[number - 1][1]}")
