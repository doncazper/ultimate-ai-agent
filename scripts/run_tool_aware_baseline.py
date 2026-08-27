#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.evals.tool_aware_baseline import (  # noqa: E402
    AcceptanceEvidenceBinding,
    AdjudicationBundle,
    BASELINE_ACCEPTANCE_AUTHORITY_CONFIGURED,
    BaselineReceipt,
    BlindScoreBundle,
    CandidateLock,
    PairManifest,
    PowerAnalysisReceipt,
    RandomizationBundle,
    SourceDependencyClosure,
    SourceProjection,
    TAW00_ACCEPTANCE_EVIDENCE_CONTRACT_COMPLETE,
    TAW00Protocol,
    durable_payload_has_forbidden_fields,
    protocol_readiness,
    validate_acceptance_evidence_binding,
    validate_baseline_receipt,
    validate_blind_score_set,
    validate_power_analysis_receipt,
    validate_randomization_bundle,
    verify_candidate_lock,
    verify_source_dependency_closure,
)
from ultimate_ai_agent.core.evals.tool_aware_corpus import (  # noqa: E402
    DevelopmentCorpusManifest,
    DevelopmentManifestBuildSpec,
    HoldoutCommitment,
    HoldoutOpeningReceipt,
    build_development_corpus_manifest,
)
from ultimate_ai_agent.core.evals.tool_aware_evidence import (  # noqa: E402
    ArtifactCensus,
    CompleteAcceptanceEvidenceBinding,
    ComputedPowerAnalysisReceipt,
    EvaluationMatrixCensus,
    FamilywiseBoundReceipt,
    ObservationCensus,
    validate_complete_acceptance_evidence,
)

DEFAULT_PROTOCOL = ROOT / "docs/evals/tool_aware_cognition_taw00_protocol_v1.json"
DEFAULT_SOURCE_PROJECTION = (
    ROOT / "docs/evals/tool_aware_cognition_taw00_source_projection_v1.json"
)
_GIT_REVISION = re.compile(r"^[0-9a-f]{40}$")


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _emit(payload: object) -> None:
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def _validate_safe(payload: object) -> None:
    if durable_payload_has_forbidden_fields(payload):
        raise ValueError("durable artifact contains a forbidden raw field or value")


def _validate_protocol(path: Path) -> TAW00Protocol:
    payload = _json(path)
    _validate_safe(payload)
    return TAW00Protocol.model_validate(payload)


def _git_content(revision_ref: str, path_ref: str) -> bytes:
    revision = revision_ref.removeprefix("git-sha:")
    relative = path_ref.removeprefix("repo-path-ref:")
    if not path_ref.startswith("repo-path-ref:") or ".." in Path(relative).parts:
        raise ValueError("candidate path ref is invalid")
    completed = subprocess.run(  # noqa: S603
        ["git", "-C", str(ROOT), "show", f"{revision}:{relative}"],
        check=True,
        capture_output=True,
    )
    return completed.stdout


def _git_path_refs(revision_ref: str) -> set[str]:
    revision = revision_ref.removeprefix("git-sha:")
    if not _GIT_REVISION.fullmatch(revision):
        raise ValueError("source revision ref is invalid")
    completed = subprocess.run(  # noqa: S603
        ["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", revision],
        check=True,
        capture_output=True,
        text=True,
    )
    return {f"repo-path-ref:{path}" for path in completed.stdout.splitlines() if path}


def _baseline_verification_failures(
    *,
    receipt: BaselineReceipt,
    protocol: TAW00Protocol,
    source_projection: SourceProjection,
    pair_manifest: PairManifest,
) -> tuple[str, ...]:
    failures = set(
        validate_baseline_receipt(
            receipt,
            protocol,
            source_projection_digest_ref=source_projection.projection_digest_ref,
            pair_manifest_digest_ref=pair_manifest.manifest_digest_ref,
            source_revision_ref=source_projection.source_revision_ref,
            pair_manifest=pair_manifest,
        )
    )
    if protocol.status != "locked":
        failures.add("failure-ref:taw00:protocol-not-locked")
    if protocol.expected_pair_manifest_digest_ref != pair_manifest.manifest_digest_ref:
        failures.add("failure-ref:taw00:protocol-pair-manifest-drift")
    projection_paths = tuple(item.path_ref for item in source_projection.entries)
    if projection_paths != protocol.source_projection_path_refs:
        failures.add("failure-ref:taw00:source-projection-path-census-drift")
    for entry in source_projection.entries:
        content = _git_content(source_projection.source_revision_ref, entry.path_ref)
        actual_digest = f"sha256:{hashlib.sha256(content).hexdigest()}"
        if actual_digest != entry.content_digest_ref:
            failures.add("failure-ref:taw00:source-projection-revision-content-drift")
    if not BASELINE_ACCEPTANCE_AUTHORITY_CONFIGURED:
        failures.add("failure-ref:taw00:baseline-acceptance-authority-missing")
    if not TAW00_ACCEPTANCE_EVIDENCE_CONTRACT_COMPLETE:
        failures.add("failure-ref:taw00:acceptance-evidence-contract-incomplete")
    return tuple(sorted(failures))


def _complete_artifact_payloads(
    payloads: Mapping[str, object],
) -> dict[str, tuple[str, object]]:
    names = {
        "adjudications": "adjudications",
        "candidate_lock": "candidate-lock",
        "computed_power": "computed-power",
        "familywise_bounds": "familywise-bounds",
        "commitment": "holdout-commitment",
        "holdout_opening": "holdout-opening",
        "power_analysis": "legacy-power",
        "matrix_census": "matrix-census",
        "observations": "observation-census",
        "pair_manifest": "pair-manifest",
        "protocol": "protocol",
        "randomization": "randomization",
        "scores": "scores",
        "source_closure": "source-closure",
        "source_projection": "source-projection",
    }
    return {
        f"artifact-ref:taw00:{artifact_name}": (
            f"schema-ref:taw00:{artifact_name}",
            payloads[payload_name],
        )
        for payload_name, artifact_name in names.items()
    }


def _validate_complete_payloads(payloads: Mapping[str, object]) -> tuple[str, ...]:
    return validate_complete_acceptance_evidence(
        CompleteAcceptanceEvidenceBinding.model_validate(payloads["complete_binding"]),
        legacy_binding=AcceptanceEvidenceBinding.model_validate(payloads["binding"]),
        protocol=TAW00Protocol.model_validate(payloads["protocol"]),
        legacy_power_analysis=PowerAnalysisReceipt.model_validate(
            payloads["power_analysis"]
        ),
        source_projection=SourceProjection.model_validate(
            payloads["source_projection"]
        ),
        source_closure=SourceDependencyClosure.model_validate(
            payloads["source_closure"]
        ),
        candidate_lock=CandidateLock.model_validate(payloads["candidate_lock"]),
        pair_manifest=PairManifest.model_validate(payloads["pair_manifest"]),
        baseline_receipt=BaselineReceipt.model_validate(payloads["baseline_receipt"]),
        randomization_bundle=RandomizationBundle.model_validate(
            payloads["randomization"]
        ),
        score_bundle=BlindScoreBundle.model_validate(payloads["scores"]),
        adjudication_bundle=AdjudicationBundle.model_validate(
            payloads["adjudications"]
        ),
        commitment=HoldoutCommitment.model_validate(payloads["commitment"]),
        opening=HoldoutOpeningReceipt.model_validate(payloads["holdout_opening"]),
        matrix=EvaluationMatrixCensus.model_validate(payloads["matrix_census"]),
        computed_power=ComputedPowerAnalysisReceipt.model_validate(
            payloads["computed_power"]
        ),
        observations=ObservationCensus.model_validate(payloads["observations"]),
        familywise_bounds=FamilywiseBoundReceipt.model_validate(
            payloads["familywise_bounds"]
        ),
        artifact_census=ArtifactCensus.model_validate(payloads["artifact_census"]),
        artifact_payloads=_complete_artifact_payloads(payloads),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="TAW-00 content-safe baseline facility"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_protocol = subparsers.add_parser("validate-protocol")
    validate_protocol.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)

    generate = subparsers.add_parser("generate-development-manifest")
    generate.add_argument("--spec", type=Path, required=True)

    verify_commitment = subparsers.add_parser("verify-public-commitment")
    verify_commitment.add_argument("--commitment", type=Path, required=True)

    verify_baseline = subparsers.add_parser("verify-baseline-receipt")
    verify_baseline.add_argument("--receipt", type=Path, required=True)
    verify_baseline.add_argument("--protocol", type=Path, required=True)
    verify_baseline.add_argument("--source-projection", type=Path, required=True)
    verify_baseline.add_argument("--pair-manifest", type=Path, required=True)

    verify_scores = subparsers.add_parser("verify-score-receipts")
    verify_scores.add_argument("--scores", type=Path, required=True)
    verify_scores.add_argument("--adjudications", type=Path, required=True)
    verify_scores.add_argument("--pair-manifest", type=Path, required=True)
    verify_scores.add_argument("--randomization", type=Path)

    verify_power = subparsers.add_parser("verify-power-analysis")
    verify_power.add_argument("--receipt", type=Path, required=True)
    verify_power.add_argument("--protocol", type=Path, required=True)
    verify_power.add_argument("--pair-manifest", type=Path, required=True)

    verify_randomization = subparsers.add_parser("verify-randomization")
    verify_randomization.add_argument("--bundle", type=Path, required=True)
    verify_randomization.add_argument("--pair-manifest", type=Path, required=True)
    verify_randomization.add_argument("--candidate-lock", type=Path, required=True)

    verify_closure = subparsers.add_parser("verify-source-closure")
    verify_closure.add_argument("--closure", type=Path, required=True)
    verify_closure.add_argument("--source-projection", type=Path, required=True)

    verify_binding = subparsers.add_parser("verify-acceptance-binding")
    verify_binding.add_argument("--binding", type=Path, required=True)
    verify_binding.add_argument("--protocol", type=Path, required=True)
    verify_binding.add_argument("--power-analysis", type=Path, required=True)
    verify_binding.add_argument("--source-projection", type=Path, required=True)
    verify_binding.add_argument("--source-closure", type=Path, required=True)
    verify_binding.add_argument("--candidate-lock", type=Path, required=True)
    verify_binding.add_argument("--pair-manifest", type=Path, required=True)
    verify_binding.add_argument("--baseline-receipt", type=Path, required=True)
    verify_binding.add_argument("--randomization", type=Path, required=True)
    verify_binding.add_argument("--scores", type=Path, required=True)
    verify_binding.add_argument("--adjudications", type=Path, required=True)

    verify_complete = subparsers.add_parser("verify-complete-evidence")
    for option in (
        "binding",
        "complete-binding",
        "protocol",
        "power-analysis",
        "source-projection",
        "source-closure",
        "candidate-lock",
        "pair-manifest",
        "baseline-receipt",
        "randomization",
        "scores",
        "adjudications",
        "commitment",
        "holdout-opening",
        "matrix-census",
        "computed-power",
        "observations",
        "familywise-bounds",
        "artifact-census",
    ):
        verify_complete.add_argument(f"--{option}", type=Path, required=True)

    readiness = subparsers.add_parser("report-readiness")
    readiness.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    readiness.add_argument("--commitment", type=Path, required=True)
    readiness.add_argument("--development-corpus", type=Path, required=True)
    readiness.add_argument("--pair-manifest", type=Path, required=True)
    readiness.add_argument("--power-analysis", type=Path, required=True)
    readiness.add_argument("--baseline-receipt", type=Path, required=True)
    readiness.add_argument(
        "--source-projection", type=Path, default=DEFAULT_SOURCE_PROJECTION
    )
    readiness.add_argument("--candidate-lock", type=Path, required=True)
    readiness.add_argument("--source-closure", type=Path, required=True)
    readiness.add_argument("--randomization", type=Path, required=True)
    readiness.add_argument("--acceptance-binding", type=Path, required=True)
    readiness.add_argument("--scores", type=Path, required=True)
    readiness.add_argument("--adjudications", type=Path, required=True)
    readiness.add_argument("--holdout-opening", type=Path, required=True)
    readiness.add_argument("--matrix-census", type=Path, required=True)
    readiness.add_argument("--computed-power", type=Path, required=True)
    readiness.add_argument("--observations", type=Path, required=True)
    readiness.add_argument("--familywise-bounds", type=Path, required=True)
    readiness.add_argument("--artifact-census", type=Path, required=True)
    readiness.add_argument("--complete-binding", type=Path, required=True)

    args = parser.parse_args()
    try:
        if args.command == "validate-protocol":
            protocol = _validate_protocol(args.protocol)
            _emit({"protocol_ref": protocol.protocol_ref, "status": protocol.status})
        elif args.command == "generate-development-manifest":
            spec = DevelopmentManifestBuildSpec.model_validate(_json(args.spec))
            manifest = build_development_corpus_manifest(
                corpus_ref=spec.corpus_ref,
                deterministic_seed_ref=spec.deterministic_seed_ref,
                seed_material=bytes.fromhex(spec.seed_material_hex),
                specs=spec.cases,
            )
            _emit(manifest.model_dump(mode="json"))
        elif args.command == "verify-public-commitment":
            payload = _json(args.commitment)
            _validate_safe(payload)
            commitment = HoldoutCommitment.model_validate(payload)
            _emit(
                {
                    "cycle_ref": commitment.cycle_ref,
                    "status": "structure_valid_but_acceptance_blocked",
                }
            )
            return 2
        elif args.command == "verify-baseline-receipt":
            payloads = {
                "receipt": _json(args.receipt),
                "protocol": _json(args.protocol),
                "source_projection": _json(args.source_projection),
                "pair_manifest": _json(args.pair_manifest),
            }
            _validate_safe(payloads)
            receipt = BaselineReceipt.model_validate(payloads["receipt"])
            protocol = TAW00Protocol.model_validate(payloads["protocol"])
            source_projection = SourceProjection.model_validate(
                payloads["source_projection"]
            )
            pair_manifest = PairManifest.model_validate(payloads["pair_manifest"])
            failures = _baseline_verification_failures(
                receipt=receipt,
                protocol=protocol,
                source_projection=source_projection,
                pair_manifest=pair_manifest,
            )
            _emit(
                {
                    "baseline_ref": receipt.baseline_ref,
                    "status": "receipt_consistency_only_acceptance_blocked",
                    "failure_refs": failures,
                }
            )
            return 2
        elif args.command == "verify-score-receipts":
            score_payload = _json(args.scores)
            adjudication_payload = _json(args.adjudications)
            pair_manifest_payload = _json(args.pair_manifest)
            randomization_payload = (
                _json(args.randomization) if args.randomization is not None else None
            )
            _validate_safe(score_payload)
            _validate_safe(adjudication_payload)
            _validate_safe(pair_manifest_payload)
            if randomization_payload is not None:
                _validate_safe(randomization_payload)
            pair_manifest = PairManifest.model_validate(pair_manifest_payload)
            score_bundle = BlindScoreBundle.model_validate(score_payload)
            adjudication_bundle = AdjudicationBundle.model_validate(
                adjudication_payload
            )
            randomization_bundle = (
                RandomizationBundle.model_validate(randomization_payload)
                if randomization_payload is not None
                else None
            )
            if any(
                digest != pair_manifest.manifest_digest_ref
                for digest in (
                    score_bundle.pair_manifest_digest_ref,
                    adjudication_bundle.pair_manifest_digest_ref,
                )
            ):
                raise ValueError("score bundle pair-manifest binding drift")
            report = validate_blind_score_set(
                score_bundle.scores,
                adjudication_bundle.adjudications,
                pair_manifest=pair_manifest,
                randomization_bundle=randomization_bundle,
            )
            _emit(
                {
                    "status": "receipt_consistency_only_acceptance_blocked",
                    "failure_refs": report.failure_refs,
                    "agreement_by_language_dimension": (
                        report.agreement_by_language_dimension
                    ),
                }
            )
            return 2
        elif args.command == "verify-power-analysis":
            payloads = {
                "receipt": _json(args.receipt),
                "protocol": _json(args.protocol),
                "pair_manifest": _json(args.pair_manifest),
            }
            _validate_safe(payloads)
            power_receipt = PowerAnalysisReceipt.model_validate(payloads["receipt"])
            protocol = TAW00Protocol.model_validate(payloads["protocol"])
            pair_manifest = PairManifest.model_validate(payloads["pair_manifest"])
            failures = validate_power_analysis_receipt(
                power_receipt, protocol, pair_manifest=pair_manifest
            )
            _emit(
                {
                    "status": "receipt_consistency_only_acceptance_blocked",
                    "failure_refs": failures,
                }
            )
            return 2
        elif args.command == "verify-randomization":
            payloads = {
                "bundle": _json(args.bundle),
                "pair_manifest": _json(args.pair_manifest),
                "candidate_lock": _json(args.candidate_lock),
            }
            _validate_safe(payloads)
            bundle = RandomizationBundle.model_validate(payloads["bundle"])
            pair_manifest = PairManifest.model_validate(payloads["pair_manifest"])
            candidate_lock = CandidateLock.model_validate(payloads["candidate_lock"])
            failures = validate_randomization_bundle(
                bundle,
                pair_manifest=pair_manifest,
                candidate_lock=candidate_lock,
            )
            _emit(
                {
                    "status": "receipt_consistency_only_acceptance_blocked",
                    "failure_refs": failures,
                }
            )
            return 2
        elif args.command == "verify-source-closure":
            payloads = {
                "closure": _json(args.closure),
                "source_projection": _json(args.source_projection),
            }
            _validate_safe(payloads)
            closure = SourceDependencyClosure.model_validate(payloads["closure"])
            projection = SourceProjection.model_validate(payloads["source_projection"])
            content_by_path = {
                entry.path_ref: _git_content(
                    closure.source_revision_ref, entry.path_ref
                )
                for entry in closure.entries
            }
            failures = verify_source_dependency_closure(
                closure,
                source_projection=projection,
                content_by_path_ref=content_by_path,
                available_path_refs=_git_path_refs(closure.source_revision_ref),
            )
            _emit(
                {
                    "status": "receipt_consistency_only_acceptance_blocked",
                    "failure_refs": failures,
                }
            )
            return 2
        elif args.command == "verify-acceptance-binding":
            payloads = {
                name: _json(path)
                for name, path in (
                    ("binding", args.binding),
                    ("protocol", args.protocol),
                    ("power_analysis", args.power_analysis),
                    ("source_projection", args.source_projection),
                    ("source_closure", args.source_closure),
                    ("candidate_lock", args.candidate_lock),
                    ("pair_manifest", args.pair_manifest),
                    ("baseline_receipt", args.baseline_receipt),
                    ("randomization", args.randomization),
                    ("scores", args.scores),
                    ("adjudications", args.adjudications),
                )
            }
            _validate_safe(payloads)
            failures = validate_acceptance_evidence_binding(
                AcceptanceEvidenceBinding.model_validate(payloads["binding"]),
                protocol=TAW00Protocol.model_validate(payloads["protocol"]),
                power_analysis=PowerAnalysisReceipt.model_validate(
                    payloads["power_analysis"]
                ),
                source_projection=SourceProjection.model_validate(
                    payloads["source_projection"]
                ),
                source_closure=SourceDependencyClosure.model_validate(
                    payloads["source_closure"]
                ),
                candidate_lock=CandidateLock.model_validate(payloads["candidate_lock"]),
                pair_manifest=PairManifest.model_validate(payloads["pair_manifest"]),
                baseline_receipt=BaselineReceipt.model_validate(
                    payloads["baseline_receipt"]
                ),
                randomization_bundle=RandomizationBundle.model_validate(
                    payloads["randomization"]
                ),
                score_bundle=BlindScoreBundle.model_validate(payloads["scores"]),
                adjudication_bundle=AdjudicationBundle.model_validate(
                    payloads["adjudications"]
                ),
            )
            _emit(
                {
                    "status": "receipt_consistency_only_acceptance_blocked",
                    "failure_refs": failures,
                }
            )
            return 2
        elif args.command == "verify-complete-evidence":
            payloads = {
                name: _json(getattr(args, name))
                for name in (
                    "binding",
                    "complete_binding",
                    "protocol",
                    "power_analysis",
                    "source_projection",
                    "source_closure",
                    "candidate_lock",
                    "pair_manifest",
                    "baseline_receipt",
                    "randomization",
                    "scores",
                    "adjudications",
                    "commitment",
                    "holdout_opening",
                    "matrix_census",
                    "computed_power",
                    "observations",
                    "familywise_bounds",
                    "artifact_census",
                )
            }
            _validate_safe(payloads)
            failures = _validate_complete_payloads(payloads)
            _emit(
                {
                    "status": "complete_contract_consistency_only_external_acceptance_blocked",
                    "failure_refs": failures,
                }
            )
            return 2
        elif args.command == "report-readiness":
            protocol = _validate_protocol(args.protocol)
            artifacts = {
                name: _json(path)
                for name, path in (
                    ("commitment", args.commitment),
                    ("development_corpus", args.development_corpus),
                    ("pair_manifest", args.pair_manifest),
                    ("power_analysis", args.power_analysis),
                    ("baseline_receipt", args.baseline_receipt),
                    ("source_projection", args.source_projection),
                    ("source_closure", args.source_closure),
                    ("candidate_lock", args.candidate_lock),
                    ("randomization", args.randomization),
                    ("acceptance_binding", args.acceptance_binding),
                    ("scores", args.scores),
                    ("adjudications", args.adjudications),
                    ("holdout_opening", args.holdout_opening),
                    ("matrix_census", args.matrix_census),
                    ("computed_power", args.computed_power),
                    ("observations", args.observations),
                    ("familywise_bounds", args.familywise_bounds),
                    ("artifact_census", args.artifact_census),
                    ("complete_binding", args.complete_binding),
                )
            }
            _validate_safe(artifacts)
            commitment = HoldoutCommitment.model_validate(artifacts["commitment"])
            development_corpus = DevelopmentCorpusManifest.model_validate(
                artifacts["development_corpus"]
            )
            pair_manifest = PairManifest.model_validate(artifacts["pair_manifest"])
            power_analysis = PowerAnalysisReceipt.model_validate(
                artifacts["power_analysis"]
            )
            baseline = BaselineReceipt.model_validate(artifacts["baseline_receipt"])
            projection = SourceProjection.model_validate(artifacts["source_projection"])
            source_closure = SourceDependencyClosure.model_validate(
                artifacts["source_closure"]
            )
            candidate_lock = CandidateLock.model_validate(artifacts["candidate_lock"])
            randomization = RandomizationBundle.model_validate(
                artifacts["randomization"]
            )
            acceptance_binding = AcceptanceEvidenceBinding.model_validate(
                artifacts["acceptance_binding"]
            )
            score_bundle = BlindScoreBundle.model_validate(artifacts["scores"])
            adjudication_bundle = AdjudicationBundle.model_validate(
                artifacts["adjudications"]
            )
            if any(
                digest != pair_manifest.manifest_digest_ref
                for digest in (
                    score_bundle.pair_manifest_digest_ref,
                    adjudication_bundle.pair_manifest_digest_ref,
                )
            ):
                raise ValueError("score bundle pair-manifest binding drift")
            score_report = validate_blind_score_set(
                score_bundle.scores,
                adjudication_bundle.adjudications,
                pair_manifest=pair_manifest,
                randomization_bundle=randomization,
            )
            source_paths = tuple(item.path_ref for item in projection.entries)
            source_projection_verified = all(
                item.content_digest_ref
                == "sha256:"
                + hashlib.sha256(
                    _git_content(projection.source_revision_ref, item.path_ref)
                ).hexdigest()
                for item in projection.entries
            )
            expected_paths = protocol.acceptance_affecting_path_refs
            revision_content = {
                path_ref: _git_content(candidate_lock.git_revision_ref, path_ref)
                for path_ref in expected_paths
            }
            candidate_failures = verify_candidate_lock(
                candidate_lock,
                expected_path_refs=expected_paths,
                revision_content_by_path_ref=revision_content,
            )
            baseline_failures = validate_baseline_receipt(
                baseline,
                protocol,
                source_projection_digest_ref=projection.projection_digest_ref,
                pair_manifest_digest_ref=pair_manifest.manifest_digest_ref,
                source_revision_ref=projection.source_revision_ref,
                pair_manifest=pair_manifest,
            )
            closure_content = {
                entry.path_ref: _git_content(
                    source_closure.source_revision_ref, entry.path_ref
                )
                for entry in source_closure.entries
            }
            source_closure_failures = verify_source_dependency_closure(
                source_closure,
                source_projection=projection,
                content_by_path_ref=closure_content,
                available_path_refs=_git_path_refs(source_closure.source_revision_ref),
            )
            randomization_failures = validate_randomization_bundle(
                randomization,
                pair_manifest=pair_manifest,
                candidate_lock=candidate_lock,
            )
            binding_failures = validate_acceptance_evidence_binding(
                acceptance_binding,
                protocol=protocol,
                power_analysis=power_analysis,
                source_projection=projection,
                source_closure=source_closure,
                candidate_lock=candidate_lock,
                pair_manifest=pair_manifest,
                baseline_receipt=baseline,
                randomization_bundle=randomization,
                score_bundle=score_bundle,
                adjudication_bundle=adjudication_bundle,
            )
            complete_failures = _validate_complete_payloads(
                {**artifacts, "binding": artifacts["acceptance_binding"]}
            )
            report = protocol_readiness(
                protocol,
                commitment=commitment,
                development_corpus=development_corpus,
                pair_manifest=pair_manifest,
                power_analysis_receipt=power_analysis,
                baseline_receipt=baseline,
                source_projection_digest_ref=projection.projection_digest_ref,
                source_projection_path_refs=source_paths,
                source_projection_verified=source_projection_verified,
                source_closure_verified=not source_closure_failures,
                source_closure_failures=source_closure_failures,
                baseline_acceptance_verified=False,
                candidate_lock_verified=not candidate_failures,
                candidate_lock_failures=tuple(
                    (*candidate_failures, *baseline_failures)
                ),
                score_report=score_report,
                randomization_verified=not randomization_failures,
                randomization_failures=randomization_failures,
                acceptance_binding_verified=not binding_failures,
                acceptance_binding_failures=binding_failures,
                complete_evidence_verified=not complete_failures,
                complete_evidence_failures=complete_failures,
            )
            _emit(report)
            if report["status"] != "ready":
                return 2
    except (
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as exc:
        _emit({"status": "invalid", "reason_code": type(exc).__name__})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
