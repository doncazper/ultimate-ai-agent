import scripts.verify_control_center_visual_regression as visual
import scripts.verify_local_runtime_packaging_proof as packaging


def test_control_center_visual_regression_manifest_is_safe() -> None:
    failures = visual.validate_manifest(visual.load_manifest())

    assert failures == []


def test_local_runtime_packaging_proof_manifest_is_safe() -> None:
    failures = packaging.validate_manifest(packaging.load_manifest())

    assert failures == []


def test_local_runtime_packaging_proof_summary_shape_is_safe() -> None:
    summary = {
        "schema_version": "uaa-local-runtime-packaging-proof-summary.v1",
        "status": "passed",
        "proof_ref": "packaging-proof:latest",
        "distribution_claims_allowed": False,
        "route_manifest": {
            "endpoint_ref": "local-loopback-api-manifest",
            "route_count": 112,
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
