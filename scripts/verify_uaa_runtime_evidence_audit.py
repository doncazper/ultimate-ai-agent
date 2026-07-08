#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.storage import (  # noqa: E402
    EVIDENCE_AUDIT_GROUP_KINDS,
    EVIDENCE_AUDIT_RECEIPT_SPINE_CONTRACT_REF,
    EVIDENCE_AUDIT_RECEIPT_SPINE_SOURCE,
    FounderLoopRepository,
)


BROAD_AUTHORITY_FLAGS = (
    "approval_ref_authority",
    "action_execution_enabled",
    "tool_execution_enabled",
    "connector_write_enabled",
    "provider_model_call_enabled",
    "runtime_model_call_enabled",
    "provider_sdk_call_enabled",
    "live_web_enabled",
    "shell_subprocess_execution_enabled",
    "browser_execution_enabled",
    "background_autonomy_enabled",
    "external_export_enabled",
    "production_authority_enabled",
)


def main() -> int:
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="uaa-evidence-audit-") as temp:
        repo = FounderLoopRepository(Path(temp) / "founder-loop")
        timeline = repo.evidence_timeline(limit=50)
        spine = timeline.get("evidence_audit_receipt_spine") or {}

    if (
        timeline.get("evidence_audit_receipt_spine_contract_ref")
        != EVIDENCE_AUDIT_RECEIPT_SPINE_CONTRACT_REF
    ):
        failures.append("evidence audit spine contract ref missing from timeline")
    if spine.get("contract_ref") != EVIDENCE_AUDIT_RECEIPT_SPINE_CONTRACT_REF:
        failures.append("evidence audit spine contract ref drifted")
    if spine.get("source") != EVIDENCE_AUDIT_RECEIPT_SPINE_SOURCE:
        failures.append("evidence audit spine source drifted")
    for field in [
        "backend_owned",
        "control_center_presentation_only",
        "local_read_model_only",
        "safe_refs_only",
        "redacted_summaries_only",
    ]:
        if spine.get(field) is not True:
            failures.append(f"evidence audit spine {field} must be true")
    if spine.get("raw_content_included") is not False:
        failures.append("evidence audit spine raw content must be omitted")
    for flag in BROAD_AUTHORITY_FLAGS:
        if spine.get(flag) is not False:
            failures.append(f"evidence audit spine broadened {flag}")
    if spine.get("timeline_group_kinds") != list(EVIDENCE_AUDIT_GROUP_KINDS):
        failures.append("evidence audit spine group kinds drifted")
    if spine.get("group_count") != len(spine.get("groups") or []):
        failures.append("evidence audit group count mismatch")
    if spine.get("envelope_count") != len(spine.get("receipt_envelopes") or []):
        failures.append("evidence audit envelope count mismatch")
    if spine.get("missing_receipt_count") != len(
        spine.get("missing_receipt_refs") or []
    ):
        failures.append("evidence audit missing receipt count mismatch")
    if "receipt-envelope-field:artifact-hash-ref" not in (
        spine.get("receipt_envelope_field_refs") or []
    ):
        failures.append("evidence audit envelope artifact hash field missing")
    if "inspect-evidence-audit-spine" not in str(spine.get("cli_ref") or ""):
        failures.append("evidence audit CLI ref missing from read model")
    if not spine.get("receipt_envelopes"):
        failures.append("evidence audit spine must expose receipt envelopes")
    for envelope in spine.get("receipt_envelopes") or []:
        if envelope.get("raw_content_included") is not False:
            failures.append("evidence audit envelope raw content must be omitted")
        if not str(envelope.get("artifact_hash_ref") or "").startswith(
            "artifact-hash-ref:"
        ):
            failures.append("evidence audit envelope artifact hash ref missing")
        if envelope.get("receipt_recorded") is False and not envelope.get(
            "missing_receipt_refs"
        ):
            failures.append("missing receipt envelope must expose missing refs")

    docs = [
        ROOT / "docs/control_center/UAA_RUNTIME_EVIDENCE_AUDIT.md",
        ROOT / "docs/control_center/UAA_RUNTIME_CAPABILITY_SCOREBOARD.md",
    ]
    for doc in docs:
        if not doc.exists():
            failures.append(f"required doc missing: {doc.name}")
            continue
        text = doc.read_text(encoding="utf-8")
        if EVIDENCE_AUDIT_RECEIPT_SPINE_CONTRACT_REF not in text:
            failures.append(f"evidence audit contract ref missing from {doc.name}")
        if "inspect-evidence-audit-spine" not in text:
            failures.append(f"evidence audit CLI ref missing from {doc.name}")
        if "read-only lineage" not in " ".join(text.lower().split()):
            failures.append(f"read-only lineage boundary missing from {doc.name}")

    cli_text = (ROOT / "scripts/dev/uaa_founder_loop.py").read_text(
        encoding="utf-8"
    )
    if "inspect-evidence-audit-spine" not in cli_text:
        failures.append("Founder Loop CLI evidence audit command missing")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("UAA runtime evidence audit verifier passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
