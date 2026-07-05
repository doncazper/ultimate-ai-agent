import json
import os
import subprocess
import sys

from ultimate_ai_agent.core.extension_catalog import (
    build_default_inspectable_extension_catalog,
)


def test_phase09_extension_catalog_has_operator_posture_without_callability() -> None:
    catalog = build_default_inspectable_extension_catalog()
    payload = catalog.model_dump(mode="json")

    assert payload["read_only"] is True
    assert payload["inspectable_catalog_enabled"] is True
    assert payload["callable_catalog_enabled"] is False
    assert payload["runtime_import_enabled"] is False
    assert payload["execution_enabled"] is False
    assert payload["connector_writes_enabled"] is False
    assert payload["browser_automation_enabled"] is False
    assert payload["public_distribution_claimed"] is False
    assert "doc:goatcitadel-catchup-extensibility-final" in payload["docs_refs"]
    assert (
        "verifier:goatcitadel-catchup-extensibility-final"
        in payload["final_hardening_refs"]
    )

    for entry in payload["entries"]:
        assert entry["visibility_status"] in {
            "implemented",
            "partial",
            "planned",
            "mock_only",
            "blocked",
            "deprecated",
            "contradicted",
            "unknown",
        }
        assert entry["callable_posture"] in {
            "inspectable_only",
            "blocked_runtime",
            "future_exact_lane_required",
        }
        assert entry["callable_posture"] != "callable"
        assert entry["blocked_reason"]
        assert entry["review_evidence_refs"]
        assert entry["safe_adoption_posture"] in {
            "repo_owned_metadata_only",
            "reviewed_adaptation_required",
            "blocked_until_scoped_milestone",
        }


def test_uaa_extensions_cli_inspects_same_safe_catalog() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_extensions.py",
            "inspect-catalog",
        ],
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )

    payload = json.loads(result.stdout)
    assert payload["catalog_ref"] == "inspectable-catalog:uaa-extension-catalog-v1"
    assert payload["callable_catalog_enabled"] is False
    assert payload["runtime_import_enabled"] is False
    assert payload["execution_enabled"] is False
    assert payload["entries"]
