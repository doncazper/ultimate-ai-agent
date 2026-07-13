from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import verify_uaa_runtime_capability_scoreboard as scoreboard


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = (
    ROOT / "docs" / "benchmarks" / "runtime_capability_foundation" / "phase00_baseline.json"
)
REPORT = ROOT / "docs" / "control_center" / "UAA_RUNTIME_CAPABILITY_SCOREBOARD.md"


def _data() -> dict[str, object]:
    return json.loads(BENCHMARK.read_text(encoding="utf-8"))


def test_phase00_benchmark_and_scoreboard_verify() -> None:
    data = scoreboard.verify(BENCHMARK, REPORT)
    assert len(data["components"]) == 16
    assert len(data["scenarios"]) == 12
    assert data["weighted_totals"] == {"uaa": 74.5, "goatcitadel": 84.3}


def test_pending_timing_fails_closed_by_default() -> None:
    data = _data()
    data["timing_snapshot"]["measurements"][0].update(
        {"status": "pending_measurement", "samples": [], "median": None}
    )
    with pytest.raises(scoreboard.VerificationError, match="remains pending"):
        scoreboard.verify_benchmark(data)


def test_exact_pending_and_external_blocked_timing_schemas_are_bounded() -> None:
    data = _data()
    data["timing_snapshot"]["measurements"][0] = {
        "command_ref": "command-ref:pytest-shards-tracked-seed",
        "status": "pending_measurement",
        "samples": [],
        "median": None,
    }
    scoreboard.verify_benchmark(data, allow_pending_timings=True)

    data["timing_snapshot"]["measurements"][0] = {
        "command_ref": "command-ref:pytest-shards-tracked-seed",
        "status": "external_blocked",
        "samples": [],
        "median": None,
        "blocker_ref": "blocker-ref:hosted-capacity",
    }
    scoreboard.verify_benchmark(data)
    data["timing_snapshot"]["measurements"][0]["notes"] = "extra"
    with pytest.raises(scoreboard.VerificationError, match="keys drift"):
        scoreboard.verify_benchmark(data)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("benchmark_ref", "benchmark-ref:changed", "benchmark_ref"),
        ("status", "draft", "benchmark status"),
    ),
)
def test_baseline_identity_is_pinned(field: str, value: str, message: str) -> None:
    data = _data()
    data[field] = value
    with pytest.raises(scoreboard.VerificationError, match=message):
        scoreboard.verify_benchmark(data)


def test_scoring_and_gap_contracts_are_pinned() -> None:
    data = _data()
    data["scoring"]["maximum"] = 11
    with pytest.raises(scoreboard.VerificationError, match="scoring bounds"):
        scoreboard.verify_benchmark(data)

    data = _data()
    data["gap_map"].append(
        {"gap_ref": "gap-ref:extra", "phase_owner": "phase_09", "terminal_posture": "blocked"}
    )
    with pytest.raises(scoreboard.VerificationError, match="exact finite gap"):
        scoreboard.verify_benchmark(data)

    data = _data()
    data["components"][0]["unknown_refs"] *= 2
    with pytest.raises(scoreboard.VerificationError, match="unknown refs must be unique"):
        scoreboard.verify_benchmark(data)


def test_score_arithmetic_rejects_drift() -> None:
    data = _data()
    data["components"][0]["uaa"]["score"] = 9.9
    with pytest.raises(scoreboard.VerificationError, match="weighted total drift"):
        scoreboard.verify_benchmark(data, allow_pending_timings=True)


@pytest.mark.parametrize("mutation", ("missing", "duplicate", "weight"))
def test_component_contract_is_exact(mutation: str) -> None:
    data = _data()
    if mutation == "missing":
        data["components"].pop()
    elif mutation == "duplicate":
        data["components"][1]["component_id"] = data["components"][0]["component_id"]
    else:
        data["components"][0]["weight"] = 9
    with pytest.raises(scoreboard.VerificationError):
        scoreboard.verify_benchmark(data, allow_pending_timings=True)


def test_component_taxonomy_and_unknowns_are_exact() -> None:
    data = _data()
    data["components"][0]["label"] = "Generic reasoning"
    with pytest.raises(scoreboard.VerificationError, match="taxonomy"):
        scoreboard.verify_benchmark(data)

    data = _data()
    data["components"][0]["unknown_refs"] = []
    with pytest.raises(scoreboard.VerificationError, match="unknown refs"):
        scoreboard.verify_benchmark(data)


@pytest.mark.parametrize(
    ("field", "value"),
    (("status", "aspirational"), ("confidence", "certain")),
)
def test_assessment_vocabulary_fails_closed(field: str, value: str) -> None:
    data = _data()
    data["components"][0]["uaa"][field] = value
    with pytest.raises(scoreboard.VerificationError, match=f"invalid uaa {field}"):
        scoreboard.verify_benchmark(data, allow_pending_timings=True)


def test_positive_score_requires_evidence() -> None:
    data = _data()
    data["components"][0]["uaa"]["evidence_refs"] = []
    with pytest.raises(scoreboard.VerificationError, match="requires evidence"):
        scoreboard.verify_benchmark(data, allow_pending_timings=True)


def test_every_gap_requires_phase_and_terminal_posture() -> None:
    data = _data()
    data["gap_map"][0]["terminal_posture"] = ""
    with pytest.raises(scoreboard.VerificationError, match="terminal posture"):
        scoreboard.verify_benchmark(data, allow_pending_timings=True)


def test_gap_owner_must_match_component_owner() -> None:
    data = _data()
    data["gap_map"][0]["phase_owner"] = "phase_02"
    with pytest.raises(scoreboard.VerificationError, match="gap owner"):
        scoreboard.verify_benchmark(data)


def test_scenario_contract_is_exact_and_ordered() -> None:
    data = _data()
    data["scenarios"].pop()
    with pytest.raises(scoreboard.VerificationError, match="twelve-scenario"):
        scoreboard.verify_benchmark(data, allow_pending_timings=True)


def test_scenario_requires_exact_phase_refs_and_summary() -> None:
    data = _data()
    data["scenarios"][0]["phase_refs"] = []
    with pytest.raises(scoreboard.VerificationError, match="scenario phase"):
        scoreboard.verify_benchmark(data)

    data = _data()
    data["scenarios"][0]["safe_summary"] = ""
    with pytest.raises(scoreboard.VerificationError, match="safe_summary"):
        scoreboard.verify_benchmark(data)


def test_goatcitadel_baseline_is_pinned_read_only() -> None:
    data = _data()
    data["comparison"]["goatcitadel"]["commit_ref"] = "git-sha:changed"
    with pytest.raises(scoreboard.VerificationError, match="GoatCitadel"):
        scoreboard.verify_benchmark(data, allow_pending_timings=True)


@pytest.mark.parametrize(
    "unsafe_fragment",
    (
        "/Users/example/private", "/home/example/private", "C:\\private\\file",
        "/tmp/private", "/etc/passwd", "/opt/private", "/Volumes/secret",
    ),
)
def test_absolute_paths_are_rejected(unsafe_fragment: str) -> None:
    data = _data()
    data["components"][0]["uaa"]["safe_summary"] = unsafe_fragment
    with pytest.raises(scoreboard.VerificationError, match="absolute local path"):
        scoreboard.verify_benchmark(data, allow_pending_timings=True)


@pytest.mark.parametrize(
    "unsafe_key",
    ("raw_prompt", "prompt_text", "message_body", "secret_value", "provider_payload"),
)
def test_unsafe_raw_field_is_rejected(unsafe_key: str) -> None:
    data = _data()
    data[unsafe_key] = "content"
    with pytest.raises(scoreboard.VerificationError, match="unsafe durable field"):
        scoreboard.verify_benchmark(data, allow_pending_timings=True)


def test_unknown_fields_and_secret_like_values_are_rejected() -> None:
    data = _data()
    data["notes"] = "benign"
    with pytest.raises(scoreboard.VerificationError, match="top-level benchmark keys drift"):
        scoreboard.verify_benchmark(data)

    data = _data()
    data["components"][0]["uaa"]["safe_summary"] = "api_key=synthetic-example"
    with pytest.raises(scoreboard.VerificationError, match="secret-like value"):
        scoreboard.verify_benchmark(data)


def test_web_hybrid_preservation_and_denials_are_exact() -> None:
    data = _data()
    data["preservation_refs"].remove("capability-ref:web.search.searxng.readonly")
    with pytest.raises(scoreboard.VerificationError, match="preservation refs drift"):
        scoreboard.verify_benchmark(data, allow_pending_timings=True)

    data = _data()
    data["denied_postures"].remove("browser_actions")
    with pytest.raises(scoreboard.VerificationError, match="denied postures drift"):
        scoreboard.verify_benchmark(data, allow_pending_timings=True)


def test_timing_median_is_recomputed() -> None:
    data = _data()
    measurement = data["timing_snapshot"]["measurements"][0]
    measurement.update({"status": "measured", "samples": [1.0, 2.0, 9.0], "median": 9.0})
    with pytest.raises(scoreboard.VerificationError, match="timing median drift"):
        scoreboard.verify_benchmark(data, allow_pending_timings=True)


@pytest.mark.parametrize("mutation", ("command", "runner", "safe", "count", "partition"))
def test_timing_topology_and_safety_are_exact(mutation: str) -> None:
    data = _data()
    if mutation == "command":
        data["timing_snapshot"]["measurements"][1]["command_ref"] = data["timing_snapshot"]["measurements"][0]["command_ref"]
    elif mutation == "runner":
        data["timing_snapshot"]["runner_profile_ref"] = "runner-profile:unknown"
    elif mutation == "safe":
        data["timing_snapshot"]["safe_summary_only"] = False
    elif mutation == "count":
        data["timing_snapshot"]["measurements"][0]["test_count"] = -1
    else:
        data["timing_snapshot"]["measurements"][0]["warm_samples"] = [1.0]
    with pytest.raises(scoreboard.VerificationError):
        scoreboard.verify_benchmark(data)


def test_report_hash_and_rows_reject_drift(tmp_path: Path) -> None:
    report = tmp_path / "scoreboard.md"
    report.write_text(REPORT.read_text(encoding="utf-8").replace("74.5/100", "74.6/100"), encoding="utf-8")
    with pytest.raises(scoreboard.VerificationError, match="scoreboard drift"):
        scoreboard.verify_report(_data(), report, BENCHMARK)


def test_benchmark_hash_changes_on_tamper(tmp_path: Path) -> None:
    tampered = tmp_path / "benchmark.json"
    original = BENCHMARK.read_bytes()
    tampered.write_bytes(original + b"\n")
    assert scoreboard._benchmark_hash(tampered) != scoreboard._benchmark_hash(BENCHMARK)
