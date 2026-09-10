"""Live caption and navigation regression; run with the app on port 8501.

uv run --with playwright python tests/browser_non_newtonian.py
"""
from pathlib import Path
import tempfile

from playwright.sync_api import expect, sync_playwright

from browser_smoke import select_chapter, wait_for_chapter


if __name__ == "__main__":
    output = Path(tempfile.gettempdir()) / "fluid-non-newtonian-verification"
    output.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        try:
            page = browser.new_page(viewport={"width": 1400, "height": 1000})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto("http://127.0.0.1:8501/")
            wait_for_chapter(page, 1)
            select_chapter(page, "7 · Non-Newtonian")
            caption = page.get_by_text("For these settings", exact=False)
            before = caption.inner_text()
            slider = page.locator(".st-key-nn_curve_n").get_by_role("slider")
            slider.focus()
            slider.press("Home")
            for _ in range(16):
                slider.press("ArrowRight")
            slider.press("Tab")
            # Wait for changed output before the existing recap.
            expect(caption).to_contain_text("At n = 1", timeout=60000)
            wait_for_chapter(page, 7)
            assert caption.inner_text() != before
            ratio = page.get_by_test_id("stMetric").filter(
                has=page.get_by_text("Low/high shear viscosity ratio", exact=True)
            )
            expect(ratio).to_contain_text("1×")
            caption.scroll_into_view_if_needed()
            page.screenshot(path=str(output / "caption-desktop.png"))
            select_chapter(page, "1 · Energy")
            select_chapter(page, "7 · Non-Newtonian")
            expect(caption).to_contain_text("At n = 1")
            page.get_by_test_id("stSidebarHeader").hover()
            page.get_by_test_id("stSidebarCollapseButton").get_by_role("button").click()
            expect(page.get_by_test_id("stSidebar")).not_to_be_in_viewport()
            page.set_viewport_size({"width": 390, "height": 844})
            caption.scroll_into_view_if_needed()
            page.screenshot(path=str(output / "caption-mobile.png"))
            expect(page.locator(".katex-error")).to_have_count(0)
            expect(page.get_by_test_id("stException")).to_have_count(0)
            assert not errors, errors
            print(f"PASS: live viscosity caption, chapter round trip, mobile rendering. {output}")
        finally:
            browser.close()
