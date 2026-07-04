from pathlib import Path

import scripts.verify_beta_13_frontend_loading_visual_proof as beta13


ROOT = Path(__file__).resolve().parents[1]


def test_beta_13_frontend_loading_visual_proof_verifier_passes() -> None:
    assert beta13.validate(ROOT) == []


def test_beta_13_frontend_loading_visual_proof_verifier_requires_state_scenarios(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "docs/control_center/visual_regression_manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        """
        {
          "schema_version": "uaa-control-center-visual-regression.v1",
          "status": "active checked-in visual baseline",
          "playwright_dependency_status": "control-center devDependency",
          "baseline_policy": {
            "checked_in_redacted_baselines_required": true,
            "raw_private_screenshots_allowed": false,
            "absolute_paths_allowed": false,
            "local_user_paths_allowed": false,
            "secret_material_allowed": false
          },
          "surfaces": [],
          "state_scenarios": []
        }
        """,
        encoding="utf-8",
    )

    failures = beta13.validate(tmp_path)

    assert any("visual state scenarios" in failure for failure in failures)
