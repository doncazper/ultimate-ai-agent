import json
from concurrent.futures import ThreadPoolExecutor

import scripts.run_foundation_gate as run_foundation_gate
from ultimate_ai_agent.core.gate.reports import FoundationGateResult, build_foundation_gate_report


class _FastFoundationGateEvaluator:
    def __init__(self, root=None):
        self.root = root

    def evaluate(self):
        return build_foundation_gate_report(
            version="test",
            results=[
                FoundationGateResult(
                    criterion_id="test_fast_gate_report",
                    status=run_foundation_gate.FoundationGateStatus.passed,
                    safe_message="Fast test report generated without repository scan.",
                )
            ],
        )


def _use_fast_gate_report(monkeypatch):
    monkeypatch.setattr(
        run_foundation_gate,
        "FoundationGateEvaluator",
        _FastFoundationGateEvaluator,
    )


def test_run_foundation_gate_writes_requested_output(tmp_path, monkeypatch):
    _use_fast_gate_report(monkeypatch)
    output_path = tmp_path / "gate_report.json"

    exit_code = run_foundation_gate.main(["--skip-commands", "--output", str(output_path)])

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["overall_status"] == "passed"
    assert payload["command_mode"] == "report-only"
    assert payload["command_receipts"][0]["status"] == "report_only"
    expected_count = len(payload["results"])
    assert payload["summary"] == f"{expected_count} passed, 0 failed, 0 warnings, 0 blocked."


def test_run_foundation_gate_ci_mode_records_external_verify_receipt(tmp_path, monkeypatch):
    _use_fast_gate_report(monkeypatch)
    output_path = tmp_path / "gate_report.json"

    exit_code = run_foundation_gate.main(
        ["--command-mode", "ci-after-verify-all", "--no-write-latest", "--output", str(output_path)]
    )

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["command_mode"] == "ci-after-verify-all"
    assert payload["command_receipts"][0]["command_ref"] == "command:scripts.verify_all"
    assert payload["command_receipts"][0]["status"] == "satisfied_external"
    assert payload["command_receipts"][0]["satisfied_by"] == "ci-master-verification"


def test_run_foundation_gate_parallel_ci_mode_records_external_verify_receipt(tmp_path, monkeypatch):
    _use_fast_gate_report(monkeypatch)
    output_path = tmp_path / "gate_report.json"

    exit_code = run_foundation_gate.main(
        ["--command-mode", "ci-parallel", "--no-write-latest", "--output", str(output_path)]
    )

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["command_mode"] == "ci-parallel"
    assert payload["command_receipts"][0]["command_ref"] == "command:ci.parallel_verification"
    assert payload["command_receipts"][0]["status"] == "satisfied_external"
    assert payload["command_receipts"][0]["satisfied_by"] == "ci-parallel-required-jobs"


def test_atomic_report_write_leaves_latest_json_valid_after_repeated_writes(tmp_path):
    report_path = tmp_path / "latest_foundation_gate_report.json"
    payloads = [
        {"report_id": "gate_report_1", "overall_status": "passed", "summary": "first"},
        {"report_id": "gate_report_2", "overall_status": "passed", "summary": "second"},
        {"report_id": "gate_report_3", "overall_status": "passed", "summary": "third"},
    ]

    for payload in payloads:
        run_foundation_gate.write_json_atomic(report_path, json.dumps(payload, indent=2))
        latest = json.loads(report_path.read_text(encoding="utf-8"))
        assert latest["overall_status"] == "passed"

    latest = json.loads(report_path.read_text(encoding="utf-8"))
    assert latest["report_id"] == "gate_report_3"
    assert report_path.stat().st_size > 0


def test_atomic_report_write_keeps_latest_json_parseable_under_concurrent_writes(tmp_path):
    report_path = tmp_path / "latest_foundation_gate_report.json"

    def write_report(index: int) -> None:
        payload = {
            "report_id": f"gate_report_{index}",
            "overall_status": "passed",
            "summary": f"{index} passed, 0 failed, 0 warnings, 0 blocked.",
        }
        run_foundation_gate.write_json_atomic(report_path, json.dumps(payload, indent=2))

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(write_report, range(16)))

    latest = json.loads(report_path.read_text(encoding="utf-8"))
    assert latest["overall_status"] == "passed"
    assert latest["report_id"].startswith("gate_report_")
    assert report_path.stat().st_size > 0
    assert not list(tmp_path.glob(".latest_foundation_gate_report.json.*.tmp"))
