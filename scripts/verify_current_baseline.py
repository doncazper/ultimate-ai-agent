#!/usr/bin/env python3
import sys
import re
from pathlib import Path

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

    # 8.7 Check M3.5 secret/provider files existence
    m35_files = [
        "src/ultimate_ai_agent/core/secrets/__init__.py",
        "src/ultimate_ai_agent/core/secrets/enums.py",
        "src/ultimate_ai_agent/core/secrets/credentials.py",
        "src/ultimate_ai_agent/core/secrets/handles.py",
        "src/ultimate_ai_agent/core/secrets/broker.py",
        "src/ultimate_ai_agent/core/secrets/redaction.py",
        "src/ultimate_ai_agent/core/secrets/validation.py",
        "src/ultimate_ai_agent/core/providers/__init__.py",
        "src/ultimate_ai_agent/core/providers/enums.py",
        "src/ultimate_ai_agent/core/providers/manifests.py",
        "src/ultimate_ai_agent/core/providers/registry.py",
        "src/ultimate_ai_agent/core/providers/requests.py",
        "src/ultimate_ai_agent/core/providers/results.py",
        "src/ultimate_ai_agent/core/providers/resolver.py",
        "src/ultimate_ai_agent/core/providers/normalization.py",
        "src/ultimate_ai_agent/core/providers/validation.py",
    ]
    for rel_path in m35_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M3.5 file is missing: {rel_path}")
    ok("All M3.5 secret broker and provider registry files exist")

    # 8.8 Check M4 memory/file manager files existence
    m4_files = [
        "src/ultimate_ai_agent/core/memory/__init__.py",
        "src/ultimate_ai_agent/core/memory/enums.py",
        "src/ultimate_ai_agent/core/memory/records.py",
        "src/ultimate_ai_agent/core/memory/requests.py",
        "src/ultimate_ai_agent/core/memory/decisions.py",
        "src/ultimate_ai_agent/core/memory/store.py",
        "src/ultimate_ai_agent/core/memory/retrieval.py",
        "src/ultimate_ai_agent/core/memory/policies.py",
        "src/ultimate_ai_agent/core/memory/validation.py",
        "src/ultimate_ai_agent/core/memory/redaction.py",
        "src/ultimate_ai_agent/core/files/__init__.py",
        "src/ultimate_ai_agent/core/files/enums.py",
        "src/ultimate_ai_agent/core/files/refs.py",
        "src/ultimate_ai_agent/core/files/operations.py",
        "src/ultimate_ai_agent/core/files/manager.py",
        "src/ultimate_ai_agent/core/files/diffs.py",
        "src/ultimate_ai_agent/core/files/snapshots.py",
        "src/ultimate_ai_agent/core/files/policies.py",
        "src/ultimate_ai_agent/core/files/validation.py",
        "src/ultimate_ai_agent/core/files/rollback.py",
    ]
    for rel_path in m4_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M4 file is missing: {rel_path}")
    ok("All M4 memory service and file manager files exist")

    # 8.9 Check M4.5 truth source/evidence governance files existence
    m45_files = [
        "src/ultimate_ai_agent/core/truth/__init__.py",
        "src/ultimate_ai_agent/core/truth/enums.py",
        "src/ultimate_ai_agent/core/truth/sources.py",
        "src/ultimate_ai_agent/core/truth/grounding.py",
        "src/ultimate_ai_agent/core/truth/claims.py",
        "src/ultimate_ai_agent/core/truth/evidence.py",
        "src/ultimate_ai_agent/core/truth/conflicts.py",
        "src/ultimate_ai_agent/core/truth/retrieval_log.py",
        "src/ultimate_ai_agent/core/truth/freshness.py",
        "src/ultimate_ai_agent/core/truth/router.py",
        "src/ultimate_ai_agent/core/truth/validation.py",
    ]
    for rel_path in m45_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M4.5 file is missing: {rel_path}")
    ok("All M4.5 truth source and evidence governance files exist")

    # 8.10 Check M5 kernel files existence
    m5_files = [
        "src/ultimate_ai_agent/core/kernel/__init__.py",
        "src/ultimate_ai_agent/core/kernel/enums.py",
        "src/ultimate_ai_agent/core/kernel/requests.py",
        "src/ultimate_ai_agent/core/kernel/results.py",
        "src/ultimate_ai_agent/core/kernel/receipts.py",
        "src/ultimate_ai_agent/core/kernel/runner.py",
        "src/ultimate_ai_agent/core/kernel/validation.py",
    ]
    for rel_path in m5_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M5 file is missing: {rel_path}")
    ok("All M5 minimum lovable kernel files exist")

    # 8.11 Check M6 Foundation Gate files existence
    m6_files = [
        "src/ultimate_ai_agent/core/gate/__init__.py",
        "src/ultimate_ai_agent/core/gate/enums.py",
        "src/ultimate_ai_agent/core/gate/criteria.py",
        "src/ultimate_ai_agent/core/gate/reports.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/gate/shadow_replay.py",
        "src/ultimate_ai_agent/core/gate/validation.py",
        "scripts/run_foundation_gate.py",
        "reports/foundation_gate/sample_foundation_gate_report.json",
        "reports/foundation_gate/sample_foundation_gate_report.md",
    ]
    for rel_path in m6_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M6 Foundation Gate file is missing: {rel_path}")
    ok("All M6 Foundation Gate and shadow replay files exist")

    # 8.12 Check M7 model router and cost/resource governor files existence
    m7_files = [
        "src/ultimate_ai_agent/core/model_router/__init__.py",
        "src/ultimate_ai_agent/core/model_router/enums.py",
        "src/ultimate_ai_agent/core/model_router/profiles.py",
        "src/ultimate_ai_agent/core/model_router/policies.py",
        "src/ultimate_ai_agent/core/model_router/requests.py",
        "src/ultimate_ai_agent/core/model_router/decisions.py",
        "src/ultimate_ai_agent/core/model_router/router.py",
        "src/ultimate_ai_agent/core/model_router/validation.py",
        "src/ultimate_ai_agent/core/costs/__init__.py",
        "src/ultimate_ai_agent/core/costs/enums.py",
        "src/ultimate_ai_agent/core/costs/budgets.py",
        "src/ultimate_ai_agent/core/costs/estimates.py",
        "src/ultimate_ai_agent/core/costs/decisions.py",
        "src/ultimate_ai_agent/core/costs/governor.py",
        "src/ultimate_ai_agent/core/costs/validation.py",
    ]
    for rel_path in m7_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M7 file is missing: {rel_path}")
    ok("All M7 model router and cost/resource governor files exist")
    
    # 9. Enforce scans by delegating to verify_all
    try:
        from verify_all import run_static_scans
    except Exception as exc:
        fail(f"Could not import verify_all scan helpers: {exc}")
    run_static_scans()

    print("\nConsistency verification PASSED")

if __name__ == "__main__":
    main()
