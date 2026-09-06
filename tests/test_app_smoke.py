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


def test_the_course_has_one_structure_and_one_set_of_names():
    """The banner used to number the course 01-06 while the navigation below it
    numbered the same twelve chapters 1-12, so "04 · External flow" in the
    banner was chapter 8 in the radio. Everything now reads from PARTS /
    NAV_LABELS / LESSONS, and this pins that they agree.
    """
    from src.ui import learning_path as lp

    assert len(lp.LESSONS) == len(lp.NAV_LABELS) == 12

    # Every chapter belongs to exactly one part, and the parts tile 1..12.
    covered = [n for _, _, (first, last) in lp.PARTS for n in range(first, last + 1)]
    assert covered == list(range(1, 13)), covered
    for number in range(1, 13):
        lp.part_for(number)  # raises if a chapter is orphaned

    # Part names must be distinct: the old data used "SOLUTIONS & VERIFICATION"
    # for two different parts and gave part 4 two different names.
    names = [name for _, name, _ in lp.PARTS]
    assert len(set(names)) == len(names), names

    # The navigation labels are what app.py renders and the browser tests click.
    assert lp.chapter_labels() == EXPECTED_TABS

    # The banner route names real chapter spans, not a second numbering.
    route = lp.part_route()
    assert len(route) == len(lp.PARTS)
    assert route[3] == "Part 4 · Viscous solutions & drag · ch 7–8"


def test_chapter_header_eyebrow_agrees_with_the_navigation():
    from src.ui import learning_path as lp

    for number in range(1, 13):
        part_number, part_name, (first, last) = lp.part_for(number)
        assert first <= number <= last
        assert lp.chapter_label(number).startswith(f"{number} · ")
        assert part_name  # non-empty, and used verbatim in the chapter eyebrow


@pytest.mark.parametrize("chapter", EXPECTED_TABS)
def test_every_chapter_renders_without_exception(chapter):
    """One chapter at a time, because only the selected one executes.

    The two spot-checks above left ten panels unexercised, which is exactly
    where a bad expander, a missing import or a malformed f-string hides.
    """
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    at.radio(key="chapter_nav").set_value(chapter).run()
    assert not at.exception, f"{chapter}: {at.exception}"


def test_changing_display_units_keeps_the_reader_on_their_chapter():
    """A sidebar st.rerun() used to abort the script before the chapter radio
    was created, so Streamlit garbage-collected `chapter_nav` and the reader
    was thrown back to chapter 1 just for switching units.
    """
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    at.radio(key="chapter_nav").set_value("9 · Turbomachinery").run()
    assert at.radio(key="chapter_nav").value == "9 · Turbomachinery"

    at.selectbox(key="unit_toggle_select").set_value("Nondimensional [-]").run()
    assert not at.exception, at.exception
    assert at.radio(key="chapter_nav").value == "9 · Turbomachinery", (
        "switching display units moved the reader off their chapter"
    )
    labels = [m.label for m in at.metric]
    assert any("MAC shaft power" in label for label in labels), (
        "chapter 9 stopped rendering after the unit change"
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


def test_calculator_and_self_check_survive_chapter_round_trip():
    at = AppTest.from_file(APP, default_timeout=300).run()
    at.radio(key='chapter_nav').set_value('9 · Turbomachinery').run()
    at.number_input(key='asu_mair').set_value(60.0).run()
    check = next(r for r in at.radio if r.key != 'chapter_nav')
    check_key, answer = check.key, check.options[-1]
    check.set_value(answer).run()
    power = next(m.value for m in at.metric if m.label == 'MAC shaft power')
    at.radio(key='chapter_nav').set_value('1 · Energy').run()
    at.radio(key='chapter_nav').set_value('9 · Turbomachinery').run()
    assert not at.exception
    assert at.number_input(key='asu_mair').value == 60
    assert at.radio(key=check_key).value == answer
    assert next(m.value for m in at.metric if m.label == 'MAC shaft power') == power
    # A new edit must supersede the saved value.
    at.number_input(key='asu_mair').set_value(45.0).run()
    assert at.number_input(key='asu_mair').value == 45


def test_previously_unkeyed_input_survives_chapter_round_trip():
    at = AppTest.from_file(APP, default_timeout=300).run()
    at.radio(key='chapter_nav').set_value('10 · Compressible').run()
    temperature = next(w for w in at.number_input if w.label == 'Reservoir stagnation temperature [K]')
    key = temperature.key
    temperature.set_value(450.0).run()
    at.radio(key='chapter_nav').set_value('1 · Energy').run()
    at.radio(key='chapter_nav').set_value('10 · Compressible').run()
    assert not at.exception
    assert at.number_input(key=key).value == 450


def test_lesson_values_are_isolated_between_sessions():
    first = AppTest.from_file(APP, default_timeout=300).run()
    first.radio(key='chapter_nav').set_value('9 · Turbomachinery').run()
    first.number_input(key='asu_mair').set_value(60.0).run()
    second = AppTest.from_file(APP, default_timeout=300).run()
    second.radio(key='chapter_nav').set_value('9 · Turbomachinery').run()
    assert second.number_input(key='asu_mair').value == 30


def test_network_edits_and_solution_survive_navigation():
    at = AppTest.from_file(APP, default_timeout=300).run()
    at.radio(key='chapter_nav').set_value('2 · Pipes').run()
    # AppTest has no editor API; supply the same delta payload as the browser.
    at.session_state['network_nodes'] = {
        'edited_rows': {1: {'elevation_m': 17.0}}, 'added_rows': [], 'deleted_rows': [],
    }
    at.run()
    at.button(key='solve_network_button').click().run()
    signature = at.session_state['solved_network'][0]
    at.radio(key='chapter_nav').set_value('1 · Energy').run()
    at.radio(key='chapter_nav').set_value('2 · Pipes').run()
    assert not at.exception
    table = at.session_state['_lesson_tables']['network_nodes']['latest']
    assert table.loc[1, 'elevation_m'] == 17
    assert at.session_state['solved_network'][0] == signature
    assert any('Solved in' in message.value for message in at.success)
    # Editing after re-entry invalidates the old result until an explicit solve.
    at.session_state['network_nodes'] = {
        'edited_rows': {1: {'elevation_m': 18.0}}, 'added_rows': [], 'deleted_rows': [],
    }
    at.run()
    assert not any('Solved in' in message.value for message in at.success)


def test_network_row_addition_and_deletion_are_not_replayed():
    at = AppTest.from_file(APP, default_timeout=300).run()
    at.radio(key='chapter_nav').set_value('2 · Pipes').run()
    original = at.session_state['_lesson_tables']['network_pipes']['latest']
    replacement = dict(original.iloc[2], pipe='Replacement')
    at.session_state['network_pipes'] = {
        'edited_rows': {}, 'added_rows': [replacement], 'deleted_rows': [2],
    }
    at.run()
    expected = at.session_state['_lesson_tables']['network_pipes']['latest'].to_dict('records')
    for _ in range(2):
        at.run()
        at.radio(key='chapter_nav').set_value('1 · Energy').run()
        at.radio(key='chapter_nav').set_value('2 · Pipes').run()
        assert not at.exception
        assert at.session_state['_lesson_tables']['network_pipes']['latest'].to_dict('records') == expected
