import json
import subprocess
import sys

from ultimate_ai_agent import __version__
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.openapi import verify_openapi_contract


def test_openapi_schema_has_unique_stable_operation_ids_and_manifest_path():
    schema = app.openapi()
    operation_ids = [
        operation["operationId"]
        for path_item in schema["paths"].values()
        for operation in path_item.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]

    assert schema["info"]["version"] == __version__
    assert "/api/manifest" in schema["paths"]
    assert schema["paths"]["/api/manifest"]["get"]["operationId"] == "get_api_manifest"
    assert len(operation_ids) == len(set(operation_ids))
    assert all("_" in operation_id for operation_id in operation_ids)


def test_openapi_contract_verifier_accepts_current_app():
    status = verify_openapi_contract(app)

    assert status.version_consistent is True
    assert status.openapi_generated is True
    assert status.route_inventory_valid is True
    assert status.unsafe_routes_detected is False
    assert status.errors == []


def test_export_openapi_script_writes_valid_json_to_stdout():
    result = subprocess.run(
        [sys.executable, "scripts/export_openapi.py"],
        check=True,
        capture_output=True,
        text=True,
    )

    schema = json.loads(result.stdout)
    assert schema["info"]["version"] == __version__
    assert "/api/manifest" in schema["paths"]


def test_verify_all_runs_openapi_contract_verifier():
    verify_all = open("scripts/verify_all.py", encoding="utf-8").read()

    assert "scripts/verify_openapi_contract.py" in verify_all
