"""Static checker for every LaTeX fragment the UI can hand to KaTeX.

KaTeX fails *silently loud*: an unknown control sequence or an unbalanced brace
renders as red raw TeX in the middle of a lesson, and nothing in Python notices.
The derivations added to these panels contain hundreds of equations, far past
the point where reading them all is a reliable check, so this test does the
reading instead:

* every ``\\command`` must be on the allowlist below, which is a list of macros
  actually supported by KaTeX -- a typo such as ``\\parital`` cannot pass;
* braces, ``\\left``/``\\right`` and ``\\begin``/``\\end`` must balance;
* environments must be ones KaTeX ships.

Adding a genuinely new macro means adding it here **after** confirming it is in
KaTeX's supported-functions list. That is the point: the allowlist is the
review step.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
UI_DIR = ROOT / "src" / "ui"

DISPLAY_MATH = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
INLINE_MATH = re.compile(r"(?<!\$)\$([^$\n]+?)\$(?!\$)")
COMMAND = re.compile(r"\\([A-Za-z]+)")
ENVIRONMENT = re.compile(r"\\(begin|end)\{([a-z*]+)\}")

# KaTeX-supported macros used by this course. Grouped for review, not by syntax.
ALLOWED_COMMANDS = frozenset(
    """
    frac tfrac dfrac sqrt int oint sum prod lim max min sup inf
    left right big Big bigl bigr Bigl Bigr middle
    partial nabla infty propto approx sim simeq equiv neq ne le ge leq geq
    ll gg lesssim gtrsim pm mp times cdot cdots ldots dots vdots ddots
    to mapsto implies impliedby iff in notin not subset subseteq
    rightarrow leftarrow longrightarrow longleftarrow xrightarrow xleftarrow
    Rightarrow Leftarrow Longrightarrow Longleftarrow Longleftrightarrow
    leftrightarrow Leftrightarrow parallel perp angle
    alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota
    kappa lambda mu nu xi pi varpi rho varrho sigma varsigma tau upsilon
    phi varphi chi psi omega
    Gamma Delta Theta Lambda Xi Pi Sigma Upsilon Phi Psi Omega
    mathrm mathbf mathbb mathcal mathit mathsf mathtt boldsymbol bm text textbf
    operatorname
    bar hat tilde vec dot ddot overline underline widehat widetilde
    overbrace underbrace overset underset stackrel
    quad qquad , ; ! : space enspace hspace
    ln log exp sin cos tan sinh cosh tanh arctan arcsin arccos
    det dim ker deg gcd
    boxed begin end cases bmatrix pmatrix matrix vmatrix array aligned
    ell circ prime star ast dagger
    displaystyle textstyle scriptstyle scriptscriptstyle limits nolimits
    color textcolor
    """.split()
)

ALLOWED_ENVIRONMENTS = frozenset(
    {"cases", "bmatrix", "pmatrix", "vmatrix", "matrix", "array", "aligned", "align", "align*"}
)


def math_fragments(source: str):
    """Yield every ``(kind, fragment)`` of math in one module's string literals."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
            continue
        literal = node.value
        for match in DISPLAY_MATH.finditer(literal):
            yield node.lineno, "display", match.group(1)
        # Inline spans, with the display spans removed so they are not rescanned.
        for match in INLINE_MATH.finditer(DISPLAY_MATH.sub(" ", literal)):
            yield node.lineno, "inline", match.group(1)


def unknown_commands(fragment: str) -> list[str]:
    return sorted({c for c in COMMAND.findall(fragment) if c not in ALLOWED_COMMANDS})


def balance_problems(fragment: str) -> list[str]:
    """Report unbalanced braces, ``\\left``/``\\right`` and environments."""
    problems: list[str] = []

    depth = 0
    index = 0
    while index < len(fragment):
        char = fragment[index]
        if char == "\\" and index + 1 < len(fragment):
            index += 2  # an escaped brace is a literal, not a group
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                problems.append("closing brace with no opening brace")
                depth = 0
        index += 1
    if depth:
        problems.append(f"{depth} unclosed brace(s)")

    # \left and \right must pair; \big and friends are unpaired sizers.
    opens = len(re.findall(r"\\left(?![A-Za-z])", fragment))
    closes = len(re.findall(r"\\right(?![A-Za-z])", fragment))
    if opens != closes:
        problems.append(f"\\left x{opens} vs \\right x{closes}")

    stack: list[str] = []
    for kind, env in ENVIRONMENT.findall(fragment):
        if env not in ALLOWED_ENVIRONMENTS:
            problems.append(f"unsupported environment {env!r}")
        if kind == "begin":
            stack.append(env)
        elif not stack or stack.pop() != env:
            problems.append(f"\\end{{{env}}} does not match its \\begin")
    if stack:
        problems.append(f"unclosed environment(s) {stack}")

    return problems


@pytest.mark.parametrize("path", sorted(UI_DIR.glob("*.py")), ids=lambda p: p.name)
def test_every_math_fragment_is_renderable(path: Path):
    failures: list[str] = []
    for lineno, kind, fragment in math_fragments(path.read_text(encoding="utf-8")):
        for command in unknown_commands(fragment):
            failures.append(
                f"{path.name}:{lineno}: unknown macro \\{command} in {kind} math: "
                f"{fragment.strip()[:90]!r}"
            )
        for problem in balance_problems(fragment):
            failures.append(
                f"{path.name}:{lineno}: {problem} in {kind} math: "
                f"{fragment.strip()[:90]!r}"
            )
    assert not failures, (
        "KaTeX would render these as red raw TeX:\n" + "\n".join(failures) +
        "\n\nIf a macro is genuinely supported by KaTeX, add it to "
        "ALLOWED_COMMANDS in this file."
    )


def test_the_checker_catches_a_typo_and_an_unclosed_brace():
    assert unknown_commands(r"\parital u/\parital t") == ["parital"]
    assert unknown_commands(r"\frac{\partial u}{\partial t}") == []
    assert balance_problems(r"\frac{a}{b}") == []
    assert balance_problems(r"\frac{a}{b") == ["1 unclosed brace(s)"]
    assert balance_problems(r"\left( a \right)") == []
    assert "\\left x1 vs \\right x0" in balance_problems(r"\left( a )")
    assert balance_problems(r"\begin{bmatrix} 1 \end{bmatrix}") == []
    assert balance_problems(r"\begin{bmatrix} 1 \end{cases}")
