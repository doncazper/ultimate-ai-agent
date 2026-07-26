#!/usr/bin/env python3
"""Validate the stored UAA developer-feedback prompt pack."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT / "docs" / "prompts" / "uaa_developer_feedback"
MANIFEST_PATH = PACK_DIR / "prompt_bundle_manifest.json"
README_PATH = PACK_DIR / "README.md"
HASH_PREFIX = "sha256:"
EXPECTED_VERSION = "1.0.0"
README_REF = "docs/prompts/uaa_developer_feedback/README.md"
IMPLEMENTATION_PLAN_REF = "docs/implementation/UAA_DEVELOPER_FEEDBACK_IMPLEMENTATION_PLAN.md"
EXPECTED_PROMPTS = (
    "00_execute_all_review_verify_harden.prompt.md",
    "01_contract_authority_and_schema.prompt.md",
    "02_core_storage_api_cli.prompt.md",
    "03_native_shell_global_developer_mode.prompt.md",
    "04_screenshot_annotation_workflow.prompt.md",
    "05_video_timeline_keyframes.prompt.md",
    "06_extreme_diagnostics_and_feedback_inbox.prompt.md",
    "07_post_quit_codex_handoff.prompt.md",
    "08_codex_patch_workflow.prompt.md",
    "09_whole_app_acceptance_hardening.prompt.md",
)
ABSOLUTE_LOCAL_PATH_PATTERN = re.compile(
    r"(?:/Users/|/home/|/workspace/|/tmp/|/private/tmp/|"
    r"/var/folders/|/private/var/folders/|[A-Za-z]:\\Users\\)[^)\s`]+"
)
FORBIDDEN_SELF_AUTHORITY_PHRASES = (
    "current operator request authorizes",
    "operator request authorizes the post-quit lane",
    "approval ref authorizes",
    "privacy review is unnecessary",
)
README_AUTHORITY_FRAGMENTS = (
    "promotes nothing by itself",
    "separate exact capabilities",
    "Immediately before every callable operation",
    "Unknown, stale, expired, or mismatched state fails closed before start",
    "separate exact content-disclosure decision",
    "attachment materialization stays blocked",
)
WRAPPER_RELEASE_FRAGMENTS = (
    "one dedicated `codex/uaa-developer-feedback-XX-*` branch and one PR per phase",
    "Open the phase PR as draft",
    "repository-required GitHub-hosted CI on standard macOS runners only",
    "never paid larger runners or self-hosted compute",
    "Merge only when required checks are green",
    "Update local `main` to the exact remote merge",
    "Do not commit or push a repair directly to `main`",
    "verified local SHA already matches `origin/main`",
    "remove only clean merged phase branches/worktrees",
)
DISCLOSURE_PHASE_FRAGMENTS: dict[int, tuple[str, ...]] = {
    1: (
        "Separate exact capability/authority entries",
        "No broad developer-feedback capability is callable",
        "never makes the handoff callable by itself",
    ),
    4: ("exact destination/content-disclosure decision", "materialization remains blocked"),
    5: (
        "separately accepted exact video-capture capability",
        "immediately before recording starts",
        "exact destination/content-disclosure decision",
        "explicit operator confirmation",
    ),
    7: ("separate exact destination/content-disclosure", "Approval refs alone never authorize"),
    8: (
        "separate exact capabilities",
        "proposal-only",
        "Approval refs alone authorize nothing",
        "Without those lanes, a reviewed patch proposal",
    ),
    9: (
        "Run each walkthrough only when every exact capability",
        "explicit blocked acceptance result",
        "without claiming unproven runtime behavior",
    ),
}


class VerificationError(RuntimeError):
    """Raised when the prompt pack violates its integrity or safety contract."""


def _load_manifest() -> dict[str, Any]:
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise VerificationError(f"invalid manifest: {exc}") from exc
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
        raise VerificationError(f"unsafe prompt ref: {ref}")
    return ROOT / path


def compute_bundle_hash(refs: list[str]) -> str:
    """Return the canonical plan-plus-README-plus-prompts digest."""
    digest = hashlib.sha256()
    for ref in (IMPLEMENTATION_PLAN_REF, README_REF, *refs):
        digest.update(b"\n--UAA-PROMPT-PACK-FILE--\n")
        digest.update(ref.encode("utf-8"))
        digest.update(b"\n")
        digest.update(_repo_path(ref).read_bytes())
    return f"{HASH_PREFIX}{digest.hexdigest()}"


def _require_fragments(label: str, text: str, fragments: tuple[str, ...]) -> None:
    normalized_text = " ".join(text.split())
    missing = [
        fragment
        for fragment in fragments
        if " ".join(fragment.split()) not in normalized_text
    ]
    if missing:
        raise VerificationError(f"missing {label}: {', '.join(missing)}")


def _validate_text(path: Path, text: str) -> None:
    if ABSOLUTE_LOCAL_PATH_PATTERN.search(text):
        raise VerificationError(f"{path.name} contains an absolute local path")
    lowered = text.lower()
    for phrase in FORBIDDEN_SELF_AUTHORITY_PHRASES:
        if phrase in lowered:
            raise VerificationError(f"{path.name} contains self-authorizing phrase: {phrase}")


def verify_manifest() -> dict[str, Any]:
    manifest = _load_manifest()
    if manifest.get("version") != EXPECTED_VERSION:
        raise VerificationError(f"manifest version must be {EXPECTED_VERSION}")

    refs = _prompt_refs(manifest)
    names = tuple(Path(ref).name for ref in refs)
    if names != EXPECTED_PROMPTS:
        raise VerificationError("prompt refs must contain the ordered 00-09 pack")
    if len(set(refs)) != len(refs):
        raise VerificationError("prompt refs must be unique")

    prompt_texts: list[str] = []
    for ref in refs:
        expected_prefix = "docs/prompts/uaa_developer_feedback/"
        if not ref.startswith(expected_prefix):
            raise VerificationError(f"prompt ref is outside the pack: {ref}")
        path = _repo_path(ref)
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise VerificationError(f"missing prompt: {ref}") from exc
        _validate_text(path, text)
        prompt_texts.append(text)

    readme = README_PATH.read_text(encoding="utf-8")
    _validate_text(README_PATH, readme)
    _require_fragments("README authority contract", readme, README_AUTHORITY_FRAGMENTS)
    _require_fragments("finite release loop", prompt_texts[0], WRAPPER_RELEASE_FRAGMENTS)
    for phase, fragments in DISCLOSURE_PHASE_FRAGMENTS.items():
        _require_fragments(f"phase {phase:02d} authority contract", prompt_texts[phase], fragments)

    expected_hash = compute_bundle_hash(refs)
    if manifest.get("bundle_hash") != expected_hash:
        raise VerificationError(
            f"bundle_hash mismatch: expected {expected_hash}, got {manifest.get('bundle_hash')}"
        )

    return {
        "bundle_id": manifest.get("bundle_id"),
        "version": manifest.get("version"),
        "prompt_count": len(refs),
        "phase_count": len(refs) - 1,
        "bundle_hash": expected_hash,
        "self_authorizing_phrases_rejected": True,
        "content_disclosure_gated": True,
        "merge_gated_release_loop": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = verify_manifest()
    except VerificationError as exc:
        print(f"developer-feedback prompt pack verification failed: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            "developer-feedback prompt pack verified: "
            f"{result['prompt_count']} prompts, {result['bundle_hash']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
