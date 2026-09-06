"""UI module for chapter 10: integral momentum balances and what they buy you.

Chapters 5-9 worked locally: a differential balance on a fluid element, solved
where the geometry allowed. This chapter goes back to a finite control volume
and asks the one question a differential equation cannot answer cheaply --
*what force does this device carry?* -- for the classical cases every textbook
uses: jets on vanes, pipe bends, sudden expansions, hydraulic jumps, weirs and
gates, rockets and rotors.

All numbers on the page are computed live from src.physics.momentum, never
quoted.
"""

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src.physics import momentum as mom
from src.svg_diagrams import (
    diagram_hydraulic_jump,
    diagram_momentum_control_volume,
    diagram_rocket_control_volume,
    diagram_weir_and_gate,
    render_svg,
)
from src.theme import apply_plotly_theme
from src.ui.pedagogy import (
    render_callout,
    render_checklist,
    render_derivation,
    render_objectives,
    render_plot,
    render_predict,
    render_prose_and_latex as prose,
    render_self_check,
    render_symbols,
    render_what_to_notice,
)
from src.ui.state import persistent_input
from src.units import get_fluid_state


def render_tab_momentum() -> None:
    render_objectives(
        [
            "State the integral momentum balance and say which terms survive in steady flow.",
            "Choose a control volume whose boundary you actually know something about.",
            "Compute the anchor force on a bend, the load on a sluice gate, and the thrust of a rocket from the same equation.",
            "Use momentum where energy fails (a jump, an expansion) and subtract the two to measure the loss.",
        ]
    )

    _section_theorem()
    _section_jets()
    _section_bends()
    _section_expansion()
    _section_jump()
    _section_weirs()
    _section_propulsion()
    _section_when_it_fails()


# ==========================================================================
# 10.1 The theorem
# ==========================================================================
def _section_theorem() -> None:
    st.markdown("### 10.1 One balance, drawn around whatever you like")
    render_svg(diagram_momentum_control_volume())
    prose(
        r"""
        Chapter 5 shrank Newton's second law onto a fluid element and got Euler's
        equation; chapter 6 added viscous stress and got Navier-Stokes. Both are
        *local*: they hold at every point, and they demand that you know the flow at
        every point. A bolted flange does not need that. It needs one number — the
        force — and momentum will give it without any knowledge of the interior at
        all.
        $$\sum\mathbf F=\frac{d}{dt}\int_{CV}\rho\,\mathbf u\,dV
        +\oint_{CS}\rho\,\mathbf u\,(\mathbf u\cdot\mathbf n)\,dA$$
        For steady flow with one-dimensional inlets and outlets this collapses to a
        statement you can evaluate on the back of a drawing:
        $$\sum\mathbf F=\sum_{\text{out}}\dot m\,\mathbf u-\sum_{\text{in}}\dot m\,\mathbf u$$
        """
    )
    render_derivation(
        "the integral momentum balance, and why the interior drops out",
        [
            (
                "Newton's second law applies to a body of fluid, not to a region of space",
                r"""
                Newton is a statement about a fixed **system** of matter: the rate of
                change of its momentum equals the force on it. But the object we care
                about — a bend, a gate, a nozzle — is fixed in space while fluid pours
                through it. Those are different things, and conflating them is the
                origin of nearly every sign error in this chapter.
                $$\left(\frac{d\mathbf P}{dt}\right)_{\text{system}}=\sum\mathbf F$$
                """,
            ),
            (
                "The Reynolds transport theorem converts one into the other",
                r"""
                Chapter 5 already used this for mass. For any extensive property with
                intensity $\mathbf b$ per unit mass, the rate of change following the
                matter equals the rate of change inside the fixed volume plus the net
                rate at which the property is *carried out* through the surface:
                $$\left(\frac{dB}{dt}\right)_{\text{sys}}
                =\frac{d}{dt}\int_{CV}\rho\,\mathbf b\,dV
                +\oint_{CS}\rho\,\mathbf b\,(\mathbf u\cdot\mathbf n)\,dA$$
                Setting $\mathbf b=\mathbf u$ (momentum per unit mass is just velocity)
                gives the momentum theorem. The second term is not a force; it is
                bookkeeping for matter walking across the boundary and taking its
                momentum with it.
                """,
            ),
            (
                r"$\mathbf u\cdot\mathbf n$ signs the flux automatically",
                r"""
                With $\mathbf n$ the **outward** normal, $\mathbf u\cdot\mathbf n$ is
                negative at an inlet and positive at an outlet, so the single surface
                integral already carries the "out minus in" structure. You never add
                that sign by hand. For a uniform one-dimensional inlet or outlet of
                area $A$ the integral is $\pm\dot m\mathbf u$ with $\dot m=\rho uA$.
                """,
            ),
            (
                "Steady does not mean uniform: the correction factor",
                r"""
                Real pipe flow is not a plug. Writing the flux with the mean speed
                undercounts it, exactly as it did for kinetic energy in chapter 1:
                $$\int_A\rho u^{2}\,dA=\beta\,\rho\bar u^{2}A,
                \qquad \beta\equiv\frac{1}{A\bar u^{2}}\int_A u^{2}\,dA$$
                Chapter 4 integrates the profiles: $\beta=4/3$ for the laminar
                parabola, and about $1.02$ for a turbulent pipe. Note that $\beta$ is
                much closer to one than the kinetic-energy $\alpha$ is, because
                momentum weights the profile by $u^{2}$ rather than $u^{3}$. Every
                calculator on this page takes $\beta=1$, which is a good assumption in
                turbulent flow and a two-percent error at worst; it is *not* safe for
                laminar flow, where it under-predicts the force by a third.
                """,
            ),
            (
                "Only two kinds of force can appear on the left",
                r"""
                Surface forces (pressure and shear over the control surface, plus
                whatever a support or a wall supplies where the surface cuts solid
                material) and body forces (weight). Nothing else exists — chapter 6
                established that a surface transmits force only through the stress
                tensor.
                $$\sum\mathbf F=\underbrace{\oint_{CS}\boldsymbol\sigma\cdot\mathbf n\,dA}
                _{\text{pressure, shear, and the support's reaction}}
                +\underbrace{\int_{CV}\rho\,\mathbf g\,dV}_{\text{weight}}$$
                """,
            ),
            (
                "Work in gauge pressure, and the atmosphere deletes itself exactly",
                r"""
                A uniform pressure over a closed surface contributes nothing, because
                $\oint\mathbf n\,dA=\mathbf 0$ — the same fact that made uniform
                pressure contribute no drag in chapter 9. So subtracting
                $p_{\text{atm}}$ everywhere changes no force, and it removes the large
                nearly-cancelling numbers that otherwise dominate the arithmetic. This
                is exact, not an approximation.
                """,
            ),
            (
                "Why the messy interior never appears",
                r"""
                Read the final equation again: every term lives on the boundary or is
                the total weight. Whatever happens inside — separation, a recirculating
                eddy, a turbulent roller, combustion — is invisible to it. That is the
                entire reason this chapter exists. Energy has no such property: a
                dissipative interior destroys mechanical energy, so Bernoulli fails
                precisely where momentum still works.
                """,
            ),
        ],
        symbols=[
            (r"\mathbf u", "velocity at a point on the control surface (m/s)."),
            (r"\mathbf n", "outward unit normal of the control surface."),
            (r"\dot m=\rho\bar uA", "mass flow through a one-dimensional face (kg/s)."),
            (r"\beta", "momentum-flux correction factor; 1 for a plug, 4/3 for a laminar pipe."),
            (r"\sum\mathbf F", "every surface and body force on the fluid inside the volume (N)."),
        ],
        closing=(
            "**Method, every time.** (1) Draw the control volume and say where each face is. "
            "(2) Mark the outward normal on each face. (3) List the forces on the fluid, in gauge "
            "pressure. (4) Write one scalar equation per direction. (5) Solve for the reaction, "
            "then flip its sign to get the force on the hardware."
        ),
    )
    render_callout(
        r"""
        **Where to cut the surface.** The balance is exact wherever you draw it, but it is
        only *useful* where you know the terms. Cut across a plane where the streamlines
        are straight and parallel, because there the pressure is hydrostatic (or uniform)
        and the velocity is a single number. Never cut through the middle of a jet, a
        separated eddy, or a section where the area is still changing: you would need the
        very pressure distribution you were trying to avoid computing.
        """,
        title="Choosing the control volume is the whole skill",
    )


# ==========================================================================
# 10.2 Jets and vanes
# ==========================================================================
def _section_jets() -> None:
    st.markdown("### 10.2 A jet on a vane · where the force comes from turning, not stopping")
    prose(
        r"""
        A free jet in air sits at atmospheric pressure along its whole length, so in gauge
        terms **there is no pressure force anywhere on the control surface**. Every newton
        the vane feels is momentum flux, which makes this the cleanest possible test of the
        theorem.
        $$F_x=\dot m\,w\,(1-\cos\theta),\qquad F_y=-\dot m\,w\sin\theta,\qquad w=V-U$$
        """
    )
    render_derivation(
        "the vane force, the moving-frame trick, and why a Pelton wheel runs at half jet speed",
        [
            (
                "A control volume around the vane, with the jet as its only traffic",
                r"""
                Take the surface to cut the incoming jet, the leaving sheet, and the vane
                support. On the jet faces the gauge pressure is zero (the jet is
                surrounded by atmosphere and its streamlines are straight), so the only
                force on the fluid is the reaction $\mathbf R$ from the vane. The
                momentum balance in $x$ is therefore
                $$R_x=\dot m\,u_{2x}-\dot m\,u_{1x}$$
                and the force on the vane is $-R_x$. Nothing else appears — no friction
                law, no profile, no assumption about the film of water on the blade.
                """,
            ),
            (
                "If the vane moves, ride with it",
                r"""
                A vane translating at constant $U$ is an inertial frame, so the balance
                holds unchanged in it, and in that frame the flow is **steady** —
                which the ground frame is not. The fluid enters at the relative speed
                $$w=V-U$$
                and, since the jet neither gains nor loses energy along a smooth blade
                (atmospheric pressure throughout, negligible elevation change), it
                *leaves at the same relative speed*, turned through the blade angle.
                Only the direction changes.
                """,
            ),
            (
                "Resolve, and the turning angle does all the work",
                r"""
                Entering along $+x$ with relative speed $w$ and leaving at angle $\theta$
                to it:
                $$u_{1x}=w,\qquad u_{2x}=w\cos\theta$$
                $$F_x=\dot m\,w\,(1-\cos\theta),\qquad F_y=-\dot m\,w\sin\theta$$
                Read the factor $(1-\cos\theta)$: at $\theta=0$ the vane does nothing;
                at $\theta=90^\circ$ it is $1$; at $\theta=180^\circ$ it is **2**. A
                bucket that reverses the jet is twice as strong as a flat plate that
                merely stops it, because it must also throw the water back.
                """,
            ),
            (
                "Which mass flow? The commonest error in the chapter",
                r"""
                For a **single** vane running away from the nozzle, the jet has to chase
                it, and the vane only intercepts $\dot m=\rho A(V-U)$. For a **wheel of
                buckets**, each bucket is replaced by the next as it moves away, so the
                machine as a whole intercepts the entire jet, $\dot m=\rho AV$. The
                Pelton turbine is the second case, and the difference changes the answer
                completely: the optimum runs at $U=V/2$ instead of $U=V/3$.
                """,
            ),
            (
                r"Power, and the maximum at $U=V/2$",
                r"""
                Power is force times the speed the force travels at:
                $$P=F_xU=\rho AV(V-U)(1-\cos\theta)\,U$$
                With $\theta=180^\circ$ and the jet power $\tfrac12\rho AV^{3}$ as the
                denominator,
                $$\eta=\frac{2\rho AV(V-U)U}{\tfrac12\rho AV^{3}}=\frac{4U(V-U)}{V^{2}}$$
                $$\frac{d\eta}{dU}=\frac{4V-8U}{V^{2}}=0\;\Longrightarrow\;U=\frac{V}{2},
                \qquad\eta_{\max}=1$$
                At that speed the water leaves with **zero absolute velocity**: it has
                given up everything it had, and falls out of the bucket. That is the
                physical meaning of a hundred percent — and also why a real wheel uses
                about $165^\circ$ rather than $180^\circ$, so the discharged sheet
                misses the following bucket.
                """,
            ),
            (
                r"The single vane: same algebra, a smaller $\dot m$",
                r"""
                A lone vane only intercepts $\dot m=\rho A(V-U)$, so the extra factor of
                $(V-U)$ that the wheel case did not carry survives into the power:
                $$P=F_xU=\rho A(V-U)^2(1-\cos\theta)\,U$$
                Dividing by the same jet power $\tfrac12\rho AV^{3}$ and writing $x=U/V$,
                with $\theta=180^\circ$:
                $$\eta(x)=4x(1-x)^{2}$$
                $$\frac{d\eta}{dx}=4(1-x)(1-3x)=0\;\Longrightarrow\;x=\frac13\ \text{or}\
                x=1\ (\eta=0)$$
                $$\eta_{\max}=4\cdot\frac13\cdot\left(\frac23\right)^{2}=\frac{16}{27}
                \approx0.593\quad\text{at }U=\frac V3$$
                The peak moves from $U=V/2$ to $U=V/3$ and drops from $1$ to $16/27$ for
                the same reason: a vane running away lets most of the jet go past
                uncaught, and no amount of turning angle recovers momentum from water
                the vane never touched.
                """,
            ),
        ],
        closing=(
            "The same reasoning, with the blade speed written as $U=\\omega r$ and the "
            "*angular* momentum balance instead of the linear one, is exactly what chapter 11 "
            "uses to derive Euler's turbomachinery equation. This section is that derivation "
            "with the radius held constant."
        ),
    )

    st.markdown("#### 10.2.1 Lab · a jet, a bucket and a wheel")
    fluid = get_fluid_state()
    rho = fluid["rho"]
    c1, c2, c3, c4 = st.columns(4)
    d_jet = persistent_input(
        c1.number_input, "Jet diameter [mm]", min_value=1.0, max_value=500.0,
        value=50.0, step=5.0, key="mom_jet_d",
    ) / 1000.0
    v_jet = persistent_input(
        c2.number_input, "Jet speed V [m/s]", min_value=0.1, max_value=200.0,
        value=30.0, step=1.0, key="mom_jet_v",
    )
    u_vane = persistent_input(
        c3.number_input, "Vane speed U [m/s]", min_value=0.0, max_value=200.0,
        value=15.0, step=1.0, key="mom_jet_u",
    )
    theta = persistent_input(
        c4.number_input, "Deflection θ [deg]", min_value=0.0, max_value=180.0,
        value=165.0, step=5.0, key="mom_jet_theta",
    )
    arrangement = persistent_input(
        st.radio, "Arrangement", options=["Wheel of buckets (Pelton)", "One isolated vane"],
        key="mom_jet_series", horizontal=True,
    )
    series = arrangement.startswith("Wheel")
    area = math.pi * d_jet**2 / 4.0
    jet = mom.jet_on_vane(rho, area, v_jet, u_vane, theta, series=series)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Force along the jet", f"{jet['force_x'] / 1000:.3g} kN")
    m2.metric("Force across it", f"{jet['force_y'] / 1000:.3g} kN")
    m3.metric("Shaft power", f"{jet['power'] / 1000:.4g} kW")
    m4.metric("Efficiency", f"{100 * jet['efficiency']:.1f} %")
    st.caption(
        f"ρ = {rho:g} kg/m³ · jet area {area * 1e4:.2f} cm² · mass flow intercepted "
        f"{jet['mass_flow']:.1f} kg/s of the {jet['jet_mass_flow']:.1f} kg/s the nozzle "
        f"delivers · relative speed w = {jet['relative_speed']:.2f} m/s · jet power "
        f"{jet['jet_power'] / 1000:.4g} kW. Best vane speed for this arrangement: "
        f"{jet['optimum_vane_speed']:.2f} m/s."
    )
    if u_vane >= v_jet:
        st.warning(
            "The vane is running at or above the jet speed, so nothing catches up with it: "
            "the relative speed is zero or negative and the model has left its range."
        )

    ratio = np.linspace(0.0, 1.0, 121)
    fig = go.Figure()
    for label, is_series in (("Wheel of buckets · ṁ = ρAV", True), ("Single vane · ṁ = ρA(V−U)", False)):
        eff = [
            mom.jet_on_vane(rho, area, v_jet, r * v_jet, theta, series=is_series)["efficiency"]
            for r in ratio
        ]
        fig.add_trace(go.Scatter(x=ratio, y=eff, name=label, mode="lines"))
    fig.add_trace(
        go.Scatter(
            x=[u_vane / v_jet], y=[jet["efficiency"]], mode="markers",
            marker=dict(size=12, symbol="x"), name="your setting",
        )
    )
    fig.update_layout(
        title=f"Efficiency against speed ratio, at θ = {theta:g}°",
        xaxis_title="U / V", yaxis_title="Power / jet power", height=420,
    )
    apply_plotly_theme(fig)
    render_plot(fig, "momentum-jet-efficiency")
    render_what_to_notice(
        "The wheel peaks at U/V = 0.5 and the single vane at U/V = 1/3, and the single vane's "
        "best efficiency is only 16/27 — it never even catches most of the water. Lowering θ "
        "below 180° scales both curves down by (1 − cos θ)/2 without moving their peaks."
    )
    render_self_check(
        "mom_check_jet",
        "A Pelton wheel is running at U = V/2 with 180° buckets. What is the absolute "
        "velocity of the water leaving the bucket?",
        [
            "V/2 forwards — it keeps half of what it had",
            "Zero — it has given up all of its kinetic energy",
            "V backwards — the bucket reverses it",
        ],
        "Zero — it has given up all of its kinetic energy",
        "In the bucket frame the water leaves at −w = −(V − U) = −V/2, and the bucket itself "
        "moves at +V/2, so in the ground frame the two cancel exactly. That is why the "
        "efficiency reaches one there: nothing walks away with kinetic energy.",
    )


# ==========================================================================
# 10.3 Bends
# ==========================================================================
def _section_bends() -> None:
    st.markdown("### 10.3 Pipe bends and reducers · the load on the thrust block")
    prose(
        r"""
        Inside a pipe the pressure force is usually much the larger of the two terms, and it
        does not cancel once the pipe turns. A buried main that changes direction needs a
        concrete thrust block sized for exactly this calculation; an unanchored flanged bend
        is a classic way to separate a pipeline.
        $$\mathbf F_{\text{on bend}}=\left(p_1A_1+\dot mu_1\right)\hat{\mathbf e}_1
        -\left(p_2A_2+\dot mu_2\right)\hat{\mathbf e}_2$$
        """
    )
    render_derivation(
        "the anchor force on a reducing bend, one direction at a time",
        [
            (
                "Cut the control surface across two straight runs, and through the bolts",
                r"""
                Put face 1 and face 2 far enough from the elbow that the streamlines are
                parallel there, so the pressure is uniform across each face and one
                velocity describes it. The surface also cuts the pipe wall, and where it
                does, the metal exerts an unknown reaction $\mathbf R$ on the fluid.
                That reaction is the answer we want.
                """,
            ),
            (
                "Continuity fixes the two speeds before any force is written",
                r"""
                $$u_1=\frac{Q}{A_1},\qquad u_2=\frac{Q}{A_2},\qquad \dot m=\rho Q$$
                In a *reducing* bend $u_2>u_1$, and the momentum change has a
                contribution from the speeding up as well as from the turning.
                """,
            ),
            (
                "Energy supplies the downstream pressure, which momentum cannot",
                r"""
                The momentum balance has two unknowns, $\mathbf R$ and $p_2$, so it needs
                one more equation — and this is the one place a bend calculation must
                borrow from chapter 1:
                $$p_2=p_1+\tfrac12\rho\left(u_1^{2}-u_2^{2}\right)-K_L\tfrac12\rho u_1^{2}$$
                Set $K_L=0$ for the ideal estimate. A real elbow loses roughly
                $K_L\approx0.3$ velocity heads, and dropping $p_2$ lowers the computed
                force, so the ideal number is the conservative one for sizing an anchor.
                """,
            ),
            (
                "Write one scalar equation per direction",
                r"""
                With the outlet along $(\cos\theta,\sin\theta)$ and gauge pressures
                pushing **inward** on each face:
                $$R_x=\dot m\,u_2\cos\theta-\dot m\,u_1-p_1A_1+p_2A_2\cos\theta$$
                $$R_y=\dot m\,u_2\sin\theta+p_2A_2\sin\theta$$
                The force on the *bend* is minus this, which rearranges into the boxed
                form above: each face contributes its pressure force plus its momentum
                flux, and the two faces are subtracted as vectors.
                """,
            ),
            (
                "Sanity checks that catch a sign error immediately",
                r"""
                **Straight run, no area change, no loss:** $\theta=0$ and $p_2=p_1$ make
                the two vectors identical and the force is exactly zero — a straight
                pipe needs no anchor, which is why the balance must give this.
                **Return bend, $\theta=180^\circ$:** the two contributions now *add*,
                giving $2(pA+\dot mu)$, the largest force any fitting can carry.
                Any algebra that fails either check is wrong.
                """,
            ),
            (
                "Which term dominates, and when",
                r"""
                Compare $pA$ with $\dot mu=\rho Au^{2}$: their ratio is
                $p/(\rho u^{2})$, an Euler number. In a water main at a few metres per
                second and a few bar, $\rho u^{2}\sim10^{4}$ Pa against
                $p\sim10^{5}$ Pa, so **pressure wins by an order of magnitude** and the
                thrust block is essentially resisting static pressure. In a free jet or
                a rocket exhaust, gauge pressure is zero and momentum is all there is.
                The lab below prints both parts so you can see which regime you are in.
                """,
            ),
        ],
    )

    st.markdown("#### 10.3.1 Lab · anchor force on a bend")
    fluid = get_fluid_state()
    rho = fluid["rho"]
    c1, c2, c3 = st.columns(3)
    d1 = persistent_input(
        c1.number_input, "Inlet diameter [mm]", min_value=10.0, max_value=3000.0,
        value=300.0, step=10.0, key="mom_bend_d1",
    ) / 1000.0
    d2 = persistent_input(
        c2.number_input, "Outlet diameter [mm]", min_value=10.0, max_value=3000.0,
        value=200.0, step=10.0, key="mom_bend_d2",
    ) / 1000.0
    angle = persistent_input(
        c3.number_input, "Turn angle [deg]", min_value=0.0, max_value=180.0,
        value=90.0, step=15.0, key="mom_bend_angle",
    )
    c4, c5, c6 = st.columns(3)
    q = persistent_input(
        c4.number_input, "Flow rate Q [m³/s]", min_value=0.001, max_value=20.0,
        value=0.25, step=0.01, key="mom_bend_q",
    )
    p1 = persistent_input(
        c5.number_input, "Inlet gauge pressure [kPa]", min_value=0.0, max_value=10000.0,
        value=400.0, step=25.0, key="mom_bend_p1",
    ) * 1000.0
    k_loss = persistent_input(
        c6.number_input, "Bend loss coefficient K", min_value=0.0, max_value=2.0,
        value=0.0, step=0.05, key="mom_bend_k",
    )
    bend = mom.bend_force(rho, d1, d2, q, p1, angle, loss_k=k_loss)
    m1, m2, m3 = st.columns(3)
    m1.metric("Anchor force", f"{bend['force'] / 1000:.4g} kN")
    m2.metric("Direction from inlet axis", f"{bend['direction_deg']:.1f} °")
    m3.metric("Outlet gauge pressure", f"{bend['p2_gauge'] / 1000:.4g} kPa")
    st.caption(
        f"u₁ = {bend['u_in']:.2f} m/s, u₂ = {bend['u_out']:.2f} m/s, ṁ = {bend['mass_flow']:.1f} kg/s. "
        f"Components: Fx = {bend['force_x'] / 1000:.3g} kN, Fy = {bend['force_y'] / 1000:.3g} kN. "
        f"The pressure terms contribute {bend['pressure_part'] / 1000:.3g} kN and the momentum "
        f"terms {bend['momentum_part'] / 1000:.3g} kN — a ratio of "
        f"{bend['pressure_part'] / bend['momentum_part']:.1f} to 1."
        if bend["momentum_part"] > 0
        else "Zero flow: only the pressure terms remain."
    )
    if bend["p2_gauge"] < 0:
        st.warning(
            "The computed outlet pressure is below atmospheric. Either the reducer is too "
            "aggressive for this flow or the loss coefficient is too large; a real line would "
            "be at risk of cavitation here (chapter 2's NPSH check is the same physics)."
        )
    render_predict(
        "mom_predict_bend",
        "Keeping everything else fixed, you double the inlet gauge pressure on a 90° bend. "
        "The anchor force…",
        ["roughly doubles", "is unchanged", "rises by about 40%"],
        "roughly doubles",
        "In a water main the pressure terms dominate the momentum terms by roughly an order "
        "of magnitude, so the force is very nearly proportional to pressure. Try it in the lab "
        "and watch the pressure/momentum ratio in the caption to see how far from exactly "
        "double it lands.",
    )


# ==========================================================================
# 10.4 Sudden expansion
# ==========================================================================
def _section_expansion() -> None:
    st.markdown("### 10.4 Sudden expansion · two balances on one control volume")
    prose(
        r"""
        Chapter 2 derived the Borda–Carnot head loss to justify the fitting coefficient
        $K_L=(1-A_1/A_2)^2$. Here the same control volume is read for what it says about
        *pressure* and about *force*, because that is what makes the trick general: momentum
        gives the pressure rise a dissipative device actually achieves, energy says what an
        ideal one would have achieved, and the gap between them is the loss.
        $$\underbrace{p_2-p_1=\rho u_2(u_1-u_2)}_{\text{momentum}}
        \qquad
        \underbrace{p_2-p_1=\tfrac12\rho(u_1^{2}-u_2^{2})}_{\text{ideal, Bernoulli}}$$
        """
    )
    render_derivation(
        "the pressure rise, the loss, and the force on the step",
        [
            (
                "The modelling assumption is about the step face, and it is the only one",
                r"""
                The jet leaving the small pipe cannot turn the corner, so it separates and
                a slow recirculating eddy fills the annular corner. Because that eddy is
                nearly stagnant and the streamlines through the plane are still straight,
                the pressure over the **whole** face — the jet and the annulus alike — is
                effectively $p_1$. Everything else follows without further assumption.
                Note what is *not* assumed: nothing about the eddy's shape, its
                turbulence, or where the jet reattaches.
                """,
            ),
            (
                "Momentum from the step plane to a refilled section",
                r"""
                Take face 2 far enough downstream that the pipe is running full and
                parallel again. Neglecting wall shear over that short length:
                $$(p_1-p_2)A_2=\dot m(u_2-u_1)=\rho A_2u_2(u_2-u_1)$$
                $$\Longrightarrow\;p_2-p_1=\rho u_2(u_1-u_2)>0$$
                The pressure **rises**, because the flow is decelerating and something
                must be pushing back on it. That is a genuine, useful pressure recovery,
                not an artefact.
                """,
            ),
            (
                "Energy on the same two faces defines the loss",
                r"""
                $$g\,h_L=\frac{p_1-p_2}{\rho}+\frac{u_1^{2}-u_2^{2}}{2}$$
                Substituting the momentum result collapses it to a perfect square, as
                chapter 2 showed:
                $$g\,h_L=\frac{(u_1-u_2)^{2}}{2}
                \;\Longrightarrow\;h_L=\frac{(u_1-u_2)^{2}}{2g}$$
                What is dissipated is the kinetic energy of the **velocity difference** —
                the relative motion the jet must mix away.
                """,
            ),
            (
                "Read the same two equations as a recovery fraction",
                r"""
                Bernoulli would have promised $\tfrac12\rho(u_1^{2}-u_2^{2})$. Subtract:
                $$\underbrace{\tfrac12\rho(u_1^{2}-u_2^{2})}_{\text{ideal}}
                -\underbrace{\rho u_2(u_1-u_2)}_{\text{actual}}
                =\tfrac12\rho(u_1-u_2)^{2}=\rho g h_L$$
                So the two balances are not rivals: their **difference is the loss**, and
                the ratio of actual to ideal is the pressure recovery a diffuser designer
                quotes. A gradual conical diffuser exists precisely to move that ratio
                towards one by avoiding the separation this geometry guarantees.
                """,
            ),
            (
                "The force the fluid puts on the step",
                r"""
                The annular face is a real piece of metal, and it carries
                $$F_{\text{step}}=p_1\left(A_2-A_1\right)$$
                pushing downstream. This is what the momentum balance assumed, so
                computing it is a consistency check rather than a new result — but it is
                also the number a flange design needs, and it is dominated by static
                pressure in exactly the way the bend of §10.3 was.
                """,
            ),
            (
                "The limit that explains the exit fitting",
                r"""
                Let $A_2\to\infty$: a pipe discharging into a tank. Then $u_2\to0$,
                $K_L\to1$, and the fitting throws away exactly one velocity head. The
                pressure recovery also goes to zero, which is the honest statement of
                what a plain open-ended pipe does with its kinetic energy.
                """,
            ),
        ],
    )

    st.markdown("#### 10.4.1 Lab · what an abrupt enlargement recovers and what it wastes")
    fluid = get_fluid_state()
    rho = fluid["rho"]
    c1, c2, c3, c4 = st.columns(4)
    d1 = persistent_input(
        c1.number_input, "Small pipe [mm]", min_value=5.0, max_value=2000.0,
        value=100.0, step=5.0, key="mom_exp_d1",
    ) / 1000.0
    d2 = persistent_input(
        c2.number_input, "Large pipe [mm]", min_value=6.0, max_value=4000.0,
        value=200.0, step=5.0, key="mom_exp_d2",
    ) / 1000.0
    u1 = persistent_input(
        c3.number_input, "Speed in the small pipe [m/s]", min_value=0.1, max_value=30.0,
        value=4.0, step=0.5, key="mom_exp_u1",
    )
    p1 = persistent_input(
        c4.number_input, "Upstream gauge pressure [kPa]", min_value=0.0, max_value=5000.0,
        value=200.0, step=10.0, key="mom_exp_p1",
    ) * 1000.0
    if d2 <= d1:
        st.warning("The downstream pipe must be larger than the upstream one for an expansion.")
        return
    exp = mom.sudden_expansion(rho, d1, d2, u1, p1)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Actual pressure rise", f"{exp['pressure_rise'] / 1000:.4g} kPa")
    m2.metric("Ideal (Bernoulli) rise", f"{exp['ideal_pressure_rise'] / 1000:.4g} kPa")
    m3.metric("Head loss", f"{exp['head_loss']:.4g} m")
    m4.metric("Pressure recovered", f"{100 * exp['pressure_recovery_fraction']:.1f} %")
    st.caption(
        f"Area ratio A₁/A₂ = {exp['area_ratio']:.3f}, so K = {exp['loss_coefficient']:.3f} and "
        f"u₂ = {exp['u_out']:.2f} m/s. The Bernoulli defect is "
        f"{exp['pressure_defect'] / 1000:.4g} kPa, which equals ρg·h_L = "
        f"{rho * mom.G * exp['head_loss'] / 1000:.4g} kPa — the same number by two routes. "
        f"At this flow the step wastes {exp['dissipated_power'] / 1000:.3g} kW, and pushes "
        f"{exp['step_force'] / 1000:.3g} kN downstream on the annular face."
    )
    ratios = np.linspace(0.02, 0.98, 120)
    recovery = [
        mom.sudden_expansion(rho, d1, d1 / math.sqrt(r), u1)["pressure_recovery_fraction"]
        for r in ratios
    ]
    losses = [
        mom.sudden_expansion(rho, d1, d1 / math.sqrt(r), u1)["loss_coefficient"] for r in ratios
    ]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ratios, y=recovery, name="Pressure recovered / ideal"))
    fig.add_trace(go.Scatter(x=ratios, y=losses, name="Loss coefficient K on u₁"))
    fig.add_trace(
        go.Scatter(
            x=[exp["area_ratio"]], y=[exp["pressure_recovery_fraction"]],
            mode="markers", marker=dict(size=12, symbol="x"), name="your setting",
        )
    )
    fig.update_layout(
        title="An abrupt expansion is worst where it changes the most",
        xaxis_title="Area ratio A₁/A₂", yaxis_title="Fraction [-]", height=420,
    )
    apply_plotly_theme(fig)
    render_plot(fig, "momentum-expansion")
    render_what_to_notice(
        "The recovered fraction is 2r/(1+r) with r = A₁/A₂, so the two curves tell the same "
        "story from opposite ends: a barely-changing area recovers nearly everything and loses "
        "almost nothing, while discharging into a tank (r → 0) recovers nothing and throws away "
        "a full velocity head."
    )


# ==========================================================================
# 10.5 Hydraulic jump
# ==========================================================================
def _section_jump() -> None:
    st.markdown("### 10.5 The hydraulic jump · momentum where energy is destroyed")
    render_svg(diagram_hydraulic_jump())
    prose(
        r"""
        Chapter 2 established that a supercritical stream cannot be influenced from
        downstream: no wave can travel back up it. When such a stream has to meet a
        subcritical depth — below a spillway, downstream of a sluice gate — it cannot adjust
        gradually, so it does so through a short, violent, turbulent front. Energy is
        destroyed there in an amount nobody can compute from the interior, and momentum
        does not care.
        $$M=\frac{q^{2}}{gy}+\frac{y^{2}}{2}\ \ \text{is equal on both sides}
        \qquad\Longrightarrow\qquad
        \frac{y_2}{y_1}=\frac12\left(\sqrt{1+8\,\mathrm{Fr}_1^{2}}-1\right)$$
        """
    )
    render_derivation(
        "conjugate depths from the momentum function, and the loss the jump hides",
        [
            (
                "Why energy is unavailable and momentum is not",
                r"""
                The roller is unsteady, aerated and strongly turbulent: there is no way
                to write its dissipation from first principles, so **specific energy
                cannot be equated across the jump**. But the control volume from just
                upstream to just downstream has straight, parallel, hydrostatic flow on
                both faces, a short horizontal bed (so bed shear is negligible over the
                length), and no other external force. Momentum is therefore exact here
                while energy is merely unknown. This is the same division of labour as
                the normal shock in chapter 12.
                """,
            ),
            (
                "The two forces on the faces are hydrostatic",
                r"""
                Because the streamlines are parallel at each face, the pressure there
                varies hydrostatically, and integrating $\rho g(y-z)$ over the depth
                gives the familiar resultant per unit width acting at $y/3$ above the
                bed:
                $$F=\int_0^{y}\rho g(y-z)\,dz=\frac{\rho gy^{2}}{2}$$
                No new physics — this is the hydrostatics of chapter 1, applied face by
                face.
                """,
            ),
            (
                "Momentum per unit width, with q as the constant",
                r"""
                Continuity per unit width gives $q=u_1y_1=u_2y_2$, so the momentum flux
                at a face is $\rho q u=\rho q^{2}/y$. The balance is
                $$\frac{\rho gy_1^{2}}{2}-\frac{\rho gy_2^{2}}{2}
                =\rho q^{2}\left(\frac{1}{y_2}-\frac{1}{y_1}\right)$$
                Divide by $\rho g$ and gather each depth on its own side:
                $$\frac{q^{2}}{gy_1}+\frac{y_1^{2}}{2}
                =\frac{q^{2}}{gy_2}+\frac{y_2^{2}}{2}
                \;\equiv\;M$$
                That function $M(y)$ is the **momentum function**, and the whole jump is
                the statement that it takes the same value on both sides. Two depths
                share each value of $M$ — the *conjugate* pair — exactly as two depths
                share each value of specific energy.
                """,
            ),
            (
                "Solve the cubic, and discard the root you already have",
                r"""
                Multiplying out, $M(y_1)=M(y_2)$ is a cubic in $y_2$ with the known root
                $y_2=y_1$. Dividing it out leaves a quadratic,
                $$y_2^{2}+y_1y_2-\frac{2q^{2}}{gy_1}=0$$
                whose positive root, written with
                $\mathrm{Fr}_1=u_1/\sqrt{gy_1}$ so that $q^{2}=\mathrm{Fr}_1^{2}gy_1^{3}$, is
                $$\frac{y_2}{y_1}=\frac12\left(\sqrt{1+8\,\mathrm{Fr}_1^{2}}-1\right)$$
                the Bélanger equation. Check it: $\mathrm{Fr}_1=1$ gives
                $y_2/y_1=\tfrac12(3-1)=1$ — at critical flow there is nothing to jump.
                """,
            ),
            (
                "Now go back to energy — not to solve, but to measure",
                r"""
                With both depths known, the dissipation is simply the difference in
                specific energy, and it factors beautifully:
                $$\Delta E=E_1-E_2=\frac{(y_2-y_1)^{3}}{4y_1y_2}$$
                The cube is worth staring at. A weak jump ($y_2\approx y_1$) destroys
                almost nothing; a strong one destroys a large fraction of the approach
                energy. **This is the only equation in the chapter that came from energy,
                and it came last** — after momentum had already supplied the geometry.
                """,
            ),
            (
                "What this is for",
                r"""
                A stilling basin below a spillway exists to force the jump to happen
                where the concrete can survive it, rather than letting a supercritical
                sheet run downstream and scour out the toe of the dam. The design
                variables are exactly the ones above: the approach Froude number sets the
                jump type and the tailwater must be deep enough to hold $y_2$, or the
                jump is swept downstream.
                """,
            ),
        ],
    )

    st.markdown("#### 10.5.1 Lab · conjugate depths and dissipation")
    c1, c2 = st.columns(2)
    y1 = persistent_input(
        c1.number_input, "Approach depth y₁ [m]", min_value=0.02, max_value=5.0,
        value=0.30, step=0.05, key="mom_jump_y1",
    )
    q_unit = persistent_input(
        c2.number_input, "Discharge per unit width q [m²/s]", min_value=0.05, max_value=30.0,
        value=2.50, step=0.1, key="mom_jump_q",
    )
    jump = mom.hydraulic_jump(y1, q_unit)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Approach Froude Fr₁", f"{jump['froude_1']:.3f}")
    m2.metric("Sequent depth y₂", f"{jump['y2']:.3f} m")
    m3.metric("Energy lost", f"{jump['energy_loss']:.4g} m")
    m4.metric("Fraction of E₁ lost", f"{100 * jump['loss_fraction']:.1f} %")
    st.caption(
        f"u₁ = {jump['u1']:.2f} m/s → u₂ = {jump['u2']:.2f} m/s; Fr₂ = {jump['froude_2']:.3f}. "
        f"Critical depth for this discharge is {jump['critical_depth']:.3f} m, and the jump "
        f"straddles it. Momentum function: M₁ = {jump['momentum_1']:.4f} m² and "
        f"M₂ = {jump['momentum_2']:.4f} m² — equal, as the balance requires — while specific "
        f"energy falls from {jump['energy_1']:.4f} m to {jump['energy_2']:.4f} m. "
        f"Classification: {jump['kind']}."
    )
    if not jump["exists"]:
        st.warning(
            "The approach flow is subcritical (Fr₁ < 1), so there is no jump: the second root "
            "of the momentum function is a *drop*, and a drop would have to create energy. "
            "Reduce the depth or raise the discharge to make the approach supercritical."
        )

    depths = np.linspace(max(0.02, 0.05 * jump["critical_depth"]), 2.2 * max(jump["y2"], y1), 400)
    energies = [mom.specific_energy(y, q_unit) for y in depths]
    momenta = [mom.momentum_function(y, q_unit) for y in depths]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=energies, y=depths, name="Specific energy E(y) [m]"))
    fig.add_trace(go.Scatter(x=momenta, y=depths, name="Momentum function M(y) [m²]"))
    fig.add_trace(
        go.Scatter(
            x=[jump["energy_1"], jump["energy_2"]], y=[y1, jump["y2"]],
            mode="markers+text", text=["1", "2"], textposition="middle right",
            marker=dict(size=11), name="the two states, on E",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[jump["momentum_1"], jump["momentum_2"]], y=[y1, jump["y2"]],
            mode="markers", marker=dict(size=11, symbol="square-open"),
            name="the two states, on M",
        )
    )
    fig.add_hline(y=jump["critical_depth"], line_dash="dot", annotation_text="critical depth")
    fig.update_layout(
        title="The jump moves vertically on M and leftwards on E",
        xaxis_title="E [m] or M [m²]", yaxis_title="Depth y [m]", height=460,
    )
    apply_plotly_theme(fig)
    render_plot(fig, "momentum-jump-curves")
    render_what_to_notice(
        "The two square markers sit at the same M — that is the whole solution, read off a "
        "curve. The two round markers do not sit at the same E, and the horizontal gap between "
        "them is the dissipation. Both curves have their nose at the same critical depth, which "
        "is why minimum energy and minimum momentum coincide there."
    )
    render_self_check(
        "mom_check_jump",
        "Why can the sequent depth not be obtained from Bernoulli?",
        [
            "Because the flow is compressible in the roller",
            "Because the roller dissipates an unknown amount of energy, while momentum only counts the boundary",
            "Because the bed slope is unknown",
        ],
        "Because the roller dissipates an unknown amount of energy, while momentum only counts the boundary",
        "Applying energy would give the *alternate* depth (same E), not the sequent depth (same M), "
        "and it would predict no loss at all. The dissipation is then recovered afterwards, as the "
        "difference between the two specific energies.",
    )


# ==========================================================================
# 10.6 Weirs and gates
# ==========================================================================
def _section_weirs() -> None:
    st.markdown("### 10.6 Weirs and gates · measuring flow with geometry")
    render_svg(diagram_weir_and_gate())
    prose(
        r"""
        Chapter 2 showed that critical depth depends on discharge and cross-section alone —
        not on roughness or slope. That independence is what a flow-measuring structure sells:
        force the flow through a geometry you control, read one depth, and the discharge
        follows without knowing anything about the channel.
        $$Q_{\text{rect}}=\tfrac23C_db\sqrt{2g}\,H^{3/2},\qquad
        Q_{\text{V-notch}}=\tfrac{8}{15}C_d\tan\!\frac{\theta}{2}\sqrt{2g}\,H^{5/2}$$
        """
    )
    render_derivation(
        "the weir formula by integration, and why the exponent is the whole design choice",
        [
            (
                "Treat each horizontal strip of the nappe as a small free jet",
                r"""
                Take the reservoir surface as the datum and follow a streamline to the
                crest. The flow there is a free sheet at atmospheric pressure, so
                Bernoulli from the still upstream surface to a point a depth $h$ below it
                gives Torricelli's speed:
                $$u(h)=\sqrt{2gh}$$
                This is the one place in the chapter where energy leads and momentum
                follows — a free jet has no dissipation to hide, so Bernoulli is
                legitimate.
                """,
            ),
            (
                "Integrate over the depth of the nappe, not the width",
                r"""
                A strip of thickness $dh$ at depth $h$ has area $b\,dh$ for a
                rectangular notch, so
                $$Q=\int_0^{H}b\sqrt{2gh}\;dh
                =b\sqrt{2g}\left[\frac{2}{3}h^{3/2}\right]_0^{H}
                =\frac{2}{3}b\sqrt{2g}\,H^{3/2}$$
                The $2/3$ is nothing but the integral of $h^{1/2}$, and the $3/2$ power
                is the deep reason a weir reading is *nonlinear*: a ten-percent error in
                head becomes a fifteen-percent error in flow.
                """,
            ),
            (
                r"Change the notch shape and the exponent changes with it",
                r"""
                In a V-notch of included angle $\theta$, the strip width itself grows
                with depth: at depth $h$ below the surface, the water is
                $2(H-h)\tan(\theta/2)$ wide. So
                $$Q=\int_0^{H}2(H-h)\tan\frac{\theta}{2}\sqrt{2gh}\,dh
                =\frac{8}{15}\tan\frac{\theta}{2}\sqrt{2g}\,H^{5/2}$$
                The steeper $5/2$ power is why a V-notch is the standard gauge for small
                and variable flows: at low flow the rectangular weir's head becomes tiny
                and unreadable, while the V-notch keeps a measurable head.
                """,
            ),
            (
                r"$C_d$ is the honest accounting of everything the integral ignored",
                r"""
                The integration assumed no contraction at the crest, no viscosity, no
                surface tension, no approach velocity, and parallel streamlines — all
                false. The measured coefficient absorbs them, and it is not a constant:
                Rehbock's fit
                $$C_d=0.611+0.075\frac{H}{P}$$
                rises as the nappe grows relative to the crest height $P$, because a
                faster approach flow carries velocity head the derivation left out. A
                weir also needs its nappe **ventilated**: if the air beneath is entrained
                away, the sheet clings to the plate, the pressure under it falls, and the
                discharge for a given head rises out of calibration.
                """,
            ),
            (
                "A broad-crested weir is a different mechanism with the same job",
                r"""
                Make the crest long enough and the flow becomes parallel *on* the crest,
                which forces it through critical depth there. Then chapter 2's result
                applies directly: $y_c=\tfrac23H$ and $q=\sqrt g\,y_c^{3/2}$, giving
                $$Q=C_db\sqrt g\left(\tfrac23H\right)^{3/2}$$
                Same exponent, different physics: the sharp-crested weir is a free jet,
                the broad-crested one is a critical-flow control.
                """,
            ),
        ],
    )
    render_derivation(
        "the load on a sluice gate: energy for the discharge, momentum for the force",
        [
            (
                "The vena contracta is where the flow is parallel again",
                r"""
                Directly under the gate the streamlines are still curving, so pressure
                there is not hydrostatic and no control-volume face may be drawn. A short
                distance downstream the jet has contracted to its minimum and become
                parallel; that plane, at $y_2=C_ca$ with $C_c\approx0.61$ for a sharp
                edge, is the face to use.
                """,
            ),
            (
                "Energy first, because the reach is short and smooth",
                r"""
                Between the pool and the vena contracta there is no separation and little
                friction, so specific energy is conserved:
                $$y_1+\frac{q^{2}}{2gy_1^{2}}=y_2+\frac{q^{2}}{2gy_2^{2}}$$
                Solving for $q$ gives, without approximation,
                $$q=y_1y_2\sqrt{\frac{2g}{y_1+y_2}}$$
                Note the gate has forced the flow supercritical: $y_2$ is below critical
                depth, which is what makes a downstream hydraulic jump inevitable and
                connects this section directly to §10.5.
                """,
            ),
            (
                "Momentum second, on the same two faces, for the force",
                r"""
                Both faces are parallel flow, so both pressure resultants are
                hydrostatic. Per unit width, with $F_g$ the force the gate exerts on the
                fluid (upstream, opposing the flow):
                $$\frac{\rho gy_1^{2}}{2}-\frac{\rho gy_2^{2}}{2}-F_g
                =\rho q\left(u_2-u_1\right)$$
                $$\Longrightarrow\;
                F_g=\frac{\rho g}{2}\left(y_1^{2}-y_2^{2}\right)-\rho q(u_2-u_1)$$
                and the force on the gate is equal and opposite.
                """,
            ),
            (
                "Read the answer against the wrong answer",
                r"""
                A designer's first instinct is the hydrostatic thrust of a solid wall,
                $\tfrac12\rho gy_1^{2}$. The gate carries **less** than that, and the two
                terms above say exactly why: part of the upstream pressure force is spent
                accelerating the water rather than being resisted by the gate. Using the
                hydrostatic value is conservative for the gate structure and wrong for
                anything that needs the actual load — a lifting mechanism, or a check on
                the reaction at the sill. The lab prints both.
                """,
            ),
        ],
    )

    st.markdown("#### 10.6.1 Lab · a weir and a gate on the same channel")
    c1, c2, c3 = st.columns(3)
    head = persistent_input(
        c1.number_input, "Head over the weir crest H [m]", min_value=0.01, max_value=2.0,
        value=0.25, step=0.01, key="mom_weir_h",
    )
    width = persistent_input(
        c2.number_input, "Weir / channel width b [m]", min_value=0.1, max_value=20.0,
        value=1.50, step=0.1, key="mom_weir_b",
    )
    crest = persistent_input(
        c3.number_input, "Crest height above the bed P [m]", min_value=0.05, max_value=5.0,
        value=0.50, step=0.05, key="mom_weir_p",
    )
    rect = mom.rectangular_weir(head, width, crest_height=crest)
    vee = mom.v_notch_weir(head, 90.0)
    broad = mom.broad_crested_weir(head, width)
    m1, m2, m3 = st.columns(3)
    m1.metric("Sharp-crested rectangular", f"{rect['discharge']:.4g} m³/s")
    m2.metric("90° V-notch", f"{vee['discharge']:.4g} m³/s")
    m3.metric("Broad-crested", f"{broad['discharge']:.4g} m³/s")
    st.caption(
        f"Rehbock gives C_d = {rect['cd']:.3f} at H/P = {head / crest:.2f}; the ideal "
        f"(uncorrected) integral would have predicted {rect['ideal_discharge']:.4g} m³/s, so the "
        f"coefficient is removing {100 * (1 - rect['discharge'] / rect['ideal_discharge']):.0f}% "
        f"of it. The broad-crested weir puts critical depth {broad['critical_depth']:.3f} m on "
        "its crest. A 1% error in the head reading becomes 1.5% in the rectangular discharge "
        "and 2.5% in the V-notch — the price of that steeper exponent."
    )
    if head / crest > 5.0:
        st.warning(
            f"H/P = {head / crest:.1f} is past the range Rehbock's fit was measured over "
            "(about 5). The weir is drowning in its own approach flow; treat the coefficient "
            "as an extrapolation, not a calibration."
        )

    c4, c5, c6 = st.columns(3)
    pool = persistent_input(
        c4.number_input, "Upstream pool depth y₁ [m]", min_value=0.2, max_value=10.0,
        value=2.00, step=0.1, key="mom_gate_y1",
    )
    opening = persistent_input(
        c5.number_input, "Gate opening a [m]", min_value=0.02, max_value=5.0,
        value=0.30, step=0.02, key="mom_gate_a",
    )
    cc = persistent_input(
        c6.number_input, "Contraction coefficient C_c", min_value=0.5, max_value=1.0,
        value=0.61, step=0.01, key="mom_gate_cc",
    )
    if cc * opening >= pool:
        st.warning("The gate is open wider than the pool is deep; there is nothing to discharge under.")
        return
    fluid = get_fluid_state()
    gate = mom.sluice_gate(pool, opening, cc, rho=fluid["rho"])
    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Discharge per width", f"{gate['unit_discharge']:.4g} m²/s")
    g2.metric("Force on the gate", f"{gate['gate_force_per_width'] / 1000:.4g} kN/m")
    g3.metric("Hydrostatic thrust", f"{gate['hydrostatic_force_per_width'] / 1000:.4g} kN/m")
    g4.metric("Force / hydrostatic", f"{100 * gate['force_ratio']:.1f} %")
    downstream = mom.hydraulic_jump(gate["y2"], gate["unit_discharge"])
    st.caption(
        f"The jet contracts to y₂ = {gate['y2']:.3f} m and accelerates from "
        f"{gate['u1']:.2f} to {gate['u2']:.2f} m/s, taking the flow from Fr = "
        f"{gate['froude_1']:.2f} to Fr = {gate['froude_2']:.2f}. Because it leaves "
        "supercritical, it must return to the downstream depth through a jump: §10.5's "
        f"balance puts the sequent depth at {downstream['y2']:.3f} m and the dissipation at "
        f"{downstream['energy_loss']:.3f} m. That is the apron the gate needs."
    )


# ==========================================================================
# 10.7 Propulsion
# ==========================================================================
def _section_propulsion() -> None:
    st.markdown("### 10.7 Rockets and rotors · momentum with nothing to push against")
    render_svg(diagram_rocket_control_volume())
    prose(
        r"""
        A rocket works in vacuum, which disposes of the folk explanation that exhaust pushes
        on the air. What pushes the vehicle is the same thing that pushed the vane in §10.2:
        the reaction to a momentum flux across the control surface, plus the pressure term
        the exit plane fails to cancel.
        $$F=\dot m\,v_e+(p_e-p_a)A_e,\qquad
        \Delta v=c\,\ln\!\frac{m_0}{m_f}-g\,t_b-\Delta v_{\text{drag}}$$
        """
    )
    render_derivation(
        "the thrust equation and the rocket equation, from one control volume",
        [
            (
                "Ride with the vehicle so the flow is steady",
                r"""
                In the ground frame nothing about a rocket is steady: the vehicle
                accelerates and its mass falls. Attach the control volume to the vehicle
                instead. While the acceleration is modest this is very nearly inertial,
                and in that frame the chamber, throat and nozzle are in steady operation
                — the same trick that made the moving vane tractable in §10.2.
                """,
            ),
            (
                "Only two things cross the boundary, and only one is momentum",
                r"""
                Propellant leaves through the exit plane at relative speed $v_e$,
                carrying momentum flux $\dot mv_e$ backwards. Everywhere else the control
                surface is either solid or exposed to a uniform atmosphere at $p_a$,
                which contributes nothing to a closed surface. The exception is the exit
                plane itself, where the gas is at $p_e$ rather than $p_a$:
                $$F=\dot m\,v_e+(p_e-p_a)A_e$$
                The pressure term is not a correction bolted on afterwards; it is the
                only part of the atmospheric integral that fails to cancel. It is also
                why the *same* engine produces more thrust in vacuum than at sea level,
                by exactly $p_{\text{atm}}A_e$.
                """,
            ),
            (
                r"Lump both terms into an effective exhaust velocity",
                r"""
                Define $c\equiv F/\dot m$, so that $F=\dot mc$ whatever the pressure
                mismatch is doing. Specific impulse is the same number in different
                units, $I_{sp}=c/g_0$, which is why a "seconds" figure and a velocity
                figure describe the same engine. It is $c$, not $v_e$, that belongs in
                everything that follows.
                """,
            ),
            (
                "Newton on a body whose mass is falling",
                r"""
                For the vehicle of instantaneous mass $m$, with thrust forward, weight
                and drag against:
                $$m\frac{dv}{dt}=F-mg-D=-c\frac{dm}{dt}-mg-D$$
                using $\dot m=-dm/dt$. **Do not** write $F=d(mv)/dt$ for the vehicle
                alone: that is the classic trap, because the vehicle is not a closed
                system and the departing mass carries momentum of its own. The control
                volume above is what keeps the accounting straight.
                """,
            ),
            (
                "Divide by m and integrate: a logarithm is the only possible answer",
                r"""
                In free space ($g=D=0$), dividing by $m$ leaves
                $$dv=-c\,\frac{dm}{m}
                \;\Longrightarrow\;
                \int_0^{\Delta v}dv=-c\int_{m_0}^{m_f}\frac{dm}{m}
                \;\Longrightarrow\;
                \Delta v=c\ln\frac{m_0}{m_f}$$
                The mass could only ever appear as $dm/m$, so the result *had* to be
                logarithmic. Inverting it, $m_0/m_f=\exp(\Delta v/c)$: every extra unit
                of $\Delta v$ multiplies the vehicle rather than adding to it, which is
                the entire reason launchers are staged.
                """,
            ),
            (
                "What a real launch gives back",
                r"""
                Keeping gravity for a vertical burn of duration $t_b$ subtracts
                $\int g\,dt=g\,t_b$ — the **gravity loss** — and drag subtracts its own
                integral. Neither depends on how good the engine is, only on how long it
                takes: a high-thrust first stage wastes less to gravity than a gentle one
                with the identical $I_{sp}$. That is why a launcher leaves the pad hard
                and pitches downrange as early as the structure allows.
                """,
            ),
        ],
    )

    st.markdown("#### 10.7.1 Lab · thrust, altitude and the mass ratio")
    c1, c2, c3 = st.columns(3)
    mdot = persistent_input(
        c1.number_input, "Propellant mass flow [kg/s]", min_value=0.1, max_value=5000.0,
        value=2200.0, step=50.0, key="mom_rkt_mdot",
    )
    ve = persistent_input(
        c2.number_input, "Exhaust velocity vₑ [m/s]", min_value=100.0, max_value=6000.0,
        value=2800.0, step=50.0, key="mom_rkt_ve",
    )
    ae = persistent_input(
        c3.number_input, "Exit area Aₑ [m²]", min_value=0.0, max_value=20.0,
        value=4.00, step=0.25, key="mom_rkt_ae",
    )
    c4, c5, c6 = st.columns(3)
    pe = persistent_input(
        c4.number_input, "Exit pressure pₑ [kPa]", min_value=0.0, max_value=500.0,
        value=60.0, step=5.0, key="mom_rkt_pe",
    ) * 1000.0
    pa = persistent_input(
        c5.number_input, "Ambient pressure pₐ [kPa]", min_value=0.0, max_value=200.0,
        value=101.325, step=5.0, key="mom_rkt_pa",
    ) * 1000.0
    burn = persistent_input(
        c6.number_input, "Burn time [s]", min_value=0.0, max_value=1000.0,
        value=200.0, step=10.0, key="mom_rkt_tb",
    )
    c7, c8 = st.columns(2)
    m0 = persistent_input(
        c7.number_input, "Initial mass m₀ [t]", min_value=0.1, max_value=5000.0,
        value=500.0, step=10.0, key="mom_rkt_m0",
    ) * 1000.0
    mf = persistent_input(
        c8.number_input, "Burnout mass m_f [t]", min_value=0.05, max_value=5000.0,
        value=60.0, step=5.0, key="mom_rkt_mf",
    ) * 1000.0
    thrust = mom.rocket_thrust(mdot, ve, pe, pa, ae)
    if mf >= m0:
        st.warning("The burnout mass must be below the initial mass; there is no propellant here.")
        return
    flight = mom.tsiolkovsky(thrust["effective_exhaust_velocity"], m0, mf, burn_time=burn)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Thrust", f"{thrust['thrust'] / 1000:.4g} kN")
    m2.metric("Specific impulse", f"{thrust['specific_impulse']:.1f} s")
    m3.metric("Ideal Δv", f"{flight['delta_v_ideal']:.0f} m/s")
    m4.metric("Δv after gravity loss", f"{flight['delta_v_net']:.0f} m/s")
    vacuum = mom.rocket_thrust(mdot, ve, pe, 0.0, ae)
    st.caption(
        f"Momentum thrust {thrust['momentum_thrust'] / 1000:.4g} kN plus pressure thrust "
        f"{thrust['pressure_thrust'] / 1000:.4g} kN, giving an effective exhaust velocity of "
        f"{thrust['effective_exhaust_velocity']:.0f} m/s. The identical engine in vacuum would "
        f"give {vacuum['thrust'] / 1000:.4g} kN ({vacuum['specific_impulse']:.1f} s) — "
        f"{100 * (vacuum['thrust'] / thrust['thrust'] - 1):.1f}% more, purely from the missing "
        f"atmosphere on the exit plane. Mass ratio {flight['mass_ratio']:.2f} "
        f"({100 * flight['propellant_fraction']:.1f}% propellant), and the burn hands "
        f"{flight['gravity_loss']:.0f} m/s back to gravity."
    )
    implied_burn = (m0 - mf) / mdot
    if abs(implied_burn - burn) > 0.05 * max(implied_burn, 1.0):
        st.caption(
            f"Note that {mdot:g} kg/s would consume this propellant in {implied_burn:.0f} s, not "
            f"the {burn:g} s entered. The two are independent inputs here — the rocket equation "
            "never sees the burn time except through the gravity loss — but a real vehicle has "
            "only one answer."
        )
    if thrust["thrust"] < m0 * mom.G0:
        st.warning(
            f"Thrust ({thrust['thrust'] / 1000:.0f} kN) is below the initial weight "
            f"({m0 * mom.G0 / 1000:.0f} kN), so this vehicle cannot lift off. The Δv above is "
            "still valid for a stage ignited in flight."
        )

    dv = np.linspace(0.0, max(12000.0, 1.2 * flight["delta_v_ideal"]), 200)
    fig = go.Figure()
    for c_value, label in (
        (thrust["effective_exhaust_velocity"], "this engine"),
        (3400.0, "hydrogen/oxygen, c ≈ 3400 m/s"),
        (2200.0, "solid motor, c ≈ 2200 m/s"),
    ):
        fig.add_trace(
            go.Scatter(
                x=dv, y=[mom.rocket_mass_ratio_for(v, c_value) for v in dv],
                name=f"{label} (c = {c_value:.0f} m/s)",
            )
        )
    fig.add_trace(
        go.Scatter(
            x=[flight["delta_v_ideal"]], y=[flight["mass_ratio"]], mode="markers",
            marker=dict(size=12, symbol="x"), name="your vehicle",
        )
    )
    fig.update_layout(
        title="The tyranny of the rocket equation: mass ratio needed for a given Δv",
        xaxis_title="Δv [m/s]", yaxis=dict(type="log", title="m₀ / m_f [-]"), height=430,
    )
    apply_plotly_theme(fig)
    render_plot(fig, "momentum-rocket-equation")
    render_what_to_notice(
        "On a logarithmic axis the curves are straight lines, which is the exponential said "
        "plainly: equal increments of Δv cost equal *multiples* of mass. Raising c rotates the "
        "line flatter, which is why a better engine is worth far more than a lighter tank."
    )

    st.markdown("#### 10.7.2 The actuator disc · propellers, rotors and the Betz limit")
    prose(
        r"""
        The same balance, applied to a stream tube through a disc that adds or removes axial
        momentum, bounds every wind turbine ever built — without a single word about blades.
        $$C_P=\frac{P}{\tfrac12\rho AU^{3}}=4a(1-a)^{2},
        \qquad C_{P,\max}=\frac{16}{27}\ \text{at}\ a=\tfrac13$$
        """
    )
    render_derivation(
        "the Betz limit: why no rotor can take more than 16/27 of the wind",
        [
            (
                "The stream tube, and where the slowing happens",
                r"""
                Draw a control volume along the stream tube that passes through the disc.
                Far upstream the speed is $U$; at the disc it is $U(1-a)$, defining the
                axial induction factor $a$; far downstream in the wake it is some
                $U(1-b)$. Continuity forces the tube to expand as it slows, which is why
                the wake is wider than the rotor.
                """,
            ),
            (
                "Momentum on the tube gives the thrust",
                r"""
                Atmospheric pressure acts all round the tube and cancels, so the only
                axial force is the disc's:
                $$T=\dot m\left(U-U(1-b)\right)=\rho A U(1-a)\,Ub$$
                """,
            ),
            (
                "Bernoulli, applied twice and never across the disc",
                r"""
                The disc extracts energy, so Bernoulli may not be carried through it. But
                it is perfectly valid *upstream* of the disc and *downstream* of it
                separately. Doing both and subtracting gives the pressure jump across the
                disc, hence
                $$T=\Delta p\,A=\tfrac12\rho A\left(U^{2}-U^{2}(1-b)^{2}\right)$$
                Equating the two expressions for $T$ yields $b=2a$: **the wake loses
                twice what the disc has lost**, or equivalently half of the total
                slowdown has already happened before the air reaches the rotor.
                """,
            ),
            (
                "Power is thrust times the speed at the disc",
                r"""
                $$T=2\rho AU^{2}a(1-a),\qquad
                P=TU(1-a)=2\rho AU^{3}a(1-a)^{2}$$
                $$C_P=\frac{P}{\tfrac12\rho AU^{3}}=4a(1-a)^{2}$$
                """,
            ),
            (
                "Maximise, and notice what the limit is really saying",
                r"""
                $$\frac{dC_P}{da}=4\left(1-4a+3a^{2}\right)=4(1-a)(1-3a)=0
                \;\Longrightarrow\;a=\tfrac13$$
                $$C_{P,\max}=4\cdot\tfrac13\cdot\left(\tfrac23\right)^{2}=\frac{16}{27}\approx0.593$$
                The physical content is a trade-off, not a mystery: extracting energy
                requires slowing the air, but air that has been slowed too much no longer
                arrives. At $a=\tfrac12$ the wake would be at rest and no new air could
                get through, so $C_P$ returns to zero. Real turbines reach about
                $0.45$–$0.50$ because blades also shed tip vortices, spin the wake, and
                have finite drag — all effects this control volume never claimed to
                include.
                """,
            ),
        ],
        closing=(
            "Run the disc the other way — adding momentum instead of removing it — and the "
            "same algebra describes a propeller or a helicopter rotor, with an ideal propulsive "
            "efficiency of $1/(1+a)$. Both are the momentum theorem applied to a stream tube; "
            "only the sign of the work changes."
        ),
    )
    c1, c2, c3 = st.columns(3)
    diameter = persistent_input(
        c1.number_input, "Rotor diameter [m]", min_value=0.5, max_value=250.0,
        value=90.0, step=5.0, key="mom_disk_d",
    )
    wind = persistent_input(
        c2.number_input, "Wind speed U [m/s]", min_value=1.0, max_value=40.0,
        value=10.0, step=0.5, key="mom_disk_u",
    )
    induction = persistent_input(
        c3.slider, "Induction factor a", min_value=0.0, max_value=0.5,
        value=0.33, step=0.01, key="mom_disk_a",
    )
    disk_area = math.pi * diameter**2 / 4.0
    air = 1.225
    disk = mom.actuator_disk(air, disk_area, wind, induction)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Power extracted", f"{disk['power'] / 1e6:.3g} MW")
    m2.metric("Power coefficient", f"{disk['power_coefficient']:.3f}")
    m3.metric("Thrust on the tower", f"{disk['thrust'] / 1000:.4g} kN")
    m4.metric("Wake speed", f"{disk['u_wake']:.2f} m/s")
    st.caption(
        f"Swept area {disk_area:.0f} m² in air at {air} kg/m³ (this section uses standard air, "
        "not the shared fluid, because a wind rotor is not the liquid lab). The stream carries "
        f"{disk['available_power'] / 1e6:.3g} MW through that area; the Betz ceiling would allow "
        f"{disk['betz_limit'] * disk['available_power'] / 1e6:.3g} MW, reached at a = 1/3. Air "
        f"reaches the disc at {disk['u_disk']:.2f} m/s, exactly halfway between the free stream "
        "and the wake."
    )
    a_values = np.linspace(0.0, 0.5, 200)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=a_values,
            y=[mom.actuator_disk(air, disk_area, wind, a)["power_coefficient"] for a in a_values],
            name="C_P = 4a(1−a)²",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=a_values,
            y=[mom.actuator_disk(air, disk_area, wind, a)["thrust_coefficient"] for a in a_values],
            name="C_T = 4a(1−a)",
        )
    )
    fig.add_hline(y=16 / 27, line_dash="dot", annotation_text="Betz, 16/27")
    fig.add_trace(
        go.Scatter(
            x=[induction], y=[disk["power_coefficient"]], mode="markers",
            marker=dict(size=12, symbol="x"), name="your setting",
        )
    )
    fig.update_layout(
        title="Power and thrust coefficients of an ideal disc",
        xaxis_title="Axial induction factor a", yaxis_title="Coefficient [-]", height=420,
    )
    apply_plotly_theme(fig)
    render_plot(fig, "momentum-actuator-disk")
    render_what_to_notice(
        "C_P peaks at a = 1/3 while C_T keeps rising to a = 1/2. A rotor pushed past its "
        "best power point therefore gains structural load while losing output — which is why "
        "turbines pitch their blades to shed thrust in high winds rather than chasing power."
    )


# ==========================================================================
# 10.8 Limits
# ==========================================================================
def _section_when_it_fails() -> None:
    st.markdown("### 10.8 What the integral balance does not know")
    render_checklist(
        "Assumptions behind every calculator on this page",
        [
            (
                "Steady flow in the chosen frame",
                True,
                "The accumulation term was dropped. A water-hammer transient or a starting jet "
                "keeps it, and neglecting it there can be badly wrong.",
            ),
            (
                "One-dimensional faces with β = 1",
                True,
                "Fine for turbulent pipe flow (β ≈ 1.02); in laminar flow β = 4/3 and the force "
                "is a third larger than these numbers say.",
            ),
            (
                "Wall shear over the control volume is negligible",
                True,
                "True for a short fitting, a jump or a gate. Over a long pipe it is the whole "
                "answer, which is why chapter 2 is a friction chapter and this one is not.",
            ),
            (
                "Constant density",
                False,
                "Not assumed by the theorem itself, but assumed by every liquid calculator here. "
                "Chapter 12 applies the same balance to a compressible gas and to a shock.",
            ),
            (
                "It gives a force, never a loss",
                False,
                "Momentum alone cannot tell you the dissipation; it took the energy balance as "
                "well to get h_L and ΔE. Nor does it locate anything: it gives the resultant, "
                "not the pressure distribution or the point of application.",
            ),
        ],
    )
    render_symbols(
        [
            (r"q=Q/b", "discharge per unit width in an open channel (m²/s)."),
            (r"\mathrm{Fr}=u/\sqrt{gy}", "Froude number; above one, nothing propagates upstream."),
            (r"M", "momentum function per unit width (m²); conserved across a jump."),
            (r"C_c", "contraction coefficient of a gate jet; about 0.61 for a sharp edge."),
            (r"c=F/\dot m", "effective exhaust velocity, including the pressure term (m/s)."),
            (r"a", "axial induction factor of an actuator disc; the fractional slowdown at the disc."),
        ]
    )
    render_self_check(
        "mom_check_theorem",
        "Which of these can the integral momentum balance deliver on its own?",
        [
            "The head loss through a fitting",
            "The resultant force on a device whose interior is unknown",
            "The pressure distribution over the device's wetted surface",
        ],
        "The resultant force on a device whose interior is unknown",
        "The loss needs the energy balance as well (§10.4, §10.5), and the distribution needs a "
        "local solution — the differential equations of chapters 5–8, or the CFD of chapter 13. "
        "The resultant is exactly what the boundary integral gives you, and all it gives you.",
    )
    st.markdown(
        "**Connect to practice.** A thrust block on a buried main, the anchor loads on a "
        "relief-valve discharge elbow, the apron below a sluice gate, the stilling basin under "
        "a spillway, the reaction on a fire nozzle and the mounting of a jet mixer are all this "
        "one balance with a different control volume drawn around them. Chapter 11 keeps the "
        "balance and changes the quantity — angular momentum instead of linear — which is how a "
        "rotating blade converts the same idea into shaft work."
    )
