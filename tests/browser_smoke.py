"""Optional real-browser regression: uv run --with playwright python tests/browser_smoke.py.

Start the app on port 8501 first. Requires installed Microsoft Edge.
"""
import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    page = browser.new_page(viewport={'width': 1400, 'height': 1000})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://127.0.0.1:8501/')
    page.get_by_role('tab', name='2 · Pipes', exact=True).click(timeout=60000)
    page.get_by_role('tab', name='12 · Reference', exact=True).click()
    page.get_by_role('heading', name='12. Reference & model selection', exact=True).wait_for(timeout=30000)
    # Completion matters: watcher stalls can leave a fully drawn page unable
    # to process subsequent widget actions, which AppTest cannot detect.
    page.get_by_role('button', name='Stop', exact=True).wait_for(state='hidden', timeout=30000)
    page.get_by_role('tab', name='2 · Pipes', exact=True).click()
    page.get_by_role('button', name='Solve network', exact=True).click()
    download = page.get_by_role('button', name='Download pipe results (CSV)', exact=True)
    download.wait_for(timeout=30000)
    assert page.locator('.st-key-plot-network').count() == 1
    page.locator('.st-key-plot-network').screenshot(path='network-verification.png')
    with page.expect_download() as downloaded:
        download.click()
    assert downloaded.value.suggested_filename == 'network-pipes.csv'
    for title in ['8 · External flow', '9 · Turbomachinery', '10 · Compressible', '11 · CFD', '12 · Reference']:
        page.get_by_role('tab', name=title, exact=True).click()
        assert page.locator('.katex-error').count() == 0
        assert page.locator('[data-testid="stException"]').count() == 0
    assert not errors, errors
    print('PASS: live network solve, CSV download, new chapters and equation rendering.')
    browser.close()
