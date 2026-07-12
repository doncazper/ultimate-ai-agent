#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import stat
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.verification.changed_path_selector import COMMANDS  # noqa: E402
from scripts.verify_release_lanes import release_lanes  # noqa: E402


SCHEMA_VERSION = "uaa-verifier-unique-value-audit.v2"
MEASUREMENT_PATH = ROOT / "docs/verification/verifier_value_measurements.json"


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
        "verifier-ref:api-contract",
        (
            "selector:command-ref:api-contract-snapshot",
            "selector:command-ref:api-lane",
            "selector:command-ref:openapi",
            "release-lane:openapi",
        ),
        "defect-ref:api-schema-route-and-security-policy-drift",
        "overlap-ref:shared-api-context",
        "retain-consolidated",
        "measurement-ref:api-affected",
    ),
    VerifierValue(
        "verifier-ref:documentation-integrity",
        ("selector:command-ref:documentation", "release-lane:docs"),
        "defect-ref:canonical-doc-link-and-index-drift",
        "overlap-ref:none-material",
        "retain",
        "measurement-ref:docs-fast",
    ),
    VerifierValue(
        "verifier-ref:product-truth",
        ("selector:command-ref:product-truth",),
        "defect-ref:unsupported-product-claim",
        "overlap-ref:documentation-text-scan-partial",
        "retain",
        "measurement-ref:product-truth-warm",
    ),
    VerifierValue(
        "verifier-ref:security-redaction",
        ("selector:command-ref:redaction", "release-lane:security-redaction"),
        "defect-ref:unsafe-durable-artifact-content",
        "overlap-ref:product-truth-claim-scan-partial",
        "retain",
    ),
    VerifierValue(
        "verifier-ref:control-center-frontend",
        (
            "selector:command-ref:frontend-check",
            "selector:command-ref:frontend-safety",
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
        ("selector:command-ref:web-hybrid",),
        "defect-ref:web-gateway-provider-authority-drift",
        "overlap-ref:openapi-none",
        "retain",
    ),
    VerifierValue(
        "verifier-ref:authority-durability",
        ("selector:command-ref:authority-focused", "release-lane:durability"),
        "defect-ref:authority-replay-and-ledger-safety",
        "overlap-ref:full-pytest-partial",
        "retain",
    ),
    VerifierValue(
        "verifier-ref:desktop-packaging",
        (
            "selector:command-ref:packaging-focused",
            "release-lane:desktop-packaging",
        ),
        "defect-ref:desktop-local-package-proof",
        "overlap-ref:frontend-none",
        "retain",
    ),
    VerifierValue(
        "verifier-ref:full-local-gate",
        (
            "selector:command-ref:verification:full-local-gate",
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


def load_measurements(path: Path = MEASUREMENT_PATH) -> dict[str, object]:
    metadata = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        raise ValueError("VERIFIER_MEASUREMENT_ARTIFACT_INVALID")
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("schema_version") != "uaa-verifier-value-measurements.v1":
        raise ValueError("VERIFIER_MEASUREMENT_SCHEMA_INVALID")
    if result.get("fingerprint") != _measurement_fingerprint(result):
        raise ValueError("VERIFIER_MEASUREMENT_FINGERPRINT_INVALID")
    return result


def required_coverage_refs() -> set[str]:
    selector_refs = {f"selector:{command_ref}" for command_ref in COMMANDS}
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
    if covered != required_coverage_refs():
        raise ValueError("VERIFIER_VALUE_COVERAGE_DRIFT")
    measurement_rows = measurements.get("measurements")
    if not isinstance(measurement_rows, list):
        raise ValueError("VERIFIER_MEASUREMENT_ROWS_INVALID")
    measurement_refs = {
        row.get("measurement_ref") for row in measurement_rows if isinstance(row, dict)
    }
    for value in values:
        if not value.coverage_refs or not all(
            (value.verifier_ref, value.unique_defect_ref, value.overlap_ref, value.disposition)
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
