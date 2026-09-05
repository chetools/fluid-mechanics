# Working in this repository

- Use `uv run` to execute commands. Use `uv pip install`, never `pip install`, when installation is necessary.
- Read [docs/DEVELOPMENT_NOTES.md](docs/DEVELOPMENT_NOTES.md) before changing course structure, physics, rendering, or Streamlit lifecycle behavior.
- Keep mathematical calculations in `src/physics/` and Streamlit presentation in `src/ui/`. Make units, sign conventions, assumptions and model limits visible beside calculators.
- Render display equations with the helpers in `src/ui/pedagogy.py`; do not put multiline display math in `st.markdown`, alerts, or raw HTML.
- Use the existing native-image SVG renderer and `render_plot` wrapper. Check actual browser rendering as well as Python tests for visual or interaction changes.
- When adding a chapter/module, update the lesson metadata, app tabs/imports, source fingerprint/reload list, cross-references and README together.
- Preserve `fileWatcherType = "none"` and `fastReruns = false` unless a real-browser regression demonstrates that an alternative works. A fully drawn page and a passing AppTest do not establish that live widgets work.
- Run relevant tests after changes. For lifecycle/network UI changes, also run `tests/browser_smoke.py` against the running app; details and limitations are in the development notes.

These instructions describe the current project workflow, not permission to publish, deploy or discard existing changes.
