"""End-to-end checks that app.py actually renders.

The module reload guard in app.py swallows every import/reload exception, so a
chapter that fails to import is invisible to the physics unit tests. These
tests execute the whole script the way Streamlit does.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import app as app_module

APP = str(Path(__file__).resolve().parents[1] / "app.py")

EXPECTED_TABS = [
    "1 · Energy", "2 · Pipes", "3 · Scaling", "4 · Turbulence",
    "5 · Euler", "6 · Stress & NS", "7 · Exact flows", "8 · External flow",
    "9 · Turbomachinery", "10 · Compressible", "11 · CFD", "12 · Reference",
]


@pytest.fixture(scope="module")
def rendered():
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    return at


def test_app_renders_without_exception(rendered):
    assert not rendered.exception, rendered.exception


def test_all_twelve_chapters_are_present(rendered):
    """Chapters are a radio group, not st.tabs: only the selected one renders.

    st.tabs executes every panel body on every run, which is what stalled the
    browser once the course grew. See the comment in app.py.
    """
    options = list(rendered.radio(key="chapter_nav").options)
    assert options == EXPECTED_TABS


def test_only_the_selected_chapter_renders(rendered):
    """The whole point of the radio: chapter 9's content is absent on chapter 1."""
    assert rendered.radio(key="chapter_nav").value == EXPECTED_TABS[0]
    labels = [m.label for m in rendered.metric]
    assert not any("MAC shaft power" in label for label in labels)


def test_switching_chapter_renders_that_chapter():
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    at.radio(key="chapter_nav").set_value("9 · Turbomachinery").run()
    assert not at.exception, at.exception
    labels = [m.label for m in at.metric]
    assert any("MAC shaft power" in label for label in labels), (
        "the air-separation worked example did not render on chapter 9"
    )


def test_reload_list_matches_the_source_tree():
    """A module missing from _MODULE_RELOAD_ORDER is never reloaded or fingerprinted."""
    root = Path(app_module.__file__).resolve().parent
    on_disk = {
        ".".join(path.relative_to(root).with_suffix("").parts)
        for path in (root / "src").rglob("*.py")
        if path.name != "__init__.py"
    }
    listed = set(app_module._MODULE_RELOAD_ORDER)
    assert on_disk - listed == set(), (
        f"add these to _MODULE_RELOAD_ORDER in app.py: {sorted(on_disk - listed)}"
    )
    assert listed - on_disk == set(), (
        f"_MODULE_RELOAD_ORDER names modules that do not exist: {sorted(listed - on_disk)}"
    )


def test_source_fingerprint_is_stable_and_complete():
    first = app_module._source_fingerprint()
    assert first == app_module._source_fingerprint()
    assert len(first) == 64


def test_air_separation_power_scales_with_feed():
    """A live widget change must recompute the worked example, not just redraw it."""
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    at.radio(key="chapter_nav").set_value("9 · Turbomachinery").run()

    def mac_power(app):
        for metric in app.metric:
            if metric.label == "MAC shaft power":
                return float(metric.value.split()[0])
        raise AssertionError("MAC shaft power metric not rendered")

    base = mac_power(at)
    at.number_input(key="asu_mair").set_value(60.0).run()
    assert not at.exception, at.exception
    # Specific work is unchanged by mass flow, so power must scale exactly with it.
    assert mac_power(at) == pytest.approx(2.0 * base, rel=1e-3)


def test_canal_calculator_reacts_to_roughness():
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    at.radio(key="chapter_nav").set_value("2 · Pipes").run()

    def normal_depth(app):
        for metric in app.metric:
            if metric.label == "Normal depth y_n":
                return float(metric.value.split()[0])
        raise AssertionError("Normal depth metric not rendered")

    smooth = normal_depth(at)
    at.selectbox(key="canal_mat").set_value("Gravel bed, cobbles").run()
    assert not at.exception, at.exception
    # A rougher channel needs more depth to pass the same discharge.
    assert normal_depth(at) > smooth
