import json

import scripts.run_foundation_gate as run_foundation_gate
from ultimate_ai_agent.core.gate import default_foundation_gate_criteria


def test_run_foundation_gate_writes_requested_output(tmp_path):
    output_path = tmp_path / "gate_report.json"

    exit_code = run_foundation_gate.main(["--skip-commands", "--output", str(output_path)])

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["overall_status"] == "passed"
    expected_count = len(default_foundation_gate_criteria())
    assert payload["summary"] == f"{expected_count} passed, 0 failed, 0 warnings, 0 blocked."
