"""UI module for Dimensional Analysis: Buckingham Pi & Linear Algebra Null-Space Approach."""

import streamlit as st
from src.ui.state import persistent_input
import pandas as pd
import numpy as np

from src.svg_diagrams import (
    diagram_null_space_matrix,
    diagram_transport_analogy,
    diagram_transport_geometries,
    render_svg,
)
from src.physics.transport_analogy import (
    CORRELATIONS,
    analogy_pair,
    diffusivities,
    pohlhausen_theta_gradient,
    sweep_reynolds,
)
from src.plotting import plot_thermal_boundary_layers, plot_transport_correlations
from src.ui.pedagogy import render_plot, render_symbols
from src.physics.dimensional_analysis import (
    VARIABLE_REGISTRY,
    compute_null_space_pi_groups,
    get_cheme_preset
)
from src.ui.pedagogy import (
    render_callout,
    render_derivation,
    render_objectives,
    render_prose_and_latex,
    render_self_check,
    render_what_to_notice,
)

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

    render_derivation(
        r"scaling Navier–Stokes, so that $\mathrm{Re}$, $\mathrm{Fr}$ and $\mathrm{Eu}$ appear by themselves",
        [
            (
                "Choose a ruler for every variable",
                r"""
                A problem with one geometry and one imposed speed offers exactly one length
                $L$ and one velocity $U$. Everything else must be built from them. Starred
                symbols are pure numbers of order one:
                $$\mathbf x^{*}=\frac{\mathbf x}{L},\quad
                \mathbf u^{*}=\frac{\mathbf u}{U},\quad
                t^{*}=\frac{tU}{L},\quad
                \nabla^{*}=L\nabla$$
                The time scale is not an extra choice: $L/U$ is how long the flow takes to
                cross the object, the only clock the problem has.
                """,
            ),
            (
                "Substitute into each term and see what falls out in front",
                r"""
                Putting these into the incompressible momentum equation and using
                $\partial/\partial t=(U/L)\partial/\partial t^{*}$:
                $$\underbrace{\frac{\rho U^{2}}{L}}_{\text{inertia}}
                \left[\frac{\partial\mathbf u^{*}}{\partial t^{*}}
                +(\mathbf u^{*}\cdot\nabla^{*})\mathbf u^{*}\right]
                =-\frac{\Delta p}{L}\nabla^{*}p^{*}
                +\underbrace{\frac{\mu U}{L^{2}}}_{\text{viscous}}\nabla^{*2}\mathbf u^{*}
                -\underbrace{\rho g}_{\text{gravity}}\,\hat{\mathbf z}$$
                Each bracket is now a pure number of order one, so **the prefactors carry all
                the physics of relative importance**. This is the same estimate used in Tab 4
                to get $\mathrm{Re}$, done to the whole equation at once.
                """,
            ),
            (
                "Divide by the inertia scale, and name what is left",
                r"""
                Dividing through by $\rho U^{2}/L$:
                $$\frac{\partial\mathbf u^{*}}{\partial t^{*}}
                +(\mathbf u^{*}\cdot\nabla^{*})\mathbf u^{*}
                =-\underbrace{\frac{\Delta p}{\rho U^{2}}}_{\mathrm{Eu}}\nabla^{*}p^{*}
                +\underbrace{\frac{\mu}{\rho U L}}_{1/\mathrm{Re}}\nabla^{*2}\mathbf u^{*}
                -\underbrace{\frac{gL}{U^{2}}}_{1/\mathrm{Fr}^{2}}\hat{\mathbf z}$$
                Three named groups, each the ratio of one term to inertia, and **no others** —
                because there were no other terms. Dimensional analysis of the variable list
                (§3.2) must give the same answer, since it is the same information counted a
                different way.
                """,
            ),
            (
                "The pressure scale is a modelling decision, not an accident",
                r"""
                $\Delta p$ has no independent definition, so we must choose it. Taking
                $\Delta p=\rho U^{2}$ makes $\mathrm{Eu}=1$ and asserts that pressure balances
                **inertia** — right for a Venturi or a nozzle. Taking $\Delta p=\mu U/L$
                instead puts $\mathrm{Re}$ in front of the *inertia* term and asserts pressure
                balances **viscosity** — which is exactly the scaling used to derive Stokes
                flow in Tab 8, and the reason that derivation could delete inertia rather than
                the pressure. Same equation; the choice of ruler declares which balance you
                expect.
                """,
            ),
            (
                "What this buys: two flows are the same flow",
                r"""
                The starred equation contains **no dimensional quantity at all** — only
                $\mathrm{Re}$, $\mathrm{Fr}$ and the dimensionless geometry and boundary
                conditions. So two flows that match in those match everywhere, and a model
                test predicts the full-scale machine. It also states the limit honestly:
                matching $\mathrm{Re}$ *and* $\mathrm{Fr}$ at reduced scale usually requires a
                fluid nobody has, which is why ship-model testing splits the drag into a
                Froude-scaled part and a Reynolds-scaled part rather than matching both.
                """,
            ),
            (
                "And one warning the algebra makes precise",
                r"""
                Large $\mathrm{Re}$ makes $1/\mathrm{Re}$ small, but it multiplies
                $\nabla^{*2}\mathbf u^{*}$, which is *not* order one near a wall — that is the
                whole content of the boundary layer in Tab 7. A small coefficient only permits
                dropping a term when the term it multiplies is genuinely order one. This is
                the single most common misuse of a scaling argument.
                """,
            ),
        ],
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
    
    preset_choice = persistent_input(st.selectbox,
        "Chemical Engineering Problem Preset",
        options=[
            "Pipe Flow Pressure Drop",
            "Stirred Tank Mixing Power",
            "Submerged Body Drag",
            "Capillary Rise / Atomization",
            "Custom Variable Selection"
        ], key="tab_dimensional_analysis_chemical_engineering_problem_preset")
    
    if preset_choice != "Custom Variable Selection":
        selected_vars = get_cheme_preset(preset_choice)
    else:
        all_keys = list(VARIABLE_REGISTRY.keys())
        selected_vars = persistent_input(st.multiselect,
            "Select Physical Variables",
            options=all_keys,
            default=["delta_p", "u", "D", "rho", "mu"],
            format_func=lambda k: f"{VARIABLE_REGISTRY[k]['name']} [{VARIABLE_REGISTRY[k]['unit']}]", key="tab_dimensional_analysis_select_physical_variables")
        
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

    # -------------------------------------------------------------------------
    # PART 6: Transport analogies
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 3.6 The same analysis for heat and mass transfer")
    render_objectives(
        [
            "Say why $\\nu$, $\\alpha$ and $D_{AB}$ are the same kind of quantity.",
            "Get $\\mathrm{Nu} = f(\\mathrm{Re},\\mathrm{Pr})$ and $\\mathrm{Sh} = f(\\mathrm{Re},\\mathrm{Sc})$ from the same dimensional matrix.",
            "Derive the flat-plate correlation from the Blasius solution instead of quoting it.",
            "Convert a heat-transfer correlation into a mass-transfer one, and know when that is not allowed.",
        ]
    )
    render_prose_and_latex(
        r"""
        Everything above was about momentum. None of it was *specific* to momentum. Run the
        same machinery on heat and on species and you get the same structure, because the
        governing equations are the same equation.
        """
    )
    render_svg(diagram_transport_analogy())

    st.markdown("#### 3.6.1 Three diffusivities doing one job")
    render_prose_and_latex(
        r"""
        Momentum, heat and species each spread by a **diffusivity** with units of m²/s:
        $$\nu = \frac{\mu}{\rho}, \qquad \alpha = \frac{k}{\rho c_p}, \qquad D_{AB}$$
        In the boundary layer they appear in identical positions:
        $$u\frac{\partial u}{\partial x}+v\frac{\partial u}{\partial y}=\nu\frac{\partial^2 u}{\partial y^2},
        \quad u\frac{\partial T}{\partial x}+v\frac{\partial T}{\partial y}=\alpha\frac{\partial^2 T}{\partial y^2},
        \quad u\frac{\partial c}{\partial x}+v\frac{\partial c}{\partial y}=D_{AB}\frac{\partial^2 c}{\partial y^2}$$
        Because a diffusivity is the *only* property in each equation, non-dimensionalising
        can leave only **ratios of diffusivities**:
        $$\mathrm{Pr}=\frac{\nu}{\alpha}, \qquad \mathrm{Sc}=\frac{\nu}{D_{AB}},
        \qquad \mathrm{Le}=\frac{\alpha}{D_{AB}}=\frac{\mathrm{Sc}}{\mathrm{Pr}}$$
        Read them as *relative* rates. $\mathrm{Pr}\gg 1$ means momentum spreads faster than
        heat, so the thermal layer sits *inside* the velocity layer. $\mathrm{Pr}\ll 1$
        (a liquid metal) is the reverse.
        """
    )
    render_symbols(
        [
            (r"\nu", r"momentum diffusivity, $\mu/\rho$ (m²/s). Also called kinematic viscosity."),
            (r"\alpha", r"thermal diffusivity, $k/(\rho c_p)$ (m²/s)."),
            (r"D_{AB}", "mass diffusivity of A through B (m²/s)."),
            (r"\mathrm{Nu}", r"Nusselt number, $hL/k$. The dimensionless wall temperature gradient."),
            (r"\mathrm{Sh}", r"Sherwood number, $k_c L/D_{AB}$. The dimensionless wall concentration gradient."),
            (r"\mathrm{St}", r"Stanton number, $\mathrm{Nu}/(\mathrm{Re}\,\mathrm{Pr}) = h/(\rho c_p U)$."),
        ]
    )

    st.markdown("#### 3.6.2 The dimensional analysis, done twice")
    render_prose_and_latex(
        r"""
        Run §3.3's procedure on convective heat transfer. The variables are
        $h, L, U, \rho, \mu, k, c_p$ — seven of them, in four dimensions
        ($M, L, T, \Theta$, adding temperature). Rank 4, so
        $$p = n - \operatorname{rank}(\mathbf{A}) = 7 - 4 = 3$$
        three groups, conventionally
        $$\mathrm{Nu}=\Phi\left(\mathrm{Re},\ \mathrm{Pr}\right)$$
        Now mass transfer: $k_c, L, U, \rho, \mu, D_{AB}$ — six variables in three dimensions
        ($M, L, T$; no temperature, and concentration cancels for dilute transfer). Rank 3, so
        $p = 3$ again:
        $$\mathrm{Sh}=\Phi\left(\mathrm{Re},\ \mathrm{Sc}\right)$$

        **The two $\Phi$ are the same function.** That is not a coincidence and not an
        empirical observation — it follows from the equations being identical once written in
        dimensionless form. Whatever correlation holds for heat on a geometry holds for mass
        on that geometry, with $\mathrm{Pr}\to\mathrm{Sc}$ and $\mathrm{Nu}\to\mathrm{Sh}$.
        """
    )

    st.markdown("#### 3.6.3 Where the flat-plate correlation comes from")
    render_prose_and_latex(
        r"""
        The textbook result $\mathrm{Nu}_x = 0.332\,\mathrm{Re}_x^{1/2}\mathrm{Pr}^{1/3}$ is
        usually quoted as though it were a fit to data. It is not. It is the Blasius solution
        of chapter 7, carrying a temperature field along with it.

        **Step 1 — the same similarity variable.** Scale temperature between its two boundary
        values, and use chapter 7's $\eta$ unchanged:
        $$\theta(\eta) = \frac{T-T_w}{T_\infty-T_w},
        \qquad \eta = y\sqrt{\frac{U_\infty}{\nu x}}$$

        **Step 2 — substitute.** Putting $T = T_w + (T_\infty-T_w)\theta(\eta)$ into the
        energy equation, with $u$ and $v$ taken from the Blasius solution, every $x$ and $y$
        cancels exactly as it did for momentum, leaving
        $$\boxed{\;\theta'' + \tfrac{1}{2}\mathrm{Pr}\,f\,\theta' = 0\;}
        \qquad \theta(0)=0,\quad \theta(\infty)=1$$
        The momentum problem enters **only** through $f$, which is already known. The thermal
        problem is a passenger on it, and $\mathrm{Pr}$ is the only new parameter.

        **Step 3 — solve, without shooting.** The equation is linear and homogeneous in
        $\theta$, so it needs no iteration: integrate once with $\theta'(0)=1$ to get some
        $\tilde\theta$, then the condition at infinity fixes the true gradient exactly,
        $$\theta'(0) = \frac{1}{\tilde\theta(\infty)}$$
        Equivalently, in closed form,
        $$\theta'(0)=\left[\int_0^\infty \exp\left(-\tfrac{\mathrm{Pr}}{2}\int_0^{\eta}f\,d\eta'\right)d\eta\right]^{-1}$$

        **Step 4 — read off the Nusselt number.** The wall flux is
        $q_w = -k\,\partial T/\partial y|_0$, and $h \equiv q_w/(T_w-T_\infty)$, so
        $$\mathrm{Nu}_x=\frac{hx}{k}=\theta'(0)\sqrt{\mathrm{Re}_x}$$
        All the physics sits in $\theta'(0)$, and $\theta'(0)$ turns out to be very close to
        $0.332\,\mathrm{Pr}^{1/3}$ over the ordinary range of fluids. That — and only that —
        is where the constant and the cube root come from.
        """
    )
    render_callout(
        """
        **The cleanest check available.** Set $\\mathrm{Pr}=1$. The energy equation becomes
        $\\theta'' + \\tfrac12 f\\theta' = 0$, which is *exactly* the equation $f'$ satisfies
        (differentiate Blasius once), with the same boundary conditions. So $\\theta$ must
        equal $f'$, and therefore
        $$\\theta'(0) = f''(0) = 0.332057\\ldots$$
        The heat-transfer constant **is** the momentum constant. The app solves the ODE
        numerically below; at $\\mathrm{Pr}=1$ it returns 0.33206, which is not a coincidence
        to four decimal places.
        """,
        title="At Pr = 1 the two problems are the same problem",
    )

    prandtl_choices = [0.7, 1.0, 7.0, 50.0]
    thermal_profiles = [pohlhausen_theta_gradient(pr) for pr in prandtl_choices]
    render_what_to_notice(
        "Left: the dashed velocity profile never moves — momentum does not know Pr exists. "
        "Only θ moves, and the ratio of the two thicknesses is what Pr names: "
        "δ_t/δ ≈ Pr^(−1/3). Right: the solved ODE against the 0.332 Pr^(1/3) fit — they "
        "agree to about 2% from Pr = 0.6 to 100, which is exactly the range the textbooks quote."
    )
    render_plot(plot_thermal_boundary_layers(thermal_profiles), "thermal-similarity")
    st.caption(
        "Solved here, not tabulated: θ'(0) = "
        + ", ".join(
            f"{p['theta_gradient']:.4f} at Pr = {p['prandtl']:g}" for p in thermal_profiles
        )
        + f". The Pr = 1 value equals Blasius f''(0) = {thermal_profiles[1]['theta_gradient']:.5f}. "
        "Below about Pr = 0.6 the cube-root fit degrades badly — liquid metals need their own "
        "correlation, because there the thermal layer is far thicker than the velocity layer "
        "and the assumption behind the fit fails."
    )
    render_prose_and_latex(
        r"""
        **And now for free, the mass-transfer result.** The species equation differs from the
        energy equation only in the letter naming the diffusivity, so the identical solution
        with $\mathrm{Pr}\to\mathrm{Sc}$ gives
        $$\mathrm{Sh}_x = 0.332\,\mathrm{Re}_x^{1/2}\,\mathrm{Sc}^{1/3},
        \qquad \frac{\delta_c}{\delta}\approx \mathrm{Sc}^{-1/3}$$
        No new derivation, no new experiment. The same curve on the plot above serves both,
        with its horizontal axis relabelled.
        """
    )

    st.markdown("#### 3.6.4 The correlations, and swapping between them")
    render_svg(diagram_transport_geometries())

    geo1, geo2, geo3 = st.columns(3)
    geometry = persistent_input(geo1.selectbox, "Geometry", list(CORRELATIONS.keys()), key="ta_geom")
    re_ta = persistent_input(geo2.number_input, "Reynolds number", min_value=1e-3, max_value=1e8,
                              value=1.0e4, step=1e3, format="%.4g", key="ta_re")
    fluid_choice = persistent_input(geo3.selectbox,
        "Fluid", ["Water (20 °C)", "Air (20 °C)", "Engine oil", "Liquid sodium"], key="ta_fluid")
    presets = {
        "Water (20 °C)": dict(rho=998.2, mu=1.002e-3, k_thermal=0.598, cp=4182.0, d_ab=1.5e-9),
        "Air (20 °C)": dict(rho=1.204, mu=1.82e-5, k_thermal=0.0257, cp=1005.0, d_ab=2.4e-5),
        "Engine oil": dict(rho=888.0, mu=0.8, k_thermal=0.145, cp=1880.0, d_ab=1.0e-10),
        "Liquid sodium": dict(rho=927.0, mu=7.0e-4, k_thermal=86.0, cp=1380.0, d_ab=1.0e-8),
    }
    props = diffusivities(**presets[fluid_choice])

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("ν (momentum)", f"{props['nu']:.3e} m²/s")
    d2.metric("α (heat)", f"{props['alpha']:.3e} m²/s")
    d3.metric("Prandtl ν/α", f"{props['prandtl']:.4g}")
    d4.metric("Schmidt ν/D_AB", f"{props['schmidt']:.4g}")

    try:
        pair = analogy_pair(geometry, re_ta, props["prandtl"], props["schmidt"])
    except ValueError as exc:
        st.error(str(exc))
    else:
        h1, h2, h3 = st.columns(3)
        h1.metric("Nu (heat)", f"{pair['heat']['value']:.4g}")
        h2.metric("Sh (mass)", f"{pair['mass']['value']:.4g}")
        h3.metric("Lewis Sc/Pr", f"{pair['lewis']:.4g}")

        for result in (pair["heat"], pair["mass"]):
            for warning in result["warnings"]:
                st.warning(f"{result['symbol']}: {warning}")
        if pair["heat"]["in_range"] and pair["mass"]["in_range"]:
            st.success(
                f"Both inside the correlation's stated range "
                f"(Re {CORRELATIONS[geometry]['re_range'][0]:.3g}–"
                f"{CORRELATIONS[geometry]['re_range'][1]:.3g})."
            )
        st.caption(
            f"**{geometry}** · length scale: {CORRELATIONS[geometry]['length_scale']} · "
            f"source: {CORRELATIONS[geometry]['source']}. {CORRELATIONS[geometry]['note']}"
        )
        if not pair["offset_breaks_pure_power_law"]:
            st.caption(
                f"Pure power law, so the analogy predicts Sh/Nu = Le^n = "
                f"{pair['ratio_from_lewis']:.4g}, and the computed ratio is "
                f"{pair['ratio']:.4g}. They agree because the *same* correlation produced both."
            )
        else:
            st.caption(
                f"This correlation has a conduction floor, so Sh/Nu = {pair['ratio']:.4g} is "
                "not a clean power of Le: the additive 2 does not scale. The analogy still "
                "holds term by term; only the tidy ratio is lost."
            )

        curves = [
            sweep_reynolds(name, props["prandtl"])
            for name in ("Flat plate, laminar (local)", "Sphere (Ranz-Marshall)",
                         "Pipe, turbulent (Dittus-Boelter)", "Packed bed (Wakao)")
        ]
        render_plot(
            plot_transport_correlations(curves, pair["heat"]), "transport-correlations"
        )
        st.caption(
            "Each curve is drawn only across its own stated range of validity, which is why "
            "they do not span the same axis. Extrapolating one past its band is the most "
            "common way to misuse a correlation, so the plot refuses to draw it."
        )

    render_prose_and_latex(
        r"""
        **The Chilton–Colburn analogy** goes one step further and ties both to friction:
        $$j_H=\mathrm{St}\,\mathrm{Pr}^{2/3}
        =j_D=\mathrm{St}_m\,\mathrm{Sc}^{2/3}
        =\frac{f_F}{2}=\frac{f_D}{8}$$
        so a pressure-drop measurement predicts a heat-transfer coefficient. Chapter 4 uses
        this; chapter 2 warns about the factor of four between $f_F$ and $f_D$.

        **Where it breaks, and why.** The friction equality holds against **skin friction
        only**. On a sphere, a cylinder or a packed bed most of the drag is *form* drag —
        pressure acting on a separated wake — and form drag transports neither heat nor
        species. Using $f_D/8$ there over-predicts $j$ badly. The heat/mass half of the
        analogy ($j_H = j_D$) survives on bluff bodies; the friction half does not.
        """
    )
    render_self_check(
        "transport_self_check_swap",
        "You measured Nu = 120 for air (Pr = 0.71) over a cylinder. For the same cylinder "
        "and the same Re, evaporating a species with Sc = 2.4, Sh is closest to…",
        ["120", "180", "40"],
        "180",
        "Same geometry, same Re, so the same correlation: Sh/Nu = (Sc/Pr)^(1/3) = "
        "(2.4/0.71)^(1/3) = 1.50, giving Sh ≈ 180. Nothing was re-derived and no new "
        "experiment was needed — that is the whole value of the analogy.",
    )
    render_callout(
        """
        **Assumptions the analogy needs and does not announce.** Constant properties;
        no viscous dissipation; **low mass-transfer rates**, so the blowing velocity at the
        surface does not distort the velocity profile (high-flux evaporation needs a
        correction factor); no chemical reaction; and matching boundary conditions — a
        constant-temperature wall corresponds to a constant-concentration surface, not a
        constant-flux one. Every correlation above is also bounded in Re and in Pr or Sc,
        and the calculator refuses to hide it when you leave that range.
        """
    )
