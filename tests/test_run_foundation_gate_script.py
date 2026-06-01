import json

import scripts.run_foundation_gate as run_foundation_gate


def test_run_foundation_gate_writes_requested_output(tmp_path):
    output_path = tmp_path / "gate_report.json"

    exit_code = run_foundation_gate.main(["--skip-commands", "--output", str(output_path)])

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["overall_status"] == "passed"
    assert payload["summary"] == "20 passed, 0 failed, 0 warnings, 0 blocked."
