#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verification.ci_command_manifest import (  # noqa: E402
    CI_JOB_GRAPH,
    VERIFICATION_DAG,
    build_plan,
)
from scripts.verification.verification_contracts import (  # noqa: E402
    VerificationPlan,
    VerificationReceipt,
    VerificationRunManifest,
    VerificationTerminalStatus,
)
from scripts.verification.verification_github_transport import (  # noqa: E402
    VerificationGithubJobOutputEnvelope,
    VerificationGithubTransportError,
    MAX_ENCODED_CHARS,
    build_github_job_output_envelope,
    decode_github_job_output,
    encode_github_job_output,
    validate_github_job_output_against_plan,
)
from scripts.verification.verification_run_aggregator import (  # noqa: E402
    aggregate_verification_run,
)


SCHEMA_VERSION = "uaa_foundation_prerequisite_manifest.v1"
CONSTRUCTION_POSTURE = "repository_constructed_non_authoritative"
REDACTION_STATUS = "content_free_refs_hashes_counts_and_unit_bindings_only"
CONTENT_REF_PREFIX = "foundation-prerequisite:"
MAX_MANIFEST_BYTES = 64 * 1024
MAX_EVIDENCE_BYTES = 2 * 1024 * 1024
MAX_INTEGER = (1 << 63) - 1
MAX_GITHUB_OUTPUT_BYTES = 1024 * 1024
OWNER_FILE_MODE = 0o600

PRE_PYTEST_SOURCE_UNIT_REFS = (
    "manifest-attestation",
    "lint",
    "affected-preflight",
    "release-lane-docs",
    "release-lane-openapi",
    "release-lane-api-safety",
    "release-lane-security-redaction",
    "release-lane-product-truth",
    "release-lane-local-model-e2e",
    "release-lane-durability",
)
PYTEST_AGGREGATE_SOURCE_UNIT_REFS = (
    *PRE_PYTEST_SOURCE_UNIT_REFS,
    "pytest-shards",
)
PREREQUISITE_SOURCE_UNIT_REFS = (
    *PYTEST_AGGREGATE_SOURCE_UNIT_REFS,
    "static-verification",
)
MAX_ENVELOPES = len(PREREQUISITE_SOURCE_UNIT_REFS)
PREREQUISITE_CHAIN_UNIT_REFS = (
    "manifest-attestation",
    "lint",
    "affected-preflight",
    "pytest-shards",
    "pytest",
    "static-verification",
)

_SAFE_REF_PATTERN = re.compile(r"^[a-z0-9][a-z0-9:._-]{0,191}$")
_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "construction_posture",
        "repository_sha",
        "plan_fingerprint",
        "source_envelope_refs",
        "prerequisite_unit_refs",
        "prerequisite_receipt_refs",
        "run_manifest_ref",
        "run_manifest_fingerprint",
        "run_status",
        "missing_full_plan_unit_refs",
        "reason_refs",
        "redaction_status",
        "content_fingerprint",
        "content_ref",
    }
)
_FORBIDDEN_GATE_FIELDS = frozenset(
    {
        "authorized",
        "gate_passed",
        "github_gate_satisfied",
        "github_green",
        "merge_allowed",
        "merge_gate_satisfied",
    }
)
_EVIDENCE_SCHEMA_VERSION = "uaa_foundation_prerequisite_evidence.v1"
_EVIDENCE_CONTENT_REF_PREFIX = "foundation-prerequisite-evidence:"
_EVIDENCE_FIELDS = frozenset(
    {
        "schema_version",
        "construction_posture",
        "repository_sha",
        "plan_fingerprint",
        "source_envelopes",
        "manifest",
        "redaction_status",
        "content_fingerprint",
        "content_ref",
    }
)


class VerificationGithubPrerequisiteError(ValueError):
    """Stable content-free prerequisite rejection."""

    def __init__(self, reason_ref: str) -> None:
        self.reason_ref = reason_ref
        super().__init__(f"GitHub prerequisite evidence rejected ({reason_ref})")


def _fail(reason_ref: str) -> None:
    raise VerificationGithubPrerequisiteError(reason_ref)


def _validate_safe_ref(value: str, *, reason_ref: str) -> None:
    if not isinstance(value, str) or _SAFE_REF_PATTERN.fullmatch(value) is None:
        _fail(reason_ref)


def _validate_unique_refs(values: tuple[str, ...], *, reason_ref: str) -> None:
    if len(values) != len(set(values)):
        _fail(reason_ref)
    for value in values:
        _validate_safe_ref(value, reason_ref=reason_ref)


@dataclass(frozen=True)
class FoundationPrerequisiteManifest:
    schema_version: str
    construction_posture: str
    repository_sha: str
    plan_fingerprint: str
    source_envelope_refs: tuple[str, ...]
    prerequisite_unit_refs: tuple[str, ...]
    prerequisite_receipt_refs: tuple[str, ...]
    run_manifest_ref: str
    run_manifest_fingerprint: str
    run_status: str
    missing_full_plan_unit_refs: tuple[str, ...]
    reason_refs: tuple[str, ...]
    redaction_status: str
    content_fingerprint: str
    content_ref: str

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            _fail("reason-ref:github-prerequisite:schema-invalid")
        if self.construction_posture != CONSTRUCTION_POSTURE:
            _fail("reason-ref:github-prerequisite:authority-posture-invalid")
        if self.redaction_status != REDACTION_STATUS:
            _fail("reason-ref:github-prerequisite:redaction-posture-invalid")
        if _SHA_PATTERN.fullmatch(self.repository_sha) is None:
            _fail("reason-ref:github-prerequisite:sha-invalid")
        for digest in (
            self.plan_fingerprint,
            self.run_manifest_fingerprint,
            self.content_fingerprint,
        ):
            if _DIGEST_PATTERN.fullmatch(digest) is None:
                _fail("reason-ref:github-prerequisite:digest-invalid")
        _validate_unique_refs(
            self.source_envelope_refs,
            reason_ref="reason-ref:github-prerequisite:envelope-refs-invalid",
        )
        if len(self.source_envelope_refs) != len(PREREQUISITE_SOURCE_UNIT_REFS):
            _fail("reason-ref:github-prerequisite:envelope-refs-invalid")
        if self.prerequisite_unit_refs != PREREQUISITE_CHAIN_UNIT_REFS:
            _fail("reason-ref:github-prerequisite:chain-invalid")
        _validate_unique_refs(
            self.prerequisite_receipt_refs,
            reason_ref="reason-ref:github-prerequisite:receipt-refs-invalid",
        )
        if len(self.prerequisite_receipt_refs) != len(PREREQUISITE_CHAIN_UNIT_REFS):
            _fail("reason-ref:github-prerequisite:receipt-refs-invalid")
        if (
            not self.run_manifest_ref.startswith("run:verification:")
            or _DIGEST_PATTERN.fullmatch(
                self.run_manifest_ref.removeprefix("run:verification:")
            )
            is None
            or self.run_manifest_ref
            != f"run:verification:{self.run_manifest_fingerprint}"
        ):
            _fail("reason-ref:github-prerequisite:run-ref-invalid")
        _validate_unique_refs(
            self.missing_full_plan_unit_refs,
            reason_ref="reason-ref:github-prerequisite:missing-unit-refs-invalid",
        )
        _validate_unique_refs(
            self.reason_refs,
            reason_ref="reason-ref:github-prerequisite:reason-refs-invalid",
        )
        if self.run_status not in {"passed", "blocked"}:
            _fail("reason-ref:github-prerequisite:run-status-invalid")
        if self.missing_full_plan_unit_refs:
            if self.run_status != "blocked" or self.reason_refs != (
                "reason-ref:verification:whole-run-incomplete",
            ):
                _fail("reason-ref:github-prerequisite:full-plan-posture-invalid")
        elif self.run_status != "passed" or self.reason_refs:
            _fail("reason-ref:github-prerequisite:full-plan-posture-invalid")
        expected_fingerprint = foundation_prerequisite_manifest_fingerprint(self)
        if self.content_fingerprint != expected_fingerprint:
            _fail("reason-ref:github-prerequisite:content-fingerprint-mismatch")
        if self.content_ref != f"{CONTENT_REF_PREFIX}{expected_fingerprint}":
            _fail("reason-ref:github-prerequisite:content-ref-mismatch")


@dataclass(frozen=True)
class FoundationPrerequisiteResult:
    manifest: FoundationPrerequisiteManifest
    run_manifest: VerificationRunManifest
    derived_receipts: tuple[VerificationReceipt, ...]


@dataclass(frozen=True)
class PytestAggregateResult:
    receipt: VerificationReceipt
    run_manifest: VerificationRunManifest


@dataclass(frozen=True)
class FoundationPrerequisiteEvidenceBundle:
    schema_version: str
    construction_posture: str
    repository_sha: str
    plan_fingerprint: str
    source_envelopes: tuple[str, ...]
    manifest: FoundationPrerequisiteManifest
    redaction_status: str
    content_fingerprint: str
    content_ref: str

    def validate(self) -> None:
        if self.schema_version != _EVIDENCE_SCHEMA_VERSION:
            _fail("reason-ref:github-prerequisite:evidence-schema-invalid")
        if self.construction_posture != CONSTRUCTION_POSTURE:
            _fail("reason-ref:github-prerequisite:authority-posture-invalid")
        if self.redaction_status != REDACTION_STATUS:
            _fail("reason-ref:github-prerequisite:redaction-posture-invalid")
        if _SHA_PATTERN.fullmatch(self.repository_sha) is None:
            _fail("reason-ref:github-prerequisite:sha-invalid")
        if (
            _DIGEST_PATTERN.fullmatch(self.plan_fingerprint) is None
            or _DIGEST_PATTERN.fullmatch(self.content_fingerprint) is None
        ):
            _fail("reason-ref:github-prerequisite:digest-invalid")
        if (
            len(self.source_envelopes) != MAX_ENVELOPES
            or len(self.source_envelopes) != len(set(self.source_envelopes))
            or any(
                not isinstance(envelope, str) or not envelope or len(envelope) > 400_000
                for envelope in self.source_envelopes
            )
        ):
            _fail("reason-ref:github-prerequisite:evidence-envelopes-invalid")
        self.manifest.validate()
        try:
            envelope_refs = tuple(
                decode_github_job_output(envelope).content_ref
                for envelope in self.source_envelopes
            )
        except VerificationGithubTransportError:
            _fail("reason-ref:github-prerequisite:evidence-envelopes-invalid")
        if (
            self.manifest.repository_sha != self.repository_sha
            or self.manifest.plan_fingerprint != self.plan_fingerprint
            or envelope_refs != self.manifest.source_envelope_refs
        ):
            _fail("reason-ref:github-prerequisite:evidence-plan-mismatch")
        expected = foundation_prerequisite_evidence_fingerprint(self)
        if self.content_fingerprint != expected:
            _fail("reason-ref:github-prerequisite:evidence-fingerprint-mismatch")
        if self.content_ref != f"{_EVIDENCE_CONTENT_REF_PREFIX}{expected}":
            _fail("reason-ref:github-prerequisite:evidence-ref-mismatch")


def _manifest_payload(
    manifest: FoundationPrerequisiteManifest,
    *,
    include_content_identity: bool = True,
) -> dict[str, Any]:
    payload = {
        field_name: getattr(manifest, field_name)
        for field_name in FoundationPrerequisiteManifest.__dataclass_fields__
        if include_content_identity
        or field_name not in {"content_fingerprint", "content_ref"}
    }
    return payload


def _canonical_json(payload: Any, *, max_bytes: int = MAX_MANIFEST_BYTES) -> bytes:
    try:
        encoded = json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (RecursionError, TypeError, ValueError):
        _fail("reason-ref:github-prerequisite:json-invalid")
    if not 0 < len(encoded) <= max_bytes:
        _fail("reason-ref:github-prerequisite:manifest-size-invalid")
    return encoded


def foundation_prerequisite_manifest_fingerprint(
    manifest: FoundationPrerequisiteManifest,
) -> str:
    return hashlib.sha256(
        _canonical_json(_manifest_payload(manifest, include_content_identity=False))
    ).hexdigest()


def _evidence_payload(
    evidence: FoundationPrerequisiteEvidenceBundle,
    *,
    include_content_identity: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": evidence.schema_version,
        "construction_posture": evidence.construction_posture,
        "repository_sha": evidence.repository_sha,
        "plan_fingerprint": evidence.plan_fingerprint,
        "source_envelopes": evidence.source_envelopes,
        "manifest": _manifest_payload(evidence.manifest),
        "redaction_status": evidence.redaction_status,
    }
    if include_content_identity:
        payload["content_fingerprint"] = evidence.content_fingerprint
        payload["content_ref"] = evidence.content_ref
    return payload


def foundation_prerequisite_evidence_fingerprint(
    evidence: FoundationPrerequisiteEvidenceBundle,
) -> str:
    return hashlib.sha256(
        _canonical_json(
            _evidence_payload(evidence, include_content_identity=False),
            max_bytes=MAX_EVIDENCE_BYTES,
        )
    ).hexdigest()


def build_foundation_prerequisite_evidence(
    plan: VerificationPlan,
    encoded_envelopes: tuple[str, ...],
    result: FoundationPrerequisiteResult | None = None,
) -> FoundationPrerequisiteEvidenceBundle:
    computed = collect_foundation_prerequisites(plan, encoded_envelopes)
    if result is not None and result != computed:
        _fail("reason-ref:github-prerequisite:evidence-result-mismatch")
    encoded_by_ref = {
        decode_github_job_output(encoded).content_ref: encoded
        for encoded in encoded_envelopes
    }
    canonical_envelopes = tuple(
        encoded_by_ref[envelope_ref]
        for envelope_ref in computed.manifest.source_envelope_refs
    )
    evidence = FoundationPrerequisiteEvidenceBundle(
        schema_version=_EVIDENCE_SCHEMA_VERSION,
        construction_posture=CONSTRUCTION_POSTURE,
        repository_sha=plan.repository_sha,
        plan_fingerprint=plan.plan_fingerprint,
        source_envelopes=canonical_envelopes,
        manifest=computed.manifest,
        redaction_status=REDACTION_STATUS,
        content_fingerprint="0" * 64,
        content_ref=f"{_EVIDENCE_CONTENT_REF_PREFIX}{'0' * 64}",
    )
    fingerprint = foundation_prerequisite_evidence_fingerprint(evidence)
    evidence = replace(
        evidence,
        content_fingerprint=fingerprint,
        content_ref=f"{_EVIDENCE_CONTENT_REF_PREFIX}{fingerprint}",
    )
    evidence.validate()
    return evidence


def encode_foundation_prerequisite_evidence(
    evidence: FoundationPrerequisiteEvidenceBundle,
) -> str:
    if type(evidence) is not FoundationPrerequisiteEvidenceBundle:
        _fail("reason-ref:github-prerequisite:evidence-type-invalid")
    evidence.validate()
    return _canonical_json(
        _evidence_payload(evidence),
        max_bytes=MAX_EVIDENCE_BYTES,
    ).decode("ascii")


def _canonical_ci_units_by_ref() -> dict[str, Any]:
    return {unit.unit_ref: unit for unit in CI_JOB_GRAPH}


def _validate_plan_chain(plan: VerificationPlan) -> None:
    try:
        plan.validate()
    except ValueError:
        _fail("reason-ref:github-prerequisite:plan-invalid")
    if plan.schema_version not in {
        "uaa_ci_command_manifest.v3",
        "uaa_verification_plan.v3",
    }:
        _fail("reason-ref:github-prerequisite:plan-version-invalid")
    selected = set(plan.selected_unit_refs)
    if not set(PREREQUISITE_CHAIN_UNIT_REFS).issubset(selected):
        _fail("reason-ref:github-prerequisite:plan-chain-missing")
    canonical = _canonical_ci_units_by_ref()
    if any(unit_ref not in canonical for unit_ref in PREREQUISITE_CHAIN_UNIT_REFS):
        _fail("reason-ref:github-prerequisite:canonical-chain-invalid")


def collect_foundation_prerequisites(
    plan: VerificationPlan,
    encoded_envelopes: tuple[str, ...],
) -> FoundationPrerequisiteResult:
    """Validate exact job evidence and derive a non-authoritative prerequisite view."""

    _validate_plan_chain(plan)
    if not isinstance(encoded_envelopes, tuple) or len(encoded_envelopes) != len(
        PREREQUISITE_SOURCE_UNIT_REFS
    ):
        _fail("reason-ref:github-prerequisite:envelope-count-invalid")
    ordered_envelopes = _validated_source_envelopes(
        plan,
        encoded_envelopes,
        expected_unit_refs=PREREQUISITE_SOURCE_UNIT_REFS,
    )
    try:
        aggregate = aggregate_verification_run(
            plan,
            VERIFICATION_DAG,
            tuple(envelope.receipt for envelope in ordered_envelopes),
            execution_surface_ref="surface-ref:github",
        )
    except ValueError:
        _fail("reason-ref:github-prerequisite:aggregate-invalid")
    if (
        tuple(receipt.unit_ref for receipt in aggregate.derived_receipts) != ("pytest",)
        or aggregate.derived_receipts[0].status is not VerificationTerminalStatus.PASSED
    ):
        _fail("reason-ref:github-prerequisite:aggregate-proof-invalid")
    receipts_by_unit = {
        envelope.receipt.unit_ref: envelope.receipt for envelope in ordered_envelopes
    }
    receipts_by_unit["pytest"] = aggregate.derived_receipts[0]
    prerequisite_receipts = tuple(
        receipts_by_unit[unit_ref] for unit_ref in PREREQUISITE_CHAIN_UNIT_REFS
    )
    if any(
        receipt.status is not VerificationTerminalStatus.PASSED
        for receipt in prerequisite_receipts
    ):
        _fail("reason-ref:github-prerequisite:chain-not-passed")
    run = aggregate.run_manifest
    if run.status not in {
        VerificationTerminalStatus.PASSED,
        VerificationTerminalStatus.BLOCKED,
    }:
        _fail("reason-ref:github-prerequisite:full-plan-posture-invalid")
    manifest = FoundationPrerequisiteManifest(
        schema_version=SCHEMA_VERSION,
        construction_posture=CONSTRUCTION_POSTURE,
        repository_sha=plan.repository_sha,
        plan_fingerprint=plan.plan_fingerprint,
        source_envelope_refs=tuple(
            envelope.content_ref for envelope in ordered_envelopes
        ),
        prerequisite_unit_refs=PREREQUISITE_CHAIN_UNIT_REFS,
        prerequisite_receipt_refs=tuple(
            receipt.receipt_ref for receipt in prerequisite_receipts
        ),
        run_manifest_ref=run.run_ref,
        run_manifest_fingerprint=run.run_fingerprint,
        run_status=run.status.value,
        missing_full_plan_unit_refs=run.missing_unit_refs,
        reason_refs=run.reason_refs,
        redaction_status=REDACTION_STATUS,
        content_fingerprint="0" * 64,
        content_ref=f"{CONTENT_REF_PREFIX}{'0' * 64}",
    )
    fingerprint = foundation_prerequisite_manifest_fingerprint(manifest)
    manifest = replace(
        manifest,
        content_fingerprint=fingerprint,
        content_ref=f"{CONTENT_REF_PREFIX}{fingerprint}",
    )
    manifest.validate()
    return FoundationPrerequisiteResult(
        manifest=manifest,
        run_manifest=run,
        derived_receipts=aggregate.derived_receipts,
    )


def _validated_source_envelopes(
    plan: VerificationPlan,
    encoded_envelopes: tuple[str, ...],
    *,
    expected_unit_refs: tuple[str, ...],
) -> tuple[VerificationGithubJobOutputEnvelope, ...]:
    envelopes_by_unit: dict[str, VerificationGithubJobOutputEnvelope] = {}
    envelope_refs: set[str] = set()
    receipt_refs: set[str] = set()
    for encoded in encoded_envelopes:
        try:
            envelope = decode_github_job_output(encoded)
            validate_github_job_output_against_plan(envelope, plan)
        except VerificationGithubTransportError:
            _fail("reason-ref:github-prerequisite:envelope-invalid")
        receipt = envelope.receipt
        if (
            envelope.final_run_manifest is not None
            or receipt.unit_ref not in expected_unit_refs
        ):
            _fail("reason-ref:github-prerequisite:extra-evidence")
        if (
            receipt.unit_ref in envelopes_by_unit
            or envelope.content_ref in envelope_refs
            or receipt.receipt_ref in receipt_refs
        ):
            _fail("reason-ref:github-prerequisite:duplicate-evidence")
        if receipt.status is not VerificationTerminalStatus.PASSED:
            _fail("reason-ref:github-prerequisite:nonpassing-evidence")
        envelopes_by_unit[receipt.unit_ref] = envelope
        envelope_refs.add(envelope.content_ref)
        receipt_refs.add(receipt.receipt_ref)
    if set(envelopes_by_unit) != set(expected_unit_refs):
        _fail("reason-ref:github-prerequisite:chain-evidence-missing")
    return tuple(envelopes_by_unit[unit_ref] for unit_ref in expected_unit_refs)


def collect_pytest_aggregate(
    plan: VerificationPlan,
    encoded_envelopes: tuple[str, ...],
) -> PytestAggregateResult:
    """Derive only the commandless pytest aggregate before static verification."""

    _validate_plan_chain(plan)
    if not isinstance(encoded_envelopes, tuple) or len(encoded_envelopes) != len(
        PYTEST_AGGREGATE_SOURCE_UNIT_REFS
    ):
        _fail("reason-ref:github-prerequisite:envelope-count-invalid")
    ordered_envelopes = _validated_source_envelopes(
        plan,
        encoded_envelopes,
        expected_unit_refs=PYTEST_AGGREGATE_SOURCE_UNIT_REFS,
    )
    try:
        aggregate = aggregate_verification_run(
            plan,
            VERIFICATION_DAG,
            tuple(envelope.receipt for envelope in ordered_envelopes),
            execution_surface_ref="surface-ref:github",
        )
    except ValueError:
        _fail("reason-ref:github-prerequisite:aggregate-invalid")
    if (
        tuple(receipt.unit_ref for receipt in aggregate.derived_receipts) != ("pytest",)
        or aggregate.derived_receipts[0].status is not VerificationTerminalStatus.PASSED
    ):
        _fail("reason-ref:github-prerequisite:aggregate-proof-invalid")
    if aggregate.run_manifest.status is not VerificationTerminalStatus.BLOCKED:
        _fail("reason-ref:github-prerequisite:full-plan-posture-invalid")
    return PytestAggregateResult(
        receipt=aggregate.derived_receipts[0],
        run_manifest=aggregate.run_manifest,
    )


def encode_foundation_prerequisite_manifest(
    manifest: FoundationPrerequisiteManifest,
) -> str:
    if type(manifest) is not FoundationPrerequisiteManifest:
        _fail("reason-ref:github-prerequisite:manifest-type-invalid")
    manifest.validate()
    return _canonical_json(_manifest_payload(manifest)).decode("ascii")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            _fail("reason-ref:github-prerequisite:json-duplicate-field")
        output[key] = value
    return output


def _parse_integer(value: str) -> int:
    if len(value.lstrip("-")) > 19:
        _fail("reason-ref:github-prerequisite:json-integer-invalid")
    parsed = int(value)
    if not -MAX_INTEGER <= parsed <= MAX_INTEGER:
        _fail("reason-ref:github-prerequisite:json-integer-invalid")
    return parsed


def _parse_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        _fail("reason-ref:github-prerequisite:json-number-nonfinite")
    return parsed


def _reject_nonfinite(_value: str) -> None:
    _fail("reason-ref:github-prerequisite:json-number-nonfinite")


def _parse_strict_json_object(encoded: str, *, max_bytes: int) -> dict[str, Any]:
    if not isinstance(encoded, str) or not 0 < len(encoded) <= max_bytes:
        _fail("reason-ref:github-prerequisite:manifest-size-invalid")
    try:
        raw = encoded.encode("ascii")
        payload = json.loads(
            raw,
            object_pairs_hook=_reject_duplicate_keys,
            parse_int=_parse_integer,
            parse_float=_parse_float,
            parse_constant=_reject_nonfinite,
        )
    except VerificationGithubPrerequisiteError:
        raise
    except (
        UnicodeEncodeError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        TypeError,
        ValueError,
    ):
        _fail("reason-ref:github-prerequisite:json-invalid")
    if not isinstance(payload, dict):
        _fail("reason-ref:github-prerequisite:json-invalid")
    if _canonical_json(payload, max_bytes=max_bytes) != raw:
        _fail("reason-ref:github-prerequisite:json-not-canonical")
    return payload


def parse_foundation_prerequisite_manifest(
    encoded: str,
) -> FoundationPrerequisiteManifest:
    payload = _parse_strict_json_object(encoded, max_bytes=MAX_MANIFEST_BYTES)
    if set(payload) != _MANIFEST_FIELDS:
        if set(payload) & _FORBIDDEN_GATE_FIELDS:
            _fail("reason-ref:github-prerequisite:gate-claim-forbidden")
        _fail("reason-ref:github-prerequisite:manifest-fields-invalid")
    tuple_fields = {
        "source_envelope_refs",
        "prerequisite_unit_refs",
        "prerequisite_receipt_refs",
        "missing_full_plan_unit_refs",
        "reason_refs",
    }
    if any(
        not isinstance(payload[field_name], list)
        or not all(isinstance(item, str) for item in payload[field_name])
        for field_name in tuple_fields
    ):
        _fail("reason-ref:github-prerequisite:manifest-shape-invalid")
    scalar_fields = _MANIFEST_FIELDS - tuple_fields
    if not all(isinstance(payload[field_name], str) for field_name in scalar_fields):
        _fail("reason-ref:github-prerequisite:manifest-shape-invalid")
    manifest = FoundationPrerequisiteManifest(
        **{
            field_name: (
                tuple(payload[field_name])
                if field_name in tuple_fields
                else payload[field_name]
            )
            for field_name in _MANIFEST_FIELDS
        }
    )
    manifest.validate()
    return manifest


def parse_foundation_prerequisite_evidence(
    encoded: str,
) -> FoundationPrerequisiteEvidenceBundle:
    payload = _parse_strict_json_object(encoded, max_bytes=MAX_EVIDENCE_BYTES)
    if set(payload) != _EVIDENCE_FIELDS:
        if set(payload) & _FORBIDDEN_GATE_FIELDS:
            _fail("reason-ref:github-prerequisite:gate-claim-forbidden")
        _fail("reason-ref:github-prerequisite:evidence-fields-invalid")
    if (
        not isinstance(payload["source_envelopes"], list)
        or not all(
            isinstance(envelope, str) for envelope in payload["source_envelopes"]
        )
        or not isinstance(payload["manifest"], dict)
    ):
        _fail("reason-ref:github-prerequisite:evidence-shape-invalid")
    scalar_fields = _EVIDENCE_FIELDS - {"source_envelopes", "manifest"}
    if not all(isinstance(payload[field_name], str) for field_name in scalar_fields):
        _fail("reason-ref:github-prerequisite:evidence-shape-invalid")
    manifest = parse_foundation_prerequisite_manifest(
        _canonical_json(payload["manifest"]).decode("ascii")
    )
    evidence = FoundationPrerequisiteEvidenceBundle(
        schema_version=payload["schema_version"],
        construction_posture=payload["construction_posture"],
        repository_sha=payload["repository_sha"],
        plan_fingerprint=payload["plan_fingerprint"],
        source_envelopes=tuple(payload["source_envelopes"]),
        manifest=manifest,
        redaction_status=payload["redaction_status"],
        content_fingerprint=payload["content_fingerprint"],
        content_ref=payload["content_ref"],
    )
    evidence.validate()
    return evidence


def _directory_flags() -> int:
    return os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)


def _open_parent_directory(path: Path) -> tuple[int, str]:
    absolute = Path(os.path.abspath(os.fspath(path)))
    if absolute == Path(absolute.anchor) or absolute.name in {"", ".", ".."}:
        _fail("reason-ref:github-prerequisite:output-path-invalid")
    components = absolute.parent.parts[1:]
    try:
        descriptor = os.open(absolute.anchor, _directory_flags())
    except OSError:
        _fail("reason-ref:github-prerequisite:output-path-unavailable")
    try:
        for component in components:
            if component in {"", ".", ".."}:
                _fail("reason-ref:github-prerequisite:output-path-invalid")
            next_descriptor = os.open(component, _directory_flags(), dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
    except VerificationGithubPrerequisiteError:
        os.close(descriptor)
        raise
    except OSError:
        os.close(descriptor)
        _fail("reason-ref:github-prerequisite:output-path-unsafe")
    return descriptor, absolute.name


def _validate_owner_file(metadata: os.stat_result, *, max_bytes: int) -> None:
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
        or metadata.st_uid != os.geteuid()
        or stat.S_IMODE(metadata.st_mode) & 0o022
        or not 0 <= metadata.st_size <= max_bytes
    ):
        _fail("reason-ref:github-prerequisite:output-file-unsafe")


def _write_all(descriptor: int, encoded: bytes) -> None:
    offset = 0
    while offset < len(encoded):
        try:
            written = os.write(descriptor, encoded[offset:])
        except OSError:
            _fail("reason-ref:github-prerequisite:output-write-failed")
        if written <= 0:
            _fail("reason-ref:github-prerequisite:output-write-failed")
        offset += written


def _write_owner_safe(
    path: Path,
    encoded: bytes,
    *,
    append: bool,
    max_bytes: int,
) -> None:
    if not encoded or len(encoded) > max_bytes:
        _fail("reason-ref:github-prerequisite:output-size-invalid")
    parent_descriptor, name = _open_parent_directory(path)
    descriptor: int | None = None
    try:
        flags = (
            os.O_WRONLY
            | os.O_CLOEXEC
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        if append:
            flags |= os.O_APPEND
        try:
            descriptor = os.open(name, flags, dir_fd=parent_descriptor)
        except FileNotFoundError:
            if append:
                _fail("reason-ref:github-prerequisite:output-path-unavailable")
            try:
                descriptor = os.open(
                    name,
                    flags | os.O_CREAT | os.O_EXCL,
                    OWNER_FILE_MODE,
                    dir_fd=parent_descriptor,
                )
            except OSError:
                _fail("reason-ref:github-prerequisite:output-path-unsafe")
        except OSError:
            _fail("reason-ref:github-prerequisite:output-path-unsafe")
        assert descriptor is not None
        metadata = os.fstat(descriptor)
        _validate_owner_file(metadata, max_bytes=max_bytes)
        if metadata.st_size + len(encoded) > max_bytes:
            _fail("reason-ref:github-prerequisite:output-size-invalid")
        if append:
            os.lseek(descriptor, 0, os.SEEK_END)
        else:
            try:
                os.ftruncate(descriptor, 0)
                os.lseek(descriptor, 0, os.SEEK_SET)
            except OSError:
                _fail("reason-ref:github-prerequisite:output-write-failed")
        _write_all(descriptor, encoded)
        try:
            os.fsync(descriptor)
        except OSError:
            _fail("reason-ref:github-prerequisite:output-write-failed")
        expected_size = metadata.st_size + len(encoded) if append else len(encoded)
        final_metadata = os.fstat(descriptor)
        _validate_owner_file(final_metadata, max_bytes=max_bytes)
        if final_metadata.st_size != expected_size:
            _fail("reason-ref:github-prerequisite:output-write-failed")
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent_descriptor)


def append_github_output(path: Path, key: str, value: str) -> None:
    """Append one validated transport envelope without opening unsafe file types."""

    if key != "verification_envelope":
        _fail("reason-ref:github-prerequisite:github-output-key-invalid")
    if (
        not isinstance(value, str)
        or not 0 < len(value) <= MAX_ENCODED_CHARS
        or any(character in value for character in "\r\n=")
    ):
        _fail("reason-ref:github-prerequisite:github-output-value-invalid")
    try:
        decode_github_job_output(value)
    except VerificationGithubTransportError:
        _fail("reason-ref:github-prerequisite:github-output-value-invalid")
    _write_owner_safe(
        Path(path),
        f"{key}={value}\n".encode("ascii"),
        append=True,
        max_bytes=MAX_GITHUB_OUTPUT_BYTES,
    )


def _read_owner_safe(path: Path, *, max_bytes: int) -> bytes:
    parent_descriptor, name = _open_parent_directory(path)
    descriptor: int | None = None
    try:
        try:
            descriptor = os.open(
                name,
                os.O_RDONLY
                | os.O_CLOEXEC
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_NONBLOCK", 0),
                dir_fd=parent_descriptor,
            )
        except OSError:
            _fail("reason-ref:github-prerequisite:manifest-file-unavailable")
        metadata = os.fstat(descriptor)
        _validate_owner_file(metadata, max_bytes=max_bytes)
        if metadata.st_size <= 0:
            _fail("reason-ref:github-prerequisite:manifest-file-invalid")
        remaining = metadata.st_size
        chunks: list[bytes] = []
        while remaining:
            try:
                chunk = os.read(descriptor, min(remaining, 64 * 1024))
            except OSError:
                _fail("reason-ref:github-prerequisite:manifest-file-invalid")
            if not chunk:
                _fail("reason-ref:github-prerequisite:manifest-file-invalid")
            chunks.append(chunk)
            remaining -= len(chunk)
        final_metadata = os.fstat(descriptor)
        if (
            final_metadata.st_dev != metadata.st_dev
            or final_metadata.st_ino != metadata.st_ino
            or final_metadata.st_mode != metadata.st_mode
            or final_metadata.st_nlink != metadata.st_nlink
            or final_metadata.st_uid != metadata.st_uid
            or final_metadata.st_size != metadata.st_size
        ):
            _fail("reason-ref:github-prerequisite:manifest-file-substituted")
        return b"".join(chunks)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent_descriptor)


def _reconstruct_plan(
    repo: Path,
    sha: str,
    base_sha: str,
    visual_scope: str,
) -> VerificationPlan:
    if (
        _SHA_PATTERN.fullmatch(sha) is None
        or _SHA_PATTERN.fullmatch(base_sha) is None
    ):
        _fail("reason-ref:github-prerequisite:sha-invalid")
    try:
        return build_plan(
            repo,
            sha,
            base_sha=base_sha,
            frontend_visual_scope=visual_scope,
            force_full=True,
            verify_repository_state=True,
        )
    except (OSError, ValueError):
        _fail("reason-ref:github-prerequisite:plan-reconstruction-failed")


def load_foundation_prerequisite_manifest(
    path: Path,
    repo: Path,
    sha: str,
    base_sha: str | None = None,
) -> FoundationPrerequisiteManifest:
    encoded = _read_owner_safe(Path(path), max_bytes=MAX_EVIDENCE_BYTES)
    try:
        evidence = parse_foundation_prerequisite_evidence(encoded.decode("ascii"))
    except (UnicodeDecodeError, VerificationGithubPrerequisiteError):
        _fail("reason-ref:github-prerequisite:manifest-file-invalid")
    resolved_base_sha = base_sha or os.environ.get(
        "UAA_VERIFICATION_BASE_SHA",
        sha,
    )
    visual_scope = os.environ.get(
        "UAA_VERIFICATION_VISUAL_SCOPE",
        "unknown_fail_closed",
    )
    plan = _reconstruct_plan(Path(repo), sha, resolved_base_sha, visual_scope)
    if (
        evidence.repository_sha != sha
        or evidence.plan_fingerprint != plan.plan_fingerprint
    ):
        _fail("reason-ref:github-prerequisite:manifest-plan-mismatch")
    try:
        recomputed = collect_foundation_prerequisites(
            plan,
            evidence.source_envelopes,
        )
    except VerificationGithubPrerequisiteError:
        _fail("reason-ref:github-prerequisite:manifest-evidence-invalid")
    if evidence.manifest != recomputed.manifest:
        _fail("reason-ref:github-prerequisite:manifest-recomputation-mismatch")
    return evidence.manifest


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build bounded non-authoritative GitHub verification evidence."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("aggregate", "foundation-manifest"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--repo", type=Path, required=True)
        subparser.add_argument("--sha", required=True)
        subparser.add_argument("--base-sha", required=True)
        subparser.add_argument(
            "--visual-scope",
            default="unknown_fail_closed",
            choices=("affected", "not_affected", "unknown_fail_closed"),
        )
        subparser.add_argument("--envelope", action="append", required=True)
        if command == "aggregate":
            subparser.add_argument("--github-output-file", type=Path, required=True)
        else:
            subparser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        plan = _reconstruct_plan(
            args.repo,
            args.sha,
            args.base_sha,
            args.visual_scope,
        )
        if args.command == "aggregate":
            aggregate = collect_pytest_aggregate(plan, tuple(args.envelope))
            output_envelope = build_github_job_output_envelope(
                plan,
                aggregate.receipt,
                final_run_manifest=aggregate.run_manifest,
            )
            value = encode_github_job_output(output_envelope)
            append_github_output(
                args.github_output_file,
                "verification_envelope",
                value,
            )
        else:
            result = collect_foundation_prerequisites(plan, tuple(args.envelope))
            evidence = build_foundation_prerequisite_evidence(
                plan,
                tuple(args.envelope),
                result,
            )
            _write_owner_safe(
                args.output,
                encode_foundation_prerequisite_evidence(evidence).encode("ascii"),
                append=False,
                max_bytes=MAX_EVIDENCE_BYTES,
            )
    except (
        StopIteration,
        VerificationGithubPrerequisiteError,
        VerificationGithubTransportError,
    ) as error:
        reason_ref = getattr(
            error,
            "reason_ref",
            "reason-ref:github-prerequisite:aggregate-proof-invalid",
        )
        print(f"GitHub prerequisite evidence: blocked ({reason_ref})", file=sys.stderr)
        return 2
    return 0


__all__ = [
    "CONSTRUCTION_POSTURE",
    "FoundationPrerequisiteEvidenceBundle",
    "FoundationPrerequisiteManifest",
    "FoundationPrerequisiteResult",
    "PYTEST_AGGREGATE_SOURCE_UNIT_REFS",
    "PREREQUISITE_CHAIN_UNIT_REFS",
    "PREREQUISITE_SOURCE_UNIT_REFS",
    "VerificationGithubPrerequisiteError",
    "append_github_output",
    "build_foundation_prerequisite_evidence",
    "collect_foundation_prerequisites",
    "collect_pytest_aggregate",
    "encode_foundation_prerequisite_evidence",
    "encode_foundation_prerequisite_manifest",
    "foundation_prerequisite_evidence_fingerprint",
    "foundation_prerequisite_manifest_fingerprint",
    "load_foundation_prerequisite_manifest",
    "main",
    "parse_foundation_prerequisite_evidence",
    "parse_foundation_prerequisite_manifest",
]


if __name__ == "__main__":
    raise SystemExit(main())
