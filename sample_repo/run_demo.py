import os
import subprocess
import time
from pathlib import Path


def run(cmd: str, check=True):
    print(f"\n> {cmd}")
    subprocess.run(cmd, shell=True, check=check)
    time.sleep(1)


def main():
    print("=== Causalyn 48-Hour Demo Scenario ===")
    repo_dir = Path(__file__).parent.resolve()
    os.chdir(repo_dir)

    # 1. Setup
    run("git add .", check=False)
    run('git commit -m "Add demo files"', check=False)
    
    if not (repo_dir / ".causalyn").exists():
        run("causalyn init", check=False)
    
    # Reset git to clean state in case this is run multiple times
    current_branch = subprocess.run("git branch --show-current", shell=True, capture_output=True, text=True).stdout.strip()
    if not current_branch or current_branch == "causalyn/checkpoints":
        run("git checkout main || git checkout master", check=False)
    
    # Don't do git clean -fd, we just reset files tracked by git
    run("git reset --hard")
    
    print("\n--- Simulating Agent Steps (Claude Code) ---")
    
    # Step 1: Normal step
    run('python -c "print(\'Step 1: Analyzing codebase...\')"')
    
    print("\nSimulating agent steps using CheckpointEngine...")
    
    from causalyn.checkpoint import CheckpointEngine
    from causalyn.models import StepKind
    from causalyn.config import CausalynConfig
    
    config = CausalynConfig.from_env()
    engine = CheckpointEngine(repo_dir=repo_dir, branch=config.checkpoint_branch)
    engine.begin_session()
    
    # Step 0
    engine.create("Baseline", StepKind.COMMAND_RUN, "step_0")
    print("Checkpoint: step_0 (Baseline)")
    
    # Step 1 (Safe)
    (repo_dir / "utils.py").write_text("def helper(): pass\n")
    engine.create("Add utils.py", StepKind.FILE_WRITE, "step_1")
    print("Checkpoint: step_1 (Add utils.py)")
    
    # Step 2 (THE BUG - removing auth import)
    app_py = repo_dir / "app.py"
    content = app_py.read_text()
    # Let's break it by replacing auth instance with None
    broken_content = content.replace("auth = AuthMiddleware()", "auth = None # Agent accidentally removed this")
    app_py.write_text(broken_content)
    
    engine.create("Refactor app.py (SILENT MISTAKE)", StepKind.FILE_WRITE, "step_2")
    print("Checkpoint: step_2 (SILENT BUG INTRODUCED)")
    
    # Step 3 (Building on broken state)
    (repo_dir / "config.py").write_text("DEBUG = True\n")
    engine.create("Add config.py", StepKind.FILE_WRITE, "step_3")
    print("Checkpoint: step_3 (More agent work)")
    
    # Step 4 (The Crash)
    print("\n--- Agent runs tests (Step 4) ---")
    run("pytest test_app.py", check=False)
    engine.create("Run pytest (CRASH)", StepKind.COMMAND_RUN, "step_4")
    
    print("\n--- Causalyn Intercepts! ---")
    print("Running: causalyn bisect 'pytest test_app.py -q'")
    run("causalyn bisect \"pytest test_app.py -q\"", check=False)
    
    print("\n--- Agent proposes a fix ---")
    print("The agent proposes changing 'auth = None' to 'auth = object()' instead of fixing the real issue.")
    bad_fix = (repo_dir / "bad_fix.patch")
    bad_fix.write_text("-auth = None # Agent accidentally removed this\n+auth = object() # Bad fix")
    
    print("\nRunning: causalyn verify bad_fix.patch --task 'Add user profile'")
    print("(Note: This requires OPENAI_API_KEY to be set)")
    
    if os.name == "nt":
        env_vars = "set CAUSALYN_VERIFICATION_PROVIDER=mock&& set CAUSALYN_VERIFICATION_MODEL=mock-eval-70b&& "
    else:
        env_vars = "CAUSALYN_VERIFICATION_PROVIDER=mock CAUSALYN_VERIFICATION_MODEL=mock-eval-70b "
        
    run(f"{env_vars}causalyn verify bad_fix.patch --task \"Add user profile\"", check=False)
        
    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    main()
