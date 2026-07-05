#!/usr/bin/env python3
"""Validate and emit the UAA GoatCitadel catch-up prompt pack."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT / "docs" / "prompts" / "uaa_goatcitadel_catchup"
MANIFEST_PATH = PACK_DIR / "prompt_bundle_manifest.json"
README_PATH = PACK_DIR / "README.md"
WRAPPER_PROMPT = (
    "docs/prompts/uaa_goatcitadel_catchup/"
    "00_execute_uaa_goatcitadel_catchup_end_to_end.prompt.md"
)
PROMPT_REF_PATTERN = re.compile(
    r"^docs/prompts/uaa_goatcitadel_catchup/"
    r"(0[0-9]_[a-z0-9_]+\.prompt\.md)$"
)
HASH_PREFIX = "sha256:"
ABSOLUTE_LOCAL_PATH_PATTERN = re.compile(r"/Users/[^)\s`]+")
FORBIDDEN_RUNTIME_PHRASES = (
    "grants runtime authority",
    "unrestricted shell execution is allowed",
    "browser automation is allowed",
    "connector writes are allowed",
    "production authority is granted",
)


class VerificationError(RuntimeError):
    """Raised when prompt-pack verification fails."""


def _load_manifest() -> dict[str, Any]:
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise VerificationError(f"missing manifest: {MANIFEST_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise VerificationError(f"invalid manifest json: {exc}") from exc
    if not isinstance(data, dict):
        raise VerificationError("manifest must be a JSON object")
    return data


def _prompt_refs(manifest: dict[str, Any]) -> list[str]:
    refs = manifest.get("developer_prompt_refs")
    if not isinstance(refs, list) or not refs:
        raise VerificationError("manifest developer_prompt_refs must be a non-empty list")
    if any(not isinstance(ref, str) for ref in refs):
        raise VerificationError("manifest developer_prompt_refs must contain strings only")
    return list(refs)


def _repo_path(ref: str) -> Path:
    if ref.startswith("/") or ".." in Path(ref).parts:
        raise VerificationError(f"unsafe prompt ref: {ref}")
    return ROOT / ref


def compute_bundle_hash(refs: list[str]) -> str:
    digest = hashlib.sha256()
    for ref in refs:
        path = _repo_path(ref)
        digest.update(b"\n--UAA-PROMPT-PACK-FILE--\n")
        digest.update(ref.encode("utf-8"))
        digest.update(b"\n")
        digest.update(path.read_bytes())
    return f"{HASH_PREFIX}{digest.hexdigest()}"


def _validate_text_safety(path: Path, text: str) -> None:
    repo_relative = path.relative_to(ROOT)
    if ABSOLUTE_LOCAL_PATH_PATTERN.search(text):
        raise VerificationError(f"{repo_relative} contains an absolute local user path")
    lowered = text.lower()
    for phrase in FORBIDDEN_RUNTIME_PHRASES:
        if phrase in lowered:
            raise VerificationError(f"{repo_relative} contains forbidden authority phrase: {phrase}")


def verify_manifest(allow_placeholder_hash: bool = False) -> dict[str, Any]:
    if not README_PATH.is_file():
        raise VerificationError(f"missing README: {README_PATH.relative_to(ROOT)}")

    manifest = _load_manifest()
    if manifest.get("bundle_id") != "uaa-goatcitadel-catchup-001":
        raise VerificationError("unexpected bundle_id")
    if manifest.get("version") != "1.0.0":
        raise VerificationError("unexpected version")
    if manifest.get("stable_within_run") is not True:
        raise VerificationError("stable_within_run must be true")

    refs = _prompt_refs(manifest)
    if refs[0] != WRAPPER_PROMPT:
        raise VerificationError("first prompt ref must be the end-to-end wrapper prompt")
    if len(refs) != 10:
        raise VerificationError(f"expected 10 prompt refs, found {len(refs)}")
    if len(set(refs)) != len(refs):
        raise VerificationError("prompt refs must be unique")

    for index, ref in enumerate(refs):
        if not PROMPT_REF_PATTERN.match(ref):
            raise VerificationError(f"prompt ref has unexpected format: {ref}")
        if index > 0:
            expected_prefix = f"0{index}_"
            filename = Path(ref).name
            if not filename.startswith(expected_prefix):
                raise VerificationError(f"prompt {ref} must start with {expected_prefix}")
        path = _repo_path(ref)
        if not path.is_file():
            raise VerificationError(f"missing prompt file: {ref}")
        text = path.read_text(encoding="utf-8")
        if not text.startswith("# "):
            raise VerificationError(f"prompt file must start with a markdown h1: {ref}")
        _validate_text_safety(path, text)

    _validate_text_safety(README_PATH, README_PATH.read_text(encoding="utf-8"))

    actual_hash = compute_bundle_hash(refs)
    manifest_hash = manifest.get("bundle_hash")
    if manifest_hash == f"{HASH_PREFIX}PLACEHOLDER" and allow_placeholder_hash:
        manifest["computed_bundle_hash"] = actual_hash
        return manifest
    if manifest_hash != actual_hash:
        raise VerificationError(
            f"bundle_hash mismatch: manifest={manifest_hash!r} computed={actual_hash!r}"
        )

    manifest["computed_bundle_hash"] = actual_hash
    return manifest


def emit_combined_prompt(refs: list[str], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = _load_manifest()
    header = [
        "# UAA GoatCitadel Catch-Up Prompt Pack Combined Run",
        "",
        f"Bundle id: `{manifest['bundle_id']}`",
        f"Bundle version: `{manifest['version']}`",
        f"Bundle hash: `{manifest['bundle_hash']}`",
        "",
        "This file is generated for operator review or Codex CLI input.",
        "The source prompt files remain the durable repo-owned bundle.",
        "",
        "## Prompt Refs",
        "",
    ]
    for ref in refs:
        header.append(f"- `{ref}`")
    header.extend(["", "---", ""])

    chunks = ["\n".join(header)]
    for ref in refs:
        path = _repo_path(ref)
        chunks.append(f"<!-- BEGIN {ref} -->\n")
        chunks.append(path.read_text(encoding="utf-8").rstrip())
        chunks.append(f"\n<!-- END {ref} -->\n\n")
    output.write_text("".join(chunks), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print verification metadata as JSON")
    parser.add_argument("--list", action="store_true", help="list prompt refs")
    parser.add_argument("--print-hash", action="store_true", help="print computed bundle hash")
    parser.add_argument("--allow-placeholder-hash", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--emit-combined", type=Path, help="write a combined prompt file")
    args = parser.parse_args(argv)

    try:
        manifest = verify_manifest(allow_placeholder_hash=args.allow_placeholder_hash)
        refs = _prompt_refs(manifest)
        if args.emit_combined:
            emit_combined_prompt(refs, args.emit_combined)
        if args.list:
            for ref in refs:
                print(ref)
        if args.print_hash:
            print(manifest["computed_bundle_hash"])
        if args.json:
            print(
                json.dumps(
                    {
                        "bundle_id": manifest["bundle_id"],
                        "version": manifest["version"],
                        "prompt_count": len(refs),
                        "bundle_hash": manifest["computed_bundle_hash"],
                        "combined_output": str(args.emit_combined) if args.emit_combined else None,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        if not (args.list or args.print_hash or args.json):
            print(
                "UAA GoatCitadel catch-up prompt pack verified: "
                f"{len(refs)} prompts, {manifest['computed_bundle_hash']}"
            )
            if args.emit_combined:
                print(f"Combined prompt written: {args.emit_combined}")
        return 0
    except VerificationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

