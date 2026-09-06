import plotly.graph_objects as go
import streamlit as st
from src.ui.state import persistent_input
from src.physics.gas_dynamics import gas_machine
from src.physics.impeller import blade_camberline, head_flow_curve, velocity_triangles
from src.plotting import plot_impeller_head_curve
from src.svg_diagrams import diagram_asu_flowsheet, render_svg
from src.svg_impeller import (
    diagram_blade_angles,
    diagram_impeller_meridional,
    diagram_outlet_triangle_true_shape,
)
from src.ui.pedagogy import (
    render_callout,
    render_derivation,
    render_plot,
    render_prose_and_latex as prose,
    render_self_check,
    render_what_to_notice,
)
from src.theme import apply_plotly_theme
from src.units import get_fluid_state


def render_tab_turbomachinery():
    st.markdown('### 9.1 Euler’s turbomachinery equation · angular momentum')
    prose(r'''Euler's local inviscid momentum equation and Euler's rotor-work equation express related conservation physics, but they are different formulas. A rotor exchanges shaft work by changing the fluid's **angular momentum**.

**1 · Choose a stationary control volume around the rotor.** Use absolute velocity C, blade velocity U and velocity relative to the blade W. Resolve C into meridional and tangential components. Positive tangential direction follows positive shaft rotation.
$$\mathbf C=\mathbf U+\mathbf W,\qquad U=\omega r,\qquad \omega=2\pi N/60$$
**2 · Take moments about the shaft.** A mass element carries specific angular momentum rCθ. For steady flow, the net external torque on the fluid equals outgoing minus incoming angular-momentum flux. Axisymmetric pressure forces have no moment about the axis; this idealized balance neglects other external torques.
$$\tau_{\mathrm{fluid}}=\dot m(r_2C_{\theta2}-r_1C_{\theta1})$$
**3 · Multiply torque by angular speed.** Power delivered by the rotor is angular speed times torque. Divide by mass flow to get specific shaft work into the fluid.
$$\dot W_{\mathrm{in}}=\omega\tau_{\mathrm{fluid}},\quad w_{\mathrm{in}}=U_2C_{\theta2}-U_1C_{\theta1}$$
**4 · Connect to the first law.** For an adiabatic rotor with negligible elevation change, shaft work increases stagnation enthalpy. Static enthalpy also depends on how much kinetic energy changes.
$$h_{02}-h_{01}=w_{\mathrm{in}},\quad h_0=h+C^2/2$$
$$h_2-h_1=U_2C_{\theta2}-U_1C_{\theta1}-\frac{C_2^2-C_1^2}{2}$$
**5 · Recognize the two operating directions.** Positive work means compressor/pump action; negative work means turbine/expander action. The shaft experiences the opposite torque. An adiabatic stationary stator has no shaft work: it can exchange static enthalpy and kinetic energy while preserving h₀.
$$\Delta T_0=\frac{w_{\mathrm{in}}}{c_p}\quad\text{(constant-}c_p\text{ ideal gas)}$$
Another useful check follows from W² = C² + U² − 2UCθ: Euler's equation implies constant rothalpy through an ideal adiabatic rotor.
$$h+\frac{W^2}{2}-\frac{U^2}{2}=\text{constant}$$''')

    render_derivation(
        r"Euler's rotor equation from moment of momentum, and why the blade shape never appears",
        [
            (
                "Linear momentum is the wrong balance to start from",
                r"""
                A shaft does not push the fluid; it **twists** it. Whatever crosses the
                coupling is a torque, so the conservation statement that can see shaft work
                is the moment of momentum, not the force balance used everywhere else in this
                course.
                """,
            ),
            (
                "Build the moment-of-momentum theorem from Newton",
                r"""
                For a single particle, cross $\mathbf r$ into $\mathbf F=d(m\mathbf v)/dt$:
                $$\mathbf r\times\mathbf F=\frac{d}{dt}(\mathbf r\times m\mathbf v)$$
                because $\dot{\mathbf r}\times m\mathbf v=\mathbf v\times m\mathbf v=\mathbf 0$.
                Summing over the fluid inside a fixed control volume and applying the transport
                theorem for **steady** flow — storage inside is unchanging, so only the flux
                through the boundary survives:
                $$\sum(\text{torque about the axis})
                =\oint_{S}(r C_\theta)\,\rho(\mathbf C\cdot\mathbf n)\,dA$$
                The quantity being transported is $rC_\theta$, angular momentum per kilogram.
                """,
            ),
            (
                "Only the tangential velocity has a moment arm",
                r"""
                A geometric point worth pausing on. Decompose $\mathbf C$ at the rotor exit
                into axial, radial and tangential parts. The axial component is **parallel**
                to the shaft, so its moment about the shaft is zero; the radial component's
                line of action **passes through** the axis, so its moment is zero too. Only
                $C_\theta$, acting at arm $r$, carries angular momentum. That is why the
                entire chapter is about swirl.
                """,
            ),
            (
                "Almost every external torque vanishes, which is what makes this useful",
                r"""
                On an axisymmetric casing, pressure acts along lines that intersect the axis:
                no axial moment. Gravity on a vertical machine likewise has none, and casing
                shear is a loss term, not a work term. So the **only** surviving torque is
                the one the blades exert. With one inlet and one outlet, using mass-averaged
                velocities:
                $$\tau_{\text{fluid}}=\dot m\left(r_2C_{\theta2}-r_1C_{\theta1}\right)$$
                """,
            ),
            (
                "Multiply by shaft speed to get power, then divide by mass flow",
                r"""
                Power is torque times angular speed, and the blade speed is $U=\omega r$:
                $$\dot W_{\text{in}}=\omega\tau_{\text{fluid}}
                =\dot m\left(\omega r_2 C_{\theta2}-\omega r_1 C_{\theta1}\right)
                \;\Longrightarrow\;
                \boxed{w_{\text{in}}=U_2C_{\theta2}-U_1C_{\theta1}}$$
                Look at what is **absent**: no blade count, no blade shape, no viscosity, no
                fluid property, and no statement of whether this is a pump, a fan, a
                compressor or a turbine. Euler's equation is a conservation statement, so it
                constrains every machine of this type; the geometry re-enters only when you
                ask what $C_{\theta2}$ actually is (§9.2).
                """,
            ),
            (
                "Attach it to the first law to get a thermodynamic result",
                r"""
                For an adiabatic rotor with negligible elevation change, the steady-flow
                energy equation of §1.2 says shaft work goes entirely into stagnation
                enthalpy:
                $$h_{02}-h_{01}=w_{\text{in}},\qquad h_0=h+\tfrac12C^{2}$$
                so the *static* enthalpy rise is whatever is left after the kinetic energy
                change is accounted for:
                $$h_2-h_1=U_2C_{\theta2}-U_1C_{\theta1}-\frac{C_2^{2}-C_1^{2}}{2}$$
                A rotor that dumps most of its work into $C_2$ has done little to the static
                state and has handed the diffuser a large job. That fraction is exactly the
                degree of reaction reported in the lab below.
                """,
            ),
            (
                "Sign convention, stated once",
                r"""
                $w_{\text{in}}>0$ means the rotor adds angular momentum: pump, fan or
                compressor. $w_{\text{in}}<0$ means the fluid loses swirl and drives the
                shaft: turbine or expander. The shaft always feels the equal and opposite
                torque. A stationary blade row has $U=0$, hence no work at all — it can only
                trade static enthalpy for kinetic energy at constant $h_0$, which is precisely
                what a nozzle or a diffuser does.
                """,
            ),
        ],
    )

    render_derivation(
        r"the velocity triangle identity, and the three separate ways a rotor makes head",
        [
            (
                r"$\mathbf C=\mathbf U+\mathbf W$ is a change of observer, nothing more",
                r"""
                Stand in the room and you see the absolute velocity $\mathbf C$. Ride the
                blade — a frame moving tangentially at $\mathbf U=\omega r$ — and you see the
                relative velocity $\mathbf W$. Galilean addition of velocities gives
                $\mathbf C=\mathbf U+\mathbf W$, and drawing that vector sum *is* the velocity
                triangle. The blade can only impose a direction on $\mathbf W$, because that
                is the velocity it actually sees.
                """,
            ),
            (
                "Apply the cosine rule to that triangle",
                r"""
                The angle between $\mathbf C$ and $\mathbf U$ is $\alpha$, so
                $C\cos\alpha=C_\theta$, and the side opposite is $W$:
                $$W^{2}=C^{2}+U^{2}-2UC\cos\alpha=C^{2}+U^{2}-2UC_\theta$$
                Rearranged, this is a rewriting of the Euler work per unit blade speed:
                $$UC_\theta=\tfrac12\left(C^{2}+U^{2}-W^{2}\right)$$
                """,
            ),
            (
                "Substitute into Euler and read the three mechanisms",
                r"""
                $$w_{\text{in}}=\underbrace{\frac{C_2^{2}-C_1^{2}}{2}}_{\text{(a) kinetic energy}}
                +\underbrace{\frac{U_2^{2}-U_1^{2}}{2}}_{\text{(b) centrifugal}}
                -\underbrace{\frac{W_2^{2}-W_1^{2}}{2}}_{\text{(c) relative diffusion}}$$
                **(a)** is energy handed to the absolute stream as *speed*; a volute or
                diffuser must convert it to pressure afterwards, at some loss.
                **(b)** is pressure produced simply by carrying fluid outward against the
                centrifugal field — it needs no diffusion at all, which is the fundamental
                reason a centrifugal stage makes several times the head of an axial stage at
                the same tip speed. **(c)** is diffusion inside the rotating passage, limited
                by the same separation physics as any diffuser.
                """,
            ),
            (
                "The same identity gives a conserved quantity in the rotating frame",
                r"""
                Put $h_{02}-h_{01}=U_2C_{\theta2}-U_1C_{\theta1}$ together with
                $h_0=h+\tfrac12C^{2}$ and the cosine rule above. Everything with subscript 2
                collects on one side and everything with subscript 1 on the other:
                $$h+\frac{W^{2}}{2}-\frac{U^{2}}{2}=\text{constant}$$
                This is **rothalpy** — the rotating-frame analogue of stagnation enthalpy.
                The $-U^{2}/2$ is the potential of the centrifugal field, exactly as $gz$ is
                the potential of gravity. Rothalpy is the check to run on any ideal adiabatic
                rotor calculation: if it drifts between inlet and outlet, the triangle is
                wrong.
                """,
            ),
        ],
    )
    st.caption('[MIT: Euler turbine equation and velocity components](https://web.mit.edu/course/16/16.unified/www/SPRING/thermodynamics/notes/node91.html). Velocities in this balance are mass-flow averages; blade losses and nonuniformity require additional modeling.')
    st.markdown('### 9.2 Where the angles are · impeller geometry and blade angles')
    prose(r'''Almost every mistake in a turbomachinery calculation is an angle measured from the wrong reference. Fix the conventions once and the arithmetic follows.

**The two planes.** A radial machine is cut two ways, and they are perpendicular. The **meridional** (r–z) section contains the shaft axis: it shows the ninety-degree turn from axial inlet to radial discharge, and it is where the passage widths $b_1$ and $b_2$ are measured. The **blade-to-blade** section is taken on the surface of revolution the flow actually follows — for a radial impeller that is the $r$–$\theta$ plane, perpendicular to the shaft. It shows the blade curvature, and it is the plane the velocity triangle lives in. (In an *axial* machine the same surface is a cylinder at fixed radius, which is why that description is the one usually quoted.) A drawing that mixes them will not close.

**The convention used here.** Blade and flow angles are measured **from the tangential direction**, so a radial-ended blade is $\beta=90^\circ$ and an industrial backswept impeller is $\beta_2\approx20$–$35^\circ$. Gas-turbine texts often measure from the meridional direction instead, where the same blade reads $90^\circ-\beta$. Both numbers are reported below so the lab can be checked against either book.

**What a blade angle actually asserts.** It is a statement about the slope of the camberline, and nothing more:
$$\tan\beta=\frac{dr}{r\,d\theta}$$
Integrating that relation *is* how the blade in the figure was drawn. A constant $\beta$ gives a logarithmic spiral, $\theta=\ln(r/r_1)/\tan\beta$; a shallow angle wraps much further around the shaft, which is why heavily backswept impellers look like spirals and radial-bladed ones like spokes.''')

    render_svg(diagram_impeller_meridional(r1=0.045, r2=0.150, b1=0.030, b2=0.012))

    st.markdown('#### Rotor and velocity-triangle lab')
    st.caption('The figures, the triangle and the numbers below all come from the same geometry code, so they cannot disagree.')

    g1, g2, g3, g4 = st.columns(4)
    imp_rpm = persistent_input(g1.number_input, 'Shaft speed [rpm]', min_value=100., max_value=60000., value=2900., step=100., key='imp_rpm')
    imp_q = persistent_input(g1.number_input, 'Volumetric flow Q [m³/s]', min_value=.001, max_value=2., value=.030, step=.005, format='%.3f', key='imp_q')
    imp_r1 = persistent_input(g2.number_input, 'Inlet (eye) radius r₁ [m]', min_value=.005, max_value=.4, value=.045, step=.005, key='imp_r1')
    imp_r2 = persistent_input(g2.number_input, 'Tip radius r₂ [m]', min_value=.01, max_value=1., value=.150, step=.005, key='imp_r2')
    imp_b1 = persistent_input(g3.number_input, 'Inlet width b₁ [m]', min_value=.002, max_value=.3, value=.030, step=.002, key='imp_b1')
    imp_b2 = persistent_input(g3.number_input, 'Outlet width b₂ [m]', min_value=.002, max_value=.3, value=.012, step=.002, key='imp_b2')
    imp_beta1 = persistent_input(g4.slider, 'Inlet blade angle β₁ [° from tangential]', 5., 89., 30., key='imp_beta1')
    imp_beta2 = persistent_input(g4.slider, 'Outlet blade angle β₂ [° from tangential]', 5., 89., 25., key='imp_beta2')
    imp_blades = persistent_input(st.slider, 'Number of blades Z', 2, 20, 7, key='imp_blades')

    if imp_r2 <= imp_r1:
        st.error('A centrifugal impeller needs r₂ > r₁: the work comes from the change in radius.')
    else:
        tri = velocity_triangles(
            rpm=imp_rpm, flow_rate=imp_q, r1=imp_r1, r2=imp_r2,
            beta1_deg=imp_beta1, beta2_deg=imp_beta2, b1=imp_b1, b2=imp_b2,
            n_blades=imp_blades, rho=float(get_fluid_state()['rho']),
        )
        render_svg(diagram_blade_angles(
            r1=imp_r1, r2=imp_r2, beta1_deg=imp_beta1, beta2_deg=imp_beta2,
            b1=imp_b1, b2=imp_b2, n_blades=imp_blades,
        ))
        render_svg(diagram_outlet_triangle_true_shape(
            beta2_deg=imp_beta2, u2=tri['u2'], cm2=tri['cm2'], sigma=tri['slip_factor'],
        ))

        m1, m2, m3, m4 = st.columns(4)
        m1.metric('Blade speed U₂', f"{tri['u2']:.2f} m/s")
        m2.metric('Swirl Cθ₂', f"{tri['c_theta2']:.2f} m/s")
        m3.metric('Euler head', f"{tri['head_euler_m']:.2f} m")
        m4.metric('Slip factor σ', f"{tri['slip_factor']:.3f}")
        n1, n2, n3, n4 = st.columns(4)
        n1.metric('Meridional Cₘ₂', f"{tri['cm2']:.2f} m/s")
        n2.metric('Absolute C₂', f"{tri['c2']:.2f} m/s")
        n3.metric('Flow angle α₂', f"{tri['alpha2_deg']:.1f}° from tangential")
        n4.metric('Degree of reaction R', f"{tri['reaction']:.3f}")

        st.caption(
            f"Work into the fluid {tri['work'] / 1000:.3f} kJ/kg · hydraulic power "
            f"{tri['power_w'] / 1000:.2f} kW · blade wrap "
            f"{blade_camberline(imp_r1, imp_r2, imp_beta1, imp_beta2)['wrap_angle_deg']:.0f}°. "
            f"In the from-meridional convention β₂ = {tri['beta2_blade_from_meridional_deg']:.0f}° "
            f"and α₂ = {tri['alpha2_from_meridional_deg']:.1f}°."
        )

        if abs(tri['incidence_deg']) < 1.0:
            st.success(
                f"Shockless entry: the inlet blade angle matches the inlet flow angle "
                f"({tri['beta1_flow_deg']:.1f}°) to within {abs(tri['incidence_deg']):.2f}°. "
                "At this one flow rate the fluid slides onto the blade without turning a corner."
            )
        else:
            st.warning(
                f"Incidence {tri['incidence_deg']:+.1f}°: the flow arrives at "
                f"{tri['beta1_flow_deg']:.1f}° while the blade is set at {imp_beta1:.0f}°. "
                "Set β₁ to the flow angle for shockless entry — this mismatch is the leading "
                "reason a pump loses efficiency away from its design flow, and it is why a "
                "fixed-geometry machine has a best efficiency point at all."
            )

        render_what_to_notice(
            "Raise β₂ towards 90° and Cθ₂ climbs — though slip keeps it well short of U₂, because σ falls as the blade goes radial. A radial-bladed impeller extracts "
            "the most work per unit speed. Then look at C₂ — it climbs too, and that kinetic "
            "energy has to be diffused in the volute at some loss. Backsweep trades head for a "
            "stable curve and an easier diffuser. That trade is the whole design argument."
        )

        fig_curve = plot_impeller_head_curve(
            head_flow_curve(imp_rpm, imp_r1, imp_r2, imp_beta1, imp_beta2,
                            imp_b1, imp_b2, imp_blades, q_max=max(imp_q * 2.0, 0.01)),
            operating_q=imp_q, operating_h=tri['head_euler_m'],
        )
        render_plot(fig_curve, 'impeller-head-curve')
        st.caption(
            'Ideal Euler head only: H = σU₂²/g − U₂Q/(g·2πr₂b₂·tanβ₂). The slope comes entirely '
            'from β₂. A measured pump curve bends below this line because friction grows like Q² '
            'and incidence loss grows on both sides of the design point; the intercept is the '
            'shutoff head. Nothing here models the volute, leakage or disc friction.'
        )

        render_derivation(
            r"from a blade angle to the head curve $H(Q)$, one geometric fact at a time",
            [
                (
                    "What a blade angle asserts, and what it draws",
                    r"""
                    On the blade-to-blade surface, a step along the camberline has a radial
                    part $dr$ and a tangential part $r\,d\theta$ — the arc length, which is why
                    the radius multiplies the angle. Measuring $\beta$ from the tangential
                    direction, "opposite over adjacent" gives
                    $$\tan\beta=\frac{dr}{r\,d\theta}$$
                    That is the *entire* content of a blade angle. Integrating it with $\beta$
                    held constant,
                    $$\theta=\frac{1}{\tan\beta}\ln\frac{r}{r_1}$$
                    a logarithmic spiral — and it is literally how the blade in the figure was
                    drawn. A shallow $\beta$ makes $1/\tan\beta$ large, so the blade wraps much
                    further around the shaft: that is why heavily backswept impellers look like
                    spirals and radial-bladed ones like spokes.
                    """,
                ),
                (
                    "Start the head from Euler, with the usual inlet assumption",
                    r"""
                    Head is work per unit weight, $H=w_{\text{in}}/g$. Most pumps are designed
                    for swirl-free entry ($C_{\theta1}=0$, the flow arriving straight down the
                    eye), so Euler's equation collapses to one term:
                    $$H=\frac{U_2C_{\theta2}}{g},\qquad U_2=\omega r_2$$
                    Everything that follows is the work of finding $C_{\theta2}$.
                    """,
                ),
                (
                    "Continuity fixes the meridional component — and only that component",
                    r"""
                    The fluid leaves through the cylindrical surface at the tip, area
                    $A_2=2\pi r_2b_2$ (blade thickness blockage ignored here). Only the
                    velocity component **normal** to that surface transports volume through
                    it, and at the tip of a radial machine that is the radial (meridional)
                    component:
                    $$C_{m2}=\frac{Q}{2\pi r_2 b_2}$$
                    The swirl $C_{\theta2}$ slides *along* the surface and carries no flow
                    through it — which is exactly why swirl can be large without any of it
                    showing up in the flow rate.
                    """,
                ),
                (
                    "The blade fixes the direction of the relative velocity",
                    r"""
                    A blade can only steer the fluid it sees, so in the ideal case the relative
                    velocity leaves *parallel to the blade*. From the outlet triangle, with
                    $\beta_2$ measured from tangential,
                    $$\tan\beta_2=\frac{C_{m2}}{W_{\theta2}}
                    \;\Longrightarrow\; W_{\theta2}=\frac{C_{m2}}{\tan\beta_2}$$
                    and since $C_\theta=U-W_\theta$ along the tangential direction,
                    $$C_{\theta2}=U_2-\frac{C_{m2}}{\tan\beta_2}$$
                    Notice the flow rate has now entered the swirl through $C_{m2}$. That
                    coupling is the origin of the whole head curve.
                    """,
                ),
                (
                    "Finite blades do not perfectly guide the flow: slip",
                    r"""
                    Perfect guidance would need infinitely many blades. In a real passage the
                    fluid tends to keep its **absolute** orientation while the passage rotates
                    around it, which appears in the rotating frame as an eddy turning opposite
                    to the shaft. That relative eddy subtracts tangential momentum at the tip
                    — with no viscosity involved; it survives in potential flow. It is folded
                    into one measured factor $\sigma<1$ (the lab uses Wiesner's fit to
                    Busemann's solution):
                    $$C_{\theta2}=\sigma U_2-\frac{C_{m2}}{\tan\beta_2}$$
                    Fewer blades means a wider passage, a stronger relative eddy and a smaller
                    $\sigma$. This is the one genuinely empirical step in the chain.
                    """,
                ),
                (
                    "Assemble, and the curve is a straight line",
                    r"""
                    $$H=\frac{U_2}{g}\left(\sigma U_2-\frac{Q}{2\pi r_2b_2\tan\beta_2}\right)
                    =\underbrace{\frac{\sigma U_2^{2}}{g}}_{\text{shutoff head}}
                    -\underbrace{\frac{U_2}{2\pi r_2b_2 g\tan\beta_2}}_{\text{slope}}\;Q$$
                    The intercept at $Q=0$ is the shutoff head, and it depends only on tip
                    speed — which is why "head scales with $U_2^{2}$" is the first thing said
                    about any centrifugal machine, and why doubling the speed quadruples the
                    head (the affinity law).
                    """,
                ),
                (
                    "The sign of the slope is the whole stability argument",
                    r"""
                    Backswept ($\beta_2<90^\circ$): $\tan\beta_2>0$, the slope is **negative**,
                    and the curve falls with flow. If the operating point is disturbed toward
                    higher flow, the pump offers less head than the system needs and the flow
                    falls back — a restoring slope. Radial-ended ($\beta_2=90^\circ$):
                    $\tan\beta_2\to\infty$, the slope vanishes and the curve is flat, so
                    nothing restores the operating point. Forward-curved: the slope reverses
                    and the curve **rises**, which is the classical route to surge described in
                    §9.5.4. Backsweep costs head — visible as the drop in $C_{\theta2}$ in the
                    lab above — and buys stability plus an easier diffuser.
                    """,
                ),
                (
                    "What this straight line deliberately omits",
                    r"""
                    A measured pump curve bends below it. Friction inside the passages grows
                    roughly as $Q^{2}$; incidence loss grows on **both** sides of the design
                    flow, because §9.2's shockless-entry condition holds at only one $Q$; and
                    nothing here represents the volute, leakage, disc friction or blade
                    blockage. The line is the ideal envelope those losses subtract from.
                    """,
                ),
            ],
        )

    render_self_check(
        'turbo_self_check_angle',
        'An impeller has β₂ = 25° in this app\'s convention. A textbook that measures from the meridional direction would call the same blade…',
        ['65°', '25°', '115°'],
        '65°',
        'The two conventions are complements: 90° − 25° = 65°. Always check which reference a '
        'correlation assumes before substituting an angle into it — this single ambiguity causes '
        'more wrong answers in turbomachinery than any other.',
    )

    st.markdown('### 9.3 Pressure ratio, efficiency and heating/cooling')
    prose(r'''The Euler work equation alone does not determine the pressure ratio. Add an equation of state and a thermodynamic path. Here all inlet/outlet temperatures and pressures are **stagnation quantities**, with constant cp and γ.

**1 · Derive the reversible reference.** Gibbs' relation gives Tds = dh − v dp. For an ideal gas dh = cp dT and v = RT/p; set ds = 0 and integrate. Here $v$ is **specific volume** $1/\rho$ (Tab 1), not a velocity component.
$$0=c_p\frac{dT}{T}-R\frac{dp}{p}\quad\Rightarrow\quad\ln\frac{T_{02s}}{T_{01}}=\frac{R}{c_p}\ln\frac{p_{02}}{p_{01}}$$
$$T_{02s}=T_{01}\left(\frac{p_{02}}{p_{01}}\right)^{(\gamma-1)/\gamma}$$
**2 · Compression.** A real adiabatic compressor needs more work than the reversible reference to reach the same outlet pressure. Thus its actual temperature rise is larger.
$$\eta_c=\frac{h_{02s}-h_{01}}{h_{02}-h_{01}},\quad T_{02}=T_{01}+\frac{T_{02s}-T_{01}}{\eta_c},\quad w_{\mathrm{in}}=c_p(T_{02}-T_{01})$$
**3 · Expansion.** A turbine produces less work than the reversible reference, so its temperature drop is smaller. It cools while exporting shaft work, even with no heat crossing its casing.
$$\eta_t=\frac{h_{01}-h_{02}}{h_{01}-h_{02s}},\quad T_{02}=T_{01}-\eta_t(T_{01}-T_{02s}),\quad w_{\mathrm{out}}=c_p(T_{01}-T_{02})$$
Heating/cooling describes temperature changes here; it does not imply heat transfer. With heat transfer q positive into the fluid, the first law becomes Δh₀ = q + w_in.''')
    a,b,c=st.columns(3)
    mode=persistent_input(a.selectbox, 'Machine',['Compressor','Turbine'], key="tab_turbomachinery_machine")
    tin=persistent_input(a.number_input, 'Inlet stagnation temperature [K]',min_value=1.,value=300., key="tab_turbomachinery_inlet_stagnation_temperature_k")
    ratio=persistent_input(b.number_input, 'High / low stagnation pressure ratio',min_value=1.,max_value=100.,value=4., key="tab_turbomachinery_high_low_stagnation_pressure_ratio")
    eta=persistent_input(b.slider, 'Isentropic efficiency',.1,1.,.8, key="tab_turbomachinery_isentropic_efficiency")
    gamma=persistent_input(c.number_input, 'Machine γ',min_value=1.01,max_value=1.67,value=1.4, key="tab_turbomachinery_machine_comparison")
    gasr=persistent_input(c.number_input, 'Machine gas constant [J/(kg·K)]',min_value=1.,value=287.05, key="tab_turbomachinery_machine_gas_constant_j_kg_k")
    result=gas_machine(tin,ratio,eta,mode,gamma,gasr)
    a,b,c=st.columns(3)
    a.metric('Isentropic outlet T₀₂s',f'{result["ideal_temperature"]:.2f} K'); b.metric('Actual outlet T₀₂',f'{result["outlet_temperature"]:.2f} K'); c.metric('Work into fluid',f'{result["work_into_fluid"]/1000:+.2f} kJ/kg')
    fig=go.Figure(go.Bar(x=['Inlet','Isentropic outlet','Actual outlet'],y=[tin,result['ideal_temperature'],result['outlet_temperature']],marker_color=['#94a3b8','#38bdf8','#fbbf24']))
    fig.update_layout(title=f'{mode}: compare the same inlet and pressure ratio',yaxis_title='Stagnation temperature [K]',height=360)
    apply_plotly_theme(fig); render_plot(fig,'machine-temperature')
    st.markdown('### 9.4 Intercooling, reheating and throttling')
    prose(r'''**Compression with cooling.** From reversible steady-flow work dw_in = v dp, substitute v = RT/p. At constant T, integration gives the isothermal lower reference. Heat rejection must remove this work to keep enthalpy constant.
$$w_{\mathrm{iso,in}}=RT\ln(p_2/p_1),\qquad q=-w_{\mathrm{iso,in}}$$
For n identical compressor stages with perfect intercooling back to the original inlet temperature, minimize the sum of stage works subject to the product of stage pressure ratios. Equal ratios minimize the sum because the power function is convex in log pressure ratio.
$$r_{p,\mathrm{stage}}=r_p^{1/n},\quad w_{n}=\frac{nc_pT_{\mathrm{in}}}{\eta_c}\left[r_p^{(\gamma-1)/(n\gamma)}-1\right]$$
Each intercooler rejects cp times the preceding temperature rise. There are n−1 intercoolers; a final aftercooler is a separate duty. This ideal comparison assumes equal efficiency and no interstage pressure losses.

**Expansion with reheating.** Reheating between equal-ratio turbine stages back to the original hot inlet temperature increases shaft output; external heat supplies the added energy. A refrigeration expander instead keeps the cold exhaust and avoids reheating.
$$w_{n,\mathrm{out}}=n\eta_tc_pT_{\mathrm{in}}\left[1-r_p^{-(\gamma-1)/(n\gamma)}\right]$$
**Throttling is different.** A valve has no shaft output. With negligible heat, elevation and endpoint kinetic-energy changes, h₂ = h₁. An ideal gas therefore has no temperature change through the complete valve process. Real-gas Joule–Thomson cooling or heating depends on state and composition; it is not the turbine relation. Steam, condensing fluids and large temperature ranges require real property data.''')

    render_derivation(
        r"why compressor work is $\int v\,dp$, and why equal stage ratios are optimal",
        [
            (
                r"Reversible steady-flow work is $\int v\,dp$, not $\int p\,dv$",
                r"""
                Two facts, combined. The steady-flow energy equation with negligible kinetic
                and potential changes gives $\delta w_{\text{in}}=dh-\delta q$. Gibbs' relation
                gives $dh=T\,ds+v\,dp$, and reversibility gives $\delta q=T\,ds$. Subtract:
                $$\delta w_{\text{in}}=T\,ds+v\,dp-T\,ds=v\,dp
                \;\Longrightarrow\; w_{\text{in}}=\int_{p_1}^{p_2}v\,dp$$
                The closed-system result $\int p\,dv$ is a different quantity for a different
                situation; using it for a compressor is a standard and expensive error.
                The $v$ in $\int v\,dp$ is Tab 1's $1/\rho$, not a velocity — thermodynamics
                reused the letter; this course keeps $1/\rho$ wherever a speed is nearby.
                The practical reading is immediate: **work is proportional to
                specific volume**, so anything that keeps the gas dense while you squeeze it
                — cooling — reduces the bill.
                """,
            ),
            (
                "The isothermal reference, and why it is the cheapest possible path",
                r"""
                Hold $T$ constant and substitute the ideal-gas $v=RT/p$:
                $$w_{\text{iso,in}}=\int_{p_1}^{p_2}\frac{RT}{p}dp=RT\ln\frac{p_2}{p_1}$$
                Since $\Delta h=0$ for an isothermal ideal gas, the first law forces
                $q=-w_{\text{iso,in}}$: every joule of shaft work must be removed as heat.
                Adiabatic compression instead lets $T$ — and therefore $v$ — climb as the
                pressure rises, so the integrand grows and the same pressure ratio costs more.
                Isothermal is the floor; adiabatic is the ceiling.
                """,
            ),
            (
                "Stage work for the real, adiabatic machine",
                r"""
                Each stage is adiabatic with isentropic efficiency $\eta_c$, and perfect
                intercooling returns the gas to $T_{\text{in}}$ before the next one. Writing
                $k=(\gamma-1)/\gamma$, §9.3 gives one stage of ratio $r_i$:
                $$w_i=\frac{c_pT_{\text{in}}}{\eta_c}\left(r_i^{\,k}-1\right)$$
                Every stage starts from the same $T_{\text{in}}$ — that is what intercooling
                buys, and it is what makes the stages *comparable* in the next step.
                """,
            ),
            (
                "Minimise the sum subject to the fixed overall ratio",
                r"""
                The constraint is a product, $\prod_i r_i=r_p$, so take logarithms and let
                $x_i=\ln r_i$; the constraint becomes a **sum**, $\sum x_i=\ln r_p$, and the
                objective becomes
                $$\sum_i e^{k x_i}\ \to\ \min \quad\text{subject to}\quad \sum_i x_i=\text{const}$$
                $e^{kx}$ is convex, and for a convex function with a fixed sum of arguments
                the sum of values is smallest when all the arguments are **equal** (Jensen).
                Hence
                $$r_{p,\text{stage}}=r_p^{1/n},\qquad
                w_n=\frac{n\,c_pT_{\text{in}}}{\eta_c}\left(r_p^{\frac{\gamma-1}{n\gamma}}-1\right)$$
                The physical statement behind the algebra: any stage doing more than its share
                of the pressure ratio arrives at the next intercooler hotter, and hot gas is
                expensive to compress.
                """,
            ),
            (
                "Take the many-stage limit and recover the isothermal floor",
                r"""
                As $n\to\infty$, $r_p^{k/n}-1\to (k/n)\ln r_p$, so
                $$w_n\to\frac{c_pT_{\text{in}}}{\eta_c}\,k\ln r_p
                =\frac{R\,T_{\text{in}}}{\eta_c}\ln r_p$$
                using $c_pk=c_p(\gamma-1)/\gamma=R$. Infinitely many stages with perfect
                intercooling *is* isothermal compression, recovered exactly. Real machines
                stop at three or four stages because each intercooler brings pressure drop,
                cost and fouling — the curve of diminishing returns is steep.
                """,
            ),
            (
                "Where the rejected heat goes",
                r"""
                Each intercooler must remove the temperature rise the preceding stage created,
                $q_i=c_p\left(T_{\text{out},i}-T_{\text{in}}\right)$, and there are $n-1$ of
                them between $n$ stages. An aftercooler, if fitted, is a separate duty. Note
                that irreversibility is paid for twice: once as extra shaft work, and again as
                extra cooling-water duty to throw that same energy away.
                """,
            ),
            (
                "Throttling is not a degenerate case of any of this",
                r"""
                A valve has no shaft, so $w=0$, and with negligible heat and kinetic terms the
                energy equation reduces to $h_2=h_1$. For an ideal gas $h$ depends on $T$
                alone, so $T_2=T_1$ exactly — an ideal-gas throttle produces **no** cooling.
                Real-gas Joule–Thomson cooling comes entirely from the departure of $h$ from
                ideality, which is why §9.5 has to size it with a measured coefficient rather
                than derive it here.
                """,
            ),
        ],
    )
    stages=persistent_input(st.slider, 'Number of ideal intercooled / reheated stages',1,8,2, key="tab_turbomachinery_number_of_ideal_intercooled_reheated_stages")
    exponent=(gamma-1)/(gamma*stages)
    if mode=='Compressor':
        rise=tin*(ratio**exponent-1)/eta
        workn=stages*result['cp']*rise
        st.write(f'Perfect intercooling comparison: {workn/1000:.2f} kJ/kg shaft input; {(stages-1)*result["cp"]*rise/1000:.2f} kJ/kg rejected in intercoolers (no aftercooler).')
    else:
        drop=eta*tin*(1-ratio**(-exponent))
        st.write(f'Perfect reheating comparison: {stages*result["cp"]*drop/1000:.2f} kJ/kg shaft output; {(stages-1)*result["cp"]*drop/1000:.2f} kJ/kg added by reheaters.')
    st.markdown('**Daily and plant examples.** A bicycle pump warms because compression raises internal energy; slow pumping allows more heat rejection. Multistage synthesis-gas compression uses intercooling to reduce power and discharge temperature. A cryogenic air-separation expander supplies refrigeration by exporting shaft work. A pressure-reducing valve does not recover that work.')

    st.markdown('### 9.5 Where this actually runs: a cryogenic air separation unit')
    st.markdown(
        'Sections 9.1–9.4 are the general theory. This section puts every piece of it inside one '
        'real plant — the machine that makes the oxygen for a steel mill, the nitrogen for a '
        'semiconductor fab, and the argon for a welding shop. An air separation unit (ASU) is '
        'the purest example of turbomachinery doing thermodynamic work, because **the plant has '
        'no fuel and no refrigerant**: the only energy input is shaft work into compressors, and '
        'the only source of cold is shaft work taken *out* by an expander.'
    )
    render_svg(diagram_asu_flowsheet())

    st.markdown('#### 9.5.1 What the plant is trying to do, and why it is hard')
    prose(r'''Air is 78% N₂, 21% O₂, 0.93% Ar. Nitrogen boils at 77.4 K and oxygen at 90.2 K at one atmosphere — a 12.8 K gap. That gap is the entire basis of the separation, and it is the reason the plant must operate at 100 K rather than at ambient: **distillation needs a phase difference**, and air has none until it is cryogenic.

Three consequences follow immediately, and each one is a piece of turbomachinery.

**1 · The feed must be compressed.** Not because pressure separates anything, but because the cold end has to be reached through a heat exchanger and a throttle, and because the double column needs two pressures. The **main air compressor (MAC)** is a multistage intercooled centrifugal machine, typically three or four stages to about 5.5–6 bar. It is usually the single largest motor on the site.

**2 · The plant must be dried and scrubbed first.** At 100 K, water, CO₂ and heavy hydrocarbons are solids. They would plug the brazed-aluminium exchanger passages within hours. A **prepurifier** — a pair of molecular-sieve beds swapping between adsorption and regeneration — removes them upstream. Hydrocarbons matter for a second reason: they concentrate in the liquid-oxygen sump, where they are a genuine explosion hazard, which is why oxygen plants monitor sump hydrocarbons continuously.

**3 · Something must supply the refrigeration.** The cold box is well insulated but not perfectly, and the products leave colder than the feed arrives. Steady operation needs a continuous source of cold to cover heat leak and the product enthalpy deficit. That source is the **turboexpander**.''')

    render_callout(
        """
        **The idea the whole plant turns on.** A throttling valve and an expander both drop the
        pressure. The valve is isenthalpic: for an ideal gas it produces *no* temperature change
        at all, and for real air near 180 K it produces roughly 0.3–0.5 K per bar of
        Joule–Thomson cooling. The expander removes energy as **shaft work**, so it has a real
        enthalpy drop where the valve has exactly none, and its temperature drop is larger by
        nearly an order of magnitude at the same pressure ratio. Section 9.4 stated this as a distinction between processes. Here it
        is the difference between a plant that runs and a plant that slowly warms up and stops.
        """,
        title="Valve versus expander",
    )

    st.markdown('#### 9.5.2 The double column, and why it needs two pressures')
    prose(r'''A single distillation column separating air would need a condenser colder than 77 K and a reboiler hotter than 90 K, and there is no free cold sink at 77 K anywhere on the plant. Linde's double column solves this by **stacking two columns and letting one boil the other**.

The high-pressure (HP) column runs at about 5.5 bar. Raising the pressure raises every saturation temperature, so nitrogen condenses at roughly 95 K instead of 77 K. The low-pressure (LP) column above it runs near 1.4 bar, where liquid oxygen boils at about 93 K — not the 90.2 K normal boiling point quoted earlier, because it too is above atmospheric. Put a heat exchanger between them — the **condenser–reboiler** — and the HP column's condensing nitrogen boils the LP column's oxygen across a temperature difference of only about 2 K.

$$T_{\mathrm{cond}}^{\mathrm{HP}}(\mathrm{N_2},\ 5.5\ \mathrm{bar}) \approx 95\ \mathrm{K}
\;>\; T_{\mathrm{boil}}^{\mathrm{LP}}(\mathrm{O_2},\ 1.4\ \mathrm{bar}) \approx 93\ \mathrm{K}$$

The reflux for both columns is generated internally, with no external refrigeration duty at all. **The pressure ratio is doing thermodynamic work** — and that pressure ratio is what the MAC exists to supply. This is the clearest answer to "why compress air you are only going to separate": the compressor is not pushing the flow, it is buying a temperature difference.''')

    st.markdown('#### 9.5.3 Fully worked example')
    st.markdown(
        'A mid-size ASU. Every number below is computed live from §9.3\'s stage model with '
        'constant $c_p$ and $\\gamma$, so the assumptions are visible and the arithmetic can be '
        'checked by hand. Change an input and the conclusions move with it.'
    )

    asu1, asu2, asu3 = st.columns(3)
    m_air = persistent_input(asu1.number_input, 'Air feed ṁ [kg/s]', min_value=1., max_value=200., value=30., step=1., key='asu_mair')
    t_amb = persistent_input(asu1.number_input, 'Ambient / intercooled T [K]', min_value=270., max_value=320., value=293., step=1., key='asu_tamb')
    p_mac = persistent_input(asu2.number_input, 'MAC discharge [bar a]', min_value=2., max_value=12., value=5.8, step=.1, key='asu_pmac')
    n_mac = persistent_input(asu2.slider, 'MAC stages', 1, 5, 3, key='asu_nmac')
    eta_c = persistent_input(asu3.slider, 'Compressor isentropic efficiency', .60, .92, .82, key='asu_etac')
    eta_t = persistent_input(asu3.slider, 'Expander isentropic efficiency', .60, .92, .85, key='asu_etat')

    bac1, bac2, bac3 = st.columns(3)
    m_side = persistent_input(bac1.number_input, 'Expander side stream ṁ [kg/s]', min_value=.5, max_value=100., value=6., step=.5, key='asu_mside')
    p_bac = persistent_input(bac1.number_input, 'BAC discharge [bar a]', min_value=8., max_value=60., value=28., step=1., key='asu_pbac')
    t_exp_in = persistent_input(bac2.number_input, 'Expander inlet T [K]', min_value=100., max_value=300., value=180., step=5., key='asu_texp')
    p_exp_out = persistent_input(bac2.number_input, 'Expander outlet [bar a]', min_value=1.1, max_value=8., value=1.4, step=.1, key='asu_pexp')
    o2_recovery = persistent_input(bac3.slider, 'Oxygen recovery from the feed', .40, .98, .65, key='asu_rec')
    p_amb = persistent_input(bac3.number_input, 'Suction pressure [bar a]', min_value=.8, max_value=1.2, value=1.013, step=.005, key='asu_pamb')

    gamma_air, r_air = 1.4, 287.05
    stage_ratio = (p_mac / p_amb) ** (1.0 / n_mac)
    mac_stage = gas_machine(t_amb, stage_ratio, eta_c, 'Compressor', gamma_air, r_air)
    w_mac = n_mac * mac_stage['work_into_fluid']
    p_mac_w = m_air * w_mac

    bac_ratio = (p_bac / p_mac) ** 0.5
    bac_stage = gas_machine(t_amb, bac_ratio, eta_c, 'Compressor', gamma_air, r_air)
    w_bac = 2 * bac_stage['work_into_fluid']
    p_bac_w = m_side * w_bac

    exp = gas_machine(t_exp_in, p_bac / p_exp_out, eta_t, 'Turbine', gamma_air, r_air)
    w_exp = -exp['work_into_fluid']
    p_exp_w = m_side * w_exp
    refrigeration = m_side * mac_stage['cp'] * (t_exp_in - exp['outlet_temperature'])

    o2_mass_fraction = 0.2320
    m_o2 = m_air * o2_mass_fraction * o2_recovery
    net_power = p_mac_w + p_bac_w - p_exp_w
    kwh_per_tonne = (net_power / 1000.0) / (m_o2 * 3.6) if m_o2 > 0 else float('nan')

    st.markdown('**Step 1 · Main air compressor.** Equal stage ratios minimise the total work (§9.4), so each stage sees $r_p^{1/n}$ and perfect intercooling returns the gas to the intercooled temperature before the next stage.')
    s1a, s1b, s1c, s1d = st.columns(4)
    s1a.metric('Stage pressure ratio', f'{stage_ratio:.3f}')
    s1b.metric('Stage discharge T', f'{mac_stage["outlet_temperature"]:.1f} K')
    s1c.metric('MAC specific work', f'{w_mac / 1000:.1f} kJ/kg')
    s1d.metric('MAC shaft power', f'{p_mac_w / 1e6:.2f} MW')
    st.caption(
        f'Isentropic discharge would be {mac_stage["ideal_temperature"]:.1f} K; the extra '
        f'{mac_stage["outlet_temperature"] - mac_stage["ideal_temperature"]:.1f} K is the '
        f'irreversibility, and it is paid for twice — once as shaft work and again as '
        f'intercooler duty. Each of the {n_mac - 1} intercoolers rejects '
        f'{mac_stage["cp"] * (mac_stage["outlet_temperature"] - t_amb) / 1000:.1f} kJ/kg, '
        f'with an aftercooler on top. Without intercooling the same overall ratio in one stage '
        f'would need '
        f'{gas_machine(t_amb, p_mac / p_amb, eta_c, "Compressor", gamma_air, r_air)["work_into_fluid"] / 1000:.1f} kJ/kg — '
        f'{100 * (gas_machine(t_amb, p_mac / p_amb, eta_c, "Compressor", gamma_air, r_air)["work_into_fluid"] / w_mac - 1):.1f}% more.'
    )

    st.markdown('**Step 2 · Booster air compressor.** A side stream is boosted well above column pressure purely so the expander has a pressure ratio to work with. This is refrigeration equipment, not feed compression: the pressure it makes is destroyed on purpose in step 3.')
    s2a, s2b, s2c = st.columns(3)
    s2a.metric('BAC pressure ratio', f'{p_bac / p_mac:.2f}')
    s2b.metric('BAC specific work', f'{w_bac / 1000:.1f} kJ/kg')
    s2c.metric('BAC shaft power', f'{p_bac_w / 1e6:.2f} MW')

    st.markdown('**Step 3 · Turboexpander.** The boosted stream is cooled in the main exchanger to the expander inlet temperature, then expanded. Its temperature drop is the plant\'s refrigeration.')
    s3a, s3b, s3c, s3d = st.columns(4)
    s3a.metric('Expansion ratio', f'{p_bac / p_exp_out:.1f}')
    s3b.metric('Isentropic outlet T', f'{exp["ideal_temperature"]:.1f} K')
    s3c.metric('Actual outlet T', f'{exp["outlet_temperature"]:.1f} K')
    s3d.metric('Refrigeration produced', f'{refrigeration / 1e6:.3f} MW')
    st.caption(
        f'Specific shaft output {w_exp / 1000:.1f} kJ/kg; total {p_exp_w / 1e6:.3f} MW, normally '
        f'recovered by loading the expander shaft onto the booster wheel rather than a generator. '
        f'Temperature drop {t_exp_in - exp["outlet_temperature"]:.1f} K. The irreversibility shows '
        f'up here with the opposite sign to a compressor: the real machine ends '
        f'{exp["outlet_temperature"] - exp["ideal_temperature"]:.1f} K *warmer* than isentropic, '
        f'so a poor expander produces less cold as well as less work.'
    )

    st.markdown('**Step 4 · The comparison that justifies the expander.**')
    jt_coefficient = 0.40
    jt_drop = jt_coefficient * (p_bac - p_exp_out)
    cmp1, cmp2, cmp3 = st.columns(3)
    cmp1.metric('Expander ΔT', f'{t_exp_in - exp["outlet_temperature"]:.1f} K')
    cmp2.metric('J–T valve ΔT (real air)', f'≈ {jt_drop:.1f} K')
    cmp3.metric('Ratio', f'{(t_exp_in - exp["outlet_temperature"]) / max(jt_drop, 1e-9):.1f}×')
    st.caption(
        f'Same inlet state, same pressure drop. The valve figure uses a representative '
        f'Joule–Thomson coefficient of {jt_coefficient} K/bar for air near {t_exp_in:.0f} K — a '
        f'real-gas effect that vanishes entirely for an ideal gas, which is why §9.4 insists an '
        f'ideal-gas throttle has no temperature change at all. The expander is not a better '
        f'valve; it is a different process, because it exports work.'
    )

    st.markdown('**Step 5 · Plant specific energy.**')
    s5a, s5b, s5c = st.columns(3)
    s5a.metric('Oxygen produced', f'{m_o2:.2f} kg/s ({m_o2 * 86.4:.0f} t/day)')
    s5b.metric('Net shaft power', f'{net_power / 1e6:.2f} MW')
    s5c.metric('Specific energy', f'{kwh_per_tonne:.0f} kWh per tonne O₂')
    render_callout(
        f'**Sanity check against industry.** Modern large ASUs achieve roughly 200-260 kWh per '
        f'tonne of gaseous oxygen. This simplified model gives {kwh_per_tonne:.0f} kWh/t, and it '
        rf'should be expected to land high: constant $c_p$ and $\gamma$ overstate the work of '
        f'compressing cold dense air, the column is not optimised, adiabatic stage efficiency '
        f"ignores the real machines' intercooler effectiveness, and no credit is taken for "
        f'co-produced nitrogen or argon. The purpose of the calculation is the *structure* - '
        f'where the energy goes, and what each machine is for - not a guarantee number.'
    )

    st.markdown('#### 9.5.4 Which machine is which, and why')
    st.markdown(
        '| Duty | Machine | Why that type |\n'
        '|---|---|---|\n'
        '| Main air compression, 1→6 bar, large volume | Multistage centrifugal, intercooled | High volumetric flow at modest ratio; centrifugal stages tolerate the flow and are robust. Backswept impellers give the falling head curve §9.2 showed, which keeps the machine stable against surge. |\n'
        '| Boosting a side stream to 30–60 bar | Centrifugal booster, often on the expander shaft | Small flow, large ratio. Mounting it on the expander shaft recovers the expander work directly as compression, with no generator or gearbox. |\n'
        '| Producing refrigeration | Radial-inflow turboexpander, 20 000–90 000 rpm | Needs a large enthalpy drop in one stage at small flow. Radial inflow gives high work per stage; gas bearings avoid oil contamination in an oxygen plant. |\n'
        '| Pumping liquid oxygen to pipeline pressure | Cryogenic centrifugal pump | Compressing a liquid costs far less than compressing the gas — the internally compressed cycle that has largely replaced high-pressure gas compression. |\n'
    )
    st.markdown(
        '**Failure modes worth knowing.** A compressor pushed to low flow at high head enters '
        '**surge**: the flow through the passage reverses periodically, at a few hertz, and the '
        'machine shakes itself apart. §9.2 explains the root cause — a forward-curved or radial '
        'blade gives a flat or rising head curve, so there is no restoring slope to hold the '
        'operating point. Backsweep plus an anti-surge recycle valve is the standard answer. On '
        'the cold end, an expander ingesting liquid droplets erodes its blades within hours, '
        'which is why the inlet temperature is held well above the dew line and why the '
        'prepurifier is not optional.'
    )
    st.caption(
        'Model limits: constant-$c_p$ ideal gas throughout, no real-gas or phase-change behaviour, '
        'no column mass balance, no heat-leak or exchanger model, and no pressure drops. A design '
        'calculation needs real air property data (for example NIST REFPROP) and a solved column. '
        'Argon recovery, which adds a third column and materially changes the energy balance, is '
        'not modelled at all.'
    )
