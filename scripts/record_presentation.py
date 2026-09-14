"""
Autonomous Presentation Recording Script for Causalyn
Generates a broadcast-quality 1080p recording of the complete working Causalyn hypervisor.
Outputs:
  - causalyn_presentation_demo.mp4 (High-bitrate H.264 1080p MP4)
  - causalyn_presentation_demo.webp (Optimized animated WebP for markdown/docs)
"""
import os
import sys
import time
import shutil
import tempfile
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

ARTIFACT_DIR = Path(r"C:\Users\vaish\.gemini\antigravity-ide\brain\e0573855-1dfc-47e9-9ff0-acf49c2035c3")
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def smooth_scroll(page, delta_y, steps=25, interval=0.03):
    step_y = delta_y / steps
    for _ in range(steps):
        page.evaluate(f"window.scrollBy(0, {step_y})")
        time.sleep(interval)

def main():
    print("=" * 65)
    print("  CAUSALYN PRESENTATION RECORDING ENGINE (BROADCAST QUALITY)")
    print("=" * 65)

    temp_video_dir = Path(tempfile.mkdtemp(prefix="causalyn_record_"))
    print(f"[*] Temporary video directory: {temp_video_dir}")

    try:
        with sync_playwright() as p:
            print("[*] Launching Chromium with WebGL support...")
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--use-gl=angle",
                    "--use-angle=gl",
                    "--enable-webgl",
                    "--ignore-gpu-blocklist",
                    "--no-sandbox",
                    "--disable-setuid-sandbox"
                ]
            )

            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                record_video_dir=str(temp_video_dir),
                record_video_size={"width": 1920, "height": 1080}
            )

            page = context.new_page()

            print("\n>>> Scene 1: Initial Resting Equilibrium Cockpit (kappa=0.00)")
            page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
            page.wait_for_selector(".app-container", state="visible", timeout=15000)
            page.wait_for_selector("#manifold-canvas", state="attached", timeout=15000)
            print("    [+] Cockpit loaded. Showcasing 3D Symplectic Wireframe Manifold...")
            time.sleep(3.5)

            print("    [+] Demonstrating 3D Camera Controls...")
            page.click('button.btn-cam[data-cam="top"]')
            print("        - Selected: TOPOLOGICAL Preset")
            time.sleep(2.0)

            page.click('button.btn-cam[data-cam="orbit"]')
            print("        - Selected: KINETIC ORBIT Preset")
            time.sleep(2.5)

            page.click('button.btn-cam[data-cam="perspective"]')
            print("        - Selected: 45° ISOMETRIC Preset")
            time.sleep(2.0)

            print("\n>>> Scene 2: Sub-millisecond CEGIS AST Auto-Patching (44µs)")
            print("    [+] Injecting candidate parameter mutation via #btn-sim-paradox...")
            page.click("#btn-sim-paradox")
            print("    [+] Capturing LLM thought token streaming, AST diff repair, and Ricci flow...")
            time.sleep(5.0)

            print("\n>>> Scene 3: Malicious DDL Annihilation / Zero Disk Leak")
            print("    [+] Injecting DROP TABLE malicious mutation...")
            page.click('button.preset-chip.danger[data-prompt*="drop table"]')
            print("    [+] Capturing paradox spike (kappa=999.00), quantum collapse, and ledger entry...")
            time.sleep(4.5)

            print("\n>>> Scene 4: Safe Equilibrium Recovery")
            print("    [+] Injecting compliant specification (#btn-sim-safe)...")
            page.click("#btn-sim-safe")
            print("    [+] State relaxed back to pristine harmonic equilibrium (kappa=0.00)...")
            time.sleep(3.5)

            print("\n>>> Scene 5: Policy Studio & Live SMT Verification")
            print("    [+] Navigating to /invariants via top nav...")
            page.click('a[href="/invariants"]')
            page.wait_for_selector(".policy-table", state="visible", timeout=15000)
            print("    [+] Policy Studio active. Demonstrating invariant rules and KPIs...")
            time.sleep(2.5)
            smooth_scroll(page, 300)
            time.sleep(1.5)

            print("    [+] Executing live in-memory SMT dry-run verification (#btn-dryrun)...")
            page.click("#btn-dryrun")
            print("    [+] Z3 SMT satisfiable banner displayed...")
            time.sleep(3.5)

            print("\n>>> Scene 6: Theory & Formal Proofs")
            print("    [+] Navigating to /proofs via top nav...")
            page.click('a[href="/proofs"]')
            page.wait_for_selector(".proofs-main-content", state="visible", timeout=15000)
            print("    [+] Theory & Proofs active. Showcasing Axioms I & II + Manim video derivations...")
            time.sleep(2.5)
            smooth_scroll(page, 550)
            time.sleep(3.0)
            print("    [+] Scrolling to Axioms III & IV...")
            smooth_scroll(page, 550)
            time.sleep(3.5)

            print("\n>>> Scene 7: Grand Finale Return to Live Cockpit")
            print("    [+] Returning to / via top nav...")
            page.click('a[href="/"]')
            page.wait_for_selector(".app-container", state="visible", timeout=15000)
            print("    [+] Final equilibrium verification...")
            time.sleep(4.0)

            video_path = page.video.path()
            print(f"\n[*] Finalizing raw video recording from Playwright: {video_path}")
            context.close()
            browser.close()

        raw_video = Path(video_path)
        if not raw_video.exists():
            print(f"[!] Error: Raw video file {raw_video} not found!")
            sys.exit(1)

        print(f"[+] Raw video size: {raw_video.stat().st_size / (1024*1024):.2f} MB")

        out_mp4_root = PROJECT_ROOT / "causalyn_presentation_demo.mp4"
        out_webp_root = PROJECT_ROOT / "causalyn_presentation_demo.webp"

        out_mp4_artifact = ARTIFACT_DIR / "causalyn_presentation_demo.mp4"
        out_webp_artifact = ARTIFACT_DIR / "causalyn_presentation_demo.webp"

        print("\n[*] Encoding broadcast-quality 1080p MP4 (H.264 / 30fps)...")
        cmd_mp4 = [
            "ffmpeg", "-y",
            "-i", str(raw_video),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-preset", "medium",
            "-movflags", "+faststart",
            str(out_mp4_root)
        ]
        subprocess.run(cmd_mp4, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"    [+] 1080p MP4 encoded: {out_mp4_root} ({out_mp4_root.stat().st_size / (1024*1024):.2f} MB)")

        print("\n[*] Encoding optimized animated WebP (1280x720 / 18fps)...")
        cmd_webp = [
            "ffmpeg", "-y",
            "-i", str(raw_video),
            "-vf", "fps=18,scale=1280:-1:flags=lanczos",
            "-loop", "0",
            "-c:v", "libwebp",
            "-lossless", "0",
            "-q:v", "75",
            "-compression_level", "4",
            str(out_webp_root)
        ]
        subprocess.run(cmd_webp, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"    [+] Animated WebP encoded: {out_webp_root} ({out_webp_root.stat().st_size / (1024*1024):.2f} MB)")

        # Copy to artifact directory
        shutil.copy2(out_mp4_root, out_mp4_artifact)
        shutil.copy2(out_webp_root, out_webp_artifact)
        print(f"    [+] Saved MP4 to artifact: {out_mp4_artifact}")
        print(f"    [+] Saved WebP to artifact: {out_webp_artifact}")

        print("\n" + "=" * 65)
        print("  PRESENTATION RECORDING COMPLETED SUCCESSFULLY!")
        print("=" * 65)

    finally:
        shutil.rmtree(temp_video_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
