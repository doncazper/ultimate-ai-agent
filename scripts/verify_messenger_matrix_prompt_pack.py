#!/usr/bin/env python3
"""Validate the finite, desktop-only Messenger Matrix prompt bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT / "docs" / "prompts" / "messenger_matrix"
MANIFEST_PATH = PACK_DIR / "prompt_bundle_manifest.json"
README_PATH = PACK_DIR / "README.md"
README_REF = "docs/prompts/messenger_matrix/README.md"
DESIGN_REFS = (
    "docs/design/UAA_MESSENGER_MATRIX_IMPLEMENTATION_PLAN.md",
    "docs/design/control_center_north_star/UAA_COMMUNICATIONS_MATRIX_NORTH_STAR.md",
)
HASH_PREFIX = "sha256:"
EXPECTED_VERSION = "1.1.0"
EXPECTED_PROMPT_COUNT = 13
EXPECTED_NO_NEW_AUTHORITY_COUNT = 4
EXPECTED_STAGED_AUTHORITY_COUNT = 7
PROMPT_REF_PATTERN = re.compile(
    r"^docs/prompts/messenger_matrix/"
    r"(0[0-9]|1[0-2])_[a-z0-9_]+\.prompt\.md$"
)
ABSOLUTE_LOCAL_PATH_PATTERN = re.compile(
    r"(?:"
    r"/Users/|/home/|/(?:private/)?tmp/|/var/folders/|"
    r"/workspaces?/|/mnt/|/Volumes/|[A-Za-z]:\\Users\\"
    r")[^)\s`]+"
)
FORBIDDEN_CLAIMS = (
    "this bundle grants runtime authority",
    "full machine access enables matrix",
    "approval refs authorize execution",
    "ui state grants authority",
    "mobile implementation is in scope",
    "use github-hosted compute",
    "use paid ci",
)
RELEASE_FRAGMENTS = (
    "open a draft PR",
    "local review and hardening",
    "Mark it ready only after local checks pass",
    "repository-required GitHub-hosted CI on standard macOS runners",
    "never paid larger runners or self-hosted compute",
    "Merge only when required checks are green",
    "update local `main` to the exact remote merge",
    "post-merge verification",
    "push verified `main`",
    "post-merge push must be a synchronization no-op",
    "new scoped branch and PR",
    "clean worktree",
)
DESKTOP_ONLY_FRAGMENTS = (
    "This milestone is desktop-only",
    "Do not add, test, capture, or claim mobile surfaces",
)
STAGED_AUTHORITY_FRAGMENTS = (
    "## Stage A — Exact Authority Acceptance",
    "## Stage B — Runtime Implementation",
    "On this branch and PR",
    "eligible for fresh request-scoped evaluation only",
)
PRE_START_AUTHORITY_FRAGMENTS = (
    "Immediately before every Stage B runtime call",
    "PolicyEngine",
    "LocalApprovalAuthority scope where required",
    "current exact AuthorityLease",
    "exact capability, adapter, provider, target, mission, and run",
    "TTL/deadline",
    "budget",
    "readiness",
    "kill switch",
    "safe-disable",
    "idempotency/replay posture",
    "Approval refs alone never authorize",
    "fails closed before the call starts",
)
EXERCISED_RUNTIME_AUTHORITY_FRAGMENTS = (
    "Immediately before every runtime call",
    "PolicyEngine",
    "exact LocalApprovalAuthority scope where required",
    "current exact AuthorityLease",
    "exact capability, adapter, provider, target, mission, and run",
    "TTL/deadline",
    "budget",
    "readiness",
    "kill switch",
    "safe-disable",
    "idempotency/replay posture",
    "Approval refs alone never authorize",
    "Unknown, stale, expired, or mismatched state fails closed",
)
REQUIRED_README_FRAGMENTS = (
    "planning artifacts only; no runtime authority granted",
    "Prompts 04–10 use a two-stage contract on one branch and PR",
    "Acceptance makes a lane eligible for fresh request-scoped evaluation",
    "repository-required GitHub-hosted CI on standard macOS runners",
    "Every phase is desktop-only and macOS-first",
)
PHASE_FRAGMENTS: dict[int, tuple[str, ...]] = {
    0: ("planning-only milestone", "MSG-MX-000", "MSG-MX-012"),
    1: ("clean-room/license ADR", "all 15 renders", "threat model"),
    2: ("fixture-only desktop product surface", "Preview, Planned, or Blocked"),
    3: ("CommunicationsService", "disabled Matrix adapter shell"),
    4: ("digest-pinned Synapse image", "unencrypted fixtures", "encryption metadata"),
    5: (
        "exact version",
        "Rust/WASM crypto dependency",
        "dependency-license",
        "approved adapter boundary",
        "dependency rollback",
    ),
    6: (
        "encrypted-at-rest offline cache",
        "macOS Keychain backend",
        "Fail closed when the cache is locked",
        "plaintext scans",
    ),
    7: ("current Rust crypto", "external facility", "external_facility_required"),
    8: (
        "separate encrypted, TTL-bounded store",
        "external facility",
        "AI-generated or autonomous sends remain blocked",
    ),
    9: (
        "filesystem materialization",
        "quarantine before any preview",
        "external_facility_required",
    ),
    10: (
        "four separately scoped lane families",
        "attachment-analysis proposals only when",
        "automatic durable Memory",
    ),
    11: ("grants no new runtime lane", "external_facility_required"),
    12: (
        "at most two focused repair passes",
        "external_facility_required",
        "stop at the finite acceptance endpoint",
    ),
}


class VerificationError(RuntimeError):
    """Raised when the prompt bundle violates its stored contract."""


def _load_manifest() -> dict[str, Any]:
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise VerificationError(f"missing manifest: {MANIFEST_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise VerificationError(f"invalid manifest json: {exc}") from exc
    if not isinstance(manifest, dict):
        raise VerificationError("manifest must be a JSON object")
    return manifest


def _prompt_refs(manifest: dict[str, Any]) -> list[str]:
    refs = manifest.get("developer_prompt_refs")
    if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
        raise VerificationError("developer_prompt_refs must be a list of strings")
    return list(refs)


def _repo_path(ref: str) -> Path:
    path = Path(ref)
    if path.is_absolute() or ".." in path.parts:
        raise VerificationError(f"unsafe bundle ref: {ref}")
    return ROOT / path


def compute_bundle_hash(refs: list[str]) -> str:
    digest = hashlib.sha256()
    for ref in (README_REF, *DESIGN_REFS, *refs):
        path = _repo_path(ref)
        digest.update(b"\n--UAA-PROMPT-PACK-FILE--\n")
        digest.update(ref.encode("utf-8"))
        digest.update(b"\n")
        digest.update(path.read_bytes())
    return f"{HASH_PREFIX}{digest.hexdigest()}"


def _validate_text_safety(path: Path, text: str) -> None:
    if ABSOLUTE_LOCAL_PATH_PATTERN.search(text):
        raise VerificationError(f"{path.name} contains an absolute local user path")
    lowered = text.lower()
    for claim in FORBIDDEN_CLAIMS:
        if claim in lowered:
            raise VerificationError(f"{path.name} contains forbidden claim: {claim}")


def _require_fragments(label: str, text: str, fragments: tuple[str, ...]) -> None:
    normalized_text = " ".join(re.sub(r"-\s*\n\s*", "-", text).split())
    missing = [
        fragment
        for fragment in fragments
        if " ".join(re.sub(r"-\s*\n\s*", "-", fragment).split())
        not in normalized_text
    ]
    if missing:
        raise VerificationError(f"{label} missing: {', '.join(missing)}")


def _validate_prompt(
    index: int,
    ref: str,
    text: str,
) -> tuple[bool, bool, bool]:
    _validate_text_safety(_repo_path(ref), text)
    _require_fragments(f"prompt {index:02d} desktop-only contract", text, DESKTOP_ONLY_FRAGMENTS)
    _require_fragments(f"prompt {index:02d} release loop", text, RELEASE_FRAGMENTS)
    _require_fragments(f"prompt {index:02d} semantics", text, PHASE_FRAGMENTS[index])

    expected_branch = f"codex/msg-mx-{index:02d}-"
    if expected_branch not in text:
        raise VerificationError(f"prompt {index:02d} missing dedicated branch prefix")
    if "Python Core remains authoritative" not in text:
        raise VerificationError(f"prompt {index:02d} missing Python authority statement")
    if "safe refs" not in text or "content-free receipts" not in text:
        raise VerificationError(f"prompt {index:02d} missing safe mutation contract")

    staged = 4 <= index <= 10
    if staged:
        _require_fragments(
            f"prompt {index:02d} staged authority contract",
            text,
            STAGED_AUTHORITY_FRAGMENTS,
        )
        _require_fragments(
            f"prompt {index:02d} pre-start authority contract",
            text,
            PRE_START_AUTHORITY_FRAGMENTS,
        )
    elif "## Stage A — Exact Authority Acceptance" in text:
        raise VerificationError(f"prompt {index:02d} must not accept a new authority lane")

    no_new_authority = index <= 3
    if no_new_authority and not re.search(
        r"(?:requires no new|grants no(?: Matrix)?) runtime authority",
        text,
        flags=re.IGNORECASE,
    ):
        raise VerificationError(f"prompt {index:02d} must explicitly grant no runtime authority")

    if index >= 11 and not re.search(
        r"grants no new runtime (?:lane|authority)",
        text,
        flags=re.IGNORECASE,
    ):
        raise VerificationError(f"prompt {index:02d} must grant no new authority lane")
    if index >= 11:
        _require_fragments(
            f"prompt {index:02d} exercised runtime authority contract",
            text,
            EXERCISED_RUNTIME_AUTHORITY_FRAGMENTS,
        )

    return True, no_new_authority, staged


def verify_manifest() -> dict[str, Any]:
    manifest = _load_manifest()
    if manifest.get("$schema") != "../../schemas/prompt_bundle_manifest.schema.json":
        raise VerificationError("manifest $schema ref is missing or incorrect")
    if manifest.get("bundle_id") != "messenger-matrix-001":
        raise VerificationError("unexpected bundle_id")
    if manifest.get("version") != EXPECTED_VERSION:
        raise VerificationError(f"manifest version must be {EXPECTED_VERSION}")
    if manifest.get("stable_within_run") is not True:
        raise VerificationError("stable_within_run must be true")

    refs = _prompt_refs(manifest)
    if len(refs) != EXPECTED_PROMPT_COUNT or len(set(refs)) != len(refs):
        raise VerificationError("manifest must contain 13 unique prompt refs")

    readme = README_PATH.read_text(encoding="utf-8")
    _validate_text_safety(README_PATH, readme)
    _require_fragments("README execution contract", readme, REQUIRED_README_FRAGMENTS)

    desktop_only_count = 0
    no_new_authority_count = 0
    staged_authority_count = 0
    release_loop_count = 0
    for index, ref in enumerate(refs):
        if not PROMPT_REF_PATTERN.fullmatch(ref):
            raise VerificationError(f"invalid prompt ref: {ref}")
        if not Path(ref).name.startswith(f"{index:02d}_"):
            raise VerificationError(f"prompt refs are not ordered at index {index}")
        path = _repo_path(ref)
        if not path.is_file():
            raise VerificationError(f"missing prompt: {ref}")
        text = path.read_text(encoding="utf-8")
        desktop, no_new, staged = _validate_prompt(index, ref, text)
        desktop_only_count += int(desktop)
        no_new_authority_count += int(no_new)
        staged_authority_count += int(staged)
        release_loop_count += 1

    if no_new_authority_count != EXPECTED_NO_NEW_AUTHORITY_COUNT:
        raise VerificationError("expected exactly four no-new-authority prompts")
    if staged_authority_count != EXPECTED_STAGED_AUTHORITY_COUNT:
        raise VerificationError("expected exactly seven staged-authority prompts")

    actual_hash = manifest.get("bundle_hash")
    expected_hash = compute_bundle_hash(refs)
    if actual_hash != expected_hash:
        raise VerificationError(
            f"bundle_hash mismatch: expected {expected_hash}, found {actual_hash}"
        )

    return {
        "bundle_id": manifest["bundle_id"],
        "version": manifest["version"],
        "prompt_count": len(refs),
        "desktop_only_count": desktop_only_count,
        "no_new_authority_count": no_new_authority_count,
        "staged_authority_count": staged_authority_count,
        "release_loop_count": release_loop_count,
        "readme_integrity_protected": True,
        "bundle_hash": actual_hash,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()
    try:
        report = verify_manifest()
    except (OSError, VerificationError) as exc:
        print(f"Messenger Matrix prompt pack verification failed: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            "Messenger Matrix prompt pack verified: "
            f"{report['prompt_count']} prompts, {report['bundle_hash']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
