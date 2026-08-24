#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.evals.tool_aware_baseline import (  # noqa: E402
    AdjudicationBundle,
    BASELINE_ACCEPTANCE_AUTHORITY_CONFIGURED,
    BaselineReceipt,
    BlindScoreBundle,
    CandidateLock,
    PairManifest,
    SourceProjection,
    TAW00_ACCEPTANCE_EVIDENCE_CONTRACT_COMPLETE,
    TAW00Protocol,
    durable_payload_has_forbidden_fields,
    protocol_readiness,
    validate_baseline_receipt,
    validate_blind_score_set,
    verify_candidate_lock,
)
from ultimate_ai_agent.core.evals.tool_aware_corpus import (  # noqa: E402
    DevelopmentCorpusManifest,
    DevelopmentManifestBuildSpec,
    HoldoutCommitment,
    build_development_corpus_manifest,
)

DEFAULT_PROTOCOL = ROOT / "docs/evals/tool_aware_cognition_taw00_protocol_v1.json"
DEFAULT_SOURCE_PROJECTION = (
    ROOT / "docs/evals/tool_aware_cognition_taw00_source_projection_v1.json"
)


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

    readiness = subparsers.add_parser("report-readiness")
    readiness.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    readiness.add_argument("--commitment", type=Path, required=True)
    readiness.add_argument("--development-corpus", type=Path, required=True)
    readiness.add_argument("--pair-manifest", type=Path, required=True)
    readiness.add_argument("--baseline-receipt", type=Path, required=True)
    readiness.add_argument(
        "--source-projection", type=Path, default=DEFAULT_SOURCE_PROJECTION
    )
    readiness.add_argument("--candidate-lock", type=Path, required=True)
    readiness.add_argument("--scores", type=Path, required=True)
    readiness.add_argument("--adjudications", type=Path, required=True)

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
            _validate_safe(score_payload)
            _validate_safe(adjudication_payload)
            _validate_safe(pair_manifest_payload)
            pair_manifest = PairManifest.model_validate(pair_manifest_payload)
            score_bundle = BlindScoreBundle.model_validate(score_payload)
            adjudication_bundle = AdjudicationBundle.model_validate(
                adjudication_payload
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
        elif args.command == "report-readiness":
            protocol = _validate_protocol(args.protocol)
            artifacts = {
                name: _json(path)
                for name, path in (
                    ("commitment", args.commitment),
                    ("development_corpus", args.development_corpus),
                    ("pair_manifest", args.pair_manifest),
                    ("baseline_receipt", args.baseline_receipt),
                    ("source_projection", args.source_projection),
                    ("candidate_lock", args.candidate_lock),
                    ("scores", args.scores),
                    ("adjudications", args.adjudications),
                )
            }
            _validate_safe(artifacts)
            commitment = HoldoutCommitment.model_validate(artifacts["commitment"])
            development_corpus = DevelopmentCorpusManifest.model_validate(
                artifacts["development_corpus"]
            )
            pair_manifest = PairManifest.model_validate(artifacts["pair_manifest"])
            baseline = BaselineReceipt.model_validate(artifacts["baseline_receipt"])
            projection = SourceProjection.model_validate(artifacts["source_projection"])
            candidate_lock = CandidateLock.model_validate(artifacts["candidate_lock"])
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
            )
            report = protocol_readiness(
                protocol,
                commitment=commitment,
                development_corpus=development_corpus,
                pair_manifest=pair_manifest,
                baseline_receipt=baseline,
                source_projection_digest_ref=projection.projection_digest_ref,
                source_projection_path_refs=source_paths,
                source_projection_verified=source_projection_verified,
                baseline_acceptance_verified=False,
                candidate_lock_verified=not candidate_failures,
                candidate_lock_failures=tuple(
                    (*candidate_failures, *baseline_failures)
                ),
                score_report=score_report,
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
