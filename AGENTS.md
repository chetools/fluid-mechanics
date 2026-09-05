# Working in this repository

- Use `uv run` to execute commands. Use `uv pip install`, never `pip install`, when installation is necessary.
- Read [docs/DEVELOPMENT_NOTES.md](docs/DEVELOPMENT_NOTES.md) before changing course structure, physics, rendering, or Streamlit lifecycle behavior.
- Keep mathematical calculations in `src/physics/` and Streamlit presentation in `src/ui/`. Make units, sign conventions, assumptions and model limits visible beside calculators.
- Render display equations with the helpers in `src/ui/pedagogy.py`; do not put multiline display math in `st.markdown`, alerts, or raw HTML.
- Prose blocks containing a blank line must go through `render_prose_and_latex`, which dedents them. A triple-quoted literal passed straight to `st.markdown` keeps its source indentation, and four or more leading spaces after a blank line makes markdown treat it as a code block, so the markup and the maths both render literally.
- Mark angles only where they are true: a plan or true-shape view, never an axonometric projection, which foreshortens each direction differently. Draw both bounding rays from the vertex.
- Unicode has no subscript for `w` or for capitals; use `svg_diagrams._sub()` rather than guessing a numeric entity, which lands in the currency block.
- Compute worked-example numbers from the app's own defaults, and prefer having the app recompute a claimed constant over asserting it.
- Use the existing native-image SVG renderer and `render_plot` wrapper. Check actual browser rendering as well as Python tests for visual or interaction changes.
- When adding a chapter/module, update the lesson metadata, app tabs/imports, source fingerprint/reload list, cross-references and README together.
- Preserve `fileWatcherType = "none"` and `fastReruns = false` unless a real-browser regression demonstrates that an alternative works. A fully drawn page and a passing AppTest do not establish that live widgets work.
- Run relevant tests after changes. For lifecycle/network UI changes, also run `tests/browser_smoke.py` against the running app; details and limitations are in the development notes.

These instructions describe the current project workflow, not permission to publish, deploy or discard existing changes.
