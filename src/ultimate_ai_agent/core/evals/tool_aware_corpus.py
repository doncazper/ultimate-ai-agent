from __future__ import annotations

import hashlib
import hmac
import json
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import validate_execution_ref


TAW00_GENERATOR_REF = "generator-ref:taw00:synthetic-corpus:v1"
TAW00_GENERATOR_VERSION = "1"
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def canonical_digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _digest(value: str, field_name: str) -> None:
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be an exact sha256 digest")


class DevelopmentCaseSpec(_FrozenModel):
    case_ref: str
    category_ref: str
    rubric_ref: str
    parameter_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    variant_index: int = Field(..., ge=0, le=100_000)

    @model_validator(mode="after")
    def validate_refs(self) -> "DevelopmentCaseSpec":
        for value, field_name in (
            (self.case_ref, "case_ref"),
            (self.category_ref, "category_ref"),
            (self.rubric_ref, "rubric_ref"),
        ):
            _ref(value, field_name)
        if len(self.parameter_refs) != len(set(self.parameter_refs)):
            raise ValueError("parameter_refs must be unique")
        for value in self.parameter_refs:
            _ref(value, "parameter_ref")
        return self


class DevelopmentManifestBuildSpec(_FrozenModel):
    corpus_ref: str
    deterministic_seed_ref: str
    seed_material_hex: str = Field(..., min_length=32, max_length=256)
    cases: tuple[DevelopmentCaseSpec, ...] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_build_spec(self) -> "DevelopmentManifestBuildSpec":
        _ref(self.corpus_ref, "corpus_ref")
        _ref(self.deterministic_seed_ref, "deterministic_seed_ref")
        try:
            seed_material = bytes.fromhex(self.seed_material_hex)
        except ValueError as exc:
            raise ValueError("seed material must be canonical hexadecimal") from exc
        if len(seed_material) < 16 or self.seed_material_hex != seed_material.hex():
            raise ValueError("development seed material must contain at least 128 bits")
        return self


class DevelopmentCaseRecord(_FrozenModel):
    case_ref: str
    category_ref: str
    rubric_ref: str
    parameter_refs: tuple[str, ...]
    variant_index: int = Field(..., ge=0, le=100_000)
    generated_content_digest: str

    @model_validator(mode="after")
    def validate_record(self) -> "DevelopmentCaseRecord":
        for value, field_name in (
            (self.case_ref, "case_ref"),
            (self.category_ref, "category_ref"),
            (self.rubric_ref, "rubric_ref"),
        ):
            _ref(value, field_name)
        for value in self.parameter_refs:
            _ref(value, "parameter_ref")
        _digest(self.generated_content_digest, "generated_content_digest")
        return self


class SyntheticCasePayload(_FrozenModel):
    """Transient synthetic payload reconstructed locally, never a durable receipt."""

    system_text: str = Field(..., min_length=1, max_length=1_024)
    user_text: str = Field(..., min_length=1, max_length=2_048)


class DevelopmentCorpusManifest(_FrozenModel):
    schema_version: Literal["uaa-taw00-development-corpus.v1"] = (
        "uaa-taw00-development-corpus.v1"
    )
    corpus_ref: str
    generator_ref: Literal["generator-ref:taw00:synthetic-corpus:v1"] = (
        TAW00_GENERATOR_REF
    )
    generator_version: Literal["1"] = TAW00_GENERATOR_VERSION
    deterministic_seed_ref: str
    deterministic_seed_material_hex: str = Field(..., min_length=32, max_length=256)
    cases: tuple[DevelopmentCaseRecord, ...] = Field(..., min_length=1)
    corpus_digest: str
    synthetic_only: Literal[True] = True
    raw_content_persisted: Literal[False] = False

    @model_validator(mode="after")
    def validate_manifest(self) -> "DevelopmentCorpusManifest":
        _ref(self.corpus_ref, "corpus_ref")
        _ref(self.deterministic_seed_ref, "deterministic_seed_ref")
        try:
            seed_material = bytes.fromhex(self.deterministic_seed_material_hex)
        except ValueError as exc:
            raise ValueError(
                "development seed material must be canonical hexadecimal"
            ) from exc
        if (
            len(seed_material) < 16
            or self.deterministic_seed_material_hex != seed_material.hex()
        ):
            raise ValueError("development seed material must contain at least 128 bits")
        case_refs = [case.case_ref for case in self.cases]
        if len(case_refs) != len(set(case_refs)):
            raise ValueError("development case refs must be unique")
        for case in self.cases:
            spec = DevelopmentCaseSpec(
                case_ref=case.case_ref,
                category_ref=case.category_ref,
                rubric_ref=case.rubric_ref,
                parameter_refs=case.parameter_refs,
                variant_index=case.variant_index,
            )
            generated = generate_synthetic_case_payload(seed_material, spec)
            if canonical_digest(generated.model_dump(mode="json")) != (
                case.generated_content_digest
            ):
                raise ValueError("development generated-content digest binding drift")
        expected = canonical_digest(
            {
                "generator_ref": self.generator_ref,
                "generator_version": self.generator_version,
                "deterministic_seed_ref": self.deterministic_seed_ref,
                "deterministic_seed_material_hex": self.deterministic_seed_material_hex,
                "cases": [case.model_dump(mode="json") for case in self.cases],
            }
        )
        if self.corpus_digest != expected:
            raise ValueError("development corpus digest binding drift")
        return self


class HoldoutCommitment(_FrozenModel):
    schema_version: Literal["uaa-taw00-holdout-commitment.v1"] = (
        "uaa-taw00-holdout-commitment.v1"
    )
    cycle_ref: str
    custodian_ref: str
    generator_ref: Literal["generator-ref:taw00:synthetic-corpus:v1"] = (
        TAW00_GENERATOR_REF
    )
    generator_version: Literal["1"] = TAW00_GENERATOR_VERSION
    commitment_envelope_version: Literal["uaa-taw00-holdout-envelope.v1"] = (
        "uaa-taw00-holdout-envelope.v1"
    )
    commitment_algorithm: Literal["hmac-sha256"] = "hmac-sha256"
    commitment_digest: str
    creation_order_evidence_ref: str
    custodian_attestation_ref: str
    private_material_disclosed: Literal[False] = False

    @model_validator(mode="after")
    def validate_commitment(self) -> "HoldoutCommitment":
        for value, field_name in (
            (self.cycle_ref, "cycle_ref"),
            (self.custodian_ref, "custodian_ref"),
            (self.creation_order_evidence_ref, "creation_order_evidence_ref"),
            (self.custodian_attestation_ref, "custodian_attestation_ref"),
        ):
            _ref(value, field_name)
        _digest(self.commitment_digest, "commitment_digest")
        return self


class PrivateHoldoutManifest(_FrozenModel):
    """Custodian-only manifest. It must never be written into the candidate repo."""

    schema_version: Literal["uaa-taw00-private-holdout.v1"] = (
        "uaa-taw00-private-holdout.v1"
    )
    cycle_ref: str
    corpus_ref: str
    deterministic_seed_ref: str
    seed_material_hex: str = Field(..., min_length=64, max_length=256)
    cases: tuple[DevelopmentCaseSpec, ...] = Field(..., min_length=1)
    synthetic_only: Literal[True] = True

    @model_validator(mode="after")
    def validate_private_manifest(self) -> "PrivateHoldoutManifest":
        for value, field_name in (
            (self.cycle_ref, "cycle_ref"),
            (self.corpus_ref, "corpus_ref"),
            (self.deterministic_seed_ref, "deterministic_seed_ref"),
        ):
            _ref(value, field_name)
        try:
            seed = bytes.fromhex(self.seed_material_hex)
        except ValueError as exc:
            raise ValueError("seed_material_hex must be canonical hexadecimal") from exc
        if len(seed) < 32 or self.seed_material_hex != seed.hex():
            raise ValueError("private holdout seed must contain at least 256 bits")
        case_refs = [case.case_ref for case in self.cases]
        if len(case_refs) != len(set(case_refs)):
            raise ValueError("private holdout case refs must be unique")
        return self


def generate_synthetic_case_payload(
    seed_material: bytes, spec: DevelopmentCaseSpec
) -> SyntheticCasePayload:
    """Reconstruct the exact synthetic system/user payload from safe inputs."""
    if len(seed_material) < 16:
        raise ValueError("development seed material must contain at least 128 bits")
    token_material = json.dumps(
        {
            "generator_ref": TAW00_GENERATOR_REF,
            "generator_version": TAW00_GENERATOR_VERSION,
            "seed_digest": hashlib.sha256(seed_material).hexdigest(),
            "spec": spec.model_dump(mode="json"),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    variant_token = hashlib.sha256(token_material).hexdigest()[:24]
    return SyntheticCasePayload(
        system_text=(
            "Synthetic evaluation case. Follow the rubric identified by "
            f"{spec.rubric_ref}; do not execute tools or external actions."
        ),
        user_text=(
            f"Synthetic request {spec.case_ref} in {spec.category_ref}; "
            f"parameters {','.join(spec.parameter_refs)}; variant "
            f"{spec.variant_index}; deterministic token {variant_token}."
        ),
    )


def reconstruct_development_case_payload(
    manifest: DevelopmentCorpusManifest, case_ref: str
) -> SyntheticCasePayload:
    """Reconstruct and digest-check a development case from its manifest alone."""
    matches = [case for case in manifest.cases if case.case_ref == case_ref]
    if len(matches) != 1:
        raise ValueError("development case ref must identify exactly one manifest case")
    record = matches[0]
    payload = generate_synthetic_case_payload(
        bytes.fromhex(manifest.deterministic_seed_material_hex),
        DevelopmentCaseSpec(
            case_ref=record.case_ref,
            category_ref=record.category_ref,
            rubric_ref=record.rubric_ref,
            parameter_refs=record.parameter_refs,
            variant_index=record.variant_index,
        ),
    )
    if (
        canonical_digest(payload.model_dump(mode="json"))
        != record.generated_content_digest
    ):
        raise ValueError("development generated-content digest binding drift")
    return payload


def build_development_corpus_manifest(
    *,
    corpus_ref: str,
    deterministic_seed_ref: str,
    seed_material: bytes,
    specs: tuple[DevelopmentCaseSpec, ...],
) -> DevelopmentCorpusManifest:
    if len(seed_material) < 16:
        raise ValueError("development seed material must contain at least 128 bits")
    if not specs:
        raise ValueError("development corpus requires at least one case")
    cases = tuple(
        DevelopmentCaseRecord(
            case_ref=spec.case_ref,
            category_ref=spec.category_ref,
            rubric_ref=spec.rubric_ref,
            parameter_refs=spec.parameter_refs,
            variant_index=spec.variant_index,
            generated_content_digest=canonical_digest(
                generate_synthetic_case_payload(seed_material, spec).model_dump(
                    mode="json"
                )
            ),
        )
        for spec in specs
    )
    digest = canonical_digest(
        {
            "generator_ref": TAW00_GENERATOR_REF,
            "generator_version": TAW00_GENERATOR_VERSION,
            "deterministic_seed_ref": deterministic_seed_ref,
            "deterministic_seed_material_hex": seed_material.hex(),
            "cases": [case.model_dump(mode="json") for case in cases],
        }
    )
    return DevelopmentCorpusManifest(
        corpus_ref=corpus_ref,
        deterministic_seed_ref=deterministic_seed_ref,
        deterministic_seed_material_hex=seed_material.hex(),
        cases=cases,
        corpus_digest=digest,
    )


def build_holdout_commitment(
    *,
    cycle_ref: str,
    custodian_ref: str,
    creation_order_evidence_ref: str,
    custodian_attestation_ref: str,
    secret_key: bytes,
    private_manifest: bytes,
) -> HoldoutCommitment:
    if len(secret_key) < 32:
        raise ValueError("holdout HMAC key must contain at least 256 bits")
    try:
        raw_manifest = json.loads(private_manifest.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("private holdout manifest must be canonical JSON") from exc
    manifest = PrivateHoldoutManifest.model_validate(raw_manifest)
    if manifest.cycle_ref != cycle_ref:
        raise ValueError("private holdout manifest cycle does not match commitment")
    canonical_manifest = json.dumps(
        manifest.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    ).encode()
    envelope = {
        "schema_version": "uaa-taw00-holdout-envelope.v1",
        "cycle_ref": cycle_ref,
        "custodian_ref": custodian_ref,
        "custodian_attestation_ref": custodian_attestation_ref,
        "generator_ref": TAW00_GENERATOR_REF,
        "generator_version": TAW00_GENERATOR_VERSION,
        "creation_order_evidence_ref": creation_order_evidence_ref,
        "private_manifest_digest_ref": f"sha256:{hashlib.sha256(canonical_manifest).hexdigest()}",
    }
    digest = hmac.new(
        secret_key,
        json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode(),
        hashlib.sha256,
    ).hexdigest()
    return HoldoutCommitment(
        cycle_ref=cycle_ref,
        custodian_ref=custodian_ref,
        commitment_digest=f"sha256:{digest}",
        creation_order_evidence_ref=creation_order_evidence_ref,
        custodian_attestation_ref=custodian_attestation_ref,
    )


def verify_holdout_commitment(
    commitment: HoldoutCommitment,
    *,
    secret_key: bytes,
    private_manifest: bytes,
) -> bool:
    try:
        expected = build_holdout_commitment(
            cycle_ref=commitment.cycle_ref,
            custodian_ref=commitment.custodian_ref,
            creation_order_evidence_ref=commitment.creation_order_evidence_ref,
            custodian_attestation_ref=commitment.custodian_attestation_ref,
            secret_key=secret_key,
            private_manifest=private_manifest,
        )
    except ValueError:
        return False
    return hmac.compare_digest(expected.commitment_digest, commitment.commitment_digest)
