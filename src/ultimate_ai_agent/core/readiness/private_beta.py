from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.readiness.private_operator_trial import (
    PRIVATE_PRODUCT_LOOP_TRIAL_SCRIPT_CONTRACT_REF,
)


PRIVATE_BETA_READINESS_CONTRACT_REF = (
    "contract-ref:private-beta-readiness-gate:v1"
)

PrivateBetaReadinessSurface = Literal[
    "Start Here",
    "Setup Assistant",
    "Today",
    "Morning Briefing",
    "Action Inbox",
    "Proof Detail",
    "Memory Review",
    "Evidence Timeline",
    "Trust Authority Map",
    "Chat/Plans Handoff",
    "Governed Code",
    "CRM-Lite Follow-Ups",
    "Dogfood Live Loop",
]

PrivateBetaReadinessGateState = Literal[
    "pass",
    "fail",
    "skipped",
    "blocked",
    "partial",
    "mock_only",
    "accepted_failure",
]

PRIVATE_BETA_READINESS_REQUIRED_SURFACES: list[PrivateBetaReadinessSurface] = [
    "Start Here",
    "Setup Assistant",
    "Today",
    "Morning Briefing",
    "Action Inbox",
    "Proof Detail",
    "Memory Review",
    "Evidence Timeline",
    "Trust Authority Map",
    "Chat/Plans Handoff",
    "Governed Code",
    "CRM-Lite Follow-Ups",
    "Dogfood Live Loop",
]

PRIVATE_BETA_READINESS_ACCEPTANCE_STATES: list[PrivateBetaReadinessGateState] = [
    "pass",
    "fail",
    "skipped",
    "blocked",
    "partial",
    "mock_only",
    "accepted_failure",
]

PRIVATE_BETA_READINESS_REQUIRED_REF_FIELDS = [
    "criterion_ref",
    "surface",
    "gate_state",
    "safe_summary",
    "evidence_refs",
    "required_contract_refs",
    "acceptance_refs",
    "missing_evidence_refs",
    "blocked_state_refs",
    "next_safe_action",
]

_PRIVATE_BETA_READINESS_COMMON_BLOCKED_REFS = [
    "blocked-state:no-public-beta",
    "blocked-state:no-public-distribution",
    "blocked-state:no-production-readiness-claim",
    "blocked-state:no-production-authority",
    "blocked-state:no-broad-autonomy",
    "blocked-state:no-connector-write",
    "blocked-state:no-provider-model-authority",
    "blocked-state:no-unrestricted-shell",
    "blocked-state:no-shell-subprocess-execution",
    "blocked-state:no-remote-execution",
    "blocked-state:no-account-sync",
    "blocked-state:no-crm-write",
    "blocked-state:no-memory-write",
    "blocked-state:no-automatic-memory-write",
    "blocked-state:no-context-injection",
    "blocked-state:no-approval-grant-capture",
    "blocked-state:no-action-execution",
    "blocked-state:no-code-apply-execution",
]

PRIVATE_BETA_READINESS_SURFACE_BLOCKED_REFS: dict[str, list[str]] = {
    "Start Here": [
        "blocked-state:private-beta:start-here-runtime-control",
    ],
    "Setup Assistant": [
        "blocked-state:private-beta:setup-install",
        "blocked-state:private-beta:setup-launch-agent",
        "blocked-state:private-beta:setup-notarization",
        "blocked-state:private-beta:setup-login-material-capture",
    ],
    "Today": [
        "blocked-state:private-beta:today-rehearsal-receipts",
    ],
    "Morning Briefing": [
        "blocked-state:private-beta:briefing-source-reads",
        "blocked-state:private-beta:briefing-delivery",
    ],
    "Action Inbox": [
        "blocked-state:private-beta:action-inbox-execution",
        "blocked-state:private-beta:approval-capture",
    ],
    "Proof Detail": [
        "blocked-state:private-beta:proof-approval-grant",
        "blocked-state:private-beta:proof-rollback-execution",
    ],
    "Memory Review": [
        "blocked-state:private-beta:memory-write",
        "blocked-state:private-beta:memory-context-injection",
    ],
    "Evidence Timeline": [
        "blocked-state:private-beta:evidence-run-receipts",
    ],
    "Trust Authority Map": [
        "blocked-state:private-beta:trust-authority-grant",
        "blocked-state:private-beta:trust-standing-authority",
    ],
    "Chat/Plans Handoff": [
        "blocked-state:private-beta:handoff-execution",
        "blocked-state:private-beta:model-output-authority",
    ],
    "Governed Code": [
        "blocked-state:private-beta:code-apply",
        "blocked-state:private-beta:code-rollback-execution",
    ],
    "CRM-Lite Follow-Ups": [
        "blocked-state:private-beta:crm-write",
        "blocked-state:private-beta:account-sync",
    ],
    "Dogfood Live Loop": [
        "blocked-state:private-beta:dogfood-seed-from-gate",
        "blocked-state:private-beta:dogfood-gate-execution",
    ],
}

PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS = list(
    dict.fromkeys(
        [
            *_PRIVATE_BETA_READINESS_COMMON_BLOCKED_REFS,
            *[
                blocked_ref
                for refs in PRIVATE_BETA_READINESS_SURFACE_BLOCKED_REFS.values()
                for blocked_ref in refs
            ],
        ]
    )
)

_DENIED_FLAGS = [
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_readiness_claim_enabled",
    "production_authority_enabled",
    "broad_autonomy_enabled",
    "connector_write_enabled",
    "provider_model_authority_allowed",
    "unrestricted_shell_enabled",
    "shell_subprocess_execution_enabled",
    "remote_execution_enabled",
    "account_sync_enabled",
    "crm_write_enabled",
    "memory_write_authorized",
    "automatic_memory_write_authorized",
    "context_injection_authorized",
    "approval_grant_capture_enabled",
    "action_execution_enabled",
    "code_apply_execution_enabled",
]

_UNSAFE_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider payload",
    "provider_payload",
    "raw source",
    "raw file",
    "raw_file",
    "raw log",
    "raw_log",
    "browser state",
    "shell history",
    "account identifier",
    "username",
    "hostname",
    "credential",
    "api key",
    "authorization",
    "password",
    "token",
    "secret",
    "/users/",
    "/home/",
    "/var/",
    "/etc/",
)


class PrivateBetaReadinessCriterion(BaseModel):
    contract_ref: str = PRIVATE_BETA_READINESS_CONTRACT_REF
    criterion_ref: str = Field(..., min_length=1)
    surface: PrivateBetaReadinessSurface
    gate_state: PrivateBetaReadinessGateState
    safe_summary: str = Field(..., min_length=1, max_length=420)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    required_contract_refs: list[str] = Field(default_factory=list, min_length=1)
    acceptance_refs: list[str] = Field(default_factory=list, min_length=1)
    missing_evidence_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS)
    )
    next_safe_action: str = Field(..., min_length=1, max_length=240)
    local_private_only: bool = True
    safe_refs_only: bool = True
    review_required: bool = True
    evidence_required: bool = True
    redaction_required: bool = True
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_readiness_claim_enabled: bool = False
    production_authority_enabled: bool = False
    broad_autonomy_enabled: bool = False
    connector_write_enabled: bool = False
    provider_model_authority_allowed: bool = False
    unrestricted_shell_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    remote_execution_enabled: bool = False
    account_sync_enabled: bool = False
    crm_write_enabled: bool = False
    memory_write_authorized: bool = False
    automatic_memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    approval_grant_capture_enabled: bool = False
    action_execution_enabled: bool = False
    code_apply_execution_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_criterion(self) -> "PrivateBetaReadinessCriterion":
        if self.contract_ref != PRIVATE_BETA_READINESS_CONTRACT_REF:
            raise ValueError("private beta readiness contract ref drifted")
        for field_name in ["contract_ref", "criterion_ref"]:
            _safe_ref(getattr(self, field_name), field_name)
        for field_name in [
            "evidence_refs",
            "required_contract_refs",
            "acceptance_refs",
            "missing_evidence_refs",
            "blocked_state_refs",
        ]:
            _safe_refs(getattr(self, field_name), field_name)
        for field_name in [
            "surface",
            "gate_state",
            "safe_summary",
            "next_safe_action",
        ]:
            _safe_text(str(getattr(self, field_name)), field_name)
        required_true = {
            "local_private_only": self.local_private_only,
            "safe_refs_only": self.safe_refs_only,
            "review_required": self.review_required,
            "evidence_required": self.evidence_required,
            "redaction_required": self.redaction_required,
        }
        missing_true = [name for name, value in required_true.items() if not value]
        if missing_true:
            raise ValueError(f"private beta readiness disabled {missing_true[0]}")
        missing_blocked = set(PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        )
        if missing_blocked:
            raise ValueError("private beta readiness criterion missing blocked refs")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag) is not False:
                raise ValueError(f"{flag} is denied by private beta readiness")
        return self


class PrivateBetaReadinessGate(BaseModel):
    contract_ref: str = PRIVATE_BETA_READINESS_CONTRACT_REF
    overall_gate_state: PrivateBetaReadinessGateState = "partial"
    status: str = "implemented_private_beta_readiness_gate_authority_blocked"
    evidence_packet_ref: str = "evidence-packet:private-beta-readiness:local-founder-loop"
    readiness_window_ref: str = "readiness-window:local-private-beta"
    full_strength_goal: str = (
        "Local-first command center where setup, daily loop, Action Inbox, "
        "exact local task commit, receipt, evidence, proof, reviewed memory, "
        "and Trust posture form one operator workflow."
    )
    repo_safe_scope: str = (
        "Backend-owned safe-ref readiness metadata, verifier coverage, and "
        "read-only presentation only; no runtime authority is granted."
    )
    blocked_authority_summary: str = (
        "Public beta, distribution, production authority, connector writes, "
        "provider calls, browser automation, shell subprocess, background "
        "autonomy, account sync, CRM writes, broad memory writes, context "
        "injection, Code apply, rollback execution, and action execution remain blocked."
    )
    promotion_path_refs: list[str] = Field(
        default_factory=lambda: [
            "promotion-path-ref:private-beta:rehearsal-receipts",
            "promotion-path-ref:private-beta:operator-review-notes",
            "promotion-path-ref:private-beta:api-perimeter-hardening",
            "promotion-path-ref:private-beta:scoped-authority-prs",
        ],
        min_length=1,
    )
    product_loop_trial_script_ref: str = PRIVATE_PRODUCT_LOOP_TRIAL_SCRIPT_CONTRACT_REF
    private_operator_trial_ledger_ref: str = (
        "ledger-ref:private-operator-trial-acceptance:v1"
    )
    required_surfaces: list[PrivateBetaReadinessSurface] = Field(
        default_factory=lambda: list(PRIVATE_BETA_READINESS_REQUIRED_SURFACES)
    )
    acceptance_states: list[PrivateBetaReadinessGateState] = Field(
        default_factory=lambda: list(PRIVATE_BETA_READINESS_ACCEPTANCE_STATES)
    )
    acceptance_state_definitions: list[dict[str, str | bool]]
    required_ref_fields: list[str] = Field(
        default_factory=lambda: list(PRIVATE_BETA_READINESS_REQUIRED_REF_FIELDS)
    )
    criteria: list[PrivateBetaReadinessCriterion] = Field(
        default_factory=list, min_length=1
    )
    surface_bindings: list[dict[str, str]]
    authority_posture: dict[str, bool]
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS)
    )
    missing_evidence_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = (
        "Run a local private beta rehearsal against safe refs, then record "
        "pass/fail/blocked evidence before any broader readiness claim."
    )
    local_private_only: bool = True
    safe_refs_only: bool = True
    review_required: bool = True
    evidence_required: bool = True
    redaction_required: bool = True
    private_beta_execution_authorized: bool = False
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_readiness_claim_enabled: bool = False
    production_authority_enabled: bool = False
    broad_autonomy_enabled: bool = False
    connector_write_enabled: bool = False
    provider_model_authority_allowed: bool = False
    unrestricted_shell_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    remote_execution_enabled: bool = False
    account_sync_enabled: bool = False
    crm_write_enabled: bool = False
    memory_write_authorized: bool = False
    automatic_memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    approval_grant_capture_enabled: bool = False
    action_execution_enabled: bool = False
    code_apply_execution_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_gate(self) -> "PrivateBetaReadinessGate":
        _safe_ref(self.contract_ref, "contract_ref")
        _safe_ref(self.evidence_packet_ref, "evidence_packet_ref")
        _safe_ref(self.readiness_window_ref, "readiness_window_ref")
        _safe_ref(self.product_loop_trial_script_ref, "product_loop_trial_script_ref")
        _safe_ref(
            self.private_operator_trial_ledger_ref,
            "private_operator_trial_ledger_ref",
        )
        _safe_refs(self.promotion_path_refs, "promotion_path_refs")
        _safe_text(self.status, "status")
        _safe_text(self.overall_gate_state, "overall_gate_state")
        _safe_text(self.full_strength_goal, "full_strength_goal")
        _safe_text(self.repo_safe_scope, "repo_safe_scope")
        _safe_text(self.blocked_authority_summary, "blocked_authority_summary")
        _safe_text(self.next_safe_action, "next_safe_action")
        if self.contract_ref != PRIVATE_BETA_READINESS_CONTRACT_REF:
            raise ValueError("private beta readiness gate ref drifted")
        if self.product_loop_trial_script_ref != (
            PRIVATE_PRODUCT_LOOP_TRIAL_SCRIPT_CONTRACT_REF
        ):
            raise ValueError("private beta readiness product loop trial ref drifted")
        if self.required_surfaces != PRIVATE_BETA_READINESS_REQUIRED_SURFACES:
            raise ValueError("private beta readiness required surfaces drifted")
        if set(self.acceptance_states) != set(PRIVATE_BETA_READINESS_ACCEPTANCE_STATES):
            raise ValueError("private beta readiness acceptance states drifted")
        if self.required_ref_fields != PRIVATE_BETA_READINESS_REQUIRED_REF_FIELDS:
            raise ValueError("private beta readiness ref fields drifted")
        criterion_surfaces = [criterion.surface for criterion in self.criteria]
        if criterion_surfaces != PRIVATE_BETA_READINESS_REQUIRED_SURFACES:
            raise ValueError("private beta readiness criteria missing surfaces")
        criterion_refs = [criterion.criterion_ref for criterion in self.criteria]
        if len(criterion_refs) != len(set(criterion_refs)):
            raise ValueError("private beta readiness criteria refs must be unique")
        binding_surfaces = [binding.get("surface") for binding in self.surface_bindings]
        if binding_surfaces != PRIVATE_BETA_READINESS_REQUIRED_SURFACES:
            raise ValueError("private beta readiness surface bindings drifted")
        if self.overall_gate_state == "pass":
            if self.missing_evidence_refs:
                raise ValueError("private beta readiness cannot pass with missing evidence")
            if any(criterion.gate_state != "pass" for criterion in self.criteria):
                raise ValueError("private beta readiness cannot pass with open criteria")
        for field_name in ["blocked_state_refs", "missing_evidence_refs"]:
            _safe_refs(getattr(self, field_name), field_name)
        for row in self.acceptance_state_definitions:
            for key, value in row.items():
                _safe_text(str(key), "acceptance_state_definition_key")
                _safe_text(str(value), "acceptance_state_definition_value")
        for binding in self.surface_bindings:
            for key, value in binding.items():
                _safe_text(str(key), "surface_binding_key")
                _safe_text(str(value), "surface_binding_value")
        missing_blocked = set(PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        )
        if missing_blocked:
            raise ValueError("private beta readiness gate missing blocked refs")
        required_true = {
            "local_private_only": self.local_private_only,
            "safe_refs_only": self.safe_refs_only,
            "review_required": self.review_required,
            "evidence_required": self.evidence_required,
            "redaction_required": self.redaction_required,
        }
        missing_true = [name for name, value in required_true.items() if not value]
        if missing_true:
            raise ValueError(f"private beta readiness gate disabled {missing_true[0]}")
        if self.private_beta_execution_authorized:
            raise ValueError("private beta execution is not authorized by this gate")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag) is not False:
                raise ValueError(f"{flag} is denied by private beta readiness")
            if self.authority_posture.get(flag) is not False:
                raise ValueError(f"authority posture enabled {flag}")
        for flag in [
            "local_private_only",
            "safe_refs_only",
            "review_required",
            "evidence_required",
            "redaction_required",
        ]:
            if self.authority_posture.get(flag) is not True:
                raise ValueError(f"authority posture missing {flag}")
        return self


def build_private_beta_readiness_gate() -> PrivateBetaReadinessGate:
    return PrivateBetaReadinessGate(
        acceptance_state_definitions=_acceptance_state_definitions(),
        criteria=_criteria(),
        surface_bindings=private_beta_readiness_surface_bindings(),
        authority_posture=private_beta_readiness_authority_posture(),
        missing_evidence_refs=[
            "missing-evidence-ref:private-beta:run-rehearsal-receipts",
            "missing-evidence-ref:private-beta:operator-review-notes",
            "missing-evidence-ref:private-beta:api-perimeter-hardening",
        ],
    )


def private_beta_readiness_authority_posture() -> dict[str, bool]:
    return {
        "local_private_only": True,
        "safe_refs_only": True,
        "review_required": True,
        "evidence_required": True,
        "redaction_required": True,
        "private_beta_execution_authorized": False,
        "public_beta_claim_enabled": False,
        "public_distribution_claim_enabled": False,
        "production_readiness_claim_enabled": False,
        "production_authority_enabled": False,
        "broad_autonomy_enabled": False,
        "connector_write_enabled": False,
        "provider_model_authority_allowed": False,
        "unrestricted_shell_enabled": False,
        "shell_subprocess_execution_enabled": False,
        "remote_execution_enabled": False,
        "account_sync_enabled": False,
        "crm_write_enabled": False,
        "memory_write_authorized": False,
        "automatic_memory_write_authorized": False,
        "context_injection_authorized": False,
        "approval_grant_capture_enabled": False,
        "action_execution_enabled": False,
        "code_apply_execution_enabled": False,
    }


def private_beta_readiness_surface_bindings() -> list[dict[str, str]]:
    return [
        {
            "surface": surface,
            "feed_status": _surface_state(surface),
            "feed_ref": f"private-beta-readiness:{_surface_slug(surface)}",
            "authority_boundary": (
                "Private beta readiness evidence is local safe-ref metadata only."
            ),
        }
        for surface in PRIVATE_BETA_READINESS_REQUIRED_SURFACES
    ]


def _criteria() -> list[PrivateBetaReadinessCriterion]:
    rows = [
        (
            "Start Here",
            "partial",
            "Start Here can guide one local governed loop with backend refs, while setup mutation and runtime control remain blocked.",
            [
                "contract-ref:start-here-local-loop:v1",
                "contract-ref:private-beta-readiness-gate:v1",
            ],
        ),
        (
            "Setup Assistant",
            "partial",
            "Setup Assistant can show local prerequisite and package-readiness posture, but install, launch, login-material capture, shell, and public distribution authority remain blocked.",
            [
                "contract-ref:macos-setup-assistant:local-readiness",
                "contract-ref:local-package-proof:macos-private",
            ],
        ),
        (
            "Today",
            "partial",
            "Today can show the product spine, blockers, follow-ups, and readiness refs, but the gate still needs rehearsal receipts.",
            [
                "contract-ref:today-product-spine:v1",
                "contract-ref:evidence-history-grammar:v1",
            ],
        ),
        (
            "Morning Briefing",
            "mock_only",
            "Morning Briefing has a storage-backed skeleton and source-readiness blockers, not live source reads.",
            ["contract-ref:morning-briefing-source-readiness-missing"],
        ),
        (
            "Action Inbox",
            "partial",
            "Action Inbox can review envelopes and memory-derived proposals, while execution and approval capture remain blocked.",
            [
                "contract-ref:plans-action-envelope:v1",
                "contract-ref:memory-to-loop-binding:v1",
            ],
        ),
        (
            "Proof Detail",
            "partial",
            "Proof Detail can inspect safe refs, receipts, evidence, approval posture, and blocked authority, but cannot grant approval or execute rollback.",
            [
                "contract-ref:control-center-proof-spine:v1",
                "contract-ref:dogfood-live-loop:acceptance",
            ],
        ),
        (
            "Memory Review",
            "partial",
            "Memory Review shows source, provenance, quality, decision, and loop refs without writing memory or injecting context.",
            [
                "contract-ref:memory-review-decision:v1",
                "contract-ref:business-memory-quality-controls:v1",
                "contract-ref:cross-surface-memory-intake:v1",
            ],
        ),
        (
            "Evidence Timeline",
            "partial",
            "Evidence Timeline reads as history for proposed, approved, happened, changed, undoable, stale, and blocked states.",
            ["contract-ref:evidence-history-grammar:v1"],
        ),
        (
            "Trust Authority Map",
            "partial",
            "Trust can explain enabled local read/proposal lanes, exact approval requirements, safe-disable posture, rollback posture, and blocked authority without granting authority.",
            [
                "contract-ref:trust-authority-map:v1",
                "contract-ref:usable-authority-tiers:v1",
            ],
        ),
        (
            "Chat/Plans Handoff",
            "partial",
            "Local Chat can produce runtime, auth, tool-denial, and handoff refs, but output is not authority.",
            [
                "contract-ref:chat-local-operator-surface:v1",
                "contract-ref:plans-action-envelope:v1",
            ],
        ),
        (
            "Governed Code",
            "partial",
            "Governed Code can propose repo-local safe diff refs with validation and rollback posture while apply stays blocked.",
            ["contract-ref:governed-code-workbench:v1"],
        ),
        (
            "CRM-Lite Follow-Ups",
            "blocked",
            "CRM-lite follow-ups can be represented as reviewed memory/action refs only; account sync and CRM writes remain blocked.",
            [
                "contract-ref:business-memory-quality-controls:v1",
                "contract-ref:memory-to-loop-binding:v1",
            ],
        ),
        (
            "Dogfood Live Loop",
            "partial",
            "Dogfood Live Loop can inspect one deterministic repo-local loop through safe refs; this gate cannot seed approvals, commit local tasks, or claim runtime authority.",
            [
                "contract-ref:dogfood-live-loop:acceptance",
                "contract-ref:local-task-create:exact-lane",
            ],
        ),
    ]
    criteria: list[PrivateBetaReadinessCriterion] = []
    for surface, state, summary, contract_refs in rows:
        surface_slug = _surface_slug(surface)
        criteria.append(
            PrivateBetaReadinessCriterion(
                criterion_ref=f"private-beta-readiness-criterion:{surface_slug}",
                surface=surface,  # type: ignore[arg-type]
                gate_state=state,  # type: ignore[arg-type]
                safe_summary=summary,
                evidence_refs=[f"evidence-ref:private-beta:{surface_slug}"],
                required_contract_refs=contract_refs,
                acceptance_refs=[
                    f"acceptance-ref:private-beta:{surface_slug}:{state}"
                ],
                missing_evidence_refs=[
                    f"missing-evidence-ref:private-beta:{surface_slug}:rehearsal"
                ],
                blocked_state_refs=list(PRIVATE_BETA_READINESS_REQUIRED_BLOCKED_REFS),
                next_safe_action=(
                    "Collect local operator review evidence and keep blocked "
                    "authority refs visible before any readiness claim."
                ),
            )
        )
    return criteria


def _acceptance_state_definitions() -> list[dict[str, str | bool]]:
    return [
        {
            "state": "pass",
            "terminal": True,
            "definition": "Acceptance evidence is present and no blocker remains.",
        },
        {
            "state": "fail",
            "terminal": True,
            "definition": "Evidence contradicts the acceptance criterion.",
        },
        {
            "state": "skipped",
            "terminal": False,
            "definition": "Criterion was intentionally skipped with a safe reason.",
        },
        {
            "state": "blocked",
            "terminal": False,
            "definition": "Required evidence or authority boundary is missing.",
        },
        {
            "state": "partial",
            "terminal": False,
            "definition": "Some evidence exists, but beta-test proof is incomplete.",
        },
        {
            "state": "mock_only",
            "terminal": False,
            "definition": "Only mock or skeleton evidence exists.",
        },
        {
            "state": "accepted_failure",
            "terminal": True,
            "definition": "Known failure is accepted only with documented risk refs.",
        },
    ]


def _surface_state(surface: PrivateBetaReadinessSurface) -> str:
    state_by_surface = {
        "Start Here": "partial_backend_loop_guide_runtime_blocked",
        "Setup Assistant": "partial_local_setup_readiness_mutation_blocked",
        "Today": "partial_spine_evidence_needs_rehearsal",
        "Morning Briefing": "mock_only_source_reads_blocked",
        "Action Inbox": "partial_reviewable_envelopes_execution_blocked",
        "Proof Detail": "partial_safe_ref_proof_spine_execution_blocked",
        "Memory Review": "partial_review_only_memory_controls",
        "Evidence Timeline": "partial_history_grammar_present",
        "Trust Authority Map": "partial_authority_map_grants_blocked",
        "Chat/Plans Handoff": "partial_local_operator_handoff_refs",
        "Governed Code": "partial_repo_local_proposal_refs_apply_blocked",
        "CRM-Lite Follow-Ups": "blocked_no_crm_write_or_account_sync",
        "Dogfood Live Loop": "partial_repo_local_dogfood_loop_public_beta_blocked",
    }
    return state_by_surface[surface]


def _surface_slug(surface: str) -> str:
    return surface.lower().replace("/", "-").replace(" ", "-")


def _safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _safe_refs(values: list[str], field_name: str) -> None:
    for value in values:
        _safe_ref(value, field_name)


def _safe_text(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    lowered = value.lower()
    for fragment in _UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains unsafe private beta text")
