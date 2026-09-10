"""Chapter 7: Newtonian and non-Newtonian fluids.

Chapter 6 closed the Navier-Stokes equations by *assuming* a linear, memoryless
relation between stress and strain rate. This chapter asks what that assumption
is actually a statement about -- the microstructure, not the mathematics -- and
then works through what happens to the pipe, the pump and the vessel when each
part of it fails.
"""

import numpy as np
import streamlit as st

from src.physics.exact_solutions import hagen_poiseuille_pipe
from src.physics.non_newtonian import (
    MODEL_INFO,
    buckingham_reiner_flow,
    flow_curve,
    herschel_bulkley_pipe,
    maxwell_startup,
    power_law_pressure_drop,
    thixotropic_step,
    timescale_numbers,
)
from src.plotting import (
    plot_flow_curves,
    plot_thixotropy,
    plot_viscoelastic_startup,
    plot_yield_stress_pipe,
)
from src.svg_diagrams import (
    diagram_deborah_timescales,
    diagram_microstructure_gallery,
    diagram_newtonian_origin,
    diagram_power_law,
    diagram_viscoelastic_effects,
    render_svg,
)
from src.ui.pedagogy import (
    render_callout,
    render_checklist,
    render_derivation,
    render_objectives,
    render_plot,
    render_predict,
    render_prose_and_latex,
    render_self_check,
    render_symbols,
    render_what_to_notice,
)
from src.ui.state import persistent_input
from src.units import get_fluid_state

# Defaults for the flow-curve lab, chosen so the three cards in the
# microstructure gallery each have a curve on the rheogram.
CURVE_DEFAULTS = {
    "Newtonian": {"mu": 0.05},
    "Power law (Ostwald-de Waele)": {"K": 2.0, "n": 0.45},
    "Bingham plastic": {"tau_y": 8.0, "mu_p": 0.05},
    "Herschel-Bulkley": {"tau_y": 8.0, "K": 2.0, "n": 0.45},
    "Casson": {"tau_y": 8.0, "mu_c": 0.05},
    "Carreau-Yasuda": {"mu_0": 20.0, "mu_inf": 0.02, "lam": 1.0, "n": 0.45, "a": 2.0},
}


def render_tab_non_newtonian():
    """Render the constitutive-behaviour chapter."""
    fluid = get_fluid_state()

    render_prose_and_latex(
        r"""
        Chapter 6 did not *derive* $\boldsymbol{\sigma}=-p\mathbf{I}+2\mu\mathbf{D}$.
        It derived the Cauchy balance, which is a momentum statement and holds for
        every material, and then chose the simplest law that is linear, isotropic
        and depends only on the strain rate **now**. Water obeys it to
        extraordinary accuracy. Paint, blood, ketchup, drilling mud, molten
        polymer, chocolate and wet cement do not, and none of them is exotic.

        The useful question is not "which fluids are non-Newtonian" but **what has
        to be true of a fluid for the linear law to hold at all** — because
        everything that breaks it is a fact about the fluid's internal structure,
        and that structure is what you can see, reason about and often design.
        """
    )
    render_objectives(
        [
            "Recover $\\tau = \\mu\\,\\dot\\gamma$ from momentum carried across a plane, and read off the two microscopic assumptions it needs.",
            "Connect each departure — thinning, thickening, a yield stress, memory — to the structure that causes it.",
            "Read a flow curve, and see why $\\mu_{app}=\\tau/\\dot\\gamma$ is a chord, not a material property.",
            "Redo the pipe balance for a yield-stress fluid and find the unyielded plug, checked against Buckingham–Reiner.",
            "Size a laminar polymer line with the Metzner–Reed Reynolds number.",
            "Separate the two elastic questions with the Weissenberg and Deborah numbers.",
        ]
    )

    # -------------------------------------------------------------------------
    # 7.1 What "Newtonian" actually asserts
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 7.1 What the Newtonian law is really claiming")
    render_svg(diagram_newtonian_origin())
    render_prose_and_latex(
        r"""
        **Scope of the picture:** a dilute gas near local equilibrium, with a smooth
        velocity field on scales much larger than its mean free path. The coloured
        paths represent molecular crossings; the horizontal arrows are mean layer
        velocities. This kinetic estimate explains momentum transport in a gas.
        Liquids can also be Newtonian, but their dense molecular interactions need
        a different microscopic treatment.
        """
    )
    render_derivation(
        r"$\tau = \mu\,\dot\gamma$ from momentum crossing a plane",
        [
            (
                "Track the momentum exchanged across an internal plane",
                r"""
                Put an imaginary plane inside the fluid, parallel to the flow. Molecules
                cross it in both directions all the time; on average as many go up as come
                down, or the fluid would gain mass. But the ones arriving from above carry
                the streamwise momentum of a **faster** layer, and the ones arriving from
                below carry that of a slower one.

                Momentum moves from the faster layer towards the slower layer even
                though the opposing mass transfers cancel. Stress is force per area;
                here its magnitude equals the net molecular momentum transfer rate
                per area. For $du/dy>0$, define the positive shear magnitude $\tau$:
                $$\tau=\frac{\text{net x-momentum transferred downwards per unit time}}{\text{area}}$$
                The signed momentum flux in the positive $y$ direction is $-\tau$.
                Chapter 6 distinguishes this flux sign from the traction on a chosen face.
                This is the same statement as Chapter 3's transport analogy, where $\nu$,
                $\alpha$ and $D_{AB}$ all turned out to be diffusivities of *something*.
                """,
            ),
            (
                "Estimate the momentum each crossing carries",
                r"""
                A molecule that last collided a mean free path $\ell$ away arrives carrying
                the mean velocity of the layer it came from. Over that distance the layer
                velocity differs by
                $$\Delta u \approx \ell\,\frac{du}{dy}$$
                so each crossing delivers about $m\,\ell\,(du/dy)$ of excess momentum. This
                is a *linearisation*: it is the first term of a Taylor expansion, and it is
                accurate when $\ell$ is small compared with the length scale over which
                the velocity gradient varies.
                """,
            ),
            (
                "Count the crossings — and notice the flow does not control them",
                r"""
                The number of crossings per unit area per unit time is set by the number
                density $n_{mol}$ and mean thermal speed, of order $n_{mol}\bar c$.
                At a fixed local thermodynamic state, the shear barely changes that
                thermal traffic **provided the velocity change across one free path
                is small compared with the thermal speed**:
                $$|\dot\gamma|\ell\ll\bar c
                \quad\Longleftrightarrow\quad
                |\dot\gamma|t_{collision}\ll1,\qquad t_{collision}\sim\ell/\bar c$$
                Both sides of the first comparison are speeds. Equivalently, a molecule
                undergoes little shear deformation between collisions. Multiplying
                the crossing rate by the excess momentum, with $\rho=n_{mol}m$, gives
                $$\tau \sim (n_{mol}\bar{c}m\ell)\,\frac{du}{dy}\;\Longrightarrow\;
                \tau=\mu\,\frac{du}{dy},\qquad \mu\sim \rho\,\bar{c}\,\ell$$
                This is a linear-response estimate: the coefficient is independent of
                shear rate within these assumptions. The order-one factor requires
                averaging molecular directions and speeds; it is not determined here.
                """,
            ),
            (
                "Two assumptions were smuggled in, and both are structural",
                r"""
                **(1) Shear does not appreciably change the transport coefficient.**
                The estimate used a near-equilibrium molecular distribution. It did not
                include chain alignment, deformable droplets or a particle contact network.
                Such changes can make the effective viscosity depend on the shear rate.

                **(2) Relaxation is fast compared with the imposed motion.**
                When molecular relaxation is short compared with both the shear time
                and the time over which the imposed flow changes, stress is well
                approximated by the instantaneous strain rate. This is a comparison
                of timescales, not a universal relaxation time for all fluids or flows.

                Long chains, deformable drops or attractive particles give shear something
                to orient (assumption 1); a slow relaxation time gives the fluid a memory
                (assumption 2). Section 7.7 makes these comparisons explicit through
                the Weissenberg and Deborah numbers.
                """,
            ),
        ],
        symbols=[
            (r"\tau", "positive shear magnitude for the illustrated positive velocity gradient (Pa)"),
            (r"\dot\gamma = du/dy", "shear rate, the rate at which two layers slide past each other (1/s)"),
            (r"\ell", "mean free path — how far a molecule travels between collisions (m)"),
            (r"\bar{c}", "mean thermal speed of the molecules (m/s)"),
            (r"\mu", "dynamic viscosity; here a *derived* quantity, ~ρ c̄ ℓ, not an input (Pa·s)"),
        ],
        closing=(
            "The kinetic estimate $\\mu\\sim\\rho\\bar{c}\\ell$ is quantitative enough to "
            "predict the dilute-gas trend at fixed temperature and composition: viscosity "
            "is approximately pressure independent because raising density increases "
            "$\\rho$ while shortening $\\ell$ inversely. This estimate requires a "
            "continuum gas; it does not establish pressure independence for dense gases or liquids."
        ),
    )
    st.caption(
        "Further reading: [MIT mean-free-path transport notes]"
        "(https://ocw.mit.edu/courses/5-62-physical-chemistry-ii-spring-2008/"
        "f90a4c878e68f44e42b85dbbd4d18751_31_562ln08.pdf)."
    )
    render_callout(
        title="The definition, stated so that it can fail",
        body=r"""
        A fluid is **Newtonian** when the stress is (i) linear in the strain rate,
        (ii) instantaneous, (iii) isotropic, and (iv) purely deviatoric — no normal
        stress differences in shear. Four separate claims: a fluid can break any
        one of them and keep the others. Shear thinning breaks only (i);
        a thixotropic paste breaks (i) and (ii); a polymer melt breaks all four.
        """,
    )

    # -------------------------------------------------------------------------
    # 7.2 The structural causes
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 7.2 Four structures, four departures")
    render_prose_and_latex(
        """
        Each card below is a mechanism first and a curve second. Reading them in
        this order matters: a power-law index is a two-parameter summary of
        entangled chains being combed straight, and if you fit one to a fluid
        whose structure is doing something else, the fit will extrapolate
        confidently in the wrong direction.
        """
    )
    render_svg(diagram_microstructure_gallery())
    render_callout(
        title="Why shear thinning is so common, in one sentence",
        body=r"""
        Almost any structure — a coil, a floc, a droplet, an aggregate — is *harder
        to push through* when randomly arranged than when combed into the flow
        direction, and shear does the combing. Shear **thickening** is rarer
        because it needs the opposite: a structure that only forms under load,
        which in practice means particles crowded closely enough to touch.
        """,
    )
    picked = persistent_input(
        st.selectbox,
        "Inspect one constitutive model",
        options=list(MODEL_INFO.keys()),
        key="nn_model_info_pick",
    )
    info = MODEL_INFO[picked]
    with st.container(border=True):
        st.markdown(f"**{picked}**")
        st.latex(info["law"])
        st.markdown(f"**Why the structure does this.** {info['mechanism']}")
        st.caption(f"Typical materials: {info['examples']}")

    # -------------------------------------------------------------------------
    # 7.3 Flow-curve lab
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 7.3 The flow curve, and the viscosity that is not one")
    render_prose_and_latex(
        r"""
        A rheometer imposes a shear rate and measures a stress, giving
        $\tau(\dot\gamma)$. People then quote an **apparent viscosity**
        $$\mu_{app}=\frac{\tau}{\dot\gamma}$$
        which is the slope of the *chord from the origin* to the point on the flow
        curve — not the local slope, and not a material constant. For a Newtonian
        fluid the two coincide and the second panel below is flat. For everything
        else, a single quoted "viscosity" is meaningless until the shear rate is
        stated with it.
        """
    )
    render_predict(
        "nn_predict_flow_curve",
        "On log–log axes, what does a yield-stress fluid's apparent viscosity do as γ̇ → 0?",
        [
            "It levels off at a finite plateau",
            "It rises without bound",
            "It falls to zero",
        ],
        "It rises without bound",
        "τ tends to the finite τ_y while γ̇ tends to zero, so the chord slope τ/γ̇ diverges. "
        "That divergence is the material telling you it is a solid down there — no viscosity describes it.",
    )
    chosen = persistent_input(
        st.multiselect,
        "Models to plot",
        options=list(CURVE_DEFAULTS.keys()),
        default=["Newtonian", "Power law (Ostwald-de Waele)", "Bingham plastic", "Carreau-Yasuda"],
        key="nn_curve_models",
    )
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        n_curve = persistent_input(
            st.slider, "Power-law index n", min_value=0.2, max_value=1.8,
            value=0.45, step=0.05, key="nn_curve_n",
            help="Shared by the power-law, Herschel–Bulkley and Carreau–Yasuda curves.",
        )
    with col_c2:
        tau_y_curve = persistent_input(
            st.slider, "Yield stress τ_y [Pa]", min_value=0.0, max_value=40.0,
            value=8.0, step=1.0, key="nn_curve_tauy",
            help="Shared by the Bingham, Herschel–Bulkley and Casson curves.",
        )
    with col_c3:
        lam_curve = persistent_input(
            st.slider, "Carreau relaxation time λ [s]", min_value=0.01, max_value=10.0,
            value=1.0, step=0.01, key="nn_curve_lam",
            help="The power-law region begins near γ̇ = 1/λ.",
        )
    gamma_sweep = np.logspace(-2, 3, 220)
    curves = []
    for model in chosen:
        params = dict(CURVE_DEFAULTS[model])
        if "n" in params:
            params["n"] = float(n_curve)
        if "tau_y" in params:
            params["tau_y"] = float(tau_y_curve)
        if "lam" in params:
            params["lam"] = float(lam_curve)
        curves.append(flow_curve(model, gamma_sweep, **params))
    if curves:
        render_what_to_notice(
            "A constant apparent viscosity gives a flat line on the right. "
            "At n = 1, the power-law and Carreau–Yasuda models also become Newtonian. "
            f"The Carreau rate scale is 1/λ = {1.0/float(lam_curve):.3g} 1/s; "
            "the selected index n controls whether viscosity falls, stays constant or rises."
        )
        render_plot(plot_flow_curves(curves), key="nn-flow-curves")
        carreau = next((c for c in curves if c["model"] == "Carreau-Yasuda"), None)
        if carreau is not None:
            mu_low = float(carreau["mu_app"][0])
            mu_high = float(carreau["mu_app"][-1])
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("μ at γ̇ = 0.01 1/s", f"{mu_low:.3g} Pa·s")
            col_m2.metric("μ at γ̇ = 1000 1/s", f"{mu_high:.3g} Pa·s")
            col_m3.metric("Low/high shear viscosity ratio", f"{mu_low / mu_high:.3g}×")
            st.caption(
                f"For these settings, the low/high shear viscosity ratio is {mu_low / mu_high:.3g} "
                "across the displayed sweep. "
                + ("At n = 1, this model has constant viscosity throughout the sweep."
                   if float(n_curve) == 1.0 else
                   "Report the measurement's shear rate alongside its viscosity.")
            )
    else:
        st.info("Select at least one model to draw the flow curve.")
    render_callout(
        title="Shear rates you are actually designing for",
        body="""
        Sedimentation in a tank, $10^{-4}$ to $10^{-2}\\;\\mathrm{s^{-1}}$ · levelling of a
        paint film, $10^{-2}$ to $10^{-1}$ · pouring, $10$ to $10^{2}$ · pipe flow,
        $10$ to $10^{3}$ · spraying, brushing and coating, $10^{3}$ to $10^{5}$.

        A shear-thinning paint is engineered around that spread: thick where
        $\\dot\\gamma$ is tiny so it does not sag on the wall, thin under the brush.
        Measure the flow curve over the decades your process uses, not over the
        decades your rheometer prefers.
        """,
    )

    # -------------------------------------------------------------------------
    # 7.4 Pipe flow: the balance is unchanged, the kinematics are not
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 7.4 Laminar pipe flow with a yield stress")
    render_svg(diagram_power_law())
    render_derivation(
        "the plug radius, and why every fluid shares the same τ(r)",
        [
            (
                "The force balance does not know what fluid this is",
                r"""
                Repeat Chapter 4's cylindrical-plug balance word for word: steady, fully
                developed flow, so the pressure force on a coaxial plug of radius $r$ is
                carried entirely by the shear on its jacket,
                $$\tau(r)=\frac{r}{2}\left(-\frac{dp}{dz}\right),
                \qquad \tau_w=\frac{R}{2}\left(-\frac{dp}{dz}\right)$$
                **This holds for any material whatsoever** — Newtonian, power-law, paste or
                slurry — because it is a momentum statement, not a material one. The linear
                $\tau(r)$ in the right-hand panel below is therefore not a result of the
                model; it is a constraint every model must satisfy.
                """,
            ),
            (
                "A yield stress converts a stress threshold into a radius",
                r"""
                If the material does not flow until $\tau>\tau_y$, then since $\tau$ rises
                linearly from zero on the axis, there is a radius inside which it is never
                stressed enough:
                $$r_{plug}=\frac{2\tau_y}{(-dp/dz)}=R\,\frac{\tau_y}{\tau_w}$$
                Inside it the material moves as an **unsheared solid plug**, at whatever
                speed the sheared annulus around it carries. Nothing was assumed about how
                it flows once yielded — only geometry and the linear stress profile.

                Two consequences follow immediately. If $\tau_w\le\tau_y$ the plug fills the
                pipe and **there is no flow at all, at any pressure below that threshold**.
                And since $\tau_w=R(-dp/dz)/2$, a *smaller* pipe needs a *larger* pressure
                gradient to start — the opposite of the intuition trained on Newtonian lines.
                """,
            ),
            (
                "Only now insert the constitutive law",
                r"""
                Herschel–Bulkley, $\tau=\tau_y+K\dot\gamma^{\,n}$, with $u$ decreasing
                outwards so $\dot\gamma=-du/dr>0$, gives in the yielded annulus
                $$-\frac{du}{dr}=\left[\frac{\tau(r)-\tau_y}{K}\right]^{1/n}$$
                Setting $\tau_y=0$ recovers the power law; setting $\tau_y=0,\,n=1,\,K=\mu$
                recovers the Hagen–Poiseuille result of Chapters 4 and 8. Running those checks
                before trusting anything downstream is the point of writing it this way.
                """,
            ),
            (
                "Integrate inward from the wall, where the velocity is known",
                r"""
                Assume $G=-dp/dz>0$ and $\tau_w>\tau_y$, so a yielded annulus exists.
                The wall supplies the integration constant through no-slip, $u(R)=0$.
                For $r\ge r_{plug}$, integrate the shear rate only across this annulus:
                $$u(r)=\int_r^R\left[\frac{Gs/2-\tau_y}{K}\right]^{1/n}\,ds$$
                The momentum balance gives $d\tau=(G/2)\,ds$. Changing variable makes
                the limits $\tau(r)$ and $\tau_w$, both at or above the yield stress:
                $$u(r)=\frac{2}{G}K^{-1/n}\int_{\tau(r)}^{\tau_w}(\tau-\tau_y)^{1/n}\,d\tau$$
                Integrating the power gives the velocity in the yielded annulus:
                $$u(r)=\frac{2}{G}\cdot\frac{n}{n+1}\cdot K^{-1/n}
                \left[(\tau_w-\tau_y)^{\frac{n+1}{n}}-(\tau(r)-\tau_y)^{\frac{n+1}{n}}\right]$$
                Do not continue this fractional-power expression into the unyielded core,
                where $\tau(r)-\tau_y$ is negative.
                """,
            ),
            (
                "Match the moving rigid plug to the yielded annulus",
                r"""
                Below the yield stress the ideal material has zero shear rate, so
                $du/dr=0$ inside the plug. Velocity continuity at $r=r_{plug}$ fixes
                this constant to the annular velocity at its inner edge:
                $$u(r)=u(r_{plug})=\frac{2n}{G(n+1)}K^{-1/n}
                (\tau_w-\tau_y)^{(n+1)/n},\qquad 0\le r\le r_{plug}$$
                Thus the plug can translate without shearing. If $\tau_w\le\tau_y$,
                the entire section is unyielded and the no-slip wall fixes its speed
                to zero instead.
                """,
            ),
            (
                "Read the zero-yield limit as a shape, not just an exponent",
                r"""
                Setting $\tau_y=0$ removes the finite-radius plug and gives the
                power-law profile. Compare shapes at fixed $r/R$ and fixed $u/u_{max}$:
                $$\frac{u}{u_{max}}=1-(r/R)^m,\qquad m=1+\frac1n$$
                At $n=1$ this is a parabola. For $n>1$, $1<m<2$, giving a more pointed
                core. For $0<n<1$, $m>2$: raising a number between zero and one to a
                larger power makes it smaller, so the velocity stays closer to its
                maximum through more of the pipe. As $n\to0^+$, $m\to\infty$ and shear
                concentrates near the wall. This is a plug-like limiting shape;
                a zero-yield power law has no finite unyielded core.
                """,
            ),
            (
                r"Why $\mathrm{Re}_{MR}$ has to be *defined* rather than derived",
                r"""
                A power-law fluid has no single viscosity, so $\rho\bar{u}D/\mu$ is not even
                well posed. Metzner and Reed ran the argument backwards: **define** a
                Reynolds number by whatever expression makes the laminar friction factor
                come out at exactly $f_D=64/\mathrm{Re}$, so the Newtonian
                laminar head-loss relation in Chapter 2 can be written in the same form:
                $$\mathrm{Re}_{MR}=\frac{\rho\,\bar u^{\,2-n}D^{n}}
                {K\,8^{\,n-1}\left(\frac{3n+1}{4n}\right)^{n}}$$
                Every awkward factor in the denominator is there to make that identity
                exact. Note what it does **not** do: it does not predict the transition
                point. The $2100$ used below is carried over from Newtonian pipes and is an
                approximation for these fluids. This identity applies to the **power-law
                case with zero yield stress**. For Herschel–Bulkley flow below, this
                Reynolds number uses only the power-law part and is a diagnostic guide.
                """,
            ),
            (
                "Use the actual wall stress when the fluid has a yield stress",
                r"""
                Chapter 2 defines Fanning friction as wall shear divided by dynamic
                pressure. The cylindrical force balance above supplies the actual wall
                stress, so it includes the yield-stress contribution without a friction
                correlation. For positive mean velocity,
                $$f_F=\frac{\tau_w}{\rho\bar u^2/2},\qquad f_D=4f_F$$
                To compare yielding with viscous deformation, choose the shear-rate
                scale $\bar u/D$. The consistency $K$ then gives a stress scale
                $K(\bar u/D)^n$, so their ratio is dimensionless:
                $$\mathrm{Bn}=\frac{\tau_y}{K(\bar u/D)^n}$$
                Here $D=2R$; other shear-rate conventions give different numerical
                Bingham numbers. With yield stress, $f_D=64/\mathrm{Re}_{MR}$ using
                the power-law-only Reynolds number is no longer an identity.
                """,
            ),
        ],
        symbols=[
            (r"\tau_y", "yield stress: the stress below which the material behaves as a solid (Pa)"),
            (r"K", "consistency index; the stress at unit shear rate above yield (Pa·sⁿ)"),
            (r"n", "flow-behaviour index; n<1 thinning, n=1 Newtonian, n>1 thickening (-)"),
            (r"r_{plug}", "radius of the unyielded core (m)"),
            (r"\mathrm{Bn}", "Bingham number: yield stress divided by the viscous stress scale (-)"),
        ],
    )
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    with col_p1:
        n_pipe = persistent_input(
            st.slider, "n", min_value=0.3, max_value=1.7, value=0.7, step=0.05, key="nn_pipe_n"
        )
    with col_p2:
        k_pipe = persistent_input(
            st.number_input, "K [Pa·sⁿ]", min_value=1e-4, max_value=10.0,
            value=max(float(fluid["mu"]), 1e-3), format="%.4f", key="nn_pipe_K",
        )
    with col_p3:
        tau_y_pipe = persistent_input(
            st.slider, "τ_y [Pa]", min_value=0.0, max_value=1.5,
            value=0.2, step=0.05, key="nn_pipe_tauy",
        )
    with col_p4:
        dpdz_pipe = persistent_input(
            st.slider, "dp/dz [Pa/m]", min_value=-120.0, max_value=-5.0,
            value=-40.0, step=5.0, key="nn_pipe_dpdz",
        )
    pipe_R = 0.025
    hb = herschel_bulkley_pipe(
        radius=pipe_R, dp_dz=float(dpdz_pipe), K=float(k_pipe), n=float(n_pipe),
        tau_y=float(tau_y_pipe), rho=float(fluid["rho"]),
    )
    newt = hagen_poiseuille_pipe(
        radius=pipe_R, dp_dx=float(dpdz_pipe), mu=float(fluid["mu"]), rho=float(fluid["rho"])
    )
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    col_r1.metric("τ_w = R(−dp/dz)/2", f"{hb['tau_wall']:.3f} Pa",
                  help="Set by the momentum balance alone: K, n and τ_y do not enter.")
    col_r2.metric("Unyielded plug r_plug/R", f"{hb['plug_fraction']:.3f}",
                  help="τ_y/τ_w. Reaches 1 when the wall stress cannot yield the material.")
    col_r3.metric("Mean velocity ū", f"{hb['u_avg']:.4f} m/s")
    col_r4.metric("Re_MR", f"{hb['re_mr']:.1f}" if hb["flowing"] else "no flow")
    if not hb["flowing"]:
        st.warning(
            f"τ_w = {hb['tau_wall']:.3f} Pa does not exceed τ_y = {hb['tau_y']:.3f} Pa, so nothing "
            "yields anywhere and the flow rate is exactly zero. Raise |dp/dz| or lower τ_y."
        )
    elif not hb["laminar"]:
        st.warning("Re_MR ≥ 2100: the laminar profile may be outside its validity range. "
                   "This power-law-only Reynolds number is an approximate transition guide for yield-stress fluids.")
    render_what_to_notice(
        "Both panels share the same vertical axis. The flat core on the left starts exactly where "
        "the stress line on the right crosses τ_y — the plug is read off the stress plot, not fitted."
    )
    render_plot(plot_yield_stress_pipe(hb, newt), key="nn-yield-pipe")

    # The Bingham case has an independent closed-form answer; use it rather than
    # asserting that the integrated profile is right.
    if abs(float(n_pipe) - 1.0) < 1e-9:
        q_ref = buckingham_reiner_flow(pipe_R, float(dpdz_pipe), float(k_pipe), float(tau_y_pipe))
        check = "n = 1 exactly, so Buckingham–Reiner applies."
    else:
        q_ref = buckingham_reiner_flow(pipe_R, float(dpdz_pipe), float(k_pipe), float(tau_y_pipe))
        check = "Buckingham–Reiner is the n = 1 result; it is shown for reference only."
    with st.container(border=True):
        st.markdown("**Verification, computed live rather than claimed**")
        col_v1, col_v2 = st.columns(2)
        col_v1.metric("Q from the integrated profile", f"{hb['flow_rate']*3.6e3:.4f} m³/h")
        col_v2.metric("Q from Buckingham–Reiner (n=1)", f"{q_ref*3.6e3:.4f} m³/h")
        if abs(float(n_pipe) - 1.0) < 1e-9 and q_ref > 0:
            err = abs(hb["flow_rate"] - q_ref) / q_ref
            st.markdown(
                f":green[**Agreement to {err*100:.4f}%**] — the numerically integrated "
                "Herschel–Bulkley profile reproduces the closed-form Bingham flow rate "
                r"$Q=\frac{\pi R^4 G}{8\mu_p}\left[1-\frac{4}{3}\xi+\frac{\xi^4}{3}\right]$, "
                r"$\xi=\tau_y/\tau_w$."
            )
        else:
            st.caption(check + " Set n = 1.00 to run the comparison.")
    render_self_check(
        "nn_self_check_plug",
        "Doubling the pressure gradient in a Bingham line does what to the plug radius?",
        [
            "Doubles it — more stress, more plug",
            "Halves it — r_plug = 2τ_y/(−dp/dz)",
            "Leaves it unchanged; the plug depends only on τ_y",
        ],
        "Halves it — r_plug = 2τ_y/(−dp/dz)",
        "The stress profile steepens, so the radius at which it crosses τ_y moves inward. "
        "Push hard enough and the plug shrinks toward the axis, where it can never quite vanish: τ(0) = 0 always.",
    )

    # -------------------------------------------------------------------------
    # 7.5 Design consequence: sizing a laminar polymer line
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 7.5 What this costs at the pump")
    render_prose_and_latex(
        r"""
        Chapter 2 sized lines with $\Delta p = f_D(L/D)(\rho\bar u^2/2)$ and a
        Newtonian friction factor. For a laminar power-law fluid the same laminar
        result inverts directly to a pressure drop, and it no longer scales with
        $Q$ — it scales with $Q^{\,n}$:
        $$\Delta p = \frac{2KL}{R}\left[\frac{Q\,(3n+1)}{\pi n R^{3}}\right]^{n}$$
        A strongly shear-thinning fluid ($n\approx0.4$) therefore punishes a
        throughput increase far less than a Newtonian one, which is a genuine
        process advantage — and it also means a turndown gains you much less than
        you would expect.
        """
    )
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        q_design = persistent_input(
            st.number_input, "Design flow Q [m³/h]", min_value=0.05, max_value=50.0,
            value=2.0, step=0.25, key="nn_design_q",
        )
    with col_d2:
        d_design = persistent_input(
            st.number_input, "Inside diameter D [m]", min_value=0.01, max_value=0.30,
            value=0.05, step=0.005, format="%.3f", key="nn_design_d",
        )
    with col_d3:
        l_design = persistent_input(
            st.number_input, "Line length L [m]", min_value=1.0, max_value=2000.0,
            value=100.0, step=10.0, key="nn_design_l",
        )
    q_si = float(q_design) / 3600.0
    dp_pl = power_law_pressure_drop(q_si, float(d_design) / 2.0, float(l_design), float(k_pipe), float(n_pipe))
    dp_double = power_law_pressure_drop(2.0 * q_si, float(d_design) / 2.0, float(l_design), float(k_pipe), float(n_pipe))
    dp_newt = 128.0 * float(fluid["mu"]) * float(l_design) * q_si / (np.pi * float(d_design) ** 4)
    col_e1, col_e2, col_e3 = st.columns(3)
    col_e1.metric("Δp, power-law laminar", f"{dp_pl/1000.0:.3f} kPa")
    col_e2.metric("Δp at twice the flow", f"{dp_double/1000.0:.3f} kPa",
                  delta=f"×{(dp_double/dp_pl):.2f}" if dp_pl > 0 else None)
    col_e3.metric("Δp if it were Newtonian at sidebar μ", f"{dp_newt/1000.0:.3f} kPa")
    st.caption(
        f"Doubling the flow multiplies Δp by 2ⁿ = {2.0**float(n_pipe):.2f}, not by 2, because the extra shear "
        f"thins the fluid on the way. The Newtonian column uses the sidebar μ = {fluid['mu']:.3e} Pa·s and is "
        "shown only to make the comparison concrete — it is not the same material."
    )
    render_checklist(
        "Assumptions behind this Δp",
        [
            ("Laminar", bool(hb["laminar"]),
             f"Re_MR = {hb['re_mr']:.0f} from the profile lab above; the 2100 threshold is borrowed from Newtonian pipes."),
            ("No yield stress in the design formula", float(tau_y_pipe) == 0.0,
             "Δp above is the pure power-law inversion. With τ_y > 0 use the plug lab, which is the correct model."),
            ("Fully developed, isothermal, no wall slip", False,
             "Entrance lengths are longer for shear-thinning fluids, and concentrated suspensions frequently slip at smooth walls — a real and often dominant error."),
            ("Time-independent", float(tau_y_pipe) == 0.0,
             "A thixotropic fluid's Δp depends on how long it has been flowing. Section 7.6 shows why."),
        ],
    )

    # -------------------------------------------------------------------------
    # 7.6 Time enters the constitutive law: thixotropy
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 7.6 Memory, part one: thixotropy")
    render_prose_and_latex(
        r"""
        Everything so far still assumed the stress depends only on the strain rate
        **now**. Drop that and the second Newtonian assumption goes with it. The
        simplest honest model gives the structure its own equation: a parameter
        $\lambda\in[0,1]$ for the fraction of the network still intact, broken by
        flow and rebuilt by Brownian motion,
        $$\frac{d\lambda}{dt}=k_b\,(1-\lambda)-k_f\,\lambda\,\dot\gamma,
        \qquad \mu=\mu_\infty\,(1+c\,\lambda)$$
        At a fixed shear rate $\lambda$ relaxes exponentially to
        $k_b/(k_b+k_f\dot\gamma)$ with time constant $1/(k_b+k_f\dot\gamma)$ — so
        breaking is fast (large $\dot\gamma$) and rebuilding is slow. That
        asymmetry is the whole phenomenon.
        """
    )
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        gamma_hi = persistent_input(
            st.slider, "High shear rate γ̇ [1/s]", min_value=5.0, max_value=200.0,
            value=50.0, step=5.0, key="nn_thix_hi",
        )
    with col_t2:
        k_build = persistent_input(
            st.slider, "Rebuild rate k_b [1/s]", min_value=0.02, max_value=1.0,
            value=0.25, step=0.02, key="nn_thix_build",
        )
    with col_t3:
        t_hold = persistent_input(
            st.slider, "Hold time per step [s]", min_value=5.0, max_value=120.0,
            value=30.0, step=5.0, key="nn_thix_hold",
        )
    thix = thixotropic_step(
        gamma_hi=float(gamma_hi), gamma_lo=1.0, k_build=float(k_build),
        k_break=0.05, t_hold=float(t_hold),
    )
    col_x1, col_x2, col_x3 = st.columns(3)
    col_x1.metric("Break-down time constant", f"{thix['tau_build_high']:.2f} s",
                  help="1/(k_b + k_f γ̇) at the high shear rate.")
    col_x2.metric("Rebuild time constant", f"{thix['tau_build_low']:.2f} s",
                  help="1/(k_b + k_f γ̇) back at the low shear rate.")
    col_x3.metric("Rebuild / break-down", f"{thix['tau_build_low']/thix['tau_build_high']:.1f}×")
    render_what_to_notice(
        "The structure falls quickly when the step goes up and crawls back when it comes down. "
        "The stress panel is the consequence: the same low shear rate gives a much lower stress "
        "*after* the high-shear excursion than it did before it."
    )
    render_plot(plot_thixotropy(thix), key="nn-thixotropy")
    render_callout(
        title="Why a rheometer draws a loop, and what that loop is not",
        body="""
        Sweep the shear rate up and back down on a thixotropic sample and the two
        branches do not coincide: the down-sweep is measured on a partly broken
        structure. The enclosed area is often quoted as a "thixotropy index", but
        it is not a material property — it depends entirely on how fast you swept.
        Two labs sweeping at different rates will report different numbers for the
        same drum of mud. Report the sweep protocol, or report the kinetics.
        """,
    )

    # -------------------------------------------------------------------------
    # 7.7 Memory, part two: viscoelasticity
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 7.7 Memory, part two: elasticity and normal stresses")
    render_prose_and_latex(
        r"""
        A thixotropic fluid remembers how much structure it has. A **viscoelastic**
        fluid remembers the deformation itself — it stores it, like a spring, and
        gives it back. Start a steady shear on a Maxwell fluid and the stress does
        not appear at once; it grows over the relaxation time $\lambda$:
        $$\tau(t)=\mu\dot\gamma\left(1-e^{-t/\lambda}\right)$$
        And because the stretched chains pull **along** the streamlines, the same
        motion produces a normal stress the Newtonian law cannot generate at all:
        $$N_1=\sigma_{xx}-\sigma_{yy}=2\mu\lambda\dot\gamma^{2}=2\,\mathrm{Wi}\,\tau$$
        Notice the square. $N_1$ is negligible at low shear rate and dominant at
        high, which is why rod-climbing and die swell look like thresholds even
        though nothing switches on.
        """
    )
    render_svg(diagram_viscoelastic_effects())
    col_w1, col_w2, col_w3 = st.columns(3)
    with col_w1:
        lam_ve = persistent_input(
            st.slider, "Relaxation time λ [s]", min_value=0.01, max_value=5.0,
            value=0.5, step=0.01, key="nn_ve_lam",
        )
    with col_w2:
        gdot_ve = persistent_input(
            st.slider, "Shear rate γ̇ [1/s]", min_value=0.1, max_value=100.0,
            value=10.0, step=0.1, key="nn_ve_gdot",
        )
    with col_w3:
        t_proc = persistent_input(
            st.number_input, "Process residence time [s]", min_value=0.01, max_value=600.0,
            value=5.0, step=0.5, key="nn_ve_tproc",
            help="Time a parcel spends in the equipment — a contraction, a die, a mixer.",
        )
    ve = maxwell_startup(
        gamma_dot=float(gdot_ve), relax_time=float(lam_ve), mu=5.0,
        t_end=max(6.0 * float(lam_ve), 0.5),
    )
    numbers = timescale_numbers(float(lam_ve), float(gdot_ve), float(t_proc))
    col_y1, col_y2, col_y3 = st.columns(3)
    col_y1.metric("Weissenberg Wi = λγ̇", f"{numbers['weissenberg']:.2f}",
                  help="Is the microstructure distorted by the flow?")
    col_y2.metric("Deborah De = λ/t_process", f"{numbers['deborah']:.3f}",
                  help="Does the material have time to forget within the equipment?")
    col_y3.metric("N₁ / τ = 2Wi", f"{ve['n1_over_tau']:.2f}")
    st.caption(
        f"Regime: {numbers['regime']}. "
        + ("The structure is significantly distorted (Wi > 1), so normal stresses matter."
           if numbers["distorted"] else
           "The structure is barely distorted (Wi < 1), so a purely viscous model is defensible here.")
    )
    render_what_to_notice(
        "The Newtonian dashed line is at the steady value from t = 0; the viscoelastic stress needs a few λ to reach it. "
        "The bar chart shows N₁ overtaking τ as soon as Wi exceeds ½."
    )
    render_plot(plot_viscoelastic_startup(ve), key="nn-viscoelastic")
    render_prose_and_latex(
        """
        **The two numbers ask different questions, and confusing them is the usual
        error.** Weissenberg compares the relaxation time with the *strain rate*:
        it asks whether the flow is deforming the microstructure. Deborah compares
        it with the *time available*: it asks whether the material can relax within
        the equipment. Steady shear in a long pipe can have a large Wi and a
        vanishing De. A sudden contraction can have a large De at modest Wi — and
        that is where extrudate distortion and melt fracture live.
        """
    )
    render_svg(diagram_deborah_timescales())
    render_self_check(
        "nn_self_check_deborah",
        "Pitch (λ ≈ 10⁴–10⁵ s) shatters under a hammer but drips through a funnel over years. Which statement is right?",
        [
            "It is a solid; the funnel experiment is an illusion",
            "It is a liquid; the hammer experiment is an illusion",
            "Both are correct — De is large for the hammer and small for the drip",
        ],
        "Both are correct — De is large for the hammer and small for the drip",
        "De = λ/t_process. A millisecond impact gives De ~ 10⁷ and the material stores the deformation elastically until it fractures. "
        "A year-long drip gives De ~ 10⁻³ and it flows. The material did not change; the clock did.",
    )

    # -------------------------------------------------------------------------
    # 7.8 Choosing a model
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 7.8 Choosing a model, and knowing when it will fail you")
    render_prose_and_latex(
        """
        A constitutive model is a claim about structure, so choose it from what the
        material *is*, then confirm it against a flow curve measured over your
        process's shear rates.
        """
    )
    with st.container(border=True):
        st.markdown("**A short decision path**")
        st.markdown(
            "1. **Does it hold its shape on a spoon, or refuse to restart in a line?** "
            "Then it has a yield stress — Bingham if the yielded material is nearly "
            "Newtonian, Herschel–Bulkley if it also thins. Size the *start-up* pressure, "
            "not just the running pressure."
        )
        st.markdown(
            "2. **Does the measured viscosity change with shear rate but not with time?** "
            "Power law over a decade or two; Carreau–Yasuda if you need the low-shear "
            "plateau (settling, levelling) and the high-shear one (spraying) in the same model."
        )
        st.markdown(
            "3. **Does it depend on how long it has been sheared?** Thixotropic. No "
            "time-independent model can size it; you need the kinetics, or a protocol "
            "that fixes the shear history."
        )
        st.markdown(
            "4. **Does it climb, swell, recoil or draw a stable filament?** It is elastic. "
            "Check Wi and De before assuming any generalised-Newtonian model at all — "
            "they all predict N₁ = 0, which is qualitatively wrong for these flows."
        )
    render_checklist(
        "Failure modes worth stating out loud",
        [
            ("A power law fitted over one decade extrapolates badly", False,
             "It predicts infinite viscosity at zero shear and zero at infinite shear. Neither happens. Fit over the decades you will use."),
            ("Wall slip is not a fluid property", False,
             "Concentrated suspensions and pastes often form a thin depleted layer at a smooth wall, so the pipe transports far more than the model says. It shows up as an apparent diameter dependence — the standard check is measuring in tubes of different diameter."),
            ("Re_MR does not predict transition", False,
             "It is defined to make the laminar friction factor come out at 64/Re. The 2100 threshold is borrowed, and shear-thinning fluids commonly stay laminar past it."),
            ("Generalised-Newtonian models have no elasticity", False,
             "Power law, Bingham, Carreau: all predict zero normal stress difference. They cannot describe rod-climbing, die swell or elastic instability, no matter how the parameters are fitted."),
            ("The momentum balance never fails", True,
             "τ_w = R(−dp/dz)/2 is true for every fluid in this chapter. When a measurement disagrees with a model, the constitutive law is the suspect."),
        ],
    )
    render_symbols(
        [
            (r"\dot\gamma", "shear rate (1/s)"),
            (r"\mu_{app}=\tau/\dot\gamma", "apparent viscosity: a chord slope, quoted only with its shear rate (Pa·s)"),
            (r"\tau_y", "yield stress (Pa)"),
            (r"K,\;n", "consistency index (Pa·sⁿ) and flow-behaviour index (-)"),
            (r"\lambda", "relaxation time of the microstructure (s)"),
            (r"\mathrm{Wi}=\lambda\dot\gamma", "Weissenberg number: is the structure distorted? (-)"),
            (r"\mathrm{De}=\lambda/t_{proc}", "Deborah number: does it have time to relax? (-)"),
            (r"N_1", "first normal stress difference; zero for every Newtonian and generalised-Newtonian fluid (Pa)"),
            (r"\mathrm{Re}_{MR}", "Metzner–Reed Reynolds number, defined so that f_D = 64/Re in laminar flow (-)"),
        ]
    )
