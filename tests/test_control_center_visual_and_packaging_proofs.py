from pathlib import Path

import scripts.verify_control_center_visual_regression as visual
import scripts.verify_local_runtime_packaging_proof as packaging


ROOT = Path(__file__).resolve().parents[1]


def test_control_center_visual_regression_manifest_is_safe() -> None:
    failures = visual.validate_manifest(visual.load_manifest())

    assert failures == []


def test_control_center_visual_regression_manifest_requires_state_scenarios() -> None:
    manifest = visual.load_manifest()
    manifest["state_scenarios"] = []

    failures = visual.validate_manifest(manifest)

    assert any(
        "missing state scenario: state-loading" in failure for failure in failures
    )
    assert any(
        "missing state scenario: state-success" in failure for failure in failures
    )


def test_control_center_visual_regression_manifest_keeps_non_macos_ports_as_placeholders() -> (
    None
):
    manifest = visual.load_manifest()
    manifest["platform_posture"]["linux"]["status"] = "implemented"

    failures = visual.validate_manifest(manifest)

    assert (
        "visual platform posture must implement macOS and keep Linux/Windows as deferred render placeholders"
        in failures
    )


def test_control_center_visual_regression_requires_both_studio_desktop_variants() -> (
    None
):
    manifest = visual.load_manifest()
    studio = next(
        surface
        for surface in manifest["surfaces"]
        if surface["surface"] == "Studio Skill Workbench"
    )
    studio["desktop_variants"].pop("compact")

    failures = visual.validate_manifest(manifest)

    assert (
        "Studio Skill Workbench must list wide and compact desktop variants" in failures
    )


def test_control_center_visual_regression_rejects_studio_mobile_variant() -> None:
    manifest = visual.load_manifest()
    studio = next(
        surface
        for surface in manifest["surfaces"]
        if surface["surface"] == "Studio Skill Workbench"
    )
    studio["desktop_variants"]["mobile"] = {}

    failures = visual.validate_manifest(manifest)

    assert any("Studio Skill Workbench" in failure for failure in failures)


def test_control_center_visual_regression_requires_all_messenger_desktop_variants() -> (
    None
):
    manifest = visual.load_manifest()
    messenger = next(
        surface
        for surface in manifest["surfaces"]
        if surface["surface"] == "Messenger Desktop Fixture"
    )
    messenger["desktop_variants"].pop("founder-compact")

    failures = visual.validate_manifest(manifest)

    assert (
        "Messenger Desktop Fixture must list all 15 surfaces at wide and compact desktop widths"
        in failures
    )


def test_control_center_visual_regression_rejects_messenger_mobile_variant() -> None:
    manifest = visual.load_manifest()
    messenger = next(
        surface
        for surface in manifest["surfaces"]
        if surface["surface"] == "Messenger Desktop Fixture"
    )
    messenger["desktop_variants"]["mobile"] = {}

    failures = visual.validate_manifest(manifest)

    assert any("Messenger Desktop Fixture" in failure for failure in failures)


def test_local_runtime_packaging_proof_manifest_is_safe() -> None:
    failures = packaging.validate_manifest(packaging.load_manifest())

    assert failures == []


def test_local_runtime_binds_exact_selected_control_center_origin() -> None:
    compose = (ROOT / "packaging/local-runtime/compose.yaml").read_text()

    assert (
        "UAA_CONTROL_CENTER_CORS_ORIGIN: "
        "http://127.0.0.1:${UAA_LOCAL_RUNTIME_CONTROL_CENTER_PORT:-5173}"
    ) in compose


def test_local_runtime_operator_entry_binds_clean_source_and_session_bearer() -> None:
    operator = (ROOT / "scripts/dev/uaa_local_runtime.py").read_text()
    compose = (ROOT / "packaging/local-runtime/compose.yaml").read_text()
    auth = (ROOT / "src/ultimate_ai_agent/api/local_auth.py").read_text()

    assert operator.index("verified_clean_source_commit(ROOT)") < operator.index(
        '_run_compose(["up"'
    )
    assert '"UAA_BUILD_COMMIT": commit' in operator
    assert '"UAA_LOCAL_RUNTIME_VERIFIED_SOURCE": "verified-clean-source:v1"' in operator
    assert "uaa-session-bearer" in operator
    assert "webbrowser.open(session_url)" in operator
    assert "UAA_LOCAL_RUNTIME_VERIFIED_SOURCE: ${UAA_LOCAL_RUNTIME_VERIFIED_SOURCE:?" in compose
    assert "UAA_LOCAL_RUNTIME_SECRET_FILE: /run/secrets/uaa_local_runtime_secret" in compose
    assert 'LOCAL_API_BEARER_FILE_ENV = "UAA_LOCAL_RUNTIME_SECRET_FILE"' in auth


def test_local_runtime_packaging_proof_summary_shape_is_safe() -> None:
    summary = {
        "schema_version": "uaa-local-runtime-packaging-proof-summary.v1",
        "status": "passed",
        "proof_ref": "packaging-proof:latest",
        "distribution_claims_allowed": False,
        "route_manifest": {
            "endpoint_ref": "local-loopback-api-manifest",
            "route_count": 127,
        },
        "screenshot_proof": {
            "safe_evidence_ref": "packaging-proof:screenshot-capture",
            "artifact_ref": "packaging-proof-artifact:control-center-today",
            "sha256": "sha256:" + ("a" * 64),
            "raw_private_screenshot_included": False,
        },
        "steps": [
            {
                "step_id": step_id,
                "status": "passed",
                "safe_evidence_ref": f"packaging-proof:{step_id}",
                "raw_log_included": False,
                "reason_codes": [],
            }
            for step_id in packaging.REQUIRED_STEPS
        ],
        "redactions_applied": [
            "raw_logs_omitted",
            "raw_paths_omitted",
            "credentials_omitted",
            "safe_refs_only",
        ],
    }

    assert packaging.validate_summary(summary) == []


def test_local_runtime_packaging_proof_summary_requires_passed_loop() -> None:
    summary = {
        "schema_version": "uaa-local-runtime-packaging-proof-summary.v1",
        "status": "failed",
        "proof_ref": "packaging-proof:latest",
        "distribution_claims_allowed": False,
        "route_manifest": {
            "endpoint_ref": "local-loopback-api-manifest",
            "route_count": 0,
        },
        "screenshot_proof": {
            "safe_evidence_ref": "packaging-proof:screenshot-capture",
            "artifact_ref": "packaging-proof-artifact:control-center-today",
            "sha256": "sha256:" + ("a" * 64),
            "raw_private_screenshot_included": False,
        },
        "steps": [
            {
                "step_id": step_id,
                "status": "passed",
                "safe_evidence_ref": f"packaging-proof:{step_id}",
                "raw_log_included": False,
                "reason_codes": [],
            }
            for step_id in packaging.REQUIRED_STEPS
        ],
        "redactions_applied": [
            "raw_logs_omitted",
            "raw_paths_omitted",
            "credentials_omitted",
            "safe_refs_only",
        ],
    }

    summary["steps"][0]["status"] = "failed"

    failures = packaging.validate_summary(summary)

    assert "packaging proof summary status must be passed" in failures
    assert "packaging proof summary route count must be positive" in failures
    assert any("summary status must be passed" in failure for failure in failures)
