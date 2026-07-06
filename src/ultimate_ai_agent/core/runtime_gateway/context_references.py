from __future__ import annotations

import hashlib
import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import GOVERNED_RUNTIME_REDACTIONS
from ultimate_ai_agent.core.runtime_gateway.delegation import (
    RUNTIME_DELEGATION_CONTROL_CENTER_REF,
)
from ultimate_ai_agent.core.runtime_gateway.sensitive_context import (
    SENSITIVE_CONTEXT_BLOCKED_AUTHORITY_REFS,
    SENSITIVE_CONTEXT_CLASSIFIER_REF,
    SENSITIVE_CONTEXT_GUARD_REF,
    validate_sensitive_context_candidate_allowed,
)


RUNTIME_CONTEXT_REFERENCES_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-context-references:v1"
)
RUNTIME_CONTEXT_REFERENCES_ROUTE_REF = "GET /api/runtime/context-references"
RUNTIME_CONTEXT_REFERENCES_CLI_REF = "uaa runtime inspect-context-references"
RUNTIME_CONTEXT_REFERENCES_PREVIEW_REF = (
    "context-preview-ref:runtime:governed-safe-refs"
)
RUNTIME_CONTEXT_REFERENCES_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-16:context-references"
)

RUNTIME_CONTEXT_REFERENCES_BLOCKED_AUTHORITY_REFS = [
    "blocked-authority:context-references-no-live-url-fetch",
    "blocked-authority:context-references-no-raw-path-persistence",
    "blocked-authority:context-references-no-raw-file-content",
    "blocked-authority:context-references-no-automatic-context-injection",
    "blocked-authority:context-references-no-protected-config-read",
    "blocked-authority:context-references-no-provider-model-call",
    "blocked-authority:context-references-no-connector-write",
    "blocked-authority:context-references-no-shell-execution",
    "blocked-authority:context-references-no-browser-automation",
    "blocked-authority:context-references-no-production-authority",
]


class RuntimeContextReferenceKind(str, Enum):
    file = "file"
    folder = "folder"
    diff = "diff"
    url_evidence = "url_evidence"
    run = "run"
    proof = "proof"
    task = "task"
    memory = "memory"
    crm_object = "crm_object"
    issue = "issue"


class RuntimeContextReferenceStatus(str, Enum):
    included = "included"
    candidate = "candidate"
    blocked = "blocked"
    excluded = "excluded"


CONTEXT_REF_KIND_PREFIXES = {
    RuntimeContextReferenceKind.file.value: "file-ref:",
    RuntimeContextReferenceKind.folder.value: "folder-ref:",
    RuntimeContextReferenceKind.diff.value: "diff-ref:",
    RuntimeContextReferenceKind.url_evidence.value: "url-evidence-ref:",
    RuntimeContextReferenceKind.run.value: "run-ref:",
    RuntimeContextReferenceKind.proof.value: "proof-ref:",
    RuntimeContextReferenceKind.task.value: "task-ref:",
    RuntimeContextReferenceKind.memory.value: "memory-ref:",
    RuntimeContextReferenceKind.crm_object.value: "crm-object-ref:",
    RuntimeContextReferenceKind.issue.value: "issue-ref:",
}


class RuntimeContextReference(BaseModel):
    context_ref: str
    ref_kind: RuntimeContextReferenceKind
    status: RuntimeContextReferenceStatus
    display_label: str
    safe_summary: str
    source_ref: str
    source_route_ref: str
    token_estimate: int = Field(..., ge=0)
    why_included_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    preview_available: bool = True
    operator_selected: bool = True
    live_url_fetch_performed: bool = False
    raw_path_persisted: bool = False
    raw_file_content_persisted: bool = False
    raw_prompt_persisted: bool = False
    raw_response_persisted: bool = False
    raw_provider_payload_persisted: bool = False
    secret_config_read_performed: bool = False
    automatic_context_injection_performed: bool = False
    provider_model_call_performed: bool = False
    connector_write_performed: bool = False
    shell_execution_performed: bool = False
    browser_automation_performed: bool = False
    production_authority_performed: bool = False
    sensitive_context_guard_ref: str = SENSITIVE_CONTEXT_GUARD_REF
    sensitive_context_classifier_ref: str = SENSITIVE_CONTEXT_CLASSIFIER_REF
    sensitive_context_guard_applied: bool = True

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_reference(self) -> "RuntimeContextReference":
        validate_execution_ref(self.context_ref, "context_ref")
        validate_execution_ref(self.source_ref, "source_ref")
        validate_execution_ref(
            self.sensitive_context_guard_ref,
            "sensitive_context_guard_ref",
        )
        validate_execution_ref(
            self.sensitive_context_classifier_ref,
            "sensitive_context_classifier_ref",
        )
        for field_name in (
            "why_included_refs",
            "evidence_refs",
            "proof_refs",
            "blocked_authority_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.display_label, "display_label"),
            (self.safe_summary, "safe_summary"),
            (self.source_route_ref, "source_route_ref"),
        ]:
            validate_safe_execution_text(value, field_name)
        expected_prefix = CONTEXT_REF_KIND_PREFIXES[str(self.ref_kind)]
        if not self.context_ref.startswith(expected_prefix):
            raise ValueError("RUNTIME_CONTEXT_REF_KIND_PREFIX_MISMATCH")
        if not self.why_included_refs:
            raise ValueError("RUNTIME_CONTEXT_REF_WHY_INCLUDED_REQUIRED")
        if self.status == RuntimeContextReferenceStatus.blocked.value:
            if self.preview_available:
                raise ValueError("RUNTIME_CONTEXT_REF_BLOCKED_PREVIEW_DENIED")
            if not self.blocked_authority_refs:
                raise ValueError("RUNTIME_CONTEXT_REF_BLOCKER_REQUIRED")
        if not self.sensitive_context_guard_applied:
            raise ValueError("RUNTIME_CONTEXT_REF_SENSITIVE_GUARD_REQUIRED")
        for candidate, candidate_kind in (
            (self.context_ref, "context-ref"),
            (self.source_ref, "source-ref"),
        ):
            validate_sensitive_context_candidate_allowed(
                candidate,
                candidate_kind=candidate_kind,
                status=str(self.status),
                preview_available=self.preview_available,
                blocked_authority_refs=self.blocked_authority_refs,
            )
        denied_flags = {
            "live_url_fetch_performed": self.live_url_fetch_performed,
            "raw_path_persisted": self.raw_path_persisted,
            "raw_file_content_persisted": self.raw_file_content_persisted,
            "raw_prompt_persisted": self.raw_prompt_persisted,
            "raw_response_persisted": self.raw_response_persisted,
            "raw_provider_payload_persisted": self.raw_provider_payload_persisted,
            "secret_config_read_performed": self.secret_config_read_performed,
            "automatic_context_injection_performed": (
                self.automatic_context_injection_performed
            ),
            "provider_model_call_performed": self.provider_model_call_performed,
            "connector_write_performed": self.connector_write_performed,
            "shell_execution_performed": self.shell_execution_performed,
            "browser_automation_performed": self.browser_automation_performed,
            "production_authority_performed": self.production_authority_performed,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_CONTEXT_REFERENCES_AUTHORITY_DENIED: " + ", ".join(enabled)
            )
        return self


class RuntimeContextReferencePostureReadModel(BaseModel):
    schema_version: str = "runtime_context_references.v1"
    contract_ref: str = RUNTIME_CONTEXT_REFERENCES_CONTRACT_REF
    status: str = "read_only_context_reference_preview"
    preview_ref: str = RUNTIME_CONTEXT_REFERENCES_PREVIEW_REF
    preview_hash_ref: str = "snapshot-hash-ref:runtime-context-references:pending"
    route_ref: str = RUNTIME_CONTEXT_REFERENCES_ROUTE_REF
    cli_ref: str = RUNTIME_CONTEXT_REFERENCES_CLI_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    safe_ref_grammar_ref: str = "safe-ref-grammar:runtime-context-references"
    safe_summary: str = (
        "Context references are operator-selected safe refs with bounded "
        "previews, budget estimates, why-included refs, and blocked live-fetch "
        "or automatic injection posture."
    )
    sensitive_context_guard_ref: str = SENSITIVE_CONTEXT_GUARD_REF
    sensitive_context_classifier_ref: str = SENSITIVE_CONTEXT_CLASSIFIER_REF
    sensitive_context_blocking_enabled: bool = True
    sensitive_context_bypass_enabled: bool = False
    sensitive_context_bypass_approval_required: bool = True
    sensitive_context_blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(SENSITIVE_CONTEXT_BLOCKED_AUTHORITY_REFS)
    )
    references: list[RuntimeContextReference]
    reference_count: int = 0
    included_count: int = 0
    candidate_count: int = 0
    blocked_count: int = 0
    token_budget_limit: int = 0
    estimated_token_count: int = 0
    token_budget_remaining: int = 0
    budget_state_ref: str = "budget-state-ref:runtime-context:within-budget"
    supported_ref_kinds: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    live_url_fetch_enabled: bool = False
    raw_path_persistence_enabled: bool = False
    raw_file_content_persistence_enabled: bool = False
    automatic_context_injection_enabled: bool = False
    hidden_prompt_context_enabled: bool = False
    secret_config_reads_enabled: bool = False
    provider_model_call_enabled: bool = False
    connector_writes_enabled: bool = False
    shell_execution_enabled: bool = False
    browser_automation_enabled: bool = False
    production_authority_enabled: bool = False
    redactions_applied: list[str] = Field(
        default_factory=lambda: (
            list(GOVERNED_RUNTIME_REDACTIONS)
            + [
                "raw_paths_omitted",
                "raw_file_content_omitted",
                "raw_url_body_omitted",
                "raw_prompt_response_omitted",
                "secret_config_values_omitted",
            ]
        )
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeContextReferencePostureReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.preview_ref, "preview_ref"),
            (self.preview_hash_ref, "preview_hash_ref"),
            (self.control_center_ref, "control_center_ref"),
            (self.safe_ref_grammar_ref, "safe_ref_grammar_ref"),
            (self.budget_state_ref, "budget_state_ref"),
            (self.sensitive_context_guard_ref, "sensitive_context_guard_ref"),
            (
                self.sensitive_context_classifier_ref,
                "sensitive_context_classifier_ref",
            ),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "supported_ref_kinds",
            "blocked_authority_refs",
            "proof_refs",
            "verifier_refs",
            "next_safe_action_refs",
            "sensitive_context_blocked_authority_refs",
        ):
            for ref in getattr(self, field_name):
                validate_execution_ref(ref, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.status, "status"),
            (self.route_ref, "route_ref"),
            (self.cli_ref, "cli_ref"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(str(value), field_name)
        if self.reference_count != len(self.references):
            raise ValueError("RUNTIME_CONTEXT_REFERENCES_COUNT_MISMATCH")
        if self.included_count != len(
            [
                ref
                for ref in self.references
                if ref.status == RuntimeContextReferenceStatus.included.value
            ]
        ):
            raise ValueError("RUNTIME_CONTEXT_REFERENCES_INCLUDED_COUNT_MISMATCH")
        if self.candidate_count != len(
            [
                ref
                for ref in self.references
                if ref.status == RuntimeContextReferenceStatus.candidate.value
            ]
        ):
            raise ValueError("RUNTIME_CONTEXT_REFERENCES_CANDIDATE_COUNT_MISMATCH")
        if self.blocked_count != len(
            [
                ref
                for ref in self.references
                if ref.status == RuntimeContextReferenceStatus.blocked.value
            ]
        ):
            raise ValueError("RUNTIME_CONTEXT_REFERENCES_BLOCKED_COUNT_MISMATCH")
        expected_kinds = sorted(f"context-ref-kind:{kind.value}" for kind in RuntimeContextReferenceKind)
        if sorted(self.supported_ref_kinds) != expected_kinds:
            raise ValueError("RUNTIME_CONTEXT_REFERENCES_KIND_GRAMMAR_MISMATCH")
        if self.estimated_token_count != sum(
            ref.token_estimate
            for ref in self.references
            if ref.status == RuntimeContextReferenceStatus.included.value
        ):
            raise ValueError("RUNTIME_CONTEXT_REFERENCES_TOKEN_ESTIMATE_MISMATCH")
        if (
            self.token_budget_remaining
            != self.token_budget_limit - self.estimated_token_count
        ):
            raise ValueError("RUNTIME_CONTEXT_REFERENCES_TOKEN_BUDGET_MISMATCH")
        denied_flags = {
            "live_url_fetch_enabled": self.live_url_fetch_enabled,
            "raw_path_persistence_enabled": self.raw_path_persistence_enabled,
            "raw_file_content_persistence_enabled": (
                self.raw_file_content_persistence_enabled
            ),
            "automatic_context_injection_enabled": (
                self.automatic_context_injection_enabled
            ),
            "hidden_prompt_context_enabled": self.hidden_prompt_context_enabled,
            "secret_config_reads_enabled": self.secret_config_reads_enabled,
            "provider_model_call_enabled": self.provider_model_call_enabled,
            "connector_writes_enabled": self.connector_writes_enabled,
            "shell_execution_enabled": self.shell_execution_enabled,
            "browser_automation_enabled": self.browser_automation_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_CONTEXT_REFERENCES_AUTHORITY_DENIED: " + ", ".join(enabled)
            )
        if not self.sensitive_context_blocking_enabled:
            raise ValueError("RUNTIME_CONTEXT_REFERENCES_SENSITIVE_GUARD_REQUIRED")
        if self.sensitive_context_bypass_enabled:
            raise ValueError("RUNTIME_CONTEXT_REFERENCES_SENSITIVE_BYPASS_DENIED")
        if not self.sensitive_context_bypass_approval_required:
            raise ValueError("RUNTIME_CONTEXT_REFERENCES_BYPASS_APPROVAL_REQUIRED")
        if set(SENSITIVE_CONTEXT_BLOCKED_AUTHORITY_REFS) - set(
            self.sensitive_context_blocked_authority_refs
        ):
            raise ValueError("RUNTIME_CONTEXT_REFERENCES_SENSITIVE_BLOCKERS_REQUIRED")
        if RUNTIME_CONTEXT_REFERENCES_PROOF_REF not in self.proof_refs:
            raise ValueError("RUNTIME_CONTEXT_REFERENCES_PHASE_PROOF_REQUIRED")
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_CONTEXT_REFERENCES_BLOCKERS_REQUIRED")
        return self


def _hash_payload(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:24]
    return f"snapshot-hash-ref:runtime-context-references:{digest}"


def _context_ref(
    *,
    context_ref: str,
    ref_kind: RuntimeContextReferenceKind,
    status: RuntimeContextReferenceStatus,
    display_label: str,
    safe_summary: str,
    source_ref: str,
    source_route_ref: str,
    token_estimate: int,
    why_included_refs: list[str],
    evidence_refs: list[str] | None = None,
    proof_refs: list[str] | None = None,
    blocked_authority_refs: list[str] | None = None,
    preview_available: bool = True,
) -> RuntimeContextReference:
    return RuntimeContextReference(
        context_ref=context_ref,
        ref_kind=ref_kind,
        status=status,
        display_label=display_label,
        safe_summary=safe_summary,
        source_ref=source_ref,
        source_route_ref=source_route_ref,
        token_estimate=token_estimate,
        why_included_refs=why_included_refs,
        evidence_refs=evidence_refs or [],
        proof_refs=proof_refs or [],
        blocked_authority_refs=blocked_authority_refs
        or list(RUNTIME_CONTEXT_REFERENCES_BLOCKED_AUTHORITY_REFS),
        preview_available=preview_available,
    )


def _default_references() -> list[RuntimeContextReference]:
    return [
        _context_ref(
            context_ref="file-ref:repo-readme-summary",
            ref_kind=RuntimeContextReferenceKind.file,
            status=RuntimeContextReferenceStatus.included,
            display_label="README summary ref",
            safe_summary="Repo overview is represented by a safe file ref only.",
            source_ref="source-ref:repo-doc-summary",
            source_route_ref="repo-local-safe-ref-index",
            token_estimate=220,
            why_included_refs=["why-included-ref:context:repo-orientation"],
            evidence_refs=["evidence-ref:repo-readme-summary"],
        ),
        _context_ref(
            context_ref="folder-ref:runtime-gateway-safe-summary",
            ref_kind=RuntimeContextReferenceKind.folder,
            status=RuntimeContextReferenceStatus.included,
            display_label="Runtime gateway folder summary",
            safe_summary="Runtime gateway module scope is summarized without raw paths.",
            source_ref="source-ref:runtime-gateway-summary",
            source_route_ref="repo-local-safe-ref-index",
            token_estimate=260,
            why_included_refs=["why-included-ref:context:runtime-boundary"],
            proof_refs=["proof-ref:runtime-gateway-boundary"],
        ),
        _context_ref(
            context_ref="diff-ref:pending-phase-safe-summary",
            ref_kind=RuntimeContextReferenceKind.diff,
            status=RuntimeContextReferenceStatus.candidate,
            display_label="Pending phase diff summary",
            safe_summary="Diff context is available only as a bounded summary ref.",
            source_ref="source-ref:phase-diff-summary",
            source_route_ref="repo-local-safe-ref-index",
            token_estimate=0,
            why_included_refs=["why-included-ref:context:operator-review-candidate"],
        ),
        _context_ref(
            context_ref="url-evidence-ref:docs-homepage-safe-ref",
            ref_kind=RuntimeContextReferenceKind.url_evidence,
            status=RuntimeContextReferenceStatus.included,
            display_label="URL evidence ref",
            safe_summary="URL evidence may be cited as a reviewed ref; live fetch is blocked.",
            source_ref="source-ref:reviewed-url-evidence",
            source_route_ref="web-access-gateway-disabled-safe-ref",
            token_estimate=120,
            why_included_refs=["why-included-ref:context:reviewed-evidence"],
            evidence_refs=["evidence-ref:reviewed-url-metadata"],
        ),
        _context_ref(
            context_ref="run-ref:turn-run-approval-chain:sample",
            ref_kind=RuntimeContextReferenceKind.run,
            status=RuntimeContextReferenceStatus.included,
            display_label="Durable run ref",
            safe_summary="Durable run state is attachable as a safe ref.",
            source_ref="source-ref:turn-run-approval-chain",
            source_route_ref="GET /api/runtime/prepared-turn",
            token_estimate=180,
            why_included_refs=["why-included-ref:context:run-state"],
            proof_refs=["proof-ref:turn-run-approval-chain"],
        ),
        _context_ref(
            context_ref="proof-ref:hermes-runtime-adoption:phase-16:context-references",
            ref_kind=RuntimeContextReferenceKind.proof,
            status=RuntimeContextReferenceStatus.included,
            display_label="Proof ref",
            safe_summary="Proof ref ties this context posture to Phase 16 evidence.",
            source_ref="source-ref:phase-16-proof",
            source_route_ref="repo-local-safe-ref-index",
            token_estimate=80,
            why_included_refs=["why-included-ref:context:proof-linkage"],
            proof_refs=[RUNTIME_CONTEXT_REFERENCES_PROOF_REF],
        ),
        _context_ref(
            context_ref="task-ref:operator-loop-next-action",
            ref_kind=RuntimeContextReferenceKind.task,
            status=RuntimeContextReferenceStatus.included,
            display_label="Task ref",
            safe_summary="Task posture is safe-ref only and grants no action authority.",
            source_ref="source-ref:operator-loop-task",
            source_route_ref="GET /control-center/today",
            token_estimate=120,
            why_included_refs=["why-included-ref:context:operator-task"],
        ),
        _context_ref(
            context_ref="memory-ref:reviewed-preference-safe-summary",
            ref_kind=RuntimeContextReferenceKind.memory,
            status=RuntimeContextReferenceStatus.included,
            display_label="Reviewed memory ref",
            safe_summary="Memory is recall context only, not truth or authority.",
            source_ref="source-ref:reviewed-memory",
            source_route_ref="GET /control-center/memory/review",
            token_estimate=160,
            why_included_refs=["why-included-ref:context:reviewed-memory"],
        ),
        _context_ref(
            context_ref="crm-object-ref:relationship-safe-summary",
            ref_kind=RuntimeContextReferenceKind.crm_object,
            status=RuntimeContextReferenceStatus.included,
            display_label="CRM object ref",
            safe_summary="CRM object context is a redacted local read-model ref.",
            source_ref="source-ref:crm-local-command-center",
            source_route_ref="GET /control-center/crm/relationships",
            token_estimate=140,
            why_included_refs=["why-included-ref:context:crm-relationship"],
        ),
        _context_ref(
            context_ref="issue-ref:governed-runtime-followup",
            ref_kind=RuntimeContextReferenceKind.issue,
            status=RuntimeContextReferenceStatus.included,
            display_label="Issue ref",
            safe_summary="Issue context is represented as local safe-ref metadata.",
            source_ref="source-ref:work-board-issue",
            source_route_ref="GET /control-center/work-board",
            token_estimate=120,
            why_included_refs=["why-included-ref:context:work-board"],
        ),
        _context_ref(
            context_ref="file-ref:protected-config-blocked",
            ref_kind=RuntimeContextReferenceKind.file,
            status=RuntimeContextReferenceStatus.blocked,
            display_label="Protected config ref",
            safe_summary="Protected configuration remains blocked from context previews.",
            source_ref="source-ref:protected-config-blocked",
            source_route_ref="repo-local-safe-ref-index",
            token_estimate=0,
            why_included_refs=["why-included-ref:context:sensitive-config-blocked"],
            blocked_authority_refs=[
                "blocked-authority:context-references-no-protected-config-read",
                "blocked-authority:context-references-no-raw-path-persistence",
                *SENSITIVE_CONTEXT_BLOCKED_AUTHORITY_REFS,
            ],
            preview_available=False,
        ),
    ]


def build_runtime_context_references_read_model() -> (
    RuntimeContextReferencePostureReadModel
):
    references = _default_references()
    included = [
        ref
        for ref in references
        if ref.status == RuntimeContextReferenceStatus.included.value
    ]
    candidates = [
        ref
        for ref in references
        if ref.status == RuntimeContextReferenceStatus.candidate.value
    ]
    blocked = [
        ref for ref in references if ref.status == RuntimeContextReferenceStatus.blocked.value
    ]
    token_budget_limit = 4000
    estimated_token_count = sum(ref.token_estimate for ref in included)
    model = RuntimeContextReferencePostureReadModel(
        references=references,
        reference_count=len(references),
        included_count=len(included),
        candidate_count=len(candidates),
        blocked_count=len(blocked),
        token_budget_limit=token_budget_limit,
        estimated_token_count=estimated_token_count,
        token_budget_remaining=token_budget_limit - estimated_token_count,
        supported_ref_kinds=[
            f"context-ref-kind:{kind.value}" for kind in RuntimeContextReferenceKind
        ],
        blocked_authority_refs=list(RUNTIME_CONTEXT_REFERENCES_BLOCKED_AUTHORITY_REFS),
        proof_refs=[RUNTIME_CONTEXT_REFERENCES_PROOF_REF],
        verifier_refs=["verifier:hermes-runtime-adoption-phase-16"],
        next_safe_action_refs=[
            "next-safe-action-ref:context-references:review-preview",
            "next-safe-action-ref:context-references:keep-live-fetch-blocked",
            "next-safe-action-ref:context-references:require-context-pack-receipt-before-injection",
        ],
    )
    payload = model.model_dump(mode="json", exclude={"preview_hash_ref"})
    return model.model_copy(update={"preview_hash_ref": _hash_payload(payload)})
