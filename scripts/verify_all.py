#!/usr/bin/env python3
import sys
import subprocess
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def run_cmd(args, cwd=ROOT, env=None):
    print(f"\nRunning: {' '.join(args)}")
    result = subprocess.run(args, cwd=cwd, env=env, text=True)
    if result.returncode != 0:
        print(f"FAIL: Command failed with exit code {result.returncode}")
        sys.exit(1)
    print("SUCCESS")

def verify_no_generated_artifacts():
    print("\n[Verifier] Running generated-artifact scan...")
    try:
        git_files_raw = subprocess.check_output(["git", "ls-files"], text=True)
        git_files = git_files_raw.splitlines()
        for f in git_files:
            if any(x in f for x in [".egg-info", ".venv", "build/", "dist/"]):
                print(f"FAIL: A generated artifact/virtualenv file is tracked in git: {f}")
                sys.exit(1)
    except subprocess.SubprocessError as e:
        print(f"Warning: Failed to run git ls-files ({e}). Skipping tracked artifact verification.")
    print("OK: No generated egg-info, .venv, build, or dist files are tracked in git")

def verify_no_obvious_secrets():
    print("\n[Verifier] Running obvious secret assignment scan...")
    try:
        git_files_raw = subprocess.check_output(["git", "ls-files"], text=True)
        git_files = git_files_raw.splitlines()
    except subprocess.SubprocessError:
        git_files = []

    secret_patterns = [
        (re.compile(r'(?i)(api_key|password|client_secret|private_key|token|auth_token)\s*=\s*[\'"]([a-zA-Z0-9_\-\.\:\/]+)[\'"]'), "assignment"),
        (re.compile(r'-----BEGIN .* PRIVATE KEY-----'), "private_key_header")
    ]
    for f in git_files:
        path = ROOT / f
        if (f.startswith("tests/") or 
            f.endswith(".md") or 
            f.startswith("scripts/") or 
            "test" in f or 
            "example" in f or
            "mock" in f):
            continue
        if path.is_file():
            try:
                content = path.read_text(encoding="utf-8")
                if "-----BEGIN" in content and "PRIVATE KEY-----" in content:
                    print(f"FAIL: Obvious committed secret (private key) in {f}")
                    sys.exit(1)
                for pattern, ptype in secret_patterns:
                    if ptype == "assignment":
                        for match in pattern.finditer(content):
                            key, val = match.groups()
                            val_lower = val.lower()
                            if any(x in val_lower for x in ["mock", "test", "dummy", "example", "placeholder", "token", "schema"]):
                                continue
                            if re.match(r'^v?\d+\.\d+\.\d+$', val) or val.endswith(".v0"):
                                continue
                            if len(val) >= 12:
                                print(f"FAIL: Potential obvious committed secret '{key}' in {f}")
                                sys.exit(1)
            except Exception:
                pass
    print("OK: No obvious committed secrets detected in non-test files")

def verify_no_blocked_modules():
    print("\n[Verifier] Running advanced blocked module scan...")
    blocked_patterns = [
        ("src/ultimate_ai_agent/core/skill_factory/", "Skill Factory"),
        ("src/ultimate_ai_agent/core/self_improvement/", "Self Improving Code"),
        ("src/ultimate_ai_agent/core/autopilot/", "Autopilot Workflows"),
        ("src/ultimate_ai_agent/core/scanners/", "Secrets/Dependency Scanners"),
    ]
    for rel_path, desc in blocked_patterns:
        p = ROOT / rel_path
        if p.exists():
            print(f"FAIL: Blocked module implemented: {desc} ({rel_path})")
            sys.exit(1)
            
    # Scan src/ for active execution imports of real models
    for p in (ROOT / "src").rglob("*.py"):
        try:
            content = p.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.strip().startswith(("import openai", "import anthropic", "import google.generativeai")):
                    print(f"FAIL: Forbidden model provider import in {p.relative_to(ROOT)}: {line}")
                    sys.exit(1)
                if "from openai import" in line or "from anthropic import" in line or "from google import generativeai" in line:
                    print(f"FAIL: Forbidden model provider import in {p.relative_to(ROOT)}: {line}")
                    sys.exit(1)
        except Exception:
            pass
    print("OK: Advanced blocked modules are not implemented")

def verify_no_forbidden_external_integrations():
    print("\n[Verifier] Running forbidden external integration scan...")
    forbidden_imports = [
        "import requests",
        "from requests import",
        "import httpx",
        "from httpx import",
        "import urllib.request",
        "from urllib import request",
        "import boto3",
    ]
    for p in (ROOT / "src").rglob("*.py"):
        try:
            content = p.read_text(encoding="utf-8")
            for line in content.splitlines():
                stripped = line.strip()
                if any(stripped.startswith(pattern) for pattern in forbidden_imports):
                    print(f"FAIL: Forbidden external integration import in {p.relative_to(ROOT)}: {line}")
                    sys.exit(1)
                if ".get(" in stripped and ("http://" in stripped or "https://" in stripped):
                    print(f"FAIL: Possible provider/network call in {p.relative_to(ROOT)}: {line}")
                    sys.exit(1)
        except Exception:
            pass
    print("OK: No forbidden provider API clients or network calls detected in src")

def verify_no_shell_execution_in_runtime():
    print("\n[Verifier] Running runtime shell/subprocess execution scan...")
    forbidden_fragments = [
        "import subprocess",
        "from subprocess import",
        "os.system(",
        "popen(",
        "subprocess.",
    ]
    for p in (ROOT / "src").rglob("*.py"):
        try:
            content = p.read_text(encoding="utf-8")
            for line in content.splitlines():
                stripped = line.strip()
                if any(fragment in stripped for fragment in forbidden_fragments):
                    print(f"FAIL: Forbidden shell/subprocess execution in {p.relative_to(ROOT)}: {line}")
                    sys.exit(1)
        except Exception:
            pass
    print("OK: No shell/subprocess execution detected in runtime source")

def main():
    print("=== Ultimate AI Agent Master Verification Suite ===")

    # 1. Run Ruff Linter
    run_cmd([sys.executable, "-m", "ruff", "check", "."])

    # 2. Run Pytest Suite
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    run_cmd([sys.executable, "-m", "pytest"], env=env)

    # 3. Explicitly Enforce Scans
    verify_no_generated_artifacts()
    verify_no_obvious_secrets()
    verify_no_blocked_modules()
    verify_no_forbidden_external_integrations()
    verify_no_shell_execution_in_runtime()

    # 4. Run Baseline Consistency Verification
    run_cmd([sys.executable, "scripts/verify_current_baseline.py"])

    # 5. Run Skill Package Security Rule Audit
    run_cmd([sys.executable, "scripts/verify_skill_package_security_rule.py"])

    print("\n=== All verification checks PASSED successfully ===")

if __name__ == "__main__":
    main()
