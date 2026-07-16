#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verification.ci_command_manifest import (  # noqa: E402
    CI_JOB_GRAPH,
    VERIFICATION_DAG,
    command_registry,
)
from scripts.verification.verification_risk import (  # noqa: E402
    ChangeKind,
    ChangeRecord,
    normalize_repo_path,
)
from scripts.verification.verification_selection import (  # noqa: E402
    VerificationSelection,
    select_verification,
)


SCHEMA_VERSION = "uaa-changed-verification-selection.v2"
FULL_COMMAND_REF = "command-ref:verification:full-local-gate"


@dataclass(frozen=True)
class Selection:
    tier: str
    risk_tier: str
    changed_paths: tuple[str, ...]
    matched_rule_refs: tuple[str, ...]
    selected_unit_refs: tuple[str, ...]
    selected_command_refs: tuple[str, ...]
    selected_test_refs: tuple[str, ...]
    coverage_proof_obligation_refs: tuple[str, ...]
    unknown_paths: tuple[str, ...]
    fallback_reason_refs: tuple[str, ...]
    status: str
    selection_fingerprint: str
    release_gate_equivalent: bool = False

    def payload(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "mode": "local_dev_advisory",
            "tier": self.tier,
            "risk_tier": self.risk_tier,
            "status": self.status,
            "changed_paths": list(self.changed_paths),
            "matched_rule_refs": list(self.matched_rule_refs),
            "selected_unit_refs": list(self.selected_unit_refs),
            "selected_command_refs": list(self.selected_command_refs),
            "selected_test_refs": list(self.selected_test_refs),
            "coverage_proof_obligation_refs": list(
                self.coverage_proof_obligation_refs
            ),
            "unknown_paths": list(self.unknown_paths),
            "fallback_reason_refs": list(self.fallback_reason_refs),
            "selection_fingerprint": self.selection_fingerprint,
            "release_gate_equivalent": self.release_gate_equivalent,
        }


def normalize_path(raw_path: str) -> str:
    return normalize_repo_path(raw_path)


def _safe_repository_root(repo: Path) -> None:
    try:
        metadata = repo.lstat()
    except OSError as exc:
        raise ValueError("VERIFICATION_REPOSITORY_ROOT_INVALID") from exc
    if repo.is_symlink() or not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("VERIFICATION_REPOSITORY_ROOT_INVALID")


def _command_refs(selection: VerificationSelection) -> tuple[str, ...]:
    if selection.full_gate_required:
        return (FULL_COMMAND_REF,)
    units_by_ref = {unit.unit_ref: unit for unit in VERIFICATION_DAG}
    return tuple(
        dict.fromkeys(
            command_ref
            for unit_ref in selection.selected_unit_refs
            for command_ref in units_by_ref[unit_ref].command_refs
        )
    )


def _project_selection(selection: VerificationSelection, *, tier: str) -> Selection:
    unclassified = (
        selection.changed_path_refs
        if "reason-ref:risk:unclassified-path" in selection.escalation_reason_refs
        else ()
    )
    fallback_reasons = (
        selection.escalation_reason_refs if selection.full_gate_required else ()
    )
    return Selection(
        tier=tier,
        risk_tier=selection.risk_tier.value,
        changed_paths=selection.changed_path_refs,
        matched_rule_refs=selection.matched_rule_refs,
        selected_unit_refs=selection.selected_unit_refs,
        selected_command_refs=_command_refs(selection),
        selected_test_refs=selection.selected_test_refs,
        coverage_proof_obligation_refs=selection.coverage_proof_obligation_refs,
        unknown_paths=unclassified,
        fallback_reason_refs=fallback_reasons,
        status=(
            "full_gate_required"
            if selection.full_gate_required
            else "selected"
        ),
        selection_fingerprint=selection.selection_fingerprint,
    )


def select_paths(
    paths: list[str],
    *,
    tier: str = "affected",
    repo: Path = ROOT,
    force_full: bool = False,
) -> Selection:
    if tier not in {"fast", "affected"}:
        raise ValueError("VERIFICATION_SELECTION_TIER_INVALID")
    _safe_repository_root(repo)
    normalized = tuple(sorted({normalize_path(path) for path in paths}))
    if not normalized and not force_full:
        return Selection(
            tier=tier,
            risk_tier="tier_0",
            changed_paths=(),
            matched_rule_refs=(),
            selected_unit_refs=(),
            selected_command_refs=(),
            selected_test_refs=(),
            coverage_proof_obligation_refs=(),
            unknown_paths=(),
            fallback_reason_refs=(),
            status="no_changes",
            selection_fingerprint="0" * 64,
        )
    canonical = select_verification(
        tuple(
            ChangeRecord(ChangeKind.MODIFIED, (path,))
            for path in normalized
        ),
        verification_dag=VERIFICATION_DAG,
        full_unit_refs=tuple(unit.unit_ref for unit in CI_JOB_GRAPH),
        repo=repo,
        force_full=force_full,
    )
    return _project_selection(canonical, tier=tier)


def _parse_name_status(output: bytes) -> tuple[set[str], bool]:
    fields = [field.decode("utf-8") for field in output.split(b"\x00") if field]
    paths: set[str] = set()
    destructive = False
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        path_count = 2 if status.startswith(("R", "C")) else 1
        if index + path_count > len(fields):
            raise ValueError("VERIFICATION_GIT_STATUS_INVALID")
        paths.update(fields[index : index + path_count])
        destructive = destructive or status.startswith(("D", "R", "C", "T"))
        index += path_count
    return paths, destructive


def _git_paths(base_ref: str) -> tuple[list[str], bool]:
    commands = (
        ["git", "diff", "--name-status", "-z", f"{base_ref}...HEAD"],
        ["git", "diff", "--name-status", "-z"],
        ["git", "diff", "--cached", "--name-status", "-z"],
    )
    paths: set[str] = set()
    destructive = False
    for command in commands:
        result = subprocess.run(
            command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            raise ValueError("VERIFICATION_GIT_DIFF_FAILED")
        command_paths, command_destructive = _parse_name_status(result.stdout)
        paths.update(command_paths)
        destructive = destructive or command_destructive
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if untracked.returncode != 0:
        raise ValueError("VERIFICATION_GIT_DIFF_FAILED")
    paths.update(
        item.decode("utf-8") for item in untracked.stdout.split(b"\x00") if item
    )
    return sorted(paths), destructive


def _resolved_argv(
    command_ref: str,
    *,
    selection: Selection,
    base_ref: str,
    temp_root: Path,
) -> tuple[str, ...]:
    command = command_registry()[command_ref]
    argv = tuple(
        token.replace("{base_sha}", base_ref)
        .replace("{repository_sha}", "HEAD")
        .replace("{temp_root}", str(temp_root))
        for token in command.argv
    )
    if argv and argv[0] == ".venv/bin/python":
        argv = (sys.executable, *argv[1:])
    if command_ref == "command:pytest.focused":
        return (
            sys.executable,
            "-m",
            "pytest",
            "-q",
            *selection.selected_test_refs,
        )
    return argv


def execute_selection(selection: Selection, *, base_ref: str = "main") -> int:
    env = {**os.environ, "PYTHONPATH": "src", "PYTHONHASHSEED": "0"}
    if selection.selected_command_refs == (FULL_COMMAND_REF,):
        return subprocess.run(
            ("make", "verify-dev-sharded"),
            cwd=ROOT,
            env=env,
            check=False,
        ).returncode
    with tempfile.TemporaryDirectory(prefix="uaa-affected-verification-") as temp:
        temp_root = Path(temp)
        for command_ref in selection.selected_command_refs:
            result = subprocess.run(
                _resolved_argv(
                    command_ref,
                    selection=selection,
                    base_ref=base_ref,
                    temp_root=temp_root,
                ),
                cwd=ROOT,
                env=env,
                check=False,
            )
            if result.returncode:
                return result.returncode
    return 0


def _blocked_selection(tier: str) -> Selection:
    return Selection(
        tier=tier,
        risk_tier="tier_3",
        changed_paths=(),
        matched_rule_refs=("risk-rule:selector-error-full",),
        selected_unit_refs=tuple(unit.unit_ref for unit in CI_JOB_GRAPH),
        selected_command_refs=(FULL_COMMAND_REF,),
        selected_test_refs=(),
        coverage_proof_obligation_refs=(
            "proof-obligation-ref:complete-pytest",
            "proof-obligation-ref:foundation-gate",
        ),
        unknown_paths=(),
        fallback_reason_refs=("reason-ref:verification:selector-error",),
        status="full_gate_required",
        selection_fingerprint="0" * 64,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Select deterministic fail-closed local verification from the "
            "canonical risk DAG."
        )
    )
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--base-ref", default="main")
    parser.add_argument("--tier", choices=("fast", "affected"), default="affected")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    if args.json and args.execute:
        parser.error("--json and --execute cannot be combined")
    try:
        git_paths, destructive = _git_paths(args.base_ref)
        paths = sorted({*git_paths, *args.path})
        selection = select_paths(
            paths,
            tier=args.tier,
            force_full=destructive,
        )
    except (OSError, UnicodeDecodeError, ValueError):
        selection = _blocked_selection(args.tier)
    if args.json:
        print(json.dumps(selection.payload(), sort_keys=True))
    else:
        print(f"Verification selection: {selection.status}")
        print(f"  risk tier: {selection.risk_tier}")
        for path in selection.changed_paths:
            print(f"  changed: {path}")
        for ref in selection.selected_command_refs:
            print(f"  command: {ref}")
        for ref in selection.selected_test_refs:
            print(f"  test: {ref}")
        if selection.fallback_reason_refs:
            print("  Full local verification is required before merge or release.")
        else:
            print("  Advisory checks do not replace merge or release gates.")
    return (
        execute_selection(selection, base_ref=args.base_ref)
        if args.execute
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
