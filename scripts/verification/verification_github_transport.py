from __future__ import annotations

import base64
import binascii
import hashlib
import json
import math
import re
import types
import zlib
from dataclasses import MISSING, dataclass, fields, is_dataclass, replace
from enum import Enum
from typing import Any, Union, get_args, get_origin, get_type_hints

from scripts.verification.verification_contracts import (
    VerificationPlan,
    VerificationReceipt,
    VerificationRunManifest,
    dependency_lock_set_fingerprint,
    dependency_state_fingerprint,
    verification_receipt_payload,
    verification_run_manifest_payload,
)


SCHEMA_VERSION = "uaa_verification_github_job_output.v1"
CONSTRUCTION_POSTURE = "repository_constructed_non_authoritative"
REDACTION_STATUS = "content_free_refs_hashes_counts_durations_and_unit_bindings_only"
CONTENT_REF_PREFIX = "github-job-output:"
PLAN_BINDING_SCHEMA_VERSION = "uaa_verification_github_plan_binding.v1"
PLAN_BINDING_REDACTION_STATUS = "content_free_refs_hashes_and_unit_bindings_only"

# GitHub job outputs are not an artifact store. Keep one envelope well below the
# platform output ceiling and reject high-entropy or unexpectedly expansive plans.
MAX_CANONICAL_BYTES = 512 * 1024
MAX_COMPRESSED_BYTES = 288 * 1024
MAX_ENCODED_CHARS = (MAX_COMPRESSED_BYTES * 4 + 2) // 3
MAX_JSON_DEPTH = 16
MAX_JSON_NODES = 32_768
MAX_STRING_CHARS = 2_048
MAX_INTEGER = (1 << 63) - 1

_BASE64URL_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
_WINDOWS_ABSOLUTE_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")
_SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)(?:authorization|cookie|password|passwd|secret|token|api[_-]?key)\s*[:=]"
)
_ENV_ASSIGNMENT_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{2,}=")
_RAW_LOG_PREFIXES = ("Traceback (most recent call last):", "stdout:", "stderr:")
_SAFE_REF_PATTERN = re.compile(r"^[a-z0-9][a-z0-9:._-]{0,191}$")
_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_ENVELOPE_FIELDS = frozenset(
    {
        "authorized",
        "callable",
        "gate_passed",
        "github_green",
        "merge_allowed",
        "merge_authorized",
        "required_checks_green",
    }
)


class VerificationGithubTransportError(ValueError):
    """A content-free, stable rejection from the GitHub output codec."""

    def __init__(self, reason_ref: str) -> None:
        self.reason_ref = reason_ref
        super().__init__(f"verification GitHub transport rejected ({reason_ref})")


def _fail(reason_ref: str) -> None:
    raise VerificationGithubTransportError(reason_ref)


@dataclass(frozen=True)
class VerificationGithubPlanBinding:
    """Compact exact-plan projection; selection booleans stay in the local plan."""

    schema_version: str
    repository_sha: str
    base_sha: str
    plan_fingerprint: str
    definition_fingerprint: str
    risk_manifest_fingerprint: str
    change_fingerprint: str
    verification_dag_fingerprint: str
    dependency_state_fingerprint: str
    dependency_lock_set_fingerprint: str
    platform_fingerprint: str
    command_manifest_fingerprint: str
    verifier_definition_fingerprint: str
    test_collection_fingerprint: str
    pytest_shard_plan_fingerprint: str
    typescript_project_fingerprint: str
    selected_unit_refs: tuple[str, ...]
    selected_unit_definition_fingerprints: tuple[tuple[str, str], ...]
    redaction_status: str

    def validate(self) -> None:
        if self.schema_version != PLAN_BINDING_SCHEMA_VERSION:
            _fail("reason-ref:github-transport:plan-binding-schema-invalid")
        if self.redaction_status != PLAN_BINDING_REDACTION_STATUS:
            _fail("reason-ref:github-transport:plan-binding-redaction-invalid")
        if (
            _SHA_PATTERN.fullmatch(self.repository_sha) is None
            or _SHA_PATTERN.fullmatch(self.base_sha) is None
        ):
            _fail("reason-ref:github-transport:plan-binding-sha-invalid")
        for digest in (
            self.plan_fingerprint,
            self.definition_fingerprint,
            self.risk_manifest_fingerprint,
            self.change_fingerprint,
            self.verification_dag_fingerprint,
            self.dependency_state_fingerprint,
            self.dependency_lock_set_fingerprint,
            self.platform_fingerprint,
            self.command_manifest_fingerprint,
            self.verifier_definition_fingerprint,
            self.test_collection_fingerprint,
            self.pytest_shard_plan_fingerprint,
            self.typescript_project_fingerprint,
        ):
            if _DIGEST_PATTERN.fullmatch(digest) is None:
                _fail("reason-ref:github-transport:plan-binding-digest-invalid")
        if not self.selected_unit_refs or len(self.selected_unit_refs) > 128:
            _fail("reason-ref:github-transport:plan-binding-membership-invalid")
        if len(self.selected_unit_refs) != len(set(self.selected_unit_refs)):
            _fail("reason-ref:github-transport:plan-binding-membership-invalid")
        for unit_ref in self.selected_unit_refs:
            if _SAFE_REF_PATTERN.fullmatch(unit_ref) is None:
                _fail("reason-ref:github-transport:plan-binding-membership-invalid")
        definition_refs: list[str] = []
        for unit_ref, digest in self.selected_unit_definition_fingerprints:
            if (
                _SAFE_REF_PATTERN.fullmatch(unit_ref) is None
                or _DIGEST_PATTERN.fullmatch(digest) is None
            ):
                _fail("reason-ref:github-transport:plan-binding-membership-invalid")
            definition_refs.append(unit_ref)
        if tuple(definition_refs) != self.selected_unit_refs:
            _fail("reason-ref:github-transport:plan-binding-membership-invalid")


@dataclass(frozen=True)
class VerificationGithubJobOutputEnvelope:
    schema_version: str
    construction_posture: str
    repository_sha: str
    plan_fingerprint: str
    plan_binding: VerificationGithubPlanBinding
    receipt: VerificationReceipt
    final_run_manifest: VerificationRunManifest | None
    redaction_status: str
    content_fingerprint: str
    content_ref: str

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            _fail("reason-ref:github-transport:schema-invalid")
        if self.construction_posture != CONSTRUCTION_POSTURE:
            _fail("reason-ref:github-transport:authority-posture-invalid")
        if self.redaction_status != REDACTION_STATUS:
            _fail("reason-ref:github-transport:redaction-posture-invalid")
        if (
            type(self.plan_binding) is not VerificationGithubPlanBinding
            or type(self.receipt) is not VerificationReceipt
        ):
            _fail("reason-ref:github-transport:contract-type-invalid")
        if (
            self.final_run_manifest is not None
            and type(self.final_run_manifest) is not VerificationRunManifest
        ):
            _fail("reason-ref:github-transport:contract-type-invalid")
        try:
            self.plan_binding.validate()
            self.receipt.validate()
            if self.final_run_manifest is not None:
                self.final_run_manifest.validate()
        except ValueError:
            _fail("reason-ref:github-transport:contract-invalid")
        if self.receipt.schema_version != "uaa_verification_receipt.v3":
            _fail("reason-ref:github-transport:receipt-version-invalid")
        if (
            self.repository_sha != self.plan_binding.repository_sha
            or self.plan_fingerprint != self.plan_binding.plan_fingerprint
        ):
            _fail("reason-ref:github-transport:plan-binding-mismatch")
        _validate_receipt_binding(self.plan_binding, self.receipt)
        if self.final_run_manifest is not None:
            _validate_run_binding(
                self.plan_binding,
                self.receipt,
                self.final_run_manifest,
            )
        expected_fingerprint = github_job_output_content_fingerprint(self)
        if self.content_fingerprint != expected_fingerprint:
            _fail("reason-ref:github-transport:content-fingerprint-mismatch")
        if self.content_ref != f"{CONTENT_REF_PREFIX}{expected_fingerprint}":
            _fail("reason-ref:github-transport:content-ref-mismatch")


def _validate_receipt_binding(
    plan_binding: VerificationGithubPlanBinding,
    receipt: VerificationReceipt,
) -> None:
    expected = (
        receipt.plan_fingerprint == plan_binding.plan_fingerprint,
        receipt.repository_sha == plan_binding.repository_sha,
        receipt.unit_ref in plan_binding.selected_unit_refs,
        receipt.dependency_state_fingerprint
        == plan_binding.dependency_state_fingerprint,
        receipt.dependency_lock_set_fingerprint
        == plan_binding.dependency_lock_set_fingerprint,
        receipt.platform_fingerprint == plan_binding.platform_fingerprint,
        receipt.command_manifest_fingerprint
        == plan_binding.command_manifest_fingerprint,
        receipt.verifier_definition_fingerprint
        == plan_binding.verifier_definition_fingerprint,
        receipt.test_collection_fingerprint == plan_binding.test_collection_fingerprint,
        receipt.pytest_shard_plan_fingerprint
        == plan_binding.pytest_shard_plan_fingerprint,
        receipt.execution_surface_ref == "surface-ref:github",
    )
    if not all(expected):
        _fail("reason-ref:github-transport:receipt-binding-mismatch")


def _validate_run_binding(
    plan_binding: VerificationGithubPlanBinding,
    receipt: VerificationReceipt,
    run_manifest: VerificationRunManifest,
) -> None:
    if run_manifest.schema_version != "uaa_verification_run.v3":
        _fail("reason-ref:github-transport:run-version-invalid")
    receipt_bindings = dict(run_manifest.unit_receipt_bindings)
    expected = (
        run_manifest.plan_fingerprint == plan_binding.plan_fingerprint,
        run_manifest.repository_sha == plan_binding.repository_sha,
        run_manifest.dependency_state_fingerprint
        == plan_binding.dependency_state_fingerprint,
        run_manifest.dependency_lock_set_fingerprint
        == plan_binding.dependency_lock_set_fingerprint,
        run_manifest.platform_fingerprint == plan_binding.platform_fingerprint,
        run_manifest.command_manifest_fingerprint
        == plan_binding.command_manifest_fingerprint,
        run_manifest.verifier_definition_fingerprint
        == plan_binding.verifier_definition_fingerprint,
        run_manifest.test_collection_fingerprint
        == plan_binding.test_collection_fingerprint,
        run_manifest.pytest_shard_plan_fingerprint
        == plan_binding.pytest_shard_plan_fingerprint,
        run_manifest.typescript_project_fingerprint
        == plan_binding.typescript_project_fingerprint,
        run_manifest.required_unit_refs == plan_binding.selected_unit_refs,
        run_manifest.execution_surface_ref == "surface-ref:github",
        receipt.receipt_ref in run_manifest.receipt_refs,
        receipt_bindings.get(receipt.unit_ref) == receipt.receipt_ref,
    )
    if not all(expected):
        _fail("reason-ref:github-transport:run-binding-mismatch")


def github_job_output_envelope_payload(
    envelope: VerificationGithubJobOutputEnvelope,
    *,
    include_content_identity: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": envelope.schema_version,
        "construction_posture": envelope.construction_posture,
        "repository_sha": envelope.repository_sha,
        "plan_fingerprint": envelope.plan_fingerprint,
        "plan_binding": _plan_binding_payload(envelope.plan_binding),
        "receipt": verification_receipt_payload(envelope.receipt),
        "final_run_manifest": (
            verification_run_manifest_payload(envelope.final_run_manifest)
            if envelope.final_run_manifest is not None
            else None
        ),
        "redaction_status": envelope.redaction_status,
    }
    if include_content_identity:
        payload["content_fingerprint"] = envelope.content_fingerprint
        payload["content_ref"] = envelope.content_ref
    return payload


def _plan_binding_payload(binding: VerificationGithubPlanBinding) -> dict[str, Any]:
    return {
        field.name: getattr(binding, field.name)
        for field in fields(VerificationGithubPlanBinding)
    }


def build_github_plan_binding(plan: VerificationPlan) -> VerificationGithubPlanBinding:
    try:
        plan.validate()
    except ValueError:
        _fail("reason-ref:github-transport:contract-invalid")
    if plan.schema_version not in {
        "uaa_ci_command_manifest.v4",
        "uaa_ci_command_manifest.v3",
        "uaa_verification_plan.v3",
    }:
        _fail("reason-ref:github-transport:plan-version-invalid")
    assert plan.verification_dag_fingerprint is not None
    binding = VerificationGithubPlanBinding(
        schema_version=PLAN_BINDING_SCHEMA_VERSION,
        repository_sha=plan.repository_sha,
        base_sha=plan.base_sha,
        plan_fingerprint=plan.plan_fingerprint,
        definition_fingerprint=plan.definition_fingerprint,
        risk_manifest_fingerprint=plan.risk_manifest_fingerprint,
        change_fingerprint=plan.change_fingerprint,
        verification_dag_fingerprint=plan.verification_dag_fingerprint,
        dependency_state_fingerprint=dependency_state_fingerprint(plan),
        dependency_lock_set_fingerprint=dependency_lock_set_fingerprint(plan),
        platform_fingerprint=plan.platform_fingerprint,
        command_manifest_fingerprint=plan.command_manifest_fingerprint,
        verifier_definition_fingerprint=plan.verifier_definition_fingerprint,
        test_collection_fingerprint=plan.test_collection_fingerprint,
        pytest_shard_plan_fingerprint=plan.pytest_shard_plan_fingerprint,
        typescript_project_fingerprint=plan.typescript_project_fingerprint,
        selected_unit_refs=plan.selected_unit_refs,
        selected_unit_definition_fingerprints=(
            plan.selected_unit_definition_fingerprints
        ),
        redaction_status=PLAN_BINDING_REDACTION_STATUS,
    )
    binding.validate()
    return binding


def _canonical_json(payload: Any) -> bytes:
    try:
        encoded = json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (RecursionError, TypeError, ValueError):
        _fail("reason-ref:github-transport:json-invalid")
    if not 0 < len(encoded) <= MAX_CANONICAL_BYTES:
        _fail("reason-ref:github-transport:canonical-size-invalid")
    return encoded


def github_job_output_content_fingerprint(
    envelope: VerificationGithubJobOutputEnvelope,
) -> str:
    return hashlib.sha256(
        _canonical_json(
            github_job_output_envelope_payload(
                envelope,
                include_content_identity=False,
            )
        )
    ).hexdigest()


def build_github_job_output_envelope(
    plan: VerificationPlan,
    receipt: VerificationReceipt,
    *,
    final_run_manifest: VerificationRunManifest | None = None,
) -> VerificationGithubJobOutputEnvelope:
    plan_binding = build_github_plan_binding(plan)
    envelope = VerificationGithubJobOutputEnvelope(
        schema_version=SCHEMA_VERSION,
        construction_posture=CONSTRUCTION_POSTURE,
        repository_sha=plan.repository_sha,
        plan_fingerprint=plan.plan_fingerprint,
        plan_binding=plan_binding,
        receipt=receipt,
        final_run_manifest=final_run_manifest,
        redaction_status=REDACTION_STATUS,
        content_fingerprint="0" * 64,
        content_ref=f"{CONTENT_REF_PREFIX}{'0' * 64}",
    )
    fingerprint = github_job_output_content_fingerprint(envelope)
    envelope = replace(
        envelope,
        content_fingerprint=fingerprint,
        content_ref=f"{CONTENT_REF_PREFIX}{fingerprint}",
    )
    envelope.validate()
    return envelope


def validate_github_job_output_against_plan(
    envelope: VerificationGithubJobOutputEnvelope,
    plan: VerificationPlan,
) -> None:
    """Reconstruct locally and require byte-equivalent exact plan bindings."""

    envelope.validate()
    if envelope.plan_binding != build_github_plan_binding(plan):
        _fail("reason-ref:github-transport:reconstructed-plan-mismatch")


def encode_github_job_output(envelope: VerificationGithubJobOutputEnvelope) -> str:
    if type(envelope) is not VerificationGithubJobOutputEnvelope:
        _fail("reason-ref:github-transport:envelope-type-invalid")
    envelope.validate()
    encoded = _canonical_json(github_job_output_envelope_payload(envelope))
    compressed = zlib.compress(encoded, level=9)
    if not 0 < len(compressed) <= MAX_COMPRESSED_BYTES:
        _fail("reason-ref:github-transport:compressed-size-invalid")
    output = base64.urlsafe_b64encode(compressed).rstrip(b"=").decode("ascii")
    if not 0 < len(output) <= MAX_ENCODED_CHARS:
        _fail("reason-ref:github-transport:encoded-size-invalid")
    return output


def _decode_base64url(value: str) -> bytes:
    if (
        not isinstance(value, str)
        or not 0 < len(value) <= MAX_ENCODED_CHARS
        or "=" in value
        or _BASE64URL_PATTERN.fullmatch(value) is None
    ):
        _fail("reason-ref:github-transport:encoding-invalid")
    padding = "=" * (-len(value) % 4)
    try:
        compressed = base64.b64decode(
            (value + padding).encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
    except (UnicodeEncodeError, binascii.Error, ValueError):
        _fail("reason-ref:github-transport:encoding-invalid")
    if base64.urlsafe_b64encode(compressed).rstrip(b"=").decode("ascii") != value:
        _fail("reason-ref:github-transport:encoding-not-canonical")
    if not 0 < len(compressed) <= MAX_COMPRESSED_BYTES:
        _fail("reason-ref:github-transport:compressed-size-invalid")
    return compressed


def _decompress_bounded(compressed: bytes) -> bytes:
    decoder = zlib.decompressobj()
    try:
        output = decoder.decompress(compressed, MAX_CANONICAL_BYTES + 1)
        if len(output) > MAX_CANONICAL_BYTES or decoder.unconsumed_tail:
            _fail("reason-ref:github-transport:decompression-bound-exceeded")
        remaining = MAX_CANONICAL_BYTES + 1 - len(output)
        output += decoder.flush(remaining)
    except VerificationGithubTransportError:
        raise
    except (MemoryError, zlib.error):
        _fail("reason-ref:github-transport:compression-invalid")
    if len(output) > MAX_CANONICAL_BYTES:
        _fail("reason-ref:github-transport:decompression-bound-exceeded")
    if not decoder.eof:
        _fail("reason-ref:github-transport:compression-truncated")
    if decoder.unused_data or decoder.unconsumed_tail:
        _fail("reason-ref:github-transport:compression-trailing-data")
    return output


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            _fail("reason-ref:github-transport:json-duplicate-field")
        output[key] = value
    return output


def _parse_integer(value: str) -> int:
    if len(value.lstrip("-")) > 19:
        _fail("reason-ref:github-transport:json-integer-invalid")
    parsed = int(value)
    if not -MAX_INTEGER <= parsed <= MAX_INTEGER:
        _fail("reason-ref:github-transport:json-integer-invalid")
    return parsed


def _parse_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        _fail("reason-ref:github-transport:json-number-nonfinite")
    return parsed


def _reject_nonfinite(_value: str) -> None:
    _fail("reason-ref:github-transport:json-number-nonfinite")


def _validate_tree(payload: Any) -> None:
    pending: list[tuple[Any, int]] = [(payload, 1)]
    observed = 0
    while pending:
        value, depth = pending.pop()
        observed += 1
        if observed > MAX_JSON_NODES:
            _fail("reason-ref:github-transport:json-node-bound-exceeded")
        if depth > MAX_JSON_DEPTH:
            _fail("reason-ref:github-transport:json-depth-bound-exceeded")
        if isinstance(value, dict):
            for key, item in value.items():
                if not isinstance(key, str) or len(key) > 128:
                    _fail("reason-ref:github-transport:json-field-invalid")
                pending.append((item, depth + 1))
        elif isinstance(value, list):
            pending.extend((item, depth + 1) for item in value)
        elif isinstance(value, str):
            if len(value) > MAX_STRING_CHARS:
                _fail("reason-ref:github-transport:string-bound-exceeded")
            _validate_content_free_string(value)
        elif isinstance(value, int):
            if isinstance(value, bool):
                continue
            if not -MAX_INTEGER <= value <= MAX_INTEGER:
                _fail("reason-ref:github-transport:json-integer-invalid")
        elif isinstance(value, float):
            if not math.isfinite(value):
                _fail("reason-ref:github-transport:json-number-nonfinite")
        elif value is not None and not isinstance(value, bool):
            _fail("reason-ref:github-transport:json-value-invalid")


def _validate_content_free_string(value: str) -> None:
    if (
        value.startswith(("/", "file://", "\\\\"))
        or _WINDOWS_ABSOLUTE_PATTERN.match(value) is not None
        or "-----BEGIN " in value
        or _SECRET_ASSIGNMENT_PATTERN.search(value) is not None
        or _ENV_ASSIGNMENT_PATTERN.match(value) is not None
        or value.startswith(_RAW_LOG_PREFIXES)
        or any(ord(character) < 0x20 for character in value)
    ):
        _fail("reason-ref:github-transport:redaction-boundary-violated")


def _decode_canonical_json(encoded: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(
            encoded,
            object_pairs_hook=_reject_duplicate_keys,
            parse_int=_parse_integer,
            parse_float=_parse_float,
            parse_constant=_reject_nonfinite,
        )
    except VerificationGithubTransportError:
        raise
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        TypeError,
        ValueError,
    ):
        _fail("reason-ref:github-transport:json-invalid")
    if not isinstance(payload, dict):
        _fail("reason-ref:github-transport:json-invalid")
    _validate_tree(payload)
    if _canonical_json(payload) != encoded:
        _fail("reason-ref:github-transport:json-not-canonical")
    return payload


def _coerce_json_value(value: Any, expected_type: Any) -> Any:
    if expected_type is Any:
        return value
    origin = get_origin(expected_type)
    arguments = get_args(expected_type)
    if origin in {Union, types.UnionType}:
        if value is None and type(None) in arguments:
            return None
        for candidate in arguments:
            if candidate is type(None):
                continue
            try:
                return _coerce_json_value(value, candidate)
            except (TypeError, ValueError):
                continue
        raise TypeError
    if origin is tuple:
        if not isinstance(value, list):
            raise TypeError
        if len(arguments) == 2 and arguments[1] is Ellipsis:
            return tuple(_coerce_json_value(item, arguments[0]) for item in value)
        if len(arguments) != len(value):
            raise TypeError
        return tuple(
            _coerce_json_value(item, item_type)
            for item, item_type in zip(value, arguments, strict=True)
        )
    if isinstance(expected_type, type) and issubclass(expected_type, Enum):
        if not isinstance(value, str):
            raise TypeError
        return expected_type(value)
    if expected_type is str:
        if not isinstance(value, str):
            raise TypeError
        return value
    if expected_type is bool:
        if not isinstance(value, bool):
            raise TypeError
        return value
    if expected_type is int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError
        return value
    if is_dataclass(expected_type):
        if not isinstance(value, dict):
            raise TypeError
        return _contract_from_payload(expected_type, value)
    if value is None and expected_type is type(None):
        return None
    if not isinstance(value, expected_type):
        raise TypeError
    return value


def _contract_from_payload(contract_type: type[Any], payload: dict[str, Any]) -> Any:
    contract_fields = {field.name: field for field in fields(contract_type)}
    required_fields = {
        field_name
        for field_name, field in contract_fields.items()
        if field.default is MISSING and field.default_factory is MISSING
    }
    payload_fields = set(payload)
    if (
        not required_fields.issubset(payload_fields)
        or payload_fields - set(contract_fields)
    ):
        _fail("reason-ref:github-transport:contract-fields-invalid")
    try:
        type_hints = get_type_hints(contract_type)
        values = {
            key: _coerce_json_value(value, type_hints[key])
            for key, value in payload.items()
        }
        contract = contract_type(**values)
        contract.validate()
    except VerificationGithubTransportError:
        raise
    except (KeyError, RecursionError, TypeError, ValueError):
        _fail("reason-ref:github-transport:contract-invalid")
    return contract


def _envelope_from_payload(
    payload: dict[str, Any],
) -> VerificationGithubJobOutputEnvelope:
    expected_fields = {
        field.name for field in fields(VerificationGithubJobOutputEnvelope)
    }
    if set(payload) != expected_fields:
        if _FORBIDDEN_ENVELOPE_FIELDS & set(payload):
            _fail("reason-ref:github-transport:gate-claim-forbidden")
        _fail("reason-ref:github-transport:envelope-fields-invalid")
    try:
        plan_binding = _contract_from_payload(
            VerificationGithubPlanBinding,
            payload["plan_binding"],
        )
        receipt = _contract_from_payload(VerificationReceipt, payload["receipt"])
        raw_run = payload["final_run_manifest"]
        run_manifest = (
            None
            if raw_run is None
            else _contract_from_payload(VerificationRunManifest, raw_run)
        )
        scalar_values = {
            key: payload[key]
            for key in (
                "schema_version",
                "construction_posture",
                "repository_sha",
                "plan_fingerprint",
                "redaction_status",
                "content_fingerprint",
                "content_ref",
            )
        }
        if not all(isinstance(value, str) for value in scalar_values.values()):
            raise TypeError
        envelope = VerificationGithubJobOutputEnvelope(
            **scalar_values,
            plan_binding=plan_binding,
            receipt=receipt,
            final_run_manifest=run_manifest,
        )
        envelope.validate()
    except VerificationGithubTransportError:
        raise
    except (KeyError, RecursionError, TypeError, ValueError):
        _fail("reason-ref:github-transport:envelope-invalid")
    return envelope


def decode_github_job_output(value: str) -> VerificationGithubJobOutputEnvelope:
    compressed = _decode_base64url(value)
    encoded = _decompress_bounded(compressed)
    payload = _decode_canonical_json(encoded)
    return _envelope_from_payload(payload)


__all__ = [
    "CONSTRUCTION_POSTURE",
    "MAX_CANONICAL_BYTES",
    "MAX_COMPRESSED_BYTES",
    "MAX_ENCODED_CHARS",
    "REDACTION_STATUS",
    "SCHEMA_VERSION",
    "VerificationGithubJobOutputEnvelope",
    "VerificationGithubPlanBinding",
    "VerificationGithubTransportError",
    "build_github_job_output_envelope",
    "build_github_plan_binding",
    "decode_github_job_output",
    "encode_github_job_output",
    "github_job_output_content_fingerprint",
    "github_job_output_envelope_payload",
    "validate_github_job_output_against_plan",
]
