"""Small Streamlit helpers for learning objectives, predict/observe, and checklists.

KaTeX is not evaluated inside raw HTML, `st.info`/`st.success`/`st.warning`/
`st.error`, or a multi-line `$$...$$` span in `st.markdown`. Streamlit's
markdown parser ends a display-math span at the first newline, so the first
line can vanish and the rest dumps as red raw TeX. Route display math through
`st.latex` (flatten to one line). Inline `$...$` on a single markdown line is
fine.
"""

from __future__ import annotations

import re
from typing import Iterator, List, Optional, Sequence, Tuple

import streamlit as st

DISPLAY_MATH_RE = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)


def render_plot(figure, key: str) -> None:
    """Keep multi-panel plots readable with a scrollable frame on small screens."""
    with st.container(key=f"plot-{key}"):
        st.plotly_chart(figure, width="stretch")
    st.caption("Hover for values. On small screens, scroll the plot horizontally or use its fullscreen control.")


def flatten_display_latex(tex: str) -> str:
    """Collapse whitespace so the same source cannot split across markdown lines."""
    return " ".join(tex.strip().split())


def iter_prose_and_math(md: str) -> Iterator[Tuple[str, str]]:
    """Yield ``("prose", text)`` / ``("math", flattened_latex)`` chunks."""
    pos = 0
    for match in DISPLAY_MATH_RE.finditer(md):
        prose = md[pos : match.start()].strip()
        if prose:
            yield "prose", prose
        yield "math", flatten_display_latex(match.group(1))
        pos = match.end()
    rest = md[pos:].strip()
    if rest:
        yield "prose", rest


def render_latex(tex: str) -> None:
    """Display math via Streamlit KaTeX. Always one physical line."""
    st.latex(flatten_display_latex(tex))


def render_prose_and_latex(md: str) -> None:
    """Render markdown prose, routing ``$$...$$`` through ``st.latex``.

    Never put display math in ``st.markdown``: a newline inside ``$$`` is the
    class of bug that prints red TeX and can drop the first term (e.g. ``p/ρ``).
    """
    for kind, text in iter_prose_and_math(md):
        if kind == "math":
            st.latex(text)
        else:
            st.markdown(text)


def render_symbols(rows: Sequence[Tuple[str, str]]) -> None:
    """Define every symbol at the point of first use.

    Each row is ``(latex_without_dollars, plain-English definition)``.
    """
    with st.container(border=True):
        st.markdown("**Symbols**")
        for sym, meaning in rows:
            st.markdown(f"- ${sym}$ — {meaning}")


def render_callout(body: str, title: str | None = None) -> None:
    """Bordered note that still runs KaTeX (``st.info`` does not for ``$$``)."""
    with st.container(border=True):
        if title:
            st.markdown(f"**{title}**")
        render_prose_and_latex(body)


def render_objectives(items: Sequence[str]) -> None:
    """Render a short 'in this panel you will' list."""
    with st.container(border=True):
        st.markdown("**In this panel you will**")
        for i, item in enumerate(items, 1):
            st.markdown(f"{i}. {item}")


def render_what_to_notice(text: str) -> None:
    """Caption that tells the student what the live figure is supposed to show."""
    st.markdown(f":green[**What you should see:**] {text}")


def render_checklist(title: str, rows: Sequence[Tuple[str, bool, str]]) -> None:
    """Assumption checklist. Each row is (label, currently_true, note)."""
    st.markdown(f"**{title}**")
    for label, ok, note in rows:
        mark = "holds" if ok else "violated / not in this lab"
        color = "green" if ok else "orange"
        st.markdown(f"- :{color}[**{mark}**] — {label}. {note}")


def render_predict(
    key: str,
    question: str,
    options: Sequence[str],
    correct: str,
    explanation: str,
) -> Optional[str]:
    """Force a prediction before the lab numbers are interpreted.

    Returns the selected option, or None if the student has not chosen yet.
    """
    st.markdown(f"**Predict first:** {question}")
    pick = st.radio(
        "Your prediction",
        options=list(options),
        key=key,
        index=None,
        horizontal=True,
        label_visibility="collapsed",
    )
    if pick is None:
        st.caption("Choose a prediction, then operate the controls.")
        return None
    if pick == correct:
        st.markdown(f":green[**Yes.**] {explanation}")
    else:
        st.markdown(f":orange[**Not quite.**] {explanation}")
    return pick


def render_self_check(
    key: str,
    question: str,
    options: Sequence[str],
    correct: str,
    explanation: str,
) -> None:
    """One multiple-choice check with immediate feedback."""
    with st.container(border=True):
        st.markdown(f"**Self-check.** {question}")
        pick = st.radio(
            "Answer",
            options=list(options),
            key=key,
            index=None,
            label_visibility="collapsed",
        )
        if pick is None:
            return
        if pick == correct:
            st.markdown(f":green[**Yes.**] {explanation}")
        else:
            st.markdown(f":orange[**Revisit the derivation.**] {explanation}")


def render_concept_map() -> None:
    """Tab order is the pedagogical path."""
    steps: List[Tuple[str, str]] = [
        ("1. ChemE energy", "Plant Δp/pumps; Bernoulli from the first law; friction as heat"),
        ("2. Pipe & pumping", "Darcy, Moody, NPSH, entrance length"),
        ("3. Dimensional analysis", "Experiments, SVD rotation onto Re/Eu, IT-π information"),
        ("4. Laminar f & straws", "Force balance → 64/Re; packing capillaries vs turbulence cost"),
        ("5. Euler", "Differential momentum; d'Alembert"),
        ("6. Stress & NS", "Tensors and constitutive laws"),
        ("7. Exact solutions & BL", "Couette, Hagen, Stokes, Blasius, separation"),
        ("8. External flow", "Stokes drag, settling and drag crisis"),
        ("9. Turbomachinery", "Euler work, compression and expansion"),
        ("10. Compressible", "Nozzles, choking, shocks and heated ducts"),
        ("11. CFD", "Incompressible projection and verification"),
        ("12. Reference", "Nomenclature and validity matrix"),
    ]
    st.markdown("**Path (easier plant story → harder mathematics)**")
    for title, blurb in steps:
        st.caption(f"{title} — {blurb}")
