"""UI module for Panel 3: Stress Tensor, Constitutive Equations & Navier-Stokes."""

import streamlit as st
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
from src.physics.non_newtonian import power_law_pipe
from src.physics.exact_solutions import hagen_poiseuille_pipe
from src.plotting import plot_fluid_element_deformation, plot_power_law_pipe
from src.units import format_quantity, get_fluid_state
from src.ui.pedagogy import render_objectives, render_what_to_notice, render_self_check


KINEMATIC_PRESETS = {
    "Pure shear (Couette-like)": {"dudx": 0.0, "dudy": 1.0, "dvdx": 0.0, "dvdy": 0.0},
    "Pure rotation (rigid)": {"dudx": 0.0, "dudy": -1.0, "dvdx": 1.0, "dvdy": 0.0},
    "Incompressible extension": {"dudx": 1.0, "dudy": 0.0, "dvdx": 0.0, "dvdy": -1.0},
    "Dilatation (∇·u ≠ 0)": {"dudx": 1.0, "dudy": 0.0, "dvdx": 0.0, "dvdy": 1.0},
    "Custom": None,
}


def render_tab_stress_ns():
    """Render detailed step-by-step stress tensor and Navier-Stokes derivations."""
    fluid = get_fluid_state()
    st.markdown("## 6. Incorporating Stress, Constitutive Equations & Navier–Stokes")
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
        st.markdown("The Cauchy stress is a $3\\times 3$ matrix. Streamlit does not render KaTeX inside `st.info` / raw HTML.")
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

    with st.expander("🔍 Step-by-Step Proof: Stress Tensor Symmetry via Angular Momentum Conservation", expanded=True):
        st.markdown(
            r"""
            Consider an infinitesimal 2D element $dx \times dy$ in the $xy$-plane.
            Take the sum of torques about the center of the element:
            $$\sum M_z = I_z \alpha_z$$

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

    with st.expander("🔍 Step-by-Step Derivation: Cauchy's Equation of Motion"):
        st.markdown(
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
        st.markdown(
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
    st.markdown(
        """
        Sir Isaac Newton posited in 1687 that the shear resistance in a fluid is linearly
        proportional to the spatial velocity gradient: $\\tau = \\mu \\frac{du}{dy}$.

        Generalizing this to 3D isotropic fluids requires splitting total Cauchy stress into
        isotropic pressure and deviatoric viscous stress:
        $$\\boldsymbol{\\sigma} = -p \\mathbf{I} + \\boldsymbol{\\tau}$$
        """
    )

    with st.expander("🔍 Mathematical Formulation: From 1D Newton to 3D Stokes Constitutive Equation"):
        st.markdown(
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

    with st.expander("🔍 Vector Calculus Step: Divergence of the Viscous Stress Tensor"):
        st.markdown(
            r"""
            $$\nabla \cdot \boldsymbol{\sigma} = \nabla \cdot (-p\mathbf{I}) + \nabla \cdot (2\mu \mathbf{D})$$
            $$\nabla \cdot (-p\mathbf{I}) = -\nabla p$$
            For constant viscosity $\mu$:
            $$\nabla \cdot (2\mu \mathbf{D}) = \mu \nabla \cdot \left(\nabla \mathbf{u} + (\nabla \mathbf{u})^T\right) = \mu \left[\nabla^2 \mathbf{u} + \nabla(\nabla \cdot \mathbf{u})\right]$$
            Since the fluid is incompressible ($\nabla \cdot \mathbf{u} = 0$):
            $$\nabla \cdot (2\mu \mathbf{D}) = \mu \nabla^2 \mathbf{u}$$
            Combining terms yields the famous Navier–Stokes momentum equation!
            """
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

    for key, val in {"dudx": 0.0, "dudy": 1.0, "dvdx": 0.0, "dvdy": 0.0}.items():
        st.session_state.setdefault(f"stress_{key}", float(val))

    preset_name = st.selectbox("Kinematic preset", options=list(KINEMATIC_PRESETS.keys()))
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
        dudx = st.slider("∂u/∂x [1/s] (Normal strain)", min_value=-2.0, max_value=2.0, step=0.1, key="stress_dudx")
    with col_sl2:
        dudy = st.slider("∂u/∂y [1/s] (Shear rate)", min_value=-2.0, max_value=2.0, step=0.1, key="stress_dudy")
    with col_sl3:
        dvdx = st.slider("∂v/∂x [1/s] (Shear rate)", min_value=-2.0, max_value=2.0, step=0.1, key="stress_dvdx")
    with col_sl4:
        dvdy = st.slider("∂v/∂y [1/s] (Normal strain)", min_value=-2.0, max_value=2.0, step=0.1, key="stress_dvdy")

    col_prop1, col_prop2 = st.columns(2)
    with col_prop1:
        mu_default = float(np.clip(fluid["mu"], 0.001, 0.1))
        mu_val = st.slider(
            "Dynamic Viscosity μ [Pa·s]",
            min_value=0.001,
            max_value=0.1,
            value=mu_default,
            step=0.005,
            help=f"Sidebar fluid μ = {fluid['mu']:.3e} Pa·s. This slider is capped for Mohr-circle readability.",
        )
    with col_prop2:
        p_val_kpa = st.slider("Hydrostatic Pressure p [kPa]", min_value=10.0, max_value=200.0, value=101.3, step=5.0)

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
    if preset_name.startswith("Pure rotation"):
        render_what_to_notice("D is the zero matrix — the green 'pure strain' outline stays square. τ_max is only the hydrostatic Mohr radius from p.")
    elif preset_name.startswith("Pure shear"):
        render_what_to_notice("The parcel shears into a parallelogram. Ω is nonzero too (vorticity = −∂u/∂y): simple shear is half strain, half spin.")
    elif preset_name.startswith("Incompressible"):
        render_what_to_notice("Extension in x, compression in y, area preserved. This is an incompressible straining motion.")
    else:
        render_what_to_notice("Dashed square = t₀. Filled = full L. Dotted green = strain D only (no rotation).")

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
    st.plotly_chart(fig_deform, width="stretch")

    # -------------------------------------------------------------------------
    # PART 6: Power-law constitutive
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 6.6 Non-Newtonian Constitutive Law: Power-Law Pipe Flow")
    st.markdown(
        r"""
        Newtonian stress is $\boldsymbol{\tau} = 2\mu\mathbf{D}$ with $\mu$ constant.
        Many ChemE fluids are **Ostwald–de Waele** (power-law):
        $$\tau = K |\dot{\gamma}|^{n-1}\dot{\gamma}$$
        $n=1, K=\mu$ recovers Newton. $n<1$ shear-thinning (polymer melts, blood);
        $n>1$ shear-thickening (slurries). The validity matrix in the Reference tab
        lists this as the Newtonian failure mode — here is the replacement law.
        """
    )
    render_svg(diagram_power_law())
    col_n1, col_n2, col_n3 = st.columns(3)
    with col_n1:
        n_pl = st.slider("Power-law index n", min_value=0.3, max_value=1.7, value=0.7, step=0.05, key="pl_n")
    with col_n2:
        k_pl = st.number_input(
            "Consistency K [Pa·sⁿ]",
            min_value=1e-4,
            max_value=10.0,
            value=max(float(fluid["mu"]), 1e-3),
            format="%.4f",
            key="pl_K",
        )
    with col_n3:
        pl_dp = st.slider("dp/dz [Pa/m]", min_value=-80.0, max_value=-5.0, value=-20.0, step=5.0, key="pl_dp")
    pl_R = 0.025
    pl_res = power_law_pipe(
        radius=pl_R, dp_dz=pl_dp, K=float(k_pl), n=float(n_pl), rho=float(fluid["rho"])
    )
    newt = hagen_poiseuille_pipe(
        radius=pl_R, dp_dx=pl_dp, mu=float(fluid["mu"]), rho=float(fluid["rho"])
    )
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    col_p1.metric("u_max / u_avg", f"{pl_res['ratio_max_avg']:.2f}", help="2.00 when n = 1")
    col_p2.metric("Re_MR (Metzner–Reed)", f"{pl_res['re_mr']:.1f}")
    col_p3.metric("μ_app at wall", f"{pl_res['mu_apparent']:.3e} Pa·s")
    col_p4.metric("f_D = 64/Re_MR", f"{pl_res['f_darcy']:.4f}" if pl_res["laminar"] else "not laminar")
    if not pl_res["laminar"]:
        st.warning("Re_MR ≥ 2100: the laminar power-law profile and f = 64/Re_MR no longer apply.")
    st.caption(
        f"Same wall shear τ_w = R(−dp/dz)/2 = {pl_res['tau_wall']:.3f} Pa as the dashed Newtonian overlay "
        f"(sidebar μ = {fluid['mu']:.3e} Pa·s). Thinning (n<1) blunts the core like a turbulent pipe; "
        "thickening (n>1) sharpens the apex."
    )
    render_what_to_notice(
        "n = 1 and K = μ must sit on the Newtonian parabola. n < 1 is flatter (plug-like). Tab 2 can use this Δp for laminar polymer lines."
    )
    fig_pl = plot_power_law_pipe(pl_res, newt)
    st.plotly_chart(fig_pl, width="stretch")
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
