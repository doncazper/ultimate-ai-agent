from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import validate_execution_ref


CAPABILITY_EVALUATION_LAB_SCHEMA_VERSION = "uaa-capability-evaluation-lab.v1"
CAPABILITY_EVALUATION_LAB_CONTRACT_REF = "contract-ref:capability-evaluation-lab:v1"
CAPABILITY_EVALUATION_LAB_SUBJECT_REFS = (
    "subject-ref:uaa-native",
    "subject-ref:hermes",
    "subject-ref:openclaw",
    "subject-ref:goatcitadel",
)

_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_EXACT_REVISION_RE = re.compile(
    r"^(?:git-sha:[0-9a-f]{40}|"
    r"source-revision-ref:[a-z0-9][a-z0-9_.:-]*:sha256:[0-9a-f]{64})$"
)


class CapabilityLabExpectedStatus(str, Enum):
    passed = "passed"


class CapabilityLabObservedStatus(str, Enum):
    passed = "passed"
    failed = "failed"
    unknown = "unknown"


class CapabilityLabFailureAttribution(str, Enum):
    none = "none"
    subject_regression = "subject_regression"
    verifier_failure = "verifier_failure"
    evaluator_environment = "evaluator_environment"
    evidence_unavailable = "evidence_unavailable"
    timeout = "timeout"
    unknown = "unknown"


class CapabilityLabGateStatus(str, Enum):
    passed = "passed"
    failed = "failed"


class _FrozenLabModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _validate_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _validate_refs(values: tuple[str, ...], field_name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} contains duplicate refs")
    for value in values:
        _validate_ref(value, field_name)


def _validate_digest(value: str, field_name: str) -> None:
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} requires an exact sha256 digest")


def _canonical_digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


class CapabilityEvaluationLabCase(_FrozenLabModel):
    schema_version: Literal["uaa-capability-evaluation-lab.v1"] = (
        CAPABILITY_EVALUATION_LAB_SCHEMA_VERSION
    )
    contract_ref: Literal["contract-ref:capability-evaluation-lab:v1"] = (
        CAPABILITY_EVALUATION_LAB_CONTRACT_REF
    )
    case_ref: str
    case_version: Literal["1"] = "1"
    subject_ref: Literal[
        "subject-ref:uaa-native",
        "subject-ref:hermes",
        "subject-ref:openclaw",
        "subject-ref:goatcitadel",
    ]
    claim_ref: str
    source_revision_binding: Literal["evaluator_revision", "pinned"]
    source_revision_ref: str | None = None
    source_evidence_digest_ref: str | None = None
    expected_status: CapabilityLabExpectedStatus
    verifier_ref: str
    evidence_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    deterministic_seed_ref: str
    bounded_variance: Literal[False] = False
    live_provider_benchmark_performed: Literal[False] = False
    raw_content_persisted: Literal[False] = False
    score_authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_case(self) -> "CapabilityEvaluationLabCase":
        for value, field_name in (
            (self.contract_ref, "contract_ref"),
            (self.case_ref, "case_ref"),
            (self.subject_ref, "subject_ref"),
            (self.claim_ref, "claim_ref"),
            (self.verifier_ref, "verifier_ref"),
            (self.deterministic_seed_ref, "deterministic_seed_ref"),
        ):
            _validate_ref(value, field_name)
        _validate_refs(self.evidence_refs, "evidence_refs")
        if self.source_revision_binding == "pinned":
            if self.source_revision_ref is None or not _EXACT_REVISION_RE.fullmatch(
                self.source_revision_ref
            ):
                raise ValueError("pinned case requires an exact source revision")
            if self.source_evidence_digest_ref is None:
                raise ValueError("pinned case requires an exact source evidence digest")
            _validate_digest(
                self.source_evidence_digest_ref,
                "source_evidence_digest_ref",
            )
        elif (
            self.source_revision_ref is not None
            or self.source_evidence_digest_ref is not None
        ):
            raise ValueError(
                "evaluator-bound case resolves source revision only at run time"
            )
        return self


class CapabilityEvaluationClaimContract(_FrozenLabModel):
    claim_ref: str
    subject_ref: Literal[
        "subject-ref:uaa-native",
        "subject-ref:hermes",
        "subject-ref:openclaw",
        "subject-ref:goatcitadel",
    ]
    required_case_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    score_authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_claim(self) -> "CapabilityEvaluationClaimContract":
        _validate_ref(self.claim_ref, "claim_ref")
        _validate_ref(self.subject_ref, "subject_ref")
        _validate_refs(self.required_case_refs, "required_case_refs")
        return self


class CapabilityEvaluationLabManifest(_FrozenLabModel):
    schema_version: Literal["uaa-capability-evaluation-lab.v1"] = (
        CAPABILITY_EVALUATION_LAB_SCHEMA_VERSION
    )
    contract_ref: Literal["contract-ref:capability-evaluation-lab:v1"] = (
        CAPABILITY_EVALUATION_LAB_CONTRACT_REF
    )
    manifest_ref: str
    manifest_version: Literal["1"] = "1"
    case_refs: tuple[str, ...] = Field(..., min_length=4, max_length=32)
    cases: tuple[CapabilityEvaluationLabCase, ...] = Field(
        ..., min_length=4, max_length=32
    )
    claims: tuple[CapabilityEvaluationClaimContract, ...] = Field(
        ..., min_length=4, max_length=16
    )
    deterministic_only: Literal[True] = True
    local_only: Literal[True] = True
    content_free: Literal[True] = True
    live_provider_benchmark_enabled: Literal[False] = False
    model_judgment_enabled: Literal[False] = False
    score_authority_enabled: Literal[False] = False
    authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_manifest(self) -> "CapabilityEvaluationLabManifest":
        _validate_ref(self.contract_ref, "contract_ref")
        _validate_ref(self.manifest_ref, "manifest_ref")
        _validate_refs(self.case_refs, "case_refs")
        cases_by_ref = {case.case_ref: case for case in self.cases}
        if len(cases_by_ref) != len(self.cases):
            raise ValueError("capability lab case refs must be unique")
        if tuple(cases_by_ref) != self.case_refs:
            raise ValueError("capability lab case order or coverage drift")
        if {case.subject_ref for case in self.cases} != set(
            CAPABILITY_EVALUATION_LAB_SUBJECT_REFS
        ):
            raise ValueError("capability lab must cover all declared subjects")
        claims_by_ref = {claim.claim_ref: claim for claim in self.claims}
        if len(claims_by_ref) != len(self.claims):
            raise ValueError("capability lab claim refs must be unique")
        covered_case_refs: set[str] = set()
        for claim in self.claims:
            if not set(claim.required_case_refs) <= set(self.case_refs):
                raise ValueError("claim requires an unknown evaluation case")
            for case_ref in claim.required_case_refs:
                case = cases_by_ref[case_ref]
                if case.claim_ref != claim.claim_ref:
                    raise ValueError("case claim binding drift")
                if case.subject_ref != claim.subject_ref:
                    raise ValueError("case subject binding drift")
            covered_case_refs.update(claim.required_case_refs)
        if covered_case_refs != set(self.case_refs):
            raise ValueError("every evaluation case must support a claim gate")
        return self


class CapabilityEvaluationCaseResult(_FrozenLabModel):
    case_ref: str
    subject_ref: str
    claim_ref: str
    source_revision_ref: str
    source_evidence_digest_ref: str
    observed_status: CapabilityLabObservedStatus
    failure_attribution: CapabilityLabFailureAttribution
    reason_ref: str
    evidence_digest_ref: str

    @model_validator(mode="after")
    def validate_result(self) -> "CapabilityEvaluationCaseResult":
        for value, field_name in (
            (self.case_ref, "case_ref"),
            (self.subject_ref, "subject_ref"),
            (self.claim_ref, "claim_ref"),
            (self.source_revision_ref, "source_revision_ref"),
            (self.reason_ref, "reason_ref"),
        ):
            _validate_ref(value, field_name)
        if not _EXACT_REVISION_RE.fullmatch(self.source_revision_ref):
            raise ValueError("result requires an exact source revision")
        _validate_digest(
            self.source_evidence_digest_ref,
            "source_evidence_digest_ref",
        )
        _validate_digest(self.evidence_digest_ref, "evidence_digest_ref")
        safe_outcome = self.observed_status == CapabilityLabObservedStatus.passed
        if safe_outcome != (
            self.failure_attribution == CapabilityLabFailureAttribution.none
        ):
            raise ValueError("failure attribution does not match observed status")
        return self


class CapabilityEvaluationClaimGate(_FrozenLabModel):
    claim_ref: str
    subject_ref: str
    required_case_refs: tuple[str, ...]
    status: CapabilityLabGateStatus
    evidence_digest_ref: str

    @model_validator(mode="after")
    def validate_gate(self) -> "CapabilityEvaluationClaimGate":
        _validate_ref(self.claim_ref, "claim_ref")
        _validate_ref(self.subject_ref, "subject_ref")
        _validate_refs(self.required_case_refs, "required_case_refs")
        _validate_digest(self.evidence_digest_ref, "evidence_digest_ref")
        return self


class CapabilityEvaluationRunReceipt(_FrozenLabModel):
    schema_version: Literal["uaa-capability-evaluation-lab.v1"] = (
        CAPABILITY_EVALUATION_LAB_SCHEMA_VERSION
    )
    contract_ref: Literal["contract-ref:capability-evaluation-lab:v1"] = (
        CAPABILITY_EVALUATION_LAB_CONTRACT_REF
    )
    run_ref: str
    manifest_ref: str
    manifest_digest_ref: str
    evaluator_revision_ref: str
    evaluator_source_digest_ref: str
    evaluator_environment_digest_ref: str
    case_count: int = Field(..., ge=4, le=32)
    results: tuple[CapabilityEvaluationCaseResult, ...]
    missing_case_refs: tuple[str, ...] = ()
    unexpected_case_refs: tuple[str, ...] = ()
    claim_gates: tuple[CapabilityEvaluationClaimGate, ...]
    status: CapabilityLabGateStatus
    evidence_digest_ref: str
    deterministic: Literal[True] = True
    bounded_variance_present: Literal[False] = False
    content_free: Literal[True] = True
    raw_content_persisted: Literal[False] = False
    live_provider_benchmark_performed: Literal[False] = False
    model_judgment_performed: Literal[False] = False
    score_authority_granted: Literal[False] = False
    authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_receipt(self) -> "CapabilityEvaluationRunReceipt":
        for value, field_name in (
            (self.contract_ref, "contract_ref"),
            (self.run_ref, "run_ref"),
            (self.manifest_ref, "manifest_ref"),
            (self.evaluator_revision_ref, "evaluator_revision_ref"),
        ):
            _validate_ref(value, field_name)
        if not re.fullmatch(r"git-sha:[0-9a-f]{40}", self.evaluator_revision_ref):
            raise ValueError("receipt requires an exact evaluator revision")
        for digest, field_name in (
            (self.manifest_digest_ref, "manifest_digest_ref"),
            (self.evaluator_source_digest_ref, "evaluator_source_digest_ref"),
            (
                self.evaluator_environment_digest_ref,
                "evaluator_environment_digest_ref",
            ),
            (self.evidence_digest_ref, "evidence_digest_ref"),
        ):
            _validate_digest(digest, field_name)
        _validate_refs(self.missing_case_refs, "missing_case_refs")
        _validate_refs(self.unexpected_case_refs, "unexpected_case_refs")
        if self.case_count != len(self.results) + len(self.missing_case_refs):
            raise ValueError("receipt denominator cannot omit missing cases")
        result_refs = [result.case_ref for result in self.results]
        if len(result_refs) != len(set(result_refs)):
            raise ValueError("receipt result refs must be unique")
        failed = bool(self.missing_case_refs or self.unexpected_case_refs) or any(
            gate.status == CapabilityLabGateStatus.failed for gate in self.claim_gates
        )
        if self.status != (
            CapabilityLabGateStatus.failed if failed else CapabilityLabGateStatus.passed
        ):
            raise ValueError("receipt status does not match regression gates")
        return self


def capability_evaluation_manifest_digest(
    manifest: CapabilityEvaluationLabManifest,
) -> str:
    return _canonical_digest(manifest.model_dump(mode="json"))


def capability_evaluation_case_evidence_digest(
    *,
    case: CapabilityEvaluationLabCase,
    evaluator_revision_ref: str,
    evaluator_source_digest_ref: str,
    evaluator_environment_digest_ref: str,
    source_revision_ref: str,
    source_evidence_digest_ref: str,
    observed_status: CapabilityLabObservedStatus,
    failure_attribution: CapabilityLabFailureAttribution,
    reason_ref: str,
) -> str:
    return _canonical_digest(
        {
            "case": case.model_dump(mode="json"),
            "evaluator_revision_ref": evaluator_revision_ref,
            "evaluator_source_digest_ref": evaluator_source_digest_ref,
            "evaluator_environment_digest_ref": evaluator_environment_digest_ref,
            "source_revision_ref": source_revision_ref,
            "source_evidence_digest_ref": source_evidence_digest_ref,
            "observed_status": observed_status.value,
            "failure_attribution": failure_attribution.value,
            "reason_ref": reason_ref,
        }
    )


def build_capability_evaluation_run_receipt(
    *,
    manifest: CapabilityEvaluationLabManifest,
    evaluator_revision_ref: str,
    evaluator_source_digest_ref: str,
    evaluator_environment_digest_ref: str,
    results: tuple[CapabilityEvaluationCaseResult, ...],
) -> CapabilityEvaluationRunReceipt:
    if not re.fullmatch(r"git-sha:[0-9a-f]{40}", evaluator_revision_ref):
        raise ValueError("exact evaluator revision is required")
    _validate_digest(evaluator_source_digest_ref, "evaluator_source_digest_ref")
    _validate_digest(
        evaluator_environment_digest_ref, "evaluator_environment_digest_ref"
    )
    result_by_ref: dict[str, CapabilityEvaluationCaseResult] = {}
    for result in results:
        if result.case_ref in result_by_ref:
            raise ValueError("duplicate capability evaluation result")
        result_by_ref[result.case_ref] = result
    case_by_ref = {case.case_ref: case for case in manifest.cases}
    missing = tuple(ref for ref in manifest.case_refs if ref not in result_by_ref)
    unexpected = tuple(sorted(set(result_by_ref) - set(manifest.case_refs)))
    ordered_results = tuple(
        result_by_ref[ref] for ref in manifest.case_refs if ref in result_by_ref
    )
    for result in ordered_results:
        case = case_by_ref[result.case_ref]
        if result.subject_ref != case.subject_ref or result.claim_ref != case.claim_ref:
            raise ValueError("result case binding drift")
        expected_revision = (
            evaluator_revision_ref
            if case.source_revision_binding == "evaluator_revision"
            else case.source_revision_ref
        )
        expected_digest = (
            evaluator_source_digest_ref
            if case.source_revision_binding == "evaluator_revision"
            else case.source_evidence_digest_ref
        )
        if (
            result.source_revision_ref != expected_revision
            or result.source_evidence_digest_ref != expected_digest
        ):
            raise ValueError("result source revision binding drift")
        expected_evidence_digest = capability_evaluation_case_evidence_digest(
            case=case,
            evaluator_revision_ref=evaluator_revision_ref,
            evaluator_source_digest_ref=evaluator_source_digest_ref,
            evaluator_environment_digest_ref=evaluator_environment_digest_ref,
            source_revision_ref=result.source_revision_ref,
            source_evidence_digest_ref=result.source_evidence_digest_ref,
            observed_status=result.observed_status,
            failure_attribution=result.failure_attribution,
            reason_ref=result.reason_ref,
        )
        if result.evidence_digest_ref != expected_evidence_digest:
            raise ValueError("result evidence digest binding drift")

    gates: list[CapabilityEvaluationClaimGate] = []
    for claim in manifest.claims:
        claim_results = [result_by_ref.get(ref) for ref in claim.required_case_refs]
        passed = all(
            result is not None
            and result.observed_status.value
            == case_by_ref[result.case_ref].expected_status.value
            for result in claim_results
        )
        gate_payload = {
            "claim_ref": claim.claim_ref,
            "subject_ref": claim.subject_ref,
            "required_case_refs": claim.required_case_refs,
            "result_evidence_refs": [
                result.evidence_digest_ref if result is not None else "missing"
                for result in claim_results
            ],
            "status": "passed" if passed else "failed",
        }
        gates.append(
            CapabilityEvaluationClaimGate(
                claim_ref=claim.claim_ref,
                subject_ref=claim.subject_ref,
                required_case_refs=claim.required_case_refs,
                status=(
                    CapabilityLabGateStatus.passed
                    if passed
                    else CapabilityLabGateStatus.failed
                ),
                evidence_digest_ref=_canonical_digest(gate_payload),
            )
        )
    failed = bool(missing or unexpected) or any(
        gate.status == CapabilityLabGateStatus.failed for gate in gates
    )
    manifest_digest = capability_evaluation_manifest_digest(manifest)
    receipt_payload = {
        "manifest_ref": manifest.manifest_ref,
        "manifest_digest_ref": manifest_digest,
        "evaluator_revision_ref": evaluator_revision_ref,
        "evaluator_source_digest_ref": evaluator_source_digest_ref,
        "evaluator_environment_digest_ref": evaluator_environment_digest_ref,
        "results": [result.model_dump(mode="json") for result in ordered_results],
        "missing_case_refs": missing,
        "unexpected_case_refs": unexpected,
        "claim_gates": [gate.model_dump(mode="json") for gate in gates],
        "status": "failed" if failed else "passed",
    }
    evidence_digest = _canonical_digest(receipt_payload)
    return CapabilityEvaluationRunReceipt(
        run_ref=f"evaluation-run-ref:capability-lab:{evidence_digest}",
        manifest_ref=manifest.manifest_ref,
        manifest_digest_ref=manifest_digest,
        evaluator_revision_ref=evaluator_revision_ref,
        evaluator_source_digest_ref=evaluator_source_digest_ref,
        evaluator_environment_digest_ref=evaluator_environment_digest_ref,
        case_count=len(manifest.case_refs),
        results=ordered_results,
        missing_case_refs=missing,
        unexpected_case_refs=unexpected,
        claim_gates=tuple(gates),
        status=(
            CapabilityLabGateStatus.failed if failed else CapabilityLabGateStatus.passed
        ),
        evidence_digest_ref=evidence_digest,
    )


__all__ = [
    "CAPABILITY_EVALUATION_LAB_CONTRACT_REF",
    "CAPABILITY_EVALUATION_LAB_SCHEMA_VERSION",
    "CAPABILITY_EVALUATION_LAB_SUBJECT_REFS",
    "CapabilityEvaluationCaseResult",
    "CapabilityEvaluationClaimContract",
    "CapabilityEvaluationClaimGate",
    "CapabilityEvaluationLabCase",
    "CapabilityEvaluationLabManifest",
    "CapabilityEvaluationRunReceipt",
    "CapabilityLabExpectedStatus",
    "CapabilityLabFailureAttribution",
    "CapabilityLabGateStatus",
    "CapabilityLabObservedStatus",
    "build_capability_evaluation_run_receipt",
    "capability_evaluation_case_evidence_digest",
    "capability_evaluation_manifest_digest",
]
