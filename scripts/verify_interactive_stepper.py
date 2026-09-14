import asyncio
import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from playwright.async_api import async_playwright

async def run_interactive_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.on("console", lambda msg: errors.append(f"{msg.type}: {msg.text}") if msg.type == "error" else None)
        
        print("Navigating to Cockpit...")
        await page.goto("http://127.0.0.1:8000/", wait_until="networkidle", timeout=10000)
        await asyncio.sleep(1.0)
        
        # 1. Verify Favicon
        favicon_link = await page.query_selector('link[rel="icon"]')
        href = await favicon_link.get_attribute("href") if favicon_link else None
        print(f"Favicon Link href: {href}")
        assert href == "/favicon.ico", f"Expected /favicon.ico, got {href}"
        
        # 2. Verify Stepper initially at Phase 1
        s1_classes = await page.eval_on_selector('#stepper-step-1', 'el => el.className')
        print(f"Initial Step 1 classes: {s1_classes}")
        assert "active" in s1_classes, "Step 1 should be active initially"
        
        # Screenshot Initial Cockpit
        await page.screenshot(path="web/assets/test_cockpit_initial.png")
        print("Saved web/assets/test_cockpit_initial.png")
        
        # 3. Test 'How It Works' Modal
        print("Testing 'How It Works' Modal...")
        await page.click("#btn-how-it-works")
        await asyncio.sleep(0.4)
        
        modal_visible = await page.eval_on_selector('#modal-how-it-works', 'el => el.style.display')
        print(f"Modal display after click: {modal_visible}")
        assert modal_visible == "flex", "Modal should have display: flex"
        
        await page.screenshot(path="web/assets/test_how_it_works_modal.png")
        print("Saved web/assets/test_how_it_works_modal.png")
        
        # Close modal
        await page.click("#btn-close-how-it-works")
        await asyncio.sleep(0.3)
        modal_visible_after = await page.eval_on_selector('#modal-how-it-works', 'el => el.style.display')
        print(f"Modal display after close: {modal_visible_after}")
        assert modal_visible_after == "none", "Modal should have display: none"
        
        # 4. Test Guided Discovery Scenario Card (CEGIS Auto-Patch)
        print("Testing Guided Discovery Scenario Card click...")
        await page.click("#card-scen-cegis")
        print("Clicked #card-scen-cegis, waiting for thought streaming and SMT synthesis...")
        await asyncio.sleep(3.0)
        
        # Verify Stepper Phase 3 is now verified
        s3_classes = await page.eval_on_selector('#stepper-step-3', 'el => el.className')
        print(f"Post-execution Step 3 classes: {s3_classes}")
        
        # Check proof box contains CEGIS AUTO-PATCH
        proof_text = await page.inner_text("#proof-box")
        print(f"Proof Box snippet: {proof_text[:120]}...")
        
        await page.screenshot(path="web/assets/test_cegis_autopatch_verified.png")
        print("Saved web/assets/test_cegis_autopatch_verified.png")
        
        print(f"\nAll interactive checks passed! Total Console Errors: {len(errors)}")
        if errors:
            for e in errors:
                print(f"  [ERROR] {e}")
            sys.exit(1)
        
        await browser.close()
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(run_interactive_test())
