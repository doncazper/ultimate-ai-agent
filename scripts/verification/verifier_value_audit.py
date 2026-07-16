#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import stat
import subprocess
import sys
from statistics import median
from dataclasses import dataclass
from pathlib import Path
from pathlib import PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.verification.ci_command_manifest import (  # noqa: E402
    FOCUSED_VERIFICATION_UNITS,
)
from scripts.verification.verifier_value_measurement import (  # noqa: E402
    bindings_from_repository,
    validate_measurement_run,
)
from scripts.verify_release_lanes import release_lanes  # noqa: E402


SCHEMA_VERSION = "uaa-verifier-unique-value-audit.v2"
MEASUREMENT_PATH = ROOT / "docs/verification/verifier_value_measurements.json"
MEASUREMENT_BINDING_FIELDS = (
    "dependency_state_fingerprint",
    "platform_fingerprint",
    "command_manifest_fingerprint",
    "verifier_definition_fingerprint",
    "test_collection_fingerprint",
)


@dataclass(frozen=True)
class VerifierValue:
    verifier_ref: str
    coverage_refs: tuple[str, ...]
    unique_defect_ref: str
    overlap_ref: str
    disposition: str
    measurement_ref: str | None = None

    def payload(self) -> dict[str, object]:
        return {
            "verifier_ref": self.verifier_ref,
            "coverage_refs": list(self.coverage_refs),
            "unique_defect_ref": self.unique_defect_ref,
            "overlap_ref": self.overlap_ref,
            "disposition": self.disposition,
            "measurement_ref": self.measurement_ref,
        }


VALUES = (
    VerifierValue(
        "verifier-ref:ruff-changed",
        ("selector:command:ci.ruff",),
        "defect-ref:changed-python-lint-drift",
        "overlap-ref:full-ruff-partial",
        "retain-fast-loop",
    ),
    VerifierValue(
        "verifier-ref:verification-value-audit",
        ("measurement-ref:synthetic-verifier-value",),
        "defect-ref:verifier-measurement-and-coverage-drift",
        "overlap-ref:verifier-maintainability-partial",
        "retain",
    ),
    VerifierValue(
        "verifier-ref:api-contract",
        (
            "selector:command:openapi.contract",
            "selector:command:api.safe-errors",
            "selector:command:control-center.api-routes",
            "release-lane:openapi",
        ),
        "defect-ref:api-schema-route-and-security-policy-drift",
        "overlap-ref:shared-api-context",
        "retain",
        "measurement-ref:api-affected",
    ),
    VerifierValue(
        "verifier-ref:documentation-integrity",
        ("selector:command:docs.integrity", "release-lane:docs"),
        "defect-ref:canonical-doc-link-and-index-drift",
        "overlap-ref:none-material",
        "retain",
        "measurement-ref:docs-fast",
    ),
    VerifierValue(
        "verifier-ref:product-truth",
        (
            "selector:command:product-truth.regression-verifier",
            "release-lane:product-truth-regression",
        ),
        "defect-ref:unsupported-product-claim",
        "overlap-ref:documentation-text-scan-partial",
        "retain",
        "measurement-ref:product-truth-warm",
    ),
    VerifierValue(
        "verifier-ref:security-redaction",
        (
            "selector:command:security.artifact-redaction",
            "release-lane:security-redaction",
        ),
        "defect-ref:unsafe-durable-artifact-content",
        "overlap-ref:product-truth-claim-scan-partial",
        "retain",
    ),
    VerifierValue(
        "verifier-ref:control-center-frontend",
        (
            "selector:command:frontend.typecheck",
            "selector:command:frontend.unit-tests",
            "selector:command:frontend.vite-build",
            "selector:command:frontend.safety",
            "release-lane:frontend",
        ),
        "defect-ref:frontend-type-test-build-contract",
        "overlap-ref:frontend-safety-static-partial",
        "retain",
        "measurement-ref:frontend-after",
    ),
    VerifierValue(
        "verifier-ref:visual-regression",
        ("release-lane:visual-regression",),
        "defect-ref:accepted-render-drift",
        "overlap-ref:frontend-build-none",
        "retain-release-only",
    ),
    VerifierValue(
        "verifier-ref:web-hybrid",
        ("coverage-ref:web-hybrid-contracts",),
        "defect-ref:web-gateway-provider-authority-drift",
        "overlap-ref:openapi-none",
        "retain",
    ),
    VerifierValue(
        "verifier-ref:authority-durability",
        ("selector:command:pytest.focused", "release-lane:durability"),
        "defect-ref:authority-replay-and-ledger-safety",
        "overlap-ref:full-pytest-partial",
        "retain",
    ),
    VerifierValue(
        "verifier-ref:desktop-packaging",
        (
            "release-lane:desktop-packaging",
        ),
        "defect-ref:desktop-local-package-proof",
        "overlap-ref:frontend-none",
        "retain",
    ),
    VerifierValue(
        "verifier-ref:full-local-gate",
        (
            "selector:command:git.diff-check",
            "release-lane:performance",
        ),
        "defect-ref:cross-boundary-regression-and-performance-budget",
        "overlap-ref:all-focused-lanes-aggregated",
        "retain-outside-fast-loop",
        "measurement-ref:full-local-after",
    ),
    VerifierValue(
        "verifier-ref:local-model-e2e",
        ("release-lane:local-model-e2e",),
        "defect-ref:local-model-release-posture-drift",
        "overlap-ref:full-pytest-partial",
        "retain-release-only",
    ),
    VerifierValue(
        "verifier-ref:api-safety",
        ("release-lane:api-safety",),
        "defect-ref:unsafe-api-error-or-control-center-route",
        "overlap-ref:api-contract-partial",
        "retain-release-only",
    ),
)


def _canonical(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def _measurement_fingerprint(payload: dict[str, object]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "fingerprint"}
    return (
        "verifier-measurement-fingerprint:sha256:"
        f"{hashlib.sha256(_canonical(unsigned)).hexdigest()}"
    )


@dataclass(frozen=True)
class RepositoryMeasurementState:
    current_sha: str
    changed_path_refs: tuple[str, ...]


def _run_git(
    repo: Path,
    arguments: tuple[str, ...],
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ("git", *arguments),
            cwd=repo,
            check=check,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError("VERIFIER_MEASUREMENT_REPOSITORY_STATE_UNAVAILABLE") from exc


def _repository_measurement_state(
    repo: Path,
    source_sha: str,
) -> RepositoryMeasurementState:
    current_sha = _run_git(repo, ("rev-parse", "HEAD")).stdout.strip()
    source = _run_git(
        repo,
        ("cat-file", "-e", f"{source_sha}^{{commit}}"),
        check=False,
    )
    if source.returncode != 0:
        raise ValueError("VERIFIER_MEASUREMENT_SOURCE_COMMIT_MISSING")
    ancestor = _run_git(
        repo,
        ("merge-base", "--is-ancestor", source_sha, current_sha),
        check=False,
    )
    if ancestor.returncode == 1:
        raise ValueError("VERIFIER_MEASUREMENT_SOURCE_NOT_ANCESTOR")
    if ancestor.returncode != 0:
        raise ValueError("VERIFIER_MEASUREMENT_REPOSITORY_STATE_UNAVAILABLE")
    if source_sha == current_sha:
        return RepositoryMeasurementState(current_sha, ())
    changed = _run_git(
        repo,
        (
            "diff",
            "--name-only",
            "--no-renames",
            "-z",
            f"{source_sha}..{current_sha}",
            "--",
        ),
    ).stdout
    return RepositoryMeasurementState(
        current_sha,
        tuple(path for path in changed.split("\0") if path),
    )


def _is_measurement_neutral_path(path_ref: str) -> bool:
    path = PurePosixPath(path_ref)
    return (
        bool(path.parts)
        and not path.is_absolute()
        and ".." not in path.parts
        and path.parts[0] == "docs"
    )


def _current_measurement_bindings(repo: Path) -> dict[str, str]:
    try:
        return bindings_from_repository(repo).payload()
    except (RuntimeError, ValueError) as exc:
        raise ValueError("VERIFIER_MEASUREMENT_CURRENT_BINDING_UNAVAILABLE") from exc


def _validate_measurement_freshness(
    measurement_run: dict[str, object],
    source_sha: str,
    *,
    repo: Path,
) -> None:
    state = _repository_measurement_state(repo, source_sha)
    if state.current_sha != source_sha and (
        not state.changed_path_refs
        or any(
            not _is_measurement_neutral_path(path_ref)
            for path_ref in state.changed_path_refs
        )
    ):
        raise ValueError("VERIFIER_MEASUREMENT_SOURCE_SCOPE_INVALID")
    run_bindings = measurement_run.get("bindings")
    if not isinstance(run_bindings, dict):
        raise ValueError("VERIFIER_MEASUREMENT_RUN_INVALID")
    current_bindings = _current_measurement_bindings(repo)
    if any(
        current_bindings.get(field) != run_bindings.get(field)
        for field in MEASUREMENT_BINDING_FIELDS
    ):
        raise ValueError("VERIFIER_MEASUREMENT_INPUT_BINDING_DRIFT")


def load_measurements(
    path: Path = MEASUREMENT_PATH,
    *,
    repo: Path = ROOT,
) -> dict[str, object]:
    metadata = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        raise ValueError("VERIFIER_MEASUREMENT_ARTIFACT_INVALID")
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("schema_version") not in {
        "uaa-verifier-value-measurements.v1",
        "uaa-verifier-value-measurements.v2",
    }:
        raise ValueError("VERIFIER_MEASUREMENT_SCHEMA_INVALID")
    if result.get("fingerprint") != _measurement_fingerprint(result):
        raise ValueError("VERIFIER_MEASUREMENT_FINGERPRINT_INVALID")
    if result.get("schema_version") == "uaa-verifier-value-measurements.v2":
        measurement_run = result.get("measurement_run")
        if not isinstance(measurement_run, dict):
            raise ValueError("VERIFIER_MEASUREMENT_RUN_INVALID")
        try:
            validate_measurement_run(measurement_run)
        except (RuntimeError, ValueError) as exc:
            raise ValueError("VERIFIER_MEASUREMENT_RUN_INVALID") from exc
        source_sha = result.get("source_repository_sha")
        run_bindings = measurement_run.get("bindings")
        if (
            not isinstance(source_sha, str)
            or len(source_sha) != 40
            or any(character not in "0123456789abcdef" for character in source_sha)
            or not isinstance(run_bindings, dict)
            or run_bindings.get("repository_sha") != source_sha
        ):
            raise ValueError("VERIFIER_MEASUREMENT_SOURCE_BINDING_INVALID")
        _validate_measurement_freshness(
            measurement_run,
            source_sha,
            repo=repo,
        )
        _validate_timing_comparisons(result.get("timing_comparisons"))
    return result


def _validate_timing_comparisons(value: object) -> None:
    if not isinstance(value, list) or not value:
        raise ValueError("VERIFIER_TIMING_COMPARISONS_INVALID")
    refs: set[str] = set()
    for row in value:
        if not isinstance(row, dict) or set(row) != {
            "timing_ref",
            "comparison_kind",
            "machine_profile_ref",
            "before_samples_ms",
            "after_samples_ms",
            "before_median_ms",
            "after_median_ms",
            "delta_percent",
            "comparable",
            "regression_warning",
            "evidence_posture",
        }:
            raise ValueError("VERIFIER_TIMING_ROW_INVALID")
        timing_ref = row.get("timing_ref")
        if (
            not isinstance(timing_ref, str)
            or timing_ref in refs
            or not timing_ref.startswith("timing-ref:")
        ):
            raise ValueError("VERIFIER_TIMING_REF_INVALID")
        refs.add(timing_ref)
        before = row.get("before_samples_ms")
        after = row.get("after_samples_ms")
        if (
            not isinstance(before, list)
            or not isinstance(after, list)
            or not 1 <= len(before) <= 10
            or not 1 <= len(after) <= 10
            or any(
                not isinstance(duration, int)
                or isinstance(duration, bool)
                or not 1 <= duration <= 7_200_000
                for duration in (*before, *after)
            )
        ):
            raise ValueError("VERIFIER_TIMING_SAMPLES_INVALID")
        before_median = median(before)
        after_median = median(after)
        delta_percent = round(
            ((after_median - before_median) / before_median) * 100,
            2,
        )
        comparable = row.get("comparable")
        warning = comparable is True and delta_percent > 15.0
        if (
            row.get("before_median_ms") != before_median
            or row.get("after_median_ms") != after_median
            or row.get("delta_percent") != delta_percent
            or row.get("regression_warning") is not warning
            or not isinstance(comparable, bool)
            or row.get("comparison_kind")
            not in {"cold_to_warm", "before_to_after_warm"}
            or row.get("machine_profile_ref")
            != "machine-profile:macos-arm64-private"
            or row.get("evidence_posture")
            not in {
                "same_machine_advisory",
                "same_machine_noncomparable_diagnostic",
            }
        ):
            raise ValueError("VERIFIER_TIMING_DERIVATION_INVALID")


def required_coverage_refs() -> set[str]:
    selector_refs = {
        f"selector:{command_ref}"
        for unit in FOCUSED_VERIFICATION_UNITS
        for command_ref in unit.command_refs
    }
    release_refs = {f"release-lane:{lane.lane_id}" for lane in release_lanes()}
    return selector_refs | release_refs


def validate(
    values: tuple[VerifierValue, ...] = VALUES,
    measurements: dict[str, object] | None = None,
) -> None:
    measurements = measurements or load_measurements()
    refs = [value.verifier_ref for value in values]
    defects = [value.unique_defect_ref for value in values]
    if len(refs) != len(set(refs)):
        raise ValueError("VERIFIER_VALUE_DUPLICATE_REF")
    if len(defects) != len(set(defects)):
        raise ValueError("VERIFIER_VALUE_DUPLICATE_DEFECT")
    covered = {ref for value in values for ref in value.coverage_refs}
    if not required_coverage_refs().issubset(covered):
        raise ValueError("VERIFIER_VALUE_COVERAGE_DRIFT")
    measurement_rows = measurements.get("measurements")
    if not isinstance(measurement_rows, list):
        raise ValueError("VERIFIER_MEASUREMENT_ROWS_INVALID")
    measurement_refs = {
        row.get("measurement_ref") for row in measurement_rows if isinstance(row, dict)
    }
    for value in values:
        if not value.coverage_refs or not all(
            (
                value.verifier_ref,
                value.unique_defect_ref,
                value.overlap_ref,
                value.disposition,
            )
        ):
            raise ValueError("VERIFIER_VALUE_FIELD_MISSING")
        if value.measurement_ref and value.measurement_ref not in measurement_refs:
            raise ValueError("VERIFIER_VALUE_MEASUREMENT_REF_MISSING")


def payload() -> dict[str, object]:
    measurements = load_measurements()
    validate(VALUES, measurements)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "current",
        "measurement_artifact_ref": MEASUREMENT_PATH.relative_to(ROOT).as_posix(),
        "measurement_fingerprint": measurements["fingerprint"],
        "release_gate_replacement": False,
        "verifiers": [value.payload() for value in VALUES],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit unique verifier value against active selector and release lanes."
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = payload()
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("Verifier unique-value audit: current")
        print(f"  coverage refs: {len(required_coverage_refs())}")
        print(f"  measurement: {result['measurement_fingerprint']}")
        for value in VALUES:
            status = value.measurement_ref or "not-measured"
            print(f"  {value.verifier_ref}: {status} -> {value.disposition}")
        print("  This audit does not replace merge or release gates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
