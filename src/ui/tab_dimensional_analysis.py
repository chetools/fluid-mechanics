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
from src.ui.pedagogy import render_objectives, render_what_to_notice, render_self_check, render_prose_and_latex, render_callout

def render_tab_dimensional_analysis():
    """Render comprehensive educational panel for Dimensional Analysis."""
    st.markdown(
        """
        Dimensional analysis organizes a physical problem into ratios that do not depend
        on the choice of units. It tells us which combinations of variables can matter.
        It does **not** determine the correlation, its coefficients, or whether the
        starting list of physical variables is complete.

        After the energy and pipe labs, this panel is **how you design the experiment**
        that produces a Moody chart: collapse $\\Delta p = f(D,L,u,\\rho,\\mu,\\varepsilon)$
        onto $\\mathrm{Eu}=\\Phi(\\mathrm{Re},\\varepsilon/D,L/D)$, then rotate the SVD
        kernel until those named groups appear. The sidebar Re is one Π group, not the whole story.
        """
    )
    render_objectives(
        [
            "Count independent dimensionless groups as n − rank(A), then distinguish response groups from input groups.",
            "Carry out Buckingham's five steps for pipe Δp.",
            "See that SVD gives *a* kernel; ChemE names (Re, Eu, ε/D) come from a conventional basis.",
        ]
    )
    
    # -------------------------------------------------------------------------
    # PART 1: Why Dimensional Analysis?
    # -------------------------------------------------------------------------
    st.markdown("### 3.1 Why Dimensional Analysis? The Five Major Advantages")
    
    col_adv1, col_adv2 = st.columns(2)
    with col_adv1:
        render_callout(
            """
            **1. Dramatic Reduction in Experimental Complexity**
            
            Suppose pipe pressure drop depends on 6 variables: $\\Delta p = f(D, L, u, \\rho, \\mu, \\epsilon)$.
            Testing 5 values for each variable would require:
            $$5^6 = 15,625 \\text{ experiments!}$$
            Including the response, there are 7 variables and 4 dimensionless groups:
            $\\text{Eu} = \\Phi(\\text{Re}, \\epsilon/D, L/D)$.
            A five-level grid over the **three independent inputs** has $5^3 = 125$ points.
            This illustrates potential savings; it is not a guaranteed experiment count.
            The groups must be independently controllable, and repeats and validation still matter.
            """
        )
        render_callout(
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
        render_callout(
            """
            **3. Creation of Universal Master Correlations**
            
            Dimensional analysis is what makes the **Moody Chart** possible. 
            Instead of needing separate graphs for water, crude oil, air, and gasoline across every pipe diameter, 
            one relationship between $f_D$, $\\text{Re}$, and $\\epsilon/D$ describes
            **fully developed, single-phase Newtonian flow in circular pipes** within
            the correlation's range. Entrance effects, strong compressibility, non-Newtonian
            behavior, and other geometries require additional checks or models.
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
        render_callout(
            """
            **5. Nondimensional PDEs reveal dominant balances**

            Scaling Navier–Stokes with $U$ and $L$ produces Re, Fr, Eu in front of each term.
            At small Re, viscous effects dominate inertia. At large Re, inviscid outer-flow
            approximations may be useful, but thin wall layers can remain essential.
            A large Reynolds number does not justify dropping viscosity everywhere.
            """
        )

    # -------------------------------------------------------------------------
    # PART 2: Classical Buckingham Pi Method
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 3.2 Solution Method 1: The Classical Buckingham Π Theorem")
    st.markdown(
        """
        Formulated by Edgar Buckingham in 1914, the theorem states that if an equation involving 
        $n$ physical variables is dimensionally homogeneous, it can be reduced to a relationship 
        among $p = n - k$ independent dimensionless groups ($\\Pi_1, \\Pi_2, \\dots, \\Pi_p$), 
        where $k$ is the **rank of the dimensional matrix**. It equals the number of
        listed base dimensions only when their rows are independent.
        """
    )
    
    with st.expander("🔍 Step-by-Step Walkthrough: The 5 Standard Steps of Buckingham Π"):
        render_prose_and_latex(
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
    st.markdown("### 3.3 Solution Method 2: One theorem, and everything follows")
    render_prose_and_latex(
        r"""
        Buckingham's repeating-variable method works, but it is trial and error, and it
        miscounts when the variables have degenerate rank. There is a cleaner foundation.
        Everything this chapter needs — *how many* dimensionless groups exist, *which*
        products are dimensionless, and *why the answer is never unique* — follows from a
        single theorem of linear algebra, which we state and use without proving.

        **The singular value decomposition.** Every real matrix $\mathbf{A}$, of any shape,
        can be written
        $$\mathbf{A} = \mathbf{U}\,\boldsymbol{\Sigma}\,\mathbf{V}^{T}$$
        where $\mathbf{U}$ and $\mathbf{V}$ are **orthogonal** (their columns are unit
        vectors at right angles, so they rotate and reflect without stretching), and
        $\boldsymbol{\Sigma}$ is **diagonal** with non-negative entries
        $\sigma_1 \ge \sigma_2 \ge \dots \ge 0$, the **singular values**.

        No exceptions, no conditions: square or not, invertible or not, every matrix has one.
        """
    )
    render_callout(
        """
        **What it says geometrically.** A matrix is a linear map, and a linear map can look
        complicated — it can rotate, stretch, squash and flip all at once. The SVD says every
        such map is really just three simple moves in a row:

        1. $\\mathbf{V}^{T}$ — **rotate** the input so that a particular set of perpendicular
           directions lines up with the axes.
        2. $\\boldsymbol{\\Sigma}$ — **stretch along those axes**, each by its own factor
           $\\sigma_i$. This is the only step that changes lengths.
        3. $\\mathbf{U}$ — **rotate** the result into its final orientation.

        Rotate, stretch, rotate. A unit sphere goes to an ellipsoid whose semi-axis lengths
        are the singular values. Nothing else can happen.
        """,
        title="Rotate, stretch, rotate",
    )
    render_prose_and_latex(
        r"""
        **The one consequence that matters here.** A stretch factor of *zero* collapses a
        direction: whatever went in along that axis comes out as $\mathbf{0}$. So the input
        directions that $\mathbf{A}$ annihilates are exactly the columns of $\mathbf{V}$
        whose singular value is zero. Read off the decomposition:

        * The number of **non-zero** singular values is the $\operatorname{rank}$ — the number
          of directions that survive.
        * The columns of $\mathbf{V}$ with $\sigma = 0$ are an **orthonormal basis of the null
          space** $\ker(\mathbf{A})$ — the directions that are crushed.
        * Counting the columns of $\mathbf{V}$ two ways gives rank–nullity for free:
        $$\operatorname{rank}(\mathbf{A}) + \dim\ker(\mathbf{A}) = n$$

        We never had to prove any of this; it is visible in the decomposition once the
        decomposition is granted.
        """
    )
    render_prose_and_latex(
        r"""
        **Now point it at dimensional analysis.** Build the $m \times n$ **dimensional
        matrix** $\mathbf{A}$: row $i$ is a base dimension ($M$, $L$, $T$), column $j$ is a
        variable $q_j$, and $A_{ij}$ is the power of that dimension in that variable. A
        product
        $$\Pi = q_1^{x_1} q_2^{x_2} \cdots q_n^{x_n}$$
        has dimensions $\prod_i (\text{dimension } i)^{\sum_j A_{ij}x_j}$, so it is
        **dimensionless exactly when every one of those exponents vanishes**:
        $$\mathbf{A}\mathbf{x} = \mathbf{0}$$

        That is the whole translation. *Finding dimensionless groups is finding the null space
        of the dimensional matrix*, and the SVD hands it over:

        | Question about scaling | Answer from the SVD of $\mathbf{A}$ |
        |---|---|
        | How many independent $\Pi$ groups? | $p = n - \operatorname{rank}(\mathbf{A})$, and the rank is the count of non-zero $\sigma$ |
        | Which products are dimensionless? | the columns of $\mathbf{V}$ with $\sigma = 0$, read as exponent vectors |
        | Why isn't the answer unique? | any basis of a subspace may be rotated; every choice is equally valid |
        | Are my groups independent? | a basis is linearly independent by construction |

        Buckingham's theorem is the third row of that table plus a counting argument. The SVD
        gives all four rows at once, and gives them numerically, for any set of variables you
        care to type in.
        """
    )
    render_what_to_notice(
        "The non-uniqueness is not a defect and not a licence for sloppiness. The kernel is a "
        "subspace, so it has infinitely many bases; Re, Eu and ε/D are one conventional "
        "choice, and the raw SVD basis is another. §3.4 below computes the raw basis and then "
        "rotates it onto the named groups, so you can watch the same subspace wear two "
        "different sets of labels."
    )

    render_svg(diagram_null_space_matrix())

    with st.expander("🔍 Why a zero singular value means a dimensionless group"):
        render_prose_and_latex(
            r"""
            Take $\mathbf{v}$, a column of $\mathbf{V}$ with singular value $0$. Because
            $\mathbf{V}$ is orthogonal, $\mathbf{V}^{T}\mathbf{v} = \mathbf{e}$, the standard
            basis vector picking out that column's slot. Then
            $$\mathbf{A}\mathbf{v} = \mathbf{U}\boldsymbol{\Sigma}\mathbf{V}^{T}\mathbf{v}
            = \mathbf{U}\boldsymbol{\Sigma}\mathbf{e} = \mathbf{U}(\sigma\,\mathbf{e}) = \mathbf{0}$$
            since $\sigma = 0$. The middle step is the only one doing work: $\boldsymbol{\Sigma}$
            is diagonal, so it just multiplies that slot by its own singular value.

            Reading $\mathbf{v}$ as a list of exponents, $\mathbf{A}\mathbf{v} = \mathbf{0}$
            says every base dimension cancels in
            $q_1^{v_1}q_2^{v_2}\cdots q_n^{v_n}$ — a dimensionless group.

            **A caution the algebra makes obvious.** These exponents are components of a unit
            vector, so they are generally irrational and the products look nothing like the
            named groups. Rounding them to neat integers leaves the null space and stops being
            dimensionless. If you want integers, rotate the basis deliberately, as §3.4 does;
            do not round.

            **Where floating point enters.** A singular value is never exactly zero
            numerically. Rank is decided by counting $\sigma_i$ above a tolerance, so a matrix
            that is nearly degenerate can have its rank — and therefore its number of $\Pi$
            groups — reported differently by different tolerances. That is a real limitation
            of doing this on a computer, not an artefact of this app.
            """
        )

    # -------------------------------------------------------------------------
    # PART 4: Interactive Dimensional Analysis Solver
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 3.4 Interactive Dimensional Analysis Solver")
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

    st.markdown("#### Rotate the SVD kernel onto the named groups")
    st.markdown(
        r"""
        SVD returns *an* orthonormal basis $N$ of $\ker(A)$. Named ChemE groups
        $C = [\mathrm{Eu},\,\mathrm{Re},\,\varepsilon/D,\,L/D]$ are another basis of the
        **same** subspace. A $p\times p$ rotation (really a change of basis)
        $R$ satisfies $N R \approx C$:
        """
    )
    rot = res_dim.get("rotation")
    if rot is not None:
        st.latex(r"R = \arg\min_X \|N X - C\|_F \qquad\text{(least squares)}")
        st.markdown("**Mixing: each named group as a combination of SVD columns $N_j$**")
        for mix in rot["mixes"]:
            st.markdown(f"- **{mix['name']}** $= {mix['mix']}$")
        st.caption(
            f"Relative reconstruction error ||NR - C|| / ||C|| = {rot['reconstruction_error']:.2e}. "
            "If this is tiny, the SVD kernel *already contained* Re and Eu; we only rotated the labels."
        )
        r_df = pd.DataFrame(
            np.round(rot["R"], 3),
            index=[f"N_{i+1}" for i in range(rot["R"].shape[0])],
            columns=[m["name"].split("=")[0].strip()[:24] for m in rot["mixes"]],
        )
        st.dataframe(r_df, width="stretch")
        render_what_to_notice(
            "Raw SVD groups look like random products. After R they are the Moody variables. "
            "Do not treat an unrotated SVD column as Re."
        )
    else:
        st.caption("Rotation needs a square match between SVD columns and named groups.")

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

    st.markdown("---")
    st.markdown("### 3.5 Maximum information from experiments (IT-π)")
    st.markdown(
        r"""
        Buckingham tells you *a* set of dimensionless inputs, not *which mix*
        of them carries the data. Yuan & Lozano-Durán (2025) close that gap.

        **Paper.** Yuan, Y. & Lozano-Durán, A. *Dimensionless learning based on information.*
        *Nature Communications* **16** (2025). [doi:10.1038/s41467-025-64425-8](https://doi.org/10.1038/s41467-025-64425-8)
        ([arXiv:2504.03927](https://arxiv.org/abs/2504.03927)).
        """
    )
    with st.container(border=True):
        st.markdown("**Intuition (no information theory required)**")
        st.markdown(
            r"""
1. Any candidate Π-set is just a rotation of the SVD kernel above. Some rotations
   make the Moody plot a *single* curve; others smear it.
2. **Mutual information** $I(\Pi_{\mathrm{out}}; \Pi_{\mathrm{in}})$ measures how
   much of the output (say $f_D$ or $C_f$) is already determined by those inputs.
   If $I$ is infinite, an exact law exists (Hagen–Poiseuille). If $I$ is finite,
   some physics is missing from the variable list.
3. IT-π **searches the kernel** for the rotation that maximises $I$ (equivalently,
   minimises an *irreducible* prediction error $\epsilon_{LB}$ that no model —
   linear regression or a deep net — can beat). That is the Carnot bound of
   dimensionless laws.
4. Extra Π groups that do not raise $I$ are **wasted experiments**. Buckingham
   may list $l = n - k$ groups; the data may need only $l^\* \le l$ of them.
            """
        )
    st.markdown(
        r"""
        **Why a ChemE should care.** In their rough-wall heat-flux example, Buckingham
        asked for **seven** dimensionless inputs. Three levels each would be
        $3^7 = 2187$ runs. IT-π found **two** groups already give ~92% of the
        extractable information — $3^2 = 9$ runs. The Moody chart is the 19th-century
        version of the same idea: once $f_D = \Phi(\mathrm{Re},\,\varepsilon/D)$,
        you never again test water and oil as separate universes.

        **What to do in the lab.** After you have the kernel (this tab), you still
        choose *which* combination to hold constant in a pilot plant. Prefer the
        rotation that (i) matches named groups when they collapse data, and
        (ii) drops Π's that do not change $I$. That is experimental design, not
        extra algebra.
        """
    )
    render_self_check(
        "dim_self_check_itpi",
        "IT-π's main experimental message is…",
        [
            "Always measure all n − k Buckingham groups at a full factorial",
            "Search the kernel for the fewest Π's that share the most information with the output",
            "SVD columns are already the optimal experiment",
        ],
        "Search the kernel for the fewest Π's that share the most information with the output",
        "Buckingham is an upper bound on the number of groups. Information tells you which mix is worth measuring.",
    )
