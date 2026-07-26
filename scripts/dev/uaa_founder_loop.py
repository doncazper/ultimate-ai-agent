#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any, Sequence

from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.control_center.action_decisions import (  # noqa: E402
    FounderLoopActionDecisionRequest,
    FounderLoopActionEnvelopePromotionRequest,
    action_id_to_item_ref,
)
from ultimate_ai_agent.core.control_center.agent_loop import (  # noqa: E402
    build_agent_loop_thread_read_model,
)
from ultimate_ai_agent.core.control_center import (  # noqa: E402
    FOUNDER_LOOP_PRODUCT_PROOF_CONTRACT_REF,
    FOUNDER_LOOP_PRODUCT_PROOF_READ_MODEL_SOURCE,
    FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER,
    FOUNDER_LOOP_PRODUCTIZATION_SURFACE_ORDER,
    UNIFIED_WORK_THREAD_CONTRACT_REF,
    UNIFIED_WORK_THREAD_READ_MODEL_SOURCE,
    UNIFIED_WORK_THREAD_STEP_ORDER,
)
from ultimate_ai_agent.core.control_center.local_tasks import (  # noqa: E402
    FounderLoopLocalTaskCommitRequest,
)
from ultimate_ai_agent.core.control_center.dogfood_live_loop import (  # noqa: E402
    build_dogfood_live_loop_acceptance_read_model,
)
from ultimate_ai_agent.core.control_center.backend_truth import (  # noqa: E402
    build_control_center_backend_truth,
)
from ultimate_ai_agent.core.control_center.proof import (  # noqa: E402
    build_control_center_proof_detail,
    build_control_center_proof_index,
)
from ultimate_ai_agent.core.control_center.start_here import (  # noqa: E402
    build_control_center_start_here_summary,
)
from ultimate_ai_agent.core.control_center.trust_authority import (  # noqa: E402
    build_trust_authority_matrix_read_model,
)
from ultimate_ai_agent.core.control_center.web_evidence_product_slice import (  # noqa: E402
    WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_BLOCKED_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_CAPABILITY_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_DOMAIN_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_MODE_REF,
    WebEvidenceProductSliceAuthorityError,
    WebEvidenceProductSliceRequest,
    build_web_evidence_product_slice_receipt,
)
from ultimate_ai_agent.core.authority import (  # noqa: E402
    AUTHORITY_STATE_DIR_ENV,
    AuthorityLeaseStore,
)
from ultimate_ai_agent.api.dependencies import (  # noqa: E402
    clear_founder_attention_workflow_cache,
    get_founder_attention_workflow,
)
from ultimate_ai_agent.core.control_center.founder_loop_attention_workflow import (  # noqa: E402
    attention_execution_owner_ref,
    build_attention_workflow_request,
)
from ultimate_ai_agent.core.time import utc_now  # noqa: E402
from ultimate_ai_agent.core.memory import (  # noqa: E402
    FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
    MEMORY_FEEDBACK_QUALITY_BLOCKED_STATE_REFS,
    MEMORY_MANUAL_INTAKE_BLOCKED_STATE_REFS,
    ManualMemoryCandidateRequest,
    MemoryContextPackActionProposalRequest,
    MemoryFeedbackRequest,
    MemoryReviewDecisionRequest,
)
from ultimate_ai_agent.core.storage import (  # noqa: E402
    FOUNDER_LOOP_STATE_DIR_ENV,
    FounderLoopAuthorityError,
    FounderLoopRepository,
    FounderLoopStorageDuplicateError,
    FounderLoopStorageError,
)


def _repository(args: argparse.Namespace) -> FounderLoopRepository:
    if args.state_dir is None:
        return FounderLoopRepository.from_env()
    return FounderLoopRepository(Path(args.state_dir))


def _safe_action_projection(action: dict[str, Any]) -> dict[str, Any]:
    return {
        "item_ref": action.get("item_ref"),
        "title": action.get("title"),
        "surface": action.get("surface"),
        "status": action.get("status"),
        "priority": action.get("priority"),
        "risk_class": action.get("risk_class"),
        "side_effect_class": action.get("side_effect_class"),
        "action_envelope_ref": action.get("action_envelope_ref"),
        "approval_envelope_ref": action.get("approval_envelope_ref"),
        "approval_envelope_status": action.get("approval_envelope_status"),
        "state_change_contract_ref": action.get("state_change_contract_ref"),
        "state_change_readiness": action.get("state_change_readiness"),
        "action_kind": action.get("action_kind"),
        "local_task_ref": action.get("local_task_ref"),
        "local_task_commit_approval_ref": action.get("local_task_commit_approval_ref"),
        "local_task_commit_eligible": action.get("local_task_commit_eligible"),
        "local_task_commit_approval_status": action.get(
            "local_task_commit_approval_status"
        ),
        "local_task_commit_contract_ref": action.get("local_task_commit_contract_ref"),
        "local_task_commit_route_ref": action.get("local_task_commit_route_ref"),
        "local_task_commit_receipt_ref": action.get("local_task_commit_receipt_ref"),
        "local_task_commit_next_safe_action": action.get(
            "local_task_commit_next_safe_action"
        ),
        "local_task_commit_blocked_reasons": list(
            action.get("local_task_commit_blocked_reasons") or []
        ),
        "local_task_commit_external_authority_blocked_refs": list(
            action.get("local_task_commit_external_authority_blocked_refs") or []
        ),
        "local_task_safe_disable_posture": action.get(
            "local_task_safe_disable_posture"
        ),
        "local_task_safe_disable_active": action.get("local_task_safe_disable_active"),
        "local_task_safe_disable_posture_ref": action.get(
            "local_task_safe_disable_posture_ref"
        ),
        "local_task_safe_disable_ref": action.get("local_task_safe_disable_ref"),
        "local_task_rollback_ref": action.get("local_task_rollback_ref"),
        "local_task_rollback_execution_enabled": action.get(
            "local_task_rollback_execution_enabled"
        ),
        "local_task_rollback_blocker_refs": list(
            action.get("local_task_rollback_blocker_refs") or []
        ),
        "receipt_refs": list(action.get("receipt_refs") or []),
        "audit_refs": list(action.get("audit_refs") or []),
        "evidence_refs": list(action.get("evidence_refs") or []),
        "rollback_ref": action.get("rollback_ref"),
        "safe_disable_ref": action.get("safe_disable_ref"),
        "next_safe_action": action.get("next_safe_action"),
        "task_decomposition_proposal_ref": action.get(
            "task_decomposition_proposal_ref"
        ),
        "task_decomposition_review_envelope_ref": action.get(
            "task_decomposition_review_envelope_ref"
        ),
        "task_decomposition_step_refs": list(
            action.get("task_decomposition_step_refs") or []
        ),
        "task_decomposition_dependency_refs": list(
            action.get("task_decomposition_dependency_refs") or []
        ),
        "task_decomposition_ambiguity_refs": list(
            action.get("task_decomposition_ambiguity_refs") or []
        ),
        "task_decomposition_missing_evidence_refs": list(
            action.get("task_decomposition_missing_evidence_refs") or []
        ),
        "task_decomposition_blocked_authority_refs": list(
            action.get("task_decomposition_blocked_authority_refs") or []
        ),
        "task_decomposition_review_only": action.get("task_decomposition_review_only"),
        "task_decomposition_proposal_only": action.get(
            "task_decomposition_proposal_only"
        ),
        "task_decomposition_execution_performed": action.get(
            "task_decomposition_execution_performed"
        ),
    }


def _safe_plan_projection(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "plan_ref": plan.get("plan_ref"),
        "title": plan.get("title"),
        "status": plan.get("status"),
        "task_decomposition_contract_ref": plan.get("task_decomposition_contract_ref"),
        "task_decomposition_request_ref": plan.get("task_decomposition_request_ref"),
        "task_decomposition_review_envelope_ref": plan.get(
            "task_decomposition_review_envelope_ref"
        ),
        "task_decomposition_proposal_ref": plan.get("task_decomposition_proposal_ref"),
        "task_decomposition_status": plan.get("task_decomposition_status"),
        "task_decomposition_step_refs": list(
            plan.get("task_decomposition_step_refs") or []
        ),
        "task_decomposition_dependency_refs": list(
            plan.get("task_decomposition_dependency_refs") or []
        ),
        "task_decomposition_ambiguity_refs": list(
            plan.get("task_decomposition_ambiguity_refs") or []
        ),
        "task_decomposition_missing_evidence_refs": list(
            plan.get("task_decomposition_missing_evidence_refs") or []
        ),
        "task_decomposition_suggested_action_inbox_proposal_refs": list(
            plan.get("task_decomposition_suggested_action_inbox_proposal_refs") or []
        ),
        "task_decomposition_required_approvals": list(
            plan.get("task_decomposition_required_approvals") or []
        ),
        "task_decomposition_blocked_authority_refs": list(
            plan.get("task_decomposition_blocked_authority_refs") or []
        ),
        "task_decomposition_review_only": plan.get("task_decomposition_review_only"),
        "task_decomposition_proposal_only": plan.get(
            "task_decomposition_proposal_only"
        ),
        "task_decomposition_execution_performed": plan.get(
            "task_decomposition_execution_performed"
        ),
        "evidence_refs": list(plan.get("evidence_refs") or []),
    }


def _safe_evidence_projection(item: dict[str, Any]) -> dict[str, Any]:
    answers = item.get("history_answers") or {}
    return {
        "timeline_item_ref": item.get("timeline_item_ref"),
        "item_kind": item.get("item_kind"),
        "title": item.get("title"),
        "status_refs": {
            key: value.get("refs", [])
            for key, value in answers.items()
            if isinstance(value, dict)
        },
        "blocked_state_refs": list(item.get("blocked_state_refs") or []),
        "evidence_refs": list(item.get("evidence_refs") or []),
    }


def _inspect_state(args: argparse.Namespace) -> int:
    repo = _repository(args)
    today = repo.today_summary(limit=args.limit)
    plans = repo.list_plan_summaries(limit=args.limit)
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-inspect",
        "storage_status": repo.storage_status(),
        "today_status": today.get("status"),
        "plan_action_state": today.get("plan_action_state"),
        "plans": [_safe_plan_projection(plan) for plan in plans],
        "task_decomposition_proposal_summary": {
            "contract_ref": today.get("task_decomposition_proposal_contract_ref"),
            "status": today.get("task_decomposition_proposal_status"),
            "proposal_count": today.get("task_decomposition_proposal_count"),
            "action_proposal_refs": list(
                today.get("task_decomposition_action_proposal_refs") or []
            ),
            "blocked_authority_refs": list(
                today.get("task_decomposition_required_blocked_refs") or []
            ),
            "authority_posture": today.get("task_decomposition_authority_posture"),
        },
        "actions": [
            _safe_action_projection(action)
            for action in repo.list_action_inbox(limit=args.limit)
        ],
        "evidence_timeline": [
            _safe_evidence_projection(item)
            for item in today.get("evidence_timeline", [])[: args.limit]
            if isinstance(item, dict)
        ],
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_start_here(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        summary = build_control_center_start_here_summary(
            today_summary=repo.today_summary(limit=args.limit)
        )
    except Exception:
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-inspect-start-here",
                error_ref="FOUNDER_LOOP_START_HERE_READ_MODEL_UNAVAILABLE",
            )
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-inspect-start-here",
        "start_here": summary,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_action_work_queue(args: argparse.Namespace) -> int:
    repo = _repository(args)
    inbox = repo.actions_inbox(limit=args.limit)
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-action-work-queue",
        "action_inbox_work_queue_read_model": inbox.get(
            "action_inbox_work_queue_read_model"
        ),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_action_tool_code_catalog(args: argparse.Namespace) -> int:
    repo = _repository(args)
    inbox = repo.actions_inbox(limit=args.limit)
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-action-tool-code-catalog",
        "action_tool_code_lane_catalog_read_model": inbox.get(
            "action_tool_code_lane_catalog_read_model"
        ),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_evidence_memory_binding(args: argparse.Namespace) -> int:
    repo = _repository(args)
    today = repo.today_summary(limit=args.limit)
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-evidence-memory-binding",
        "evidence_memory_loop_binding_read_model": today.get(
            "evidence_memory_loop_binding_read_model"
        ),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_evidence_audit_spine(args: argparse.Namespace) -> int:
    repo = _repository(args)
    timeline = repo.evidence_timeline(limit=args.limit)
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-evidence-audit-spine",
        "evidence_audit_receipt_spine_contract_ref": timeline.get(
            "evidence_audit_receipt_spine_contract_ref"
        ),
        "evidence_audit_receipt_spine": timeline.get("evidence_audit_receipt_spine"),
        "receipt_refs": list(timeline.get("receipt_refs") or []),
        "approval_refs": list(timeline.get("approval_refs") or []),
        "idempotency_refs": list(timeline.get("idempotency_refs") or []),
        "rollback_refs": list(timeline.get("rollback_refs") or []),
        "blocked_states": list(timeline.get("blocked_states") or []),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_agent_loop(args: argparse.Namespace) -> int:
    repo = _repository(args)
    today_summary = repo.today_summary(limit=args.limit)
    thread = build_agent_loop_thread_read_model(
        today_summary=today_summary,
        actions_inbox=repo.actions_inbox(limit=args.limit),
        evidence_timeline=repo.evidence_timeline(limit=args.limit),
        memory_review=repo.memory_review(limit=args.limit),
        proof_index=build_control_center_proof_index(today_summary=today_summary),
        trust_authority_matrix=build_trust_authority_matrix_read_model(
            today_summary=today_summary
        ),
    )
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-agent-loop-thread",
        "agent_loop_thread": thread,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_reasoning_truth(args: argparse.Namespace) -> int:
    repo = _repository(args)
    today_summary = repo.today_summary(limit=args.limit)
    thread = build_agent_loop_thread_read_model(
        today_summary=today_summary,
        actions_inbox=repo.actions_inbox(limit=args.limit),
        evidence_timeline=repo.evidence_timeline(limit=args.limit),
        memory_review=repo.memory_review(limit=args.limit),
        proof_index=build_control_center_proof_index(today_summary=today_summary),
        trust_authority_matrix=build_trust_authority_matrix_read_model(
            today_summary=today_summary
        ),
    )
    truth = thread["reasoning_truth"]
    revision = thread["plan_revision"]
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-inspect-reasoning",
        "reasoning_truth": truth,
        "plan_revision": revision,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    if args.json:
        _print_json(output)
        return 0

    print(
        f"Reasoning truth: {truth['confidence_band']} confidence; "
        f"{truth['ambiguity_posture']}"
    )
    print(f"Intent ref: {truth['intent_ref']}")
    print(f"Intent fingerprint: {truth['intent_fingerprint_ref']}")
    print(f"Content posture: {truth['instruction_content_posture']}")
    print("Facts:")
    for item in truth["facts"]:
        print(f"  - {item['safe_summary']} [{item['statement_ref']}]")
    print("Assumptions:")
    for item in truth["assumptions"]:
        print(f"  - {item['safe_summary']} [{item['statement_ref']}]")
    print("Unknowns:")
    for item in truth["unknowns"]:
        print(f"  - {item['safe_summary']} [{item['statement_ref']}]")
    print("Questions requiring operator input:")
    for item in truth["operator_questions"]:
        print(f"  - {item['safe_question']} [{item['question_ref']}]")
    print(
        f"Plan revision: {revision['revision_ref']} "
        f"({revision['revision_fingerprint_ref']})"
    )
    print(f"Revision reason: {revision['safe_reason']}")
    print(
        "Authority: non-authoritative reasoning and plan truth; exact "
        "request-scoped evaluation is still required."
    )
    return 0


def _inspect_cockpit_parity(args: argparse.Namespace) -> int:
    repo = _repository(args)
    today_summary = repo.today_summary(limit=args.limit)
    thread = build_agent_loop_thread_read_model(
        today_summary=today_summary,
        actions_inbox=repo.actions_inbox(limit=args.limit),
        evidence_timeline=repo.evidence_timeline(limit=args.limit),
        memory_review=repo.memory_review(limit=args.limit),
        proof_index=build_control_center_proof_index(today_summary=today_summary),
        trust_authority_matrix=build_trust_authority_matrix_read_model(
            today_summary=today_summary
        ),
    )
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-cockpit-cli-api-parity",
        "operator_decision_matrix": thread.get("operator_decision_matrix"),
        "agent_loop_thread_ref": thread.get("thread_ref"),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    if args.json:
        _print_json(output)
        return 0
    matrix = output["operator_decision_matrix"] or {}
    print("UAA governed operator cockpit")
    print("  Truth owner: Python Agent Core")
    print(f"  Contract: {matrix.get('contract_ref', 'unavailable')}")
    print(f"  Route: {matrix.get('route_ref', 'unavailable')}")
    print("  Control Center authority: presentation only; cannot mint authority")
    print("  External content: untrusted evidence, never instructions or authority")
    print("Operator decisions")
    for row in matrix.get("rows", []):
        print(f"- {row['surface']} [{row['capability_status']}]")
        print(f"  Question: {row['operator_question']}")
        print(f"  Route: {row['backend_route_ref']}")
        print(f"  CLI: {row['cli_ref']}")
        print(f"  Approval: {row['approval_posture']}")
        print("  Mutation: blocked")
        print(f"  Next: {row['safe_action']}")
        refs = [
            row["primary_ref"],
            *row["receipt_refs"],
            *row["blocked_state_refs"],
        ]
        print(f"  Refs: {', '.join(refs[:5])}")
    print(f"Next safe decision: {matrix.get('next_safe_operator_decision')}")
    return 0


def _inspect_high_maturity_spine(args: argparse.Namespace) -> int:
    repo = _repository(args)
    today_summary = repo.today_summary(limit=args.limit)
    thread = build_agent_loop_thread_read_model(
        today_summary=today_summary,
        actions_inbox=repo.actions_inbox(limit=args.limit),
        evidence_timeline=repo.evidence_timeline(limit=args.limit),
        memory_review=repo.memory_review(limit=args.limit),
        proof_index=build_control_center_proof_index(today_summary=today_summary),
        trust_authority_matrix=build_trust_authority_matrix_read_model(
            today_summary=today_summary
        ),
    )
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-high-maturity-spine",
        "agent_loop_thread_ref": thread.get("thread_ref"),
        "high_maturity_spine_readiness": thread.get(
            "high_maturity_spine_readiness"
        ),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_product_cockpit_posture(args: argparse.Namespace) -> int:
    repo = _repository(args)
    today_summary = repo.today_summary(limit=args.limit)
    thread = build_agent_loop_thread_read_model(
        today_summary=today_summary,
        actions_inbox=repo.actions_inbox(limit=args.limit),
        evidence_timeline=repo.evidence_timeline(limit=args.limit),
        memory_review=repo.memory_review(limit=args.limit),
        proof_index=build_control_center_proof_index(today_summary=today_summary),
        trust_authority_matrix=build_trust_authority_matrix_read_model(
            today_summary=today_summary
        ),
    )
    high_maturity = thread.get("high_maturity_spine_readiness") or {}
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-product-cockpit-posture",
        "agent_loop_thread_ref": thread.get("thread_ref"),
        "founder_loop_product_cockpit_posture": high_maturity.get(
            "founder_loop_product_cockpit_posture"
        ),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_trust_authority(args: argparse.Namespace) -> int:
    repo = _repository(args)
    matrix = build_trust_authority_matrix_read_model(
        today_summary=repo.today_summary(limit=args.limit)
    )
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-trust-authority",
        "trust_authority_matrix": matrix,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_proof(args: argparse.Namespace) -> int:
    repo = _repository(args)
    today_summary = repo.today_summary(limit=args.limit)
    if args.proof_ref:
        payload = build_control_center_proof_detail(
            today_summary=today_summary,
            proof_ref=args.proof_ref,
        )
        command_ref = "repo-local-command:founder-loop-inspect-proof-detail"
        key = "proof_detail"
    else:
        payload = build_control_center_proof_index(today_summary=today_summary)
        command_ref = "repo-local-command:founder-loop-inspect-proof-index"
        key = "proof_index"
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": command_ref,
        key: payload,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_web_evidence(args: argparse.Namespace) -> int:
    repo = _repository(args)
    attachments = repo.list_web_evidence_attachments(limit=args.limit)
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-web-evidence-inspect",
        "web_evidence_attachments": attachments,
        "attachment_count": len(attachments),
        "proof_ref": "proof-ref:web-evidence:product-slice",
        "safe_refs_only": True,
        "redacted_preview_omitted": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _attach_web_evidence(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        request = WebEvidenceProductSliceRequest(
            request_ref=args.request_ref,
            url=args.url,
            allowed_host=args.allowed_host,
            attach_to_ref=args.attach_to_ref,
            safe_summary=args.safe_summary,
            evidence_refs=args.evidence_ref,
            metadata_refs=args.metadata_ref,
        )
        receipt = build_web_evidence_product_slice_receipt(
            request,
            active_authority_leases=AuthorityLeaseStore().list_leases(
                active_only=True
            ),
        )
        durable_record = repo.record_web_evidence_attachment(receipt)
        replayed = bool(durable_record.get("replayed", False))
    except WebEvidenceProductSliceAuthorityError as exc:
        _print_json(
            {
                "schema_version": "founder-loop-cli:v1",
                "command_ref": "repo-local-command:founder-loop-web-evidence-attach",
                "status": "blocked",
                "error_ref": "FOUNDER_LOOP_WEB_EVIDENCE_AUTHORITY_DENIED",
                "request_ref": args.request_ref,
                "reason_refs": [
                    *exc.decision.reason_refs,
                    WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_BLOCKED_REF,
                ],
                "required_refs": {
                    "authority_decision_ref": exc.decision.decision_ref,
                    "required_mode_ref": WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_MODE_REF,
                    "required_domain_ref": WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_DOMAIN_REF,
                    "required_capability_ref": WEB_EVIDENCE_PRODUCT_SLICE_AUTHORITY_CAPABILITY_REF,
                    "safe_disable_ref": exc.decision.safe_disable_ref,
                    "rollback_ref": exc.decision.rollback_ref,
                },
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "raw_paths_omitted": True,
            }
        )
        return 1
    except (ValidationError, ValueError):
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-web-evidence-attach",
                error_ref="FOUNDER_LOOP_WEB_EVIDENCE_REQUEST_BLOCKED",
                request_ref=args.request_ref,
            )
        )
        return 1
    except (FounderLoopStorageDuplicateError, FounderLoopStorageError) as exc:
        _print_json(
            {
                "schema_version": "founder-loop-cli:v1",
                "command_ref": "repo-local-command:founder-loop-web-evidence-attach",
                "status": "blocked",
                "error_ref": str(exc) or "FOUNDER_LOOP_WEB_EVIDENCE_STORAGE_BLOCKED",
                "request_ref": args.request_ref,
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "raw_paths_omitted": True,
            }
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-web-evidence-attach",
        "web_evidence_receipt": receipt.model_copy(
            update={"replayed": replayed}
        ).model_dump(mode="json"),
        "durable_record_ref": durable_record.get("attachment_ref"),
        "safe_refs_only": True,
        "bounded_redacted_preview_returned": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _safe_loop_proof_step_projection(step: dict[str, Any]) -> dict[str, Any]:
    return {
        "step_id": step.get("step_id"),
        "surface": step.get("surface"),
        "backend_route_ref": step.get("backend_route_ref"),
        "frontend_route_ref": step.get("frontend_route_ref"),
        "status": step.get("status"),
        "source_refs": list(step.get("source_refs") or []),
        "evidence_refs": list(step.get("evidence_refs") or []),
        "receipt_refs": list(step.get("receipt_refs") or []),
        "blocked_state_refs": list(step.get("blocked_state_refs") or []),
    }


def _safe_loop_productized_surface_projection(
    binding: dict[str, Any],
) -> dict[str, Any]:
    return {
        "surface_id": binding.get("surface_id"),
        "surface": binding.get("surface"),
        "frontend_route_ref": binding.get("frontend_route_ref"),
        "backend_route_ref": binding.get("backend_route_ref"),
        "status": binding.get("status"),
        "product_posture": binding.get("product_posture"),
        "shared_ref": binding.get("shared_ref"),
        "primary_proof_ref": binding.get("primary_proof_ref"),
        "source_refs": list(binding.get("source_refs") or []),
        "receipt_refs": list(binding.get("receipt_refs") or []),
        "evidence_refs": list(binding.get("evidence_refs") or []),
        "memory_candidate_refs": list(binding.get("memory_candidate_refs") or []),
        "blocked_state_refs": list(binding.get("blocked_state_refs") or []),
        "next_safe_action": binding.get("next_safe_action"),
    }


def _loop_spine_state_dir(args: argparse.Namespace) -> Path:
    if args.state_dir is not None:
        return Path(args.state_dir)
    configured = os.environ.get(FOUNDER_LOOP_STATE_DIR_ENV)
    if configured:
        return Path(configured)
    return Path.home() / ".ultimate_ai_agent" / "founder_loop"


def _loop_spine_base_output(
    *,
    status: str,
    storage_state: str,
    inspection_error_ref: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-inspect-loop-spine",
        "contract_ref": FOUNDER_LOOP_PRODUCT_PROOF_CONTRACT_REF,
        "source": FOUNDER_LOOP_PRODUCT_PROOF_READ_MODEL_SOURCE,
        "status": status,
        "storage_state": storage_state,
        "inspection_error_ref": inspection_error_ref,
        "scenario_ref": None,
        "shared_state_ref": None,
        "full_strength_goal": None,
        "repo_safe_scope": None,
        "blocked_authority_summary": None,
        "exact_promotion_path_refs": [],
        "productized_surface_order": list(FOUNDER_LOOP_PRODUCTIZATION_SURFACE_ORDER),
        "productized_surface_count": 0,
        "productized_surface_bindings": [],
        "productized_route_refs": [],
        "productized_backend_route_refs": [],
        "loop_order": list(FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER),
        "steps": [],
        "decision_receipt_status": "state_not_found_no_write",
        "memory_review_status": "none",
        "weekly_review_status": "state_not_found_no_write",
        "morning_briefing_refs": [],
        "today_refs": [],
        "action_inbox_refs": [],
        "receipt_refs": [],
        "evidence_timeline_refs": [],
        "memory_review_candidate_refs": [],
        "memory_review_receipt_refs": [],
        "weekly_review_refs": [],
        "blocked_authority_refs": [],
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "provider_model_call_enabled": False,
        "runtime_model_call_enabled": False,
        "a2a_runtime_dispatch_enabled": False,
        "mcp_runtime_dispatch_enabled": False,
        "browser_execution_enabled": False,
        "live_web_enabled": False,
        "connector_write_enabled": False,
        "email_calendar_send_enabled": False,
        "crm_write_enabled": False,
        "account_sync_enabled": False,
        "shell_subprocess_execution_enabled": False,
        "background_autonomy_enabled": False,
        "memory_write_authorized": False,
        "context_injection_authorized": False,
        "public_beta_claim_enabled": False,
        "public_release_claim_enabled": False,
        "production_authority_enabled": False,
    }


def _inspect_loop_spine(args: argparse.Namespace) -> int:
    state_dir = _loop_spine_state_dir(args)
    if not (state_dir / "founder_loop.sqlite3").exists():
        _print_json(
            _loop_spine_base_output(
                status="metadata_only_no_state_found",
                storage_state="state_not_found_no_write",
            )
        )
        return 0

    try:
        repo = FounderLoopRepository(
            state_dir,
            seed_defaults=False,
            ensure_storage=False,
            read_only=True,
        )
        proof = repo.founder_loop_product_proof(limit=args.limit)
    except Exception:
        _print_json(
            _loop_spine_base_output(
                status="existing_state_unreadable_redacted",
                storage_state="existing_state_unreadable_redacted",
                inspection_error_ref=(
                    "error-ref:founder-loop-inspect-loop-spine:read-failed-redacted"
                ),
            )
        )
        return 0

    read_model = proof["founder_loop_v1_product_proof_read_model"]
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-inspect-loop-spine",
        "contract_ref": read_model.get("contract_ref"),
        "source": read_model.get("source"),
        "status": read_model.get("status"),
        "storage_state": "existing_state_read_only",
        "inspection_error_ref": None,
        "scenario_ref": read_model.get("scenario_ref"),
        "shared_state_ref": read_model.get("shared_state_ref"),
        "full_strength_goal": read_model.get("full_strength_goal"),
        "repo_safe_scope": read_model.get("repo_safe_scope"),
        "blocked_authority_summary": read_model.get("blocked_authority_summary"),
        "exact_promotion_path_refs": list(
            read_model.get("exact_promotion_path_refs") or []
        ),
        "productized_surface_order": list(
            read_model.get("productized_surface_order") or []
        ),
        "productized_surface_count": read_model.get("productized_surface_count"),
        "productized_surface_bindings": [
            _safe_loop_productized_surface_projection(binding)
            for binding in read_model.get("productized_surface_bindings", [])
            if isinstance(binding, dict)
        ],
        "productized_route_refs": list(read_model.get("productized_route_refs") or []),
        "productized_backend_route_refs": list(
            read_model.get("productized_backend_route_refs") or []
        ),
        "loop_order": list(read_model.get("loop_order") or []),
        "steps": [
            _safe_loop_proof_step_projection(step)
            for step in read_model.get("steps", [])[: args.limit]
            if isinstance(step, dict)
        ],
        "decision_receipt_status": read_model.get("decision_receipt_status"),
        "memory_review_status": read_model.get("memory_review_status"),
        "weekly_review_status": read_model.get("weekly_review_status"),
        "morning_briefing_refs": list(read_model.get("morning_briefing_refs") or []),
        "today_refs": list(read_model.get("today_refs") or []),
        "action_inbox_refs": list(read_model.get("action_inbox_refs") or []),
        "receipt_refs": list(read_model.get("receipt_refs") or []),
        "evidence_timeline_refs": list(read_model.get("evidence_timeline_refs") or []),
        "memory_review_candidate_refs": list(
            read_model.get("memory_review_candidate_refs") or []
        ),
        "memory_review_receipt_refs": list(
            read_model.get("memory_review_receipt_refs") or []
        ),
        "weekly_review_refs": list(read_model.get("weekly_review_refs") or []),
        "blocked_authority_refs": list(read_model.get("blocked_authority_refs") or []),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "provider_model_call_enabled": False,
        "runtime_model_call_enabled": False,
        "a2a_runtime_dispatch_enabled": False,
        "mcp_runtime_dispatch_enabled": False,
        "browser_execution_enabled": False,
        "live_web_enabled": False,
        "connector_write_enabled": False,
        "email_calendar_send_enabled": False,
        "crm_write_enabled": False,
        "account_sync_enabled": False,
        "shell_subprocess_execution_enabled": False,
        "background_autonomy_enabled": False,
        "memory_write_authorized": False,
        "context_injection_authorized": False,
        "public_beta_claim_enabled": False,
        "public_release_claim_enabled": False,
        "production_authority_enabled": False,
    }
    _print_json(output)
    return 0


def _safe_work_thread_step_projection(step: dict[str, Any]) -> dict[str, Any]:
    return {
        "step_id": step.get("step_id"),
        "surface": step.get("surface"),
        "frontend_route_ref": step.get("frontend_route_ref"),
        "backend_route_ref": step.get("backend_route_ref"),
        "status": step.get("status"),
        "safe_summary": step.get("safe_summary"),
        "source_refs": list(step.get("source_refs") or []),
        "proposal_refs": list(step.get("proposal_refs") or []),
        "receipt_refs": list(step.get("receipt_refs") or []),
        "evidence_refs": list(step.get("evidence_refs") or []),
        "blocked_authority_refs": list(step.get("blocked_authority_refs") or []),
        "next_safe_action": step.get("next_safe_action"),
    }


def _work_thread_base_output(
    *,
    status: str,
    storage_state: str,
    inspection_error_ref: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-inspect-work-thread",
        "contract_ref": UNIFIED_WORK_THREAD_CONTRACT_REF,
        "source": UNIFIED_WORK_THREAD_READ_MODEL_SOURCE,
        "status": status,
        "storage_state": storage_state,
        "inspection_error_ref": inspection_error_ref,
        "thread_ref": None,
        "safe_summary": None,
        "authority_boundary": None,
        "next_safe_action": None,
        "step_order": list(UNIFIED_WORK_THREAD_STEP_ORDER),
        "steps": [],
        "chat_turn_receipt_refs": [],
        "chat_handoff_receipt_refs": [],
        "plan_refs": [],
        "plan_proposal_refs": [],
        "action_refs": [],
        "action_decision_receipt_refs": [],
        "evidence_timeline_refs": [],
        "evidence_event_refs": [],
        "memory_review_candidate_refs": [],
        "memory_review_receipt_refs": [],
        "weekly_review_refs": [],
        "receipt_refs": [],
        "evidence_refs": [],
        "blocked_authority_refs": [],
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "provider_model_call_enabled": False,
        "runtime_model_call_enabled": False,
        "a2a_runtime_dispatch_enabled": False,
        "mcp_runtime_dispatch_enabled": False,
        "browser_execution_enabled": False,
        "live_web_enabled": False,
        "connector_read_enabled": False,
        "connector_write_enabled": False,
        "email_calendar_send_enabled": False,
        "crm_write_enabled": False,
        "account_sync_enabled": False,
        "shell_subprocess_execution_enabled": False,
        "background_autonomy_enabled": False,
        "memory_write_authorized": False,
        "context_injection_authorized": False,
        "action_execution_enabled": False,
        "public_beta_claim_enabled": False,
        "public_release_claim_enabled": False,
        "production_authority_enabled": False,
    }


def _inspect_work_thread(args: argparse.Namespace) -> int:
    state_dir = _loop_spine_state_dir(args)
    if not (state_dir / "founder_loop.sqlite3").exists():
        _print_json(
            _work_thread_base_output(
                status="metadata_only_no_state_found",
                storage_state="state_not_found_no_write",
            )
        )
        return 0

    try:
        repo = FounderLoopRepository(
            state_dir,
            seed_defaults=False,
            ensure_storage=False,
            read_only=True,
        )
        today = repo.today_summary(limit=args.limit)
    except Exception:
        _print_json(
            _work_thread_base_output(
                status="existing_state_unreadable_redacted",
                storage_state="existing_state_unreadable_redacted",
                inspection_error_ref=(
                    "error-ref:founder-loop-inspect-work-thread:read-failed-redacted"
                ),
            )
        )
        return 0

    read_model = today.get("unified_work_thread_read_model") or {}
    if not isinstance(read_model, dict):
        _print_json(
            _work_thread_base_output(
                status="backend_read_model_missing",
                storage_state="existing_state_read_only",
            )
        )
        return 0
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-inspect-work-thread",
        "contract_ref": read_model.get("contract_ref"),
        "source": read_model.get("source"),
        "status": read_model.get("status"),
        "storage_state": "existing_state_read_only",
        "inspection_error_ref": None,
        "thread_ref": read_model.get("thread_ref"),
        "safe_summary": read_model.get("safe_summary"),
        "authority_boundary": read_model.get("authority_boundary"),
        "next_safe_action": read_model.get("next_safe_action"),
        "step_order": list(read_model.get("step_order") or []),
        "steps": [
            _safe_work_thread_step_projection(step)
            for step in read_model.get("steps", [])[: args.limit]
            if isinstance(step, dict)
        ],
        "chat_turn_receipt_refs": list(read_model.get("chat_turn_receipt_refs") or []),
        "chat_handoff_receipt_refs": list(
            read_model.get("chat_handoff_receipt_refs") or []
        ),
        "plan_refs": list(read_model.get("plan_refs") or []),
        "plan_proposal_refs": list(read_model.get("plan_proposal_refs") or []),
        "action_refs": list(read_model.get("action_refs") or []),
        "action_decision_receipt_refs": list(
            read_model.get("action_decision_receipt_refs") or []
        ),
        "evidence_timeline_refs": list(read_model.get("evidence_timeline_refs") or []),
        "evidence_event_refs": list(read_model.get("evidence_event_refs") or []),
        "memory_review_candidate_refs": list(
            read_model.get("memory_review_candidate_refs") or []
        ),
        "memory_review_receipt_refs": list(
            read_model.get("memory_review_receipt_refs") or []
        ),
        "weekly_review_refs": list(read_model.get("weekly_review_refs") or []),
        "receipt_refs": list(read_model.get("receipt_refs") or []),
        "evidence_refs": list(read_model.get("evidence_refs") or []),
        "blocked_authority_refs": list(read_model.get("blocked_authority_refs") or []),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "provider_model_call_enabled": False,
        "runtime_model_call_enabled": False,
        "a2a_runtime_dispatch_enabled": False,
        "mcp_runtime_dispatch_enabled": False,
        "browser_execution_enabled": False,
        "live_web_enabled": False,
        "connector_read_enabled": False,
        "connector_write_enabled": False,
        "email_calendar_send_enabled": False,
        "crm_write_enabled": False,
        "account_sync_enabled": False,
        "shell_subprocess_execution_enabled": False,
        "background_autonomy_enabled": False,
        "memory_write_authorized": False,
        "context_injection_authorized": False,
        "action_execution_enabled": False,
        "public_beta_claim_enabled": False,
        "public_release_claim_enabled": False,
        "production_authority_enabled": False,
    }
    _print_json(output)
    return 0


def _inspect_dogfood_live_loop(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        acceptance = build_dogfood_live_loop_acceptance_read_model(
            repo=repo,
            seed_fixture=bool(args.seed_fixture),
            limit=args.limit,
        )
    except (FounderLoopStorageDuplicateError, FounderLoopStorageError) as exc:
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-inspect-dogfood-live-loop",
                error_ref=str(exc) or "FOUNDER_LOOP_DOGFOOD_LIVE_LOOP_BLOCKED",
            )
        )
        return 1

    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-inspect-dogfood-live-loop",
        "dogfood_live_loop_acceptance": acceptance,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_backend_truth(args: argparse.Namespace) -> int:
    try:
        repo = _repository(args)
        truth = build_control_center_backend_truth(repo=repo)
    except Exception:
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-inspect-backend-truth",
                error_ref="CONTROL_CENTER_BACKEND_TRUTH_STORAGE_BLOCKED",
            )
        )
        return 1

    _print_json(
        {
            "schema_version": "founder-loop-cli:v1",
            "command_ref": "repo-local-command:founder-loop-inspect-backend-truth",
            "backend_truth": truth,
            "safe_refs_only": True,
            "raw_content_omitted": True,
            "raw_paths_omitted": True,
        }
    )
    return 0


def _promote_action_envelope(args: argparse.Namespace) -> int:
    repo = _repository(args)
    command_ref = "repo-local-command:founder-loop-promote-action-envelope"
    request = FounderLoopActionEnvelopePromotionRequest(
        today_item_ref=args.today_item_ref,
        decision_reason_ref=args.decision_reason_ref,
        risk_class=args.risk_class,
        priority=args.priority,
        metadata_refs=args.metadata_ref,
    )
    try:
        receipt = repo.promote_today_item_to_action_envelope(
            request=request,
            idempotency_key_ref=args.idempotency_ref,
        )
    except FounderLoopAuthorityError as exc:
        _print_json(
            _blocked_cli_payload(
                command_ref=command_ref,
                error_ref=exc.code,
                reason_refs=exc.reason_refs,
                required_refs=exc.required_refs,
            )
        )
        return 1
    except FounderLoopStorageDuplicateError:
        _print_json(
            _blocked_cli_payload(
                command_ref=command_ref,
                error_ref="FOUNDER_LOOP_ACTION_ENVELOPE_IDEMPOTENCY_CONFLICT",
            )
        )
        return 1
    except FounderLoopStorageError as exc:
        _print_json(
            _blocked_cli_payload(
                command_ref=command_ref,
                error_ref=str(exc)
                or "FOUNDER_LOOP_ACTION_ENVELOPE_PROMOTION_BLOCKED",
            )
        )
        return 1
    except (ValueError, ValidationError):
        _print_json(
            _blocked_cli_payload(
                command_ref=command_ref,
                error_ref="FOUNDER_LOOP_ACTION_ENVELOPE_UNSAFE_INPUT",
            )
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": command_ref,
        "receipt": receipt,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _record_action_decision(args: argparse.Namespace) -> int:
    repo = _repository(args)
    request = FounderLoopActionDecisionRequest(
        approval_ref=args.approval_ref,
        decision_reason_ref=args.decision_reason_ref,
        edited_envelope_ref=args.edited_envelope_ref,
        defer_until_ref=args.defer_until_ref,
        metadata_refs=args.metadata_ref,
    )
    try:
        receipt = repo.record_action_decision(
            action_id=args.action_id,
            decision=args.decision,
            request=request,
            idempotency_key_ref=args.idempotency_ref,
        )
    except (
        FounderLoopStorageDuplicateError,
        FounderLoopStorageError,
        ValidationError,
        ValueError,
    ) as exc:
        _print_json(
            {
                "schema_version": "founder-loop-cli:v1",
                "command_ref": "repo-local-command:founder-loop-record-action-decision",
                "status": "blocked",
                "error_ref": str(exc) or "FOUNDER_LOOP_ACTION_DECISION_BLOCKED",
                "action_ref": args.action_id,
                "decision": args.decision,
                "idempotency_ref": args.idempotency_ref,
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "raw_paths_omitted": True,
            }
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-record-action-decision",
        "receipt": receipt,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _commit_local_task(args: argparse.Namespace) -> int:
    repo = _repository(args)
    item_ref = action_id_to_item_ref(args.action_id)
    action = next(
        (
            candidate
            for candidate in repo.list_action_inbox(limit=200)
            if candidate.get("item_ref") == item_ref
        ),
        None,
    )
    if action is None:
        _print_json(
            {
                "schema_version": "founder-loop-cli:v1",
                "command_ref": "repo-local-command:founder-loop-commit-local-task",
                "status": "blocked",
                "safe_message": "No safe Action Inbox item exists for this action ref.",
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "raw_paths_omitted": True,
            }
        )
        return 1
    request = FounderLoopLocalTaskCommitRequest(
        approval_ref=args.approval_ref,
        decision_reason_ref=args.decision_reason_ref,
        metadata_refs=args.metadata_ref,
    )
    try:
        receipt = repo.commit_local_task(
            action_id=args.action_id,
            request=request,
            idempotency_key_ref=args.idempotency_ref,
        )
    except (
        FounderLoopStorageDuplicateError,
        FounderLoopStorageError,
        ValidationError,
        ValueError,
    ) as exc:
        _print_json(
            {
                "schema_version": "founder-loop-cli:v1",
                "command_ref": "repo-local-command:founder-loop-commit-local-task",
                "status": "blocked",
                "error_ref": str(exc) or "FOUNDER_LOOP_LOCAL_TASK_COMMIT_BLOCKED",
                "action_ref": args.action_id,
                "approval_ref": args.approval_ref,
                "idempotency_ref": args.idempotency_ref,
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "raw_paths_omitted": True,
            }
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-commit-local-task",
        "receipt": receipt,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_memory_workbench(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        workbench = repo.memory_workbench(
            query_ref=args.query_ref,
            limit=args.limit,
        )
    except ValueError:
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-memory-workbench",
                error_ref="FOUNDER_LOOP_MEMORY_WORKBENCH_REF_DENIED",
            )
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-workbench",
        "workbench": workbench,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _search_memory(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        search = repo.memory_search(
            query_ref=args.query_ref,
            kind=args.kind,
            source_ref=args.source_ref,
            project_ref=args.project_ref,
            person_ref=args.person_ref,
            org_ref=args.org_ref,
            deal_ref=args.deal_ref,
            review_state=args.review_state,
            quality_state=args.quality_state,
            stale_state=args.stale_state,
            conflict_state=args.conflict_state,
            limit=args.limit,
        )
    except ValueError:
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-memory-search",
                error_ref="FOUNDER_LOOP_MEMORY_SEARCH_REF_DENIED",
            )
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-search",
        "search": search,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_memory_impact_graph(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        impact_graph = repo.memory_impact_graph(
            query_ref=args.query_ref,
            limit=args.limit,
        )
    except ValueError:
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-memory-impact-graph",
                error_ref="FOUNDER_LOOP_MEMORY_IMPACT_GRAPH_REF_DENIED",
            )
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-impact-graph",
        "impact_graph": impact_graph,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_memory_follow_ups(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        follow_up_queue = repo.memory_follow_up_queue(
            query_ref=args.query_ref,
            limit=args.limit,
        )
    except ValueError:
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-memory-follow-ups",
                error_ref="FOUNDER_LOOP_MEMORY_FOLLOW_UPS_REF_DENIED",
            )
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-follow-ups",
        "follow_up_queue": follow_up_queue,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_memory_recall_health(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        recall_health = repo.memory_recall_health_v2(
            query_ref=args.query_ref,
            limit=args.limit,
        )
    except ValueError:
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-memory-recall-health",
                error_ref="FOUNDER_LOOP_MEMORY_RECALL_HEALTH_REF_DENIED",
            )
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-recall-health",
        "recall_health": recall_health,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_memory_retrieval_diagnostics(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        diagnostics = repo.memory_retrieval_diagnostics(
            query_ref=args.query_ref,
            limit=args.limit,
        )
    except ValueError:
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-memory-retrieval-diagnostics",
                error_ref="FOUNDER_LOOP_MEMORY_RETRIEVAL_DIAGNOSTICS_REF_DENIED",
            )
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-retrieval-diagnostics",
        "retrieval_diagnostics": diagnostics,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_memory_citation_integrity(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        citation_integrity = repo.memory_citation_integrity(
            query_ref=args.query_ref,
            limit=args.limit,
        )
    except ValueError:
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-memory-citation-integrity",
                error_ref="FOUNDER_LOOP_MEMORY_CITATION_INTEGRITY_REF_DENIED",
            )
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-citation-integrity",
        "citation_integrity": citation_integrity,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_memory_quality_issues(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        quality_issues = repo.memory_quality_issues(
            query_ref=args.query_ref,
            limit=args.limit,
        )
    except ValueError:
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-memory-quality-issues",
                error_ref="FOUNDER_LOOP_MEMORY_QUALITY_ISSUES_REF_DENIED",
            )
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-quality-issues",
        "quality_issues": quality_issues,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_memory_maintenance_runs(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        maintenance_runs = repo.memory_maintenance_runs(
            query_ref=args.query_ref,
            limit=args.limit,
        )
    except ValueError:
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-memory-maintenance-runs",
                error_ref="FOUNDER_LOOP_MEMORY_MAINTENANCE_RUNS_REF_DENIED",
            )
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-maintenance-runs",
        "maintenance_runs": maintenance_runs,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def render_memory_context_manifest_readable(context_manifest: dict[str, Any]) -> str:
    governed = context_manifest.get("governed_context") or {}
    budget = governed.get("budget") or {}
    return "\n".join(
        [
            "Memory context manifest",
            f"  Status: {governed.get('status', context_manifest.get('status'))}",
            f"  Manifest: {governed.get('context_manifest_ref', 'unavailable')}",
            f"  Receipt: {governed.get('context_receipt_ref', 'unavailable')}",
            (
                "  Selected / candidates: "
                f"{governed.get('selection_count', 0)} / "
                f"{governed.get('candidate_count', 0)}"
            ),
            (
                "  Capacity: "
                f"{budget.get('used_tokens', 0)} / "
                f"{budget.get('max_tokens', 0)} estimated units"
            ),
            "  Context injection: blocked (preview only)",
        ]
    )


def _inspect_memory_context_manifest(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        context_manifest = repo.memory_context_manifest(
            query_ref=args.query_ref,
            limit=args.limit,
        )
    except ValueError:
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-memory-context-manifest",
                error_ref="FOUNDER_LOOP_MEMORY_CONTEXT_MANIFEST_REF_DENIED",
            )
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-context-manifest",
        "context_manifest": context_manifest,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    if args.json:
        _print_json(output)
    else:
        print(render_memory_context_manifest_readable(context_manifest))
    return 0


def _inspect_memory_context_pack_preview(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        context_pack_preview = repo.memory_context_pack_preview(
            context_pack_ref=args.context_pack_ref,
        )
    except ValueError:
        _print_json(
            _blocked_cli_payload(
                command_ref=(
                    "repo-local-command:founder-loop-memory-context-pack-preview"
                ),
                error_ref="FOUNDER_LOOP_MEMORY_CONTEXT_PACK_PREVIEW_REF_DENIED",
            )
        )
        return 1
    except FounderLoopStorageError as exc:
        _print_json(
            _blocked_cli_payload(
                command_ref=(
                    "repo-local-command:founder-loop-memory-context-pack-preview"
                ),
                error_ref=str(exc)
                or "FOUNDER_LOOP_MEMORY_CONTEXT_PACK_PREVIEW_NOT_FOUND",
            )
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-context-pack-preview",
        "context_pack_preview": context_pack_preview,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _record_memory_context_pack_action_proposal(args: argparse.Namespace) -> int:
    repo = _repository(args)
    command_ref = "repo-local-command:founder-loop-memory-context-pack-action-proposal"
    request = MemoryContextPackActionProposalRequest(
        exact_approval_scope_ref=args.exact_approval_scope_ref,
        approval_ref=args.approval_ref,
        decision_reason_ref=args.decision_reason_ref,
        risk_class=args.risk_class,
        priority=args.priority,
        metadata_refs=args.metadata_ref or [],
    )
    try:
        receipt = repo.record_memory_context_pack_action_proposal(
            context_pack_ref=args.context_pack_ref,
            request=request,
            idempotency_key_ref=args.idempotency_ref,
        )
    except FounderLoopAuthorityError as exc:
        _print_json(
            _blocked_cli_payload(
                command_ref=command_ref,
                error_ref=exc.code,
                reason_refs=exc.reason_refs,
                required_refs=exc.required_refs,
            )
        )
        return 1
    except FounderLoopStorageDuplicateError:
        _print_json(
            _blocked_cli_payload(
                command_ref=command_ref,
                error_ref=(
                    "FOUNDER_LOOP_MEMORY_CONTEXT_PACK_ACTION_IDEMPOTENCY_CONFLICT"
                ),
            )
        )
        return 1
    except FounderLoopStorageError as exc:
        _print_json(
            _blocked_cli_payload(
                command_ref=command_ref,
                error_ref=str(exc)
                or "FOUNDER_LOOP_MEMORY_CONTEXT_PACK_ACTION_PROPOSAL_BLOCKED",
            )
        )
        return 1
    except (ValueError, ValidationError):
        _print_json(
            _blocked_cli_payload(
                command_ref=command_ref,
                error_ref="FOUNDER_LOOP_MEMORY_CONTEXT_PACK_ACTION_UNSAFE_INPUT",
            )
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": command_ref,
        "memory_context_pack_action_proposal_receipt": receipt,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "action_execution_enabled": False,
        "context_injection_authorized": False,
    }
    _print_json(output)
    return 0


def _inspect_memory_learning_posture(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        workbench = repo.memory_workbench(
            query_ref=args.query_ref,
            limit=args.limit,
        )
    except ValueError:
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-memory-learning-posture",
                error_ref="FOUNDER_LOOP_MEMORY_LEARNING_POSTURE_REF_DENIED",
            )
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-learning-posture",
        "learning_posture": workbench.get("learning_posture"),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_memory_bounded_posture(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        workbench = repo.memory_workbench(
            query_ref=args.query_ref,
            limit=args.limit,
        )
    except ValueError:
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-memory-bounded-posture",
                error_ref="FOUNDER_LOOP_MEMORY_BOUNDED_POSTURE_REF_DENIED",
            )
        )
        return 1
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-bounded-posture",
        "bounded_memory_posture": workbench.get("bounded_memory_posture"),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_prompt_omitted": True,
        "raw_response_omitted": True,
        "raw_provider_payload_omitted": True,
    }
    _print_json(output)
    return 0


def _inspect_memory_receipts(args: argparse.Namespace) -> int:
    repo = _repository(args)
    review = repo.memory_review(limit=args.limit)
    reviewed_recall_records = repo.list_memory_review_recall_records()
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-receipts",
        "route_ref": review.get("route_ref"),
        "decision_route_refs": review.get("decision_route_refs"),
        "exact_write_scope_ref": review.get("exact_write_scope_ref"),
        "approval_binding": review.get("approval_binding"),
        "write_safe_disable_posture": review.get("write_safe_disable_posture"),
        "reviewed_recall_write_authorized_decisions": review.get(
            "reviewed_recall_write_authorized_decisions"
        ),
        "reviewed_recall_record_refs": [
            f"memory-record-ref:{record.get('memory_id')}"
            for record in reviewed_recall_records
        ],
        "reviewed_recall_record_count": len(reviewed_recall_records),
        "decision_receipts": list(review.get("decision_receipts") or []),
        "decision_receipt_refs": list(review.get("decision_receipt_refs") or []),
        "workbench_health": review.get("workbench_health"),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _record_memory_feedback(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        request = MemoryFeedbackRequest(
            target_ref=args.target_ref,
            target_kind=args.target_kind,
            feedback_kind=args.feedback_kind,
            reviewer_ref=args.reviewer_ref,
            evidence_refs=args.evidence_ref,
            reason_refs=args.reason_ref,
            metadata_refs=args.metadata_ref,
            blocked_state_refs=(
                args.blocked_state_ref
                or list(MEMORY_FEEDBACK_QUALITY_BLOCKED_STATE_REFS)
            ),
        )
        receipt = repo.record_memory_feedback(
            request=request,
            idempotency_key_ref=args.idempotency_ref,
        )
    except (ValidationError, ValueError):
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-memory-feedback",
                error_ref="FOUNDER_LOOP_MEMORY_FEEDBACK_REF_DENIED",
                target_ref=args.target_ref,
                feedback_kind=args.feedback_kind,
                idempotency_ref=args.idempotency_ref,
            )
        )
        return 1
    except (FounderLoopStorageDuplicateError, FounderLoopStorageError) as exc:
        _print_json(
            {
                "schema_version": "founder-loop-cli:v1",
                "command_ref": "repo-local-command:founder-loop-memory-feedback",
                "status": "blocked",
                "error_ref": str(exc) or "FOUNDER_LOOP_MEMORY_FEEDBACK_BLOCKED",
                "target_ref": args.target_ref,
                "feedback_kind": args.feedback_kind,
                "idempotency_ref": args.idempotency_ref,
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "raw_paths_omitted": True,
            }
        )
        return 1

    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-feedback",
        "receipt": receipt,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _record_memory_decision(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        request = MemoryReviewDecisionRequest(
            reviewer_ref=args.reviewer_ref,
            corrected_summary_ref=args.corrected_summary_ref,
            corrected_safe_summary=args.corrected_safe_summary,
            source_refs=args.source_ref,
            evidence_refs=args.evidence_ref,
            metadata_refs=args.metadata_ref,
            merge_refs=args.merge_ref,
            supersedes_refs=args.supersedes_ref,
            forget_request_ref=args.forget_request_ref,
            blocked_state_refs=(
                args.blocked_state_ref
                or list(FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS)
            ),
        )
        receipt = repo.record_memory_review_decision(
            candidate_ref=args.candidate_ref,
            decision=args.decision,
            request=request,
            idempotency_key_ref=args.idempotency_ref,
        )
    except (ValidationError, ValueError):
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-memory-decision",
                error_ref="FOUNDER_LOOP_MEMORY_DECISION_REF_DENIED",
                candidate_ref=args.candidate_ref,
                decision=args.decision,
                idempotency_ref=args.idempotency_ref,
            )
        )
        return 1
    except (FounderLoopStorageDuplicateError, FounderLoopStorageError) as exc:
        _print_json(
            {
                "schema_version": "founder-loop-cli:v1",
                "command_ref": "repo-local-command:founder-loop-memory-decision",
                "status": "blocked",
                "error_ref": str(exc) or "FOUNDER_LOOP_MEMORY_DECISION_BLOCKED",
                "candidate_ref": args.candidate_ref,
                "decision": args.decision,
                "idempotency_ref": args.idempotency_ref,
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "raw_paths_omitted": True,
            }
        )
        return 1

    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-decision",
        "receipt": receipt,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _record_manual_memory_candidate(args: argparse.Namespace) -> int:
    repo = _repository(args)
    try:
        request = ManualMemoryCandidateRequest(
            candidate_kind=args.candidate_kind,
            title=args.title,
            safe_summary=args.safe_summary,
            priority=args.priority,
            reviewer_ref=args.reviewer_ref,
            source_refs=args.source_ref,
            provenance_refs=args.provenance_ref,
            evidence_refs=args.evidence_ref,
            missing_evidence_refs=args.missing_evidence_ref,
            related_entity_refs=args.related_entity_ref,
            tag_refs=args.tag_ref,
            metadata_refs=args.metadata_ref,
            blocked_state_refs=(
                args.blocked_state_ref or list(MEMORY_MANUAL_INTAKE_BLOCKED_STATE_REFS)
            ),
        )
        receipt = repo.record_manual_memory_candidate(
            request=request,
            idempotency_key_ref=args.idempotency_ref,
        )
    except (ValidationError, ValueError):
        _print_json(
            _blocked_cli_payload(
                command_ref="repo-local-command:founder-loop-memory-manual-candidate",
                error_ref="FOUNDER_LOOP_MANUAL_MEMORY_CANDIDATE_REF_DENIED",
                candidate_kind=args.candidate_kind,
                idempotency_ref=args.idempotency_ref,
            )
        )
        return 1
    except (FounderLoopStorageDuplicateError, FounderLoopStorageError) as exc:
        _print_json(
            {
                "schema_version": "founder-loop-cli:v1",
                "command_ref": "repo-local-command:founder-loop-memory-manual-candidate",
                "status": "blocked",
                "error_ref": str(exc) or "FOUNDER_LOOP_MANUAL_MEMORY_CANDIDATE_BLOCKED",
                "candidate_kind": args.candidate_kind,
                "idempotency_ref": args.idempotency_ref,
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "raw_paths_omitted": True,
            }
        )
        return 1

    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-memory-manual-candidate",
        "receipt": receipt,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }
    _print_json(output)
    return 0


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _blocked_cli_payload(
    *,
    command_ref: str,
    error_ref: str,
    **extra: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": command_ref,
        "status": "blocked",
        "error_ref": error_ref,
        **{key: value for key, value in extra.items() if value is not None},
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
    }


def _configure_exact_action_state(args: argparse.Namespace) -> None:
    if args.state_dir is not None:
        os.environ[FOUNDER_LOOP_STATE_DIR_ENV] = args.state_dir
    if args.authority_state_dir is not None:
        os.environ[AUTHORITY_STATE_DIR_ENV] = args.authority_state_dir
    clear_founder_attention_workflow_cache()


def _exact_action_status(args: argparse.Namespace) -> int:
    _configure_exact_action_state(args)
    try:
        workflow = get_founder_attention_workflow()
        source_refs = workflow.required_source_refs(args.today_item_ref)
        verified = workflow.verified_status(args.today_item_ref)
        action = verified.action
        target = next(iter(workflow.mission_service.targets.values()))
    except ValueError:
        print("Exact Founder Loop action: blocked (attention item unavailable)")
        return 1
    payload = {
        "schema_version": "founder-loop-exact-action-cli:v1",
        "status": action.status,
        "today_item_ref": args.today_item_ref,
        "target_ref": target.target_ref,
        "root_ref": target.root_ref,
        "path_ref": target.path_ref,
        "required_inspected_source_refs": list(source_refs),
        "mission_scoped_lease_required": True,
        "receipt_refs": list(action.receipt_refs),
        "exact_approval_required": verified.exact_approval_required,
        "execution_performed": verified.execution_performed,
        "execution_truth_status": verified.execution_truth_status,
        "approval_truth_status": verified.approval_truth_status,
        "recovery_required": verified.recovery_required,
        "safe_refs_only": True,
    }
    if args.json:
        _print_json(payload)
    else:
        print(f"Exact Founder Loop action: {action.status.replace('_', ' ')}")
        print(f"Today item: {args.today_item_ref}")
        print(f"Target: {target.safe_label} ({target.target_ref})")
        print("Required source refs to review:")
        for ref in source_refs:
            print(f"  - {ref}")
        if verified.execution_performed is True:
            print("Execution: performed")
        elif verified.execution_performed is False:
            print("Execution: not performed")
        else:
            print("Execution: unknown; recovery required")
    return 0


def _prepare_exact_action(args: argparse.Namespace) -> int:
    _configure_exact_action_state(args)
    try:
        workflow = get_founder_attention_workflow()
        target = next(iter(workflow.mission_service.targets.values()))
        source_review = workflow.review_source_refs(
            today_item_ref=args.today_item_ref,
            inspected_source_refs=tuple(args.source_ref),
            idempotency_ref=f"{args.idempotency_ref}:source-review",
            mission_ref=args.mission_ref,
            lease_ref=args.lease_ref,
        )
        request = build_attention_workflow_request(
            workflow_ref=args.workflow_ref,
            today_item_ref=args.today_item_ref,
            inspected_source_refs=tuple(args.source_ref),
            source_review_receipt_ref=source_review.source_review_receipt_ref,
            mission_ref=args.mission_ref,
            run_ref=args.run_ref,
            lease_ref=args.lease_ref,
            start_deadline=utc_now() + timedelta(seconds=args.deadline_seconds),
            idempotency_ref=args.idempotency_ref,
            target_ref=target.target_ref,
        )
        prepared = workflow.prepare(request)
    except (ValidationError, ValueError):
        print("Exact Founder Loop action: blocked (exact binding or authority denied)")
        return 1
    payload = {
        "schema_version": "founder-loop-exact-action-cli:v1",
        **prepared.model_dump(mode="json"),
        "source_review_receipt_ref": source_review.source_review_receipt_ref,
        "execution_performed": False,
        "safe_refs_only": True,
        "raw_paths_omitted": True,
        "raw_content_omitted": True,
    }
    if args.json:
        _print_json(payload)
    else:
        print("Exact Founder Loop action: prepared for separate review")
        print(f"Proposal: {prepared.proposal_ref}")
        print(f"Approval request: {prepared.approval_request_ref}")
        print(f"Source review: {source_review.source_review_receipt_ref}")
        print("Execution: not performed")
    return 0


def _run_exact_action(args: argparse.Namespace) -> int:
    if not args.confirm_exact_approval:
        print("Exact Founder Loop action: blocked (explicit approval confirmation required)")
        return 1
    _configure_exact_action_state(args)
    try:
        workflow = get_founder_attention_workflow()
        prepared = workflow.mission_service.prepared_proposal(args.proposal_ref)
        prepared_request = workflow.mission_service.prepared_request(args.proposal_ref)
        if (
            prepared is None
            or prepared_request is None
            or prepared.proposal.approval_request_ref != args.approval_request_ref
            or prepared_request.mission_ref != args.mission_ref
            or prepared_request.run_ref != args.run_ref
            or prepared_request.lease_ref != args.lease_ref
        ):
            raise ValueError("FOUNDER_LOOP_ATTENTION_REVIEWED_PROPOSAL_REQUIRED")
        if workflow.verified_status(args.today_item_ref).action.status == "receipt_recorded":
            approval_ref = args.approval_ref
        else:
            approval_ref = workflow.grant_exact_approval(
                workflow_ref=args.workflow_ref,
                today_item_ref=args.today_item_ref,
                inspected_source_refs=tuple(args.source_ref),
                source_review_receipt_ref=args.source_review_receipt_ref,
                proposal_ref=args.proposal_ref,
                approved_by_actor_ref="operator-ref:local-user",
                approval_ref=args.approval_ref,
            )
        result = workflow.execute(
            workflow_ref=args.workflow_ref,
            today_item_ref=args.today_item_ref,
            inspected_source_refs=tuple(args.source_ref),
            source_review_receipt_ref=args.source_review_receipt_ref,
            proposal_ref=args.proposal_ref,
            approval_ref=approval_ref,
            owner_ref=attention_execution_owner_ref(
                proposal_ref=args.proposal_ref,
                idempotency_ref=args.idempotency_ref,
            ),
        )
    except (ValidationError, ValueError):
        print("Exact Founder Loop action: blocked (exact binding or authority denied)")
        return 1
    payload = {
        "schema_version": "founder-loop-exact-action-cli:v1",
        **result.model_dump(mode="json"),
        "safe_refs_only": True,
        "raw_paths_omitted": True,
        "raw_content_omitted": True,
    }
    if args.json:
        _print_json(payload)
    else:
        print("Exact Founder Loop action: receipt recorded")
        print(f"Completion: {result.completion_ref}")
        print("Memory candidate: not created for metadata-only evidence")
        print("Receipt refs:")
        for ref in result.receipt_refs:
            print(f"  - {ref}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="uaa_founder_loop",
        description="Inspect local Founder Loop state and create review-only Action envelopes.",
    )
    parser.add_argument(
        "--state-dir",
        help="Use an explicit local state directory; the value is not echoed in output.",
    )
    parser.add_argument(
        "--authority-state-dir",
        help="Use an explicit authority state directory; the value is not echoed in output.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    exact_status_parser = subparsers.add_parser(
        "exact-action-status",
        help="Inspect one exact metadata-only Founder Loop action without execution.",
    )
    exact_status_parser.add_argument("--today-item-ref", required=True)
    exact_status_parser.add_argument("--json", action="store_true")
    exact_status_parser.set_defaults(func=_exact_action_status)

    exact_prepare_parser = subparsers.add_parser(
        "prepare-exact-action",
        help="Review source refs and prepare one exact metadata action without approval.",
    )
    exact_prepare_parser.add_argument("--workflow-ref", required=True)
    exact_prepare_parser.add_argument("--today-item-ref", required=True)
    exact_prepare_parser.add_argument("--source-ref", action="append", required=True)
    exact_prepare_parser.add_argument("--mission-ref", required=True)
    exact_prepare_parser.add_argument("--run-ref", required=True)
    exact_prepare_parser.add_argument("--lease-ref", required=True)
    exact_prepare_parser.add_argument("--idempotency-ref", required=True)
    exact_prepare_parser.add_argument("--deadline-seconds", type=int, default=600)
    exact_prepare_parser.add_argument("--json", action="store_true")
    exact_prepare_parser.set_defaults(func=_prepare_exact_action)

    exact_run_parser = subparsers.add_parser(
        "run-exact-action",
        help="Approve and execute one previously reviewed exact metadata proposal.",
    )
    exact_run_parser.add_argument("--workflow-ref", required=True)
    exact_run_parser.add_argument("--today-item-ref", required=True)
    exact_run_parser.add_argument("--source-ref", action="append", required=True)
    exact_run_parser.add_argument("--mission-ref", required=True)
    exact_run_parser.add_argument("--run-ref", required=True)
    exact_run_parser.add_argument("--lease-ref", required=True)
    exact_run_parser.add_argument("--idempotency-ref", required=True)
    exact_run_parser.add_argument("--proposal-ref", required=True)
    exact_run_parser.add_argument("--approval-request-ref", required=True)
    exact_run_parser.add_argument("--source-review-receipt-ref", required=True)
    exact_run_parser.add_argument("--approval-ref", required=True)
    exact_run_parser.add_argument("--confirm-exact-approval", action="store_true")
    exact_run_parser.add_argument("--json", action="store_true")
    exact_run_parser.set_defaults(func=_run_exact_action)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Print safe refs for Today, Actions, receipts, and Evidence Timeline state.",
    )
    inspect_parser.add_argument("--limit", type=int, default=12)
    inspect_parser.set_defaults(func=_inspect_state)

    start_here_parser = subparsers.add_parser(
        "inspect-start-here",
        help=("Print the backend-owned Start Here loop contract with safe refs only."),
    )
    start_here_parser.add_argument("--limit", type=int, default=12)
    start_here_parser.set_defaults(func=_inspect_start_here)

    action_work_queue_parser = subparsers.add_parser(
        "inspect-action-work-queue",
        help="Print the backend-owned Action Inbox work queue summary.",
    )
    action_work_queue_parser.add_argument("--limit", type=int, default=50)
    action_work_queue_parser.set_defaults(func=_inspect_action_work_queue)

    action_tool_code_parser = subparsers.add_parser(
        "inspect-action-tool-code-catalog",
        help=(
            "Print the backend-owned Action/Tool/Code lane catalog with "
            "approval, receipt, and blocked-authority posture."
        ),
    )
    action_tool_code_parser.add_argument("--limit", type=int, default=50)
    action_tool_code_parser.set_defaults(func=_inspect_action_tool_code_catalog)

    evidence_memory_binding_parser = subparsers.add_parser(
        "inspect-evidence-memory-binding",
        help="Print the backend-owned Evidence/Memory loop binding summary.",
    )
    evidence_memory_binding_parser.add_argument("--limit", type=int, default=50)
    evidence_memory_binding_parser.set_defaults(func=_inspect_evidence_memory_binding)

    evidence_audit_spine_parser = subparsers.add_parser(
        "inspect-evidence-audit-spine",
        help=(
            "Print the backend-owned Evidence audit receipt spine with "
            "grouped timeline and receipt-envelope refs."
        ),
    )
    evidence_audit_spine_parser.add_argument("--limit", type=int, default=50)
    evidence_audit_spine_parser.set_defaults(func=_inspect_evidence_audit_spine)

    agent_loop_parser = subparsers.add_parser(
        "inspect-agent-loop",
        help=(
            "Print the backend-owned Agent Loop thread over Today, Actions, "
            "Evidence, Proof, Memory, and Trust refs."
        ),
    )
    agent_loop_parser.add_argument("--limit", type=int, default=50)
    agent_loop_parser.set_defaults(func=_inspect_agent_loop)

    reasoning_parser = subparsers.add_parser(
        "inspect-reasoning",
        help=(
            "Explain deterministic intent and immutable plan-revision truth; "
            "human-readable output is the default."
        ),
    )
    reasoning_parser.add_argument("--limit", type=int, default=12)
    reasoning_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the same backend-owned safe truth as redacted JSON.",
    )
    reasoning_parser.set_defaults(func=_inspect_reasoning_truth)

    cockpit_parity_parser = subparsers.add_parser(
        "inspect-cockpit-parity",
        help=(
            "Print the backend-owned cockpit operator decision matrix with "
            "matching route, CLI, evidence, proof, and blocked-authority refs."
        ),
    )
    cockpit_parity_parser.add_argument("--limit", type=int, default=50)
    cockpit_parity_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the same redacted backend-owned cockpit truth as JSON.",
    )
    cockpit_parity_parser.set_defaults(func=_inspect_cockpit_parity)

    high_maturity_spine_parser = subparsers.add_parser(
        "inspect-high-maturity-spine",
        help=(
            "Print the backend-owned W1-W13 High-Maturity Agent Spine "
            "coverage map with evidence, tests, gaps, and blocked authority refs."
        ),
    )
    high_maturity_spine_parser.add_argument("--limit", type=int, default=50)
    high_maturity_spine_parser.set_defaults(func=_inspect_high_maturity_spine)

    product_cockpit_posture_parser = subparsers.add_parser(
        "inspect-product-cockpit-posture",
        help=(
            "Print the backend-owned Founder Loop product cockpit posture with "
            "route, CLI, UI, evidence, test, and blocked-authority refs."
        ),
    )
    product_cockpit_posture_parser.add_argument("--limit", type=int, default=50)
    product_cockpit_posture_parser.set_defaults(
        func=_inspect_product_cockpit_posture
    )

    trust_authority_parser = subparsers.add_parser(
        "inspect-trust-authority",
        help="Print the backend-owned Trust authority matrix.",
    )
    trust_authority_parser.add_argument("--limit", type=int, default=50)
    trust_authority_parser.set_defaults(func=_inspect_trust_authority)

    proof_parser = subparsers.add_parser(
        "inspect-proof",
        help="Print the backend-owned universal proof index or proof detail.",
    )
    proof_parser.add_argument("proof_ref", nargs="?")
    proof_parser.add_argument("--limit", type=int, default=50)
    proof_parser.set_defaults(func=_inspect_proof)

    inspect_web_evidence_parser = subparsers.add_parser(
        "inspect-web-evidence",
        help="Print stored web evidence product-slice receipt refs; no fetch is performed.",
    )
    inspect_web_evidence_parser.add_argument("--limit", type=int, default=20)
    inspect_web_evidence_parser.set_defaults(func=_inspect_web_evidence)

    attach_web_evidence_parser = subparsers.add_parser(
        "attach-web-evidence",
        help=(
            "Attach one allowlisted HTTPS GET web evidence preview through "
            "WebAccessGateway."
        ),
    )
    attach_web_evidence_parser.add_argument("--request-ref", required=True)
    attach_web_evidence_parser.add_argument("--url", required=True)
    attach_web_evidence_parser.add_argument("--allowed-host", required=True)
    attach_web_evidence_parser.add_argument(
        "--attach-to-ref",
        default="founder-loop:daily-loop",
    )
    attach_web_evidence_parser.add_argument(
        "--safe-summary",
        default=(
            "Attach one allowlisted read-only web evidence preview to the local loop."
        ),
    )
    attach_web_evidence_parser.add_argument(
        "--evidence-ref", action="append", default=[]
    )
    attach_web_evidence_parser.add_argument(
        "--metadata-ref", action="append", default=[]
    )
    attach_web_evidence_parser.set_defaults(func=_attach_web_evidence)

    loop_spine_parser = subparsers.add_parser(
        "inspect-loop-spine",
        help=(
            "Print the seeded/demo-safe Morning Briefing to Weekly Review loop path "
            "from the backend-owned product proof read model."
        ),
    )
    loop_spine_parser.add_argument("--limit", type=int, default=7)
    loop_spine_parser.set_defaults(func=_inspect_loop_spine)

    work_thread_parser = subparsers.add_parser(
        "inspect-work-thread",
        help=(
            "Print the backend-owned Chat to Weekly Review unified work thread "
            "from existing Founder Loop safe refs."
        ),
    )
    work_thread_parser.add_argument("--limit", type=int, default=7)
    work_thread_parser.set_defaults(func=_inspect_work_thread)

    dogfood_live_loop_parser = subparsers.add_parser(
        "inspect-dogfood-live-loop",
        help=(
            "Print one backend-owned dogfood loop acceptance summary; optionally "
            "seed the deterministic local fixture first."
        ),
    )
    dogfood_live_loop_parser.add_argument("--limit", type=int, default=50)
    dogfood_live_loop_parser.add_argument(
        "--seed-fixture",
        action="store_true",
        help=(
            "Seed exact local approval and local-task commit receipt refs before "
            "inspection. This uses existing local-only backend lanes."
        ),
    )
    dogfood_live_loop_parser.set_defaults(func=_inspect_dogfood_live_loop)

    backend_truth_parser = subparsers.add_parser(
        "inspect-backend-truth",
        help=(
            "Print the short-lived, revision-bound backend truth envelope for "
            "critical Control Center surfaces without granting authority."
        ),
    )
    backend_truth_parser.set_defaults(func=_inspect_backend_truth)

    promote_parser = subparsers.add_parser(
        "promote-action-envelope",
        help="Create a review-only Action envelope receipt from a Today item ref.",
    )
    promote_parser.add_argument("--today-item-ref", required=True)
    promote_parser.add_argument("--idempotency-ref", required=True)
    promote_parser.add_argument(
        "--decision-reason-ref",
        default="decision-reason-ref:founder-loop:cli-today-action-envelope",
    )
    promote_parser.add_argument(
        "--risk-class",
        choices=["low", "medium", "high", "critical"],
        default="medium",
    )
    promote_parser.add_argument(
        "--priority",
        choices=["low", "medium", "high"],
        default="medium",
    )
    promote_parser.add_argument(
        "--metadata-ref",
        action="append",
        default=[],
        help="Safe metadata ref to attach to the receipt. May be repeated.",
    )
    promote_parser.set_defaults(func=_promote_action_envelope)

    decision_parser = subparsers.add_parser(
        "record-action-decision",
        help="Record a backend-owned Action Inbox decision receipt without executing the action.",
    )
    decision_parser.add_argument("--action-id", required=True)
    decision_parser.add_argument(
        "--decision",
        choices=["approve", "edit", "reject", "defer"],
        required=True,
    )
    decision_parser.add_argument("--idempotency-ref", required=True)
    decision_parser.add_argument(
        "--approval-ref",
        default=None,
        help=(
            "Optional safe approval ref. If omitted for approve, Python Core "
            "records a backend-owned exact local approval ref."
        ),
    )
    decision_parser.add_argument(
        "--decision-reason-ref",
        default="decision-reason-ref:founder-loop:cli-action-decision",
    )
    decision_parser.add_argument("--edited-envelope-ref", default=None)
    decision_parser.add_argument("--defer-until-ref", default=None)
    decision_parser.add_argument(
        "--metadata-ref",
        action="append",
        default=[],
        help="Safe metadata ref to attach to the receipt. May be repeated.",
    )
    decision_parser.set_defaults(func=_record_action_decision)

    commit_parser = subparsers.add_parser(
        "commit-local-task",
        help="Commit an approved local_task_create Action Inbox item to local task state.",
    )
    commit_parser.add_argument("--action-id", required=True)
    commit_parser.add_argument("--idempotency-ref", required=True)
    commit_parser.add_argument("--approval-ref", required=True)
    commit_parser.add_argument(
        "--decision-reason-ref",
        default="decision-reason-ref:founder-loop:cli-local-task-commit",
    )
    commit_parser.add_argument(
        "--metadata-ref",
        action="append",
        default=[],
        help="Safe metadata ref to attach to the receipt. May be repeated.",
    )
    commit_parser.set_defaults(func=_commit_local_task)

    memory_workbench_parser = subparsers.add_parser(
        "memory-workbench",
        help="Inspect the backend-owned Memory Workbench read model.",
    )
    memory_workbench_parser.add_argument("--query-ref", default=None)
    memory_workbench_parser.add_argument("--limit", type=int, default=20)
    memory_workbench_parser.set_defaults(func=_inspect_memory_workbench)

    memory_search_parser = subparsers.add_parser(
        "memory-search",
        help="Search reviewed safe memory summaries and refs without semantic search.",
    )
    memory_search_parser.add_argument("--query-ref", default=None)
    memory_search_parser.add_argument("--kind", default=None)
    memory_search_parser.add_argument("--source-ref", default=None)
    memory_search_parser.add_argument("--project-ref", default=None)
    memory_search_parser.add_argument("--person-ref", default=None)
    memory_search_parser.add_argument("--org-ref", default=None)
    memory_search_parser.add_argument("--deal-ref", default=None)
    memory_search_parser.add_argument("--review-state", default=None)
    memory_search_parser.add_argument("--quality-state", default=None)
    memory_search_parser.add_argument("--stale-state", default=None)
    memory_search_parser.add_argument("--conflict-state", default=None)
    memory_search_parser.add_argument("--limit", type=int, default=20)
    memory_search_parser.set_defaults(func=_search_memory)

    memory_impact_parser = subparsers.add_parser(
        "memory-impact-graph",
        help="Inspect the FCC-MEM-015 Memory Impact Graph read model.",
    )
    memory_impact_parser.add_argument("--query-ref", default=None)
    memory_impact_parser.add_argument("--limit", type=int, default=20)
    memory_impact_parser.set_defaults(func=_inspect_memory_impact_graph)

    memory_follow_ups_parser = subparsers.add_parser(
        "memory-follow-ups",
        help="Inspect proposal-only memory-derived follow-up candidates.",
    )
    memory_follow_ups_parser.add_argument("--query-ref", default=None)
    memory_follow_ups_parser.add_argument("--limit", type=int, default=20)
    memory_follow_ups_parser.set_defaults(func=_inspect_memory_follow_ups)

    memory_recall_health_parser = subparsers.add_parser(
        "memory-recall-health",
        help="Inspect FCC-MEM-015 Recall Health Dashboard V2 metrics.",
    )
    memory_recall_health_parser.add_argument("--query-ref", default=None)
    memory_recall_health_parser.add_argument("--limit", type=int, default=20)
    memory_recall_health_parser.set_defaults(func=_inspect_memory_recall_health)

    memory_retrieval_diagnostics_parser = subparsers.add_parser(
        "memory-retrieval-diagnostics",
        help="Inspect FCC-MEM-016 retrieval diagnostics without context injection.",
    )
    memory_retrieval_diagnostics_parser.add_argument("--query-ref", default=None)
    memory_retrieval_diagnostics_parser.add_argument("--limit", type=int, default=20)
    memory_retrieval_diagnostics_parser.set_defaults(
        func=_inspect_memory_retrieval_diagnostics
    )

    memory_citation_integrity_parser = subparsers.add_parser(
        "memory-citation-integrity",
        help="Inspect FCC-MEM-017 context-pack citation integrity.",
    )
    memory_citation_integrity_parser.add_argument("--query-ref", default=None)
    memory_citation_integrity_parser.add_argument("--limit", type=int, default=20)
    memory_citation_integrity_parser.set_defaults(
        func=_inspect_memory_citation_integrity
    )

    memory_quality_issues_parser = subparsers.add_parser(
        "memory-quality-issues",
        help="Inspect FCC-MEM-018 feedback-derived memory quality issues.",
    )
    memory_quality_issues_parser.add_argument("--query-ref", default=None)
    memory_quality_issues_parser.add_argument("--limit", type=int, default=20)
    memory_quality_issues_parser.set_defaults(func=_inspect_memory_quality_issues)

    memory_maintenance_runs_parser = subparsers.add_parser(
        "memory-maintenance-runs",
        help="Inspect FCC-MEM-019 proposal-only maintenance scan output.",
    )
    memory_maintenance_runs_parser.add_argument("--query-ref", default=None)
    memory_maintenance_runs_parser.add_argument("--limit", type=int, default=20)
    memory_maintenance_runs_parser.set_defaults(func=_inspect_memory_maintenance_runs)

    memory_context_manifest_parser = subparsers.add_parser(
        "memory-context-manifest",
        help="Inspect FCC-MEM-020 context manifests without hidden injection.",
    )
    memory_context_manifest_parser.add_argument("--query-ref", default=None)
    memory_context_manifest_parser.add_argument("--limit", type=int, default=20)
    memory_context_manifest_parser.add_argument("--json", action="store_true")
    memory_context_manifest_parser.set_defaults(func=_inspect_memory_context_manifest)

    memory_context_pack_preview_parser = subparsers.add_parser(
        "memory-context-pack-preview",
        help="Inspect one FCC-MEM-020 context-pack preview without runtime injection.",
    )
    memory_context_pack_preview_parser.add_argument("--context-pack-ref", required=True)
    memory_context_pack_preview_parser.set_defaults(
        func=_inspect_memory_context_pack_preview
    )

    memory_context_pack_action_parser = subparsers.add_parser(
        "memory-context-pack-action-proposal",
        help=(
            "Record one AuthorityLease-gated internal Action proposal from a "
            "reviewed context pack without execution."
        ),
    )
    memory_context_pack_action_parser.add_argument("--context-pack-ref", required=True)
    memory_context_pack_action_parser.add_argument(
        "--idempotency-ref",
        required=True,
        help="Safe idempotency ref for the proposal receipt.",
    )
    memory_context_pack_action_parser.add_argument(
        "--exact-approval-scope-ref",
        default=None,
    )
    memory_context_pack_action_parser.add_argument("--approval-ref", default=None)
    memory_context_pack_action_parser.add_argument(
        "--decision-reason-ref",
        default="decision-reason-ref:phase6.1-context-pack-action-proposal",
    )
    memory_context_pack_action_parser.add_argument(
        "--risk-class",
        choices=["low", "medium", "high", "critical"],
        default="low",
    )
    memory_context_pack_action_parser.add_argument(
        "--priority",
        choices=["low", "medium", "high"],
        default="medium",
    )
    memory_context_pack_action_parser.add_argument(
        "--metadata-ref",
        action="append",
        default=[],
    )
    memory_context_pack_action_parser.set_defaults(
        func=_record_memory_context_pack_action_proposal
    )

    memory_learning_posture_parser = subparsers.add_parser(
        "memory-learning-posture",
        help="Inspect governed memory learning, feedback, and context posture.",
    )
    memory_learning_posture_parser.add_argument("--query-ref", default=None)
    memory_learning_posture_parser.add_argument("--limit", type=int, default=20)
    memory_learning_posture_parser.set_defaults(func=_inspect_memory_learning_posture)

    memory_bounded_posture_parser = subparsers.add_parser(
        "memory-bounded-posture",
        help="Inspect bounded governed memory capacity, target, and review posture.",
    )
    memory_bounded_posture_parser.add_argument("--query-ref", default=None)
    memory_bounded_posture_parser.add_argument("--limit", type=int, default=20)
    memory_bounded_posture_parser.set_defaults(func=_inspect_memory_bounded_posture)

    memory_receipts_parser = subparsers.add_parser(
        "memory-receipts",
        help="Inspect memory review lifecycle receipt refs and workbench health.",
    )
    memory_receipts_parser.add_argument("--limit", type=int, default=20)
    memory_receipts_parser.set_defaults(func=_inspect_memory_receipts)

    memory_feedback_parser = subparsers.add_parser(
        "record-memory-feedback",
        help="Record a memory feedback quality signal receipt without memory writes.",
    )
    memory_feedback_parser.add_argument("--target-ref", required=True)
    memory_feedback_parser.add_argument(
        "--target-kind",
        choices=[
            "memory_candidate",
            "reviewed_recall",
            "impact_graph_node",
            "context_pack_preview",
            "follow_up_proposal",
            "today_item",
            "action_proposal",
            "evidence_event",
        ],
        required=True,
    )
    memory_feedback_parser.add_argument(
        "--feedback-kind",
        choices=[
            "useful",
            "stale",
            "missing",
            "wrong",
            "duplicate",
            "conflict",
            "irrelevant",
            "privacy_concern",
        ],
        required=True,
    )
    memory_feedback_parser.add_argument("--idempotency-ref", required=True)
    memory_feedback_parser.add_argument(
        "--reviewer-ref",
        default="actor-ref:founder-loop-cli-memory-feedback",
    )
    memory_feedback_parser.add_argument("--evidence-ref", action="append", default=[])
    memory_feedback_parser.add_argument("--reason-ref", action="append", default=[])
    memory_feedback_parser.add_argument("--metadata-ref", action="append", default=[])
    memory_feedback_parser.add_argument(
        "--blocked-state-ref",
        action="append",
        default=[],
    )
    memory_feedback_parser.set_defaults(func=_record_memory_feedback)

    memory_decision_parser = subparsers.add_parser(
        "record-memory-decision",
        help="Record a Memory Review lifecycle receipt without executing memory delete/export/context authority.",
    )
    memory_decision_parser.add_argument("--candidate-ref", required=True)
    memory_decision_parser.add_argument(
        "--decision",
        choices=[
            "accept",
            "correct",
            "reject",
            "defer",
            "merge",
            "supersede",
            "expire",
            "forget_request",
        ],
        required=True,
    )
    memory_decision_parser.add_argument("--idempotency-ref", required=True)
    memory_decision_parser.add_argument(
        "--reviewer-ref",
        default="actor-ref:founder-loop-cli-memory-review",
    )
    memory_decision_parser.add_argument("--corrected-summary-ref", default=None)
    memory_decision_parser.add_argument("--corrected-safe-summary", default=None)
    memory_decision_parser.add_argument("--forget-request-ref", default=None)
    memory_decision_parser.add_argument("--source-ref", action="append", default=[])
    memory_decision_parser.add_argument("--evidence-ref", action="append", default=[])
    memory_decision_parser.add_argument("--metadata-ref", action="append", default=[])
    memory_decision_parser.add_argument("--merge-ref", action="append", default=[])
    memory_decision_parser.add_argument("--supersedes-ref", action="append", default=[])
    memory_decision_parser.add_argument(
        "--blocked-state-ref",
        action="append",
        default=[],
    )
    memory_decision_parser.set_defaults(func=_record_memory_decision)

    manual_memory_parser = subparsers.add_parser(
        "memory-manual-candidate",
        help="Create a manual safe-summary Memory Review candidate; no recall record is created.",
    )
    manual_memory_parser.add_argument("--candidate-kind", required=True)
    manual_memory_parser.add_argument("--title", required=True)
    manual_memory_parser.add_argument("--safe-summary", required=True)
    manual_memory_parser.add_argument("--idempotency-ref", required=True)
    manual_memory_parser.add_argument(
        "--priority",
        choices=["low", "medium", "high"],
        default="medium",
    )
    manual_memory_parser.add_argument(
        "--reviewer-ref",
        default="actor-ref:founder-loop-cli-memory-intake",
    )
    manual_memory_parser.add_argument("--source-ref", action="append", default=[])
    manual_memory_parser.add_argument("--provenance-ref", action="append", default=[])
    manual_memory_parser.add_argument("--evidence-ref", action="append", default=[])
    manual_memory_parser.add_argument(
        "--missing-evidence-ref",
        action="append",
        default=[],
    )
    manual_memory_parser.add_argument(
        "--related-entity-ref",
        action="append",
        default=[],
    )
    manual_memory_parser.add_argument("--tag-ref", action="append", default=[])
    manual_memory_parser.add_argument("--metadata-ref", action="append", default=[])
    manual_memory_parser.add_argument(
        "--blocked-state-ref",
        action="append",
        default=[],
    )
    manual_memory_parser.set_defaults(func=_record_manual_memory_candidate)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
