#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CONTRACT_DOC = (
    ROOT / "docs/control_center/UAA_P1_072_BUSINESS_MEMORY_QUALITY_CONTROLS.md"
)
SCHEMA = ROOT / "docs/schemas/business_memory_quality_controls.schema.json"
BUSINESS_MEMORY = ROOT / "src/ultimate_ai_agent/core/memory/business_memory.py"
MEMORY_INIT = ROOT / "src/ultimate_ai_agent/core/memory/__init__.py"
STORAGE_INIT = ROOT / "src/ultimate_ai_agent/core/storage/__init__.py"
FOUNDER_LOOP = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_MOCK = ROOT / "apps/control-center/src/mocks/controlCenterData.ts"
ROUTE_MANIFEST = ROOT / "docs/control_center/route_status_manifest.json"
FOCUSED_TEST = ROOT / "tests/test_uaa_p1_072_business_memory_quality_controls.py"
STORAGE_TEST = ROOT / "tests/test_founder_loop_storage.py"
API_TEST = ROOT / "tests/test_control_center_founder_loop_api.py"
APP_TEST = ROOT / "apps/control-center/src/App.test.tsx"

CANDIDATE_KINDS = [
    "profile",
    "project",
    "relationship",
    "organization",
    "deal",
    "opportunity",
    "promise",
    "follow_up",
    "preference",
    "decision",
    "commitment",
]

QUALITY_STATES = [
    "duplicate",
    "conflict",
    "stale_expired",
    "low_confidence",
    "source_missing",
    "evidence_missing",
    "blocked",
    "reviewed",
]

REQUIRED_BLOCKED_REFS = [
    "blocked-state:no-memory-write",
    "blocked-state:no-memory-delete",
    "blocked-state:no-memory-export",
    "blocked-state:no-context-injection",
    "blocked-state:no-external-crm-write",
    "blocked-state:no-account-sync",
    "blocked-state:no-automatic-recall",
    "blocked-state:no-connector-runtime",
    "blocked-state:no-account-auth",
    "blocked-state:no-model-provider-authority",
    "blocked-state:no-source-truth-authority",
    "blocked-state:no-raw-source-display",
    "blocked-state:no-public-beta-or-distribution",
    "blocked-state:no-production-authority",
]

DENIED_FLAGS = [
    "memory_write_authorized",
    "memory_delete_authorized",
    "memory_export_authorized",
    "automatic_memory_write_authorized",
    "context_injection_authorized",
    "external_crm_write_authorized",
    "account_sync_authorized",
    "connector_runtime_enabled",
    "account_auth_enabled",
    "provider_or_model_authority_allowed",
    "source_truth_authority",
    "accepted_as_recall",
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

FORBIDDEN_RUNTIME_CALLS = [
    "write_memory",
    "put_record",
    "mark_deleted",
    "export_records",
    "external_crm_client",
    "sync_account",
    "account_sync_client",
    "connector.write",
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
        "business_memory_quality_contract_ref": today[
            "business_memory_quality_contract_ref"
        ],
        "business_memory_candidate_kinds": today["business_memory_candidate_kinds"],
        "business_memory_quality_states": today["business_memory_quality_states"],
        "business_memory_required_ref_fields": today[
            "business_memory_required_ref_fields"
        ],
        "business_memory_surface_bindings": today["business_memory_surface_bindings"],
        "business_memory_authority_posture": today["business_memory_authority_posture"],
        "business_memory_status": today["business_memory_status"],
        "memory_review_queue": today["memory_review_queue"],
    }


def _validate_live_contract(schema: dict, failures: list[str]) -> None:
    from ultimate_ai_agent.core.memory import (
        BUSINESS_MEMORY_CANDIDATE_KINDS,
        BUSINESS_MEMORY_QUALITY_CONTRACT_REF,
        BUSINESS_MEMORY_QUALITY_STATES,
        BusinessMemoryQualityEnvelope,
    )
    from ultimate_ai_agent.core.storage import FounderLoopRepository

    with tempfile.TemporaryDirectory(prefix="uaa-p1-072-") as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir), seed_defaults=True)
        today = repo.today_summary()

    contract = _extract(today)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(contract), key=lambda error: error.path)
    for error in errors:
        failures.append(f"live business memory schema error: {error.message}")

    if (
        contract["business_memory_quality_contract_ref"]
        != BUSINESS_MEMORY_QUALITY_CONTRACT_REF
    ):
        failures.append("live business memory contract ref drifted")
    if [
        row["candidate_kind"] for row in contract["business_memory_candidate_kinds"]
    ] != (BUSINESS_MEMORY_CANDIDATE_KINDS):
        failures.append("live business memory candidate kinds drifted")
    if [row["quality_state"] for row in contract["business_memory_quality_states"]] != (
        BUSINESS_MEMORY_QUALITY_STATES
    ):
        failures.append("live business memory quality states drifted")

    serialized = json.dumps(contract, sort_keys=True).lower()
    for forbidden in FORBIDDEN_SNIPPETS:
        if forbidden in serialized:
            failures.append(f"live business memory contract contains {forbidden}")

    posture = contract["business_memory_authority_posture"]
    if posture.get("safe_refs_only") is not True:
        failures.append("business memory posture is not safe-ref-only")
    if posture.get("review_required_before_recall") is not True:
        failures.append("business memory recall review requirement drifted")
    for flag in DENIED_FLAGS:
        if posture.get(flag) is not False:
            failures.append(f"business memory posture has unsafe {flag}")

    for item in contract["memory_review_queue"]:
        if item.get("business_memory_quality_contract_ref") != (
            BUSINESS_MEMORY_QUALITY_CONTRACT_REF
        ):
            failures.append(
                f"{item.get('review_ref')} missing business quality contract"
            )
        if item.get("business_memory_safe_refs_only") is not True:
            failures.append(f"{item.get('review_ref')} is not safe-ref-only")
        if item.get("business_memory_review_required_before_recall") is not True:
            failures.append(f"{item.get('review_ref')} skipped recall review")
        if item.get("business_memory_source_provenance_contract_ref") != (
            "contract-ref:memory-source-provenance:v1"
        ):
            failures.append(f"{item.get('review_ref')} lacks source provenance")
        if item.get("business_memory_source_trust_posture") != (
            "untrusted_until_reviewed"
        ):
            failures.append(f"{item.get('review_ref')} source trust drifted")
        if item.get("business_memory_redaction_status") != "redacted_summary_only":
            failures.append(f"{item.get('review_ref')} redaction status drifted")
        for flag in [
            "business_memory_accepted_as_recall",
            "business_memory_write_authorized",
            "business_memory_delete_authorized",
            "business_memory_export_authorized",
            "business_memory_crm_write_authorized",
            "business_memory_account_sync_authorized",
            "business_memory_context_injection_authorized",
        ]:
            if item.get(flag) is not False:
                failures.append(f"{item.get('review_ref')} has unsafe {flag}")
        for blocked_ref in REQUIRED_BLOCKED_REFS:
            if blocked_ref not in item.get("business_memory_blocker_refs", []):
                failures.append(f"{item.get('review_ref')} missing {blocked_ref}")

    for flag in DENIED_FLAGS:
        try:
            BusinessMemoryQualityEnvelope(
                review_ref="memory-review:unsafe",
                candidate_ref="business-memory-candidate:preference:unsafe",
                candidate_kind="preference",
                safe_summary="Business memory quality envelope for a safe candidate.",
                source_refs=["source-ref:manual-note:unsafe"],
                provenance_refs=["provenance-ref:manual-note:unsafe"],
                evidence_refs=["evidence-ref:memory-review:unsafe"],
                related_entity_refs=["business-memory-entity:preference:unsafe"],
                **{flag: True},
            )
        except ValueError:
            continue
        failures.append(f"business memory quality accepted unsafe {flag}=true")

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
        "raw private content marker",
    ]:
        try:
            BusinessMemoryQualityEnvelope(
                review_ref="memory-review:unsafe-summary",
                candidate_ref="business-memory-candidate:preference:unsafe-summary",
                candidate_kind="preference",
                safe_summary=unsafe_summary,
                source_refs=["source-ref:manual-note:unsafe-summary"],
                provenance_refs=["provenance-ref:manual-note:unsafe-summary"],
                evidence_refs=["evidence-ref:memory-review:unsafe-summary"],
                related_entity_refs=[
                    "business-memory-entity:preference:unsafe-summary"
                ],
            )
        except ValueError:
            continue
        failures.append("business memory quality accepted unsafe summary text")

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
            "quality_state_refs": ["business-memory-quality:duplicate"],
        },
        {
            "quality_state_refs": ["business-memory-quality:conflict"],
        },
    ]:
        try:
            payload = {
                "review_ref": "memory-review:mismatch",
                "candidate_ref": "business-memory-candidate:preference:mismatch",
                "candidate_kind": "preference",
                "safe_summary": "Business memory quality envelope for a safe candidate.",
                "source_refs": ["source-ref:manual-note:mismatch"],
                "provenance_refs": ["provenance-ref:manual-note:mismatch"],
                "evidence_refs": ["evidence-ref:memory-review:mismatch"],
                "related_entity_refs": ["business-memory-entity:preference:mismatch"],
            }
            payload.update(mismatched)
            BusinessMemoryQualityEnvelope(**payload)
        except ValueError:
            continue
        failures.append("business memory quality accepted weak source or quality refs")


def main() -> int:
    failures: list[str] = []
    for path in [
        CONTRACT_DOC,
        SCHEMA,
        BUSINESS_MEMORY,
        MEMORY_INIT,
        STORAGE_INIT,
        FOUNDER_LOOP,
        FRONTEND_TYPES,
        FRONTEND_PANEL,
        FRONTEND_MOCK,
        ROUTE_MANIFEST,
        FOCUSED_TEST,
        STORAGE_TEST,
        API_TEST,
        APP_TEST,
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
            "contract-ref:business-memory-quality-controls:v1",
            "profile",
            "relationship",
            "opportunity",
            "follow_up",
            "stale_expired",
            "No external CRM write",
            "No account sync",
            "UAA-P1-073",
        ],
        failures,
    )
    _require(
        BUSINESS_MEMORY,
        [
            "BusinessMemoryQualityEnvelope",
            "BUSINESS_MEMORY_CANDIDATE_KINDS",
            "BUSINESS_MEMORY_QUALITY_STATES",
            "BUSINESS_MEMORY_REQUIRED_BLOCKED_STATE_REFS",
            "business_memory_authority_posture",
            "source_provenance_contract_ref",
            "external_crm_write_authorized",
            "account_sync_authorized",
            "accepted_as_recall",
        ],
        failures,
    )
    _require(
        FOUNDER_LOOP,
        [
            "business_memory_quality_contract_ref",
            "business_memory_candidate_kinds",
            "business_memory_quality_states",
            "business_memory_surface_bindings",
            "business_memory_authority_posture",
            "implemented_review_queue_safe_ref_quality_metadata_contract",
            "storage_backed_review_queue_with_backend_decision_receipts",
        ],
        failures,
    )
    _require(
        FRONTEND_PANEL,
        [
            "Business memory",
            "CRM write authority",
            "Account sync authority",
            "Business quality refs",
            "Business blocker refs",
        ],
        failures,
    )
    _require(
        FOCUSED_TEST,
        [
            "test_business_memory_contract_covers_candidate_kinds_and_quality_states",
            "test_business_memory_quality_envelope_rejects_authority_creep",
            "test_business_memory_quality_envelope_rejects_unsafe_ref_markers",
            "test_business_memory_quality_envelope_binds_source_kind_to_refs",
            "test_business_memory_quality_envelope_requires_state_specific_refs",
            "test_founder_loop_today_exposes_business_memory_quality_contract",
        ],
        failures,
    )
    _require_absent(BUSINESS_MEMORY, FORBIDDEN_RUNTIME_CALLS, failures)

    if not failures:
        schema = json.loads(_read(SCHEMA))
        _validate_live_contract(schema, failures)

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1

    print("UAA-P1-072 business memory quality controls verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
