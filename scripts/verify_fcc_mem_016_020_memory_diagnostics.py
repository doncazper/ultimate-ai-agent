#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.verification.api_lane import default_api_verifier_context  # noqa: E402
from scripts.verification.api_routes import projected_routes, route_fixture  # noqa: E402
from scripts.verification.repo import (  # noqa: E402
    append_missing_doc_snippets,
    print_failures_or_success,
    read_text,
)
from ultimate_ai_agent.core.memory import (  # noqa: E402
    FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
    MEMORY_CITATION_INTEGRITY_CONTRACT_REF,
    MEMORY_CONTEXT_MANIFEST_BLOCKED_STATE_REFS,
    MEMORY_CONTEXT_MANIFEST_CONTRACT_REF,
    MEMORY_FEEDBACK_QUALITY_BLOCKED_STATE_REFS,
    MEMORY_FEEDBACK_QUALITY_CONTRACT_REF,
    MEMORY_MAINTENANCE_RUN_CONTRACT_REF,
    MEMORY_RETRIEVAL_DIAGNOSTICS_CONTRACT_REF,
    MemoryFeedbackRequest,
    MemoryReviewDecisionRequest,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


SUCCESS_MESSAGE = "FCC-MEM-016 through FCC-MEM-020 verification passed."
SPEC_DOC = (
    "docs/control_center/"
    "FCC_MEM_016_020_MEMORY_DIAGNOSTICS_CITATIONS_FEEDBACK_MAINTENANCE_CONTEXT.md"
)
PROMPTS = [
    "docs/prompts/fcc_memory_module_sequence/16_fcc_mem_016_retrieval_diagnostics.prompt.md",
    "docs/prompts/fcc_memory_module_sequence/17_fcc_mem_017_citation_integrity.prompt.md",
    "docs/prompts/fcc_memory_module_sequence/18_fcc_mem_018_feedback_quality_queue.prompt.md",
    "docs/prompts/fcc_memory_module_sequence/19_fcc_mem_019_proposal_only_maintenance_runs.prompt.md",
    "docs/prompts/fcc_memory_module_sequence/20_fcc_mem_020_context_manifest.prompt.md",
]
ROUTE_EXPECTATIONS = {
    ("GET", "/control-center/memory/retrieval-diagnostics"): (
        "get_control_center_memory_retrieval_diagnostics",
        "local_sensitive",
    ),
    ("GET", "/control-center/memory/citation-integrity"): (
        "get_control_center_memory_citation_integrity",
        "local_sensitive",
    ),
    ("GET", "/control-center/memory/quality-issues"): (
        "get_control_center_memory_quality_issues",
        "local_sensitive",
    ),
    ("GET", "/control-center/memory/maintenance-runs"): (
        "get_control_center_memory_maintenance_runs",
        "local_sensitive",
    ),
    ("GET", "/control-center/memory/context-manifest"): (
        "get_control_center_memory_context_manifest",
        "local_sensitive",
    ),
    ("POST", "/control-center/memory/feedback"): (
        "post_control_center_memory_feedback",
        "mutating_requires_authority",
    ),
}
REQUIRED_DOC_SNIPPETS = {
    SPEC_DOC: [
        "FCC-MEM-016 Retrieval Diagnostics",
        "FCC-MEM-017 Citation Integrity",
        "FCC-MEM-018 Feedback And Quality Issues",
        "FCC-MEM-019 Proposal-Only Maintenance Runs",
        "FCC-MEM-020 Context Manifest",
        "no hidden prompt injection",
        "no automatic memory write",
        "no auto-merge",
        "no provider/model calls",
    ],
    "docs/prompts/fcc_memory_module_sequence/README.md": [
        "16_fcc_mem_016_retrieval_diagnostics.prompt.md",
        "20_fcc_mem_020_context_manifest.prompt.md",
    ],
    "docs/api/openapi_contract.md": [
        "GET /control-center/memory/retrieval-diagnostics",
        "GET /control-center/memory/context-manifest",
        "POST /control-center/memory/feedback",
    ],
    "docs/api/route_inventory.md": [
        "GET /control-center/memory/retrieval-diagnostics",
        "GET /control-center/memory/context-manifest",
        "POST /control-center/memory/feedback",
    ],
}


def verify(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    _append_required_file_failures(failures, root)
    _append_doc_failures(failures)
    _append_route_failures(failures)
    _append_repository_contract_failures(failures)
    _append_cli_failures(failures)
    return failures


def _append_required_file_failures(failures: list[str], root: Path) -> None:
    for rel_path in [SPEC_DOC, *PROMPTS, "tests/test_fcc_mem_016_020_memory_diagnostics.py"]:
        if not (root / rel_path).exists():
            failures.append(f"missing FCC-MEM-016-020 file: {rel_path}")


def _append_doc_failures(failures: list[str]) -> None:
    append_missing_doc_snippets(failures, REQUIRED_DOC_SNIPPETS)
    forbidden = [
        "auto-merge authorized",
        "auto-forget authorized",
        "hidden prompt injection enabled",
        "context injection authorized",
        "production authority enabled",
    ]
    for rel_path in [SPEC_DOC, *PROMPTS]:
        compact = " ".join(read_text(rel_path).lower().split())
        for snippet in forbidden:
            if snippet in compact:
                failures.append(f"{rel_path} contains forbidden claim '{snippet}'")


def _append_route_failures(failures: list[str]) -> None:
    context = default_api_verifier_context()
    if route_fixture()["routes"] != projected_routes(context.manifest):
        failures.append("frozen API route inventory does not match live manifest")
    for key, (operation_id, classification) in ROUTE_EXPECTATIONS.items():
        route = context.routes_by_key.get(key)
        if route is None:
            failures.append(f"missing route {key[0]} {key[1]}")
            continue
        if route["operation_id"] != operation_id:
            failures.append(f"{key[0]} {key[1]} operation_id drifted")
        if route["route_classification"] != classification:
            failures.append(f"{key[0]} {key[1]} classification drifted")
        if route["side_effect_class"] != "local_dev_workspace_only":
            failures.append(f"{key[0]} {key[1]} side_effect_class drifted")
    feedback = context.routes_by_key.get(("POST", "/control-center/memory/feedback"))
    if feedback:
        if feedback.get("idempotency_required") is not True:
            failures.append("memory feedback route must require idempotency")
        if feedback.get("rate_limit_group") != "memory_feedback":
            failures.append("memory feedback route rate-limit group drifted")


def _append_repository_contract_failures(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="uaa-fcc-mem-016-020-") as tmp:
        repo = FounderLoopRepository(Path(tmp) / "state")
        try:
            _accept_first_candidate(repo)
            retrieval = repo.memory_retrieval_diagnostics(limit=10)
            citation = repo.memory_citation_integrity(limit=10)
            quality = repo.memory_quality_issues(limit=10)
            maintenance = repo.memory_maintenance_runs(limit=10)
            manifest = repo.memory_context_manifest(limit=10)
            _assert_contracts(
                failures,
                retrieval=retrieval,
                citation=citation,
                quality=quality,
                maintenance=maintenance,
                manifest=manifest,
            )
            target_ref = str(repo.memory_impact_graph(limit=10)["nodes"][0]["memory_ref"])
            receipt = repo.record_memory_feedback(
                request=MemoryFeedbackRequest(
                    target_ref=target_ref,
                    target_kind="impact_graph_node",
                    feedback_kind="useful",
                    reviewer_ref="actor-ref:fcc-mem-016-020-verifier",
                    reason_refs=["reason-ref:fcc-mem-016-020:useful"],
                    blocked_state_refs=list(MEMORY_FEEDBACK_QUALITY_BLOCKED_STATE_REFS),
                ),
                idempotency_key_ref="idempotency-ref:fcc-mem-016-020-feedback",
            )
            if receipt.get("memory_write_performed") is not False:
                failures.append("memory feedback receipt performed a memory write")
            if receipt.get("context_injection_authorized") is not False:
                failures.append("memory feedback receipt authorized context injection")
            after_feedback = repo.memory_quality_issues(limit=10)
            if receipt.get("receipt_ref") not in after_feedback.get("feedback_receipt_refs", []):
                failures.append("memory feedback receipt did not feed quality issue queue")
        except Exception as exc:  # pragma: no cover - verifier failure reporting
            failures.append(f"repository contract smoke failed: {type(exc).__name__}: {exc}")


def _accept_first_candidate(repo: FounderLoopRepository) -> None:
    candidate_ref = str(
        repo.list_memory_review_queue(limit=1)[0]["business_memory_candidate_ref"]
    )
    repo.record_memory_review_decision(
        candidate_ref=candidate_ref,
        decision="accept",
        request=MemoryReviewDecisionRequest(
            reviewer_ref="actor-ref:fcc-mem-016-020-verifier",
            source_refs=["source-ref:fcc-mem-016-020:verifier"],
            evidence_refs=["evidence-ref:fcc-mem-016-020:verifier"],
            blocked_state_refs=list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS),
        ),
        idempotency_key_ref="idempotency-ref:fcc-mem-016-020-accept",
    )


def _assert_contracts(
    failures: list[str],
    *,
    retrieval: dict[str, Any],
    citation: dict[str, Any],
    quality: dict[str, Any],
    maintenance: dict[str, Any],
    manifest: dict[str, Any],
) -> None:
    expectations = [
        (retrieval, "fcc_mem_016_retrieval_diagnostics.v1", MEMORY_RETRIEVAL_DIAGNOSTICS_CONTRACT_REF),
        (citation, "fcc_mem_017_citation_integrity.v1", MEMORY_CITATION_INTEGRITY_CONTRACT_REF),
        (quality, "fcc_mem_018_feedback_quality_queue.v1", MEMORY_FEEDBACK_QUALITY_CONTRACT_REF),
        (maintenance, "fcc_mem_019_proposal_only_maintenance_run.v1", MEMORY_MAINTENANCE_RUN_CONTRACT_REF),
        (manifest, "fcc_mem_020_context_manifest.v1", MEMORY_CONTEXT_MANIFEST_CONTRACT_REF),
    ]
    for payload, schema_version, contract_ref in expectations:
        if payload.get("schema_version") != schema_version:
            failures.append(f"{schema_version} schema_version missing")
        if payload.get("contract_ref") != contract_ref:
            failures.append(f"{schema_version} contract_ref drifted")
        if payload.get("safe_refs_only") is not True:
            failures.append(f"{schema_version} must be safe_refs_only")
    required_false = {
        "context_injection_authorized",
        "memory_write_authorized",
        "production_authority_enabled",
    }
    for payload_name, payload in [
        ("retrieval", retrieval),
        ("citation", citation),
        ("quality", quality),
        ("maintenance", maintenance),
        ("manifest", manifest),
    ]:
        for field in required_false:
            if field in payload and payload[field] is not False:
                failures.append(f"{payload_name} {field} drifted")
    if retrieval.get("cache_hit") is not False:
        failures.append("retrieval diagnostics must not claim cache hits")
    if maintenance.get("auto_merge_authorized") is not False:
        failures.append("maintenance runs must not authorize auto merge")
    if maintenance.get("auto_forget_authorized") is not False:
        failures.append("maintenance runs must not authorize auto forget")
    if manifest.get("hidden_prompt_context_authorized") is not False:
        failures.append("context manifest must block hidden prompt context")
    for field in [
        "runtime_prompt_context_injection_authorized",
        "live_model_context_injection_authorized",
        "automatic_memory_inclusion_authorized",
        "connector_derived_context_injection_authorized",
        "browser_web_derived_context_injection_authorized",
        "shell_file_derived_context_injection_authorized",
        "raw_payload_persistence_enabled",
        "provider_prompt_context_injection_authorized",
        "broad_autonomy_authorized",
        "public_beta_claim_authorized",
        "public_distribution_claim_authorized",
        "production_readiness_claim_authorized",
    ]:
        if manifest.get(field) is not False:
            failures.append(f"context manifest {field} must stay false")
    blocked_refs = set(manifest.get("blocked_state_refs") or [])
    for blocked_ref in MEMORY_CONTEXT_MANIFEST_BLOCKED_STATE_REFS:
        if blocked_ref not in blocked_refs:
            failures.append(f"context manifest missing blocked ref {blocked_ref}")
    for item in manifest.get("manifests", []) or []:
        item_blocked_refs = set(item.get("blocked_state_refs") or [])
        for blocked_ref in MEMORY_CONTEXT_MANIFEST_BLOCKED_STATE_REFS:
            if blocked_ref not in item_blocked_refs:
                failures.append(
                    f"context manifest item missing blocked ref {blocked_ref}"
                )
    serialized = json.dumps(
        {
            "retrieval": retrieval,
            "citation": citation,
            "quality": quality,
            "maintenance": maintenance,
            "manifest": manifest,
        },
        sort_keys=True,
    ).lower()
    for unsafe in ["raw_prompt", "provider_payload", "secret", "credential"]:
        if unsafe in serialized:
            failures.append(f"unsafe serialized memory diagnostics content: {unsafe}")


def _append_cli_failures(failures: list[str]) -> None:
    cli_text = read_text("scripts/dev/uaa_founder_loop.py")
    for command in [
        "memory-retrieval-diagnostics",
        "memory-citation-integrity",
        "memory-quality-issues",
        "memory-maintenance-runs",
        "memory-context-manifest",
        "record-memory-feedback",
    ]:
        if command not in cli_text:
            failures.append(f"Founder Loop CLI missing {command}")


def main() -> int:
    return print_failures_or_success(
        failures=verify(),
        success_message=SUCCESS_MESSAGE,
    )


if __name__ == "__main__":
    raise SystemExit(main())
