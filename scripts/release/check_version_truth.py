#!/usr/bin/env python3
"""Read-only version truth checker.

This local verifier validates current-version claims against VERSION without
performing writes, network calls, git operations, tag operations, or commits.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-rc\.(0|[1-9]\d*))?$")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_version(root: Path) -> str:
    version_path = root / "VERSION"
    if not version_path.exists():
        raise ValueError("VERSION is missing")
    version = version_path.read_text(encoding="utf-8").strip()
    if not SEMVER_RE.fullmatch(version):
        raise ValueError(f"VERSION is not bare SemVer: {version!r}")
    return version


def check_contains(path: str, expected: str, failures: list[str]) -> None:
    full = ROOT / path
    if not full.exists():
        failures.append(f"{path} is missing")
        return
    text = read_text(full)
    if expected not in text:
        failures.append(f"{path} does not contain {expected!r}")


def check_no_current_v2(path: str, failures: list[str]) -> None:
    full = ROOT / path
    if not full.exists():
        return
    text = read_text(full)
    forbidden_patterns = [
        r"Current active baseline:\s*\*\*v2\.0\.0\*\*",
        r"Active baseline\s*\|\s*\*\*v2\.0\.0\*\*",
        r"product/package baseline is `v2\.0\.0`",
        r"Baseline:\s*v2\.0\.0\s*/\s*2\.0\.0",
    ]
    for pattern in forbidden_patterns:
        if re.search(pattern, text):
            failures.append(f"{path} still contains current v2.0.0 claim matching {pattern!r}")


def run_checks() -> int:
    failures: list[str] = []
    try:
        version = load_version(ROOT)
    except ValueError as exc:
        print(f"FAIL: {exc}")
        return 1

    v_version = f"v{version}"
    check_contains("VERSION.md", v_version, failures)
    check_contains("README.md", v_version, failures)
    check_contains("docs/README.md", v_version, failures)
    check_contains("docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md", v_version, failures)
    check_contains("pyproject.toml", f'version = "{version}"', failures)
    check_contains("src/ultimate_ai_agent/__init__.py", f'__version__ = "{version}"', failures)

    for path in [
        "AGENTS.md",
        "VERSION.md",
        "README.md",
        "docs/README.md",
        "docs/DOCUMENTATION_INDEX.md",
        "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
        "SECURITY.md",
    ]:
        check_no_current_v2(path, failures)

    if failures:
        print("Version truth check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Version truth check passed for v{version}.")
    return 0


def self_test() -> int:
    examples = ["0.0.1", "0.102.0", "1.0.0-rc.1"]
    bad = ["v0.1.0", "1.0", "1.0.0-alpha", "01.0.0"]
    for value in examples:
        assert SEMVER_RE.fullmatch(value), value
    for value in bad:
        assert not SEMVER_RE.fullmatch(value), value
    print("check_version_truth.py self-test passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    return run_checks()


if __name__ == "__main__":
    sys.exit(main())
