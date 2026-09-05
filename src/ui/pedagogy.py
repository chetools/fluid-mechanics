"""Small Streamlit helpers for learning objectives, predict/observe, and checklists.

KaTeX is not evaluated inside raw HTML, so these helpers use markdown
containers and `st.latex` rather than styled HTML wrappers.
"""

from typing import List, Optional, Sequence, Tuple

import streamlit as st


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
        st.success(explanation)
    else:
        st.info(f"Not quite. {explanation}")
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
            st.success(explanation)
        else:
            st.warning(f"Revisit the derivation. {explanation}")


def render_concept_map() -> None:
    """Tab order is the pedagogical path."""
    steps: List[Tuple[str, str]] = [
        ("1. Euler", "Continuity, inviscid momentum, Bernoulli"),
        ("2. Dimensional analysis", "Why Re, Eu, Fr exist before they appear on axes"),
        ("3. Stress & NS", "Viscosity, then power-law when Newton fails"),
        ("4. Exact solutions & BL", "Couette, Hagen, Stokes, Blasius, cylinder separation"),
        ("5. Laminar / turbulent", "Pipe regimes, α, wall law — circular pipe only"),
        ("6. Pipe design", "Darcy, mechanical energy, NPSH, entrance length"),
        ("7. CFD", "Projection method after you know what 'steady' means"),
        ("8. Reference", "Nomenclature and validity matrix"),
    ]
    st.markdown("**Path (tab order)**")
    for title, blurb in steps:
        st.caption(f"{title} — {blurb}")
