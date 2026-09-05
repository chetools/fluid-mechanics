"""UI module for Dimensional Analysis: Buckingham Pi & Linear Algebra Null-Space Approach."""

import streamlit as st
import pandas as pd
import numpy as np

from src.svg_diagrams import diagram_null_space_matrix, render_svg
from src.physics.dimensional_analysis import (
    VARIABLE_REGISTRY,
    compute_null_space_pi_groups,
    get_cheme_preset
)
from src.ui.pedagogy import render_objectives, render_what_to_notice, render_self_check

def render_tab_dimensional_analysis():
    """Render comprehensive educational panel for Dimensional Analysis."""
    st.markdown("## 2. Dimensional Analysis: Why, Buckingham Π & The Null-Space Method")
    st.markdown(
        """
        Dimensional analysis is one of the most powerful analytical weapons in engineering.
        It allows us to deduce the functional relationships governing complex physical systems
        **without solving the Navier–Stokes partial differential equations**, collapse thousands
        of experiments onto single universal master curves, and scale up lab pilot plants to full industrial scale.

        Read this panel **before** trusting every Re on the KPI strip. The sidebar Re is
        $\\rho U_0 L/\\mu$ — one Π group, not a complete description of the flow.
        """
    )
    render_objectives(
        [
            "Cut an experimental matrix with Π groups (n − rank(A) experiments, not n).",
            "Carry out Buckingham's five steps for pipe Δp.",
            "See that SVD gives *a* kernel; ChemE names (Re, Eu, ε/D) come from a conventional basis.",
        ]
    )
    
    # -------------------------------------------------------------------------
    # PART 1: Why Dimensional Analysis?
    # -------------------------------------------------------------------------
    st.markdown("### 2.1 Why Dimensional Analysis? The Five Major Advantages")
    
    col_adv1, col_adv2 = st.columns(2)
    with col_adv1:
        st.info(
            """
            **1. Dramatic Reduction in Experimental Complexity**
            
            Suppose pipe pressure drop depends on 6 variables: $\\Delta p = f(D, L, u, \\rho, \\mu, \\epsilon)$.
            Testing 5 values for each variable would require:
            $$5^6 = 15,625 \\text{ experiments!}$$
            Dimensional analysis reduces this to 3 dimensionless groups: $\\text{Eu} = \\Phi(\\text{Re}, \\epsilon/D, L/D)$.
            Testing 5 values now requires only $5^3 = 125$ experiments—a **99.2% reduction in experimental effort and cost**!
            """
        )
        st.info(
            """
            **2. Pilot Plant Scale-Up & True Similitude**
            
            Building full-scale chemical plants (e.g., 50,000-liter bioreactors or oil pipelines) is expensive and risky. 
            Dimensional analysis establishes the rules of **Dynamic Similitude**:
            - **Geometric Similarity:** Equal aspect ratios ($L/D = \\text{const}$).
            - **Kinematic Similarity:** Streamlines in model and prototype have identical geometric patterns.
            - **Dynamic Similarity:** Ratio of all force vectors (inertial, viscous, gravitational) are matched: $\\text{Re}_{\\text{model}} = \\text{Re}_{\\text{prototype}}$, $\\text{Fr}_{\\text{model}} = \\text{Fr}_{\\text{prototype}}$.
            """
        )
    with col_adv2:
        st.info(
            """
            **3. Creation of Universal Master Correlations**
            
            Dimensional analysis is what makes the **Moody Chart** possible. 
            Instead of needing separate graphs for water, crude oil, air, and gasoline across every pipe diameter, 
            a single plot of $f$ vs. $\\text{Re}$ and $\\epsilon/D$ governs **all Newtonian fluids in all pipes forever**.
            """
        )
        st.info(
            """
            **4. Model Independence & Physical Insight**

            Even if we know nothing about turbulence or molecular kinetics,
            dimensional consistency guarantees that any physically valid equation
            must balance dimensions on both sides (**Fourier's Principle of Dimensional Homogeneity**).
            """
        )
        st.info(
            """
            **5. Nondimensional PDEs reveal dominant balances**

            Scaling Navier–Stokes with $U$ and $L$ produces Re, Fr, Eu in front of each term.
            Taking Re → 0 recovers Stokes flow; Re → ∞ recovers Euler — the story of Tabs 1 and 3–4 —
            *without solving anything*.
            """
        )

    # -------------------------------------------------------------------------
    # PART 2: Classical Buckingham Pi Method
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 2.2 Solution Method 1: The Classical Buckingham Π Theorem")
    st.markdown(
        """
        Formulated by Edgar Buckingham in 1914, the theorem states that if an equation involving 
        $n$ physical variables is dimensionally homogeneous, it can be reduced to a relationship 
        among $p = n - k$ independent dimensionless groups ($\\Pi_1, \\Pi_2, \\dots, \\Pi_p$), 
        where $k$ is the number of fundamental dimensions.
        """
    )
    
    with st.expander("🔍 Step-by-Step Walkthrough: The 5 Standard Steps of Buckingham Π"):
        st.markdown(
            r"""
            **Step 1: List all $n$ physical variables affecting the phenomenon**
            Example: Pressure drop in a pipe $\Delta p_f$:
            $$\Delta p, \quad D, \quad L, \quad u, \quad \rho, \quad \mu, \quad \epsilon \quad (n = 7)$$

            **Step 2: Express each variable in primary dimensions $[M, L, T]$**
            * $\Delta p = [M L^{-1} T^{-2}]$
            * $D = [L]$
            * $L = [L]$
            * $u = [L T^{-1}]$
            * $\rho = [M L^{-3}]$
            * $\mu = [M L^{-1} T^{-1}]$
            * $\epsilon = [L]$
            Number of base dimensions: $k = 3$ ($M, L, T$).

            **Step 3: Calculate the number of dimensionless $\Pi$ groups**
            $$p = n - k = 7 - 3 = 4 \quad \Pi\text{-groups}$$

            **Step 4: Select $k$ repeating variables**
            Rules for repeating variables:
            1. Must contain all $k$ base dimensions ($M, L, T$).
            2. Must not themselves form a dimensionless group!
            *Standard choice for flow:* $\rho$ (fluid mass), $u$ (fluid kinematics), and $D$ (geometry).

            **Step 5: Formulate each $\Pi$ group and solve the linear exponent equations**
            * $\Pi_1 = \Delta p \cdot \rho^a u^b D^c \implies [M L^{-1} T^{-2}][M L^{-3}]^a [L T^{-1}]^b [L]^c = [M^0 L^0 T^0]$
              * Mass $[M]$: $1 + a = 0 \implies a = -1$
              * Time $[T]$: $-2 - b = 0 \implies b = -2$
              * Length $[L]$: $-1 - 3a + b + c = 0 \implies -1 + 3 - 2 + c = 0 \implies c = 0$
              * **Result:** $\Pi_1 = \frac{\Delta p}{\rho u^2} = Eu$ (Euler number / friction factor)
            * $\Pi_2 = \mu \cdot \rho^a u^b D^c \implies \Pi_2 = \frac{\mu}{\rho u D} = \frac{1}{Re}$ (Reynolds number)
            * $\Pi_3 = \epsilon \cdot \rho^a u^b D^c \implies \Pi_3 = \frac{\epsilon}{D}$ (Relative roughness)
            * $\Pi_4 = L \cdot \rho^a u^b D^c \implies \Pi_4 = \frac{L}{D}$ (Aspect ratio)

            **Final Law:** $\frac{\Delta p}{\rho u^2} = \Phi\left(Re, \frac{\epsilon}{D}, \frac{L}{D}\right)$
            """
        )

    # -------------------------------------------------------------------------
    # PART 3: Modern Null-Space (Kernel) Linear Algebra Approach
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 2.3 Solution Method 2: The Modern Linear Algebra Null-Space (Kernel) Approach")
    st.markdown(
        """
        While Buckingham's repeating variables method is traditional, it relies on trial-and-error 
        and can fail when variables have degenerate rank. 
        
        The **Null-Space approach** is the rigorous linear algebra generalization:
        Any set of dimensionless exponents $\\mathbf{x} = [a_1, a_2, \\dots, a_n]^T$ 
        must satisfy the homogeneous matrix equation:
        $$\\mathbf{A} \\mathbf{x} = \\mathbf{0}$$
        where $\\mathbf{A}$ is the $m \\times n$ **dimensional matrix**. 
        The dimensionless groups are nothing more than the **basis vectors of the null space** $\\ker(\\mathbf{A})$!
        """
    )
    
    render_svg(diagram_null_space_matrix())
    
    with st.expander("🔍 Mathematical Foundation: The Rank-Nullity Theorem"):
        st.markdown(
            r"""
            Let $\mathbf{A} \in \mathbb{R}^{m \times n}$ be the dimensional matrix where:
            * Row $i$ corresponds to base dimension $i$ ($M, L, T$).
            * Column $j$ corresponds to variable $q_j$.
            * Entry $A_{ij}$ is the power of base dimension $i$ in variable $q_j$.

            A product $\Pi = q_1^{x_1} q_2^{x_2} \cdots q_n^{x_n}$ is dimensionless if and only if for each base dimension $i$:
            $$\sum_{j=1}^n A_{ij} x_j = 0 \iff \mathbf{A} \mathbf{x} = \mathbf{0}$$

            By the **Fundamental Rank-Nullity Theorem of Linear Algebra**:
            $$\dim(\operatorname{null}(\mathbf{A})) + \operatorname{rank}(\mathbf{A}) = n$$
            $$\text{Nullity } p = \dim(\ker(\mathbf{A})) = n - \operatorname{rank}(\mathbf{A})$$

            **What linear algebra actually buys you, versus Buckingham:**
            1. **Rank, not folklore:** $p = n - \operatorname{rank}(A)$, so degenerate dimensions are not miscounted.
            2. **A basis, not the basis:** SVD returns *an* orthonormal kernel. Those vectors are linear combinations of Re, Eu, $\varepsilon/D$ — they are not themselves Re. This app rotates onto a repeating-variable basis and names the groups.
            3. **Independence:** any kernel basis is linearly independent; integer rounding of SVD vectors is *not* orthonormal.
            """
        )

    # -------------------------------------------------------------------------
    # PART 4: Interactive Dimensional Analysis Solver
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 2.4 Interactive Dimensional Analysis Solver")
    st.markdown(
        """
        Choose a classic Chemical Engineering preset or pick your own custom physical variables. 
        The solver builds $\\mathbf{A}$, reads $\\operatorname{rank}(A)$ from SVD, then constructs
        a **conventional** Π basis by choosing repeating variables $(\\rho, u, D, \\ldots)$
        and naming Re, Eu, $\\varepsilon/D$ when they appear.
        """
    )
    
    preset_choice = st.selectbox(
        "Chemical Engineering Problem Preset",
        options=[
            "Pipe Flow Pressure Drop",
            "Stirred Tank Mixing Power",
            "Submerged Body Drag",
            "Capillary Rise / Atomization",
            "Custom Variable Selection"
        ]
    )
    
    if preset_choice != "Custom Variable Selection":
        selected_vars = get_cheme_preset(preset_choice)
    else:
        all_keys = list(VARIABLE_REGISTRY.keys())
        selected_vars = st.multiselect(
            "Select Physical Variables",
            options=all_keys,
            default=["delta_p", "u", "D", "rho", "mu"],
            format_func=lambda k: f"{VARIABLE_REGISTRY[k]['name']} [{VARIABLE_REGISTRY[k]['unit']}]"
        )
        
    if len(selected_vars) < 3:
        st.warning("Please select at least 3 variables to perform dimensional analysis.")
        return
        
    res_dim = compute_null_space_pi_groups(selected_vars)
    
    col_st1, col_st2, col_st3 = st.columns(3)
    col_st1.metric("Variables (n)", f"{res_dim['n_vars']}")
    col_st2.metric("Matrix Rank r = rank(A)", f"{res_dim['rank']}")
    col_st3.metric("Nullity (p = n - r)", f"{res_dim['nullity']} Dimensionless Groups")
    
    st.markdown("#### Dimensional Matrix A (Rows = [M, L, T], Columns = Variables)")
    dim_df = pd.DataFrame(
        res_dim["A"],
        index=["Mass [M]", "Length [L]", "Time [T]"],
        columns=res_dim["symbols"]
    )
    st.dataframe(dim_df.style.format("{:.0f}"), width="stretch")
    
    if res_dim.get("repeating_symbols"):
        st.caption(
            "Repeating variables: "
            + ", ".join(f"${s}$" for s in res_dim["repeating_symbols"])
            + ". Remaining variables each generate one named Π group."
        )

    st.markdown(r"#### Named dimensionless groups (conventional repeating-variable basis)")
    render_what_to_notice(
        "For pipe flow you should recover Eu, Re, ε/D, and L/D (up to inversion). "
        "If a group is unnamed, the exponents still lie in ker(A)."
    )

    for i, pi in enumerate(res_dim["pi_groups"]):
        with st.container(border=True):
            name = pi.get("canonical_name") or "Unnamed Π group (still dimensionless)"
            st.markdown(f"**$\\Pi_{{{i+1}}}$ — {name}**")
            st.latex(rf"\Pi_{{{i+1}}} = {pi['formula_latex']}")
            st.caption(f"Exponent vector $\\mathbf{{x}}_{{{i+1}}} = {list(pi['vector'])}$")

    with st.expander("Raw SVD kernel (unrotated — usually not Re or Eu)"):
        st.markdown(
            "These columns of $\\ker(A)$ from SVD are orthonormal in $\\mathbb{R}^n$ "
            "before integer rounding. They span the same space as the named groups above."
        )
        for i, pi in enumerate(res_dim.get("svd_groups") or []):
            st.latex(rf"\Pi^{{\mathrm{{SVD}}}}_{{{i+1}}} = {pi['formula_latex']}")
            st.caption(f"raw = {np.round(pi['raw_vector'], 3).tolist()}")

    render_self_check(
        "dim_self_check_count",
        "Pipe Δp = f(D, L, u, ρ, μ, ε) has n = 7 variables in M, L, T. How many independent Π groups?",
        ["7", "4  (n − rank A = 7 − 3)", "3  (one per base dimension)"],
        "4  (n − rank A = 7 − 3)",
        "Buckingham: p = n − k with k = rank(A) = 3, so four groups: Eu, Re, ε/D, L/D.",
    )
