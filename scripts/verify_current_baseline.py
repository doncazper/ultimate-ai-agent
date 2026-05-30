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
    
    version_content = version_file.read_text()
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
        
    pyproject_content = pyproject_file.read_text()
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
        
    init_content = init_file.read_text()
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
        
    readme_content = readme_file.read_text()
    if f"v{version}" not in readme_content:
        fail(f"README.md does not mention the active baseline v{version}")
        
    # Check that it doesn't mention older version_IMPORT files where it should mention current
    old_version = "0.5.8"
    if f"README_IMPORT_v{old_version.replace('.', '_')}.md" in readme_content:
        fail(f"README.md contains legacy start file README_IMPORT_v{old_version.replace('.', '_')}.md")
    if f"ultimate_ai_agent_master_plan_v{old_version.replace('.', '_')}.md" in readme_content:
        fail(f"README.md contains legacy start file ultimate_ai_agent_master_plan_v{old_version.replace('.', '_')}.md")
        
    # Check that current start files are listed
    if f"README_IMPORT_v{version_with_underscores}.md" not in readme_content:
        fail(f"README.md is missing active start file README_IMPORT_v{version_with_underscores}.md")
    if f"ultimate_ai_agent_master_plan_v{version_with_underscores}.md" not in readme_content:
        fail(f"README.md is missing active start file ultimate_ai_agent_master_plan_v{version_with_underscores}.md")
    ok("README.md active baseline references are consistent")
    
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
    
    # 8. Verify no tracked egg-info files or directories in git
    try:
        git_files_raw = subprocess.check_output(["git", "ls-files"], text=True)
        git_files = git_files_raw.splitlines()
        for f in git_files:
            if ".egg-info" in f:
                fail(f"A generated egg-info file is currently tracked in git: {f}")
    except subprocess.SubprocessError as e:
        print(f"Warning: Failed to run git ls-files ({e}). Skipping tracked egg-info verification.")
        
    ok("No generated egg-info files are tracked in git")
    print("\nConsistency verification PASSED")

if __name__ == "__main__":
    main()
