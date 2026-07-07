from __future__ import annotations

import hashlib
import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.authority import (
    AuthorityDecisionCatalogEntry,
    build_authority_decision_catalog,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import GOVERNED_RUNTIME_REDACTIONS
from ultimate_ai_agent.core.runtime_gateway.delegation import (
    RUNTIME_DELEGATION_CONTROL_CENTER_REF,
)


RUNTIME_SESSION_LINEAGE_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-session-lineage:v1"
)
RUNTIME_SESSION_LINEAGE_ROUTE_REF = "GET /api/runtime/session-lineage"
RUNTIME_SESSION_LINEAGE_CLI_REF = "uaa runtime inspect-session-lineage"
RUNTIME_SESSION_LINEAGE_SNAPSHOT_REF = "session-lineage-snapshot-ref:runtime:forks"
RUNTIME_SESSION_LINEAGE_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-19:session-lineage"
)
RUNTIME_SESSION_LINEAGE_AUTHORITY_STATE_ROUTE_REF = "GET /api/runtime/authority-state"
RUNTIME_SESSION_LINEAGE_AUTHORITY_STATE_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-state"
)
RUNTIME_SESSION_LINEAGE_AUTHORITY_MAPPING_REF = (
    "lane-ref:runtime-session-lineage-read-model"
)
_AUTHORITY_DECISION_OUTCOMES = {"allow", "ask", "deny", "degrade_to_draft"}

RUNTIME_SESSION_LINEAGE_BLOCKED_AUTHORITY_REFS = [
    "blocked-authority:session-lineage-no-raw-transcript-clone",
    "blocked-authority:session-lineage-no-raw-prompt-persistence",
    "blocked-authority:session-lineage-no-raw-response-persistence",
    "blocked-authority:session-lineage-no-hidden-context-injection",
    "blocked-authority:session-lineage-no-runtime-dispatch",
    "blocked-authority:session-lineage-no-provider-model-call",
    "blocked-authority:session-lineage-no-shell-execution",
    "blocked-authority:session-lineage-no-browser-automation",
    "blocked-authority:session-lineage-no-connector-write",
    "blocked-authority:session-lineage-no-production-authority",
]


class RuntimeLineageNodeKind(str, Enum):
    user_request = "user_request"
    coding_task = "coding_task"
    runtime_run = "runtime_run"
    proof_record = "proof_record"
    review_branch = "review_branch"
    retry_branch = "retry_branch"
    comparison_branch = "comparison_branch"


class RuntimeLineageForkStatus(str, Enum):
    read_only_lineage = "read_only_lineage"
    promotion_ready = "promotion_ready"
    blocked_raw_clone = "blocked_raw_clone"


class RuntimeSessionLineageNode(BaseModel):
    node_ref: str
    node_kind: RuntimeLineageNodeKind
    session_ref: str
    parent_node_ref: str | None = None
    child_node_refs: list[str] = Field(default_factory=list)
    user_request_ref: str
    task_ref: str | None = None
    run_ref: str | None = None
    proof_ref: str | None = None
    branch_ref: str | None = None
    fork_reason_ref: str | None = None
    retrieval_log_ref: str
    safe_summary: str
    lineage_depth: int = 0
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    raw_transcript_cloned: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    hidden_context_injected: bool = False
    runtime_dispatch_performed: bool = False
    provider_model_call_performed: bool = False
    shell_execution_performed: bool = False
    browser_automation_performed: bool = False
    connector_write_performed: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_node(self) -> "RuntimeSessionLineageNode":
        for value, field_name in [
            (self.node_ref, "node_ref"),
            (self.session_ref, "session_ref"),
            (self.user_request_ref, "user_request_ref"),
            (self.retrieval_log_ref, "retrieval_log_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.parent_node_ref, "parent_node_ref"),
            (self.task_ref, "task_ref"),
            (self.run_ref, "run_ref"),
            (self.proof_ref, "proof_ref"),
            (self.branch_ref, "branch_ref"),
            (self.fork_reason_ref, "fork_reason_ref"),
        ]:
            if value is not None:
                validate_execution_ref(value, field_name)
        for field_name in (
            "child_node_refs",
            "evidence_refs",
            "receipt_refs",
            "proof_refs",
            "blocked_authority_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        validate_safe_execution_text(str(self.node_kind), "node_kind")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if self.lineage_depth < 0:
            raise ValueError("RUNTIME_SESSION_LINEAGE_DEPTH_INVALID")
        denied_flags = {
            "raw_transcript_cloned": self.raw_transcript_cloned,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
            "hidden_context_injected": self.hidden_context_injected,
            "runtime_dispatch_performed": self.runtime_dispatch_performed,
            "provider_model_call_performed": self.provider_model_call_performed,
            "shell_execution_performed": self.shell_execution_performed,
            "browser_automation_performed": self.browser_automation_performed,
            "connector_write_performed": self.connector_write_performed,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_SESSION_LINEAGE_AUTHORITY_DENIED: " + ", ".join(enabled)
            )
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_SESSION_LINEAGE_BLOCKERS_REQUIRED")
        return self


class RuntimeSessionForkPosture(BaseModel):
    fork_ref: str
    status: RuntimeLineageForkStatus
    parent_session_ref: str
    child_session_ref: str
    parent_node_ref: str
    child_node_ref: str
    branch_ref: str
    reason_ref: str
    operator_intent_ref: str
    redacted_fork_envelope_ref: str
    retrieval_log_ref: str
    compare_view_ref: str
    proof_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    safe_summary: str
    explicit_operator_intent_required: bool = True
    redacted_fork_envelope_required: bool = True
    proof_binding_required: bool = True
    raw_transcript_cloned: bool = False
    hidden_context_injected: bool = False
    runtime_dispatch_performed: bool = False
    provider_model_call_performed: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_fork(self) -> "RuntimeSessionForkPosture":
        for value, field_name in [
            (self.fork_ref, "fork_ref"),
            (self.parent_session_ref, "parent_session_ref"),
            (self.child_session_ref, "child_session_ref"),
            (self.parent_node_ref, "parent_node_ref"),
            (self.child_node_ref, "child_node_ref"),
            (self.branch_ref, "branch_ref"),
            (self.reason_ref, "reason_ref"),
            (self.operator_intent_ref, "operator_intent_ref"),
            (self.redacted_fork_envelope_ref, "redacted_fork_envelope_ref"),
            (self.retrieval_log_ref, "retrieval_log_ref"),
            (self.compare_view_ref, "compare_view_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in ("proof_refs", "evidence_refs", "blocked_authority_refs"):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        validate_safe_execution_text(str(self.status), "status")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        denied_flags = {
            "raw_transcript_cloned": self.raw_transcript_cloned,
            "hidden_context_injected": self.hidden_context_injected,
            "runtime_dispatch_performed": self.runtime_dispatch_performed,
            "provider_model_call_performed": self.provider_model_call_performed,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_SESSION_FORK_AUTHORITY_DENIED: " + ", ".join(enabled)
            )
        if not self.explicit_operator_intent_required:
            raise ValueError("RUNTIME_SESSION_FORK_OPERATOR_INTENT_REQUIRED")
        if not self.redacted_fork_envelope_required:
            raise ValueError("RUNTIME_SESSION_FORK_REDACTED_ENVELOPE_REQUIRED")
        if not self.proof_binding_required:
            raise ValueError("RUNTIME_SESSION_FORK_PROOF_BINDING_REQUIRED")
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_SESSION_FORK_BLOCKERS_REQUIRED")
        return self


class RuntimeSessionLineageReadModel(BaseModel):
    schema_version: str = "runtime_session_lineage.v1"
    contract_ref: str = RUNTIME_SESSION_LINEAGE_CONTRACT_REF
    status: str = "read_only_session_lineage_and_fork_posture"
    snapshot_ref: str = RUNTIME_SESSION_LINEAGE_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:runtime-session-lineage:pending"
    route_ref: str = RUNTIME_SESSION_LINEAGE_ROUTE_REF
    cli_ref: str = RUNTIME_SESSION_LINEAGE_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    authority_state_route_ref: str
    authority_state_cli_ref: str
    authority_state_mapping_ref: str
    authority_state_catalog_ref: str
    authority_state_decision_ref: str
    authority_state_decision_outcome: str
    authority_state_status: str
    authority_state_operator_message: str
    authority_state_reason_refs: list[str] = Field(default_factory=list)
    unsupported_adapter_refs: list[str] = Field(default_factory=list)
    safe_summary: str = (
        "Session lineage exposes safe parent, child, fork, proof, and reason refs "
        "without cloning raw transcripts or injecting hidden context."
    )
    root_node_refs: list[str] = Field(default_factory=list)
    nodes: list[RuntimeSessionLineageNode]
    forks: list[RuntimeSessionForkPosture]
    node_count: int = 0
    fork_count: int = 0
    root_count: int = 0
    parent_child_link_count: int = 0
    max_lineage_depth: int = 0
    raw_transcript_clone_enabled: bool = False
    hidden_context_injection_enabled: bool = False
    runtime_dispatch_enabled: bool = False
    provider_model_call_enabled: bool = False
    production_authority_enabled: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: (
            list(GOVERNED_RUNTIME_REDACTIONS)
            + [
                "raw_transcripts_omitted",
                "raw_prompts_omitted",
                "raw_responses_omitted",
                "fork_context_payloads_omitted",
            ]
        )
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeSessionLineageReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.control_center_ref, "control_center_ref"),
            (self.authority_state_mapping_ref, "authority_state_mapping_ref"),
            (self.authority_state_catalog_ref, "authority_state_catalog_ref"),
            (self.authority_state_decision_ref, "authority_state_decision_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "root_node_refs",
            "authority_state_reason_refs",
            "unsupported_adapter_refs",
            "blocked_authority_refs",
            "proof_refs",
            "verifier_refs",
            "next_safe_action_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.status, "status"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.authority_state_route_ref, "authority_state_route_ref"),
            (self.authority_state_cli_ref, "authority_state_cli_ref"),
            (
                self.authority_state_decision_outcome,
                "authority_state_decision_outcome",
            ),
            (self.authority_state_status, "authority_state_status"),
            (
                self.authority_state_operator_message,
                "authority_state_operator_message",
            ),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        if self.node_count != len(self.nodes):
            raise ValueError("RUNTIME_SESSION_LINEAGE_NODE_COUNT_MISMATCH")
        if self.fork_count != len(self.forks):
            raise ValueError("RUNTIME_SESSION_LINEAGE_FORK_COUNT_MISMATCH")
        if self.root_count != len(self.root_node_refs):
            raise ValueError("RUNTIME_SESSION_LINEAGE_ROOT_COUNT_MISMATCH")
        if self.parent_child_link_count != sum(
            len(node.child_node_refs) for node in self.nodes
        ):
            raise ValueError("RUNTIME_SESSION_LINEAGE_LINK_COUNT_MISMATCH")
        expected_max_depth = max((node.lineage_depth for node in self.nodes), default=0)
        if self.max_lineage_depth != expected_max_depth:
            raise ValueError("RUNTIME_SESSION_LINEAGE_DEPTH_COUNT_MISMATCH")
        node_refs = {node.node_ref for node in self.nodes}
        for root_ref in self.root_node_refs:
            if root_ref not in node_refs:
                raise ValueError("RUNTIME_SESSION_LINEAGE_ROOT_UNKNOWN")
        for node in self.nodes:
            if node.parent_node_ref and node.parent_node_ref not in node_refs:
                raise ValueError("RUNTIME_SESSION_LINEAGE_PARENT_UNKNOWN")
            for child_ref in node.child_node_refs:
                if child_ref not in node_refs:
                    raise ValueError("RUNTIME_SESSION_LINEAGE_CHILD_UNKNOWN")
        if (
            self.authority_state_mapping_ref
            != RUNTIME_SESSION_LINEAGE_AUTHORITY_MAPPING_REF
        ):
            raise ValueError("RUNTIME_SESSION_LINEAGE_AUTHORITY_MAPPING_MISMATCH")
        if self.authority_state_decision_outcome not in _AUTHORITY_DECISION_OUTCOMES:
            raise ValueError("RUNTIME_SESSION_LINEAGE_AUTHORITY_DECISION_INVALID")
        denied_flags = {
            "raw_transcript_clone_enabled": self.raw_transcript_clone_enabled,
            "hidden_context_injection_enabled": self.hidden_context_injection_enabled,
            "runtime_dispatch_enabled": self.runtime_dispatch_enabled,
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_SESSION_LINEAGE_AUTHORITY_DENIED: " + ", ".join(enabled)
            )
        if RUNTIME_SESSION_LINEAGE_PROOF_REF not in self.proof_refs:
            raise ValueError("RUNTIME_SESSION_LINEAGE_PROOF_REQUIRED")
        if set(RUNTIME_SESSION_LINEAGE_BLOCKED_AUTHORITY_REFS) - set(
            self.blocked_authority_refs
        ):
            raise ValueError("RUNTIME_SESSION_LINEAGE_BLOCKERS_REQUIRED")
        return self


def _hash_payload(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:24]
    return f"snapshot-hash-ref:runtime-session-lineage:{digest}"


def _node(
    *,
    node_ref: str,
    node_kind: RuntimeLineageNodeKind,
    session_ref: str,
    user_request_ref: str,
    retrieval_log_ref: str,
    safe_summary: str,
    lineage_depth: int,
    parent_node_ref: str | None = None,
    child_node_refs: list[str] | None = None,
    task_ref: str | None = None,
    run_ref: str | None = None,
    proof_ref: str | None = None,
    branch_ref: str | None = None,
    fork_reason_ref: str | None = None,
    evidence_refs: list[str] | None = None,
    receipt_refs: list[str] | None = None,
    proof_refs: list[str] | None = None,
) -> RuntimeSessionLineageNode:
    return RuntimeSessionLineageNode(
        node_ref=node_ref,
        node_kind=node_kind,
        session_ref=session_ref,
        parent_node_ref=parent_node_ref,
        child_node_refs=child_node_refs or [],
        user_request_ref=user_request_ref,
        task_ref=task_ref,
        run_ref=run_ref,
        proof_ref=proof_ref,
        branch_ref=branch_ref,
        fork_reason_ref=fork_reason_ref,
        retrieval_log_ref=retrieval_log_ref,
        safe_summary=safe_summary,
        lineage_depth=lineage_depth,
        evidence_refs=evidence_refs or [],
        receipt_refs=receipt_refs or [],
        proof_refs=proof_refs or [],
        blocked_authority_refs=list(RUNTIME_SESSION_LINEAGE_BLOCKED_AUTHORITY_REFS),
    )


def _fork(
    *,
    fork_ref: str,
    status: RuntimeLineageForkStatus,
    parent_session_ref: str,
    child_session_ref: str,
    parent_node_ref: str,
    child_node_ref: str,
    branch_ref: str,
    reason_ref: str,
    operator_intent_ref: str,
    redacted_fork_envelope_ref: str,
    retrieval_log_ref: str,
    compare_view_ref: str,
    safe_summary: str,
    proof_refs: list[str],
    evidence_refs: list[str],
) -> RuntimeSessionForkPosture:
    return RuntimeSessionForkPosture(
        fork_ref=fork_ref,
        status=status,
        parent_session_ref=parent_session_ref,
        child_session_ref=child_session_ref,
        parent_node_ref=parent_node_ref,
        child_node_ref=child_node_ref,
        branch_ref=branch_ref,
        reason_ref=reason_ref,
        operator_intent_ref=operator_intent_ref,
        redacted_fork_envelope_ref=redacted_fork_envelope_ref,
        retrieval_log_ref=retrieval_log_ref,
        compare_view_ref=compare_view_ref,
        safe_summary=safe_summary,
        proof_refs=proof_refs,
        evidence_refs=evidence_refs,
        blocked_authority_refs=list(RUNTIME_SESSION_LINEAGE_BLOCKED_AUTHORITY_REFS),
    )


def _default_nodes() -> list[RuntimeSessionLineageNode]:
    root = "lineage-node-ref:phase-19:operator-request"
    task = "lineage-node-ref:phase-19:coding-task"
    run = "lineage-node-ref:phase-19:runtime-run"
    proof = "lineage-node-ref:phase-19:proof-record"
    review = "lineage-node-ref:phase-19:review-fork"
    retry = "lineage-node-ref:phase-19:retry-fork"
    comparison = "lineage-node-ref:phase-19:comparison-fork"
    return [
        _node(
            node_ref=root,
            node_kind=RuntimeLineageNodeKind.user_request,
            session_ref="session-ref:hermes-lineage:operator-request",
            user_request_ref="user-request-ref:hermes-lineage:operator-task",
            retrieval_log_ref="retrieval-log-ref:session-lineage:operator-request",
            safe_summary=(
                "Operator request is represented by a safe ref and branches into "
                "task, review, retry, and comparison posture."
            ),
            lineage_depth=0,
            child_node_refs=[task, review, retry, comparison],
            evidence_refs=["evidence-ref:session-lineage:operator-request"],
            proof_refs=[RUNTIME_SESSION_LINEAGE_PROOF_REF],
        ),
        _node(
            node_ref=task,
            node_kind=RuntimeLineageNodeKind.coding_task,
            session_ref="coding-session:mock-fallback",
            parent_node_ref=root,
            child_node_refs=[run],
            user_request_ref="user-request-ref:hermes-lineage:operator-task",
            task_ref="coding-task-ref:cockpit:read-model",
            branch_ref="branch-ref:session-lineage:primary-approach",
            retrieval_log_ref="retrieval-log-ref:session-lineage:primary-task",
            safe_summary=(
                "Primary task branch links coding session, task, run, and proof "
                "refs without file mutation or shell work."
            ),
            lineage_depth=1,
            evidence_refs=["evidence-ref:coding-cockpit:read-model"],
            proof_refs=["proof-ref:coding-cockpit:session-read-model"],
        ),
        _node(
            node_ref=run,
            node_kind=RuntimeLineageNodeKind.runtime_run,
            session_ref="runtime-session-ref:hermes-agent:sample",
            parent_node_ref=task,
            child_node_refs=[proof],
            user_request_ref="user-request-ref:hermes-lineage:operator-task",
            task_ref="coding-task-ref:cockpit:read-model",
            run_ref="runtime-run-ref:hermes-agent:mock-approval-wait",
            branch_ref="branch-ref:session-lineage:primary-approach",
            retrieval_log_ref="retrieval-log-ref:session-lineage:runtime-run",
            safe_summary=(
                "Runtime run node links delegated runtime posture to UAA proof "
                "refs while dispatch remains blocked."
            ),
            lineage_depth=2,
            evidence_refs=["evidence-ref:runtime-run-events:phase-03"],
            proof_refs=["proof-ref:hermes-runtime-adoption:phase-03:run-events"],
        ),
        _node(
            node_ref=proof,
            node_kind=RuntimeLineageNodeKind.proof_record,
            session_ref="session-ref:proof:local",
            parent_node_ref=run,
            user_request_ref="user-request-ref:hermes-lineage:operator-task",
            task_ref="coding-task-ref:cockpit:read-model",
            run_ref="runtime-run-ref:hermes-agent:mock-approval-wait",
            proof_ref="proof-ref:hermes-runtime-adoption:phase-19:lineage-proof",
            branch_ref="branch-ref:session-lineage:primary-approach",
            retrieval_log_ref="retrieval-log-ref:session-lineage:proof-record",
            safe_summary=(
                "Proof node binds evidence and receipt refs for the primary "
                "branch without exposing transcript or runtime payload content."
            ),
            lineage_depth=3,
            evidence_refs=["evidence-ref:session-lineage:proof-binding"],
            receipt_refs=["receipt-ref:session-lineage:read-only"],
            proof_refs=["proof-ref:hermes-runtime-adoption:phase-19:lineage-proof"],
        ),
        _node(
            node_ref=review,
            node_kind=RuntimeLineageNodeKind.review_branch,
            session_ref="session-ref:hermes-lineage:review-branch",
            parent_node_ref=root,
            user_request_ref="user-request-ref:hermes-lineage:operator-task",
            branch_ref="branch-ref:session-lineage:review",
            fork_reason_ref="fork-reason-ref:session-lineage:second-opinion",
            retrieval_log_ref="retrieval-log-ref:session-lineage:review-branch",
            safe_summary=(
                "Review branch is available as proposal lineage only; no advisor "
                "runtime is called."
            ),
            lineage_depth=1,
            evidence_refs=["evidence-ref:session-lineage:review-branch"],
            proof_refs=[RUNTIME_SESSION_LINEAGE_PROOF_REF],
        ),
        _node(
            node_ref=retry,
            node_kind=RuntimeLineageNodeKind.retry_branch,
            session_ref="session-ref:hermes-lineage:retry-branch",
            parent_node_ref=root,
            user_request_ref="user-request-ref:hermes-lineage:operator-task",
            branch_ref="branch-ref:session-lineage:retry-after-blocker",
            fork_reason_ref="fork-reason-ref:session-lineage:blocked-retry",
            retrieval_log_ref="retrieval-log-ref:session-lineage:retry-branch",
            safe_summary=(
                "Retry branch records recovery posture and blocker refs without "
                "replaying raw context."
            ),
            lineage_depth=1,
            evidence_refs=["evidence-ref:session-lineage:retry-branch"],
            proof_refs=[RUNTIME_SESSION_LINEAGE_PROOF_REF],
        ),
        _node(
            node_ref=comparison,
            node_kind=RuntimeLineageNodeKind.comparison_branch,
            session_ref="session-ref:hermes-lineage:comparison-branch",
            parent_node_ref=root,
            user_request_ref="user-request-ref:hermes-lineage:operator-task",
            branch_ref="branch-ref:session-lineage:compare-approaches",
            fork_reason_ref="fork-reason-ref:session-lineage:compare-approaches",
            retrieval_log_ref="retrieval-log-ref:session-lineage:comparison-branch",
            safe_summary=(
                "Comparison branch links alternate plans by safe ref only and "
                "requires explicit operator intent before any future dispatch."
            ),
            lineage_depth=1,
            evidence_refs=["evidence-ref:session-lineage:comparison-branch"],
            proof_refs=[RUNTIME_SESSION_LINEAGE_PROOF_REF],
        ),
    ]


def _default_forks() -> list[RuntimeSessionForkPosture]:
    parent = "session-ref:hermes-lineage:operator-request"
    root = "lineage-node-ref:phase-19:operator-request"
    return [
        _fork(
            fork_ref="fork-ref:session-lineage:review-second-opinion",
            status=RuntimeLineageForkStatus.promotion_ready,
            parent_session_ref=parent,
            child_session_ref="session-ref:hermes-lineage:review-branch",
            parent_node_ref=root,
            child_node_ref="lineage-node-ref:phase-19:review-fork",
            branch_ref="branch-ref:session-lineage:review",
            reason_ref="fork-reason-ref:session-lineage:second-opinion",
            operator_intent_ref="operator-intent-ref:session-lineage:review",
            redacted_fork_envelope_ref="fork-envelope-ref:session-lineage:review",
            retrieval_log_ref="retrieval-log-ref:session-lineage:review-branch",
            compare_view_ref="compare-view-ref:session-lineage:review",
            safe_summary=(
                "Review fork has the refs needed for a future explicit "
                "second-opinion lane, but no runtime dispatch is enabled."
            ),
            proof_refs=[RUNTIME_SESSION_LINEAGE_PROOF_REF],
            evidence_refs=["evidence-ref:session-lineage:review-fork"],
        ),
        _fork(
            fork_ref="fork-ref:session-lineage:retry-after-blocker",
            status=RuntimeLineageForkStatus.read_only_lineage,
            parent_session_ref=parent,
            child_session_ref="session-ref:hermes-lineage:retry-branch",
            parent_node_ref=root,
            child_node_ref="lineage-node-ref:phase-19:retry-fork",
            branch_ref="branch-ref:session-lineage:retry-after-blocker",
            reason_ref="fork-reason-ref:session-lineage:blocked-retry",
            operator_intent_ref="operator-intent-ref:session-lineage:retry",
            redacted_fork_envelope_ref="fork-envelope-ref:session-lineage:retry",
            retrieval_log_ref="retrieval-log-ref:session-lineage:retry-branch",
            compare_view_ref="compare-view-ref:session-lineage:retry",
            safe_summary=(
                "Retry fork records recovery posture and blocked state refs for "
                "inspection only."
            ),
            proof_refs=[RUNTIME_SESSION_LINEAGE_PROOF_REF],
            evidence_refs=["evidence-ref:session-lineage:retry-fork"],
        ),
        _fork(
            fork_ref="fork-ref:session-lineage:compare-approaches",
            status=RuntimeLineageForkStatus.blocked_raw_clone,
            parent_session_ref=parent,
            child_session_ref="session-ref:hermes-lineage:comparison-branch",
            parent_node_ref=root,
            child_node_ref="lineage-node-ref:phase-19:comparison-fork",
            branch_ref="branch-ref:session-lineage:compare-approaches",
            reason_ref="fork-reason-ref:session-lineage:compare-approaches",
            operator_intent_ref="operator-intent-ref:session-lineage:comparison",
            redacted_fork_envelope_ref="fork-envelope-ref:session-lineage:comparison",
            retrieval_log_ref="retrieval-log-ref:session-lineage:comparison-branch",
            compare_view_ref="compare-view-ref:session-lineage:comparison",
            safe_summary=(
                "Comparison fork stays blocked for raw transcript cloning and "
                "hidden context transfer until an exact promotion lane exists."
            ),
            proof_refs=[RUNTIME_SESSION_LINEAGE_PROOF_REF],
            evidence_refs=["evidence-ref:session-lineage:comparison-fork"],
        ),
    ]


def build_runtime_session_lineage_read_model() -> RuntimeSessionLineageReadModel:
    return build_runtime_session_lineage_read_model_from_authority_catalog(
        authority_decision_catalog=build_authority_decision_catalog()
    )


def build_runtime_session_lineage_read_model_from_authority_catalog(
    *,
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry],
) -> RuntimeSessionLineageReadModel:
    authority_entry = _authority_entry(authority_decision_catalog)
    nodes = _default_nodes()
    forks = _default_forks()
    model = RuntimeSessionLineageReadModel(
        authority_state_route_ref=RUNTIME_SESSION_LINEAGE_AUTHORITY_STATE_ROUTE_REF,
        authority_state_cli_ref=RUNTIME_SESSION_LINEAGE_AUTHORITY_STATE_CLI_REF,
        authority_state_mapping_ref=authority_entry.lane_ref,
        authority_state_catalog_ref=authority_entry.catalog_ref,
        authority_state_decision_ref=authority_entry.decision.decision_ref,
        authority_state_decision_outcome=_authority_value(
            authority_entry.decision.outcome
        ),
        authority_state_status=authority_entry.status,
        authority_state_operator_message=authority_entry.decision.operator_message,
        authority_state_reason_refs=list(authority_entry.decision.reason_refs),
        unsupported_adapter_refs=list(authority_entry.unsupported_adapter_refs),
        root_node_refs=["lineage-node-ref:phase-19:operator-request"],
        nodes=nodes,
        forks=forks,
        node_count=len(nodes),
        fork_count=len(forks),
        root_count=1,
        parent_child_link_count=sum(len(node.child_node_refs) for node in nodes),
        max_lineage_depth=max(node.lineage_depth for node in nodes),
        blocked_authority_refs=list(RUNTIME_SESSION_LINEAGE_BLOCKED_AUTHORITY_REFS),
        proof_refs=[RUNTIME_SESSION_LINEAGE_PROOF_REF],
        verifier_refs=["verifier-ref:hermes-runtime-adoption:phase-19"],
        next_safe_action_refs=[
            "next-safe-action-ref:session-lineage:inspect-read-model",
            "next-safe-action-ref:session-lineage:require-redacted-fork-envelope",
            "next-safe-action-ref:session-lineage:keep-raw-cloning-blocked",
        ],
    )
    payload = model.model_dump(mode="json", exclude={"snapshot_hash_ref"})
    return model.model_copy(update={"snapshot_hash_ref": _hash_payload(payload)})


def _authority_entry(
    authority_decision_catalog: list[AuthorityDecisionCatalogEntry],
) -> AuthorityDecisionCatalogEntry:
    for entry in authority_decision_catalog:
        if entry.lane_ref == RUNTIME_SESSION_LINEAGE_AUTHORITY_MAPPING_REF:
            return entry
    raise ValueError("RUNTIME_SESSION_LINEAGE_AUTHORITY_MAPPING_NOT_FOUND")


def _authority_value(value: object) -> str:
    return str(getattr(value, "value", value))
