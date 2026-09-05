import math
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from src.ui.state import persistent_input
from src.units import get_fluid_state
from src.physics.gas_dynamics import sphere_drag
from src.svg_diagrams import diagram_sphere_forces, diagram_sphere_separation, render_svg
from src.ui.pedagogy import render_prose_and_latex as prose, render_plot
from src.theme import apply_plotly_theme


def render_tab_external_flow():
    st.markdown('### 8.1 From wall shear to wake drag')
    prose(r'''An immersed object feels both pressure and viscous traction. Far upstream the fluid is nearly uniform; a boundary layer forms on the object and may separate into a wake. Use the object's diameter for a sphere, and the **projected frontal area** in its drag coefficient.
$$F_D=\int_S(-p\mathbf n+\boldsymbol\tau\cdot\mathbf n)\cdot\mathbf e_U\,dS=\tfrac12\rho U^2C_D A,\quad A=\pi d^2/4,\quad Re_d=\rho Ud/\mu$$
A flat plate aligned with flow is often dominated by skin friction; a bluff sphere or cylinder often has substantial pressure drag. Their coefficient curves and reference areas are different. Pipe transition thresholds do not classify these flows.''')
    st.markdown('### 8.2 Stokes flow · a derivation for a sphere')
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
    st.markdown('### 8.3 Settling and finite-inertia drag lab')
    fluid = get_fluid_state(); rho, mu = fluid['rho'], fluid['mu']
    c1,c2,c3 = st.columns(3)
    diameter = persistent_input(c1.number_input, 'Sphere diameter [mm]', min_value=.001, value=.1, key='sphere_d')/1000
    speed = persistent_input(c2.number_input, 'Relative speed [m/s]', min_value=.000001, value=.001, format='%.6f', key='sphere_u')
    density = persistent_input(c3.number_input, 'Particle density [kg/m³]', min_value=.1, value=2500., key='sphere_rho')
    re = rho*speed*diameter/mu
    drag=3*math.pi*mu*diameter*speed
    terminal=(density-rho)*9.81*diameter**2/(18*mu)
    ret=rho*abs(terminal)*diameter/mu
    a,b,c=st.columns(3)
    a.metric('Re at entered speed',f'{re:.4g}'); b.metric('Stokes drag estimate',f'{drag:.3e} N'); c.metric('Stokes terminal velocity',f'{terminal:.4g} m/s')
    st.caption(f'Shared fluid: ρ = {rho:g} kg/m³, μ = {mu:g} Pa·s. Positive terminal velocity is downward. Terminal Re = {ret:.3g}; this is a self-consistency check, not a corrected settling solution.')
    if re > .1 or ret > .1:
        st.warning('At least one Stokes estimate is outside the conservative Re ≤ 0.1 creeping-flow range. Check finite-inertia drag before accepting it.')
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
    st.markdown('### 8.4 Drag crisis · why a turbulent layer can reduce drag')
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
