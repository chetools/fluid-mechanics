"""Chapter 12, section 5: rocket nozzles.

Kept out of `tab_compressible.py` for the same reason `pipe_network_lab.py` is
kept out of `tab_pipe_flow.py`: it is a self-contained lab with its own
calculators, and the host chapter should read as a table of contents rather
than as one very long function.

Everything here is the converging-diverging duct of sections 12.2 and 12.3 used
as a machine. Nothing new is assumed about the gas; what is new is that the
*exit* state has become the design variable, and that the atmosphere outside is
now part of the problem.
"""

import math

import numpy as np
import streamlit as st

from src.physics.rocket_nozzle import (
    ROCKET_DEMO_DEFAULTS,
    altitude_sweep,
    bell_contour,
    characteristic_velocity,
    conical_nozzle,
    converging_contour,
    march_along_contour,
    moc_minimum_length_nozzle,
    nozzle_performance,
    optimum_expansion_ratio,
    standard_atmosphere_pressure,
    thrust_coefficient,
)
from src.plotting import (
    plot_moc_nozzle,
    plot_nozzle_expansion,
    plot_nozzle_geometry,
    plot_thrust_coefficient_map,
    plot_thrust_vs_altitude,
)
from src.svg_diagrams import (
    diagram_bell_contour_construction,
    diagram_moc_wave_logic,
    diagram_nozzle_expansion_regimes,
    diagram_rocket_pressure_thrust,
    render_svg,
)
from src.ui.pedagogy import (
    render_callout,
    render_derivation,
    render_plot,
    render_prose_and_latex as prose,
    render_self_check,
    render_what_to_notice,
)
from src.ui.state import persistent_input


def render_rocket_nozzle_lab():
    _thrust_and_impulse()
    _sea_level_versus_vacuum()
    _sizing_march()
    _contour_design()
    _limits_and_checks()


# ---------------------------------------------------------------------------
# 12.5.1
# ---------------------------------------------------------------------------
def _thrust_and_impulse():
    st.markdown('### 12.5 Rocket nozzles · the same duct, used as a machine')
    prose(r'''
    A rocket nozzle is the converging-diverging passage of §12.2 with three
    things added: the reservoir is a combustion chamber rather than a tank, the throat is
    always choked in flight, and the diverging section is sized to control the **exit** state
    rather than merely to pass the flow. Every equation below is one already derived in this
    chapter; only the question being asked of them is new.

    The question is this. A chamber holds gas at $p_c$ and $T_c$. You may choose the throat
    area $A_t$ and the exit area $A_e$. How much force does the engine produce, and how does
    that force change when the vehicle climbs out of the atmosphere?''')

    st.markdown('#### 12.5.1 What chapter 10 already settled, and what it could not')
    prose(r'''
    Chapter 10 derived the thrust equation from a control volume riding with the
    vehicle, in §10.7. It will not be re-derived here:
    $$F=\dot m\,v_e+(p_e-p_a)A_e,\qquad c=\frac{F}{\dot m},\qquad I_{sp}=\frac{c}{g_0}$$
    That argument established *that* the pressure term is the only part of the atmospheric
    integral which fails to cancel on a closed surface, and therefore that the same engine
    produces more thrust in vacuum, by exactly $p_{\text{atm}}A_e$.

    What a momentum balance cannot tell you is **what $v_e$, $p_e$ and $A_e$ actually are**. It
    takes them as given. Supplying them is a gas-dynamics question, and it is this chapter's
    job: the area–Mach relation of §12.2 fixes $M_e$ from the area ratio, and the stagnation
    relations turn that into $v_e$ and $p_e$. Only then is the thrust equation a number rather
    than a set of symbols.

    The figure below adds the one thing the control-volume picture deliberately hides. Thrust is
    not applied at the exit plane; it is applied to the **metal**, as gas pressure on the inside
    of the chamber and the bell that has nothing pushing back on the outside. The two views give
    the same total, and the second is the one that explains why a bell is a thrust-producing
    structure rather than merely a duct.''')
    render_svg(diagram_rocket_pressure_thrust())

    prose(r'''
    **Split the engine in two.** The throat is choked, so §12.3's mass flux applies
    with the chamber as the reservoir. Group the gas constants into the symbol they always
    appear in:
    $$\Gamma=\sqrt{\gamma}\left(\frac{2}{\gamma+1}\right)^{\frac{\gamma+1}{2(\gamma-1)}},
    \qquad \dot m=\frac{p_cA_t\Gamma}{\sqrt{RT_c}}$$
    That rearranges into a quantity with units of velocity that mentions nothing downstream of
    the throat, and a dimensionless quantity that mentions nothing upstream of it:
    $$c^{*}=\frac{p_cA_t}{\dot m}=\frac{\sqrt{RT_c}}{\Gamma},
    \qquad C_F=\frac{F}{p_cA_t},\qquad I_{sp}=\frac{C_F\,c^{*}}{g_0}$$''')

    render_derivation(
        r"why $c^{*}$ and $C_F$ are worth separating, and what each one can and cannot blame",
        [
            (
                r"$c^{*}$ is a statement about combustion, and only about combustion",
                r"""
                $c^{*}=\sqrt{RT_c}/\Gamma$ contains the gas constant, the flame temperature and
                $\gamma$. It contains no area except the throat, and the throat cancels:
                $c^{*}=p_cA_t/\dot m$. Physically it asks *how much chamber pressure a given
                propellant flow can hold up through a given hole*. A better propellant, or more
                complete combustion, raises it. Nothing you do to the bell can.
                """,
            ),
            (
                r"$C_F$ is a statement about the nozzle, and only about the nozzle",
                r"""
                Divide the thrust equation by $p_cA_t$ and substitute the isentropic exit state:
                $$C_F=\underbrace{\sqrt{\frac{2\gamma^{2}}{\gamma-1}
                \left(\frac{2}{\gamma+1}\right)^{\frac{\gamma+1}{\gamma-1}}
                \left[1-\left(\frac{p_e}{p_c}\right)^{\frac{\gamma-1}{\gamma}}\right]}}
                _{\text{momentum, set by }\gamma\text{ and }\varepsilon}
                \;+\;\underbrace{\left(\frac{p_e}{p_c}-\frac{p_a}{p_c}\right)\varepsilon}
                _{\text{pressure, the only altitude-aware term}}$$
                with $\varepsilon=A_e/A_t$. Chamber temperature has vanished: a hotter chamber
                does not change $C_F$ at all. That is the point of the split.
                """,
            ),
            (
                "Multiply them back together and check the units",
                r"""
                $$C_F\,c^{*}=\frac{F}{p_cA_t}\cdot\frac{p_cA_t}{\dot m}=\frac{F}{\dot m}=c$$
                so $I_{sp}=C_Fc^{*}/g_0$ exactly. Performance is a *product* of a chamber
                number and a nozzle number, which is why the two can be developed, tested and
                blamed independently.
                """,
            ),
            (
                "What a test stand does with this",
                r"""
                A static firing measures $p_c$, $\dot m$, $A_t$ and $F$ — four things, all
                directly. From them it forms the measured $c^{*}$ and the measured $C_F$ and
                compares each with the ideal value computed here. A low $c^{*}$ efficiency means
                the injector is not mixing or the chamber is too short. A low $C_F$ efficiency
                at the same $c^{*}$ means the nozzle: divergence, boundary layer, or separation.
                Without the split, one number would be low and nobody would know which end of
                the engine to open.
                """,
            ),
        ],
    )


# ---------------------------------------------------------------------------
# 12.5.2
# ---------------------------------------------------------------------------
def _sea_level_versus_vacuum():
    st.markdown('#### 12.5.2 Sea level against vacuum, and why one nozzle cannot do both')
    prose(r'''
    Fix the chamber and the geometry. Then the exit Mach number follows from the area
    ratio alone, through the relation already derived in §12.2, and the exit pressure follows
    from that Mach number:
    $$\varepsilon=\frac{A_e}{A_t}=\frac{1}{M_e}\left[\frac{2}{\gamma+1}
    \left(1+\frac{\gamma-1}{2}M_e^{2}\right)\right]^{\frac{\gamma+1}{2(\gamma-1)}},
    \qquad \frac{p_e}{p_c}=\left(1+\frac{\gamma-1}{2}M_e^{2}\right)^{-\frac{\gamma}{\gamma-1}}$$
    **$p_e$ is a property of the engine. $p_a$ is a property of the sky.** They are set by
    completely unrelated things, they are equal at exactly one altitude, and everything in the
    figure below is the consequence of their disagreeing everywhere else.''')
    render_svg(diagram_nozzle_expansion_regimes())

    render_derivation(
        r"the matched-exit condition, from one differential ring of bell",
        [
            (
                "Ask a geometric question instead of an algebraic one",
                r"""
                Suppose the nozzle is built and running, and you weld one more thin ring of bell
                onto the end, adding $dA_e$ of exit area. Was that a good idea? Notice that this
                question needs no differentiation of the $C_F$ expression — it only needs to know
                what forces act on the new ring.
                """,
            ),
            (
                "Two pressures act on the ring, and they act on the same projected area",
                r"""
                The exhaust presses outward on the ring's inner face; the atmosphere presses
                inward on its outer face. What matters for thrust is the **axial projection** of
                each, and for a ring that grows the exit area by $dA_e$ that projection is
                exactly $dA_e$ for both faces, whatever the local wall angle — the same
                projected-area argument used for the slanted wall in §12.2. So the net forward
                force it contributes is
                $$dF=(p-p_a)\,dA_e\;\approx\;(p_e-p_a)\,dA_e$$
                """,
            ),
            (
                "Read off the sign, and with it the design rule",
                r"""
                $$\frac{dF}{dA_e}=p_e-p_a$$
                While $p_e>p_a$ the ring pays for itself: the nozzle is **under-expanded** and
                lengthening it adds thrust. When $p_e<p_a$ the ring is pushed *backwards* harder
                than forwards: the nozzle is **over-expanded** and the last of the bell is
                costing thrust. The optimum is where the derivative changes sign,
                $$\boxed{p_e=p_a}$$
                No calculus on $C_F$ was needed, and the answer did not depend on $\gamma$, on
                $T_c$, or on how the bell is shaped. It is a statement about one ring.
                """,
            ),
            (
                "Confirm it against the algebra, because a picture is not a proof",
                r"""
                Differentiating the full $C_F$ expression with respect to $\varepsilon$ at fixed
                $\gamma$ and $p_a/p_c$ gives a stationary point at the same place. The plot of
                $C_F$ against $\varepsilon$ below marks the matched ratio computed independently
                from $p_e=p_a$; it lands on each curve's peak. If it did not, one of the two
                calculations would be wrong, and that is exactly why both are drawn.
                """,
            ),
            (
                "Then notice what the rule cannot give you",
                r"""
                A launch vehicle passes through every ambient pressure from 101 kPa to zero. The
                matched ratio at sea level is a small number; in vacuum it is unbounded, because
                $p_e=0$ needs $\varepsilon=\infty$. **No fixed geometry is optimal for more than
                one instant of a climb.** A first stage therefore compromises toward the pad, an
                upper stage expands as far as the fairing and the mass budget allow, and
                altitude-compensating designs — plug nozzles, aerospikes, dual-bell contours —
                exist to escape the compromise, at a cost in complexity that has kept almost all
                of them off flight vehicles.
                """,
            ),
        ],
    )

    render_callout(
        r"""
        **Over-expansion has a hard floor, and it is not in the ideal model.** Ideal theory is
        happy to over-expand without limit: it simply predicts a lower $C_F$. Reality is not.
        The exhaust must be recompressed to ambient through shocks, and those shocks sit on a
        boundary layer. Past roughly $p_e\approx0.4\,p_a$ — Summerfield's crude and durable rule
        of thumb — the boundary layer separates, the flow tears off the wall, and the separation
        line is not axisymmetric. The resulting **side loads** are structural, unsteady, and have
        damaged real hardware during start-up transients. This is why a vacuum nozzle cannot
        simply be lit on the pad, and why the calculator below refuses to report such a case
        without saying so.
        """,
        title="Why you cannot just fit the biggest bell you can carry",
    )

    st.markdown('##### One engine, one altitude · calculator')
    c1, c2, c3 = st.columns(3)
    p_c = persistent_input(c1.number_input, 'Chamber pressure p_c [bar a]', min_value=1.,
                           max_value=400., value=97., step=1., key='rocket_pc') * 1e5
    t_c = persistent_input(c1.number_input, 'Chamber temperature T_c [K]', min_value=300.,
                           max_value=5000., value=3500., step=25., key='rocket_tc')
    eps = persistent_input(c2.number_input, 'Expansion ratio A_e/A_t', min_value=1.2,
                           max_value=300., value=16., step=.5, key='rocket_eps')
    altitude = persistent_input(c2.slider, 'Altitude [km]', 0., 80., 0., step=.5,
                                key='rocket_altitude')
    gamma = persistent_input(c3.number_input, 'Exhaust γ', min_value=1.05, max_value=1.67,
                             value=1.24, step=.01, key='rocket_gamma')
    r_gas = persistent_input(c3.number_input, 'Exhaust gas constant R [J/(kg·K)]',
                             min_value=100., max_value=4200., value=355., step=5.,
                             key='rocket_r')
    a_t = persistent_input(c3.number_input, 'Throat area A_t [m²]', min_value=1e-5,
                           max_value=5., value=.0305, step=.001, format='%.5f',
                           key='rocket_at')

    p_a = standard_atmosphere_pressure(altitude * 1000)
    result = nozzle_performance(p_c, t_c, eps, p_a, a_t, gamma, r_gas)
    vacuum = nozzle_performance(p_c, t_c, eps, 0.0, a_t, gamma, r_gas)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric('Thrust', f"{result['thrust'] / 1000:.1f} kN",
              f"{(result['thrust'] - vacuum['thrust']) / 1000:.1f} kN vs vacuum")
    m2.metric('Specific impulse', f"{result['specific_impulse']:.1f} s",
              f"{result['specific_impulse'] - vacuum['specific_impulse']:.1f} s vs vacuum")
    m3.metric('Exit Mach', f"{result['exit_mach']:.2f}")
    m4.metric('Exit pressure', f"{result['exit_pressure'] / 1000:.1f} kPa abs",
              f"ambient {p_a / 1000:.1f} kPa")

    n1, n2, n3, n4 = st.columns(4)
    n1.metric('Mass flow', f"{result['mass_flow']:.1f} kg/s")
    n2.metric('Thrust coefficient C_F', f"{result['thrust_coefficient']:.3f}")
    n3.metric('Characteristic velocity c*', f"{result['characteristic_velocity']:.0f} m/s")
    n4.metric('Exit area', f"{result['exit_area']:.3f} m²")

    matched = optimum_expansion_ratio(p_c, p_a, gamma) if p_a > 0 else math.inf
    if result['separation_predicted']:
        st.error(
            f"**{result['mode']}, and separation is predicted.** Exit pressure "
            f"{result['exit_pressure'] / 1000:.1f} kPa is below Summerfield's threshold of "
            f"{result['separation_exit_pressure'] / 1000:.1f} kPa at this altitude. The reported "
            "thrust assumes attached full-flowing exhaust and is therefore not trustworthy "
            "here; the real engine would be flowing separated, unsteadily, with side loads. "
            f"A nozzle matched to this altitude would have ε = {matched:.1f}."
        )
    elif result['mode'].startswith('over'):
        st.warning(
            f"**Over-expanded** but attached: p_e/p_a = "
            f"{result['pressure_ratio_exit_ambient']:.2f}. Thrust is below what this chamber "
            f"could give here; a nozzle matched to this altitude would have ε = {matched:.1f}."
        )
    elif result['mode'].startswith('under'):
        st.info(
            f"**Under-expanded**: p_e/p_a = {result['pressure_ratio_exit_ambient']:.2f}. The "
            "plume keeps expanding outside, so exit pressure is being left uncollected. A "
            f"nozzle matched to this altitude would have ε = "
            f"{'unbounded' if math.isinf(matched) else f'{matched:.1f}'}."
        )
    else:
        st.success(
            f"**Matched.** p_e = p_a = {p_a / 1000:.1f} kPa, so this is the best thrust this "
            "chamber and throat can produce at this altitude."
        )

    render_what_to_notice(
        'Drag the altitude slider from 0 to 80 km with everything else fixed. Mass flow, exit '
        'Mach and exit pressure never move — the engine cannot tell that it is climbing. Only '
        'the pressure term, and therefore the thrust and Isp, change. Then raise the expansion '
        'ratio to 150 and return to sea level: the model now refuses to vouch for the answer.'
    )

    sweeps = {
        f'ε = {eps:.0f} (your engine)':
            altitude_sweep(p_c, t_c, eps, a_t, gamma, r_gas),
        'ε = 165 (vacuum-optimised)':
            altitude_sweep(p_c, t_c, 165., a_t, gamma, r_gas),
    }
    render_plot(plot_thrust_vs_altitude(sweeps), 'rocket-altitude')

    curves = []
    ratios = np.geomspace(2., 250., 70)
    for label, ambient in (('sea level, p_a = 101 kPa', 101325.0),
                           ('10 km, p_a = 26 kPa', standard_atmosphere_pressure(10000)),
                           ('25 km, p_a = 2.5 kPa', standard_atmosphere_pressure(25000))):
        optimum = optimum_expansion_ratio(p_c, ambient, gamma)
        curves.append({
            'label': label,
            'expansion_ratio': [float(value) for value in ratios],
            'thrust_coefficient': [
                thrust_coefficient(gamma, float(value), ambient / p_c)['thrust_coefficient']
                for value in ratios],
            'optimum': (optimum, thrust_coefficient(
                gamma, optimum, ambient / p_c)['thrust_coefficient']),
        })
    render_what_to_notice(
        'Each open circle is placed at the expansion ratio where p_e = p_a, computed from the '
        'pressure relation alone and never from the curve it sits on. It lands on the peak of '
        'that curve. That agreement is the differential-ring argument and the algebra checking '
        'each other.'
    )
    render_plot(
        plot_thrust_coefficient_map(
            curves,
            {'expansion_ratio': eps, 'thrust_coefficient': result['thrust_coefficient']}),
        'rocket-cf-map',
    )

    st.markdown('##### Worked comparison: the same chamber, two bells')
    defaults = ROCKET_DEMO_DEFAULTS
    sea_level_engine = dict(defaults, expansion_ratio=16.0)
    vacuum_engine = dict(defaults, expansion_ratio=165.0)
    sl_pad = nozzle_performance(
        sea_level_engine['chamber_pressure'], sea_level_engine['chamber_temperature'],
        16.0, 101325.0, defaults['throat_area'], defaults['gamma'], defaults['gas_constant'])
    sl_vac = nozzle_performance(
        sea_level_engine['chamber_pressure'], sea_level_engine['chamber_temperature'],
        16.0, 0.0, defaults['throat_area'], defaults['gamma'], defaults['gas_constant'])
    vac_vac = nozzle_performance(
        vacuum_engine['chamber_pressure'], vacuum_engine['chamber_temperature'],
        165.0, 0.0, defaults['throat_area'], defaults['gamma'], defaults['gas_constant'])
    vac_pad = nozzle_performance(
        vacuum_engine['chamber_pressure'], vacuum_engine['chamber_temperature'],
        165.0, 101325.0, defaults['throat_area'], defaults['gamma'], defaults['gas_constant'])
    matched_altitude = _altitude_where_matched(sl_pad['exit_pressure'])

    st.dataframe([
        {'Engine': 'ε = 16, first stage', 'Where': 'sea level',
         'Exit p [kPa]': round(sl_pad['exit_pressure'] / 1000, 1),
         'Thrust [kN]': round(sl_pad['thrust'] / 1000, 1),
         'Isp [s]': round(sl_pad['specific_impulse'], 1),
         'Regime': sl_pad['mode']},
        {'Engine': 'ε = 16, first stage', 'Where': 'vacuum',
         'Exit p [kPa]': round(sl_vac['exit_pressure'] / 1000, 1),
         'Thrust [kN]': round(sl_vac['thrust'] / 1000, 1),
         'Isp [s]': round(sl_vac['specific_impulse'], 1),
         'Regime': sl_vac['mode']},
        {'Engine': 'ε = 165, upper stage', 'Where': 'vacuum',
         'Exit p [kPa]': round(vac_vac['exit_pressure'] / 1000, 2),
         'Thrust [kN]': round(vac_vac['thrust'] / 1000, 1),
         'Isp [s]': round(vac_vac['specific_impulse'], 1),
         'Regime': vac_vac['mode']},
        {'Engine': 'ε = 165, upper stage', 'Where': 'sea level (do not)',
         'Exit p [kPa]': round(vac_pad['exit_pressure'] / 1000, 2),
         'Thrust [kN]': round(vac_pad['thrust'] / 1000, 1),
         'Isp [s]': round(vac_pad['specific_impulse'], 1),
         'Regime': vac_pad['mode'] + ', separated'},
    ], hide_index=True, width='stretch')

    prose(f'''
    All four rows share one chamber: {defaults['chamber_pressure'] / 1e5:g} bar,
    {defaults['chamber_temperature']:g} K, γ = {defaults['gamma']:g},
    R = {defaults['gas_constant']:g} J/(kg·K), throat area {defaults['throat_area']:g} m².
    The mass flow is therefore identical in every row, at
    {sl_pad['mass_flow']:.1f} kg/s, and so is c* at
    {sl_pad['characteristic_velocity']:.0f} m/s. **Only the bell differs.**

    **1 · The first-stage bell gains {sl_vac["thrust"] / 1000 - sl_pad["thrust"] / 1000:.0f} kN
    on the way up**, from {sl_pad['thrust'] / 1000:.0f} kN on the pad to
    {sl_vac['thrust'] / 1000:.0f} kN in vacuum, a rise of
    {100 * (sl_vac['thrust'] / sl_pad['thrust'] - 1):.1f}%. Nothing inside the engine changed.
    That entire gain is the term (p_e − p_a)A_e losing its p_a A_e part, which is
    {p_ambient_term(sl_pad):.0f} kN of atmosphere pressing on
    {sl_pad['exit_area']:.3f} m² of exit plane.

    **2 · It is over-expanded on the pad**, at an exit pressure of
    {sl_pad['exit_pressure'] / 1000:.1f} kPa against 101.3 kPa ambient, and becomes matched at
    about {matched_altitude / 1000:.1f} km. First stages are routinely built this way: a bell
    matched on the pad would be too small to be efficient over most of the trajectory, so the
    design accepts a few percent of over-expansion loss at liftoff to gain it back with altitude.

    **3 · The upper-stage bell is worth {vac_vac["specific_impulse"] - sl_vac["specific_impulse"]:.1f} s
    of Isp in vacuum** — {vac_vac['specific_impulse']:.1f} s against
    {sl_vac['specific_impulse']:.1f} s — for ten times the exit area, at
    {vac_vac['exit_area']:.2f} m². Isp is what an upper stage is paid in, because the rocket
    equation is exponential in it.

    **4 · The same upper-stage bell is a liability at sea level.** Its exit pressure of
    {vac_pad['exit_pressure'] / 1000:.2f} kPa is far below Summerfield's threshold of
    {vac_pad['separation_exit_pressure'] / 1000:.1f} kPa, so the ideal figure of
    {vac_pad['thrust'] / 1000:.0f} kN is fiction: the flow would separate inside the bell. The
    ideal model reports the number without complaint, which is precisely why the separation
    check is carried alongside it.''')


def p_ambient_term(result):
    """Atmospheric force on the exit plane, in kN — quoted in the worked example."""
    return result['ambient_pressure'] * result['exit_area'] / 1000


def _altitude_where_matched(exit_pressure, ceiling=80000.0):
    """Altitude at which the standard atmosphere equals a given exit pressure."""
    if exit_pressure >= standard_atmosphere_pressure(0.0):
        return 0.0
    if exit_pressure <= standard_atmosphere_pressure(ceiling):
        return ceiling
    from scipy.optimize import brentq
    return brentq(lambda h: standard_atmosphere_pressure(h) - exit_pressure,
                  0.0, ceiling, xtol=1.0)


# ---------------------------------------------------------------------------
# 12.5.3
# ---------------------------------------------------------------------------
def _sizing_march():
    st.markdown('#### 12.5.3 Sizing the nozzle · five steps, in the order they are forced')
    prose(r'''
    Nothing above tells you how big to make anything. This does. The order matters:
    each step uses only quantities already fixed by the ones before it, which is why the design
    closes without iteration.''')

    render_derivation(
        r"from a required thrust to a throat and an exit area",
        [
            (
                "Step 1 — the chamber, which is a cycle decision and not a fluids one",
                r"""
                $p_c$, $T_c$, $\gamma$ and $R$ come from the propellant combination and the
                engine cycle: how hard the turbopumps can push, what the chamber wall can survive,
                what the combustion products actually are. A chemistry code supplies $T_c$,
                $\gamma$ and $R$; this chapter takes them as given and says what follows. Compute
                $$\Gamma,\qquad c^{*}=\frac{\sqrt{RT_c}}{\Gamma}$$
                which is now fixed for the rest of the design.
                """,
            ),
            (
                r"Step 2 — the expansion ratio, from the altitude you choose to match",
                r"""
                Pick the design altitude, read $p_a$ from the atmosphere, and set $p_e=p_a$. The
                exit Mach follows from the pressure relation and $\varepsilon$ from the area
                relation:
                $$M_e=\sqrt{\frac{2}{\gamma-1}\left[\left(\frac{p_c}{p_a}\right)
                ^{\frac{\gamma-1}{\gamma}}-1\right]},
                \qquad \varepsilon=\frac{A_e}{A_t}\Big|_{M_e}$$
                For a first stage the "design altitude" is a compromise over the whole
                trajectory rather than a single point, and for an upper stage $\varepsilon$ is
                usually limited by the fairing diameter and the nozzle's own mass long before
                the optimum is reached.
                """,
            ),
            (
                r"Step 3 — the thrust coefficient, which needs no areas yet",
                r"""
                $C_F$ depends only on $\gamma$, $\varepsilon$ and $p_a/p_c$, all now known:
                $$C_F=\sqrt{\frac{2\gamma^{2}}{\gamma-1}
                \left(\frac{2}{\gamma+1}\right)^{\frac{\gamma+1}{\gamma-1}}
                \left[1-\left(\frac{p_e}{p_c}\right)^{\frac{\gamma-1}{\gamma}}\right]}
                +\left(\frac{p_e-p_a}{p_c}\right)\varepsilon$$
                This is the step that would be circular in any other ordering — and is not, only
                because $C_F$ was constructed to be independent of size.
                """,
            ),
            (
                r"Step 4 — the throat, which is the first actual dimension",
                r"""
                $F=C_Fp_cA_t$ inverts directly:
                $$\boxed{A_t=\frac{F_{\text{required}}}{C_F\,p_c}}\qquad
                d_t=\sqrt{\frac{4A_t}{\pi}}$$
                Everything about the engine's *size* enters here and nowhere else. Doubling the
                required thrust at fixed chamber pressure doubles the throat area and multiplies
                every other area by the same factor: rocket engines scale almost perfectly, which
                is why the same design can be built at very different sizes.
                """,
            ),
            (
                "Step 5 — the rest of the geometry, and the sanity checks",
                r"""
                $$\dot m=\frac{p_cA_t}{c^{*}},\qquad A_e=\varepsilon A_t,
                \qquad I_{sp}=\frac{C_Fc^{*}}{g_0}$$
                Then check, before drawing anything: is $\dot m$ what the pumps can deliver? Does
                $A_e$ fit inside the vehicle? At the *lowest* altitude the engine will ever run,
                is $p_e$ above the separation threshold? Any "no" sends you back to step 1 or 2,
                and it is much cheaper to discover that here than after the contour is cut.
                """,
            ),
        ],
    )

    st.markdown('##### Sizing calculator')
    s1, s2, s3 = st.columns(3)
    thrust_req = persistent_input(s1.number_input, 'Required thrust [kN]', min_value=.1,
                                  max_value=10000., value=500., step=10.,
                                  key='rocket_size_thrust') * 1000
    design_km = persistent_input(s1.slider, 'Design (matched) altitude [km]', 0., 40., 3.,
                                 step=.5, key='rocket_size_altitude')
    p_c = persistent_input(s2.number_input, 'Chamber pressure [bar a]', min_value=1.,
                           max_value=400., value=97., step=1., key='rocket_size_pc') * 1e5
    t_c = persistent_input(s2.number_input, 'Chamber temperature [K]', min_value=300.,
                           max_value=5000., value=3500., step=25., key='rocket_size_tc')
    gamma = persistent_input(s3.number_input, 'γ', min_value=1.05, max_value=1.67, value=1.24,
                             step=.01, key='rocket_size_gamma')
    r_gas = persistent_input(s3.number_input, 'R [J/(kg·K)]', min_value=100., max_value=4200.,
                             value=355., step=5., key='rocket_size_r')

    p_design = standard_atmosphere_pressure(design_km * 1000)
    eps = optimum_expansion_ratio(p_c, p_design, gamma)
    coefficients = thrust_coefficient(gamma, eps, p_design / p_c)
    c_star = characteristic_velocity(gamma, r_gas, t_c)
    a_t = thrust_req / (coefficients['thrust_coefficient'] * p_c)
    a_e = eps * a_t
    m_dot = p_c * a_t / c_star

    d1, d2, d3, d4 = st.columns(4)
    d1.metric('Step 2 · expansion ratio', f"{eps:.1f}")
    d2.metric('Step 3 · C_F at design', f"{coefficients['thrust_coefficient']:.3f}")
    d3.metric('Step 4 · throat diameter', f"{1000 * math.sqrt(4 * a_t / math.pi):.1f} mm")
    d4.metric('Step 5 · exit diameter', f"{1000 * math.sqrt(4 * a_e / math.pi):.0f} mm")
    e1, e2, e3, e4 = st.columns(4)
    e1.metric('Throat area', f"{a_t * 1e4:.1f} cm²")
    e2.metric('Mass flow', f"{m_dot:.1f} kg/s")
    e3.metric('c*', f"{c_star:.0f} m/s")
    e4.metric('Isp at design altitude',
              f"{coefficients['thrust_coefficient'] * c_star / 9.80665:.1f} s")

    pad = nozzle_performance(p_c, t_c, eps, 101325.0, a_t, gamma, r_gas)
    st.caption(
        f"Design point: matched at {design_km:g} km, where p_a = {p_design / 1000:.1f} kPa. "
        f"Flown down to the pad this same engine gives {pad['thrust'] / 1000:.0f} kN at "
        f"{pad['specific_impulse']:.1f} s and is {pad['mode']}"
        + (" **with separation predicted** — this design cannot be lit at sea level."
           if pad['separation_predicted'] else ", which is normal and acceptable.")
    )


# ---------------------------------------------------------------------------
# 12.5.4
# ---------------------------------------------------------------------------
def _contour_design():
    st.markdown('#### 12.5.4 The shape of the diverging section, step by step')
    prose(r'''
    Section 12.5.3 produced two areas and no shape. That is a real gap, not a
    formality: the quasi-one-dimensional model of §12.2 knows only $A(x)$, and *any* wall that
    passes through the right throat and exit areas satisfies it. The wall that a real engine
    needs must do more than hit two numbers — it must deliver exhaust that is **uniform and
    axial** at the exit, in the **shortest and lightest** structure that will do it, without
    separating.

    Three families of answer, in increasing order of how much they know:''')

    st.markdown('##### A · The cone, and the loss that motivates everything else')
    prose(r'''
    A straight-walled cone of half-angle $\alpha$ is trivial to draw and to machine.
    Its problem is that the exhaust leaves on a *spread* of directions, and only the axial
    component of each streamline's momentum produces thrust. Averaging that over the exit gives
    a divergence efficiency
    $$\lambda=\frac{1+\cos\alpha}{2}$$
    which is 0.983 at the traditional 15° — 1.7% of the momentum thrust thrown sideways and
    wasted. Steeper cones are shorter and lighter but lose more; shallower cones lose less but
    are long and heavy. The bell exists to escape that trade entirely.''')

    render_derivation(
        r"the divergence loss $\lambda=(1+\cos\alpha)/2$, by averaging over the exit",
        [
            (
                "Idealise the exit flow in the only way a cone permits",
                r"""
                Far from the throat, a conical nozzle's streamlines are very nearly straight
                lines radiating from the cone's apex. So model the exit as a **spherical cap** of
                half-angle $\alpha$ centred on that apex, crossed by gas of uniform speed $v_e$
                and uniform density, every element moving radially outward. This is an
                idealisation, and it is the source of every subsequent number.
                """,
            ),
            (
                "Only the axial component of each element's momentum counts",
                r"""
                An element leaving at polar angle $\theta$ from the axis carries momentum flux
                $d\dot m\,v_e$ along its own direction, of which $d\dot m\,v_e\cos\theta$ is
                axial. The transverse components cancel by symmetry around the axis — they do
                not vanish, they simply pull the exhaust apart instead of pushing the vehicle.
                """,
            ),
            (
                "Weight by area, because uniform flow means uniform flux per unit area",
                r"""
                On a sphere of radius $R$ the ring between $\theta$ and $\theta+d\theta$ has area
                $2\pi R^{2}\sin\theta\,d\theta$, so $d\dot m\propto\sin\theta\,d\theta$. The
                efficiency is the ratio of the axial momentum to the momentum a perfectly axial
                jet of the same mass flow would carry:
                $$\lambda=\frac{\int_0^{\alpha}\cos\theta\,\sin\theta\,d\theta}
                {\int_0^{\alpha}\sin\theta\,d\theta}$$
                """,
            ),
            (
                "Both integrals are elementary, and the result collapses",
                r"""
                $$\int_0^{\alpha}\cos\theta\sin\theta\,d\theta=\frac{\sin^{2}\alpha}{2},
                \qquad \int_0^{\alpha}\sin\theta\,d\theta=1-\cos\alpha$$
                $$\lambda=\frac{\sin^{2}\alpha}{2(1-\cos\alpha)}
                =\frac{1-\cos^{2}\alpha}{2(1-\cos\alpha)}
                =\boxed{\frac{1+\cos\alpha}{2}}$$
                The factorisation of $1-\cos^{2}\alpha$ is the whole trick. Note the shape of the
                answer: the loss goes as $\alpha^{2}/4$ for small angles, so it is *quadratic* —
                which is why 15° costs only 1.7% while 30° would cost 6.7%.
                """,
            ),
        ],
    )

    st.markdown('##### B · The method of characteristics, which computes the exact wall')
    prose(r'''
    The cone is a guess. The method of characteristics is not: it constructs the wall
    that produces uniform axial exhaust *by construction*, wave by wave. It rests on one fact
    about supersonic flow — information travels along the two families of Mach lines and nowhere
    else — and on the Prandtl–Meyer function that says how much a stream turns when it expands.
    $$\nu(M)=\sqrt{\frac{\gamma+1}{\gamma-1}}\arctan\sqrt{\frac{\gamma-1}{\gamma+1}(M^{2}-1)}
    -\arctan\sqrt{M^{2}-1},\qquad \mu=\arcsin\frac{1}{M}$$''')
    render_svg(
        diagram_moc_wave_logic(),
        "Waves are drawn as straight lines because the flow state is constant along "
        "each of them; that is what makes a characteristic a characteristic. Schematic "
        "spacing, not a solved mesh -- the computed mesh is the figure below.",
    )

    render_derivation(
        r"the marching procedure, and the closed form it collapses to for a minimum-length nozzle",
        [
            (
                "The invariants: what is actually conserved along a Mach line",
                r"""
                For steady, irrotational, two-dimensional supersonic flow the governing equations
                reduce along the two Mach-line families to
                $$\theta+\nu=K_-\ \text{(constant along a }C_-\text{ line)},\qquad
                \theta-\nu=K_+\ \text{(constant along a }C_+\text{ line)}$$
                where $\theta$ is the flow angle and $\nu$ the Prandtl–Meyer angle. Two lines
                crossing therefore determine the state at their intersection completely:
                $$\theta=\tfrac{1}{2}(K_-+K_+),\qquad \nu=\tfrac{1}{2}(K_--K_+)$$
                This is the entire computational content of the method. Everything else is
                bookkeeping about which line carries which invariant.
                """,
            ),
            (
                "The corner: spend half the available turn",
                r"""
                A minimum-length nozzle expands the flow through a single sharp corner at the
                throat. The gas starts sonic ($\nu=0$) and must end at $M_e$ with $\theta=0$.
                Since the wall must turn out and then back by the same amount,
                $$\theta_{\max}=\frac{\nu(M_e)}{2}$$
                Discretise that turn into $n$ waves of $\Delta\theta=\theta_{\max}/n$. Wave $i$
                leaves the corner having turned the flow to $\theta_i=i\,\Delta\theta$, and
                because the expansion began at $M=1$, at that point $\nu_i=\theta_i$ too. So wave
                $i$ carries $K_-=2i\,\Delta\theta$ downstream, unchanged, forever.
                """,
            ),
            (
                "The axis: symmetry converts each arriving wave into an outgoing one",
                r"""
                Where wave $k$ reaches the centreline, symmetry forces $\theta=0$, so
                $\nu=K_-=2k\,\Delta\theta$ and the reflected $C_+$ line carries
                $K_+=-2k\,\Delta\theta$. The wave has not been absorbed; it has been turned
                around.
                """,
            ),
            (
                "The wall: absorb, and that choice is the contour",
                r"""
                A reflected wave arriving at the wall would reflect again and spoil the exit
                uniformity. So the wall is *defined* to turn to the local flow angle at each
                arrival, cancelling the wave. This is the design decision; everything else was
                physics.
                """,
            ),
            (
                "Put the three together and the whole mesh state is closed form",
                r"""
                Label a point by the reflected line it sits on ($k$) and how many waves it has
                since crossed ($j$). It carries $K_+=-2k\,\Delta\theta$ from the axis and
                $K_-=2(k+j)\,\Delta\theta$ from the corner, so
                $$\theta_{k,j}=j\,\Delta\theta,\qquad \nu_{k,j}=(2k+j)\,\Delta\theta$$
                and the wall point ending row $k$ has $\theta=(n-k)\Delta\theta$,
                $\nu=(n+k)\Delta\theta$. At $k=n$ that gives $\theta=0$ and
                $\nu=2n\Delta\theta=\nu(M_e)$: **axial flow at exactly the design Mach number**,
                which is the proof that the construction does what it claims.
                """,
            ),
            (
                "Only the geometry is approximate, and it converges",
                r"""
                Every $(\theta,\nu)$ above is exact. What is approximate is *where* each point
                lies, because the code advances along each characteristic using the average of
                its slope $\tan(\theta\mp\mu)$ at the two ends rather than integrating the curved
                line. That is a second-order step, so refining $n$ refines the wall shape while
                the exit Mach number stays pinned at its imposed value. The table below is that
                convergence, computed rather than asserted.
                """,
            ),
        ],
    )

    m1, m2, m3 = st.columns(3)
    design_mach = persistent_input(m1.slider, 'Design exit Mach number', 1.2, 5., 2.4, step=.05,
                                   key='rocket_moc_mach')
    moc_gamma = persistent_input(m2.number_input, 'γ for the characteristics', min_value=1.05,
                                 max_value=1.67, value=1.4, step=.01, key='rocket_moc_gamma')
    n_waves = persistent_input(m3.slider, 'Number of expansion waves n', 3, 40, 14, step=1,
                               key='rocket_moc_n')
    moc = moc_minimum_length_nozzle(design_mach, moc_gamma, n_waves, 1.0)

    q1, q2, q3, q4 = st.columns(4)
    q1.metric('ν(M_e)', f"{math.degrees(moc['nu_exit']):.2f}°")
    q2.metric('Wall turn θ_max', f"{math.degrees(moc['theta_max']):.2f}°",
              'exactly half of ν(M_e)')
    q3.metric('Half-height ratio', f"{moc['achieved_area_ratio']:.4f}",
              f"ideal {moc['ideal_area_ratio']:.4f}")
    q4.metric('Length / throat half-height', f"{moc['length']:.2f}")

    render_what_to_notice(
        'θ_max is exactly half of ν(M_e) at every setting — that is step 2 of the derivation, '
        'not a coincidence. Increase n and watch the achieved half-height ratio climb toward '
        'the ideal value while θ_max does not move at all, because the wave count changes the '
        'geometry and never the imposed exit state.'
    )
    render_plot(plot_moc_nozzle(moc), 'rocket-moc')

    convergence = []
    for count in (3, 5, 10, 20, 40):
        run = moc_minimum_length_nozzle(design_mach, moc_gamma, count, 1.0)
        convergence.append({
            'waves n': count,
            'θ_max [deg]': round(math.degrees(run['theta_max']), 4),
            'half-height ratio': round(run['achieved_area_ratio'], 5),
            'ideal': round(run['ideal_area_ratio'], 5),
            'error [%]': round(100 * run['area_ratio_error'], 3),
            'length': round(run['length'], 4),
        })
    st.dataframe(convergence, hide_index=True, width='stretch')
    st.caption(
        'Computed live from the current design Mach number and γ. θ_max is identical in every '
        'row because it is imposed; the error falls roughly in proportion to 1/n because the '
        'averaged-slope step is what is being refined. This is a **planar** construction: a real '
        'axisymmetric nozzle carries an extra term in the characteristic equations and its '
        'contour differs, though the three rules are the same.'
    )

    st.markdown('##### C · The bell, which is the MOC contour made manufacturable')
    prose(r'''
    A minimum-length nozzle has a sharp corner at the throat, which concentrates heat
    flux exactly where the wall is thinnest, and its wall is a curve defined point by point.
    Rao's contribution was to show that a **parabola** between two well-chosen tangent angles
    reproduces the optimum contour to within a fraction of a percent, and that the optimum can
    be shortened to 70–85% of the equivalent 15° cone with almost no performance loss. Every
    modern bell is drawn this way.''')
    render_svg(diagram_bell_contour_construction())

    b1, b2, b3 = st.columns(3)
    bell_eps = persistent_input(b1.number_input, 'Expansion ratio for the contour',
                                min_value=2., max_value=200., value=16., step=1.,
                                key='rocket_bell_eps')
    fraction = persistent_input(b1.slider, 'Bell length, as a fraction of the 15° cone',
                                .6, 1., .8, step=.01, key='rocket_bell_fraction')
    theta_n = persistent_input(b2.slider, 'Initial wall angle θn [deg]', 15., 40., 22., step=.5,
                               key='rocket_bell_theta_n')
    theta_e = persistent_input(b2.slider, 'Exit wall angle θe [deg]', 2., 20., 11., step=.5,
                               key='rocket_bell_theta_e')
    cone_angle = persistent_input(b3.slider, 'Reference cone half-angle [deg]', 10., 25., 15.,
                                  step=.5, key='rocket_bell_cone')
    contraction = persistent_input(b3.slider, 'Chamber radius / throat radius', 1.5, 5., 3.,
                                   step=.1, key='rocket_bell_contraction')

    if theta_e >= theta_n:
        st.error('A bell turns back toward the axis, so the exit angle must be below the '
                 'initial angle. Lower θe or raise θn.')
    else:
        cone = conical_nozzle(bell_eps, 1.0, cone_angle)
        bell = bell_contour(bell_eps, 1.0, theta_n, theta_e, fraction, cone_angle)
        converging = converging_contour(1.0, contraction, 30.)
        g1, g2, g3, g4 = st.columns(4)
        g1.metric('Cone length / r_t', f"{cone['length']:.2f}")
        g2.metric('Bell length / r_t', f"{bell['length']:.2f}",
                  f"{100 * (bell['length'] / cone['length'] - 1):.0f}%")
        g3.metric('Cone divergence efficiency', f"{cone['divergence_efficiency']:.4f}",
                  f"{100 * (cone['divergence_efficiency'] - 1):.2f}% of momentum thrust")
        g4.metric('Contraction ratio', f"{converging['contraction_ratio']:.1f}")
        render_what_to_notice(
            'Both walls end at the same exit radius, because both have the same expansion '
            'ratio. Shorten the bell and watch it turn harder immediately after the throat to '
            'get there — that steep initial turn is what a cone cannot do, and it is why the '
            'bell reaches the same area in less length.'
        )
        render_plot(plot_nozzle_geometry(bell, cone, converging), 'rocket-contour')

        march = march_along_contour(bell['x'], bell['r'], 97e5, 3500., 1.24, 355.,
                                    throat_radius=1.0)
        render_what_to_notice(
            'Most of the expansion happens in the first fifth of the bell. That is why the '
            'contour can be truncated at 80% of the cone length so cheaply, and why the throat '
            'region — not the exit — is where the heat flux and the manufacturing tolerance '
            'both matter.'
        )
        render_plot(
            plot_nozzle_expansion(march, {
                'sea level': 101325.0,
                '10 km': standard_atmosphere_pressure(10000),
                '25 km': standard_atmosphere_pressure(25000),
            }),
            'rocket-expansion',
        )
        st.caption(
            'The pressure march is quasi-one-dimensional: each station is given the Mach number '
            'its own local area implies. That deliberately ignores the two-dimensionality the '
            'method of characteristics exists to capture, so read it for *where* the expansion '
            'happens, not as a design result. θn and θe are inputs here rather than outputs, '
            'because reproducing Rao’s optimisation requires an axisymmetric characteristics '
            'solve with a variational condition on a control surface; what the app guarantees '
            'is that the contour drawn is tangent-continuous and hits the requested area ratio '
            'exactly.'
        )


# ---------------------------------------------------------------------------
# 12.5.5
# ---------------------------------------------------------------------------
def _limits_and_checks():
    st.markdown('#### 12.5.5 What this ideal model is not telling you')
    st.dataframe([
        {'Left out': 'Chemistry', 'What the model does':
            'Constant γ and R, chamber temperature given.',
         'What really happens':
            'γ falls through the expansion as the gas cools; recombination releases heat and '
            'raises Isp above the frozen-flow value. Design uses an equilibrium code (CEA, RPA).'},
        {'Left out': 'Boundary layer', 'What the model does': 'Inviscid, full-flowing wall.',
         'What really happens':
            'A displacement thickness that reduces the effective area ratio, wall friction, and '
            'the layer whose separation sets the over-expansion limit.'},
        {'Left out': 'Heat transfer', 'What the model does': 'Adiabatic walls.',
         'What really happens':
            'Throat heat flux of tens of MW/m²; regenerative cooling, film cooling and ablation '
            'exist entirely because of it, and they change the gas state as well.'},
        {'Left out': 'Two-phase flow', 'What the model does': 'Single-phase perfect gas.',
         'What really happens':
            'Solid motors carry condensed aluminium oxide that lags the gas in both velocity '
            'and temperature — a real and calculable Isp loss.'},
        {'Left out': 'Transients', 'What the model does': 'Steady flow only.',
         'What really happens':
            'Start-up and shut-down sweep the shock system through the bell. Side loads during '
            'those seconds size the gimbal structure of large first-stage engines.'},
        {'Left out': 'Altitude compensation', 'What the model does': 'One fixed area ratio.',
         'What really happens':
            'Aerospikes, plug and dual-bell nozzles trade complexity for a wider matched range; '
            'the ideal model can size them but says nothing about whether they are worth it.'},
    ], hide_index=True, width='stretch')

    render_self_check(
        'rocket_self_check_altitude',
        'A first-stage engine is over-expanded on the pad. As it climbs, with throttle, chamber '
        'pressure and mass flow all held constant, its thrust rises. The rise comes from…',
        ['the exhaust leaving faster as the air thins',
         'the ambient pressure no longer pushing back on the exit plane',
         'the throat passing more mass at lower back pressure'],
        'the ambient pressure no longer pushing back on the exit plane',
        'The throat is choked, so mass flow cannot respond to anything downstream — that also '
        'rules out the third answer, and it is the same argument as §12.3. The exit Mach and '
        'exit velocity are fixed by the area ratio, so the exhaust speed does not change either. '
        'Only the term (p_e − p_a)A_e moves, and it moves by exactly p_a A_e.',
    )
    render_self_check(
        'rocket_self_check_expansion',
        'Two engines share a chamber and a throat. Engine B has twice the exit area of engine A '
        'and is matched at 20 km. Compared with A, engine B in vacuum has…',
        ['the same mass flow and higher thrust',
         'higher mass flow and higher thrust',
         'the same thrust, since the throat is unchanged'],
        'the same mass flow and higher thrust',
        'Mass flow is fixed by the choked throat and the chamber state alone: c* is identical, '
        'so ṁ = p_c A_t / c* is identical. The larger bell converts more of the exhaust’s '
        'remaining pressure into axial momentum, so both v_e and the vacuum pressure term rise. '
        'That is the whole reason upper stages carry large bells.',
    )
    render_self_check(
        'rocket_self_check_contour',
        'The method of characteristics is used to design the wall rather than merely to analyse '
        'a given one because…',
        ['it is the only way to satisfy conservation of mass in a diverging duct',
         'the wall angle at each wave arrival is chosen so the wave is absorbed, and that choice '
         'is what makes the exit uniform',
         'it accounts for the boundary layer that the one-dimensional model omits'],
        'the wall angle at each wave arrival is chosen so the wave is absorbed, and that choice '
        'is what makes the exit uniform',
        'Quasi-one-dimensional flow already conserves mass for any A(x), which is exactly why it '
        'cannot pick a shape. The characteristics method is inviscid, so it says nothing about '
        'boundary layers. Its contribution is the cancellation condition: bending the wall to '
        'the local flow direction at every arriving wave is a *design choice*, and imposing it '
        'everywhere is what produces uniform axial exhaust.',
    )

    st.caption(
        'Model limits: steady, inviscid, adiabatic, single-phase, calorically perfect gas with '
        'constant γ; full-flowing attached nozzle; planar characteristics; empirical separation '
        'criteria quoted as correlations rather than results. Sources: '
        '[NASA: rocket thrust equation](https://www.grc.nasa.gov/www/k-12/airplane/rockth.html) · '
        '[NASA: nozzle design](https://www.grc.nasa.gov/www/k-12/airplane/nozzle.html) · '
        'G. V. R. Rao, "Exhaust nozzle contour for optimum thrust", *Jet Propulsion* 28 (1958). '
        'Propellant numbers used in the examples are representative teaching values, not a '
        'manufacturer’s data sheet.'
    )
