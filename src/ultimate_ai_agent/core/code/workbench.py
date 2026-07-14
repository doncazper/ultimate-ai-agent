from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.capability_availability import (
    validate_capability_availability_safe_text,
)
from ultimate_ai_agent.core.control_center.fusion_routing import (
    CacheContextEconomics,
    DelegationProposalEnvelope,
    WorkClassification,
    WorkClassificationValue,
    build_cache_context_economics,
    build_delegation_proposal,
    build_work_classification,
)
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


GOVERNED_CODE_WORKBENCH_CONTRACT_REF = "contract-ref:governed-code-workbench:v1"
GOVERNED_CODE_PATCH_REVIEW_CONTRACT_REF = "contract-ref:governed-code-patch-review:v1"
GOVERNED_CODE_PATCH_REVIEW_SCHEMA_VERSION = "governed_code_patch_review.v1"
GOVERNED_CODE_WORKBENCH_REQUIRED_REF_FIELDS = [
    "proposal_ref",
    "repo_scope_ref",
    "safe_diff_summary_ref",
    "validation_plan_ref",
    "validation_result_refs",
    "approval_requirement_ref",
    "expected_apply_receipt_ref",
    "expected_rollback_receipt_ref",
    "evidence_refs",
    "idempotency_key_ref",
    "blocked_state_refs",
]
GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS = [
    "blocked-state:no-unapproved-mutation",
    "blocked-state:no-apply-execution",
    "blocked-state:no-approval-grant-capture",
    "blocked-state:no-unrestricted-shell",
    "blocked-state:no-shell-subprocess-execution",
    "blocked-state:no-remote-execution",
    "blocked-state:no-broad-coding-agent-autonomy",
    "blocked-state:no-provider-sdk-call",
    "blocked-state:no-web-fetch",
    "blocked-state:no-connector-write",
    "blocked-state:no-diff-body-storage",
    "blocked-state:no-production-authority",
]
SAFE_CODE_SUFFIX_CHARS = re.compile(r"[^a-z0-9_.@-]+")
UNSAFE_CODE_WORKBENCH_TEXT_FRAGMENTS = (
    "raw diff",
    "full diff",
    "unredacted diff",
    "raw patch",
    "provider payload",
    "api key",
    "authorization",
    "credential",
    "password",
)
GOVERNED_CODE_PATCH_MAX_UTF8_BYTES = 512_000
GOVERNED_CODE_PATCH_MAX_LINES = 20_000
GOVERNED_CODE_PATCH_MAX_LINE_BYTES = 16_384
GOVERNED_CODE_PATCH_MAX_TARGET_REFS = 64
_SHA256_HEX_RE = re.compile(r"^[a-f0-9]{64}$")
_IMMUTABLE_GIT_REVISION_REF_RE = re.compile(r"^git-commit-ref:sha1:[a-f0-9]{40}$")


class _FrozenWorkClassification(WorkClassification):
    reason_refs: tuple[str, ...] = Field(default_factory=tuple, min_length=1)
    blocked_authority_refs: tuple[str, ...] = Field(default_factory=tuple)
    source_refs: tuple[str, ...] = Field(default_factory=tuple, min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, min_length=1)

    model_config = ConfigDict(use_enum_values=True, extra="forbid", frozen=True)


class _FrozenCacheContextEconomics(CacheContextEconomics):
    cache_or_context_blocker_refs: tuple[str, ...] = Field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)

    model_config = ConfigDict(use_enum_values=True, extra="forbid", frozen=True)


class _FrozenDelegationProposalEnvelope(DelegationProposalEnvelope):
    main_owner_responsibility_refs: tuple[str, ...] = Field(
        default_factory=tuple,
        min_length=1,
    )
    delegated_work_refs: tuple[str, ...] = Field(default_factory=tuple)
    blocked_execution_refs: tuple[str, ...] = Field(
        default_factory=tuple,
        min_length=1,
    )
    expected_receipt_refs: tuple[str, ...] = Field(
        default_factory=tuple,
        min_length=1,
    )
    rollback_safe_disable_posture_refs: tuple[str, ...] = Field(
        default_factory=tuple,
        min_length=1,
    )
    work_classification: _FrozenWorkClassification

    model_config = ConfigDict(use_enum_values=True, extra="forbid", frozen=True)


class GovernedCodeWorkbenchProposal(BaseModel):
    contract_ref: str = GOVERNED_CODE_WORKBENCH_CONTRACT_REF
    proposal_ref: str = Field(..., min_length=1)
    repo_scope_ref: str = Field(..., min_length=1)
    safe_diff_summary_ref: str = Field(..., min_length=1)
    validation_plan_ref: str = Field(..., min_length=1)
    validation_result_refs: tuple[str, ...] = Field(
        default_factory=tuple,
        min_length=1,
    )
    approval_requirement_ref: str = Field(..., min_length=1)
    expected_apply_receipt_ref: str = Field(..., min_length=1)
    expected_rollback_receipt_ref: str = Field(..., min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple, min_length=1)
    idempotency_key_ref: str = Field(..., min_length=1)
    blocked_state_refs: tuple[str, ...] = Field(default_factory=tuple, min_length=1)
    work_classification: _FrozenWorkClassification
    delegation_proposal: _FrozenDelegationProposalEnvelope
    cache_context_economics: _FrozenCacheContextEconomics
    safe_summary: str = Field(..., min_length=1, max_length=500)
    validation_plan_summary: str = Field(..., min_length=1, max_length=500)
    side_effect_class: str = "local_dev_workspace_only"
    risk_class: str = "high"
    repo_local_scope_required: bool = True
    safe_diff_summary_only: bool = True
    validation_required_before_apply: bool = True
    approval_required_before_apply: bool = True
    atomic_apply_required: bool = True
    rollback_receipt_required: bool = True
    audit_required: bool = True
    redaction_required: bool = True
    apply_execution_enabled: bool = False
    approval_grant_capture_enabled: bool = False
    direct_file_write_enabled: bool = False
    unrestricted_shell_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    remote_execution_enabled: bool = False
    broad_coding_agent_autonomy_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    web_fetch_enabled: bool = False
    connector_write_enabled: bool = False
    diff_body_storage_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_proposal(self) -> "GovernedCodeWorkbenchProposal":
        if self.contract_ref != GOVERNED_CODE_WORKBENCH_CONTRACT_REF:
            raise ValueError("unexpected governed Code workbench contract ref")
        for field_name in [
            "contract_ref",
            "proposal_ref",
            "repo_scope_ref",
            "safe_diff_summary_ref",
            "validation_plan_ref",
            "approval_requirement_ref",
            "expected_apply_receipt_ref",
            "expected_rollback_receipt_ref",
            "idempotency_key_ref",
        ]:
            _validate_safe_durable_ref(getattr(self, field_name), field_name)
        for field_name in [
            "validation_result_refs",
            "evidence_refs",
            "blocked_state_refs",
        ]:
            for ref_value in getattr(self, field_name):
                _validate_safe_durable_ref(ref_value, field_name)
        for field_name in [
            "safe_summary",
            "validation_plan_summary",
            "side_effect_class",
            "risk_class",
        ]:
            validate_safe_task_text(getattr(self, field_name), field_name)
        missing_blockers = set(GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        )
        if missing_blockers:
            raise ValueError("governed Code workbench proposal missing blocked refs")
        if self.work_classification.execution_authorized:
            raise ValueError("work classification cannot authorize execution")
        if self.delegation_proposal.worker_execution_enabled:
            raise ValueError("delegation proposal cannot execute")
        if self.cache_context_economics.runtime_model_switch_performed:
            raise ValueError("cache/context economics cannot switch models")
        required_true_flags = {
            "repo_local_scope_required": self.repo_local_scope_required,
            "safe_diff_summary_only": self.safe_diff_summary_only,
            "validation_required_before_apply": self.validation_required_before_apply,
            "approval_required_before_apply": self.approval_required_before_apply,
            "atomic_apply_required": self.atomic_apply_required,
            "rollback_receipt_required": self.rollback_receipt_required,
            "audit_required": self.audit_required,
            "redaction_required": self.redaction_required,
        }
        missing_true = [
            name for name, value in required_true_flags.items() if not value
        ]
        if missing_true:
            raise ValueError(f"governed Code workbench disabled {missing_true[0]}")
        denied_flags = {
            "apply_execution_enabled": self.apply_execution_enabled,
            "approval_grant_capture_enabled": self.approval_grant_capture_enabled,
            "direct_file_write_enabled": self.direct_file_write_enabled,
            "unrestricted_shell_enabled": self.unrestricted_shell_enabled,
            "shell_subprocess_execution_enabled": self.shell_subprocess_execution_enabled,
            "remote_execution_enabled": self.remote_execution_enabled,
            "broad_coding_agent_autonomy_enabled": (
                self.broad_coding_agent_autonomy_enabled
            ),
            "provider_sdk_call_enabled": self.provider_sdk_call_enabled,
            "web_fetch_enabled": self.web_fetch_enabled,
            "connector_write_enabled": self.connector_write_enabled,
            "diff_body_storage_enabled": self.diff_body_storage_enabled,
            "production_authority_enabled": self.production_authority_enabled,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(f"governed Code workbench enabled {enabled[0]}")
        payload = self.model_dump(mode="json")
        _validate_no_denied_fragments(payload)
        validate_safe_task_payload(payload, "governed_code_workbench_proposal")
        return self


class GovernedCodePatchReview(BaseModel):
    schema_version: Literal["governed_code_patch_review.v1"] = (
        GOVERNED_CODE_PATCH_REVIEW_SCHEMA_VERSION
    )
    contract_ref: str = GOVERNED_CODE_PATCH_REVIEW_CONTRACT_REF
    review_ref: str = Field(..., min_length=1)
    proposal_ref: str = Field(..., min_length=1)
    patch_hash_ref: str = Field(..., min_length=1)
    target_fingerprint_ref: str = Field(..., min_length=1)
    base_revision_ref: str = Field(..., min_length=1)
    target_refs: tuple[str, ...] = Field(..., min_length=1, max_length=64)
    approval_scope_fingerprint_ref: str = Field(..., min_length=1)
    validation_plan_ref: str = Field(..., min_length=1)
    rollback_plan_ref: str = Field(..., min_length=1)
    idempotency_key_ref: str = Field(..., min_length=1)
    line_addition_count: int = Field(..., ge=0, le=1_000_000)
    line_deletion_count: int = Field(..., ge=0, le=1_000_000)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    exact_patch_hash_bound: bool = True
    exact_target_fingerprint_bound: bool = True
    exact_base_revision_bound: bool = True
    exact_approval_scope_required: bool = True
    authority_lease_required: bool = True
    validation_required_before_apply: bool = True
    rollback_required: bool = True
    receipt_required: bool = True
    patch_body_persisted: bool = False
    patch_apply_performed: bool = False
    approval_ref_grants_authority: bool = False
    model_output_grants_authority: bool = False

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_review(self) -> "GovernedCodePatchReview":
        if self.contract_ref != GOVERNED_CODE_PATCH_REVIEW_CONTRACT_REF:
            raise ValueError("governed Code patch review contract ref drift")
        for field_name in [
            "contract_ref",
            "review_ref",
            "proposal_ref",
            "patch_hash_ref",
            "target_fingerprint_ref",
            "base_revision_ref",
            "approval_scope_fingerprint_ref",
            "validation_plan_ref",
            "rollback_plan_ref",
            "idempotency_key_ref",
        ]:
            _validate_safe_durable_ref(getattr(self, field_name), field_name)
        for target_ref in self.target_refs:
            _validate_safe_durable_ref(target_ref, "target_ref")
        if self.target_refs != tuple(sorted(set(self.target_refs))):
            raise ValueError("governed Code patch review targets must be canonical")
        if _IMMUTABLE_GIT_REVISION_REF_RE.fullmatch(self.base_revision_ref) is None:
            raise ValueError(
                "governed Code patch review requires immutable base revision"
            )
        patch_digest = _require_sha256_ref(
            self.patch_hash_ref,
            "patch-hash-ref:sha256:",
            "patch hash",
        )
        target_digest = _target_fingerprint(self.target_refs)
        expected_target_ref = f"target-fingerprint-ref:sha256:{target_digest}"
        if self.target_fingerprint_ref != expected_target_ref:
            raise ValueError("governed Code patch target fingerprint drift")
        scope_digest = _approval_scope_fingerprint(
            proposal_ref=self.proposal_ref,
            patch_digest=patch_digest,
            target_digest=target_digest,
            base_revision_ref=self.base_revision_ref,
        )
        expected_scope_ref = f"approval-scope-fingerprint-ref:sha256:{scope_digest}"
        if self.approval_scope_fingerprint_ref != expected_scope_ref:
            raise ValueError("governed Code patch approval scope fingerprint drift")
        review_digest = _patch_review_fingerprint(
            proposal_ref=self.proposal_ref,
            patch_digest=patch_digest,
            target_digest=target_digest,
            base_revision_ref=self.base_revision_ref,
            scope_digest=scope_digest,
            line_addition_count=self.line_addition_count,
            line_deletion_count=self.line_deletion_count,
            safe_summary=self.safe_summary,
        )
        expected_refs = {
            "review_ref": f"code-patch-review-ref:sha256:{review_digest}",
            "validation_plan_ref": (
                f"validation-plan-ref:governed-code:sha256:{review_digest}"
            ),
            "rollback_plan_ref": (
                f"rollback-plan-ref:governed-code:sha256:{review_digest}"
            ),
            "idempotency_key_ref": (
                f"idempotency-ref:governed-code:sha256:{scope_digest}"
            ),
        }
        if any(getattr(self, name) != value for name, value in expected_refs.items()):
            raise ValueError("governed Code patch review fingerprint drift")
        required = [
            self.exact_patch_hash_bound,
            self.exact_target_fingerprint_bound,
            self.exact_base_revision_bound,
            self.exact_approval_scope_required,
            self.authority_lease_required,
            self.validation_required_before_apply,
            self.rollback_required,
            self.receipt_required,
        ]
        denied = [
            self.patch_body_persisted,
            self.patch_apply_performed,
            self.approval_ref_grants_authority,
            self.model_output_grants_authority,
        ]
        if not all(required) or any(denied):
            raise ValueError("governed Code patch review authority drift")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        payload = self.model_dump(mode="json")
        _validate_no_denied_fragments(payload)
        validate_safe_task_payload(payload, "governed_code_patch_review")
        return self


def build_governed_code_patch_review(
    *,
    patch_body: str,
    target_refs: list[str],
    proposal_ref: str = "code-proposal:governed-workbench",
    base_revision_ref: str | None = None,
) -> GovernedCodePatchReview:
    if len(patch_body) > GOVERNED_CODE_PATCH_MAX_UTF8_BYTES:
        raise ValueError("governed Code patch review exceeds byte limit")
    patch_bytes = patch_body.encode("utf-8")
    if len(patch_bytes) > GOVERNED_CODE_PATCH_MAX_UTF8_BYTES:
        raise ValueError("governed Code patch review exceeds byte limit")
    patch_lines = patch_bytes.splitlines()
    if len(patch_lines) > GOVERNED_CODE_PATCH_MAX_LINES:
        raise ValueError("governed Code patch review exceeds line limit")
    if any(len(line) > GOVERNED_CODE_PATCH_MAX_LINE_BYTES for line in patch_lines):
        raise ValueError("governed Code patch review exceeds per-line byte limit")
    if len(target_refs) > GOVERNED_CODE_PATCH_MAX_TARGET_REFS:
        raise ValueError("governed Code patch review exceeds target limit")
    if not patch_body.strip():
        raise ValueError("governed Code patch review requires patch content")
    if not target_refs:
        raise ValueError("governed Code patch review requires target refs")
    if len(target_refs) != len(set(target_refs)):
        raise ValueError("governed Code patch review requires unique target refs")
    if any(
        fragment in patch_body.lower()
        for fragment in UNSAFE_CODE_WORKBENCH_TEXT_FRAGMENTS
    ):
        raise ValueError("governed Code patch review contains denied content")
    if contains_secret_like(patch_body) or contains_obvious_secret(patch_body):
        raise ValueError("governed Code patch review rejected secret-like content")
    if base_revision_ref is None:
        raise ValueError("governed Code patch review requires immutable base revision")
    if _IMMUTABLE_GIT_REVISION_REF_RE.fullmatch(base_revision_ref) is None:
        raise ValueError("governed Code patch review requires immutable base revision")
    for target_ref in target_refs:
        _validate_safe_durable_ref(target_ref, "target_ref")
    _validate_safe_durable_ref(proposal_ref, "proposal_ref")
    _validate_safe_durable_ref(base_revision_ref, "base_revision_ref")
    canonical_targets = sorted(target_refs)
    patch_digest = hashlib.sha256(patch_bytes).hexdigest()
    target_digest = _target_fingerprint(canonical_targets)
    scope_digest = _approval_scope_fingerprint(
        proposal_ref=proposal_ref,
        patch_digest=patch_digest,
        target_digest=target_digest,
        base_revision_ref=base_revision_ref,
    )
    additions = sum(
        1
        for line in patch_lines
        if line.startswith(b"+") and not line.startswith(b"+++")
    )
    deletions = sum(
        1
        for line in patch_lines
        if line.startswith(b"-") and not line.startswith(b"---")
    )
    safe_summary = (
        "Exact patch hash, targets, base revision, approval scope, validation, "
        "rollback, and receipt requirements are bound for operator review. "
        "No patch was applied and no patch body was persisted."
    )
    review_digest = _patch_review_fingerprint(
        proposal_ref=proposal_ref,
        patch_digest=patch_digest,
        target_digest=target_digest,
        base_revision_ref=base_revision_ref,
        scope_digest=scope_digest,
        line_addition_count=additions,
        line_deletion_count=deletions,
        safe_summary=safe_summary,
    )
    return GovernedCodePatchReview(
        review_ref=f"code-patch-review-ref:sha256:{review_digest}",
        proposal_ref=proposal_ref,
        patch_hash_ref=f"patch-hash-ref:sha256:{patch_digest}",
        target_fingerprint_ref=f"target-fingerprint-ref:sha256:{target_digest}",
        base_revision_ref=base_revision_ref,
        target_refs=tuple(canonical_targets),
        approval_scope_fingerprint_ref=f"approval-scope-fingerprint-ref:sha256:{scope_digest}",
        validation_plan_ref=(
            f"validation-plan-ref:governed-code:sha256:{review_digest}"
        ),
        rollback_plan_ref=(f"rollback-plan-ref:governed-code:sha256:{review_digest}"),
        idempotency_key_ref=(f"idempotency-ref:governed-code:sha256:{scope_digest}"),
        line_addition_count=additions,
        line_deletion_count=deletions,
        safe_summary=safe_summary,
    )


def _target_fingerprint(target_refs: list[str]) -> str:
    payload = json.dumps(target_refs, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_safe_durable_ref(value: str, field_name: str) -> str:
    validate_task_ref(value, field_name)
    try:
        return validate_capability_availability_safe_text(value, field_name)
    except ValueError as exc:
        raise ValueError(f"governed Code patch {field_name} ref is unsafe") from exc


def _approval_scope_fingerprint(
    *,
    proposal_ref: str,
    patch_digest: str,
    target_digest: str,
    base_revision_ref: str,
) -> str:
    payload = json.dumps(
        {
            "base_revision_ref": base_revision_ref,
            "patch_digest": patch_digest,
            "proposal_ref": proposal_ref,
            "target_digest": target_digest,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _patch_review_fingerprint(
    *,
    proposal_ref: str,
    patch_digest: str,
    target_digest: str,
    base_revision_ref: str,
    scope_digest: str,
    line_addition_count: int,
    line_deletion_count: int,
    safe_summary: str,
) -> str:
    payload = json.dumps(
        {
            "base_revision_ref": base_revision_ref,
            "contract_ref": GOVERNED_CODE_PATCH_REVIEW_CONTRACT_REF,
            "line_addition_count": line_addition_count,
            "line_deletion_count": line_deletion_count,
            "patch_digest": patch_digest,
            "proposal_ref": proposal_ref,
            "scope_digest": scope_digest,
            "schema_version": GOVERNED_CODE_PATCH_REVIEW_SCHEMA_VERSION,
            "safe_summary": safe_summary,
            "target_digest": target_digest,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _require_sha256_ref(value: str, prefix: str, field_name: str) -> str:
    if not value.startswith(prefix):
        raise ValueError(f"governed Code patch {field_name} ref format invalid")
    digest = value[len(prefix) :]
    if _SHA256_HEX_RE.fullmatch(digest) is None:
        raise ValueError(f"governed Code patch {field_name} digest invalid")
    return digest


def build_governed_code_workbench_proposal(
    *,
    proposal_ref: str = "code-proposal:founder-loop-safe-diff",
    safe_summary: str = (
        "Governed Code proposal records repo-local scope, safe diff summary, "
        "validation plan, approval requirement, expected apply receipt, and "
        "rollback receipt refs; apply remains blocked."
    ),
    validation_plan_summary: str = (
        "Run focused tests and verifiers before any exact approval-bound apply."
    ),
    validation_result_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
) -> GovernedCodeWorkbenchProposal:
    suffix = _safe_suffix(proposal_ref)
    work_classification = build_work_classification(
        WorkClassificationValue.validation,
        suffix_ref=proposal_ref,
        source_ref=proposal_ref,
        evidence_ref=(evidence_refs or ["evidence-ref:governed-code:today"])[0],
        reason_ref=f"classification-reason-ref:governed-code:{suffix}",
    )
    frozen_work_classification = _FrozenWorkClassification.model_validate(
        work_classification.model_dump(mode="python")
    )
    delegation_proposal = build_delegation_proposal(
        work_classification=work_classification,
        suffix_ref=proposal_ref,
    )
    frozen_delegation_proposal = _FrozenDelegationProposalEnvelope.model_validate(
        delegation_proposal.model_dump(mode="python")
    )
    cache_context_economics = build_cache_context_economics(
        suffix_ref=proposal_ref,
        blocker_refs=["blocked-state:governed-code-no-runtime-model-switch"],
    )
    return GovernedCodeWorkbenchProposal(
        proposal_ref=proposal_ref,
        repo_scope_ref=f"repo-scope:governed-code:{suffix}",
        safe_diff_summary_ref=f"diff-summary-ref:governed-code:{suffix}",
        validation_plan_ref=f"validation-plan-ref:governed-code:{suffix}",
        validation_result_refs=validation_result_refs
        or ["validation-result-ref:governed-code:not-run"],
        approval_requirement_ref=f"approval-requirement:governed-code:{suffix}",
        expected_apply_receipt_ref=f"receipt-plan:governed-code-apply:{suffix}",
        expected_rollback_receipt_ref=(f"rollback-receipt-plan:governed-code:{suffix}"),
        evidence_refs=evidence_refs or ["evidence-ref:governed-code:today"],
        idempotency_key_ref=f"idempotency-ref:governed-code:{suffix}",
        blocked_state_refs=list(GOVERNED_CODE_WORKBENCH_REQUIRED_BLOCKED_REFS),
        work_classification=frozen_work_classification,
        delegation_proposal=frozen_delegation_proposal,
        cache_context_economics=_FrozenCacheContextEconomics.model_validate(
            cache_context_economics.model_dump(mode="python")
        ),
        safe_summary=safe_summary,
        validation_plan_summary=validation_plan_summary,
    )


def governed_code_workbench_authority_posture() -> dict[str, bool]:
    return {
        "safe_refs_only": True,
        "repo_local_scope_required": True,
        "safe_diff_summary_only": True,
        "validation_required_before_apply": True,
        "approval_required_before_apply": True,
        "atomic_apply_required": True,
        "rollback_receipt_required": True,
        "audit_required": True,
        "redaction_required": True,
        "apply_execution_enabled": False,
        "approval_grant_capture_enabled": False,
        "direct_file_write_enabled": False,
        "unrestricted_shell_enabled": False,
        "shell_subprocess_execution_enabled": False,
        "remote_execution_enabled": False,
        "broad_coding_agent_autonomy_enabled": False,
        "provider_sdk_call_enabled": False,
        "web_fetch_enabled": False,
        "connector_write_enabled": False,
        "diff_body_storage_enabled": False,
        "production_authority_enabled": False,
    }


def governed_code_workbench_surface_bindings() -> list[dict[str, str]]:
    return [
        {
            "surface": "Today",
            "feed_status": "implemented_governed_code_proposal_refs",
            "feed_ref": GOVERNED_CODE_WORKBENCH_CONTRACT_REF,
            "authority_boundary": "Code state is safe proposal metadata only.",
        },
        {
            "surface": "Code",
            "feed_status": "repo_local_safe_diff_summary_contract",
            "feed_ref": "code-proposal:governed-workbench",
            "authority_boundary": "Code proposals do not apply mutations.",
        },
        {
            "surface": "Actions",
            "feed_status": "approval_bound_apply_receipt_refs_only",
            "feed_ref": "receipt-plan:governed-code-apply",
            "authority_boundary": "Apply receipts are expected refs until scoped.",
        },
        {
            "surface": "Evidence",
            "feed_status": "validation_and_rollback_receipt_refs",
            "feed_ref": "evidence-ref:governed-code",
            "authority_boundary": "Evidence records proposal posture, not file changes.",
        },
        {
            "surface": "Memory",
            "feed_status": "cross_surface_memory_intake_proposal_refs_only",
            "feed_ref": "memory-intake-proposal:local-coding",
            "authority_boundary": (
                "Code can feed reviewed memory intake candidates only; memory "
                "writes and context injection remain blocked."
            ),
        },
    ]


def _safe_suffix(value: str) -> str:
    lowered = value.strip().lower().replace(":", "-")
    suffix = SAFE_CODE_SUFFIX_CHARS.sub("-", lowered).strip("-")
    return suffix or "missing"


def _validate_no_denied_fragments(payload: Any) -> None:
    if isinstance(payload, str):
        lowered = payload.lower()
        for fragment in UNSAFE_CODE_WORKBENCH_TEXT_FRAGMENTS:
            if fragment in lowered:
                raise ValueError("governed Code workbench contains denied content")
        return
    if isinstance(payload, dict):
        for value in payload.values():
            _validate_no_denied_fragments(value)
        return
    if isinstance(payload, list):
        for value in payload:
            _validate_no_denied_fragments(value)
