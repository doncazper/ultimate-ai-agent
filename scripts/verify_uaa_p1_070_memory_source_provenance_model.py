#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CONTRACT_DOC = ROOT / "docs/control_center/UAA_P1_070_MEMORY_SOURCE_PROVENANCE_MODEL.md"
SCHEMA = ROOT / "docs/schemas/memory_source_provenance.schema.json"
SOURCE_PROVENANCE = ROOT / "src/ultimate_ai_agent/core/memory/source_provenance.py"
MEMORY_INIT = ROOT / "src/ultimate_ai_agent/core/memory/__init__.py"
MEMORY_VALIDATION = ROOT / "src/ultimate_ai_agent/core/memory/validation.py"
FOUNDER_LOOP = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
FRONTEND_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FRONTEND_PANEL = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
FRONTEND_MOCK = ROOT / "apps/control-center/src/mocks/controlCenterData.ts"
STORAGE_TEST = ROOT / "tests/test_founder_loop_storage.py"
API_TEST = ROOT / "tests/test_control_center_founder_loop_api.py"
FOCUSED_TEST = ROOT / "tests/test_uaa_p1_070_memory_source_provenance_model.py"

SOURCE_KINDS = [
    "manual_note",
    "external_assistant_review_summary",
    "local_chat_summary",
    "local_coding_summary",
    "task_plan",
    "action_proposal",
    "evidence_timeline_ref",
    "read_only_calendar_metadata_ref",
    "read_only_email_metadata_ref",
    "crm_lite_business_record",
]

DENIED_FLAGS = [
    "source_truth_authority",
    "memory_write_authorized",
    "automatic_memory_write_authorized",
    "context_injection_authorized",
    "connector_runtime_enabled",
    "account_auth_enabled",
    "provider_or_model_authority_allowed",
    "source_payload_storage_allowed",
    "private_content_storage_allowed",
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_authority_enabled",
]

FORBIDDEN_SERIALIZED_SNIPPETS = [
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

REQUIRED_DOC_SNIPPETS = [
    "contract-ref:memory-source-provenance:v1",
    "manual_note",
    "external_assistant_review_summary",
    "local_chat_summary",
    "local_coding_summary",
    "read_only_calendar_metadata_ref",
    "read_only_email_metadata_ref",
    "crm_lite_business_record",
    "untrusted_until_reviewed",
    "No review decision capture",
    "UAA-P1-071",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(path: Path, snippets: list[str], failures: list[str]) -> None:
    text = _read(path)
    for snippet in snippets:
        if snippet not in text:
            failures.append(f"{path.relative_to(ROOT)} missing {snippet!r}")


def _extract_memory_source_contract(today: dict) -> dict:
    return {
        "memory_source_provenance_contract_ref": today[
            "memory_source_provenance_contract_ref"
        ],
        "memory_source_required_kinds": today["memory_source_required_kinds"],
        "memory_source_policy": today["memory_source_policy"],
        "memory_source_denied_content_refs": today[
            "memory_source_denied_content_refs"
        ],
        "memory_source_review_posture": today["memory_source_review_posture"],
        "memory_review_queue": today["memory_review_queue"],
    }


def _validate_live_contract(schema: dict, failures: list[str]) -> None:
    from ultimate_ai_agent.core.memory import (
        MEMORY_SOURCE_PROVENANCE_CONTRACT_REF,
        MEMORY_SOURCE_PROVENANCE_REQUIRED_KINDS,
        MemorySourceProvenanceRef,
        MemorySourceRef,
    )
    from ultimate_ai_agent.core.memory.validation import validate_memory_source_ref
    from ultimate_ai_agent.core.storage import FounderLoopRepository

    with tempfile.TemporaryDirectory(prefix="uaa-p1-070-") as temp_dir:
        repo = FounderLoopRepository(Path(temp_dir), seed_defaults=True)
        today = repo.today_summary()

    contract = _extract_memory_source_contract(today)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(contract), key=lambda error: error.path)
    for error in errors:
        failures.append(f"live memory source schema error: {error.message}")

    if (
        contract["memory_source_provenance_contract_ref"]
        != MEMORY_SOURCE_PROVENANCE_CONTRACT_REF
    ):
        failures.append("live memory source contract ref drifted")
    if contract["memory_source_required_kinds"] != MEMORY_SOURCE_PROVENANCE_REQUIRED_KINDS:
        failures.append("live memory source kinds drifted")

    serialized = json.dumps(contract, sort_keys=True).lower()
    for forbidden in FORBIDDEN_SERIALIZED_SNIPPETS:
        if forbidden in serialized:
            failures.append(f"live memory source contract contains unsafe snippet: {forbidden}")

    for item in contract["memory_review_queue"]:
        if item.get("source_trust_posture") != "untrusted_until_reviewed":
            failures.append(f"{item.get('review_ref')} is not untrusted until reviewed")
        for flag in [
            "source_truth_authority",
            "memory_write_authorized",
            "automatic_memory_write_authorized",
            "context_injection_authorized",
            "account_auth_enabled",
            "public_beta_claim_enabled",
            "public_distribution_claim_enabled",
            "production_authority_enabled",
            "source_payload_storage_allowed",
            "prompt_body_storage_allowed",
            "response_body_storage_allowed",
            "provider_body_storage_allowed",
            "path_body_storage_allowed",
            "log_body_storage_allowed",
            "account_ref_storage_allowed",
            "private_content_storage_allowed",
            "connector_runtime_allowed",
            "provider_or_model_authority_allowed",
            "accepted_as_truth",
        ]:
            if item.get(flag) is not False:
                failures.append(f"{item.get('review_ref')} has unsafe {flag}")

    for flag in DENIED_FLAGS:
        try:
            MemorySourceProvenanceRef(
                source_ref="source-ref:manual-note:unsafe",
                source_kind="manual_note",
                provenance_ref="provenance-ref:manual-note:unsafe",
                safe_label="Manual note summary",
                **{flag: True},
            )
        except ValueError:
            continue
        failures.append(f"memory source model accepted unsafe {flag}=true")

    for unsafe_source in [
        MemorySourceRef(
            source_id="unsafe-source",
            source_type="file",
            file_ref="file-ref:unsafe",
            source_uri="/Users/private/workspace/source.txt",
        ),
        MemorySourceRef(
            source_id="unsafe-source",
            source_type="assistant",
            source_ref="source-ref:assistant-review:unsafe",
            source_kind="external_assistant_review_summary",
            metadata={"provider_payload": "private-provider-body"},
        ),
    ]:
        try:
            validate_memory_source_ref(unsafe_source)
        except ValueError:
            continue
        failures.append("legacy memory source validation accepted unsafe provenance")


def main() -> int:
    failures: list[str] = []
    for path in [
        CONTRACT_DOC,
        SCHEMA,
        SOURCE_PROVENANCE,
        MEMORY_INIT,
        MEMORY_VALIDATION,
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

    _require(CONTRACT_DOC, REQUIRED_DOC_SNIPPETS, failures)
    _require(
        SOURCE_PROVENANCE,
        [
            "MemorySourceProvenanceRef",
            "MEMORY_SOURCE_PROVENANCE_REQUIRED_KINDS",
            "memory_source_provenance_policy_rows",
            "validate_memory_source_provenance_ref",
            "public_beta_claim_enabled",
            "production_authority_enabled",
        ],
        failures,
    )
    _require(
        MEMORY_INIT,
        [
            "MemorySourceProvenanceRef",
            "MEMORY_SOURCE_PROVENANCE_CONTRACT_REF",
            "validate_memory_source_provenance_ref",
        ],
        failures,
    )
    _require(
        MEMORY_VALIDATION,
        [
            "UNSAFE_PROVENANCE_KEY_PATTERN",
            "UNSAFE_PROVENANCE_VALUE_PATTERN",
            "unsafe provenance content",
        ],
        failures,
    )
    _require(
        FOUNDER_LOOP,
        [
            "MEMORY_SOURCE_PROVENANCE_CONTRACT_REF",
            "memory_source_provenance_policy_rows",
            "_memory_source_contract_payload",
            "source_trust_posture",
        ],
        failures,
    )
    _require(
        FRONTEND_TYPES,
        [
            "FounderLoopMemorySourcePolicy",
            "memory_source_provenance_contract_ref",
            "source_trust_posture",
            "accepted_as_truth",
        ],
        failures,
    )
    _require(
        FRONTEND_PANEL,
        [
            "Source provenance",
            "Source trust",
            "Accepted as truth",
            "Memory write authority",
        ],
        failures,
    )
    _require(
        FRONTEND_MOCK,
        [
            "contract-ref:memory-source-provenance:v1",
            "read_only_calendar_metadata_ref",
            "untrusted_until_reviewed",
            "accepted_as_truth",
        ],
        failures,
    )
    _require(
        FOCUSED_TEST,
        [
            "test_memory_source_provenance_contract_covers_required_source_kinds",
            "test_legacy_memory_source_validation_rejects_unsafe_provenance_markers",
            "test_founder_loop_today_exposes_memory_source_provenance_contract",
        ],
        failures,
    )

    if not failures:
        schema = json.loads(_read(SCHEMA))
        _validate_live_contract(schema, failures)

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1

    print("UAA-P1-070 memory source provenance model verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
