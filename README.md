# Educational Fluid Mechanics: From Euler to Navier–Stokes & Chemical Engineering Applications

An interactive, rigorous educational Streamlit application for fluid mechanics and transport phenomena—modeled after the pedagogical, mathematical, and visual standards of the isopropanol-water distillation reference platform.

[![Deploy with Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=chetools/fluid-mechanics&branch=master&mainModule=app.py)

The application guides students and engineers from first-principles momentum conservation in inviscid flow, through continuum kinematics and Cauchy stress, up to exact analytical solutions, live numerical CFD, chemical engineering piping network sizing, and linear algebra dimensional analysis.

---

## What It Does

The interface features a persistent physical KPI strip above nine panels, ordered from plant energy to harder mathematics:

| Tab | Contents |
|---|---|
| **🏭 1. ChemE Energy & Bernoulli** | Why $\Delta p$, pumps, and NPSH matter; Bernoulli from a steady energy balance; viscosity as frictional heating |
| **🚰 2. Pipe Flow & Pumping** | Darcy vs Fanning, Moody, pump OPEX, entrance length, NPSH station, $D_H$ |
| **📐 3. Dimensional Analysis** | Experimental collapse, SVD kernel **rotated** onto Re/Eu/$\varepsilon/D$, IT-π (maximum information) |
| **🌪️ 4. Laminar $f$, Turbulence & Straws** | Force balance $\Rightarrow f_D=64/\mathrm{Re}$ vs Moody; straw-packing vs open-pipe pump kW |
| **⚗️ 5. Euler (1D → 3D)** | Continuity, differential Euler, Venturi, d'Alembert |
| **🧱 6. Stress & Navier–Stokes** | Cauchy stress, $\mathbf{D}+\boldsymbol{\Omega}$, Newtonian NS, power-law pipe |
| **📏 7. Exact Solutions & BL** | Couette, Hagen–Poiseuille, Stokes, Blasius, cylinder separation |
| **💻 8. CFD (Projection)** | Chorin projection; cavity with $t^*$ and Ghia only at Re = 100 |
| **📖 9. Reference & Audit** | Nomenclature, tensor primer, validity matrix |

---

## Pedagogical Design & Mathematical Rigor

1. **No Skipped Steps**: Every derivation is conducted without skipping algebra or calculus steps. Lengthy proofs, multivariable Taylor expansions, and tensor contractions are organized into clean, collapsible drawers (`st.expander`) to maintain conceptual narrative flow.
2. **Textbook-Quality Vector Diagrams**: Custom inline SVG schematics rendered with crisp coordinate systems, dimension lines, and physical force tractions.
3. **Dual Unit System**: Toggle displayed metrics and plot axes between **SI Metric** (m, s, Pa, Pa·s, kg/m³) and **Nondimensional** ($x/L, u/U_0, Eu$). Scaling uses the sidebar $U_0$, $L$, and $\rho$. Sliders stay in SI so stored values do not jump. Physics always runs in SI.
4. **One fluid object**: Sidebar $\rho$, $\mu$, $U_0$, and $L$ feed the Venturi, cylinder, Couette, Hagen–Poiseuille, Stokes, pipe/pump, and Mach number (speed of sound of the *selected* fluid). Pipe Re = 2300 is labeled as a circular-pipe threshold, not a universal law.
5. **Code Reads as Mathematics**: Calculation modules use tensor contractions (`np.einsum`) and explicit index representations directly mirroring printed textbook equations.
6. **Real-Time CFD**: A 2D lid-driven cavity via Chorin's projection method. Ghia et al. (1982) overlay appears **only at Re = 100**, with $t^*$ and RMSE, so a short run is not labeled a benchmark match.
7. **Chemical Engineering Focus**: Plant piping design from the mechanical energy equation, Moody chart, Fanning vs Darcy, and Π-groups rotated onto named Re / Eu / $\varepsilon/D$ rather than a raw SVD mix.

---

## Getting Started

### Prerequisites
* Python 3.12+ (Python 3.14 recommended)
* [uv](https://github.com/astral-sh/uv) package manager

### Installation & Launch

```bash
# Clone or navigate to the project directory
cd c:\Users\carlo\Documents\Projects\fluid-mechanics

# Install dependencies and launch the app
uv run streamlit run app.py
```

### Running the Test Suite

```bash
uv run pytest
```

## Deploying to Streamlit Community Cloud

1. This repository is public at [github.com/chetools/fluid-mechanics](https://github.com/chetools/fluid-mechanics).
2. Sign in to [share.streamlit.io](https://share.streamlit.io).
3. Click **Create app**, choose this repository, main file `app.py`, Python **3.12**.
4. Streamlit Cloud installs from `requirements.txt`.

One-click deploy: [share.streamlit.io/deploy](https://share.streamlit.io/deploy?repository=chetools/fluid-mechanics&branch=master&mainModule=app.py).

---

## Authoritative References
* **Batchelor, G. K.** (1967). *An Introduction to Fluid Dynamics*. Cambridge University Press.
* **Bird, R. B., Stewart, W. E., & Lightfoot, E. N.** (2002). *Transport Phenomena* (2nd ed.). John Wiley & Sons.
* **Kundu, P. K., Cohen, I. M., & Dowling, D. R.** (2015). *Fluid Mechanics* (6th ed.). Academic Press.
* **White, F. M.** (2011). *Viscous Fluid Flow* (3rd ed.). McGraw-Hill.
* **Crane Co.** (1988). *Flow of Fluids Through Valves, Fittings, and Pipe* (Technical Paper No. 410).
* **Churchill, S. W.** (1977). *Friction-factor equation spans all fluid-flow regimes*. Chemical Engineering, 84(24), 91-92.
* **Chorin, A. J.** (1968). *Numerical solution of the Navier-Stokes equations*. Mathematics of Computation, 22(104), 745-762.
* **Schlichting, H., & Gersten, K.** (2017). *Boundary-Layer Theory* (9th ed.). Springer.
* **Ghia, U., Ghia, K. N., & Shin, C. T.** (1982). *High-Re solutions for incompressible flow using the Navier-Stokes equations and a multigrid method*. Journal of Computational Physics, 48(3), 387-411.
