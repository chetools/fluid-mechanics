"""UI module for Reference, Mathematical Nomenclature, and Validity Matrix."""

import streamlit as st
import pandas as pd
from src.ui.pedagogy import render_prose_and_latex
from src.svg_diagrams import diagram_model_selection, render_svg

def render_tab_reference():
    """Render reference, tensor guide, and assumption validity matrix."""
    render_svg(diagram_model_selection(), "Start from the quantity you need, then check the assumptions. The table below gives the detailed limits of each model.")
    
    ref_tab1, ref_tab2, ref_tab3 = st.tabs([
        "📖 1. Nomenclature & Units",
        "🧮 2. Tensor Notation Primer",
        "⚖️ 3. Assumption & Validity Matrix"
    ])
    
    with ref_tab1:
        st.markdown("### Complete Mathematical Nomenclature")
        nom_data = [
            {"Symbol": "u, v, w", "Quantity": "Velocity vector components", "SI Units": "m/s", "Dimensions": "[L T⁻¹]"},
            {"Symbol": "ū, u_avg", "Quantity": "Area-mean speed Q/A", "SI Units": "m/s", "Dimensions": "[L T⁻¹]"},
            {"Symbol": "p", "Quantity": "Thermodynamic static pressure", "SI Units": "Pa = N/m²", "Dimensions": "[M L⁻¹ T⁻²]"},
            {"Symbol": "ρ", "Quantity": "Fluid mass density", "SI Units": "kg/m³", "Dimensions": "[M L⁻³]"},
            {"Symbol": "μ", "Quantity": "Dynamic shear viscosity", "SI Units": "Pa·s = kg/(m·s)", "Dimensions": "[M L⁻¹ T⁻¹]"},
            {"Symbol": "ν", "Quantity": "Kinematic viscosity (ν = μ/ρ)", "SI Units": "m²/s", "Dimensions": "[L² T⁻¹]"},
            {"Symbol": "g", "Quantity": "Gravitational acceleration", "SI Units": "m/s²", "Dimensions": "[L T⁻²]"},
            {"Symbol": "z", "Quantity": "Elevation above a datum", "SI Units": "m", "Dimensions": "[L]"},
            {"Symbol": "α (pipe)", "Quantity": "Kinetic-energy correction (1/A)∫(u/ū)³ dA. Circular pipe: 2 laminar, ≈1.05 turbulent. Not an angle.", "SI Units": "[-]", "Dimensions": "[1]"},
            {"Symbol": "α_z (Tab 6)", "Quantity": "Angular acceleration about z (stress-symmetry proof). Not the pipe α.", "SI Units": "rad/s²", "Dimensions": "[T⁻²]"},
            {"Symbol": "w_shaft", "Quantity": "Shaft work per unit mass (pump positive)", "SI Units": "J/kg", "Dimensions": "[L² T⁻²]"},
            {"Symbol": "h_shaft", "Quantity": "Pump head w_shaft/g", "SI Units": "m", "Dimensions": "[L]"},
            {"Symbol": "h_f", "Quantity": "Major (skin-friction) head loss", "SI Units": "m", "Dimensions": "[L]"},
            {"Symbol": "h_minor", "Quantity": "Fitting/entrance/exit head loss Σ K_L u²/(2g)", "SI Units": "m", "Dimensions": "[L]"},
            {"Symbol": "e_f", "Quantity": "Lost mechanical work per unit mass; e_f/g = h_f + h_minor", "SI Units": "J/kg", "Dimensions": "[L² T⁻²]"},
            {"Symbol": "Φ", "Quantity": "Viscous dissipation 2μ D:D", "SI Units": "W/m³", "Dimensions": "[M L⁻¹ T⁻³]"},
            {"Symbol": "f_D", "Quantity": "Darcy friction factor (Moody). Laminar pipe: 64/Re", "SI Units": "[-]", "Dimensions": "[1]"},
            {"Symbol": "f_F", "Quantity": "Fanning friction factor = f_D/4. Laminar pipe: 16/Re", "SI Units": "[-]", "Dimensions": "[1]"},
            {"Symbol": "ε", "Quantity": "Equivalent sand-grain roughness", "SI Units": "m", "Dimensions": "[L]"},
            {"Symbol": "A_Ch, B_Ch", "Quantity": "Churchill (1977) auxiliary groups (not area A)", "SI Units": "[-]", "Dimensions": "[1]"},
            {"Symbol": "D_H", "Quantity": "Hydraulic diameter 4A/P_w", "SI Units": "m", "Dimensions": "[L]"},
            {"Symbol": "NPSH_A / NPSH_R", "Quantity": "Available / required net positive suction head", "SI Units": "m", "Dimensions": "[L]"},
            {"Symbol": "σ_ij", "Quantity": "Cauchy stress tensor", "SI Units": "Pa", "Dimensions": "[M L⁻¹ T⁻²]"},
            {"Symbol": "τ_ij", "Quantity": "Viscous deviatoric stress tensor", "SI Units": "Pa", "Dimensions": "[M L⁻¹ T⁻²]"},
            {"Symbol": "D_ij", "Quantity": "Strain-rate tensor (symmetric)", "SI Units": "1/s", "Dimensions": "[T⁻¹]"},
            {"Symbol": "Ω_ij", "Quantity": "Spin / rotation tensor (anti-symmetric)", "SI Units": "1/s", "Dimensions": "[T⁻¹]"},
            {"Symbol": "ω", "Quantity": "Vorticity vector (curl of velocity)", "SI Units": "1/s", "Dimensions": "[T⁻¹]"},
            {"Symbol": "ψ", "Quantity": "Streamfunction", "SI Units": "m²/s", "Dimensions": "[L² T⁻¹]"},
            {"Symbol": "Re", "Quantity": "Reynolds number (ρUL/μ)", "SI Units": "[-]", "Dimensions": "[1] (Dimensionless)"},
            {"Symbol": "Eu", "Quantity": "Euler number Δp/(ρ u²)", "SI Units": "[-]", "Dimensions": "[1]"},
            {"Symbol": "Ma", "Quantity": "Mach number (u/a)", "SI Units": "[-]", "Dimensions": "[1] (Dimensionless)"},
            {"Symbol": "CFL", "Quantity": "Courant–Friedrichs–Lewy number (u·Δt/Δx)", "SI Units": "[-]", "Dimensions": "[1] (Dimensionless)"},
        ]
        st.caption(
            "α in Tabs 1–4 and 7 is the kinetic-energy correction, never an angle. "
            "Tab 6's α_z is angular acceleration in the stress-symmetry proof. "
            "Churchill's A_Ch, B_Ch are not area."
        )
        st.dataframe(pd.DataFrame(nom_data), width="stretch", hide_index=True)
        
    with ref_tab2:
        st.markdown("### Tensor Calculus Primer for Fluid Mechanics")
        render_prose_and_latex(
            r"""
            In modern continuum mechanics, equations are written in **index notation** with 
            the **Einstein Summation Convention**: whenever an index is repeated in a single term, 
            summation over $\{1, 2, 3\}$ is implied!

            1. **Velocity Vector:**
               $$u_i = (u_1, u_2, u_3) = (u, v, w)$$
            2. **Gradient Operator:**
               $$\frac{\partial}{\partial x_i} = \left(\frac{\partial}{\partial x}, \frac{\partial}{\partial y}, \frac{\partial}{\partial z}\right)$$
            3. **Divergence (Scalar Incompressibility):**
               $$\nabla \cdot \mathbf{u} = \frac{\partial u_i}{\partial x_i} = \frac{\partial u_1}{\partial x_1} + \frac{\partial u_2}{\partial x_2} + \frac{\partial u_3}{\partial x_3} = 0$$
            4. **Convective Acceleration Term:**
               $$[(\mathbf{u}\cdot\nabla)\mathbf{u}]_i = u_j \frac{\partial u_i}{\partial x_j}$$
            5. **Kronecker Delta $\delta_{ij}$:**
               $$\delta_{ij} = \begin{cases} 1 & \text{if } i = j \\ 0 & \text{if } i \neq j \end{cases}$$
            6. **Levi-Civita Permutation Tensor $\epsilon_{ijk}$ (Vorticity & Cross Products):**
               $$\omega_i = [\nabla \times \mathbf{u}]_i = \epsilon_{ijk} \frac{\partial u_k}{\partial x_j}$$
            7. **Complete Incompressible Navier–Stokes in Index Notation:**
               $$\rho \left(\frac{\partial u_i}{\partial t} + u_j \frac{\partial u_i}{\partial x_j}\right) = -\frac{\partial p}{\partial x_i} + \mu \frac{\partial^2 u_i}{\partial x_j \partial x_j} + \rho g_i$$
            """
        )
        
    with ref_tab3:
        st.markdown("### Assumption, Consequence & Failure-Mode Matrix")
        matrix_data = [
            {
                "Model": "Inviscid Euler",
                "Key Assumption": "μ = 0 (Zero viscosity)",
                "Physical Consequence": "Slip allowed at walls, no vorticity generated at boundaries",
                "Failure Mode": "Misses viscous wall layers. Zero drag follows only for steady, irrotational ideal flow under d'Alembert's assumptions."
            },
            {
                "Model": "Stokes Creeping Flow",
                "Key Assumption": "Re ≪ 1 (Neglect (u·∇)u)",
                "Physical Consequence": "Linear momentum equations; steady creeping-flow kinematics are reversible",
                "Failure Mode": "Stokes' Paradox in 2D (no steady solution around cylinder without inertia); breaks at high speed"
            },
            {
                "Model": "Incompressible Navier–Stokes",
                "Key Assumption": "ρ = const (Ma < 0.3)",
                "Physical Consequence": "Pressure acts instantaneously as an elliptic Lagrange multiplier",
                "Failure Mode": "Cannot model acoustic sound waves, sonic booms, or supersonic shock waves"
            },
            {
                "Model": "Newtonian Constitutive Law",
                "Key Assumption": "Linear stress-strain rate relation",
                "Physical Consequence": "Constant viscosity μ independent of shear rate",
                "Failure Mode": "Fails for blood, polymer melts, cornstarch (shear thinning / thickening viscoelastic fluids)"
            },
            {
                "Model": "Pipe Re = 2300 / 4000",
                "Key Assumption": "Circular pipe, fully developed, Newtonian",
                "Physical Consequence": "Osborne Reynolds' dye-streak thresholds",
                "Failure Mode": "Wrong for cavities, cylinders, plates, and non-circular ducts without D_H caveats"
            },
            {
                "Model": "Ghia cavity overlay",
                "Key Assumption": "Steady 2D NS at the tabulated Re (here Re = 100)",
                "Physical Consequence": "Centerline u(y) as a code-verification target",
                "Failure Mode": "A short explicit run (t* ≪ viscous time) is spin-up, not a match"
            },
            {
                "Model": "Blasius plate BL",
                "Key Assumption": "Steady 2D laminar, zero pressure gradient, large Re_x",
                "Physical Consequence": "δ/x ≈ 4.91/√Re_x, c_f = 0.664/√Re_x, finite drag",
                "Failure Mode": "Separates in any strong adverse dp/dx; not a cylinder or turbulent plate"
            },
            {
                "Model": "Power-law pipe (Ostwald–de Waele)",
                "Key Assumption": "τ = K γ̇^n, fully developed, Re_MR < ~2100",
                "Physical Consequence": "u_max/u_avg = (3n+1)/(n+1); f_D = 64/Re_MR",
                "Failure Mode": "No yield stress (Bingham), no elasticity, not a turbulent correlation"
            },
            {
                "Model": "NPSH_A tank formula",
                "Key Assumption": "Single free surface, incompressible liquid, P_v at bulk T",
                "Physical Consequence": "Cavitation when NPSH_A < NPSH_R",
                "Failure Mode": "Dissolved gas, hot spots, and two-phase suction lines need extra margin"
            }
        ]
        st.dataframe(pd.DataFrame(matrix_data), width="stretch", hide_index=True)
        
        st.markdown("---")
        st.markdown("### Authoritative Textbook References")
        render_prose_and_latex(
            """
            * **Batchelor, G. K.** (1967). *An Introduction to Fluid Dynamics*. Cambridge University Press.
            * **Bird, R. B., Stewart, W. E., & Lightfoot, E. N.** (2002). *Transport Phenomena* (2nd ed.). John Wiley & Sons. (Fanning $f_F$, BSL notation.)
            * **Kundu, P. K., Cohen, I. M., & Dowling, D. R.** (2015). *Fluid Mechanics* (6th ed.). Academic Press.
            * **White, F. M.** (2011). *Viscous Fluid Flow* (3rd ed.). McGraw-Hill.
            * **Crane Co.** (1988). *Flow of Fluids Through Valves, Fittings, and Pipe* (Technical Paper No. 410).
            * **Churchill, S. W.** (1977). *Friction-factor equation spans all fluid-flow regimes*. Chemical Engineering, 84(24), 91-92.
            * **Chorin, A. J.** (1968). *Numerical solution of the Navier-Stokes equations*. Mathematics of Computation, 22(104), 745-762.
            * **Yuan, Y., & Lozano-Durán, A.** (2025). *Dimensionless learning based on information.* Nature Communications. [doi:10.1038/s41467-025-64425-8](https://doi.org/10.1038/s41467-025-64425-8) (IT-π: which Π groups carry the data).
            * **Schlichting, H., & Gersten, K.** (2017). *Boundary-Layer Theory* (9th ed.). Springer. (Blasius; laminar cylinder separation ~105°.)
            * **Ghia, U., Ghia, K. N., & Shin, C. T.** (1982). *High-Re solutions for incompressible flow using the Navier-Stokes equations and a multigrid method*. Journal of Computational Physics, 48(3), 387-411.
            """
        )
