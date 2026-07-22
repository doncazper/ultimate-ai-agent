#!/usr/bin/env python3
"""Validate and emit the UAA Hermes/OpenClaw parity gap closure prompt pack."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT / "docs" / "prompts" / "uaa_parity_gap_closure"
MANIFEST_PATH = PACK_DIR / "prompt_bundle_manifest.json"
README_PATH = PACK_DIR / "README.md"
MANIFEST_REF = "docs/prompts/uaa_parity_gap_closure/prompt_bundle_manifest.json"
README_REF = "docs/prompts/uaa_parity_gap_closure/README.md"
EXPECTED_VERSION = "1.0.0"
EXPECTED_BUNDLE_ID = "uaa-hermes-openclaw-parity-gap-closure-001"
HASH_PREFIX = "sha256:"
EXPECTED_PROMPTS = (
    "00_execute_parity_gap_closure_end_to_end.prompt.md",
    "01_fresh_inventory_and_convergence_ledger.prompt.md",
    "02_backend_truth_first_loop_and_evidence.prompt.md",
    "03_live_local_setup_and_packaging.prompt.md",
    "04_goals_durable_events_and_lifecycle.prompt.md",
    "05_action_inbox_work_board_and_session_ux.prompt.md",
    "06_morning_briefing_sources_and_background_worker.prompt.md",
    "07_memory_search_backup_and_storage_integrity.prompt.md",
    "08_performance_supply_chain_and_efficiency.prompt.md",
    "09_cross_cutting_reliability_and_future_lane_proofs.prompt.md",
    "10_end_to_end_acceptance_and_parity_truth.prompt.md",
)
EXPECTED_PROMPT_REFS = tuple(
    f"docs/prompts/uaa_parity_gap_closure/{name}" for name in EXPECTED_PROMPTS
)
ABSOLUTE_LOCAL_PATH_PATTERN = re.compile(
    r"(?:^|[\s(`'\"=:\[\]{},])(?:file:(?://)?/|/(?:Users|home|root|private|tmp|var|etc|"
    r"System|Library|Applications|opt|usr|Volumes|srv|mnt|proc|dev|run|bin|sbin|"
    r"workspace|build|runner|github)"
    r"(?:/|\b)|~/|[A-Za-z]:\\Users\\|\\\\)",
    re.MULTILINE,
)
FORBIDDEN_SELF_AUTHORITY_PHRASES = (
    "this pack authorizes",
    "current request authorizes runtime",
    "approval ref authorizes execution",
    "parity requirement grants authority",
    "competitor behavior grants authority",
)
README_REQUIRED = (
    "Only `merged_proven` may be skipped as complete",
    "Live-Data And No-Mock Completion Floor",
    "This stored pack promotes nothing by itself",
    "Never modify, merge, close, or supersede an overlapping pull request owned by another task",
    "H01",
    "H06",
    "O01",
    "O08",
    "P01",
    "P10",
    "B01",
    "B14",
    "L01",
    "L16",
    "at most two focused repair passes",
)
WRAPPER_REQUIRED = (
    "Continue automatically through all independent phases",
    "Fresh Inventory Before Every Phase",
    "create one dedicated `codex/parity-gap-XX-*` branch/worktree",
    "Merge only when required checks are green",
    "Update local `main` to the exact remote merge SHA",
    "Remove only clean, merged temporary phase branches/worktrees",
    "verified combined snapshot",
    "do not replace the snapshot's manifest or prompt text",
    "Do not commit repairs directly to `main`",
    "at most two focused repair passes",
    "Do not generate another pack",
)
PHASE_REQUIRED: dict[int, tuple[str, ...]] = {
    1: (
        "H01-H06",
        "open_pr_owned_elsewhere",
        "Every skip is backed by current-main code",
    ),
    2: ("mockControlCenterData", "complete one readable path", "Stop the backend"),
    3: (
        "smallest real, safe, macOS-first setup lifecycle",
        "This pack is not authority",
        "stop and rollback",
    ),
    4: ("verified_complete", "real durable event source", "arbitrary UTF-8 splits"),
    5: ("backend revision/version", "stale approvals", "two clients"),
    6: (
        "real accepted read-only email/calendar adapters",
        "one named Morning Briefing refresh job",
        "connector writes",
    ),
    7: ("LLM-Free Search Outcomes", "fresh target", "archive bombs"),
    8: (
        "before/after measurements",
        "Inventory every cache",
        "locked Python and Node installations",
    ),
    9: ("B01-B14", "Delivery-attempt state machine", "single-flight invocation guard"),
    10: (
        "Required Live-Data Journeys",
        "at most two focused repair branches",
        "No critical journey may rely",
    ),
}
EXPECTED_COVERAGE_IDS = tuple(
    [f"H{index:02d}" for index in range(1, 7)]
    + [f"O{index:02d}" for index in range(1, 9)]
    + [f"P{index:02d}" for index in range(1, 11)]
    + [f"B{index:02d}" for index in range(1, 15)]
    + [f"L{index:02d}" for index in range(1, 17)]
)
COVERAGE_ROW_PATTERN = re.compile(
    r"^\| (?P<coverage_id>[HOPBL]\d{2}) \| (?P<label>[^|]+) \| (?P<phase>[^|]+) \|$",
    flags=re.MULTILINE,
)


class VerificationError(RuntimeError):
    """Raised when the prompt pack violates integrity or safety rules."""


@dataclass(frozen=True)
class VerifiedPromptPack:
    """Immutable verified prompt graph used for rendering and execution."""

    bundle_id: str
    version: str
    bundle_hash: str
    refs: tuple[str, ...]
    contents: tuple[tuple[str, bytes], ...]

    def content(self, ref: str) -> bytes:
        for content_ref, content in self.contents:
            if content_ref == ref:
                return content
        raise VerificationError(f"verified prompt-pack content is missing: {ref}")

    def result(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "version": self.version,
            "prompt_count": len(self.refs),
            "phase_count": len(self.refs) - 1,
            "coverage_item_count": len(EXPECTED_COVERAGE_IDS),
            "bundle_hash": self.bundle_hash,
            "fresh_inventory_before_each_phase": True,
            "live_data_completion_floor": True,
            "overlap_ownership_protected": True,
            "merge_gated_execution": True,
            "self_authorizing_phrases_rejected": True,
        }


def _load_manifest() -> dict[str, Any]:
    try:
        raw = _read_repo_bytes(MANIFEST_REF, "manifest")
        value = json.loads(_decode_utf8(MANIFEST_REF, raw, "manifest"))
    except OSError as exc:
        raise VerificationError("manifest is missing or unreadable") from exc
    except json.JSONDecodeError as exc:
        raise VerificationError(
            f"manifest JSON is invalid at line {exc.lineno}, column {exc.colno}"
        ) from exc
    if not isinstance(value, dict):
        raise VerificationError("manifest must be a JSON object")
    return value


def _prompt_refs(manifest: dict[str, Any]) -> list[str]:
    refs = manifest.get("developer_prompt_refs")
    if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
        raise VerificationError("developer_prompt_refs must be a list of strings")
    return list(refs)


def _manifest_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        strings: list[str] = []
        for key, nested in value.items():
            strings.append(str(key))
            strings.extend(_manifest_strings(nested))
        return strings
    if isinstance(value, list):
        strings = []
        for nested in value:
            strings.extend(_manifest_strings(nested))
        return strings
    return []


def _repo_path(ref: str) -> Path:
    candidate = Path(ref)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise VerificationError(f"unsafe prompt ref: {ref}")
    path = ROOT / candidate
    cursor = ROOT
    for part in candidate.parts:
        cursor /= part
        if cursor.is_symlink():
            raise VerificationError(f"symlinked prompt-pack path is unsafe: {ref}")
    if not path.resolve(strict=False).is_relative_to(ROOT.resolve(strict=True)):
        raise VerificationError(f"prompt ref escapes the repository: {ref}")
    return path


def _read_repo_bytes(ref: str, label: str) -> bytes:
    try:
        return _repo_path(ref).read_bytes()
    except OSError as exc:
        raise VerificationError(f"{label} is missing or unreadable") from exc


def _decode_utf8(ref: str, content: bytes, label: str) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise VerificationError(f"{label} is not valid UTF-8: {ref}") from exc


def _bundle_hash_from_contents(
    refs: tuple[str, ...], contents: dict[str, bytes], manifest: dict[str, Any]
) -> str:
    digest = hashlib.sha256()
    digest.update(b"\n--UAA-PROMPT-PACK-MANIFEST--\n")
    digest.update(_canonical_manifest_bytes(manifest, omit_bundle_hash=True))
    for ref in (README_REF, *refs):
        digest.update(b"\n--UAA-PROMPT-PACK-FILE--\n")
        digest.update(ref.encode("utf-8"))
        digest.update(b"\n")
        digest.update(contents[ref])
    return f"{HASH_PREFIX}{digest.hexdigest()}"


def compute_bundle_hash(refs: list[str]) -> str:
    ordered_refs = tuple(refs)
    manifest = _load_manifest()
    contents = {
        ref: _read_repo_bytes(ref, "prompt-pack source")
        for ref in (README_REF, *ordered_refs)
    }
    return _bundle_hash_from_contents(ordered_refs, contents, manifest)


def _canonical_manifest_bytes(
    manifest: dict[str, Any], *, omit_bundle_hash: bool
) -> bytes:
    payload = dict(manifest)
    if omit_bundle_hash:
        payload.pop("bundle_hash", None)
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _require_fragments(label: str, text: str, fragments: tuple[str, ...]) -> None:
    normalized = " ".join(text.split())
    normalized_folded = normalized.casefold()
    missing = [
        fragment
        for fragment in fragments
        if " ".join(fragment.split()).casefold() not in normalized_folded
    ]
    if missing:
        raise VerificationError(f"missing {label}: {', '.join(missing)}")


def _validate_text(path: Path, text: str) -> None:
    if ABSOLUTE_LOCAL_PATH_PATTERN.search(text):
        raise VerificationError(f"{path.name} contains an absolute local path")
    lowered = text.lower()
    for phrase in FORBIDDEN_SELF_AUTHORITY_PHRASES:
        if phrase in lowered:
            raise VerificationError(
                f"{path.name} contains self-authorizing phrase: {phrase}"
            )


def _validate_coverage_matrix(readme: str) -> None:
    rows = list(COVERAGE_ROW_PATTERN.finditer(readme))
    observed_ids = tuple(match.group("coverage_id") for match in rows)
    if observed_ids != EXPECTED_COVERAGE_IDS:
        raise VerificationError(
            "coverage matrix must list every H/O/P/B/L item once and in order"
        )
    for match in rows:
        phases = [value.strip() for value in match.group("phase").split(",")]
        if not phases or any(
            not value.isdigit() or not 2 <= int(value) <= 9 for value in phases
        ):
            raise VerificationError(
                f"invalid phase mapping for {match.group('coverage_id')}: {match.group('phase')}"
            )


def _verify_pack() -> VerifiedPromptPack:
    manifest = _load_manifest()
    for manifest_text in _manifest_strings(manifest):
        _validate_text(MANIFEST_PATH, manifest_text)
    if manifest.get("bundle_id") != EXPECTED_BUNDLE_ID:
        raise VerificationError("unexpected bundle_id")
    if manifest.get("version") != EXPECTED_VERSION:
        raise VerificationError(f"manifest version must be {EXPECTED_VERSION}")
    if manifest.get("stable_within_run") is not True:
        raise VerificationError("stable_within_run must be true")

    refs = tuple(_prompt_refs(manifest))
    if refs != EXPECTED_PROMPT_REFS:
        raise VerificationError(
            "prompt refs must match the canonical ordered 00-10 pack"
        )
    if len(refs) != len(set(refs)):
        raise VerificationError("prompt refs must be unique")

    prefix = "docs/prompts/uaa_parity_gap_closure/"
    contents: dict[str, bytes] = {}
    texts: list[str] = []
    for ref in refs:
        if not ref.startswith(prefix):
            raise VerificationError(f"prompt ref is outside the pack: {ref}")
        path = _repo_path(ref)
        content = _read_repo_bytes(ref, "prompt")
        text = _decode_utf8(ref, content, "prompt")
        if not text.startswith("# "):
            raise VerificationError(f"prompt must start with a Markdown heading: {ref}")
        _validate_text(path, text)
        contents[ref] = content
        texts.append(text)

    readme_content = _read_repo_bytes(README_REF, "pack README")
    readme = _decode_utf8(README_REF, readme_content, "pack README")
    contents[README_REF] = readme_content
    _validate_text(README_PATH, readme)
    _validate_coverage_matrix(readme)
    _require_fragments(
        "README convergence and coverage contract", readme, README_REQUIRED
    )
    _require_fragments("wrapper continuous merge loop", texts[0], WRAPPER_REQUIRED)
    for phase, fragments in PHASE_REQUIRED.items():
        expected_heading = f"# Phase {phase:02d}:"
        if not texts[phase].startswith(expected_heading):
            raise VerificationError(f"phase {phase:02d} has the wrong heading")
        _require_fragments(f"phase {phase:02d} contract", texts[phase], fragments)

    actual_hash = _bundle_hash_from_contents(refs, contents, manifest)
    configured_hash = manifest.get("bundle_hash")
    if configured_hash != actual_hash:
        raise VerificationError(
            f"bundle_hash mismatch: expected {actual_hash}, got {configured_hash}"
        )

    ordered_contents = (
        (MANIFEST_REF, _canonical_manifest_bytes(manifest, omit_bundle_hash=False)),
        *((ref, contents[ref]) for ref in (README_REF, *refs)),
    )
    return VerifiedPromptPack(
        bundle_id=EXPECTED_BUNDLE_ID,
        version=EXPECTED_VERSION,
        bundle_hash=actual_hash,
        refs=refs,
        contents=ordered_contents,
    )


def verify_manifest() -> dict[str, Any]:
    return _verify_pack().result()


def render_combined(pack: VerifiedPromptPack) -> bytes:
    chunks = [
        "# UAA Hermes/OpenClaw Parity Gap Closure Combined Prompt Pack\n\n"
        f"Bundle id: `{pack.bundle_id}`\n\n"
        f"Bundle version: `{pack.version}`\n\n"
        f"Bundle hash: `{pack.bundle_hash}`\n\n"
        "Generated for operator review. Source prompt files remain canonical.\n",
        f"\n<!-- BEGIN {MANIFEST_REF} -->\n",
        _decode_utf8(
            MANIFEST_REF,
            pack.content(MANIFEST_REF),
            "verified manifest",
        ).rstrip(),
        f"\n<!-- END {MANIFEST_REF} -->\n",
        f"\n<!-- BEGIN {README_REF} -->\n",
        _decode_utf8(README_REF, pack.content(README_REF), "verified README").rstrip(),
        f"\n<!-- END {README_REF} -->\n",
    ]
    for ref in pack.refs:
        chunks.extend(
            [
                f"\n<!-- BEGIN {ref} -->\n",
                _decode_utf8(ref, pack.content(ref), "verified prompt").rstrip(),
                f"\n<!-- END {ref} -->\n",
            ]
        )
    return ("\n".join(chunks) + "\n").encode("utf-8")


def emit_combined(content: bytes, output: Path) -> None:
    temporary_path: Path | None = None
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".uaa-parity-gap-closure-",
            dir=output.parent,
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, output)
        temporary_path = None
    except OSError as exc:
        raise VerificationError("combined prompt output is unavailable") from exc
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--emit-combined", type=Path)
    parser.add_argument("--stream-combined", action="store_true")
    args = parser.parse_args()
    if args.stream_combined and (args.json or args.list):
        parser.error("--stream-combined cannot be combined with --json or --list")
    try:
        pack = _verify_pack()
        result = pack.result()
        combined = (
            render_combined(pack)
            if args.emit_combined or args.stream_combined
            else None
        )
        if args.emit_combined:
            if combined is None:
                raise VerificationError("combined prompt rendering is unavailable")
            emit_combined(combined, args.emit_combined)
    except VerificationError as exc:
        print(
            f"parity gap closure prompt pack verification failed: {exc}",
            file=sys.stderr,
        )
        return 1

    if args.stream_combined:
        if combined is None:
            print("combined prompt rendering is unavailable", file=sys.stderr)
            return 1
        sys.stdout.buffer.write(combined)
    elif args.list:
        print("\n".join(pack.refs))
    elif args.emit_combined:
        print("emitted combined prompt pack: configured-output-ref")
    elif args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            "parity gap closure prompt pack verified: "
            f"{result['prompt_count']} prompts, {result['bundle_hash']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
