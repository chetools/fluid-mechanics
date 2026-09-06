"""UI module for Panel 3: Stress Tensor, Constitutive Equations & Navier-Stokes."""

import streamlit as st
from src.ui.state import persistent_input
from src.ui.pedagogy import render_plot
import numpy as np

from src.svg_diagrams import (
    diagram_stress_tensor_cube,
    diagram_kinematic_decomposition,
    diagram_power_law,
    render_svg
)
from src.physics.stress_tensor import (
    decompose_velocity_gradient_2d,
    compute_cauchy_stress_2d,
    deform_fluid_element_2d
)
from src.plotting import plot_fluid_element_deformation
from src.units import format_quantity, get_fluid_state
from src.ui.pedagogy import (
    render_objectives,
    render_what_to_notice,
    render_self_check,
    render_prose_and_latex,
    render_symbols,
    render_derivation,
)


KINEMATIC_PRESETS = {
    "Simple shear (Couette-like)": {"dudx": 0.0, "dudy": 1.0, "dvdx": 0.0, "dvdy": 0.0},
    "Pure shear (symmetric)": {"dudx": 0.0, "dudy": 1.0, "dvdx": 1.0, "dvdy": 0.0},
    "Pure rotation (rigid)": {"dudx": 0.0, "dudy": -1.0, "dvdx": 1.0, "dvdy": 0.0},
    "Incompressible extension": {"dudx": 1.0, "dudy": 0.0, "dvdx": 0.0, "dvdy": -1.0},
    "Dilatation (∇·u ≠ 0)": {"dudx": 1.0, "dudy": 0.0, "dvdx": 0.0, "dvdy": 1.0},
    "Custom": None,
}


def render_tab_stress_ns():
    """Render detailed step-by-step stress tensor and Navier-Stokes derivations."""
    fluid = get_fluid_state()
    st.markdown(
        """
        Euler's equation assumed fluids could sustain **only isotropic normal pressure**
        and zero friction. Real fluids undergo internal friction between adjacent layers
        moving at different velocities.

        To construct the complete governing equations of fluid motion, we proceed through
        three rigorous physical steps:
        1. Establish the **Cauchy stress tensor** $\\boldsymbol{\\sigma}$ on a differential element.
        2. Analyze fluid **kinematics** (strain rate vs. rigid rotation).
        3. Relate stress to deformation via the **Newtonian constitutive law**.
        """
    )
    render_objectives(
        [
            "Read $\\sigma_{ij}$: first index = face, second = traction direction.",
            "Split $\\nabla\\mathbf{u} = \\mathbf{D} + \\boldsymbol{\\Omega}$ and see that $\\boldsymbol{\\Omega}$ does no viscous work.",
            "Arrive at incompressible Navier–Stokes from Cauchy + Newton + $\\nabla\\cdot\\mathbf{u}=0$.",
        ]
    )

    # -------------------------------------------------------------------------
    # PART 1: The Infinitesimal Stress Cube & Cauchy Momentum
    # -------------------------------------------------------------------------
    st.markdown("### 6.1 The Infinitesimal Stress Cube & Cauchy Momentum Equation")
    st.markdown(
        """
        When fluid layers slide past one another, forces act both perpendicular (normal)
        and parallel (tangential/shear) to internal surfaces.
        """
    )

    render_svg(diagram_stress_tensor_cube())

    with st.container(border=True):
        st.markdown("**Stress tensor index nomenclature $\\sigma_{ij}$**")
        st.markdown("The Cauchy stress is a $3\\times 3$ matrix. On a chosen face, resolve the traction into one normal force per unit area and two tangential components. Pressure contributes only to the normal component; viscous stress can contribute to both.")
        st.latex(
            r"\boldsymbol{\sigma} = \begin{bmatrix}"
            r"\sigma_{xx} & \tau_{xy} & \tau_{xz} \\"
            r"\tau_{yx} & \sigma_{yy} & \tau_{yz} \\"
            r"\tau_{zx} & \tau_{zy} & \sigma_{zz}"
            r"\end{bmatrix}"
        )
        st.markdown(
            r"""
- **First index $i$:** orientation of the face (outward normal).
- **Second index $j$:** direction of the traction on that face.
- **Normal stresses** ($i=j$): $\sigma_{xx},\sigma_{yy},\sigma_{zz}$.
- **Shear stresses** ($i\neq j$): $\tau_{xy},\tau_{xz},\ldots$ (friction).
            """
        )

    with st.expander("🔍 Step-by-Step Proof: Stress Tensor Symmetry via Angular Momentum Conservation", expanded=False):
        render_prose_and_latex(
            r"""
            Consider an infinitesimal 2D element $dx \times dy$ in the $xy$-plane.
            Take the sum of torques about the center of the element:
            $$\sum M_z = I_z \alpha_z$$
            Here $\alpha_z$ is **angular acceleration** (rad/s²), not the kinetic-energy
            correction of Tabs 1–4.

            The shear stresses $\tau_{xy}$ (acting on the $+x$ face) and $-\tau_{xy}$ (on the $-x$ face) exert a counter-clockwise torque:
            $$T_{xy} = (\tau_{xy} \, dy) \cdot \left(\frac{dx}{2}\right) + (\tau_{xy} \, dy) \cdot \left(\frac{dx}{2}\right) = \tau_{xy} \, dx \, dy$$

            Similarly, the shear stresses $\tau_{yx}$ (acting on top and bottom faces) exert a clockwise torque:
            $$T_{yx} = -(\tau_{yx} \, dx) \cdot \left(\frac{dy}{2}\right) - (\tau_{yx} \, dx) \cdot \left(\frac{dy}{2}\right) = -\tau_{yx} \, dx \, dy$$

            The moment of inertia of the element is $I_z = \frac{1}{12} dm (dx^2 + dy^2) = \frac{1}{12}\rho dx dy (dx^2 + dy^2)$.
            Equating torque to rate of change of angular momentum:
            $$(\tau_{xy} - \tau_{yx}) \, dx \, dy = \frac{1}{12}\rho \, dx \, dy (dx^2 + dy^2) \alpha_z$$
            Dividing by the element area $dx \, dy$:
            $$\tau_{xy} - \tau_{yx} = \frac{1}{12}\rho (dx^2 + dy^2) \alpha_z$$

            As the element shrinks to a point ($dx \to 0, dy \to 0$):
            $$\tau_{xy} - \tau_{yx} = 0 \implies \tau_{xy} = \tau_{yx}$$
            **The Cauchy stress tensor is always symmetric ($\sigma_{ij} = \sigma_{ji}$) in any continuum without internal point body couples!**
            """
        )
        render_symbols(
            [
                (r"\alpha_z", r"angular acceleration about $z$ (rad/s²). **Not** the pipe kinetic-energy factor $\alpha$ of Tabs 1–4."),
                (r"M_z", "net torque about the element centre (N·m)."),
                (r"I_z", r"moment of inertia of the fluid element about $z$ (kg·m²)."),
                (r"\tau_{xy},\ \tau_{yx}", "shear tractions on the $x$ and $y$ faces (Pa)."),
            ]
        )

    with st.expander("🔍 Step-by-Step Derivation: Cauchy's Equation of Motion"):
        render_prose_and_latex(
            r"""
            Net force along the $x$-direction across all 6 faces of the differential box $dx \times dy \times dz$:
            $$dF_x = \left(\frac{\partial \sigma_{xx}}{\partial x}dx\right) dy dz + \left(\frac{\partial \tau_{yx}}{\partial y}dy\right) dx dz + \left(\frac{\partial \tau_{zx}}{\partial z}dz\right) dx dy + \rho g_x dx dy dz$$
            Dividing by the volume $dV = dx \, dy \, dz$:
            $$\rho \frac{Du}{Dt} = \frac{\partial \sigma_{xx}}{\partial x} + \frac{\partial \tau_{yx}}{\partial y} + \frac{\partial \tau_{zx}}{\partial z} + \rho g_x$$
            Using tensor divergence notation $\nabla \cdot \boldsymbol{\sigma}$:
            $$\rho \frac{D\mathbf{u}}{Dt} = \nabla \cdot \boldsymbol{\sigma} + \rho \mathbf{g}$$
            This is **Cauchy's Equation of Motion**—valid for *any* continuum (solids, gases, polymer melts, or water).
            """
        )

    # -------------------------------------------------------------------------
    # PART 2: Kinematic Decomposition
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 6.2 Kinematic Decomposition: Deformation vs. Rigid Rotation")
    st.markdown(
        """
        Why does a solid undergo stress proportional to **displacement** $\\mathbf{x}$,
        while a fluid undergoes stress proportional to **rate of deformation** $\\nabla \\mathbf{u}$?
        Because fluids cannot sustain static shear—they continuously deform!
        """
    )

    render_svg(diagram_kinematic_decomposition())

    st.markdown(":blue[**Velocity Gradient Tensor Decomposition:**]")
    st.latex(r"\nabla \mathbf{u} = \mathbf{D} + \mathbf{\Omega}")
    st.latex(r"\mathbf{D} = \frac{1}{2}\left[\nabla \mathbf{u} + (\nabla \mathbf{u})^T\right] \quad \text{(Strain-Rate Tensor: causes friction \& dissipation)}")
    st.latex(r"\mathbf{\Omega} = \frac{1}{2}\left[\nabla \mathbf{u} - (\nabla \mathbf{u})^T\right] \quad \text{(Spin / Vorticity Tensor: pure rigid rotation, ZERO stress)}")

    with st.expander("🔍 Geometric Insight: Why Pure Rotation (Ω) Generates Exactly Zero Viscous Stress"):
        render_prose_and_latex(
            r"""
            Consider a fluid parcel undergoing pure rigid-body rotation at angular velocity $\omega$:
            $$\mathbf{u} = \boldsymbol{\omega} \times \mathbf{r} = (-\omega y, \omega x, 0)$$
            The velocity gradient tensor is:
            $$\nabla \mathbf{u} = \begin{bmatrix} 0 & -\omega \\ \omega & 0 \end{bmatrix}$$
            Computing the strain-rate tensor $\mathbf{D}$:
            $$\mathbf{D} = \frac{1}{2}\left(\nabla \mathbf{u} + (\nabla \mathbf{u})^T\right) = \frac{1}{2}\left(\begin{bmatrix} 0 & -\omega \\ \omega & 0 \end{bmatrix} + \begin{bmatrix} 0 & \omega \\ -\omega & 0 \end{bmatrix}\right) = \begin{bmatrix} 0 & 0 \\ 0 & 0 \end{bmatrix} = \mathbf{0}$$
            Since $\mathbf{D} = \mathbf{0}$, no distances or angles between adjacent fluid molecules change!
            The fluid parcel simply pivots in space like a solid wheel.
            **Therefore, viscous friction depends exclusively on the symmetric strain-rate tensor $\mathbf{D}$, never on $\mathbf{\Omega}$!**
            """
        )

    # -------------------------------------------------------------------------
    # PART 3: The Newtonian Constitutive Law
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 6.3 The Newtonian Constitutive Law & Stokes' Hypothesis")
    render_prose_and_latex(
        """
        Sir Isaac Newton posited in 1687 that the shear resistance in a fluid is linearly
        proportional to the spatial velocity gradient: $\\tau = \\mu \\frac{du}{dy}$.

        Generalizing this to 3D isotropic fluids requires splitting total Cauchy stress into
        isotropic pressure and deviatoric viscous stress:
        $$\\boldsymbol{\\sigma} = -p \\mathbf{I} + \\boldsymbol{\\tau}$$
        """
    )

    with st.expander("🔍 Mathematical Formulation: From 1D Newton to 3D Stokes Constitutive Equation"):
        render_prose_and_latex(
            r"""
            For an isotropic linear viscous fluid, the stress tensor must be linear in strain-rate $\mathbf{D}$:
            $$\tau_{ij} = 2\mu D_{ij} + \lambda (\nabla \cdot \mathbf{u}) \delta_{ij}$$
            where:
            * $\mu$ is the **dynamic shear viscosity** (Pa·s).
            * $\lambda$ is the **second coefficient of viscosity** (Lamé's second fluid parameter).

            The mean mechanical normal stress is:
            $$\bar{\sigma} = \frac{1}{3}\operatorname{tr}(\boldsymbol{\sigma}) = -p + \left(\lambda + \frac{2}{3}\mu\right)(\nabla \cdot \mathbf{u})$$
            The quantity $\zeta = \lambda + \frac{2}{3}\mu$ is the **bulk viscosity** (associated with volume compression resistance).

            **Stokes' Hypothesis (1845):**
            George Gabriel Stokes hypothesized that for monatomic fluids and dilute gases, bulk viscosity vanishes:
            $$\zeta = 0 \implies \lambda = -\frac{2}{3}\mu$$
            For incompressible flows, $\nabla \cdot \mathbf{u} = 0$, so the dilatation term vanishes identically regardless of Stokes' hypothesis!
            $$\boldsymbol{\tau} = 2\mu \mathbf{D} = \mu \left(\nabla \mathbf{u} + (\nabla \mathbf{u})^T\right)$$
            """
        )

    render_derivation(
        r"why an isotropic linear fluid has exactly two viscosity coefficients",
        [
            (
                "Count the equations and see what is missing",
                r"""
                Cauchy's equation is three scalar equations, but the symmetric stress tensor
                carries six unknown components on top of the three velocities and the pressure.
                Conservation laws alone can never close this: they hold for water, honey,
                custard and steel alike, and those materials plainly behave differently. What
                is missing is a statement about **the material**, and that is what a
                constitutive law is.
                """,
            ),
            (
                "Three physical postulates, each of which can be argued from experience",
                r"""
                **(a) Stress depends on the rate of deformation, not on the deformation.**
                A solid pushed out of shape pushes back and remembers its original shape; a
                fluid does not. Left alone under a static shear stress a fluid simply keeps
                flowing, so the stress can only respond to $\nabla\mathbf u$, never to
                displacement.
                **(b) The dependence is linear.** This is Newton's experimental observation,
                and it is a *restriction*: §6.6 gives fluids that violate it.
                **(c) The fluid is isotropic.** Water has no grain, no fibres and no preferred
                direction, so the law must take the same form in every rotated frame.
                """,
            ),
            (
                r"Postulate (a) plus frame-indifference eliminates $\boldsymbol\Omega$",
                r"""
                Any linear function of $\nabla\mathbf u$ can be split as
                $\nabla\mathbf u=\mathbf D+\boldsymbol\Omega$. Suppose the stress responded to
                $\boldsymbol\Omega$. Then a bucket of water rotating steadily as a solid body
                would carry internal viscous stress — yet an observer rotating with the bucket
                sees still water, and no material can generate stress that depends on who is
                looking at it. So the viscous stress is a function of $\mathbf D$ only, which
                is the formal version of §6.2's geometric argument.
                """,
            ),
            (
                "Isotropy collapses a fourth-order tensor down to two numbers",
                r"""
                The most general linear map from a tensor to a tensor is
                $\tau_{ij}=C_{ijkl}D_{kl}$, with $81$ coefficients. Requiring $C$ to be
                **isotropic** — unchanged by every rotation — forces it into the only available
                isotropic form, built from products of Kronecker deltas:
                $$C_{ijkl}=\lambda\,\delta_{ij}\delta_{kl}
                +\mu\left(\delta_{ik}\delta_{jl}+\delta_{il}\delta_{jk}\right)$$
                Contracting with the symmetric $\mathbf D$ gives
                $$\boxed{\tau_{ij}=2\mu D_{ij}+\lambda\,(\nabla\cdot\mathbf u)\,\delta_{ij}}$$
                since $D_{kk}=\nabla\cdot\mathbf u$. Eighty-one numbers have become two, and no
                experiment can ever require a third for an isotropic linear fluid.
                """,
            ),
            (
                r"Fix $\mu$ by checking against Newton's own experiment",
                r"""
                Put simple shear $\mathbf u=(\dot\gamma y,0,0)$ into the result. Then
                $D_{xy}=\tfrac12\dot\gamma$ and $\nabla\cdot\mathbf u=0$, so
                $$\tau_{xy}=2\mu\cdot\tfrac12\dot\gamma=\mu\dot\gamma$$
                which is exactly $\tau=\mu\,du/dy$. The factor of $2$ in front of $\mathbf D$ is
                there precisely so that $\mu$ means what Newton measured in 1687 — it is not a
                stray coefficient.
                """,
            ),
            (
                r"Take the trace to find out what $\lambda$ is for",
                r"""
                The mechanical mean normal stress is one third of the trace of the **total**
                stress. Using $\operatorname{tr}(\mathbf I)=3$ and
                $\operatorname{tr}(\mathbf D)=\nabla\cdot\mathbf u$:
                $$\bar\sigma=\tfrac13\operatorname{tr}(\boldsymbol\sigma)
                =-p+\tfrac13\left(2\mu+3\lambda\right)(\nabla\cdot\mathbf u)
                =-p+\underbrace{\left(\lambda+\tfrac23\mu\right)}_{\textstyle\zeta}(\nabla\cdot\mathbf u)$$
                So the thermodynamic pressure and the average of what a gauge would feel differ
                **only when the fluid is changing volume**. $\zeta$ is the bulk viscosity: a
                resistance to the *rate* of compression, quite distinct from the bulk modulus,
                which resists the *amount*.
                """,
            ),
            (
                "Stokes' hypothesis, and when you are allowed to stop caring",
                r"""
                Stokes proposed $\zeta=0$, i.e. $\lambda=-\tfrac23\mu$, which is exact for a
                dilute monatomic gas and approximate otherwise; where $\zeta$ matters at all it
                matters for sound absorption and shock thickness. For **incompressible** flow
                $\nabla\cdot\mathbf u=0$ kills the whole term regardless of what $\lambda$ is,
                which is why the rest of this course never mentions it again:
                $$\boldsymbol\tau=2\mu\mathbf D
                =\mu\left(\nabla\mathbf u+(\nabla\mathbf u)^{T}\right)$$
                """,
            ),
        ],
    )

    # -------------------------------------------------------------------------
    # PART 4: Arriving at Navier–Stokes
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 6.4 The Incompressible Navier–Stokes Equations")
    st.markdown(
        r"""
        Substituting the Newtonian constitutive law $\boldsymbol{\sigma} = -p\mathbf{I} + 2\mu \mathbf{D}$
        into Cauchy's momentum equation $\rho \frac{D\mathbf{u}}{Dt} = \nabla \cdot \boldsymbol{\sigma} + \rho \mathbf{g}$:
        """
    )

    render_derivation(
        r"taking the divergence of the stress, index by index",
        [
            (
                "Split the stress before differentiating",
                r"""
                $$\nabla\cdot\boldsymbol\sigma
                =\nabla\cdot(-p\mathbf I)+\nabla\cdot(2\mu\mathbf D)$$
                The first piece is easy in components: $\partial_j(-p\,\delta_{ij})
                =-\partial_i p$, i.e. $-\nabla p$. A fluid element is pushed by the
                **gradient** of pressure, not by pressure itself — uniform pressure squeezes
                a parcel equally from all sides and moves it nowhere.
                """,
            ),
            (
                "Write the viscous term in indices and split the two derivatives",
                r"""
                With constant $\mu$, and $2D_{ij}=\partial_ju_i+\partial_iu_j$:
                $$\left[\nabla\cdot(2\mu\mathbf D)\right]_i
                =\mu\,\partial_j\left(\partial_ju_i+\partial_iu_j\right)
                =\mu\,\underbrace{\partial_j\partial_ju_i}_{\nabla^{2}u_i}
                +\mu\,\partial_j\partial_iu_j$$
                """,
            ),
            (
                "Swap the order of the mixed derivative — the step that does the work",
                r"""
                Partial derivatives of a smooth field commute, so in the second term
                $\partial_j\partial_i u_j=\partial_i\left(\partial_ju_j\right)
                =\partial_i(\nabla\cdot\mathbf u)$. Hence in general
                $$\nabla\cdot(2\mu\mathbf D)=\mu\left[\nabla^{2}\mathbf u
                +\nabla(\nabla\cdot\mathbf u)\right]$$
                Both terms come from viscosity; the second is the resistance to *compressing*
                rather than to *shearing*.
                """,
            ),
            (
                "Impose incompressibility and read the surviving operator",
                r"""
                $\nabla\cdot\mathbf u=0$ deletes the second term outright:
                $$\nabla\cdot(2\mu\mathbf D)=\mu\nabla^{2}\mathbf u$$
                and substituting into Cauchy gives Navier–Stokes. The Laplacian is worth
                recognising for what it is: the **same operator that appears in heat
                conduction and in Fick diffusion**. Viscosity diffuses momentum exactly as
                conductivity diffuses heat, with $\nu=\mu/\rho$ playing the part of thermal
                diffusivity — which is the formal basis of the transport analogy used in
                Tab 3 and Tab 8.
                """,
            ),
        ],
    )

    st.markdown(":blue[**Incompressible Navier–Stokes Equations:**]")
    st.latex(r"\rho \underbrace{\left(\frac{\partial \mathbf{u}}{\partial t} + (\mathbf{u}\cdot\nabla)\mathbf{u}\right)}_{\text{Inertial Acceleration}} = \underbrace{-\nabla p}_{\text{Pressure Force}} + \underbrace{\mu \nabla^2 \mathbf{u}}_{\text{Viscous Diffusion}} + \underbrace{\rho \mathbf{g}}_{\text{Body Force}}")
    st.latex(r"\text{Continuity (Mass Conservation): } \quad \nabla \cdot \mathbf{u} = 0")

    render_self_check(
        "stress_self_check_omega",
        "A fluid parcel in pure rigid rotation ($\\mathbf{D}=0$, $\\boldsymbol{\\Omega}\\neq 0$) experiences…",
        [
            "viscous shear because it is spinning",
            "zero viscous stress — only D dissipates",
            "a pressure equal to μω",
        ],
        "zero viscous stress — only D dissipates",
        "Newtonian viscous stress is 2μD. Rigid rotation does not change distances between neighboring particles.",
    )

    # -------------------------------------------------------------------------
    # PART 5: Interactive Fluid Element Deformation Lab
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 6.5 Interactive Fluid Element Deformation Lab")
    st.markdown(
        """
        Start from a kinematic **preset**, then inspect $\\mathbf{D}$, $\\boldsymbol{\\Omega}$,
        and Mohr's circle. Custom sliders are for exploration after the presets.
        """
    )

    preset_name = persistent_input(st.selectbox, "Kinematic preset", options=list(KINEMATIC_PRESETS.keys()), key="tab_stress_ns_kinematic_preset")
    preset = KINEMATIC_PRESETS[preset_name]
    last_key = "stress_preset_last"
    if last_key not in st.session_state:
        st.session_state[last_key] = preset_name
        if preset is not None:
            for key, val in preset.items():
                st.session_state[f"stress_{key}"] = float(val)
    elif preset_name != st.session_state[last_key]:
        if preset is not None:
            for key, val in preset.items():
                st.session_state[f"stress_{key}"] = float(val)
        st.session_state[last_key] = preset_name

    col_sl1, col_sl2, col_sl3, col_sl4 = st.columns(4)
    with col_sl1:
        dudx = persistent_input(st.slider, "∂u/∂x [1/s] (Normal strain)", min_value=-2.0, max_value=2.0, step=0.1, key="stress_dudx")
    with col_sl2:
        dudy = persistent_input(st.slider, "∂u/∂y [1/s] (Shear rate)", min_value=-2.0, max_value=2.0, step=0.1, key="stress_dudy")
    with col_sl3:
        dvdx = persistent_input(st.slider, "∂v/∂x [1/s] (Shear rate)", min_value=-2.0, max_value=2.0, step=0.1, key="stress_dvdx")
    with col_sl4:
        dvdy = persistent_input(st.slider, "∂v/∂y [1/s] (Normal strain)", min_value=-2.0, max_value=2.0, step=0.1, key="stress_dvdy")

    col_prop1, col_prop2 = st.columns(2)
    with col_prop1:
        mu_default = float(np.clip(fluid["mu"], 0.001, 0.1))
        mu_val = persistent_input(st.slider,
            "Dynamic Viscosity μ [Pa·s]",
            min_value=0.001,
            max_value=0.1,
            value=mu_default,
            step=0.005,
            help=f"Sidebar fluid μ = {fluid['mu']:.3e} Pa·s. This slider is capped for Mohr-circle readability.", key="tab_stress_ns_dynamic_viscosity_pa_s")
    with col_prop2:
        p_val_kpa = persistent_input(st.slider, "Hydrostatic Pressure p [kPa]", min_value=10.0, max_value=200.0, value=101.3, step=5.0, key="tab_stress_ns_hydrostatic_pressure_p_kpa")

    decomp = decompose_velocity_gradient_2d(dudx, dudy, dvdx, dvdy)
    deform_res = deform_fluid_element_2d(dudx, dudy, dvdx, dvdy, dt=0.25)
    stress_res = compute_cauchy_stress_2d(dudx, dudy, dvdx, dvdy, mu=mu_val, p=p_val_kpa * 1000.0)

    dilation = float(decomp["dilation"])
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    col_k1.metric("Volumetric Dilatation ∇·u", f"{dilation:.2f} 1/s", help="0 for incompressible fluids")
    col_k2.metric("Angular Shear Rate D_xy", f"{0.5*(dudy + dvdx):.2f} 1/s")
    col_k3.metric("Vorticity ω_z", f"{dvdx - dudy:.2f} 1/s")
    col_k4.metric("Max Shear Stress τ_max", format_quantity(float(stress_res["max_shear"]), "shear_stress"))

    if abs(dilation) > 1e-6:
        st.warning(
            "∇·u ≠ 0: this parcel is changing volume. The incompressible Navier–Stokes "
            "equation derived above assumed ∇·u = 0; the constitutive law here still includes "
            "the dilatation term (Stokes λ = −2μ/3)."
        )
    matches_preset = preset is not None and all(
        np.isclose(value, preset[key]) for key, value in
        dict(dudx=dudx, dudy=dudy, dvdx=dvdx, dvdy=dvdy).items()
    )
    if matches_preset and preset_name.startswith("Pure rotation"):
        render_what_to_notice("D is zero: the green D-only outline stays square, while the full parcel rotates without changing shape or area. Mohr's circle collapses to a point at −p. Changing pressure moves that point without creating shear.")
    elif matches_preset and preset_name.startswith("Simple shear"):
        render_what_to_notice("The parcel shears into a parallelogram. Both D and Ω are nonzero: simple shear combines instantaneous strain and spin. Their finite-time outlines are separate comparison flows, not shapes to add together.")
    elif matches_preset and preset_name.startswith("Pure shear"):
        render_what_to_notice("Ω is zero. The full and D-only outlines coincide: stretch along one diagonal and compression along the other preserve area, with no rigid spin.")
    elif matches_preset and preset_name.startswith("Incompressible"):
        render_what_to_notice("Extension in x, compression in y, area preserved. This is an incompressible straining motion.")
    else:
        render_what_to_notice("Dashed square = t₀. Filled = full L. Dotted green = the D-only comparison flow. Dash-dot orange = the Ω-only rigid rotation. Read the matrices for the current slider values.")

    render_prose_and_latex(r'''The geometry follows a constant velocity gradient for Δt = 0.25 s:
$$\frac{d\mathbf x}{dt}=\mathbf L\mathbf x,\qquad \mathbf x(t)=e^{\mathbf L t}\mathbf x(0),\qquad \frac{A(t)}{A(0)}=e^{\mathrm{tr}(\mathbf L)t}.$$
Thus zero divergence preserves area exactly. The D-only and Ω-only outlines solve two separate flows. In general, their finite-time maps cannot be added or simply composed to recover the full motion.''')
    st.caption(f"Computed area ratio A(t)/A(0) = {deform_res['area_ratio']:.6f}. Mohr's circle below uses Pa relative to the mean normal stress, so small viscous stresses remain visible. Changing pressure shifts the mean, while leaving the radius unchanged.")

    D = decomp["D"]
    Omega = decomp["Omega"]
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown("**Strain-rate $\\mathbf{D}$ (1/s)**")
        st.dataframe(
            {"x": [f"{D[0,0]:.2f}", f"{D[1,0]:.2f}"], "y": [f"{D[0,1]:.2f}", f"{D[1,1]:.2f}"]},
            hide_index=True,
        )
    with col_m2:
        st.markdown("**Spin $\\boldsymbol{\\Omega}$ (1/s)**")
        st.dataframe(
            {"x": [f"{Omega[0,0]:.2f}", f"{Omega[1,0]:.2f}"], "y": [f"{Omega[0,1]:.2f}", f"{Omega[1,1]:.2f}"]},
            hide_index=True,
        )

    fig_deform = plot_fluid_element_deformation(deform_res, stress_res)
    render_plot(fig_deform, key="tab_stress_ns-fig_deform")

    # -------------------------------------------------------------------------
    # PART 6: Where the Newtonian law stops, and what replaces it
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 6.6 The one assumption still unpaid for")
    render_prose_and_latex(
        r"""
        Everything above followed from balances: the Cauchy stress from a force
        balance on a tetrahedron, the decomposition
        $\nabla\mathbf{u}=\mathbf{D}+\boldsymbol{\Omega}$ from algebra, the
        momentum equation from Newton's second law. Only the last step,
        $\boldsymbol{\sigma}=-p\mathbf{I}+2\mu\mathbf{D}$, was a **choice** — the
        simplest law that is linear in $\mathbf{D}$, isotropic, and depends on the
        strain rate at this instant alone.

        That choice is a claim about the fluid's microstructure, and it is false for
        paint, blood, ketchup, drilling mud, molten polymer and wet cement. The next
        chapter takes it apart: where $\mu$ comes from, which structures break the
        linearity, what a yield stress does to the pipe profile of Chapter 4, and how
        elastic memory produces stresses this equation cannot represent at all.
        """
    )
    render_svg(diagram_power_law())
    st.caption(
        "The pipe momentum balance τ_w = (R/2)(−dp/dz) is unchanged for every one of these "
        "curves — only the kinematics differ. Chapter 7 derives the profiles, the unyielded "
        "plug and the Metzner–Reed Reynolds number, and runs the power-law and yield-stress labs."
    )
    render_self_check(
        "pl_self_check_n1",
        "When n = 1, the power-law pipe must recover…",
        [
            "a 1/7th-power turbulent profile",
            "Hagen–Poiseuille, with u_max / u_avg = 2",
            "zero wall shear",
        ],
        "Hagen–Poiseuille, with u_max / u_avg = 2",
        "n=1, K=μ is Newton. Momentum still gives τ_w = R Δp /(2L); the parabola is the kinematics.",
    )
