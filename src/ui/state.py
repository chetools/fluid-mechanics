"""Keep lesson inputs when Streamlit removes widgets from an inactive chapter."""

from copy import deepcopy

import streamlit as st


def persistent_input(widget, *args, key: str, **kwargs):
    """Render a keyed input and retain its value outside widget-owned state.

    Streamlit deletes widget keys when the widget is absent from a run. The
    separate dictionary survives that cleanup. Restore only an absent key so
    a live edit always wins over the last saved value. Buttons are deliberately
    excluded: their one-run events must never be restored.
    """
    saved = st.session_state.setdefault("_lesson_inputs", {})
    if key not in st.session_state and key in saved:
        st.session_state[key] = deepcopy(saved[key])
    value = widget(*args, key=key, **kwargs)
    saved[key] = deepcopy(value)
    return value


def persistent_editor(data, *, key: str, **kwargs):
    """Preserve edited tables without assigning to data_editor's read-only key.

    Keep a fixed base while the editor is mounted: its edits are deltas against
    that base. On returning to the chapter, mount the last complete table as
    the new base, so row insertions/deletions are not applied twice.
    """
    saved = st.session_state.setdefault("_lesson_tables", {})
    if key not in saved:
        saved[key] = {"base": deepcopy(data), "latest": deepcopy(data)}
    table = saved[key]
    if key not in st.session_state:
        table["base"] = deepcopy(table["latest"])
    value = st.data_editor(table["base"], key=key, **kwargs)
    table["latest"] = deepcopy(value)
    return value
