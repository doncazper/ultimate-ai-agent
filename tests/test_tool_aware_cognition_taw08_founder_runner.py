from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
from types import SimpleNamespace
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest

import ultimate_ai_agent.core.evals.tool_aware_acceptance as acceptance
from ultimate_ai_agent.core.authority.approval_validation import (
    AuthorityLeaseApprovalStore,
)
from ultimate_ai_agent.core.authority import (
    AuthorityActionRequest,
    AuthorityDecisionOutcome,
    evaluate_authority_request,
)
from ultimate_ai_agent.core.evals.tool_aware_acceptance import (
    FounderMeasurementKind,
    FounderPrivateAcceptanceEvidence,
    TAW08_FOUNDER_PROFILE_PATH_REF,
    _CandidateLockVerificationReceipt,
    _bind_evaluator_environment_receipt,
    _bind_foundation_gate_receipt,
)
from ultimate_ai_agent.core.evals.tool_aware_baseline import (
    CandidateLock,
    CandidateManifestEntry,
    canonical_digest,
    durable_payload_has_forbidden_fields,
)
from ultimate_ai_agent.core.local_model_management import FakeM164GatewayTransport
from ultimate_ai_agent.core.runtime_gateway import (
    LocalModelRuntimeAdapter,
    RuntimeGateway,
    RuntimeInvocationStore,
)
from tests.authority_helpers import provider_model_execute_authority_lease


RUNNER_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts/run_tool_aware_cognition_taw08_founder_acceptance.py"
)
RUNNER_SPEC = importlib.util.spec_from_file_location(
    "taw08_founder_runner", RUNNER_PATH
)
assert RUNNER_SPEC is not None and RUNNER_SPEC.loader is not None
runner = importlib.util.module_from_spec(RUNNER_SPEC)
sys.modules[RUNNER_SPEC.name] = runner
RUNNER_SPEC.loader.exec_module(runner)
REPOSITORY_ROOT = Path.cwd().resolve()
CORPUS_PATH = REPOSITORY_ROOT / runner.CORPUS_RELATIVE_PATH
LEASE_HELPER_PATH = (
    REPOSITORY_ROOT / "scripts/manage_tool_aware_cognition_taw08_live_lease.py"
)
LEASE_HELPER_SPEC = importlib.util.spec_from_file_location(
    "taw08_founder_runner_lease_helper_test", LEASE_HELPER_PATH
)
assert LEASE_HELPER_SPEC is not None and LEASE_HELPER_SPEC.loader is not None
lease_helper = importlib.util.module_from_spec(LEASE_HELPER_SPEC)
sys.modules[LEASE_HELPER_SPEC.name] = lease_helper
LEASE_HELPER_SPEC.loader.exec_module(lease_helper)


CANDIDATE_REVISION_REF = "git-sha:" + "4" * 40
MODEL_ARTIFACT_REF = "model-artifact-digest-ref:sha256:" + "5" * 64
HARDWARE_OBSERVATION_REF = "hardware-observation-ref:sha256:" + "6" * 64
RUN_REF = "run-ref:taw08:founder-runner-test"


def _candidate_lock() -> CandidateLock:
    entries = tuple(
        sorted(
            (
                CandidateManifestEntry(
                    path_ref=TAW08_FOUNDER_PROFILE_PATH_REF,
                    content_digest_ref="sha256:" + "7" * 64,
                ),
                CandidateManifestEntry(
                    path_ref=runner.CORPUS_PATH_REF,
                    content_digest_ref=f"sha256:{hashlib.sha256(CORPUS_PATH.read_bytes()).hexdigest()}",
                ),
                CandidateManifestEntry(
                    path_ref=runner.RUNNER_PATH_REF,
                    content_digest_ref=(
                        f"sha256:{hashlib.sha256(RUNNER_PATH.read_bytes()).hexdigest()}"
                    ),
                ),
                CandidateManifestEntry(
                    path_ref=runner.LEASE_HELPER_PATH_REF,
                    content_digest_ref=(
                        f"sha256:{hashlib.sha256(LEASE_HELPER_PATH.read_bytes()).hexdigest()}"
                    ),
                ),
            ),
            key=lambda item: item.path_ref,
        )
    )
    values = {
        "candidate_ref": "candidate-ref:taw08:founder-runner-test",
        "git_revision_ref": CANDIDATE_REVISION_REF,
        "entries": [item.model_dump(mode="json") for item in entries],
        "evidence_only_delta_path_refs": (
            "repo-path-ref:docs/evals/"
            "tool_aware_cognition_taw08_acceptance_report_v1.json",
        ),
    }
    return CandidateLock(
        candidate_ref=values["candidate_ref"],
        git_revision_ref=values["git_revision_ref"],
        entries=entries,
        manifest_digest_ref=canonical_digest(values),
        evidence_only_delta_path_refs=values["evidence_only_delta_path_refs"],
    )


def _model_artifact(tmp_path: Path) -> runner.LocalModelArtifactAttestation:
    tmp_path.mkdir(parents=True, exist_ok=True)
    artifact = tmp_path / runner.LOCAL_MODEL_ARTIFACT_FILENAME
    content = b"GGUF\x03\x00\x00\x00unit-test-qwen-artifact"
    artifact.write_bytes(content)
    artifact.chmod(0o600)
    original_size = runner.LOCAL_MODEL_ARTIFACT_BYTE_COUNT
    original_digest = runner.LOCAL_MODEL_ARTIFACT_SHA256
    try:
        runner.LOCAL_MODEL_ARTIFACT_BYTE_COUNT = len(content)
        runner.LOCAL_MODEL_ARTIFACT_SHA256 = hashlib.sha256(content).hexdigest()
        return runner.attest_local_model_artifact(artifact.resolve())
    finally:
        runner.LOCAL_MODEL_ARTIFACT_BYTE_COUNT = original_size
        runner.LOCAL_MODEL_ARTIFACT_SHA256 = original_digest


def _model_catalog() -> dict[str, object]:
    return {
        "models": [
            {
                "type": "llm",
                "key": runner.LOCAL_MODEL_CATALOG_KEY,
                "architecture": runner.LOCAL_MODEL_ARCHITECTURE,
                "format": runner.LOCAL_MODEL_FORMAT,
                "selected_variant": runner.LOCAL_MODEL_VARIANT,
                "max_context_length": 262_144,
                "quantization": {
                    "name": runner.LOCAL_MODEL_QUANTIZATION,
                    "bits_per_weight": 4,
                },
                "loaded_instances": [
                    {
                        "id": runner.LOCAL_MODEL_REF,
                        "config": {
                            "context_length": runner.LOCAL_MODEL_CONTEXT_LENGTH,
                            "parallel": 1,
                        },
                    }
                ],
            }
        ]
    }


def _foundation_receipt():
    environment = _bind_evaluator_environment_receipt(
        python_implementation="cpython",
        python_version="3.12.13",
        platform_system="darwin",
        platform_machine="arm64",
        python_executable_digest_ref="sha256:" + "1" * 64,
        python_standard_library_file_count=1,
        python_standard_library_digest_ref="sha256:" + "2" * 64,
        git_executable_digest_ref="sha256:" + "3" * 64,
        git_provenance_ref="git-provenance-ref:test-platform",
        installed_distribution_count=1,
        installed_distributions_digest_ref="sha256:" + "8" * 64,
        pyproject_digest_ref="sha256:" + "9" * 64,
        uv_lock_digest_ref="sha256:" + "a" * 64,
        lock_check_command_ref=(
            "command-ref:python-installed-distribution-lock-closure"
        ),
        independent_lock_closure_verified=True,
        locked_environment_verified=True,
        raw_content_persisted=False,
    )
    return _bind_foundation_gate_receipt(
        stage="exact_head",
        revision_ref=CANDIDATE_REVISION_REF,
        report_digest_ref="sha256:" + "b" * 64,
        report_ref="foundation-report-ref:taw08-runner-test",
        command_mode="report-only",
        evaluator_environment_receipt=environment,
        evaluator_environment_digest_ref=environment.receipt_digest_ref,
        passed=True,
        redacted=True,
        raw_content_persisted=False,
    )


def _candidate_verification_receipt(lock: CandidateLock):
    environment = _foundation_receipt().evaluator_environment_receipt
    payload = {
        "schema_version": "uaa-taw08-candidate-lock-verification.v1",
        "candidate_revision_ref": lock.git_revision_ref,
        "candidate_manifest_digest_ref": lock.manifest_digest_ref,
        "source_projection_digest_ref": "sha256:" + "c" * 64,
        "source_closure_digest_ref": "sha256:" + "d" * 64,
        "path_census_digest_ref": "sha256:" + "e" * 64,
        "repository_verifier_digest_ref": "sha256:" + "f" * 64,
        "executing_source_path_refs": (
            "repo-path-ref:scripts/verify_tool_aware_cognition_taw08.py",
        ),
        "executing_source_census_digest_ref": "sha256:" + "0" * 64,
        "evaluator_environment_receipt": environment,
        "evaluator_environment_digest_ref": environment.receipt_digest_ref,
        "verifier_ref": "verifier-ref:taw08:candidate-lock:v1",
        "verified": True,
    }
    return _CandidateLockVerificationReceipt(
        **payload,
        receipt_digest_ref=canonical_digest(
            {
                **payload,
                "evaluator_environment_receipt": environment.model_dump(mode="json"),
            }
        ),
    )


class _PassingProbe:
    def __init__(self) -> None:
        self.calls: list[tuple[FounderMeasurementKind, str, int, str]] = []

    def observe(
        self,
        *,
        measurement_kind: FounderMeasurementKind,
        stratum_ref: str,
        ordinal: int,
        phase: str,
    ) -> runner.FounderObservationOutcome:
        self.calls.append((measurement_kind, stratum_ref, ordinal, phase))
        suffix = stratum_ref.rsplit(":", 1)[-1]
        return runner.FounderObservationOutcome(
            success=True,
            evidence_ref=(
                f"evidence-ref:taw08:test:{measurement_kind.value}:"
                f"{suffix}:{phase}:{ordinal}"
            ),
            model_call_count=int(
                measurement_kind is FounderMeasurementKind.live_model_hardware
                or stratum_ref == "stratum-ref:taw08:chat"
            ),
        )


class _CountingGateway:
    def __init__(
        self,
        *,
        replayed: bool = False,
        response_byte_count: int | None = None,
    ) -> None:
        self.calls = 0
        self.replayed = replayed
        self.response_byte_count = response_byte_count

    def invoke_local_model(
        self,
        _request: object,
        *,
        idempotency_ref: str,
    ) -> SimpleNamespace:
        self.calls += 1
        metadata = SimpleNamespace(
            response_received=True,
            response_truncated=False,
            bounded_preview_returned=True,
            bounded_preview_persisted=False,
            tools_executed=False,
            memory_written=False,
            files_written=False,
            provider_called=False,
            remote_called=False,
            response_byte_count=(
                self.response_byte_count
                if self.response_byte_count is not None
                else len(runner.LOCAL_MODEL_SUCCESS_MARKER.encode("utf-8"))
            ),
        )
        receipt = SimpleNamespace(
            receipt_ref=f"receipt-ref:taw08:runner-test:{self.calls}",
            model_receipt_metadata=metadata,
            connector_write_performed=False,
            browser_automation_performed=False,
            model_call_performed=True,
            execution_performed=True,
        )
        policy = SimpleNamespace(
            allowed_to_execute=True,
            adapter_execution_enabled=True,
            model_call_enabled=True,
            command_execution_enabled=False,
            authority_decision_outcome="allow",
            authority_lease_ref="authority-lease-ref:test-provider-model-execute",
            authority_domain=runner.EXPECTED_AUTHORITY_DOMAIN.value,
            authority_capability=runner.EXPECTED_AUTHORITY_CAPABILITY.value,
            authority_required_mode=runner.EXPECTED_AUTHORITY_MODE.value,
            authority_known_authority=True,
            authority_unsupported_adapter=False,
            authority_decision_ref="decision-ref:taw08:runner-test",
            authority_audit_ref="audit-ref:taw08:runner-test",
            authority_policy_receipt_ref="receipt-ref:taw08:runner-test",
            authority_safe_disable_ref="safe-disable-ref:taw08:runner-test",
            authority_rollback_ref="rollback-ref:taw08:runner-test",
        )
        return SimpleNamespace(
            replayed=self.replayed,
            response_preview=runner.LOCAL_MODEL_SUCCESS_MARKER,
            error_category=None,
            record=SimpleNamespace(
                replay_count=int(self.replayed),
                receipt=receipt,
                policy_decision=policy,
                status="receipt_recorded",
                idempotency_ref=idempotency_ref,
            ),
        )


def _governed_probe(
    tmp_path: Path,
    *,
    gateway: object | None = None,
    catalog_reader=None,
) -> runner.GovernedLocalQwenProbe:
    return runner.GovernedLocalQwenProbe(
        candidate_lock=_candidate_lock(),
        run_ref="run-ref:taw08:full-runner-test",
        gateway=gateway or _CountingGateway(),  # type: ignore[arg-type]
        model_artifact=_model_artifact(tmp_path),
        authority_lease_ref="authority-lease-ref:test-provider-model-execute",
        authority_lease_posture_ref=("authority-lease-posture-ref:taw08:runner-test"),
        runner_source_posture_ref="runner-source-posture-ref:taw08:runner-test",
        corpus_path=CORPUS_PATH,
        catalog_reader=catalog_reader or _model_catalog,
    )


def _configure_founder_key(
    monkeypatch: pytest.MonkeyPatch,
) -> Ed25519PrivateKey:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    monkeypatch.setattr(
        acceptance,
        "TAW08_FOUNDER_DECISION_PUBLIC_KEY_HEX",
        public_key.hex(),
    )
    return private_key


def test_runner_builds_redacted_digest_bound_founder_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_key = _configure_founder_key(monkeypatch)
    probe = _PassingProbe()

    evidence = runner.collect_founder_private_evidence(
        candidate_lock=_candidate_lock(),
        exact_head_foundation_receipt=_foundation_receipt(),
        private_key=private_key,
        probe=probe,
        model_artifact_ref=MODEL_ARTIFACT_REF,
        backend_ref="backend-ref:lm-studio:qwen3-8-27b",
        hardware_family_ref="hardware-family-ref:mac",
        hardware_observation_ref=HARDWARE_OBSERVATION_REF,
    )

    assert len(probe.calls) == 624
    assert (
        FounderPrivateAcceptanceEvidence.model_validate(
            evidence.model_dump(mode="json")
        )
        == evidence
    )
    assert len(evidence.live_model_hardware_receipts) == 1
    live = evidence.live_model_hardware_receipts[0].result
    assert live.observation_count == 24
    assert live.same_host_baseline is not None
    assert live.same_host_baseline.observation_count == 24
    assert live.model_artifact_or_configuration_ref == MODEL_ARTIFACT_REF
    assert live.observed_hardware_ref == HARDWARE_OBSERVATION_REF
    payload = evidence.model_dump(mode="json")
    assert durable_payload_has_forbidden_fields(payload) is False
    rendered = json.dumps(payload, sort_keys=True)
    assert "private-key" not in rendered
    assert "/Users/" not in rendered
    assert "hostname" not in rendered


def test_governed_probe_uses_one_local_call_and_persists_metadata_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("UAA_LLAMA_CPP_BASE_URL", runner.LOCAL_MODEL_BASE_URL)
    monkeypatch.setenv("UAA_LLAMA_CPP_MODEL_ID", runner.LOCAL_MODEL_REF)
    store = RuntimeInvocationStore(
        tmp_path,
        active_authority_leases=[provider_model_execute_authority_lease()],
    )
    gateway = RuntimeGateway(
        store=store,
        local_model_adapter=LocalModelRuntimeAdapter(
            transport_factory=lambda _request: FakeM164GatewayTransport(
                runner.LOCAL_MODEL_SUCCESS_MARKER
            )
        ),
        local_model_runtime_enabled=True,
    )
    model_artifact = _model_artifact(tmp_path)
    probe = runner.GovernedLocalQwenProbe(
        candidate_lock=_candidate_lock(),
        run_ref="run-ref:taw08:runner-test",
        gateway=gateway,
        model_artifact=model_artifact,
        authority_lease_ref="authority-lease-ref:test-provider-model-execute",
        authority_lease_posture_ref=("authority-lease-posture-ref:taw08:runner-test"),
        runner_source_posture_ref="runner-source-posture-ref:taw08:runner-test",
        corpus_path=CORPUS_PATH,
        catalog_reader=_model_catalog,
    )

    outcome = probe.observe(
        measurement_kind=FounderMeasurementKind.live_model_hardware,
        stratum_ref="stratum-ref:taw08:live-model-response",
        ordinal=0,
        phase="candidate",
    )
    chat_outcome = probe.observe(
        measurement_kind=FounderMeasurementKind.end_to_end_journey,
        stratum_ref="stratum-ref:taw08:chat",
        ordinal=0,
        phase="candidate",
    )
    direct_outcome = probe.observe(
        measurement_kind=FounderMeasurementKind.response_scoring,
        stratum_ref="stratum-ref:taw08:direct-chat",
        ordinal=0,
        phase="candidate",
    )

    assert outcome.success is True
    assert outcome.model_call_count == 1
    assert chat_outcome == outcome
    assert direct_outcome.success is True
    assert direct_outcome.model_call_count == 0
    assert direct_outcome.evidence_ref != outcome.evidence_ref
    entries = store.list_entries()
    completed = [
        item.record.receipt
        for item in entries
        if item.record.receipt is not None
        and item.record.receipt.model_receipt_metadata is not None
        and item.record.receipt.model_receipt_metadata.response_received
    ]
    assert len(completed) == 1
    assert completed[0].model_call_performed is True
    metadata = completed[0].model_receipt_metadata
    assert metadata is not None
    assert metadata.provider_called is False
    assert metadata.remote_called is False
    assert metadata.tools_executed is False
    persisted = (tmp_path / "runtime_gateway_invocations.jsonl").read_text(
        encoding="utf-8"
    )
    assert runner.LOCAL_MODEL_SUCCESS_MARKER not in persisted
    assert "/no_think" not in persisted
    assert "raw_prompt" not in persisted
    assert "provider_payload" not in persisted


def test_governed_probe_rejects_non_loopback_and_model_substitution() -> None:
    lock = _candidate_lock()
    common = {
        "candidate_lock": lock,
        "run_ref": "run-ref:taw08:runner-test",
        "gateway": object(),
        "model_artifact": object(),
        "authority_lease_ref": "authority-lease-ref:test-provider-model-execute",
        "authority_lease_posture_ref": (
            "authority-lease-posture-ref:taw08:runner-test"
        ),
        "runner_source_posture_ref": ("runner-source-posture-ref:taw08:runner-test"),
        "corpus_path": CORPUS_PATH,
    }
    with pytest.raises(ValueError, match="loopback"):
        runner.GovernedLocalQwenProbe(
            **common,  # type: ignore[arg-type]
            base_url="https://example.invalid",
            catalog_reader=_model_catalog,
        )
    with pytest.raises(ValueError, match="accepted local model alias"):
        runner.GovernedLocalQwenProbe(
            **common,  # type: ignore[arg-type]
            model_ref="another-model",
            catalog_reader=_model_catalog,
        )


def test_governed_probe_rejects_marker_preview_with_trailing_response_bytes(
    tmp_path: Path,
) -> None:
    marker_bytes = len(runner.LOCAL_MODEL_SUCCESS_MARKER.encode("utf-8"))
    probe = _governed_probe(
        tmp_path,
        gateway=_CountingGateway(response_byte_count=marker_bytes + 1),
    )

    outcome = probe.observe(
        measurement_kind=FounderMeasurementKind.live_model_hardware,
        stratum_ref="stratum-ref:taw08:live-model-response",
        ordinal=0,
        phase="candidate",
    )

    assert outcome.success is False
    assert outcome.model_call_count == 1


def test_structural_probe_replays_every_non_model_stratum(tmp_path: Path) -> None:
    class _NoModelGateway:
        def invoke_local_model(self, *_args: object, **_kwargs: object) -> None:
            raise AssertionError("structural replay must not call a model")

    probe = runner.GovernedLocalQwenProbe(
        candidate_lock=_candidate_lock(),
        run_ref="run-ref:taw08:structural-test",
        gateway=_NoModelGateway(),  # type: ignore[arg-type]
        model_artifact=_model_artifact(tmp_path),
        authority_lease_ref="authority-lease-ref:test-provider-model-execute",
        authority_lease_posture_ref=("authority-lease-posture-ref:taw08:runner-test"),
        runner_source_posture_ref="runner-source-posture-ref:taw08:runner-test",
        corpus_path=CORPUS_PATH,
        catalog_reader=_model_catalog,
    )
    structural_specs = (
        *acceptance.TAW08_FOUNDER_MEASUREMENT_SPECS[
            FounderMeasurementKind.stale_cache_recovery
        ],
        *acceptance.TAW08_FOUNDER_MEASUREMENT_SPECS[
            FounderMeasurementKind.routing_confidence
        ],
        *tuple(
            item
            for item in acceptance.TAW08_FOUNDER_MEASUREMENT_SPECS[
                FounderMeasurementKind.end_to_end_journey
            ]
            if item[0] != "stratum-ref:taw08:chat"
        ),
    )

    outcomes = tuple(
        probe.observe(
            measurement_kind=(
                FounderMeasurementKind.stale_cache_recovery
                if spec[0].startswith("stratum-ref:taw08:cache-")
                else FounderMeasurementKind.routing_confidence
                if spec
                in acceptance.TAW08_FOUNDER_MEASUREMENT_SPECS[
                    FounderMeasurementKind.routing_confidence
                ]
                else FounderMeasurementKind.end_to_end_journey
            ),
            stratum_ref=spec[0],
            ordinal=ordinal,
            phase="candidate",
        )
        for spec in structural_specs
        for ordinal in range(24)
    )

    assert len(outcomes) == 360
    assert all(item.success for item in outcomes)
    assert all(item.model_call_count == 0 for item in outcomes)


def test_response_strata_use_all_frozen_cases_and_all_injection_fields(
    tmp_path: Path,
) -> None:
    probe = _governed_probe(tmp_path)
    expected_case_refs = tuple(item.case_ref for item in probe._corpus.cases)
    assert len(expected_case_refs) == len(set(expected_case_refs)) == 24

    for stratum_ref, *_rest in acceptance.TAW08_FOUNDER_MEASUREMENT_SPECS[
        FounderMeasurementKind.response_scoring
    ]:
        observed = tuple(
            probe._response_case(ordinal)[0].case_ref for ordinal in range(24)
        )
        assert observed == expected_case_refs, stratum_ref

    injection_fields: list[str] = []
    context_refs: list[str] = []
    for ordinal in range(24):
        case, _payload = probe._response_case(ordinal)
        context, field, rendering_ref, context_ref = probe._untrusted_catalog_context(
            case
        )
        if field is None:
            assert context == ""
            assert rendering_ref is None
            continue
        injection_fields.append(field)
        context_refs.append(context_ref)
        assert "UAA_UNTRUSTED_CAPABILITY_DATA_BEGIN" in context
        assert "UAA_UNTRUSTED_CAPABILITY_DATA_END" in context
        assert case.case_ref in context
        assert field in context
        assert rendering_ref in context
        assert "ignore prior" in context.lower() or "ignore-prior" in context.lower()
    assert tuple(sorted(injection_fields)) == tuple(
        sorted(runner.TAW04_CATALOG_INJECTION_FIELD_PATHS)
    )
    assert len(context_refs) == len(set(context_refs)) == 15


def test_full_founder_collection_makes_exactly_216_fresh_model_calls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_key = _configure_founder_key(monkeypatch)
    gateway = _CountingGateway()
    probe = _governed_probe(tmp_path, gateway=gateway)

    evidence = runner.collect_founder_private_evidence(
        candidate_lock=_candidate_lock(),
        exact_head_foundation_receipt=_foundation_receipt(),
        private_key=private_key,
        probe=probe,
        model_artifact_ref=probe._model_artifact.digest_ref,
        backend_ref=runner.LOCAL_MODEL_BACKEND_REF,
        hardware_family_ref="hardware-family-ref:mac",
        hardware_observation_ref=HARDWARE_OBSERVATION_REF,
    )

    assert gateway.calls == 216
    assert evidence.founder_decision_ref == runner.FOUNDER_DECISION_REF


def test_live_reuse_requires_source_observation_and_replay_fails_closed(
    tmp_path: Path,
) -> None:
    probe = _governed_probe(tmp_path)
    with pytest.raises(ValueError, match="bound live observation"):
        probe.observe(
            measurement_kind=FounderMeasurementKind.response_scoring,
            stratum_ref="stratum-ref:taw08:direct-chat",
            ordinal=0,
            phase="candidate",
        )
    with pytest.raises(ValueError, match="bound live observation"):
        probe.observe(
            measurement_kind=FounderMeasurementKind.end_to_end_journey,
            stratum_ref="stratum-ref:taw08:chat",
            ordinal=0,
            phase="candidate",
        )

    replayed = _governed_probe(
        tmp_path / "replayed", gateway=_CountingGateway(replayed=True)
    )
    with pytest.raises(ValueError, match="fresh non-replayed"):
        replayed.observe(
            measurement_kind=FounderMeasurementKind.live_model_hardware,
            stratum_ref="stratum-ref:taw08:live-model-response",
            ordinal=0,
            phase="baseline",
        )


def test_artifact_and_loaded_model_posture_reject_substitution(
    tmp_path: Path,
) -> None:
    artifact = _model_artifact(tmp_path)
    assert runner.validate_loaded_model_catalog(
        _model_catalog(), artifact=artifact
    ).posture_ref.startswith("model-server-posture-ref:taw08:")

    substituted = _model_catalog()
    model = substituted["models"][0]
    assert isinstance(model, dict)
    model["selected_variant"] = "qwen/qwen3.8-27b@q6_k"
    with pytest.raises(ValueError, match="metadata drifted"):
        runner.validate_loaded_model_catalog(substituted, artifact=artifact)

    additional = _model_catalog()
    models = additional["models"]
    assert isinstance(models, list)
    models.append(
        {
            "key": "another/model",
            "loaded_instances": [{"id": "another-model"}],
        }
    )
    with pytest.raises(ValueError, match="load census"):
        runner.validate_loaded_model_catalog(additional, artifact=artifact)

    artifact.path.write_bytes(b"substituted-model-bytes")
    with pytest.raises(ValueError, match="changed during the run"):
        artifact.verify_unchanged()


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS extended ACL semantics")
def test_model_artifact_attestation_and_recheck_reject_extended_acl(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = _model_artifact(tmp_path)
    content = artifact.path.read_bytes()
    monkeypatch.setattr(runner, "LOCAL_MODEL_ARTIFACT_BYTE_COUNT", len(content))
    monkeypatch.setattr(
        runner,
        "LOCAL_MODEL_ARTIFACT_SHA256",
        hashlib.sha256(content).hexdigest(),
    )
    try:
        subprocess.run(
            ("/bin/chmod", "+a", "everyone allow write", str(artifact.path)),
            check=True,
            capture_output=True,
        )
        with pytest.raises(ValueError, match="extended ACL"):
            artifact.verify_unchanged()
        with pytest.raises(ValueError, match="extended ACL"):
            runner.attest_local_model_artifact(artifact.path)
    finally:
        subprocess.run(
            ("/bin/chmod", "-N", str(artifact.path)),
            check=False,
            capture_output=True,
        )


def test_model_artifact_size_is_rejected_before_hash_traversal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = tmp_path / runner.LOCAL_MODEL_ARTIFACT_FILENAME
    content = b"GGUF\x03\x00\x00\x00bounded-model-artifact"
    artifact.write_bytes(content)
    artifact.chmod(0o600)
    reads = 0
    real_read = runner.os.read

    def counted_read(descriptor: int, size: int) -> bytes:
        nonlocal reads
        reads += 1
        return real_read(descriptor, size)

    monkeypatch.setattr(runner.os, "read", counted_read)
    monkeypatch.setattr(runner, "LOCAL_MODEL_ARTIFACT_BYTE_COUNT", len(content) - 1)
    with pytest.raises(ValueError, match="provenance is invalid"):
        runner.attest_local_model_artifact(artifact.resolve())
    assert reads == 0

    monkeypatch.setattr(runner, "LOCAL_MODEL_ARTIFACT_BYTE_COUNT", len(content))
    monkeypatch.setattr(
        runner,
        "LOCAL_MODEL_ARTIFACT_SHA256",
        hashlib.sha256(content).hexdigest(),
    )
    attestation = runner.attest_local_model_artifact(artifact.resolve())
    assert attestation.byte_count == len(content)
    assert reads > 0


def test_executing_runner_and_raw_response_identity_are_exact() -> None:
    posture_ref = runner.verify_executing_runner_source(
        _candidate_lock(), candidate_repository=REPOSITORY_ROOT
    )
    assert posture_ref.startswith("runner-source-posture-ref:taw08:")

    transport = object.__new__(runner.ExactQwenIdentityTransport)
    transport._inner = SimpleNamespace(
        chat_completions=lambda *_args, **_kwargs: {
            "model": runner.LOCAL_MODEL_RESPONSE_IDENTITY,
            "system_fingerprint": "substituted-model",
        }
    )
    with pytest.raises(ValueError, match="response identity"):
        transport.chat_completions(object(), object())

    transport._inner = SimpleNamespace(
        chat_completions=lambda *_args, **_kwargs: {
            "model": runner.LOCAL_MODEL_REF,
            "system_fingerprint": runner.LOCAL_MODEL_REF,
        }
    )
    assert transport.chat_completions(object(), object())["model"] == (
        runner.LOCAL_MODEL_REF
    )


def test_artifact_attestation_rejects_a_different_gguf_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = tmp_path / runner.LOCAL_MODEL_ARTIFACT_FILENAME
    content = b"GGUF\x03\x00\x00\x00different-model"
    artifact.write_bytes(content)
    artifact.chmod(0o600)
    monkeypatch.setattr(runner, "LOCAL_MODEL_ARTIFACT_BYTE_COUNT", len(content))
    monkeypatch.setattr(runner, "LOCAL_MODEL_ARTIFACT_SHA256", "0" * 64)

    with pytest.raises(ValueError, match="accepted GGUF"):
        runner.attest_local_model_artifact(artifact.resolve())


def test_runner_accepts_only_the_candidate_bound_helper_lease_and_receipt(
    tmp_path: Path,
) -> None:
    lock = _candidate_lock()
    authority_state = tmp_path / "authority"
    runtime_state = tmp_path / "runtime"
    authority_state.mkdir(mode=0o700)
    runtime_state.mkdir(mode=0o700)
    issued = lease_helper.issue_live_lease(
        state_dir=authority_state.resolve(),
        idempotency_ref="idempotency-ref:taw08-runner-lease-integration",
        candidate_revision_ref=lock.git_revision_ref,
        candidate_manifest_digest_ref=lock.manifest_digest_ref,
        run_ref=RUN_REF,
    )
    expected_constraints = runner.expected_live_lease_constraints(
        lock,
        run_ref=RUN_REF,
    )
    store = runner.ExactLeaseRuntimeInvocationStore(
        runtime_state.resolve(),
        authority_state_dir=authority_state.resolve(),
        expected_lease_ref=str(issued["lease_ref"]),
        expected_constraints=expected_constraints,
    )
    assert store.lease_posture_ref.startswith("authority-lease-posture-ref:taw08:")
    assert len(store.current_authority_leases()) == 1
    lease = store.current_authority_leases()[0]
    exact_decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="action-ref:taw08:exact-run",
            domain=runner.EXPECTED_AUTHORITY_DOMAIN,
            capability=runner.EXPECTED_AUTHORITY_CAPABILITY,
            safe_summary="Exercise the exact founder acceptance run.",
            resource_refs=sorted(
                [
                    RUN_REF,
                    runner.runtime_local_model_endpoint_ref(
                        runner.LOCAL_MODEL_BASE_URL
                    ),
                    runner.runtime_local_model_model_ref(runner.LOCAL_MODEL_REF),
                ]
            ),
            requested_mode=runner.EXPECTED_AUTHORITY_MODE,
        ),
        [lease],
    )
    unrelated_decision = evaluate_authority_request(
        AuthorityActionRequest(
            action_ref="action-ref:taw08:unrelated-run",
            domain=runner.EXPECTED_AUTHORITY_DOMAIN,
            capability=runner.EXPECTED_AUTHORITY_CAPABILITY,
            safe_summary="Attempt a different local model run.",
            resource_refs=["run-ref:taw08:unrelated"],
            requested_mode=runner.EXPECTED_AUTHORITY_MODE,
        ),
        [lease],
    )
    assert exact_decision.outcome == AuthorityDecisionOutcome.allow.value
    assert unrelated_decision.outcome != AuthorityDecisionOutcome.allow.value

    substituted = dict(expected_constraints)
    substituted["candidate_manifest_digest_ref"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="exact live authority lease"):
        runner.validate_exact_live_lease(
            runner.AuthorityLeaseStore(authority_state).get_lease(
                str(issued["lease_ref"])
            ),
            expected_lease_ref=str(issued["lease_ref"]),
            expected_constraints=substituted,
        )

    AuthorityLeaseApprovalStore(authority_state).records_path.unlink()
    with pytest.raises(ValueError, match="exact live authority approval"):
        store.current_authority_leases()


def test_private_key_loader_requires_absolute_owner_only_raw_key(
    tmp_path: Path,
) -> None:
    private_key = Ed25519PrivateKey.generate()
    raw = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    path = tmp_path / "founder.raw"
    path.write_bytes(raw)
    path.chmod(0o600)

    loaded = runner.load_founder_private_key(path)

    assert (
        loaded.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        == raw
    )
    path.chmod(0o644)
    with pytest.raises(ValueError, match="unsafe|owner-only"):
        runner.load_founder_private_key(path)
    with pytest.raises(ValueError, match="unsafe|owner-only"):
        runner.load_hardware_attestation_key(path)


def test_hardware_key_loader_rejects_path_substitution_during_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    key_dir = tmp_path / "keys"
    key_dir.mkdir(mode=0o700)
    target = key_dir / "hardware.raw"
    replacement = key_dir / "replacement.raw"
    target.write_bytes(b"a" * 32)
    replacement.write_bytes(b"b" * 32)
    target.chmod(0o600)
    replacement.chmod(0o600)
    original_open = os.open
    swapped = False

    def substituting_open(path: object, flags: int, *args: object, **kwargs: object):
        nonlocal swapped
        if Path(path) == target and not swapped:
            swapped = True
            target.rename(key_dir / "original.raw")
            replacement.rename(target)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", substituting_open)
    with pytest.raises(ValueError, match="changed during inspection"):
        runner.load_hardware_attestation_key(target.resolve())


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS extended ACL semantics")
def test_private_key_and_parent_reject_extended_acl(tmp_path: Path) -> None:
    key_dir = tmp_path / "keys"
    key_dir.mkdir(mode=0o700)
    key = key_dir / "founder.raw"
    key.write_bytes(b"k" * 32)
    key.chmod(0o600)
    try:
        subprocess.run(
            ("/bin/chmod", "+a", "everyone allow read", str(key)),
            check=True,
            capture_output=True,
        )
        with pytest.raises(ValueError, match="extended ACL"):
            runner.load_founder_private_key(key.resolve())
    finally:
        subprocess.run(
            ("/bin/chmod", "-N", str(key)),
            check=False,
            capture_output=True,
        )
    try:
        subprocess.run(
            ("/bin/chmod", "+a", "everyone allow read", str(key_dir)),
            check=True,
            capture_output=True,
        )
        with pytest.raises(ValueError, match="extended ACL"):
            runner.load_founder_private_key(key.resolve())
    finally:
        subprocess.run(
            ("/bin/chmod", "-N", str(key_dir)),
            check=False,
            capture_output=True,
        )


def test_private_output_is_mode_0600_even_with_process_umask_022(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir(mode=0o700)
    output = output_dir / "founder-evidence.json"
    prior_umask = os.umask(0o022)
    try:
        runner._write_private_output(output.resolve(), b'{"safe":true}\n')
    finally:
        os.umask(prior_umask)

    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    assert output.read_bytes() == b'{"safe":true}\n'
    with pytest.raises(ValueError, match="output path is invalid"):
        runner._write_private_output(output.resolve(), b'{"safe":true}\n')


def test_private_output_rejects_unverifiable_access_controls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir(mode=0o700)
    output = output_dir / "founder-evidence.json"
    monkeypatch.setattr(
        runner,
        "require_no_extended_acl_fd",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ValueError("founder evidence output access controls cannot be verified")
        ),
    )
    with pytest.raises(ValueError, match="cannot be verified"):
        runner._write_private_output(output.resolve(), b'{"safe":true}\n')
    assert not output.exists()


def test_hardware_observation_is_keyed_opaque_and_os_bound() -> None:
    first = runner.derive_hardware_observation_ref(
        attestation_key=b"h" * 32,
        hardware_family_ref="hardware-family-ref:mac",
        candidate_lock=_candidate_lock(),
        run_ref="run-ref:taw08:hardware-test",
        observed_system="Darwin",
        observed_machine="arm64",
        observed_node="transient-node-value",
    )
    second = runner.derive_hardware_observation_ref(
        attestation_key=b"i" * 32,
        hardware_family_ref="hardware-family-ref:mac",
        candidate_lock=_candidate_lock(),
        run_ref="run-ref:taw08:hardware-test",
        observed_system="Darwin",
        observed_machine="arm64",
        observed_node="transient-node-value",
    )

    assert first.startswith("hardware-observation-ref:sha256:")
    assert first != second
    assert "transient-node-value" not in first
    with pytest.raises(ValueError, match="observed OS"):
        runner.derive_hardware_observation_ref(
            attestation_key=b"h" * 32,
            hardware_family_ref="hardware-family-ref:windows",
            candidate_lock=_candidate_lock(),
            run_ref="run-ref:taw08:hardware-test",
            observed_system="Darwin",
            observed_machine="arm64",
            observed_node="transient-node-value",
        )


def _founder_inputs_bundle() -> dict[str, object]:
    lock = _candidate_lock()
    candidate_receipt = _candidate_verification_receipt(lock)
    foundation_receipt = _foundation_receipt()
    payload = {
        "schema_version": "uaa-taw08-founder-run-inputs.v1",
        "candidate_lock": lock.model_dump(mode="json"),
        "candidate_verification_receipt": candidate_receipt.model_dump(mode="json"),
        "exact_head_foundation_receipt": foundation_receipt.model_dump(mode="json"),
        "raw_content_persisted": False,
    }
    return {**payload, "bundle_digest_ref": canonical_digest(payload)}


def test_export_bundle_loader_binds_candidate_and_receipts() -> None:
    bundle = _founder_inputs_bundle()

    loaded_lock, loaded_foundation = runner._load_founder_inputs_bundle(
        json.dumps(bundle).encode("utf-8")
    )

    assert loaded_lock == _candidate_lock()
    assert loaded_foundation == _foundation_receipt()
    bundle["bundle_digest_ref"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="digest binding drift"):
        runner._load_founder_inputs_bundle(json.dumps(bundle).encode("utf-8"))


def test_foundation_provenance_ignores_only_fresh_report_identity() -> None:
    first = _foundation_receipt()
    fresh_report = _bind_foundation_gate_receipt(
        stage=first.stage,
        revision_ref=first.revision_ref,
        report_digest_ref="sha256:" + "c" * 64,
        report_ref="foundation-report-ref:taw08-fresh-rerun",
        command_mode=first.command_mode,
        evaluator_environment_receipt=first.evaluator_environment_receipt,
        evaluator_environment_digest_ref=first.evaluator_environment_digest_ref,
        passed=first.passed,
        redacted=first.redacted,
        raw_content_persisted=first.raw_content_persisted,
    )
    stable_drift = _bind_foundation_gate_receipt(
        stage=first.stage,
        revision_ref="git-sha:" + "f" * 40,
        report_digest_ref="sha256:" + "d" * 64,
        report_ref="foundation-report-ref:taw08-drifted-rerun",
        command_mode=first.command_mode,
        evaluator_environment_receipt=first.evaluator_environment_receipt,
        evaluator_environment_digest_ref=first.evaluator_environment_digest_ref,
        passed=first.passed,
        redacted=first.redacted,
        raw_content_persisted=first.raw_content_persisted,
    )

    assert fresh_report != first
    assert runner.same_stable_foundation_receipt(first, fresh_report)
    assert not runner.same_stable_foundation_receipt(first, stable_drift)


def test_runner_invokes_locked_verifier_and_rejects_saved_bundle_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "candidate"
    scripts = repository / "scripts"
    scripts.mkdir(parents=True)
    verifier = scripts / "verify_tool_aware_cognition_taw08.py"
    verifier.write_text("# exact verifier fixture\n", encoding="utf-8")
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    observed = SimpleNamespace()

    def fake_run(command: tuple[str, ...], **kwargs: object) -> SimpleNamespace:
        observed.command = command
        observed.cwd = kwargs["cwd"]
        observed.env = kwargs["env"]
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(_founder_inputs_bundle()).encode("utf-8"),
            stderr=b"",
        )

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    lock, foundation = runner.load_locked_founder_inputs(
        candidate_repository=repository.resolve(),
        locked_wheelhouse=wheelhouse.resolve(),
    )

    assert lock == _candidate_lock()
    assert foundation == _foundation_receipt()
    assert observed.command == (
        sys.executable,
        "-I",
        "-B",
        str(verifier),
    )
    environment = observed.env
    assert isinstance(environment, dict)
    assert environment["UAA_TAW08_EXPORT_FOUNDER_INPUTS"] == "1"
    assert environment["UAA_TAW08_LOCKED_WHEELHOUSE"] == str(wheelhouse)
    option_strings = {
        option
        for action in runner._parser()._actions
        for option in action.option_strings
    }
    assert "--founder-inputs-json" not in option_strings
    assert "--candidate-repository" in option_strings
    assert "--output" in option_strings
    hardware_action = next(
        action
        for action in runner._parser()._actions
        if "--hardware-family-ref" in action.option_strings
    )
    assert hardware_action.choices == ("hardware-family-ref:mac",)


def test_main_bounds_runtime_failures_without_echoing_raw_details(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_runtime_environment() -> None:
        raise RuntimeError("raw local detail: /private/operator/path")

    monkeypatch.setattr(
        runner,
        "_validate_runtime_environment",
        fail_runtime_environment,
    )
    placeholder = str(tmp_path.resolve())

    status = runner.main(
        [
            "--candidate-repository",
            placeholder,
            "--locked-wheelhouse",
            placeholder,
            "--founder-private-key",
            placeholder,
            "--hardware-attestation-key",
            placeholder,
            "--model-artifact-path",
            placeholder,
            "--authority-state-dir",
            placeholder,
            "--runtime-state-dir",
            placeholder,
            "--output",
            str((tmp_path / "founder-evidence.json").resolve()),
            "--authority-lease-ref",
            "authority-lease-ref:taw08:test",
            "--hardware-family-ref",
            "hardware-family-ref:mac",
            "--run-ref",
            RUN_REF,
        ]
    )

    captured = capsys.readouterr()
    assert status == 1
    assert captured.out == ""
    assert captured.err == "TAW-08 founder acceptance blocked.\n"
    assert "/private/operator/path" not in captured.err
