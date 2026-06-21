#!/usr/bin/env python3
"""Dry-run-first local version helper.

This local helper never creates commits, tags, pushes, network calls, or remote
mutations. It previews version changes by default and only edits known local
files when --apply --yes are both provided.
"""
from __future__ import annotations


import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SEMVER_RE = re.compile(r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-rc\.(?P<rc>0|[1-9]\d*))?$")


@dataclass(frozen=True)
class Version:
    major: int
    minor: int
    patch: int
    rc: int | None = None

    @classmethod
    def parse(cls, value: str) -> "Version":
        match = SEMVER_RE.fullmatch(value)
        if not match:
            raise ValueError(f"Invalid bare SemVer: {value!r}")
        return cls(
            int(match.group("major")),
            int(match.group("minor")),
            int(match.group("patch")),
            int(match.group("rc")) if match.group("rc") is not None else None,
        )

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.rc is not None:
            return f"{base}-rc.{self.rc}"
        return base


def next_version(current: Version, kind: str, yes: bool) -> Version:
    if kind == "docs":
        if current.major == 0 and current.minor == 0:
            return Version(0, 0, current.patch + 1)
        return Version(current.major, current.minor, current.patch + 1)
    if kind == "first-code":
        if (current.major, current.minor, current.patch) >= (0, 1, 0):
            raise ValueError("--kind first-code is only valid before 0.1.0")
        return Version(0, 1, 0)
    if kind == "patch":
        return Version(current.major, current.minor, current.patch + 1)
    if kind == "minor":
        return Version(current.major, current.minor + 1, 0)
    if kind == "rc":
        if current.major == 1 and current.minor == 0 and current.patch == 0 and current.rc is not None:
            return Version(1, 0, 0, current.rc + 1)
        if not yes:
            raise ValueError("--kind rc requires --yes when starting the 1.0.0-rc sequence")
        return Version(1, 0, 0, 1)
    if kind == "stable":
        if not (current.major == 1 and current.minor == 0 and current.patch == 0 and current.rc is not None):
            raise ValueError("--kind stable only promotes from 1.0.0-rc.N")
        if not yes:
            raise ValueError("--kind stable requires --yes")
        return Version(1, 0, 0)
    raise ValueError(f"Unknown kind: {kind}")


def replace_literal(path: Path, old: str, new: str) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    updated = text.replace(old, new)
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def apply_known_updates(old: Version, new: Version) -> list[str]:
    old_bare = str(old)
    new_bare = str(new)
    old_tag = f"v{old_bare}"
    new_tag = f"v{new_bare}"
    changed: list[str] = []
    for rel in [
        "VERSION",
        "VERSION.md",
        "README.md",
        "docs/README.md",
        "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
        "pyproject.toml",
        "src/ultimate_ai_agent/__init__.py",
        "apps/control-center/package.json",
    ]:
        path = ROOT / rel
        before_exists = path.exists()
        touched = False
        if rel == "VERSION":
            path.write_text(f"{new_bare}\n", encoding="utf-8")
            touched = True
        else:
            touched = replace_literal(path, old_tag, new_tag) or touched
            touched = replace_literal(path, old_bare, new_bare) or touched
        if touched or not before_exists and path.exists():
            changed.append(rel)
    return changed


def load_current() -> Version:
    path = ROOT / "VERSION"
    if not path.exists():
        raise ValueError("VERSION is missing; create it in an approved repair phase before using the bump helper")
    return Version.parse(path.read_text(encoding="utf-8").strip())


def self_test() -> int:
    assert str(next_version(Version(0, 0, 1), "docs", False)) == "0.0.2"
    assert str(next_version(Version(0, 0, 9), "first-code", False)) == "0.1.0"
    assert str(next_version(Version(0, 101, 0), "minor", False)) == "0.102.0"
    assert str(next_version(Version(1, 0, 0, 1), "rc", False)) == "1.0.0-rc.2"
    assert str(next_version(Version(1, 0, 0, 3), "stable", True)) == "1.0.0"
    print("bump_version.py self-test passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=["docs", "first-code", "patch", "minor", "rc", "stable"], default="patch")
    parser.add_argument("--apply", action="store_true", help="write local file edits; never commits, tags, or pushes")
    parser.add_argument("--yes", action="store_true", help="required for rc/stable transitions and apply mode")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.apply and not args.yes:
        print("FAIL: --apply requires --yes")
        return 1

    try:
        current = load_current()
        new = next_version(current, args.kind, args.yes)
    except ValueError as exc:
        print(f"FAIL: {exc}")
        return 1

    print(f"old version: {current}")
    print(f"new version: {new}")
    print(f"proposed tag: v{new}")
    print("git/tag/push behavior: disabled")
    if not args.apply:
        print("dry run: no files changed")
        return 0

    changed = apply_known_updates(current, new)
    print("files changed:")
    for rel in changed:
        print(f"- {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
