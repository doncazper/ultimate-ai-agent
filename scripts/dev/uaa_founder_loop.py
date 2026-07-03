#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
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
from ultimate_ai_agent.core.control_center import (  # noqa: E402
    FOUNDER_LOOP_PRODUCT_PROOF_CONTRACT_REF,
    FOUNDER_LOOP_PRODUCT_PROOF_READ_MODEL_SOURCE,
    FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER,
    UNIFIED_WORK_THREAD_CONTRACT_REF,
    UNIFIED_WORK_THREAD_READ_MODEL_SOURCE,
    UNIFIED_WORK_THREAD_STEP_ORDER,
)
from ultimate_ai_agent.core.control_center.local_tasks import (  # noqa: E402
    FounderLoopLocalTaskCommitRequest,
)
from ultimate_ai_agent.core.control_center.proof import (  # noqa: E402
    build_control_center_proof_detail,
    build_control_center_proof_index,
)
from ultimate_ai_agent.core.control_center.start_here import (  # noqa: E402
    build_control_center_start_here_summary,
)
from ultimate_ai_agent.core.memory import (  # noqa: E402
    FCC_MEMORY_REVIEW_DECISION_BLOCKED_STATE_REFS,
    MEMORY_FEEDBACK_QUALITY_BLOCKED_STATE_REFS,
    MEMORY_MANUAL_INTAKE_BLOCKED_STATE_REFS,
    ManualMemoryCandidateRequest,
    MemoryFeedbackRequest,
    MemoryReviewDecisionRequest,
)
from ultimate_ai_agent.core.storage import (  # noqa: E402
    FOUNDER_LOOP_STATE_DIR_ENV,
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
        "local_task_commit_approval_ref": action.get(
            "local_task_commit_approval_ref"
        ),
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
        "task_decomposition_review_only": action.get(
            "task_decomposition_review_only"
        ),
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
        "task_decomposition_contract_ref": plan.get(
            "task_decomposition_contract_ref"
        ),
        "task_decomposition_request_ref": plan.get(
            "task_decomposition_request_ref"
        ),
        "task_decomposition_review_envelope_ref": plan.get(
            "task_decomposition_review_envelope_ref"
        ),
        "task_decomposition_proposal_ref": plan.get(
            "task_decomposition_proposal_ref"
        ),
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
            plan.get("task_decomposition_suggested_action_inbox_proposal_refs")
            or []
        ),
        "task_decomposition_required_approvals": list(
            plan.get("task_decomposition_required_approvals") or []
        ),
        "task_decomposition_blocked_authority_refs": list(
            plan.get("task_decomposition_blocked_authority_refs") or []
        ),
        "task_decomposition_review_only": plan.get(
            "task_decomposition_review_only"
        ),
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
        "evidence_timeline_refs": list(
            read_model.get("evidence_timeline_refs") or []
        ),
        "memory_review_candidate_refs": list(
            read_model.get("memory_review_candidate_refs") or []
        ),
        "memory_review_receipt_refs": list(
            read_model.get("memory_review_receipt_refs") or []
        ),
        "weekly_review_refs": list(read_model.get("weekly_review_refs") or []),
        "blocked_authority_refs": list(
            read_model.get("blocked_authority_refs") or []
        ),
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
        "chat_turn_receipt_refs": list(
            read_model.get("chat_turn_receipt_refs") or []
        ),
        "chat_handoff_receipt_refs": list(
            read_model.get("chat_handoff_receipt_refs") or []
        ),
        "plan_refs": list(read_model.get("plan_refs") or []),
        "plan_proposal_refs": list(read_model.get("plan_proposal_refs") or []),
        "action_refs": list(read_model.get("action_refs") or []),
        "action_decision_receipt_refs": list(
            read_model.get("action_decision_receipt_refs") or []
        ),
        "evidence_timeline_refs": list(
            read_model.get("evidence_timeline_refs") or []
        ),
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
        "blocked_authority_refs": list(
            read_model.get("blocked_authority_refs") or []
        ),
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


def _promote_action_envelope(args: argparse.Namespace) -> int:
    repo = _repository(args)
    request = FounderLoopActionEnvelopePromotionRequest(
        today_item_ref=args.today_item_ref,
        decision_reason_ref=args.decision_reason_ref,
        risk_class=args.risk_class,
        priority=args.priority,
        metadata_refs=args.metadata_ref,
    )
    receipt = repo.promote_today_item_to_action_envelope(
        request=request,
        idempotency_key_ref=args.idempotency_ref,
    )
    output = {
        "schema_version": "founder-loop-cli:v1",
        "command_ref": "repo-local-command:founder-loop-promote-action-envelope",
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
    _print_json(output)
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
                args.blocked_state_ref
                or list(MEMORY_MANUAL_INTAKE_BLOCKED_STATE_REFS)
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="uaa_founder_loop",
        description="Inspect local Founder Loop state and create review-only Action envelopes.",
    )
    parser.add_argument(
        "--state-dir",
        help="Use an explicit local state directory; the value is not echoed in output.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Print safe refs for Today, Actions, receipts, and Evidence Timeline state.",
    )
    inspect_parser.add_argument("--limit", type=int, default=12)
    inspect_parser.set_defaults(func=_inspect_state)

    start_here_parser = subparsers.add_parser(
        "inspect-start-here",
        help=(
            "Print the backend-owned Start Here loop contract with safe refs only."
        ),
    )
    start_here_parser.add_argument("--limit", type=int, default=12)
    start_here_parser.set_defaults(func=_inspect_start_here)

    action_work_queue_parser = subparsers.add_parser(
        "inspect-action-work-queue",
        help="Print the backend-owned Action Inbox work queue summary.",
    )
    action_work_queue_parser.add_argument("--limit", type=int, default=50)
    action_work_queue_parser.set_defaults(func=_inspect_action_work_queue)

    evidence_memory_binding_parser = subparsers.add_parser(
        "inspect-evidence-memory-binding",
        help="Print the backend-owned Evidence/Memory loop binding summary.",
    )
    evidence_memory_binding_parser.add_argument("--limit", type=int, default=50)
    evidence_memory_binding_parser.set_defaults(
        func=_inspect_evidence_memory_binding
    )

    proof_parser = subparsers.add_parser(
        "inspect-proof",
        help="Print the backend-owned universal proof index or proof detail.",
    )
    proof_parser.add_argument("proof_ref", nargs="?")
    proof_parser.add_argument("--limit", type=int, default=12)
    proof_parser.set_defaults(func=_inspect_proof)

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
    memory_context_manifest_parser.set_defaults(func=_inspect_memory_context_manifest)

    memory_context_pack_preview_parser = subparsers.add_parser(
        "memory-context-pack-preview",
        help="Inspect one FCC-MEM-020 context-pack preview without runtime injection.",
    )
    memory_context_pack_preview_parser.add_argument("--context-pack-ref", required=True)
    memory_context_pack_preview_parser.set_defaults(
        func=_inspect_memory_context_pack_preview
    )

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
