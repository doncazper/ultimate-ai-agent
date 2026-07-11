from __future__ import annotations

import scripts.verify_operational_maturity as operational_maturity_verifier


def test_operational_maturity_manifest_passes_full_verifier() -> None:
    assert operational_maturity_verifier.verify() == []


def test_operational_maturity_full_verifier_runs_all_runtime_probes(
    monkeypatch,
) -> None:
    calls: list[str] = []

    def record_probe(name: str):
        def append_probe(_failures, *_args) -> None:
            calls.append(name)

        return append_probe

    monkeypatch.setattr(
        operational_maturity_verifier,
        "_append_public_request_schema_failures",
        record_probe("public_request_schema"),
    )
    monkeypatch.setattr(
        operational_maturity_verifier,
        "_append_mock_fallback_fixture_failures",
        record_probe("mock_fallback_fixture"),
    )
    monkeypatch.setattr(
        operational_maturity_verifier,
        "_append_behavior_probe_failures",
        record_probe("behavior"),
    )
    monkeypatch.setattr(
        operational_maturity_verifier,
        "_append_read_only_status_probe_failures",
        record_probe("read_only_status"),
    )

    assert operational_maturity_verifier.verify() == []
    assert calls == [
        "public_request_schema",
        "mock_fallback_fixture",
        "behavior",
        "read_only_status",
    ]
