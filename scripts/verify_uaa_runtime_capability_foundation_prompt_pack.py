#!/usr/bin/env python3
"""Validate and emit the UAA runtime capability foundation prompt pack."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT / "docs" / "prompts" / "uaa_runtime_capability_foundation"
MANIFEST_PATH = PACK_DIR / "prompt_bundle_manifest.json"
README_PATH = PACK_DIR / "README.md"
README_REF = "docs/prompts/uaa_runtime_capability_foundation/README.md"
WRAPPER_PROMPT = (
    "docs/prompts/uaa_runtime_capability_foundation/"
    "00_execute_uaa_runtime_capability_foundation_end_to_end.prompt.md"
)
PROMPT_REF_PATTERN = re.compile(
    r"^docs/prompts/uaa_runtime_capability_foundation/"
    r"(0[0-9]_[a-z0-9_]+\.prompt\.md)$"
)
HASH_PREFIX = "sha256:"
EXPECTED_VERSION = "1.2.0"
ABSOLUTE_LOCAL_PATH_PATTERN = re.compile(
    r"(?:/Users/|/home/|[A-Za-z]:\\Users\\)[^)\s`]+"
)
FORBIDDEN_RUNTIME_PHRASES = (
    "grants runtime authority",
    "unrestricted shell execution is allowed",
    "browser automation is allowed",
    "connector writes are allowed",
    "production authority is granted",
)
FORBIDDEN_STALE_PHRASES = (
    "stop after phase 01",
    "do not add live web fetch",
    "recommended next exact prompt",
    "generate unblock prompts",
    "authorized=true",
    "callable=true",
    "exact next prompts",
    "next prompts",
)
REQUIRED_COMPONENTS = (
    "reasoning and task understanding",
    "planning and orchestration",
    "learning and adaptation",
    "memory and context management",
    "communication and interaction quality",
    "action and tool calling",
    "autonomy and authority management",
    "code and implementation assistance",
    "research, web, and external information handling",
    "model and provider management",
    "evidence, audit, and observability",
    "safety, security, and failure handling",
    "UX as an AI cockpit",
    "CLI/API parity",
    "extensibility and ecosystem",
    "productized agent loop",
)
REQUIRED_WEAKNESSES = tuple(f"W{index}" for index in range(1, 20))
REQUIRED_MILESTONES = tuple(f"M{index}" for index in range(1, 7))
REQUIRED_EXTERNAL_REFERENCE_PATTERNS = (
    "GoatCitadel",
    "durable orchestration",
    "tamper-aware evidence receipts",
    "operator cockpit UX",
    "exact action/tool lanes",
    "Code Mode discipline",
    "model/provider observability",
    "governed memory retrieval",
    "extension catalog clarity",
)
REQUIRED_BLOCKED_AUTHORITY_PHRASES = (
    "Broad browser action, connector writes, production authority, unrestricted",
    "shell, runtime model calls beyond separately accepted exact lanes, and plugin",
)
REQUIRED_FINITE_FRAGMENTS = (
    "exactly ten merge-gated phases",
    "Phase 00 through Phase 09",
    "at most two focused final repair passes",
    "Do not automatically continue into another program",
    "stop the program",
)
REQUIRED_GIT_LOOP_FRAGMENTS = (
    "isolated `codex/capability-maturity-XX` branch and worktree",
    "read-only subagents",
    "Commit, push, and open one scoped PR",
    "wait three minutes and rerun once",
    "Merge only when required evidence is green",
    "Fast-forward local `main`",
    "Delete only clean, merged temporary branches and worktrees",
)
REQUIRED_PRESERVATION_FRAGMENTS = (
    "WebAccessGateway",
    "exact bounded SearXNG lane",
    "self-hosted Firecrawl one-page markdown extraction",
    "free-plan Firecrawl Cloud",
    "at most one eligible cloud fallback",
    "local web-service configuration",
    "WEB-HYBRID activation prompt",
    "WEB-HYBRID implementation plan",
    "TypeScript 7 exact stable pin",
    "pytest sharding",
    "isolated basetemps",
    "verifier-maintainability refactors",
    "extracted runtime CLI modules",
    "approval waits, retries, dead letters",
    "bounded deterministic SSE progress-preview replay",
)
REQUIRED_WEB_BOUNDARY_FRAGMENTS = (
    "content_untrusted=true",
    "not_instruction_authority=true",
    "inside the final locked transport-start boundary",
    "A self-hosted attempt does not authorize its cloud fallback",
    "no generic",
    "browser clicks/forms/auth/cookies/downloads/uploads",
    "zero network calls",
)
REQUIRED_SCORE_FRAGMENTS = (
    "normalized overall score at least 82/100",
    "stretch score 86/100",
    "authority, safety, and evidence at least 9.0",
    "planning and CLI/API parity at least 8.5",
    "reasoning, code, and extensibility at least 7.5",
    "learning at least 7.0",
)
REQUIRED_SCENARIOS = (
    "ambiguous intent",
    "plan revision",
    "DAG replay and crash",
    "approval expiry",
    "cancellation race",
    "budget exhaustion and settlement",
    "exact tool idempotency",
    "sandbox escape denial",
    "memory correction",
    "web citation and injection handling",
    "unavailable or stale provider",
    "receipt tamper plus UI/CLI/API parity",
)
REQUIRED_PERMANENT_AUTHORITY_FRAGMENTS = (
    "Unknown authority is denied",
    "approval ref is an identifier only",
    "PolicyEngine",
    "exact LocalApprovalAuthority result",
    "current AuthorityLease",
    "capability and adapter",
    "provider and target",
    "mission and run",
    "TTL and deadline",
    "budget",
    "kill switch",
    "safe-disable",
    "readiness",
    "idempotency",
    "replay posture",
)
REQUIRED_TERMINAL_REPORT_FRAGMENTS = (
    "commit, branch, PR, hosted CI, merge, and post-merge result",
    "commands, test counts, timings, and blockers",
    "unsupported or external adapters",
    "adapter required",
    "configuration required",
    "external facility required",
    "deferred by authority policy",
    "Do not use paid CI, provider, review, or marketplace services",
    "Communication Center and Conversation Vault (`FCC-COMMS`)",
    "Only the Phase 09 final deliverable may name at most one optional unactivated",
)
REQUIRED_PHASE_CONTRACTS: dict[int, tuple[str, ...]] = {
    1: ("safe intent ref and fingerprint", "facts, assumptions, and unknowns", "revision fingerprint"),
    2: ("Productized Founder Loop And Mission Completion", "mission-wide operation, time, cost, and concurrency budgets", "crash during settlement"),
    3: ("Memory, Learning, And Governed Context", "included and excluded source refs", "corrections win deterministically"),
    4: ("Useful Exact Tool And Code Lanes", "bounded repository filesystem metadata", "Sandbox Proof Floor"),
    5: ("Web Research And Provider Observability", "bounded SearXNG search", "final locked transport-start boundary"),
    6: ("Portable Evidence And Observability", "tamper, truncation, reorder, replay", "macOS Keychain-backed lifecycle"),
    7: ("Extensibility Ecosystem", "Inspectable never", "arbitrary runtime import"),
    8: ("macOS Cockpit And CLI/API Parity", "Linux and Windows remain explicit render placeholders", "bounded deterministic SSE progress-preview replay"),
    9: ("Benchmark, Gap Closure, And Stop", "at most two focused repair passes", "No recursively generated"),
}
REQUIRED_README_PHASE_ROWS = (
    "| 00 Pack/baseline |",
    "| 01 Reasoning/task understanding |",
    "| 02 Founder Loop/mission completion |",
    "| 03 Memory/learning/context |",
    "| 04 Exact tool/code lanes |",
    "| 05 Web/provider observability |",
    "| 06 Portable evidence |",
    "| 07 Extensibility ecosystem |",
    "| 08 macOS cockpit/CLI/API |",
    "| 09 Benchmark/gap closure/stop |",
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
    for ref in (README_REF, *refs):
        path = _repo_path(ref)
        digest.update(b"\n--UAA-PROMPT-PACK-FILE--\n")
        digest.update(ref.encode("utf-8"))
        digest.update(b"\n")
        digest.update(path.read_bytes())
    return f"{HASH_PREFIX}{digest.hexdigest()}"


def _validate_text_safety(path: Path, text: str) -> None:
    try:
        repo_relative = path.relative_to(ROOT)
    except ValueError:
        repo_relative = Path(path.name)
    if ABSOLUTE_LOCAL_PATH_PATTERN.search(text):
        raise VerificationError(f"{repo_relative} contains an absolute local user path")
    lowered = text.lower()
    for phrase in FORBIDDEN_RUNTIME_PHRASES:
        if phrase in lowered:
            raise VerificationError(f"{repo_relative} contains forbidden authority phrase: {phrase}")


def _validate_required_fragments(label: str, corpus: str, fragments: tuple[str, ...]) -> None:
    missing = [fragment for fragment in fragments if fragment not in corpus]
    if missing:
        raise VerificationError(f"missing {label}: {', '.join(missing)}")


def _validate_high_maturity_coverage(texts: list[str]) -> None:
    corpus = "\n".join(texts)
    lowered = corpus.lower()
    _validate_required_fragments("AI-agent component coverage", lowered, tuple(
        component.lower() for component in REQUIRED_COMPONENTS
    ))
    _validate_required_fragments("W1-W19 weakness coverage", corpus, REQUIRED_WEAKNESSES)
    _validate_required_fragments("M1-M6 authority milestone coverage", corpus, REQUIRED_MILESTONES)
    _validate_required_fragments(
        "external reference pattern coverage",
        corpus,
        REQUIRED_EXTERNAL_REFERENCE_PATTERNS,
    )
    _validate_required_fragments(
        "blocked-authority coverage",
        corpus,
        REQUIRED_BLOCKED_AUTHORITY_PHRASES,
    )


def _validate_finite_contract(readme: str, wrapper: str, corpus: str) -> None:
    normalized_readme = " ".join(readme.split())
    normalized_wrapper = " ".join(wrapper.split())
    normalized_corpus = " ".join(corpus.split())
    _validate_required_fragments(
        "finite endpoint contract", normalized_wrapper, REQUIRED_FINITE_FRAGMENTS
    )
    _validate_required_fragments("per-phase git loop", normalized_wrapper, REQUIRED_GIT_LOOP_FRAGMENTS)
    _validate_required_fragments(
        "preservation contract",
        f"{normalized_readme} {normalized_wrapper}",
        REQUIRED_PRESERVATION_FRAGMENTS,
    )
    _validate_required_fragments("score targets", normalized_wrapper, REQUIRED_SCORE_FRAGMENTS)
    _validate_required_fragments("benchmark scenarios", normalized_wrapper, REQUIRED_SCENARIOS)
    _validate_required_fragments(
        "permanent authority rules", normalized_wrapper, REQUIRED_PERMANENT_AUTHORITY_FRAGMENTS
    )
    _validate_required_fragments(
        "terminal report and scope contract", normalized_wrapper, REQUIRED_TERMINAL_REPORT_FRAGMENTS
    )
    _validate_required_fragments(
        "README phase map", normalized_readme, REQUIRED_README_PHASE_ROWS
    )

    phase_numbers = re.findall(r"^### Phase (\d{2}) \u2014", wrapper, flags=re.MULTILINE)
    expected = [f"{index:02d}" for index in range(10)]
    if phase_numbers != expected:
        raise VerificationError(
            f"finite phase headings must be exactly 00-09, found {phase_numbers!r}"
        )

    lowered = normalized_corpus.lower()
    stale = [phrase for phrase in FORBIDDEN_STALE_PHRASES if phrase in lowered]
    if stale:
        raise VerificationError(f"stale or unsafe prompt-pack phrases found: {', '.join(stale)}")


def _validate_web_contract(readme: str, phase_five: str) -> None:
    combined = " ".join(f"{readme}\n{phase_five}".split())
    _validate_required_fragments(
        "WEB-HYBRID preservation and boundary contract",
        combined,
        REQUIRED_WEB_BOUNDARY_FRAGMENTS,
    )


def _validate_phase_contracts(refs: list[str], prompt_texts: dict[str, str]) -> None:
    for index, fragments in REQUIRED_PHASE_CONTRACTS.items():
        ref = refs[index]
        raw_text = prompt_texts[ref]
        if not raw_text.startswith(f"# Phase {index:02d}:"):
            raise VerificationError(f"phase {index:02d} prompt has the wrong heading")
        _validate_required_fragments(
            f"Phase {index:02d} semantic contract",
            " ".join(raw_text.split()),
            fragments,
        )


def verify_manifest(allow_placeholder_hash: bool = False) -> dict[str, Any]:
    if not README_PATH.is_file():
        raise VerificationError(f"missing README: {README_PATH.relative_to(ROOT)}")

    manifest = _load_manifest()
    if manifest.get("bundle_id") != "uaa-runtime-capability-foundation-001":
        raise VerificationError("unexpected bundle_id")
    if manifest.get("version") != EXPECTED_VERSION:
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

    texts = [README_PATH.read_text(encoding="utf-8")]
    prompt_texts: dict[str, str] = {}
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
        texts.append(text)
        prompt_texts[ref] = text

    _validate_text_safety(README_PATH, texts[0])
    _validate_high_maturity_coverage(texts)
    wrapper = prompt_texts[WRAPPER_PROMPT]
    corpus = "\n".join(texts)
    _validate_finite_contract(texts[0], wrapper, corpus)
    _validate_phase_contracts(refs, prompt_texts)
    _validate_web_contract(texts[0], prompt_texts[refs[5]])

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
        "# UAA Runtime Capability Foundation Prompt Pack Combined Run",
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
    chunks.append(f"<!-- BEGIN {README_REF} -->\n")
    chunks.append(README_PATH.read_text(encoding="utf-8").rstrip())
    chunks.append(f"\n<!-- END {README_REF} -->\n\n")
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
                        "component_count": len(REQUIRED_COMPONENTS),
                        "weakness_count": len(REQUIRED_WEAKNESSES),
                        "authority_milestone_count": len(REQUIRED_MILESTONES),
                        "finite_phase_count": 10,
                        "repair_pass_limit": 2,
                        "benchmark_scenario_count": len(REQUIRED_SCENARIOS),
                        "readme_integrity_protected": True,
                        "combined_output": str(args.emit_combined) if args.emit_combined else None,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        if not (args.list or args.print_hash or args.json):
            print(
                "UAA runtime capability foundation prompt pack verified: "
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
