"""Optional real-browser regression: uv run --with playwright python tests/browser_smoke.py.

Start the app on port 8501 first. Requires installed Microsoft Edge.
"""
import sys

from playwright.sync_api import expect, sync_playwright

sys.stdout.reconfigure(encoding='utf-8')


def wait_for_chapter(page, number):
    # The recap is emitted after the selected chapter, including its plots.
    # A chapter-specific marker prevents checking the previous chapter's DOM.
    expect(page.locator(f'.st-key-chapter-recap-{number}')).to_be_visible(timeout=60000)
    page.get_by_role('button', name='Stop', exact=True).wait_for(state='hidden', timeout=60000)
    expect(page.locator('.katex-error')).to_have_count(0)
    expect(page.locator('[data-testid="stException"]')).to_have_count(0)


def select_chapter(page, title):
    radio = page.get_by_role('radio', name=title, exact=True)
    # The styled radio's label covers its input; click the visible label.
    page.get_by_test_id('stRadioOption').filter(has=radio).click()
    expect(radio).to_be_checked()
    wait_for_chapter(page, int(title.split(' · ')[0]))


if __name__ == '__main__':
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        try:
            page = browser.new_page(viewport={'width': 1400, 'height': 1000})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto('http://127.0.0.1:8501/')
            wait_for_chapter(page, 1)

            select_chapter(page, '9 · Turbomachinery')
            feed = page.get_by_role('spinbutton', name='Air feed ṁ [kg/s]', exact=True)
            feed.fill('60')
            feed.press('Enter')
            expect(feed).to_have_value('60.00')
            wait_for_chapter(page, 9)
            select_chapter(page, '1 · Energy')
            select_chapter(page, '9 · Turbomachinery')
            expect(feed).to_have_value('60.00')

            select_chapter(page, '2 · Pipes')
            page.get_by_role('button', name='Solve network', exact=True).click()
            download = page.get_by_role('button', name='Download pipe results (CSV)', exact=True)
            download.wait_for(timeout=30000)
            wait_for_chapter(page, 2)
            expect(page.locator('.st-key-plot-network')).to_have_count(1)
            page.locator('.st-key-plot-network').screenshot(path='network-verification.png')
            with page.expect_download() as downloaded:
                download.click()
            assert downloaded.value.suggested_filename == 'network-pipes.csv'
            wait_for_chapter(page, 2)
            expect(download).to_be_visible()

            for title in [
                '3 · Scaling', '4 · Turbulence', '5 · Euler', '6 · Stress & NS',
                '7 · Exact flows', '8 · External flow', '10 · Compressible',
                '11 · CFD', '12 · Reference',
            ]:
                select_chapter(page, title)
            assert not errors, errors
            print('PASS: all chapters, live input persistence, network solve, CSV download and equation rendering.')
        finally:
            browser.close()
