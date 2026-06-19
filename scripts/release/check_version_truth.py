#!/usr/bin/env python3
"""Verify that current version truth is anchored to VERSION."""

from __future__ import annotations

import argparse
import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-rc\.([1-9]\d*))?$")


@dataclass(frozen=True)
class VersionTruth:
    bare: str

    @property
    def tag(self) -> str:
        return f"v{self.bare}"

    @property
    def archive_key(self) -> str:
        return self.bare.replace(".", "_").replace("-", "_")


def parse_version(value: str) -> VersionTruth:
    stripped = value.strip()
    if stripped.startswith("v"):
        raise ValueError("VERSION must use bare SemVer without a leading v")
    if not VERSION_RE.fullmatch(stripped):
        raise ValueError("VERSION must be MAJOR.MINOR.PATCH or MAJOR.MINOR.PATCH-rc.N")
    major = int(stripped.split(".", 1)[0])
    if major >= 2:
        raise ValueError("v2.x.x is forbidden by the active SemVer policy")
    return VersionTruth(stripped)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require_contains(failures: list[str], rel_path: str, expected: str) -> None:
    path = ROOT / rel_path
    if not path.exists():
        failures.append(f"{rel_path} is missing")
        return
    if expected not in read(path):
        failures.append(f"{rel_path} is missing expected current version text: {expected}")


def package_json_version(rel_path: str) -> str | None:
    path = ROOT / rel_path
    if not path.exists():
        return None
    return json.loads(read(path)).get("version")


def package_lock_root_version(rel_path: str) -> tuple[str | None, str | None]:
    path = ROOT / rel_path
    if not path.exists():
        return None, None
    data = json.loads(read(path))
    return data.get("version"), data.get("packages", {}).get("", {}).get("version")


def verify(root: Path = ROOT) -> list[str]:
    global ROOT
    previous_root = ROOT
    ROOT = root
    try:
        failures: list[str] = []
        version_path = ROOT / "VERSION"
        if not version_path.exists():
            return ["VERSION source of truth is missing"]

        try:
            version = parse_version(read(version_path))
        except ValueError as exc:
            return [str(exc)]

        require_contains(failures, "VERSION.md", f"Current active baseline: **{version.tag}**")
        require_contains(failures, "README.md", f"Current active baseline | **{version.tag}**")
        require_contains(failures, "README.md", f"baseline is **{version.tag}** / `{version.bare}`")
        require_contains(failures, "docs/README.md", f"Current through: {version.tag}")
        release_filename = f"v{version.archive_key}.md"
        require_contains(failures, "docs/README.md", f"docs/release_notes/{release_filename}")
        require_contains(failures, "docs/DOCUMENTATION_INDEX.md", f"Current active baseline: **{version.tag}**")
        require_contains(failures, "docs/DOCUMENTATION_INDEX.md", f"docs/release_notes/{release_filename}")
        require_contains(failures, "docs/canonical/CANONICAL_DOC_MAP.md", f"Current active baseline: **{version.tag}**")
        require_contains(failures, "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md", f"Baseline: {version.tag} / {version.bare}")
        require_contains(failures, "docs/control_center/OPERATOR_SHELL_GAP_MAP.md", f"Baseline: {version.tag} / {version.bare}")
        require_contains(failures, "SECURITY.md", f"active public security posture for {version.tag}")
        require_contains(failures, "AGENTS.md", f"Active baseline: {version.tag}. Package version: {version.bare}.")

        release_notes = ROOT / "docs" / "release_notes" / release_filename
        if not release_notes.exists():
            failures.append(f"current release notes are missing: docs/release_notes/{release_notes.name}")

        archive_dir = ROOT / "docs" / "archive" / "releases" / f"v{version.archive_key}"
        for packet in ("README_IMPORT.md", "master_plan.md"):
            if not (archive_dir / packet).exists():
                failures.append(f"current release packet is missing: docs/archive/releases/v{version.archive_key}/{packet}")

        pyproject = ROOT / "pyproject.toml"
        if not pyproject.exists():
            failures.append("pyproject.toml is missing")
        else:
            project_version = tomllib.loads(read(pyproject)).get("project", {}).get("version")
            if project_version != version.bare:
                failures.append(f"pyproject.toml project.version is {project_version!r}, expected {version.bare!r}")

        init_path = ROOT / "src" / "ultimate_ai_agent" / "__init__.py"
        if not init_path.exists():
            failures.append("src/ultimate_ai_agent/__init__.py is missing")
        else:
            match = re.search(r'(?m)^__version__\s*=\s*[\'"]([^\'"]+)[\'"]', read(init_path))
            if not match or match.group(1) != version.bare:
                found = match.group(1) if match else None
                failures.append(f"__version__ is {found!r}, expected {version.bare!r}")

        app_version = package_json_version("apps/control-center/package.json")
        if app_version is not None and app_version != version.bare:
            failures.append(f"apps/control-center/package.json version is {app_version!r}, expected {version.bare!r}")

        lock_version, lock_root_version = package_lock_root_version("apps/control-center/package-lock.json")
        if lock_version is not None and lock_version != version.bare:
            failures.append(f"apps/control-center/package-lock.json version is {lock_version!r}, expected {version.bare!r}")
        if lock_root_version is not None and lock_root_version != version.bare:
            failures.append(
                "apps/control-center/package-lock.json root package version "
                f"is {lock_root_version!r}, expected {version.bare!r}"
            )

        project_claim_files = [
            "README.md",
            "VERSION.md",
            "docs/README.md",
            "docs/DOCUMENTATION_INDEX.md",
            "docs/canonical/CANONICAL_DOC_MAP.md",
            "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
            "docs/control_center/OPERATOR_SHELL_GAP_MAP.md",
            "SECURITY.md",
            "AGENTS.md",
            "apps/control-center/src/mocks/controlCenterData.ts",
        ]
        for rel_path in project_claim_files:
            path = ROOT / rel_path
            if path.exists():
                content = read(path).lower()
                if "v2.0.0" in content or "baseline: v2" in content:
                    failures.append(f"{rel_path} contains a forbidden current v2 claim")

        return failures
    finally:
        ROOT = previous_root


def self_test() -> None:
    assert parse_version("0.100.0").tag == "v0.100.0"
    assert parse_version("1.0.0-rc.1").archive_key == "1_0_0_rc_1"
    for bad in ("v0.100.0", "2.0.0", "1.0", "1.0.0-beta.1", "1.0.0-rc.0"):
        try:
            parse_version(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected invalid version: {bad}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="Run internal parser checks.")
    args = parser.parse_args(argv)

    if args.self_test:
        self_test()
        print("OK: check_version_truth self-test passed")
        return 0

    failures = verify()
    if failures:
        print("Version truth verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("OK: VERSION, package metadata, current docs, and release packets agree.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
