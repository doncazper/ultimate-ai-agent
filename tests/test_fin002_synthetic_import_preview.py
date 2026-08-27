from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.finance import import_preview
from ultimate_ai_agent.core.finance.import_preview import (
    FinanceImportPreviewError,
    SyntheticImportPreview,
    load_synthetic_import_fixture_manifest,
    preview_synthetic_csv_fixture,
    synthetic_import_fixture_manifest_ref,
)


CLEAN_FIXTURE_REF = "fixture-ref:finance/FIN-002:synthetic-csv-clean:v1"
DUPLICATE_FIXTURE_REF = "fixture-ref:finance/FIN-002:synthetic-csv-duplicate:v1"
ADVERSARIAL_FIXTURE_REF = "fixture-ref:finance/FIN-002:synthetic-csv-adversarial:v1"
EXPECTED_MANIFEST_REF = (
    "fixture-manifest-ref:finance/FIN-002:sha256:"
    "c76f8728cf10aa5402b89be4d936779dc6023404f650531535f586d8b0d705de"
)


def test_manifest_is_exact_allowlisted_and_synthetic_only() -> None:
    fixtures = load_synthetic_import_fixture_manifest()
    assert synthetic_import_fixture_manifest_ref() == EXPECTED_MANIFEST_REF
    assert {item.fixture_ref for item in fixtures} == {
        CLEAN_FIXTURE_REF,
        DUPLICATE_FIXTURE_REF,
        ADVERSARIAL_FIXTURE_REF,
    }
    assert all(item.synthetic_only for item in fixtures)
    assert all(not item.arbitrary_operator_input_allowed for item in fixtures)


def test_clean_fixture_produces_typed_preview_and_noop_rollback_proof() -> None:
    preview = preview_synthetic_csv_fixture(CLEAN_FIXTURE_REF)

    assert (preview.row_count, preview.accepted_count) == (2, 2)
    assert preview.duplicate_count == preview.quarantine_count == 0
    assert len(preview.observations) == len(preview.candidates) == 2
    assert preview.rollback_proof.preview_ref == preview.preview_ref
    assert preview.rollback_proof.affected_candidate_refs == tuple(
        item.candidate_ref for item in preview.candidates
    )
    assert preview.rollback_proof.mutation_performed is False
    assert preview.rollback_proof.persistent_state_changed is False
    assert preview.rollback_proof.rollback_required is False


def test_duplicate_fixture_deduplicates_semantic_rows() -> None:
    preview = preview_synthetic_csv_fixture(DUPLICATE_FIXTURE_REF)

    assert preview.row_count == 2
    assert preview.accepted_count == 1
    assert preview.duplicate_count == 1
    assert preview.quarantine_count == 0
    assert preview.duplicate_fingerprint_refs == (
        preview.observations[0].source_fingerprint_ref,
    )


def test_existing_fingerprint_replay_is_duplicate_without_mutation() -> None:
    first = preview_synthetic_csv_fixture(CLEAN_FIXTURE_REF)
    replay = preview_synthetic_csv_fixture(
        CLEAN_FIXTURE_REF,
        existing_fingerprint_refs=(first.observations[0].source_fingerprint_ref,),
    )

    assert replay.accepted_count == 1
    assert replay.duplicate_count == 1
    assert replay.mutation_performed is False
    assert replay.rollback_proof.persistent_state_changed is False


def test_adversarial_rows_are_quarantined_without_raw_values() -> None:
    preview = preview_synthetic_csv_fixture(ADVERSARIAL_FIXTURE_REF)

    assert preview.accepted_count == preview.duplicate_count == 0
    assert preview.quarantine_count == 3
    assert {item.reason for item in preview.quarantines} == {
        "invalid_amount",
        "invalid_direction",
        "unsafe_cell",
    }
    serialized = json.dumps(preview.redacted_read_model(), sort_keys=True)
    for forbidden in ("synthetic-formula", "vendor-e", "amount_minor"):
        assert forbidden not in serialized


def test_unknown_fixture_and_invalid_existing_ref_fail_closed() -> None:
    with pytest.raises(FinanceImportPreviewError, match="FIN002_FIXTURE_REF_UNKNOWN"):
        preview_synthetic_csv_fixture("fixture-ref:finance/FIN-002:not-allowlisted:v1")
    with pytest.raises(ValueError):
        preview_synthetic_csv_fixture(
            CLEAN_FIXTURE_REF,
            existing_fingerprint_refs=("unsafe",),
        )
    with pytest.raises(ValueError):
        preview_synthetic_csv_fixture(
            CLEAN_FIXTURE_REF,
            existing_fingerprint_refs=("source-fingerprint-ref:sk_live_abc123",),
        )


def test_header_drift_fails_before_row_processing(monkeypatch) -> None:
    monkeypatch.setitem(
        import_preview._SYNTHETIC_FIXTURE_CSV,
        CLEAN_FIXTURE_REF,
        "unexpected_header\nvalue\n",
    )

    with pytest.raises(FinanceImportPreviewError, match="FIN002_CSV_HEADER_MISMATCH"):
        preview_synthetic_csv_fixture(CLEAN_FIXTURE_REF)


def test_preview_contract_rejects_count_and_rollback_binding_tamper() -> None:
    preview = preview_synthetic_csv_fixture(CLEAN_FIXTURE_REF)
    payload = preview.model_dump(mode="python")
    payload["accepted_count"] = 1
    with pytest.raises(ValidationError, match="FIN002_PREVIEW_COUNT_MISMATCH"):
        SyntheticImportPreview.model_validate(payload)

    payload = preview.model_dump(mode="python")
    payload["rollback_proof"]["preview_ref"] = (
        "import-preview-ref:finance/FIN-002:tampered"
    )
    with pytest.raises(
        ValidationError, match="FIN002_ROLLBACK_PREVIEW_BINDING_MISMATCH"
    ):
        SyntheticImportPreview.model_validate(payload)

    payload = preview.model_dump(mode="python")
    payload["candidates"][0]["observation_ref"] = (
        "observation-ref:finance/FIN-002:tampered"
    )
    with pytest.raises(
        ValidationError, match="FIN002_CANDIDATE_OBSERVATION_BINDING_MISMATCH"
    ):
        SyntheticImportPreview.model_validate(payload)

    payload = preview.model_dump(mode="python")
    payload["preview_ref"] = "import-preview-ref:finance/FIN-002:tampered"
    payload["rollback_proof"]["preview_ref"] = payload["preview_ref"]
    with pytest.raises(ValidationError, match="FIN002_PREVIEW_REF_BINDING_MISMATCH"):
        SyntheticImportPreview.model_validate(payload)

    payload = preview.model_dump(mode="python")
    payload["rollback_proof"]["rollback_ref"] = (
        "rollback-proof-ref:finance/FIN-002:tampered"
    )
    with pytest.raises(ValidationError, match="FIN002_ROLLBACK_REF_BINDING_MISMATCH"):
        SyntheticImportPreview.model_validate(payload)


def test_cli_exposes_manifest_and_redacted_fixture_preview_only() -> None:
    root = Path(__file__).resolve().parents[1]
    cli = root / "scripts/dev/uaa_finance_import.py"
    manifest = subprocess.run(
        [sys.executable, str(cli), "manifest"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert manifest.returncode == 0
    assert json.loads(manifest.stdout)["manifest_ref"] == EXPECTED_MANIFEST_REF

    preview = subprocess.run(
        [sys.executable, str(cli), "preview", "--fixture-ref", CLEAN_FIXTURE_REF],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert preview.returncode == 0
    payload = json.loads(preview.stdout)
    assert payload["counts"] == {
        "accepted": 2,
        "duplicates": 0,
        "quarantined": 0,
        "rows": 2,
    }
    assert payload["raw_source_content_included"] is False
    assert payload["mutation_performed"] is False

    rejected = subprocess.run(
        [
            sys.executable,
            str(cli),
            "preview",
            "--fixture-ref",
            "fixture-ref:finance/FIN-002:not-allowlisted:v1",
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert rejected.returncode == 2
    assert json.loads(rejected.stdout)["error_code"] == "FIN002_FIXTURE_REF_UNKNOWN"


def test_fin002_repository_verifier_passes() -> None:
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "scripts/verify_fin002_synthetic_import_preview.py"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "verification passed" in result.stdout
