#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import stat
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verification.ci_command_manifest import (  # noqa: E402
    CI_JOB_GRAPH,
    build_plan,
)
from scripts.verification.verification_contracts import (  # noqa: E402
    SHA_PATTERN,
    VerificationPlan,
)
from scripts.verification.verification_risk import (  # noqa: E402
    ChangeKind,
    ChangeRecord,
    classify_changes,
    normalize_repo_path,
    unit_refs_for_selection,
)


MAX_CHANGED_RECORDS = 512
STATUS_KINDS = {
    "A": ChangeKind.ADDED,
    "M": ChangeKind.MODIFIED,
    "D": ChangeKind.DELETED,
    "T": ChangeKind.TYPE_CHANGED,
    "U": ChangeKind.UNKNOWN,
    "X": ChangeKind.UNKNOWN,
    "B": ChangeKind.UNKNOWN,
}


def _git(repo: Path, *args: str, text: bool = True) -> str | bytes:
    completed = subprocess.run(
        ("git", *args),
        cwd=repo,
        check=False,
        capture_output=True,
        text=text,
        timeout=30,
    )
    if completed.returncode != 0:
        raise ValueError("VERIFICATION_GIT_QUERY_FAILED")
    return completed.stdout


def _validate_repository(repo: Path, *, head_sha: str) -> None:
    if repo.is_symlink() or not repo.is_dir():
        raise ValueError("VERIFICATION_REPOSITORY_PATH_UNSAFE")
    if SHA_PATTERN.fullmatch(head_sha) is None:
        raise ValueError("VERIFICATION_SHA_INVALID")
    if _git(repo, "rev-parse", "HEAD") != f"{head_sha}\n":
        raise ValueError("VERIFICATION_HEAD_MISMATCH")
    if _git(repo, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("VERIFICATION_WORKTREE_NOT_CLEAN")


def _validate_commit(repo: Path, sha: str) -> None:
    if SHA_PATTERN.fullmatch(sha) is None:
        raise ValueError("VERIFICATION_SHA_INVALID")
    _git(repo, "cat-file", "-e", f"{sha}^{{commit}}")


def _validate_comparison(
    repo: Path,
    *,
    base_sha: str,
    head_sha: str,
    force_full: bool,
) -> None:
    if base_sha == head_sha:
        if force_full:
            return
        raise ValueError("VERIFICATION_BASE_EQUALS_HEAD")
    completed = subprocess.run(
        ("git", "merge-base", "--is-ancestor", base_sha, head_sha),
        cwd=repo,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=30,
    )
    if completed.returncode != 0:
        raise ValueError("VERIFICATION_BASE_NOT_ANCESTOR")


def parse_name_status(raw: bytes) -> tuple[ChangeRecord, ...]:
    tokens = raw.split(b"\0")
    if tokens and tokens[-1] == b"":
        tokens.pop()
    records: list[ChangeRecord] = []
    index = 0
    try:
        while index < len(tokens):
            status_token = tokens[index].decode("ascii")
            index += 1
            if status_token.startswith(("R", "C")):
                if len(status_token) < 2 or not status_token[1:].isdigit():
                    raise ValueError("VERIFICATION_DIFF_STATUS_INVALID")
                old_path = normalize_repo_path(tokens[index].decode("utf-8"))
                new_path = normalize_repo_path(tokens[index + 1].decode("utf-8"))
                index += 2
                kind = (
                    ChangeKind.RENAMED
                    if status_token.startswith("R")
                    else ChangeKind.COPIED
                )
                records.append(ChangeRecord(kind, (old_path, new_path)))
                continue
            kind = STATUS_KINDS.get(status_token)
            if kind is None:
                raise ValueError("VERIFICATION_DIFF_STATUS_INVALID")
            path = normalize_repo_path(tokens[index].decode("utf-8"))
            index += 1
            records.append(ChangeRecord(kind, (path,)))
    except (IndexError, UnicodeDecodeError) as exc:
        raise ValueError("VERIFICATION_DIFF_RECORD_INVALID") from exc
    if len(records) > MAX_CHANGED_RECORDS:
        raise ValueError("VERIFICATION_DIFF_RECORD_BOUND_EXCEEDED")
    return tuple(records)


def changed_records(
    repo: Path, *, base_sha: str, head_sha: str
) -> tuple[ChangeRecord, ...]:
    raw = _git(
        repo,
        "diff",
        "--name-status",
        "-z",
        "--find-renames",
        base_sha,
        head_sha,
        "--",
        text=False,
    )
    assert isinstance(raw, bytes)
    return parse_name_status(raw)


def _head_path_is_unsafe(repo: Path, *, head_sha: str, path_ref: str) -> bool:
    raw = _git(repo, "ls-tree", "-z", head_sha, "--", path_ref, text=False)
    assert isinstance(raw, bytes)
    if not raw:
        return True
    entries = [entry for entry in raw.split(b"\0") if entry]
    if len(entries) != 1:
        return True
    try:
        metadata, encoded_path = entries[0].split(b"\t", maxsplit=1)
        mode, object_kind, _object_ref = metadata.decode("ascii").split(" ", maxsplit=2)
        observed_path = encoded_path.decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return True
    if (
        observed_path != path_ref
        or object_kind != "blob"
        or mode not in {"100644", "100755"}
    ):
        return True
    worktree_path = repo / path_ref
    try:
        info = worktree_path.lstat()
    except FileNotFoundError:
        return True
    return not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode)


def unsafe_path_refs(
    repo: Path,
    *,
    head_sha: str,
    records: tuple[ChangeRecord, ...],
) -> tuple[str, ...]:
    refs: set[str] = set()
    for record in records:
        if record.kind is ChangeKind.DELETED:
            continue
        candidate = record.path_refs[-1]
        if _head_path_is_unsafe(repo, head_sha=head_sha, path_ref=candidate):
            refs.add(candidate)
    return tuple(sorted(refs))


def plan_changed_verification(
    repo: Path,
    *,
    base_sha: str,
    head_sha: str,
    force_full: bool = False,
) -> VerificationPlan:
    _validate_repository(repo, head_sha=head_sha)
    _validate_commit(repo, base_sha)
    _validate_commit(repo, head_sha)
    _validate_comparison(
        repo,
        base_sha=base_sha,
        head_sha=head_sha,
        force_full=force_full,
    )
    records = changed_records(repo, base_sha=base_sha, head_sha=head_sha)
    unsafe_refs = unsafe_path_refs(repo, head_sha=head_sha, records=records)
    selection = classify_changes(
        records,
        force_full=force_full,
        unsafe_path_refs=unsafe_refs,
    )
    selected_units = unit_refs_for_selection(
        selection,
        full_unit_refs=tuple(unit.unit_ref for unit in CI_JOB_GRAPH),
    )
    return build_plan(
        repo,
        head_sha,
        change_records=records,
        selected_unit_refs=selected_units,
        base_sha=base_sha,
        force_full=force_full,
        shadow_mode=True,
        unsafe_path_refs=unsafe_refs,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Plan UAA's canonical risk-based verification DAG in shadow mode."
    )
    parser.add_argument("--repo", default=".")
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--force-full", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        plan = plan_changed_verification(
            Path(args.repo),
            base_sha=args.base_sha,
            head_sha=args.head_sha,
            force_full=args.force_full,
        )
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        code = str(exc)
        if not code.startswith("VERIFICATION_"):
            code = "VERIFICATION_PLAN_BLOCKED"
        print(f"Risk-based verification plan blocked: {code}", file=sys.stderr)
        return 2
    payload = asdict(plan)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("UAA risk-based verification shadow plan")
        print(f"Risk tier: {plan.risk_tier.value}")
        print(f"Exact SHA: {plan.repository_sha}")
        print(f"Changed paths: {len(plan.changed_path_refs)}")
        print(f"Verification units: {len(plan.selected_unit_refs)}")
        print(f"Audit posture: {plan.audit_posture}")
        print(f"Plan fingerprint: {plan.plan_fingerprint}")
        print(
            "Authority: advisory shadow only; existing merge gates remain authoritative"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
