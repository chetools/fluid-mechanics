import math
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from src.physics.gas_dynamics import (
    normal_shock,
    nozzle,
    relief_capacity_curve,
    relief_sizing,
)
from src.plotting import plot_relief_capacity
from src.svg_diagrams import diagram_relief_valve, render_svg
from src.ui.pedagogy import (
    render_callout,
    render_plot,
    render_prose_and_latex as prose,
    render_self_check,
    render_what_to_notice,
)
from src.theme import apply_plotly_theme


def render_tab_compressible():
    st.markdown('### 10.1 Why density becomes an unknown')
    prose(r'''Compressible flow couples momentum to thermodynamics. A tire hiss, a gas jet and a process nitrogen restriction can accelerate gas until pressure, density and temperature change together. The incompressible approximation is often useful below Mach 0.3 **when heating and imposed density changes are also small**; low Mach alone does not imply constant density.

We start with steady, one-dimensional, single-phase flow of a calorically perfect ideal gas. Cross-section averages describe the stream, gravity is negligible and cp and γ are constant. All gas pressures are **absolute**, all temperatures kelvin. The gas controls below are independent of the liquid-property sidebar.
$$p=\rho RT,\quad h=c_pT,\quad c_p-c_v=R,\quad\gamma=c_p/c_v,\quad c_p=\gamma R/(\gamma-1)$$
**Sound speed.** A small, rapid disturbance is approximately isentropic. Combining the linearized mass and momentum equations gives a wave equation with a² = (∂p/∂ρ)s. Integrating ds = cv dT/T − R dρ/ρ = 0 gives p/ρ^γ constant, hence
$$a^2=\left(\frac{\partial p}{\partial\rho}\right)_s=\frac{\gamma p}{\rho}=\gamma RT,\qquad M=u/a.$$''')
    st.markdown('### 10.2 Derive the nozzle equations, one balance at a time')
    prose(r'''**1 · Mass conservation.** The same mass crosses every section. Differentiate the product and divide by ρuA.
$$\dot m=\rho uA,\qquad\frac{d\rho}{\rho}+\frac{du}{u}+\frac{dA}{A}=0$$
**2 · Momentum.** The axial pressure force accelerates the gas. For negligible wall friction and no body force, cancellation of the pressure-area terms gives
$$dp+\rho u\,du=0.$$ 
**3 · Energy.** An adiabatic nozzle has no shaft work. Static enthalpy is converted to kinetic energy, with stagnation enthalpy unchanged.
$$dh+u\,du=0,\quad c_pT+u^2/2=c_pT_0,\quad\frac{T_0}{T}=1+\frac{\gamma-1}{2}M^2$$
**4 · Entropy.** Substitute dh = −u du and dp = −ρu du into Tds = dh − dp/ρ. Then ds = 0 for this smooth, frictionless process. Integrate the ideal-gas entropy equation between the moving stream and its hypothetical isentropic rest state.
$$ds=c_p\frac{dT}{T}-R\frac{dp}{p}=0$$
$$\frac{p_0}{p}=\left(1+\frac{\gamma-1}{2}M^2\right)^{\gamma/(\gamma-1)},\quad\frac{\rho_0}{\rho}=\left(1+\frac{\gamma-1}{2}M^2\right)^{1/(\gamma-1)}$$
**5 · Area and speed.** Since dp = a²dρ along an isentrope, momentum gives dρ/ρ = −M²du/u. Substitute into continuity:
$$\boxed{\frac{dA}{A}=(M^2-1)\frac{du}{u}}$$
A converging passage accelerates subsonic flow. Supersonic flow accelerates in a diverging passage. A smooth passage through M = 1 requires a throat, but a throat alone does not guarantee sonic flow: the boundary pressures must support it.

**6 · Integrate to the area–Mach relation.** Substitute u = M√(γRT) and the stagnation ratios into mass conservation. Compare the local area with the sonic area A* at the same mass flow and stagnation state.
$$\frac{A}{A^*}=\frac{1}{M}\left[\frac{2}{\gamma+1}\left(1+\frac{\gamma-1}{2}M^2\right)\right]^{(\gamma+1)/(2(\gamma-1))}$$
For A/A* > 1 there are subsonic and supersonic mathematical branches. Boundary conditions, shocks and the nozzle geometry select the realized branch.''')
    st.markdown('### 10.3 Choking · a converging-nozzle calculator')
    prose(r'''Write mass flux using the same substitutions. At fixed reservoir p₀ and T₀, differentiating its logarithm with respect to M gives a maximum at M = 1.
$$\frac{\dot m}{A}=\frac{p_0}{\sqrt{T_0}}\sqrt{\frac{\gamma}{R}}\,M\left(1+\frac{\gamma-1}{2}M^2\right)^{-(\gamma+1)/(2(\gamma-1))}$$
$$\frac{p^*}{p_0}=\left(\frac{2}{\gamma+1}\right)^{\gamma/(\gamma-1)},\quad\frac{T^*}{T_0}=\frac{2}{\gamma+1}$$
Below the critical back-pressure ratio, a converging nozzle is sonic at its exit and further lowering the downstream pressure cannot increase its ideal mass flow. The jet adjusts outside the nozzle. The exit static pressure then differs from the imposed back pressure.
$$\dot m_* =A\frac{p_0}{\sqrt{T_0}}\sqrt{\frac{\gamma}{R}}\left(\frac{2}{\gamma+1}\right)^{(\gamma+1)/(2(\gamma-1))}$$''')
    a,b,c=st.columns(3)
    p0=a.number_input('Reservoir stagnation pressure [kPa absolute]',min_value=.001,value=500.)*1000
    t0=a.number_input('Reservoir stagnation temperature [K]',min_value=1.,value=300.)
    pb=b.number_input('Back pressure [kPa absolute]',min_value=.001,value=100.)*1000
    d=b.number_input('Converging-nozzle exit diameter [mm]',min_value=.01,value=5.)/1000
    gamma=c.number_input('Nozzle γ',min_value=1.01,max_value=1.67,value=1.4)
    gasr=c.number_input('Nozzle gas constant [J/(kg·K)]',min_value=1.,value=287.05)
    area=math.pi*d*d/4; result=nozzle(p0,t0,pb,area,gamma,gasr)
    a,b,c,e=st.columns(4)
    a.metric('Mass flow',f'{result["mass_flow"]:.5f} kg/s'); b.metric('Exit Mach',f'{result["mach"]:.3f}'); c.metric('Exit static T',f'{result["temperature"]:.2f} K'); e.metric('Exit static pressure',f'{result["pressure"]/1000:.2f} kPa abs')
    if pb>=p0:
        st.info('No forward flow: back pressure is at or above reservoir pressure. This calculator does not model reverse flow.')
    else:
        st.info(f'{"Choked" if result["choked"] else "Unchoked"} · critical back-pressure ratio = {result["critical_ratio"]:.4f}. Ideal smooth nozzle, discharge coefficient = 1.')
    ratios=np.linspace(.02,1,160)
    fig=go.Figure(go.Scatter(x=ratios,y=[nozzle(p0,t0,p0*r,area,gamma,gasr)['mass_flow'] for r in ratios],name='Ideal mass flow'))
    fig.add_vline(x=result['critical_ratio'],line_dash='dash',annotation_text='Sonic threshold',annotation_position='top left')
    fig.add_trace(go.Scatter(x=[min(pb/p0,1)],y=[result['mass_flow']],mode='markers',marker=dict(size=12),name='Your input (capped at ratio 1)'))
    fig.update_layout(title='Lowering back pressure eventually stops increasing flow',xaxis_title='Back pressure / reservoir stagnation pressure',yaxis_title='Mass flow [kg/s]',height=400)
    apply_plotly_theme(fig); render_plot(fig,'nozzle-choking')
    machs=np.concatenate([np.linspace(.12,1,80),np.linspace(1.01,3,80)])
    ar=1/machs*(2/(gamma+1)*(1+(gamma-1)*machs*machs/2))**((gamma+1)/(2*(gamma-1)))
    fig=go.Figure(go.Scatter(x=machs,y=ar,name='Area–Mach relation'))
    fig.update_layout(title='One area ratio, two possible Mach numbers',xaxis_title='Mach number',yaxis_title='A / A*',height=360)
    apply_plotly_theme(fig); render_plot(fig,'area-mach')
    st.caption('[NASA: isentropic flow relations](https://www.grc.nasa.gov/www/k-12/airplane/isentrop.html). Real orifices, valves and relief devices need geometry-dependent discharge coefficients and appropriate property models; this calculator represents an ideal converging nozzle.')
    st.markdown('### 10.4 A shock breaks the isentropic assumption')
    prose(r'''A normal shock is a very thin irreversible compression in supersonic flow. Integrate conservation across it instead of applying a smooth isentropic relation through it. Let 1 be upstream and 2 downstream, with equal cross-sectional areas.
$$\rho_1u_1=\rho_2u_2,\quad p_1+\rho_1u_1^2=p_2+\rho_2u_2^2,\quad c_pT_1+u_1^2/2=c_pT_2+u_2^2/2$$
**Eliminate velocity.** Set r = ρ₂/ρ₁ so u₂ = u₁/r. Momentum gives p₂/p₁ = 1 + γM₁²(1 − 1/r). The ideal-gas law gives T₂/T₁ = (p₂/p₁)/r. Substitute these into energy and solve the resulting quadratic; discard the unchanged-flow root r = 1 for M₁ > 1.
$$\frac{\rho_2}{\rho_1}=\frac{(\gamma+1)M_1^2}{2+(\gamma-1)M_1^2},\qquad\frac{p_2}{p_1}=1+\frac{2\gamma}{\gamma+1}(M_1^2-1)$$
$$M_2^2=\frac{1+(\gamma-1)M_1^2/2}{\gamma M_1^2-(\gamma-1)/2},\quad\frac{T_2}{T_1}=\frac{p_2/p_1}{\rho_2/\rho_1}$$
Static pressure and temperature rise; Mach number drops below one. Stagnation temperature stays constant because there is no heat or work. Entropy rises and stagnation pressure falls. Compute each side's stagnation pressure separately:
$$\frac{p_{02}}{p_{01}}=\frac{p_2}{p_1}\left[\frac{1+(\gamma-1)M_2^2/2}{1+(\gamma-1)M_1^2/2}\right]^{\gamma/(\gamma-1)}<1$$''')
    m1=st.slider('Upstream normal-shock Mach number',1.,5.,2.,step=.05)
    shock=normal_shock(m1,gamma)
    a,b,c,e=st.columns(4)
    a.metric('Downstream Mach',f'{shock["mach2"]:.3f}'); b.metric('Static p₂ / p₁',f'{shock["pressure_ratio"]:.3f}'); c.metric('Static T₂ / T₁',f'{shock["temperature_ratio"]:.3f}'); e.metric('Stagnation p₀₂ / p₀₁',f'{shock["stagnation_pressure_ratio"]:.4f}')
    st.caption('[NASA: normal-shock conservation relations](https://www.grc.nasa.gov/WWW/k-12/airplane/normal.html).')
    st.markdown('### 10.5 Long ducts: friction and heating can also choke flow')
    prose(r'''**Fanno flow: constant area, adiabatic, friction present.** Continuity gives dρ/ρ = −du/u. Energy keeps T₀ constant. The wall force on a length dx of circular pipe is τwπDdx, so dividing by area gives 4τw dx/D. With Darcy fD = 8τw/(ρu²), momentum becomes
$$dp+\rho u\,du+\frac{f_D}{D}\frac{\rho u^2}{2}dx=0,\quad c_p dT=-u\,du$$
Use the gas law, dp/p = dρ/ρ + dT/T. After substitution, the two velocity terms combine into (M²−1)du/u:
$$\frac{du}{u}=\frac{\gamma M^2}{2(1-M^2)}\frac{f_D\,dx}{D}$$
Friction accelerates a subsonic gas and decelerates a supersonic gas toward M = 1. Pressure energy, density and speed adjust together; the incompressible intuition “friction always slows flow downstream” is inadequate. The remaining nondimensional length to choking is
$$\int_x^{x^*}\frac{f_D}{D}dx=\frac{1-M^2}{\gamma M^2}+\frac{\gamma+1}{2\gamma}\ln\left[\frac{(\gamma+1)M^2}{2+(\gamma-1)M^2}\right].$$
For constant fD and D the left side is fD L*/D. Do not add an extra factor of four: many references instead use the Fanning factor. A specified inlet state cannot support an arbitrarily long duct at the same mass flow; the global boundary-value solution must adjust.

**Rayleigh flow: constant area, heat transfer, negligible friction.** Mass flux G = ρu is constant; momentum gives p + ρu² constant. Divide momentum by p and compare with the sonic reference on the same Rayleigh line:
$$\frac{p}{p^*}=\frac{\gamma+1}{1+\gamma M^2},\quad\frac{T}{T^*}=M^2\left(\frac{\gamma+1}{1+\gamma M^2}\right)^2$$
Energy now gives dq = dh₀ = cp dT₀. Multiplying the static-temperature ratio by the ratio of stagnation corrections yields
$$\frac{T_0}{T_0^*}=\frac{2(\gamma+1)M^2[1+(\gamma-1)M^2/2]}{(1+\gamma M^2)^2}.$$
Adding heat drives either branch toward sonic conditions, where T₀ is maximal along the line. Removing heat drives it away. Static temperature is not monotonic over the entire subsonic branch: it reaches a maximum at M = 1/√γ. Real heated rough pipes combine both effects; separate Fanno and Rayleigh formulas cannot simply be added.''')
    st.caption('[NPTEL: Fanno flow](https://archive.nptel.ac.in/content/storage2/courses/112103021/module2/lec15/1.html) · [Rayleigh flow](https://archive.nptel.ac.in/content/storage2/courses/112103021/module2/lec14/1.html).')
    st.markdown('### 10.6 Use the model in everyday and process problems')
    st.dataframe([
        {'Situation':'Air escaping a tire','First model':'Reservoir + restriction; test choking','What changes':'Reservoir pressure and temperature fall with time; steady nozzle relation is an instantaneous approximation.'},
        {'Situation':'Blowing through a narrow nozzle','First model':'Mass + momentum + energy','What changes':'The accelerating gas cools statically even though its stagnation temperature stays nearly constant.'},
        {'Situation':'Nitrogen supply to a reactor','First model':'Absolute-pressure boundaries, valve/nozzle and gas-line losses','What changes':'Check mass flow rather than assuming equal inlet/outlet volumetric flow; use compressible pipe modeling for large density changes.'},
        {'Situation':'Compressor with intercooler','First model':'Shaft work followed by heat rejection','What changes':'Stage discharge warms; cooling reduces the next stage’s specific volume and work.'},
        {'Situation':'Hot process gas in a duct','First model':'Coupled friction and heat transfer','What changes':'Mass, momentum, energy and properties must be solved together; choking limits admissible flow.'},
        {'Situation':'Aerosol can, steam or relief discharge','First model':'Check phase and real-gas properties first','What changes':'Flashing, condensation and two-phase choking can invalidate the perfect-gas model.'},
    ],hide_index=True,width='stretch')
    st.markdown('**Before CFD.** The next chapter solves incompressible Navier–Stokes. Its pressure correction enforces approximately zero velocity divergence; it does not solve the gas energy equation, shock waves or sonic choking. Compressible CFD instead couples density, momentum and total energy with an equation of state and requires suitable wave-resolving numerical fluxes.')

    st.markdown('### 10.7 Why choking is the foundation of pressure relief design')
    st.markdown(
        'Choking is not a curiosity confined to rockets and wind tunnels. It is the single '
        'fact that makes a relief valve sizeable at all, and every process plant on earth '
        'depends on it. Section 10.3 showed the mass-flow plateau; this section is what that '
        'plateau is worth.'
    )
    render_svg(diagram_relief_valve())

    st.markdown('#### 10.7.1 The design fact')
    prose(r'''Every pressure vessel needs a relief device sized so that, in a defined worst-case scenario — external fire, blocked outlet, control-valve failure open, thermal expansion — it can pass enough mass to stop the pressure climbing past the code limit. To size the hole you must know the flow through it.

For an incompressible flow that would be a problem, because the flow through an orifice depends on the pressure on **both** sides, and the downstream side is a flare header shared with every other device on the plant, whose pressure during an upset is not something you know precisely.

Choking removes the difficulty entirely. Above the critical ratio the throat runs sonic, and no information can travel upstream against a flow already moving at the speed of sound. The throat therefore cannot detect the downstream pressure, and
$$G=\frac{\dot m}{A}=p_0\sqrt{\frac{\gamma}{RT_0}}\left(\frac{2}{\gamma+1}\right)^{\frac{\gamma+1}{2(\gamma-1)}}$$
contains no back pressure at all. The required area follows immediately:
$$A=\frac{W}{K_d\,G}$$
with $W$ the required relief rate and $K_d$ the device's discharge coefficient. **The capacity of a relief device is a property of the vessel and the hole, not of what it discharges into.**''')
    render_callout(
        """
        **For air-like gases the threshold is $p_0/p_b > 1.9$.** The critical ratio is
        $(2/(\\gamma+1))^{\\gamma/(\\gamma-1)} = 0.528$ for $\\gamma = 1.4$, so anything
        relieving from above roughly 1.9 bar absolute to atmosphere is already choked. Since
        set pressures are usually many times atmospheric, **choked flow is the normal case in
        relief sizing, not the exception** — which is why the sizing equations in API 520 are
        written for it and carry a separate, messier subcritical form for the rest.
        """,
        title="Almost every relief case is choked",
    )

    st.markdown('#### 10.7.2 What the formula tells a designer')
    prose(r'''Three consequences fall straight out of $G \propto p_0/\sqrt{T_0}$, and each one is a mistake someone has made.

**1 · You cannot buy capacity with a lower downstream pressure.** Routing a valve to a lower-pressure header, or to a vacuum, adds nothing while it stays choked. If a device is undersized the only remedies are more area or a higher set pressure.

**2 · A hot relief case is a bigger relief case.** $G$ falls as $\sqrt{T_0}$ rises, so the same hole passes less mass. The fire case is often sizing precisely because the relieving temperature is high — and it is the *relieving* stagnation temperature that matters, not the normal operating one.

**3 · Rising back pressure eventually does bite, in two separate ways.** Once the total back pressure exceeds the critical ratio, flow unchokes and capacity genuinely falls, and the subcritical equation must be used. Separately, and usually first, back pressure interferes with the *valve* rather than the *flow*: a conventional spring valve becomes unstable above roughly 10% built-up back pressure, which is why balanced-bellows and pilot-operated designs exist.''')

    st.markdown('#### 10.7.3 Sizing calculator')
    rl1, rl2, rl3 = st.columns(3)
    w_req = rl1.number_input('Required relief rate W [kg/s]', min_value=.001, max_value=500.,
                             value=5.0, step=.5, key='relief_w')
    p_set = rl1.number_input('Relieving pressure p₀ [bar a]', min_value=1.05, max_value=400.,
                             value=12.0, step=.5, key='relief_p0')
    t_rel = rl2.number_input('Relieving temperature T₀ [K]', min_value=100., max_value=1500.,
                             value=333.15, step=5., key='relief_t0')
    p_back = rl2.number_input('Total back pressure [bar a]', min_value=.05, max_value=390.,
                              value=1.013, step=.1, key='relief_pb')
    kd = rl3.number_input('Discharge coefficient K_d', min_value=.1, max_value=1.,
                          value=.975, step=.005, key='relief_kd')
    gamma_r = rl3.number_input('γ', min_value=1.01, max_value=1.7, value=1.4, step=.01,
                               key='relief_gamma')
    r_gas = rl3.number_input('Gas constant R [J/(kg·K)]', min_value=20., max_value=4200.,
                             value=287.05, step=1., key='relief_r')

    if p_back >= p_set:
        st.error('Back pressure must be below the relieving pressure, or nothing flows out.')
    else:
        sizing = relief_sizing(w_req, p_set * 1e5, t_rel, p_back * 1e5,
                               gamma_r, r_gas, kd)
        s1, s2, s3, s4 = st.columns(4)
        s1.metric('Required throat area', f"{sizing['area'] * 1e6:.0f} mm²")
        s2.metric('Equivalent bore', f"{sizing['diameter'] * 1000:.1f} mm")
        s3.metric('Mass flux G', f"{sizing['mass_flux']:.0f} kg/(s·m²)")
        s4.metric('p_b / p₀', f"{sizing['back_pressure_ratio']:.3f}",
                  'choked' if sizing['choked'] else 'NOT choked')

        if sizing['choked']:
            st.success(
                f"Choked: {sizing['back_pressure_ratio']:.3f} is below the critical ratio "
                f"{sizing['critical_ratio']:.3f}. Capacity is fixed by p₀ and T₀ alone — "
                "lowering the back pressure further would change nothing."
            )
        else:
            st.warning(
                f"**Not choked.** {sizing['back_pressure_ratio']:.3f} exceeds the critical "
                f"ratio {sizing['critical_ratio']:.3f}, so the throat now feels the "
                f"downstream pressure and capacity has fallen "
                f"{100 * sizing['capacity_loss_vs_choked']:.1f}% below the choked value. "
                "The area above already accounts for that. Check the valve type too: this "
                "much back pressure will also affect lift on a conventional spring valve."
            )
        st.caption(
            f"Choked mass flux at these conditions would be "
            f"{sizing['choked_mass_flux']:.0f} kg/(s·m²). Sizing basis: A = W/(K_d G) with "
            f"K_d = {kd:g}. Doubling p₀ halves the area; raising T₀ from {t_rel:.0f} K to "
            f"{4 * t_rel:.0f} K would double it."
        )
        render_what_to_notice(
            'Drag the back pressure up from 1 bar. Nothing at all happens to the area until '
            'you cross the critical ratio — then it starts to climb. That flat stretch is '
            'the entire reason relief devices can be sized against a header whose pressure '
            'nobody knows exactly.'
        )
        render_plot(
            plot_relief_capacity(
                relief_capacity_curve(p_set * 1e5, t_rel, gamma_r, r_gas),
                sizing['back_pressure_ratio'],
            ),
            'relief-capacity',
        )

    st.markdown('#### 10.7.4 Worked example: a blocked-outlet case')
    prose(r'''A vessel with a set pressure of 10 bar g relieves gas at 10% overpressure, so $p_0 = 11$ bar g $= 12.0$ bar a. The relieving temperature is 60 °C = 333 K, the gas is air-like, and the blocked-outlet scenario requires $W = 5$ kg/s. The device discharges to a flare header at 1.013 bar a through a nozzle-type valve, $K_d = 0.975$.

**1 · Is it choked?** $p_b/p_0 = 1.013/12.0 = 0.084$, far below 0.528. Choked, comfortably.

**2 · Mass flux.** With $\gamma = 1.4$ and $R = 287$ J/(kg·K),
$$G = 12.0\times10^{5}\sqrt{\frac{1.4}{287\times333}}\left(\frac{2}{2.4}\right)^{3} = 2.66\times10^{3}\ \mathrm{kg/(s\,m^2)}$$

**3 · Area.** $A = W/(K_d G) = 5/(0.975 \times 2657) = 1.93\times10^{-3}\ \mathrm{m^2}$, an equivalent bore of 49.6 mm. In API 526 terms that falls between the standard "P" and "Q" orifices, and you would select the next size up — never down.

**4 · Now test the assumptions.** Raise the header to 8 bar a and $p_b/p_0 = 0.67$: no longer choked, capacity down about 4%, and a conventional spring valve would be well past its 10% built-up back-pressure limit. Raise the relieving temperature to the fire case instead, say 811 K, and $G$ falls by $\sqrt{811/333} = 1.56$, so the required area grows by the same factor to 77 mm — a different valve entirely. **The scenario, not the vessel, sizes the device.**''')
    render_self_check(
        'relief_self_check_backpressure',
        'A relief valve is choked, discharging to a 1 bar a header. Someone proposes routing '
        'it to a 0.3 bar a vacuum header to gain capacity. The gain is…',
        ['about three times', 'none at all', 'about 40%'],
        'none at all',
        'While choked, the throat cannot detect downstream pressure — the mass flux contains '
        'no p_b term. The only ways to pass more are more area or a higher relieving '
        'pressure. This is the most useful single consequence of choking in process safety.',
    )
    st.caption(
        'Model limits: single-phase ideal gas with constant γ, no inlet line loss, no valve '
        'dynamics. **This does not size two-phase or flashing relief**, which needs the omega '
        'method or a homogeneous equilibrium model and can require an order of magnitude more '
        'area — the single most consequential way a gas-only calculation goes wrong. Real '
        'sizing follows API 520/521 with certified K_d values, checks the 3% inlet-loss rule, '
        'and verifies the built-up back pressure against the valve type. Nothing here is a '
        'substitute for that.'
    )
