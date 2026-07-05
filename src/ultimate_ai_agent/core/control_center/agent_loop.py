from __future__ import annotations

from typing import Any


AGENT_LOOP_THREAD_CONTRACT_REF = (
    "contract-ref:goatcitadel-catchup-agent-loop-thread:v1"
)
AGENT_LOOP_THREAD_ROUTE_REF = "GET /control-center/agent-loop/thread"
AGENT_LOOP_THREAD_CLI_REF = "scripts/dev/uaa_founder_loop.py inspect-agent-loop"
AGENT_LOOP_THREAD_SOURCE = "python_core_agent_loop_thread_read_model"
AGENT_LOOP_THREAD_BLOCKED_AUTHORITY_REFS = (
    "blocked-state:agent-loop:no-runtime-model-calls",
    "blocked-state:agent-loop:no-provider-sdk-calls",
    "blocked-state:agent-loop:no-live-web-fetching",
    "blocked-state:agent-loop:no-browser-automation",
    "blocked-state:agent-loop:no-connector-writes",
    "blocked-state:agent-loop:no-unrestricted-shell",
    "blocked-state:agent-loop:no-plugin-runtime-import",
    "blocked-state:agent-loop:no-background-autonomy",
    "blocked-state:agent-loop:no-production-authority",
    "blocked-state:agent-loop:no-raw-payload-persistence",
)


def build_agent_loop_thread_read_model(
    *,
    today_summary: dict[str, Any],
    actions_inbox: dict[str, Any],
    evidence_timeline: dict[str, Any],
    memory_review: dict[str, Any],
    proof_index: dict[str, Any],
    trust_authority_matrix: dict[str, Any],
) -> dict[str, Any]:
    """Compose the safe operator loop from existing backend-owned read models."""

    action_items = _records(actions_inbox.get("items") or today_summary.get("actions"))
    plan_items = _records(today_summary.get("plans"))
    memory_items = _records(memory_review.get("items") or today_summary.get("memory_review_queue"))
    evidence_events = _records(evidence_timeline.get("events"))
    proof_items = _records(proof_index.get("items") or proof_index.get("proofs"))
    next_safe_actions = _records(today_summary.get("next_safe_actions"))

    primary_action = action_items[0] if action_items else {}
    primary_plan = plan_items[0] if plan_items else {}
    primary_ref = _first_string(
        primary_action.get("item_ref"),
        primary_plan.get("plan_ref"),
        primary_plan.get("item_ref"),
        "work-request-ref:agent-loop:current",
    )
    primary_summary = _safe_text(
        primary_action.get("safe_summary")
        or primary_action.get("title")
        or primary_plan.get("safe_summary")
        or primary_plan.get("title"),
        fallback="Inspect the current governed founder loop before selecting the next safe action.",
    )

    evidence_refs = _dedupe(
        [
            "evidence-ref:control-center:agent-loop-thread",
            "evidence-ref:founder-loop:today-summary",
            "evidence-ref:founder-loop:action-inbox",
            *_refs_from_records(action_items, "evidence_refs"),
            *_refs_from_records(memory_items, "evidence_refs"),
            *_string_values(evidence_timeline.get("receipt_refs")),
        ]
    )
    proof_refs = _dedupe(
        [
            *_refs_from_records(proof_items, "proof_ref"),
            *_string_values(proof_index.get("proof_refs")),
            *_refs_from_records(action_items, "receipt_refs"),
        ]
    )[:12]
    memory_candidate_refs = _dedupe(
        [
            *_refs_from_records(memory_items, "candidate_ref"),
            *_string_values(today_summary.get("memory_candidate_refs")),
        ]
    )
    blocked_refs = _dedupe(
        [
            *AGENT_LOOP_THREAD_BLOCKED_AUTHORITY_REFS,
            *_string_values(today_summary.get("blocked_states")),
            *_string_values(actions_inbox.get("blocked_states")),
            *_string_values(memory_review.get("blocked_state_refs")),
            *_string_values(evidence_timeline.get("blocked_states")),
        ]
    )

    proposed_actions = [
        {
            "action_ref": _safe_text(action.get("item_ref"), fallback="action-ref:unknown"),
            "title": _safe_text(action.get("title"), fallback="Untitled action"),
            "status": _safe_text(action.get("status"), fallback="unknown"),
            "action_kind": _safe_text(action.get("action_kind"), fallback="proposal"),
            "approval_required": bool(action.get("approval_required")),
            "approval_envelope_ref": _safe_text(
                action.get("approval_envelope_ref"),
                fallback="approval-envelope-ref:not-required",
            ),
            "state_change_readiness": _safe_text(
                action.get("state_change_readiness"),
                fallback="proposal_only",
            ),
            "execution_enabled": False,
            "receipt_refs": _string_values(action.get("receipt_refs")),
            "evidence_refs": _string_values(action.get("evidence_refs")),
            "next_safe_action": _safe_text(
                action.get("next_safe_action"),
                fallback="Review the action posture in Action Inbox.",
            ),
        }
        for action in action_items[:6]
    ]

    plan_steps = [
        {
            "step_ref": _first_string(
                plan.get("plan_ref"),
                plan.get("item_ref"),
                f"plan-step-ref:agent-loop:{index + 1}",
            ),
            "title": _safe_text(plan.get("title"), fallback=f"Plan step {index + 1}"),
            "status": _safe_text(plan.get("status"), fallback="proposal_only"),
            "evidence_refs": _string_values(plan.get("evidence_refs")),
            "blocked_state_refs": _string_values(plan.get("blocked_state_refs")),
            "execution_enabled": False,
        }
        for index, plan in enumerate(plan_items[:6])
    ]
    if not plan_steps:
        plan_steps = [
            {
                "step_ref": "plan-step-ref:agent-loop:inspect",
                "title": "Inspect backend-owned loop refs",
                "status": "implemented_read_only",
                "evidence_refs": ["evidence-ref:founder-loop:today-summary"],
                "blocked_state_refs": [],
                "execution_enabled": False,
            },
            {
                "step_ref": "plan-step-ref:agent-loop:operator-decision",
                "title": "Choose the next safe operator decision",
                "status": "proposal_only",
                "evidence_refs": ["evidence-ref:founder-loop:action-inbox"],
                "blocked_state_refs": [
                    "blocked-state:agent-loop:no-action-execution"
                ],
                "execution_enabled": False,
            },
        ]

    next_decision = _safe_text(
        (next_safe_actions[0].get("label") if next_safe_actions else None)
        or (next_safe_actions[0].get("safe_summary") if next_safe_actions else None)
        or actions_inbox.get("disabled_state_label")
        or actions_inbox.get("next_safe_action"),
        fallback="Review Action Inbox and Memory Review refs before any approved local mutation.",
    )

    return {
        "schema_version": "goatcitadel_catchup_agent_loop_thread.v1",
        "contract_ref": AGENT_LOOP_THREAD_CONTRACT_REF,
        "thread_ref": "agent-loop-thread:goatcitadel-catchup:current",
        "status": "implemented_backend_owned_read_model_no_new_authority",
        "capability_status": "partial",
        "source": AGENT_LOOP_THREAD_SOURCE,
        "backend_owned": True,
        "local_read_model_only": True,
        "safe_refs_only": True,
        "raw_content_included": False,
        "route_ref": AGENT_LOOP_THREAD_ROUTE_REF,
        "cli_ref": AGENT_LOOP_THREAD_CLI_REF,
        "work_request": {
            "request_ref": primary_ref,
            "safe_summary": primary_summary,
            "source_surface": _safe_text(
                primary_action.get("surface") or today_summary.get("surface"),
                fallback="Today",
            ),
        },
        "intent": {
            "status": _safe_text(
                today_summary.get("user_intent_understanding_status"),
                fallback="implemented_review_required",
            ),
            "classification_ref": "intent-ref:agent-loop:current-request",
            "ambiguity_state": (
                "operator_review_required"
                if today_summary.get("user_intent_review_required", True)
                else "reviewed"
            ),
            "confidence_label": "bounded_from_existing_refs",
            "low_confidence_asks_user": bool(
                today_summary.get("user_intent_low_confidence_asks_user", True)
            ),
            "action_execution_enabled": False,
        },
        "facts": [
            {
                "fact_ref": "fact-ref:agent-loop:backend-owned-surfaces",
                "summary": (
                    "Today, Action Inbox, Evidence, Proof, Memory, and Trust are "
                    "read from Python Core/API read models."
                ),
                "evidence_refs": [
                    "GET /control-center/today/summary",
                    "GET /control-center/actions/inbox",
                    "GET /control-center/evidence/timeline",
                ],
            },
            {
                "fact_ref": "fact-ref:agent-loop:proposal-first-authority",
                "summary": (
                    "The loop can show plans, proposed actions, receipts, proof refs, "
                    "and memory review candidates without treating them as authority."
                ),
                "evidence_refs": evidence_refs[:6],
            },
        ],
        "assumptions": [
            {
                "assumption_ref": "assumption-ref:agent-loop:operator-selects-next-safe-action",
                "summary": (
                    "The operator chooses the next decision; Control Center does not "
                    "infer approval or execute broad workflows from the display."
                ),
                "review_required": True,
            }
        ],
        "unknowns": [
            {
                "unknown_ref": "unknown-ref:agent-loop:external-runtime-results",
                "summary": (
                    "External model, connector, browser, shell, plugin, and production "
                    "results are unknown because those broad lanes remain blocked."
                ),
                "blocked_state_refs": list(AGENT_LOOP_THREAD_BLOCKED_AUTHORITY_REFS),
            }
        ],
        "plan": {
            "status": "proposal_first",
            "revision_ref": "plan-revision-ref:agent-loop:current",
            "revision_count": len(plan_steps),
            "steps": plan_steps,
        },
        "proposed_actions": proposed_actions,
        "approval_posture": {
            "approval_required_before_mutation": True,
            "control_center_mints_authority": False,
            "approval_refs_are_identifiers_only": True,
            "action_execution_enabled": False,
            "exact_local_task_lane_visible": any(
                action.get("action_kind") == "local_task_create"
                for action in action_items
            ),
            "decision_route_refs": _string_values(
                actions_inbox.get("decision_route_refs")
            ),
        },
        "current_state": {
            "state": "partial_governed_loop_visible",
            "blocked_state_refs": blocked_refs,
            "degraded_state_refs": [],
            "next_safe_operator_decision": next_decision,
        },
        "evidence": {
            "route_ref": "GET /control-center/evidence/timeline",
            "event_count": int(evidence_timeline.get("event_count") or len(evidence_events)),
            "evidence_refs": evidence_refs[:16],
            "proof_refs": proof_refs,
        },
        "memory_review": {
            "route_ref": "GET /control-center/memory/review",
            "candidate_refs": memory_candidate_refs[:12],
            "candidate_count": len(memory_candidate_refs) or len(memory_items),
            "decision_receipt_refs": _string_values(
                memory_review.get("decision_receipt_refs")
            ),
            "automatic_memory_write_authorized": False,
            "context_injection_authorized": False,
            "next_safe_action": _safe_text(
                memory_review.get("authority_boundary"),
                fallback="Review memory candidates without hidden context injection.",
            ),
        },
        "surface_bindings": [
            {"surface": "Chat", "route_ref": "GET /control-center/chat/turns"},
            {"surface": "Today", "route_ref": "GET /control-center/today/summary"},
            {"surface": "Plans", "route_ref": "GET /control-center/today/summary"},
            {"surface": "Actions", "route_ref": "GET /control-center/actions/inbox"},
            {"surface": "Proof", "route_ref": "GET /control-center/proof/index"},
            {"surface": "Evidence", "route_ref": "GET /control-center/evidence/timeline"},
            {"surface": "Memory", "route_ref": "GET /control-center/memory/review"},
            {"surface": "Trust", "route_ref": "GET /control-center/trust-authority/matrix"},
        ],
        "authority_posture": {
            "python_core_owns_truth": True,
            "control_center_mints_authority": False,
            "runtime_model_calls_enabled": False,
            "provider_sdk_calls_enabled": False,
            "live_web_fetching_enabled": False,
            "browser_automation_enabled": False,
            "connector_writes_enabled": False,
            "unrestricted_shell_enabled": False,
            "plugin_runtime_import_enabled": False,
            "memory_write_authority_enabled": False,
            "background_autonomy_enabled": False,
            "production_authority_enabled": False,
        },
        "blocked_authority_refs": list(AGENT_LOOP_THREAD_BLOCKED_AUTHORITY_REFS),
        "redactions_applied": [
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "raw_prompt_omitted",
            "raw_response_omitted",
            "raw_provider_payload_omitted",
            "raw_local_paths_omitted",
            "read_only_control_center_projection",
        ],
    }


def _records(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _string_values(value: object) -> list[str]:
    if isinstance(value, str) and value:
        return [_safe_text(value)]
    if not isinstance(value, list):
        return []
    return [_safe_text(item) for item in value if isinstance(item, str) and item]


def _refs_from_records(records: list[dict[str, Any]], field: str) -> list[str]:
    values: list[str] = []
    for record in records:
        value = record.get(field)
        if isinstance(value, list):
            values.extend(_string_values(value))
        elif isinstance(value, str):
            values.append(_safe_text(value))
    return values


def _first_string(*values: object) -> str:
    for value in values:
        if isinstance(value, str) and value:
            return _safe_text(value)
    return "ref:unavailable"


def _safe_text(value: object, *, fallback: str = "not available") -> str:
    if not isinstance(value, str) or not value:
        return fallback
    compact = " ".join(value.split())
    lowered = compact.lower()
    unsafe_markers = (
        "raw_prompt",
        "raw response",
        "provider_payload",
        "api_key",
        "bearer ",
        "/users/",
        "password",
        "token=",
    )
    if any(marker in lowered for marker in unsafe_markers):
        return fallback
    return compact[:240]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output
