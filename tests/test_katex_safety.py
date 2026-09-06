"""Forbid Streamlit paths that dump raw TeX or skip KaTeX.

Root cause (screenshots 2026-09-05 075219 / 075245): Streamlit markdown ends a
``$$`` span at the first newline, so the first term can vanish and the rest
prints as red TeX. ``st.info`` / HTML never run KaTeX on display math.
"""

from __future__ import annotations

import ast
from pathlib import Path

from src.ui.pedagogy import flatten_display_latex, iter_prose_and_math

ROOT = Path(__file__).resolve().parents[1]
UI_DIR = ROOT / "src" / "ui"
ALERTS = frozenset({"info", "success", "warning", "error"})


def _attr_name(func: ast.AST) -> tuple[str | None, str | None]:
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        return func.value.id, func.attr
    return None, None


def _string_bits(node: ast.AST) -> str:
    chunks: list[str] = []

    def walk(n: ast.AST) -> None:
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            chunks.append(n.value)
        elif isinstance(n, ast.JoinedStr):
            for value in n.values:
                if isinstance(value, ast.FormattedValue):
                    chunks.append("\x00")
                else:
                    walk(value)
        elif isinstance(n, ast.BinOp):
            walk(n.left)
            walk(n.right)
        elif isinstance(n, ast.Call):
            for arg in n.args:
                walk(arg)
            for kw in n.keywords:
                walk(kw.value)

    walk(node)
    return "".join(chunks)


def find_violations_in_source(src: str, filename: str) -> list[str]:
    """Return human-readable violations in one Python module."""
    tree = ast.parse(src)
    hits: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        owner, attr = _attr_name(node.func)
        if owner != "st" or attr is None:
            continue
        text = _string_bits(node)
        html = False
        for kw in node.keywords:
            if kw.arg == "unsafe_allow_html" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                html = True
        loc = f"{filename}:{node.lineno}"
        if attr == "markdown" and "$$" in text:
            hits.append(f"{loc}: st.markdown contains $$ (route through st.latex / render_prose_and_latex)")
        if attr in ALERTS and ("$" in text or r"\begin" in text):
            hits.append(f"{loc}: st.{attr} contains math; KaTeX does not run in alerts (use render_callout)")
        if html and ("$" in text or r"\begin" in text):
            hits.append(f"{loc}: unsafe_allow_html contains math; KaTeX does not run in raw HTML")
    return hits


def test_flatten_collapses_newlines():
    tex = "\\frac{p}{\\rho}\n+ \\frac{\\alpha u^2}{2}"
    flat = flatten_display_latex(tex)
    assert "\n" not in flat
    assert r"\frac{p}{\rho}" in flat
    assert r"\alpha" in flat


def test_iter_prose_and_math_extracts_first_law_block():
    """The expander dump started at +W_shaft because the first $$ line was split."""
    md = r"""
**Step 1.** For a control volume:
$$\dot{m}\left(h + \frac{u^2}{2} + gz\right)_{\mathrm{in}}
+ \dot{W}_{\mathrm{shaft}} + \dot{Q}
= \dot{m}\left(h + \frac{u^2}{2} + gz\right)_{\mathrm{out}}$$
Enthalpy $h = \hat{u}_{\mathrm{int}} + p/\rho$ already contains flow work.
"""
    chunks = list(iter_prose_and_math(md))
    kinds = [k for k, _ in chunks]
    assert "math" in kinds
    math = next(text for kind, text in chunks if kind == "math")
    assert r"\dot{m}" in math
    assert r"\dot{W}" in math
    assert "\n" not in math
    prose = " ".join(text for kind, text in chunks if kind == "prose")
    assert "Enthalpy" in prose
    assert r"\hat{u}" in prose


def test_scanner_flags_markdown_display_math_and_alert_math():
    bad = '''
st.markdown(r"""
$$a + b$$
""")
st.info("see $x$")
st.markdown("inline $x$ is allowed")
'''
    hits = find_violations_in_source(bad, "fake.py")
    assert any("st.markdown contains $$" in h for h in hits)
    assert any("st.info contains math" in h for h in hits)
    assert not any("inline" in h for h in hits)


def test_scanner_does_not_flag_symbol_table_fstring():
    """`$` wrapping an f-expression is inline math, not a $$ display span."""
    src = 'st.markdown(f"- ${sym}$ — {meaning}")\n'
    assert find_violations_in_source(src, "sym.py") == []


def test_scanner_allows_st_latex_and_helpers():
    ok = '''
render_prose_and_latex(r"""
$$\\alpha = 2$$
""")
st.latex(r"\\frac{p}{\\rho}")
st.markdown("alpha $\\\\alpha$ is the kinetic-energy correction")
'''
    assert find_violations_in_source(ok, "ok.py") == []


def test_alpha_defined_in_energy_tab():
    src = (UI_DIR / "tab_cheme_energy.py").read_text(encoding="utf-8")
    assert "kinetic-energy correction" in src
    assert r"\alpha = \frac{1}{A}" in src


def test_injection_work_is_derived_not_named():
    src = (UI_DIR / "tab_cheme_energy.py").read_text(encoding="utf-8")
    assert "diagram_injection_work" in src
    assert r"W_{\mathrm{on}}=-p\Delta V" in src
    assert r"\Delta V=-1/\rho" in src
    assert "velocity component" in src


def test_churchill_formula_is_displayed():
    src = (UI_DIR / "tab_pipe_flow.py").read_text(encoding="utf-8")
    assert "37530" in src
    assert "2.457" in src
    assert r"A_{\mathrm{Ch}}" in src
    assert "Churchill" in src


def test_ui_modules_have_no_katex_traps():
    files = sorted(UI_DIR.glob("*.py"))
    files.append(ROOT / "app.py")
    assert files
    all_hits: list[str] = []
    for path in files:
        src = path.read_text(encoding="utf-8")
        all_hits.extend(find_violations_in_source(src, str(path.relative_to(ROOT))))
    assert all_hits == [], "KaTeX traps:\n" + "\n".join(all_hits)
