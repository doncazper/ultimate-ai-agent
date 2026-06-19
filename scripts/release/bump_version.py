#!/usr/bin/env python3
"""Bump Ultimate AI Agent versions without bypassing the SemVer policy."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-rc\.([1-9]\d*))?$")


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int
    rc: int | None = None

    @classmethod
    def parse(cls, value: str) -> "Version":
        stripped = value.strip()
        if stripped.startswith("v"):
            raise ValueError("use bare SemVer without a leading v")
        match = VERSION_RE.fullmatch(stripped)
        if not match:
            raise ValueError("expected MAJOR.MINOR.PATCH or MAJOR.MINOR.PATCH-rc.N")
        major, minor, patch, rc = match.groups()
        parsed = cls(int(major), int(minor), int(patch), int(rc) if rc else None)
        if parsed.major >= 2:
            raise ValueError("v2.x.x is forbidden before a real v1 stable history")
        return parsed

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.rc is not None:
            return f"{base}-rc.{self.rc}"
        return base

    @property
    def tag(self) -> str:
        return f"v{self}"

    @property
    def key(self) -> str:
        return str(self).replace(".", "_").replace("-", "_")


def next_version(current: Version, kind: str, *, approved: bool = False) -> Version:
    if kind == "docs":
        return Version(current.major, current.minor, current.patch + 1)
    if kind == "first-code":
        if current.major != 0 or current.minor != 0:
            raise ValueError("first-code is only valid before v0.1.0 exists")
        return Version(0, 1, 0)
    if kind == "patch":
        if current.rc is not None:
            raise ValueError("patch bumps are not allowed from a release candidate")
        return Version(current.major, current.minor, current.patch + 1)
    if kind == "minor":
        if current.rc is not None:
            raise ValueError("minor bumps are not allowed from a release candidate")
        if current.major >= 1:
            raise ValueError("post-v1 minor bumps require a dedicated release policy update")
        return Version(0, current.minor + 1, 0)
    if kind == "rc":
        if current == Version(1, 0, 0, None):
            raise ValueError("v1.0.0 is already final")
        if current.major == 1 and current.minor == 0 and current.patch == 0 and current.rc is not None:
            return Version(1, 0, 0, current.rc + 1)
        if not approved:
            raise ValueError("starting the v1.0.0 release-candidate lane requires --yes")
        return Version(1, 0, 0, 1)
    if kind == "stable":
        if current.major != 1 or current.minor != 0 or current.patch != 0 or current.rc is None:
            raise ValueError("stable promotion must start from v1.0.0-rc.N")
        if not approved:
            raise ValueError("final v1.0.0 stable promotion requires --yes")
        return Version(1, 0, 0)
    raise ValueError(f"unknown bump kind: {kind}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, content: str, *, dry_run: bool, changed: list[str]) -> None:
    rel = path.relative_to(ROOT).as_posix()
    if path.exists() and read(path) == content:
        return
    changed.append(rel)
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def replace_in_file(path: Path, replacements: list[tuple[str, str]], *, dry_run: bool, changed: list[str]) -> None:
    if not path.exists():
        return
    content = read(path)
    updated = content
    for old, new in replacements:
        updated = updated.replace(old, new)
    write(path, updated, dry_run=dry_run, changed=changed)


def update_json_version(path: Path, version: Version, *, dry_run: bool, changed: list[str], lockfile: bool = False) -> None:
    if not path.exists():
        return
    data = json.loads(read(path))
    data["version"] = str(version)
    if lockfile:
        data.setdefault("packages", {}).setdefault("", {})["version"] = str(version)
    write(path, json.dumps(data, indent=2) + "\n", dry_run=dry_run, changed=changed)


def maybe_rename(old_path: Path, new_path: Path, *, dry_run: bool, changed: list[str]) -> Path:
    if old_path == new_path:
        return old_path
    if old_path.exists():
        changed.append(f"{old_path.relative_to(ROOT).as_posix()} -> {new_path.relative_to(ROOT).as_posix()}")
        if not dry_run:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            old_path.rename(new_path)
        return new_path
    return new_path


def update_versions(old: Version, new: Version, *, dry_run: bool) -> list[str]:
    changed: list[str] = []
    old_key = old.key
    new_key = new.key
    replacements = [
        (old.tag, new.tag),
        (str(old), str(new)),
        (f"v{old_key}", f"v{new_key}"),
        (old_key, new_key),
    ]

    release_note = maybe_rename(
        ROOT / "docs" / "release_notes" / f"v{old_key}.md",
        ROOT / "docs" / "release_notes" / f"v{new_key}.md",
        dry_run=dry_run,
        changed=changed,
    )
    maybe_rename(
        ROOT / "docs" / "implementation" / f"foundation_gate_implementation_plan_v{old_key}.md",
        ROOT / "docs" / "implementation" / f"foundation_gate_implementation_plan_v{new_key}.md",
        dry_run=dry_run,
        changed=changed,
    )
    maybe_rename(
        ROOT / "docs" / "archive" / "releases" / f"v{old_key}",
        ROOT / "docs" / "archive" / "releases" / f"v{new_key}",
        dry_run=dry_run,
        changed=changed,
    )

    write(ROOT / "VERSION", f"{new}\n", dry_run=dry_run, changed=changed)

    text_paths = [
        "VERSION.md",
        "README.md",
        "docs/README.md",
        "docs/DOCUMENTATION_INDEX.md",
        "docs/canonical/CANONICAL_DOC_MAP.md",
        "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
        "docs/control_center/OPERATOR_SHELL_GAP_MAP.md",
        "SECURITY.md",
        "AGENTS.md",
        "apps/control-center/src/mocks/controlCenterData.ts",
        f"docs/release_notes/v{new_key}.md",
        f"docs/archive/releases/v{new_key}/README_IMPORT.md",
        f"docs/archive/releases/v{new_key}/master_plan.md",
        f"docs/implementation/foundation_gate_implementation_plan_v{new_key}.md",
    ]
    for rel_path in text_paths:
        replace_in_file(ROOT / rel_path, replacements, dry_run=dry_run, changed=changed)

    pyproject = ROOT / "pyproject.toml"
    if pyproject.exists():
        content = read(pyproject)
        updated = re.sub(r'(?m)^(version\s*=\s*)["\'][^"\']+["\']', rf'\1"{new}"', content, count=1)
        write(pyproject, updated, dry_run=dry_run, changed=changed)

    init_file = ROOT / "src" / "ultimate_ai_agent" / "__init__.py"
    if init_file.exists():
        content = read(init_file)
        updated = re.sub(r'(?m)^__version__\s*=\s*["\'][^"\']+["\']', f'__version__ = "{new}"', content)
        write(init_file, updated, dry_run=dry_run, changed=changed)

    update_json_version(ROOT / "apps" / "control-center" / "package.json", new, dry_run=dry_run, changed=changed)
    update_json_version(
        ROOT / "apps" / "control-center" / "package-lock.json",
        new,
        dry_run=dry_run,
        changed=changed,
        lockfile=True,
    )

    if not release_note.exists() and not dry_run:
        write(
            release_note,
            (
                f"# {new.tag}\n\n"
                "Status: local pre-1.0 version bump snapshot.\n\n"
                "This release note records version currentness only. It does not grant "
                "production authority, public distribution, provider/model authority, "
                "shell authority, connector writes, plugin runtime import, or broad autonomy.\n"
            ),
            dry_run=dry_run,
            changed=changed,
        )

    return changed


def current_version() -> Version:
    return Version.parse(read(ROOT / "VERSION"))


def create_tag(version: Version, *, dry_run: bool) -> None:
    existing = subprocess.run(["git", "tag", "--list", version.tag], cwd=ROOT, text=True, capture_output=True, check=True)
    if existing.stdout.strip():
        raise ValueError(f"local tag already exists: {version.tag}")
    message = f"{version.tag} pre-1.0 version snapshot"
    command = ["git", "tag", "-a", version.tag, "-m", message]
    if dry_run:
        print("DRY RUN:", " ".join(command))
        return
    subprocess.run(command, cwd=ROOT, check=True)


def self_test() -> None:
    assert Version.parse("0.0.1") == Version(0, 0, 1)
    assert str(next_version(Version.parse("0.0.0"), "docs")) == "0.0.1"
    assert str(next_version(Version.parse("0.0.9"), "first-code")) == "0.1.0"
    assert str(next_version(Version.parse("0.100.0"), "patch")) == "0.100.1"
    assert str(next_version(Version.parse("0.100.0"), "minor")) == "0.101.0"
    assert str(next_version(Version.parse("0.100.0"), "rc", approved=True)) == "1.0.0-rc.1"
    assert str(next_version(Version.parse("1.0.0-rc.1"), "rc")) == "1.0.0-rc.2"
    assert str(next_version(Version.parse("1.0.0-rc.2"), "stable", approved=True)) == "1.0.0"
    for bad in ("v0.1.0", "2.0.0", "1.0", "1.0.0-beta.1"):
        try:
            Version.parse(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected invalid version: {bad}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=["docs", "first-code", "patch", "minor", "rc", "stable"])
    parser.add_argument("--dry-run", action="store_true", help="Show the bump without writing files or creating tags.")
    parser.add_argument("--tag", action="store_true", help="Create a local annotated tag for the new version.")
    parser.add_argument("--yes", action="store_true", help="Confirm an RC or final stable promotion gate.")
    parser.add_argument("--self-test", action="store_true", help="Run internal SemVer rule tests.")
    args = parser.parse_args(argv)

    if args.self_test:
        self_test()
        print("OK: bump_version self-test passed")
        return 0
    if not args.kind:
        parser.error("--kind is required unless --self-test is used")

    old = current_version()
    try:
        new = next_version(old, args.kind, approved=args.yes)
    except ValueError as exc:
        print(f"Version bump rejected: {exc}")
        return 1

    changed = update_versions(old, new, dry_run=args.dry_run)
    print(f"Current version: {old.tag} / {old}")
    print(f"Next version: {new.tag} / {new}")
    if changed:
        print("Changed files:")
        for rel_path in sorted(set(changed)):
            print(f"- {rel_path}")
    else:
        print("No file changes were needed.")

    if args.tag:
        try:
            create_tag(new, dry_run=args.dry_run)
        except ValueError as exc:
            print(f"Tag creation rejected: {exc}")
            return 1
        print(f"Local annotated tag prepared: {new.tag}")
    else:
        print(f"Local tag not created. Use --tag to create {new.tag}.")

    print("Remote push is intentionally not performed by this tool.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
