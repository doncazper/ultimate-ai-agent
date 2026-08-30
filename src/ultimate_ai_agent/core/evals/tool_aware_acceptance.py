from __future__ import annotations

import hashlib
import re
from enum import Enum
from typing import Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.evals.tool_aware_baseline import (
    CandidateLock,
    canonical_digest,
)
from ultimate_ai_agent.core.execution.validation import validate_execution_ref


TAW08_CONTRACT_REF = "contract-ref:taw08:founder-private-acceptance:v1"
TAW08_EVALUATOR_REF = "evaluator-ref:taw08:deterministic-acceptance:v1"
TAW08_MAX_EVIDENCE_DELTA_ENTRIES = 32
TAW08_MAX_EVIDENCE_DELTA_ARTIFACT_BYTES = 4 * 1024 * 1024
TAW08_FOUNDER_EVIDENCE_MISSING_REFS = (
    "evidence-missing-ref:taw08:end-to-end-journey-receipt",
    "evidence-missing-ref:taw08:exact-head-foundation-receipt",
    "evidence-missing-ref:taw08:founder-acceptance-decision",
    "evidence-missing-ref:taw08:live-model-hardware-measurements",
    "evidence-missing-ref:taw08:response-scoring",
    "evidence-missing-ref:taw08:routing-confidence-bounds",
    "evidence-missing-ref:taw08:stale-cache-recovery",
)
TAW08_POSTMERGE_EVIDENCE_MISSING_REF = (
    "evidence-missing-ref:taw08:postmerge-foundation-receipt"
)
TAW08_INDEPENDENT_PROMOTION_BLOCKER_REFS = (
    "blocker-ref:taw00:external-baseline-acceptance-authority-missing",
    "blocker-ref:taw00:independent-custodian-identity-authority-missing",
    "blocker-ref:taw00:independent-evaluator-identity-authority-missing",
    "blocker-ref:taw08:sealed-holdout-evidence-missing",
)
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_GIT_RE = re.compile(r"^git-sha:[0-9a-f]{40}$")


class EvidenceOnlyArtifactKind(str, Enum):
    acceptance_report = "acceptance_report"
    immutable_evidence_refs = "immutable_evidence_refs"
    claim_reconciliation = "claim_reconciliation"


class TAW08AcceptanceStatus(str, Enum):
    blocked_missing_founder_evidence = "blocked_missing_founder_evidence"
    founder_private_accepted_postmerge_pending = (
        "founder_private_accepted_postmerge_pending"
    )
    founder_private_accepted_promotion_blocked = (
        "founder_private_accepted_promotion_blocked"
    )
    failed = "failed"


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _validate_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _validate_digest(value: str, field_name: str) -> None:
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be an exact sha256 digest")


def _validate_git_ref(value: str, field_name: str) -> None:
    if not _GIT_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be an exact Git revision")


def _validate_sorted_refs(values: tuple[str, ...], field_name: str) -> None:
    if values != tuple(sorted(values)) or len(values) != len(set(values)):
        raise ValueError(f"{field_name} must be unique and sorted")
    for value in values:
        _validate_ref(value, field_name)


class EvidenceOnlyDeltaEntry(_FrozenModel):
    path_ref: str
    artifact_kind: EvidenceOnlyArtifactKind
    content_digest_ref: str

    @model_validator(mode="after")
    def validate_entry(self) -> "EvidenceOnlyDeltaEntry":
        _validate_ref(self.path_ref, "path_ref")
        _validate_digest(self.content_digest_ref, "content_digest_ref")
        return self


class EvidenceOnlyDeltaManifest(_FrozenModel):
    schema_version: Literal["uaa-taw08-evidence-only-delta.v1"] = (
        "uaa-taw08-evidence-only-delta.v1"
    )
    candidate_revision_ref: str
    candidate_manifest_digest_ref: str
    delta_revision_ref: str
    entries: tuple[EvidenceOnlyDeltaEntry, ...] = Field(
        ..., min_length=1, max_length=TAW08_MAX_EVIDENCE_DELTA_ENTRIES
    )
    manifest_digest_ref: str
    executable_changes_added: Literal[False] = False
    route_changes_added: Literal[False] = False
    prompt_changes_added: Literal[False] = False
    policy_changes_added: Literal[False] = False
    configuration_changes_added: Literal[False] = False
    dependency_changes_added: Literal[False] = False
    evaluator_changes_added: Literal[False] = False
    threshold_changes_added: Literal[False] = False
    corpus_or_holdout_changes_added: Literal[False] = False

    @model_validator(mode="after")
    def validate_manifest(self) -> "EvidenceOnlyDeltaManifest":
        _validate_git_ref(self.candidate_revision_ref, "candidate_revision_ref")
        _validate_git_ref(self.delta_revision_ref, "delta_revision_ref")
        _validate_digest(
            self.candidate_manifest_digest_ref, "candidate_manifest_digest_ref"
        )
        path_refs = tuple(item.path_ref for item in self.entries)
        if path_refs != tuple(sorted(path_refs)) or len(path_refs) != len(
            set(path_refs)
        ):
            raise ValueError("evidence-only delta entries must be unique and sorted")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"manifest_digest_ref"})
        )
        if self.manifest_digest_ref != expected:
            raise ValueError("evidence-only delta manifest digest binding drift")
        return self


class FoundationGateReceipt(_FrozenModel):
    schema_version: Literal["uaa-taw08-foundation-receipt.v1"] = (
        "uaa-taw08-foundation-receipt.v1"
    )
    stage: Literal["exact_head", "postmerge"]
    revision_ref: str
    report_digest_ref: str
    report_ref: str
    command_mode: Literal["report-only"] = "report-only"
    passed: Literal[True] = True
    redacted: Literal[True] = True
    raw_content_persisted: Literal[False] = False
    receipt_digest_ref: str

    @model_validator(mode="after")
    def validate_receipt(self) -> "FoundationGateReceipt":
        _validate_git_ref(self.revision_ref, "revision_ref")
        _validate_digest(self.report_digest_ref, "report_digest_ref")
        _validate_ref(self.report_ref, "report_ref")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"receipt_digest_ref"})
        )
        if self.receipt_digest_ref != expected:
            raise ValueError("Foundation Gate receipt digest binding drift")
        return self


class FounderPrivateAcceptanceEvidence(_FrozenModel):
    schema_version: Literal["uaa-taw08-founder-acceptance-evidence.v1"] = (
        "uaa-taw08-founder-acceptance-evidence.v1"
    )
    candidate_revision_ref: str
    candidate_manifest_digest_ref: str
    stale_cache_recovery_receipt_ref: str
    routing_confidence_receipt_ref: str
    response_scoring_receipt_ref: str
    live_model_hardware_receipt_refs: tuple[str, ...] = Field(
        ..., min_length=1, max_length=32
    )
    end_to_end_journey_receipt_ref: str
    founder_decision_ref: str
    exact_head_foundation_receipt: FoundationGateReceipt
    evidence_digest_ref: str
    raw_content_persisted: Literal[False] = False
    runtime_model_calls_added: Literal[False] = False
    provider_calls_added: Literal[False] = False
    execution_authority_added: Literal[False] = False

    @model_validator(mode="after")
    def validate_evidence(self) -> "FounderPrivateAcceptanceEvidence":
        _validate_git_ref(self.candidate_revision_ref, "candidate_revision_ref")
        _validate_digest(
            self.candidate_manifest_digest_ref, "candidate_manifest_digest_ref"
        )
        for value, field_name in (
            (self.stale_cache_recovery_receipt_ref, "stale_cache_recovery_receipt_ref"),
            (self.routing_confidence_receipt_ref, "routing_confidence_receipt_ref"),
            (self.response_scoring_receipt_ref, "response_scoring_receipt_ref"),
            (self.end_to_end_journey_receipt_ref, "end_to_end_journey_receipt_ref"),
            (self.founder_decision_ref, "founder_decision_ref"),
        ):
            _validate_ref(value, field_name)
        _validate_sorted_refs(
            self.live_model_hardware_receipt_refs,
            "live_model_hardware_receipt_refs",
        )
        if (
            self.exact_head_foundation_receipt.stage != "exact_head"
            or self.exact_head_foundation_receipt.revision_ref
            != self.candidate_revision_ref
        ):
            raise ValueError(
                "exact-head Foundation receipt must bind the candidate revision"
            )
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"evidence_digest_ref"})
        )
        if self.evidence_digest_ref != expected:
            raise ValueError("founder acceptance evidence digest binding drift")
        return self


class TAW08AcceptanceReport(_FrozenModel):
    schema_version: Literal["uaa-taw08-acceptance-report.v1"] = (
        "uaa-taw08-acceptance-report.v1"
    )
    contract_ref: Literal["contract-ref:taw08:founder-private-acceptance:v1"] = (
        TAW08_CONTRACT_REF
    )
    evaluator_ref: Literal["evaluator-ref:taw08:deterministic-acceptance:v1"] = (
        TAW08_EVALUATOR_REF
    )
    status: TAW08AcceptanceStatus
    candidate_revision_ref: str
    candidate_manifest_digest_ref: str
    founder_evidence: FounderPrivateAcceptanceEvidence | None
    founder_evidence_digest_ref: str | None
    evidence_only_delta: EvidenceOnlyDeltaManifest | None
    evidence_only_delta_manifest_digest_ref: str | None
    postmerge_foundation_receipt: FoundationGateReceipt | None
    postmerge_foundation_receipt_digest_ref: str | None
    founder_private_accepted: bool
    founder_evidence_missing_refs: tuple[str, ...]
    failure_refs: tuple[str, ...]
    independent_promotion_blocker_refs: tuple[str, ...]
    independent_promotion_ready: Literal[False] = False
    sealed_holdout_evidence_verified: Literal[False] = False
    public_quality_claims_allowed: Literal[False] = False
    production_authority_added: Literal[False] = False
    runtime_model_calls_added: Literal[False] = False
    provider_calls_added: Literal[False] = False
    execution_authority_added: Literal[False] = False
    raw_content_persisted: Literal[False] = False
    report_fingerprint_ref: str

    @model_validator(mode="after")
    def validate_report(self) -> "TAW08AcceptanceReport":
        _validate_git_ref(self.candidate_revision_ref, "candidate_revision_ref")
        _validate_digest(
            self.candidate_manifest_digest_ref, "candidate_manifest_digest_ref"
        )
        for value, field_name in (
            (self.founder_evidence_digest_ref, "founder_evidence_digest_ref"),
            (
                self.evidence_only_delta_manifest_digest_ref,
                "evidence_only_delta_manifest_digest_ref",
            ),
            (
                self.postmerge_foundation_receipt_digest_ref,
                "postmerge_foundation_receipt_digest_ref",
            ),
        ):
            if value is not None:
                _validate_digest(value, field_name)
        expected_founder_digest = (
            self.founder_evidence.evidence_digest_ref
            if self.founder_evidence is not None
            else None
        )
        if self.founder_evidence_digest_ref != expected_founder_digest:
            raise ValueError("founder evidence digest must bind the embedded evidence")
        if self.founder_evidence is not None and (
            self.founder_evidence.candidate_revision_ref != self.candidate_revision_ref
            or self.founder_evidence.candidate_manifest_digest_ref
            != self.candidate_manifest_digest_ref
        ):
            raise ValueError("founder evidence must bind the report candidate")
        expected_delta_digest = (
            self.evidence_only_delta.manifest_digest_ref
            if self.evidence_only_delta is not None
            else None
        )
        if self.evidence_only_delta_manifest_digest_ref != expected_delta_digest:
            raise ValueError("delta digest must bind the embedded delta manifest")
        if self.evidence_only_delta is not None and (
            self.evidence_only_delta.candidate_revision_ref
            != self.candidate_revision_ref
            or self.evidence_only_delta.candidate_manifest_digest_ref
            != self.candidate_manifest_digest_ref
        ):
            raise ValueError("evidence-only delta must bind the report candidate")
        expected_postmerge_digest = (
            self.postmerge_foundation_receipt.receipt_digest_ref
            if self.postmerge_foundation_receipt is not None
            else None
        )
        if self.postmerge_foundation_receipt_digest_ref != expected_postmerge_digest:
            raise ValueError(
                "postmerge digest must bind the embedded Foundation receipt"
            )
        if self.postmerge_foundation_receipt is not None:
            if self.postmerge_foundation_receipt.stage != "postmerge":
                raise ValueError("postmerge Foundation receipt stage drift")
            if (
                self.evidence_only_delta is not None
                and self.postmerge_foundation_receipt.revision_ref
                != self.evidence_only_delta.delta_revision_ref
            ):
                raise ValueError("postmerge Foundation receipt revision drift")
        _validate_sorted_refs(
            self.founder_evidence_missing_refs, "founder_evidence_missing_refs"
        )
        _validate_sorted_refs(self.failure_refs, "failure_refs")
        if (
            self.independent_promotion_blocker_refs
            != TAW08_INDEPENDENT_PROMOTION_BLOCKER_REFS
        ):
            raise ValueError("independent promotion blocker census drift")
        if self.failure_refs:
            expected_status = TAW08AcceptanceStatus.failed
            expected_founder_accepted = False
        elif self.founder_evidence_digest_ref is None:
            expected_status = TAW08AcceptanceStatus.blocked_missing_founder_evidence
            expected_founder_accepted = False
        elif self.postmerge_foundation_receipt_digest_ref is None:
            expected_status = (
                TAW08AcceptanceStatus.founder_private_accepted_postmerge_pending
            )
            expected_founder_accepted = True
        else:
            expected_status = (
                TAW08AcceptanceStatus.founder_private_accepted_promotion_blocked
            )
            expected_founder_accepted = True
        if (
            self.status != expected_status
            or self.founder_private_accepted != expected_founder_accepted
        ):
            raise ValueError("TAW-08 acceptance status does not match bound evidence")
        expected_missing = (
            ()
            if self.founder_evidence_digest_ref is not None
            else TAW08_FOUNDER_EVIDENCE_MISSING_REFS
        )
        if self.postmerge_foundation_receipt_digest_ref is None:
            expected_missing = tuple(
                sorted((*expected_missing, TAW08_POSTMERGE_EVIDENCE_MISSING_REF))
            )
        if self.founder_evidence_missing_refs != expected_missing:
            raise ValueError("TAW-08 missing-evidence census drift")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"report_fingerprint_ref"})
        )
        expected_ref = f"taw08-acceptance-report-ref:{expected}"
        if self.report_fingerprint_ref != expected_ref:
            raise ValueError("TAW-08 acceptance report fingerprint binding drift")
        return self


def bind_evidence_only_delta(**values: object) -> EvidenceOnlyDeltaManifest:
    normalized = dict(values)
    entries = normalized.get("entries")
    if isinstance(entries, (list, tuple)):
        normalized["entries"] = tuple(
            item
            if isinstance(item, EvidenceOnlyDeltaEntry)
            else EvidenceOnlyDeltaEntry.model_validate(item)
            for item in entries
        )
    payload = EvidenceOnlyDeltaManifest.model_construct(
        **normalized,
        manifest_digest_ref="sha256:" + "0" * 64,
    ).model_dump(mode="json", exclude={"manifest_digest_ref"})
    return EvidenceOnlyDeltaManifest.model_validate(
        {**payload, "manifest_digest_ref": canonical_digest(payload)}
    )


def bind_foundation_gate_receipt(**values: object) -> FoundationGateReceipt:
    payload = FoundationGateReceipt.model_construct(
        **values,
        receipt_digest_ref="sha256:" + "0" * 64,
    ).model_dump(mode="json", exclude={"receipt_digest_ref"})
    return FoundationGateReceipt.model_validate(
        {**payload, "receipt_digest_ref": canonical_digest(payload)}
    )


def bind_founder_private_acceptance_evidence(
    **values: object,
) -> FounderPrivateAcceptanceEvidence:
    normalized = dict(values)
    receipt = normalized.get("exact_head_foundation_receipt")
    if isinstance(receipt, dict):
        normalized["exact_head_foundation_receipt"] = (
            FoundationGateReceipt.model_validate(receipt)
        )
    payload = FounderPrivateAcceptanceEvidence.model_construct(
        **normalized,
        evidence_digest_ref="sha256:" + "0" * 64,
    ).model_dump(mode="json", exclude={"evidence_digest_ref"})
    return FounderPrivateAcceptanceEvidence.model_validate(
        {**payload, "evidence_digest_ref": canonical_digest(payload)}
    )


def verify_evidence_only_delta(
    *,
    candidate_lock: CandidateLock,
    delta: EvidenceOnlyDeltaManifest,
    changed_content_by_path_ref: Mapping[str, bytes],
) -> tuple[str, ...]:
    failures: set[str] = set()
    if len(changed_content_by_path_ref) > TAW08_MAX_EVIDENCE_DELTA_ENTRIES:
        return ("failure-ref:taw08:evidence-delta-path-bound-exceeded",)
    allowed_refs = set(candidate_lock.evidence_only_delta_path_refs)
    candidate_refs = {item.path_ref for item in candidate_lock.entries}
    actual_refs = set(changed_content_by_path_ref)
    entry_by_ref = {item.path_ref: item for item in delta.entries}
    if (
        delta.candidate_revision_ref != candidate_lock.git_revision_ref
        or delta.candidate_manifest_digest_ref != candidate_lock.manifest_digest_ref
    ):
        failures.add("failure-ref:taw08:evidence-delta-candidate-binding-drift")
    if set(entry_by_ref) != actual_refs:
        failures.add("failure-ref:taw08:evidence-delta-path-census-drift")
    if actual_refs - allowed_refs:
        failures.add("failure-ref:taw08:evidence-delta-unapproved-path")
    if actual_refs & candidate_refs:
        failures.add("failure-ref:taw08:evidence-delta-acceptance-path-overlap")
    for path_ref, content in changed_content_by_path_ref.items():
        entry = entry_by_ref.get(path_ref)
        if entry is None:
            continue
        if not isinstance(content, bytes):
            failures.add("failure-ref:taw08:evidence-delta-content-shape-invalid")
            continue
        if len(content) > TAW08_MAX_EVIDENCE_DELTA_ARTIFACT_BYTES:
            failures.add("failure-ref:taw08:evidence-delta-content-bound-exceeded")
            continue
        digest = f"sha256:{hashlib.sha256(content).hexdigest()}"
        if entry.content_digest_ref != digest:
            failures.add("failure-ref:taw08:evidence-delta-content-drift")
    return tuple(sorted(failures))


def evaluate_taw08_acceptance(
    *,
    candidate_lock: CandidateLock,
    founder_evidence: FounderPrivateAcceptanceEvidence | None = None,
    evidence_only_delta: EvidenceOnlyDeltaManifest | None = None,
    postmerge_foundation_receipt: FoundationGateReceipt | None = None,
    failure_refs: tuple[str, ...] = (),
) -> TAW08AcceptanceReport:
    _validate_sorted_refs(failure_refs, "failure_refs")
    missing = list(TAW08_FOUNDER_EVIDENCE_MISSING_REFS)
    founder_accepted = founder_evidence is not None
    derived_failures = set(failure_refs)
    if founder_evidence is not None:
        missing.clear()
        if (
            founder_evidence.candidate_revision_ref != candidate_lock.git_revision_ref
            or founder_evidence.candidate_manifest_digest_ref
            != candidate_lock.manifest_digest_ref
        ):
            derived_failures.add(
                "failure-ref:taw08:founder-evidence-candidate-binding-drift"
            )
            founder_accepted = False
    if evidence_only_delta is not None and (
        evidence_only_delta.candidate_revision_ref != candidate_lock.git_revision_ref
        or evidence_only_delta.candidate_manifest_digest_ref
        != candidate_lock.manifest_digest_ref
    ):
        derived_failures.add("failure-ref:taw08:evidence-delta-candidate-binding-drift")
    if postmerge_foundation_receipt is None:
        missing.append(TAW08_POSTMERGE_EVIDENCE_MISSING_REF)
    elif postmerge_foundation_receipt.stage != "postmerge":
        derived_failures.add("failure-ref:taw08:postmerge-foundation-stage-drift")
    elif (
        evidence_only_delta is not None
        and postmerge_foundation_receipt.revision_ref
        != evidence_only_delta.delta_revision_ref
    ):
        derived_failures.add("failure-ref:taw08:postmerge-delta-revision-drift")
    if derived_failures:
        status = TAW08AcceptanceStatus.failed
        founder_accepted = False
    elif not founder_accepted:
        status = TAW08AcceptanceStatus.blocked_missing_founder_evidence
    elif postmerge_foundation_receipt is None:
        status = TAW08AcceptanceStatus.founder_private_accepted_postmerge_pending
    else:
        status = TAW08AcceptanceStatus.founder_private_accepted_promotion_blocked
    payload = {
        "schema_version": "uaa-taw08-acceptance-report.v1",
        "contract_ref": TAW08_CONTRACT_REF,
        "evaluator_ref": TAW08_EVALUATOR_REF,
        "status": status.value,
        "candidate_revision_ref": candidate_lock.git_revision_ref,
        "candidate_manifest_digest_ref": candidate_lock.manifest_digest_ref,
        "founder_evidence": (
            founder_evidence.model_dump(mode="json") if founder_evidence else None
        ),
        "founder_evidence_digest_ref": (
            founder_evidence.evidence_digest_ref if founder_evidence else None
        ),
        "evidence_only_delta": (
            evidence_only_delta.model_dump(mode="json") if evidence_only_delta else None
        ),
        "evidence_only_delta_manifest_digest_ref": (
            evidence_only_delta.manifest_digest_ref if evidence_only_delta else None
        ),
        "postmerge_foundation_receipt": (
            postmerge_foundation_receipt.model_dump(mode="json")
            if postmerge_foundation_receipt
            else None
        ),
        "postmerge_foundation_receipt_digest_ref": (
            postmerge_foundation_receipt.receipt_digest_ref
            if postmerge_foundation_receipt
            else None
        ),
        "founder_private_accepted": founder_accepted,
        "founder_evidence_missing_refs": tuple(sorted(missing)),
        "failure_refs": tuple(sorted(derived_failures)),
        "independent_promotion_blocker_refs": (
            TAW08_INDEPENDENT_PROMOTION_BLOCKER_REFS
        ),
        "independent_promotion_ready": False,
        "sealed_holdout_evidence_verified": False,
        "public_quality_claims_allowed": False,
        "production_authority_added": False,
        "runtime_model_calls_added": False,
        "provider_calls_added": False,
        "execution_authority_added": False,
        "raw_content_persisted": False,
    }
    return TAW08AcceptanceReport.model_validate(
        {
            **payload,
            "report_fingerprint_ref": (
                f"taw08-acceptance-report-ref:{canonical_digest(payload)}"
            ),
        }
    )
