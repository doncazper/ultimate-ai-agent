from __future__ import annotations

import base64
import hashlib
import json
import zlib
from dataclasses import replace

import pytest

from scripts.verification.verification_contracts import (
    VerificationPlan,
    VerificationReceipt,
    VerificationRiskTier,
    VerificationTerminalStatus,
    VerificationUnit,
    dependency_lock_set_fingerprint,
    dependency_state_fingerprint,
    verification_dag_definition_fingerprint,
    verification_plan_contract_fingerprint,
    verification_receipt_fingerprint,
    verification_unit_definition_fingerprint,
)
from scripts.verification.verification_execution_identity import (
    build_verification_execution_identity,
)
from scripts.verification.verification_github_transport import (
    CONSTRUCTION_POSTURE,
    MAX_CANONICAL_BYTES,
    VerificationGithubTransportError,
    build_github_job_output_envelope,
    decode_github_job_output,
    encode_github_job_output,
    github_job_output_envelope_payload,
    validate_github_job_output_against_plan,
)
from scripts.verification.verification_run_aggregator import (
    aggregate_verification_run,
)


SHA = "a" * 40
DIGEST = "b" * 64
SURFACE = "surface-ref:github"


def _unit() -> VerificationUnit:
    return VerificationUnit(
        unit_ref="unit:github-transport",
        display_name="GitHub transport",
        lane_ref="lane:github-transport",
        needs=(),
        command_refs=("command:github-transport",),
        proof_equivalence_ref="proof-equivalence:github-transport",
    )


def _plan(*, base_sha: str = SHA) -> VerificationPlan:
    unit = _unit()
    plan = VerificationPlan(
        schema_version="uaa_verification_plan.v3",
        profile_ref="profile:github-transport",
        repository_sha=SHA,
        definition_fingerprint=DIGEST,
        dependency_lock_fingerprints=(("uv.lock", DIGEST),),
        affected_path_classification="bounded_core",
        selected_lane_refs=(unit.lane_ref,),
        selected_command_refs=unit.command_refs,
        pytest_shard_plan_fingerprint=DIGEST,
        frontend_visual_scope="not_affected",
        redaction_status="content_free_refs_hashes_and_repo_paths_only",
        plan_fingerprint="0" * 64,
        base_sha=base_sha,
        risk_manifest_version="uaa_verification_risk_manifest.v1",
        risk_manifest_fingerprint=DIGEST,
        risk_tier=VerificationRiskTier.TIER_2,
        changed_path_refs=("scripts/verification/example.py",),
        change_fingerprint=DIGEST,
        escalation_reason_refs=(),
        selected_unit_refs=(unit.unit_ref,),
        selected_test_refs=(),
        audit_posture="not_required",
        full_pytest_required=False,
        typescript_typecheck_required=False,
        release_gate_required=False,
        platform_fingerprint=DIGEST,
        command_manifest_fingerprint=DIGEST,
        verifier_definition_fingerprint=DIGEST,
        test_collection_fingerprint=DIGEST,
        test_collection_posture="inventory_bound",
        typescript_project_fingerprint=DIGEST,
        typescript_project_posture="not_applicable",
        force_full=False,
        shadow_mode=False,
        verification_dag_fingerprint=verification_dag_definition_fingerprint((unit,)),
        selected_unit_definition_fingerprints=(
            (unit.unit_ref, verification_unit_definition_fingerprint(unit)),
        ),
    )
    return replace(plan, plan_fingerprint=verification_plan_contract_fingerprint(plan))


def _receipt(plan: VerificationPlan | None = None) -> VerificationReceipt:
    plan = plan or _plan()
    unit = _unit()
    result_ref = (
        f"result-ref:verification:{hashlib.sha256(unit.unit_ref.encode()).hexdigest()}"
    )
    receipt = VerificationReceipt(
        schema_version="uaa_verification_receipt.v4",
        receipt_ref=f"receipt:verification:{'0' * 64}",
        plan_fingerprint=plan.plan_fingerprint,
        unit_ref=unit.unit_ref,
        repository_sha=plan.repository_sha,
        dependency_state_fingerprint=dependency_state_fingerprint(plan),
        platform_fingerprint=plan.platform_fingerprint,
        command_manifest_fingerprint=plan.command_manifest_fingerprint,
        verifier_definition_fingerprint=plan.verifier_definition_fingerprint,
        test_collection_fingerprint=plan.test_collection_fingerprint,
        status=VerificationTerminalStatus.PASSED,
        started_at="2026-07-15T00:00:00Z",
        completed_at="2026-07-15T00:00:01Z",
        duration_ms=1_000,
        result_refs=(result_ref,),
        output_byte_count=0,
        output_digest=DIGEST,
        command_refs=unit.command_refs,
        command_result_bindings=((unit.command_refs[0], result_ref),),
        execution_surface_ref=SURFACE,
        proof_equivalence_ref=unit.proof_equivalence_ref,
        receipt_fingerprint="0" * 64,
        dependency_lock_set_fingerprint=dependency_lock_set_fingerprint(plan),
        pytest_shard_plan_fingerprint=plan.pytest_shard_plan_fingerprint,
        execution_identity_ref=build_verification_execution_identity(
            plan,
            unit,
            execution_surface_ref=SURFACE,
        ).identity_ref,
        executed_command_result_bindings=((unit.command_refs[0], result_ref),),
        observed_platform_fingerprint=DIGEST,
    )
    fingerprint = verification_receipt_fingerprint(receipt)
    return replace(
        receipt,
        receipt_ref=f"receipt:verification:{fingerprint}",
        receipt_fingerprint=fingerprint,
    )


def _envelope(*, include_run: bool = False):
    plan = _plan()
    receipt = _receipt(plan)
    run = None
    if include_run:
        run = aggregate_verification_run(
            plan,
            (_unit(),),
            (receipt,),
            execution_surface_ref=SURFACE,
        ).run_manifest
    return build_github_job_output_envelope(
        plan,
        receipt,
        final_run_manifest=run,
    )


def _encode_raw(raw: bytes) -> str:
    return base64.urlsafe_b64encode(zlib.compress(raw, level=9)).rstrip(b"=").decode()


def _encode_payload(payload: object, *, canonical: bool = True) -> str:
    raw = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":") if canonical else None,
        sort_keys=canonical,
    ).encode()
    return _encode_raw(raw)


def _payload(*, include_run: bool = False) -> dict[str, object]:
    return github_job_output_envelope_payload(_envelope(include_run=include_run))


def _assert_reason(encoded: str, reason_ref: str) -> None:
    with pytest.raises(VerificationGithubTransportError) as error:
        decode_github_job_output(encoded)
    assert error.value.reason_ref == reason_ref
    assert encoded not in str(error.value)


def test_round_trip_is_canonical_content_bound_and_non_authoritative() -> None:
    envelope = _envelope()
    encoded = encode_github_job_output(envelope)

    assert "=" not in encoded
    assert decode_github_job_output(encoded) == envelope
    assert envelope.construction_posture == CONSTRUCTION_POSTURE
    assert envelope.content_ref.endswith(envelope.content_fingerprint)
    payload = github_job_output_envelope_payload(envelope)
    assert "plan" not in payload
    assert "plan_binding" in payload
    assert payload["plan_binding"]["base_sha"] == SHA
    assert not any(
        isinstance(value, bool) for value in payload["plan_binding"].values()
    )
    assert not {
        "authorized",
        "gate_passed",
        "github_green",
        "merge_allowed",
    } & set(payload)


def test_consumer_must_reconstruct_the_exact_plan_locally() -> None:
    plan = _plan()
    envelope = build_github_job_output_envelope(plan, _receipt(plan))

    validate_github_job_output_against_plan(envelope, plan)

    changed = replace(plan, change_fingerprint="c" * 64, plan_fingerprint="0" * 64)
    changed = replace(
        changed,
        plan_fingerprint=verification_plan_contract_fingerprint(changed),
    )
    with pytest.raises(VerificationGithubTransportError) as error:
        validate_github_job_output_against_plan(envelope, changed)
    assert error.value.reason_ref == (
        "reason-ref:github-transport:reconstructed-plan-mismatch"
    )

    changed_base = _plan(base_sha="c" * 40)
    with pytest.raises(VerificationGithubTransportError) as base_error:
        validate_github_job_output_against_plan(envelope, changed_base)
    assert base_error.value.reason_ref == (
        "reason-ref:github-transport:reconstructed-plan-mismatch"
    )


def test_optional_final_run_manifest_is_exactly_bound() -> None:
    envelope = _envelope(include_run=True)

    decoded = decode_github_job_output(encode_github_job_output(envelope))

    assert decoded.final_run_manifest == envelope.final_run_manifest
    assert decoded.receipt.receipt_ref in decoded.final_run_manifest.receipt_refs


def test_builder_rejects_legacy_or_mismatched_contracts() -> None:
    plan = _plan()
    legacy = replace(
        plan,
        schema_version="uaa_verification_plan.v2",
        verification_dag_fingerprint=None,
        selected_unit_definition_fingerprints=(),
        plan_fingerprint="0" * 64,
    )
    legacy = replace(
        legacy,
        plan_fingerprint=verification_plan_contract_fingerprint(legacy),
    )
    with pytest.raises(VerificationGithubTransportError) as legacy_error:
        build_github_job_output_envelope(legacy, _receipt(plan))
    assert (
        legacy_error.value.reason_ref
        == "reason-ref:github-transport:plan-version-invalid"
    )

    changed_plan = replace(plan, repository_sha="c" * 40, plan_fingerprint="0" * 64)
    changed_plan = replace(
        changed_plan,
        plan_fingerprint=verification_plan_contract_fingerprint(changed_plan),
    )
    with pytest.raises(VerificationGithubTransportError) as mismatch_error:
        build_github_job_output_envelope(changed_plan, _receipt(plan))
    assert (
        mismatch_error.value.reason_ref
        == "reason-ref:github-transport:receipt-binding-mismatch"
    )


def test_builder_rejects_non_github_surface_and_unbound_final_run() -> None:
    plan = _plan()
    receipt = _receipt(plan)
    private_receipt = replace(
        receipt,
        execution_surface_ref="surface-ref:private",
        receipt_ref=f"receipt:verification:{'0' * 64}",
        receipt_fingerprint="0" * 64,
    )
    fingerprint = verification_receipt_fingerprint(private_receipt)
    private_receipt = replace(
        private_receipt,
        receipt_ref=f"receipt:verification:{fingerprint}",
        receipt_fingerprint=fingerprint,
    )
    with pytest.raises(VerificationGithubTransportError) as surface_error:
        build_github_job_output_envelope(plan, private_receipt)
    assert (
        surface_error.value.reason_ref
        == "reason-ref:github-transport:receipt-binding-mismatch"
    )

    other_receipt = _receipt(plan)
    run = aggregate_verification_run(
        plan,
        (_unit(),),
        (other_receipt,),
        execution_surface_ref=SURFACE,
    ).run_manifest
    mismatched_receipt = replace(
        receipt,
        output_digest="c" * 64,
        receipt_ref=f"receipt:verification:{'0' * 64}",
        receipt_fingerprint="0" * 64,
    )
    fingerprint = verification_receipt_fingerprint(mismatched_receipt)
    mismatched_receipt = replace(
        mismatched_receipt,
        receipt_ref=f"receipt:verification:{fingerprint}",
        receipt_fingerprint=fingerprint,
    )
    with pytest.raises(VerificationGithubTransportError) as run_error:
        build_github_job_output_envelope(
            plan,
            mismatched_receipt,
            final_run_manifest=run,
        )
    assert (
        run_error.value.reason_ref == "reason-ref:github-transport:run-binding-mismatch"
    )


@pytest.mark.parametrize("field", ["merge_allowed", "authorized", "gate_passed"])
def test_gate_or_authority_booleans_are_forbidden(field: str) -> None:
    payload = _payload()
    payload[field] = True
    _assert_reason(
        _encode_payload(payload),
        "reason-ref:github-transport:gate-claim-forbidden",
    )


def test_unknown_top_level_and_nested_fields_are_rejected() -> None:
    payload = _payload()
    payload["unknown_ref"] = "safe-ref:unknown"
    _assert_reason(
        _encode_payload(payload),
        "reason-ref:github-transport:envelope-fields-invalid",
    )

    payload = _payload()
    assert isinstance(payload["receipt"], dict)
    payload["receipt"]["unknown_ref"] = "safe-ref:unknown"
    _assert_reason(
        _encode_payload(payload),
        "reason-ref:github-transport:contract-fields-invalid",
    )

    payload = _payload()
    assert isinstance(payload["plan_binding"], dict)
    payload["plan_binding"]["release_gate_required"] = True
    _assert_reason(
        _encode_payload(payload),
        "reason-ref:github-transport:contract-fields-invalid",
    )


def test_duplicate_fields_are_rejected_at_every_depth() -> None:
    canonical = json.dumps(_payload(), separators=(",", ":"), sort_keys=True)
    duplicated = (
        canonical[:-1] + ',"schema_version":"uaa_verification_github_job_output.v1"}'
    )
    _assert_reason(
        _encode_raw(duplicated.encode()),
        "reason-ref:github-transport:json-duplicate-field",
    )

    marker = '"unit_ref":"unit:github-transport"'
    nested_duplicate = canonical.replace(marker, f"{marker},{marker}", 1)
    _assert_reason(
        _encode_raw(nested_duplicate.encode()),
        "reason-ref:github-transport:json-duplicate-field",
    )


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_numbers_are_rejected(constant: str) -> None:
    raw = b'{"value":' + constant.encode() + b"}"
    _assert_reason(
        _encode_raw(raw),
        "reason-ref:github-transport:json-number-nonfinite",
    )


def test_huge_integers_and_overdeep_trees_are_rejected() -> None:
    _assert_reason(
        _encode_raw(b'{"value":9223372036854775808}'),
        "reason-ref:github-transport:json-integer-invalid",
    )
    value: object = "leaf"
    for _ in range(20):
        value = [value]
    _assert_reason(
        _encode_payload({"nested": value}),
        "reason-ref:github-transport:json-depth-bound-exceeded",
    )


@pytest.mark.parametrize(
    "unsafe_value",
    [
        "/Users/operator/private.log",
        r"C:\\Users\\operator\\private.log",
        "TOKEN=not-transport-safe",
        "Traceback (most recent call last): raw failure",
        "authorization: bearer-value",
    ],
)
def test_absolute_paths_environment_secrets_and_raw_logs_are_rejected(
    unsafe_value: str,
) -> None:
    payload = _payload()
    payload["construction_posture"] = unsafe_value
    _assert_reason(
        _encode_payload(payload),
        "reason-ref:github-transport:redaction-boundary-violated",
    )


def test_padded_non_urlsafe_whitespace_and_noncanonical_json_are_rejected() -> None:
    encoded = encode_github_job_output(_envelope())
    _assert_reason(
        encoded + "=",
        "reason-ref:github-transport:encoding-invalid",
    )
    _assert_reason(
        encoded + "+",
        "reason-ref:github-transport:encoding-invalid",
    )
    _assert_reason(
        encoded + "\n",
        "reason-ref:github-transport:encoding-invalid",
    )
    _assert_reason(
        _encode_payload(_payload(), canonical=False),
        "reason-ref:github-transport:json-not-canonical",
    )


def test_truncated_and_trailing_zlib_streams_are_rejected() -> None:
    raw = json.dumps(_payload(), separators=(",", ":"), sort_keys=True).encode()
    compressed = zlib.compress(raw, level=9)
    truncated = base64.urlsafe_b64encode(compressed[:-2]).rstrip(b"=").decode()
    _assert_reason(
        truncated,
        "reason-ref:github-transport:compression-truncated",
    )

    concatenated = compressed + zlib.compress(b"{}", level=9)
    trailing = base64.urlsafe_b64encode(concatenated).rstrip(b"=").decode()
    _assert_reason(
        trailing,
        "reason-ref:github-transport:compression-trailing-data",
    )


def test_decompression_bomb_is_bounded_before_json_parsing() -> None:
    oversized = b"{" + b'"value":"' + (b"a" * MAX_CANONICAL_BYTES) + b'"}'
    encoded = _encode_raw(oversized)
    _assert_reason(
        encoded,
        "reason-ref:github-transport:decompression-bound-exceeded",
    )


def test_changed_content_identity_is_rejected() -> None:
    payload = _payload()
    payload["content_fingerprint"] = "c" * 64
    _assert_reason(
        _encode_payload(payload),
        "reason-ref:github-transport:content-fingerprint-mismatch",
    )

    payload = _payload()
    payload["content_ref"] = f"github-job-output:{'c' * 64}"
    _assert_reason(
        _encode_payload(payload),
        "reason-ref:github-transport:content-ref-mismatch",
    )


def test_changed_redaction_posture_is_rejected_before_use() -> None:
    payload = _payload()
    payload["redaction_status"] = "content_free_refs_hashes_and_repo_paths_only"
    _assert_reason(
        _encode_payload(payload),
        "reason-ref:github-transport:redaction-posture-invalid",
    )
