#!/usr/bin/env python3
"""Verify that the Skill Package Security Rule is present in the v0.5.8 docs."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "docs/canonical/23_security_threat_model.md",
    "docs/canonical/30_agent_constitution.md",
    "docs/canonical/32_capability_registry_and_dependency_graph.md",
    "docs/implementation/foundation_gate_implementation_plan_v0_5_8.md",
    "docs/backlog/external_agent_tooling_watchlist.md",
]

REQUIRED_PHRASES = [
    "All skills are untrusted packages by default",
    "a manifest",
    "declared permissions",
    "source/provenance metadata",
    "static review",
    "sandbox test execution",
    "Tool Broker permission mapping",
    "Event Ledger logging",
    "version pinning",
    "revocation/disable support",
    "human approval for high-risk capabilities",
]

ok = True

for rel in REQUIRED_FILES:
    path = ROOT / rel
    if not path.exists():
        print(f"FAIL missing required file: {rel}")
        ok = False
    else:
        print(f"OK file exists: {rel}")

for rel in REQUIRED_FILES[:4]:
    path = ROOT / rel
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8")
    for phrase in REQUIRED_PHRASES:
        if phrase not in text:
            print(f"FAIL {rel} missing phrase: {phrase}")
            ok = False
    if "Skill Package Security Rule" in text:
        print(f"OK {rel} includes Skill Package Security Rule section")
    else:
        print(f"FAIL {rel} missing Skill Package Security Rule section")
        ok = False

pyproject = ROOT / "pyproject.toml"
if pyproject.exists():
    pytext = pyproject.read_text(encoding="utf-8")
    for dep in ["jsonschema", "ruff"]:
        if dep not in pytext:
            print(f"FAIL pyproject.toml missing dev dependency: {dep}")
            ok = False
        else:
            print(f"OK pyproject.toml includes {dep}")
else:
    print("FAIL missing pyproject.toml")
    ok = False

gitignore = ROOT / ".gitignore"
if gitignore.exists():
    gi = gitignore.read_text(encoding="utf-8")
    if "*.egg-info/" in gi or ".egg-info/" in gi:
        print("OK .gitignore ignores egg-info")
    else:
        print("FAIL .gitignore should ignore egg-info")
        ok = False

egg_info_dirs = list((ROOT / "src").glob("*.egg-info")) if (ROOT / "src").exists() else []
if egg_info_dirs:
    print("FAIL generated egg-info directories should not be committed:")
    for p in egg_info_dirs:
        print(f"  - {p.relative_to(ROOT)}")
    ok = False
else:
    print("OK no generated egg-info directories under src")

if not ok:
    sys.exit(1)

print("Skill package security cleanup verification PASSED")
