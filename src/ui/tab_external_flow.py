import math
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from src.ui.state import persistent_input
from src.units import get_fluid_state
from src.physics.gas_dynamics import sphere_drag, sphere_terminal_velocity
from src.svg_diagrams import diagram_sphere_forces, diagram_sphere_separation, render_svg
from src.ui.pedagogy import render_derivation, render_prose_and_latex as prose, render_plot
from src.theme import apply_plotly_theme


def render_tab_external_flow():
    st.markdown('### 9.1 From wall shear to wake drag')
    prose(r'''An immersed object feels both pressure and viscous traction. Far upstream the fluid is nearly uniform; a boundary layer forms on the object and may separate into a wake. Use the object's diameter for a sphere, and the **projected frontal area** in its drag coefficient.
$$F_D=\int_S(-p\mathbf n+\boldsymbol\tau\cdot\mathbf n)\cdot\mathbf e_U\,dS=\tfrac12\rho U^2C_D A,\quad A=\pi d^2/4,\quad Re_d=\rho Ud/\mu$$
A flat plate aligned with flow is often dominated by skin friction; a bluff sphere or cylinder often has substantial pressure drag. Their coefficient curves and reference areas are different. Pipe transition thresholds do not classify these flows.''')
    render_derivation(
        r"the drag integral, and what $C_D$ is actually measuring",
        [
            (
                "A surface can only transmit force through the stress tensor",
                r"""
                Tab 6 shows that the force per unit area a fluid exerts on a surface with
                outward normal $\mathbf n$ is the traction
                $\mathbf t=\boldsymbol\sigma\cdot\mathbf n$, and that for a Newtonian fluid the
                stress splits into an isotropic pressure and a deviatoric part:
                $$\boldsymbol\sigma=-p\mathbf I+\boldsymbol\tau
                \;\Longrightarrow\;
                \mathbf t=-p\,\mathbf n+\boldsymbol\tau\cdot\mathbf n$$
                Those are the only two ways the fluid can push on the body: **squeezing it
                normal to the surface** and **dragging it tangentially**. There is no third
                mechanism, so this integral is complete, not a model.
                """,
            ),
            (
                "Drag is the component along the oncoming stream, so project before adding",
                r"""
                Force is a vector; adding magnitudes over a closed surface would give
                nonsense. Dot with the unit vector $\mathbf e_U$ along the free stream and
                integrate over the wetted surface:
                $$F_D=\oint_S\left(-p\,\mathbf n+\boldsymbol\tau\cdot\mathbf n\right)
                \cdot\mathbf e_U\,dS$$
                The component perpendicular to $\mathbf e_U$ is lift, and for a symmetric
                body at zero incidence it cancels by symmetry. Note that a *uniform*
                pressure contributes nothing at all: $\oint\mathbf n\,dS=\mathbf 0$ over any
                closed surface. Only pressure **differences** front to back can drag.
                """,
            ),
            (
                "Non-dimensionalise with the momentum the body actually intercepts",
                r"""
                The stream carries momentum flux of order $\rho U^{2}$ per unit area, and the
                body blocks its frontal (projected) area $A$. So $\tfrac12\rho U^{2}A$ is the
                natural force scale — the same $\tfrac12\rho U^{2}$ dynamic pressure that
                appears in Bernoulli. Defining
                $$C_D\equiv\frac{F_D}{\tfrac12\rho U^{2}A}$$
                makes $C_D$ read as "drag, in units of the momentum the body stands in the
                way of". Because it is a *definition*, it predicts nothing by itself; the
                physics lives entirely in how $C_D$ depends on $\mathrm{Re}_d$.
                """,
            ),
            (
                "The reference area is part of the definition, not a detail",
                r"""
                $A=\pi d^{2}/4$ for a sphere is the projected frontal area. A flat plate
                aligned with the flow is quoted on its *wetted* area instead, and an aerofoil
                on its planform. Quoting a $C_D$ without its reference area is meaningless,
                and mixing conventions is a common factor-of-several error.
                """,
            ),
        ],
    )
    st.markdown('### 9.2 Stokes flow · a derivation for a sphere')
    render_svg(diagram_sphere_forces())
    prose(r'''**1 · Scale the equations.** Compare inertia with viscous stress. If Re ≪ 1, discard inertia but retain viscosity everywhere. Assume steady incompressible Newtonian flow, an isolated rigid sphere and no slip.
$$Re(\mathbf u^*\cdot\nabla^*)\mathbf u^*=-\nabla^*p^*+\nabla^{*2}\mathbf u^*\quad\longrightarrow\quad\nabla p=\mu\nabla^2\mathbf u,\quad\nabla\cdot\mathbf u=0$$
**2 · Enforce geometry and boundary conditions.** Write an axisymmetric streamfunction with radius a = d/2 and polar angle θ measured from the positive upstream velocity direction. The curl of momentum eliminates pressure and gives the biharmonic streamfunction equation. Its uniform-flow, r and 1/r terms are fixed by no slip at r = a and uniform speed U far away.
$$\psi=\frac{U\sin^2\theta}{2}\left(r^2-\frac{3ar}{2}+\frac{a^3}{2r}\right)$$
$$u_r=U\cos\theta\left(1-\frac{3a}{2r}+\frac{a^3}{2r^3}\right),\quad u_\theta=-U\sin\theta\left(1-\frac{3a}{4r}-\frac{a^3}{4r^3}\right)$$
**3 · Recover pressure and wall shear.** Substitute velocities into radial momentum and set the far-field pressure to p∞.
$$p-p_\infty=-\frac{3\mu Ua\cos\theta}{2r^2},\qquad \tau_{r\theta}|_{r=a}=-\frac{3\mu U\sin\theta}{2a}$$
**4 · Integrate the axial force.** Pressure uses the projection cos θ; shear uses −sin θ. Integrating with dS = 2πa² sin θ dθ gives one third of the drag from pressure and two thirds from shear.
$$F_p=2\pi\mu aU,\quad F_\mu=4\pi\mu aU,\quad F_D=6\pi\mu aU=3\pi\mu dU$$
$$C_D=\frac{3\pi\mu dU}{\rho U^2\pi d^2/8}=\frac{24}{Re_d}$$
The coefficient diverges as U → 0, but the **force tends to zero linearly**. A high coefficient is not necessarily a large force.''')
    render_derivation(
        r"Stokes' $6\pi\mu a U$ in full — where every constant comes from",
        [
            (
                "Justify dropping inertia, term by term",
                r"""
                Scale the steady Navier–Stokes equation with $U$, $a$ and the viscous
                pressure scale $\mu U/a$ (the pressure a viscous stress can generate over the
                sphere):
                $$\underbrace{\mathrm{Re}\,(\mathbf u^{*}\cdot\nabla^{*})\mathbf u^{*}}
                _{\text{inertia}}
                =-\nabla^{*}p^{*}+\nabla^{*2}\mathbf u^{*}$$
                For $\mathrm{Re}\ll1$ the left side is uniformly small, so we delete it —
                and unlike the boundary-layer approximation of Tab 8, we keep the viscous
                term **everywhere**, including far from the sphere. What is left is linear:
                $$\nabla p=\mu\nabla^{2}\mathbf u,\qquad \nabla\cdot\mathbf u=0$$
                Linearity is why this problem has an exact closed-form answer while almost
                nothing else in the course does.
                """,
            ),
            (
                "Eliminate pressure by taking the curl, then use the stream function",
                r"""
                Taking the curl of the momentum equation kills $\nabla p$ (the curl of a
                gradient is zero) and leaves $\nabla^{2}\boldsymbol\omega=0$. The flow is
                axisymmetric with no swirl, so a single scalar stream function $\psi(r,\theta)$
                carries both velocity components and satisfies continuity *identically*:
                $$u_r=\frac{1}{r^{2}\sin\theta}\frac{\partial\psi}{\partial\theta},
                \qquad
                u_\theta=-\frac{1}{r\sin\theta}\frac{\partial\psi}{\partial r}$$
                Substituting turns $\nabla^{2}\boldsymbol\omega=0$ into a fourth-order
                **linear** equation for $\psi$ — the Stokes analogue of the biharmonic
                equation. Three unknown fields have become one.
                """,
            ),
            (
                r"The far field dictates the $\sin^{2}\theta$ separation",
                r"""
                A uniform stream $U\mathbf e_U$ has stream function
                $\psi_\infty=\tfrac12Ur^{2}\sin^{2}\theta$. The operator does not mix angular
                harmonics, so the disturbance the sphere creates must carry the same angular
                factor. Write $\psi=f(r)\sin^{2}\theta$; the fourth-order equation reduces to
                an equidimensional (Euler) ODE in $r$, whose four independent solutions are
                $$f(r)=D r^{4}+A r^{2}+B r+\frac{C}{r}$$
                No physics has been assumed yet beyond axisymmetry.
                """,
            ),
            (
                "Boundary conditions fix all four constants",
                r"""
                **Far away** the disturbance may not grow, which kills $D$, and matching
                $\psi\to\psi_\infty$ gives $A=U/2$. **At the surface** no-slip demands both
                velocity components vanish at $r=a$:
                $$u_r=2\cos\theta\left(\frac{U}{2}+\frac{B}{r}+\frac{C}{r^{3}}\right)=0,
                \qquad
                u_\theta=-\sin\theta\left(U+\frac{B}{r}-\frac{C}{r^{3}}\right)=0
                \quad\text{at } r=a$$
                Two linear equations, two unknowns:
                $B=-\tfrac34aU$ and $C=\tfrac14a^{3}U$. Substituting them reproduces the
                $\psi$, $u_r$ and $u_\theta$ quoted above. Check the result at $r=a$:
                $1-\tfrac32+\tfrac12=0$ and $1-\tfrac34-\tfrac14=0$. The famously slow
                $1/r$ decay of the disturbance is the $B$ term — a Stokes sphere is felt
                enormously far away, which is why particle interactions matter at low
                concentration.
                """,
            ),
            (
                "Recover the two tractions the drag integral needs",
                r"""
                Substituting $\mathbf u$ back into the radial momentum equation and setting
                $p\to p_\infty$ far away gives
                $$p-p_\infty=-\frac{3\mu Ua\cos\theta}{2r^{2}}$$
                — high pressure on the upstream face ($\theta=\pi$), low on the downstream
                face, perfectly antisymmetric. The surface shear follows from the Newtonian
                constitutive law in spherical coordinates:
                $$\tau_{r\theta}\big|_{r=a}=-\frac{3\mu U\sin\theta}{2a}$$
                which is largest at the equator, where the fluid slides past fastest.
                """,
            ),
            (
                "Integrate each contribution over the sphere",
                r"""
                Use the ring element $dS=2\pi a^{2}\sin\theta\,d\theta$: a band of constant
                $\theta$. Pressure acts along $\mathbf n=\mathbf e_r$, whose component along
                the flow is $\cos\theta$; shear acts along $\mathbf e_\theta$, whose component
                is $-\sin\theta$. The uniform $p_\infty$ integrates to zero, as Step 2 of the
                previous derivation promised:
                $$F_p=\int_0^\pi\frac{3\mu U}{2a}\cos^{2}\theta\;2\pi a^{2}\sin\theta\,d\theta
                =3\pi\mu Ua\int_0^\pi\cos^{2}\theta\sin\theta\,d\theta
                =3\pi\mu Ua\cdot\frac23=2\pi\mu Ua$$
                $$F_\mu=\int_0^\pi\frac{3\mu U}{2a}\sin^{2}\theta\;2\pi a^{2}\sin\theta\,d\theta
                =3\pi\mu Ua\int_0^\pi\sin^{3}\theta\,d\theta
                =3\pi\mu Ua\cdot\frac43=4\pi\mu Ua$$
                The famous one-third / two-thirds split is nothing more exotic than the ratio
                of $\int\cos^{2}\theta\sin\theta$ to $\int\sin^{3}\theta$.
                """,
            ),
            (
                "Add, then convert to a coefficient",
                r"""
                $$F_D=2\pi\mu Ua+4\pi\mu Ua=6\pi\mu a U=3\pi\mu d U$$
                $$C_D=\frac{3\pi\mu dU}{\tfrac12\rho U^{2}\cdot\pi d^{2}/4}
                =\frac{24\mu}{\rho U d}=\frac{24}{\mathrm{Re}_d}$$
                The $24/\mathrm{Re}$ is not an experimental fit. It is $6\pi$ divided by the
                $\pi/8$ buried in the definition of $C_D$ — which is exactly why a coefficient
                that "blows up" at low speed describes a force that is *vanishing* linearly
                with $U$.
                """,
            ),
            (
                "Know where it stops being true",
                r"""
                Deleting inertia in Step 1 is uniformly valid only for $\mathrm{Re}\lesssim0.1$.
                Far from the sphere the neglected inertia term eventually beats the retained
                viscous one no matter how small $\mathrm{Re}$ is — the reason the same method
                *fails outright* for a cylinder (Stokes' paradox) and needs Oseen's correction.
                The lab below warns whenever your entered or terminal $\mathrm{Re}$ leaves the
                valid range.
                """,
            ),
        ],
    )
    st.markdown('### 9.3 Settling and finite-inertia drag lab')
    fluid = get_fluid_state(); rho, mu = fluid['rho'], fluid['mu']
    c1,c2,c3 = st.columns(3)
    diameter = persistent_input(c1.number_input, 'Sphere diameter [mm]', min_value=.001, value=.1, key='sphere_d')/1000
    speed = persistent_input(c2.number_input, 'Relative speed [m/s]', min_value=.000001, value=.001, format='%.6f', key='sphere_u')
    density = persistent_input(c3.number_input, 'Particle density [kg/m³]', min_value=.1, value=2500., key='sphere_rho')
    re = rho*speed*diameter/mu
    drag=3*math.pi*mu*diameter*speed
    settle = sphere_terminal_velocity(diameter, density, rho, mu)
    a,b,c=st.columns(3)
    a.metric('Re at entered speed',f'{re:.4g}'); b.metric('Stokes drag estimate',f'{drag:.3e} N'); c.metric('Stokes terminal velocity',f'{settle["stokes_u"]:.4g} m/s')
    st.caption(
        f'Shared fluid: ρ = {rho:g} kg/m³, μ = {mu:g} Pa·s. Positive terminal velocity is downward. '
        f'Stokes Re_t = {settle["stokes_re"]:.3g}. '
        f'Schiller–Naumann terminal speed = {settle["sn_u"]:.4g} m/s (Re_t = {settle["sn_re"]:.3g}), '
        'from the implicit balance the derivation below requires when Stokes Re_t is not small.'
    )
    if re > .1 or settle['stokes_re'] > .1:
        st.warning('At least one Stokes estimate is outside the conservative Re ≤ 0.1 creeping-flow range. Use the Schiller–Naumann terminal speed rather than the Stokes rearrangement.')
    if not settle['in_sn_range']:
        st.warning(
            f'Schiller–Naumann terminal Re_t = {settle["sn_re"]:.3g} is past the Re = 1000 fit. '
            'The Newton-regime drag is closer to C_D ≈ 0.44; do not use this settling speed as a prediction.'
        )
    cd=sphere_drag(re,strict=False)
    force=0.5*rho*speed**2*cd*math.pi*diameter**2/4
    if re <= 1000:
        st.write(f'Schiller–Naumann finite-inertia estimate: CD = {cd:.4g}; drag = {force:.3e} N. Used here only up to Re = 1000 for an isolated rigid sphere.')
    else:
        st.warning(
            f'Re = {re:.4g} is past the Re = 1000 fit range of Schiller–Naumann. Extrapolating gives '
            f'CD = {cd:.4g} (drag {force:.3e} N), but the measured curve flattens near CD ≈ 0.44 through '
            'the Newton regime instead of continuing to fall — compare the two on the chart below. '
            'Do not use the extrapolated number.'
        )
    prose(r'''At terminal speed, acceleration is zero: weight minus buoyancy balances drag. Cancel the common πd factor to obtain the Stokes settling law. It does not describe interacting particles, walls, deformable drops or bubbles with mobile interfaces.
$$\frac{\pi d^3}{6}(\rho_p-\rho)g=3\pi\mu dU_t\quad\Rightarrow\quad U_t=\frac{(\rho_p-\rho)gd^2}{18\mu}$$
For modest inertia, the empirical Schiller–Naumann correction is
$$C_D=\frac{24}{Re}\left(1+0.15Re^{0.687}\right).$$''')
    render_derivation(
        r"the settling law $U_t=(\rho_p-\rho)gd^{2}/18\mu$, including where buoyancy comes from",
        [
            (
                "Newton's second law for the particle, at the moment nothing accelerates",
                r"""
                A released particle speeds up until drag has grown to match the net downward
                pull; after that $m\,dU/dt=0$ **by definition of terminal**. So the terminal
                condition is a statics problem:
                $$\underbrace{W}_{\text{weight}}-\underbrace{F_b}_{\text{buoyancy}}
                -\underbrace{F_D}_{\text{drag}}=0$$
                Note this is an equilibrium, not an equation of motion: it says nothing about
                how long the particle takes to get there.
                """,
            ),
            (
                "Buoyancy is a pressure integral, not a separate force law",
                r"""
                It belongs in the *same* surface integral as drag. Hydrostatics gives
                $p=p_0-\rho g z$, and over a closed surface
                $$-\oint p\,\mathbf n\,dS=-\oint\nabla p\,dV=+\rho g V\,\mathbf e_{\text{up}}$$
                by the divergence theorem: the upward force equals the weight of displaced
                fluid, which is Archimedes derived rather than recalled. We separate it out
                only because it is the part of the pressure integral that survives when the
                fluid is *not* moving; Stokes' $2\pi\mu Ua$ is the extra piece caused by
                motion.
                """,
            ),
            (
                "Insert the three expressions",
                r"""
                With sphere volume $V=\pi d^{3}/6$ and Stokes drag from §9.2:
                $$\frac{\pi d^{3}}{6}\rho_p g-\frac{\pi d^{3}}{6}\rho g=3\pi\mu d\,U_t
                \;\Longrightarrow\;
                \frac{\pi d^{3}}{6}(\rho_p-\rho)g=3\pi\mu d\,U_t$$
                Only the density **difference** appears. A neutrally buoyant particle never
                settles, however large it is, and a particle lighter than the fluid rises with
                the same formula and a sign change.
                """,
            ),
            (
                r"Cancel and read the two powers of $d$",
                r"""
                Divide both sides by $\pi d$:
                $$\frac{d^{2}}{6}(\rho_p-\rho)g=3\mu U_t
                \;\Longrightarrow\;
                \boxed{U_t=\frac{(\rho_p-\rho)g\,d^{2}}{18\mu}}$$
                The $d^{2}$ is the physical heart of it: driving force grows as volume
                ($d^{3}$) while Stokes drag grows only as $d$ (a viscous force scales with
                size times velocity, not with area). That single power difference is why a
                $10\ \mu\text{m}$ particle settles a hundred times faster than a
                $1\ \mu\text{m}$ one, and why fine catalyst fines are so hard to remove.
                """,
            ),
            (
                "The result must be checked against the assumption that produced it",
                r"""
                $U_t$ was obtained from a drag law valid only for $\mathrm{Re}\ll1$, so the
                answer is not usable until you compute $\mathrm{Re}_t=\rho U_td/\mu$ from it
                and confirm it is still small. The lab above reports exactly that number and
                warns when it exceeds $0.1$. If it fails, the Schiller–Naumann correction
                makes the balance implicit in $U_t$ — the drag no longer scales linearly with
                velocity, so the equation must be solved numerically rather than rearranged.
                """,
            ),
        ],
    )
    st.markdown('### 9.4 Drag crisis · why a turbulent layer can reduce drag')
    render_svg(diagram_sphere_separation())
    st.markdown('As Reynolds number rises, a smooth sphere develops a separated wake. Near the drag crisis (often a few hundred thousand), transition within the boundary layer increases near-wall momentum transport. Separation moves downstream, the wake narrows, and pressure drag drops sharply even though skin friction increases. Surface roughness and free-stream turbulence shift the transition; there is no universal critical Reynolds number.')
    fig=go.Figure()
    x=np.logspace(-3,3,180)
    fig.add_trace(go.Scatter(x=x,y=24/x,name='Stokes · only Re ≪ 1',line=dict(dash='dash')))
    fig.add_trace(go.Scatter(x=x,y=[sphere_drag(v) for v in x],name='Schiller–Naumann · Re ≤ 1000'))
    fig.add_trace(go.Scatter(x=[1e3,1e4,1e5,2e5,3e5,4e5,1e6],y=[.44,.44,.47,.48,.2,.1,.18],name='Smooth-sphere crisis · schematic only',line=dict(dash='dot')))
    fig.update_layout(title='Sphere drag: viscous regime → wake regime → drag crisis',xaxis=dict(type='log',title='Sphere Reynolds number'),yaxis=dict(type='log',title='Drag coefficient CD'),height=440)
    apply_plotly_theme(fig); render_plot(fig,'sphere-drag')
    st.caption('The dotted high-Re curve illustrates the mechanism; it is not used by the force calculator and is not a design correlation. [NASA: drag of a sphere](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/drag-of-a-sphere/).')
    st.markdown('**Connect to practice.** Sedimentation of fine catalyst particles starts with gravity, buoyancy and drag; verify terminal Re afterward. Golf-ball dimples deliberately alter boundary-layer transition. Crossflow around heat-exchanger tubes involves cylinder wakes and tube-bank interactions, so a sphere correlation is unsuitable. Aerosol droplets may evaporate and change diameter while settling.')
