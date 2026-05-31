#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def run_cmd(args, cwd=ROOT, env=None):
    print(f"\nRunning: {' '.join(args)}")
    result = subprocess.run(args, cwd=cwd, env=env, text=True)
    if result.returncode != 0:
        print(f"FAIL: Command failed with exit code {result.returncode}")
        sys.exit(1)
    print("SUCCESS")

def main():
    print("=== Ultimate AI Agent Master Verification Suite ===")

    # 1. Run Ruff Linter
    run_cmd([sys.executable, "-m", "ruff", "check", "."])

    # 2. Run Pytest Suite
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    run_cmd([sys.executable, "-m", "pytest"], env=env)

    # 3. Run Baseline Consistency Verification
    run_cmd([sys.executable, "scripts/verify_current_baseline.py"])

    # 4. Run Skill Package Security Rule Audit
    run_cmd([sys.executable, "scripts/verify_skill_package_security_rule.py"])

    print("\n=== All verification checks PASSED successfully ===")

if __name__ == "__main__":
    main()
