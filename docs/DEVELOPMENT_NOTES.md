# Development notes and lessons learned

Recorded 2026-09-05 after the pedagogy/visual improvements and expansion into pipe networks, external flow, turbomachinery and compressible flow. Treat test counts and package versions below as a dated baseline, not permanent requirements.

## Start here

The application is an educational Streamlit course with working calculations. The intended experience is: physical question → assumptions → ordered derivation → interactive example → interpretation and checks. The user values detailed explanations and diagrams that actually render correctly, rather than equations or calculations alone.

Use `uv run` for execution and `uv pip install` if explicit package installation is needed. The project supports Python 3.12+; this work was exercised on Windows with Python 3.14 and Streamlit 1.63/Plotly 7. Dependencies are specified in `pyproject.toml`.

```powershell
uv run streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8501
uv run python -m pytest -q
```

Keep one main server on 8501. Stop temporary diagnostic servers when finished. Session/process IDs from an earlier conversation are not durable launch instructions.

## Before you start: the traps that have actually bitten

Each of these cost real time at least once and is invisible to a casual read. The
detail is further down; this is the index.

| Symptom | Real cause | Guard |
|---|---|---|
| LaTeX renders as literal `$...$` in monospace | markdown, not KaTeX: the prose block kept its Python source indentation, and 4+ spaces after a blank line is an indented code block | `tests/test_markdown_indentation.py`; route blocks through `render_prose_and_latex` |
| Math renders as raw TeX inside a note | `st.info`/`st.warning`/`st.error` do not run KaTeX | `tests/test_katex_safety.py`; use `render_callout` |
| A subscript renders as a currency symbol | Unicode has no subscript `w` or capitals; nearby entities are Currency Symbols (U+20A2 is CRUZEIRO SIGN) | `svg_diagrams._sub()`; currency scan in `tests/test_svg_diagrams.py` |
| An angle in a figure is visibly not the angle it names | it was drawn on an axonometric projection, which foreshortens each direction differently | mark angles on the plan view only |
| Second panel of a subplot figure looks light/unstyled | `update_layout(xaxis=...)` reaches only axis 1 | the registered Plotly template; `tests/test_plotting_theme.py` |
| Page renders partially, script "still running", no error | the whole course was being built every run | one chapter at a time; never restore `st.tabs` |
| A new module silently never reloads | missing from `_MODULE_RELOAD_ORDER` | bidirectional check in `tests/test_app_smoke.py` |
| `{name}` appears literally in an SVG | doubled brace in an f-string | placeholder scan in `tests/test_svg_diagrams.py` |
| Prose numbers disagree with the live calculator | the worked example was written against different inputs | compute worked examples from the app's own defaults |

**The verification loop that works.** Passing tests do not establish that a page
renders. Run the app, open the chapter, and look at it. For a figure, render it
to a standalone HTML file inside a `max-width: 880px` wrapper so it is scaled the
way Streamlit scales it — without that constraint the SVG renders oversized and
overflow judgements are wrong. XML validity proves nothing about layout: every
diagram in the third pass parsed cleanly and still had colliding labels or text
running past the viewBox.

## Architecture and chapter integration

| Location | Responsibility |
|---|---|
| `app.py` | Shared fluid sidebar, navigation, chapter wrappers, source fingerprint and module reload guard |
| `src/ui/learning_path.py` | Twelve lesson records: question, prerequisites, route, equation, explanation and closing experiment |
| `src/ui/pedagogy.py` | Prose/math rendering, callouts and scrollable Plotly wrapper |
| `src/theme.py` | Streamlit CSS and Plotly theme |
| `src/svg_diagrams.py` | SVG teaching figures, cleanup and native-image rendering |
| `src/units.py` | Shared fluid state and existing display-unit conversions |
| `src/physics/pipe_flow.py` | Churchill/Colebrook friction, pipe/pump calculations and material roughness estimates |
| `src/physics/pipe_network.py` | Nominal schedules, pipe-input resolution, signed head losses and nodal network solution |
| `src/physics/open_channel.py` | Trapezoidal geometry, Manning and Darcy uniform flow, normal/critical depth, Froude, freeboard |
| `src/physics/transport_analogy.py` | Diffusivity ratios, one correlation table serving heat and mass, Pohlhausen thermal-layer ODE |
| `src/physics/impeller.py` | Blade camberline from the angle definition, 3D blade surfaces, slip, velocity triangles, isometric projection |
| `src/svg_impeller.py` | Impeller diagrams projected from that computed geometry (needs NumPy, so kept out of `svg_diagrams.py`) |
| `src/physics/gas_dynamics.py` | Perfect-gas nozzle, normal shock, compressor/turbine and sphere-drag calculations |
| `src/physics/rocket_nozzle.py` | Expansion ratio, thrust coefficient and c*, US Standard Atmosphere, Prandtl-Meyer, method-of-characteristics contour, cone/bell/converging geometry |
| `src/ui/pipe_network_lab.py` | Chapter 2 schedule calculator, editable node/pipe tables and network results |
| `src/ui/tab_non_newtonian.py` | Chapter 7: constitutive behaviour — flow curves, Herschel–Bulkley pipe flow, thixotropy kinetics, Weissenberg/Deborah |
| `src/ui/tab_external_flow.py` | Chapter 9: Stokes flow, settling and drag crisis |
| `src/ui/tab_turbomachinery.py` | Chapter 11: angular momentum, velocity triangles, work and thermal effects |
| `src/ui/tab_compressible.py` | Chapter 12: compressible derivations, nozzle/shock labs, Fanno and Rayleigh flow |
| `src/ui/rocket_nozzle_lab.py` | Chapter 12 section 5: rocket nozzle performance, altitude behaviour, sizing march and contour design |
| `src/ui/tab_cfd.py` | Chapter 13: incompressible projection solver and benchmark interpretation |

Current order: 1 Energy, 2 Pipes, 3 Scaling, 4 Turbulence, 5 Euler, 6 Stress & NS, 7 Non-Newtonian, 8 Exact flows, 9 External flow, 10 Momentum, 11 Turbomachinery, 12 Compressible, 13 CFD, 14 Reference. Chapter 7 sits directly after the chapter that states the Newtonian constitutive law, because it is that law being taken apart. Keep compressible flow before CFD, while explicitly explaining that the existing CFD solver is incompressible.

`app.py` owns chapter headers/recaps. Avoid duplicate main headings inside individual renderers. Adding a module also requires adding it to `_MODULE_RELOAD_ORDER`: the fingerprint only includes `app.py` and modules named in that list. Keep dependency reloads before their consumers. The current reload guard catches import/reload exceptions, so it is not a substitute for a compile/import check or AppTest.

Shared sidebar density/viscosity feed incompressible, pipe and external-flow labs. The gas-machine/nozzle labs have separate thermodynamic inputs. New engineering calculators show explicitly labeled SI quantities independently of the older nondimensional display toggle; do not claim that the toggle changes every calculator.

## Rendering failures to avoid

### Equations

Streamlit can mishandle multiline `$$...$$` in `st.markdown`, displaying raw TeX or losing a line. Alerts and raw HTML are also unsuitable paths for display equations.

- Use `render_prose_and_latex` for prose containing display blocks, and `render_latex`/`st.latex` for individual equations. Prefer raw Python strings for TeX.
- The helper flattens whitespace before rendering each equation.
- `tests/test_katex_safety.py` checks source patterns; browser checks additionally look for `.katex-error`.
- A syntactically valid equation can still be too wide: verify small-screen overflow and readability visually.
- **A prose literal whose first line is flush against the opening quotes is never dedented.** `textwrap.dedent` strips the *common* leading whitespace, so `prose(r'''First line...` with later lines indented to match the code has a common prefix of `""` and nothing is removed. Every paragraph after the first blank line then arrives with four spaces and renders as a monospace code block with its `$math$` and `**bold**` intact -- it looks like a KaTeX failure and is a markdown one. Start the literal with a newline so every line shares one indent. `tests/test_markdown_indentation.py::test_prose_literals_survive_dedenting` scans every `prose`/`render_callout` literal in `src/ui` for this, including plain paragraphs, which the older `accidental_code_blocks` scan deliberately ignores.

### SVG diagrams

An earlier cleanup routine joined stripped SVG lines with an empty separator. Attributes on neighboring lines then merged into invalid XML. `clean_svg` now joins with spaces. Preserve this separator.

Raw-HTML rendering stripped SVG content in the installed Streamlit frontend. `render_svg` now uses `st.image` inside a keyed figure container. Keep descriptions/labels and the native-image path. Tests parse the cleaned SVG as XML and check the renderer API.

Check labels, arrows, geometry and clipping, not just XML validity. The prior visual pass covered 16 existing SVG teaching diagrams. New plots supplement those figures; adding a new SVG requires extending the relevant test coverage.

### Plotly and responsive layout

- Use `apply_plotly_theme` and `render_plot(figure, unique_key)`.
- Explicitly set an absent title to an empty string; Plotly 7 otherwise exposed an `undefined` title in this app.
- The installed Streamlit tab DOM uses role-based/React Aria selectors. Old `data-baseweb` tab selectors did not apply.
- A minimum width on only `stPlotlyChart` did not reliably resize Plotly's internal SVG. The existing CSS sets a minimum width on the element container inside `st-key-plot-*`, with an outer horizontal scroll area.
- The wide plot is intentional on narrow screens. Check that scrolling is available and that labels are readable across the entire figure.
- **A shape on a log axis is positioned in log10 of the data value.** `add_hline(y=101.3)` on a `type="log"` axis asks Plotly for `y = 10^101.3`, which drags the axis range out to `10^110` and flattens the real curve onto the floor of the panel. Pass `np.log10(value)` for `add_hline`, `add_vline` and `add_shape` whenever that axis is logarithmic. Traces are unaffected -- they take data coordinates as usual, which is what makes the mistake easy to miss in review and obvious on screen.
- An honest curve can still be a useless picture: a sea-level `C_F` curve continues to zero and below far past its optimum, compressing every peak into the top of the frame. Clip the view to the region the comparison lives in and say why in the prose, rather than letting autoscale decide.
- Network node labels needed explicit axis padding. Automatic ranges clipped the second line of the lowest node label. Direction arrows follow actual signed flow; table `from`/`to` remains the reference convention.

## Live-browser rerun problem: observations and working configuration

This was the most time-consuming failure. A page could appear fully drawn, with no Python exception or KaTeX error, while the Stop/running indicator remained visible and subsequent widget actions did not produce results. The network worked in direct Python calls and Streamlit AppTest, yet the live solve button appeared ineffective. A separate headless Edge session reproduced the failure, so it was not confined to the in-app browser automation.

Diagnostic prints showed that application rendering reached its end. Repeated browser reloads, extra tabs and restarting the server alone did not reliably resolve the interaction problem. Disabling automatic file watching produced a successful isolated browser run. The final main-server verification passed with **both** of these settings and with the test waiting for complete initial rendering:

```toml
[server]
fileWatcherType = "none"

[runner]
fastReruns = false
```

These settings are committed in `.streamlit/config.toml`. They avoid filesystem watching and overlapping script reruns while this app reloads shared Python modules. Restart the server when changing server configuration; manually refresh/rerun after source edits.

**Evidence boundary:** the combined configuration and browser sequence were verified. The session did not isolate a definitive upstream Streamlit/Python defect or prove that either setting alone fixes every case. Do not reduce this history to an established universal “Windows watcher bug,” or re-enable either setting based only on unit tests.

For future diagnosis, first wait for the final reference chapter to exist and the running indicator to disappear. Then exercise a real widget and wait for its result. If a regression returns, inspect browser console errors and the server lifecycle, and compare a clean browser session. Avoid accumulating diagnostic tabs/servers. Remove diagnostic prints and temporary scripts when finished.

## Physics contracts and model limits

### Churchill and nominal pipe sizes

Churchill returns the **Darcy** friction factor; Fanning is one quarter of Darcy. At small positive Reynolds number use the laminar limit `64/Re`. At zero flow the friction factor is undefined, but losses and pumping power must be zero. Preserve the finite laminar slope of signed head loss at zero flow for network iteration.

The schedule table covers nominal steel pipe NPS 1/2–4, Schedule 40/80. Compute inside diameter from nominal OD minus twice wall thickness; do not mistake NPS for bore. Measured ID is the escape hatch for other sizes. Schedules are geometry, not pressure ratings, and corrosion/lining/tolerances affect real bore. Material roughness values are estimates, not certified properties.

Source: [Wheatland manufacturer brochure](https://www.wheatland.com/wp-content/uploads/2017/12/Standard-Pipe-Brochure-2.pdf), nominal OD/wall tables on printed pages 4–5. Computing ID from those dimensions avoids inconsistencies in rounded tabulated IDs.

### Network solver

- Steady, incompressible, single-phase flow. No pump curves, automatic valves, compressible-gas behavior or cavitation model.
- Node head is `H = z + p/(rho*g)` with a common **gauge-pressure** reference. Junctions are common hydraulic-head connections; entered minor losses account for fittings within this approximation.
- A `Pressure` node prescribes pressure/elevation. Its boundary exchange is an output, and its demand input must be zero.
- A `Junction` prescribes elevation and signed external demand. Pressure is an output; its pressure input is ignored.
- Demand is positive for withdrawal, negative for injection. Continuity is `sum(out) - sum(in) + demand = 0`. Only zero-demand junctions have zero net pipe flow.
- A pipe's positive flow follows its `from` → `to` reference; negative means reverse flow. Signed loss is proportional to `Q*abs(Q)` outside the creeping-flow branch.
- Each connected component needs a prescribed-pressure boundary. Reject isolated/duplicate nodes, missing endpoints and invalid dimensions.
- The solver guesses unknown nodal heads, inverts each pipe's head-loss relationship with a bracketed scalar solve, and adjusts heads using nonlinear least squares on junction imbalances. Recompute Churchill friction at each flow; do not freeze resistance across changing regimes.
- Current limits: 2–40 nodes, 1–80 pipes, relative roughness at most 0.05. Report continuity and edge-energy residuals, not just solver success.
- Results are stored alongside a signature of edited tables and fluid properties. Display only matching results, so changed inputs cannot show a stale solution. Downloads should preserve the current result.

The default four-node/four-pipe loop has Supply at 300 kPag and z = 0, Outlet at 50 kPag and z = 8 m, and a 2 m³/h withdrawal at B. With default water properties, supply is approximately 32.0179 m³/h, A is 204.953 kPag, and B is 103.556 kPag. The example solved in seven iterations with residuals near floating-point precision. These values are a sanity check, not hard-coded outputs.

[EPA EPANET](https://www.epa.gov/water-research/epanet) is a reference for network conservation principles. This implementation is a custom educational nodal solver, not EPANET.

### External flow

Sphere drag uses projected area `pi*d²/4` and sphere Reynolds number. Stokes drag is `3*pi*mu*d*U`; its terminal-settling estimate must be checked against the resulting terminal Reynolds number, not merely the entered-speed Reynolds number. It assumes an isolated rigid sphere with no slip in creeping flow.

Schiller–Naumann is used only up to Re = 1000 in this demonstration. The dotted high-Re drag-crisis curve is explicitly schematic and is **not** used to calculate force. Roughness and upstream turbulence shift the crisis; do not present a universal critical Re or apply circular-pipe thresholds. [NASA's sphere-drag explanation](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/drag-of-a-sphere/) supports the boundary-layer/separation discussion.

### Turbomachinery and compressible flow

- Euler rotor work is `delta h0 = U2*Ctheta2 - U1*Ctheta1`, using **absolute** tangential velocity. Positive work enters the fluid; turbine shaft output has the opposite sign. Keep `C = U + W` and distinguish static from stagnation enthalpy.
- Machine pressure ratio is entered as **high/low ≥ 1**, with mode selecting compression or expansion. Lower compressor efficiency increases the temperature rise; lower turbine efficiency reduces the temperature drop and shaft output.
- Gas pressures are **absolute**, temperatures kelvin, and cp/γ constant. These models do not cover real-gas or phase-change behavior.
- The nozzle is an ideal converging nozzle with discharge coefficient 1. Choked flow plateaus below the critical back-pressure ratio. Exit pressure need not equal back pressure when choked. Back pressure at/above reservoir pressure returns no forward flow; reverse flow is not modeled.
- Normal shocks conserve mass, momentum and total energy. Stagnation temperature remains constant while stagnation pressure falls. Apply isentropic stagnation relations separately on each side, never through the shock itself.
- A nozzle's static cooling, a turbine's stagnation cooling and a valve's approximately constant-enthalpy process are different. An ideal-gas throttle has no temperature change under the stated endpoint assumptions; real-gas Joule–Thomson behavior depends on state.
- Intercooling/reheating comparisons assume equal stage ratios, constant efficiency and no interstage pressure loss. Distinguish intercooler duty from a final aftercooler.
- Fanno and Rayleigh sections are derivations and model explanations, not a combined heated compressible-pipe network solver. The Fanno length expression uses **Darcy** friction; avoid an extra factor of four.

Primary references linked in the lessons: [MIT Euler turbine equation](https://web.mit.edu/course/16/16.unified/www/SPRING/thermodynamics/notes/node91.html), [NASA isentropic relations](https://www.grc.nasa.gov/www/k-12/airplane/isentrop.html), [NASA normal shocks](https://www.grc.nasa.gov/WWW/k-12/airplane/normal.html), [NPTEL Fanno flow](https://archive.nptel.ac.in/content/storage2/courses/112103021/module2/lec15/1.html), and [NPTEL Rayleigh flow](https://archive.nptel.ac.in/content/storage2/courses/112103021/module2/lec14/1.html).

### Rocket nozzles

- Chamber conditions are stagnation conditions. Combustion, finite nozzle-inlet Mach number, boundary layers, wall heat transfer, chemical recombination during the expansion and two-phase (condensed-oxide) flow are all outside the model. Real engines report a `c*` efficiency of roughly 0.92-0.99 and a nozzle efficiency of roughly 0.95-0.99 against exactly these ideal numbers; do not present the ideal value as a prediction of hardware.
- Split performance as `Isp = C_F c* / g0`. `c* = sqrt(R T_c)/Gamma` is a statement about the **chamber alone** and contains no area but the throat, which cancels. `C_F` is a statement about the **nozzle alone** and contains no chamber temperature. The split is what lets a test stand blame the injector or the bell separately, and the tests pin both invariances.
- Thrust is `F = mdot ve + (pe - pa) Ae`. That equation is derived in chapter 10 §10.7 from a control volume; chapter 12 must not re-derive it. What chapter 12 adds is the gas dynamics that supply `ve`, `pe` and `Ae`, which a momentum balance takes as given.
- `pe` is fixed by the area ratio and the chamber state; `pa` is fixed by altitude. They are equal at one altitude only. The matched condition follows from `dF/dAe = pe - pa` -- a differential ring of bell -- and the app checks that argument against the algebra by marking the independently computed matched ratio on each `C_F` curve, where it must land on the peak.
- Momentum thrust is altitude-blind. The whole sea-level/vacuum difference is `pa Ae`, and a test asserts that the vacuum-minus-pad thrust equals it exactly.
- Separation criteria (Summerfield `pe ~ 0.4 pa`, Schmucker) are **correlations of test data, not results of the model**. The ideal model will happily report thrust for a deeply over-expanded nozzle that would in reality be flowing separated with side loads. Always report the separation check beside the number; the lesson's `eps = 165` row exists to show the model being wrong without complaint.
- The method-of-characteristics contour is **planar (2D)**, which is the case whose arithmetic can be followed by hand. Axisymmetric nozzles carry an extra term. Within the planar construction every `(theta, nu)` is exact and closed form -- `theta = j dtheta`, `nu = (2k+j) dtheta` -- and only the *positions* carry discretisation error from averaging characteristic slopes between points. So refining the wave count refines the wall shape while the exit Mach number stays pinned at its imposed value; the convergence table in the lesson is computed live rather than asserted.
- `theta_max = nu(Me)/2` for a minimum-length nozzle, exactly. For M = 2.4 and gamma = 1.4 that is 18.37 degrees, matching Anderson's worked example, and the last wall point comes out axial at exactly the design Mach number. That is the construction's own success criterion and is tested as such.
- Rao's `theta_n` and `theta_e` are **inputs, not outputs**. Reproducing his optimisation needs an axisymmetric characteristics solve with a variational condition on a control surface. What `bell_contour` guarantees is a tangent-continuous contour that hits the requested area ratio exactly; the 1.5 `r_t` and 0.382 `r_t` throat arcs are workshop conventions, not derivations, and the lesson says so.
- The cone divergence efficiency `lambda = (1 + cos a)/2` is derived by averaging axial momentum over a spherical cap, and the test checks the closed form against the integral rather than against a remembered 0.983.
- `march_along_contour` is quasi-one-dimensional and deliberately ignores the two-dimensionality that the characteristics method exists to capture. It shows *where* the expansion happens; it is not a design result.
- Atmosphere is US Standard 1976 to 71 km, extrapolated above. Only pressure is returned, because that is the only atmospheric property a thrust calculation needs -- the nozzle's working fluid is the propellant, not the air. The test re-derives each layer's published base pressure by chaining the barometric formula.

Primary references linked in the lesson: [NASA rocket thrust](https://www.grc.nasa.gov/www/k-12/airplane/rockth.html), [NASA nozzle design](https://www.grc.nasa.gov/www/k-12/airplane/nozzle.html), and G. V. R. Rao, "Exhaust nozzle contour for optimum thrust", *Jet Propulsion* 28 (1958). Propellant numbers in the worked examples are representative teaching values, not a manufacturer's data sheet.

### Existing CFD regressions

Retain tests for the first-step moving-lid boundary condition, preservation of interior vertical momentum, viscous timestep limit, invalid parameters and nondimensional Ghia error scaling. The Ghia overlay is only meaningful for the matching Re = 100 case. A short visually plausible vortex is not a converged benchmark: report nondimensional elapsed time, divergence and benchmark error together. Compressible shocks/choking are outside this solver's scope.

## Verification workflow and baseline

At completion of the third pass, **247 pytest cases passed** (76 after the first pass, 170 after the second). The live headless-Edge check also passed: network solve, CSV download, new chapter navigation, no KaTeX errors and no browser page errors. A separate AppTest exercise changed a junction elevation and changed a pipe to measured ID with relative roughness; the resulting geometry/pressure changed correctly. Invalid roughness, compressor/turbine switching and no-forward-flow nozzle behavior were also exercised.

```powershell
# Optional integration test; keep the app running on port 8501.
uv run --with playwright python tests/browser_smoke.py
```

This command uses a temporary uv-provided Playwright dependency and an installed Microsoft Edge browser. It writes `network-verification.png` in the project root. The screenshot is generated evidence, not an input to the application. Python subprocess output on Windows may need UTF-8 configuration for symbols; the script already configures stdout.

The browser smoke test is intentionally separate from default pytest. It checks live lifecycle behavior that AppTest cannot establish. Its current automated layout coverage is desktop-sized; manually inspect narrow screens, horizontal scroll areas, new diagrams, changed formulas and edited-table workflows when modifying those surfaces. Neither test suite proves all physical assumptions are appropriate for arbitrary user input.

Useful test files: `test_network_and_gas.py` (conservation, analytical limits, signs and input validation), `test_pipe_flow.py` (zero flow and friction), `test_numerical_solver.py` (CFD regressions), `test_katex_safety.py` (math rendering paths), and `test_svg_diagrams.py` (XML/native-image rendering).

## Boundaries for future extensions

Potential extensions include more verified schedules, pump curves and valves, real-gas property backends, combined heat/friction gas ducts, or a compressible network solver. These are not implemented by the current educational correlations. Add their governing equations, boundary-condition semantics and conservation tests before presenting them as supported capabilities. Preserve the existing editable incompressible network workflow and the distinction between schematic diagrams and validated numerical correlations.

## Second pass: theme template, SOR projection, and three expanded chapters

Recorded after the review that followed the notes above. Treat counts here as a dated baseline.

### Plotly theming is a template, not per-figure updates

`apply_plotly_theme` used `update_layout(xaxis=..., yaxis=...)`, which only reaches
`layout.xaxis` and `layout.yaxis`. Nine figures use `make_subplots`, so **every second and
third panel rendered with Plotly's light defaults** — a white grid and near-black tick
labels on the dark surface. Verified directly: `xaxis.gridcolor` was `#1e293b` while
`xaxis2.gridcolor` was `None`.

The fix registers a `plotly.io.templates` entry once and sets `template=` per figure. A
template's `layout.xaxis` applies to *every* x axis, so subplots are covered, and the
per-figure dict merging (0.36 s of a 1.37 s profiled rerun across 21 figures) disappears.
`tests/test_plotting_theme.py` pins this, including an assertion that `plotting.py` contains
no `gridcolor` at all — per-figure colour overrides are how this regression would return.
The explicit `title=` assignment stays: Plotly 7 renders an `undefined` title without it.

### The pressure Poisson solve was never converging

Two separate problems, found while replacing Jacobi with red-black SOR:

1. **Solvability.** With `dp/dn = 0` on every wall, the source must integrate to zero or no
   solution exists. Impermeable walls make the *continuous* net flux zero, but central
   differences on a collocated grid decouple even and odd nodes and leave a small nonzero
   discrete mean. Until that is projected out, more sweeps cannot help — the residual
   saturated at ~19 regardless of iteration count. Subtracting the interior mean of the RHS
   is the standard remedy and is now applied; do not remove it.
2. **Relaxation rate.** Jacobi needs O(N²) sweeps for the longest wavelength; SOR with
   ω → 2 needs O(N). Measured on a 41×41 test problem at 1000 sweeps: Jacobi residual
   6.35e-3, red-black SOR 5.97e-11. `test_sor_converges_and_beats_jacobi` keeps the old
   Jacobi as a baseline in the test file so the comparison stays honest.

The red-black colouring matters: it keeps each half-sweep a single NumPy expression while
still reading updated neighbours (true Gauss–Seidel). A naive in-place slice assignment is
still Jacobi, because NumPy evaluates the whole right-hand side first.

**`max_divergence` is dominated by the lid corners**, where u jumps from `u_lid` to 0 across
one cell. That is a singularity of the problem statement, not a failure of the projection,
and no amount of solving removes it. The solver now also returns `max_divergence_interior`,
excluding three nodes from each wall, and the UI shows that with the global figure in the
tooltip. A staggered (MAC) grid would fix the underlying collocated-grid decoupling; that is
a rewrite, not a patch, and was deliberately not attempted.

### Diagrams generated from geometry

`src/svg_impeller.py` projects the blade surfaces computed in `src/physics/impeller.py`
rather than drawing them freehand, so an angle in the figure is the angle the arithmetic
uses. Two conventions were made explicit because mixing them is the single most common
turbomachinery error: **angles here are measured from the tangential direction**, and every
result dictionary also reports the from-meridional complement.

Things learned while drawing them:

- The axial scale must be exaggerated (2.6× in the 3D view, 2.4× in the meridional) or a
  12 mm passage on a 300 mm wheel collapses into edge-on slivers. Radii and all
  r–theta angles are untouched, and the captions say so.
- Far blades need real contrast, not just low opacity, or the wheel reads as empty.
- **There is no Unicode subscript "w".** U+2095 is subscript *h*, so `P&#8341;` silently
  rendered as `Pₕ`. Wall subscripts now use a `tspan`. Subscript h *is* correct for `R_h`
  and `D_h`.
- A doubled brace inside an f-string leaks a literal `{name}` into the SVG. This was caught
  only by looking at the rendered page, so `test_no_unresolved_format_placeholders_in_diagrams`
  now scans every `diagram_*` function for it.
- XML validity proves nothing about layout. Every diagram in this pass was rendered in a
  real browser and several were repositioned afterwards; label collisions and text
  overflowing the viewBox were the common faults.

### Test and lint infrastructure

- `tests/test_app_smoke.py` runs the whole app through `AppTest` and asserts no exception.
  It also checks `_MODULE_RELOAD_ORDER` against the files on disk in both directions — this
  caught three new modules that had not been registered, exactly the failure the reload
  guard hides by swallowing exceptions.
- `ruff` is configured in `pyproject.toml` with `select = ["F", "E9", "W6"]` — undefined
  names, unused imports, syntax errors. Style rules are deliberately off so the existing
  dense physics formatting is not churned.
- `.github/workflows/tests.yml` runs `uv sync --locked`, pytest and ruff.
- The existing `test_katex_safety.py` earned its keep: it caught math placed inside
  `st.info` in the new air-separation section. Alerts do not run KaTeX; use `render_callout`.

### Worked examples must match the calculator defaults

The canal worked example was first written with `n = 0.025` while the calculator's default
material is 0.022, so a student following the text would not reproduce the numbers. Every
worked figure in these chapters is now computed with the app's own defaults. Where a number
in prose comes from the physics modules, recompute it rather than editing it by hand.

### Navigation: one chapter at a time, and why `st.tabs` had to go

`st.tabs` executes **every** panel body on every script run. With twelve chapters that meant
rebuilding every Plotly figure, every SVG and every solver call whenever any widget moved.
After the Blasius, open-channel and air-separation sections were added, the front end
stopped finishing the render.

The symptom is worth recording precisely, because it looks like a Python bug and is not:

- `AppTest` completed the whole script in 0.47 s with **no exception** and produced all 103
  metrics, including every air-separation one.
- The browser stopped at 74 metrics, part-way through chapter 9, with the running indicator
  still showing. Reproduced on a freshly started server, held for 90+ seconds, and produced
  no console errors.
- Bisection settled it: commenting out chapters 1–6 let chapter 9 render to completion and
  the run finish. The cause was cumulative page size, not the new content.

`@st.fragment` does not help here — fragments limit *reruns*, not the initial render. The
fix is to render only the selected chapter. `app.py` now drives a `st.radio` keyed
`chapter_nav` and dispatches to one renderer. Measured effect: a rerun went from 0.47 s to
0.02 s.

The radio is styled in `src/theme.py` to look like the old tabs, using `data-testid` and
`data-selected` selectors rather than the generated `st-emotion-cache-*` class names, which
are not stable across Streamlit versions. The radio dot is hidden with CSS only; the
accessible `<input type="radio">` is untouched, so keyboard and screen-reader behaviour is
unchanged.

Consequences to keep in mind:

- Switching chapters is now a rerun, not a client-side tab switch. Explicit widget keys
  alone do **not** preserve values: Streamlit cleans up keys for widgets that are absent
  from a run. Use `persistent_input` from `src/ui/state.py` for lesson controls and
  self-checks; it saves values in a separate session dictionary and restores them when
  the widget returns. Each input needs a unique explicit key.
- Anything that assumed all chapters are in the DOM at once — old browser tests, in-page
  anchors between chapters — no longer holds.
- `tests/test_app_smoke.py` pins the behaviour in both directions: the twelve options exist,
  chapter 9's content is *absent* while chapter 1 is selected, and selecting chapter 9
  renders it. Two further tests change a widget and assert the numbers actually recompute
  (air feed doubles MAC power; a rougher canal runs deeper).

Do not restore `st.tabs` without re-measuring the full-page render in a real browser. A
passing AppTest does not establish that the page finishes drawing — that was the entire
lesson here, and it matches the earlier live-browser section above.

## Third pass: rendering root causes, transport analogy, relief sizing

Recorded after the session that fixed the LaTeX rendering complaint, rebuilt the
impeller figures, founded the scaling chapter on the SVD, and added the
transport analogy and pressure-relief sections. Test count went 195 to 247.

### Markdown indentation kills KaTeX, and looks like a KaTeX bug

The reported symptom was "LaTeX did not render properly, this happens in many
places". The cause was markdown.

A triple-quoted prose block carries the source indentation of the function it
sits in. `iter_prose_and_math` only called `.strip()`, which dedents the **first**
line; every later line still began with eight spaces. In CommonMark a line
indented four or more spaces *after a blank line* opens an indented code block,
so the list, the `**bold**` and the `$...$` all rendered literally in monospace
and KaTeX never ran on any of it.

Why it hid: a single-paragraph block is unaffected, because its later lines are
lazy continuations of the first paragraph and their indentation is ignored. The
bug only fires when a chunk contains a blank line followed by indented content,
which means lists and multi-paragraph prose. Two live instances had presumably
been visible for some time before anyone reported them: the Moody-zone list in
chapter 2 and the entire textbook reference list in chapter 12.

`src/ui/pedagogy.py` now exposes `dedent_markdown()` and applies it inside
`iter_prose_and_math`, so anything routed through the helpers is safe.
`textwrap.dedent` strips only the common prefix, so a list continuation indented
three spaces deeper stays three deeper and remains inside its list item.

Direct `st.markdown` calls bypass the helpers, so
`tests/test_markdown_indentation.py` walks the AST of every UI module, extracts
string literals passed to `st.markdown` / `st.caption` / `st.write`, and fails on
any that CommonMark would swallow. **Prefer `render_prose_and_latex` for any
block containing a blank line.**

### Unicode has no subscript for "w", and the neighbours are currency signs

Subscripts exist in Unicode for digits and a handful of lowercase letters. There
is none for `w`, and none for capitals. Guessing a numeric entity near the
subscript block lands in Currency Symbols: `&#8354;` is U+20A2, the CRUZEIRO
SIGN, and it was rendering as a wall subscript in the canal diagrams. The
transport diagrams then repeated the mistake twice more, with `&#8347;`
(subscript *s*, used for *x*) and `&#8320;&#8342;` (subscript zero and *k*, used
for *AB*).

Use `svg_diagrams._sub()` for any subscript Unicode does not provide. `R_h` and
`D_h` are genuinely fine as `&#8341;`, because subscript *h* exists.
`test_no_diagram_contains_a_currency_or_stray_symbol` asserts no diagram output
contains a Currency Symbols character, which catches the entire class for free.

### Angles cannot be drawn on an axonometric projection

The impeller figure originally marked beta_2 on the 3D view. A projection
foreshortens each direction by a different amount, so a 25-degree blade angle
rendered as roughly 50. No caption rescues an angle that is drawn wrong.

The figure is now two panels, the split turbomachinery texts use: the axonometric
wheel for shape, claiming nothing about angles, and a plan view down the shaft
for the angles, where the r-theta plane is undistorted and they are true. As a
side effect the legend fits, because each panel only has to label what it can
honestly show.

Two related rules came out of the same work:

* **Every angle mark draws both bounding rays from its vertex.** An arc floating
  beside a vector does not say which two directions it spans; that was the
  substance of the original complaint. `_angle_mark` in `src/svg_impeller.py`
  does vertex dot, two dashed rays, shaded wedge, label on the bisector.
* **A velocity triangle is drawn closed, head to tail.** The 3D figure had drawn
  U2, W2, Cm2 and C2 radiating from one point, which is not a triangle and shows
  nothing of C = U + W.

When placing annotations on a projected figure, pick the annotated feature by
*projected* geometry, not by world geometry: `diagram_blade_angles` chooses the
blade whose tangent survives the projection best **and** points into empty
canvas, and sizes the marks by their length in pixels rather than in metres.
Choosing by world angle alone gives marks that shrink or overlap the wheel
depending on the viewing angle.

### Confusing a ratio of derivatives with a ratio of integrated changes

The one physics error a reader spotted directly. The Blasius section claimed
`dp/dy` is smaller than `dp/dx` by `(delta/x)^2`. It is smaller by `delta/x`;
`(delta/x)^2` is the ratio of the pressure *changes*, because the transverse one
is accumulated over only `delta` while the streamwise one accumulates over `x`.

Both numbers appear in textbooks attached to different quantities, which is
exactly why the slip is easy. When writing a scaling argument, state explicitly
whether the comparison is between gradients or between integrated changes, and
if both are interesting, give both with their factors, as that section now does.

### Internal inconsistency is the cheapest error signal

An independent audit of the new content found six confirmed errors. **Three of
them contradicted a neighbouring sentence in the same paragraph:**

* the shape factor was said to rise as the profile becomes *fuller*, two
  sentences before correctly saying separation is approached at high `H`;
* the degree of reaction was said to approach 1 for a radial blade, immediately
  before correctly describing the radial blade's fast discharge;
* the blade-to-blade plane was described as a fixed-radius cut, in a paragraph
  whose own equation `tan(beta) = dr/(r dtheta)` requires otherwise.

Re-reading a passage against itself is far cheaper than re-deriving it, and it
found half the defects here. Do that pass before asking for external review.

### Make the app compute what the prose claims

Wherever a constant or a comparison could be recomputed, it now is, and the
recomputation is the check:

* `pohlhausen_theta_gradient` solves the thermal boundary-layer ODE, and at
  `Pr = 1` returns 0.33206 against Blasius `f''(0) = 0.332057` -- because at
  `Pr = 1` the energy equation *is* the differentiated Blasius equation. The
  familiar `0.332 Pr^(1/3)` is then shown to be a ~2% fit to the solved ODE,
  rather than quoted.
* The open-channel section runs Darcy alongside Manning and prints the
  disagreement instead of hiding it.
* The SOR change was justified by benchmarking against the Jacobi it replaced,
  and the old Jacobi is kept in the test file as that baseline.

This is more work than asserting the number, and it is what makes the numbers
trustworthy when the surrounding prose is later edited.

### Physics module conventions worth keeping

Established across `impeller.py`, `open_channel.py` and `transport_analogy.py`:

* **State the convention in code, and report both.** Blade angles are measured
  from tangential; every result dictionary also carries the `*_from_meridional`
  complement, so a reader can check against either textbook. The single
  ambiguity that causes the most wrong answers is not left implicit.
* **Store a shared correlation once.** `transport_analogy.CORRELATIONS` holds one
  entry per geometry and evaluates it for heat or mass by swapping `Pr` for `Sc`.
  Heat and mass therefore cannot drift apart -- the analogy is expressed as code
  rather than as a claim in prose.
* **Attach validity ranges and report them.** Correlations carry `re_range` and
  `pr_range`; the UI warns rather than silently extrapolating, and the plot draws
  each curve only across its own band.
* **Put the model limits in the module docstring**, not only in the UI. They are
  what the next person needs before reusing the function.

### Writing source files: escaping hazards

Two mistakes cost time and both are silent:

* A bash heredoc carrying Python turned `\theta` into a literal **tab** character
  inside a prose string. It passed tests and only showed up in the rendered page.
* `"\m"` and similar produced `SyntaxWarning: invalid escape sequence` in strings
  that then behaved unexpectedly.

Prefer writing file content with an editor tool over shell heredocs when the
content contains backslashes; use raw strings for anything with TeX; and after a
bulk edit, scan for stray control characters, which is a two-line check and
catches the tab case immediately.

### Test patterns that earned their keep

All of these are cheap, and each catches a whole class rather than one instance:

| Test | Catches |
|---|---|
| AST scan of `st.markdown` literals | indentation that becomes a code block |
| Currency-character scan of every diagram | invented Unicode subscripts |
| `{placeholder}` regex over every diagram | doubled braces in f-strings |
| `_MODULE_RELOAD_ORDER` vs the file tree, both directions | modules that never reload |
| "no `gridcolor` in `plotting.py`" | per-figure theme overrides returning |
| Build every figure, assert traces > 0 | figures that silently render empty |
| AppTest widget change, assert the number moves | UI that redraws but does not recompute |
| Old algorithm kept as a benchmark baseline | performance claims going stale |

## Navigation and diagnostic fixes

The navigation round-trip regression was reproduced with air feed: 60 kg/s reverted
to 30 kg/s after leaving and returning to chapter 9. `persistent_input` now covers
calculator inputs, conditional controls and self-checks. Keep button events outside
this helper. `persistent_editor` stores both the editor's fixed base and its latest
complete table; it mounts the latest table as a new base only after widget cleanup.
Replacing the base on every rerun would replay editor deltas and corrupt added or
deleted rows. Saved network solutions still require a matching input signature.

An explicit widget key controls identity, not lifetime. `persistent_input` saves
values in a non-widget session dictionary and restores only absent widget keys,
so a current edit takes priority. Avoid initializing a restored control with
`session_state.setdefault(widget_key, default)` before calling the helper: that
creates the key early and prevents restoration. This occurred in the stress
preset lab. Initialize a preset when it is first selected or actually changes;
otherwise let the persistence helper restore the previous values. Keep storage
session-local, and test that a second browser/AppTest session starts at defaults.

The live browser test clicks the visible radio label, waits for the selected chapter's
recap and for script completion, and then checks for errors. A radio-input click is
intercepted by the custom label; the old tab selectors do not match anything. The test
now visits all twelve chapters and verifies an air-feed round trip, network solve and
CSV download. AppTest additionally covers editor cell changes, row insertion/deletion,
result invalidation and isolation between sessions.

**The browser waits that mattered:**

- On chapter changes, wait for `.st-key-chapter-recap-N`, then the running/Stop
  indicator to disappear, before checking errors. Immediately checking the DOM
  after a click can inspect the previous chapter instead.
- On **same-chapter** changes, the recap already exists. First wait for a
  distinctive new result (the changed preset explanation or expected bore), then
  wait for completion. A stable old recap is not an acknowledgement of a rerun.
- The styled radio input is covered by its label. Click `stRadioOption` containing
  the named radio, not the input itself; do not work around this with force-clicks.
- For the searchable preset combobox, click, fill the desired option text, and
  select that exact option. Reopening it after screenshots/scrolling without
  filling proved unreliable in the educational test.
- The sidebar collapse control is revealed by hovering `stSidebarHeader`.
  Collapse it at desktop width before resizing to phone width, then wait for the
  sidebar to leave the viewport. Trying to click it after resizing failed when
  its button was outside the viewport.
- SVG scrolling belongs to the figure's `stImage` element, not its outer keyed
  container. Check its `scrollWidth > clientWidth`, move `scrollLeft`, and inspect
  the result. The Plotly wrapper has a different scrolling structure.

The CFD Poisson residual now uses the same mean-adjusted Neumann source as the solver.
The signed source mean removed is reported separately as
`poisson_compatibility_correction`, in the same pressure-Laplacian units as the residual.
A small iterative residual does not imply a small compatibility correction or exact
velocity mass conservation.

Test this distinction with a deliberately nonzero-mean source. The solver can
converge on the compatible equation while the removed mean remains large; a
zero-mean-only fixture cannot detect using the wrong source in the residual.

Relief sizing rejects non-finite or out-of-range discharge coefficients and back
pressure at or above the upstream stagnation pressure. Unlike the nozzle capacity
function, a sizing function cannot return a finite area for positive required flow
when there is no forward-flow pressure difference.

## Educational geometry and worked examples

The deformation lab now integrates a constant velocity gradient with `exp(L t)`.
The old `I + L t` approximation enlarged a rigidly rotating parcel by 6.25% at
the displayed time step. Perimeters and internal grid lines use the same exact
map; the displayed angle is measured from transformed material directions.
The D-only and Omega-only outlines are separate hypothetical flows, not an
additive or generally composable finite-deformation decomposition. Distinguish
Couette-like **simple shear** (strain and spin) from symmetric **pure shear**.

Mohr's circle uses Pa relative to its mean normal stress, with equal axis scales.
Report the mean separately: hydrostatic pressure shifts the mean, not the radius.
Zero-radius rigid rotation must appear as a point. Preset explanations are shown
only while the actual slider values still match the preset.

Tests should check the drawn geometry as well as reported diagnostics. The
deformation tests compute polygon area from the returned perimeter, compare
rotation and internal grid lines with the analytical rotation matrix, and check
the angle of a finite simple shear. Merely asserting an `area_ratio` field of
one would allow the picture and its label to disagree again. Likewise, a tiny
stress is not zero: test the Mohr trace values and units, not only that a figure
builds. `Omega_yx = (dv/dx - du/dy)/2` under the code's gradient convention; match
the diagram's indices to that convention.

`RELIEF_DEMO_DEFAULTS` is shared by the calculator and its worked example.
Recompute the hot and high-back-pressure cases from those defaults. At fixed
required rate, upstream pressure, gas and coefficient, choked area scales as the
square root of temperature, while bore scales as its fourth root. The lesson's
fixed-area flow model does not predict real valve lift or certify a device.

The corrected default example gives 49.57 mm bore at 333.15 K and 61.92 mm at
811 K (approximately 1,930 and 3,011 mm²). These are dated sanity checks, not
constants to put back into the lesson. The canal recap had a related comparison
error: at fixed section, depth and Manning roughness, quadrupling slope doubles
capacity. The calculator instead fixes discharge and solves for normal depth.
Always identify the dependent variable and the held-fixed inputs before claiming
a percentage or power law.

The sphere figures distinguish local surface traction from the settling free
body, and mark separation/wake boundaries as schematic. The nozzle figure shows
the upstream acoustic branch at lab-frame speed `u-a`, which becomes zero at a
sonic throat. Use `uv run --with playwright python tests/browser_education.py`
with the app running to check the stress presets, hot relief bore, native SVG
rendering and narrow-screen scrolling. Its screenshots go to the system temp
directory for visual inspection.
Teaching SVGs keep an 880 px minimum image width inside their local scroll area;
shrinking an 880 px drawing to 600 px made its 12 px labels roughly 8 px on phones.

## Reproducing this session's verification

Baseline: **2026-09-05, commit `7f0afdc`**, 276 pytest cases passed, ruff passed,
and both live Edge scripts passed. Desktop and mobile screenshots were inspected.
This establishes the tested scenarios, not a comprehensive validation of every
model, browser or input combination. The educational review began with source
inspection and direct calculations; browser inspection followed implementation.

Use normal `uv run` commands first. In this Windows session uv intermittently
failed to initialize its default cache with **WinError 183**, even though earlier
commands had worked. These alternatives succeeded without deleting the cache or
changing app dependencies:

```powershell
# Existing synchronized environment: run one server in a separate terminal.
uv run --no-cache --no-sync python -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8501

# Tests and temporary verification dependencies.
uv run --no-cache --no-sync pytest -q
uv run --cache-dir "$env:TEMP\uv-education-cache" --with ruff ruff check .
uv run --cache-dir "$env:TEMP\uv-education-cache" --with playwright python tests/browser_smoke.py
uv run --cache-dir "$env:TEMP\uv-education-cache" --with playwright python tests/browser_education.py
uv run --no-cache --no-sync git diff --check
```

`--no-sync` assumes the project environment is already installed; it is not an
installation recipe. A pytest cache-write warning also occurred once while all
tests passed. Distinguish cache diagnostics from assertion failures rather than
changing application code to address them. For ad hoc Python output containing
Unicode on Windows, use `python -X utf8`; a PowerShell single-quoted here-string
piped to Python avoids nested-quote problems. Prefer `apply_patch` for source
changes containing LaTeX.

`browser_smoke.py` saves the ignored `network-verification.png` in the repository.
`browser_education.py` saves images under
`%TEMP%\fluid-education-verification`. The scripts locate figures using the same
cleaned-SVG hash as `render_svg`, so text or geometry edits do not require
hard-coded selector hashes. Temporary screenshots and process IDs are evidence,
not app inputs or durable launch instructions. Stop diagnostic servers afterward.

For an authorized commit/push, inspect the diff and working tree, check the fetched
remote for divergence, commit the reviewed scope, and verify the remote branch's
hash matches local HEAD after pushing. The session's push was to `origin/master`;
that is history, not an instruction or standing authorization for future pushes.

