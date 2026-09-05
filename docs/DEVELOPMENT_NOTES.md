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
| `src/physics/impeller.py` | Blade camberline from the angle definition, 3D blade surfaces, slip, velocity triangles, isometric projection |
| `src/svg_impeller.py` | Impeller diagrams projected from that computed geometry (needs NumPy, so kept out of `svg_diagrams.py`) |
| `src/physics/gas_dynamics.py` | Perfect-gas nozzle, normal shock, compressor/turbine and sphere-drag calculations |
| `src/ui/pipe_network_lab.py` | Chapter 2 schedule calculator, editable node/pipe tables and network results |
| `src/ui/tab_external_flow.py` | Chapter 8: Stokes flow, settling and drag crisis |
| `src/ui/tab_turbomachinery.py` | Chapter 9: angular momentum, velocity triangles, work and thermal effects |
| `src/ui/tab_compressible.py` | Chapter 10: compressible derivations, nozzle/shock labs, Fanno and Rayleigh flow |
| `src/ui/tab_cfd.py` | Chapter 11: incompressible projection solver and benchmark interpretation |

Current order: 1 Energy, 2 Pipes, 3 Scaling, 4 Turbulence, 5 Euler, 6 Stress & NS, 7 Exact flows, 8 External flow, 9 Turbomachinery, 10 Compressible, 11 CFD, 12 Reference. Keep compressible flow before CFD, while explicitly explaining that the existing CFD solver is incompressible.

`app.py` owns chapter headers/recaps. Avoid duplicate main headings inside individual renderers. Adding a module also requires adding it to `_MODULE_RELOAD_ORDER`: the fingerprint only includes `app.py` and modules named in that list. Keep dependency reloads before their consumers. The current reload guard catches import/reload exceptions, so it is not a substitute for a compile/import check or AppTest.

Shared sidebar density/viscosity feed incompressible, pipe and external-flow labs. The gas-machine/nozzle labs have separate thermodynamic inputs. New engineering calculators show explicitly labeled SI quantities independently of the older nondimensional display toggle; do not claim that the toggle changes every calculator.

## Rendering failures to avoid

### Equations

Streamlit can mishandle multiline `$$...$$` in `st.markdown`, displaying raw TeX or losing a line. Alerts and raw HTML are also unsuitable paths for display equations.

- Use `render_prose_and_latex` for prose containing display blocks, and `render_latex`/`st.latex` for individual equations. Prefer raw Python strings for TeX.
- The helper flattens whitespace before rendering each equation.
- `tests/test_katex_safety.py` checks source patterns; browser checks additionally look for `.katex-error`.
- A syntactically valid equation can still be too wide: verify small-screen overflow and readability visually.

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

### Existing CFD regressions

Retain tests for the first-step moving-lid boundary condition, preservation of interior vertical momentum, viscous timestep limit, invalid parameters and nondimensional Ghia error scaling. The Ghia overlay is only meaningful for the matching Re = 100 case. A short visually plausible vortex is not a converged benchmark: report nondimensional elapsed time, divergence and benchmark error together. Compressible shocks/choking are outside this solver's scope.

## Verification workflow and baseline

At completion, **170 pytest cases passed**. The live headless-Edge check also passed: network solve, CSV download, new chapter navigation, no KaTeX errors and no browser page errors. A separate AppTest exercise changed a junction elevation and changed a pipe to measured ID with relative roughness; the resulting geometry/pressure changed correctly. Invalid roughness, compressor/turbine switching and no-forward-flow nozzle behavior were also exercised.

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

- Switching chapters is now a rerun, not a client-side tab switch. Widget state survives
  because every widget in the course already carries an explicit `key`.
- Anything that assumed all chapters are in the DOM at once — old browser tests, in-page
  anchors between chapters — no longer holds.
- `tests/test_app_smoke.py` pins the behaviour in both directions: the twelve options exist,
  chapter 9's content is *absent* while chapter 1 is selected, and selecting chapter 9
  renders it. Two further tests change a widget and assert the numbers actually recompute
  (air feed doubles MAC power; a rougher canal runs deeper).

Do not restore `st.tabs` without re-measuring the full-page render in a real browser. A
passing AppTest does not establish that the page finishes drawing — that was the entire
lesson here, and it matches the earlier live-browser section above.
