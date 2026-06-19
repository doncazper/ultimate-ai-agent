import copy
import json
from pathlib import Path

import scripts.verify_agent_module_maturity_map as verifier


ROOT = Path(__file__).resolve().parent.parent
MAP_PATH = ROOT / "docs/registry/agent_module_maturity_map.json"


def _payload() -> dict:
    return json.loads(MAP_PATH.read_text(encoding="utf-8"))


def test_agent_module_maturity_map_verifier_passes_current_repo():
    assert verifier.verify(ROOT, MAP_PATH) == []


def test_agent_module_maturity_map_covers_requested_modules_exactly():
    payload = _payload()
    module_ids = {module["id"] for module in payload["modules"]}

    assert module_ids == verifier.REQUIRED_MODULE_IDS


def test_agent_module_maturity_map_flags_missing_referenced_path():
    payload = _payload()
    broken = copy.deepcopy(payload)
    broken["modules"][0]["primary_paths"] = ["src/ultimate_ai_agent/core/not_real.py"]

    failures = verifier.verify_payload(broken, ROOT)

    assert any("references missing path" in failure for failure in failures)


def test_agent_module_maturity_map_flags_unknown_maturity():
    payload = _payload()
    broken = copy.deepcopy(payload)
    broken["modules"][0]["maturity"] = "vibes_only"

    failures = verifier.verify_payload(broken, ROOT)

    assert any("unknown maturity level" in failure for failure in failures)
