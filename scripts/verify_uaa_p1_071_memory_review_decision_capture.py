#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CONTRACT_DOC = ROOT / "docs/control_center/UAA_P1_071_MEMORY_REVIEW_DECISION_CAPTURE.md"
SCHEMA = ROOT / "docs/schemas/memory_review_decision_capture.schema.json"
REVIEW_DECISIONS = ROOT / "src/ultimate_ai_agent/core/memory/review_decisions.py"
MEMORY_INIT = ROOT / "src/ultimate_ai_agent/core/memory/__init__.py"
FOUNDER_LOOP = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_MOCK = ROOT / "apps/control-center/src/mocks/controlCenterData.ts"
STORAGE_TEST = ROOT / "tests/test_founder_loop_storage.py"
API_TEST = ROOT / "tests/test_control_center_founder_loop_api.py"
FOCUSED_TEST = ROOT / "tests/test_uaa_p1_071_memory_review_decision_capture.py"

DECISION_STATES = [
    "accept",
    "correct",
    "reject",
    "defer",
    "merge",
    "supersede",
    "forget_request",
]

REQUIRED_BLOCKED_STATE_REFS = [
    "blocked-state:no-memory-write",
    "blocked-state:no-memory-delete",
    "blocked-state:no-memory-export",
    "blocked-state:no-context-injection",
]

DENIED_FLAGS = [
    "memory_write_authorized",
    "memory_delete_authorized",
    "memory_export_authorized",
    "context_injection_authorized",
    "connector_runtime_enabled",
    "account_auth_enabled",
    "provider_or_model_authority_allowed",
    "source_truth_authority",
    "accepted_as_recall",
    "retention_execution_authorized",
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_authority_enabled",
]

FORBIDDEN_SNIPPETS = [
    "raw_prompt",
    "raw_response",
    "provider_payload",
    "api_key",
    "authorization",
    "cookie",
    "password",
    "private_key",
    "/users/",
    "/home/",
    "/var/",
    "/etc/",
]

FORBIDDEN_LEGACY_MEMORY_CALLS = [
    "MemoryStore",
    "LocalMemoryStore",
    "write_memory",
    "put_record",
    "mark_deleted",
    "export_records",
    "memory/write/evaluate",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(path: Path, snippets: list[str], failures: list[str]) -> None:
    text = _read(path)
    for snippet in snippets:
        if snippet not in text:
            failures.append(f"{path.relative_to(ROOT)} missing {snippet!r}")


def _require_absent(path: Path, snippets: list[str], failures: list[str]) -> None:
    text = _read(path)
    for snippet in snippets:
        if snippet in text:
            failures.append(f"{path.relative_to(ROOT)} contains forbidden {snippet!r}")


def _extract(today: dict) -> dict:
    return {
        "memory_review_decision_contract_ref": today[
            "memory_review_decision_contract_ref"
        ],
        "memory_review_decision_states": today["memory_review_decision_states"],
        "memory_review_decision_required_ref_fields": today[
            "memory_review_decision_required_ref_fields"
        ],
        "memory_review_decision_authority_posture": today[
            "memory_review_decision_authority_posture"
        ],
        "memory_review_queue": today["memory_review_queue"],
    }


def _source_prefix(source_kind: str) -> str:
    return f"source-ref:{source_kind.replace('_', '-')}"


def _provenance_prefix(source_kind: str) -> str:
    return f"provenance-ref:{source_kind.replace('_', '-')}"


def _matches_prefix(value: str, prefix: str) -> bool:
    return value == prefix or value.startswith(f"{prefix}:")


def _validate_live_contract(schema: dict, failures: list[str]) -> None:
    from ultimate_ai_agent.core.memory import (
        MEMORY_REVIEW_DECISION_CONTRACT_REF,
        MEMORY_REVIEW_DECISION_STATES,
        MemoryReviewDecisionEnvelope,
    )
    from ultimate_ai_agent.core.storage import FounderLoopRepository

    with tempfile.TemporaryDirectory(prefix="uaa-p1-071-") as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir), seed_defaults=True)
        today = repo.today_summary()

    contract = _extract(today)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(contract), key=lambda error: error.path)
    for error in errors:
        failures.append(f"live memory review decision schema error: {error.message}")

    if (
        contract["memory_review_decision_contract_ref"]
        != MEMORY_REVIEW_DECISION_CONTRACT_REF
    ):
        failures.append("live memory review decision contract ref drifted")
    if [
        row["decision_state"] for row in contract["memory_review_decision_states"]
    ] != MEMORY_REVIEW_DECISION_STATES:
        failures.append("live memory review decision states drifted")
    for row in contract["memory_review_decision_states"]:
        for required_flag in [
            "provenance_refs_required",
            "blocked_state_refs_required",
        ]:
            if row.get(required_flag) is not True:
                failures.append(f"live decision state row missing {required_flag}")

    serialized = json.dumps(contract, sort_keys=True).lower()
    for forbidden in FORBIDDEN_SNIPPETS:
        if forbidden in serialized:
            failures.append(f"live decision contract contains unsafe snippet: {forbidden}")

    for item in contract["memory_review_queue"]:
        if item.get("decision_review_only") is not True:
            failures.append(f"{item.get('review_ref')} is not review-only")
        for flag in [
            "memory_write_authorized",
            "memory_delete_authorized",
            "memory_export_authorized",
            "context_injection_authorized",
            "connector_runtime_allowed",
            "account_auth_enabled",
            "provider_or_model_authority_allowed",
            "retention_execution_authorized",
            "accepted_as_truth",
        ]:
            if item.get(flag) is not False:
                failures.append(f"{item.get('review_ref')} has unsafe {flag}")
        if item.get("decision_source_provenance_contract_ref") != (
            "contract-ref:memory-source-provenance:v1"
        ):
            failures.append(f"{item.get('review_ref')} lacks source provenance binding")
        if item.get("decision_source_trust_posture") != "untrusted_until_reviewed":
            failures.append(f"{item.get('review_ref')} source trust posture drifted")
        if item.get("decision_redaction_status") != "redacted_summary_only":
            failures.append(f"{item.get('review_ref')} redaction status drifted")
        source_kind = str(item.get("decision_source_kind", ""))
        for source_ref in item.get("source_refs", []):
            if not _matches_prefix(str(source_ref), _source_prefix(source_kind)):
                failures.append(f"{item.get('review_ref')} source ref kind mismatch")
        for provenance_ref in item.get("provenance_refs", []):
            if not _matches_prefix(
                str(provenance_ref),
                _provenance_prefix(source_kind),
            ):
                failures.append(f"{item.get('review_ref')} provenance ref kind mismatch")
        for blocked_ref in REQUIRED_BLOCKED_STATE_REFS:
            if blocked_ref not in item.get("decision_blocked_state_refs", []):
                failures.append(f"{item.get('review_ref')} missing {blocked_ref}")

    for flag in DENIED_FLAGS:
        try:
            MemoryReviewDecisionEnvelope(
                decision_ref="memory-review-decision:unsafe",
                review_ref="memory-review:unsafe",
                decision_state="accept",
                actor_ref="actor-ref:local-operator",
                safe_summary="Review decision envelope for a safe memory candidate.",
                source_refs=["source-ref:manual-note:unsafe"],
                provenance_refs=["provenance-ref:manual-note:unsafe"],
                evidence_refs=["evidence-ref:memory-review:unsafe"],
                audit_refs=["audit-plan:memory-review:unsafe"],
                receipt_refs=["receipt-plan:memory-review:unsafe"],
                **{flag: True},
            )
        except ValueError:
            continue
        failures.append(f"memory review decision accepted unsafe {flag}=true")

    for unsafe_summary in [
        "raw_prompt material",
        "raw_response material",
        "provider_payload body",
        "raw path marker",
        "raw log marker",
        "account identifier marker",
        "username: private actor",
        "hostname: private host",
        "credential material",
        "raw_private_content marker",
    ]:
        try:
            MemoryReviewDecisionEnvelope(
                decision_ref="memory-review-decision:unsafe-summary",
                review_ref="memory-review:unsafe-summary",
                decision_state="accept",
                actor_ref="actor-ref:local-operator",
                safe_summary=unsafe_summary,
                source_refs=["source-ref:manual-note:unsafe-summary"],
                provenance_refs=["provenance-ref:manual-note:unsafe-summary"],
                evidence_refs=["evidence-ref:memory-review:unsafe-summary"],
                audit_refs=["audit-plan:memory-review:unsafe-summary"],
                receipt_refs=["receipt-plan:memory-review:unsafe-summary"],
            )
        except ValueError:
            continue
        failures.append("memory review decision accepted unsafe summary text")
    for unsafe_ref_field, unsafe_ref_value in [
        ("decision_ref", "memory-review-decision:raw_prompt"),
        ("review_ref", "memory-review:raw_response"),
        ("actor_ref", "actor-ref:username"),
        ("source_refs", ["source-ref:raw-prompt:test"]),
        ("provenance_refs", ["provenance-ref:provider-payload:test"]),
        ("evidence_refs", ["evidence-ref:raw-log:test"]),
        ("audit_refs", ["audit-plan:account-identifier:test"]),
        ("receipt_refs", ["receipt-plan:credential:test"]),
        ("blocked_state_refs", ["blocked-state:raw-private-content"]),
    ]:
        try:
            payload = {
                "decision_ref": "memory-review-decision:unsafe-ref",
                "review_ref": "memory-review:unsafe-ref",
                "decision_state": "accept",
                "actor_ref": "actor-ref:local-operator",
                "safe_summary": "Review decision envelope for a safe memory candidate.",
                "source_refs": ["source-ref:manual-note:unsafe-ref"],
                "provenance_refs": ["provenance-ref:manual-note:unsafe-ref"],
                "evidence_refs": ["evidence-ref:memory-review:unsafe-ref"],
                "audit_refs": ["audit-plan:memory-review:unsafe-ref"],
                "receipt_refs": ["receipt-plan:memory-review:unsafe-ref"],
            }
            payload[unsafe_ref_field] = unsafe_ref_value
            MemoryReviewDecisionEnvelope(**payload)
        except ValueError:
            continue
        failures.append(f"memory review decision accepted unsafe {unsafe_ref_field}")
    for mismatched in [
        {
            "source_kind": "local_chat_summary",
            "source_refs": ["source-ref:manual-note:mismatch"],
            "provenance_refs": ["provenance-ref:local-chat-summary:mismatch"],
        },
        {
            "source_kind": "local_chat_summary",
            "source_refs": ["source-ref:local-chat-summary:mismatch"],
            "provenance_refs": ["provenance-ref:manual-note:mismatch"],
        },
        {
            "blocked_state_refs": ["blocked-state:no-memory-write"],
        },
    ]:
        try:
            payload = {
                "decision_ref": "memory-review-decision:mismatch",
                "review_ref": "memory-review:mismatch",
                "decision_state": "accept",
                "actor_ref": "actor-ref:local-operator",
                "safe_summary": "Review decision envelope for a safe memory candidate.",
                "source_refs": ["source-ref:manual-note:mismatch"],
                "provenance_refs": ["provenance-ref:manual-note:mismatch"],
                "evidence_refs": ["evidence-ref:memory-review:mismatch"],
                "audit_refs": ["audit-plan:memory-review:mismatch"],
                "receipt_refs": ["receipt-plan:memory-review:mismatch"],
            }
            payload.update(mismatched)
            MemoryReviewDecisionEnvelope(**payload)
        except ValueError:
            continue
        failures.append("memory review decision accepted weak source or blocked refs")


def main() -> int:
    failures: list[str] = []
    for path in [
        CONTRACT_DOC,
        SCHEMA,
        REVIEW_DECISIONS,
        MEMORY_INIT,
        FOUNDER_LOOP,
        FRONTEND_TYPES,
        FRONTEND_PANEL,
        FRONTEND_MOCK,
        STORAGE_TEST,
        API_TEST,
        FOCUSED_TEST,
    ]:
        if not path.exists():
            failures.append(f"{path.relative_to(ROOT)} is missing")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1

    _require(
        CONTRACT_DOC,
        [
            "contract-ref:memory-review-decision:v1",
            "accept",
            "correct",
            "reject",
            "defer",
            "merge",
            "supersede",
            "forget-request",
            "No memory writes",
            "UAA-P1-072",
        ],
        failures,
    )
    _require(
        REVIEW_DECISIONS,
        [
            "MemoryReviewDecisionEnvelope",
            "MEMORY_REVIEW_DECISION_STATES",
            "MEMORY_REVIEW_DECISION_REQUIRED_BLOCKED_STATE_REFS",
            "memory_review_decision_authority_posture",
            "accepted_as_recall",
            "production_authority_enabled",
            "blocked_state_refs",
            "_source_prefix",
        ],
        failures,
    )
    _require(
        FRONTEND_PANEL,
        [
            "Review decisions",
            "Decision capture",
            "Decision audit refs",
            "Decision receipt refs",
        ],
        failures,
    )
    _require(
        FOCUSED_TEST,
        [
            "test_memory_review_decision_contract_covers_required_states",
            "test_memory_review_decision_envelope_rejects_authority_creep",
            "test_memory_review_decision_envelope_rejects_unsafe_ref_markers",
            "test_memory_review_decision_envelope_binds_source_kind_to_refs",
            "test_founder_loop_today_exposes_memory_review_decision_contract",
        ],
        failures,
    )
    for path in [REVIEW_DECISIONS, FOUNDER_LOOP]:
        _require_absent(path, FORBIDDEN_LEGACY_MEMORY_CALLS, failures)

    if not failures:
        schema = json.loads(_read(SCHEMA))
        _validate_live_contract(schema, failures)

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1

    print("UAA-P1-071 memory review decision capture verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
