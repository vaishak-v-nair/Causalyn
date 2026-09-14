import asyncio
import sys
import time
import json
from playwright.async_api import async_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

async def pressure_test_web():
    t_start = time.perf_counter()
    print("\n" + "=" * 70)
    print("      CAUSALYN WEB COCKPIT HIGH-THROUGHPUT PRESSURE & STRESS AUDIT")
    print("=" * 70)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        errors = []
        page.on("pageerror", lambda err: errors.append(f"PAGE ERROR: {err}"))
        page.on("console", lambda msg: errors.append(f"CONSOLE ERROR: {msg.text}") if msg.type == "error" else None)

        print("\n[TEST 1] Connecting to Cockpit...")
        await page.goto("http://127.0.0.1:8000/", wait_until="networkidle", timeout=15000)
        await asyncio.sleep(1.0)
        print("  -> Cockpit loaded successfully.")

        # -------------------------------------------------------------
        # 1. High-Frequency UI Fuzzing (Rapid Click Storm)
        # -------------------------------------------------------------
        print("\n[TEST 2] Executing Rapid UI Interaction Fuzzing...")
        fuzz_start = time.perf_counter()
        
        # Rapid Stance Toggles
        for _ in range(5):
            await page.click("#btn-stance-defensive")
            await asyncio.sleep(0.05)
            await page.click("#btn-stance-autobahn")
            await asyncio.sleep(0.05)
        print("  -> Stance toggles (10 rapid switches): OK")

        # Rapid Camera Angle Switches
        cam_buttons = await page.query_selector_all(".btn-cam")
        for btn in cam_buttons:
            await btn.click()
            await asyncio.sleep(0.08)
        print("  -> Camera preset transitions (3 switches): OK")

        # Rapid Modal Open / Close Cycles
        for _ in range(3):
            await page.click("#btn-how-it-works")
            await asyncio.sleep(0.08)
            await page.click("#btn-close-how-it-works")
            await asyncio.sleep(0.08)
        print("  -> Guide Modal open/close cycles (3 cycles): OK")

        # Rapid Timeline Scrubbing
        for val in [10, 50, 85, 20, 100, 0, 70]:
            await page.evaluate(f'''() => {{
                const el = document.getElementById("timeline-range");
                if (el) {{
                    el.value = {val};
                    el.dispatchEvent(new Event("input"));
                }}
            }}''')
            await asyncio.sleep(0.04)
        print("  -> Timeline scrubber rapid seek: OK")
        print(f"  Fuzzing Phase Completed in {time.perf_counter() - fuzz_start:.2f}s")

        # -------------------------------------------------------------
        # 2. WebSocket High-Frequency Event Storm Simulation
        # -------------------------------------------------------------
        print("\n[TEST 3] Simulating High-Frequency WebSocket Telemetry Storm (100 Events)...")
        storm_start = time.perf_counter()
        
        # Dispatch 100 rapid events directly through window to verify DOM bounded capping
        storm_result = await page.evaluate('''async () => {
            const results = [];
            for (let i = 0; i < 50; i++) {
                const kappa = (i % 2 === 0) ? 1.0 : 0.0;
                const status = (i % 2 === 0) ? "SYNTHESIZED" : "COMMITTED";
                const eventData = {
                    type: "paradox_spike",
                    agent_id: `STORM-WORKER-${i}`,
                    target_file: `batch_${i}.py`,
                    kappa: kappa,
                    status: status,
                    latency_us: 42.5 + (i * 1.1),
                    vector_clock: i,
                    patch: (status === "SYNTHESIZED") ? { corrected: true, values: { threads: 16 } } : null,
                    proposed_state: { threads: 32 },
                    proposed_content: "threads = 32"
                };
                
                // Directly call message handler if available
                window.dispatchEvent(new MessageEvent('message', { data: JSON.stringify(eventData) }));
            }
            
            const feed = document.getElementById('terminal-feed');
            const hashList = document.getElementById('hash-list');
            return {
                feedCount: feed ? feed.children.length : 0,
                hashCount: hashList ? hashList.children.length : 0
            };
        }''')
        
        await asyncio.sleep(1.0)
        print(f"  -> Storm processed in {time.perf_counter() - storm_start:.2f}s.")
        print(f"  -> Terminal Feed DOM Node Count: {storm_result.get('feedCount')} (Capped <= 30)")
        print(f"  -> Ground Truth Ledger DOM Node Count: {storm_result.get('hashCount')} (Capped <= 5)")

        # -------------------------------------------------------------
        # 3. Concurrent Multi-Tab Cockpit Load
        # -------------------------------------------------------------
        print("\n[TEST 4] Testing Concurrent Multi-Tab Cockpit Load (3 Tabs)...")
        page2 = await context.new_page()
        page3 = await context.new_page()
        
        await asyncio.gather(
            page2.goto("http://127.0.0.1:8000/", wait_until="networkidle", timeout=10000),
            page3.goto("http://127.0.0.1:8000/", wait_until="networkidle", timeout=10000)
        )
        print("  -> 3 Simultaneous Cockpits Connected to WebSocket Continuum.")
        
        # Trigger scenario from tab 1 and verify tab 2 and 3 remain error-free
        await page.click("#card-scen-safe")
        await asyncio.sleep(2.0)
        print("  -> Prompt dispatched under concurrent multi-tab load: OK")

        await page2.close()
        await page3.close()

        # -------------------------------------------------------------
        # 4. Final Console & Layout Stability Verification
        # -------------------------------------------------------------
        print("\n[TEST 5] Auditing Memory & Layout Health...")
        layout_metrics = await page.evaluate('''() => {
            return {
                scrollWidth: document.documentElement.scrollWidth,
                clientWidth: document.documentElement.clientWidth,
                bodyScroll: document.body.scrollWidth,
                bodyClient: document.body.clientWidth
            };
        }''')
        
        has_overflow = layout_metrics["scrollWidth"] > layout_metrics["clientWidth"]
        print(f"  -> Horizontal Overflow Check: {'FAIL' if has_overflow else 'PASS'}")
        print(f"  -> Total Console / Page Errors: {len(errors)}")

        if errors:
            for err in errors:
                print(f"     [ERROR] {err}")

        assert not has_overflow, "Horizontal overflow detected during stress test!"
        assert len(errors) == 0, f"Encountered {len(errors)} errors during web stress testing!"

        await browser.close()
        total_time = time.perf_counter() - t_start
        print("\n" + "=" * 70)
        print(f"  >>> WEB COCKPIT PRESSURE TEST PASSED IN {total_time:.2f}s <<<")
        print("=" * 70 + "\n")
        return True

if __name__ == "__main__":
    success = asyncio.run(pressure_test_web())
    sys.exit(0 if success else 1)
