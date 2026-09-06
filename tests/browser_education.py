"""Optional teaching-figure checks; run with the server on port 8501.

uv run --with playwright python tests/browser_education.py
Screenshots go to the system temporary directory, not into the source tree.
"""
import hashlib
from pathlib import Path
import sys
import tempfile

from playwright.sync_api import expect, sync_playwright
from browser_smoke import select_chapter, wait_for_chapter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.svg_diagrams import (
    clean_svg, diagram_nozzle_information, diagram_relief_valve,
    diagram_sphere_forces, diagram_sphere_separation,
)


def diagram_locator(page, generator):
    fingerprint = hashlib.sha256(clean_svg(generator()).encode()).hexdigest()[:10]
    return page.locator(f'.st-key-fig-{fingerprint}')


if __name__ == '__main__':
    output = Path(tempfile.gettempdir()) / 'fluid-education-verification'
    output.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        try:
            page = browser.new_page(viewport={'width': 1400, 'height': 1000})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto('http://127.0.0.1:8501/')
            wait_for_chapter(page, 1)
            page.get_by_test_id('stSidebarHeader').hover()
            page.get_by_test_id('stSidebarCollapseButton').get_by_role('button').click()
            expect(page.get_by_test_id('stSidebar')).not_to_be_in_viewport()
            select_chapter(page, '6 · Stress & NS')
            preset = page.get_by_role('combobox', name='Kinematic preset', exact=True)
            for name, filename, explanation in [
                ('Pure rotation (rigid)', 'rotation', "Mohr's circle collapses to a point"),
                ('Pure shear (symmetric)', 'pure-shear', 'The full and D-only outlines coincide'),
                ('Simple shear (Couette-like)', 'simple-shear', 'The parcel shears into a parallelogram'),
            ]:
                preset.click()
                preset.fill(name)
                page.get_by_role('option', name=name, exact=True).click()
                # The recap remains mounted on a same-chapter rerun. Wait for
                # changed output before checking completion or taking a picture.
                expect(page.get_by_text(explanation, exact=False)).to_be_visible()
                wait_for_chapter(page, 6)
                expect(page.get_by_text('Computed area ratio', exact=False)).to_contain_text('= 1.000000')
                page.locator('.st-key-plot-tab_stress_ns-fig_deform').screenshot(path=str(output / f'{filename}.png'))

            select_chapter(page, '9 · External flow')
            for generator in (diagram_sphere_forces, diagram_sphere_separation):
                diagram_locator(page, generator).screenshot(path=str(output / f'{generator.__name__}.png'))

            select_chapter(page, '12 · Compressible')
            expect(page.get_by_text('Bore increases by only', exact=False)).to_contain_text('61.92 mm')
            temperature = page.get_by_role('spinbutton', name='Relieving temperature T₀ [K]', exact=True)
            temperature.fill('811')
            temperature.press('Enter')
            bore = page.get_by_test_id('stMetric').filter(has=page.get_by_text('Equivalent bore', exact=True))
            expect(bore).to_contain_text('61.9 mm')
            wait_for_chapter(page, 11)
            for generator in (diagram_nozzle_information, diagram_relief_valve):
                diagram_locator(page, generator).screenshot(path=str(output / f'{generator.__name__}.png'))

            page.set_viewport_size({'width': 390, 'height': 844})
            diagram = diagram_locator(page, diagram_nozzle_information).get_by_test_id('stImage')
            diagram.scroll_into_view_if_needed()
            # The wide figure stays legible through intentional local scrolling.
            assert diagram.evaluate('(el) => el.scrollWidth > el.clientWidth')
            diagram.evaluate('(el) => { el.scrollLeft = el.scrollWidth; }')
            assert diagram.evaluate('(el) => el.scrollLeft > 0')
            page.screenshot(path=str(output / 'nozzle-mobile.png'))
            expect(page.locator('.katex-error')).to_have_count(0)
            expect(page.locator('[data-testid="stException"]')).to_have_count(0)
            assert not errors, errors
            print(f'PASS: stress presets, relief bore, native SVGs and narrow-screen scrolling. Screenshots: {output}')
        finally:
            browser.close()
