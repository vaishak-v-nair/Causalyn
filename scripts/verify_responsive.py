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

VIEWPORTS = [
    {"name": "Desktop 1080p", "width": 1920, "height": 1080},
    {"name": "Laptop 1366", "width": 1366, "height": 768},
    {"name": "Tablet Portrait", "width": 768, "height": 1024},
    {"name": "Mobile iPhone 14", "width": 390, "height": 844},
]

PAGES = [
    {"path": "/", "name": "Cockpit"},
    {"path": "/overview", "name": "Platform Overview"},
    {"path": "/invariants", "name": "Policy Studio"},
    {"path": "/proofs", "name": "Theory & Proofs"},
    {"path": "/audit", "name": "Audit Ledger"},
    {"path": "/swarm", "name": "Swarm Bus"},
]

async def verify_all():
    failed = False
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        for page_info in PAGES:
            print(f"\n==========================================")
            print(f"Auditing Page: {page_info['name']} ({page_info['path']})")
            print(f"==========================================")
            
            for vp in VIEWPORTS:
                page = await context.new_page()
                await page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
                
                errors = []
                page.on("pageerror", lambda err: errors.append(str(err)))
                page.on("console", lambda msg: errors.append(f"CONSOLE {msg.type}: {msg.text}") if msg.type == "error" else None)

                url = f"http://127.0.0.1:8000{page_info['path']}"
                try:
                    await page.goto(url, wait_until="networkidle", timeout=10000)
                    await asyncio.sleep(1.0) # allow any canvas / layout init

                    metrics = await page.evaluate('''() => {
                        return {
                            docScrollWidth: document.documentElement.scrollWidth,
                            docClientWidth: document.documentElement.clientWidth,
                            bodyScrollWidth: document.body.scrollWidth,
                            bodyClientWidth: document.body.clientWidth,
                            windowInnerWidth: window.innerWidth
                        };
                    }''')

                    doc_overflow = metrics["docScrollWidth"] > metrics["docClientWidth"]
                    body_overflow = metrics["bodyScrollWidth"] > metrics["bodyClientWidth"]
                    has_h_overflow = doc_overflow or body_overflow

                    status_sym = "[FAIL]" if has_h_overflow else "[PASS]"
                    err_status = f" | Console Errors: {len(errors)}" if errors else " | No Errors"
                    
                    print(f"{status_sym} {vp['name']} ({vp['width']}x{vp['height']}): "
                          f"docScroll={metrics['docScrollWidth']} vs client={metrics['docClientWidth']}, "
                          f"bodyScroll={metrics['bodyScrollWidth']} vs client={metrics['bodyClientWidth']}{err_status}")
                    
                    if errors:
                        for e in errors:
                            print(f"    -> {e}")
                            failed = True

                    if has_h_overflow:
                        # Find offending overflowing element
                        offender = await page.evaluate('''() => {
                            let maxEl = null;
                            let maxW = window.innerWidth;
                            document.querySelectorAll('*').forEach(el => {
                                const rect = el.getBoundingClientRect();
                                if (rect.right > maxW + 2) {
                                    maxW = rect.right;
                                    maxEl = {
                                        tag: el.tagName,
                                        id: el.id,
                                        class: el.className,
                                        right: rect.right,
                                        width: rect.width
                                    };
                                }
                            });
                            return maxEl;
                        }''')
                        print(f"    Offending Element: {offender}")
                        failed = True

                except Exception as ex:
                    print(f"[ERROR] Error navigating to {url} at {vp['name']}: {ex}")
                    failed = True
                finally:
                    await page.close()

        await browser.close()
    
    if failed:
        print("\nAudit FINISHED WITH ISSUES.")
        sys.exit(1)
    else:
        print("\nAudit ALL PASSED! 100% Zero Horizontal Overflow & Clean Console across all viewports!")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(verify_all())
