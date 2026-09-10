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
    diagram_newtonian_origin, diagram_actuator_disc,
)


def diagram_locator(page, generator):
    fingerprint = hashlib.sha256(clean_svg(generator()).encode()).hexdigest()[:10]
    return page.locator(f'.st-key-fig-{fingerprint}')


def verify_text_layout(browser, generator, output):
    """Measure rendered SVG text; XML checks cannot catch collisions or clipping."""
    page = browser.new_page(viewport={'width': 920, 'height': 650})
    try:
        page.set_content('<body style="margin:20px;background:#0f172a">'
                         '<div style="max-width:880px">' + clean_svg(generator()) + '</div></body>')
        problems = page.locator('svg').evaluate('''svg => {
            const bounds = svg.viewBox.baseVal;
            const texts = [...svg.querySelectorAll('text')].map(el => {
                const b = el.getBBox();
                return {text: el.textContent, x: b.x, y: b.y, w: b.width, h: b.height};
            });
            const issues = [];
            for (const t of texts) {
                if (t.x < 0 || t.y < 0 || t.x+t.w > bounds.width || t.y+t.h > bounds.height)
                    issues.push('Clipped: ' + t.text);
            }
            for (let i=0; i<texts.length; i++) for (let j=i+1; j<texts.length; j++) {
                const a=texts[i], b=texts[j];
                if (Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x)>1 &&
                    Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y)>1)
                    issues.push('Overlap: ' + a.text + ' / ' + b.text);
            }
            return issues;
        }''')
        page.locator('svg').screenshot(path=str(output / f'{generator.__name__}-standalone.png'))
        assert not problems, problems
    finally:
        page.close()


def capture_responsive_figure(page, generator, output):
    figure = diagram_locator(page, generator)
    loaded = figure.locator('img')
    expect(loaded).to_be_visible()
    expect(loaded).to_have_js_property('complete', True)
    assert loaded.evaluate('(img) => img.naturalWidth > 0'), 'SVG failed to decode in the native image renderer'
    figure.screenshot(path=str(output / f'{generator.__name__}-desktop.png'))
    page.set_viewport_size({'width': 390, 'height': 844})
    image = figure.get_by_test_id('stImage')
    image.scroll_into_view_if_needed()
    assert image.evaluate('(el) => el.scrollWidth > el.clientWidth')
    page.screenshot(path=str(output / f'{generator.__name__}-mobile-left.png'))
    image.evaluate('(el) => { el.scrollLeft = el.scrollWidth; }')
    assert image.evaluate('(el) => el.scrollLeft > 0')
    page.screenshot(path=str(output / f'{generator.__name__}-mobile-right.png'))
    page.set_viewport_size({'width': 1400, 'height': 1000})


if __name__ == '__main__':
    output = Path(tempfile.gettempdir()) / 'fluid-education-verification'
    output.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        try:
            for generator in (diagram_newtonian_origin, diagram_actuator_disc):
                verify_text_layout(browser, generator, output)
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

            select_chapter(page, '7 · Non-Newtonian')
            capture_responsive_figure(page, diagram_newtonian_origin, output)
            page.get_by_test_id('stExpander').filter(has_text='from momentum crossing a plane').locator('summary').click()
            kinetic = page.get_by_text('Step 3 — Count the crossings — and notice the flow does not control them', exact=True)
            kinetic.evaluate("el => el.scrollIntoView({block: 'center'})")
            page.screenshot(path=str(output / 'kinetic-derivation.png'))
            page.get_by_text('🔍 Derivation · the plug radius, and why every fluid shares the same τ(r)', exact=True).click()
            page.get_by_text('Step 8 — Use the actual wall stress when the fluid has a yield stress', exact=True).scroll_into_view_if_needed()
            plug_step = page.get_by_text('Step 5 — Match the moving rigid plug to the yielded annulus', exact=True)
            expect(plug_step).to_be_visible()
            plug_step.scroll_into_view_if_needed()
            page.screenshot(path=str(output / 'plug-derivation.png'))
            expect(page.locator('.katex-error')).to_have_count(0)

            select_chapter(page, '3 · Scaling')
            page.get_by_text('🔍 Derivation · Four null directions even when all three returned singular values are positive', exact=True).click()
            page.get_by_text('Step 2 — Follow one of those input directions through the map', exact=True).scroll_into_view_if_needed()
            matrix_step = page.get_by_text('Step 1 — Keep the full rectangular matrix in view', exact=True)
            matrix_step.scroll_into_view_if_needed()
            page.screenshot(path=str(output / 'rectangular-svd.png'))
            expect(page.get_by_text('Returned singular values:', exact=False)).to_contain_text('last 4')
            expect(page.locator('.katex-error')).to_have_count(0)

            select_chapter(page, '10 · Momentum')
            capture_responsive_figure(page, diagram_actuator_disc, output)
            page.get_by_text('🔍 Derivation · the Betz limit for an ideal unshrouded turbine', exact=True).click()
            page.get_by_text('Step 7 — Check the far-wake endpoint with continuity', exact=True).scroll_into_view_if_needed()
            bernoulli = page.get_by_text('Step 3 — Bernoulli, applied twice and never across the disc', exact=True)
            bernoulli.evaluate("el => el.scrollIntoView({block: 'center'})")
            page.screenshot(path=str(output / 'disc-bernoulli.png'))
            induction = page.locator('.st-key-mom_disk_a').get_by_role('slider')
            induction.focus()
            induction.press('End')
            induction.press('Tab')
            expect(page.get_by_text('Singular endpoint:', exact=False)).to_contain_text('0.500', timeout=60000)
            wait_for_chapter(page, 10)

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
            wait_for_chapter(page, 12)
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
            print(f'PASS: stress presets, plug/SVD/disc derivations, singular endpoint, relief bore, SVG text bounds and mobile scrolling. Screenshots: {output}')
        finally:
            browser.close()
