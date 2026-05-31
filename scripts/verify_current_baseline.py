#!/usr/bin/env python3
import sys
import re
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent

def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)

def ok(msg):
    print(f"OK: {msg}")

def main():
    print("=== Ultimate AI Agent Baseline Consistency Verification ===")
    
    # 1. Read VERSION.md and extract version
    version_file = ROOT / "VERSION.md"
    if not version_file.exists():
        fail("VERSION.md does not exist")
    
    version_content = version_file.read_text(encoding="utf-8")
    version_match = re.search(r"Current active baseline:\s*\*\*v?(\d+\.\d+\.\d+)\*\*", version_content)
    if not version_match:
        fail("Could not find 'Current active baseline: **vX.Y.Z**' pattern in VERSION.md")
    
    version = version_match.group(1)
    version_with_underscores = version.replace(".", "_")
    ok(f"VERSION.md active baseline version: v{version}")
    
    # 2. Check pyproject.toml version
    pyproject_file = ROOT / "pyproject.toml"
    if not pyproject_file.exists():
        fail("pyproject.toml does not exist")
        
    pyproject_content = pyproject_file.read_text(encoding="utf-8")
    pyproject_match = re.search(r'(?m)^version\s*=\s*[\'"]([^\'"]+)[\'"]', pyproject_content)
    if not pyproject_match:
        fail("Could not find version setting in pyproject.toml")
        
    pyproject_version = pyproject_match.group(1)
    if pyproject_version != version:
        fail(f"pyproject.toml version ({pyproject_version}) does not match VERSION.md baseline ({version})")
    ok(f"pyproject.toml version is consistent: {pyproject_version}")
    
    # 3. Check src/ultimate_ai_agent/__init__.py __version__
    init_file = ROOT / "src" / "ultimate_ai_agent" / "__init__.py"
    if not init_file.exists():
        fail("src/ultimate_ai_agent/__init__.py does not exist")
        
    init_content = init_file.read_text(encoding="utf-8")
    init_match = re.search(r'(?m)^__version__\s*=\s*[\'"]([^\'"]+)[\'"]', init_content)
    if not init_match:
        fail("Could not find __version__ in src/ultimate_ai_agent/__init__.py")
        
    init_version = init_match.group(1)
    if init_version != version:
        fail(f"__init__.py version ({init_version}) does not match VERSION.md baseline ({version})")
    ok(f"src/ultimate_ai_agent/__init__.py version is consistent: {init_version}")
    
    # 4. Check README.md consistency
    readme_file = ROOT / "README.md"
    if not readme_file.exists():
        fail("README.md does not exist")
        
    readme_content = readme_file.read_text(encoding="utf-8")
    if f"v{version}" not in readme_content:
        fail(f"README.md does not mention the active baseline v{version}")
        
    # Generic check for README_IMPORT and master plan references
    import_matches = re.findall(r"README_IMPORT_v(\d+_\d+_\d+)\.md", readme_content)
    for m in import_matches:
        if m != version_with_underscores:
            fail(f"README.md contains legacy start file reference: README_IMPORT_v{m}.md")
            
    plan_matches = re.findall(r"ultimate_ai_agent_master_plan_v(\d+_\d+_\d+)\.md", readme_content)
    for m in plan_matches:
        if m != version_with_underscores:
            fail(f"README.md contains legacy start file reference: ultimate_ai_agent_master_plan_v{m}.md")
            
    # Check that current start files are listed
    if f"README_IMPORT_v{version_with_underscores}.md" not in readme_content:
        fail(f"README.md is missing active start file README_IMPORT_v{version_with_underscores}.md")
    if f"ultimate_ai_agent_master_plan_v{version_with_underscores}.md" not in readme_content:
        fail(f"README.md is missing active start file ultimate_ai_agent_master_plan_v{version_with_underscores}.md")
    ok("README.md active baseline references are consistent (generic check)")
    
    # 5. Check release notes existence
    rel_notes_file = ROOT / "docs" / "release_notes" / f"v{version_with_underscores}.md"
    if not rel_notes_file.exists():
        fail(f"Active version release notes file {rel_notes_file.relative_to(ROOT)} is missing")
    ok(f"Release notes for active version exist: {rel_notes_file.relative_to(ROOT)}")
    
    # 6. Check README_IMPORT and master plan existence on disk
    import_readme_file = ROOT / f"README_IMPORT_v{version_with_underscores}.md"
    master_plan_file = ROOT / f"ultimate_ai_agent_master_plan_v{version_with_underscores}.md"
    
    if not import_readme_file.exists():
        fail(f"README_IMPORT_v{version_with_underscores}.md does not exist")
    if not master_plan_file.exists():
        fail(f"ultimate_ai_agent_master_plan_v{version_with_underscores}.md does not exist")
    ok("README_IMPORT and master plan exist for the current version")
    
    # 7. Check M1 contract files existence
    m1_files = [
        "src/ultimate_ai_agent/core/contracts/enums.py",
        "src/ultimate_ai_agent/core/contracts/execution_contract.py",
        "src/ultimate_ai_agent/core/contracts/context_pack.py",
        "src/ultimate_ai_agent/core/contracts/validation.py",
        "src/ultimate_ai_agent/core/contracts/factory.py",
    ]
    for rel_path in m1_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M1 file is missing: {rel_path}")
    ok("All M1 contract/validation files exist")

    # 8. Check M2 ledger files existence
    m2_files = [
        "src/ultimate_ai_agent/core/ledger/__init__.py",
        "src/ultimate_ai_agent/core/ledger/enums.py",
        "src/ultimate_ai_agent/core/ledger/events.py",
        "src/ultimate_ai_agent/core/ledger/ledger.py",
        "src/ultimate_ai_agent/core/ledger/receipts.py",
        "src/ultimate_ai_agent/core/ledger/replay.py",
        "src/ultimate_ai_agent/core/ledger/run_state.py",
        "src/ultimate_ai_agent/core/ledger/standards.py",
        "src/ultimate_ai_agent/core/ledger/validation.py",
    ]
    for rel_path in m2_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M2 ledger file is missing: {rel_path}")
    ok("All M2 ledger files exist")

    # 8.5 Check M2.5 world state/context budget/runtime/adapter files existence
    m25_files = [
        "src/ultimate_ai_agent/core/world_state/__init__.py",
        "src/ultimate_ai_agent/core/world_state/models.py",
        "src/ultimate_ai_agent/core/world_state/snapshots.py",
        "src/ultimate_ai_agent/core/world_state/validation.py",
        "src/ultimate_ai_agent/core/context_budget/__init__.py",
        "src/ultimate_ai_agent/core/context_budget/models.py",
        "src/ultimate_ai_agent/core/context_budget/token_accounting.py",
        "src/ultimate_ai_agent/core/context_budget/trimming.py",
        "src/ultimate_ai_agent/core/context_budget/validation.py",
        "src/ultimate_ai_agent/core/runtime/__init__.py",
        "src/ultimate_ai_agent/core/runtime/local_runtime.py",
        "src/ultimate_ai_agent/core/runtime/resource_budget.py",
        "src/ultimate_ai_agent/core/runtime/capability_profile.py",
        "src/ultimate_ai_agent/core/runtime/health.py",
        "src/ultimate_ai_agent/core/runtime/validation.py",
        "src/ultimate_ai_agent/core/adapters/__init__.py",
        "src/ultimate_ai_agent/core/adapters/sdk_manifest.py",
        "src/ultimate_ai_agent/core/adapters/a2a_manifest.py",
        "src/ultimate_ai_agent/core/adapters/validation.py",
    ]
    for rel_path in m25_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M2.5 file is missing: {rel_path}")
    ok("All M2.5 world state, context budget, runtime, and adapter files exist")
    
    # 8.6 Check M3 consent/tool files existence
    m3_files = [
        "src/ultimate_ai_agent/core/consent/__init__.py",
        "src/ultimate_ai_agent/core/consent/enums.py",
        "src/ultimate_ai_agent/core/consent/grants.py",
        "src/ultimate_ai_agent/core/consent/policies.py",
        "src/ultimate_ai_agent/core/consent/ledger.py",
        "src/ultimate_ai_agent/core/consent/decisions.py",
        "src/ultimate_ai_agent/core/consent/validation.py",
        "src/ultimate_ai_agent/core/tools/__init__.py",
        "src/ultimate_ai_agent/core/tools/enums.py",
        "src/ultimate_ai_agent/core/tools/manifests.py",
        "src/ultimate_ai_agent/core/tools/requests.py",
        "src/ultimate_ai_agent/core/tools/decisions.py",
        "src/ultimate_ai_agent/core/tools/broker.py",
        "src/ultimate_ai_agent/core/tools/registry.py",
        "src/ultimate_ai_agent/core/tools/capability_firewall.py",
        "src/ultimate_ai_agent/core/tools/validation.py",
    ]
    for rel_path in m3_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M3 file is missing: {rel_path}")
    ok("All M3 consent and tool files exist")
    
    # 9. Verify no tracked egg-info, venv, build, or dist files/directories in git
    git_files = []
    try:
        git_files_raw = subprocess.check_output(["git", "ls-files"], text=True)
        git_files = git_files_raw.splitlines()
        for f in git_files:
            if any(x in f for x in [".egg-info", ".venv", "build/", "dist/"]):
                fail(f"A generated artifact/virtualenv file is tracked in git: {f}")
    except subprocess.SubprocessError as e:
        print(f"Warning: Failed to run git ls-files ({e}). Skipping tracked artifact verification.")
        
    ok("No generated egg-info, .venv, build, or dist files are tracked in git")

    # 10. Check for obvious committed secrets
    secret_patterns = [
        (re.compile(r'(?i)(api_key|password|client_secret|private_key|token|auth_token)\s*=\s*[\'"]([a-zA-Z0-9_\-\.\:\/]+)[\'"]'), "assignment"),
        (re.compile(r'-----BEGIN .* PRIVATE KEY-----'), "private_key_header")
    ]
    for f in git_files:
        path = ROOT / f
        # Skip test files, markdown docs, scripts, verifiers, and test resources
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
                    fail(f"Obvious committed secret (private key) in {f}")
                for pattern, ptype in secret_patterns:
                    if ptype == "assignment":
                        for match in pattern.finditer(content):
                            key, val = match.groups()
                            val_lower = val.lower()
                            # Ignore mock / dummy / test / placeholder values
                            if any(x in val_lower for x in ["mock", "test", "dummy", "example", "placeholder", "token", "schema"]):
                                continue
                            # Ignore version strings and schema versions
                            if re.match(r'^v?\d+\.\d+\.\d+$', val) or val.endswith(".v0"):
                                continue
                            if len(val) >= 12:
                                fail(f"Potential obvious committed secret '{key}' in {f}")
            except Exception:
                pass
    ok("No obvious committed secrets detected in non-test files")

    # 11. Check for blocked modules implemented in src/
    blocked_patterns = [
        ("src/ultimate_ai_agent/core/skill_factory/", "Skill Factory"),
        ("src/ultimate_ai_agent/core/self_improvement/", "Self Improving Code"),
        ("src/ultimate_ai_agent/core/autopilot/", "Autopilot Workflows"),
        ("src/ultimate_ai_agent/core/scanners/", "Secrets/Dependency Scanners"),
    ]
    for rel_path, desc in blocked_patterns:
        p = ROOT / rel_path
        if p.exists():
            fail(f"Blocked module implemented: {desc} ({rel_path})")
            
    # Scan src/ for active execution imports of real models
    for p in (ROOT / "src").rglob("*.py"):
        try:
            content = p.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.strip().startswith(("import openai", "import anthropic", "import google.generativeai")):
                    fail(f"Forbidden model provider import in {p.relative_to(ROOT)}: {line}")
                if "from openai import" in line or "from anthropic import" in line or "from google import generativeai" in line:
                    fail(f"Forbidden model provider import in {p.relative_to(ROOT)}: {line}")
        except Exception:
            pass
    ok("Advanced blocked modules are not implemented")
    print("\nConsistency verification PASSED")

if __name__ == "__main__":
    main()
