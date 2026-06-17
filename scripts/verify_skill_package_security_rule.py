#!/usr/bin/env python3
"""Verify that the Skill Package Security Rule is present in the v0.5.8 docs."""

from pathlib import Path
import sys

import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]

# Dynamically resolve active version for versioned implementation plan check
version_file = ROOT / "VERSION.md"
active_impl_plan = "docs/implementation/foundation_gate_implementation_plan_v0_5_8.md"
if version_file.exists():
    version_content = version_file.read_text(encoding="utf-8")
    version_match = re.search(r"Current active baseline:\s*\*\*v?(\d+\.\d+\.\d+)\*\*", version_content)
    if version_match:
        ver = version_match.group(1).replace(".", "_")
        active_impl_plan = f"docs/implementation/foundation_gate_implementation_plan_v{ver}.md"

REQUIRED_FILES = [
    "docs/canonical/23_security_threat_model.md",
    "docs/canonical/30_agent_constitution.md",
    "docs/canonical/32_capability_registry_and_dependency_graph.md",
    active_impl_plan,
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

tracked_egg_info = []
try:
    tracked_files = subprocess.check_output(
        ["git", "ls-files", "src/*.egg-info", "src/*.egg-info/**"],
        cwd=ROOT,
        text=True,
        stderr=subprocess.DEVNULL,
    ).splitlines()
    tracked_egg_info = [path for path in tracked_files if ".egg-info" in path]
except (subprocess.CalledProcessError, FileNotFoundError):
    tracked_egg_info = []

if tracked_egg_info:
    print("FAIL generated egg-info files should not be committed:")
    for path in tracked_egg_info:
        print(f"  - {path}")
    ok = False
else:
    print("OK no generated egg-info files are tracked in git")

if not ok:
    sys.exit(1)

print("Skill package security cleanup verification PASSED")
