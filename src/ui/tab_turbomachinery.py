import plotly.graph_objects as go
import streamlit as st
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
    imp_rpm = g1.number_input('Shaft speed [rpm]', min_value=100., max_value=60000., value=2900., step=100., key='imp_rpm')
    imp_q = g1.number_input('Volumetric flow Q [m³/s]', min_value=.001, max_value=2., value=.030, step=.005, format='%.3f', key='imp_q')
    imp_r1 = g2.number_input('Inlet (eye) radius r₁ [m]', min_value=.005, max_value=.4, value=.045, step=.005, key='imp_r1')
    imp_r2 = g2.number_input('Tip radius r₂ [m]', min_value=.01, max_value=1., value=.150, step=.005, key='imp_r2')
    imp_b1 = g3.number_input('Inlet width b₁ [m]', min_value=.002, max_value=.3, value=.030, step=.002, key='imp_b1')
    imp_b2 = g3.number_input('Outlet width b₂ [m]', min_value=.002, max_value=.3, value=.012, step=.002, key='imp_b2')
    imp_beta1 = g4.slider('Inlet blade angle β₁ [° from tangential]', 5., 89., 30., key='imp_beta1')
    imp_beta2 = g4.slider('Outlet blade angle β₂ [° from tangential]', 5., 89., 25., key='imp_beta2')
    imp_blades = st.slider('Number of blades Z', 2, 20, 7, key='imp_blades')

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

**1 · Derive the reversible reference.** Gibbs' relation gives Tds = dh − vdp. For an ideal gas dh = cp dT and v = RT/p; set ds = 0 and integrate.
$$0=c_p\frac{dT}{T}-R\frac{dp}{p}\quad\Rightarrow\quad\ln\frac{T_{02s}}{T_{01}}=\frac{R}{c_p}\ln\frac{p_{02}}{p_{01}}$$
$$T_{02s}=T_{01}\left(\frac{p_{02}}{p_{01}}\right)^{(\gamma-1)/\gamma}$$
**2 · Compression.** A real adiabatic compressor needs more work than the reversible reference to reach the same outlet pressure. Thus its actual temperature rise is larger.
$$\eta_c=\frac{h_{02s}-h_{01}}{h_{02}-h_{01}},\quad T_{02}=T_{01}+\frac{T_{02s}-T_{01}}{\eta_c},\quad w_{\mathrm{in}}=c_p(T_{02}-T_{01})$$
**3 · Expansion.** A turbine produces less work than the reversible reference, so its temperature drop is smaller. It cools while exporting shaft work, even with no heat crossing its casing.
$$\eta_t=\frac{h_{01}-h_{02}}{h_{01}-h_{02s}},\quad T_{02}=T_{01}-\eta_t(T_{01}-T_{02s}),\quad w_{\mathrm{out}}=c_p(T_{01}-T_{02})$$
Heating/cooling describes temperature changes here; it does not imply heat transfer. With heat transfer q positive into the fluid, the first law becomes Δh₀ = q + w_in.''')
    a,b,c=st.columns(3)
    mode=a.selectbox('Machine',['Compressor','Turbine'])
    tin=a.number_input('Inlet stagnation temperature [K]',min_value=1.,value=300.)
    ratio=b.number_input('High / low stagnation pressure ratio',min_value=1.,max_value=100.,value=4.)
    eta=b.slider('Isentropic efficiency',.1,1.,.8)
    gamma=c.number_input('Machine γ',min_value=1.01,max_value=1.67,value=1.4)
    gasr=c.number_input('Machine gas constant [J/(kg·K)]',min_value=1.,value=287.05)
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
    stages=st.slider('Number of ideal intercooled / reheated stages',1,8,2)
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
    m_air = asu1.number_input('Air feed ṁ [kg/s]', min_value=1., max_value=200., value=30., step=1., key='asu_mair')
    t_amb = asu1.number_input('Ambient / intercooled T [K]', min_value=270., max_value=320., value=293., step=1., key='asu_tamb')
    p_mac = asu2.number_input('MAC discharge [bar a]', min_value=2., max_value=12., value=5.8, step=.1, key='asu_pmac')
    n_mac = asu2.slider('MAC stages', 1, 5, 3, key='asu_nmac')
    eta_c = asu3.slider('Compressor isentropic efficiency', .60, .92, .82, key='asu_etac')
    eta_t = asu3.slider('Expander isentropic efficiency', .60, .92, .85, key='asu_etat')

    bac1, bac2, bac3 = st.columns(3)
    m_side = bac1.number_input('Expander side stream ṁ [kg/s]', min_value=.5, max_value=100., value=6., step=.5, key='asu_mside')
    p_bac = bac1.number_input('BAC discharge [bar a]', min_value=8., max_value=60., value=28., step=1., key='asu_pbac')
    t_exp_in = bac2.number_input('Expander inlet T [K]', min_value=100., max_value=300., value=180., step=5., key='asu_texp')
    p_exp_out = bac2.number_input('Expander outlet [bar a]', min_value=1.1, max_value=8., value=1.4, step=.1, key='asu_pexp')
    o2_recovery = bac3.slider('Oxygen recovery from the feed', .40, .98, .65, key='asu_rec')
    p_amb = bac3.number_input('Suction pressure [bar a]', min_value=.8, max_value=1.2, value=1.013, step=.005, key='asu_pamb')

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
