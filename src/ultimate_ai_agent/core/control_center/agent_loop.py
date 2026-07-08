from __future__ import annotations

from typing import Any

from ultimate_ai_agent.core.control_center.web_evidence_product_slice import (
    WEB_EVIDENCE_PRODUCT_SLICE_BLOCKED_AUTHORITY_REFS,
    WEB_EVIDENCE_PRODUCT_SLICE_CLI_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_CONTRACT_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_PROOF_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF,
    WEB_EVIDENCE_PRODUCT_SLICE_SAFE_DISABLE_REF,
)
from ultimate_ai_agent.core.network.governed_web_evidence import (
    GOVERNED_WEB_EVIDENCE_DOCS,
    GOVERNED_WEB_EVIDENCE_REQUEST_PATH,
    GOVERNED_WEB_EVIDENCE_STATUS_PATH,
)


AGENT_LOOP_THREAD_CONTRACT_REF = (
    "contract-ref:runtime-agent-loop-thread:v1"
)
AGENT_LOOP_THREAD_ROUTE_REF = "GET /control-center/agent-loop/thread"
AGENT_LOOP_THREAD_CLI_REF = "scripts/dev/uaa_founder_loop.py inspect-agent-loop"
AGENT_LOOP_COCKPIT_PARITY_CONTRACT_REF = (
    "contract-ref:runtime-cockpit-cli-api-parity:v1"
)
AGENT_LOOP_COCKPIT_PARITY_CLI_REF = (
    "scripts/dev/uaa_founder_loop.py inspect-cockpit-parity"
)
HIGH_MATURITY_SPINE_CONTRACT_REF = (
    "contract-ref:high-maturity-agent-spine-coverage:v1"
)
SYSTEM_AGENT_EVAL_COVERAGE_CONTRACT_REF = (
    "contract-ref:system-agent-eval-coverage:v1"
)
EXTERNAL_INFORMATION_HANDLING_CONTRACT_REF = (
    "contract-ref:external-information-handling-posture:v1"
)
HIGH_MATURITY_SPINE_CLI_REF = (
    "scripts/dev/uaa_founder_loop.py inspect-high-maturity-spine"
)
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
HIGH_MATURITY_COMPONENT_IDS = (
    "W1",
    "W2",
    "W3",
    "W4",
    "W5",
    "W6",
    "W7",
    "W8",
    "W9",
    "W10",
    "W11",
    "W12",
    "W13",
)
SYSTEM_AGENT_EVAL_CATEGORY_IDS = (
    "route_choice",
    "ambiguity_handling",
    "task_decomposition",
    "approval_needed_detection",
    "memory_citation_selection",
    "blocked_state_explanation",
    "evidence_completeness",
)
EXTERNAL_INFORMATION_POSTURE_CATEGORY_IDS = (
    "trusted_local_evidence",
    "operator_supplied_external_metadata",
    "allowlisted_gateway_preview",
    "untrusted_content_quarantine",
    "browser_observe",
    "browser_action",
    "provider_search_scrape",
    "external_content_authority_isolation",
)


def build_external_information_handling_posture() -> dict[str, Any]:
    """Return web/external information posture without adding new fetch authority."""

    rows = [
        _external_information_row(
            category_id="trusted_local_evidence",
            label="Trusted local evidence",
            status="implemented_local_read_model",
            network_posture="local_evidence_only",
            authority_posture="no_external_authority_required",
            safe_summary=(
                "Evidence Timeline and Proof records are local receipt/proof "
                "refs; they do not expose raw external content as truth."
            ),
            route_refs=[
                "GET /control-center/evidence/timeline",
                "GET /control-center/proof",
            ],
            cli_refs=[
                "scripts/dev/uaa_founder_loop.py inspect-proof",
            ],
            evidence_refs=[
                "contract-ref:runtime-evidence-audit-spine:v1",
                "proof-ref:web-evidence:product-slice",
            ],
            test_refs=[
                "tests/test_runtime_evidence_audit.py",
                "tests/test_claim_evidence_contracts.py",
            ],
            blocked_authority_refs=[
                "blocked-state:external-info:no-raw-content-as-truth",
            ],
        ),
        _external_information_row(
            category_id="operator_supplied_external_metadata",
            label="Operator-supplied external metadata",
            status="implemented_review_only",
            network_posture="metadata_only_no_fetch",
            authority_posture="operator_review_required",
            safe_summary=(
                "External intake records accept bounded quotes, safe refs, "
                "freshness posture, and receipts without storing raw pages."
            ),
            route_refs=[
                "GET /control-center/web-evidence/attachments",
            ],
            cli_refs=[
                "scripts/dev/uaa_founder_loop.py inspect-web-evidence",
            ],
            evidence_refs=[
                "contract-ref:governed-web-evidence-intake:v1",
                *GOVERNED_WEB_EVIDENCE_DOCS[:2],
            ],
            test_refs=[
                "tests/test_governed_web_evidence.py",
            ],
            blocked_authority_refs=[
                "blocked-state:web-evidence:no-raw-body-persistence",
                "blocked-state:web-evidence:no-context-injection",
            ],
        ),
        _external_information_row(
            category_id="allowlisted_gateway_preview",
            label="AuthorityLease-gated gateway preview",
            status="implemented_exact_lane",
            network_posture="existing_authority_lease_gated_https_get",
            authority_posture="requires_browser_read_authority_lease",
            safe_summary=(
                "The exact Web Evidence product slice can attach one "
                "configured-host HTTPS GET preview through WebAccessGateway "
                "with bounded redaction, audit refs, proof refs, and receipts."
            ),
            route_refs=[
                WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF,
                f"POST {GOVERNED_WEB_EVIDENCE_REQUEST_PATH}",
                f"GET {GOVERNED_WEB_EVIDENCE_STATUS_PATH}",
            ],
            cli_refs=[
                WEB_EVIDENCE_PRODUCT_SLICE_CLI_REF,
                "scripts/dev/uaa_founder_loop.py inspect-web-evidence",
            ],
            evidence_refs=[
                WEB_EVIDENCE_PRODUCT_SLICE_CONTRACT_REF,
                WEB_EVIDENCE_PRODUCT_SLICE_PROOF_REF,
                WEB_EVIDENCE_PRODUCT_SLICE_SAFE_DISABLE_REF,
            ],
            test_refs=[
                "tests/test_web_evidence_product_slice.py",
                "tests/test_governed_web_evidence.py",
                "scripts/verify_beta_08_web_evidence_product_slice.py",
            ],
            blocked_authority_refs=list(
                WEB_EVIDENCE_PRODUCT_SLICE_BLOCKED_AUTHORITY_REFS
            ),
            authority_required=True,
            policy_decision_required=True,
            receipt_required=True,
            existing_exact_network_lane=True,
        ),
        _external_information_row(
            category_id="untrusted_content_quarantine",
            label="Untrusted content quarantine",
            status="implemented_policy_invariant",
            network_posture="content_untrusted_safe_refs_only",
            authority_posture="content_cannot_grant_authority",
            safe_summary=(
                "Fetched or attached web content is marked untrusted, redacted, "
                "safe-ref-only on durable surfaces, and cannot become policy."
            ),
            route_refs=[
                WEB_EVIDENCE_PRODUCT_SLICE_ROUTE_REF,
                "GET /control-center/evidence/timeline",
            ],
            cli_refs=[
                "scripts/dev/uaa_founder_loop.py inspect-web-evidence",
            ],
            evidence_refs=[
                "src/ultimate_ai_agent/core/network/governed_web_evidence.py",
                "src/ultimate_ai_agent/core/control_center/web_evidence_product_slice.py",
            ],
            test_refs=[
                "tests/test_governed_web_evidence.py",
                "tests/test_web_evidence_product_slice.py",
            ],
            blocked_authority_refs=[
                "blocked-state:web-evidence:no-context-injection",
                "blocked-state:web-evidence:no-memory-write",
                "blocked-state:web-evidence:no-provider-model-call",
            ],
        ),
        _external_information_row(
            category_id="browser_observe",
            label="Browser observe",
            status="planned_blocked_until_exact_lane",
            network_posture="future_controlled_observe_only",
            authority_posture="not_callable_from_agent_loop",
            safe_summary=(
                "Browser observe remains future/controlled and must route "
                "through WebAccessGateway with safe summaries and no cookies, "
                "clicks, forms, downloads, or raw DOM retention."
            ),
            route_refs=[],
            cli_refs=[],
            evidence_refs=[
                "docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md",
                "docs/network/WEB_ACCESS_GATEWAY.md",
            ],
            test_refs=[
                "scripts/verify_browser_gateway_ladder.py",
            ],
            blocked_authority_refs=[
                "blocked-state:web-evidence:no-browser-actions",
                "blocked-state:agent-loop:no-browser-automation",
            ],
        ),
        _external_information_row(
            category_id="browser_action",
            label="Browser action",
            status="blocked",
            network_posture="execution_blocked",
            authority_posture="no_click_form_auth_download_authority",
            safe_summary=(
                "Browser clicks, forms, auth/session state, downloads/uploads, "
                "and POST-style mutations remain blocked; future dry-run plans "
                "must not execute actions."
            ),
            route_refs=[],
            cli_refs=[],
            evidence_refs=[
                "docs/control_center/PRODUCT_LANGUAGE_RULES.md",
                "docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md",
            ],
            test_refs=[
                "scripts/verify_browser_gateway_ladder.py",
                "tests/test_tool_runtime_authority_boundaries.py",
            ],
            blocked_authority_refs=[
                "blocked-state:web-evidence:no-browser-actions",
                "blocked-state:web-evidence:no-auth-session-state",
                "blocked-state:web-evidence:no-downloads-or-uploads",
                "blocked-state:web-evidence:no-post-put-patch-delete",
            ],
        ),
        _external_information_row(
            category_id="provider_search_scrape",
            label="Provider search/scrape adapters",
            status="planned_disabled_adapter_shell",
            network_posture="provider_runtime_blocked",
            authority_posture="catalog_visibility_is_not_callable_authority",
            safe_summary=(
                "Firecrawl, Browserbase, search, and scrape providers remain "
                "future/disabled adapter shells unless an exact WebAccessGateway "
                "lane grants read-only authority with audit and receipts."
            ),
            route_refs=[],
            cli_refs=[],
            evidence_refs=[
                "docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md",
                "docs/control_center/UAA_RUNTIME_MODEL_PROVIDER_RESEARCH.md",
            ],
            test_refs=[
                "tests/test_model_runtime_no_real_calls.py",
                "tests/test_tool_runtime_authority_boundaries.py",
            ],
            blocked_authority_refs=[
                "blocked-state:agent-loop:no-provider-sdk-calls",
                "blocked-state:web-evidence:no-provider-model-call",
                "blocked-state:web-evidence:no-connector-write",
            ],
        ),
        _external_information_row(
            category_id="external_content_authority_isolation",
            label="External content authority isolation",
            status="implemented_invariant",
            network_posture="external_data_never_authority",
            authority_posture="approvals_authorize_content_does_not",
            safe_summary=(
                "External data can support citations and evidence refs, but "
                "approvals and AuthorityLeases remain the only authority source."
            ),
            route_refs=[
                "GET /api/runtime/authority-state",
                AGENT_LOOP_THREAD_ROUTE_REF,
            ],
            cli_refs=[
                HIGH_MATURITY_SPINE_CLI_REF,
            ],
            evidence_refs=[
                "contract-ref:authority-lease:v1",
                EXTERNAL_INFORMATION_HANDLING_CONTRACT_REF,
            ],
            test_refs=[
                "tests/test_authority_leases.py",
                "tests/test_runtime_agent_loop_spine.py",
            ],
            blocked_authority_refs=[
                "blocked-state:external-info:no-authority-from-content",
                "blocked-state:agent-loop:no-production-authority",
            ],
        ),
    ]
    return {
        "schema_version": "external_information_handling_posture.v1",
        "contract_ref": EXTERNAL_INFORMATION_HANDLING_CONTRACT_REF,
        "status": "implemented_read_only_posture_map_existing_lanes_only",
        "source": AGENT_LOOP_THREAD_SOURCE,
        "route_ref": AGENT_LOOP_THREAD_ROUTE_REF,
        "cli_ref": HIGH_MATURITY_SPINE_CLI_REF,
        "backend_owned": True,
        "local_read_model_only": True,
        "safe_refs_only": True,
        "raw_content_included": False,
        "category_count": len(rows),
        "implemented_or_blocked_count": len(rows),
        "existing_exact_network_lane_count": sum(
            1 for row in rows if row["existing_exact_network_lane"] is True
        ),
        "rows": rows,
        "new_live_web_fetching_added": False,
        "browser_observe_enabled": False,
        "browser_action_execution_enabled": False,
        "provider_search_enabled": False,
        "provider_sdk_calls_added": False,
        "connector_writes_added": False,
        "memory_writes_added": False,
        "context_injection_added": False,
        "production_authority_added": False,
        "safe_summary": (
            "External information handling is explicit: local evidence is "
            "receipt/proof backed, one existing WebAccessGateway HTTPS GET lane "
            "is AuthorityLease-gated, and browser/provider/action expansion "
            "remains planned or blocked."
        ),
        "blocked_authority_refs": _dedupe(
            [
                *WEB_EVIDENCE_PRODUCT_SLICE_BLOCKED_AUTHORITY_REFS,
                "blocked-state:external-info:no-authority-from-content",
                "blocked-state:agent-loop:no-provider-sdk-calls",
                "blocked-state:agent-loop:no-browser-automation",
            ]
        ),
        "redactions_applied": [
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_web_content_omitted",
            "raw_url_omitted",
            "raw_headers_omitted",
            "raw_body_omitted",
        ],
    }


def build_system_agent_eval_coverage() -> dict[str, Any]:
    """Return system-level eval coverage without scoring model intelligence."""

    rows = [
        _system_eval_row(
            category_id="route_choice",
            label="Route choice",
            status="implemented_fixture_eval",
            safe_summary=(
                "Turn router and top-level decision router fixtures check "
                "deterministic route/contract selection without provider calls."
            ),
            evidence_refs=[
                "contract-ref:turn-contract-router:v1",
                "contract-ref:top-level-decision-router:v1",
            ],
            test_refs=[
                "tests/test_turn_contract_router_quality.py",
                "tests/test_uaa_p1_089_top_level_decision_router_contract.py",
            ],
            invariant_refs=[
                "invariant:no-runtime-model-call",
                "invariant:no-router-authority-grant",
            ],
        ),
        _system_eval_row(
            category_id="ambiguity_handling",
            label="Ambiguity handling",
            status="implemented_fixture_eval",
            safe_summary=(
                "User intent and task decomposition fixtures expose ambiguity "
                "posture, clarification needs, assumptions, and missing refs."
            ),
            evidence_refs=[
                "docs/control_center/UAA_P1_079_USER_INTENT_UNDERSTANDING.md",
                "docs/control_center/UAA_P1_090_TASK_DECOMPOSITION_PROPOSAL_ENGINE.md",
            ],
            test_refs=[
                "tests/test_uaa_p1_079_user_intent_understanding.py",
                "tests/test_uaa_p1_090_task_decomposition_proposal_engine.py",
            ],
            invariant_refs=[
                "invariant:ambiguous-scope-asks-or-degrades",
                "invariant:no-hidden-context-injection",
            ],
        ),
        _system_eval_row(
            category_id="task_decomposition",
            label="Task decomposition",
            status="implemented_fixture_eval",
            safe_summary=(
                "Task decomposition fixtures check steps, dependencies, risk, "
                "approval gates, missing evidence, and proposal-only posture."
            ),
            evidence_refs=[
                "GET /control-center/task-decomposition/propose",
                "docs/control_center/UAA_P1_090_TASK_DECOMPOSITION_PROPOSAL_ENGINE.md",
            ],
            test_refs=[
                "tests/test_task_decomposition_capability_registry.py",
                "tests/test_uaa_p1_090_task_decomposition_proposal_engine.py",
            ],
            invariant_refs=[
                "invariant:decomposition-is-proposal-only",
                "invariant:approval-gates-visible",
            ],
        ),
        _system_eval_row(
            category_id="approval_needed_detection",
            label="Approval-needed detection",
            status="implemented_fixture_eval",
            safe_summary=(
                "Approval fixtures check exact approval scopes, authority "
                "boundaries, denied execution, and approval-before-mutation."
            ),
            evidence_refs=[
                "contract-ref:authority-lease:v1",
                "contract-ref:turn-run-approval-chain:v1",
            ],
            test_refs=[
                "tests/test_authority_leases.py",
                "tests/test_turn_run_approval_chain.py",
                "tests/test_approval_requests.py",
            ],
            invariant_refs=[
                "invariant:unknown-authority-denied",
                "invariant:approval-ref-is-not-authority",
            ],
        ),
        _system_eval_row(
            category_id="memory_citation_selection",
            label="Memory citation selection",
            status="implemented_fixture_eval",
            safe_summary=(
                "Memory retrieval fixtures check recall-only ranking, reviewed "
                "refs, citations, provenance, staleness, and no truth authority."
            ),
            evidence_refs=[
                "GET /control-center/memory/ranked-retrieval",
                "GET /control-center/memory/retrieval-diagnostics",
            ],
            test_refs=[
                "tests/test_memory_retrieval.py",
                "tests/test_fcc_mem_022_ranked_retrieval_recall_tuning.py",
            ],
            invariant_refs=[
                "invariant:memory-is-recall-not-truth",
                "invariant:no-memory-write-from-retrieval",
            ],
        ),
        _system_eval_row(
            category_id="blocked_state_explanation",
            label="Blocked-state explanation",
            status="implemented_fixture_eval",
            safe_summary=(
                "Runtime, authority, and Control Center fixtures check readable "
                "blocked reasons, denied authority refs, and next safe actions."
            ),
            evidence_refs=[
                "GET /api/runtime/authority-state",
                "GET /control-center/agent-loop/thread",
            ],
            test_refs=[
                "tests/test_authority_leases.py",
                "tests/test_runtime_agent_loop_spine.py",
                "tests/test_control_center_api_routes.py",
            ],
            invariant_refs=[
                "invariant:blockers-are-operator-readable",
                "invariant:denied-state-does-not-throw-raw-errors",
            ],
        ),
        _system_eval_row(
            category_id="evidence_completeness",
            label="Evidence completeness",
            status="implemented_fixture_eval",
            safe_summary=(
                "Evidence fixtures check receipt refs, proof refs, safe "
                "summaries, verification posture, and raw-payload exclusion."
            ),
            evidence_refs=[
                "contract-ref:governed-runtime-action-signed-evidence:v1",
                "contract-ref:coding-patch-proposal-signed-evidence:v1",
                "contract-ref:runtime-evidence-audit-spine:v1",
            ],
            test_refs=[
                "tests/test_claim_evidence_contracts.py",
                "tests/test_runtime_action_signed_evidence.py",
                "tests/test_coding_cockpit_read_model.py",
            ],
            invariant_refs=[
                "invariant:evidence-uses-safe-refs",
                "invariant:raw-payloads-not-durable",
            ],
        ),
    ]
    return {
        "schema_version": "system_agent_eval_coverage.v1",
        "contract_ref": SYSTEM_AGENT_EVAL_COVERAGE_CONTRACT_REF,
        "status": "implemented_backend_owned_fixture_eval_map",
        "source": AGENT_LOOP_THREAD_SOURCE,
        "route_ref": AGENT_LOOP_THREAD_ROUTE_REF,
        "cli_ref": HIGH_MATURITY_SPINE_CLI_REF,
        "backend_owned": True,
        "local_read_model_only": True,
        "safe_refs_only": True,
        "raw_content_included": False,
        "category_count": len(rows),
        "implemented_count": sum(
            1 for row in rows if row["status"] == "implemented_fixture_eval"
        ),
        "rows": rows,
        "model_intelligence_scored": False,
        "runtime_model_calls_added": False,
        "provider_sdk_calls_added": False,
        "tool_execution_added": False,
        "shell_execution_added": False,
        "browser_automation_added": False,
        "connector_writes_added": False,
        "memory_writes_added": False,
        "context_injection_added": False,
        "production_authority_added": False,
        "safe_summary": (
            "System eval coverage is fixture-backed and contract-level; it does "
            "not evaluate raw LLM intelligence or add runtime authority."
        ),
        "blocked_authority_refs": list(AGENT_LOOP_THREAD_BLOCKED_AUTHORITY_REFS),
        "redactions_applied": [
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_eval_inputs_omitted",
            "raw_model_outputs_omitted",
            "raw_provider_payloads_omitted",
        ],
    }


def build_high_maturity_agent_spine_readiness() -> dict[str, Any]:
    """Return deterministic W1-W13 coverage over existing safe UAA surfaces."""

    rows = [
        _high_maturity_row(
            weakness_id="W1",
            component="Product loop",
            status="partial",
            maturity="usable",
            score=7,
            safe_summary=(
                "Founder Loop surfaces now bind request, intent, plan, "
                "actions, evidence, memory, trust, and next decision through "
                "backend-owned read models."
            ),
            evidence_refs=[
                AGENT_LOOP_THREAD_ROUTE_REF,
                "GET /control-center/today/summary",
                "GET /control-center/actions/inbox",
                "GET /control-center/evidence/timeline",
            ],
            test_refs=[
                "tests/test_runtime_agent_loop_spine.py",
                "tests/test_operator_loop_p1_011.py",
            ],
            gap=(
                "Still proposal-first; more exact execution lanes need "
                "AuthorityLease, approval, receipt, and rollback proof."
            ),
            recommendation=(
                "Keep extending the existing Agent Loop Thread instead of "
                "creating parallel cockpit state."
            ),
        ),
        _high_maturity_row(
            weakness_id="W2",
            component="Durable planning and orchestration",
            status="partial",
            maturity="usable",
            score=7,
            safe_summary=(
                "Durable run observability and staged orchestration expose "
                "steps, approval waits, retry posture, recovery posture, and "
                "blocked states as read-only operator evidence."
            ),
            evidence_refs=[
                "GET /control-center/runs/observability",
                "docs/control_center/UAA_RUNTIME_DURABLE_ORCHESTRATION.md",
                "docs/runtime/UAA_RUNTIME_STAGED_ORCHESTRATION_ENGINE.md",
            ],
            test_refs=[
                "tests/test_durable_run_lifecycle_read_model.py",
                "tests/test_staged_orchestration_engine.py",
            ],
            gap="Recovery/cancel/retry execution remains blocked.",
            recommendation=(
                "Promote only exact orchestration transitions with approval "
                "and idempotency receipts."
            ),
        ),
        _high_maturity_row(
            weakness_id="W3",
            component="Memory retrieval and lifecycle",
            status="implemented",
            maturity="strong",
            score=8,
            safe_summary=(
                "Memory has recall-only retrieval, review decisions, quality "
                "states, provenance, context-pack previews, and no hidden "
                "context injection."
            ),
            evidence_refs=[
                "GET /control-center/memory/workbench",
                "GET /control-center/memory/review",
                "contract-ref:runtime-memory-learning-posture:v1",
            ],
            test_refs=[
                "tests/test_memory_retrieval.py",
                "tests/test_runtime_memory_learning.py",
                "tests/test_context_pack_no_injection.py",
            ],
            gap="Automatic writes, delete/export, and injection stay blocked.",
            recommendation=(
                "Keep memory as recall and reviewable proposals; graduate "
                "write/delete/export only as exact lanes."
            ),
        ),
        _high_maturity_row(
            weakness_id="W4",
            component="Operator cockpit UX",
            status="partial",
            maturity="usable",
            score=7,
            safe_summary=(
                "The Control Center shows Today, Action Inbox, Proof, "
                "Evidence, Memory, Trust, Coding, Runtime, and route state "
                "using backend truth labels and safe operator copy."
            ),
            evidence_refs=[
                "apps/control-center/src/components/FounderLoopPanels.tsx",
                "apps/control-center/src/components/TrustAuthorityPanel.tsx",
                "GET /control-center/agent-loop/thread",
            ],
            test_refs=[
                "scripts/verify_control_center_frontend.py",
                "tests/test_control_center_release_surface_manifest.py",
            ],
            gap="Some routes are still partial or fallback-shaped.",
            recommendation=(
                "Continue moving operator-critical panels onto Python/API "
                "truth with no raw JSON as the primary workflow."
            ),
        ),
        _high_maturity_row(
            weakness_id="W5",
            component="Exact action and tool lanes",
            status="partial",
            maturity="usable",
            score=7,
            safe_summary=(
                "Action, tool, and code lane catalogs separate inspectable, "
                "proposal-only, approval-required, implemented, and blocked "
                "capabilities with side-effect and receipt posture."
            ),
            evidence_refs=[
                "contract-ref:runtime-action-tool-code-catalog:v1",
                "GET /control-center/actions/inbox",
                "GET /api/runtime/authority-state#authority_lane_catalog",
            ],
            test_refs=[
                "tests/test_runtime_action_tool_code_lanes.py",
                "tests/test_tool_runtime_authority_boundaries.py",
                "tests/test_authority_leases.py",
            ],
            gap="Generic tool execution and broad shell remain blocked.",
            recommendation=(
                "Graduate narrow fixed-argv or proposal lanes one at a time "
                "behind AuthorityLease and LocalApprovalAuthority validation."
            ),
        ),
        _high_maturity_row(
            weakness_id="W6",
            component="Code Mode discipline",
            status="implemented",
            maturity="strong",
            score=8,
            safe_summary=(
                "Coding cockpit and code workbench expose proposal, patch, "
                "signed proposal evidence, apply-readiness, validation, "
                "rollback, and blocked-authority posture without broad coding "
                "autonomy."
            ),
            evidence_refs=[
                "GET /control-center/coding/session",
                "contract-ref:coding-patch-proposal-signed-evidence:v1",
                "scripts/dev/uaa_coding.py verify-patch-proposal-evidence",
                "docs/control_center/UAA_P1_075_GOVERNED_CODE_WORKBENCH.md",
                "apps/control-center/src/components/CodingCockpitPanel.tsx",
            ],
            test_refs=[
                "tests/test_coding_cockpit_read_model.py",
                "tests/test_uaa_p1_075_governed_code_workbench.py",
            ],
            gap="Exact patch apply and broad test execution remain limited.",
            recommendation=(
                "Keep code changes proposal-first; bind exact apply to patch "
                "hash, approval scope, rollback artifact, and receipt refs."
            ),
        ),
        _high_maturity_row(
            weakness_id="W7",
            component="Web and external evidence",
            status="partial",
            maturity="usable",
            score=7,
            safe_summary=(
                "Web/external information is mapped into an explicit handling "
                "posture: local evidence refs, one existing AuthorityLease-gated "
                "WebAccessGateway preview lane, untrusted-content quarantine, "
                "and blocked browser/provider/action expansion."
            ),
            evidence_refs=[
                EXTERNAL_INFORMATION_HANDLING_CONTRACT_REF,
                "GET /control-center/web-evidence/attachments",
                "docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md",
                "src/ultimate_ai_agent/core/network/governed_web_evidence.py",
            ],
            test_refs=[
                "tests/test_governed_web_evidence.py",
                "tests/test_web_evidence_product_slice.py",
            ],
            gap="Live broad fetching and browser actions remain blocked.",
            recommendation=(
                "Keep WebAccessGateway as the only boundary; add read-only "
                "fetch lanes only with allowlists and audit records."
            ),
        ),
        _high_maturity_row(
            weakness_id="W8",
            component="Model and provider management",
            status="partial",
            maturity="usable",
            score=7,
            safe_summary=(
                "Provider/model surfaces expose catalogs, readiness, cost, "
                "role evidence, routing traces, and blocked reasons while "
                "model output remains non-authoritative."
            ),
            evidence_refs=[
                "GET /control-center/providers/runtime-control-plane",
                "docs/runtime/UAA_RUNTIME_ROLE_PROVIDER_EVIDENCE.md",
                "docs/control_center/MODEL_PROVIDER_CONTROL_PLANE.md",
            ],
            test_refs=[
                "tests/test_model_provider_control_plane.py",
                "tests/test_role_provider_evidence.py",
                "tests/test_model_runtime_no_real_calls.py",
            ],
            gap="No new runtime provider/model calls are granted.",
            recommendation=(
                "Improve metadata and readiness traces without provider SDK "
                "calls unless an exact accepted lane already permits them."
            ),
        ),
        _high_maturity_row(
            weakness_id="W9",
            component="Signed evidence receipts",
            status="implemented",
            maturity="strong",
            score=8,
            safe_summary=(
                "Runtime action signed evidence, Coding patch proposal signed "
                "evidence, and evidence audit spines use safe refs, hashes, "
                "lineage, verification posture, and receipt refs instead of raw "
                "payloads."
            ),
            evidence_refs=[
                "docs/runtime/UAA_RUNTIME_ACTION_SIGNED_EVIDENCE.md",
                "contract-ref:coding-patch-proposal-signed-evidence:v1",
                "contract-ref:runtime-evidence-audit-spine:v1",
                "scripts/dev/uaa_runtime.py verify-evidence-envelope",
            ],
            test_refs=[
                "tests/test_runtime_action_signed_evidence.py",
                "tests/test_coding_cockpit_read_model.py",
                "tests/test_runtime_evidence_audit.py",
            ],
            gap="Portable production signing/compliance claims stay blocked.",
            recommendation=(
                "Keep signed evidence local and verifier-backed; add portable "
                "export only after key material and redaction posture are proven."
            ),
        ),
        _high_maturity_row(
            weakness_id="W10",
            component="Extensibility and catalog maturity",
            status="implemented",
            maturity="strong",
            score=8,
            safe_summary=(
                "Extension catalog review, disabled-install receipts, grant "
                "records, trust statuses, and rollback/delete receipts keep "
                "review separate from callable runtime import."
            ),
            evidence_refs=[
                "GET /extensions/catalog",
                "POST /extensions/disabled-install-records/rollback",
                "docs/control_center/UAA_RUNTIME_EXTENSIBILITY_FINAL.md",
            ],
            test_refs=[
                "tests/test_inspectable_extension_catalog.py",
                "tests/test_runtime_extensibility_final.py",
            ],
            gap="Plugin runtime import and connector writes remain blocked.",
            recommendation=(
                "Keep imports disabled by default; require provenance, hash, "
                "approval, receipt, and revoke posture before callable use."
            ),
        ),
        _high_maturity_row(
            weakness_id="W11",
            component="End-to-end Founder Loop",
            status="partial",
            maturity="usable",
            score=7,
            safe_summary=(
                "Start Here, Today, Plans, Actions, Proof, Evidence, Memory, "
                "Trust, Work Board, and Agent Loop Thread share backend refs "
                "for an inspectable founder/operator loop."
            ),
            evidence_refs=[
                "GET /control-center/start-here/summary",
                "GET /control-center/agent-loop/thread",
                "docs/control_center/FOUNDER_LOOP_V1_PRODUCT_PROOF_PASS.md",
            ],
            test_refs=[
                "tests/test_founder_loop_v1_product_proof.py",
                "tests/test_founder_loop_v1_proof_lane.py",
                "tests/test_founder_loop_runs_integration.py",
            ],
            gap="More live useful lanes need exact authority before mutation.",
            recommendation=(
                "Tie every new action into the same proof/evidence/memory "
                "loop instead of one-off controls."
            ),
        ),
        _high_maturity_row(
            weakness_id="W12",
            component="System-level agent evals",
            status="partial",
            maturity="usable",
            score=7,
            safe_summary=(
                "Route choice, ambiguity handling, task decomposition, "
                "approval-needed detection, memory citation selection, blocked "
                "explanation, and evidence completeness are mapped into a "
                "backend-owned fixture eval coverage spine."
            ),
            evidence_refs=[
                SYSTEM_AGENT_EVAL_COVERAGE_CONTRACT_REF,
                "tests/test_turn_contract_router_quality.py",
                "tests/test_task_decomposition_capability_registry.py",
                "tests/test_claim_evidence_contracts.py",
            ],
            test_refs=[
                "tests/test_turn_contract_router_classifier.py",
                "tests/test_uaa_p1_089_top_level_decision_router_contract.py",
            ],
            gap="No broad benchmark suite should be claimed as model intelligence.",
            recommendation=(
                "Keep evals system-level and fixture-backed; do not score raw "
                "LLM intelligence without model-evaluation evidence."
            ),
        ),
        _high_maturity_row(
            weakness_id="W13",
            component="Release and product truth alignment",
            status="implemented",
            maturity="strong",
            score=8,
            safe_summary=(
                "OpenAPI, API manifest, route inventory, release truth, docs "
                "integrity, capability surface generation, and Foundation Gate "
                "keep product claims aligned with implemented posture."
            ),
            evidence_refs=[
                "GET /api/manifest",
                "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
                "docs/control_center/capability_surface_manifest.json",
            ],
            test_refs=[
                "tests/test_api_manifest.py",
                "tests/test_control_center_api_routes.py",
                "scripts/run_foundation_gate.py --command-mode report-only",
            ],
            gap="Large prompt-driven work still needs scoped commits and gates.",
            recommendation=(
                "Keep stale comparison reports out of product truth and use "
                "generated overlays where source truth exists."
            ),
        ),
    ]
    implemented = sum(1 for row in rows if row["status"] == "implemented")
    usable_or_better = sum(
        1
        for row in rows
        if row["maturity"] in {"usable", "strong", "mature"}
    )
    average_score = round(
        sum(float(row["score_0_10"]) for row in rows) / len(rows),
        1,
    )
    return {
        "schema_version": "high_maturity_agent_spine_coverage.v1",
        "contract_ref": HIGH_MATURITY_SPINE_CONTRACT_REF,
        "status": "implemented_backend_owned_read_model_no_new_authority",
        "source": AGENT_LOOP_THREAD_SOURCE,
        "backend_owned": True,
        "local_read_model_only": True,
        "safe_refs_only": True,
        "raw_content_included": False,
        "route_ref": AGENT_LOOP_THREAD_ROUTE_REF,
        "cli_ref": HIGH_MATURITY_SPINE_CLI_REF,
        "weakness_count": len(rows),
        "implemented_count": implemented,
        "usable_or_better_count": usable_or_better,
        "average_score_0_10": average_score,
        "overall_projection_0_100": int(round(average_score * 10)),
        "coverage_status": (
            "all_w1_w13_have_code_docs_tests_or_governed_blocked_posture"
        ),
        "rows": rows,
        "external_information_handling": (
            build_external_information_handling_posture()
        ),
        "system_eval_coverage": build_system_agent_eval_coverage(),
        "blocked_authority_refs": list(AGENT_LOOP_THREAD_BLOCKED_AUTHORITY_REFS),
        "next_safe_action": (
            "Use this spine coverage as inspection truth; graduate future "
            "runtime capability only through exact AuthorityLease-gated lanes."
        ),
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
    operator_decision_matrix = _build_operator_decision_matrix(
        action_items=action_items,
        memory_items=memory_items,
        evidence_refs=evidence_refs,
        proof_refs=proof_refs,
        blocked_refs=blocked_refs,
        next_decision=next_decision,
    )

    return {
        "schema_version": "runtime_agent_loop_thread.v1",
        "contract_ref": AGENT_LOOP_THREAD_CONTRACT_REF,
        "thread_ref": "agent-loop-thread:runtime-capability-foundation:current",
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
        "high_maturity_spine_readiness": build_high_maturity_agent_spine_readiness(),
        "operator_decision_matrix": operator_decision_matrix,
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


def _high_maturity_row(
    *,
    weakness_id: str,
    component: str,
    status: str,
    maturity: str,
    score: int,
    safe_summary: str,
    evidence_refs: list[str],
    test_refs: list[str],
    gap: str,
    recommendation: str,
) -> dict[str, Any]:
    return {
        "weakness_id": _safe_text(weakness_id),
        "component": _safe_text(component),
        "status": _safe_text(status),
        "maturity": _safe_text(maturity),
        "score_0_10": score,
        "safe_summary": _safe_text(safe_summary),
        "evidence_refs": _dedupe(evidence_refs),
        "test_refs": _dedupe(test_refs),
        "gap": _safe_text(gap),
        "recommendation": _safe_text(recommendation),
        "safe_refs_only": True,
        "authority_broadened": False,
        "runtime_model_calls_added": False,
        "provider_sdk_calls_added": False,
        "live_web_fetching_added": False,
        "browser_automation_added": False,
        "connector_writes_added": False,
        "unrestricted_shell_added": False,
        "plugin_runtime_import_added": False,
        "production_authority_added": False,
    }


def _system_eval_row(
    *,
    category_id: str,
    label: str,
    status: str,
    safe_summary: str,
    evidence_refs: list[str],
    test_refs: list[str],
    invariant_refs: list[str],
) -> dict[str, Any]:
    return {
        "category_id": _safe_text(category_id),
        "label": _safe_text(label),
        "status": _safe_text(status),
        "safe_summary": _safe_text(safe_summary),
        "evidence_refs": _dedupe(evidence_refs),
        "test_refs": _dedupe(test_refs),
        "invariant_refs": _dedupe(invariant_refs),
        "safe_refs_only": True,
        "model_intelligence_scored": False,
        "runtime_model_calls_added": False,
        "provider_sdk_calls_added": False,
        "tool_execution_added": False,
        "shell_execution_added": False,
        "browser_automation_added": False,
        "connector_writes_added": False,
        "memory_writes_added": False,
        "context_injection_added": False,
        "production_authority_added": False,
    }


def _external_information_row(
    *,
    category_id: str,
    label: str,
    status: str,
    network_posture: str,
    authority_posture: str,
    safe_summary: str,
    route_refs: list[str],
    cli_refs: list[str],
    evidence_refs: list[str],
    test_refs: list[str],
    blocked_authority_refs: list[str],
    authority_required: bool = False,
    policy_decision_required: bool = True,
    receipt_required: bool = False,
    existing_exact_network_lane: bool = False,
) -> dict[str, Any]:
    return {
        "category_id": _safe_text(category_id),
        "label": _safe_text(label),
        "status": _safe_text(status),
        "network_posture": _safe_text(network_posture),
        "authority_posture": _safe_text(authority_posture),
        "safe_summary": _safe_text(safe_summary),
        "route_refs": _dedupe(route_refs),
        "cli_refs": _dedupe(cli_refs),
        "evidence_refs": _dedupe(evidence_refs),
        "test_refs": _dedupe(test_refs),
        "blocked_authority_refs": _dedupe(blocked_authority_refs),
        "authority_required": authority_required,
        "policy_decision_required": policy_decision_required,
        "receipt_required": receipt_required,
        "existing_exact_network_lane": existing_exact_network_lane,
        "safe_refs_only": True,
        "raw_content_included": False,
        "untrusted_content_can_instruct_agent": False,
        "external_content_can_grant_authority": False,
        "new_live_web_fetching_added": False,
        "browser_observe_enabled": False,
        "browser_action_execution_enabled": False,
        "provider_search_enabled": False,
        "provider_sdk_calls_added": False,
        "connector_writes_added": False,
        "memory_writes_added": False,
        "context_injection_added": False,
        "production_authority_added": False,
    }


def _build_operator_decision_matrix(
    *,
    action_items: list[dict[str, Any]],
    memory_items: list[dict[str, Any]],
    evidence_refs: list[str],
    proof_refs: list[str],
    blocked_refs: list[str],
    next_decision: str,
) -> dict[str, Any]:
    local_action = _first_record(action_items)
    memory_item = _first_record(memory_items)

    rows = [
        _operator_decision_row(
            surface="Today",
            capability_status="implemented",
            operator_question="What should I inspect first?",
            backend_route_ref="GET /control-center/today/summary",
            cli_ref=AGENT_LOOP_THREAD_CLI_REF,
            primary_ref="surface-ref:today:summary",
            approval_posture="read_only_no_approval_required",
            side_effect_class="read_only",
            safe_action="Inspect priorities, blockers, and next safe actions from Python Core.",
            evidence_refs=["evidence-ref:founder-loop:today-summary"],
            proof_refs=proof_refs[:2],
        ),
        _operator_decision_row(
            surface="Action Inbox",
            capability_status="partial",
            operator_question="Which exact local task can I approve or inspect?",
            backend_route_ref="GET /control-center/actions/inbox",
            cli_ref="scripts/dev/uaa_founder_loop.py inspect-action-work-queue",
            primary_ref=_safe_text(
                local_action.get("item_ref"),
                fallback="action-ref:founder-loop:current",
            ),
            approval_posture=_safe_text(
                local_action.get("approval_envelope_status"),
                fallback="approval_required_before_mutation",
            ),
            side_effect_class=_safe_text(
                local_action.get("side_effect_class"),
                fallback="local_dev_workspace_only",
            ),
            safe_action=_safe_text(
                local_action.get("next_safe_action"),
                fallback="Open Action Inbox and inspect the approval envelope before mutation.",
            ),
            evidence_refs=_string_values(local_action.get("evidence_refs"))
            or ["evidence-ref:founder-loop:action-inbox"],
            proof_refs=_string_values(local_action.get("receipt_refs")),
            receipt_refs=_string_values(local_action.get("receipt_refs")),
            blocked_state_refs=_string_values(
                local_action.get("local_task_commit_blocked_reasons")
            ),
            mutation_enabled=False,
        ),
        _operator_decision_row(
            surface="Plans",
            capability_status="proposal_only",
            operator_question="What plan is visible, and what still needs review?",
            backend_route_ref="GET /control-center/today/summary",
            cli_ref="scripts/dev/uaa_founder_loop.py inspect-state",
            primary_ref="plan-revision-ref:agent-loop:current",
            approval_posture="review_required_before_action",
            side_effect_class="read_only",
            safe_action="Review plan steps and blocked refs; do not treat the plan as execution authority.",
            evidence_refs=["evidence-ref:founder-loop:today-summary"],
            proof_refs=proof_refs[:2],
            blocked_state_refs=["blocked-state:agent-loop:no-plan-execution"],
        ),
        _operator_decision_row(
            surface="Evidence",
            capability_status="implemented",
            operator_question="What proof or receipt backs this state?",
            backend_route_ref="GET /control-center/evidence/timeline",
            cli_ref="scripts/dev/uaa_founder_loop.py inspect-evidence-audit-spine",
            primary_ref="evidence-ref:control-center:agent-loop-thread",
            approval_posture="read_only_no_approval_required",
            side_effect_class="read_only",
            safe_action="Open Evidence or Proof refs before trusting any action summary.",
            evidence_refs=evidence_refs[:4],
            proof_refs=proof_refs[:4],
        ),
        _operator_decision_row(
            surface="Memory",
            capability_status="partial",
            operator_question="What can be recalled or reviewed without hidden injection?",
            backend_route_ref="GET /control-center/memory/review",
            cli_ref="scripts/dev/uaa_founder_loop.py memory-learning-posture",
            primary_ref=_safe_text(
                memory_item.get("candidate_ref")
                or memory_item.get("business_memory_candidate_ref"),
                fallback="memory-candidate-ref:review-queue",
            ),
            approval_posture="review_required_for_memory_decisions",
            side_effect_class="read_only",
            safe_action="Review memory candidates as recall only; keep automatic writes and context injection blocked.",
            evidence_refs=_string_values(memory_item.get("evidence_refs"))
            or ["evidence-ref:founder-loop:memory-review"],
            proof_refs=[],
            blocked_state_refs=[
                "blocked-state:agent-loop:no-memory-write-authority",
                "blocked-state:agent-loop:no-hidden-context-injection",
            ],
        ),
        _operator_decision_row(
            surface="Trust",
            capability_status="implemented",
            operator_question="Which authority is enabled, review-only, or blocked?",
            backend_route_ref="GET /control-center/trust-authority/matrix",
            cli_ref="scripts/dev/uaa_founder_loop.py inspect-trust-authority",
            primary_ref="trust-authority-matrix:current",
            approval_posture="policy_boundary_visible",
            side_effect_class="read_only",
            safe_action="Use Trust to confirm the exact approval lane before any mutation.",
            evidence_refs=["evidence-ref:control-center:trust-authority"],
            proof_refs=proof_refs[:2],
            blocked_state_refs=blocked_refs[:8],
        ),
        _operator_decision_row(
            surface="Runtime and Providers",
            capability_status="blocked",
            operator_question="Can model/provider output make decisions?",
            backend_route_ref="GET /control-center/model-provider/control-plane",
            cli_ref="scripts/dev/uaa_runtime.py inspect-capabilities",
            primary_ref="runtime-provider-posture:metadata-only",
            approval_posture="metadata_only_no_invocation",
            side_effect_class="read_only",
            safe_action="Inspect readiness metadata only; model/provider output is not authority.",
            evidence_refs=["evidence-ref:model-provider:control-plane"],
            proof_refs=[],
            blocked_state_refs=[
                "blocked-state:agent-loop:no-runtime-model-calls",
                "blocked-state:agent-loop:no-provider-sdk-calls",
            ],
        ),
        _operator_decision_row(
            surface="Coding and Work Board",
            capability_status="partial",
            operator_question="Which workspace/code/board state is safe to inspect?",
            backend_route_ref="GET /control-center/coding/session",
            cli_ref="scripts/dev/uaa_coding.py inspect-session",
            primary_ref="operator-workspace-spine:current",
            approval_posture="proposal_or_read_only_until_exact_lane",
            side_effect_class="read_only",
            safe_action="Inspect backend-owned workspace, coding, and board refs; mutation lanes remain exact-scoped.",
            evidence_refs=["evidence-ref:operator-workspace-spine:read-model"],
            proof_refs=proof_refs[:2],
            blocked_state_refs=[
                "blocked-state:agent-loop:no-unrestricted-shell",
                "blocked-state:agent-loop:no-plugin-runtime-import",
                "blocked-state:agent-loop:no-production-authority",
            ],
        ),
    ]

    return {
        "schema_version": "runtime_cockpit_cli_api_parity.v1",
        "contract_ref": AGENT_LOOP_COCKPIT_PARITY_CONTRACT_REF,
        "status": "implemented_backend_owned_read_model_no_new_authority",
        "capability_status": "implemented",
        "source": AGENT_LOOP_THREAD_SOURCE,
        "backend_owned": True,
        "control_center_presentation_only": True,
        "safe_refs_only": True,
        "raw_content_included": False,
        "route_ref": AGENT_LOOP_THREAD_ROUTE_REF,
        "cli_ref": AGENT_LOOP_COCKPIT_PARITY_CLI_REF,
        "operator_can_decide_from_cockpit": True,
        "ui_mints_authority": False,
        "mutation_controls_enabled": False,
        "row_count": len(rows),
        "rows": rows,
        "next_safe_operator_decision": next_decision,
        "blocked_authority_refs": blocked_refs[:12],
        "redactions_applied": [
            "safe_refs_only",
            "bounded_summaries_only",
            "raw_content_omitted",
            "raw_prompt_omitted",
            "raw_response_omitted",
            "raw_provider_payload_omitted",
            "raw_local_paths_omitted",
        ],
    }


def _operator_decision_row(
    *,
    surface: str,
    capability_status: str,
    operator_question: str,
    backend_route_ref: str,
    cli_ref: str,
    primary_ref: str,
    approval_posture: str,
    side_effect_class: str,
    safe_action: str,
    evidence_refs: list[str],
    proof_refs: list[str],
    receipt_refs: list[str] | None = None,
    blocked_state_refs: list[str] | None = None,
    mutation_enabled: bool = False,
) -> dict[str, Any]:
    blocked = _dedupe(blocked_state_refs or [])
    return {
        "surface": _safe_text(surface),
        "capability_status": _safe_text(capability_status),
        "operator_question": _safe_text(operator_question),
        "backend_route_ref": _safe_text(backend_route_ref),
        "cli_ref": _safe_text(cli_ref),
        "primary_ref": _safe_text(primary_ref),
        "approval_posture": _safe_text(approval_posture),
        "side_effect_class": _safe_text(side_effect_class),
        "safe_action": _safe_text(safe_action),
        "evidence_refs": _dedupe(evidence_refs),
        "proof_refs": _dedupe(proof_refs),
        "receipt_refs": _dedupe(receipt_refs or []),
        "blocked_state_refs": blocked,
        "mutation_enabled": mutation_enabled,
        "backend_truth_required": True,
        "no_go_reason": (
            "Requires exact approval, receipt, and backend-owned state before mutation."
            if blocked or not mutation_enabled
            else "Exact scoped backend lane only."
        ),
    }


def _first_record(records: list[dict[str, Any]]) -> dict[str, Any]:
    return records[0] if records else {}


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
