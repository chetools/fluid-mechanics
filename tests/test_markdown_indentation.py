"""Guard against the indented-code-block trap that silently kills KaTeX.

The failure looks like broken LaTeX, but it is a markdown bug. In CommonMark a
line indented by four or more spaces *after a blank line* opens an indented code
block. A triple-quoted Python literal carries the source indentation of the
function it sits in, so a block like::

    st.markdown(
        \"\"\"
        **Work it by hand.**

        1. **Geometry.** $A = y(b+zy)$
        \"\"\"
    )

reaches Streamlit with eight leading spaces on the list line. Markdown renders
the list, the bold and the ``$...$`` literally in monospace, and KaTeX never
runs on any of it.

A single-paragraph literal escapes this, because its later lines are lazy
continuations of the first paragraph and their indentation is ignored. That is
why the bug hid for a long time and then surfaced only in blocks that contain a
blank line -- lists and multi-paragraph prose.

`src.ui.pedagogy` dedents everything it is given. These tests pin that, and scan
the UI source for direct ``st.markdown``/``st.caption`` calls that bypass it.
"""

import ast
import re
from pathlib import Path

import pytest

from src.ui.pedagogy import dedent_markdown, iter_prose_and_math

ROOT = Path(__file__).resolve().parents[1]
UI_DIR = ROOT / "src" / "ui"

# Calls that hand a string straight to Streamlit's markdown renderer.
RAW_MARKDOWN_CALLS = {"markdown", "caption", "write"}

# A line that markdown would treat as meaningful if it were not swallowed by an
# indented code block: list bullets, ordered items, headings, math, tables.
MEANINGFUL = re.compile(r"^(?:[*+-]\s|\d+[.)]\s|#{1,6}\s|\$|>|\|)")


def accidental_code_blocks(md: str) -> list[str]:
    """Lines that CommonMark would swallow into an indented code block."""
    offenders: list[str] = []
    previous_blank = True  # start of the string behaves like a blank line
    in_fence = False
    for line in md.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            previous_blank = False
            continue
        if in_fence:
            continue
        if not stripped:
            previous_blank = True
            continue
        indent = len(line) - len(line.lstrip(" "))
        if previous_blank and indent >= 4 and MEANINGFUL.match(stripped):
            offenders.append(line[:90])
        previous_blank = False
    return offenders


def test_the_helper_dedents_so_lists_survive():
    md = """
        **Work it by hand.**

        1. **Geometry.** $A = y(b+zy)$,
           $P_w = b + 2y$.
        2. **Manning.** $V = 1.17$ m/s.
        """
    assert accidental_code_blocks(md), "the raw literal should be a code block"
    (kind, prose), = iter_prose_and_math(md)
    assert kind == "prose"
    assert accidental_code_blocks(prose) == [], (
        "iter_prose_and_math must dedent, or markdown and KaTeX both die"
    )
    # The list continuation must stay indented *relative* to the item, or it
    # falls out of the list.
    assert "\n   $P_w" in prose


def test_dedent_preserves_relative_indentation():
    dedented = dedent_markdown("\n        - one\n          continued\n            deeper\n")
    assert dedented == "\n- one\n  continued\n    deeper\n"


def test_dedent_handles_tabs():
    assert accidental_code_blocks(dedent_markdown("\n\t\t- item\n\n\t\t- next\n")) == []


def test_prose_after_display_math_is_also_dedented():
    md = """
        Intro paragraph.

        $$a = b$$

        1. **After the math.** $x = 1$
        """
    chunks = list(iter_prose_and_math(md))
    for kind, text in chunks:
        if kind == "prose":
            assert accidental_code_blocks(text) == [], text[:120]


def _string_literals_passed_to_raw_markdown(path: Path):
    """Yield (lineno, literal) for st.markdown/caption/write string arguments."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr in RAW_MARKDOWN_CALLS):
            continue
        if not (isinstance(func.value, ast.Name) and func.value.id == "st"):
            continue
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                yield node.lineno, arg.value


@pytest.mark.parametrize("path", sorted(UI_DIR.glob("*.py")), ids=lambda p: p.name)
def test_no_raw_markdown_call_creates_an_indented_code_block(path):
    problems = []
    for lineno, literal in _string_literals_passed_to_raw_markdown(path):
        for offender in accidental_code_blocks(literal):
            problems.append(f"{path.name}:{lineno}: {offender!r}")
    assert not problems, (
        "These strings reach st.markdown with source indentation intact, so "
        "markdown renders them as a code block and KaTeX never runs:\n"
        + "\n".join(problems)
        + "\n\nFix by dedenting the literal, or route it through "
          "src.ui.pedagogy.render_prose_and_latex, which dedents."
    )
