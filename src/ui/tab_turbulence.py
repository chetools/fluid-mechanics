"""UI module for Laminar vs. Turbulent flows: Diagrams, Theory, and Practical Trade-offs."""

import streamlit as st
from src.ui.state import persistent_input
from src.ui.pedagogy import render_plot

from src.svg_diagrams import (
    diagram_reynolds_experiment,
    diagram_laminar_vs_turbulent_profiles,
    diagram_law_of_the_wall,
    render_svg
)
from src.physics.turbulence import velocity_profile_comparison, law_of_the_wall
from src.physics.pipe_flow import (
    friction_factor_churchill,
    laminar_fanning_from_force_balance,
    straw_bundle_comparison,
)
from src.plotting import plot_laminar_turbulent_profiles, plot_pipe_profile_limits, plot_law_of_the_wall, plot_straw_bundle
from src.units import get_fluid_state
from src.ui.pedagogy import (
    render_objectives,
    render_what_to_notice,
    render_predict,
    render_self_check,
    render_callout,
    render_derivation,
    render_prose_and_latex,
    render_symbols,
)

def render_tab_turbulence():
    """Render comprehensive panel comparing laminar and turbulent flows."""
    fluid = get_fluid_state()
    st.markdown(
        """
        Flow regimes govern everything in fluid transport.
        Whether a fluid flows in smooth, orderly parallel sheets (**laminar flow**)
        or chaotic, three-dimensional swirling eddies (**turbulent flow**)
        dictates friction factors, heat and mass transfer coefficients, and pumping energy.

        **Scope.** Re = 2300 / 4000, $\\alpha = 2$, and the $1/7$ power law are
        **circular-pipe** results (Osborne Reynolds' apparatus). They are not
        the transition Re of a lid-driven cavity or a cylinder.
        """
    )
    render_objectives(
        [
            "State that 2300 is a pipe threshold, not a universal law.",
            "Derive $f_F = 16/\\mathrm{Re}$ from a cylindrical force balance and compare it to Moody.",
            "Decide whether packing a pipe with straws to stay laminar actually saves pump kW.",
            "Write Chilton–Colburn with the Fanning factor: $j = f_F/2 = f_D/8$.",
        ]
    )
    
    # -------------------------------------------------------------------------
    # PART 1: The Transition Experiment
    # -------------------------------------------------------------------------
    st.markdown("### 4.1 The Physics of Transition: Osborne Reynolds (1883)")
    st.markdown(
        """
        In his historic 1883 Manchester experiments, Osborne Reynolds injected a thin filament 
        of dyed water into the center of a glass pipe to observe flow structure.
        """
    )
    
    render_svg(diagram_reynolds_experiment())
    
    render_callout(
        r"""
        **The Physical Mechanism of Turbulent Transition**
        
        The Reynolds number represents the dimensionless ratio of **destabilizing inertial forces** to **stabilizing viscous damping**:
        $$\text{Re}_D = \frac{\text{Inertia}}{\text{Viscous Damping}} = \frac{\rho u D}{\mu} \quad \text{(circular pipe)}$$
        - **At low $\text{Re}_D < 2300$ in a pipe:** Viscous forces quench small perturbations. Streamlines stay parallel.
        - **At transitional $\text{Re}_D \in [2300, 4000]$ in a pipe:** Intermittent turbulent slugs or puffs.
        - **At high $\text{Re}_D > 4000$ in a pipe:** $(\mathbf{u}\cdot\nabla)\mathbf{u}$ overwhelms damping. In *three* dimensions, vortex stretching feeds a cascade down to Kolmogorov scales.
        A flat plate, a cylinder, and a lid-driven cavity each have their own critical Re; do not import 2300 there.
        """
    )

    render_derivation(
        r"where $\rho u D/\mu$ comes from — it is a ratio of two terms in Newton's law",
        [
            (
                "Start from the momentum balance, not from a definition",
                r"""
                Tab 6 writes Newton's second law for one lump of fluid, per unit volume:
                $$\rho\underbrace{\frac{\partial\mathbf{u}}{\partial t}}_{\text{unsteady}}
                + \rho\underbrace{(\mathbf{u}\cdot\nabla)\mathbf{u}}_{\text{inertia}}
                = -\nabla p + \underbrace{\mu\nabla^{2}\mathbf{u}}_{\text{viscous}}$$
                A small wobble in the dye filament grows or dies according to which of
                the two labelled terms wins. Nothing else in the equation can decide it:
                pressure only enforces continuity, and the unsteady term is what we are
                asking about.
                """,
            ),
            (
                "Size each term geometrically, using the pipe itself as the ruler",
                r"""
                In a pipe of diameter $D$ carrying mean speed $U$, the velocity goes from
                $0$ at the wall to about $U$ at the centre — a change of order $U$ across
                a distance of order $D$. So *every* cross-stream derivative is of order
                $1/D$, and $\mathbf{u}$ itself is of order $U$:
                $$\rho(\mathbf{u}\cdot\nabla)\mathbf{u}\ \sim\ \rho\frac{U^{2}}{D},
                \qquad
                \mu\nabla^{2}\mathbf{u}\ \sim\ \mu\frac{U}{D^{2}}$$
                These are not values of the terms. They are the largest size each term
                *can* have once the geometry and the flow rate are fixed — which is all a
                competition between them requires.
                """,
            ),
            (
                "Divide. Everything cancels except one group",
                r"""
                $$\frac{\text{inertia}}{\text{viscous}}
                \sim \frac{\rho U^{2}/D}{\mu U/D^{2}} = \frac{\rho U D}{\mu} = \mathrm{Re}_D$$
                $\mathrm{Re}$ is therefore not a quantity someone chose to define. It is
                what survives when you ask Newton's law which of its two transport terms
                is bigger, and the answer is forced to be dimensionless because a ratio of
                two forces has no units to keep.
                """,
            ),
            (
                "Read the same group as a race between two clocks",
                r"""
                Momentum spreads sideways by viscous diffusion in a time $t_\nu\sim D^{2}/\nu$
                (the diffusion law of Tab 8), and the flow carries a fluid particle one pipe
                diameter downstream in $t_{\mathrm{flow}}\sim D/U$. Their ratio is the same
                number:
                $$\frac{t_\nu}{t_{\mathrm{flow}}} = \frac{D^{2}/\nu}{D/U} = \frac{UD}{\nu} = \mathrm{Re}_D$$
                At large $\mathrm{Re}$ a disturbance is swept away and stretched long before
                viscosity can smear it out, so it survives, tangles, and becomes turbulence.
                At small $\mathrm{Re}$ viscosity erases it within one pipe diameter of travel.
                """,
            ),
            (
                "This is why 2300 is a pipe number and not a law of nature",
                r"""
                Step 2 used $D$ because a pipe offers exactly one length. A flat plate offers
                the distance $x$ from its leading edge, a cylinder its diameter, this course's
                lid-driven cavity its side. Each choice rescales the same ratio by a different
                factor, so the *group* transfers to every geometry and the *critical value*
                does not.
                """,
            ),
        ],
    )

    st.markdown("### 4.1b Laminar force balance → $f_F = 16/\\mathrm{Re}$")
    st.markdown(
        r"""
        Tab 1 booked friction as lost mechanical energy. Here we *compute* it
        for fully developed laminar flow in a round pipe, then compare to the
        Moody laminar line (Tab 2).
        """
    )
    with st.expander("🔍 Force balance on a cylindrical fluid core (no skipped algebra)", expanded=False):
        render_prose_and_latex(
            r"""
            Take a coaxial plug of radius $r$ and length $L$. Steady axial flow,
            no acceleration, so $\sum F_z = 0$:
            $$\underbrace{\Delta p \cdot \pi r^2}_{\text{net pressure}}
            = \underbrace{\tau(r)\cdot 2\pi r L}_{\text{shear on the jacket}}$$
            $$\tau(r) = \frac{r}{2}\frac{\Delta p}{L}$$
            At the wall $r = R = D/2$, $\tau_w = (D/4)(\Delta p/L)$.
            Newtonian constitutive law $\tau = \mu (-du/dr)$:
            $$-\mu \frac{du}{dr} = \frac{r}{2}\frac{\Delta p}{L}$$
            Integrate with $u(R)=0$:
            $$u(r) = \frac{1}{4\mu}\frac{\Delta p}{L}(R^2 - r^2)$$
            Mean speed $u_{\mathrm{avg}} = u_{\max}/2 = (D^2/32\mu)(\Delta p/L)$
            (Hagen–Poiseuille). Now divide the wall stress by the dynamic pressure, which
            is the **Fanning** definition $f_F = \tau_w/(\tfrac12\rho u^2)$:
            $$f_F = \frac{\Delta p D}{2L\rho u^2} = \frac{16\mu}{\rho u D} = \frac{16}{\mathrm{Re}}$$
            Darcy is $f_D = 4f_F = 64/\mathrm{Re}$. Same physics, factor of four.
            """
        )
        render_symbols(
            [
                (r"\Delta p", "pressure drop over length $L$ (Pa)."),
                (r"r", "radius of the coaxial fluid plug (m). Wall is $r=R=D/2$."),
                (r"\tau(r)", r"axial shear on the cylindrical jacket (Pa). At the wall, $\tau_w=(D/4)(\Delta p/L)$."),
                (r"\mu", "dynamic viscosity (Pa·s). Sidebar fluid."),
                (r"u(r)", "axial speed of the Hagen–Poiseuille parabola (m/s)."),
                (r"f_F", r"Fanning friction factor, used throughout this app. This force balance gives $f_F=16/\mathrm{Re}$ (Darcy $f_D=4f_F=64/\mathrm{Re}$)."),
                (r"\mathrm{Re}", r"$\rho u_{\mathrm{avg}} D/\mu$ with $u_{\mathrm{avg}}$ the area-mean speed."),
            ]
        )
    re_cmp = persistent_input(st.select_slider,
        "Compare f_F(Re) at",
        options=[200, 500, 1000, 1500, 2000, 2300, 4000, 1e4],
        value=1000,
        key="lam_f_re",
    )
    f_force = laminar_fanning_from_force_balance(float(re_cmp))
    f_moody = friction_factor_churchill(float(re_cmp), 0.0)
    col_f1, col_f2, col_f3 = st.columns(3)
    col_f1.metric("Force-balance f_F = 16/Re", f"{f_force:.4f}")
    col_f2.metric("Churchill / Moody f_F", f"{f_moody:.4f}")
    col_f3.metric("Relative difference", f"{abs(f_moody - f_force)/f_force*100:.2f} %")
    if re_cmp <= 2300:
        st.success("Below Re = 2300 the two expressions agree: Moody's laminar line *is* the force balance.")
    else:
        st.warning(
            "Above transition the force balance assumed a parabolic, laminar τ(r). "
            "Turbulent eddy stress raises f_F well above 16/Re."
        )

    # -------------------------------------------------------------------------
    # PART 2: Velocity Profile Comparison
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 4.2 Pipe profiles: the power-law approximation and a smooth mean")
    st.markdown(
        """
        Turbulent momentum exchange flattens the **time-averaged** velocity profile
        across the pipe core. A fully developed, axisymmetric mean profile is still
        smooth at the centre, and its thin viscous wall layer has a finite gradient.
        The dashed power law below is retained to show where an economical fit fails.
        """
    )
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        u_mean_input = persistent_input(st.slider, "Mean Flow Velocity u_avg [m/s]", min_value=0.5, max_value=5.0, value=1.5, step=0.1, key="tab_turbulence_mean_flow_velocity_u_avg_m_s")
    with col_v2:
        re_turb_prof = persistent_input(st.select_slider,
            "Turbulent Reynolds Number",
            options=[5000, 20000, 50000, 100000, 500000, 1000000],
            value=50000, key="tab_turbulence_turbulent_reynolds_number")
        
    prof_res = velocity_profile_comparison(pipe_radius=0.05, u_avg=u_mean_input, reynolds=re_turb_prof)
    render_svg(diagram_laminar_vs_turbulent_profiles(prof_res))
    render_callout(
        title="The 1/7 rule has two endpoint defects",
        body=r"""
        The dashed curve is the unmodified $u/u_{max}=(1-r/R)^{1/n}$ fit
        ($n=7$ at the default Reynolds number). It has a **nonzero radial slope at
        the centre**, making a cusp when mirrored, and an **infinite slope at the wall**.
        Neither is physical. Do not infer wall shear by differentiating this fit.

        The solid blue curve is a **smooth mean sketch from an illustrative eddy-viscosity
        model**, not measured data or a calibrated design correlation. It satisfies
        centreline symmetry, no slip and a finite viscous wall gradient. Its assumed
        eddy viscosity is stated in the derivation below. The green parabola is a
        laminar reference shape shown at the same mean speed; the selected Reynolds
        number sets the turbulent curves.
        """,
    )
    
    col_pr1, col_pr2, col_pr3 = st.columns(3)
    col_pr1.metric("Laminar centre speed", f"{prof_res['u_max_lam']:.3f} m/s")
    col_pr2.metric("Power-law centre speed", f"{prof_res['u_max_turb']:.3f} m/s")
    col_pr3.metric("Smooth-sketch centre speed", f"{prof_res['u_max_smooth']:.3f} m/s")
    st.dataframe([
        {"Profile": label, "Kinetic-energy factor α": prof_res[f"alpha_{suffix}"],
         "Momentum factor β": prof_res[f"beta_{suffix}"]}
        for label, suffix in (("Laminar reference", "lam"),
                              (f"1/{prof_res['n_exp']:g} approximation", "turb"),
                              ("Smooth mean sketch", "smooth"))
    ], hide_index=True, width="stretch")
    st.caption(
        "Each coefficient is integrated from its own profile. The energy and momentum "
        "calculators elsewhere retain the power-law approximation; the smooth sketch is illustrative. "
        "Here Re and mean speed are independent shape controls at R = 0.05 m, so their "
        "implied kinematic viscosity is 2R × mean speed / Re; this comparison does not use the sidebar fluid."
    )
    st.caption(
        "α = 2 and u_avg/u_max = 1/2 are **circular pipe**. A plane channel has "
        "u_avg/u_max = 2/3 and α = 54/35 ≈ 1.543 for pure plane Poiseuille "
        "(Tab 8 integrates the actual Couette–Poiseuille profile)."
    )
    render_what_to_notice(
        "All three curves have the same area-mean speed. The blue curve rounds smoothly "
        "through the centre; the dashed tip is the power law's defect. Near the wall, "
        "the blue model approaches a finite slope while the dashed law does not."
    )
    
    fig_prof = plot_laminar_turbulent_profiles(prof_res)
    render_plot(fig_prof, key="tab_turbulence-fig_prof")
    render_plot(plot_pipe_profile_limits(prof_res), key="turbulence-profile-limits")
    st.caption(
        "The core inset turns the axes so the centreline defect is easier to see. "
        "The wall inset resolves the first five wall units of the smooth sketch. "
        "On the full-diameter plot that viscous layer is too thin to judge reliably."
    )
    render_derivation(
        "Why the centre is smooth, and how the blue sketch is constructed",
        [
            (
                "Apply symmetry before choosing a curve",
                r"""
                A smooth axisymmetric mean has no preferred radial direction at the
                axis. Opposite sides therefore join with zero radial gradient:
                $$\left.\frac{du}{dr}\right|_{r=0}=0$$
                Differentiating the power law instead gives
                $$\frac{du}{dr}=-\frac{u_{max}}{nR}(1-r/R)^{1/n-1}$$
                At $r=0$ this is nonzero; at $r=R$ it diverges for $n>1$.
                Its finite area integrals can be useful even though these local
                gradients are wrong. A plotting spline would conceal the defect.
                """,
            ),
            (
                "Keep molecular stress in the pipe momentum balance",
                r"""
                Section 4.1b's cylindrical balance gives total shear magnitude
                $\tau_{tot}=\tau_w r/R$. For the decreasing radial velocity define
                $q=-du/dr\ge0$ and $u_\tau=\sqrt{\tau_w/\rho}$.
                Model the turbulent contribution with an eddy viscosity $\nu_t$,
                while retaining molecular viscosity $\nu=\mu/\rho$:
                $$(\nu+\nu_t)q=u_\tau^2\eta,\qquad\eta=r/R$$
                This is a closure assumption, not an exact turbulence solution.
                At the centre its right-hand side vanishes, so $q=0$. At the wall
                turbulence must vanish; then $q_w=u_\tau^2/\nu$ is finite.
                """,
            ),
            (
                "State the illustrative eddy viscosity instead of hiding a smoothing rule",
                r"""
                Choose an effective mixing scale that behaves like wall distance nearby
                and is even and bounded through the core:
                $$d/R=(1-\eta^2)(1+2\eta^2)/6,\qquad
                E=\frac{\nu_t}{\nu}=0.41\,Re_\tau(d/R)
                \left[1-\exp\left(-\frac{Re_\tau(d/R)}{26}\right)\right]^2$$
                Here $Re_\tau=u_\tau R/\nu$. The constants and this particular
                outer continuation define the teaching sketch; they have not been
                fitted to pipe data. The damping drives $\nu_t$ to zero at the wall;
                in the core it stays finite and even in the signed diameter coordinate.
                With $S=qR/u_\tau$, the total-shear balance gives
                $$S=\frac{Re_\tau\eta}{1+E}$$
                Thus $S(0)=0$ with a smooth parabolic core to leading order, while
                $S(1)=Re_\tau$ gives a finite viscous wall gradient. Away from the
                wall damping, $\nu_t$ grows approximately as $0.41u_\tau y$, producing
                a logarithmic region when molecular stress becomes small.
                """,
            ),
            (
                "Integrate from no slip, then match the requested bulk flow",
                r"""
                The wall fixes $u^+(1)=0$, so integrate the gradient inward:
                $$u^+(\eta)=\int_\eta^1S(t)\,dt,\qquad
                \bar u^+=2\int_0^1u^+(\eta)\eta\,d\eta$$
                The same circular-area weighting used for flow rate then relates
                the friction Reynolds number to the specified bulk Reynolds number:
                $$Re_D=2Re_\tau\bar u^+$$
                The app solves this equation for $Re_\tau$, rescales to the selected
                mean speed, and integrates this curve's own energy and momentum
                corrections. Smooth-wall, steady, fully developed assumptions apply;
                transition, roughness and developing flow are not modelled.
                """,
            ),
        ],
    )
    st.caption(
        "References: [power-law limitations]"
        "(https://www-mdp.eng.cam.ac.uk/web/library/enginfo/aerothermal_dvd_only/aero/fprops/pipeflow/node22.html) "
        "and [mixing-length models for full pipe profiles]"
        "(https://doi.org/10.1017/jfm.2019.669). The blue sketch uses the explicit teaching closure above."
    )
    
    render_derivation(
        r"the kinetic-energy correction $\alpha$, and why it is exactly $2$ for a laminar pipe",
        [
            (
                "Energy rides on mass, so the flux must be integrated, not averaged",
                r"""
                Look at one small patch $dA$ of the cross-section. The mass crossing it each
                second is $\rho u\,dA$, and **each kilogram of that mass** carries $u^{2}/2$
                joules of kinetic energy. Multiply, then add up the patches:
                $$\dot{E}_k=\int_A \tfrac{1}{2}\rho u^{2}\,(u\,dA)=\int_A \tfrac{1}{2}\rho u^{3}\,dA$$
                The cube is not a typo. One power of $u$ comes from *how much mass* passes,
                two from *how fast that mass is moving*.
                """,
            ),
            (
                "The one-dimensional balance we want to write cannot see the profile",
                r"""
                Tab 1's energy equation carries a single number per section, so it wants to
                say $\tfrac{1}{2}\rho\bar{u}^{3}A$ with $\bar{u}=Q/A$. That is a different
                quantity: the mean of a cube exceeds the cube of the mean unless the profile
                is perfectly flat. Fast fluid at the centre contributes to $\dot{E}_k$ in
                proportion to $u^{3}$ while contributing to $\bar{u}$ only in proportion to
                $u$, so a peaked profile always carries **more** kinetic energy than its mean
                speed suggests.
                """,
            ),
            (
                "Name the discrepancy instead of hiding it",
                r"""
                Define $\alpha$ as exactly the factor that repairs the substitution:
                $$\dot{E}_k=\alpha\left(\tfrac{1}{2}\rho\bar{u}^{3}A\right),
                \qquad \alpha\equiv\frac{1}{A}\int_A\left(\frac{u}{\bar{u}}\right)^{3}dA$$
                This is a definition, so it is exact for any profile. Because $u\mapsto u^{3}$
                is convex, $\alpha\ge 1$ always, with equality only for plug flow. Dropping
                $\alpha$ therefore never errs on the safe side — it always understates the
                velocity head.
                """,
            ),
            (
                "Evaluate it on the parabola the force balance already gave us",
                r"""
                Section 4.1b integrated the shear balance to $u(r)=u_{\max}(1-r^{2}/R^{2})$ with
                $u_{\max}=2\bar{u}$; nothing new is assumed here. The area element of a round
                pipe is a thin annulus, $dA=2\pi r\,dr$ — the geometric step people skip.
                Put $\eta=r/R$ so $dA=2\pi R^{2}\eta\,d\eta$ and $A=\pi R^{2}$:
                $$\alpha=\left(\frac{u_{\max}}{\bar{u}}\right)^{3}\cdot 2\int_{0}^{1}(1-\eta^{2})^{3}\,\eta\,d\eta$$
                Substituting $s=\eta^{2}$ turns that integral into
                $\tfrac{1}{2}\int_{0}^{1}(1-s)^{3}ds=\tfrac{1}{8}$, so the bracket is
                $2\times\tfrac{1}{8}=\tfrac{1}{4}$, while $(u_{\max}/\bar{u})^{3}=2^{3}=8$:
                $$\alpha_{\text{laminar}}=8\times\tfrac{1}{4}=2\quad\text{exactly}$$
                The $2$ is a property of the parabola, not a measured coefficient.
                """,
            ),
            (
                "Integrate the retained power-law approximation",
                r"""
                With the empirical $u/u_{\max}=(1-r/R)^{1/7}$, the same annular integral
                (substitute $s=1-\eta$) gives $\bar{u}/u_{\max}=2(\tfrac{7}{8}-\tfrac{7}{15})=\tfrac{49}{60}$ and
                $$\alpha_{\text{turbulent}}=\left(\frac{60}{49}\right)^{3}\cdot 2\left(\tfrac{7}{10}-\tfrac{7}{17}\right)
                =\left(\frac{60}{49}\right)^{3}\frac{49}{85}\approx 1.06$$
                The table above labels this as the power-law approximation and reports
                the blue sketch's integral separately. Neither coefficient is a universal
                turbulent constant. Here $n=7$; the selectable empirical exponent changes
                the dashed curve and its coefficients at other Reynolds numbers.
                """,
            ),
            (
                "The same argument, applied to momentum instead of energy",
                r"""
                A momentum balance transports $u$ per kilogram rather than $u^{2}/2$, so the
                identical reasoning gives the **momentum** correction
                $\beta=(1/A)\int(u/\bar{u})^{2}dA$, which works out to $4/3$ for the parabola.
                Energy and momentum need *different* corrections because they weight the
                profile by different powers. Never reuse one for the other.
                """,
            ),
            (
                "What this costs in practice",
                r"""
                In a laminar line — polymer melt, heavy crude, a capillary — writing
                $\alpha=1$ halves the velocity head, a $100\%$ error in that term. In a
                turbulent line $\alpha\approx1.06$ is usually buried inside the uncertainty
                of $h_f$, which is why the shortcut became a habit. Both statements are
                **circular-pipe** results: a plane slit has $\bar{u}/u_{\max}=2/3$ and
                $\alpha=54/35\approx1.54$ (Tab 8).
                """,
            ),
        ],
        symbols=[
            (
                r"\alpha",
                r"kinetic-energy correction $\alpha=(1/A)\int(u/\bar{u})^3\,dA$. "
                "Not an angle, not thermal diffusivity, not Tab 6's angular acceleration $\\alpha_z$. "
                "Circular pipe: $\\alpha=2$ laminar, $\\alpha\\approx 1.06$ turbulent (integrated).",
            ),
            (r"\beta", r"momentum correction $(1/A)\int(u/\bar{u})^2\,dA$; $4/3$ for the laminar parabola."),
            (r"\dot{E}_k", r"true kinetic-energy flux through the cross-section (W)."),
            (r"\bar{u}", r"area-mean speed $Q/A$ (m/s)."),
            (r"dA=2\pi r\,dr", "annular area element — the right ruler for a round pipe."),
        ],
    )

    # -------------------------------------------------------------------------
    # PART 3: Law of the Wall
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 4.3 The Universal Law of the Wall")
    render_prose_and_latex(
        """
        The flow near any solid boundary is governed by inner wall variables scaled by the 
        **friction velocity** $u_\\tau = \\sqrt{\\tau_{\\text{wall}} / \\rho}$:
        $$y^+ = \\frac{y u_\\tau}{\\nu}, \\quad u^+ = \\frac{u}{u_\\tau}$$
        """
    )
    
    render_svg(diagram_law_of_the_wall())

    render_derivation(
        r"why the near-wall profile must be a straight line, then a logarithm",
        [
            (
                "The near-wall stress is constant — and that is geometry, not modelling",
                r"""
                The cylindrical force balance of §4.1b already gave the shear at any radius,
                $\tau(r)=(r/2)(\Delta p/L)$, with no assumption about laminar or turbulent.
                Measure distance from the wall instead, $y=R-r$:
                $$\tau(y)=\tau_w\left(1-\frac{y}{R}\right),\qquad \tau_w=\frac{R}{2}\frac{\Delta p}{L}$$
                For $y/R<0.05$ the stress is within $5\%$ of $\tau_w$. So a thin skin at the
                wall lives in an environment of **constant** shear stress, whatever the core
                is doing. That is what lets the wall layer have a universal life of its own.
                """,
            ),
            (
                "Constant stress supplies exactly one velocity scale",
                r"""
                Inside that skin the fluid knows only $\tau_w$, $\rho$, $\nu$ and how far it is
                from the wall. Of these, $\tau_w/\rho$ is the only combination with units of
                $(\text{m/s})^{2}$, so
                $$u_\tau\equiv\sqrt{\tau_w/\rho}$$
                is not a definition of convenience: it is the *only* speed the wall can build.
                Read it physically as the rate at which the wall drains momentum from the
                stream — a fast-eating wall makes a big $u_\tau$.
                """,
            ),
            (
                "Two variables, two dimensions, one universal curve",
                r"""
                The list $u,\;y,\;u_\tau,\;\nu$ has four quantities and two dimensions
                (length, time), so Buckingham (Tab 3) leaves $4-2=2$ groups:
                $$u^{+}=\frac{u}{u_\tau},\qquad y^{+}=\frac{y\,u_\tau}{\nu}$$
                and therefore $u^{+}=F(y^{+})$ — *one* curve for every pipe, fluid and flow
                rate. Notice that $y^{+}$ is itself a Reynolds number, built on the distance
                to the wall: it says how far out you are in units of the viscous thickness.
                """,
            ),
            (
                "Very close in, viscosity carries all of the stress",
                r"""
                An eddy at height $y$ cannot be larger than $y$ — the wall is in the way — and
                below a few viscous units such an eddy is damped out before it can turn over.
                So for $y^{+}\lesssim5$ the whole of the (constant) stress is molecular:
                $$\mu\frac{du}{dy}=\tau_w
                \;\Longrightarrow\; u=\frac{\tau_w}{\mu}y=\frac{u_\tau^{2}}{\nu}y
                \;\Longrightarrow\; \boxed{u^{+}=y^{+}}$$
                A straight line of unit slope, forced by no-slip at $y=0$ plus constant stress.
                No empirical constant enters.
                """,
            ),
            (
                "Far enough out, viscosity is irrelevant and only $y$ itself is left",
                r"""
                For $y^{+}\gtrsim30$ the same $\tau_w$ is carried by eddies rather than
                molecules, so $\nu$ drops out of the problem. But $y$ is then the **only**
                length available, and the largest eddy that fits at height $y$ has size
                proportional to $y$. That is Prandtl's mixing length, $\ell=\kappa y$. Such an
                eddy exchanges fluid over a distance $\ell$, so it carries a velocity
                difference $\ell\,du/dy$, and the momentum flux it produces is
                $$\tau=\rho\left(\ell\frac{du}{dy}\right)^{2}=\tau_w
                \;\Longrightarrow\;\frac{du}{dy}=\frac{u_\tau}{\kappa y}$$
                """,
            ),
            (
                "Integrate: a layer with no length scale of its own must give a logarithm",
                r"""
                $$\int du=\frac{u_\tau}{\kappa}\int\frac{dy}{y}
                \;\Longrightarrow\; u=\frac{u_\tau}{\kappa}\ln y+C
                \;\Longrightarrow\; \boxed{u^{+}=\frac{1}{\kappa}\ln y^{+}+B}$$
                The logarithm is not a curve fit. $du/dy\propto1/y$ is the only gradient a
                region with no intrinsic length can have, and $1/y$ integrates to $\ln y$.
                What *is* empirical is $\kappa\approx0.41$, read off the measured slope, and
                $B\approx5.0$, the integration constant fixed by matching this line back down
                through the buffer layer to $u^{+}=y^{+}$.
                """,
            ),
            (
                "The buffer layer is a blend, not a third law",
                r"""
                Between $y^{+}=5$ and $30$ neither limit is legitimate: molecular and eddy
                stress are comparable, so the two derivations above each drop a term that is
                not small. The plot bridges them; no separate physics is being claimed.
                """,
            ),
        ],
        closing=r"""
        **Where the $1/7$ power law of §4.2 came from.** $u/u_{\max}=(1-r/R)^{1/7}$ is an
        algebraic *fit* that tracks the logarithm over about a decade of $y^{+}$ and, unlike
        the log, integrates in closed form — which is why §4.2 could get $\bar{u}/u_{\max}=49/60$
        from it. Blasius' smooth-pipe friction fit,
        $f_F=0.0791\,\mathrm{Re}^{-1/4}$ (or $f_D=0.3164\,\mathrm{Re}^{-1/4}$),
        is a separate empirical approximation, not the wall derivative of this profile.
        A fixed exponent does not fit all Reynolds numbers. The power law is not a derivation,
        and it is wrong at both ends: differentiating it gives an *infinite* shear at the wall
        (where the real profile is the linear $u^{+}=y^{+}$) and a non-zero slope on the
        centreline (where symmetry demands zero).
        """,
    )

    st.caption(
        "κ ≈ 0.41 and B ≈ 5.0 are **empirical constants** for a smooth wall, not operating "
        "conditions like Re. Moving them redraws the log law; it does not change the flow you specified."
    )
    show_const = persistent_input(st.checkbox, "Explore literature-constant sensitivity (κ, B)", value=False, key="tab_turbulence_explore_literature_constant_sensitivity_b")
    if show_const:
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            karman_k = persistent_input(st.slider, "von Kármán Constant κ", min_value=0.35, max_value=0.45, value=0.41, step=0.01, key="tab_turbulence_von_k_rm_n_constant")
        with col_w2:
            wall_b = persistent_input(st.slider, "Log-Law Intercept Constant B", min_value=4.0, max_value=6.0, value=5.0, step=0.1, key="tab_turbulence_log_law_intercept_constant_b")
    else:
        karman_k, wall_b = 0.41, 5.0

    wall_res = law_of_the_wall(kappa=karman_k, B=wall_b)
    render_what_to_notice(
        "y⁺ < 5 is linear (viscous sublayer). y⁺ > 30 is the log overlap. "
        "The green curve is Spalding's interpolation — a blend, not a third law."
    )
    fig_wall = plot_law_of_the_wall(wall_res)
    render_plot(fig_wall, key="tab_turbulence-fig_wall")

    # -------------------------------------------------------------------------
    # PART 4: Practical ChemE Trade-off
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 4.4 Chemical Engineering Practical Trade-Off: Heat/Mass Transfer vs. Pumping Penalty")
    
    col_to1, col_to2 = st.columns(2)
    with col_to1:
        render_callout(
            """
            **✅ Why We Want Turbulence: Transport Enhancement**
            
            In chemical reactors, bioreactors, and heat exchangers, rapid mixing is essential:
            - **Heat Transfer:** Laminar pipe heat transfer is strictly conduction-limited (Nusselt number $\\text{Nu} = 3.66$). Turbulent heat transfer scales as $\\text{Nu} \\sim \\text{Re}^{0.8} \\cdot \\text{Pr}^{1/3}$ (Dittus–Boelter), increasing heat transfer rates by **10 to 100-fold**!
            - **Mass Transfer:** Turbulent eddy diffusivity $\\epsilon_M$ is 1,000 to 100,000 times larger than molecular diffusion coefficients.
            - **Chilton–Colburn Analogy:** $j_H = j_D = f_F / 2 = f_D / 8$.
              This app reports **Fanning** $f_F$ throughout (Tab 2), so $f_F/2$ is the form to use.
              Writing $f/2$ with a Moody (Darcy) $f$ is a factor-of-four error.
            """
        )
    with col_to2:
        render_callout(
            """
            **⚠️ The Pumping Penalty: Hydraulic Cost**
            
            Turbulence comes at a severe energetic price:
            - **Pressure Drop Scaling:**
              - In laminar flow: $\\Delta p \\propto u^{1.0}$ (linear with velocity).
              - In turbulent flow: $\\Delta p \\propto u^{1.75} \\text{ to } u^{2.0}$ (quadratic with velocity).
            - **Pumping Power:** Power scales as $P = Q \\cdot \\Delta p \\propto u^{3.0}$! Doubling flow velocity in a turbulent line requires **8 times more pump horsepower**.
            - **Process Optimization:** Chemical engineers must balance heat transfer area vs. operating electricity cost.
            """
        )

    render_derivation(
        r"where the exponents $1.75$, $2$ and $3$ actually come from",
        [
            (
                "Everything hangs on the friction factor, which has $u$ in two places",
                r"""
                Tab 2 defines the friction factor by
                $$\Delta p=4f_F\frac{L}{D}\frac{\rho u^{2}}{2}$$
                and this is a *definition*, so it cannot by itself predict an exponent. The
                velocity enters twice: explicitly as $u^{2}$, and hidden inside
                $f_F(\mathrm{Re})$, because $\mathrm{Re}=\rho u D/\mu$ moves when $u$ moves.
                The observed exponent is the sum of the two.
                """,
            ),
            (
                "Laminar: the hidden dependence cancels one power exactly",
                r"""
                §4.1b derived $f_F=16/\mathrm{Re}=16\mu/(\rho u D)$. Substitute it and watch
                the $\rho$ and one power of $u$ disappear:
                $$\Delta p=4\cdot\frac{16\mu}{\rho u D}\cdot\frac{L}{D}\cdot\frac{\rho u^{2}}{2}
                =\frac{32\,\mu L u}{D^{2}}\ \propto\ u^{1}$$
                Linear in velocity, and independent of density — which is the signature of a
                flow where inertia plays no role at all. It is also Hagen–Poiseuille written
                a second way, so the two routes agree, as they must.
                """,
            ),
            (
                "Turbulent smooth: Blasius supplies a fractional power",
                r"""
                For a smooth wall up to about $\mathrm{Re}=10^{5}$, measurement gives
                $f_F\approx0.0791\,\mathrm{Re}^{-1/4}$, so $f_F\propto u^{-1/4}$ and
                $$\Delta p\propto u^{-1/4}\cdot u^{2}=u^{7/4}=u^{1.75}$$
                The exponent is $2$ *reduced* by a quarter, because faster flow is slightly
                more slippery per unit velocity head. It is empirical, not derived: the
                $-1/4$ is the exponent in the measured smooth-pipe friction fit;
                it cannot be obtained by evaluating the power-law velocity gradient at the wall.
                """,
            ),
            (
                "Fully rough: the hidden dependence vanishes, and you get a clean square",
                r"""
                At high $\mathrm{Re}$ on a rough wall the Moody curves flatten,
                $f_F\to f_F(\varepsilon/D)$ with no $\mathrm{Re}$ left in it. Then nothing
                is hidden and $\Delta p\propto u^{2}$ exactly. Physically: the drag is now set
                by pressure forces on roughness elements, and form drag scales with dynamic
                pressure. This is the upper end of the quoted $1.75$–$2.0$ range.
                """,
            ),
            (
                "Power multiplies by one more power of $u$",
                r"""
                Hydraulic power is $P=Q\,\Delta p$ and, at fixed pipe size, $Q=uA\propto u$:
                $$P\propto u\cdot u^{1.75\text{–}2}=u^{2.75\text{–}3}$$
                Doubling the velocity in an existing turbulent line therefore costs
                $2^{2.75}\approx6.7$ to $2^{3}=8$ times the pumping power. The familiar
                "$8\times$" is the rough-wall end of that band.
                """,
            ),
            (
                "State what was held fixed, or the scaling misleads",
                r"""
                Every exponent above assumes **the same pipe and the same fluid**, with only
                the velocity changed. Debottleneck by enlarging the pipe instead and the
                accounting inverts: at fixed $Q$, $u\propto D^{-2}$ and turbulent
                $\Delta p\propto D^{-5}$ approximately, so a modest diameter increase is
                usually far cheaper than any amount of pump. That comparison, not the
                exponent alone, is the design decision.
                """,
            ),
        ],
    )

    render_self_check(
        "turb_self_check_colburn",
        "Chilton–Colburn is j = f/2. Which f is that?",
        ["Darcy f_D (Moody chart)", "Fanning f_F = f_D/4", "Either, they differ only by Re"],
        "Fanning f_F = f_D/4",
        "j_H = f_F/2 = f_D/8. This app reports Fanning; published Moody charts plot Darcy.",
    )

    st.markdown("---")
    st.markdown("### 4.5 The straw-pipe question")
    render_prose_and_latex(
        r"""
        Turbulence raises $f_F$ and $\Delta p \propto u^{1.75\text{–}2}$. A natural
        thought: **fill the pipe with $N$ capillary “straws”** so each lumen stays
        laminar ($\mathrm{Re}_d < 2300$), at the **same total** $Q$ and the same
        outer diameter $D$.

        Geometry: packing fraction $\phi$ (hexagonal $\approx 0.91$; we default 0.85),
        $N d^2 = \phi D^2$, so $d = D\sqrt{\phi/N}$. Each straw carries $Q/N$.
        Laminar Hagen–Poiseuille on each lumen:
        $$\Delta p = \frac{128\mu L (Q/N)}{\pi d^4} \propto \frac{N}{\phi^2}$$
        Shrinking $d$ hurts as $d^4$ in the denominator. Staying laminar is not free.
        """
    )
    render_derivation(
        r"the bundle penalty $\Delta p\propto N/\phi^{2}$, from Hagen–Poiseuille and packing geometry",
        [
            (
                r"Rewrite §4.1b in terms of flow rate, and see where $d^{4}$ comes from",
                r"""
                The force balance gave a mean speed, $\bar{u}=(d^{2}/32\mu)(\Delta p/L)$.
                A pump is asked for a *flow rate*, so multiply by the bore area
                $A=\pi d^{2}/4$:
                $$Q=\bar{u}A=\frac{\pi d^{4}}{128\,\mu L}\Delta p
                \qquad\Longleftrightarrow\qquad
                \Delta p=\frac{128\,\mu L\,Q}{\pi d^{4}}$$
                The fourth power is two effects multiplied. **Two powers from the area:**
                a narrower tube must run the same $Q$ faster, as $1/d^{2}$. **Two more from
                the gradient:** that higher speed has to fall to zero across a shorter gap,
                so the shear $\mu\,du/dy$ rises again as $1/d^{2}$.
                """,
            ),
            (
                "Pack the shell — geometry fixes the bore you are allowed",
                r"""
                Let $\phi$ be the fraction of the shell cross-section that is open lumen
                (hexagonal close packing of thin-walled circles tops out near $0.91$).
                Equating open area to packed area:
                $$N\frac{\pi d^{2}}{4}=\phi\frac{\pi D^{2}}{4}
                \;\Longrightarrow\; N d^{2}=\phi D^{2}
                \;\Longrightarrow\; d=D\sqrt{\phi/N}$$
                So the bore falls only as $1/\sqrt{N}$ — reassuringly slow, until you
                remember Step 1 raises it to the fourth power.
                """,
            ),
            (
                "Split the duty between identical parallel paths",
                r"""
                Every straw spans the same two headers, so every straw sees the *same*
                $\Delta p$; being identical, each therefore carries the same share
                $Q/N$. (This is the parallel-branch rule of Tab 2's network chapter:
                equal pressure difference, flow divides by conductance.)
                """,
            ),
            (
                "Substitute and let the powers of $N$ fight",
                r"""
                $d^{4}=D^{4}\phi^{2}/N^{2}$, so
                $$\Delta p=\frac{128\mu L (Q/N)}{\pi d^{4}}
                =\frac{128\mu L Q}{\pi}\cdot\frac{1}{N}\cdot\frac{N^{2}}{D^{4}\phi^{2}}
                =\frac{128\,\mu L Q}{\pi D^{4}}\cdot\frac{N}{\phi^{2}}$$
                One factor of $N$ works **for** you (each straw carries less flow) and two
                work **against** you (through $d^{4}$). Two beats one, and a single net
                factor of $N$ is left in the numerator. Poor packing is punished twice over,
                as $1/\phi^{2}$.
                """,
            ),
            (
                "Convert to the quantity that appears on the electricity bill",
                r"""
                Hydraulic power is pressure rise times volumetric rate,
                $P=Q\,\Delta p$ (Tab 1). At fixed duty $Q$ this inherits the scaling
                directly:
                $$P_{\text{bundle}}\propto N$$
                Doubling the straw count to push $\mathrm{Re}_d$ further into the laminar
                range roughly doubles the pump power. The plot below is that straight line
                on log axes, with the open-pipe (turbulent) power as the horizontal
                reference.
                """,
            ),
            (
                "The same result stated as a physical picture",
                r"""
                Friction happens at walls. The total wetted wall area of the bundle is
                $$N\,\pi d\,L=N\pi L\,D\sqrt{\phi/N}=\pi L D\sqrt{N\phi}$$
                which grows without limit as $\sqrt{N}$. Subdividing the flow buys laminar
                order by manufacturing enormous quantities of wall for the fluid to rub
                against. Turbulence is expensive, but so is the surface you install to
                avoid it — and here the surface wins.
                """,
            ),
            (
                "When engineers do it anyway",
                r"""
                A shell-and-tube exchanger is exactly this bundle, and it is built precisely
                for the $\sqrt{N}$ growth in wall area — because that area is *heat transfer
                area*. The hydraulic penalty derived above is not an oversight; it is the
                price knowingly paid for the transport enhancement of §4.4.
                """,
            ),
        ],
        symbols=[
            (r"N", "number of parallel capillary lumens."),
            (r"d", r"bore of one lumen (m), $d=D\sqrt{\phi/N}$."),
            (r"\phi", "open-lumen fraction of the shell cross-section (packing fraction)."),
            (r"P", r"hydraulic power $Q\,\Delta p$ (W), before pump efficiency."),
        ],
    )
    render_predict(
        "straw_predict",
        "At fixed Q and outer D, adding more straws to keep Re_d laminar will typically…",
        ["cut pump power because f_F = 16/Re is smaller",
         "raise pump power because d⁴ in the denominator beats the laminar f",
         "leave Δp unchanged by dimensional analysis"],
        "raise pump power because d⁴ in the denominator beats the laminar f",
        "Δp_bundle ∝ N/φ² for laminar capillaries. Open-pipe turbulence is expensive, but so is making many tiny tubes.",
    )
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        straw_Q = persistent_input(st.slider, "Total Q [m³/h]", min_value=5.0, max_value=80.0, value=25.0, step=1.0, key="straw_Q")
        straw_D = persistent_input(st.slider, "Outer D [mm]", min_value=40.0, max_value=200.0, value=75.0, step=5.0, key="straw_D")
    with col_s2:
        straw_L = persistent_input(st.slider, "Length L [m]", min_value=10.0, max_value=200.0, value=60.0, step=5.0, key="straw_L")
        straw_phi = persistent_input(st.slider, "Packing fraction φ", min_value=0.5, max_value=0.91, value=0.85, step=0.01, key="straw_phi")
    with col_s3:
        straw_N = persistent_input(st.select_slider,
            "Number of straws N",
            options=[1, 4, 7, 19, 37, 61, 100, 200, 400],
            value=19,
            key="straw_N",
        )
    one = straw_bundle_comparison(
        flow_rate=straw_Q / 3600.0,
        outer_diameter=straw_D / 1000.0,
        length=straw_L,
        density=float(fluid["rho"]),
        viscosity=float(fluid["mu"]),
        n_straws=int(straw_N),
        packing_fraction=float(straw_phi),
    )
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Open-pipe Re_D", f"{one['re_open']:.0f}")
    col_m2.metric("Straw Re_d", f"{one['re_straw']:.0f}")
    col_m3.metric("Open-pipe power", f"{one['power_open']/1000:.2f} kW")
    col_m4.metric("Bundle power", f"{one['power_bundle']/1000:.2f} kW",
                  delta=f"{one['power_ratio']:.2f} × open")
    if one["straw_laminar"] and one["power_ratio"] > 1:
        st.warning(
            "The straws are laminar — and still more expensive. You bought extra wall area "
            "(more τ_w × perimeter) to suppress eddies."
        )
    elif not one["straw_laminar"]:
        st.info("These straws are still turbulent. Increase N or lower Q.")
    n_sweep = [1, 4, 7, 19, 37, 61, 100, 200, 400]
    sweep = [
        straw_bundle_comparison(
            flow_rate=straw_Q / 3600.0,
            outer_diameter=straw_D / 1000.0,
            length=straw_L,
            density=float(fluid["rho"]),
            viscosity=float(fluid["mu"]),
            n_straws=n,
            packing_fraction=float(straw_phi),
        )
        for n in n_sweep
    ]
    render_what_to_notice(
        "Left: bundle power vs N (log). Horizontal = open pipe. Right: Re_d falls through 2300 "
        "while power is already rising. A shell-and-tube exchanger uses many tubes for *area*, "
        "not to dodge turbulence; the hydraulic penalty is paid for heat transfer."
    )
    fig_st = plot_straw_bundle(
        n_sweep,
        sweep[0]["power_open"],
        [s["power_bundle"] for s in sweep],
        [s["re_straw"] for s in sweep],
    )
    render_plot(fig_st, key="tab_turbulence-fig_st")
    render_self_check(
        "straw_self_check",
        "Why doesn’t “keep it laminar with straws” win on pump kW at fixed Q and outer D?",
        [
            "Because laminar f_F is always larger than turbulent f_F",
            "Because Δp ~ μ Q L / d⁴ and d shrinks as 1/√N, so Δp grows with N",
            "Because packing fraction φ cannot exceed 0.5",
        ],
        "Because Δp ~ μ Q L / d⁴ and d shrinks as 1/√N, so Δp grows with N",
        "Hagen–Poiseuille on each lumen: d⁴ in the denominator. More walls, more shear area.",
    )
