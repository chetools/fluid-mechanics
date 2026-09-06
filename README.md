# Educational Fluid Mechanics: From Euler to Navier–Stokes & Chemical Engineering Applications

An interactive, rigorous educational Streamlit application for fluid mechanics and transport phenomena—modeled after the pedagogical, mathematical, and visual standards of the isopropanol-water distillation reference platform.

[![Deploy with Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=chetools/fluid-mechanics&branch=master&mainModule=app.py)

The application guides students and engineers from first-principles momentum conservation in inviscid flow, through continuum kinematics and Cauchy stress, up to exact analytical solutions, live numerical CFD, chemical engineering piping network sizing, and linear algebra dimensional analysis.

---

## What It Does

The interface features a persistent physical KPI strip above twelve chapters, ordered from plant energy through gas dynamics and CFD. **One chapter renders at a time** — the chapter selector looks like a tab bar but only the selected chapter is built, which is what keeps a course this size responsive:

| Tab | Contents |
|---|---|
| **🏭 1. ChemE Energy & Bernoulli** | Why $\Delta p$, pumps, and NPSH matter; Bernoulli from a steady energy balance; viscosity as frictional heating |
| **🚰 2. Pipe Flow & Pumping** | Darcy vs Fanning, Churchill, schedule sizing, editable looped networks, pump OPEX, NPSH, hydraulic diameter, and open-channel canal design |
| **📐 3. Dimensional Analysis** | Experimental collapse, SVD kernel **rotated** onto Re/Eu/$\varepsilon/D$, IT-π (maximum information) |
| **🌪️ 4. Laminar $f$, Turbulence & Straws** | Force balance $\Rightarrow f_D=64/\mathrm{Re}$ vs Moody; straw-packing vs open-pipe pump kW |
| **⚗️ 5. Euler (1D → 3D)** | Continuity, differential Euler, Venturi, d'Alembert |
| **🧱 6. Stress & Navier–Stokes** | Cauchy stress, $\mathbf{D}+\boldsymbol{\Omega}$, Newtonian NS, power-law pipe |
| **📏 7. Exact Solutions & BL** | Couette, Hagen–Poiseuille, Stokes, step-by-step Blasius derivation, cylinder separation |
| **8. External Flow** | Stokes derivation, settling, Schiller–Naumann and drag crisis |
| **9. Turbomachinery** | Angular momentum, 3D impeller geometry and blade angles, velocity triangles, compressor/turbine efficiencies, intercooling, and a worked air-separation plant |
| **10. Compressible Flow** | Stepwise nozzle derivation, choking calculator, normal shocks, Fanno and Rayleigh flow, and choked flow as the basis of pressure-relief sizing |
| **💻 11. CFD (Projection)** | Incompressible Chorin projection; cavity with $t^*$ and Ghia only at Re = 100 |
| **📖 12. Reference & Audit** | Nomenclature, tensor primer, validity matrix |

---

## Pedagogical Design & Mathematical Rigor

Each chapter opens with a guiding question, prerequisites, a core equation, and
an ordered reading route. Detailed derivations expand on demand; the closing
"Put it together" card gives a concrete experiment and connects to the next chapter.
The course moves through plant balances, scaling and regimes, local momentum,
then external flow, turbomachinery, gas dynamics and numerical verification. All twelve
chapter buttons wrap on narrow screens. Selecting a chapter is a Streamlit rerun rather
than a client-side tab switch; widget state is preserved by explicit keys.

### Transport analogies, and where correlations come from

Chapter 3 does not stop at momentum. `nu`, `alpha` and `D_AB` are the same kind of
quantity, so the same dimensional matrix gives `Nu = Phi(Re, Pr)` and
`Sh = Phi(Re, Sc)` with the *same* `Phi`. `src/physics/transport_analogy.py`
stores each correlation once and evaluates it for either mode, so heat and mass
cannot drift apart, and each correlation carries its own range of validity, which
the app reports rather than silently extrapolating.

The flat-plate result is derived rather than quoted. Substituting the Blasius
similarity variable into the energy equation gives
`theta'' + (Pr/2) f theta' = 0`, which the app solves live. At `Pr = 1` that ODE
*is* the differentiated Blasius equation, so `theta'(0)` must equal `f''(0)`, and
the solver returns 0.33206 against 0.332057. The familiar `0.332 Pr^(1/3)` is then
shown to be a ~2% fit to the solved ODE over `Pr = 0.6` to 100.

### Pressure relief

Chapter 10 closes with the reason choking matters industrially. Above the critical
ratio the throat cannot detect the downstream pressure, so a relief device's
capacity is a property of the vessel and the hole, not of the header it discharges
into — which is what makes it sizeable at all. The calculator sizes a throat, flags
whether the case is choked, and reports the capacity lost when it is not. It covers
single-phase ideal gas only; two-phase and flashing relief need the omega method
and are explicitly out of scope.

### Open channels and canals

Chapter 2 closes with open-channel flow, which is where the hydraulic diameter of
section 2.4 comes from: the uniform-flow force balance gives `tau_w = rho g R_h S_0`,
the same equation as a pipe with the bed slope in place of the pressure gradient.
The calculator solves normal depth for a trapezoidal section by a bracketed root
find, reports critical depth and Froude regime, checks freeboard against the
customary `max(0.3 m, 0.2 y_n)`, and flags overtopping, siltation and scour
velocities. Manning and Darcy-Weisbach are both offered, along with the bridge
`n = R_h^(1/6) sqrt(f/8g)` that relates them; the two disagree by a few percent and
the app says so rather than hiding it. Steady uniform flow in a prismatic channel
only - no backwater curves, hydraulic jumps, sediment transport or flood routing.
Chapter 2 then continues with real pipe sizes (2.6) and the editable network lab (2.7).

### Impeller geometry and air separation

Chapter 9 builds the blade camberline by integrating the definition of the blade
angle, `tan(beta) = dr / (r d(theta))`, so the 3D figure, the true-shape velocity
triangle and the reported numbers cannot disagree. Angles are measured **from the
tangential direction**; the complementary from-meridional value is reported beside
every angle. Slip uses Wiesner's correlation with its radius-ratio limit checked.
The chapter closes with a fully worked cryogenic air separation unit - main air
compressor, booster, turboexpander and double column - computed live from the
constant-`cp` stage model, including the comparison that justifies the expander over
a throttling valve.

### Piping network lab

Chapter 2 includes nominal steel pipe sizes NPS 1/2–4, Schedule 40/80, from the
linked Wheatland manufacturer table. Other sizes use measured inside diameter.
Each pipe can use a material roughness estimate, absolute roughness, or ε/D.
Edit the node and pipe tables, then press **Solve network**. Junction demands are
positive for withdrawal; a zero-demand junction has zero net pipe flow. Prescribed
pressure nodes solve their boundary exchange. Elevations affect recovered gauge
pressures through piezometric head. Signed flows support reverse flow and loops.
Results include continuity and energy residuals, a network drawing and CSV export.

The network assumes steady incompressible single-phase flow, no pumps, and entered
minor-loss coefficients. Nominal schedules are geometry, not pressure ratings.
The separate gas calculators use absolute pressures, kelvin, constant cp and γ;
they do not model real-gas, flashing or two-phase behavior. New calculators retain
explicit SI labels independently of the existing nondimensional display toggle.

The SVG teaching diagrams render through Streamlit's native image API. Most are
hand-authored; the impeller figures in chapter 9 are **projections of computed
geometry** from `src/physics/impeller.py`, so a blade angle drawn there is the same
angle the velocity-triangle arithmetic uses.
Diagrams and plots scroll horizontally on small screens to preserve readable
labels; plots also offer hover values and a fullscreen control. SVG tests parse
the cleaned output as XML to catch formatting errors that can make images disappear.

1. **No Skipped Steps**: Every derivation is conducted without skipping algebra or calculus steps. Lengthy proofs, multivariable Taylor expansions, and tensor contractions are organized into clean, collapsible drawers (`st.expander`) to maintain conceptual narrative flow.
2. **Textbook-Quality Vector Diagrams**: Custom inline SVG schematics rendered with crisp coordinate systems, dimension lines, and physical force tractions.
3. **Dual Unit System**: Toggle displayed metrics and plot axes between **SI Metric** (m, s, Pa, Pa·s, kg/m³) and **Nondimensional** ($x/L, u/U_0, Eu$). Scaling uses the sidebar $U_0$, $L$, and $\rho$. Sliders stay in SI so stored values do not jump. Physics always runs in SI.
4. **One fluid object**: Sidebar $\rho$, $\mu$, $U_0$, and $L$ feed the Venturi, cylinder, Couette, Hagen–Poiseuille, Stokes, pipe/pump, and Mach number (speed of sound of the *selected* fluid). Pipe Re = 2300 is labeled as a circular-pipe threshold, not a universal law.
5. **Code Reads as Mathematics**: Calculation modules use tensor contractions (`np.einsum`) and explicit index representations directly mirroring printed textbook equations.
6. **Real-Time CFD**: A 2D lid-driven cavity via Chorin's projection method. Ghia et al. (1982) overlay appears **only at Re = 100**, with $t^*$ and RMSE, so a short run is not labeled a benchmark match.
7. **Chemical Engineering Focus**: Plant piping design from the mechanical energy equation, Moody chart, Fanning vs Darcy, and Π-groups rotated onto named Re / Eu / $\varepsilon/D$ rather than a raw SVD mix.

---

## Getting Started

For future development, start with [AGENTS.md](AGENTS.md) and the
[development notes and lessons learned](docs/DEVELOPMENT_NOTES.md). They document
the architecture, physics contracts, rendering pitfalls, live-browser rerun
investigation and verification workflow.

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

The optional live-browser check is `uv run --with playwright python tests/browser_smoke.py`
with the app running on port 8501 and Microsoft Edge installed. It verifies that
each of the twelve chapters finishes its run, then exercises input persistence
across chapter changes, the network solve and CSV download. Automatic filesystem watching and overlapping fast reruns are
disabled in the verified Windows configuration; refresh the browser after editing
source files. See the development notes for the observed failure and the limits
of the root-cause diagnosis.

For the teaching figures, run `uv run --with playwright python tests/browser_education.py`.
It checks deformation presets, the relief-temperature example and narrow-screen
diagram scrolling, and saves screenshots in the system temporary directory.

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
